"""Unit and metamorphic tests for structural alternative-group detection
(PROMPT Phase 3I) - alternative_groups.py.

Every fixture is synthetic (never a real corpus coordinate/page/question
ID/text - PROMPT section 24). Real-corpus validation (Q71/Q29) lives in
test_extraction_pipeline_2008.py.
"""

from __future__ import annotations

from enade.extraction.alternative_groups import (
    LATIN_UPPER_SCHEME,
    MARGIN_TOLERANCE,
    find_alternative_group,
)
from enade.extraction.layout import Line


def _line(text: str, x0: float, y0: float, page: int = 1, width: float = 200.0) -> Line:
    return Line(page_number=page, text=text, x0=x0, y0=y0, x1=x0 + width, y1=y0 + 12)


def _full_sequence(margin: float = 30.0, start_y: float = 100.0, step: float = 20.0) -> list[Line]:
    return [
        _line(f"{letter}\t texto da alternativa {letter}", margin, start_y + i * step)
        for i, letter in enumerate(LATIN_UPPER_SCHEME)
    ]


# --- Candidates / basic resolution ------------------------------------------


def test_full_sequence_resolves():
    lines = _full_sequence()
    group = find_alternative_group(lines)
    assert group is not None
    assert group.status == "resolved"
    assert group.is_usable
    assert [group.accepted[letter] for letter in LATIN_UPPER_SCHEME] == [0, 1, 2, 3, 4]
    assert group.competing == {}


def test_no_e_at_all_returns_none():
    lines = [_line("A\t texto", 30.0, 100.0), _line("B\t texto", 30.0, 120.0)]
    assert find_alternative_group(lines) is None


def test_partial_sequence_is_incomplete():
    lines = [
        _line("A\t texto", 30.0, 100.0),
        _line("B\t texto", 30.0, 120.0),
        _line("E\t texto", 30.0, 140.0),
        # missing C, D before E
    ]
    group = find_alternative_group(lines)
    assert group is not None
    assert group.status == "incomplete"
    assert not group.is_usable


def test_invalid_order_is_incomplete():
    """E appears before D/C in reading order - no valid D/C candidate
    exists *before* E's own position, so the sequence cannot resolve.
    """
    lines = [
        _line("A\t texto", 30.0, 100.0),
        _line("B\t texto", 30.0, 120.0),
        _line("E\t texto", 30.0, 140.0),
        _line("D\t texto", 30.0, 160.0),
        _line("C\t texto", 30.0, 180.0),
    ]
    group = find_alternative_group(lines)
    assert group is not None
    assert group.status == "incomplete"


# --- Competing candidates / margin-based disambiguation ---------------------


def test_real_regression_shape_wrapped_prose_mistaken_for_marker():
    """The confirmed Q71 shape: alternative B's own prose wraps onto a
    second line that also matches the marker shape for 'C', offset well
    to the right of the real markers' own shared margin. The real C
    marker (at the shared margin) must win.
    """
    margin = 30.0
    lines = [
        _line("A\t texto da alternativa A", margin, 100.0),
        _line("B\t inicio da alternativa B", margin, 120.0),
        _line("C mas nao e isso, e continuacao de B", margin + 20.0, 135.0),  # false candidate
        _line("C\t texto da alternativa C", margin, 150.0),  # real marker
        _line("D\t texto da alternativa D", margin, 170.0),
        _line("E\t texto da alternativa E", margin, 190.0),
    ]
    group = find_alternative_group(lines)
    assert group is not None
    assert group.status == "resolved"
    assert "C" in group.competing
    assert group.accepted["C"] == 3  # the real, margin-aligned marker


def test_two_on_margin_candidates_plus_one_off_margin_resolves_via_reading_order():
    """Real regression found and fixed this phase (2008-b Q28/Q52): margin
    partitions this letter's own candidates (one clearly off-margin), but
    TWO candidates remain on-margin - resolved deterministically via
    reading order (last of the on-margin subset) rather than blocked as
    ambiguous. An earlier, stricter version of this algorithm treated this
    exact shape as unresolvable and wrongly excluded both real questions
    entirely - see the module's own docstring for the full narrative.
    """
    margin = 30.0
    lines = [
        _line("A\t texto A", margin, 100.0),
        _line("B\t texto B", margin, 120.0),
        _line("C\t primeira candidata na margem", margin, 140.0),
        _line("C\t segunda candidata tambem na margem", margin, 155.0),
        _line("C fora da margem, apenas para confirmar particao", margin + 50.0, 165.0),
        _line("D\t texto D", margin, 180.0),
        _line("E\t texto E", margin, 200.0),
    ]
    group = find_alternative_group(lines)
    assert group is not None
    assert group.status == "resolved"
    assert group.is_usable
    assert "C" in group.competing
    assert group.accepted["C"] == 3  # last of the on-margin subset, off-margin one excluded


