"""Zone-aware reading order: a page does not necessarily share one column
topology from top to bottom (PROMPT Phase 3K).

Root cause this module exists to fix (2008-b D10, page 7, "Formação Geral
Discursiva 10" - a newspaper-collage motivational-text page): the
pre-existing ``layout.detect_column_margins`` makes exactly one
(left_margin, right_margin) decision for an *entire* page, and
``extract_page_lines`` applies it globally - every line left of the right
margin sorts first (by y0), then every line at or past it sorts second,
regardless of where on the page either actually sits. That is a correct
model for a page that is genuinely two columns from its first line of body
text to its last (the common case - a straight 2011/2021 side-by-side
objective pair). It is the wrong model for a page whose topology *changes*
partway down: D10's own page opens with a photo (left) beside a newspaper
article (right, two-column), continues as full-width single-column prose
for two more motivating fragments, then closes with a genuine two-column
bulleted "Observações" box. Applying one global split there does not
merely fail to fix the collage - it *actively scrambles* it, since the
old algorithm's own "left-then-right" rule pushes the entire right-side
newspaper article (and the entire right-side half of the bulleted box)
to after every left-side line on the page, including the closing full-width
paragraphs and even the page's own footer chrome.

The general principle applied here (Section 5 of the Phase 3K prompt):
column *detection* and reading-order *resolution* are two separate
questions. ``layout.detect_column_margins`` keeps its existing job -
deciding, from page-wide evidence, whether a genuine two-column shape
exists anywhere on this page at all, and what its two margins are. This
module answers the *second* question: given those two candidate margins,
which specific vertical windows of the page actually exhibit *both*
columns concurrently (and therefore need left-then-right interleaving
there), and which windows have only one side's content (and therefore
need nothing more than being merged, by y0, into the surrounding flow)?

A vertical window is treated as genuinely two-column only when *both*
sides have real, substantial evidence within it (the same
``MIN_LINES_PER_COLUMN`` threshold ``detect_column_margins`` itself
already requires page-wide, now required *locally*) - never merely
because some line's own x0 happens to sit past the page-wide right
margin. This is what correctly leaves D10's own photo-caption zone (one
lone citation on the "left" side, no real column there) and its own
closing full-width paragraphs (zero "right"-side content at all) as
ordinary y0-sorted flow, while still correctly interleaving the one
window that *is* genuinely two columns (the bulleted "Observações" box,
three substantial lines on each side).

The final order is built and verified as a small dependency graph (nodes:
one per line; edges: one per adjacency the algorithm asserts, tagged with
why) and resolved with :func:`graphlib.TopologicalSorter` from the
standard library - never a hand-rolled sort with no cycle-detection
guarantee. The graph this module ever actually builds is a single linear
chain (each zone's own lines, and each unclaimed line, concatenated in
window-start order) - genuinely acyclic by construction, not merely
untested for cycles - but running the formal topological sort, rather
than trusting that construction blindly, is what makes a future cycle (a
malformed edge set from a later extension) a loud ``CycleError`` instead
of a silently wrong or duplicated order (PROMPT section 8: "nunca resolver
ciclo descartando conteúdo silenciosamente").

PROMPT Phase 3L adds two things on top of the Phase 3K mechanism above,
neither of which changes zone/order computation itself:

1. ``assess_eligibility`` - a purely structural decision (zone count,
   topology transitions, graph acyclicity) for whether a given line list
   is even a *candidate* for zone-aware reordering at all - never a
   question ID, page number, or page hash. Phase 3K activated the
   mechanism via a hash-locked, page-specific override
   (``layout_overrides.LayoutOverrideSet.forces_zoned_reading_order``,
   removed in Phase 3L) after discovering that applying it unconditionally
   to *every* page regressed dozens of already-correct ones - not because
   the zoning itself was wrong, but because several *other* consumers of
   ``layout.extract_page_lines`` (``figures.py``'s own label absorption
   chief among them) use that function's own returned order as an
   implicit geometric proxy, and broke when the order changed under them
   for reasons unrelated to their own job. Phase 3L's fix is architectural
   (see ``assembler._canonical_content_lines``): this module is now only
   ever consulted from within ``assembler.assemble_question``, on one
   question's own already-sliced span, strictly *after* every geometric
   consumer (region detection, margin detection, question-boundary
   detection) has already been fed the original, untouched, page-wide
   order from ``layout.extract_page_lines``. Structural eligibility
   replaces the override as the operational selector; the override itself
   is kept in ``data/manifests/layout-overrides.yaml``, marked
   ``superseded``, as a historical record of the page-scoped fix that
   first resolved D10 safely.
2. A differential safety check (``assembler._canonical_content_lines``'s
   own ``same_lines``/``word_conserved`` gates) that never trusts
   eligibility alone: a span is only ever reordered if the candidate order
   is confirmed, by direct comparison, to be a pure permutation of the
   exact same lines - never a content change.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from graphlib import CycleError, TopologicalSorter
from statistics import median
from typing import Literal

from enade.extraction.chrome import is_chrome_line
from enade.extraction.layout import (
    COLUMN_RIGHT_MARGIN_TOLERANCE,
    MIN_COLUMN_LINE_WIDTH,
    MIN_LINES_PER_COLUMN,
    Line,
    detect_column_margins,
)

#: A Y-gap between two consecutive same-side lines larger than this many
#: times the side's own median line-to-line pitch signals a genuine
#: vertical topology change (the end of one two-column window, not an
#: ordinary paragraph/article-to-article transition within one) - a
#: relative, self-calibrating measure (PROMPT section 10: "não use
#: coordenadas absolutas"), so it scales automatically with font size and
#: line spacing rather than assuming any fixed point value. Calibrated
#: against real evidence: D10's own genuine break between its top
#: newspaper-collage window and its own closing bulleted box is a ~280pt
#: gap against a ~12pt median pitch (over 20x); an ordinary
#: article-to-article transition within the same window is at most ~2x
#: the local pitch.
ZONE_GAP_MULTIPLIER = 4.0

ReadingZoneMode = Literal[
    "single_column",
    "multi_column",
    "spanning",
    "question_local",
    "ambiguous",
]

EdgeReason = Literal[
    "same_column_vertical",
    "cross_column_transition",
    "spanning_barrier",
    "question_continuation",
    "alternative_sequence",
    "annotation_attachment",
    "reference_caption_transfer",
    "explicit_document_order",
]


@dataclass(frozen=True)
class ReadingZone:
    """One vertical window of a page with its own, independently-detected
    column topology - see this module's own docstring for why a page can
    have more than one.
    """

    zone_id: str
    page: int
    y_interval: tuple[float, float]
    mode: ReadingZoneMode
    column_count: int
    column_bounds: tuple[float, ...]
    source_line_ids: tuple[int, ...]
    detection_method: str
    confidence: float


def zone_bbox(zone: ReadingZone, lines: list[Line]) -> tuple[float, float, float, float]:
    """The real bounding box of a zone's own lines, computed on demand."""
    members = [lines[i] for i in zone.source_line_ids]
    return (
        min(ln.x0 for ln in members),
        min(ln.y0 for ln in members),
        max(ln.x1 for ln in members),
        max(ln.y1 for ln in members),
    )


