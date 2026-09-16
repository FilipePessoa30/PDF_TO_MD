"""Unit + metamorphic tests for annotations.py (PROMPT Phase 3J).

All fixtures are synthetic (round coordinates chosen only to exhibit a
named geometric shape - "bunched at the end", "already adjacent",
"partial item set") - never real PDF coordinates and never Q13/D60's own
text, per the phase's own explicit constraint that a test must not depend
on a fixed page, copied coordinates, or a specific question's full text.
"""

from __future__ import annotations

from enade.extraction.annotations import (
    DocumentAnnotation,
    _find_item_markers,
    reattach_value_annotations,
)
from enade.extraction.layout import Line


def _line(text: str, y0: float, page: int = 1, x0: float = 36.0) -> Line:
    return Line(page_number=page, text=text, x0=x0, y0=y0, x1=x0 + 100.0, y1=y0 + 10.0)


def _item(letter: str, y0: float, text: str = "some item text.", **kw) -> Line:
    return _line(f"{letter} {text}", y0, **kw)


def _value(amount: str, y0: float, **kw) -> Line:
    return _line(f"(valor: {amount} pontos)", y0, **kw)


# --- no-op cases -------------------------------------------------------


def test_no_value_annotation_is_a_true_identity_noop():
    lines = [_line("Some prose.", 10.0), _item("A", 20.0), _item("B", 30.0)]
    result, trace = reattach_value_annotations(lines)
    assert result is lines
    assert trace == []


def test_fused_inline_annotation_is_never_detected():
    # The value text shares a line with the item's own content - not a
    # standalone annotation line, so the whole-line regex never matches.
    lines = [_item("A", 10.0, text="do the thing. (valor: 3,0 pontos)")]
    result, trace = reattach_value_annotations(lines)
    assert result is lines
    assert trace == []


def test_single_overall_value_with_no_items_is_left_in_place():
    lines = [_line("Write an essay.", 10.0), _value("10,0", 20.0)]
    result, trace = reattach_value_annotations(lines)
    assert [ln.text for ln in result] == [ln.text for ln in lines]
    assert len(trace) == 1
    assert trace[0].owner_item_letter is None
    assert trace[0].reattached is False


def test_already_correctly_interleaved_annotations_are_a_content_noop():
    # D80's own real shape: each item immediately followed by its own
    # annotation, already in true reading order - nothing should move.
    lines = [
        _item("A", 10.0),
        _value("4,0", 15.0),
        _item("B", 30.0),
        _value("6,0", 35.0),
    ]
    result, trace = reattach_value_annotations(lines)
    assert [ln.text for ln in result] == [ln.text for ln in lines]
    assert all(not a.reattached for a in trace)
    assert [a.owner_item_letter for a in trace] == ["A", "B"]


# --- the real defect shape (D60) ----------------------------------------


def test_annotations_bunched_after_the_last_item_are_redistributed():
    lines = [
        _item("A", 10.0),
        _item("B", 30.0),
        _item("C", 50.0),
        _value("3,0", 15.0),  # structurally within A's own span [10, 30)
        _value("3,0", 35.0),  # within B's own span [30, 50)
        _value("4,0", 55.0),  # within C's own span [50, inf)
    ]
    result, trace = reattach_value_annotations(lines)
    assert [ln.text for ln in result] == [
        "A some item text.",
        "(valor: 3,0 pontos)",
        "B some item text.",
        "(valor: 3,0 pontos)",
        "C some item text.",
        "(valor: 4,0 pontos)",
    ]
    by_owner = {a.owner_item_letter: a.text for a in trace}
    assert by_owner == {
        "A": "(valor: 3,0 pontos)",
        "B": "(valor: 3,0 pontos)",
        "C": "(valor: 4,0 pontos)",
    }
    assert all(a.reattached for a in trace if a.owner_item_letter in ("A", "B"))


def test_partial_item_set_two_items_still_resolves():
    # Only A and B present (a 2-item discursive question, like D20/D80) -
    # the mechanism must not require a full A-E run.
    lines = [
        _item("A", 10.0),
        _item("B", 30.0),
        _value("5,0", 12.0),
        _value("7,0", 32.0),
    ]
    result, trace = reattach_value_annotations(lines)
    assert [ln.text for ln in result] == [
        "A some item text.",
        "(valor: 5,0 pontos)",
        "B some item text.",
        "(valor: 7,0 pontos)",
    ]


