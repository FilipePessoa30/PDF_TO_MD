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

from enade.extraction.chrome import is_chrome_line
from enade.extraction.fragment_reconstruction import (
    FragmentMergeTrace,
    RawLineFragment,
    group_line_fragments,
    merged_bbox_of,
)
from enade.extraction.label_normalization import LabelCorrection, normalize_known_label
from enade.extraction.layout_overrides import LayoutOverrideSet
from enade.extraction.spacing import SpacingCorrection, reconstruct_line_text
from enade.extraction.symbol_fonts import is_symbol_font, substitute_symbol_font_text

#: Only lines at least this wide (points) count as evidence of a column's
#: left margin - short lines (figure labels, single digits) are noisy signal.
MIN_COLUMN_LINE_WIDTH = 80.0
#: A left-margin bucket needs at least this many substantial lines to count.
#: 3, not 4: a genuinely two-column page can still have one thin column
#: (e.g. a short closing paragraph plus a handful of short alternatives) -
#: 2011 unified booklet page 11, where Q13's tail + Q14's own body only
#: ever reach 3 qualifying lines at their shared left margin, causing
#: column detection to return None entirely and fall back to a naive
#: (y0, x0) sort that put Q15's marker (right column, y0=67.7) ahead of
#: Q14's (left column, y0=68.2) since neither is aware of the other's
#: column. Verified empirically against the full 2021 corpus (byte-
#: identical output) before lowering this from 4.
MIN_LINES_PER_COLUMN = 3
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
#: PROMPT Phase 3C, "Classe B" - two attempts at a general fix for 2008-b's
#: own Questao 68 (a 3-line nested-SQL-subquery continuation mistaken for a
#: genuine second page column, scrambling its own WHERE clause - blocker
#: ``q68-sql-code-block-reordering``) were tried and reverted in Phase 3C;
#: both are recorded in full (evidence + diffs) under
#: ``scratchpad/experiment-column-height-ratio.diff`` and
#: ``scratchpad/experiment-q68-vs-q50-evidence.md``:
#: 1. A bare column-height-ratio gate (reject a candidate column whose own
#:    Y-extent is a small fraction of the other's) fixed Q68 but also
#:    rejected Questao 50's own genuine two-column page, whose left column
#:    is an equally short but entirely legitimate 3-line prose intro -
#:    height ratio alone does not reliably tell the two apart (0.05 vs.
#:    0.14, on the very same booklet).
#: 2. Requiring the short column's own lines to *also* be monospace (code
#:    is never a real second column's own shape in this corpus) would have
#:    distinguished them correctly in principle, but 2008-b's own PDF tags
#:    this exact SQL code with an arbitrary embedded-subset font name
#:    ("TT2F7Bo00") that ``Line.is_monospace``'s font-name-substring
#:    heuristic (courier/mono/consolas) does not recognize - the signal
#:    itself is not available for this booklet's own fonts, not just
#:    unused.
#: PHASE 3D: a third signal succeeds where (2) failed - font *size*, not
#: font *name*. Q68's own SQL code is set at 9pt against this page's own
#: 10pt body (confirmed by direct instrumentation), while Q50's own short
#: left-column intro is set at the page's own body size (10pt) exactly -
#: code in this corpus is reliably smaller than body prose even when its
#: font name gives no monospace signal at all. Combined with the height
#: ratio from attempt (1) above (required together, not alone - a short
#: column is not enough on its own, per Q50; a same-size short column, per
#: attempt (1)'s own finding, is not enough either), this correctly
#: distinguishes the two: see ``_is_short_off_size_column``.
#: Height-ratio threshold reused from the Phase 3C attempt (see above) -
#: unchanged, since it was never the source of that attempt's own false
#: positive (font size was).
MIN_COLUMN_HEIGHT_RATIO = 0.2
#: A line needs at least this many characters to count as evidence of body
#: prose for font-size purposes - mirrors
#: ``figures._MIN_BODY_TEXT_LENGTH``, duplicated here (not imported) to
#: avoid a circular import (``figures.py`` already imports from this
#: module) - the same accepted pattern already used for
#: ``_PARAGRAPH_CONTINUATION_GAP`` (see assembler.py's own copy of that
#: constant, and its docstring's own note on why importing back is
#: circular).
_MIN_BODY_TEXT_LENGTH = 20
#: Same reasoning/duplication as ``_MIN_BODY_TEXT_LENGTH`` above - mirrors
#: ``figures._MIN_MARGIN_AGREEMENT``.
_MIN_BODY_FONT_AGREEMENT = 2


