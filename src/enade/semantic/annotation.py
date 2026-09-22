"""Question-level semantic annotation contract (PROMPT Fase 5A sections
11-19). Built entirely on top of the already-published, frozen corpus
(``data/questions``) and the taxonomy (``enade.models.taxonomy``) -
never on the extraction pipeline itself, never modifying either.

Every annotation is a claim that must be independently re-verifiable:
``SemanticEvidenceRef`` records exactly which real, published fragment
justifies a topic/concept, and ``validate_evidence_integrity`` re-checks
that fragment against the actual file on disk - an annotation is never
trusted merely because it once passed schema validation.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

SHA256_PATTERN = r"^[0-9a-f]{64}$"
QUESTION_ID_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
#: PROMPT section 19.
AnnotationStatus = Literal["proposed", "needs_review", "reviewed", "rejected", "unclassifiable"]
#: A separate, narrower field from ``annotation_status`` (PROMPT section
#: 11 lists both): this one tracks only the human-in-the-loop gate - it
#: starts and stays "pending" for every annotation this phase produces,
#: since a piloted annotation is never allowed to claim human review
#: happened when it did not (section 19: "Nenhuma anotacao... pode
#: receber reviewed sem revisao humana real").
ReviewStatus = Literal["pending", "reviewed", "needs_correction", "rejected"]
ConfidenceLevel = Literal["high", "medium", "low"]
ConceptRole = Literal["required", "supporting", "contextual"]
Component = Literal["formacao_geral", "componente_especifico"]
#: PROMPT section 18 - a small, explicit vocabulary; never confused with
#: difficulty (a hard question can still be pure "recall").
CognitiveSkill = Literal[
    "recall",
    "interpret",
    "apply",
    "calculate",
    "analyze",
    "compare",
    "evaluate",
    "design",
    "justify",
]
#: PROMPT section 15 - "padrao de resposta, quando permitido": declared
#: for schema extensibility (a future, explicitly-separate derived-layer
#: annotation model), but see ``_forbid_answer_standard_evidence`` below -
#: never accepted by *this* (primary, student-visible-only) annotation
#: model, in any of its own evidence lists, unconditionally.
SourceKind = Literal[
    "statement",
    "alternative",
    "content_block",
    "table",
    "formula",
    "asset",
    "caption",
    "answer_standard",
]


class SemanticEvidenceRef(BaseModel):
    """One stable, independently-re-verifiable pointer into the
    *published* corpus (PROMPT Fase 5A section 15) - never a raw list
    index, never a reference into a ledger that is not itself persisted.
    """

    model_config = ConfigDict(extra="forbid")

    source_kind: SourceKind
    #: A stable, human-readable locator - e.g. "statement",
    #: "alternative:B", "content_block:2", "asset:table-01" - never a
    #: bare integer index with no semantic meaning.
    source_locator: str = Field(..., min_length=1)
    #: sha256 of the *whole* published question Markdown file this
    #: evidence was read from - re-checked by
    #: ``validate_evidence_integrity`` against the real file on disk, so
    #: any edit to that question (even unrelated) is detected rather than
    #: silently trusted forever.
    source_sha256: str = Field(..., pattern=SHA256_PATTERN)
    text_excerpt: str | None = Field(default=None, max_length=300)
    excerpt_sha256: str | None = Field(default=None, pattern=SHA256_PATTERN)
    asset_path: str | None = None
    #: Reused verbatim from the asset's own already-published
    #: ``Asset.sha256`` (PROMPT section 15: "reutilize IDs estaveis ja
    #: publicados") - never independently recomputed here.
    asset_sha256: str | None = Field(default=None, pattern=SHA256_PATTERN)
    page: int | None = Field(default=None, ge=1)
    bbox: tuple[float, float, float, float] | None = None

    @model_validator(mode="after")
    def _asset_evidence_requires_both_path_and_hash(self) -> SemanticEvidenceRef:
        # Runs first: a half-specified asset ref ("path" but no "hash") is
        # a more specific, more actionable defect than "no evidence at
        # all" - never masked behind the generic message below.
        if (self.asset_path is None) != (self.asset_sha256 is None):
            raise ValueError("asset_path and asset_sha256 must both be set, or both be unset")
        return self

    @model_validator(mode="after")
    def _text_or_visual_evidence_required(self) -> SemanticEvidenceRef:
        has_text = bool(self.text_excerpt and self.text_excerpt.strip())
        has_visual = self.asset_path is not None and self.asset_sha256 is not None
        if not has_text and not has_visual:
            raise ValueError(
                "evidence must have either a non-empty text_excerpt or an "
                "asset_path+asset_sha256 pair - never neither"
            )
        if has_text and not self.excerpt_sha256:
            raise ValueError("text_excerpt requires excerpt_sha256 (integrity check)")
        return self

    @model_validator(mode="after")
    def _excerpt_hash_matches_excerpt(self) -> SemanticEvidenceRef:
        if self.text_excerpt is not None and self.excerpt_sha256 is not None:
            actual = hashlib.sha256(self.text_excerpt.encode("utf-8")).hexdigest()
            if actual != self.excerpt_sha256:
                raise ValueError(
                    f"excerpt_sha256 {self.excerpt_sha256!r} does not match the recorded "
                    f"text_excerpt (recomputed: {actual!r})"
                )
        return self


class ConceptAssociation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    concept_id: str = Field(..., min_length=1)
    role: ConceptRole
    evidence_refs: list[SemanticEvidenceRef] = Field(..., min_length=1)
    confidence: ConfidenceLevel


class QuestionAnnotation(BaseModel):
    """PROMPT Fase 5A section 11. Deliberately independent of
    ``enade.models.question.Question`` - this is a *separate* artifact
    (``data/semantic/question-annotations-5a.json``), never written into
    a question's own Markdown (PROMPT section 25: "Nao edite os Markdown
    das questoes para adicionar tags").
    """

    model_config = ConfigDict(extra="forbid")

    question_id: str = Field(..., min_length=1)
    taxonomy_version: str = Field(..., min_length=1)
    #: sha256 of the published question Markdown at annotation time -
    #: re-checked the same way evidence sources are (PROMPT section 23:
    #: "source hash stale").
    source_hash: str = Field(..., pattern=SHA256_PATTERN)
    component: Component
    primary_topics: list[str] = Field(default_factory=list)
    secondary_topics: list[str] = Field(default_factory=list)
    concepts: list[ConceptAssociation] = Field(default_factory=list)
    context_tags: list[str] = Field(default_factory=list)
    cognitive_skills: list[CognitiveSkill] = Field(default_factory=list)
    search_terms: list[str] = Field(default_factory=list)
    evidence: list[SemanticEvidenceRef] = Field(default_factory=list)
    annotation_method: str = Field(..., min_length=1)
    annotation_status: AnnotationStatus
    confidence: ConfidenceLevel
    review_status: ReviewStatus = "pending"
    notes: str | None = None

    @model_validator(mode="after")
    def _validate_id_shape(self) -> QuestionAnnotation:
        if not QUESTION_ID_PATTERN.match(self.question_id):
            raise ValueError(f"question_id {self.question_id!r} must be lowercase kebab-case")
        return self

    @model_validator(mode="after")
    def _primary_topic_or_unclassifiable(self) -> QuestionAnnotation:
        """PROMPT section 12: at least one primary topic, or an explicit
        ``unclassifiable`` status - never both, and never neither.
        """
        if self.annotation_status == "unclassifiable":
            if self.primary_topics or self.secondary_topics or self.concepts:
                raise ValueError(
                    "annotation_status='unclassifiable' must not carry primary_topics, "
                    "secondary_topics, or concepts - being unclassifiable is itself the claim"
                )
        elif not self.primary_topics:
            raise ValueError(
                "every annotation needs at least one primary_topic, or an explicit "
                "annotation_status='unclassifiable'"
            )
        return self

    @model_validator(mode="after")
    def _no_topic_is_both_primary_and_secondary(self) -> QuestionAnnotation:
        overlap = set(self.primary_topics) & set(self.secondary_topics)
        if overlap:
            raise ValueError(f"topic(s) listed as both primary and secondary: {sorted(overlap)}")
        return self

    @model_validator(mode="after")
    def _reviewed_requires_a_real_reviewer_note(self) -> QuestionAnnotation:
        """PROMPT section 19: nothing this pipeline produces may claim
        ``review_status='reviewed'`` - that value exists in the schema
        only for a *future*, genuinely human-driven promotion (e.g. via
        the review packet), never set by the annotation-authoring code
        path itself. Enforced structurally here: reaching "reviewed"
        requires ``notes`` to name a human reviewer explicitly - the
        piloting code in this phase never does that, so it can never
        accidentally reach this state.
        """
        if self.review_status == "reviewed" and not (self.notes and "reviewer:" in self.notes):
            raise ValueError(
                "review_status='reviewed' requires notes to record 'reviewer: <name>' - "
                "never set automatically"
            )
        return self

    @model_validator(mode="after")
    def _forbid_answer_standard_evidence(self) -> QuestionAnnotation:
        """PROMPT section 16: the primary annotation pipeline must never
        use the answer key or padrao de resposta to justify a topic - a
        future, explicitly separate derived-layer annotation could use
        ``source_kind='answer_standard'`` evidence, but this model (the
        one and only one Fase 5A produces) never accepts it, in either
        its own top-level ``evidence`` or any concept's own
        ``evidence_refs``.
        """
        all_evidence = list(self.evidence) + [
            ref for concept in self.concepts for ref in concept.evidence_refs
        ]
        if any(ref.source_kind == "answer_standard" for ref in all_evidence):
            raise ValueError(
                "evidence with source_kind='answer_standard' is never accepted by the "
                "primary annotation pipeline (PROMPT section 16 anti-leakage)"
            )
        return self


def source_excerpt_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def source_file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
