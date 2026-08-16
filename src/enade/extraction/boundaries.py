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

#: Two distinct discursive-marker shapes are known in this corpus: 2021's
#: "QUESTAO DISCURSIVA N" (kind word *before* the number - group 1) and
#: 2008-b's "QUESTAO N - DISCURSIVA" (kind word *after* the number - group
#: 3, PROMPT Phase 3A). The trailing separator is not a plain ASCII hyphen
#: in the source PDF - it is U+2013 (en dash) for every instance except
#: 2008-b's own Q59, which uses U+2014 (em dash) and lower-case
#: "Discursiva" (confirmed by direct codepoint inspection of
#: 2008/b1_prova.pdf, not assumed) - hence matching any of ``-``/en
#: dash/em dash, case-insensitively, rather than the one literal character
#: seen most often.
_MARKER_RE = re.compile(r"(?i)quest[aã]o\s+(discursiva\s+)?0*(\d+)\b(\s*[-–—]\s*discursiva)?")
# Anchored to the *whole* (normalized) line - deliberately stricter than a
# bare substring search. The exact same phrase "questionario de percepcao da
# prova" also appears as a table-row label in page 1's instruction table and
# inside prose sentences elsewhere ("... e do questionario de percepcao da
# prova deverao ser ...", see docs/decisions.md); only when the phrase *is*
# the entire line - as it is for the real section heading on the actual
# questionnaire page - does it mean "this page belongs to the questionnaire".
# A loose, unanchored match on a faux-space-corrected line was observed to
# wrongly flag page 1 once "questi onario" was correctly reconstructed to
# "questionario" (Phase 1B regression, see docs/decisions.md).
#
# Anchoring alone is *not* sufficient, though: page 1's structure table has
# this exact phrase, and nothing else, on its own line - textually identical
# to the real section heading on page 44. Disambiguating requires a second,
# independent signal: the real questionnaire page also contains the reused
# "QUESTAO 01".."QUESTAO 09" marker lines the heading introduces, while a
# page that merely *mentions* the concept (page 1) has none (empirically
# confirmed: page 1 has 0 QUESTAO-marker lines, page 44 has 9). See
# ``detect_question_boundaries``, which requires both signals to co-occur on
# the same page before treating it as a perception page.
# The trailing qualifier wording itself varies across years (PROMPT Phase
# 3A): 2021 prints "...da prova", 2008-b prints "...sobre a prova"
# (confirmed against the real PDF) - both, and the bare heading with no
# qualifier at all, must be recognized as the same heading.
_PERCEPTION_MARKER_RE = re.compile(
    r"(?i)^question[aá]rio\s+de\s+percep[cç][aã]o(\s+(da|sobre\s+a)\s+prova)?$"
)


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
    return bool(_PERCEPTION_MARKER_RE.match(normalize_for_chrome_check(line.text)))


def detect_question_boundaries(
    all_lines: list[Line], *, combined_numbering: bool = False
) -> BoundaryDetectionResult:
    """Find every objective/discursive question marker and its content span.

    ``all_lines`` must already be in correct document reading order (see
    :func:`enade.extraction.layout.extract_document_lines`).

    ``combined_numbering`` (PROMPT Phase 3A, default False - exact prior
    behaviour unchanged): 2011/2021 give discursive questions their own,
    independent 1..N run ("QUESTAO DISCURSIVA 1".."5"), entirely separate
    from the objective 1..N run - each kind's numbering is validated for
    gaps on its own. 2008-b's discursive markers instead reuse the same
    printed number sequence as its objectives, interleaved among them
    ("QUESTAO 38", "QUESTAO 39 - DISCURSIVA", "QUESTAO 40 - DISCURSIVA",
    "QUESTAO 41") - checking *that* kind of booklet for per-kind gaps
    would misreport every interleaving as a "gap in numbering" (there
    genuinely is no discursive question 11, because 11 is objective in
    this booklet - that is not a defect). Set True for a booklet whose
    printed numbering is known to work this way; the check then runs once,
    over the union of both kinds, instead of once per kind.
    """
    warnings: list[str] = []

    candidate_perception_pages = {
        ln.page_number for ln in all_lines if _line_matches_perception_marker(ln)
    }
    pages_with_question_markers = {ln.page_number for ln in all_lines if _MARKER_RE.search(ln.text)}
    perception_pages = sorted(candidate_perception_pages & pages_with_question_markers)
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
        is_discursive = match.group(1) is not None or match.group(3) is not None
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

    if combined_numbering:
        _validate_combined_numbering(spans, warnings)
    else:
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


def _validate_combined_numbering(spans: list[QuestionSpan], warnings: list[str]) -> None:
    """The ``combined_numbering=True`` counterpart to ``_validate_numbering``
    (PROMPT Phase 3A) - objective and discursive markers share one printed
    number stream, so duplicates and gaps are checked once, across both
    kinds together, rather than per kind (see ``detect_question_boundaries``'s
    own docstring for why the per-kind check is wrong for this shape).
    """
    numbers = [s.number for s in spans]
    duplicates = {n for n in numbers if numbers.count(n) > 1}
    if duplicates:
        warnings.append(f"combined: duplicate question number(s) found: {sorted(duplicates)}")
    if not numbers:
        return
    expected = set(range(min(numbers), max(numbers) + 1))
    missing = expected - set(numbers)
    if missing:
        warnings.append(f"combined: gap(s) in numbering, missing {sorted(missing)}")
