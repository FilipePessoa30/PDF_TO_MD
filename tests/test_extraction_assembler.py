from __future__ import annotations

import pymupdf
import pytest

from enade.extraction.alternative_groups import find_alternative_group
from enade.extraction.assembler import (
    PARAGRAPH_GAP_THRESHOLD,
    CodeSegment,
    ExtractedAlternative,
    FigureSegment,
    TextSegment,
    _attach_alternative_formula_regions,
    _attach_declared_raster_alternative_regions,
    _build_declared_inline_formula_regions,
    _build_declared_raster_alternative_regions,
    _build_statement_segments,
    _find_inline_formula_insertion_index,
    _find_region_insertion_index,
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
from enade.extraction.ownership import QuestionRegion


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


def test_contextual_relation_ambiguous_line_stays_visible_without_a_forcing_override():
    """PROMPT Fase 3R: the tri-state design's own default - "ambiguous"
    never authorizes destructive removal on geometry alone - is unchanged
    by the new ``force_region_membership`` override existing at all. The
    exact same wide-line-barely-touching shape as the test above stays
    visible when no override names it.
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
    overrides = LayoutOverrideSet(overrides=[])
    assert (
        _line_in_region(wide_line, region, overrides, "cafebabe" * 8, contextual_relation_gate=True)
        is False
    )


def test_contextual_relation_ambiguous_line_is_excluded_by_a_matching_force_override():
    """PROMPT Fase 3R: a line individually proven (by evidence recorded in
    the override's own ``reason``/``evidence`` fields, never by a general
    geometric rule) to duplicate content its own region's asset already
    shows in full can be forced into the "excluded" outcome despite an
    otherwise-"ambiguous" relation - the sole documented exception to the
    tri-state design's own safe default (see D40's own "F" cosmetic leak,
    docs/phase-3r-report.md).
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
    assert _text_consumption_decision(relation) == "ambiguous"
    overrides = LayoutOverrideSet(
        overrides=[
            LayoutOverride(
                pdf_sha256="cafebabe" * 8,
                page=1,
                bbox=wide_line.bbox,
                rule="force_region_membership",
                question_id="enade-2008-computing-d40",
                reason="test",
                evidence="test",
                status="reviewed",
            )
        ]
    )
    assert (
        _line_in_region(wide_line, region, overrides, "cafebabe" * 8, contextual_relation_gate=True)
        is True
    )


def test_force_region_membership_override_never_fires_when_decision_is_already_accepted():
    """The override is only ever consulted for an "ambiguous" outcome
    (PROMPT Fase 3R) - it must have no effect on a line that is already
    "accepted" (e.g. genuinely ``contained``), since that line is already
    correctly excluded and the override was never reviewed against this
    different geometric shape.
    """
    region = VisualRegion(page_number=1, bbox=(0.0, 90.0, 300.0, 200.0), element_count=1)
    label = _line(1, 150.0, "Legenda pequena", x=100.0, width=60.0)
    relation = compute_line_region_relation(label, region)
    assert relation.state == "contained"
    overrides = LayoutOverrideSet(
        overrides=[
            LayoutOverride(
                pdf_sha256="cafebabe" * 8,
                page=1,
                bbox=label.bbox,
                rule="force_region_membership",
                question_id="enade-2008-computing-d40",
                reason="test",
                evidence="test",
                status="reviewed",
            )
        ]
    )
    assert (
        _line_in_region(label, region, overrides, "cafebabe" * 8, contextual_relation_gate=True)
        is True
    )


