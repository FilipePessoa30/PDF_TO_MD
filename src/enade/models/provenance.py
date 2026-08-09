"""Provenance contract: every derived artifact must trace back to a PDF+page.

This model is shared by the source manifest (one record per physical PDF)
and, via :class:`SourceOccurrence`, by the canonical Question contract
(one record per appearance of a question inside a specific PDF/page).
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

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
    """

    model_config = ConfigDict(extra="forbid")

    source_path: str = Field(
        ..., description="path relative to the repo root, e.g. '2021/b3_padrao.pdf'"
    )
    pdf_sha256: str = Field(..., pattern=SHA256_PATTERN)
    pages: list[int] = Field(..., min_length=1)
    text: str = Field(..., min_length=1, description="verbatim official grading rubric text")

    @field_validator("pages")
    @classmethod
    def _pages_positive(cls, v: list[int]) -> list[int]:
        if any(p < 1 for p in v):
            raise ValueError("page numbers must be >= 1")
        return v