def _page_dominant_body_font_size(lines: list[Line]) -> float | None:
    """Local copy of ``figures._dominant_body_font_size`` (see that
    function's own docstring for the full rationale and the Questao 1
    regression it exists to avoid) - duplicated rather than imported to
    avoid a circular import, since ``figures.py`` already imports from
    this module.
    """
    substantial = [ln for ln in lines if len(ln.text.strip()) >= _MIN_BODY_TEXT_LENGTH]
    if not substantial:
        return None
    margin_x0, margin_count = Counter(round(ln.x0) for ln in substantial).most_common(1)[0]
    if margin_count < _MIN_BODY_FONT_AGREEMENT:
        return None
    at_margin = [ln for ln in substantial if round(ln.x0) == margin_x0]
    size, count = Counter(round(ln.font_size, 1) for ln in at_margin).most_common(1)[0]
    if count < _MIN_BODY_FONT_AGREEMENT:
        return None
    return float(size)


def _is_short_off_size_column(
    lines: list[Line], own_height: float, other_height: float, body_font_size: float | None
) -> bool:
    """True if ``lines`` (one candidate column's own lines) are both short
    relative to the other column (see ``MIN_COLUMN_HEIGHT_RATIO``) *and*
    set in a font smaller than the page's own dominant body size - PROMPT
    Phase 3D, "Classe B". Requires both signals together: a short column
    with body-size font (2008-b's own Questao 50) is a genuine narrow
    intro, not this pattern; a same-size-as-body short column is never
    rejected regardless of font. ``body_font_size`` of ``None`` (no
    reliable body size on this page) means the font signal is unavailable,
    so this never fires - conservative by construction.
    """
    if body_font_size is None or other_height <= 0 or not lines:
        return False
    if (own_height / other_height) >= MIN_COLUMN_HEIGHT_RATIO:
        return False
    # Rounded to the same precision _page_dominant_body_font_size itself
    # uses to compute body_font_size - comparing a raw (unrounded) size
    # against a rounded one let Questao 50's own real 9.96pt body text
    # (which rounds to the same 10.0pt body size) register as "smaller
    # than body" by pure floating-point noise, wrongly rejecting its own
    # genuine two-column page (confirmed by direct regeneration).
    return all(round(ln.font_size, 1) < body_font_size for ln in lines)


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
#:
#: NOTE: a width-based filter (excluding plain-glyph-width bare letters,
#: e.g. a real table's "A B C D" column headers, from qualifying as an
#: orphan marker) was tried here and reverted - it fixed 2011 Q22's
#: truth-table header but changed 2021 Q23/Q34/D4's already-certified gold
#: output (a diagram-label letter there also merges through this same path
#: at a similarly narrow width), which PROMPT Phase 2A section 24 forbids
#: without an explicit, visually-revalidated migration. Q22's table is left
#: as a documented, disclosed needs_review case instead (see the Phase 2A
#: report) rather than risk the protected 2021 corpus for a fix that turned
#: out not to generalize as cleanly as it first appeared to.
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
    #: The largest font size (points) among this line's own spans - a
    #: mixed-size line is conservatively treated as "not small" (see
    #: ``figures._is_smaller_than_body_font``). Used to distinguish a real
    #: caption/label (PROMPT Phase 3D section 6-7: consistently set smaller
    #: than the page's own body-prose font in this corpus's own evidence,
    #: e.g. 2008-b's D9 own photo credit at 6pt against a 10pt body, 2021's
    #: own Q7 citation at 9pt against a 12pt body) from a real section
    #: header/headline sharing or exceeding the body's own font size (2008-b
    #: D9's own "DIREITOS HUMANOS EM QUESTAO" headline is 11pt, the same
    #: size as the page's own "QUESTAO 9" marker, not the 6pt of its real
    #: photo credit two lines below it - see docs/decisions.md).
    font_size: float = 0.0
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
    #: Geometric line-fragment reconstructions applied to build this line
    #: (see fragment_reconstruction.py, PROMPT Phase 3H "Cluster D") - empty
    #: unless PyMuPDF's own dict-mode reported this physical line as more
    #: than one separate "line" entry and geometric+documentary evidence
    #: (matching baseline, compatible font, a safe gap, and a literal
    #: trailing space in the raw glyph stream) justified rejoining them.
    #: Same auditability purpose and transformation-log participation as
    #: spacing_corrections/label_corrections/symbol_corrections.
    fragment_merges: tuple[FragmentMergeTrace, ...] = ()

    @property
    def bbox(self) -> tuple[float, float, float, float]:
        return (self.x0, self.y0, self.x1, self.y1)


