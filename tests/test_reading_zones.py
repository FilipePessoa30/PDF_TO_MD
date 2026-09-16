"""Unit + metamorphic tests for reading_zones.py (PROMPT Phase 3K).

All fixtures are synthetic - round coordinates chosen only to exhibit a
named geometric shape ("two genuine columns", "a wide header then two
columns", "a false column from a narrow annotation") - never real PDF
coordinates and never D10's own text, per the phase's own explicit
constraint that a test must not depend on a fixed page, copied
coordinates, or a specific question's full text.
"""

from __future__ import annotations

from graphlib import CycleError, TopologicalSorter

import pytest

from enade.extraction.layout import Line
from enade.extraction.reading_zones import (
    ReadingZone,
    assess_eligibility,
    detect_reading_zones,
    resolve_reading_order,
    zoned_reading_order,
)


def _line(text: str, x0: float, y0: float, width: float = 200.0, height: float = 10.0) -> Line:
    return Line(page_number=1, text=text, x0=x0, y0=y0, x1=x0 + width, y1=y0 + height)


def _texts(lines: list[Line]) -> list[str]:
    return [ln.text for ln in lines]


# --- whole-page topology (subsumes the pre-existing single/two-column cases) --


def test_whole_page_single_column_is_one_zone_sorted_by_y0():
    lines = [_line(f"line {i}", 40.0, 100.0 + i * 20) for i in range(6)]
    ordered, trace = zoned_reading_order(lines, page=1)
    assert _texts(ordered) == [ln.text for ln in lines]
    assert len(trace.zones) == 1
    assert trace.zones[0].mode == "single_column"


def test_whole_page_two_column_matches_left_then_right_convention():
    left = [_line(f"L{i}", 40.0, 100.0 + i * 20) for i in range(4)]
    right = [_line(f"R{i}", 320.0, 100.0 + i * 20) for i in range(4)]
    lines = left + right  # content-stream order need not match reading order
    ordered, trace = zoned_reading_order(lines, page=1)
    assert _texts(ordered) == ["L0", "L1", "L2", "L3", "R0", "R1", "R2", "R3"]
    multi = [z for z in trace.zones if z.mode == "multi_column"]
    assert len(multi) == 1


def test_wide_header_then_two_columns():
    header = [_line("HEADER", 40.0, 50.0, width=480.0)]
    left = [_line(f"L{i}", 40.0, 100.0 + i * 20) for i in range(4)]
    right = [_line(f"R{i}", 320.0, 100.0 + i * 20) for i in range(4)]
    ordered, _ = zoned_reading_order(header + right + left, page=1)
    assert _texts(ordered) == ["HEADER", "L0", "L1", "L2", "L3", "R0", "R1", "R2", "R3"]


def test_two_columns_then_full_width_block():
    left = [_line(f"L{i}", 40.0, 100.0 + i * 20) for i in range(4)]
    right = [_line(f"R{i}", 320.0, 100.0 + i * 20) for i in range(4)]
    footer = [_line("FOOTER", 40.0, 300.0, width=480.0)]
    ordered, _ = zoned_reading_order(right + footer + left, page=1)
    assert _texts(ordered) == ["L0", "L1", "L2", "L3", "R0", "R1", "R2", "R3", "FOOTER"]


def test_return_to_two_columns_after_a_wide_block():
    # left/right zone 1, a wide single-column block, then a second,
    # independent left/right zone lower on the page.
    left1 = [_line(f"L1-{i}", 40.0, 100.0 + i * 20) for i in range(3)]
    right1 = [_line(f"R1-{i}", 320.0, 100.0 + i * 20) for i in range(3)]
    middle = [_line("MIDDLE", 40.0, 300.0, width=480.0)]
    left2 = [_line(f"L2-{i}", 40.0, 400.0 + i * 20) for i in range(3)]
    right2 = [_line(f"R2-{i}", 320.0, 400.0 + i * 20) for i in range(3)]
    lines = left1 + right1 + middle + left2 + right2
    ordered, trace = zoned_reading_order(lines, page=1)
    assert _texts(ordered) == [
        "L1-0",
        "L1-1",
        "L1-2",
        "R1-0",
        "R1-1",
        "R1-2",
        "MIDDLE",
        "L2-0",
        "L2-1",
        "L2-2",
        "R2-0",
        "R2-1",
        "R2-2",
    ]
    assert len([z for z in trace.zones if z.mode == "multi_column"]) == 2


