"""Spatial ownership of page content, by question (PROMPT Phase 2C, section
6-11).

**Problem this module exists to fix**: a candidate visual region (built from
nearby drawings/images and grown by label absorption - see figures.py) was
previously accepted by *any* question whose own text happened to sit close
enough, with no concept of "whose content is this really". On a page with
several questions sharing a column, this let one question's own region grow
across into - and get attached to - a completely different, sometimes
non-adjacent question (2011 unified booklet: Questao 25's own crop
contained the whole of Questao 24's roman-numeral items plus Questao 26's
own card image; Questao 40's own crop contained Questao 38's own missing
LR-automaton states - see docs/decisions.md, Phase 2C ADR).

**Fix**: before any region is grown or rendered, it is assigned an *owner*
- the one question whose own claimed territory (``QuestionRegion``, the
tight bbox of that question's own non-chrome lines on that page) contains
or is nearest to the region's seed. Growth and final rendering are then
clipped to the owner's own territory (plus a small, fixed safety margin -
never the old, generous ``MAX_ABSORPTION_GROWTH``), so a region literally
cannot expand into a neighboring question's own space regardless of how
close/absorbable its own labels look.

Ownership is derived only from each question's own lines - never guessed
from a neighbor's boundary, never a heuristic distance split down the
middle of the gap between two questions.
"""

from __future__ import annotations

from dataclasses import dataclass

from enade.extraction.boundaries import QuestionKind, QuestionSpan
from enade.extraction.chrome import is_chrome_line
from enade.extraction.layout import Line

Rect = tuple[float, float, float, float]

#: Safety margin (points) a region may extend beyond its owner's own claimed
#: bbox - deliberately small and fixed, unlike the old, generous
#: MAX_ABSORPTION_GROWTH (110pt): real figure content (a diagram's own
#: outermost path, an axis label sitting just past the last text line) sits
#: within a few points of the owning question's own text, while a
#: neighboring question in this corpus is always tens to hundreds of points
#: further away - see docs/decisions.md, Phase 2C ADR (ownership model).
OWNERSHIP_MARGIN = 20.0
#: Horizontal tolerance (points) used when deciding whether a point "belongs
#: to the same column" as a QuestionRegion, for nearest-owner fallback.
_COLUMN_TOLERANCE = 20.0


def question_key(span: QuestionSpan) -> str:
    """Stable, document-local identifier for a span - not the final
    ``question_id`` (that depends on year/course/shorthand, resolved later
    in pipeline.py), just enough to tell "same span" from "different span"
    within one ownership computation.
    """
    return f"{span.kind.value}-{span.number}"


@dataclass(frozen=True)
class QuestionRegion:
    """One question's own claimed rectangle on one page: the tight bbox of
    its own non-chrome lines on that page, nothing more, nothing guessed.
    """

    question_key: str
    page_number: int
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def bbox(self) -> Rect:
        return (self.x0, self.y0, self.x1, self.y1)

    def clip(self, rect: Rect, margin: float = OWNERSHIP_MARGIN) -> Rect:
        """Clamp ``rect`` to this region's own bbox, expanded by ``margin`` -
        the hard limit that keeps a grown region from ever reaching into a
        different question's own territory.
        """
        return (
            max(rect[0], self.x0 - margin),
            max(rect[1], self.y0 - margin),
            min(rect[2], self.x1 + margin),
            min(rect[3], self.y1 + margin),
        )


def render_bounds_for_owner(
    owner: QuestionRegion | None, column_margins: tuple[float, float] | None
) -> tuple[float, float] | None:
    """The safe x-range a rendered crop may widen into, for one owner.

    Shared by every asset-rendering call site that needs to cap
    ``assets.py``'s own page-content-width widening (PROMPT Phase 2D
    section 11, Phase 2E section 7): ``figures.py``'s two ``VisualRegion``
    construction sites, and ``pipeline.py``'s own table-asset render call
    (``DetectedTable`` has no owner of its own - unlike ``VisualRegion``,
    it is built directly from one question's own already-scoped
    ``span.lines``, see ``tables.py``/``assembler.py`` - so the owner is
    supplied by the caller instead of looked up by bbox center).

    ``None`` when no owner is known, or the page is not a genuine
    two-column layout (``column_margins`` is ``None``) - single-column
    pages never need this cap, since a full-width asset's own drawn
    extent can legitimately exceed its owning question's own *text*
    bbox (e.g. Questao 17's own circuit diagram).
    """
    if owner is None or column_margins is None:
        return None
    return (owner.x0 - OWNERSHIP_MARGIN, owner.x1 + OWNERSHIP_MARGIN)