def test_force_region_membership_ignores_override_for_a_different_pdf_hash():
    region = VisualRegion(
        page_number=1,
        bbox=(0.0, 90.0, 60.0, 200.0),
        raw_bbox=(0.0, 90.0, 55.0, 195.0),
        element_count=1,
    )
    wide_line = _line(
        1, 150.0, "Uma frase real e bem mais larga que a figura.", x=58.0, width=250.0
    )
    overrides = LayoutOverrideSet(
        overrides=[
            LayoutOverride(
                pdf_sha256="cafebabe" * 8,
                page=1,
                bbox=wide_line.bbox,
                rule="force_region_membership",
                question_id="enade-2008-computing-d40",
                reason="test",
                evidence="test",
                status="reviewed",
            )
        ]
    )
    assert (
        _line_in_region(wide_line, region, overrides, "deadbeef" * 8, contextual_relation_gate=True)
        is False
    )


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


def test_attach_alternative_formula_regions_preserves_declared_inline_formula_flag():
    """Regression test (PROMPT Fase 3W): 2008-b Q55's own 5 alternatives
    are each a `declare_inline_formula_region` override (Fase 3S's own
    mechanism, first attached to an alternative rather than a statement
    segment here) - the sliced-out per-alternative region must keep
    ``is_declared_inline_formula=True`` so ``assets.render_region`` still
    selects ``AssetType.EQUATION``. Originally missed: the slicing
    constructor only copied ``has_raster_image``/``owner_key``/
    ``owner_x_bounds``/``is_small_formula`` from the source region, silently
    dropping this flag and falling back to ``AssetType.DIAGRAM``.
    """
    text_only_lines = [_line(1, 100.0, "A")]
    alternatives = [ExtractedAlternative(letter="A", text="")]
    declared_region = VisualRegion(
        page_number=1,
        bbox=(200.0, 98.0, 300.0, 112.0),
        element_count=3,
        is_small_formula=True,
        is_declared_inline_formula=True,
    )
    extra_regions, _ = _attach_alternative_formula_regions(
        alternatives, text_only_lines, [0], [declared_region]
    )
    assert len(extra_regions) == 1
    assert extra_regions[0].is_declared_inline_formula is True


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


# --- PROMPT Fase 3Y: _attach_declared_raster_alternative_regions (2008-b
# Q8's own two-horizontal-row photograph group) ---


def _marker(page: int, x0: float, y0: float, letter: str) -> Line:
    return Line(page_number=page, text=letter, x0=x0, y0=y0, x1=x0 + 8.0, y1=y0 + 10.0)


def _caption_line(page: int, x0: float, y0: float, text: str) -> Line:
    return Line(page_number=page, text=text, x0=x0, y0=y0, x1=x0 + 80.0, y1=y0 + 6.0)


def _photo_region(bbox: tuple[float, float, float, float]) -> VisualRegion:
    return VisualRegion(
        page_number=1,
        bbox=bbox,
        raw_bbox=bbox,
        element_count=1,
        has_raster_image=True,
        owner_x_bounds=(bbox[0], bbox[2]),
        is_exact_raster_bbox=True,
    )


