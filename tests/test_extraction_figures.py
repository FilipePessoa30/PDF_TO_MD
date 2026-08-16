from __future__ import annotations

from enade.extraction.figures import (
    MAX_ABSORPTION_GROWTH,
    TEXT_ABSORPTION_PADDING,
    VisualRegion,
    _dominant_left_margin,
    _expand_with_labels,
    _is_marker_at_margin,
    _is_paragraph_continuation,
    _is_rule_line,
    _is_two_column_body_text,
    _merge_by_vertical_proximity,
    _merge_overlapping_regions,
    _rects_touch,
)
from enade.extraction.layout import Line


def _line(page: int, y: float, text: str, x: float = 29.8, width: float = 400.0) -> Line:
    return Line(page_number=page, text=text, x0=x, y0=y, x1=x + width, y1=y + 12)


def test_rects_touch_true_within_padding():
    a = (0, 0, 10, 10)
    b = (15, 0, 25, 10)  # 5pt gap, purely horizontal (y-ranges already overlap)
    assert _rects_touch(a, b, y_padding=10, x_padding=10) is True
    assert _rects_touch(a, b, y_padding=10, x_padding=2) is False


def test_rects_touch_uses_separate_x_and_y_padding():
    """Regression test: a wide y_padding must not let a rect far away in x
    (but within y range) count as touching - this is exactly the Questao 3
    bug (see figures.py, TEXT_ABSORPTION_X_PADDING docstring), where a
    generous single padding let figure-region absorption "walk" sideways
    through page-margin-aligned lines that were never part of the figure.
    """
    a = (100, 0, 200, 10)
    far_in_x_close_in_y = (500, 40, 520, 50)  # 300pt away in x, 30pt in y
    close_in_x_and_y = (205, 40, 225, 50)  # 5pt away in x, 30pt in y

    assert _rects_touch(a, far_in_x_close_in_y, y_padding=90, x_padding=20) is False
    assert _rects_touch(a, close_in_x_and_y, y_padding=90, x_padding=20) is True


def test_merge_by_vertical_proximity_merges_close_rects():
    rects = [((0, 0, 10, 10), False), ((0, 15, 10, 25), False)]  # 5pt gap
    merged = _merge_by_vertical_proximity(rects, y_tolerance=18.0)
    assert len(merged) == 1
    bbox, count, has_image = merged[0]
    assert count == 2
    assert bbox == (0, 0, 10, 25)


def test_merge_by_vertical_proximity_keeps_far_rects_separate():
    rects = [((0, 0, 10, 10), False), ((0, 200, 10, 210), False)]
    merged = _merge_by_vertical_proximity(rects, y_tolerance=18.0)
    assert len(merged) == 2


def test_merge_tracks_has_raster_image():
    rects = [((0, 0, 10, 10), True), ((0, 15, 10, 25), False)]
    merged = _merge_by_vertical_proximity(rects, y_tolerance=18.0)
    assert merged[0][2] is True


def test_expand_with_labels_grows_bbox_to_include_nearby_label():
    bbox = (100, 100, 200, 200)
    labels = [((50, 100, 95, 115), "Rótulo próximo")]  # 5pt gap to the left
    grown = _expand_with_labels(bbox, labels)
    assert grown[0] == 50  # absorbed


def test_expand_with_labels_never_absorbs_alternative_marker():
    bbox = (100, 100, 200, 200)
    labels = [((50, 100, 95, 115), "A\t Texto da alternativa A")]
    grown = _expand_with_labels(bbox, labels)
    assert grown == bbox  # unchanged - marker line excluded


def test_expand_with_labels_growth_is_capped():
    bbox = (100, 100, 200, 200)
    far_label = (
        (100 - MAX_ABSORPTION_GROWTH - 50, 100, 100 - MAX_ABSORPTION_GROWTH - 10, 115),
        "rótulo distante",
    )
    grown = _expand_with_labels(bbox, [far_label])
    assert grown[0] >= bbox[0] - MAX_ABSORPTION_GROWTH
    assert grown[0] > far_label[0][0]  # did not reach all the way to the far label