def _collect_raw_fragments(page: pymupdf.Page, page_number: int) -> list[RawLineFragment]:
    """Every PyMuPDF dict-mode "line" entry on ``page``, before any text
    correction - the raw material ``group_line_fragments`` (PROMPT Phase
    3H, "Cluster D") groups into physical lines. ``raw_text`` is kept
    un-stripped: a trailing space is documentary evidence a fragment
    continues into its neighbour (see fragment_reconstruction.py).
    """
    raw = page.get_text("dict")
    fragments: list[RawLineFragment] = []
    for block in raw.get("blocks", []):
        if block.get("type") != 0:  # 0 = text block, 1 = image block
            continue
        for line in block.get("lines", []):
            spans = line.get("spans", [])
            if not spans:
                continue
            raw_text = "".join(span.get("text", "") for span in spans)
            if not raw_text.strip():
                continue
            fonts = tuple(span.get("font", "") for span in spans)
            is_monospace = bool(fonts) and all(
                any(hint in font.lower() for hint in _MONOSPACE_FONT_HINTS) for font in fonts
            )
            font_size = max((span.get("size", 0.0) for span in spans), default=0.0)
            x0, y0, x1, y1 = line["bbox"]
            fragments.append(
                RawLineFragment(
                    page_number=page_number,
                    x0=x0,
                    y0=y0,
                    x1=x1,
                    y1=y1,
                    raw_text=raw_text,
                    fonts=fonts,
                    font_size=font_size,
                    is_monospace=is_monospace,
                )
            )
    return fragments