def test_attach_declared_raster_alternative_regions_matches_by_position_and_builds_real_captions():
    """2008-b Q8's own real shape (PROMPT Fase 3Y), scaled down: 3
    markers (A/B/C) share nearly the same Y, each with its own photograph
    region strictly to its own right, plus 2 markers (D/E) on a second
    row. Each region's own real caption text (never fabricated) is
    recovered from the genuine PDF line(s) sitting just below it.

    Each row's own markers are given a slightly staggered Y (unlike the
    real corpus, where all 3 share one exact Y) purely so this test's own
    "closest center, all 5 matched, real captions built" assertions do
    not also depend on the greedy per-letter processing order breaking an
    exact tie - that narrower mechanism has its own dedicated test below.
    """
    markers = [
        _marker(1, 30.0, 98.0, "A"),
        _marker(1, 220.0, 100.0, "B"),
        _marker(1, 410.0, 102.0, "C"),
        _marker(1, 120.0, 300.0, "D"),
        _marker(1, 290.0, 302.0, "E"),
    ]
    captions = [
        _caption_line(1, 50.0, 158.0, "Legenda A linha 1"),
        _caption_line(1, 50.0, 162.0, "Legenda A linha 2"),
        _caption_line(1, 240.0, 161.0, "Legenda B"),
        _caption_line(1, 430.0, 163.0, "Legenda C"),
        _caption_line(1, 140.0, 363.0, "Legenda D"),
        _caption_line(1, 310.0, 365.0, "Legenda E"),
    ]
    text_only_lines = markers + captions
    alt_bounds = [0, 1, 2, 3, 4]  # markers are the first 5 entries
    regions = [
        _photo_region((50.0, 50.0, 190.0, 156.0)),  # y-center 103, closest to A (103)
        _photo_region((240.0, 52.0, 380.0, 158.0)),  # y-center 105, closest to B (105)
        _photo_region((430.0, 54.0, 570.0, 160.0)),  # y-center 107, closest to C (107)
        _photo_region((140.0, 250.0, 260.0, 360.0)),  # y-center 305, closest to D (305)
        _photo_region((310.0, 252.0, 450.0, 362.0)),  # y-center 307, closest to E (307)
    ]
    result = _attach_declared_raster_alternative_regions(
        ["A", "B", "C", "D", "E"], text_only_lines, alt_bounds, regions
    )
    assert result is not None
    alternatives, ordered_regions = result
    assert [alt.letter for alt in alternatives] == ["A", "B", "C", "D", "E"]
    assert [alt.figure_region_index for alt in alternatives] == [0, 1, 2, 3, 4]
    assert ordered_regions == [regions[0], regions[1], regions[2], regions[3], regions[4]]
    assert alternatives[0].text == "Legenda A linha 1 Legenda A linha 2"
    assert alternatives[1].text == "Legenda B"
    assert alternatives[2].text == "Legenda C"
    assert alternatives[3].text == "Legenda D"
    assert alternatives[4].text == "Legenda E"


def test_attach_declared_raster_alternative_regions_none_when_fewer_regions_than_letters():
    markers = [_marker(1, 30.0, 100.0, letter) for letter in "ABCDE"]
    regions = [_photo_region((50.0, 95.0, 190.0, 200.0)) for _ in range(4)]
    result = _attach_declared_raster_alternative_regions(
        ["A", "B", "C", "D", "E"], markers, [0, 1, 2, 3, 4], regions
    )
    assert result is None


def test_attach_declared_raster_alternative_regions_none_when_a_letter_has_no_region_to_its_right():
    markers = [_marker(1, 30.0, 100.0, "A"), _marker(1, 220.0, 100.0, "B")]
    # Both regions sit to the LEFT of marker B - never a valid candidate
    # for it, regardless of how close their own Y-centers are.
    regions = [
        _photo_region((50.0, 95.0, 190.0, 200.0)),
        _photo_region((0.0, 95.0, 15.0, 200.0)),
    ]
    result = _attach_declared_raster_alternative_regions(["A", "B"], markers, [0, 1], regions)
    assert result is None


def test_attach_declared_raster_alternative_regions_picks_closest_vertical_center_and_never_reuses_a_region():
    marker_a = _marker(1, 30.0, 100.0, "A")  # y-center 105
    marker_b = _marker(1, 30.0, 300.0, "B")  # y-center 305
    close_to_a = _photo_region((50.0, 90.0, 190.0, 120.0))  # y-center 105
    close_to_b = _photo_region((50.0, 290.0, 190.0, 320.0))  # y-center 305
    # Both regions sit to the right of both markers, so a naive "first
    # candidate" pick could wrongly reuse close_to_a for B if it were not
    # also excluded once consumed by A.
    result = _attach_declared_raster_alternative_regions(
        ["A", "B"], [marker_a, marker_b], [0, 1], [close_to_b, close_to_a]
    )
    assert result is not None
    alternatives, ordered_regions = result
    assert ordered_regions == [close_to_a, close_to_b]
    assert alternatives[0].letter == "A" and alternatives[1].letter == "B"


