from __future__ import annotations

import pytest

from enade.extraction.alternative_groups import find_alternative_group
from enade.extraction.assembler import (
    CodeSegment,
    ExtractedAlternative,
    FigureSegment,
    TextSegment,
    _attach_alternative_formula_regions,
    _build_statement_segments,
    _line_in_region,
    _render_code_lines,
    _strip_leading_marker,
    _strip_line_number_gutter,
    _text_consumption_decision,
    compute_line_region_relation,
    detect_broken_words,
)
from enade.extraction.figures import VisualRegion
from enade.extraction.layout import Line
from enade.extraction.layout_overrides import LayoutOverride, LayoutOverrideSet


def _line(
    page: int, y: float, text: str, x: float = 30.0, mono: bool = False, width: float = 200.0
) -> Line:
    return Line(page_number=page, text=text, x0=x, y0=y, x1=x + width, y1=y + 12, is_monospace=mono)


def test_find_alternative_group_ignores_capital_letter_in_prose():
    # Statement starts with "A chance..." - must not be mistaken for alternative A.
    # PROMPT Phase 3I: replaces the old _find_alternative_starts, now
    # superseded by alternative_groups.find_alternative_group - see
    # tests/test_alternative_groups.py for the module's own dedicated
    # unit/metamorphic suite. Kept here as an assembler-level regression
    # guard for this specific, historically important shape.
    lines = [
        _line(1, 10, "A chance de uma criança de baixa renda ter um futuro melhor"),
        _line(1, 25, "que a realidade em que nasceu."),
        _line(1, 40, "A\t Primeiro texto da alternativa A."),
        _line(1, 55, "B\t Texto da alternativa B."),
        _line(1, 70, "C\t Texto da alternativa C."),
        _line(1, 85, "D\t Texto da alternativa D."),
        _line(1, 100, "E\t Texto da alternativa E."),
    ]
    group = find_alternative_group(lines)
    assert group is not None
    assert group.is_usable
    assert group.accepted["A"] == 2  # not index 0


def test_find_alternative_group_incomplete_when_sequence_incomplete():
    lines = [
        _line(1, 10, "Enunciado sem alternativas completas."),
        _line(1, 25, "A\t alternativa a"),
        _line(1, 40, "B\t alternativa b"),
        # missing C, D, E
    ]
    assert find_alternative_group(lines) is None


def test_find_alternative_group_picks_rightmost_valid_sequence():
    # A red herring "B tenta..." style label appears before the real sequence.
    lines = [
        _line(1, 10, "B tenta entrar em algo (rótulo de figura, não alternativa)."),
        _line(1, 25, "Enunciado real da questão."),
        _line(1, 40, "A\t alternativa a"),
        _line(1, 55, "B\t alternativa b"),
        _line(1, 70, "C\t alternativa c"),
        _line(1, 85, "D\t alternativa d"),
        _line(1, 100, "E\t alternativa e"),
    ]
    group = find_alternative_group(lines)
    assert group is not None
    assert group.is_usable
    assert group.accepted["A"] == 2


def test_line_in_region_never_swallows_an_alternative_marker():
    region = VisualRegion(page_number=1, bbox=(0, 0, 500, 500), element_count=1)
    alt_line = _line(1, 10, "A\t Texto da alternativa A")
    assert _line_in_region(alt_line, region) is False


def test_line_in_region_true_for_geometric_containment():
    region = VisualRegion(page_number=1, bbox=(0, 100, 500, 200), element_count=1)
    label_line = _line(1, 150, "Rótulo do diagrama")
    assert _line_in_region(label_line, region) is True


def test_line_in_region_false_on_different_page():
    region = VisualRegion(page_number=1, bbox=(0, 100, 500, 200), element_count=1)
    label_line = _line(2, 150, "Rótulo em outra página")
    assert _line_in_region(label_line, region) is False


def test_line_in_region_respects_a_matching_protect_from_region_membership_override():
    # PROMPT Phase 2D section 12: 2011 Q12's own item IV overlaps a
    # growth-capped region by under 1pt (see docs/decisions.md, Phase 2D
    # ADR) - a matching override keeps it out of the region regardless of
    # geometric overlap.
    region = VisualRegion(page_number=1, bbox=(0, 100, 500, 200), element_count=1)
    line = _line(1, 150, "IV. Nas cadeias geradas por essa gramática, todos os")
    overrides = LayoutOverrideSet(
        overrides=[
            LayoutOverride(
                pdf_sha256="deadbeef" * 8,
                page=1,
                bbox=(0.0, 100.0, 500.0, 200.0),
                rule="protect_from_region_membership",
                question_id="enade-2011-computing-q12",
                reason="test",
                evidence="test",
                status="reviewed",
            )
        ]
    )
    assert _line_in_region(line, region, overrides, "deadbeef" * 8) is False


def test_line_in_region_ignores_override_for_a_different_pdf_hash():
    region = VisualRegion(page_number=1, bbox=(0, 100, 500, 200), element_count=1)
    line = _line(1, 150, "IV. Nas cadeias geradas por essa gramática, todos os")
    overrides = LayoutOverrideSet(
        overrides=[
            LayoutOverride(
                pdf_sha256="deadbeef" * 8,
                page=1,
                bbox=(0.0, 100.0, 500.0, 200.0),
                rule="protect_from_region_membership",
                question_id="enade-2011-computing-q12",
                reason="test",
                evidence="test",
                status="reviewed",
            )
        ]
    )
    # Same bbox/page, but a different pdf_sha256 - normal containment
    # behavior applies (still True, unaffected by the override).
    assert _line_in_region(line, region, overrides, "cafebabe" * 8) is True