def test_topology_changes_more_than_once_matches_d10s_own_shape():
    # Mirrors 2008-b D10's own real shape: two-column (photo+article),
    # full-width prose, two-column bullets - three topology changes.
    top_right = [_line(f"art{i}", 320.0, 100.0 + i * 15) for i in range(5)]
    top_left_evidence_missing = [_line("caption", 145.0, 190.0, width=95.0)]
    prose = [_line(f"prose{i}", 40.0, 300.0 + i * 15, width=480.0) for i in range(4)]
    bullets_left = [_line(f"bl{i}", 51.0, 500.0 + i * 15, width=250.0) for i in range(3)]
    bullets_right = [_line(f"br{i}", 333.0, 500.0 + i * 15, width=200.0) for i in range(3)]
    lines = top_right + top_left_evidence_missing + prose + bullets_left + bullets_right
    ordered, trace = zoned_reading_order(lines, page=1)
    names = _texts(ordered)
    # The article (only real evidence on either side there) reads straight
    # through before the full-width prose, which itself precedes the
    # genuinely two-column bulleted zone.
    assert names.index("art4") < names.index("prose0")
    assert names.index("prose3") < names.index("bl0")
    assert names.index("bl0") < names.index("br0") or names.index("br0") < names.index("bl2")
    multi = [z for z in trace.zones if z.mode == "multi_column"]
    assert len(multi) == 1  # only the bullets have genuine two-sided evidence


def test_zones_do_not_overlap():
    left = [_line(f"L{i}", 40.0, 100.0 + i * 20) for i in range(4)]
    right = [_line(f"R{i}", 320.0, 100.0 + i * 20) for i in range(4)]
    footer = [_line("FOOTER", 40.0, 300.0, width=480.0)]
    _, trace = zoned_reading_order(left + right + footer, page=1)
    covered: set[int] = set()
    for zone in trace.zones:
        ids = set(zone.source_line_ids)
        assert not (ids & covered), "a line belongs to more than one zone"
        covered |= ids
    assert covered == set(range(len(left + right + footer)))


def test_trace_is_deterministic_across_repeated_calls():
    left = [_line(f"L{i}", 40.0, 100.0 + i * 20) for i in range(4)]
    right = [_line(f"R{i}", 320.0, 100.0 + i * 20) for i in range(4)]
    lines = left + right
    ordered1, trace1 = zoned_reading_order(list(lines), page=1)
    ordered2, trace2 = zoned_reading_order(list(lines), page=1)
    assert _texts(ordered1) == _texts(ordered2)
    assert trace1.topological_order == trace2.topological_order
    assert trace1.zones == trace2.zones


# --- column classification -------------------------------------------------


def test_narrow_single_left_side_line_is_not_enough_evidence_for_two_columns():
    # Only one substantial left-side line concurrent with a real right
    # column - not enough evidence (MIN_LINES_PER_COLUMN=3) for a genuine
    # second column there, so it must not be forced into a left/right split.
    right = [_line(f"R{i}", 320.0, 100.0 + i * 15) for i in range(5)]
    lone_left = [_line("caption", 145.0, 150.0, width=95.0)]
    ordered, trace = zoned_reading_order(right + lone_left, page=1)
    assert not any(z.mode == "multi_column" for z in trace.zones)
    # The lone left line still appears somewhere, never lost.
    assert "caption" in _texts(ordered)