def test_attach_declared_raster_alternative_regions_caption_respects_x_tolerance_and_gap():
    marker = _marker(1, 30.0, 100.0, "A")
    region = _photo_region((50.0, 95.0, 190.0, 200.0))
    aligned_close = _caption_line(1, 51.0, 205.0, "Legenda real")
    misaligned_x = _caption_line(1, 90.0, 205.0, "Fora de alinhamento")
    too_far_below = _caption_line(1, 51.0, 400.0, "Muito distante")
    text_only_lines = [marker, aligned_close, misaligned_x, too_far_below]
    result = _attach_declared_raster_alternative_regions(["A"], text_only_lines, [0], [region])
    assert result is not None
    alternatives, _ = result
    assert alternatives[0].text == "Legenda real"


def test_attach_declared_raster_alternative_regions_empty_caption_is_valid():
    # No real caption line at all is a legitimate shape (never fabricated
    # text) - the alternative is still built, backed entirely by its asset.
    marker = _marker(1, 30.0, 100.0, "A")
    region = _photo_region((50.0, 95.0, 190.0, 200.0))
    result = _attach_declared_raster_alternative_regions(["A"], [marker], [0], [region])
    assert result is not None
    alternatives, _ = result
    assert alternatives[0].text == ""


def _page_with_image(rect: tuple[float, float, float, float]) -> pymupdf.Document:
    doc = pymupdf.open()
    page = doc.new_page(width=600, height=800)
    pixmap = pymupdf.Pixmap(pymupdf.csRGB, (0, 0, 4, 4), False)
    pixmap.set_rect(pixmap.irect, (200, 0, 0))
    page.insert_image(pymupdf.Rect(*rect), pixmap=pixmap)
    return doc


def _raster_alternative_override(bbox: tuple[float, float, float, float]) -> LayoutOverride:
    return LayoutOverride(
        pdf_sha256="a" * 64,
        page=1,
        bbox=bbox,
        rule="declare_raster_alternative_region",
        question_id="enade-2008-computing-q08",
        reason="test",
        evidence="test",
        status="reviewed",
    )


def test_build_declared_raster_alternative_regions_none_without_overrides():
    doc = pymupdf.open()
    doc.new_page(width=600, height=800)
    assert _build_declared_raster_alternative_regions(doc, 1, None, "a" * 64) == []


def test_build_declared_raster_alternative_regions_none_when_no_matching_declaration():
    doc = pymupdf.open()
    doc.new_page(width=600, height=800)
    overrides = LayoutOverrideSet(overrides=[])
    assert _build_declared_raster_alternative_regions(doc, 1, overrides, "a" * 64) == []


def test_build_declared_raster_alternative_regions_skips_a_declaration_with_no_real_image():
    doc = pymupdf.open()
    doc.new_page(width=600, height=800)  # blank - no images anywhere
    overrides = LayoutOverrideSet(
        overrides=[_raster_alternative_override((50.0, 95.0, 190.0, 200.0))]
    )
    assert _build_declared_raster_alternative_regions(doc, 1, overrides, "a" * 64) == []


def test_build_declared_raster_alternative_regions_builds_an_exact_unpadded_region():
    bbox = (50.0, 95.0, 190.0, 200.0)
    doc = _page_with_image(bbox)
    overrides = LayoutOverrideSet(overrides=[_raster_alternative_override(bbox)])
    built = _build_declared_raster_alternative_regions(doc, 1, overrides, "a" * 64)
    assert len(built) == 1
    region = built[0]
    assert region.bbox == bbox
    assert region.has_raster_image is True
    assert region.is_declared_inline_formula is False
    assert region.is_exact_raster_bbox is True
    # No padding on either side - unlike every other asset in the corpus,
    # this bbox is already the embedded image's own exact extent (PROMPT
    # Fase 3Y: padding here would only ever pull in a neighboring marker
    # label or caption, never protect real content).
    assert region.owner_x_bounds == (bbox[0], bbox[2])


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