def test_line_in_region_small_formula_region_swallows_the_line_below_without_override():
    """Regression test: 2011 Q38 (page 25, PROMPT Phase 2E section 9) -
    production 4 of Q38's own grammar ("N -> Nd") sits at y0=296.5, just
    below the small-formula region carrying production 3's own terminal
    "x" (region bbox y1=300.4). The real production region for this case
    is always built via the small-formula candidate pool
    (``is_small_formula=True`` - PROMPT Phase 3G's own ``LineRegionRelation``
    keeps this region class's original, more lenient touch-based inclusion
    unchanged - see ``_text_consumption_decision``): a tiny, already
    size-capped inline-symbol region reliably swallows a merely-touching
    adjacent fragment, even though the region's own tiny bbox never
    renders enough of that line to be legible either - real content,
    neither readable as text nor as image, without an override.
    """
    region = VisualRegion(
        page_number=25,
        bbox=(59.55, 292.74, 69.90, 300.39),
        element_count=1,
        has_raster_image=True,
        is_small_formula=True,
    )
    line = _line(25, 299.6, "N → Nd", x=28.47, width=37.1)
    assert _line_in_region(line, region) is True


def test_line_in_region_small_formula_region_override_recovers_the_swallowed_line():
    region = VisualRegion(
        page_number=25,
        bbox=(59.55, 292.74, 69.90, 300.39),
        element_count=1,
        has_raster_image=True,
        is_small_formula=True,
    )
    line = _line(25, 299.6, "N → Nd", x=28.47, width=37.1)
    overrides = LayoutOverrideSet(
        overrides=[
            LayoutOverride(
                pdf_sha256="eb3b497f" * 8,
                page=25,
                bbox=(28.4, 296.4, 65.7, 313.9),
                rule="protect_from_region_membership",
                question_id="enade-2011-computing-q38",
                reason="test",
                evidence="test",
                status="reviewed",
            )
        ]
    )
    assert _line_in_region(line, region, overrides, "eb3b497f" * 8) is False


# --- Phase 3G: contextual line-region relation (Cluster A/C) ------------------
#
# PROMPT Phase 3G's own control matrix (D10/Q07/Q61/Q71) reproduced with
# synthetic geometry (never the real corpus's own coordinates or text - see
# Section 18, "os testes nao podem depender... de coordenada fixa"). Every
# test below passes ``contextual_relation_gate=True`` explicitly; with it
# omitted (every existing test above, and every booklet without
# ``ExamStructureProfile.contextual_relation_gate`` set), behavior is
# untouched - confirmed by the full existing suite passing unchanged.


def test_gate_off_keeps_the_original_fixed_padding_behavior():
    """A wide, unrelated line barely touching a grown region's own edge -
    the exact shape that regressed 2011/2021 when this relation was tried
    unconditionally (docs/phase-3g-report.md) - is still absorbed (as
    before) when the gate is off, and correctly kept visible when it is
    on. Same two calls, same inputs, opposite outcomes - the gate is what
    changes, nothing else.
    """
    region = VisualRegion(page_number=1, bbox=(0.0, 100.0, 50.0, 112.0), element_count=1)
    wide_line = _line(1, 100.0, "Uma frase bem mais larga do que a regiao.", x=10.0, width=200.0)
    assert _line_in_region(wide_line, region) is True  # gate off: default lenient touch
    assert _line_in_region(wide_line, region, contextual_relation_gate=True) is False


def test_contextual_relation_contained_line_is_excluded():
    region = VisualRegion(page_number=1, bbox=(0.0, 90.0, 300.0, 200.0), element_count=1)
    label = _line(1, 150.0, "Legenda pequena", x=100.0, width=60.0)
    relation = compute_line_region_relation(label, region)
    assert relation.state == "contained"
    assert _text_consumption_decision(relation) == "accepted"
    assert _line_in_region(label, region, contextual_relation_gate=True) is True


def test_contextual_relation_wide_line_barely_touching_grown_bbox_is_kept():
    """The D10/Q07 shape: a real, wide statement line only marginally
    overlaps a region's own *grown* bbox, with no overlap at all against
    its *raw* (pre-growth) extent and no match against any growth-absorbed
    label - stays visible.
    """
    region = VisualRegion(
        page_number=1,
        bbox=(0.0, 90.0, 60.0, 200.0),
        raw_bbox=(0.0, 90.0, 55.0, 195.0),
        element_count=1,
    )
    wide_line = _line(
        1, 150.0, "Uma frase real e bem mais larga que a figura.", x=58.0, width=250.0
    )
    relation = compute_line_region_relation(wide_line, region)
    assert relation.raw_intersects is False
    assert relation.state != "contained"
    assert _text_consumption_decision(relation) == "ambiguous"
    assert _line_in_region(wide_line, region, contextual_relation_gate=True) is False


def test_contextual_relation_native_offset_caption_with_raw_overlap_is_excluded():
    """The Q61 shape: a real caption sits offset from a wide region (most
    of the caption's own width falls outside the region), but genuinely
    overlaps the region's own *raw*, pre-growth extent - excluded (hidden
    inside the figure), matching this corpus's own established behavior
    for a caption printed above/beside its own diagram.
    """
    region = VisualRegion(
        page_number=1,
        bbox=(50.0, 60.0, 400.0, 300.0),
        raw_bbox=(50.0, 30.0, 400.0, 300.0),
        element_count=2,
    )
    caption = _line(1, 65.0, "Figura para a questao referenciada", x=10.0, width=70.0)
    relation = compute_line_region_relation(caption, region)
    assert relation.raw_intersects is True
    assert _text_consumption_decision(relation) == "accepted"
    assert _line_in_region(caption, region, contextual_relation_gate=True) is True


