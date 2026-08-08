"""Shared controlled vocabularies for the ENADE data contracts.

These enums are intentionally small and only cover what Phase 0 needs to
express structurally. They are not a claim about the final taxonomy or
about every value a future extraction pipeline might need - new values
should be added deliberately, with a matching update to docs/decisions.md.
"""

from __future__ import annotations

from enum import StrEnum


class CourseCode(StrEnum):
    """Computing-area undergraduate courses/modalities present in the corpus.

    ``ALL_COMPUTING`` is a deliberate alias meaning "applies to every
    computing course in the given exam booklet" (e.g. Formacao Geral and
    Componente Especifico Comum in the unified 2011 booklet). It exists so
    a question does not need to enumerate every concrete course by hand.
    See docs/decisions.md (ADR on applicable_courses) for the constraint
    that ``ALL_COMPUTING`` may not be combined with other explicit codes.
    """

    CC_BACHARELADO = "ciencia-da-computacao-bacharelado"
    CC_LICENCIATURA = "ciencia-da-computacao-licenciatura"
    ENGENHARIA_COMPUTACAO = "engenharia-da-computacao"
    SISTEMAS_INFORMACAO = "sistemas-de-informacao"
    ALL_COMPUTING = "all-computing"


#: The four concrete (non-alias) computing courses known in this corpus.
CONCRETE_COURSE_CODES: tuple[CourseCode, ...] = (
    CourseCode.CC_BACHARELADO,
    CourseCode.CC_LICENCIATURA,
    CourseCode.ENGENHARIA_COMPUTACAO,
    CourseCode.SISTEMAS_INFORMACAO,
)


class DocType(StrEnum):
    """The three physical document roles found per exam sitting."""

    EXAM = "exam"  # "prova"
    ANSWER_KEY = "answer_key"  # "gabarito"
    ANSWER_STANDARD = "answer_standard"  # "padrao de resposta" (discursive rubric)


class QuestionType(StrEnum):
    MULTIPLE_CHOICE = "multiple_choice"
    DISCURSIVE = "discursive"
    PERCEPTION_SURVEY = "perception_survey"


class ExtractionMethod(StrEnum):
    MANUAL = "manual"
    TEXT_LAYER = "text_layer"
    OCR = "ocr"
    HYBRID = "hybrid"
    UNKNOWN = "unknown"
    PENDING = "pending"


class ExtractionStatus(StrEnum):
    PENDING = "pending"
    EXTRACTED = "extracted"
    NEEDS_REVIEW = "needs_review"
    VERIFIED = "verified"


class AnswerValidationStatus(StrEnum):
    PENDING = "pending"
    VALIDATED = "validated"
    ANNULLED = "annulled"
    CONFLICTING_SOURCES = "conflicting_sources"
    NOT_APPLICABLE = "not_applicable"
    UNKNOWN = "unknown"


class TaxonomyReviewStatus(StrEnum):
    PENDING = "pending"
    DRAFT = "draft"
    REVIEWED = "reviewed"


class DifficultyLevel(StrEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class AssetType(StrEnum):
    IMAGE = "image"
    DIAGRAM = "diagram"
    GRAPH = "graph"
    TABLE = "table"
    EQUATION = "equation"
    PAGE_CROP = "page_crop"


class AssetExtractionMethod(StrEnum):
    MANUAL = "manual"
    RASTER_CROP = "raster_crop"
    VECTOR_EXPORT = "vector_export"
    OCR = "ocr"
    UNKNOWN = "unknown"
    PENDING = "pending"


class MaterialType(StrEnum):
    ARTICLE = "article"
    VIDEO = "video"
    BOOK = "book"
    COURSE = "course"
    DOCUMENTATION = "documentation"
    EXERCISE_SET = "exercise_set"
    OTHER = "other"


class VerificationStatus(StrEnum):
    PENDING = "pending"
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    BROKEN = "broken"


class TaxonomyStatus(StrEnum):
    """Maturity of a taxonomy document. Phase 0 only ever produces ``demo``."""

    DEMO = "demo"
    DRAFT = "draft"
    REVIEWED = "reviewed"
    DEFINITIVE = "definitive"
