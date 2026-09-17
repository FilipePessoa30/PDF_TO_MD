"""Unit + metamorphic tests for same_row_ordering.py (PROMPT Phase 3N).

All fixtures are synthetic - round coordinates chosen only to exhibit a
named geometric shape ("two fragments sharing a true baseline but
different bbox tops", "a superscript", "a genuine next line") - never real
PDF coordinates or a specific question's own full text, matching this
project's own established convention (see test_reading_zones.py).
"""

from __future__ import annotations

from enade.extraction.layout import Line
from enade.extraction.same_row_ordering import (
    compute_same_row_relation,
    group_same_row_fragments,
    reorder_same_row_groups,
)


def _line(
    text: str,
    x0: float,
    y0: float,
    width: float = 40.0,
    height: float = 9.0,
    font_size: float = 9.0,
    baseline_y: float | None = None,
) -> Line:
    y1 = y0 + height
    return Line(
        page_number=1,
        text=text,
        x0=x0,
        y0=y0,
        x1=x0 + width,
        y1=y1,
        font_size=font_size,
        baseline_y=baseline_y if baseline_y is not None else y1 - 1.0,
    )


def _texts(lines: list[Line]) -> list[str]:
    return [ln.text for ln in lines]


# --- SameRowRelation classification ------------------------------------


def test_identical_baseline_different_bbox_top_is_same_row():
    # Mirrors D40's own real case: two fragments share the exact baseline
    # but one has a slightly different bbox top (a font-metrics artifact
    # of a different font run), inverting their apparent y0 order.
    left = _line("possui a relacao", 36.0, 100.0, baseline_y=108.0)
    right = _line("Cliente,", 134.3, 99.6, baseline_y=108.0)  # bbox y0 lower, same baseline
    relation = compute_same_row_relation(right, left)  # right (Cliente,) as "left" arg on purpose
    assert relation.classification == "same_row"
    assert relation.baseline_delta == 0.0


def test_genuine_next_printed_line_is_different_row():
    top = _line("first printed line", 36.0, 100.0, baseline_y=108.0)
    bottom = _line("second printed line", 36.0, 112.0, baseline_y=120.0)
    relation = compute_same_row_relation(top, bottom)
    assert relation.classification == "different_row"


def test_superscript_is_not_same_row():
    base = _line("x", 100.0, 100.0, font_size=10.0, baseline_y=108.0)
    exponent = _line("2", 108.0, 96.0, font_size=6.0, baseline_y=105.0)  # raised, smaller font
    relation = compute_same_row_relation(base, exponent)
    assert relation.classification == "superscript_or_subscript"


def test_subscript_is_not_same_row():
    base = _line("H", 100.0, 100.0, font_size=10.0, baseline_y=108.0)
    subscript = _line("2", 106.0, 103.0, font_size=6.0, baseline_y=111.0)  # lowered, smaller font
    relation = compute_same_row_relation(base, subscript)
    assert relation.classification == "superscript_or_subscript"


def test_ambiguous_mid_range_baseline_delta_is_never_same_row():
    # A moderate offset, same font size, some vertical overlap - not
    # confidently same-row (D40/Q33's own real cases have ~0 delta) and
    # not confidently a full different-row leading either.
    left = _line("left", 36.0, 100.0, font_size=10.0, baseline_y=108.0)
    right = _line("right", 80.0, 100.0, font_size=10.0, baseline_y=110.5)
    relation = compute_same_row_relation(left, right)
    assert relation.classification == "ambiguous"


def test_missing_true_baseline_is_never_same_row():
    left = _line("left", 36.0, 100.0, baseline_y=0.0)
    right = _line("right", 80.0, 100.0, baseline_y=108.0)
    relation = compute_same_row_relation(left, right)
    assert relation.classification == "ambiguous"
    assert "baseline" in relation.reason


def test_cross_column_pair_is_never_same_row_even_with_matching_baseline():
    left = _line("left column", 36.0, 100.0, baseline_y=108.0)
    right = _line("right column", 320.0, 100.0, baseline_y=108.0)
    relation = compute_same_row_relation(left, right, column_margins=(35.0, 305.0))
    assert relation.classification == "cross_column"


