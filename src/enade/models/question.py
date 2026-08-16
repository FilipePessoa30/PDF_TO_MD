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
from enade.models.content_block import AssetBlock, ContentBlock, TableBlock
from enade.models.enums import (
    AnswerValidationStatus,
    AutomaticValidationStatus,
    CourseCode,
    DifficultyLevel,
    ExtractionMethod,
    ExtractionStatus,
    QuestionType,
    TableValidationStatus,
    TaxonomyReviewStatus,
    VisualValidationStatus,
)
from enade.models.misconception import AlternativeDiagnostic
from enade.models.provenance import AnswerStandardReference, SourceOccurrence

QUESTION_ID_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SECTION_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
ALTERNATIVE_LETTER_PATTERN = re.compile(r"^[A-E]$")

#: Semantic version of the *shape* of this contract (not the pipeline that
#: produces data satisfying it, see ``enade.__version__``/`pipeline_version`
#: in gold.py) - bumped deliberately whenever a field is added, removed, or
#: changes meaning. Phase 1C added `content_blocks` and
#: `AnswerStandardReference.assets`, both additive/backward-compatible
#: (MINOR bump) - see docs/decisions.md, "Phase 1C" ADR 12/15.
DATA_CONTRACT_VERSION = "1.1.0"


class Alternative(BaseModel):
    model_config = ConfigDict(extra="forbid")

    letter: str = Field(..., pattern=r"^[A-E]$")
    #: Non-empty for every alternative that has any text at all - but see
    #: the ``_text_or_asset_required`` validator below for the one
    #: documented exception (an alternative whose printed content is
    #: *only* an image, with literally nothing else on its own marker
    #: line - not even trailing punctuation).
    text: str
    #: Set when this alternative's own content is (fully or partly) a
    #: small raster/vector formula image rather than text (PROMPT Phase 2E
    #: section 10) - e.g. 2011 Q14, where every alternative is only a
    #: boolean-algebra formula image with no other text at all (``text``
    #: then holds just the source's own trailing punctuation, never an
    #: invented transcription of the formula) - or 2008-b's own Q38/Q55
    #: (PROMPT Phase 3A), whose equivalent alternatives leave behind no
    #: punctuation either, hence ``text`` may be "" there (see
    #: ``_text_or_asset_required``, never invented to satisfy a length
    #: check). ``None`` for the overwhelming majority of alternatives,
    #: which are real text.
    asset: Asset | None = None
    #: Ordered text/asset segments, when this alternative's own content
    #: interleaves real text with one or more small inline formula images
    #: (PROMPT Phase 2F section 7) - e.g. 2011 Q23's own alternatives D/E,
    #: each "<text> <formula image> <text>". Reuses the same ``ContentBlock``
    #: union already defined for ``Question.content_blocks`` (only
    #: ``ParagraphBlock``/``AssetBlock`` variants are ever produced here -
    #: no new taxonomy). Distinct from ``asset`` (Phase 2E's own mechanism,
    #: for an alternative that is *only* an image with no text at all -
    #: Q14's own shape, left untouched by this field). ``None`` for every
    #: alternative that is either plain text or a single whole-alternative
    #: asset - ``text`` remains a flattened, human-readable projection of
    #: the same content even when ``content_blocks`` is set (full-text
    #: search/back-compat, the same relationship ``Question.statement``
    #: already has to ``Question.content_blocks``).
    content_blocks: list[ContentBlock] | None = None

    @model_validator(mode="after")
    def _text_or_asset_required(self) -> Alternative:
        """Blank/whitespace-only ``text`` is only ever legitimate when a
        real asset stands in for the content - either ``asset`` (PROMPT
        Phase 3A - 2008-b's Q38/Q55, whose printed alternatives are a bare
        letter marker with *nothing* else on the line, not even 2011
        Q14's own trailing punctuation) or an ``AssetBlock`` inside
        ``content_blocks`` (the interleaved shape, PROMPT Phase 2F). An
        alternative with neither is not a documented shape - a genuine
        extraction gap, never silently accepted here.
        """
        has_asset_content = self.asset is not None or (
            self.content_blocks is not None
            and any(block.type == "asset" for block in self.content_blocks)
        )
        if not self.text.strip() and not has_asset_content:
            raise ValueError(
                f"alternative {self.letter}: text is empty and no asset is set - "
                "an alternative must have real text, an asset, or both"
            )
        return self


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
    #: Ordered, mixed-content representation of the statement body -
    #: paragraph/code/table/asset blocks in reading order (see
    #: content_block.py and docs/decisions.md ADR 12). Optional and
    #: additive: ``None`` for any question whose body is adequately
    #: represented by ``statement`` + inline asset references alone (the
    #: large majority of this corpus); populated only when a question's
    #: real content mixes prose with a table and/or a code listing whose
    #: position in the reading order matters (e.g. D3, D5).
    content_blocks: list[ContentBlock] | None = None
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
    #: Result of the pipeline's own mechanical checks - necessary but not
    #: sufficient for ``verified`` (see docs/decisions.md, Phase 1B).
    automatic_validation: AutomaticValidationStatus = AutomaticValidationStatus.PENDING
    #: Result of an actual human comparison against the rendered PDF page(s).
    #: Defaults to "not performed" - a pipeline run alone must never claim
    #: this passed (PROMPT section 12).
    visual_validation: VisualValidationStatus = VisualValidationStatus.NOT_PERFORMED
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

    @model_validator(mode="after")
    def _validate_content_blocks(self) -> Question:
        asset_ids = {a.id for a in self.assets}

        if self.content_blocks is not None:
            has_visual_fallback = any(isinstance(b, AssetBlock) for b in self.content_blocks)
            for block in self.content_blocks:
                if isinstance(block, AssetBlock) and block.asset_id not in asset_ids:
                    raise ValueError(
                        f"content_blocks references undeclared asset id {block.asset_id!r}"
                    )
                if (
                    isinstance(block, TableBlock)
                    and block.validation_status != TableValidationStatus.VERIFIED
                    and not has_visual_fallback
                ):
                    # PROMPT section 5.2: a table that was not confirmed
                    # cell-by-cell must never be presented without a visual
                    # fallback the reader can fall back on - this is not
                    # optional, regardless of which question it is.
                    raise ValueError(
                        "content_blocks has a non-verified TableBlock but no AssetBlock "
                        "visual fallback - an unvalidated table must never stand alone"
                    )

        # An alternative's own content_blocks (PROMPT Phase 2F section 7,
        # e.g. 2011 Q23's own D/E) has no assets list of its own - any
        # AssetBlock it carries must reference this Question's own assets,
        # the same single source of truth every other asset reference uses.
        for alt in self.alternatives:
            if alt.content_blocks is None:
                continue
            for block in alt.content_blocks:
                if isinstance(block, AssetBlock) and block.asset_id not in asset_ids:
                    raise ValueError(
                        f"alternative {alt.letter}'s content_blocks references undeclared "
                        f"asset id {block.asset_id!r}"
                    )
        return self

    @model_validator(mode="after")
    def _validate_verified_requires_both_validations(self) -> Question:
        # Formalizes PROMPT section 13: "verified" means the statement,
        # alternatives, assets etc. were actually confirmed to match the
        # official PDF - a claim only a human visual check can support.
        # Passing every mechanical check (automatic_validation) is
        # necessary but never sufficient on its own (section 12/14: no
        # mass-promotion, no `visual_validation=passed` without a real
        # inspection).
        if self.extraction_status == ExtractionStatus.VERIFIED:
            if self.automatic_validation != AutomaticValidationStatus.PASSED:
                raise ValueError(
                    "extraction_status='verified' requires automatic_validation='passed'"
                )
            if self.visual_validation != VisualValidationStatus.PASSED:
                raise ValueError("extraction_status='verified' requires visual_validation='passed'")
        return self