@dataclass(frozen=True)
class Barrier:
    """A detected transition point between two zones of different topology."""

    barrier_id: str
    page: int
    y_position: float
    type: Literal["vertical_gap", "topology_change"]
    evidence: str
    splits_before: str
    splits_after: str
    confidence: float


@dataclass(frozen=True)
class ReadingOrderNode:
    node_id: str
    page: int
    zone_id: str
    original_index: int


@dataclass(frozen=True)
class ReadingOrderEdge:
    from_node: str
    to_node: str
    reason: EdgeReason
    evidence: str


@dataclass(frozen=True)
class ReadingOrderTrace:
    """Deterministic, machine-readable record of one page's own zoning and
    ordering decision - PROMPT section 17.
    """

    page: int
    zones: tuple[ReadingZone, ...]
    barriers: tuple[Barrier, ...]
    nodes: tuple[ReadingOrderNode, ...]
    edges: tuple[ReadingOrderEdge, ...]
    topological_order: tuple[int, ...]
    ambiguous_nodes: tuple[str, ...] = ()
    cycles: tuple[tuple[str, ...], ...] = ()
    fallbacks: tuple[str, ...] = field(default_factory=tuple)


def _is_substantial(ln: Line) -> bool:
    return (ln.x1 - ln.x0) >= MIN_COLUMN_LINE_WIDTH and not is_chrome_line(ln.text)


