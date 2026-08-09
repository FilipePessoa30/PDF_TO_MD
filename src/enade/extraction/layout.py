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

from enade.extraction.label_normalization import LabelCorrection, normalize_known_label
from enade.extraction.spacing import SpacingCorrection, reconstruct_line_text
from enade.extraction.symbol_fonts import is_symbol_font, substitute_symbol_font_text

#: Only lines at least this wide (points) count as evidence of a column's
#: left margin - short lines (figure labels, single digits) are noisy signal.
MIN_COLUMN_LINE_WIDTH = 80.0
#: A left-margin bucket needs at least this many substantial lines to count.
MIN_LINES_PER_COLUMN = 4
#: Two candidate column margins must be at least this far apart (points).
MIN_COLUMN_SEPARATION = 100.0
#: Bucket width (points) used to group x0 values before counting.
COLUMN_BUCKET_SIZE = 5.0
#: A line is classified as belonging to the right column only if its x0 is
#: within this many points of the right column's own detected margin (or
#: past it) - see ``extract_page_lines``. Matches ``COLUMN_BUCKET_SIZE``:
#: just enough to absorb the margin's own rounding, not a general-purpose
#: fuzziness margin.
COLUMN_RIGHT_MARGIN_TOLERANCE = 5.0


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
    #: Geometric spacing corrections applied to this line's text (see
    #: spacing.py) - empty unless a ligature-injected faux space was found
    #: and merged. Carried on the Line so callers can build an auditable
    #: transformation log without a separate side-channel.
    spacing_corrections: tuple[SpacingCorrection, ...] = ()
    #: Known font-mangled structural labels replaced by their canonical
    #: form on this line (see label_normalization.py) - same auditability
    #: purpose as spacing_corrections, kept as a separate list because it is
    #: a distinct transformation type (PROMPT Phase 1B section 15).
    label_corrections: tuple[LabelCorrection, ...] = ()
    #: Known symbol-font character substitutions applied to this line (see
    #: symbol_fonts.py) - reuses LabelCorrection's shape (original/corrected
    #: text) but kept in its own field/transformation-log type, since it is
    #: a mechanically distinct correction (font-glyph identity, not a
    #: whole-line label lookup).
    symbol_corrections: tuple[LabelCorrection, ...] = ()

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
            final_text = text.strip() if not is_monospace else text.lstrip("\f\v")
            corrections: list[SpacingCorrection] = []
            if not is_monospace:
                # Code lines keep their literal dict-mode text (word-geometry
                # reconstruction is prose-only; see spacing.py) - everything
                # else is re-derived from glyph geometry, which also happens
                # to normalize incidental whitespace differences for free.
                reconstructed, corrections = reconstruct_line_text(
                    page, page_number, (x0, y0, x1, y1)
                )
                if reconstructed:
                    final_text = reconstructed
            symbol_corrections: list[LabelCorrection] = []
            if not is_monospace and any(is_symbol_font(font) for font in fonts):
                substituted = substitute_symbol_font_text(final_text)
                if substituted != final_text:
                    symbol_corrections.append(
                        LabelCorrection(
                            page_number=page_number, original=final_text, corrected=substituted
                        )
                    )
                    final_text = substituted
            label_corrections: list[LabelCorrection] = []
            if not is_monospace:
                known_label = normalize_known_label(final_text)
                if known_label is not None:
                    label_corrections.append(
                        LabelCorrection(
                            page_number=page_number, original=final_text, corrected=known_label
                        )
                    )
                    final_text = known_label
            lines.append(
                Line(
                    page_number=page_number,
                    text=final_text,
                    x0=x0,
                    y0=y0,
                    x1=x1,
                    y1=y1,
                    is_monospace=is_monospace,
                    spacing_corrections=tuple(corrections),
                    label_corrections=tuple(label_corrections),
                    symbol_corrections=tuple(symbol_corrections),
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
                spacing_corrections=ln.spacing_corrections + other.spacing_corrections,
                label_corrections=ln.label_corrections + other.label_corrections,
                symbol_corrections=ln.symbol_corrections + other.symbol_corrections,
            )
        )
    return merged


def _detect_column_margins(lines: list[Line]) -> tuple[float, float] | None:
    """Return (left_margin, right_margin) if ``lines`` show a genuine two-column layout.

    ``right_margin`` is the right column's own detected left edge (not a
    midpoint) - see ``extract_page_lines``, which classifies a line as
    "right column" by closeness to this actual margin rather than by
    which side of some arbitrary midpoint it falls on.
    """
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
    return left_margin, right_margin


def extract_page_lines(page: pymupdf.Page, page_number: int) -> list[Line]:
    """Extract every physical line on ``page``, in visual reading order.

    Single-column pages: sorted by (y0, x0). Two-column pages (detected via
    :func:`_detect_column_margins`): every left-column line (top to
    bottom), then every right-column line (top to bottom) - see module
    docstring.
    """
    lines = _merge_orphan_markers(_raw_lines(page, page_number))
    margins = _detect_column_margins(lines)

    if margins is None:
        lines.sort(key=lambda ln: (round(ln.y0, 1), ln.x0))
        return lines

    _, right_margin = margins
    # A line is "right column" only if it starts at or past the right
    # column's own actual left edge (with a small tolerance for rounding
    # noise) - not merely past the midpoint between the two columns.
    # PyMuPDF's dict-mode text extraction occasionally splits one
    # continuous visual line into several separate "line" entries with
    # unusually wide (but still sub-word-wrap) gaps between them (observed:
    # a uniform 14.4pt gap splitting "B Escalonamento por taxas
    # monotonicas" into four pieces on Q9/Q10's shared page); a midpoint
    # split let the tail fragments ("taxas", "monotonicas") cross into
    # column 2's line range even though they are still far short of where
    # column 2 actually starts, corrupting Q10's statement with a
    # fragment of Q9's own alternative B (Phase 1B audit finding, see
    # docs/decisions.md). Requiring closeness to the real right-column
    # margin instead keeps ambiguous mid-page fragments in the left
    # column, where the evidence actually places them.
    right_threshold = right_margin - COLUMN_RIGHT_MARGIN_TOLERANCE
    left = sorted(
        (ln for ln in lines if ln.x0 < right_threshold), key=lambda ln: (round(ln.y0, 1), ln.x0)
    )
    right = sorted(
        (ln for ln in lines if ln.x0 >= right_threshold), key=lambda ln: (round(ln.y0, 1), ln.x0)
    )
    return left + right


def extract_document_lines(doc: pymupdf.Document) -> list[Line]:
    """Extract position-sorted lines for every page, in page order."""
    all_lines: list[Line] = []
    for index in range(doc.page_count):
        page = doc[index]
        all_lines.extend(extract_page_lines(page, page_number=index + 1))
    return all_lines