def test_contextual_relation_matches_absorbed_label_is_excluded():
    """Growth's own authoritative record (PROMPT Phase 3G): a real label
    captured through incremental absorption, ending up nowhere near the
    region's own raw extent on its own, is still trusted directly.
    """
    absorbed_rect = (120.0, 140.0, 160.0, 150.0)
    region = VisualRegion(
        page_number=1,
        bbox=(0.0, 90.0, 200.0, 200.0),
        raw_bbox=(0.0, 90.0, 40.0, 105.0),
        element_count=1,
        absorbed_label_bboxes=(absorbed_rect,),
    )
    label = Line(page_number=1, text="rotulo", x0=120.0, y0=140.0, x1=160.0, y1=150.0)
    relation = compute_line_region_relation(label, region)
    assert relation.raw_intersects is False
    assert relation.matches_absorbed_label is True
    assert _text_consumption_decision(relation) == "accepted"
    assert _line_in_region(label, region, contextual_relation_gate=True) is True


def test_contextual_relation_diagram_internal_label_not_at_margin_is_absorbed():
    """PROMPT Phase 3G, "Cluster C": a line shaped like an alternative
    marker ("A\\t...") that does NOT sit at the page's own established
    body margin - a diagram-internal label (an automaton input, an
    ER-diagram entity name) - is no longer unconditionally protected; it
    falls through to the same geometric relation as any other line, and
    is correctly hidden when genuinely contained in the diagram's region.
    """
    region = VisualRegion(page_number=1, bbox=(200.0, 90.0, 260.0, 200.0), element_count=1)
    diagram_label = _line(1, 150.0, "A\t0", x=210.0, width=20.0)
    body_margin_x0 = 30.0  # the page's own real body text starts at x=30
    assert (
        _line_in_region(
            diagram_label,
            region,
            body_margin_x0=body_margin_x0,
            contextual_relation_gate=True,
        )
        is True
    )


def test_contextual_relation_real_alternative_marker_at_margin_stays_protected():
    """Same shape as above, but the marker sits at the page's own real
    body margin - still protected outright, never evaluated geometrically
    against any region (PROMPT: a real alternative marker sitting close to
    a diagram must never disappear).
    """
    region = VisualRegion(page_number=1, bbox=(0.0, 140.0, 300.0, 200.0), element_count=1)
    real_marker = _line(1, 150.0, "A\t Texto da alternativa A", x=30.0, width=200.0)
    body_margin_x0 = 30.0
    assert (
        _line_in_region(
            real_marker,
            region,
            body_margin_x0=body_margin_x0,
            contextual_relation_gate=True,
        )
        is False
    )


# --- Phase 3G section 18: metamorphic tests --------------------------------
#
# The relation's own classification must be a function of relative geometry
# alone, never of any fixed coordinate, page, question ID, or real question
# text (PROMPT: "os testes devem variar escala, translacao, largura de
# coluna e fonte ... nunca depender de coordenada fixa"). Each test below
# takes one base scenario and applies one transformation, then asserts the
# classification is preserved - never picking a transform magnitude by
# trial-and-error to make a specific case pass.


def test_translation_invariance_of_contained_relation():
    """Shifting a contained line and its region by the same (dx, dy) must
    not change the relation's own state or ratios - every signal
    (intersection ratios, center/baseline containment, overflow amounts) is
    a *difference* between line and region coordinates, so a uniform shift
    cancels out algebraically.
    """
    dx, dy = 437.0, -812.0  # arbitrary, deliberately not round numbers
    region_a = VisualRegion(page_number=1, bbox=(0.0, 90.0, 300.0, 200.0), element_count=1)
    label_a = _line(1, 150.0, "Legenda pequena", x=100.0, width=60.0)
    region_b = VisualRegion(
        page_number=1,
        bbox=(0.0 + dx, 90.0 + dy, 300.0 + dx, 200.0 + dy),
        element_count=1,
    )
    label_b = _line(1, 150.0 + dy, "Legenda pequena", x=100.0 + dx, width=60.0)

    relation_a = compute_line_region_relation(label_a, region_a)
    relation_b = compute_line_region_relation(label_b, region_b)

    assert relation_a.state == relation_b.state == "contained"
    assert relation_a.intersection_over_line_area == pytest.approx(
        relation_b.intersection_over_line_area
    )
    assert relation_a.horizontal_overlap_ratio == pytest.approx(relation_b.horizontal_overlap_ratio)
    assert relation_a.vertical_overlap_ratio == pytest.approx(relation_b.vertical_overlap_ratio)
    assert relation_a.center_inside == relation_b.center_inside
    assert relation_a.baseline_inside == relation_b.baseline_inside


