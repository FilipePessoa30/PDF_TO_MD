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
from dataclasses import dataclass

import pymupdf

from enade.extraction.chrome import is_chrome_line
from enade.extraction.layout import extract_page_lines

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
#: Padding (points) used when testing whether a text line "touches" a
#: region's bbox for the label-absorption pass below. Generous enough to
#: catch a diagram's own row/axis labels sitting a little apart from its
#: vector paths (observed up to ~85pt for this booklet's mutex diagram),
#: but growth is hard-stopped well before it could plausibly reach the
#: next question's content - see ``_expand_with_labels``.
TEXT_ABSORPTION_PADDING = 90.0
#: Lines wider than this (points) are treated as body prose, never a figure
#: label/annotation, and are never absorbed into a region's bbox - this is
#: what stops an adjacent full-width paragraph from being swallowed by a
#: nearby diagram.
MAX_LABEL_LINE_WIDTH = 300.0
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


def _rects_touch(a: Rect, b: Rect, padding: float) -> bool:
    return not (
        a[2] + padding < b[0]
        or b[2] + padding < a[0]
        or a[3] + padding < b[1]
        or b[3] + padding < a[1]
    )


def _expand_with_labels(bbox: Rect, label_candidates: list[tuple[Rect, str]]) -> Rect:
    """Grow ``bbox`` to also cover nearby short text lines (axis labels,
    arrow annotations, row headers, ...) that vector-path detection alone
    misses, so a rendered crop doesn't clip them (see docs/decisions.md).

    Two safeguards keep this from cascading into unrelated content (observed
    empirically: without them, a tree diagram's region grew until it
    swallowed all five alternatives below it on the same page):

    1. A line matching the alternative-marker pattern (``A\\t...``) is never
       absorbed, regardless of distance - alternatives belong to the
       statement/answer flow, never to a figure.
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
        if not _ALTERNATIVE_MARKER_RE.match(text) and not _QUESTION_MARKER_RE.match(text)
    ]
    for _ in range(MAX_ABSORPTION_PASSES):
        absorbed_any = False
        still_remaining = []
        for rect, text in remaining:
            if _rects_touch(current, rect, TEXT_ABSORPTION_PADDING):
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


def detect_visual_regions(
    doc: pymupdf.Document,
    page_number: int,
    decorative_baseline: frozenset[tuple[int, int, int, int]],
    *,
    y_merge_tolerance: float = DEFAULT_Y_MERGE_TOLERANCE,
) -> list[VisualRegion]:
    """Detect non-decorative visual content regions on one (1-indexed) page."""
    page = doc[page_number - 1]
    candidates: list[tuple[Rect, bool]] = []

    for drawing in page.get_drawings():
        rect = drawing.get("rect")
        if rect is None or rect.is_empty:
            continue
        key = _round_rect((rect.x0, rect.y0, rect.x1, rect.y1))
        if key in decorative_baseline:
            continue
        candidates.append(((rect.x0, rect.y0, rect.x1, rect.y1), False))

    for image_info in page.get_image_info():
        bbox = image_info.get("bbox")
        if bbox:
            candidates.append((tuple(bbox), True))

    if not candidates:
        return []

    label_candidates = [
        ((ln.x0, ln.y0, ln.x1, ln.y1), ln.text)
        for ln in extract_page_lines(page, page_number)
        if (ln.x1 - ln.x0) <= MAX_LABEL_LINE_WIDTH and not is_chrome_line(ln.text)
    ]

    regions = []
    for bbox, count, has_image in _merge_by_vertical_proximity(candidates, y_merge_tolerance):
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        if width < MIN_REGION_WIDTH or height < MIN_REGION_HEIGHT:
            continue
        expanded_bbox = _expand_with_labels(bbox, label_candidates)
        regions.append(
            VisualRegion(
                page_number=page_number,
                bbox=expanded_bbox,
                element_count=count,
                has_raster_image=has_image,
            )
        )
    return _deduplicate_overlapping_regions(regions)
