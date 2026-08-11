"""Transform an ExtractedQuestion + answer data + rendered assets into a Question.

This is the only module that constructs the canonical Pydantic ``Question``
model (see docs/data-contract.md) from extraction internals - everywhere
else works with the intermediate ``ExtractedQuestion`` representation.
"""

from __future__ import annotations

from dataclasses import dataclass

from enade.extraction.answer_key import AnswerKeyEntry, AnswerKeyValueKind
from enade.extraction.answer_standard import AnswerStandardEntry
from enade.extraction.assembler import (
    CodeSegment,
    ExtractedQuestion,
    FigureSegment,
    TableSegment,
    TextSegment,
)
from enade.extraction.assets import RenderedAsset
from enade.extraction.boundaries import QuestionKind
from enade.extraction.tables import render_table_markdown
from enade.extraction.validator import ValidationOutcome
from enade.models.asset import Asset
from enade.models.content_block import (
    AssetBlock,
    CodeBlock,
    ContentBlock,
    ParagraphBlock,
    TableBlock,
)
from enade.models.enums import (
    AnswerValidationStatus,
    CourseCode,
    ExtractionMethod,
    ExtractionStatus,
    QuestionType,
    TableValidationStatus,
    VisualValidationStatus,
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
    extracted: ExtractedQuestion,
    assets_by_region: dict[int, RenderedAsset],
    assets_by_table: dict[int, RenderedAsset] | None = None,
) -> str:
    """Render statement segments to Markdown, resolving figure placeholders.

    Kept deliberately simple: paragraphs joined by blank lines, code
    segments as fenced blocks, figures as image references with a neutral
    (non-invented) alt description. No attempt is made to escape stray
    Markdown metacharacters in the source prose (PROMPT section 16 forbids
    altering the extracted text; the one exception already applied
    elsewhere - hyphen/line-break reconstruction - was deliberately *not*
    implemented, see docs/decisions.md).

    A table segment renders as a GFM Markdown table *plus* its mandatory
    visual-fallback crop, immediately after it (PROMPT Phase 1C section
    5.2: D3-class content must never leave the reader with only a
    structured guess and no way to check it against the original) - both
    travel together in the same rendered chunk so no later reordering can
    separate a table from its own fallback image.
    """
    assets_by_table = assets_by_table or {}
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
        elif isinstance(segment, TableSegment):
            table = extracted.tables[segment.table_index]
            chunk = render_table_markdown(table)
            asset = assets_by_table.get(segment.table_index)
            if asset is not None:
                chunk += f"\n\n![Tabela (fallback visual fiel)]({asset.relative_path})"
            parts.append(chunk)
    return "\n\n".join(parts)


def _build_content_blocks(
    extracted: ExtractedQuestion,
    assets_by_region: dict[int, RenderedAsset],
    assets_by_table: dict[int, RenderedAsset],
    *,
    table_cells_verified: bool = False,
) -> list[ContentBlock] | None:
    """Project ``statement_segments`` into ``Question.content_blocks``.

    Populated only for a question whose segments actually include a table
    or a code block (see docs/decisions.md, "Phase 1C" ADR 12) - a
    content-shape rule, not a per-question one: every other question keeps
    ``content_blocks=None`` and is unaffected.

    ``table_cells_verified`` defaults to False - automated geometric
    extraction never claims cell-by-cell visual confirmation by itself.
    Only a real, disclosed visual audit
    (``visual_audit.load_table_cell_verified_question_ids``, PROMPT section
    16) can promote a table's ``validation_status`` to ``verified``.
    """
    has_table_or_code = any(
        isinstance(seg, TableSegment | CodeSegment) for seg in extracted.statement_segments
    )
    if not has_table_or_code:
        return None

    table_status = (
        TableValidationStatus.VERIFIED
        if table_cells_verified
        else TableValidationStatus.NEEDS_REVIEW
    )

    blocks: list[ContentBlock] = []
    for segment in extracted.statement_segments:
        if isinstance(segment, TextSegment):
            blocks.append(ParagraphBlock(text=segment.text))
        elif isinstance(segment, CodeSegment):
            blocks.append(CodeBlock(text=segment.text))
        elif isinstance(segment, FigureSegment):
            asset = assets_by_region.get(segment.region_index)
            if asset is not None:
                blocks.append(AssetBlock(asset_id=asset.asset_id))
        elif isinstance(segment, TableSegment):
            table = extracted.tables[segment.table_index]
            blocks.append(
                TableBlock(
                    headers=table.headers,
                    rows=table.rows,
                    validation_status=table_status,
                )
            )
            asset = assets_by_table.get(segment.table_index)
            if asset is not None:
                blocks.append(AssetBlock(asset_id=asset.asset_id))
    return blocks or None