def test_different_region_pair_is_never_same_row():
    left = _line("statement text", 36.0, 100.0, baseline_y=108.0)
    right = _line("diagram label", 200.0, 100.0, baseline_y=108.0)
    relation = compute_same_row_relation(left, right, regions=((190.0, 90.0, 260.0, 115.0),))
    assert relation.classification == "different_region"


def test_both_inside_the_same_region_can_still_be_same_row():
    left = _line("cell one", 36.0, 100.0, baseline_y=108.0)
    right = _line("cell two", 60.0, 99.7, baseline_y=108.0)
    relation = compute_same_row_relation(left, right, regions=((30.0, 90.0, 200.0, 115.0),))
    assert relation.classification == "same_row"


def test_wide_horizontal_gap_relative_to_font_size_is_ambiguous():
    left = _line("left", 36.0, 100.0, font_size=9.0, baseline_y=108.0, width=10.0)
    right = _line("far right", 900.0, 100.0, font_size=9.0, baseline_y=108.0)
    relation = compute_same_row_relation(left, right)
    assert relation.classification == "ambiguous"


# --- grouping / complete-link -------------------------------------------


def test_two_fragments_same_row_form_a_group():
    lines = [
        _line("Cliente,", 134.3, 99.6, baseline_y=108.0),
        _line("possui a relacao", 36.0, 100.0, baseline_y=108.0),
    ]
    groups, _ = group_same_row_fragments(lines)
    assert len(groups) == 1
    assert set(groups[0].member_ids) == {0, 1}


def test_three_fragments_same_row_form_one_group():
    lines = [
        _line("com as informacoes", 185.8, 100.0, baseline_y=108.0),
        _line("Cliente,", 134.3, 99.6, baseline_y=108.0),
        _line("possui a relacao", 36.0, 100.0, baseline_y=108.0),
    ]
    groups, _ = group_same_row_fragments(lines)
    assert len(groups) == 1
    assert set(groups[0].member_ids) == {0, 1, 2}


def test_transitive_bridge_is_rejected_when_the_ends_are_incompatible():
    # A is same_row with B (small delta), B is same_row with C (small
    # delta from B), but A and C together exceed the same-row ceiling -
    # single-linkage would wrongly chain all three; complete-link must not.
    a = _line("A", 36.0, 100.0, font_size=10.0, baseline_y=108.0)
    b = _line("B", 80.0, 100.0, font_size=10.0, baseline_y=108.5)
    c = _line("C", 130.0, 100.0, font_size=10.0, baseline_y=109.0)
    lines = [a, b, c]
    groups, relations = group_same_row_fragments(lines)
    # A-B and B-C are each within the same-row ceiling; A-C is exactly
    # twice that delta - outside it.
    assert relations[(0, 1)].classification == "same_row"
    assert relations[(1, 2)].classification == "same_row"
    assert relations[(0, 2)].classification != "same_row"
    # No 3-member group may form - A and C are not compatible.
    assert not any(set(g.member_ids) == {0, 1, 2} for g in groups)


def test_ungrouped_fragment_stays_alone():
    lines = [
        _line("alone", 36.0, 100.0, baseline_y=108.0),
        _line("also alone, far below", 36.0, 300.0, baseline_y=308.0),
    ]
    groups, _ = group_same_row_fragments(lines)
    assert groups == []


def test_cross_column_fragments_never_group_despite_same_baseline():
    lines = [
        _line("left column text", 36.0, 100.0, baseline_y=108.0),
        _line("right column text", 320.0, 100.0, baseline_y=108.0),
    ]
    groups, _ = group_same_row_fragments(lines, column_margins=(35.0, 305.0))
    assert groups == []


def test_diagram_label_never_groups_with_statement_text_across_a_region():
    lines = [
        _line("statement text", 36.0, 100.0, baseline_y=108.0),
        _line("Computador A", 200.0, 100.0, baseline_y=108.0),
    ]
    groups, _ = group_same_row_fragments(lines, regions=((190.0, 90.0, 260.0, 115.0),))
    assert groups == []