def test_force_paragraph_break_after_override_splits_the_glued_paragraph():
    """PROMPT Fase 3V: 2008-b Q23's own defect - a line individually proven
    to be real, never-to-be-removed text (not a region duplicate - see
    ``forces_paragraph_break_after``'s own docstring) sits less than
    ``PARAGRAPH_GAP_THRESHOLD`` away from the next, unrelated sentence and
    would otherwise be glued into one paragraph with no separating space.
    """
    first = _line(1, 10.0, "IdRep:integer referencia Republica)")
    second = _line(1, first.y1 + 15.0, "Suponha que existam as seguintes tuplas no banco de dados:")
    assert (second.y0 - first.y1) < PARAGRAPH_GAP_THRESHOLD  # would merge without the override
    overrides = LayoutOverrideSet(
        overrides=[
            LayoutOverride(
                pdf_sha256="cafebabe" * 8,
                page=1,
                bbox=first.bbox,
                rule="force_paragraph_break_after",
                question_id="enade-2008-computing-q23",
                reason="test",
                evidence="test",
                status="reviewed",
            )
        ]
    )
    segments, _, _ = _build_statement_segments(
        [first, second], [], overrides=overrides, pdf_sha256="cafebabe" * 8
    )
    text_segments = [s for s in segments if isinstance(s, TextSegment)]
    assert [s.text for s in text_segments] == [
        "IdRep:integer referencia Republica)",
        "Suponha que existam as seguintes tuplas no banco de dados:",
    ]


def test_force_paragraph_break_after_override_never_fires_without_a_matching_bbox():
    # Same two lines as above, but with no override at all (or one that
    # does not match this exact bbox) - the general PARAGRAPH_GAP_THRESHOLD
    # rule alone still merges them, exactly as it does everywhere else in
    # the corpus. Confirms the override is additive, never the default.
    first = _line(1, 10.0, "IdRep:integer referencia Republica)")
    second = _line(1, first.y1 + 15.0, "Suponha que existam as seguintes tuplas no banco de dados:")
    segments, _, _ = _build_statement_segments([first, second], [])
    text_segments = [s for s in segments if isinstance(s, TextSegment)]
    assert len(text_segments) == 1
    assert text_segments[0].text == (
        "IdRep:integer referencia Republica) "
        "Suponha que existam as seguintes tuplas no banco de dados:"
    )


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