def test_expand_with_labels_two_independent_candidates_each_bridge_on_their_own():
    # 2011 unified booklet, Questao 6 (page 5): a chart's true bbox ended at
    # y=366.3, but TWO separate wrapped alternative-continuation lines
    # (A's and B's own second lines) each sat within TEXT_ABSORPTION_PADDING
    # of that edge independently - removing only one from the candidate
    # pool left the other still able to bridge the same gap on its own,
    # since each candidate is tested against the *current* bbox rather than
    # in some fixed order (see docs/decisions.md, Phase 2B ADR 26). This
    # models that: blocking candidate A alone still lets B grow the bbox.
    bbox = (28.5, 119.7, 284.7, 366.3)
    gap = TEXT_ABSORPTION_PADDING - 1  # just inside the absorption padding
    candidate_a = ((45.5, 366.3 + gap, 256.7, 366.3 + gap + 13.4), "garantir um emprego estavel")
    candidate_b = ((45.5, 366.3 + gap, 263.9, 366.3 + gap + 13.4), "que aumenta o nivel")

    grown_with_only_a = _expand_with_labels(bbox, [candidate_a])
    assert grown_with_only_a[3] > bbox[3]  # A alone bridges the gap

    grown_with_only_b = _expand_with_labels(bbox, [candidate_b])
    assert grown_with_only_b[3] > bbox[3]  # B alone still bridges the gap, even without A

    grown_with_neither = _expand_with_labels(bbox, [])
    assert (
        grown_with_neither == bbox
    )  # with both candidates excluded, bbox stays at its true extent


def test_is_paragraph_continuation_true_for_aligned_wrapped_tail():
    """Questao 3 regression: a narrow tail-wrap line (e.g. "atividade
    fisica.") sharing its left edge with the wide line directly above it is
    the continuation of that paragraph, not a figure label.
    """
    lines = [
        _line(1, 100, "grandes metrópoles, pois elas não emitem poluentes", x=63.8, width=470.0),
        _line(1, 114, "atividade física.", x=63.8, width=75.0),
    ]
    assert _is_paragraph_continuation(1, lines) is True


def test_is_paragraph_continuation_false_when_x0_differs():
    """Questao 17 regression: a diagram label sitting close below an
    unrelated wide sentence, but indented to a different x0, is NOT a
    paragraph continuation and must remain absorbable.
    """
    lines = [
        _line(1, 100, "Em um sentido abstrato, o comportamento que queremos é mostrado", x=29.8),
        _line(1, 114, "A entra na região crítica", x=193.2, width=116.0),
    ]
    assert _is_paragraph_continuation(1, lines) is False


def test_is_paragraph_continuation_false_when_gap_too_large():
    lines = [
        _line(1, 100, "uma frase larga qualquer que ocupa a coluna inteira", x=29.8),
        _line(1, 160, "Rótulo", x=29.8, width=40.0),  # 60pt gap - a new block, not a wrap
    ]
    assert _is_paragraph_continuation(1, lines) is False


def test_dominant_left_margin_finds_common_body_indent():
    lines = [
        _line(1, 100, "primeira linha larga de texto corrido", x=29.8),
        _line(1, 120, "segunda linha larga de texto corrido", x=29.8),
        _line(1, 140, "Rótulo", x=193.2, width=40.0),
    ]
    assert _dominant_left_margin(lines) == 30.0  # rounds 29.8 -> 30


def test_dominant_left_margin_none_without_wide_lines():
    lines = [_line(1, 100, "Rótulo", x=193.2, width=40.0)]
    assert _dominant_left_margin(lines) is None