def _build_line_from_group(
    page: pymupdf.Page, page_number: int, group: list[RawLineFragment]
) -> Line | None:
    """Build one corrected ``Line`` from a group of one or more raw
    fragments that ``group_line_fragments`` determined belong together.

    A singleton group takes exactly the same path this function's own
    predecessor (pre-Phase-3H ``_raw_lines``) always used - disabled
    behavior (a page with no fragmentation at all) is byte-identical. A
    multi-fragment group is corrected from its own *union* bbox, reusing
    the same ``reconstruct_line_text`` word-geometry mechanism a single
    line already relies on - it naturally re-derives the joined text from
    real word positions across the whole merged span, rather than
    re-stitching each fragment's own already-corrected text by hand.
    """
    first = group[0]
    is_monospace = first.is_monospace
    font_size = max(f.font_size for f in group)
    fonts = tuple(f for frag in group for f in frag.fonts)
    x0, y0, x1, y1 = merged_bbox_of(group)
    raw_text = (
        "".join(f.raw_text for f in group)
        if len(group) == 1
        else " ".join(f.raw_text.strip() for f in group)
    )
    text = raw_text.rstrip()
    if not text.strip():
        return None

    final_text = text.strip() if not is_monospace else text.lstrip("\f\v")
    corrections: list[SpacingCorrection] = []
    if not is_monospace:
        # Code lines keep their literal dict-mode text (word-geometry
        # reconstruction is prose-only; see spacing.py) - everything else
        # is re-derived from glyph geometry, which also happens to
        # normalize incidental whitespace differences (and, for a merged
        # group, the fragmentation itself) for free.
        reconstructed, corrections = reconstruct_line_text(page, page_number, (x0, y0, x1, y1))
        if reconstructed:
            final_text = reconstructed
    symbol_corrections: list[LabelCorrection] = []
    if not is_monospace and any(is_symbol_font(font) for font in fonts):
        substituted = substitute_symbol_font_text(final_text)
        if substituted != final_text:
            symbol_corrections.append(
                LabelCorrection(page_number=page_number, original=final_text, corrected=substituted)
            )
            final_text = substituted
    label_corrections: list[LabelCorrection] = []
    if not is_monospace:
        known_label = normalize_known_label(final_text)
        if known_label is not None:
            label_corrections.append(
                LabelCorrection(page_number=page_number, original=final_text, corrected=known_label)
            )
            final_text = known_label
    fragment_merges: tuple[FragmentMergeTrace, ...] = ()
    if len(group) > 1:
        fragment_merges = (
            FragmentMergeTrace(
                page_number=page_number,
                fragment_bboxes=tuple(f.bbox for f in group),
                fragment_texts=tuple(f.raw_text for f in group),
                merged_bbox=(x0, y0, x1, y1),
            ),
        )
    return Line(
        page_number=page_number,
        text=final_text,
        x0=x0,
        y0=y0,
        x1=x1,
        y1=y1,
        is_monospace=is_monospace,
        font_size=font_size,
        spacing_corrections=tuple(corrections),
        label_corrections=tuple(label_corrections),
        symbol_corrections=tuple(symbol_corrections),
        fragment_merges=fragment_merges,
    )


def _column_boundary_for_fragment_merge(fragments: list[RawLineFragment]) -> float | None:
    """This page's own right-column left edge, or None on a single-column
    page - see ``group_line_fragments``'s own docstring for why fragment
    merging must never cross it. Reuses ``detect_column_margins`` (the
    same mechanism ``extract_page_lines`` itself relies on for reading
    order) against lightweight, uncorrected ``Line`` stand-ins built
    straight from the raw fragments - column detection only ever inspects
    bbox/text, so an individual fragment's own missing corrections do not
    matter here, and most of a real page's own lines are not fragmented at
    all, leaving plenty of "substantial" evidence either way.
    """
    pseudo_lines = [
        Line(page_number=f.page_number, text=f.raw_text.strip(), x0=f.x0, y0=f.y0, x1=f.x1, y1=f.y1)
        for f in fragments
    ]
    margins = detect_column_margins(pseudo_lines)
    if margins is None:
        return None
    # Match extract_page_lines' own right-column membership test exactly
    # (right_margin - COLUMN_RIGHT_MARGIN_TOLERANCE, not the raw bucketed
    # margin) - detect_column_margins rounds to COLUMN_BUCKET_SIZE (5pt),
    # so the raw margin can sit fractionally past the right column's own
    # real content x0 (confirmed by direct instrumentation: 2021 p.19's
    # own right column starts at x0=289.465, bucketed to 290.0).
    _, right_margin = margins
    return right_margin - COLUMN_RIGHT_MARGIN_TOLERANCE


