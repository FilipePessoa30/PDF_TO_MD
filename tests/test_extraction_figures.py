from __future__ import annotations

import pymupdf

from enade.extraction.figures import (
    MAX_ABSORPTION_GROWTH,
    TEXT_ABSORPTION_PADDING,
    VisualRegion,
    _dominant_body_font_size,
    _dominant_left_margin,
    _expand_with_labels,
    _is_marker_at_margin,
    _is_paragraph_continuation,
    _is_rule_line,
    _is_two_column_body_text,
    _merge_by_vertical_proximity,
    _merge_overlapping_regions,
    _rects_touch,
    verify_drawings_present,
    verify_image_present,
)
from enade.extraction.layout import Line


def _page_with_drawing(rect: tuple[float, float, float, float]) -> pymupdf.Page:
    doc = pymupdf.open()
    page = doc.new_page(width=600, height=800)
    shape = page.new_shape()
    shape.draw_line((rect[0], rect[1]), (rect[2], rect[3]))
    shape.finish()
    shape.commit()
    return page


def _page_with_image(rect: tuple[float, float, float, float]) -> pymupdf.Page:
    doc = pymupdf.open()
    page = doc.new_page(width=600, height=800)
    pixmap = pymupdf.Pixmap(pymupdf.csRGB, (0, 0, 4, 4), False)
    pixmap.set_rect(pixmap.irect, (200, 0, 0))
    page.insert_image(pymupdf.Rect(*rect), pixmap=pixmap)
    return page


def _line(
    page: int, y: float, text: str, x: float = 29.8, width: float = 400.0, font_size: float = 10.0
) -> Line:
    return Line(
        page_number=page, text=text, x0=x, y0=y, x1=x + width, y1=y + 12, font_size=font_size
    )


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


def test_merge_by_vertical_proximity_defaults_to_unbounded_x_tolerance():
    """The original, pre-Phase-3C behavior (Y-proximity only, no X check) is
    the default every existing caller keeps unless it opts in - a real
    2011/2021 regression (Q23/Q38's own legitimate per-alternative formula
    rows, spanning 200pt+ of a shared row) was found by full regeneration
    when this was tried as the new unconditional default (see
    figures.py, MERGE_X_TOLERANCE's own docstring).
    """
    far_apart_in_x = [((0, 0, 10, 10), False), ((500, 5, 510, 15), False)]
    merged = _merge_by_vertical_proximity(far_apart_in_x, y_tolerance=18.0)
    assert len(merged) == 1


def test_merge_by_vertical_proximity_x_tolerance_rejects_far_apart_rects():
    """PROMPT Phase 3C, 'Classe A': two rects far apart in X must not merge
    just because they are Y-adjacent, when a finite x_tolerance is given -
    the 2008-b RASCUNHO-grid regression this exists to prevent (see
    docs/phase-3c-report.md section E): the grid's own left- and
    right-column row-border segments recur ~500pt apart in X at the same Y
    pitch, and were collapsing into one nearly-full-page-width region.
    """
    left_column_segment = (36.8, 401.4, 37.8, 475.4)
    right_column_segment = (558.2, 401.4, 559.2, 475.4)
    rects = [(left_column_segment, False), (right_column_segment, False)]
    merged = _merge_by_vertical_proximity(rects, y_tolerance=18.0, x_tolerance=150.0)
    assert len(merged) == 2


def test_merge_by_vertical_proximity_x_tolerance_still_merges_close_rects():
    """A genuine single diagram's own constituent paths (which overlap or
    nearly overlap in X) must still merge under a finite x_tolerance - the
    X check only rejects rects that are *also* far apart in X, never a
    normal same-drawing cluster.
    """
    rects = [((100, 0, 200, 10), False), ((110, 15, 210, 25), False)]
    merged = _merge_by_vertical_proximity(rects, y_tolerance=18.0, x_tolerance=150.0)
    assert len(merged) == 1


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


def test_dominant_body_font_size_finds_common_size_at_the_margin():
    """PROMPT Phase 3D section 6-7: font size is evidenced by the page's
    own dominant *left margin*, not by line width - a genuine narrow-column
    layout (2008-b's own D9: every real body line is well under
    MAX_LABEL_LINE_WIDTH, so ``_dominant_left_margin``'s own width-based
    evidence pool finds nothing there) must still yield a body size.
    """
    lines = [
        _line(
            1,
            100,
            "primeira linha de corpo de texto corrido, bem longa",
            x=36.8,
            width=120.0,
            font_size=10.0,
        ),
        _line(
            1,
            120,
            "segunda linha de corpo de texto corrido, bem longa",
            x=36.8,
            width=120.0,
            font_size=10.0,
        ),
        _line(
            1,
            140,
            "terceira linha de corpo de texto corrido, bem longa",
            x=36.8,
            width=120.0,
            font_size=10.0,
        ),
    ]
    assert _dominant_body_font_size(lines) == 10.0


