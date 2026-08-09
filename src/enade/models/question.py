"""The canonical Question contract every future extraction must satisfy.

This is deliberately a contract, not extracted data: Phase 0 defines the
shape and its invariants, and exercises them against small fixtures
(tests/fixtures/questions/). No real ENADE question text is invented or
extracted here (see PROMPT sections 9 and 20).

Design notes (see docs/data-contract.md and docs/decisions.md for the
full rationale):

- ``applicable_courses`` is a list, not a single course, because the 2011
  unified "COMPUTACAO" booklet has questions shared by multiple courses
  (see docs/corpus.md - "2011 special case").
- ``source_occurrences`` is a list because the same question can appear in
  more than one exam booklet/year; Phase 0 does not attempt semantic
  deduplication (PROMPT section 10), it only provides the architecture.
- Every "we don't know yet" field has an explicit pending/unknown state
  rather than a fabricated value.
"""

from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, Field, model_validator

from enade.models.asset import Asset
from enade.models.enums import (
    AnswerValidationStatus,
    CourseCode,
    DifficultyLevel,
    ExtractionMethod,
    ExtractionStatus,
    QuestionType,
    TaxonomyReviewStatus,
)
from enade.models.misconception import AlternativeDiagnostic
from enade.models.provenance import AnswerStandardReference, SourceOccurrence

QUESTION_ID_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SECTION_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
ALTERNATIVE_LETTER_PATTERN = re.compile(r"^[A-E]$")


class Alternative(BaseModel):
    model_config = ConfigDict(extra="forbid")

    letter: str = Field(..., pattern=r"^[A-E]$")
    text: str = Field(..., min_length=1)


class Question(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # --- identity -----------------------------------------------------
    id: str = Field(..., description="e.g. 'enade-2021-cc-b-q12', see docs/data-contract.md")
    exam_year: int = Field(..., ge=1990, le=2100)
    source_occurrences: list[SourceOccurrence] = Field(..., min_length=1)

    # --- classification within the exam --------------------------------
    applicable_courses: list[CourseCode] = Field(..., min_length=1)
    section: str = Field(..., min_length=1)
    question_number: int = Field(..., ge=1)
    question_type: QuestionType

    # --- content --------------------------------------------------------
    statement: str = Field(..., min_length=1)
    alternatives: list[Alternative] = Field(default_factory=list)
    correct_answer: str | None = Field(default=None, pattern=r"^[A-E]$")
    official_answer_source: str | None = Field(
        default=None,
        description="reference (e.g. exam_id/path) to the gabarito this was validated against",
    )
    answer_validation_status: AnswerValidationStatus = AnswerValidationStatus.PENDING
    answer_standard: AnswerStandardReference | None = Field(
        default=None,
        description="official grading rubric for discursive questions (see docs/decisions.md)",
    )

    assets: list[Asset] = Field(default_factory=list)

    # --- taxonomy (ids referencing data/taxonomy/*.yaml, may be empty) --
    subjects: list[str] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    concepts: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    competencies: list[str] = Field(default_factory=list)
    prerequisites: list[str] = Field(default_factory=list)
    difficulty: DifficultyLevel | None = None

    # --- error diagnosis, keyed by alternative letter --------------------
    alternative_diagnostics: dict[str, AlternativeDiagnostic] = Field(default_factory=dict)

    # --- pipeline / audit state ------------------------------------------
    extraction_method: ExtractionMethod = ExtractionMethod.PENDING
    ocr_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    extraction_status: ExtractionStatus = ExtractionStatus.PENDING
    taxonomy_review_status: TaxonomyReviewStatus = TaxonomyReviewStatus.PENDING

    # ---------------------------------------------------------------- validators
    @model_validator(mode="after")
    def _validate_id_and_section_shape(self) -> Question:
        if not QUESTION_ID_PATTERN.match(self.id):
            raise ValueError(f"id {self.id!r} must be lowercase kebab-case")
        if not SECTION_PATTERN.match(self.section):
            raise ValueError(f"section {self.section!r} must be lowercase kebab-case")
        return self

    @model_validator(mode="after")
    def _validate_applicable_courses(self) -> Question:
        if CourseCode.ALL_COMPUTING in self.applicable_courses and len(self.applicable_courses) > 1:
            raise ValueError(
                "applicable_courses: 'all-computing' is an alias for every computing course "
                "and must not be combined with other explicit course codes"
            )
        if len(set(self.applicable_courses)) != len(self.applicable_courses):
            raise ValueError("applicable_courses must not contain duplicates")
        return self

    @model_validator(mode="after")
    def _validate_alternatives(self) -> Question:
        letters = [a.letter for a in self.alternatives]
        if len(set(letters)) != len(letters):
            raise ValueError("alternatives must not repeat a letter")
        if self.question_type == QuestionType.MULTIPLE_CHOICE:
            if len(self.alternatives) < 2:
                raise ValueError("multiple_choice questions need at least 2 alternatives")
        else:
            if self.alternatives:
                raise ValueError(f"{self.question_type.value} questions must not have alternatives")
        return self

    @model_validator(mode="after")
    def _validate_correct_answer(self) -> Question:
        letters = {a.letter for a in self.alternatives}
        if self.question_type != QuestionType.MULTIPLE_CHOICE and self.correct_answer is not None:
            raise ValueError(f"{self.question_type.value} questions must not set correct_answer")
        if self.correct_answer is not None and self.correct_answer not in letters:
            raise ValueError(
                f"correct_answer {self.correct_answer!r} is not one of the declared alternatives"
            )
        if (
            self.answer_validation_status == AnswerValidationStatus.VALIDATED
            and self.correct_answer is None
        ):
            raise ValueError("answer_validation_status='validated' requires a correct_answer")
        return self

    @model_validator(mode="after")
    def _validate_ocr_confidence(self) -> Question:
        if self.ocr_confidence is not None and self.extraction_method not in (
            ExtractionMethod.OCR,
            ExtractionMethod.HYBRID,
        ):
            raise ValueError(
                "ocr_confidence may only be set when extraction_method is 'ocr' or 'hybrid'"
            )
        return self

    @model_validator(mode="after")
    def _validate_alternative_diagnostics(self) -> Question:
        letters = {a.letter for a in self.alternatives}
        for letter in self.alternative_diagnostics:
            if not ALTERNATIVE_LETTER_PATTERN.match(letter):
                raise ValueError(f"alternative_diagnostics key {letter!r} must be a letter A-E")
            if letter not in letters:
                raise ValueError(
                    f"alternative_diagnostics references undeclared alternative {letter!r}"
                )
            if letter == self.correct_answer:
                raise ValueError(
                    f"alternative_diagnostics must not target the correct answer ({letter!r})"
                )
        return self

    @model_validator(mode="after")
    def _validate_asset_ids_unique(self) -> Question:
        ids = [a.id for a in self.assets]
        if len(set(ids)) != len(ids):
            raise ValueError("assets must not repeat an id within a question")
        return self
