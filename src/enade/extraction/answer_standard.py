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

_DISCURSIVE_MARKER_RE = re.compile(r"(?i)^quest[aã]o\s+discursiva\s+0*(\d+)\b")
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

    current_number: int | None = None
    in_rubric = False
    buffer: list[Line] = []
    #: Pages where a new discursive marker or rubric heading was seen - a
    #: page *not* in this set, but that a rubric's own buffer still
    #: touches, is entirely consumed by that one rubric with nothing else
    #: on it (see the full-page widening pass below).
    pages_with_markers: set[int] = set()

    def flush() -> None:
        nonlocal buffer
        if current_number is not None and buffer:
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

    for line in lines:
        # Markers are checked *before* the chrome filter: "PADRAO DE RESPOSTA"
        # is (correctly) treated as chrome when it might leak into a question
        # statement elsewhere, but here it is the section marker this parser
        # is specifically looking for.
        marker = _DISCURSIVE_MARKER_RE.match(line.text)
        if marker:
            flush()
            current_number = int(marker.group(1))
            in_rubric = False
            pages_with_markers.add(line.page_number)
            continue
        if _RUBRIC_HEADING_RE.match(line.text.strip()):
            flush()
            in_rubric = True
            pages_with_markers.add(line.page_number)
            continue
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

    expected = set(range(1, 6))
    missing = expected - set(entries)
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