# --- horizontal reordering ------------------------------------------------


def test_reorder_places_group_members_by_x0_within_original_slots():
    lines = [
        _line("com as informacoes", 185.8, 100.0, baseline_y=108.0),
        _line("Cliente,", 134.3, 99.6, baseline_y=108.0),
        _line("possui a relacao", 36.0, 100.0, baseline_y=108.0),
    ]
    groups, _ = group_same_row_fragments(lines)
    reordered, notes = reorder_same_row_groups(lines, groups)
    assert _texts(reordered) == ["possui a relacao", "Cliente,", "com as informacoes"]
    assert len(notes) == 1


def test_reorder_is_a_pure_permutation_never_changes_word_multiset():
    lines = [
        _line("com as informacoes", 185.8, 100.0, baseline_y=108.0),
        _line("Cliente,", 134.3, 99.6, baseline_y=108.0),
        _line("possui a relacao", 36.0, 100.0, baseline_y=108.0),
    ]
    groups, _ = group_same_row_fragments(lines)
    reordered, _ = reorder_same_row_groups(lines, groups)
    assert sorted(_texts(reordered)) == sorted(_texts(lines))
    assert len(reordered) == len(lines)


def test_reorder_leaves_ungrouped_lines_completely_untouched():
    grouped_a = _line("Cliente,", 134.3, 99.6, baseline_y=108.0)
    grouped_b = _line("possui a relacao", 36.0, 100.0, baseline_y=108.0)
    unrelated_before = _line("unrelated earlier line", 36.0, 50.0, baseline_y=58.0)
    unrelated_after = _line("unrelated later line", 36.0, 200.0, baseline_y=208.0)
    lines = [unrelated_before, grouped_a, grouped_b, unrelated_after]
    groups, _ = group_same_row_fragments(lines)
    reordered, _ = reorder_same_row_groups(lines, groups)
    assert reordered[0] is unrelated_before
    assert reordered[3] is unrelated_after
    assert _texts(reordered[1:3]) == ["possui a relacao", "Cliente,"]


def test_reorder_with_no_groups_returns_input_unchanged_and_no_notes():
    lines = [_line("only", 36.0, 100.0, baseline_y=108.0)]
    reordered, notes = reorder_same_row_groups(lines, [])
    assert reordered == lines
    assert notes == []


def test_already_correctly_ordered_group_produces_no_note():
    lines = [
        _line("possui a relacao", 36.0, 100.0, baseline_y=108.0),
        _line("Cliente,", 134.3, 99.6, baseline_y=108.0),
        _line("com as informacoes", 185.8, 100.0, baseline_y=108.0),
    ]
    groups, _ = group_same_row_fragments(lines)
    reordered, notes = reorder_same_row_groups(lines, groups)
    assert _texts(reordered) == _texts(lines)
    assert notes == []


# --- metamorphic tests -----------------------------------------------------


def test_translation_invariance():
    lines = [
        _line("com as informacoes", 185.8, 100.0, baseline_y=108.0),
        _line("Cliente,", 134.3, 99.6, baseline_y=108.0),
        _line("possui a relacao", 36.0, 100.0, baseline_y=108.0),
    ]
    shifted = [
        _line(ln.text, ln.x0 + 200.0, ln.y0 + 300.0, baseline_y=ln.baseline_y + 300.0)
        for ln in lines
    ]
    groups_a, _ = group_same_row_fragments(lines)
    groups_b, _ = group_same_row_fragments(shifted)
    reordered_a, _ = reorder_same_row_groups(lines, groups_a)
    reordered_b, _ = reorder_same_row_groups(shifted, groups_b)
    assert _texts(reordered_a) == _texts(reordered_b)