def _median_pitch(sorted_lines: list[Line]) -> float:
    ys = sorted(ln.y0 for ln in sorted_lines)
    gaps = [b - a for a, b in zip(ys, ys[1:], strict=False) if b > a]
    if not gaps:
        return 1.0
    return max(median(gaps), 1.0)


def _cluster_by_y_gap(sorted_lines: list[Line], gap_threshold: float) -> list[list[Line]]:
    clusters: list[list[Line]] = []
    current: list[Line] = []
    previous_y0: float | None = None
    for ln in sorted_lines:
        if previous_y0 is not None and (ln.y0 - previous_y0) > gap_threshold:
            clusters.append(current)
            current = []
        current.append(ln)
        previous_y0 = ln.y0
    if current:
        clusters.append(current)
    return clusters


def detect_reading_zones(lines: list[Line], page: int) -> list[ReadingZone]:
    """Partition ``lines`` (one page's own, in any order) into zones.

    Falls back to a single ``single_column`` zone covering the whole page
    when ``detect_column_margins`` itself finds no page-wide two-column
    evidence at all - identical to every page this project's existing
    corpus already relies on (see this module's own docstring).
    """
    if not lines:
        return []

    margins = detect_column_margins(lines)
    if margins is None:
        ids = tuple(range(len(lines)))
        y0 = min(ln.y0 for ln in lines)
        y1 = max(ln.y1 for ln in lines)
        return [
            ReadingZone(
                zone_id=f"p{page}:z0",
                page=page,
                y_interval=(y0, y1),
                mode="single_column",
                column_count=1,
                column_bounds=(),
                source_line_ids=ids,
                detection_method="detect_column_margins:none",
                confidence=1.0,
            )
        ]

    _, right_margin = margins
    right_threshold = right_margin - COLUMN_RIGHT_MARGIN_TOLERANCE
    index_of = {id(ln): i for i, ln in enumerate(lines)}
    left_all = [ln for ln in lines if ln.x0 < right_threshold]
    right_all = [ln for ln in lines if ln.x0 >= right_threshold]
    right_substantial = sorted(
        (ln for ln in right_all if _is_substantial(ln)), key=lambda ln: ln.y0
    )

    pitch = _median_pitch(right_substantial) if right_substantial else 1.0
    gap_threshold = ZONE_GAP_MULTIPLIER * pitch
    clusters = _cluster_by_y_gap(right_substantial, gap_threshold)

    zones: list[ReadingZone] = []
    claimed: set[int] = set()
    zone_counter = 0

    def _overlaps(ln: Line, window_y0: float, window_y1: float) -> bool:
        # Genuine vertical span intersection - never a proximity buffer
        # (PROMPT section 7: "linhas-régua decorativas não podem adquirir
        # autoridade semântica apenas pela largura", and the same principle
        # applies to mere Y-nearness: a line's own paragraph-continuation
        # sitting just below a two-column window's own last right-side line
        # is not evidence of a second column there, only genuine concurrent
        # printing - both sides' own ink actually occupying the same
        # vertical band at once - is).
        return ln.y0 < window_y1 and ln.y1 > window_y0

    for cluster in clusters:
        window_y0 = min(ln.y0 for ln in cluster)
        window_y1 = max(ln.y1 for ln in cluster)
        left_in_window = [ln for ln in left_all if _overlaps(ln, window_y0, window_y1)]
        left_substantial_in_window = [ln for ln in left_in_window if _is_substantial(ln)]
        if len(left_substantial_in_window) < MIN_LINES_PER_COLUMN:
            continue  # not enough evidence of a genuine second column here
        right_in_window = [ln for ln in right_all if _overlaps(ln, window_y0, window_y1)]
        members = left_in_window + right_in_window
        member_ids = tuple(sorted(index_of[id(ln)] for ln in members))
        y0 = min(ln.y0 for ln in members)
        y1 = max(ln.y1 for ln in members)
        zones.append(
            ReadingZone(
                zone_id=f"p{page}:z{zone_counter}",
                page=page,
                y_interval=(y0, y1),
                mode="multi_column",
                column_count=2,
                column_bounds=(margins[0], right_margin),
                source_line_ids=member_ids,
                detection_method="local_two_sided_evidence",
                confidence=1.0,
            )
        )
        claimed.update(member_ids)
        zone_counter += 1

    remaining = [(i, ln) for i, ln in enumerate(lines) if i not in claimed]
    for i, ln in remaining:
        zones.append(
            ReadingZone(
                zone_id=f"p{page}:z{zone_counter}",
                page=page,
                y_interval=(ln.y0, ln.y1),
                mode="single_column",
                column_count=1,
                column_bounds=(),
                source_line_ids=(i,),
                detection_method="unclaimed_single_line",
                confidence=1.0,
            )
        )
        zone_counter += 1

    return zones