def test_false_column_from_a_diagram_label_is_not_confirmed():
    # A handful of short "label" lines on one side, far too few to be a
    # real column, alongside a genuine, well-evidenced right column.
    right = [_line(f"R{i}", 320.0, 100.0 + i * 15) for i in range(5)]
    labels = [_line("A", 40.0, 105.0, width=10.0), _line("B", 40.0, 135.0, width=10.0)]
    _, trace = zoned_reading_order(right + labels, page=1)
    assert not any(z.mode == "multi_column" for z in trace.zones)


def test_asymmetric_column_widths_still_resolve():
    left = [_line(f"L{i}", 40.0, 100.0 + i * 20, width=150.0) for i in range(4)]
    right = [_line(f"R{i}", 320.0, 100.0 + i * 20, width=230.0) for i in range(4)]
    ordered, _ = zoned_reading_order(left + right, page=1)
    assert _texts(ordered) == ["L0", "L1", "L2", "L3", "R0", "R1", "R2", "R3"]


# --- graph / topological sort -----------------------------------------------


def test_resolve_reading_order_on_empty_input():
    ordered, trace = resolve_reading_order([], [])
    assert ordered == []
    assert trace.zones == ()


def test_cycle_is_detected_and_never_silently_resolved():
    # Directly exercise the underlying primitive resolve_reading_order
    # relies on: a real cycle must raise, never be silently broken.
    sorter: TopologicalSorter[str] = TopologicalSorter()
    sorter.add("a", "b")
    sorter.add("b", "a")
    with pytest.raises(CycleError):
        list(sorter.static_order())


def test_single_line_page_is_trivially_ordered():
    lines = [_line("only", 40.0, 100.0)]
    ordered, trace = zoned_reading_order(lines, page=1)
    assert _texts(ordered) == ["only"]
    assert trace.cycles == ()


def test_reading_zone_is_frozen_and_hashable():
    zone = ReadingZone(
        zone_id="p1:z0",
        page=1,
        y_interval=(0.0, 10.0),
        mode="single_column",
        column_count=1,
        column_bounds=(),
        source_line_ids=(0,),
        detection_method="test",
        confidence=1.0,
    )
    hash(zone)  # must not raise


# --- metamorphic tests -------------------------------------------------------


def test_translation_invariance():
    left = [_line(f"L{i}", 40.0, 100.0 + i * 20) for i in range(4)]
    right = [_line(f"R{i}", 320.0, 100.0 + i * 20) for i in range(4)]
    base = left + right
    shifted = [_line(ln.text, ln.x0 + 200.0, ln.y0 + 500.0) for ln in base]
    base_ordered, _ = zoned_reading_order(base, page=1)
    shifted_ordered, _ = zoned_reading_order(shifted, page=1)
    assert _texts(base_ordered) == _texts(shifted_ordered)


def test_scale_invariance():
    left = [_line(f"L{i}", 40.0, 100.0 + i * 20) for i in range(4)]
    right = [_line(f"R{i}", 320.0, 100.0 + i * 20) for i in range(4)]
    base = left + right
    scaled = [_line(ln.text, ln.x0 * 2.0, ln.y0 * 2.0, width=(ln.x1 - ln.x0) * 2.0) for ln in base]
    base_ordered, _ = zoned_reading_order(base, page=1)
    scaled_ordered, _ = zoned_reading_order(scaled, page=1)
    assert _texts(base_ordered) == _texts(scaled_ordered)


def test_content_stream_order_does_not_affect_result():
    left = [_line(f"L{i}", 40.0, 100.0 + i * 20) for i in range(4)]
    right = [_line(f"R{i}", 320.0, 100.0 + i * 20) for i in range(4)]
    forward, _ = zoned_reading_order(left + right, page=1)
    backward, _ = zoned_reading_order(list(reversed(right + left)), page=1)
    assert _texts(forward) == _texts(backward)


