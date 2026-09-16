"""Unit tests for ``assembler._canonical_content_lines`` (PROMPT Phase 3L).

All fixtures are synthetic - round coordinates chosen only to exhibit a
named geometric shape, never real PDF coordinates or a specific question's
own full text (same convention as test_reading_zones.py). Each fixture is
named after the real 2008-b question whose own reported shape it mirrors,
so a reader can trace every assertion back to the phase-3l-report.md
narrative without this file depending on the real corpus being present.
"""

from __future__ import annotations

from enade.extraction.assembler import _canonical_content_lines
from enade.extraction.figures import VisualRegion
from enade.extraction.layout import Line


def _line(text: str, x0: float, y0: float, width: float = 200.0, height: float = 10.0) -> Line:
    return Line(page_number=1, text=text, x0=x0, y0=y0, x1=x0 + width, y1=y0 + height)


def _texts(lines: list[Line]) -> list[str]:
    return [ln.text for ln in lines]


# --- disabled mode is always a true no-op ------------------------------------


def test_disabled_mode_never_computes_zones():
    left = [_line(f"L{i}", 40.0, 100.0 + i * 20) for i in range(4)]
    right = [_line(f"R{i}", 320.0, 100.0 + i * 20) for i in range(4)]
    lines = left + right  # out-of-reading-order on purpose
    result, notes = _canonical_content_lines(lines, "disabled", [], [])
    assert result == lines
    assert notes == []


# --- D10-shaped collage: automatic activation, no override, no note ---------


def _d10_shaped_page() -> list[Line]:
    # Photo+article (two-column, concurrent), full-width prose, then a
    # second genuine two-column zone - the same three-transition shape as
    # test_reading_zones.py::test_topology_changes_more_than_once_matches_d10s_own_shape,
    # with no item/alternative marker anywhere on the page (matching D10's
    # own real span, whose only "A"-shaped line is a lone sentence-opening
    # "A" that never reaches a "B").
    article = [_line(f"art{i}", 320.0, 100.0 + i * 15) for i in range(5)]
    caption = [_line("photo caption", 145.0, 190.0, width=95.0)]
    prose = [_line(f"prose{i}", 40.0, 300.0 + i * 15, width=480.0) for i in range(4)]
    bullets_left = [_line(f"bl{i}", 51.0, 500.0 + i * 15, width=250.0) for i in range(3)]
    bullets_right = [_line(f"br{i}", 333.0, 500.0 + i * 15, width=200.0) for i in range(3)]
    return article + caption + prose + bullets_left + bullets_right


def test_d10_shaped_collage_activates_automatically_with_no_note():
    # The zone/graph resolution is geometric, never order-dependent (see
    # test_reading_zones.py's own metamorphic tests) - feeding the page in
    # reverse of its own correct reading order exercises the same
    # detection/resolution the correctly-ordered fixture would, while
    # guaranteeing the published result actually differs from this
    # (deliberately scrambled) input, the same way a real PDF's own
    # content-stream order need not match reading order at all.
    scrambled = list(reversed(_d10_shaped_page()))
    result, notes = _canonical_content_lines(scrambled, "active", [], [])
    names = _texts(result)
    assert names != _texts(scrambled)
    assert names.index("art4") < names.index("prose0")
    assert names.index("prose3") < names.index("bl0")
    # Successful activation is silent - a reorder is never itself a
    # warning-shaped event (ExtractedQuestion.zone_reorder_notes exists
    # precisely so a *rejection* can be recorded without ever touching
    # `warnings`; a clean success records nothing at all).
    assert notes == []
    # A pure permutation: no line lost, none duplicated, none invented.
    assert sorted(names) == sorted(_texts(scrambled))


def test_d10_shaped_collage_in_shadow_mode_never_changes_the_published_order():
    scrambled = list(reversed(_d10_shaped_page()))
    result, notes = _canonical_content_lines(scrambled, "shadow", [], [])
    assert _texts(result) == _texts(scrambled)
    assert len(notes) == 1
    assert "shadow" in notes[0]
    assert "eligible" in notes[0]