def test_all_candidates_sharing_the_body_margin_defer_to_reading_order():
    """When margin cannot discriminate at all (every candidate for this
    letter sits at the very same margin, e.g. two real-looking markers
    with no off-margin outlier to contrast against), the mechanism defers
    to the pre-existing, already-validated reading-order preference (the
    last candidate before the next letter) rather than inventing new
    ambiguity that was never flagged before this phase.
    """
    margin = 30.0
    lines = [
        _line("A\t texto A", margin, 100.0),
        _line("B\t texto B", margin, 120.0),
        _line("C\t primeira candidata", margin, 140.0),
        _line("C\t segunda candidata", margin, 160.0),
        _line("D\t texto D", margin, 180.0),
        _line("E\t texto E", margin, 200.0),
    ]
    group = find_alternative_group(lines)
    assert group is not None
    assert group.status == "resolved"
    assert "C" in group.competing
    assert group.accepted["C"] == 3  # last-wins, matching the pre-existing heuristic


def test_candidate_far_from_reference_margin_never_wins_over_a_single_aligned_one():
    """Even when the off-margin candidate comes later in reading order
    (the old algorithm's own preference), the margin-aligned one wins.
    """
    margin = 30.0
    lines = [
        _line("A\t texto A", margin, 100.0),
        _line("B\t texto B", margin, 120.0),
        _line("C\t texto C real", margin, 140.0),
        _line("C parece marcador mas nao esta na margem", margin + 50.0, 155.0),
        _line("D\t texto D", margin, 170.0),
        _line("E\t texto E", margin, 190.0),
    ]
    group = find_alternative_group(lines)
    assert group is not None
    assert group.status == "resolved"
    assert group.accepted["C"] == 2


def test_single_candidate_per_letter_ignores_margin_entirely():
    """When a letter has only one candidate, it is always accepted
    regardless of how far it sits from the reference margin - no
    competition, no ambiguity, matching the old algorithm's own behavior
    for the overwhelming majority of real questions.
    """
    lines = [
        _line("A\t texto A", 30.0, 100.0),
        _line("B\t texto B", 30.0, 120.0),
        _line("C\t texto C", 90.0, 140.0),  # only candidate for C, off-margin
        _line("D\t texto D", 30.0, 160.0),
        _line("E\t texto E", 30.0, 180.0),
    ]
    group = find_alternative_group(lines)
    assert group is not None
    assert group.status == "resolved"
    assert group.accepted["C"] == 2


# --- Reference margin ---------------------------------------------------


def test_reference_margin_is_the_mode_of_all_candidates():
    lines = _full_sequence(margin=42.0)
    group = find_alternative_group(lines)
    assert group is not None
    assert group.reference_margin == 42.0


def test_reference_margin_requires_at_least_two_votes():
    """A single-vote mode (every candidate at its own distinct x0) is not
    trusted as a real margin at all - ``reference_margin`` is None.
    """
    lines = [
        _line("A\t texto A", 30.0, 100.0),
        _line("B\t texto B", 90.0, 120.0),
        _line("C\t texto C", 150.0, 140.0),
        _line("D\t texto D", 210.0, 160.0),
        _line("E\t texto E", 270.0, 180.0),
    ]
    group = find_alternative_group(lines)
    assert group is not None
    assert group.reference_margin is None


def test_horizontal_grid_layout_with_no_shared_margin_defers_to_reading_order():
    """Real regression found and fixed this phase (2011 Q39, page 25):
    alternatives laid out horizontally, one per column on the same row
    ("A I.  B II.  C I e III. ..."), each at its own genuinely distinct
    x0 - there is no shared margin at all. A false 'A'-shaped candidate
    (a judged item's own text starting with the capitalized word "A...")
    happens to coincidentally match the *first-collected* letter's own
    x0 well enough that an earlier, naive mode computation without a
    minimum-vote requirement wrongly trusted it as "the" reference margin
    and preferred the false candidate over the real, later marker. Real
    votes here are all single occurrences, so no reference margin should
    be trusted at all, and resolution must defer to reading order.
    """
    lines = [
        _line("O conceito de Tipo de Dados Abstrato...", 296.68, 88.71),
        _line("I.", 313.69, 130.38),
        _line("A especificação de um TDA é composta das", 330.70, 130.38),  # false 'A' candidate
        _line("II. Dois mecanismos utilizaveis...", 313.69, 169.21),
        _line("É correto apenas o que se afirma em", 296.68, 300.54),
        _line("A\tI.", 296.68, 318.10),  # real A marker
        _line("B\tII.", 347.92, 318.10),
        _line("C\tI e III.", 399.16, 318.10),
        _line("D\tII e IV.", 450.40, 318.10),
        _line("E\tIII e IV.", 501.64, 318.10),
    ]
    group = find_alternative_group(lines)
    assert group is not None
    assert group.status == "resolved"
    assert group.reference_margin is None
    assert group.accepted["A"] == 5  # the real, later marker - not the false idx=2