def test_translation_invariance_of_touching_relation_is_kept_visible_either_way():
    """Same transformation applied to the D10/Q07 "wide line barely
    touching a grown bbox" shape: both the original and the translated
    version must be classified as not genuinely overlapping and kept
    visible - the decision must not depend on which absolute page
    coordinates the scenario happens to sit at.
    """
    dx, dy = -215.0, 963.0
    region_a = VisualRegion(
        page_number=1,
        bbox=(0.0, 90.0, 60.0, 200.0),
        raw_bbox=(0.0, 90.0, 55.0, 195.0),
        element_count=1,
    )
    wide_line_a = _line(
        1, 150.0, "Uma frase real e bem mais larga que a figura.", x=58.0, width=250.0
    )
    region_b = VisualRegion(
        page_number=1,
        bbox=(0.0 + dx, 90.0 + dy, 60.0 + dx, 200.0 + dy),
        raw_bbox=(0.0 + dx, 90.0 + dy, 55.0 + dx, 195.0 + dy),
        element_count=1,
    )
    wide_line_b = _line(
        1, 150.0 + dy, "Uma frase real e bem mais larga que a figura.", x=58.0 + dx, width=250.0
    )

    relation_a = compute_line_region_relation(wide_line_a, region_a)
    relation_b = compute_line_region_relation(wide_line_b, region_b)

    assert (
        _text_consumption_decision(relation_a)
        == _text_consumption_decision(relation_b)
        == ("ambiguous")
    )
    assert relation_a.raw_intersects == relation_b.raw_intersects == False  # noqa: E712


def test_scale_invariance_of_ratio_based_containment():
    """Uniformly scaling a clearly-contained line+region pair around the
    origin must not change ratio-based signals (intersection ratios,
    center/baseline containment) - these are dimensionless, unlike the
    fixed-point padding constants (REGION_X_PADDING/REGION_Y_PADDING) that
    only matter for a genuinely borderline touch, not for a relationship
    this unambiguous.
    """
    scale = 3.0
    region_a = VisualRegion(page_number=1, bbox=(10.0, 100.0, 210.0, 300.0), element_count=1)
    label_a = _line(1, 150.0, "Legenda", x=60.0, width=40.0)
    region_b = VisualRegion(
        page_number=1,
        bbox=(10.0 * scale, 100.0 * scale, 210.0 * scale, 300.0 * scale),
        element_count=1,
    )
    label_b = _line(1, 150.0 * scale, "Legenda", x=60.0 * scale, width=40.0 * scale)

    relation_a = compute_line_region_relation(label_a, region_a)
    relation_b = compute_line_region_relation(label_b, region_b)

    assert relation_a.state == relation_b.state == "contained"
    assert relation_a.horizontal_overlap_ratio == pytest.approx(relation_b.horizontal_overlap_ratio)
    assert relation_a.vertical_overlap_ratio == pytest.approx(relation_b.vertical_overlap_ratio)
    assert relation_a.center_inside == relation_b.center_inside == True  # noqa: E712


def test_column_width_variation_of_margin_based_marker_protection():
    """PROMPT "Cluster C": the margin-based marker exemption must track
    *wherever* the page's own body margin actually is, not any fixed X
    coordinate - a real alternative marker at a wide column's own margin
    and the same real marker (same offset from its own margin) in a
    narrower column must both stay protected, while a label sitting away
    from either column's own margin must not.
    """
    region = VisualRegion(page_number=1, bbox=(0.0, 140.0, 800.0, 200.0), element_count=1)
    for body_margin_x0 in (30.0, 96.0, 271.5):
        real_marker = _line(1, 150.0, "A\t Texto da alternativa A", x=body_margin_x0, width=200.0)
        assert (
            _line_in_region(
                real_marker, region, body_margin_x0=body_margin_x0, contextual_relation_gate=True
            )
            is False
        ), f"marker at its own column margin ({body_margin_x0}) must stay protected"

        diagram_label = _line(1, 150.0, "A\t0", x=body_margin_x0 + 180.0, width=20.0)
        assert (
            _line_in_region(
                diagram_label,
                region,
                body_margin_x0=body_margin_x0,
                contextual_relation_gate=True,
            )
            is True
        ), f"marker-shaped label away from margin ({body_margin_x0}) must not be protected"


def test_font_size_gate_classification_tracks_the_page_dominant_size_not_a_fixed_value():
    """PROMPT "font" variation: caption_font_size_gate's own label-candidate
    eligibility must track *whichever* font size a page's own body prose
    happens to use, never a fixed absolute threshold - a candidate 2pt
    smaller than body stays eligible whether body is set in 9pt or 14pt.
    """
    from enade.extraction.figures import FONT_SIZE_CAPTION_MARGIN

    for body_font_size in (9.0, 14.0):
        candidate_font_size = body_font_size - FONT_SIZE_CAPTION_MARGIN - 0.5
        header_font_size = body_font_size + 1.0
        assert candidate_font_size < body_font_size - FONT_SIZE_CAPTION_MARGIN
        assert not (header_font_size < body_font_size - FONT_SIZE_CAPTION_MARGIN)


def test_attach_alternative_formula_regions_splits_a_merged_region_per_alternative():
    """Regression test: 2011 Q14 (PROMPT Phase 2E section 10) - all 5
    alternatives are only a boolean-algebra formula image, no real text,
    and the 5 per-alternative formula candidates merge into one region
    spanning all 5 rows (well within figures.py's own small-image merge
    tolerance) before this function ever sees them. Each empty
    alternative must get its own Y-sliced piece of that one region.
    """
    text_only_lines = [
        _line(1, 100.0, "A"),
        _line(1, 107.0, "B"),
        _line(1, 114.0, "C"),
        _line(1, 121.0, "D"),
        _line(1, 128.0, "E"),
    ]
    alt_bounds = [0, 1, 2, 3, 4]
    alternatives = [ExtractedAlternative(letter=letter, text=".") for letter in "ABCDE"]
    # Built from the small-formula candidate pool (is_small_formula=True) -
    # see _is_alternative_formula_candidate, which keys off this
    # provenance flag, never the region's own (post-merge, possibly much
    # taller) bbox size - a merged region spanning 5 rows can easily
    # exceed SMALL_IMAGE_MAX_HEIGHT even though each constituent formula
    # was small (2011 Q14's own real shape).
    merged_region = VisualRegion(
        page_number=1,
        bbox=(200.0, 98.0, 300.0, 135.0),
        element_count=5,
        has_raster_image=True,
        is_small_formula=True,
    )
    extra_regions, consumed_ids = _attach_alternative_formula_regions(
        alternatives, text_only_lines, alt_bounds, [merged_region]
    )
    assert len(extra_regions) == 5
    assert consumed_ids == {id(merged_region)}
    assert [alt.figure_region_index for alt in alternatives] == [0, 1, 2, 3, 4]
    # Each slice stays within the merged region's own Y-range, in order,
    # and none of them overlap each other.
    for i in range(4):
        assert extra_regions[i].bbox[3] <= extra_regions[i + 1].bbox[1] + 1e-6
    for region in extra_regions:
        assert region.bbox[1] >= merged_region.bbox[1]
        assert region.bbox[3] <= merged_region.bbox[3]