# --- marker boundary: a real A,B,... sequence freezes itself and everything after --


def test_marker_boundary_freezes_the_marker_sequence_and_everything_after_it():
    # An eligible two-column intro (same shape as the D10 zone above) is
    # immediately followed, on the very same page, by a genuine two-item
    # discursive marker sequence ("A", then "B") - mirrors 2008-b D40's own
    # page. Reordering must never reach the markers themselves or anything
    # printed after them, regardless of how eligible the intro looks.
    left = [_line(f"L{i}", 40.0, 100.0 + i * 20) for i in range(4)]
    right = [_line(f"R{i}", 320.0, 100.0 + i * 20) for i in range(4)]
    marker_a = _line("A primeiro item", 40.0, 300.0, width=480.0)
    marker_b = _line("B segundo item", 40.0, 320.0, width=480.0)
    lines = left + right + [marker_a, marker_b]

    result, notes = _canonical_content_lines(lines, "active", [], [])

    # The frozen suffix survives at the tail, byte-identical objects, in
    # their own original relative order.
    assert result[-2] is marker_a
    assert result[-1] is marker_b
    # The eligible prefix (the two genuine columns) was free to reorder
    # among itself.
    assert set(id(ln) for ln in result[:-2]) == set(id(ln) for ln in left + right)
    assert notes == []


def test_a_lone_sentence_opening_a_does_not_count_as_a_marker_sequence():
    # A single "A"-shaped line with no matching "B" afterwards (D10's own
    # real case: "A partir da leitura dos fragmentos...") must not freeze
    # anything - len(item_markers) == 1 never counts as a real sequence.
    left = [_line(f"L{i}", 40.0, 100.0 + i * 20) for i in range(4)]
    right = [_line(f"R{i}", 320.0, 100.0 + i * 20) for i in range(4)]
    lone_a = _line("A partir da leitura dos fragmentos motivadores", 40.0, 300.0, width=480.0)
    lines = left + right + [lone_a]

    result, notes = _canonical_content_lines(lines, "active", [], [])

    names = _texts(result)
    assert names[-1] == lone_a.text  # still last, by y0, but not "frozen" - reordered normally
    assert notes == []


# --- D40-shaped uniform topology: structurally not eligible, silently kept --


def test_uniform_two_column_page_is_not_eligible_and_produces_no_note():
    # A single genuine two-column zone and nothing else on the page - zero
    # topology *transitions* (D40's own real shape once assess_eligibility,
    # not just the marker boundary, is what rejects it - see
    # test_reading_zones.py::test_assess_eligibility_rejects_a_single_uniform_multi_column_zone).
    left = [_line(f"L{i}", 40.0, 100.0 + i * 20) for i in range(4)]
    right = [_line(f"R{i}", 320.0, 100.0 + i * 20) for i in range(4)]
    lines = left + right
    result, notes = _canonical_content_lines(lines, "active", [], [])
    # Still resolves to the conventional left-then-right order (the same
    # order the old, page-wide algorithm always produced for a genuine
    # single two-column zone) - not left untouched in raw content-stream
    # order, but never a *note*, since ineligible pages are not even a
    # candidate for activation.
    assert _texts(result) == ["L0", "L1", "L2", "L3", "R0", "R1", "R2", "R3"]
    assert notes == []


# --- Q50-shaped safety-oracle rejection: eligible but unsafe -----------------