def test_dominant_body_font_size_ignores_off_margin_captions_outnumbering_body():
    """Questao 1 regression (PROMPT Phase 3D): a page with several small
    embedded images, each with its own multi-line caption, can have *more*
    long caption lines (each sitting at its own image's own x0, never the
    page's real body margin) than real body-paragraph lines. A flat mode
    over every long line picks the captions' own (smaller) font size as
    "the body size", which then wrongly lets a same-size index label
    ("IV") be absorbed as if it were a caption too, fragmenting the region.
    Restricting to lines at the dominant left margin fixes this.
    """
    lines = [
        _line(
            1,
            100,
            "corpo real do enunciado desta questao, uma frase completa",
            x=36.8,
            font_size=10.0,
        ),
        _line(1, 120, "continuacao do mesmo paragrafo do enunciado real", x=36.8, font_size=10.0),
        _line(
            1, 200, "ERMAKOFF, George. Rio de Janeiro, 1840-1900: cronica", x=222.4, font_size=6.0
        ),
        _line(
            1,
            210,
            "fotografica. Rio de Janeiro: G. Ermakoff Casa Editorial",
            x=222.4,
            font_size=6.0,
        ),
        _line(1, 300, "Disponivel em: www.example.org/alguma-pagina-longa", x=98.6, font_size=6.0),
        _line(
            1, 400, "ERMAKOFF, George. 1840-1900: outra cronica fotografica", x=405.6, font_size=6.0
        ),
    ]
    assert _dominant_body_font_size(lines) == 10.0


def test_dominant_body_font_size_none_without_enough_agreement():
    lines = [_line(1, 100, "unica linha longa o suficiente para contar", x=36.8, font_size=10.0)]
    assert _dominant_body_font_size(lines) is None


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


# --- PROMPT Fase 3S: verify_drawings_present (structural evidence gate) ---


def test_verify_drawings_present_counts_a_genuine_overlapping_drawing():
    page = _page_with_drawing((10.0, 10.0, 20.0, 20.0))
    assert verify_drawings_present(page, (8.0, 8.0, 22.0, 22.0)) == 1


def test_verify_drawings_present_zero_when_bbox_is_empty_space():
    """The core safety property (PROMPT Fase 3S Section 13: "a deteccao do
    candidato seja estrutural") - a declared override bbox pointing at a
    page location with no real vector content must never be trusted, so
    the caller (assembler._build_declared_inline_formula_regions) can
    never build a region for content that does not actually exist there
    (a stale override after a corpus refresh, a typo'd bbox, ...).
    """
    page = _page_with_drawing((10.0, 10.0, 20.0, 20.0))
    assert verify_drawings_present(page, (400.0, 400.0, 420.0, 420.0)) == 0


def test_verify_drawings_present_zero_on_a_page_with_no_drawings_at_all():
    doc = pymupdf.open()
    page = doc.new_page(width=600, height=800)
    assert verify_drawings_present(page, (10.0, 10.0, 20.0, 20.0)) == 0


def test_verify_drawings_present_counts_every_overlapping_drawing():
    doc = pymupdf.open()
    page = doc.new_page(width=600, height=800)
    for start, end in [((10.0, 10.0), (20.0, 20.0)), ((15.0, 12.0), (25.0, 18.0))]:
        shape = page.new_shape()
        shape.draw_line(start, end)
        shape.finish()
        shape.commit()
    far_shape = page.new_shape()
    far_shape.draw_line((500.0, 500.0), (510.0, 510.0))  # far away - not counted
    far_shape.finish()
    far_shape.commit()
    assert verify_drawings_present(page, (8.0, 8.0, 27.0, 22.0)) == 2


def test_visual_region_is_declared_inline_formula_defaults_false():
    # Every existing region in the corpus (built by detect_visual_regions,
    # never by assembler._build_declared_inline_formula_regions) keeps this
    # False - the new field is purely additive.
    region = VisualRegion(page_number=1, bbox=(0.0, 0.0, 10.0, 10.0), element_count=1)
    assert region.is_declared_inline_formula is False


def test_visual_region_is_exact_raster_bbox_defaults_false():
    region = VisualRegion(page_number=1, bbox=(0.0, 0.0, 10.0, 10.0), element_count=1)
    assert region.is_exact_raster_bbox is False


# --- PROMPT Fase 3Y: verify_image_present (structural evidence gate for a
# declared raster-alternative region, e.g. 2008-b Q8's own photographs) ---


def test_verify_image_present_counts_a_substantially_contained_image():
    page = _page_with_image((10.0, 10.0, 110.0, 110.0))
    assert verify_image_present(page, (8.0, 8.0, 112.0, 112.0)) == 1


def test_verify_image_present_zero_when_bbox_is_empty_space():
    """Same safety property as verify_drawings_present's own (PROMPT Fase
    3Y): a declared bbox with no real embedded image must never be
    trusted, so ``assembler._build_declared_raster_alternative_regions``
    never builds a region for content that does not actually exist there.
    """
    page = _page_with_image((10.0, 10.0, 110.0, 110.0))
    assert verify_image_present(page, (400.0, 400.0, 500.0, 500.0)) == 0


def test_verify_image_present_zero_on_a_page_with_no_images_at_all():
    doc = pymupdf.open()
    page = doc.new_page(width=600, height=800)
    assert verify_image_present(page, (10.0, 10.0, 110.0, 110.0)) == 0


def test_verify_image_present_zero_when_bbox_only_partially_overlaps():
    # A bbox that only clips a corner of the real image (well under the
    # default 90% containment threshold) must not count - this is the
    # discriminator between "this is genuinely the declared photograph"
    # and "this bbox merely brushes some unrelated image's own edge".
    page = _page_with_image((10.0, 10.0, 110.0, 110.0))
    assert verify_image_present(page, (100.0, 100.0, 200.0, 200.0)) == 0


def test_verify_image_present_respects_min_containment_threshold():
    page = _page_with_image((10.0, 10.0, 110.0, 110.0))
    # bbox covers exactly the left half of the image (50% containment) -
    # rejected at the default 0.9 threshold, accepted once the threshold
    # itself is lowered below that overlap fraction.
    assert verify_image_present(page, (10.0, 10.0, 60.0, 110.0)) == 0
    assert verify_image_present(page, (10.0, 10.0, 60.0, 110.0), min_containment=0.4) == 1