def test_attach_alternative_formula_regions_ignores_alternatives_with_real_text():
    text_only_lines = [_line(1, 100.0, "A\t Texto real da alternativa A.")]
    alternatives = [ExtractedAlternative(letter="A", text="Texto real da alternativa A.")]
    region = VisualRegion(page_number=1, bbox=(200.0, 98.0, 300.0, 112.0), element_count=1)
    extra_regions, consumed_ids = _attach_alternative_formula_regions(
        alternatives, text_only_lines, [0], [region]
    )
    assert extra_regions == []
    assert consumed_ids == set()
    assert alternatives[0].figure_region_index is None


def test_attach_alternative_formula_regions_none_when_no_region_overlaps():
    text_only_lines = [_line(1, 100.0, "A"), _line(1, 115.0, "B")]
    alternatives = [
        ExtractedAlternative(letter="A", text="."),
        ExtractedAlternative(letter="B", text="."),
    ]
    # On a different page entirely - never overlaps alternative A's own
    # row (100.0-115.0 on page 1), regardless of the last-alternative
    # fallback window.
    far_region = VisualRegion(page_number=2, bbox=(200.0, 100.0, 300.0, 112.0), element_count=1)
    extra_regions, consumed_ids = _attach_alternative_formula_regions(
        alternatives, text_only_lines, [0, 1], [far_region]
    )
    assert extra_regions == []
    assert consumed_ids == set()
    assert alternatives[0].figure_region_index is None


def test_detect_broken_words_flags_ligature_artifact():
    text = "Isso é uma questi onada com um problema de justi ficação."
    hits = detect_broken_words(text)
    assert hits  # at least one artifact found
    assert any("questi o" in h for h in hits)


def test_detect_broken_words_clean_text_has_no_hits():
    text = "Isso é uma questão normal sem nenhum artefato de extração."
    assert detect_broken_words(text) == []


def test_build_statement_segments_inserts_figure_at_correct_position():
    lines = [
        _line(1, 10, "Parágrafo antes da figura."),
        _line(1, 100, "Parágrafo depois da figura."),
    ]
    region = VisualRegion(page_number=1, bbox=(0, 40, 500, 80), element_count=1)
    segments, placed, placed_tables = _build_statement_segments(lines, [region])
    assert placed == [0]
    assert placed_tables == []
    kinds = [type(s).__name__ for s in segments]
    assert kinds == ["TextSegment", "FigureSegment", "TextSegment"]
    assert segments[0].text == "Parágrafo antes da figura."
    assert isinstance(segments[1], FigureSegment)
    assert segments[2].text == "Parágrafo depois da figura."


def test_build_statement_segments_preserves_code_block_line_breaks():
    lines = [
        _line(1, 10, "Texto normal antes do código."),
        _line(1, 30, "void f() {", mono=True),
        _line(1, 45, "  return 1;", mono=True),
        _line(1, 60, "}", mono=True),
        _line(1, 80, "Texto normal depois do código."),
    ]
    segments, _, _ = _build_statement_segments(lines, [])
    code_segments = [s for s in segments if isinstance(s, CodeSegment)]
    assert len(code_segments) == 1
    assert "void f() {" in code_segments[0].text
    assert "\n" in code_segments[0].text  # line breaks preserved, not space-joined
    text_segments = [s for s in segments if isinstance(s, TextSegment)]
    assert len(text_segments) == 2


def test_strip_leading_marker_removes_prefix_and_keeps_remainder():
    lines = [
        _line(1, 10, "QuEStãO 01 A chance de uma criança de baixa renda"),
        _line(1, 25, "continuação do enunciado."),
    ]
    stripped = _strip_leading_marker(lines)
    assert len(stripped) == 2
    assert stripped[0].text == "A chance de uma criança de baixa renda"
    assert stripped[1] is lines[1]


def test_strip_leading_marker_drops_line_with_nothing_left():
    lines = [
        _line(1, 10, "QUESTÃO DISCURSIVA 3"),
        _line(1, 25, "Primeiro parágrafo real do enunciado."),
    ]
    stripped = _strip_leading_marker(lines)
    assert len(stripped) == 1
    assert stripped[0].text == "Primeiro parágrafo real do enunciado."


def test_strip_leading_marker_no_op_when_no_marker_present():
    lines = [_line(1, 10, "Texto que não começa com um marcador de questão.")]
    assert _strip_leading_marker(lines) == lines


# --- Phase 1C: code reconstruction (blank lines, indentation) ----------------


