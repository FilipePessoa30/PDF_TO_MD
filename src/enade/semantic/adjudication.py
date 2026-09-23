"""Human adjudication template (PROMPT Fase 5B section 21).

A template entry records this phase's own *proposed* decision alongside a
set of ``human_*`` fields that must stay ``None`` until a real human
reviewer fills them in - never this or any future automated pipeline.
Building the template is a pure, read-only rendering step (mirrors
``enade.semantic.review.build_review_markdown``'s own discipline); a
separate validator (below) is the only thing ever allowed to check
whether a *filled-in* template is internally consistent, and it never
promotes anything itself.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

from enade.semantic.annotation import QuestionAnnotation

HumanDecision = Literal["approve", "correct", "reject", "defer"]


class ProposedDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    taxonomy_version: str
    annotation_status: str
    primary_topics: list[str]
    secondary_topics: list[str]
    concepts: list[str]
    confidence: str


class HumanAdjudicationEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_id: str
    proposed_decision: ProposedDecision
    human_decision: HumanDecision | None = None
    human_primary_topics: list[str] | None = None
    human_secondary_topics: list[str] | None = None
    human_concepts: list[str] | None = None
    human_notes: str | None = None
    reviewer: str | None = None
    reviewed_at: str | None = None

    @model_validator(mode="after")
    def _human_decision_requires_reviewer_and_timestamp(self) -> HumanAdjudicationEntry:
        """PROMPT section 21/27: a partially-filled entry (a decision with
        no reviewer name, or vice versa) is worse than an untouched one -
        it looks reviewed without being auditable. Either all three
        (``human_decision``, ``reviewer``, ``reviewed_at``) are set, or
        none are.
        """
        triplet = (self.human_decision, self.reviewer, self.reviewed_at)
        if any(v is not None for v in triplet) and not all(v is not None for v in triplet):
            raise ValueError(
                "human_decision, reviewer, and reviewed_at must be filled in together "
                f"(got: human_decision={self.human_decision!r}, reviewer={self.reviewer!r}, "
                f"reviewed_at={self.reviewed_at!r})"
            )
        return self

    @model_validator(mode="after")
    def _reject_or_defer_never_carries_human_topics(self) -> HumanAdjudicationEntry:
        """A ``reject``/``defer`` decision is a statement that this
        question's classification is not (yet) settled - it must never
        also claim a human-approved topic list, which would contradict
        the decision itself.
        """
        if self.human_decision in ("reject", "defer") and (
            self.human_primary_topics or self.human_secondary_topics or self.human_concepts
        ):
            raise ValueError(
                f"human_decision={self.human_decision!r} must not carry "
                "human_primary_topics/human_secondary_topics/human_concepts"
            )
        return self


def build_adjudication_template(annotations: list[QuestionAnnotation]) -> list[dict]:
    entries = []
    for annotation in sorted(annotations, key=lambda a: a.question_id):
        entries.append(
            {
                "question_id": annotation.question_id,
                "proposed_decision": {
                    "taxonomy_version": annotation.taxonomy_version,
                    "annotation_status": annotation.annotation_status,
                    "primary_topics": annotation.primary_topics,
                    "secondary_topics": annotation.secondary_topics,
                    "concepts": [c.concept_id for c in annotation.concepts],
                    "confidence": annotation.confidence,
                },
                "human_decision": None,
                "human_primary_topics": None,
                "human_secondary_topics": None,
                "human_concepts": None,
                "human_notes": None,
                "reviewer": None,
                "reviewed_at": None,
            }
        )
    return entries


def is_template_untouched(entry: dict) -> bool:
    """True iff every ``human_*`` field is still ``None`` - the state
    every entry this pipeline produces must be in.
    """
    return all(
        entry.get(field) is None
        for field in (
            "human_decision",
            "human_primary_topics",
            "human_secondary_topics",
            "human_concepts",
            "human_notes",
            "reviewer",
            "reviewed_at",
        )
    )