def _raw_lines(
    page: pymupdf.Page, page_number: int, fragment_reconstruction_gate: bool = False
) -> list[Line]:
    fragments = _collect_raw_fragments(page, page_number)
    if not fragment_reconstruction_gate:
        # Disabled (every booklet unless its own profile opts in - PROMPT
        # Phase 3H, see ExamStructureProfile.fragment_reconstruction_gate):
        # exactly one Line per raw dict-mode "line" entry, byte-identical
        # to every pre-Phase-3H run. A real, correct fix was confirmed to
        # fire against 2021's own already-published Q9 (page 19's own
        # documented "B Escalonamento por taxas monotonicas" split, see
        # layout.py's own MIN_LINES_PER_COLUMN docstring) - but *any*
        # change to a protected corpus is reverted regardless of
        # correctness (PROMPT: "nao aceite equivalencia semantica"), so
        # this stays gated the same way owner_exclusion_gate/
        # caption_font_size_gate/contextual_relation_gate already do.
        groups: list[list[RawLineFragment]] = [[f] for f in fragments]
    else:
        column_boundary = _column_boundary_for_fragment_merge(fragments)
        groups = group_line_fragments(fragments, column_boundary=column_boundary)
    lines: list[Line] = []
    for group in groups:
        built = _build_line_from_group(page, page_number, group)
        if built is not None:
            lines.append(built)
    return lines


def _line_column(ln: Line, margins: tuple[float, float] | None) -> int:
    """0 (left/single-column) or 1 (right), by closeness to the right margin.

    Mirrors the classification ``extract_page_lines`` uses for its own
    left/right split - see its docstring for why "closeness to the actual
    right-column margin" beats a midpoint split.
    """
    if margins is None:
        return 0
    _, right_margin = margins
    return 1 if ln.x0 >= right_margin - COLUMN_RIGHT_MARGIN_TOLERANCE else 0


#: Two different *general* (Level 1, PROMPT Phase 2B section 6) geometric
#: heuristics were tried here to exempt a genuine table-header cell (2011
#: unified booklet, Q22's "A B C D S" truth-table header) from
#: orphan-marker treatment, and both were rejected after full 2021 byte-diff
#: regression testing found real false positives: a bare-glyph-width check
#: also excluded the one genuine circled-marker case's near-neighbors, and
#: a "3+ short cells share this y0" row heuristic also matched three
#: independent binary-tree node labels (2021 Q23's own figure: "R", "L",
#: "A" happen to sit at the same y0 by diagram-layout coincidence, not
#: because they form a table row). Neither discriminator turned out to be
#: safe in general, so this case is instead handled by a narrow,
#: hash-and-bbox-locked override (see ``layout_overrides.py`` and
#: docs/decisions.md, Phase 2B ADR) applied only for the one PDF/page it
#: was written for - not a change to this general mechanism's own behavior.
def _is_orphan_marker(
    ln: Line, overrides: LayoutOverrideSet | None, pdf_sha256: str, page_number: int
) -> bool:
    if not _ORPHAN_MARKER_RE.match(ln.text):
        return False
    return overrides is None or not overrides.excludes_from_orphan_marker(
        pdf_sha256, page_number, ln.bbox
    )


