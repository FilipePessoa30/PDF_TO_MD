"""Provenance contract: every derived artifact must trace back to a PDF+page.

This model is shared by the source manifest (one record per physical PDF)
and, via :class:`SourceOccurrence`, by the canonical Question contract
(one record per appearance of a question inside a specific PDF/page).
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from enade.models.asset import Asset
from enade.models.enums import CourseCode, DocType

SHA256_PATTERN = r"^[0-9a-f]{64}$"
COMMIT_SHA_PATTERN = r"^[0-9a-f]{7,40}$"


class SourceRepository(BaseModel):
    """Identifies the exact upstream corpus snapshot used, for reproducibility."""

    model_config = ConfigDict(extra="forbid")

    repository_url: str = Field(..., description="e.g. https://github.com/geacc/enade")
    ref: str = Field(..., description="branch or tag name at fetch time, e.g. 'master'")
    commit_sha: str = Field(..., pattern=COMMIT_SHA_PATTERN)


class PdfProvenance(BaseModel):
    """Provenance of a single raw PDF file within the source repository."""

    model_config = ConfigDict(extra="forbid")

    repository: SourceRepository
    source_path: str = Field(
        ..., description="path relative to the repo root, e.g. '2021/b1_prova.pdf'"
    )
    sha256: str = Field(..., pattern=SHA256_PATTERN)
    file_size_bytes: int = Field(..., ge=0)
    page_count: int = Field(..., ge=0)
    exam_year: int = Field(..., ge=1990, le=2100)
    document_type: DocType
    course_codes: list[CourseCode] = Field(default_factory=list)
    retrieved_at: datetime

    @field_validator("source_path")
    @classmethod
    def _normalize_slashes(cls, v: str) -> str:
        return v.replace("\\", "/")


class SourceOccurrence(BaseModel):
    """One concrete appearance of a canonical question inside a source PDF.

    A canonical question may have several of these (see docs/data-contract.md
    - "source occurrences and duplicates"): the same question can be printed
    verbatim in more than one exam booklet/year.
    """

    model_config = ConfigDict(extra="forbid")

    exam_id: str = Field(..., description="manifest exam bundle id, e.g. 'enade-2021-cc-b'")
    pdf_sha256: str = Field(..., pattern=SHA256_PATTERN)
    source_path: str = Field(..., description="path relative to the repo root")
    pages: list[int] = Field(..., min_length=1)
    question_number: int = Field(..., ge=1)
    section: str = Field(..., min_length=1)

    @field_validator("pages")
    @classmethod
    def _pages_positive(cls, v: list[int]) -> list[int]:
        if any(p < 1 for p in v):
            raise ValueError("page numbers must be >= 1")
        return v


class AnswerStandardReference(BaseModel):
    """The official grading rubric ("padrao de resposta") for a discursive question.

    Added in Phase 1A after encountering the real 2021 corpus: the answer
    standard PDF (e.g. ``2021/b3_padrao.pdf``) contains the actual grading
    criteria text for each discursive question, distinct from both the
    question's own source (the "prova") and an objective question's
    ``correct_answer`` (which comes from the "gabarito"). See
    docs/decisions.md, ADR "answer_standard for discursive questions", for
    the full PROBLEMA/EXEMPLO/LIMITACAO/ALTERACAO/TESTE rationale.

    This is deliberately a *separate* field from ``official_answer_source``
    (which remains a lightweight pointer usable by objective questions) so
    that existing data is unaffected: this field is optional and additive.

    ``assets`` (Phase 1C, PROMPT section 9) covers visual elements that
    exist *only* in the answer standard itself - e.g. D4's worked-out
    circuit diagrams, introduced by "conforme abaixo" - as opposed to a
    reprint of the question's own figure (which the padrao PDF also
    contains for some questions, but that content is already captured via
    the question's own ``Question.assets`` from the prova and must never
    be duplicated here). Kept in a field of its own, never merged into
    ``Question.assets``, so a future consumer can enforce "never shown to
    the student before their attempt" by field alone - see
    docs/decisions.md, "Phase 1C" ADR.

    ``text`` was originally required non-empty unconditionally (PROMPT
    Phase 1A) - relaxed in Phase 3U to allow an empty string only when
    ``assets`` is non-empty (see ``_validate_text_or_assets_present``):
    2008-b's own D59 (page 3 of ``b3_padrao.pdf``) has a rubric that is
    genuinely, entirely visual - zero rubric text of any kind between its
    own "Questao 59"/"Questao 60" markers, one real embedded diagram image
    and nothing else. The three documentary modes this enables:
    ``text_only`` (non-empty text, ``assets`` empty or not - unchanged,
    every pre-Phase-3U answer standard), ``visual_only`` (``text=""``,
    ``assets`` non-empty - D59's own new shape), ``mixed`` (non-empty text
    AND non-empty assets - already the existing shape for D3/D4/D40, whose
    own worked examples/diagrams sit alongside real rubric text). The one
    state this validator still forbids, in every mode, is both empty at
    once (``text=""`` and ``assets=[]``) - there is never a "no content at
    all" answer standard; a discursive with neither is represented by
    ``Question.answer_standard is None`` instead (see
    ``answer_standard.py``'s own ``flush()``, which never creates an entry
    for that shape).
    """

    model_config = ConfigDict(extra="forbid")

    source_path: str = Field(
        ..., description="path relative to the repo root, e.g. '2021/b3_padrao.pdf'"
    )
    pdf_sha256: str = Field(..., pattern=SHA256_PATTERN)
    pages: list[int] = Field(..., min_length=1)
    text: str = Field(
        ...,
        description="verbatim official grading rubric text, or '' when the rubric is visual-only",
    )
    assets: list[Asset] = Field(default_factory=list)

    @field_validator("pages")
    @classmethod
    def _pages_positive(cls, v: list[int]) -> list[int]:
        if any(p < 1 for p in v):
            raise ValueError("page numbers must be >= 1")
        return v

    @model_validator(mode="after")
    def _validate_asset_ids_unique(self) -> AnswerStandardReference:
        ids = [a.id for a in self.assets]
        if len(set(ids)) != len(ids):
            raise ValueError("answer_standard.assets must not repeat an id")
        return self

    @model_validator(mode="after")
    def _validate_text_or_assets_present(self) -> AnswerStandardReference:
        if not self.text.strip() and not self.assets:
            raise ValueError(
                "answer_standard must have non-empty text, at least one asset, or both - "
                "never both empty (a discursive with neither should have answer_standard=None)"
            )
        return self