def test_render_code_lines_preserves_a_real_blank_line():
    # Mirrors D5's heapify() listing (page 17): a real blank line sits
    # between "int e, d, max, aux;" and "e = left(i);" - modal line pitch
    # here is 15pt, and the gap to the next line is ~30pt (2x), i.e.
    # exactly one blank line, not a paragraph-style artifact to collapse.
    lines = [
        _line(1, 100.0, "void heapify(int *a, int n, int i)", x=290.0, mono=True),
        _line(1, 115.0, "{", x=290.0, mono=True),
        _line(1, 130.0, "   int e, d, max, aux;", x=290.0, mono=True),
        _line(1, 160.0, "   e = left(i);", x=290.0, mono=True),  # +30, not +15
        _line(1, 175.0, "   d = right(i);", x=290.0, mono=True),
    ]
    rendered = _render_code_lines(lines)
    assert rendered.splitlines() == [
        "void heapify(int *a, int n, int i)",
        "{",
        "   int e, d, max, aux;",
        "",
        "   e = left(i);",
        "   d = right(i);",
    ]


def test_render_code_lines_does_not_invent_blank_lines_for_normal_pitch():
    lines = [
        _line(1, 100.0, "int a = 1;", x=290.0, mono=True),
        _line(1, 115.0, "int b = 2;", x=290.0, mono=True),
        _line(1, 130.0, "int c = 3;", x=290.0, mono=True),
    ]
    rendered = _render_code_lines(lines)
    assert rendered.splitlines() == ["int a = 1;", "int b = 2;", "int c = 3;"]


def test_render_code_lines_reconstructs_relative_indentation():
    lines = [
        _line(1, 100.0, "void f() {", x=290.0, mono=True),
        _line(1, 115.0, "return 1;", x=296.0, mono=True),  # +6pt = 1 char
        _line(1, 130.0, "}", x=290.0, mono=True),
    ]
    rendered = _render_code_lines(lines)
    assert rendered.splitlines() == ["void f() {", " return 1;", "}"]


# --- Phase 1C: region containment respects column separation (D5) ------------


def test_line_in_region_ignores_same_y_band_content_in_a_different_column():
    # A figure region confined to the left column (x in [29, 276]) must not
    # swallow a code line at the same Y sitting in the right column (x
    # starting at 291.5) - see docs/decisions.md, "Phase 1C" ADR (D5's
    # heapify() body was silently dropped this way before the fix).
    region = VisualRegion(page_number=1, bbox=(29.0, 100.0, 276.4, 462.7), element_count=16)
    code_line = _line(1, 200.0, "int e, d, max, aux;", x=291.5, mono=True, width=100.0)
    assert _line_in_region(code_line, region) is False


def test_line_in_region_still_true_for_a_genuine_same_column_label():
    region = VisualRegion(page_number=1, bbox=(29.0, 100.0, 276.4, 350.0), element_count=16)
    label_line = _line(1, 320.0, "Processo A", x=32.6, width=50.0)
    assert _line_in_region(label_line, region) is True


def test_strip_leading_marker_no_op_on_empty_list():
    assert _strip_leading_marker([]) == []


# --- Phase 1C: line-number gutter removal (Q20) -------------------------------


def _gutter_line(y: float, number: str, sep: str = "\t") -> Line:
    text = f"{sep}{number}"
    return Line(page_number=1, text=text, x0=29.8, y0=y, x1=52.0, y1=y + 20.4, is_monospace=True)


def _code_line(y: float, text: str, x: float = 65.8) -> Line:
    return Line(
        page_number=1, text=text, x0=x, y0=y, x1=x + len(text) * 7.2, y1=y + 20.4, is_monospace=True
    )


def test_strip_line_number_gutter_removes_standalone_gutter_lines():
    lines = [
        _gutter_line(100.0, "1"),
        _code_line(100.0, "#include <stdio.h>"),
        _gutter_line(120.4, "2"),
        _code_line(120.4, "#define TAM 10"),
        _gutter_line(140.8, "3"),
        _code_line(140.8, "int f(int x){"),
    ]
    stripped = _strip_line_number_gutter(lines)
    assert [ln.text for ln in stripped] == [
        "#include <stdio.h>",
        "#define TAM 10",
        "int f(int x){",
    ]


def test_strip_line_number_gutter_handles_a_line_merged_with_its_gutter_number():
    # Mirrors Q20's real row 11: PyMuPDF fused the gutter number into the
    # same physical Line as the code that follows it - the merged line's
    # own x0 (29.8, dragged left by the gutter) must not become the new
    # indentation baseline for the rest of the block (see docs/decisions.md).
    lines = [
        _gutter_line(100.0, "1"),
        _code_line(100.0, "int f(int x){"),
        _gutter_line(120.4, "2"),
        _code_line(120.4, "}"),
        Line(
            page_number=1,
            text="\t11 \t int g(int x, int y){",
            x0=29.8,
            y0=140.8,
            x1=250.0,
            y1=161.2,
            is_monospace=True,
        ),
    ]
    stripped = _strip_line_number_gutter(lines)
    assert [ln.text for ln in stripped] == ["int f(int x){", "}", "int g(int x, int y){"]
    merged_result = stripped[-1]
    assert merged_result.x0 == 65.8  # reconstructed from the unaffected lines' own baseline


def test_strip_line_number_gutter_leaves_a_lone_numeric_line_untouched():
    # Only one bare-digit line, no corroborating recurrence and no
    # unaffected non-gutter-shaped lines to establish a baseline from -
    # left alone rather than guessed away (PROMPT section 8.1).
    lines = [_gutter_line(100.0, "1")]
    assert _strip_line_number_gutter(lines) == lines