def _q50_shaped_lines_and_region() -> tuple[list[Line], VisualRegion]:
    # Two zones: a top single_column zone (only right-side evidence, "art"),
    # and a bottom multi_column zone (genuine, concurrent bl/br evidence) -
    # zone_count=2, one real transition, so this IS eligible. The candidate
    # order (resolve_reading_order, purely geometric) always resolves the
    # bottom zone as bl-then-br; ``lines`` below is deliberately given in
    # the *opposite* (br-then-bl) relative order - standing in for a real
    # page whose own stable, page-wide split disagreed with zone-local
    # resolution about which side reads first (Q50's own real regression,
    # Phase 3L section D/K). A region whose own insertion point falls
    # *inside* the bottom zone (between the first and second row) then
    # lands in front of a different line depending on which of the two
    # orderings is used - br0 in the original order, bl0 in the candidate
    # order - which is exactly what insertion_points_conserved must catch.
    art = [_line(f"art{i}", 320.0, 100.0 + i * 15) for i in range(3)]
    bl = [_line(f"bl{i}", 40.0, 300.0 + i * 15) for i in range(3)]
    br = [_line(f"br{i}", 320.0, 300.0 + i * 15) for i in range(3)]
    lines = art + br + bl
    region = VisualRegion(page_number=1, bbox=(300.0, 310.0, 500.0, 350.0), element_count=1)
    return lines, region


def test_eligible_candidate_rejected_by_the_safety_oracle_leaves_a_note_and_original_order():
    lines, region = _q50_shaped_lines_and_region()

    result, notes = _canonical_content_lines(lines, "active", [region], [])

    # Rejected: original (stable) order is exactly what is published.
    assert _texts(result) == _texts(lines)
    assert len(notes) == 1
    assert "rejected by the safety oracle" in notes[0]
    assert "page 1" in notes[0]


def test_safety_oracle_rejection_note_is_never_surfaced_as_a_warning():
    # The dedicated return channel (a plain list of strings, separate from
    # ExtractedQuestion.warnings) is itself the fix for a real regression
    # (Q50's own automatic_validation/extraction_status flipping on a safe
    # rejection) - this test pins the *shape* of the contract: notes is
    # its own list, never merged into anything else by this function.
    lines, region = _q50_shaped_lines_and_region()

    result, notes = _canonical_content_lines(lines, "active", [region], [])

    assert isinstance(notes, list)
    assert all(isinstance(n, str) for n in notes)
    # The function has no knowledge of `warnings` at all - it returns only
    # the reordered lines and its own notes list.


# --- multi-page spans: reordering never crosses a page boundary -------------


def test_reordering_is_computed_independently_per_page():
    page1_left = [_line(f"p1L{i}", 40.0, 100.0 + i * 20) for i in range(4)]
    page1_right = [_line(f"p1R{i}", 320.0, 100.0 + i * 20) for i in range(4)]
    page1 = page1_left + page1_right
    for ln in page1:
        object.__setattr__(ln, "page_number", 1)

    page2_left = [_line(f"p2L{i}", 40.0, 100.0 + i * 20) for i in range(4)]
    page2_right = [_line(f"p2R{i}", 320.0, 100.0 + i * 20) for i in range(4)]
    page2 = page2_left + page2_right
    for ln in page2:
        object.__setattr__(ln, "page_number", 2)

    lines = page1 + page2
    result, notes = _canonical_content_lines(lines, "active", [], [])
    names = _texts(result)
    assert names == ["p1L0", "p1L1", "p1L2", "p1L3", "p1R0", "p1R1", "p1R2", "p1R3"] + [
        "p2L0",
        "p2L1",
        "p2L2",
        "p2L3",
        "p2R0",
        "p2R1",
        "p2R2",
        "p2R3",
    ]
    assert notes == []


# --- metamorphic: a structurally-identical page is decided identically ------
# regardless of a changed source file hash (PROMPT Phase 3L section 26) - the
# eligibility/safety mechanism never reads a hash or any document identity at
# all, only the geometry passed to it, so two calls with the very same shape
# but no shared identity (fresh Line objects each time, standing in for "the
# same structural page extracted from two different source files") must
# reach the same decision.


def test_eligibility_and_safety_are_unaffected_by_a_changed_source_identity():
    first_call_result, first_notes = _canonical_content_lines(_d10_shaped_page(), "active", [], [])
    second_call_result, second_notes = _canonical_content_lines(
        _d10_shaped_page(), "active", [], []
    )
    assert _texts(first_call_result) == _texts(second_call_result)
    assert first_notes == second_notes == []