def _merge_orphan_markers(
    lines: list[Line],
    margins: tuple[float, float] | None = None,
    overrides: LayoutOverrideSet | None = None,
    pdf_sha256: str = "",
) -> list[Line]:
    """Merge bare-letter marker lines into their nearest same-column partner line.

    Y-distance alone is not sufficient on a two-column page: a marker in
    one column can sit closer (in Y only) to unrelated text in the *other*
    column than to its own partner a few points below it (2011 unified
    booklet, Q10: alternative B's circled-letter marker at y0=344.4 merged
    with a left-column fragment "definida como" at y0=348.5 - only 4.1pt
    away - instead of its own denominator "155" at y0=352.0, 7.6pt away,
    because the old distance check never looked at X at all). Requiring the
    same column (when one is detected) closes that hole generally, not just
    for this one page.

    NOTE (PROMPT Phase 2C): a general (Level 1) second pass was tried here
    to also recover Q10's own stacked two-line fractions (each
    alternative's answer, e.g. "61/73", is set as a numerator line above
    the marker and a denominator line below - never one line with a slash
    - so the numerator was left behind as an orphan bare-number line for
    chrome.py's own running-page-number heuristic to strip). It searched,
    once a marker's primary partner was itself bare-digit, for a second
    bare-digit line on the opposite side within the same distance/column -
    and was rejected after full 2021 regression testing found a real
    false positive: 2021 Q34's own Dijkstra-graph node-label listing
    ("C 8 A 2 B 5 E 9 D 5" - five independent single-letter-node +
    single-digit-value pairs, densely packed) has several bare-digit
    values sitting within the same distance threshold of an unrelated
    *neighboring* marker's own value, which the second pass wrongly
    spliced into spurious fractions ("B 5/1", "D 9/5") while silently
    dropping node E's own pair entirely.

    PHASE 2D: rather than a general search heuristic (rejected above),
    ``overrides.fraction_merge_partner`` supplies an explicit,
    hash-and-bbox-locked (marker bbox -> numerator bbox) pair per
    alternative - five entries, declared once, matching only Q10's own 5
    markers on 2011's own exact PDF. No search, no distance heuristic, no
    possibility of matching a different document's own content: see
    layout_overrides.py.
    """
    used: set[int] = set()
    merged: list[Line] = []
    for i, ln in enumerate(lines):
        if i in used:
            continue
        if not _is_orphan_marker(ln, overrides, pdf_sha256, ln.page_number):
            merged.append(ln)
            continue
        ln_column = _line_column(ln, margins)
        # An override-declared fraction numerator (Phase 2D) is reserved
        # for the explicit merge below and must never win the general
        # distance search itself - real-world evidence (2011 Q10) shows
        # the numerator and denominator can sit within ~0.01pt of the same
        # distance from the marker, so whichever the search happens to
        # prefer is not reliable; walling the numerator off guarantees the
        # general search can only ever find the denominator.
        numerator_bbox = (
            overrides.fraction_merge_partner(pdf_sha256, ln.page_number, ln.bbox)
            if overrides is not None
            else None
        )
        best_j: int | None = None
        best_distance: float | None = None
        for j, other in enumerate(lines):
            if j == i or j in used or other.page_number != ln.page_number:
                continue
            if _is_orphan_marker(other, overrides, pdf_sha256, other.page_number):
                continue
            if _line_column(other, margins) != ln_column:
                continue
            if numerator_bbox is not None and other.bbox == numerator_bbox:
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
        partner_text = other.text
        merge_x0, merge_y0 = min(ln.x0, other.x0), min(ln.y0, other.y0)
        merge_x1, merge_y1 = max(ln.x1, other.x1), max(ln.y1, other.y1)
        fragment_merges = ln.fragment_merges + other.fragment_merges

        if numerator_bbox is not None:
            numerator_j = next(
                (
                    k
                    for k, candidate in enumerate(lines)
                    if k not in used and candidate.bbox == numerator_bbox
                ),
                None,
            )
            if numerator_j is not None:
                numerator = lines[numerator_j]
                used.add(numerator_j)
                partner_text = f"{numerator.text}/{other.text}"
                merge_x0, merge_y0 = min(merge_x0, numerator.x0), min(merge_y0, numerator.y0)
                merge_x1, merge_y1 = max(merge_x1, numerator.x1), max(merge_y1, numerator.y1)
                fragment_merges = fragment_merges + numerator.fragment_merges

        merged.append(
            Line(
                page_number=ln.page_number,
                text=f"{ln.text.rstrip(chr(9))}\t{partner_text}",
                x0=merge_x0,
                y0=merge_y0,
                x1=merge_x1,
                y1=merge_y1,
                is_monospace=other.is_monospace,
                font_size=max(ln.font_size, other.font_size),
                spacing_corrections=ln.spacing_corrections + other.spacing_corrections,
                label_corrections=ln.label_corrections + other.label_corrections,
                symbol_corrections=ln.symbol_corrections + other.symbol_corrections,
                fragment_merges=fragment_merges,
            )
        )
    return merged