def resolve_reading_order(
    lines: list[Line], zones: list[ReadingZone]
) -> tuple[list[Line], ReadingOrderTrace]:
    """Order ``lines`` from their own zones, and return the trace that
    explains the decision (PROMPT section 8/17).
    """
    if not lines:
        page = zones[0].page if zones else 0
        return [], ReadingOrderTrace(page, (), (), (), (), ())

    page = zones[0].page if zones else lines[0].page_number

    def _zone_ordered_lines(zone: ReadingZone) -> list[int]:
        members = [(i, lines[i]) for i in zone.source_line_ids]
        if zone.mode == "multi_column":
            left_margin, right_margin_bound = zone.column_bounds
            right_threshold = right_margin_bound - COLUMN_RIGHT_MARGIN_TOLERANCE
            left = sorted(
                (pair for pair in members if pair[1].x0 < right_threshold),
                key=lambda pair: (round(pair[1].y0, 1), pair[1].x0),
            )
            right = sorted(
                (pair for pair in members if pair[1].x0 >= right_threshold),
                key=lambda pair: (round(pair[1].y0, 1), pair[1].x0),
            )
            return [i for i, _ in left] + [i for i, _ in right]
        return [i for i, _ in sorted(members, key=lambda pair: (round(pair[1].y0, 1), pair[1].x0))]

    zone_order = sorted(zones, key=lambda z: (round(z.y_interval[0], 1), z.zone_id))

    nodes: list[ReadingOrderNode] = []
    edges: list[ReadingOrderEdge] = []
    ordered_indices: list[int] = []
    sorter: TopologicalSorter[int] = TopologicalSorter()
    previous_index: int | None = None
    previous_zone: ReadingZone | None = None

    for zone in zone_order:
        zone_line_order = _zone_ordered_lines(zone)
        for position, idx in enumerate(zone_line_order):
            nodes.append(
                ReadingOrderNode(
                    node_id=f"n{idx}", page=page, zone_id=zone.zone_id, original_index=idx
                )
            )
            sorter.add(idx)
            if previous_index is not None:
                if previous_zone is zone and zone.mode == "multi_column" and position > 0:
                    reason: EdgeReason = "cross_column_transition"
                elif previous_zone is zone:
                    reason = "same_column_vertical"
                else:
                    reason = "spanning_barrier"
                sorter.add(idx, previous_index)
                edges.append(
                    ReadingOrderEdge(
                        from_node=f"n{previous_index}",
                        to_node=f"n{idx}",
                        reason=reason,
                        evidence=zone.detection_method,
                    )
                )
            previous_index = idx
            previous_zone = zone

    try:
        ordered_indices = list(sorter.static_order())
    except CycleError as exc:
        # PROMPT section 8: never resolve a cycle by discarding content -
        # fall back to the original, pre-zoning document order and record
        # the cycle for the trace/report rather than guessing.
        ordered_indices = list(range(len(lines)))
        trace = ReadingOrderTrace(
            page=page,
            zones=tuple(zone_order),
            barriers=(),
            nodes=tuple(nodes),
            edges=tuple(edges),
            topological_order=tuple(ordered_indices),
            cycles=(tuple(str(n) for n in exc.args[1]),) if len(exc.args) > 1 else (("unknown",),),
            fallbacks=("cycle_detected_reverted_to_document_order",),
        )
        return [lines[i] for i in ordered_indices], trace

    barriers = tuple(
        Barrier(
            barrier_id=f"p{page}:b{i}",
            page=page,
            y_position=zone_order[i + 1].y_interval[0],
            type="topology_change"
            if zone_order[i].mode != zone_order[i + 1].mode
            else "vertical_gap",
            evidence=f"{zone_order[i].zone_id}({zone_order[i].mode}) -> {zone_order[i + 1].zone_id}({zone_order[i + 1].mode})",
            splits_before=zone_order[i].zone_id,
            splits_after=zone_order[i + 1].zone_id,
            confidence=1.0,
        )
        for i in range(len(zone_order) - 1)
    )

    trace = ReadingOrderTrace(
        page=page,
        zones=tuple(zone_order),
        barriers=barriers,
        nodes=tuple(nodes),
        edges=tuple(edges),
        topological_order=tuple(ordered_indices),
    )
    return [lines[i] for i in ordered_indices], trace


