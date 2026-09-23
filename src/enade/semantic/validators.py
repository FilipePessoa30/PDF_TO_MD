"""Cross-artifact validators for the semantic layer (PROMPT Fase 5A
section 23) - each one *re-derives* ground truth from the real,
published corpus/taxonomy rather than trusting a claim already made
elsewhere. Every function here only ever reports; none of them repair or
promote an annotation's own status (the same discipline
``enade.extraction.content_assignment``'s own gates already follow).
"""

from __future__ import annotations

import unicodedata
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from enade.models.taxonomy import Taxonomy
from enade.semantic.annotation import QuestionAnnotation, source_file_sha256


@dataclass(frozen=True)
class Diagnostic:
    """One validator finding - always names the question and the field
    it concerns, per PROMPT section 23 ("diagnosticos por questao e
    campo"), never a bare count.
    """

    kind: str
    question_id: str
    field: str
    detail: str


def _flatten_ids_by_kind(taxonomy: Taxonomy) -> dict[str, set[str]]:
    by_kind: dict[str, set[str]] = {"subject": set(), "topic": set(), "concept": set()}
    for view in taxonomy.flatten():
        by_kind[view.kind].add(view.id)
    return by_kind


def validate_annotation_against_taxonomy(
    annotation: QuestionAnnotation, taxonomy: Taxonomy, taxonomy_version: str
) -> list[Diagnostic]:
    """PROMPT section 23: taxonomy version exists; every topic/concept id
    referenced actually exists in that taxonomy; no reference to a
    ``deprecated`` node.
    """
    diagnostics: list[Diagnostic] = []
    qid = annotation.question_id

    if annotation.taxonomy_version != taxonomy_version:
        diagnostics.append(
            Diagnostic(
                kind="taxonomy_version_mismatch",
                question_id=qid,
                field="taxonomy_version",
                detail=f"annotation declares {annotation.taxonomy_version!r}, loaded taxonomy is {taxonomy_version!r}",
            )
        )
        return diagnostics  # comparing ids across mismatched versions is meaningless

    ids_by_kind = _flatten_ids_by_kind(taxonomy)
    topic_and_subject_ids = ids_by_kind["subject"] | ids_by_kind["topic"]
    concept_ids = ids_by_kind["concept"]
    status_by_id = {view.id: view.node.status.value for view in taxonomy.flatten()}

    for field_name, topics in (
        ("primary_topics", annotation.primary_topics),
        ("secondary_topics", annotation.secondary_topics),
    ):
        for topic_id in topics:
            if topic_id not in topic_and_subject_ids:
                diagnostics.append(
                    Diagnostic(
                        kind="topic_not_found",
                        question_id=qid,
                        field=field_name,
                        detail=f"{topic_id!r} does not exist in taxonomy {taxonomy_version!r}",
                    )
                )
            elif status_by_id.get(topic_id) == "deprecated":
                diagnostics.append(
                    Diagnostic(
                        kind="topic_deprecated",
                        question_id=qid,
                        field=field_name,
                        detail=f"{topic_id!r} is deprecated in taxonomy {taxonomy_version!r}",
                    )
                )

    for concept in annotation.concepts:
        if concept.concept_id not in concept_ids:
            diagnostics.append(
                Diagnostic(
                    kind="concept_not_found",
                    question_id=qid,
                    field="concepts",
                    detail=f"{concept.concept_id!r} does not exist in taxonomy {taxonomy_version!r}",
                )
            )
        elif status_by_id.get(concept.concept_id) == "deprecated":
            diagnostics.append(
                Diagnostic(
                    kind="concept_deprecated",
                    question_id=qid,
                    field="concepts",
                    detail=f"{concept.concept_id!r} is deprecated in taxonomy {taxonomy_version!r}",
                )
            )

    return diagnostics


