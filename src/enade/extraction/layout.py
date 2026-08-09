"""Position-sorted line extraction from a PDF page.

Empirical findings this module exists to fix (Phase 1A investigation of the
2021 Ciencia da Computacao booklet, see docs/corpus.md "extraction
strategy"):

1. PyMuPDF's own linear ``page.get_text("text")`` does *not* always emit
   content in visual top-to-bottom order. On pages with a floating figure
   (e.g. page 30 / Questao 21), the figure's caption and label text is
   emitted *after* all five alternatives, even though the figure sits
   between the statement and the alternatives on the printed page. Sorting
   extracted lines by their own bounding-box position (``y0`` then ``x0``)
   fixes this for single-column pages.

2. Some pages are genuinely two-column (e.g. page 19: Questao 09 in the
   left column, Questao 10 in the right column, both starting at the same
   y0; page 17: Discursiva 5's statement in the left column, a pseudocode
   listing in the right column). A naive global (y0, x0) sort would
   interleave the two columns line-by-line and scramble both. This module
   detects the two dominant, well-separated left margins among
   "substantial" lines (width > ``MIN_COLUMN_LINE_WIDTH``, to avoid being
   fooled by a handful of short floating figure-label lines) and, when
   found, orders the whole left column before the whole right column.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

import pymupdf

#: Only lines at least this wide (points) count as evidence of a column's
#: left margin - short lines (figure labels, single digits) are noisy signal.
MIN_COLUMN_LINE_WIDTH = 80.0
#: A left-margin bucket needs at least this many substantial lines to count.
MIN_LINES_PER_COLUMN = 4
#: Two candidate column margins must be at least this far apart (points).
MIN_COLUMN_SEPARATION = 100.0
#: Bucket width (points) used to group x0 values before counting.
COLUMN_BUCKET_SIZE = 5.0


#: Font-name substrings (case-insensitive) that mark a line as monospaced -
#: i.e. source code / pseudocode, which must keep its own line breaks and
#: indentation rather than being rejoined into flowing prose (PROMPT
#: section 16: "Sempre preserve ... pseudocodigo; codigo").
_MONOSPACE_FONT_HINTS = ("courier", "mono", "consolas")

#: The circled A-E alternative markers are drawn with a dedicated pictograph
#: font ("BundesbahnPiStd-1" in this corpus) distinct from the body text
#: font. PyMuPDF's line-grouping usually keeps the marker glyph and its
#: alternative text as one physical line, but occasionally (observed on
#: page 23 / Questao 14, alternative C) splits them into two adjacent
#: "lines" with slightly different bboxes. An orphan marker line - text is
#: *only* a bare letter A-E, nothing else - is merged into whichever nearby
#: line on the same page is its most plausible partner, rather than being
#: left to silently vanish or misalign the alternative sequence.
_ORPHAN_MARKER_RE = re.compile(r"^[A-E]\t*$")
#: Max vertical distance (points) for an orphan marker to be paired with a line.
_ORPHAN_MARKER_MAX_DISTANCE = 20.0


@dataclass(frozen=True)
class Line:
    """One physical line of text on a page, with its bounding box."""

    page_number: int  # 1-indexed
    text: str
    x0: float
    y0: float
    x1: float
    y1: float
    is_monospace: bool = False

    @property
    def bbox(self) -> tuple[float, float, float, float]:
        return (self.x0, self.y0, self.x1, self.y1)


def _raw_lines(page: pymupdf.Page, page_number: int) -> list[Line]:
    raw = page.get_text("dict")
    lines: list[Line] = []
    for block in raw.get("blocks", []):
        if block.get("type") != 0:  # 0 = text block, 1 = image block
            continue
        for line in block.get("lines", []):
            spans = line.get("spans", [])
            if not spans:
                continue
            text = "".join(span.get("text", "") for span in spans).rstrip()
            if not text.strip():
                continue
            fonts = [span.get("font", "") for span in spans]
            is_monospace = bool(fonts) and all(
                any(hint in font.lower() for hint in _MONOSPACE_FONT_HINTS) for font in fonts
            )
            x0, y0, x1, y1 = line["bbox"]
            lines.append(
                Line(
                    page_number=page_number,
                    text=text.strip() if not is_monospace else text.lstrip("\f\v"),
                    x0=x0,
                    y0=y0,
                    x1=x1,
                    y1=y1,
                    is_monospace=is_monospace,
                )
            )
    return lines


def _merge_orphan_markers(lines: list[Line]) -> list[Line]:
    """Merge bare-letter marker lines into their nearest same-page partner line."""
    used: set[int] = set()
    merged: list[Line] = []
    for i, ln in enumerate(lines):
        if i in used:
            continue
        if not _ORPHAN_MARKER_RE.match(ln.text):
            merged.append(ln)
            continue
        best_j: int | None = None
        best_distance: float | None = None
        for j, other in enumerate(lines):
            if j == i or j in used or other.page_number != ln.page_number:
                continue
            if _ORPHAN_MARKER_RE.match(other.text):
                continue
            distance = abs(other.y0 - ln.y0)
            if distance <= _ORPHAN_MARKER_MAX_DISTANCE and (
                best_distance is None or distance < best_distance
            ):
                best_j, best_distance = j, distance
        if best_j is None:
            merged.append(ln)  # no plausible partner found; keep as-is (still visible, not lost)
            continue
        other = lines[best_j]
        used.add(i)
        used.add(best_j)
        merged.append(
            Line(
                page_number=ln.page_number,
                text=f"{ln.text.rstrip(chr(9))}\t{other.text}",
                x0=min(ln.x0, other.x0),
                y0=min(ln.y0, other.y0),
                x1=max(ln.x1, other.x1),
                y1=max(ln.y1, other.y1),
                is_monospace=other.is_monospace,
            )
        )
    return merged


def _detect_column_split(lines: list[Line]) -> float | None:
    """Return the x split point if ``lines`` show a genuine two-column layout."""
    substantial = [ln for ln in lines if (ln.x1 - ln.x0) >= MIN_COLUMN_LINE_WIDTH]
    if len(substantial) < 2 * MIN_LINES_PER_COLUMN:
        return None

    buckets = Counter(round(ln.x0 / COLUMN_BUCKET_SIZE) * COLUMN_BUCKET_SIZE for ln in substantial)
    common = [x for x, count in buckets.most_common() if count >= MIN_LINES_PER_COLUMN]
    if len(common) < 2:
        return None

    left_margin, right_margin = min(common[0], common[1]), max(common[0], common[1])
    if right_margin - left_margin < MIN_COLUMN_SEPARATION:
        return None
    return (left_margin + right_margin) / 2


def extract_page_lines(page: pymupdf.Page, page_number: int) -> list[Line]:
    """Extract every physical line on ``page``, in visual reading order.

    Single-column pages: sorted by (y0, x0). Two-column pages (detected via
    :func:`_detect_column_split`): every left-column line (top to bottom),
    then every right-column line (top to bottom) - see module docstring.
    """
    lines = _merge_orphan_markers(_raw_lines(page, page_number))
    split_x = _detect_column_split(lines)

    if split_x is None:
        lines.sort(key=lambda ln: (round(ln.y0, 1), ln.x0))
        return lines

    left = sorted((ln for ln in lines if ln.x0 < split_x), key=lambda ln: (round(ln.y0, 1), ln.x0))
    right = sorted(
        (ln for ln in lines if ln.x0 >= split_x), key=lambda ln: (round(ln.y0, 1), ln.x0)
    )
    return left + right


def extract_document_lines(doc: pymupdf.Document) -> list[Line]:
    """Extract position-sorted lines for every page, in page order."""
    all_lines: list[Line] = []
    for index in range(doc.page_count):
        page = doc[index]
        all_lines.extend(extract_page_lines(page, page_number=index + 1))
    return all_lines