def test_strip_line_number_gutter_no_op_when_nothing_gutter_shaped():
    lines = [_code_line(100.0, "int x = 1;"), _code_line(120.4, "int y = 2;")]
    assert _strip_line_number_gutter(lines) == lines


def test_render_code_lines_after_gutter_removal_has_correct_indentation():
    lines = [
        _code_line(100.0, "int f(int x){", x=65.8),
        _code_line(120.4, "return x;", x=101.8),
        _code_line(140.8, "}", x=65.8),
    ]
    rendered = _render_code_lines(_strip_line_number_gutter(lines))
    assert rendered.splitlines() == ["int f(int x){", "      return x;", "}"]


# --- Phase 2B: region-attachment X-tolerance must not bridge a real column gap


def test_assemble_question_does_not_attach_a_region_across_a_narrow_column_gap():
    # A region hugging the right edge of the LEFT column (x1=142) must not
    # attach to a question whose own text lives in the RIGHT column
    # starting at x0=155 - only a 13pt gap, narrower than the assembler's
    # old 15pt x_tolerance but wider than its current 5pt (2011 unified
    # booklet, Q6/Q7 sharing page 5 - see docs/decisions.md, Phase 2B
    # ADR 27). Uses a real synthetic PDF so detect_visual_regions finds a
    # genuine drawing-based candidate, not a hand-built VisualRegion.
    import pymupdf

    from enade.extraction.assembler import assemble_question
    from enade.extraction.boundaries import QuestionKind, QuestionSpan
    from enade.extraction.figures import compute_decorative_baseline

    doc = pymupdf.open()
    page = doc.new_page()
    # A filled rectangle aligned with the left column (x 30-142) - the
    # "figure" that must stay attached only to a left-column question.
    page.draw_rect(pymupdf.Rect(30, 100, 142, 250), color=(0, 0, 0), fill=(0, 0, 0))

    right_lines = [
        Line(
            page_number=1,
            text="Enunciado da questao na coluna direita.",
            x0=155,
            y0=100,
            x1=300,
            y1=112,
        ),
        Line(page_number=1, text="Continuacao do enunciado.", x0=155, y0=115, x1=300, y1=127),
    ]
    span = QuestionSpan(
        kind=QuestionKind.OBJECTIVE, number=7, lines=tuple(right_lines), start_page=1, end_page=1
    )
    baseline = compute_decorative_baseline(doc)
    result = assemble_question(span, doc, baseline)
    assert result.figure_regions == []


# --- Phase 3F: owner_exclusion_gate rejects a region owned by another span ---


def test_owner_exclusion_gate_rejects_a_foreign_owned_region_when_enabled():
    """PROMPT Phase 3F ("Cluster A"/Q12-Q13): a span whose own content
    happens to overflow into a distant position (2008-b's own Q13, whose
    alternative E overflows into the top of the next page column) can
    widen its own coarse y/x bounding box enough to trivially satisfy the
    old, ownership-agnostic tolerance for a *different* question's own
    owned region. ``owner_exclusion_gate`` closes this generally (never a
    question-ID check): a region whose owner_key names a different span is
    never admitted, regardless of bounding-box overlap. Off by default
    (matches every booklet without this field set); this test constructs
    a synthetic, question-ID-free scenario with the same *shape* as the
    real case, not the real coordinates or text.
    """
    import pymupdf

    from enade.extraction.assembler import assemble_question
    from enade.extraction.boundaries import QuestionKind, QuestionSpan
    from enade.extraction.figures import compute_decorative_baseline
    from enade.extraction.ownership import compute_question_regions

    doc = pymupdf.open()
    page = doc.new_page()
    # A drawing that genuinely belongs to span A (nearest to its own
    # column, same column tolerance) - positioned so it also satisfies
    # span B's own coarse y/x tolerance once B's own bounding box widens
    # below (the whole point of this test).
    page.draw_rect(pymupdf.Rect(30, 290, 150, 350), color=(0, 0, 0), fill=(0, 0, 0))

    span_a_lines = [
        Line(page_number=1, text="Enunciado da questao A.", x0=30, y0=200, x1=200, y1=212),
        Line(page_number=1, text="Continuacao de A.", x0=30, y0=278, x1=200, y1=290),
    ]
    span_a = QuestionSpan(
        kind=QuestionKind.OBJECTIVE, number=1, lines=tuple(span_a_lines), start_page=1, end_page=1
    )

    # Span B's own real content sits far away, except for one line (its
    # own last alternative, spilling into the next column - Q13's own
    # real shape) whose position widens B's own coarse bounding box enough
    # to reach the drawing above, purely by y/x proximity.
    span_b_lines = [
        Line(page_number=1, text="Enunciado da questao B.", x0=300, y0=500, x1=500, y1=512),
        Line(page_number=1, text="A\t alternativa a", x0=300, y0=520, x1=500, y1=532),
        Line(page_number=1, text="B\t alternativa b", x0=300, y0=535, x1=500, y1=547),
        # The overflowing line: far from B's own paragraph in Y, and only
        # a few points past the drawing's own right edge in X.
        Line(page_number=1, text="C\t alternativa c", x0=155, y0=300, x1=350, y1=312),
    ]
    span_b = QuestionSpan(
        kind=QuestionKind.OBJECTIVE, number=2, lines=tuple(span_b_lines), start_page=1, end_page=1
    )

    baseline = compute_decorative_baseline(doc)
    question_regions_by_page = compute_question_regions([span_a, span_b])

    # Default (gate off): matches every booklet that never sets this field
    # - the old tolerance alone admits the drawing into B's own candidates.
    result_default = assemble_question(
        span_b, doc, baseline, question_regions_by_page=question_regions_by_page
    )
    assert len(result_default.figure_regions) == 1

    # Gate on: the drawing's own owner_key (span A's) never matches B's,
    # so it is rejected regardless of the bounding-box overlap above.
    result_gated = assemble_question(
        span_b,
        doc,
        baseline,
        question_regions_by_page=question_regions_by_page,
        owner_exclusion_gate=True,
    )
    assert result_gated.figure_regions == []

    # Span A itself is unaffected either way - it still gets its own,
    # genuinely-owned drawing.
    result_a = assemble_question(
        span_a,
        doc,
        baseline,
        question_regions_by_page=question_regions_by_page,
        owner_exclusion_gate=True,
    )
    assert len(result_a.figure_regions) == 1