def validate_evidence_integrity(
    annotation: QuestionAnnotation, questions_dir: Path
) -> list[Diagnostic]:
    """PROMPT section 15/23: every evidence ref's ``source_sha256`` must
    match the *real*, current published Markdown file - never trust a
    hash recorded at annotation time forever. Also confirms the question
    itself still exists and that ``source_hash`` (the annotation's own
    top-level field) matches too - the same "source hash stale" check
    section 23 asks for.
    """
    diagnostics: list[Diagnostic] = []
    qid = annotation.question_id
    md_path = questions_dir / f"{qid}.md"

    if not md_path.is_file():
        diagnostics.append(
            Diagnostic(
                kind="source_question_missing",
                question_id=qid,
                field="question_id",
                detail=f"no published Markdown found at {md_path}",
            )
        )
        return diagnostics  # nothing else here is checkable without the file

    real_hash = source_file_sha256(md_path)
    if annotation.source_hash != real_hash:
        diagnostics.append(
            Diagnostic(
                kind="source_hash_stale",
                question_id=qid,
                field="source_hash",
                detail=f"annotation recorded {annotation.source_hash!r}, real file is {real_hash!r}",
            )
        )

    all_evidence = list(annotation.evidence) + [
        ref for concept in annotation.concepts for ref in concept.evidence_refs
    ]
    for i, ref in enumerate(all_evidence):
        if ref.source_sha256 != real_hash:
            diagnostics.append(
                Diagnostic(
                    kind="evidence_source_hash_stale",
                    question_id=qid,
                    field=f"evidence[{i}].source_sha256",
                    detail=f"recorded {ref.source_sha256!r}, real file is {real_hash!r}",
                )
            )
        if ref.asset_path is not None:
            asset_full_path = questions_dir / ref.asset_path
            if not asset_full_path.is_file():
                diagnostics.append(
                    Diagnostic(
                        kind="evidence_asset_missing",
                        question_id=qid,
                        field=f"evidence[{i}].asset_path",
                        detail=f"{asset_full_path} does not exist",
                    )
                )
            elif ref.asset_sha256 is not None:
                real_asset_hash = source_file_sha256(asset_full_path)
                if real_asset_hash != ref.asset_sha256:
                    diagnostics.append(
                        Diagnostic(
                            kind="evidence_asset_hash_stale",
                            question_id=qid,
                            field=f"evidence[{i}].asset_sha256",
                            detail=f"recorded {ref.asset_sha256!r}, real file is {real_asset_hash!r}",
                        )
                    )
    return diagnostics


def validate_shared_question_consistency(
    annotations: list[QuestionAnnotation], canonical_of: dict[str, str]
) -> list[Diagnostic]:
    """PROMPT section 10/23: a question shared canonically across
    courses must never receive divergent annotations under two different
    ids. ``canonical_of`` maps every question_id that appears in
    ``annotations`` to its own canonical identity (the identity function
    for a question that is not shared at all).
    """
    diagnostics: list[Diagnostic] = []
    by_canonical: dict[str, list[QuestionAnnotation]] = defaultdict(list)
    for annotation in annotations:
        canonical = canonical_of.get(annotation.question_id, annotation.question_id)
        by_canonical[canonical].append(annotation)

    for canonical, group in by_canonical.items():
        if len(group) < 2:
            continue
        primary_sets = {tuple(sorted(a.primary_topics)) for a in group}
        if len(primary_sets) > 1:
            ids = sorted(a.question_id for a in group)
            diagnostics.append(
                Diagnostic(
                    kind="shared_question_divergent_annotation",
                    question_id=canonical,
                    field="primary_topics",
                    detail=f"{ids} disagree on primary_topics: {sorted(primary_sets)}",
                )
            )
    return diagnostics