def test_dominant_left_margin_none_with_only_a_single_wide_line():
    """Questao 2 regression: a page whose only wide line is a single
    bibliographic citation (often indented very differently from body
    prose in this corpus) must not have that citation's own x0 mistaken
    for "the page's standard margin" - one data point is not agreement.
    Without this, the real "QUESTAO 02" marker (flush with the true
    margin) looked "far from the margin", became absorbable, and pulled a
    figure's region out of the question's own content bounds, silently
    dropping the asset entirely.
    """
    lines = [
        _line(1, 100, "QUESTÃO 02", x=29.8, width=74.7),
        _line(1, 700, "Disponível em: https://example.com/some/long/citation/url", x=98.3),
    ]
    assert _dominant_left_margin(lines) is None


def test_is_marker_at_margin_true_for_real_alternative():
    assert _is_marker_at_margin("A\t Texto da alternativa A", x0=29.8, body_margin_x0=30.0) is True


def test_is_marker_at_margin_false_for_diagram_label_far_from_margin():
    """Questao 17 regression: "A entra na regiao critica" and "B tenta
    entrar..." are shaped like alternative markers (bare letter + space)
    but sit deep inside the page, not at the body margin - must not be
    treated as real markers.
    """
    assert _is_marker_at_margin("A entra na região crítica", x0=193.2, body_margin_x0=30.0) is False
    assert _is_marker_at_margin("B tenta entrar", x0=249.3, body_margin_x0=30.0) is False


def test_is_marker_at_margin_true_when_margin_unknown():
    # No wide body-prose line was found on the page to establish a margin -
    # fall back to the conservative (always-exclude) behavior.
    assert _is_marker_at_margin("A\t Texto da alternativa A", x0=29.8, body_margin_x0=None) is True


def test_expand_with_labels_absorbs_marker_shaped_label_far_from_margin():
    """End-to-end version of the Questao 17 regression: a diagram label
    shaped like an alternative marker must still be absorbed when it is
    nowhere near the page's real body-text margin.
    """
    bbox = (172.0, 409.4, 462.6, 591.0)
    label = ((193.2, 394.2, 309.1, 409.5), "A entra na região crítica")
    grown = _expand_with_labels(bbox, [label], body_margin_x0=30.0)
    assert grown[1] <= 394.2  # top edge extended up to include the label


def test_expand_with_labels_still_excludes_real_alternative_at_margin():
    bbox = (100, 100, 200, 200)
    labels = [((50, 100, 95, 115), "A\t Texto da alternativa A")]
    grown = _expand_with_labels(bbox, labels, body_margin_x0=50.0)
    assert grown == bbox  # unchanged - real marker, still excluded


# --- Phase 1C: two-column body text protection (D5) ---------------------------


def test_is_two_column_body_text_true_at_either_column_margin():
    margins = (33.8, 291.5)
    left_line = _line(1, 100.0, "Um heap binário é um arranjo...", x=33.8, width=240.0)
    right_line = _line(1, 100.0, "void heapify (int *a, int n, int i)", x=291.5, width=244.9)
    assert _is_two_column_body_text(left_line, margins) is True
    assert _is_two_column_body_text(right_line, margins) is True


def test_is_two_column_body_text_false_when_no_two_column_layout_detected():
    # e.g. a single-column page (column_margins is None) - never protected,
    # so an isolated short label there can still be absorbed normally.
    line = _line(1, 100.0, "Processo A", x=32.6, width=44.0)
    assert _is_two_column_body_text(line, None) is False


def test_is_two_column_body_text_false_for_a_line_not_at_either_margin():
    margins = (33.8, 291.5)
    diagram_label = _line(1, 100.0, "12", x=160.1, width=10.6)
    assert _is_two_column_body_text(diagram_label, margins) is False


def test_merge_overlapping_regions_merges_same_owner_fragments():
    # 2011 Questao 22's own precedent (module docstring): several
    # vertically-clustered vector groups from the same owner, whose
    # expanded bboxes end up overlapping, collapse into one - unchanged
    # behavior from before the owner_key gate existed.
    a = VisualRegion(
        page_number=1, bbox=(100, 100, 300, 200), element_count=1, owner_key="objective-1"
    )
    b = VisualRegion(
        page_number=1, bbox=(100, 150, 320, 250), element_count=1, owner_key="objective-1"
    )
    merged = _merge_overlapping_regions([a, b])
    assert len(merged) == 1
    assert merged[0].bbox == (100, 100, 320, 250)
    assert merged[0].owner_key == "objective-1"


