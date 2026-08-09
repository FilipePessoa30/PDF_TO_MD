"""Transform an ExtractedQuestion + answer data + rendered assets into a Question.

This is the only module that constructs the canonical Pydantic ``Question``
model (see docs/data-contract.md) from extraction internals - everywhere
else works with the intermediate ``ExtractedQuestion`` representation.
"""

from __future__ import annotations

from dataclasses import dataclass

from enade.extraction.answer_key import AnswerKeyEntry, AnswerKeyValueKind
from enade.extraction.answer_standard import AnswerStandardEntry
from enade.extraction.assembler import CodeSegment, ExtractedQuestion, FigureSegment, TextSegment
from enade.extraction.assets import RenderedAsset
from enade.extraction.boundaries import QuestionKind
from enade.extraction.validator import ValidationOutcome
from enade.models.asset import Asset
from enade.models.enums import (
    AnswerValidationStatus,
    CourseCode,
    ExtractionMethod,
    QuestionType,
)
from enade.models.provenance import AnswerStandardReference, SourceOccurrence
from enade.models.question import Alternative, Question

#: Readable (not raw filename-letter) course shorthand for id generation -
#: see docs/data-contract.md, "ID convention".
COURSE_ID_SHORTHAND: dict[CourseCode, str] = {
    CourseCode.CC_BACHARELADO: "cc-b",
    CourseCode.CC_LICENCIATURA: "cc-l",
    CourseCode.ENGENHARIA_COMPUTACAO: "ec",
    CourseCode.SISTEMAS_INFORMACAO: "si",
}


@dataclass(frozen=True)
class ExamStructure:
    """The official part boundaries for this specific booklet (see PROMPT section 4).

    Populated from the prova's own printed instructions (page 1), not
    hard-coded blindly - see ``enade.extraction.declared_structure``.
    """

    formacao_geral_discursivas: range
    formacao_geral_objetivas: range
    componente_especifico_discursivas: range
    componente_especifico_objetivas: range


def _section_for(kind: QuestionKind, number: int, structure: ExamStructure) -> str:
    if kind == QuestionKind.DISCURSIVE:
        if number in structure.formacao_geral_discursivas:
            return "formacao-geral-discursiva"
        if number in structure.componente_especifico_discursivas:
            return "componente-especifico-discursiva"
        return "discursiva-unclassified"
    if number in structure.formacao_geral_objetivas:
        return "formacao-geral-objetiva"
    if number in structure.componente_especifico_objetivas:
        return "componente-especifico-objetiva"
    return "objetiva-unclassified"


def render_statement_markdown(
    extracted: ExtractedQuestion, assets_by_region: dict[int, RenderedAsset]
) -> str:
    """Render statement segments to Markdown, resolving figure placeholders.

    Kept deliberately simple: paragraphs joined by blank lines, code
    segments as fenced blocks, figures as image references with a neutral
    (non-invented) alt description. No attempt is made to escape stray
    Markdown metacharacters in the source prose (PROMPT section 16 forbids
    altering the extracted text; the one exception already applied
    elsewhere - hyphen/line-break reconstruction - was deliberately *not*
    implemented, see docs/decisions.md).
    """
    parts: list[str] = []
    for segment in extracted.statement_segments:
        if isinstance(segment, TextSegment):
            parts.append(segment.text)
        elif isinstance(segment, CodeSegment):
            parts.append(f"```\n{segment.text}\n```")
        elif isinstance(segment, FigureSegment):
            asset = assets_by_region.get(segment.region_index)
            if asset is not None:
                parts.append(f"![Figura da questão]({asset.relative_path})")
    return "\n\n".join(parts)


def build_question(
    *,
    extracted: ExtractedQuestion,
    exam_year: int,
    course: CourseCode,
    exam_id: str,
    prova_source_path: str,
    prova_sha256: str,
    structure: ExamStructure,
    answer_key_entry: AnswerKeyEntry | None,
    answer_standard_entry: AnswerStandardEntry | None,
    answer_standard_source_path: str | None,
    answer_standard_sha256: str | None,
    gabarito_source_path: str,
    rendered_assets: list[RenderedAsset],
    assets_by_region: dict[int, RenderedAsset],
    validation: ValidationOutcome,
) -> Question:
    kind = extracted.kind
    number = extracted.number
    shorthand = COURSE_ID_SHORTHAND[course]
    suffix = "q" if kind == QuestionKind.OBJECTIVE else "d"
    question_id = f"enade-{exam_year}-{shorthand}-{suffix}{number:02d}"

    section = _section_for(kind, number, structure)
    question_type = (
        QuestionType.MULTIPLE_CHOICE if kind == QuestionKind.OBJECTIVE else QuestionType.DISCURSIVE
    )

    statement = render_statement_markdown(extracted, assets_by_region)
    alternatives = [Alternative(letter=a.letter, text=a.text) for a in extracted.alternatives]

    correct_answer: str | None = None
    official_answer_source: str | None = None
    answer_validation_status = AnswerValidationStatus.UNKNOWN
    answer_standard: AnswerStandardReference | None = None

    if kind == QuestionKind.OBJECTIVE:
        official_answer_source = gabarito_source_path
        if answer_key_entry is None:
            answer_validation_status = AnswerValidationStatus.UNKNOWN
        elif answer_key_entry.value_kind == AnswerKeyValueKind.LETTER:
            correct_answer = answer_key_entry.letter
            answer_validation_status = AnswerValidationStatus.VALIDATED
        elif answer_key_entry.value_kind == AnswerKeyValueKind.ANNULLED:
            answer_validation_status = AnswerValidationStatus.ANNULLED
        else:
            answer_validation_status = AnswerValidationStatus.CONFLICTING_SOURCES
    else:
        answer_validation_status = AnswerValidationStatus.NOT_APPLICABLE
        if (
            answer_standard_entry is not None
            and answer_standard_source_path
            and answer_standard_sha256
        ):
            answer_standard = AnswerStandardReference(
                source_path=answer_standard_source_path,
                pdf_sha256=answer_standard_sha256,
                pages=answer_standard_entry.pages,
                text=answer_standard_entry.text,
            )

    assets = [
        Asset(
            id=asset.asset_id,
            type=asset.asset_type,
            path=asset.relative_path,
            source_page=asset.source_page,
            extraction_method=asset.extraction_method,
            sha256=asset.sha256,
        )
        for asset in rendered_assets
    ]

    source_occurrence = SourceOccurrence(
        exam_id=exam_id,
        pdf_sha256=prova_sha256,
        source_path=prova_source_path,
        pages=list(range(extracted.start_page, extracted.end_page + 1)),
        question_number=number,
        section=section,
    )

    return Question(
        id=question_id,
        exam_year=exam_year,
        source_occurrences=[source_occurrence],
        applicable_courses=[course],
        section=section,
        question_number=number,
        question_type=question_type,
        statement=statement,
        alternatives=alternatives,
        correct_answer=correct_answer,
        official_answer_source=official_answer_source,
        answer_validation_status=answer_validation_status,
        answer_standard=answer_standard,
        assets=assets,
        extraction_method=ExtractionMethod.TEXT_LAYER,
        extraction_status=validation.status,
    )