def test_uniform_scale_invariance():
    lines = [
        _line("com as informacoes", 185.8, 100.0, font_size=9.0, baseline_y=108.0),
        _line("Cliente,", 134.3, 99.6, font_size=9.0, baseline_y=108.0),
        _line("possui a relacao", 36.0, 100.0, font_size=9.0, baseline_y=108.0),
    ]
    scale = 2.0
    scaled = [
        _line(
            ln.text,
            ln.x0 * scale,
            ln.y0 * scale,
            width=(ln.x1 - ln.x0) * scale,
            font_size=ln.font_size * scale,
            baseline_y=ln.baseline_y * scale,
        )
        for ln in lines
    ]
    groups_a, _ = group_same_row_fragments(lines)
    groups_b, _ = group_same_row_fragments(scaled)
    reordered_a, _ = reorder_same_row_groups(lines, groups_a)
    reordered_b, _ = reorder_same_row_groups(scaled, groups_b)
    assert _texts(reordered_a) == _texts(reordered_b)


def test_content_stream_order_does_not_affect_grouping_or_reorder():
    lines = [
        _line("com as informacoes", 185.8, 100.0, baseline_y=108.0),
        _line("Cliente,", 134.3, 99.6, baseline_y=108.0),
        _line("possui a relacao", 36.0, 100.0, baseline_y=108.0),
    ]
    reversed_lines = list(reversed(lines))
    groups_a, _ = group_same_row_fragments(lines)
    groups_b, _ = group_same_row_fragments(reversed_lines)
    reordered_a, _ = reorder_same_row_groups(lines, groups_a)
    reordered_b, _ = reorder_same_row_groups(reversed_lines, groups_b)
    assert _texts(reordered_a) == _texts(reordered_b)


def test_small_additional_y0_jitter_within_ceiling_does_not_change_result():
    base_lines = [
        _line("com as informacoes", 185.8, 100.0, baseline_y=108.0),
        _line("Cliente,", 134.3, 99.6, baseline_y=108.0),
        _line("possui a relacao", 36.0, 100.0, baseline_y=108.0),
    ]
    jittered = [_line(ln.text, ln.x0, ln.y0 + 0.02, baseline_y=ln.baseline_y) for ln in base_lines]
    groups_a, _ = group_same_row_fragments(base_lines)
    groups_b, _ = group_same_row_fragments(jittered)
    reordered_a, _ = reorder_same_row_groups(base_lines, groups_a)
    reordered_b, _ = reorder_same_row_groups(jittered, groups_b)
    assert _texts(reordered_a) == _texts(reordered_b)


def test_source_identity_change_without_structural_change_does_not_affect_decision():
    # Equivalent to "the source PDF hash changed but nothing structural
    # did" - fresh Line objects, no shared identity, same shape.
    def _build():
        return [
            _line("com as informacoes", 185.8, 100.0, baseline_y=108.0),
            _line("Cliente,", 134.3, 99.6, baseline_y=108.0),
            _line("possui a relacao", 36.0, 100.0, baseline_y=108.0),
        ]

    groups_a, _ = group_same_row_fragments(_build())
    groups_b, _ = group_same_row_fragments(_build())
    reordered_a, _ = reorder_same_row_groups(_build(), groups_a)
    reordered_b, _ = reorder_same_row_groups(_build(), groups_b)
    assert _texts(reordered_a) == _texts(reordered_b)


def test_sub_point_noise_versus_true_second_line_boundary():
    """The explicit boundary test PROMPT section 32 asks for: a same-row
    pair (delta well inside the ceiling) versus a pair at exactly a real
    line-to-line leading (delta at the different-row floor) must classify
    oppositely, with nothing in between silently guessed as either.
    """
    same_row_pair = compute_same_row_relation(
        _line("a", 36.0, 100.0, font_size=10.0, baseline_y=108.0),
        _line("b", 80.0, 99.5, font_size=10.0, baseline_y=108.0),
    )
    different_row_pair = compute_same_row_relation(
        _line("a", 36.0, 100.0, font_size=10.0, baseline_y=108.0),
        _line("b", 36.0, 112.0, font_size=10.0, baseline_y=120.0),
    )
    assert same_row_pair.classification == "same_row"
    assert different_row_pair.classification == "different_row"