def test_annotation_before_the_first_item_defaults_to_the_first_item():
    lines = [_value("1,0", 5.0), _item("A", 10.0), _item("B", 30.0)]
    result, trace = reattach_value_annotations(lines)
    assert trace[0].owner_item_letter == "A"
    assert [ln.text for ln in result] == [
        "A some item text.",
        "(valor: 1,0 pontos)",
        "B some item text.",
    ]


# --- text pattern variations ---------------------------------------------


def test_decimal_dot_and_singular_ponto_are_recognized():
    lines = [_item("A", 10.0), _line("(valor: 1.5 ponto)", 15.0)]
    result, trace = reattach_value_annotations(lines)
    assert len(trace) == 1
    assert trace[0].annotation_type == "question_value"


def test_ordinary_prose_is_never_reordered_when_no_value_annotation_exists():
    # _find_item_markers alone is deliberately naive (same bare-letter
    # shape as alternative_groups's own known false positive, "A chance
    # de..."): safety comes from reattach_value_annotations's own early
    # exit when no value-annotation-shaped line is present at all - the
    # overwhelming majority of spans, objective and discursive alike, and
    # every real question in this corpus with plain prose starting with a
    # bare capital letter but no "(valor: ...)" annotation.
    lines = [_line("A chance de algo acontecer e alta.", 10.0)]
    assert _find_item_markers(lines) == [("A", 0)]
    result, trace = reattach_value_annotations(lines)
    assert result is lines
    assert trace == []


# --- metamorphic tests -----------------------------------------------------


def test_translation_invariance():
    base = [
        _item("A", 10.0),
        _item("B", 30.0),
        _value("3,0", 15.0),
        _value("4,0", 35.0),
    ]
    shifted = [_line(ln.text, ln.y0 + 500.0, x0=ln.x0 + 200.0) for ln in base]
    base_result, _ = reattach_value_annotations(base)
    shifted_result, _ = reattach_value_annotations(shifted)
    assert [ln.text for ln in base_result] == [ln.text for ln in shifted_result]


def test_scale_invariance():
    base = [
        _item("A", 10.0),
        _item("B", 30.0),
        _item("C", 50.0),
        _value("3,0", 15.0),
        _value("3,0", 35.0),
        _value("4,0", 55.0),
    ]
    scaled = [_line(ln.text, ln.y0 * 3.0) for ln in base]
    base_result, _ = reattach_value_annotations(base)
    scaled_result, _ = reattach_value_annotations(scaled)
    assert [ln.text for ln in base_result] == [ln.text for ln in scaled_result]


def test_page_change_between_items_is_respected():
    lines = [
        _item("A", 700.0, page=1),
        _item("B", 50.0, page=2),
        _value("3,0", 705.0, page=1),
        _value("4,0", 55.0, page=2),
    ]
    result, trace = reattach_value_annotations(lines)
    by_owner = {a.owner_item_letter: a.text for a in trace}
    assert by_owner == {"A": "(valor: 3,0 pontos)", "B": "(valor: 4,0 pontos)"}


def test_content_stream_order_does_not_affect_owner_computation():
    # Same geometry, different input list order (the annotations appear
    # first this time) - ownership must depend only on (page, y0), never
    # on position within the input list.
    lines = [
        _value("3,0", 15.0),
        _value("4,0", 35.0),
        _item("A", 10.0),
        _item("B", 30.0),
    ]
    _, trace = reattach_value_annotations(lines)
    by_owner = {a.owner_item_letter: a.text for a in trace}
    assert by_owner == {"A": "(valor: 3,0 pontos)", "B": "(valor: 4,0 pontos)"}


def test_document_annotation_is_frozen_and_hashable():
    a = DocumentAnnotation(
        annotation_type="question_value",
        text="(valor: 1,0 pontos)",
        source_page=1,
        source_line_index=0,
        owner_item_letter="A",
        reattached=False,
    )
    hash(a)  # must not raise