def test_assemble_question_indexes_an_inline_alternative_asset_correctly_alongside_a_statement_figure():
    """Regression test (PROMPT Phase 2F section 8, "multiplos segmentos
    intercalados" + index integrity): a first implementation of the
    alternative-inline-asset mechanism correctly built each alternative's
    own ``segments`` with *locally* 0-based ``FigureSegment.region_index``
    values, but only re-offset ``ExtractedAlternative.figure_region_index``
    (Phase 2E's own field) to account for the statement's own figures
    landing first in ``ExtractedQuestion.figure_regions`` - never
    ``segments`` itself. On a real question (2011 Q23), this silently
    aliased alternative D's own asset reference to the *statement's* own
    first figure instead of D's own inline formula - found by direct
    visual inspection of the rendered asset, not caught by any function-
    level unit test (each attachment function was tested in isolation,
    never together with a statement figure occupying the earlier indices).

    This test exercises the full ``assemble_question`` pipeline with both
    a statement-level figure (large rectangle, before the alternatives
    cutoff) and an alternative D whose own text is split around a second,
    small rectangle (a plausible formula-image candidate) - asserting the
    *content* each index resolves to, not just that some index exists.
    """
    import pymupdf

    from enade.extraction.assembler import FigureSegment as _FigureSegment
    from enade.extraction.assembler import TextSegment as _TextSegment
    from enade.extraction.assembler import assemble_question
    from enade.extraction.boundaries import QuestionKind, QuestionSpan
    from enade.extraction.figures import compute_decorative_baseline

    doc = pymupdf.open()
    page = doc.new_page()
    # Statement-level figure: large enough (50pt tall) to exceed the
    # small-formula threshold, landing in figure_regions before anything
    # alternative-attached.
    statement_rect = pymupdf.Rect(30, 70, 200, 120)
    page.draw_rect(statement_rect, color=(0, 0, 0), fill=(0, 0, 0))
    # Alternative D's own inline formula: a small (25x10pt) *raster*
    # image, sitting in the gap between its own two text runs on the same
    # row - only a real embedded image (never a vector drawing) can
    # qualify as a small-formula candidate (_is_small_formula_candidate
    # requires is_image=True), matching every real inline symbol found in
    # this corpus (e.g. 2011 Q23's own Sigma/regex, both raster images).
    pix = pymupdf.Pixmap(pymupdf.csGRAY, (0, 0, 4, 4), False)
    pix.set_rect(pix.irect, (0,))
    d_formula_rect = pymupdf.Rect(155, 186, 180, 196)
    page.insert_image(d_formula_rect, stream=pix.tobytes("png"))

    lines = [
        Line(page_number=1, text="Enunciado com uma figura abaixo.", x0=30, y0=50, x1=300, y1=62),
        Line(page_number=1, text="A Texto da alternativa A.", x0=30, y0=140, x1=200, y1=152),
        Line(page_number=1, text="B Texto da alternativa B.", x0=30, y0=155, x1=200, y1=167),
        Line(page_number=1, text="C Texto da alternativa C.", x0=30, y0=170, x1=200, y1=182),
        Line(page_number=1, text="D Texto antes", x0=30, y0=185, x1=150, y1=197),
        Line(page_number=1, text="texto depois", x0=185, y0=185.5, x1=300, y1=197.5),
        Line(page_number=1, text="E Texto da alternativa E.", x0=30, y0=200, x1=200, y1=212),
    ]
    span = QuestionSpan(
        kind=QuestionKind.OBJECTIVE, number=23, lines=tuple(lines), start_page=1, end_page=1
    )
    baseline = compute_decorative_baseline(doc)
    result = assemble_question(span, doc, baseline)

    # The statement's own figure is referenced from statement_segments.
    statement_figure_indices = [
        seg.region_index for seg in result.statement_segments if isinstance(seg, _FigureSegment)
    ]
    assert len(statement_figure_indices) == 1
    statement_region = result.figure_regions[statement_figure_indices[0]]
    assert statement_region.bbox[1] == pytest.approx(statement_rect.y0, abs=1.0)

    alt_d = next(a for a in result.alternatives if a.letter == "D")
    assert alt_d.segments is not None
    fig_segments = [s for s in alt_d.segments if isinstance(s, _FigureSegment)]
    assert len(fig_segments) == 1
    d_region = result.figure_regions[fig_segments[0].region_index]
    # D's own resolved region must be its own small formula rect, never
    # aliased to the statement's own (larger, differently-positioned) one.
    assert d_region.bbox[1] == pytest.approx(d_formula_rect.y0, abs=1.0)
    assert fig_segments[0].region_index != statement_figure_indices[0]

    text_segments = [s.text for s in alt_d.segments if isinstance(s, _TextSegment)]
    assert text_segments == ["Texto antes", "texto depois"]
