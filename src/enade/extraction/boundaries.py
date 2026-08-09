"""Detect question boundaries across the whole prova document.

Two empirical hazards this module exists to handle (see docs/corpus.md):

1. Formacao Geral headings ("QUESTAO 01", "QUESTAO DISCURSIVA 01", "TEXTO I")
   are set in a pseudo-small-caps style whose underlying text is
   case-mangled (e.g. "QuEStãO diSCuRSiVa 01"), while Componente
   Especifico headings extract as clean uppercase. Marker detection must be
   case-insensitive.
2. The Questionario de Percepcao (perception survey, page 44 in the 2021
   booklet) *reuses* "QUESTAO 01".."QUESTAO 09" - textually indistinguishable
   from Formacao Geral's own Q01-Q09 without page/section context. Any page
   containing the literal marker "QUESTIONARIO DE PERCEPCAO" is therefore
   excluded from academic boundary detection *in its entirety* (all
   "QUESTAO N" matches on that page belong to the questionnaire, not to the
   academic question bank - see PROMPT section 4).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

from enade.extraction.chrome import is_chrome_line, normalize_for_chrome_check
from enade.extraction.layout import Line

_MARKER_RE = re.compile(r"(?i)quest[aã]o\s+(discursiva\s+)?0*(\d+)\b")
_PERCEPTION_MARKER_RE = re.compile(r"(?i)question[aá]rio\s+de\s+percep[cç][aã]o")


class QuestionKind(StrEnum):
    OBJECTIVE = "objective"
    DISCURSIVE = "discursive"


@dataclass(frozen=True)
class Marker:
    kind: QuestionKind
    number: int
    line_index: int  # index into the position-sorted, cross-page line list
    page_number: int


@dataclass(frozen=True)
class QuestionSpan:
    kind: QuestionKind
    number: int
    lines: tuple[Line, ...]  # every line strictly within this question's span
    start_page: int
    end_page: int


@dataclass
class BoundaryDetectionResult:
    spans: list[QuestionSpan]
    perception_pages: list[int]
    warnings: list[str]


def _line_matches_perception_marker(line: Line) -> bool:
    return bool(_PERCEPTION_MARKER_RE.search(line.text))


def detect_question_boundaries(all_lines: list[Line]) -> BoundaryDetectionResult:
    """Find every objective/discursive question marker and its content span.

    ``all_lines`` must already be in correct document reading order (see
    :func:`enade.extraction.layout.extract_document_lines`).
    """
    warnings: list[str] = []

    perception_pages = sorted(
        {ln.page_number for ln in all_lines if _line_matches_perception_marker(ln)}
    )
    perception_pages_set = set(perception_pages)

    markers: list[Marker] = []
    for index, line in enumerate(all_lines):
        if line.page_number in perception_pages_set:
            continue
        match = _MARKER_RE.search(line.text)
        if not match:
            continue
        # Require the marker to be at (or very near) the start of the line -
        # avoids matching an incidental mention of "questao" mid-sentence
        # (e.g. cover-page instructions: "responda cada questao discursiva
        # em, no maximo, 15 linhas" does not match \s+\d+ right after
        # "discursiva", so it is already excluded by the regex itself; this
        # additional start-of-line check guards against similar future cases).
        prefix = normalize_for_chrome_check(line.text[: match.start()])
        if prefix:
            continue
        is_discursive = match.group(1) is not None
        number = int(match.group(2))
        markers.append(
            Marker(
                kind=QuestionKind.DISCURSIVE if is_discursive else QuestionKind.OBJECTIVE,
                number=number,
                line_index=index,
                page_number=line.page_number,
            )
        )

    if not markers:
        warnings.append(
            "no question markers found at all - check the marker regex against this PDF"
        )
        return BoundaryDetectionResult(
            spans=[], perception_pages=perception_pages, warnings=warnings
        )

    spans: list[QuestionSpan] = []
    for i, marker in enumerate(markers):
        end_index = markers[i + 1].line_index if i + 1 < len(markers) else len(all_lines)
        raw_span_lines = all_lines[marker.line_index : end_index]
        # The last marker's span would otherwise run to literal end-of-document,
        # swallowing the questionnaire page(s) and any trailing blank/"rascunho"
        # pages after the last real question. Perception-page lines are never
        # part of the academic question bank (see module docstring); trailing
        # chrome-only pages carry no real content either, so they are dropped
        # from the *span* here (a full chrome pass still runs later on the
        # remaining lines for interior furniture like per-page footers).
        span_lines = tuple(
            ln for ln in raw_span_lines if ln.page_number not in perception_pages_set
        )
        content_pages = sorted({ln.page_number for ln in span_lines if not is_chrome_line(ln.text)})
        all_span_pages = sorted({ln.page_number for ln in span_lines})
        pages = content_pages or all_span_pages
        spans.append(
            QuestionSpan(
                kind=marker.kind,
                number=marker.number,
                lines=span_lines,
                start_page=pages[0] if pages else marker.page_number,
                end_page=pages[-1] if pages else marker.page_number,
            )
        )

    _validate_numbering(spans, QuestionKind.OBJECTIVE, warnings)
    _validate_numbering(spans, QuestionKind.DISCURSIVE, warnings)

    return BoundaryDetectionResult(
        spans=spans, perception_pages=perception_pages, warnings=warnings
    )


def _validate_numbering(spans: list[QuestionSpan], kind: QuestionKind, warnings: list[str]) -> None:
    numbers = [s.number for s in spans if s.kind == kind]
    duplicates = {n for n in numbers if numbers.count(n) > 1}
    if duplicates:
        warnings.append(f"{kind.value}: duplicate question number(s) found: {sorted(duplicates)}")
    if not numbers:
        return
    expected = set(range(min(numbers), max(numbers) + 1))
    missing = expected - set(numbers)
    if missing:
        warnings.append(f"{kind.value}: gap(s) in numbering, missing {sorted(missing)}")
