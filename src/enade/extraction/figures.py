"""Detect visual regions (figures/diagrams/charts/tables) on a page.

Approach validated empirically against the 2021 Ciencia da Computacao
booklet (see docs/corpus.md): every page carries a small set of *recurring*
vector-drawing rectangles (the border box, the rule under "QUESTAO N", the
footer line, ...) at near-identical coordinates. Those are booklet
decoration, not question content, and are computed as a "decorative
baseline" from the whole document. Any drawing or embedded image on a page
that does *not* match the baseline is real content; nearby content rects
are merged (by vertical proximity) into one candidate crop region per
visual cluster, since a single figure is very often built from many small
vector paths (e.g. a tree diagram's circles + arrows) rather than one.

This directly replaces relying on `page.get_images()` alone (PROMPT section
12: "Nao confie apenas em 'extract embedded images'") - most figures in
this booklet are vector graphics with zero embedded raster images.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

import pymupdf

from enade.extraction.chrome import is_chrome_line
from enade.extraction.layout import Line, detect_column_margins, extract_page_lines
from enade.extraction.layout_overrides import LayoutOverrideSet

Rect = tuple[float, float, float, float]

#: Vertical gap (points) within which two content rects are merged into one cluster.
DEFAULT_Y_MERGE_TOLERANCE = 18.0
#: A cluster smaller than this (points) in either dimension is discarded as noise
#: (e.g. a bold-text underline rendered as a thin filled rectangle).
MIN_REGION_WIDTH = 40.0
MIN_REGION_HEIGHT = 20.0
#: A rect recurring on at least this fraction of pages is considered decorative.
DECORATIVE_PAGE_FRACTION = 0.5
#: Coordinates are rounded to this many points before fingerprinting, so that
#: sub-pixel rendering differences don't defeat the recurrence match.
COORD_ROUNDING = 1
#: Vertical padding (points) used when testing whether a text line "touches"
#: a region's bbox for the label-absorption pass below. Generous enough to
#: catch a diagram's own row/axis labels sitting a little apart from its
#: vector paths (observed up to ~85pt for this booklet's mutex diagram),
#: but growth is hard-stopped well before it could plausibly reach the
#: next question's content - see ``_expand_with_labels``.
TEXT_ABSORPTION_PADDING = 90.0
#: Horizontal padding (points) for the same touch test - deliberately much
#: tighter than the vertical padding. A genuine figure annotation (axis
#: label, row header, arrow caption) sits close against the diagram's own
#: left/right edge; a generous horizontal padding was observed to let
#: absorption "walk" sideways-and-up/down through a chain of short,
#: page-margin-aligned lines that are actually paragraph tail-wraps or
#: section headings (e.g. a lone "TEXTO II" heading, or a paragraph's
#: last short line), not figure content - on Questao 3's page, this chain
#: swallowed the entire surrounding TEXTO I/II passage and two full
#: enumerated statement items into the figure region, silently deleting
#: them from the rendered Markdown (Phase 1B regression audit finding; see
#: docs/decisions.md). Body paragraph lines are already excluded from
#: ``label_candidates`` by ``MAX_LABEL_LINE_WIDTH``, but that alone does
#: not stop absorption from reaching *past* them to a further, narrower
#: line that is itself unrelated to the figure.
TEXT_ABSORPTION_X_PADDING = 20.0
#: Lines wider than this (points) are treated as body prose, never a figure
#: label/annotation, and are never absorbed into a region's bbox - this is
#: what stops an adjacent full-width paragraph from being swallowed by a
#: nearby diagram.
MAX_LABEL_LINE_WIDTH = 300.0
#: A monospace (code/pseudocode) line is individually narrow enough to pass
#: ``MAX_LABEL_LINE_WIDTH`` but is never a figure label/annotation. On a
#: two-column page where a diagram sits in the left column and a code
#: listing sits in the right column at an overlapping Y-range (D5, page 17
#: - see docs/decisions.md, "Phase 1C" ADR), individual code lines like
#: "void heapify (int *a, int n, int i)" were being absorbed into the
#: diagram's region across the column gutter, growing its bbox ~110pt into
#: the code column (hitting ``MAX_ABSORPTION_GROWTH``) and causing
#: ``_line_in_region`` (assembler.py) to silently drop most of the
#: heapify() function body as if it were "inside the figure". Excluding
#: monospace lines from ``label_candidates`` entirely is the general fix:
#: code is its own content class (PROMPT Phase 1C section 7.2), never a
#: diagram annotation, regardless of which column it happens to share a
#: Y-range with.
#: Safety cap on label-absorption growth iterations (each pass can only add
#: lines, so this always terminates well before the cap in practice).
MAX_ABSORPTION_PASSES = 8
#: Hard cap on how far a region may grow beyond its original vector/image
#: bbox (points, per edge) during label absorption - a second, coarser
#: safety net behind the alternative-marker exclusion above (which is what
#: actually stops the chain reaction at its source: a marker line is never
#: a candidate to begin with, so growth can't walk past it). This cap only
#: needs to guard against a page with no alternatives at all somehow
#: chaining very far; it is intentionally generous so it never clips a
#: legitimate wide figure (observed: this booklet's widest figures need
#: ~90-140pt of growth beyond their vector-only bbox to include row/axis
#: labels sitting apart from the diagram body).
MAX_ABSORPTION_GROWTH = 110.0
#: A line matching this is an alternative marker (A-E) - absorbing one into
#: a figure region would corrupt alternative-boundary detection downstream,
#: so these are never absorbed regardless of distance.
_ALTERNATIVE_MARKER_RE = re.compile(r"^[A-E][\t ]")
#: Vertical gap (points) below which two consecutive lines on a page are
#: still considered the same paragraph/enumerated item, not a new one -
#: mirrors assembler.py's ``PARAGRAPH_GAP_THRESHOLD`` (kept as a separate
#: constant rather than imported, since assembler.py already imports from
#: this module - importing back would be circular).
_PARAGRAPH_CONTINUATION_GAP = 19.0
#: A wrapped continuation line shares its left edge with the rest of its
#: own paragraph almost exactly (line-wrapping does not re-indent). A
#: figure's own label sitting a little below an unrelated wide sentence
#: (e.g. "Em um sentido abstrato... e mostrado na figura a seguir.",
#: directly above Q17's diagram) is normally offset well to the right of
#: that sentence's margin, not flush with it - so requiring left-edge
#: alignment (not just vertical proximity) is what tells an actual
#: paragraph wrap apart from a same-page-but-unrelated label (Phase 1B
#: audit finding: an early version without this check clipped Q17's first
#: diagram label, see docs/decisions.md).
_PARAGRAPH_CONTINUATION_X_TOLERANCE = 5.0
#: A line matching this is a "QUESTAO [DISCURSIVA] N" heading. It sits just
#: above a question's content and is not itself a figure label - absorbing
#: it was observed to pull a region's top edge all the way up to the page
#: header (e.g. Q34's graph region grew from y=185 to y=77, the marker
#: line's own position). That went unnoticed while the marker line was
#: still present elsewhere in the rendered statement (its own y0 kept the
#: page's content y-bound low enough to include the region); once the
#: marker line is stripped from the statement (see assembler.py,
#: ``_strip_leading_marker``), the same absorption excludes the region
#: entirely. The marker must never be absorbed in the first place.
_QUESTION_MARKER_RE = re.compile(r"(?i)^quest[aã]o\s+(discursiva\s+)?0*\d+\b")
#: Tolerance (points) for treating a candidate line's x0 as "flush with the
#: page's standard body-text margin" - see ``_dominant_left_margin``.
_MARGIN_TOLERANCE = 5.0


@dataclass(frozen=True)
class VisualRegion:
    """A candidate figure/diagram/table region on one page."""

    page_number: int
    bbox: Rect
    element_count: int  # number of raw drawings/images merged into this region
    has_raster_image: bool = False  # True if a real embedded image contributed to this region


def _round_rect(rect: Rect) -> tuple[int, int, int, int]:
    return tuple(round(c / COORD_ROUNDING) * COORD_ROUNDING for c in rect)  # type: ignore[return-value]


def compute_decorative_baseline(doc: pymupdf.Document) -> frozenset[tuple[int, int, int, int]]:
    """Find drawing rects that recur across most pages - i.e. booklet decoration."""
    page_count = doc.page_count
    counts: dict[tuple[int, int, int, int], int] = {}
    for index in range(page_count):
        page = doc[index]
        seen_this_page: set[tuple[int, int, int, int]] = set()
        for drawing in page.get_drawings():
            rect = drawing.get("rect")
            if rect is None or rect.is_empty:
                continue
            seen_this_page.add(_round_rect((rect.x0, rect.y0, rect.x1, rect.y1)))
        for key in seen_this_page:
            counts[key] = counts.get(key, 0) + 1

    threshold = max(2, int(page_count * DECORATIVE_PAGE_FRACTION))
    return frozenset(key for key, count in counts.items() if count >= threshold)


def _merge_by_vertical_proximity(
    rects: list[tuple[Rect, bool]], y_tolerance: float
) -> list[tuple[Rect, int, bool]]:
    """Sweep-line merge of (rect, is_image) into vertically-clustered groups."""
    ordered = sorted(rects, key=lambda item: item[0][1])
    merged: list[list[float]] = []
    counts: list[int] = []
    has_image: list[bool] = []
    for rect, is_image in ordered:
        if merged and rect[1] <= merged[-1][3] + y_tolerance:
            merged[-1][0] = min(merged[-1][0], rect[0])
            merged[-1][1] = min(merged[-1][1], rect[1])
            merged[-1][2] = max(merged[-1][2], rect[2])
            merged[-1][3] = max(merged[-1][3], rect[3])
            counts[-1] += 1
            has_image[-1] = has_image[-1] or is_image
        else:
            merged.append(list(rect))
            counts.append(1)
            has_image.append(is_image)
    return [
        ((m[0], m[1], m[2], m[3]), c, h) for m, c, h in zip(merged, counts, has_image, strict=True)
    ]


def _rects_touch(a: Rect, b: Rect, y_padding: float, x_padding: float = 0.0) -> bool:
    return not (
        a[2] + x_padding < b[0]
        or b[2] + x_padding < a[0]
        or a[3] + y_padding < b[1]
        or b[3] + y_padding < a[1]
    )


#: A computed margin is only trusted if at least this many wide lines agree
#: on it - a single wide line (e.g. one bibliographic citation, which in
#: this corpus is often indented very differently from body prose) is not
#: reliable evidence of "the page's standard margin" on its own. Without
#: this, a page whose only wide line is such a citation (e.g. Q2's page,
#: whose entire content is one full-bleed image plus a two-line citation)
#: computed a bogus margin from that citation's own x0, which then made the
#: real "QUESTAO 02" marker line - genuinely flush with the true margin -
#: look "far from the margin" and therefore eligible for absorption,
#: pulling a figure region's bbox out of the question's own content
#: y-bounds and silently dropping the asset entirely (Phase 1B audit
#: finding, see docs/decisions.md).
_MIN_MARGIN_AGREEMENT = 2


def _dominant_left_margin(lines: list[Line]) -> float | None:
    """Most common left edge (x0) among wide (body-prose) lines on the page
    - i.e. the page's standard text margin - or None if there isn't enough
    agreement to trust one (see ``_MIN_MARGIN_AGREEMENT``).

    Used to tell a genuine alternative/question marker (observed to always
    be flush with this margin in this corpus - e.g. every real "A"/"B"/...
    alternative on Q1's page starts at x0=29.8, matching the page's own
    body-prose margin exactly) apart from a diagram label that merely
    starts with a bare letter A-E followed by a space (e.g. "A entra na
    regiao critica", "B tenta entrar..." - Q17's mutex-diagram labels,
    Phase 1B audit finding: an early absorption fix clipped this exact
    label by wrongly treating it as an alternative marker, see
    docs/decisions.md).
    """
    wide = [ln for ln in lines if (ln.x1 - ln.x0) > MAX_LABEL_LINE_WIDTH]
    if not wide:
        return None
    x0, count = Counter(round(ln.x0) for ln in wide).most_common(1)[0]
    if count < _MIN_MARGIN_AGREEMENT:
        return None
    return float(x0)


def _is_marker_at_margin(text: str, x0: float, body_margin_x0: float | None) -> bool:
    """True if ``text`` looks like an alternative/question marker *and* sits
    at the page's standard body-text margin - see ``_dominant_left_margin``.
    A marker-shaped line far from that margin is almost certainly something
    else (e.g. a diagram's own label) and must not be excluded from
    absorption just because of a coincidental textual shape.
    """
    if not (_ALTERNATIVE_MARKER_RE.match(text) or _QUESTION_MARKER_RE.match(text)):
        return False
    if body_margin_x0 is None:
        return True
    return abs(x0 - body_margin_x0) <= _MARGIN_TOLERANCE


def _expand_with_labels(
    bbox: Rect, label_candidates: list[tuple[Rect, str]], body_margin_x0: float | None = None
) -> Rect:
    """Grow ``bbox`` to also cover nearby short text lines (axis labels,
    arrow annotations, row headers, ...) that vector-path detection alone
    misses, so a rendered crop doesn't clip them (see docs/decisions.md).

    Two safeguards keep this from cascading into unrelated content (observed
    empirically: without them, a tree diagram's region grew until it
    swallowed all five alternatives below it on the same page):

    1. A line matching the alternative-marker pattern (``A\\t...``) *and*
       sitting at the page's standard body-text margin is never absorbed,
       regardless of distance - alternatives belong to the statement/answer
       flow, never to a figure (see ``_is_marker_at_margin``).
    2. Growth is capped at ``MAX_ABSORPTION_GROWTH`` points beyond the
       original bbox on each edge.
    """
    original = bbox
    min_x = original[0] - MAX_ABSORPTION_GROWTH
    min_y = original[1] - MAX_ABSORPTION_GROWTH
    max_x = original[2] + MAX_ABSORPTION_GROWTH
    max_y = original[3] + MAX_ABSORPTION_GROWTH

    current = bbox
    remaining = [
        (rect, text)
        for rect, text in label_candidates
        if not _is_marker_at_margin(text, rect[0], body_margin_x0)
    ]
    for _ in range(MAX_ABSORPTION_PASSES):
        absorbed_any = False
        still_remaining = []
        for rect, text in remaining:
            if _rects_touch(current, rect, TEXT_ABSORPTION_PADDING, TEXT_ABSORPTION_X_PADDING):
                candidate = (
                    max(min_x, min(current[0], rect[0])),
                    max(min_y, min(current[1], rect[1])),
                    min(max_x, max(current[2], rect[2])),
                    min(max_y, max(current[3], rect[3])),
                )
                if candidate != current:
                    current = candidate
                    absorbed_any = True
            else:
                still_remaining.append((rect, text))
        remaining = still_remaining
        if not absorbed_any:
            break
    return current


def _region_contains(outer: Rect, inner: Rect, tolerance: float = 5.0) -> bool:
    return (
        outer[0] - tolerance <= inner[0]
        and outer[1] - tolerance <= inner[1]
        and outer[2] + tolerance >= inner[2]
        and outer[3] + tolerance >= inner[3]
    )


#: Two regions whose y-ranges overlap by at least this fraction of the
#: shorter region's height are treated as fragments of the same visual
#: content and merged into their bounding union, rather than kept as
#: separate, overlapping/duplicate crops - one of the four known Phase 1A
#: asset bug patterns explicitly re-audited in Phase 1B (PROMPT section 9):
#: on Q28's page, "Figura 1" (pipeline stages) and "Figura 2" (the timing
#: table right below it) were detected as two separate vector-element
#: clusters that each grew via label-absorption until their bboxes
#: substantially overlapped, producing two crops that each showed a
#: different, incomplete slice of the combined content instead of one
#: crop showing both figures in full (see docs/decisions.md).
_SUBSTANTIAL_Y_OVERLAP_FRACTION = 0.3


def _y_overlap_fraction(a: Rect, b: Rect) -> float:
    """Fraction of the shorter region's height that overlaps the other, in y."""
    overlap = min(a[3], b[3]) - max(a[1], b[1])
    if overlap <= 0:
        return 0.0
    shorter_height = min(a[3] - a[1], b[3] - b[1])
    if shorter_height <= 0:
        return 0.0
    return overlap / shorter_height


def _merge_overlapping_regions(regions: list[VisualRegion]) -> list[VisualRegion]:
    """Merge any two same-page regions with substantial y-overlap into their
    bounding union - repeated to a fixed point, since a merge can create a
    new overlap with a third region.
    """
    current = list(regions)
    changed = True
    while changed:
        changed = False
        merged: list[VisualRegion] = []
        used: set[int] = set()
        for i, a in enumerate(current):
            if i in used:
                continue
            combined = a
            for j in range(i + 1, len(current)):
                if j in used or current[j].page_number != combined.page_number:
                    continue
                b = current[j]
                if _y_overlap_fraction(combined.bbox, b.bbox) >= _SUBSTANTIAL_Y_OVERLAP_FRACTION:
                    combined = VisualRegion(
                        page_number=combined.page_number,
                        bbox=(
                            min(combined.bbox[0], b.bbox[0]),
                            min(combined.bbox[1], b.bbox[1]),
                            max(combined.bbox[2], b.bbox[2]),
                            max(combined.bbox[3], b.bbox[3]),
                        ),
                        element_count=combined.element_count + b.element_count,
                        has_raster_image=combined.has_raster_image or b.has_raster_image,
                    )
                    used.add(j)
                    changed = True
            merged.append(combined)
        current = merged
    return current


def _deduplicate_overlapping_regions(regions: list[VisualRegion]) -> list[VisualRegion]:
    """Drop a region that is fully contained within another, larger one.

    Label absorption can expand what started as several distinct
    vertically-clustered vector groups (e.g. a DER diagram's boxes vs. its
    connecting lines/diamonds, initially split by the y-proximity merge)
    until their *expanded* bboxes end up overlapping or nesting entirely -
    observed on Q22, where this produced three near-duplicate crops of the
    same diagram at increasing sizes. Keeping only the largest of any nested
    group removes the duplicates without touching the y-proximity merge or
    the label-absorption growth logic those two pages actually rely on.
    """

    def area(region: VisualRegion) -> float:
        return (region.bbox[2] - region.bbox[0]) * (region.bbox[3] - region.bbox[1])

    ordered = sorted(regions, key=area, reverse=True)
    kept: list[VisualRegion] = []
    for region in ordered:
        if any(_region_contains(k.bbox, region.bbox) for k in kept):
            continue
        kept.append(region)
    return kept


def _is_paragraph_continuation(index: int, lines: list[Line]) -> bool:
    """True if ``lines[index]`` is very likely the wrapped tail of the
    preceding line's paragraph/enumerated statement item, even though its
    own width is narrow enough to otherwise qualify as a figure-label
    absorption candidate.

    A figure sitting between two paragraphs (or inside an enumerated list)
    can be wide enough to horizontally overlap the page's whole text
    column, so a horizontal-distance check alone cannot tell a genuine
    label apart from an ordinary short last-line-of-a-paragraph (e.g.
    "atividade fisica." wrapping off "...proporcionar a pratica de") -
    both can sit well within the figure's own x-range. Two purely
    geometric signals together identify a true wrap: the preceding line is
    *wide* (> MAX_LABEL_LINE_WIDTH, i.e. body prose, never a label) AND
    shares its left edge almost exactly (line-wrapping never re-indents) -
    the second check is what stops a figure's own label from being
    excluded just for sitting close below an unrelated wide sentence at a
    different x-position (PROMPT Phase 1B section 5/6 - Questao 3 and
    Questao 17 audit findings, see docs/decisions.md).
    """
    if index == 0:
        return False
    line = lines[index]
    previous = lines[index - 1]
    if previous.page_number != line.page_number:
        return False
    gap = line.y0 - previous.y1
    if gap > _PARAGRAPH_CONTINUATION_GAP:
        return False
    if abs(previous.x0 - line.x0) > _PARAGRAPH_CONTINUATION_X_TOLERANCE:
        return False
    return (previous.x1 - previous.x0) > MAX_LABEL_LINE_WIDTH


def _is_two_column_body_text(line: Line, column_margins: tuple[float, float] | None) -> bool:
    """True if ``line`` starts flush with a genuine two-column page's own
    left or right column margin (PROMPT Phase 1C section 7.2).

    ``MAX_LABEL_LINE_WIDTH`` (300pt) is calibrated against single-column
    body text (~500pt wide); on a real two-column page each column is only
    ~245pt wide (see docs/decisions.md, "Phase 1C" ADR - D5, page 17), so
    *every* prose line there - including a paragraph's very first line,
    which ``_is_paragraph_continuation`` cannot catch since it has no
    preceding line to compare against - looks "label-width" by that
    threshold alone and was being silently absorbed into an adjacent
    figure's region. ``column_margins`` (from
    ``layout.detect_column_margins``, the same detector that already
    orders two-column pages correctly) gives a second, independent
    geometric signal: real column body text recurs at one of exactly two
    stable left edges, which an isolated figure label never does.
    """
    if column_margins is None:
        return False
    left_margin, right_margin = column_margins
    return (
        abs(line.x0 - left_margin) <= _MARGIN_TOLERANCE
        or abs(line.x0 - right_margin) <= _MARGIN_TOLERANCE
    )


def detect_visual_regions(
    doc: pymupdf.Document,
    page_number: int,
    decorative_baseline: frozenset[tuple[int, int, int, int]],
    *,
    y_merge_tolerance: float = DEFAULT_Y_MERGE_TOLERANCE,
    overrides: LayoutOverrideSet | None = None,
    pdf_sha256: str = "",
) -> list[VisualRegion]:
    """Detect non-decorative visual content regions on one (1-indexed) page.

    ``overrides``/``pdf_sha256`` (PROMPT Phase 2B section 6, Level 3) drop
    any region already determined, by direct visual inspection, to be a
    false positive of the label-absorption chain-growth this function
    relies on (see ``layout_overrides.py`` and docs/decisions.md).
    """
    page = doc[page_number - 1]
    candidates: list[tuple[Rect, bool]] = []

    def _excluded(rect: tuple[float, float, float, float]) -> bool:
        return overrides is not None and overrides.excludes_from_region_candidates(
            pdf_sha256, page_number, rect
        )

    for drawing in page.get_drawings():
        rect = drawing.get("rect")
        if rect is None or rect.is_empty:
            continue
        key = _round_rect((rect.x0, rect.y0, rect.x1, rect.y1))
        if key in decorative_baseline:
            continue
        rect_tuple = (rect.x0, rect.y0, rect.x1, rect.y1)
        if _excluded(rect_tuple):
            continue
        candidates.append((rect_tuple, False))

    for image_info in page.get_image_info():
        bbox = image_info.get("bbox")
        if bbox and not _excluded(tuple(bbox)):
            candidates.append((tuple(bbox), True))

    if not candidates:
        return []

    page_lines = extract_page_lines(page, page_number)
    body_margin_x0 = _dominant_left_margin(page_lines)
    column_margins = detect_column_margins(page_lines)
    label_candidates = [
        ((ln.x0, ln.y0, ln.x1, ln.y1), ln.text)
        for i, ln in enumerate(page_lines)
        if (ln.x1 - ln.x0) <= MAX_LABEL_LINE_WIDTH
        and not ln.is_monospace
        and not is_chrome_line(ln.text)
        and not _is_paragraph_continuation(i, page_lines)
        and not _is_two_column_body_text(ln, column_margins)
        and not (
            overrides is not None
            and overrides.protects_from_label_absorption(
                pdf_sha256, page_number, (ln.x0, ln.y0, ln.x1, ln.y1)
            )
        )
    ]

    regions = []
    for bbox, count, has_image in _merge_by_vertical_proximity(candidates, y_merge_tolerance):
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        if width < MIN_REGION_WIDTH or height < MIN_REGION_HEIGHT:
            continue
        expanded_bbox = _expand_with_labels(bbox, label_candidates, body_margin_x0)
        if overrides is not None and overrides.suppresses_region(
            pdf_sha256, page_number, expanded_bbox
        ):
            continue
        regions.append(
            VisualRegion(
                page_number=page_number,
                bbox=expanded_bbox,
                element_count=count,
                has_raster_image=has_image,
            )
        )
    return _deduplicate_overlapping_regions(_merge_overlapping_regions(regions))