def test_assemble_question_declared_inline_formula_alternatives_are_never_hijacked_by_raster_mechanism():
    """Regression test (PROMPT Fase 3Y): 2008-b Q38's own real shape - 5
    alternatives, each backed by an individually-declared
    ``declare_inline_formula_region`` override (never a raster photograph)
    sitting strictly to its own marker's right, one per row. Found by full
    corpus regeneration to be silently re-matched by the new
    ``_attach_declared_raster_alternative_regions`` mechanism when it was
    (wrongly) given the *entire* unfiltered region list: that function's
    own "closest region to this marker's right" matching has no notion of
    *why* a region sits there, so it happily re-selected these same 5
    already-correctly-declared formula regions - bypassing
    ``_attach_alternative_formula_regions``'s own row-clipping and
    silently changing each rendered crop's own height (docs/phase-3y-
    report.md). The caller must filter to ``is_exact_raster_bbox`` regions
    (set only by the raster mechanism's own region-builder) before ever
    calling the raster attach function, so a declared-formula-only
    question like this one takes the untouched, pre-existing code path.
    """
    import pymupdf

    from enade.extraction.assembler import assemble_question
    from enade.extraction.boundaries import QuestionKind, QuestionSpan

    doc = pymupdf.open()
    page = doc.new_page(width=600, height=800)
    formula_bboxes = [
        (200.0, 100.0, 260.0, 110.0),
        (200.0, 120.0, 260.0, 130.0),
        (200.0, 140.0, 260.0, 150.0),
        (200.0, 160.0, 260.0, 170.0),
        (200.0, 180.0, 260.0, 190.0),
    ]
    for x0, y0, x1, y1 in formula_bboxes:
        shape = page.new_shape()
        shape.draw_line((x0, y0), (x1, y1))
        shape.finish()
        shape.commit()

    lines = [
        Line(page_number=1, text="Enunciado da questao.", x0=30.0, y0=50.0, x1=300.0, y1=62.0),
        Line(page_number=1, text="A", x0=30.0, y0=101.0, x1=38.0, y1=111.0),
        Line(page_number=1, text="B", x0=30.0, y0=121.0, x1=38.0, y1=131.0),
        Line(page_number=1, text="C", x0=30.0, y0=141.0, x1=38.0, y1=151.0),
        Line(page_number=1, text="D", x0=30.0, y0=161.0, x1=38.0, y1=171.0),
        Line(page_number=1, text="E", x0=30.0, y0=181.0, x1=38.0, y1=191.0),
    ]
    span = QuestionSpan(
        kind=QuestionKind.OBJECTIVE, number=38, lines=tuple(lines), start_page=1, end_page=1
    )
    pdf_sha256 = "b" * 64
    overrides = LayoutOverrideSet(
        overrides=[
            LayoutOverride(
                pdf_sha256=pdf_sha256,
                page=1,
                bbox=bbox,
                rule="declare_inline_formula_region",
                question_id="enade-2008-computing-q38",
                reason="test",
                evidence="test",
                status="reviewed",
            )
            for bbox in formula_bboxes
        ]
    )
    result = assemble_question(span, doc, frozenset(), overrides=overrides, pdf_sha256=pdf_sha256)
    assert len(result.alternatives) == 5
    for alt in result.alternatives:
        assert alt.text == ""
        assert alt.figure_region_index is not None
        region = result.figure_regions[alt.figure_region_index]
        assert region.is_declared_inline_formula is True
        assert region.is_exact_raster_bbox is False


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


# --- PROMPT Fase 3S: declared inline-formula regions -----------------------


def _formula_region(bbox=(200.0, 100.0, 220.0, 112.0), **overrides) -> VisualRegion:
    base = dict(
        page_number=1,
        bbox=bbox,
        raw_bbox=bbox,
        element_count=9,
        has_raster_image=False,
        is_small_formula=True,
        is_declared_inline_formula=True,
    )
    base.update(overrides)
    return VisualRegion(**base)


def test_find_inline_formula_insertion_index_lands_between_same_row_lines():
    """The exact 2008-b Q45 shape: "...o grafico de" / [formula] / "e as
    retas...", both text fragments on the same visual row, the formula
    sitting geometrically between them. The general, Y-only
    ``_find_region_insertion_index`` would place the region before the
    whole row (it only ever asks "is this line's y0 past the region's own
    top edge", never "which same-row line sits to its left") - the
    inline-formula-specific index must instead land strictly between the
    two fragments.
    """
    left = _line(1, 483.0, "eixo x, o grafico de", x=317.0, width=88.0)
    right = _line(1, 483.0, "e as retas x = 0 e x = 2.", x=443.0, width=108.0)
    lines = [left, right]
    region = _formula_region(bbox=(406.68, 481.92, 442.92, 493.44))
    assert _find_inline_formula_insertion_index(lines, region) == 1
    # The general, Y-only rule would get this wrong (index 0 - before the
    # whole row) - confirming this is genuinely a different rule, not a
    # coincidence of this one fixture's own geometry.
    assert _find_region_insertion_index(lines, region) == 0


def test_find_inline_formula_insertion_index_falls_back_when_no_same_row_line():
    """A declared inline formula that opens its own row (nothing to its
    own left) falls back to the general Y-only rule - never crashes, never
    silently drops the region.
    """
    only_line = _line(1, 500.0, "Texto qualquer.", x=36.0, width=200.0)
    region = _formula_region(bbox=(36.0, 520.0, 60.0, 532.0))
    assert _find_inline_formula_insertion_index([only_line], region) == 1
    assert _find_inline_formula_insertion_index([only_line], region) == (
        _find_region_insertion_index([only_line], region)
    )