# --- Metamorphic tests (PROMPT section 24) ----------------------------------


def test_translation_invariance():
    dx, dy = 517.0, -233.0
    base = _full_sequence(margin=30.0)
    shifted = [_line(ln.text, ln.x0 + dx, ln.y0 + dy, page=ln.page_number) for ln in base]
    group_a = find_alternative_group(base)
    group_b = find_alternative_group(shifted)
    assert group_a is not None
    assert group_b is not None
    assert group_a.status == group_b.status == "resolved"
    assert group_a.accepted == group_b.accepted


def test_scale_invariance_of_margin_alignment():
    """Scaling the whole page (margin and gap together) must not change
    which candidate wins - the tolerance is a fixed point value, so this
    test keeps the offending offset comfortably outside it at every scale
    tested (never picked to exactly straddle the boundary).
    """
    for scale in (0.5, 1.0, 2.0):
        margin = 30.0 * scale
        offset = 50.0 * scale  # always >> MARGIN_TOLERANCE regardless of scale
        lines = [
            _line("A\t texto A", margin, 100.0 * scale),
            _line("B\t texto B", margin, 120.0 * scale),
            _line("C\t texto C real", margin, 140.0 * scale),
            _line("C fora da margem", margin + offset, 155.0 * scale),
            _line("D\t texto D", margin, 170.0 * scale),
            _line("E\t texto E", margin, 190.0 * scale),
        ]
        group = find_alternative_group(lines)
        assert group is not None, f"failed at scale={scale}"
        assert group.status == "resolved", f"failed at scale={scale}"
        assert group.accepted["C"] == 2, f"failed at scale={scale}"


def test_column_width_variation_does_not_affect_resolution():
    """The same relative shape at very different absolute margins (as a
    narrower or wider column layout would produce) must resolve
    identically - never a fixed absolute x0 threshold.
    """
    for margin in (30.0, 96.0, 271.5, 400.0):
        lines = _full_sequence(margin=margin)
        group = find_alternative_group(lines)
        assert group is not None, f"failed at margin={margin}"
        assert group.status == "resolved", f"failed at margin={margin}"


def test_font_size_and_row_spacing_variation_does_not_affect_resolution():
    """Varying the vertical step (as a different font size/line height
    would produce) must not affect the outcome - the mechanism never
    looks at absolute row spacing, only relative x0 and reading order.
    """
    for step in (14.0, 20.0, 40.0):
        lines = _full_sequence(margin=30.0, step=step)
        group = find_alternative_group(lines)
        assert group is not None, f"failed at step={step}"
        assert group.status == "resolved", f"failed at step={step}"


def test_candidate_at_exactly_the_tolerance_boundary_counts_as_on_margin():
    """A candidate exactly MARGIN_TOLERANCE away from the reference margin
    counts as on-margin (inclusive boundary) - here that means BOTH
    candidates are on-margin (no off-margin outlier to partition against),
    so the mechanism defers to reading-order preference, same as the
    all-same-margin case above.
    """
    margin = 30.0
    lines = [
        _line("A\t texto A", margin, 100.0),
        _line("B\t texto B", margin, 120.0),
        _line("C\t texto C real", margin, 140.0),
        _line("C quase na margem", margin + MARGIN_TOLERANCE, 155.0),
        _line("D\t texto D", margin, 170.0),
        _line("E\t texto E", margin, 190.0),
    ]
    group = find_alternative_group(lines)
    assert group is not None
    assert group.status == "resolved"
    assert group.accepted["C"] == 3


def test_content_stream_order_does_not_affect_candidate_collection():
    """Candidates are found by iterating ``lines`` in the order given
    (already the caller's own established reading order) - shuffling the
    *unrelated* false-candidate line relative to the others must not
    change which real markers are found, only competition for the
    contested letter.
    """
    margin = 30.0
    a = _line("A\t texto A", margin, 100.0)
    b = _line("B\t texto B", margin, 120.0)
    false_c = _line("C fora da margem", margin + 50.0, 135.0)
    real_c = _line("C\t texto C real", margin, 150.0)
    d = _line("D\t texto D", margin, 170.0)
    e = _line("E\t texto E", margin, 190.0)
    group = find_alternative_group([a, b, false_c, real_c, d, e])
    assert group is not None
    assert group.status == "resolved"
    assert group.accepted["A"] == 0
    assert group.accepted["B"] == 1
    assert group.accepted["D"] == 4
    assert group.accepted["E"] == 5