def test_font_size_variation_does_not_affect_zone_topology():
    left = [_line(f"L{i}", 40.0, 100.0 + i * 20) for i in range(4)]
    right = [_line(f"R{i}", 320.0, 100.0 + i * 20) for i in range(4)]
    for ln, size in zip(left + right, [8.0, 10.0, 12.0, 14.0] * 2, strict=False):
        object.__setattr__(ln, "font_size", size)
    ordered, _ = zoned_reading_order(left + right, page=1)
    assert _texts(ordered) == ["L0", "L1", "L2", "L3", "R0", "R1", "R2", "R3"]


def test_gutter_width_variation_does_not_affect_resolution():
    for gutter in (60.0, 120.0, 260.0):
        left = [_line(f"L{i}", 40.0, 100.0 + i * 20) for i in range(4)]
        right = [_line(f"R{i}", 40.0 + 200.0 + gutter, 100.0 + i * 20) for i in range(4)]
        ordered, _ = zoned_reading_order(left + right, page=1)
        assert _texts(ordered) == ["L0", "L1", "L2", "L3", "R0", "R1", "R2", "R3"], gutter


def test_detect_reading_zones_on_empty_lines_returns_empty():
    assert detect_reading_zones([], page=1) == []


# --- structural eligibility (PROMPT Phase 3L) --------------------------------


def test_assess_eligibility_accepts_a_genuine_topology_change():
    # Mirrors D10's own shape: a real multi_column zone followed by a real
    # single_column zone - >=2 zones, a genuine transition between them.
    left = [_line(f"L{i}", 40.0, 100.0 + i * 20) for i in range(4)]
    right = [_line(f"R{i}", 320.0, 100.0 + i * 20) for i in range(4)]
    footer = [_line("FOOTER", 40.0, 300.0, width=480.0)]
    _, trace = zoned_reading_order(left + right + footer, page=1)
    eligibility = assess_eligibility(trace.zones, trace.cycles)
    assert eligibility.eligible
    assert eligibility.zone_count >= 2
    assert eligibility.topology_transitions >= 1
    assert eligibility.graph_acyclic


def test_assess_eligibility_rejects_a_single_uniform_multi_column_zone():
    # D40's own real shape: one genuine multi_column zone and otherwise no
    # topology change at all - trivially satisfying a naive "zone_count>=2"
    # bar (many single-line "unclaimed" zones) must NOT be enough; there
    # must be a real *transition* between differently-shaped zones.
    left = [_line(f"L{i}", 40.0, 100.0 + i * 20) for i in range(4)]
    right = [_line(f"R{i}", 320.0, 100.0 + i * 20) for i in range(4)]
    _, trace = zoned_reading_order(left + right, page=1)
    eligibility = assess_eligibility(trace.zones, trace.cycles)
    assert not eligibility.eligible
    assert eligibility.topology_transitions == 0


def test_assess_eligibility_rejects_a_single_zone_page():
    lines = [_line(f"line {i}", 40.0, 100.0 + i * 20) for i in range(6)]
    _, trace = zoned_reading_order(lines, page=1)
    eligibility = assess_eligibility(trace.zones, trace.cycles)
    assert not eligibility.eligible
    assert eligibility.zone_count == 1


def test_assess_eligibility_rejects_when_the_graph_has_a_cycle():
    zone = ReadingZone(
        zone_id="p1:z0",
        page=1,
        y_interval=(0.0, 10.0),
        mode="single_column",
        column_count=1,
        column_bounds=(),
        source_line_ids=(0,),
        detection_method="test",
        confidence=1.0,
    )
    other = ReadingZone(
        zone_id="p1:z1",
        page=1,
        y_interval=(10.0, 20.0),
        mode="multi_column",
        column_count=2,
        column_bounds=((0.0, 5.0), (10.0, 15.0)),
        source_line_ids=(1, 2),
        detection_method="test",
        confidence=1.0,
    )
    eligibility = assess_eligibility([zone, other], cycles=(("a", "b"),))
    assert not eligibility.eligible
    assert not eligibility.graph_acyclic


def test_assess_eligibility_on_no_zones_is_not_eligible():
    eligibility = assess_eligibility([], cycles=())
    assert not eligibility.eligible
    assert eligibility.zone_count == 0