def build_question(
    *,
    extracted: ExtractedQuestion,
    exam_year: int,
    applicable_courses: list[CourseCode],
    id_shorthand: str,
    section: str,
    exam_id: str,
    prova_source_path: str,
    prova_sha256: str,
    answer_key_entry: AnswerKeyEntry | None,
    answer_standard_entry: AnswerStandardEntry | None,
    answer_standard_source_path: str | None,
    answer_standard_sha256: str | None,
    gabarito_source_path: str,
    rendered_assets: list[RenderedAsset],
    assets_by_region: dict[int, RenderedAsset],
    assets_by_table: dict[int, RenderedAsset] | None = None,
    table_cells_verified: bool = False,
    answer_standard_assets: list[RenderedAsset] | None = None,
    validation: ValidationOutcome,
    visual_validation: VisualValidationStatus = VisualValidationStatus.NOT_PERFORMED,
) -> Question:
    """Build the canonical ``Question`` for one already-assembled extraction.

    ``applicable_courses``, ``id_shorthand`` and ``section`` are resolved by
    the caller, not derived here - a single-course booklet (2021) resolves
    them from its own fixed ``course``/``ExamStructure`` (see
    ``declared_structure.py``); a unified multi-course booklet (2011)
    resolves them per question number from an ``ExamStructureProfile`` (see
    ``exam_profile.py``). This function stays agnostic to which shape
    produced them (PROMPT Phase 2A section 10: no ``if year == 2011``
    branching inside the shared pipeline).
    """
    assets_by_table = assets_by_table or {}
    answer_standard_assets = answer_standard_assets or []
    kind = extracted.kind
    number = extracted.number
    suffix = "q" if kind == QuestionKind.OBJECTIVE else "d"
    question_id = f"enade-{exam_year}-{id_shorthand}-{suffix}{number:02d}"

    question_type = (
        QuestionType.MULTIPLE_CHOICE if kind == QuestionKind.OBJECTIVE else QuestionType.DISCURSIVE
    )

    statement = render_statement_markdown(extracted, assets_by_region, assets_by_table)
    content_blocks = _build_content_blocks(
        extracted, assets_by_region, assets_by_table, table_cells_verified=table_cells_verified
    )
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
                assets=[
                    Asset(
                        id=asset.asset_id,
                        type=asset.asset_type,
                        path=asset.relative_path,
                        source_page=asset.source_page,
                        extraction_method=asset.extraction_method,
                        sha256=asset.sha256,
                    )
                    for asset in answer_standard_assets
                ],
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

    # `validation.status` (automatic-only) can be promoted to VERIFIED here,
    # never demoted-then-promoted blindly: a real visual FAIL always wins
    # over a clean automatic pass, and a clean automatic pass is only ever
    # promoted when a genuine visual PASS is on record (PROMPT section
    # 12/14 - no mass promotion, no unearned `verified`).
    if visual_validation == VisualValidationStatus.FAILED:
        extraction_status = ExtractionStatus.NEEDS_REVIEW
    elif (
        visual_validation == VisualValidationStatus.PASSED
        and validation.status == ExtractionStatus.EXTRACTED
    ):
        extraction_status = ExtractionStatus.VERIFIED
    else:
        extraction_status = validation.status

    return Question(
        id=question_id,
        exam_year=exam_year,
        source_occurrences=[source_occurrence],
        applicable_courses=applicable_courses,
        section=section,
        question_number=number,
        question_type=question_type,
        statement=statement,
        content_blocks=content_blocks,
        alternatives=alternatives,
        correct_answer=correct_answer,
        official_answer_source=official_answer_source,
        answer_validation_status=answer_validation_status,
        answer_standard=answer_standard,
        assets=assets,
        extraction_method=ExtractionMethod.TEXT_LAYER,
        extraction_status=extraction_status,
        automatic_validation=validation.automatic_validation,
        visual_validation=visual_validation,
    )