def compute_question_regions(
    spans: list[QuestionSpan],
) -> dict[int, list[QuestionRegion]]:
    """One ``QuestionRegion`` per (span, page) it touches.

    Returns ``page_number -> list of QuestionRegion``, sorted by ``y0``
    (matches this corpus's own reading order within a page - left column
    top-to-bottom, then right column top-to-bottom - since ``span.lines``
    is itself a sub-sequence of the whole document's position-sorted line
    list; see layout.py).
    """
    by_page: dict[int, list[QuestionRegion]] = {}
    for span in spans:
        content_lines = [ln for ln in span.lines if not is_chrome_line(ln.text)]
        pages: dict[int, list[Line]] = {}
        for ln in content_lines:
            pages.setdefault(ln.page_number, []).append(ln)
        key = question_key(span)
        for page_number, lines in pages.items():
            by_page.setdefault(page_number, []).append(
                QuestionRegion(
                    question_key=key,
                    page_number=page_number,
                    x0=min(ln.x0 for ln in lines),
                    y0=min(ln.y0 for ln in lines),
                    x1=max(ln.x1 for ln in lines),
                    y1=max(ln.y1 for ln in lines),
                )
            )
    for regions in by_page.values():
        regions.sort(key=lambda r: r.y0)
    return by_page


def find_owner(regions: list[QuestionRegion], x: float, y: float) -> QuestionRegion | None:
    """The ``QuestionRegion`` that owns the point ``(x, y)``.

    Containment wins outright. When no region contains the point (a figure
    candidate often sits in the whitespace gap between two of its owner's
    own lines, technically outside the tight line-bbox), fall back to the
    nearest region *in the same column* - a point in the left column must
    never be treated as nearer to a right-column question just because that
    question's own Y-range happens to be numerically closer.
    """
    if not regions:
        return None
    containing = [r for r in regions if r.x0 <= x <= r.x1 and r.y0 <= y <= r.y1]
    if containing:
        return min(containing, key=lambda r: r.y1 - r.y0)
    same_column = [r for r in regions if r.x0 - _COLUMN_TOLERANCE <= x <= r.x1 + _COLUMN_TOLERANCE]
    candidates = same_column or regions
    return min(candidates, key=lambda r: min(abs(y - r.y0), abs(y - r.y1)))


@dataclass(frozen=True)
class ContaminationFinding:
    """One asset whose final bbox reaches into a question other than its
    own owner - the Section 10 gate's output shape.
    """

    owner_question_key: str
    intersecting_question_key: str
    asset_bbox: Rect
    intersection_area: float
    reason: str


def _intersection_area(a: Rect, b: Rect) -> float:
    x0 = max(a[0], b[0])
    y0 = max(a[1], b[1])
    x1 = min(a[2], b[2])
    y1 = min(a[3], b[3])
    if x1 <= x0 or y1 <= y0:
        return 0.0
    return (x1 - x0) * (y1 - y0)


def detect_contamination(
    owner_key: str,
    asset_bbox: Rect,
    page_regions: list[QuestionRegion],
    *,
    min_intersection_area: float = 25.0,
) -> list[ContaminationFinding]:
    """Section 10 gate: does ``asset_bbox`` (already attributed to
    ``owner_key``) reach into any *other* question's own claimed territory
    on this page, beyond a token amount of overlap?

    Geometry-only, never OCR of the rendered PNG - the same ``QuestionRegion``
    bboxes ownership itself is computed from.
    """
    findings: list[ContaminationFinding] = []
    for region in page_regions:
        if region.question_key == owner_key:
            continue
        area = _intersection_area(asset_bbox, region.bbox)
        if area >= min_intersection_area:
            findings.append(
                ContaminationFinding(
                    owner_question_key=owner_key,
                    intersecting_question_key=region.question_key,
                    asset_bbox=asset_bbox,
                    intersection_area=area,
                    reason=(
                        f"asset owned by {owner_key!r} intersects "
                        f"{region.question_key!r}'s own claimed region by "
                        f"{area:.1f}pt^2"
                    ),
                )
            )
    return findings


def span_question_key(kind: QuestionKind, number: int) -> str:
    return f"{kind.value}-{number}"
