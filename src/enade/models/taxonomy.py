"""Hierarchical taxonomy contract: subject (area) -> topic -> concept.

A concept carries its own keywords, aliases and prerequisite concept ids,
so we can distinguish e.g. "Arvores" (topic) from "Arvores Binarias" and
"Arvores Balanceadas" (concepts), rather than relying on flat free-text
keywords alone (see PROMPT section 13).

IMPORTANT: :data:`demo-taxonomy.yaml` is a small demonstration fixture
used to validate the schema shape - it is explicitly *not* the
scientific/definitive Computing taxonomy. The first real (though
``provisional``) taxonomy is ``data/taxonomy/computing-v1.yaml`` (PROMPT
Fase 5A) - see ``status``/``notice`` on each document for its own
maturity, and docs/taxonomy.md before extending either for real.

PROMPT Fase 5A (section 8) extended every node (``Subject``/``Topic``/
``Concept``) with a shared, richer contract - ``description``,
``inclusion_criteria``, ``exclusion_criteria``, ``related_ids``,
``source_references``, per-node ``status`` (active/deprecated) - all
additive, with defaults, so ``demo-taxonomy.yaml`` and every pre-existing
fixture needed no migration. ``parent_id``/``level`` are deliberately
*not* stored fields: the nested YAML shape (``Subject.topics``,
``Topic.concepts``) already encodes parent/child unambiguously and makes
a stored, potentially-inconsistent duplicate of that same fact
impossible by construction (see ``TaxonomyNodeView``/``flatten()`` for
the derived, read-only view that exposes them as computed values instead
- the same "never a second source of truth" discipline this project
already applies to e.g. `AssetBlock.asset_id` pointers).
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterator

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from enade.models.enums import TaxonomyNodeStatus, TaxonomyStatus

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SHA256_PATTERN = r"^[0-9a-f]{64}$"


def _validate_slug(v: str, kind: str) -> str:
    if not SLUG_PATTERN.match(v):
        raise ValueError(f"{kind} id {v!r} must be lowercase kebab-case")
    return v


def normalize_alias(text: str) -> str:
    """Case/accent/whitespace-insensitive key used only to detect a
    *silent* alias collision (PROMPT Fase 5A section 8) - never used to
    alter a displayed label/alias, which always keeps its original form.
    """
    decomposed = unicodedata.normalize("NFKD", text)
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", stripped).strip().casefold()


class SourceReference(BaseModel):
    """One documental grounding for a taxonomy node or document (PROMPT
    Fase 5A section 5) - an institutional source only, never a copy of
    its content. ``url``/``org``/``version``/``date`` are optional
    because a node justified purely by corpus recurrence (section 9's
    other, independent inclusion ground) legitimately has no external
    document to cite at all - only ``title`` is required, so a source
    reference can also record "corpus recurrence: <justification>"
    without pretending that is an institutional document.
    """

    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=1)
    url: str | None = None
    org: str | None = None
    version: str | None = None
    date: str | None = None
    sha256: str | None = Field(default=None, pattern=SHA256_PATTERN)


class _NodeCommon(BaseModel):
    """Fields shared by every taxonomy node level (PROMPT Fase 5A section
    8) - never instantiated directly.
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    description: str | None = None
    aliases: list[str] = Field(default_factory=list)
    inclusion_criteria: list[str] = Field(default_factory=list)
    exclusion_criteria: list[str] = Field(default_factory=list)
    related_ids: list[str] = Field(default_factory=list)
    source_references: list[SourceReference] = Field(default_factory=list)
    status: TaxonomyNodeStatus = TaxonomyNodeStatus.ACTIVE


class Concept(_NodeCommon):
    keywords: list[str] = Field(default_factory=list)
    prerequisites: list[str] = Field(default_factory=list, description="ids of other concepts")

    @field_validator("id")
    @classmethod
    def _id_slug(cls, v: str) -> str:
        return _validate_slug(v, "concept")


class Topic(_NodeCommon):
    concepts: list[Concept] = Field(default_factory=list)

    @field_validator("id")
    @classmethod
    def _id_slug(cls, v: str) -> str:
        return _validate_slug(v, "topic")


class Subject(_NodeCommon):
    topics: list[Topic] = Field(default_factory=list)

    @field_validator("id")
    @classmethod
    def _id_slug(cls, v: str) -> str:
        return _validate_slug(v, "subject")


