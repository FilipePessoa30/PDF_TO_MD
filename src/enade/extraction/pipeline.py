"""Orchestrate the full PDF -> Markdown extraction pipeline for one exam.

PdfDocument -> PageExtractor(layout) -> QuestionBoundaryDetector ->
QuestionAssembler -> AssetExtractor -> AnswerKeyParser/AnswerStandardParser
-> Question transformer -> QuestionValidator -> MarkdownWriter -> audit.

Deliberately processes exactly one exam (one prova/gabarito/padrao trio) at
a time - PROMPT section 3 restricts Phase 1A to the single 2021 CC
bacharelado booklet, and this module has no batch/"all courses" entry
point, so scaling to the other 15 booklets is a conscious decision for a
later phase, not something that falls out accidentally.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path

import pymupdf

from enade.extraction.answer_key import AnswerKeyValueKind, parse_answer_key
from enade.extraction.answer_standard import parse_answer_standard
from enade.extraction.assembler import assemble_question
from enade.extraction.assets import RenderedAsset, render_region
from enade.extraction.boundaries import QuestionKind, detect_question_boundaries
from enade.extraction.declared_structure import parse_declared_structure
from enade.extraction.figures import compute_decorative_baseline
from enade.extraction.layout import extract_document_lines
from enade.extraction.markdown_writer import WriteResult, write_question_markdown
from enade.extraction.pdf_source import PdfDocument
from enade.extraction.to_question import COURSE_ID_SHORTHAND, build_question
from enade.extraction.validator import evaluate_extraction
from enade.inventory.pdfmeta import sha256_of_file
from enade.models.enums import CourseCode, ExtractionStatus, QuestionType
from enade.models.question import Question


@dataclass
class ExtractionMetrics:
    questions_found: int = 0
    objectives_found: int = 0
    discursives_found: int = 0
    verified: int = 0
    needs_review: int = 0
    total_assets: int = 0
    total_alternatives: int = 0
    answers_linked: int = 0
    answer_standards_linked: int = 0
    pages_processed: int = 0
    prova_size_bytes: int = 0
    structural_warning_count: int = 0
    question_warning_count: int = 0
    files_written: int = 0
    files_unchanged: int = 0
    elapsed_seconds: float = 0.0


@dataclass
class ExtractionResult:
    questions: list[Question]
    per_question_warnings: dict[str, list[str]] = field(default_factory=dict)
    structural_warnings: list[str] = field(default_factory=list)
    excluded_perception_pages: list[int] = field(default_factory=list)
    write_results: list[WriteResult] = field(default_factory=list)
    metrics: ExtractionMetrics = field(default_factory=ExtractionMetrics)


def extract_exam(
    *,
    prova_path: Path,
    gabarito_path: Path,
    padrao_path: Path,
    corpus_root: Path,
    exam_year: int,
    course: CourseCode,
    exam_id: str,
    questions_output_dir: Path,
    assets_output_dir: Path,
) -> ExtractionResult:
    start = time.monotonic()
    structural_warnings: list[str] = []

    with PdfDocument(prova_path, corpus_root) as prova:
        gabarito_doc = pymupdf.open(str(gabarito_path))
        padrao_doc = pymupdf.open(str(padrao_path))
        try:
            padrao_sha256 = sha256_of_file(padrao_path)
            gabarito_source_path = gabarito_path.relative_to(corpus_root).as_posix()
            padrao_source_path = padrao_path.relative_to(corpus_root).as_posix()

            lines = extract_document_lines(prova.raw)
            boundary_result = detect_question_boundaries(lines)
            structural_warnings.extend(boundary_result.warnings)

            declared = parse_declared_structure(prova.raw)
            structural_warnings.extend(declared.notes)

            baseline = compute_decorative_baseline(prova.raw)

            answer_key_result = parse_answer_key(gabarito_doc)
            structural_warnings.extend(answer_key_result.warnings)
            answer_standard_result = parse_answer_standard(padrao_doc)
            structural_warnings.extend(answer_standard_result.warnings)

            questions: list[Question] = []
            per_question_warnings: dict[str, list[str]] = {}
            metrics = ExtractionMetrics(
                pages_processed=prova.identity.page_count,
                prova_size_bytes=prova_path.stat().st_size,
            )

            ordered_spans = sorted(boundary_result.spans, key=lambda s: (s.kind.value, s.number))
            for span in ordered_spans:
                extracted = assemble_question(span, prova.raw, baseline)

                shorthand = COURSE_ID_SHORTHAND[course]
                suffix = "q" if span.kind == QuestionKind.OBJECTIVE else "d"
                question_id = f"enade-{exam_year}-{shorthand}-{suffix}{span.number:02d}"

                rendered_assets: list[RenderedAsset] = []
                assets_by_region: dict[int, RenderedAsset] = {}
                for index, region in enumerate(extracted.figure_regions):
                    asset_id = f"figure-{index + 1:02d}"
                    relative_path = f"{question_id}/{asset_id}.png"
                    absolute_path = assets_output_dir / question_id / f"{asset_id}.png"
                    rendered = render_region(
                        prova.raw, region, absolute_path, relative_path, asset_id
                    )
                    rendered_assets.append(rendered)
                    assets_by_region[index] = rendered

                answer_key_entry = answer_key_result.lookup(span.kind, span.number)
                answer_standard_entry = (
                    answer_standard_result.entries.get(span.number)
                    if span.kind == QuestionKind.DISCURSIVE
                    else None
                )
                has_answer = (
                    answer_key_entry is not None
                    if span.kind == QuestionKind.OBJECTIVE
                    else answer_standard_entry is not None
                )

                validation = evaluate_extraction(extracted, rendered_assets, has_answer=has_answer)

                question = build_question(
                    extracted=extracted,
                    exam_year=exam_year,
                    course=course,
                    exam_id=exam_id,
                    prova_source_path=prova.identity.source_path,
                    prova_sha256=prova.identity.sha256,
                    structure=declared.structure,
                    answer_key_entry=answer_key_entry,
                    answer_standard_entry=answer_standard_entry,
                    answer_standard_source_path=padrao_source_path
                    if span.kind == QuestionKind.DISCURSIVE
                    else None,
                    answer_standard_sha256=padrao_sha256
                    if span.kind == QuestionKind.DISCURSIVE
                    else None,
                    gabarito_source_path=gabarito_source_path,
                    rendered_assets=rendered_assets,
                    assets_by_region=assets_by_region,
                    validation=validation,
                )

                questions.append(question)
                per_question_warnings[question.id] = validation.reasons
                metrics.total_assets += len(rendered_assets)
                metrics.total_alternatives += len(question.alternatives)
                metrics.question_warning_count += len(validation.reasons)
                if validation.status == ExtractionStatus.VERIFIED:
                    metrics.verified += 1
                else:
                    metrics.needs_review += 1
                if question.question_type == QuestionType.MULTIPLE_CHOICE:
                    metrics.objectives_found += 1
                    if answer_key_entry is not None and answer_key_entry.value_kind in (
                        AnswerKeyValueKind.LETTER,
                        AnswerKeyValueKind.ANNULLED,
                    ):
                        metrics.answers_linked += 1
                else:
                    metrics.discursives_found += 1
                    if question.answer_standard is not None:
                        metrics.answer_standards_linked += 1
        finally:
            gabarito_doc.close()
            padrao_doc.close()

        write_results: list[WriteResult] = []
        course_dir = questions_output_dir / str(exam_year) / course.value
        for question in questions:
            result = write_question_markdown(question, course_dir)
            write_results.append(result)
            if result.changed:
                metrics.files_written += 1
            else:
                metrics.files_unchanged += 1

    metrics.questions_found = len(questions)
    metrics.structural_warning_count = len(structural_warnings)
    metrics.elapsed_seconds = time.monotonic() - start

    return ExtractionResult(
        questions=questions,
        per_question_warnings=per_question_warnings,
        structural_warnings=structural_warnings,
        excluded_perception_pages=boundary_result.perception_pages,
        write_results=write_results,
        metrics=metrics,
    )
