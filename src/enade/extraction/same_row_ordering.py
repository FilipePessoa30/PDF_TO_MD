"""Same-visual-row fragment ordering (PROMPT Phase 3N).

## Root cause (confirmed by direct instrumentation against 2008-b's own D40
and Q33, this phase)

``layout.py``'s own final line sort (``extract_page_lines``) orders lines by
``(round(ln.y0, 1), ln.x0)`` - a *bounding-box* top, rounded to one decimal
place. Two (or more) fragments genuinely printed on the exact same visual
row can be reported by PyMuPDF's own ``get_text("dict")`` as **separate**
"line" entries whenever a font changes mid-row (a schema identifier set in
a monospace font inside otherwise-regular prose; an italicized word inside
a regular sentence) - and a font change shifts each span's own *bounding
box* top/bottom (different fonts have different ascender/descender
metrics) even though every span's own true **baseline**
(``span["origin"][1]``) is identical to many decimal places.

Confirmed by direct instrumentation (``page.get_text("dict")``, spans'
own ``origin`` field):

- 2008-b D40 (page 17): "Cliente" (Courier, a monospace schema-identifier
  font embedded inline in 9pt prose) has bbox y0=131.563 against its own
  neighbors' bbox y0=131.955 (a 0.39pt difference - large enough to escape
  even the existing 1-decimal bbox rounding) - but all three fragments'
  own span origin[1] is identically 139.07843017578125.
- 2008-b Q33 (page 14): the roman-numeral item marker "I" and its own
  item's italicized word "top-down" each report a bbox y0 differing from
  their plain-text neighbors by ~0.09-0.4pt - again with an identical
  origin[1] across the whole row.

A naive ``(round(y0, 1), x0)`` sort places the fragment with the smaller
*rounded bbox* y0 first, regardless of which one is actually further
*left* on the printed row - inverting the correct left-to-right reading
order (2008-b D40: "Cliente," sorts before "possui a relacao" even though
it prints to its right; Q33: the marker "I"/"II" sorts after its own
item's own opening words instead of before them).

## What this module does NOT do (PROMPT Phase 3N sections 13-19)

- It never merges fragment *text* (that is ``fragment_reconstruction.py``'s
  own, entirely separate job - see this module's own docstring section
  "Relation to fragment_reconstruction.py" below). Grouping two fragments
  as ``same_row`` only ever permutes their own relative order; it never
  joins their text, inserts/removes a character, or changes word count.
- It never reorders across a column boundary, a table cell, a detected
  table's own consumed lines, or a visual region boundary (see
  ``RowClassification`` - ``cross_column``/``different_region`` reject
  grouping outright).
- It never uses a fixed absolute-point tolerance as the *only* signal -
  every threshold is normalized against the pair's own local font size/
  line height (PROMPT section 9), so the same declarative rule applies
  unconditionally, without being tuned to one page's own font size.
- It never chains fragments transitively past an incompatible pair (PROMPT
  section 11) - grouping uses a complete-link rule: a candidate joins a
  group only if it is ``same_row``-compatible with *every* existing
  member, not merely its nearest neighbor.

## Relation to fragment_reconstruction.py

``fragment_reconstruction.py`` (Phase 3H) decides whether two *adjacent,
already left-to-right ordered* fragments should be joined into one
literal text run (requiring a documentary trailing space and a narrow gap
- the answer to "is this one wrapped sentence PyMuPDF's own dict-mode
happened to split apart?"). This module answers a different, earlier
question - "what is the correct left-to-right order of these fragments in
the first place?" - and never touches their text. Ordering runs first (a
correctly-ordered fragment list is what fragment_reconstruction's own
adjacency-based merge needs to see); fragment_reconstruction's own merge
decision is unaffected by this module (its own baseline check already
requires near-identical *bbox* y0/y1, which is stricter than what this
module accepts - a fragment pair this module groups as ``same_row`` via
matching *true* baseline but differing bbox is never a
``fragment_reconstruction`` merge candidate, and vice versa a real
fragment_reconstruction merge candidate, sharing near-identical bbox
already, is trivially also ``same_row`` here).

## Relation to reading_zones.py

``reading_zones.py`` (Phase 3K/3L) reorders whole ``Line`` objects across
zones/columns of a page - it never inspects sub-line fragment geometry.
This module operates *before* that, correcting which fragments belong on
the same printed row and their order within it; ``reading_zones`` then
sees an already row-corrected line list, exactly as it always has (a
same-row correction never crosses a zone or column boundary, so it cannot
change reading_zones's own zone/topology detection). This module is never
invoked from ``reading_zones.py`` or vice versa, and is never passed to
``figures.py`` (PROMPT section 15) - see ``assembler.py``'s own call site,
scoped to one question's own already-sliced span, exactly like
``_canonical_content_lines``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from enade.extraction.layout import Line

Rect = tuple[float, float, float, float]

RowClassification = Literal[
    "same_row",
    "different_row",
    "superscript_or_subscript",
    "cross_column",
    "different_owner",
    "different_region",
    "ambiguous",
]

#: A pair's own baseline delta, normalized by the pair's own shared font
#: size, at or under this fraction is confidently the *same* printed
#: baseline (PROMPT section 9 - normalized, not an absolute point value).
#: Real same-row cases measured this phase (D40, Q33) have a normalized
#: delta of 0.0 (identical origin[1] to 10 decimal places); this ceiling
#: leaves a wide margin before the next real signal (a genuine next line,
#: normalized delta >= ~1.0 - see MIN_DIFFERENT_ROW_NORMALIZED_BASELINE_DELTA)
#: without ever being tuned to one page's own absolute font size.
MAX_SAME_ROW_NORMALIZED_BASELINE_DELTA = 0.08

#: A pair's own baseline delta, normalized by shared font size, at or
#: above this fraction is confidently a *different* printed line (a real
#: line-to-line leading is never less than roughly the font's own size in
#: this corpus's evidence - single-spaced body text leading measured at
#: ~1.1-1.3x font size throughout 2008-b/2011/2021).
MIN_DIFFERENT_ROW_NORMALIZED_BASELINE_DELTA = 0.5

#: A superscript/subscript/exponent is reliably set in a *smaller* font
#: than its own base token in this corpus's evidence (a footnote marker,
#: an exponent, a chemical subscript) - never the same size. Ratio of the
#: smaller to the larger font size at or under this ceiling, combined with
#: a non-trivial baseline offset and genuine vertical overlap, marks
#: intentional typographic offset rather than same-row noise.
SUPERSCRIPT_FONT_SIZE_RATIO_CEILING = 0.85

#: Two fragments separated by more than this many times the shared font
#: size, horizontally, are never candidates for the same printed row
#: regardless of baseline match - guards against a same-baseline
#: coincidence between wholly unrelated content on opposite sides of a
#: wide page (see also the column-boundary barrier, a separate, stronger
#: check for genuinely two-column pages).
MAX_SAME_ROW_HORIZONTAL_GAP_RATIO = 40.0


@dataclass(frozen=True)
class SameRowRelation:
    """The full geometric relation between two fragments that might share
    one printed row - every signal kept, never collapsed into
    ``classification`` before it is inspectable (PROMPT section 8).
    """

    same_page: bool
    same_column: bool
    same_region: bool
    vertical_overlap_ratio: float
    baseline_delta: float
    normalized_baseline_delta: float
    center_delta: float
    normalized_center_delta: float
    horizontal_gap: float
    font_size_ratio: float
    height_ratio: float
    classification: RowClassification
    reason: str


def _vertical_overlap_ratio(a: Line, b: Line) -> float:
    intersection = max(0.0, min(a.y1, b.y1) - max(a.y0, b.y0))
    shorter = min(a.y1 - a.y0, b.y1 - b.y0)
    if shorter <= 0:
        return 0.0
    return intersection / shorter


def _region_id(line: Line, regions: tuple[Rect, ...]) -> int | None:
    """Index of the first region whose bbox contains ``line``'s own
    center point, or ``None`` if it sits outside every one - a lightweight
    structural signal (point containment, not the full consumption
    semantics of ``assembler._line_in_region``) used only to keep a
    same-row group from spanning a visual-region boundary (PROMPT section
    18 - protects 2008-b Q75's own fix: a diagram-interior label and the
    statement text beside it must never be grouped into one row just
    because they happen to share a baseline).
    """
    center_x = (line.x0 + line.x1) / 2.0
    center_y = (line.y0 + line.y1) / 2.0
    for index, bbox in enumerate(regions):
        if bbox[0] <= center_x <= bbox[2] and bbox[1] <= center_y <= bbox[3]:
            return index
    return None


def compute_same_row_relation(
    left: Line,
    right: Line,
    *,
    column_margins: tuple[float, float] | None = None,
    column_right_margin_tolerance: float = 5.0,
    regions: tuple[Rect, ...] = (),
) -> SameRowRelation:
    """The relation of ``right`` to ``left`` - order-independent metrics,
    a direction-aware ``horizontal_gap`` (``right.x0 - left.x1``, negative
    when the boxes overlap in X).

    Never classifies ``same_row`` when either fragment's own
    ``baseline_y`` is the sentinel default (0.0, never a real page
    coordinate - PROMPT: a fragment this codebase cannot demonstrate a
    real baseline for must never join a group on a guess).
    """
    same_page = left.page_number == right.page_number
    if not same_page:
        return SameRowRelation(
            same_page=False,
            same_column=False,
            same_region=False,
            vertical_overlap_ratio=0.0,
            baseline_delta=float("inf"),
            normalized_baseline_delta=float("inf"),
            center_delta=float("inf"),
            normalized_center_delta=float("inf"),
            horizontal_gap=float("inf"),
            font_size_ratio=0.0,
            height_ratio=0.0,
            classification="different_row",
            reason="different page",
        )

    if column_margins is not None:
        _, right_margin = column_margins
        threshold = right_margin - column_right_margin_tolerance
        left_is_right_col = left.x0 >= threshold
        right_is_right_col = right.x0 >= threshold
        if left_is_right_col != right_is_right_col:
            return SameRowRelation(
                same_page=True,
                same_column=False,
                same_region=False,
                vertical_overlap_ratio=_vertical_overlap_ratio(left, right),
                baseline_delta=abs(left.baseline_y - right.baseline_y),
                normalized_baseline_delta=float("inf"),
                center_delta=0.0,
                normalized_center_delta=0.0,
                horizontal_gap=right.x0 - left.x1,
                font_size_ratio=0.0,
                height_ratio=0.0,
                classification="cross_column",
                reason="fragments sit in different detected page columns",
            )
    same_column = True

    left_region = _region_id(left, regions)
    right_region = _region_id(right, regions)
    same_region = left_region == right_region
    if not same_region:
        return SameRowRelation(
            same_page=True,
            same_column=same_column,
            same_region=False,
            vertical_overlap_ratio=_vertical_overlap_ratio(left, right),
            baseline_delta=abs(left.baseline_y - right.baseline_y),
            normalized_baseline_delta=float("inf"),
            center_delta=0.0,
            normalized_center_delta=0.0,
            horizontal_gap=right.x0 - left.x1,
            font_size_ratio=0.0,
            height_ratio=0.0,
            classification="different_region",
            reason="fragments touch different visual regions (or only one touches one at all)",
        )

    vertical_overlap = _vertical_overlap_ratio(left, right)
    baseline_delta = abs(left.baseline_y - right.baseline_y)
    reference_font_size = max(left.font_size, right.font_size, 1.0)
    normalized_baseline_delta = baseline_delta / reference_font_size

    left_center = (left.y0 + left.y1) / 2.0
    right_center = (right.y0 + right.y1) / 2.0
    center_delta = abs(left_center - right_center)
    left_height = max(left.y1 - left.y0, 1.0)
    right_height = max(right.y1 - right.y0, 1.0)
    reference_height = max(left_height, right_height)
    normalized_center_delta = center_delta / reference_height

    horizontal_gap = right.x0 - left.x1
    font_size_ratio = (
        min(left.font_size, right.font_size) / max(left.font_size, right.font_size)
        if max(left.font_size, right.font_size) > 0
        else 1.0
    )
    height_ratio = min(left_height, right_height) / max(left_height, right_height)

    has_real_baseline = left.baseline_y > 0.0 and right.baseline_y > 0.0

    classification: RowClassification
    reason: str
    if not has_real_baseline:
        classification = "ambiguous"
        reason = "at least one fragment has no recorded true baseline (sentinel 0.0)"
    elif horizontal_gap > MAX_SAME_ROW_HORIZONTAL_GAP_RATIO * reference_font_size:
        classification = "ambiguous"
        reason = "horizontal gap too wide relative to font size to be one printed row"
    elif normalized_baseline_delta <= MAX_SAME_ROW_NORMALIZED_BASELINE_DELTA:
        classification = "same_row"
        reason = (
            f"normalized baseline delta {normalized_baseline_delta:.4f} is within the "
            f"same-row ceiling ({MAX_SAME_ROW_NORMALIZED_BASELINE_DELTA})"
        )
    elif (
        normalized_baseline_delta < MIN_DIFFERENT_ROW_NORMALIZED_BASELINE_DELTA
        and font_size_ratio <= SUPERSCRIPT_FONT_SIZE_RATIO_CEILING
        and vertical_overlap > 0.0
    ):
        classification = "superscript_or_subscript"
        reason = (
            f"baseline offset ({normalized_baseline_delta:.4f}) with a smaller font "
            f"(ratio {font_size_ratio:.2f}) and genuine vertical overlap - intentional "
            "typographic offset, not same-row noise"
        )
    elif normalized_baseline_delta >= MIN_DIFFERENT_ROW_NORMALIZED_BASELINE_DELTA:
        classification = "different_row"
        reason = (
            f"normalized baseline delta {normalized_baseline_delta:.4f} matches a real "
            "line-to-line leading"
        )
    else:
        classification = "ambiguous"
        reason = (
            f"normalized baseline delta {normalized_baseline_delta:.4f} sits between the "
            "same-row and different-row ceilings with no superscript/subscript evidence "
            "either - preserving the existing order rather than guessing"
        )

    return SameRowRelation(
        same_page=True,
        same_column=same_column,
        same_region=True,
        vertical_overlap_ratio=vertical_overlap,
        baseline_delta=baseline_delta,
        normalized_baseline_delta=normalized_baseline_delta,
        center_delta=center_delta,
        normalized_center_delta=normalized_center_delta,
        horizontal_gap=horizontal_gap,
        font_size_ratio=font_size_ratio,
        height_ratio=height_ratio,
        classification=classification,
        reason=reason,
    )


@dataclass(frozen=True)
class RowFragmentGroup:
    """A confirmed set of 2+ fragments that share one printed visual row
    (PROMPT section 10) - membership is complete-link (every pair inside
    the group relates as ``same_row``), never a transitive chain through
    an incompatible pair (PROMPT section 11).
    """

    page: int
    member_ids: tuple[int, ...]
    representative_baseline: float
    baseline_spread: float
    vertical_union: tuple[float, float]
    horizontal_extent: tuple[float, float]
    confidence: float


def _complete_link_groups(
    lines: list[Line],
    relations: dict[tuple[int, int], SameRowRelation],
) -> list[list[int]]:
    """Greedy complete-link clustering (PROMPT section 11): process
    fragments in original order; a fragment joins the first existing group
    every one of whose current members it relates to as ``same_row``,
    else it starts (or remains outside) its own group. Never a single-
    linkage chain: adding a member to a group requires compatibility with
    *all* current members, not just the most recently added one - so
    ``A~B`` and ``B~C`` (but not ``A~C``) can never silently imply
    ``A,B,C`` all share one row (PROMPT's own explicit transitive-bridge
    prohibition).

    A pair with no entry in ``relations`` at all (excluded by the caller's
    own cheap vertical-proximity pre-filter) is treated exactly like a
    computed non-``same_row`` relation - far enough apart in Y that it was
    never a real same-row candidate to begin with.
    """
    groups: list[list[int]] = []
    for i in range(len(lines)):
        placed = False
        for group in groups:
            if all(
                relations.get((min(i, j), max(i, j))) is not None
                and relations[(min(i, j), max(i, j))].classification == "same_row"
                for j in group
            ):
                group.append(i)
                placed = True
                break
        if not placed:
            groups.append([i])
    return [g for g in groups if len(g) >= 2]


def group_same_row_fragments(
    lines: list[Line],
    *,
    column_margins: tuple[float, float] | None = None,
    regions: tuple[Rect, ...] = (),
) -> tuple[list[RowFragmentGroup], dict[tuple[int, int], SameRowRelation]]:
    """Find every confirmed same-row group among ``lines`` (already
    restricted to one page, one owner, one already-sliced question span -
    see ``assembler.py``'s own call site).

    Returns the confirmed groups (by index into ``lines``) and the full
    pairwise relation table (every candidate pair within a generous
    vertical proximity window, not just accepted ones - for the trace).
    """
    relations: dict[tuple[int, int], SameRowRelation] = {}
    n = len(lines)
    for i in range(n):
        for j in range(i + 1, n):
            a, b = lines[i], lines[j]
            # Cheap pre-filter: never compute (or need) a relation for a
            # pair whose own bbox vertical extents are wildly far apart -
            # avoids O(n^2) full relation computation on a long span.
            if abs(a.y0 - b.y0) > 4.0 * max(a.font_size, b.font_size, 1.0):
                continue
            relations[(i, j)] = compute_same_row_relation(
                a, b, column_margins=column_margins, regions=regions
            )

    group_indices = _complete_link_groups(lines, relations)
    groups: list[RowFragmentGroup] = []
    for indices in group_indices:
        members = [lines[i] for i in indices]
        baselines = [m.baseline_y for m in members]
        y0s = [m.y0 for m in members]
        y1s = [m.y1 for m in members]
        x0s = [m.x0 for m in members]
        x1s = [m.x1 for m in members]
        groups.append(
            RowFragmentGroup(
                page=members[0].page_number,
                member_ids=tuple(indices),
                representative_baseline=sum(baselines) / len(baselines),
                baseline_spread=max(baselines) - min(baselines),
                vertical_union=(min(y0s), max(y1s)),
                horizontal_extent=(min(x0s), max(x1s)),
                confidence=1.0,
            )
        )
    return groups, relations


def reorder_same_row_groups(
    lines: list[Line],
    groups: list[RowFragmentGroup],
) -> tuple[list[Line], list[str]]:
    """Apply local horizontal order within each confirmed group; preserve
    the existing order for everything else, including the relative order
    between groups and ungrouped lines (PROMPT section 12 - horizontal
    order has authority only *within* a confirmed group).

    Deterministic tie-break within a group: ``(x0, x1, original_index)``.
    """
    result = list(lines)
    notes: list[str] = []
    for group in groups:
        ordered_positions = sorted(group.member_ids)
        members_by_original_index = {i: lines[i] for i in group.member_ids}
        reordered_members = sorted(
            group.member_ids,
            key=lambda i: (lines[i].x0, lines[i].x1, i),
        )
        if reordered_members == sorted(group.member_ids):
            continue
        for slot, member_index in zip(ordered_positions, reordered_members, strict=True):
            result[slot] = members_by_original_index[member_index]
        notes.append(
            f"page {group.page}: reordered {len(group.member_ids)} same-row fragment(s) "
            f"(baseline={group.representative_baseline:.3f}, spread={group.baseline_spread:.4f}pt) "
            "by x0 - original document order did not match left-to-right reading order"
        )
    return result, notes