def detect_column_margins(lines: list[Line]) -> tuple[float, float] | None:
    """Return (left_margin, right_margin) if ``lines`` show a genuine two-column layout.

    ``right_margin`` is the right column's own detected left edge (not a
    midpoint) - see ``extract_page_lines``, which classifies a line as
    "right column" by closeness to this actual margin rather than by
    which side of some arbitrary midpoint it falls on.

    Candidate margins are split into a left/right cluster at the single
    largest gap between consecutive sorted x0 buckets - not by taking the
    two buckets with the highest raw line counts. A column can legitimately
    have more than one recurring indentation level (e.g. a paragraph margin
    and a more-indented list-item margin both clearing
    ``MIN_LINES_PER_COLUMN``); picking "top 2 by frequency" can then select
    two buckets that both belong to the *same* physical column, which
    either fails ``MIN_COLUMN_SEPARATION`` outright or - worse - returns a
    ``right_margin`` that does not match where the right column's own
    heading/marker lines actually start, silently misclassifying them as
    left-column content (2011 unified booklet, pages 5/16/21/30: a
    two-per-page objective layout where this previously left the left
    question's own body text attributed to the following right-column
    question - found via ``detect_question_boundaries`` producing
    suspicious 1-line spans immediately followed by an oversized sibling).

    Chrome lines (running header/footer, "rascunho" ruler, barcode caption)
    are excluded from the evidence pool entirely, not just from the final
    line count: every content page repeats the same header at the same
    left margin regardless of whether the *body* below it is one or two
    columns, so counting it as column evidence can manufacture a false
    left-column margin out of page furniture (2011 page 18 / Discursiva 3:
    the header's 2 substantial-width lines plus a genuinely single-column
    paragraph's own 2 lines, both at the page's left margin, combined to
    reach the qualifying threshold and paired against one legitimately
    *indented* paragraph - wrapping around the recurrence-formula figure -
    misread as a second column, reordering the two paragraphs).

    Finally, the two candidate buckets must have *overlapping* Y-ranges
    before being accepted as genuine parallel columns. Real two-column
    content (e.g. Q9 left / Q10 right, both starting near the same y0) runs
    side by side, so their Y-ranges always share some span. A single-column
    page that merely contains an indented block - a centered quote, a poem,
    a highlighted excerpt - sits entirely *before* or entirely *after* the
    body-margin text in Y, never beside it. Without this check, such a
    block is misread as a second "column" and the whole block gets sorted
    to the end of the page's own line sequence, after even the footer
    chrome (2011 unified booklet, Questao 1's indented poem on page 2, and
    Discursiva 4's indented epigraph on page 19 - both zero-overlap blocks
    entirely above their page's body paragraph, both reordered to the very
    end of the page before this check existed).
    """
    substantial = [
        ln
        for ln in lines
        if (ln.x1 - ln.x0) >= MIN_COLUMN_LINE_WIDTH and not is_chrome_line(ln.text)
    ]
    if len(substantial) < 2 * MIN_LINES_PER_COLUMN:
        return None

    buckets = Counter(round(ln.x0 / COLUMN_BUCKET_SIZE) * COLUMN_BUCKET_SIZE for ln in substantial)
    common = sorted(x for x, count in buckets.items() if count >= MIN_LINES_PER_COLUMN)
    if len(common) < 2:
        return None

    gaps = [(common[i + 1] - common[i], i) for i in range(len(common) - 1)]
    widest_gap, split_index = max(gaps)
    if widest_gap < MIN_COLUMN_SEPARATION:
        return None

    left_margin = common[0]
    right_margin = common[split_index + 1]

    left_buckets = set(common[: split_index + 1])
    right_buckets = set(common[split_index + 1 :])
    left_lines = [
        ln
        for ln in substantial
        if round(ln.x0 / COLUMN_BUCKET_SIZE) * COLUMN_BUCKET_SIZE in left_buckets
    ]
    right_lines = [
        ln
        for ln in substantial
        if round(ln.x0 / COLUMN_BUCKET_SIZE) * COLUMN_BUCKET_SIZE in right_buckets
    ]
    left_y_top = min(ln.y0 for ln in left_lines)
    left_y_bottom = max(ln.y1 for ln in left_lines)
    right_y_top = min(ln.y0 for ln in right_lines)
    right_y_bottom = max(ln.y1 for ln in right_lines)
    if min(left_y_bottom, right_y_bottom) <= max(left_y_top, right_y_top):
        return None

    left_height = left_y_bottom - left_y_top
    right_height = right_y_bottom - right_y_top
    body_font_size = _page_dominant_body_font_size(substantial)
    if _is_short_off_size_column(
        left_lines, left_height, right_height, body_font_size
    ) or _is_short_off_size_column(right_lines, right_height, left_height, body_font_size):
        return None

    return left_margin, right_margin


