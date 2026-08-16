"""Parse the official "padrao de resposta" (grading rubric) PDF for discursives.

Structure confirmed empirically for ``2021/b3_padrao.pdf``: for each
Discursiva N, the document restates the question text (verbatim, from the
prova) and then shows a "PADRAO DE RESPOSTA" section with the actual
grading criteria. Only the rubric section is captured here - the restated
question text is intentionally discarded, since the question's real
``statement`` provenance must stay anchored to the prova (see PROMPT
section 33, "diferencie question source de answer source"), not to a
duplicate copy living in a different PDF.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, replace

import pymupdf

from enade.extraction.chrome import is_chrome_line
from enade.extraction.layout import Line, extract_document_lines

#: A bare-digit line matching this shape is, by text alone,
#: indistinguishable from a running page number (chrome.py's own
#: heuristic) - but a *row* of two or more such lines sharing a Y
#: position is a real table's own data row, never a page footer (a page
#: has exactly one page-number line, never several side by side).
_BARE_NUMBER_RE = re.compile(r"^\d+$")
#: Vertical tolerance (points) for treating two bare-number lines as
#: sitting on the same visual row - mirrors tables.py's own ROW_Y_TOLERANCE.
_ROW_Y_TOLERANCE = 3.0
#: A rescued row needs at least this many bare-number cells - one alone
#: is exactly the page-number shape this must not rescue.
_MIN_ROW_NUMBERS = 2

#: The "discursiva" qualifier itself is optional (PROMPT Phase 3A): 2021's
#: own padrao heading is "QUESTAO DISCURSIVA N", but 2008-b's is simply
#: "Questao N" - confirmed empirically to appear standalone, nothing else
#: on the same line, in both real PDFs, hence anchoring both ends (safe:
#: every heading in *this* document type is a discursive's own rubric by
#: definition, so a bare "Questao N" here is never ambiguous with an
#: objective the way it would be inside the prova itself).
_DISCURSIVE_MARKER_RE = re.compile(r"(?i)^quest[aã]o\s+(?:discursiva\s+)?0*(\d+)\b$")
_RUBRIC_HEADING_RE = re.compile(r"(?i)^padr[aã]o\s+de\s+resposta$")
#: Same paragraph-break heuristic as assembler.py: a vertical gap this large
#: (points) between consecutive lines is a real paragraph boundary.
PARAGRAPH_GAP_THRESHOLD = 19.0


@dataclass(frozen=True)
class AnswerStandardEntry:
    number: int
    pages: list[int]
    text: str
    #: Per-page (min_y0, max_y1) bounds of the rubric text itself, not the
    #: reprinted question text that precedes it on a shared page (see
    #: docs/decisions.md, "Phase 1C" ADR) - used to scope image detection
    #: (``find_answer_standard_images``) to genuinely new answer-standard
    #: diagrams, never a reprint of the question's own already-captured
    #: figure sitting earlier on the same page.
    page_bounds: dict[int, tuple[float, float]] = field(default_factory=dict)


@dataclass
class AnswerStandardParseResult:
    entries: dict[int, AnswerStandardEntry]
    warnings: list[str]


def _rescue_table_row_numbers(raw_lines: list[Line], buffer: list[Line]) -> list[Line]:
    """Recover bare-number table cells the chrome filter already dropped
    (PROMPT Phase 2D section 11/12).

    2011 D5's own answer standard has three small bit-width breakdown
    tables (e.g. "Rotulo Linha Palavra" / "13 17 2"), each just one data
    row - too few rows for tables.py's own ``detect_tables`` (built for
    D3's own larger, multi-row question-numbering grid, and requiring
    ``MIN_TABLE_ROWS=3`` to avoid false positives). A narrower, safe
    signature works here instead: a *page footer has exactly one*
    bare-number line; two or more bare-number lines sharing a Y position
    can only be a real row of table cells. Never rescues a lone digit
    (indistinguishable from a page number on text alone, so left as
    chrome, same as everywhere else in this corpus).
    """
    buffer_ids = {id(ln) for ln in buffer}
    # Row membership is judged against *every* bare-number line, whether
    # or not it still needs rescuing - a cell already present in the
    # buffer for some unrelated reason still counts as this row's own
    # partner, so its chrome-filtered neighbor is not penalized for it.
    all_numbers = [ln for ln in raw_lines if _BARE_NUMBER_RE.match(ln.text)]
    rescued: list[Line] = []
    seen_ids: set[int] = set()
    for i, ln in enumerate(all_numbers):
        if id(ln) in buffer_ids or not is_chrome_line(ln.text) or id(ln) in seen_ids:
            continue
        row = [
            other
            for j, other in enumerate(all_numbers)
            if j != i and abs(other.y0 - ln.y0) <= _ROW_Y_TOLERANCE
        ]
        if len(row) + 1 >= _MIN_ROW_NUMBERS:
            rescued.append(ln)
            seen_ids.add(id(ln))
            for other in row:
                if id(other) not in buffer_ids and id(other) not in seen_ids:
                    rescued.append(other)
                    seen_ids.add(id(other))
    return rescued


def _lines_to_paragraphs(lines: list[Line]) -> str:
    if not lines:
        return ""
    paragraphs: list[list[str]] = [[lines[0].text]]
    for previous, current in zip(lines, lines[1:], strict=False):
        same_page = previous.page_number == current.page_number
        gap = (current.y0 - previous.y1) if same_page else float("inf")
        if not same_page or gap >= PARAGRAPH_GAP_THRESHOLD:
            paragraphs.append([current.text])
        else:
            paragraphs[-1].append(current.text)
    return "\n\n".join(" ".join(p) for p in paragraphs)


def parse_answer_standard(doc: pymupdf.Document) -> AnswerStandardParseResult:
    lines = extract_document_lines(doc)
    warnings: list[str] = []
    entries: dict[int, AnswerStandardEntry] = {}
    all_marker_numbers: set[int] = set()

    # Whether this document separates a restated question from its own
    # rubric with an explicit "PADRAO DE RESPOSTA" heading is detected once
    # from the document itself, never assumed (PROMPT Phase 3A): 2011/2021's
    # own padrao always restates the question first, discarded here up to
    # that heading; 2008-b's own padrao never restates the question at all
    # and has no such heading anywhere - its rubric begins immediately after
    # the "Questao N" marker, so there is nothing to skip past.
    uses_rubric_heading = any(_RUBRIC_HEADING_RE.match(ln.text.strip()) for ln in lines)

    current_number: int | None = None
    in_rubric = not uses_rubric_heading
    buffer: list[Line] = []
    #: Every line seen while ``in_rubric`` is True, *before* chrome
    #: filtering - the table-rescue pass in ``flush()`` needs this to see
    #: a bare-number table cell that the chrome filter already dropped
    #: from ``buffer`` itself.
    raw_buffer: list[Line] = []
    #: Pages where a new discursive marker or rubric heading was seen - a
    #: page *not* in this set, but that a rubric's own buffer still
    #: touches, is entirely consumed by that one rubric with nothing else
    #: on it (see the full-page widening pass below).
    pages_with_markers: set[int] = set()

    def flush() -> None:
        nonlocal buffer, raw_buffer
        if current_number is not None and buffer:
            rescued = _rescue_table_row_numbers(raw_buffer, buffer)
            if rescued:
                buffer = sorted(buffer + rescued, key=lambda ln: (ln.page_number, ln.y0, ln.x0))
            text = _lines_to_paragraphs(buffer)
            if text.strip():
                if current_number in entries:
                    warnings.append(
                        f"answer standard: duplicate rubric text for discursiva {current_number}"
                    )
                pages = sorted({ln.page_number for ln in buffer})
                page_bounds: dict[int, tuple[float, float]] = {}
                for ln in buffer:
                    lo, hi = page_bounds.get(ln.page_number, (ln.y0, ln.y1))
                    page_bounds[ln.page_number] = (min(lo, ln.y0), max(hi, ln.y1))
                entries[current_number] = AnswerStandardEntry(
                    number=current_number, pages=pages, text=text, page_bounds=page_bounds
                )
        buffer = []
        raw_buffer = []

    for line in lines:
        # Markers are checked *before* the chrome filter: "PADRAO DE RESPOSTA"
        # is (correctly) treated as chrome when it might leak into a question
        # statement elsewhere, but here it is the section marker this parser
        # is specifically looking for.
        marker = _DISCURSIVE_MARKER_RE.match(line.text)
        if marker:
            flush()
            current_number = int(marker.group(1))
            all_marker_numbers.add(current_number)
            in_rubric = not uses_rubric_heading
            pages_with_markers.add(line.page_number)
            continue
        if _RUBRIC_HEADING_RE.match(line.text.strip()):
            flush()
            in_rubric = True
            pages_with_markers.add(line.page_number)
            continue
        if in_rubric and current_number is not None:
            raw_buffer.append(line)
        if is_chrome_line(line.text):
            continue
        if in_rubric and current_number is not None:
            buffer.append(line)

    flush()

    # A page that a rubric's own buffer touches but that never saw a new
    # marker/heading is entirely this one rubric's content, even where the
    # rubric's own *text* on that specific page is sparse (PROMPT section
    # 9.2: D4's padrao page 6 has only the one-line caption "Exemplos de
    # resposta possiveis para 'Cout':", with its actual diagram sitting
    # ~330pt further down - a narrow, text-derived bound would miss it
    # entirely). Widened to the full page height rather than guessed at,
    # since there is nothing else on the page it could conflict with.
    for number, entry in list(entries.items()):
        widened = dict(entry.page_bounds)
        changed = False
        for page_number in entry.pages:
            if page_number in pages_with_markers:
                continue
            page_height = doc[page_number - 1].rect.height
            if widened.get(page_number) != (0.0, page_height):
                widened[page_number] = (0.0, page_height)
                changed = True
        if changed:
            entries[number] = replace(entry, page_bounds=widened)

    # Every discursive number a real "Questao N" marker was actually seen
    # for (PROMPT Phase 3A - not a hardcoded range(1, 6): that was 2011/2021's
    # own D1..D5 convention specifically, and this parser has no visibility
    # into a different booklet's real discursive numbering, e.g. 2008-b's
    # own 9, 10, 20, 39, 40, 59, 60, 79, 80). A number the marker loop never
    # even encountered is simply outside this check's own scope - the
    # exam-structure profile is what knows the full expected set, not this
    # document-local parser.
    missing = all_marker_numbers - set(entries)
    if missing:
        warnings.append(
            f"answer standard: no rubric text found for discursiva(s) {sorted(missing)}"
        )

    return AnswerStandardParseResult(entries=entries, warnings=warnings)


#: Padding (points) applied to an entry's own rubric page_bounds before
#: testing whether an embedded image's vertical midpoint falls "inside" it
#: - generous enough to catch a diagram sitting just past the last rubric
#: text line, but bounded to this one page's own rubric region so it can
#: never reach back into the *reprinted question text* that precedes the
#: rubric heading on a shared page (PROMPT Phase 1C section 9.2 - D4's own
#: "Somador Completo de 1-bit" figure is reprinted this way on padrao page
#: 4, immediately before D4's rubric heading; it must never be captured
#: again here as if it were a new answer-standard-only diagram).
ANSWER_STANDARD_IMAGE_Y_PADDING = 15.0


def find_answer_standard_images(
    doc: pymupdf.Document, entry: AnswerStandardEntry
) -> list[tuple[int, tuple[float, float, float, float]]]:
    """Embedded raster images sitting within ``entry``'s own rubric text
    bounds - genuinely new answer-standard diagrams (PROMPT section 9),
    never a reprint of the question's own already-captured figure (which
    sits in a different, earlier page region covered by
    ``Question.assets`` from the prova, not here). Returns
    ``(page_number, bbox)`` pairs in document order.
    """
    found: list[tuple[int, tuple[float, float, float, float]]] = []
    for page_number in entry.pages:
        bounds = entry.page_bounds.get(page_number)
        if bounds is None:
            continue
        page = doc[page_number - 1]
        y_min = bounds[0] - ANSWER_STANDARD_IMAGE_Y_PADDING
        y_max = bounds[1] + ANSWER_STANDARD_IMAGE_Y_PADDING
        for info in page.get_image_info():
            bbox = info["bbox"]
            image_y_mid = (bbox[1] + bbox[3]) / 2
            if y_min <= image_y_mid <= y_max:
                found.append((page_number, tuple(bbox)))
    return found