def zoned_reading_order(lines: list[Line], page: int) -> tuple[list[Line], ReadingOrderTrace]:
    """Single entry point: detect this page's own zones, then resolve the
    final line order from them. See module docstring for the full
    rationale.
    """
    zones = detect_reading_zones(lines, page)
    return resolve_reading_order(lines, zones)


@dataclass(frozen=True)
class ReadingZoneEligibility:
    """Whether a line list is structurally a candidate for zone-aware
    reordering - PROMPT Phase 3L, section 9.

    Computed from zone/graph evidence alone: never a question ID, page
    number, or page hash. Deliberately does *not* decide whether the
    reorder is actually safe to publish - that is a separate concern
    (word/source-id conservation), decided by the caller after this
    structural question is answered, since this module has no notion of
    "word" or "owner" at all (see ``assembler._canonical_content_lines``).
    """

    eligible: bool
    confidence: float
    positive_evidence: tuple[str, ...]
    negative_evidence: tuple[str, ...]
    zone_count: int
    topology_transitions: int
    graph_acyclic: bool
    decision_reason: str


def assess_eligibility(
    zones: list[ReadingZone], cycles: tuple[tuple[str, ...], ...] = ()
) -> ReadingZoneEligibility:
    """Decide, from zone evidence alone, whether zone-aware reordering is
    even a candidate here.

    Positive evidence requires *both* at least two zones and at least one
    genuine mode transition between adjacent zones (a uniform single- or
    two-column page - the common case, e.g. two independent objective
    questions side by side, or a page whose own bare item markers happen
    to sit in their own column - produces exactly one zone spanning the
    whole span, or several same-mode zones with zero transitions, and is
    therefore never eligible: see ``test_reading_zones.py``'s own
    ``test_whole_page_two_column_matches_left_then_right_convention`` and
    ``test_narrow_single_left_side_line_is_not_enough_evidence_for_two_columns``).
    A cyclic graph is disqualifying regardless of transition evidence.
    """
    zone_count = len(zones)
    ordered = sorted(zones, key=lambda z: z.y_interval[0])
    transitions = sum(1 for a, b in zip(ordered, ordered[1:], strict=False) if a.mode != b.mode)
    graph_acyclic = len(cycles) == 0

    positive: list[str] = []
    negative: list[str] = []

    if zone_count < 2:
        negative.append(f"only {zone_count} zone(s) - no evidence of a topology change")
    elif transitions < 1:
        negative.append(
            f"{zone_count} zones but zero mode transitions between them - a uniform topology"
        )
    else:
        positive.append(
            f"{transitions} vertical topology transition(s) detected across {zone_count} zones"
        )

    multi_column_zones = [z for z in zones if z.mode == "multi_column"]
    if multi_column_zones:
        positive.append(
            f"{len(multi_column_zones)} zone(s) with genuine concurrent two-column evidence"
        )

    if not graph_acyclic:
        negative.append(f"reading-order graph has {len(cycles)} cycle(s)")

    eligible = bool(positive) and not negative
    confidence = 1.0 if eligible else 0.0
    reason = "; ".join(positive) if eligible else "; ".join(negative) or "no zones produced"

    return ReadingZoneEligibility(
        eligible=eligible,
        confidence=confidence,
        positive_evidence=tuple(positive),
        negative_evidence=tuple(negative),
        zone_count=zone_count,
        topology_transitions=transitions,
        graph_acyclic=graph_acyclic,
        decision_reason=reason,
    )