def extract_page_lines(
    page: pymupdf.Page,
    page_number: int,
    overrides: LayoutOverrideSet | None = None,
    pdf_sha256: str = "",
    fragment_reconstruction_gate: bool = False,
) -> list[Line]:
    """Extract every physical line on ``page``, in visual reading order.

    Single-column pages: sorted by (y0, x0). Two-column pages (detected via
    :func:`detect_column_margins`): every left-column line (top to
    bottom), then every right-column line (top to bottom) - see module
    docstring.

    ``overrides``/``pdf_sha256`` (PROMPT Phase 2B section 6, Level 3) apply
    to the orphan-marker merge below, and can also force naive single-
    column ordering for the whole page - see ``layout_overrides.py``.

    ``fragment_reconstruction_gate`` (PROMPT Phase 3H, "Cluster D", default
    False): opt-in geometric rejoining of a physical line PyMuPDF's own
    dict-mode reported as several separate "line" entries - see
    ``_raw_lines``/``fragment_reconstruction.py``. Threaded from
    ``ExamStructureProfile.fragment_reconstruction_gate`` by
    ``pipeline.py`` - every booklet without it keeps the exact original,
    unfragmented-or-not-reconstructed behavior (confirmed: this mechanism
    DOES fix a real, previously-documented defect in 2021's own corpus -
    see the "B Escalonamento" comment below - but is gated regardless,
    since any change to a protected corpus is reverted on principle, not
    just when it is wrong).
    """
    raw = _raw_lines(page, page_number, fragment_reconstruction_gate)
    if overrides is not None and overrides.forces_single_column(pdf_sha256, page_number):
        lines = _merge_orphan_markers(raw, None, overrides, pdf_sha256)
        lines.sort(key=lambda ln: (round(ln.y0, 1), ln.x0))
        return lines
    # Column margins are detected on the *raw* (pre-merge) lines and reused
    # for the orphan-marker merge below, rather than recomputed after
    # merging: an orphan marker line is far under MIN_COLUMN_LINE_WIDTH and
    # never counts as "substantial" evidence either way, so this is the
    # same geometry either order - but computing it once, first, is what
    # lets the merge itself be column-aware (see `_merge_orphan_markers`).
    margins = detect_column_margins(raw)
    lines = _merge_orphan_markers(raw, margins, overrides, pdf_sha256)

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


def extract_document_lines(
    doc: pymupdf.Document,
    overrides: LayoutOverrideSet | None = None,
    pdf_sha256: str = "",
    fragment_reconstruction_gate: bool = False,
) -> list[Line]:
    """Extract position-sorted lines for every page, in page order."""
    all_lines: list[Line] = []
    for index in range(doc.page_count):
        page = doc[index]
        all_lines.extend(
            extract_page_lines(
                page,
                page_number=index + 1,
                overrides=overrides,
                pdf_sha256=pdf_sha256,
                fragment_reconstruction_gate=fragment_reconstruction_gate,
            )
        )
    return all_lines