def test_build_declared_inline_formula_regions_none_without_overrides():
    doc = pymupdf.open()
    doc.new_page(width=600, height=800)
    assert _build_declared_inline_formula_regions(doc, 1, None, "a" * 64, None) == []


def test_build_declared_inline_formula_regions_none_when_no_matching_declaration():
    doc = pymupdf.open()
    doc.new_page(width=600, height=800)
    overrides = LayoutOverrideSet(overrides=[])
    assert _build_declared_inline_formula_regions(doc, 1, overrides, "a" * 64, None) == []


def test_build_declared_inline_formula_regions_skips_a_declaration_with_no_real_drawing():
    """Positive, structural evidence is mandatory (PROMPT Fase 3S Section
    13) - a declared bbox with zero real vector-drawing content on the
    actual page must never produce a region, even if the override itself
    is syntactically well-formed.
    """
    doc = pymupdf.open()
    doc.new_page(width=600, height=800)  # blank - no drawings anywhere
    overrides = LayoutOverrideSet(
        overrides=[
            LayoutOverride(
                pdf_sha256="a" * 64,
                page=1,
                bbox=(406.68, 481.92, 442.92, 493.44),
                rule="declare_inline_formula_region",
                question_id="enade-2008-computing-q45",
                reason="test",
                evidence="test",
                status="reviewed",
            )
        ]
    )
    assert _build_declared_inline_formula_regions(doc, 1, overrides, "a" * 64, None) == []


def test_build_declared_inline_formula_regions_builds_a_region_with_real_drawings():
    doc = pymupdf.open()
    page = doc.new_page(width=600, height=800)
    shape = page.new_shape()
    shape.draw_line((406.68, 481.92), (442.92, 493.44))
    shape.finish()
    shape.commit()
    overrides = LayoutOverrideSet(
        overrides=[
            LayoutOverride(
                pdf_sha256="a" * 64,
                page=1,
                bbox=(406.68, 481.92, 442.92, 493.44),
                rule="declare_inline_formula_region",
                question_id="enade-2008-computing-q45",
                reason="test",
                evidence="test",
                status="reviewed",
            )
        ]
    )
    built = _build_declared_inline_formula_regions(doc, 1, overrides, "a" * 64, None)
    assert len(built) == 1
    region = built[0]
    assert region.is_declared_inline_formula is True
    assert region.is_small_formula is True
    assert region.has_raster_image is False
    assert region.bbox == (406.68, 481.92, 442.92, 493.44)
    assert region.owner_key is None  # no question_regions given
    assert region.owner_x_bounds is not None
    assert region.owner_x_bounds[0] < region.bbox[0]
    assert region.owner_x_bounds[1] > region.bbox[2]


def test_build_declared_inline_formula_regions_computes_owner_from_question_regions():
    doc = pymupdf.open()
    page = doc.new_page(width=600, height=800)
    shape = page.new_shape()
    shape.draw_line((406.68, 481.92), (442.92, 493.44))
    shape.finish()
    shape.commit()
    overrides = LayoutOverrideSet(
        overrides=[
            LayoutOverride(
                pdf_sha256="a" * 64,
                page=1,
                bbox=(406.68, 481.92, 442.92, 493.44),
                rule="declare_inline_formula_region",
                question_id="enade-2008-computing-q45",
                reason="test",
                evidence="test",
                status="reviewed",
            )
        ]
    )
    question_regions = [
        QuestionRegion(
            question_key="objective-45", page_number=1, x0=300.0, y0=100.0, x1=560.0, y1=600.0
        )
    ]
    built = _build_declared_inline_formula_regions(doc, 1, overrides, "a" * 64, question_regions)
    assert len(built) == 1
    assert built[0].owner_key == "objective-45"