#: An explicit denylist of common Portuguese dictionary words that carry
#: essentially no discriminating power on their own (PROMPT Fase 5B
#: section 14's own illustrative list, plus the exact words the real Fase
#: 5A finding identified on ``teoria-geral-de-sistemas``). Deliberately
#: NOT a length-based rule: a short technical acronym ("SQL", "DER",
#: "TDA", "SaaS", "CDMA", "CID"...) is exactly as short as these words but
#: has strong discriminating power precisely because it is *not* an
#: ordinary dictionary word - conflating "short" with "generic" would
#: flag the taxonomy's own best, most precise keywords as if they were
#: the defect this validator exists to catch.
_GENERIC_KEYWORD_DENYLIST = frozenset(
    {
        "sistema",
        "processo",
        "modelo",
        "rede",
        "estrutura",
        "dados",
        "programa",
        "funcao",
        "servico",
        "informacao",
        "ambiente",
        "entrada",
        "saida",
        "feedback",
    }
)


def _normalize_keyword(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    return stripped.strip().casefold()


def validate_taxonomy_keywords_are_not_bare_generic_terms(taxonomy: Taxonomy) -> list[Diagnostic]:
    """PROMPT Fase 5B section 14/25: a concept's own ``keywords``/``aliases``
    must never be a single bare generic dictionary word with no
    discriminating power - the exact defect Fase 5A found (and fixed) on
    ``teoria-geral-de-sistemas``. Flags any node whose keyword/alias,
    once normalized, exactly matches ``_GENERIC_KEYWORD_DENYLIST`` (a
    multi-word phrase built from a generic word, e.g. "entrada e saida do
    sistema", is fine - only a bare single generic word is flagged; a
    short but specific acronym like "SQL"/"TDA"/"SaaS" is never flagged
    just for being short).
    """
    diagnostics: list[Diagnostic] = []
    for view in taxonomy.flatten():
        all_labels = list(view.node.aliases) + list(getattr(view.node, "keywords", []) or [])
        for label in all_labels:
            normalized = _normalize_keyword(label)
            if normalized in _GENERIC_KEYWORD_DENYLIST:
                diagnostics.append(
                    Diagnostic(
                        kind="generic_keyword_without_context",
                        question_id="<taxonomy>",
                        field=f"{view.id}.keywords",
                        detail=f"{label!r} is a bare generic dictionary term with no discriminating power",
                    )
                )
    return diagnostics


def validate_migration_entries_have_reason(migration_entries: list[dict]) -> list[Diagnostic]:
    """PROMPT Fase 5B section 15/25: 'migracao sem razao' - every migration
    log entry must record a non-trivial ``change_reason``, even for an
    ``unchanged`` entry (which still must say *why* nothing changed, per
    section 16: "questoes sem alteracao tambem devem aparecer como
    unchanged, para provar que foram revisadas").
    """
    diagnostics: list[Diagnostic] = []
    for entry in migration_entries:
        reason = entry.get("change_reason")
        if not reason or not str(reason).strip():
            diagnostics.append(
                Diagnostic(
                    kind="migration_without_reason",
                    question_id=entry.get("question_id", "<unknown>"),
                    field="change_reason",
                    detail="migration entry has an empty change_reason",
                )
            )
    return diagnostics


def validate_no_taxonomy_id_meaning_changed(old: Taxonomy, new: Taxonomy) -> list[Diagnostic]:
    """PROMPT Fase 5B section 15/25: 'ID reutilizado com novo significado' -
    any node id present in *both* taxonomy versions must keep the same
    ``name`` (a coarse, structural proxy for "same meaning") and the same
    ``kind`` (a subject must never become a topic under the same id, etc).
    A real semantic change requires a brand-new id, never reusing an old
    one - this is the automatable half of that rule (a full meaning check
    is a human judgement call, but a renamed/reclassified node under an
    unchanged id is always at least suspicious).
    """
    diagnostics: list[Diagnostic] = []
    old_by_id = {view.id: view for view in old.flatten()}
    new_by_id = {view.id: view for view in new.flatten()}
    for node_id, old_view in old_by_id.items():
        new_view = new_by_id.get(node_id)
        if new_view is None:
            continue  # removed - not a "reused with different meaning" case
        if new_view.kind != old_view.kind:
            diagnostics.append(
                Diagnostic(
                    kind="taxonomy_id_kind_changed",
                    question_id="<taxonomy>",
                    field=node_id,
                    detail=f"{node_id!r} was a {old_view.kind!r}, is now a {new_view.kind!r}",
                )
            )
        elif new_view.node.name != old_view.node.name:
            diagnostics.append(
                Diagnostic(
                    kind="taxonomy_id_reused_with_different_meaning",
                    question_id="<taxonomy>",
                    field=node_id,
                    detail=f"{node_id!r} name changed from {old_view.node.name!r} to {new_view.node.name!r}",
                )
            )
    return diagnostics


def validate_context_not_used_as_primary_topic(annotation: QuestionAnnotation) -> list[Diagnostic]:
    """PROMPT Fase 5B section 10/25: a context tag and a primary/secondary
    topic must never both point at the same node in the same annotation -
    that would mean the same knowledge is simultaneously claimed to be
    "just context" and "actually assessed", a direct contradiction.
    """
    diagnostics: list[Diagnostic] = []
    overlap = set(annotation.context_tags) & (
        set(annotation.primary_topics) | set(annotation.secondary_topics)
    )
    if overlap:
        diagnostics.append(
            Diagnostic(
                kind="context_used_as_primary_topic",
                question_id=annotation.question_id,
                field="context_tags",
                detail=f"id(s) {sorted(overlap)} appear as both a context_tag and a primary/secondary topic",
            )
        )
    return diagnostics


def validate_primary_evidence_not_alternative_only(
    annotation: QuestionAnnotation, questions_dir: Path
) -> list[Diagnostic]:
    """PROMPT Fase 5B section 13/25: 'topico proveniente apenas de
    alternativa isolada'. When an annotation has a primary_topic, at least
    one of its own top-level evidence refs (or a ``required``-role
    concept's evidence) must be a text excerpt found in the question's own
    *statement* (never only inside "## Alternativas") - the conservative
    rule section 13 asks for: a topic whose only textual grounding is one
    isolated alternative is exactly the distractor-leakage risk this
    guards against. Visual evidence (asset-based) is exempt, since an
    alternative-only image is not the "single wrong-answer word" pattern
    this rule targets.
    """
    if not annotation.primary_topics:
        return []
    md_path = questions_dir / f"{annotation.question_id}.md"
    if not md_path.is_file():
        return []
    full_text = md_path.read_text(encoding="utf-8")
    statement_text = full_text.split("## Alternativas")[0]

    required_evidence = list(annotation.evidence)
    for concept in annotation.concepts:
        if concept.role == "required":
            required_evidence += concept.evidence_refs

    excerpts = [ref.text_excerpt for ref in required_evidence if ref.text_excerpt]
    if not excerpts:
        return []  # visual-only evidence is exempt

    if any(excerpt in statement_text for excerpt in excerpts):
        return []

    return [
        Diagnostic(
            kind="primary_topic_grounded_only_in_alternatives",
            question_id=annotation.question_id,
            field="evidence",
            detail=(
                "every text-based required evidence excerpt was found only inside "
                "'## Alternativas', never in the statement itself"
            ),
        )
    ]


def validate_search_terms_have_provenance(annotation: QuestionAnnotation) -> list[Diagnostic]:
    """PROMPT section 17/23: every search term must derive from the
    taxonomy/annotation itself (a topic/concept id, its own name/alias,
    or explicit evidence) - never an independently invented string with
    no traceable origin. This function only checks internal consistency
    (search_terms is never empty while every topic/concept list is also
    empty, for a non-unclassifiable annotation); the full alias
    cross-check against the taxonomy happens in the CLI, which has both
    documents loaded together.
    """
    if annotation.annotation_status == "unclassifiable":
        return []
    if annotation.search_terms and not (
        annotation.primary_topics or annotation.secondary_topics or annotation.concepts
    ):
        return [
            Diagnostic(
                kind="search_terms_without_origin",
                question_id=annotation.question_id,
                field="search_terms",
                detail="search_terms is non-empty but no topic/concept exists to derive it from",
            )
        ]
    return []