class TaxonomyNodeView(BaseModel):
    """Read-only, flattened projection of one node - the derived
    ``parent_id``/``level`` PROMPT Fase 5A section 8 asks a node to
    "consider" are computed here from nesting position, never stored
    redundantly on the node itself (see module docstring).
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    kind: str  # "subject" | "topic" | "concept"
    level: int  # 0=subject/area, 1=topic, 2=concept
    parent_id: str | None
    node: Subject | Topic | Concept


class Taxonomy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    #: Stable identity of this taxonomy *document* (PROMPT section 8) -
    #: distinct from ``version`` (which changes every revision); absent
    #: from every pre-Fase-5A fixture, so it defaults to "" (falsy/unset)
    #: rather than being required, keeping ``demo-taxonomy.yaml`` valid
    #: unmodified.
    taxonomy_id: str = ""
    version: str
    status: TaxonomyStatus
    notice: str = Field(
        ...,
        min_length=1,
        description="Human-readable disclaimer about the maturity/completeness of this taxonomy.",
    )
    language: str = "pt-BR"
    created_from: list[SourceReference] = Field(default_factory=list)
    subjects: list[Subject] = Field(default_factory=list)

    def flatten(self) -> Iterator[TaxonomyNodeView]:
        """Yields every node exactly once, depth-first, with its derived
        ``parent_id``/``level`` - the single place any validator/query
        that needs those two facts computes them, instead of trusting a
        stored field that could silently disagree with real nesting.
        """
        for subject in self.subjects:
            yield TaxonomyNodeView(
                id=subject.id, kind="subject", level=0, parent_id=None, node=subject
            )
            for topic in subject.topics:
                yield TaxonomyNodeView(
                    id=topic.id, kind="topic", level=1, parent_id=subject.id, node=topic
                )
                for concept in topic.concepts:
                    yield TaxonomyNodeView(
                        id=concept.id, kind="concept", level=2, parent_id=topic.id, node=concept
                    )

    @model_validator(mode="after")
    def _check_ids_unique_and_prerequisites_resolve(self) -> Taxonomy:
        all_ids: set[str] = set()
        concept_ids: set[str] = set()
        duplicates: set[str] = set()

        def register(node_id: str) -> None:
            if node_id in all_ids:
                duplicates.add(node_id)
            all_ids.add(node_id)

        for subject in self.subjects:
            register(subject.id)
            for topic in subject.topics:
                register(topic.id)
                for concept in topic.concepts:
                    register(concept.id)
                    concept_ids.add(concept.id)

        if duplicates:
            raise ValueError(f"duplicate taxonomy ids: {sorted(duplicates)}")

        unresolved: list[str] = []
        for subject in self.subjects:
            for topic in subject.topics:
                for concept in topic.concepts:
                    for prereq in concept.prerequisites:
                        if prereq == concept.id:
                            unresolved.append(f"{concept.id} -> {prereq} (self-reference)")
                        elif prereq not in concept_ids:
                            unresolved.append(f"{concept.id} -> {prereq}")
        if unresolved:
            raise ValueError(f"unresolved concept prerequisites: {unresolved}")

        return self

    @model_validator(mode="after")
    def _check_related_ids_resolve(self) -> Taxonomy:
        """PROMPT Fase 5A section 8: ``related_ids`` is an explicitly
        *non*-hierarchical cross-reference (unlike nesting, it is never
        checked for cycles - a symmetric-ish "see also", not a
        parent/child edge) - it must still only ever point at a real id.
        """
        all_ids = {view.id for view in self.flatten()}
        unresolved: list[str] = []
        for view in self.flatten():
            for related in view.node.related_ids:
                if related == view.id:
                    unresolved.append(f"{view.id} -> {related} (self-reference)")
                elif related not in all_ids:
                    unresolved.append(f"{view.id} -> {related}")
        if unresolved:
            raise ValueError(f"unresolved related_ids: {unresolved}")
        return self

    @model_validator(mode="after")
    def _check_alias_collisions(self) -> Taxonomy:
        """PROMPT Fase 5A section 8: "aliases normalizados não podem
        colidir silenciosamente" - two *different* nodes must never
        share a normalized alias (or an alias that normalizes to another
        node's own name), since that would make alias-based lookup
        silently ambiguous. A node listing its own name as an alias of
        itself is harmless and not flagged.
        """
        owners: dict[str, str] = {}
        collisions: list[str] = []
        for view in self.flatten():
            candidates = {
                normalize_alias(view.node.name),
                *(normalize_alias(a) for a in view.node.aliases),
            }
            for key in candidates:
                if not key:
                    continue
                existing = owners.get(key)
                if existing is not None and existing != view.id:
                    collisions.append(f"{key!r} claimed by both {existing!r} and {view.id!r}")
                else:
                    owners[key] = view.id
        if collisions:
            raise ValueError(f"colliding normalized aliases: {sorted(set(collisions))}")
        return self

    @model_validator(mode="after")
    def _check_deterministic_ordering(self) -> Taxonomy:
        """PROMPT Fase 5A section 8: "ordem do YAML/JSON deve ser
        determinística" - enforced here as sorted-by-id at every level,
        so two independently-authored copies of the same logical
        taxonomy always serialize identically.

        Scoped to documents that declare a non-empty ``taxonomy_id``
        (the Fase 5A field): checked directly against
        ``data/taxonomy/demo-taxonomy.yaml`` (which never sets it) and
        found genuinely *not* sorted (``estruturas-de-dados`` before
        ``complexidade-de-algoritmos``) - a real, pre-existing, harmless
        fact about that fixture, never noticed because nothing checked
        for it before. Retroactively failing that protected fixture
        would be exactly the kind of silent-breaking-change section 8
        itself warns against ("mudanca de significado exige nova
        versao") - so this gate applies only to taxonomies that opt in
        by declaring their own ``taxonomy_id``, never retroactively.
        """
        if not self.taxonomy_id:
            return self
        offenders: list[str] = []
        subject_ids = [s.id for s in self.subjects]
        if subject_ids != sorted(subject_ids):
            offenders.append("subjects")
        for subject in self.subjects:
            topic_ids = [t.id for t in subject.topics]
            if topic_ids != sorted(topic_ids):
                offenders.append(f"{subject.id}.topics")
            for topic in subject.topics:
                concept_ids = [c.id for c in topic.concepts]
                if concept_ids != sorted(concept_ids):
                    offenders.append(f"{topic.id}.concepts")
        if offenders:
            raise ValueError(f"non-deterministic (unsorted) ordering at: {offenders}")
        return self