def test_merge_overlapping_regions_never_merges_across_different_owners():
    """Regression test: 2011 Questao 38/40 (page 25) - Questao 38's own
    end-of-statement region and Questao 40's own grid-puzzle image sat
    close enough in y to pass the plain Y-overlap check, and before this
    gate existed their union produced a crop with Questao 40's own puzzle
    rendered as if it were part of Questao 38 (see docs/decisions.md,
    Phase 2D ADR). Two regions with a different, known owner_key must never
    merge, no matter how much their bboxes overlap in y.
    """
    q38_region = VisualRegion(
        page_number=25, bbox=(28, 700, 287, 725), element_count=1, owner_key="objective-38"
    )
    q40_region = VisualRegion(
        page_number=25, bbox=(297, 690, 556, 780), element_count=1, owner_key="objective-40"
    )
    merged = _merge_overlapping_regions([q38_region, q40_region])
    assert len(merged) == 2
    bboxes = {r.bbox for r in merged}
    assert q38_region.bbox in bboxes
    assert q40_region.bbox in bboxes


def test_merge_overlapping_regions_still_merges_when_both_owners_unknown():
    # Pre-ownership behavior (question_regions not supplied, or a
    # candidate's center fell outside every known region) is unchanged:
    # two owner-less regions still merge on y-overlap alone.
    a = VisualRegion(page_number=1, bbox=(100, 100, 300, 200), element_count=1, owner_key=None)
    b = VisualRegion(page_number=1, bbox=(100, 150, 320, 250), element_count=1, owner_key=None)
    merged = _merge_overlapping_regions([a, b])
    assert len(merged) == 1
    assert merged[0].bbox == (100, 100, 320, 250)


def test_merge_overlapping_regions_unions_owner_x_bounds_for_same_owner():
    a = VisualRegion(
        page_number=1,
        bbox=(100, 100, 300, 200),
        element_count=1,
        owner_key="objective-1",
        owner_x_bounds=(90.0, 310.0),
    )
    b = VisualRegion(
        page_number=1,
        bbox=(100, 150, 320, 250),
        element_count=1,
        owner_key="objective-1",
        owner_x_bounds=(95.0, 330.0),
    )
    merged = _merge_overlapping_regions([a, b])
    assert merged[0].owner_x_bounds == (90.0, 330.0)


# --- Phase 3B: _is_rule_line (see docs/phase-3b-report.md) ------------------


def test_is_rule_line_true_for_a_tall_thin_column_separator():
    # 2008-b's own vertical column-divider bar: ~1pt wide, ~500pt tall.
    assert _is_rule_line((300.8, 267.5, 301.8, 763.9)) is True


def test_is_rule_line_true_for_a_wide_thin_horizontal_divider():
    # 2008-b's own section-divider rule between the transition block and
    # the questions below it: ~522pt wide, ~1pt tall.
    assert _is_rule_line((36.8, 263.8, 559.2, 264.7)) is True


def test_is_rule_line_false_for_a_short_thin_underline():
    # A primary-key underline in relational-schema notation (2008-b Q21's
    # own "EMPREGADO" attribute list) is thin but short - legitimate
    # content-adjacent decoration, never a rule spanning the page/column.
    assert _is_rule_line((196.7, 297.6, 245.3, 298.3)) is False


def test_is_rule_line_false_for_a_real_diagram_sized_rect():
    assert _is_rule_line((40.0, 100.0, 300.0, 350.0)) is False


def test_is_rule_line_false_for_a_small_formula_image():
    assert _is_rule_line((100.0, 100.0, 130.0, 115.0)) is False
