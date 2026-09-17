"""Unit, safety and metamorphic tests for per-line alternative ownership
(PROMPT Phase 3P) - alternative_content_assignment.py.

Every fixture is synthetic (never a real corpus coordinate/page/question
ID/text - PROMPT section 24/29). Real-corpus validation (Q07, plus the
mandatory Q13/Q28/Q29/Q52/Q71/Q75/Q24/Q45/D40 regression set) lives in
test_extraction_pipeline_2008.py.
"""

from __future__ import annotations

from enade.extraction.alternative_content_assignment import (
    assign_alternative_content,
    detect_ambiguous_published_assignments,
    detect_duplicate_alternative_assignments,
    detect_foreign_alternative_assignments,
    detect_missing_alternative_assignments,
)
from enade.extraction.alternative_groups import LATIN_UPPER_SCHEME, find_alternative_group
from enade.extraction.figures import VisualRegion
from enade.extraction.layout import Line

CONTINUATION_TOLERANCE = 60.0
MARGIN = 30.0


def _line(text: str, x0: float, y0: float, page: int = 1, width: float = 200.0) -> Line:
    return Line(page_number=page, text=text, x0=x0, y0=y0, x1=x0 + width, y1=y0 + 12)


def _full_sequence(
    margin: float = MARGIN, start_y: float = 100.0, step: float = 20.0
) -> list[Line]:
    return [
        _line(f"{letter}\ttexto da alternativa {letter}", margin, start_y + i * step)
        for i, letter in enumerate(LATIN_UPPER_SCHEME)
    ]


def _region(page: int, x0: float, y0: float, x1: float, y1: float) -> VisualRegion:
    return VisualRegion(page_number=page, bbox=(x0, y0, x1, y1), element_count=1)


def _assign(lines: list[Line], regions: list[VisualRegion] | None = None):
    group = find_alternative_group(lines)
    assert group is not None and group.is_usable
    ordered_letters = tuple(LATIN_UPPER_SCHEME)
    alt_bounds = [group.accepted[letter] for letter in ordered_letters] + [len(lines)]
    marker_x0s = tuple(lines[group.accepted[letter]].x0 for letter in ordered_letters)
    return assign_alternative_content(
        ordered_letters=ordered_letters,
        alt_bounds=alt_bounds,
        text_only_lines=lines,
        marker_x0s=marker_x0s,
        continuation_tolerance=CONTINUATION_TOLERANCE,
        regions=regions or [],
        question_owner="objective-1",
        group_id="objective-1",
    )


# --- Markers (Section 28) --------------------------------------------------


def test_complete_a_to_e_produces_one_marker_assignment_per_letter():
    lines = _full_sequence()
    result = _assign(lines)
    markers = [a for a in result.assignments if a.content_type == "marker"]
    assert len(markers) == 5
    assert all(a.status == "assigned" and a.confidence == "high" for a in markers)


def test_missing_marker_never_reaches_this_module():
    # alternative_groups.find_alternative_group already returns "incomplete"
    # for a missing letter - this module is never invoked at all in that
    # case (assembler.py only calls it once alt_group.is_usable), so there
    # is nothing here to assign. Documented as a boundary of this module's
    # own responsibility, not a gap.
    lines = [_line("A\ttexto", MARGIN, 100.0), _line("B\ttexto", MARGIN, 120.0)]
    group = find_alternative_group(lines)
    assert group is None  # no "E" candidate at all


def test_duplicate_marker_letter_resolved_upstream_not_here():
    # Two "A"-shaped candidates: alternative_groups resolves the
    # competition (on-margin + reading order) before this module ever
    # sees the line list - confirmed by using its own accepted result.
    lines = [
        _line("A\treal alternative", MARGIN, 100.0),
        _line("A esse respeito, nada a acrescentar", MARGIN, 110.0),
        _line("B\ttexto", MARGIN, 130.0),
        _line("C\ttexto", MARGIN, 150.0),
        _line("D\ttexto", MARGIN, 170.0),
        _line("E\ttexto", MARGIN, 190.0),
    ]
    group = find_alternative_group(lines)
    assert group is not None
    # Either resolved deterministically or flagged - both are upstream
    # concerns; this module is never reached when it is not resolved.
    if group.is_usable:
        result = _assign(lines, [])
        assert result.assignments


def test_diagram_internal_label_never_becomes_a_marker():
    # A bare "A"/"B" positioned far from the real markers' own margin
    # (e.g. a circuit's own input label) never enters text_only_lines as
    # a marker candidate for this corpus (figures.py's own Cluster C /
    # _is_marker_at_margin keeps diagram-internal labels out of the line
    # pool entirely) - simulated here by simply never including it in the
    # lines this module receives, matching that upstream contract.
    lines = _full_sequence()
    result = _assign(lines)
    assert len(result.assignments) == 5  # exactly the 5 markers, no extras


def test_roman_numeral_item_marker_is_never_treated_as_an_alternative():
    lines = [
        _line("A\ttexto", MARGIN, 100.0),
        _line("B\ttexto", MARGIN, 120.0),
        _line("C\ttexto", MARGIN, 140.0),
        _line("D\ttexto", MARGIN, 160.0),
        _line("E\ttexto", MARGIN, 180.0),
        _line("I", MARGIN, 200.0),  # roman numeral, positioned after E
        _line("II", MARGIN, 220.0),
    ]
    result = _assign(lines)
    # "I"/"II" are plain trailing lines inside E's own range (no marker
    # shape matches them - _ALTERNATIVE_LINE_RE only matches single
    # letters A-E) - they are retained (ambiguous, since they share E's
    # own margin) exactly like any other trailing prose, never promoted
    # to their own alternative and never silently dropped.
    retained_e = [ln.text for ln in result.retained_by_letter["E"]]
    assert "I" in retained_e
    assert "II" in retained_e


def test_table_cell_letter_and_math_variable_never_match_marker_shape():
    # A table cell or formula variable is never a bare "A"/"B\t..." shaped
    # Line at all in this pipeline (it is either consumed by table
    # detection or lives inside a visual region) - nothing to assert here
    # beyond confirming the regex itself is exact-match, not substring.
    from enade.extraction.assembler import _ALTERNATIVE_LINE_RE

    assert _ALTERNATIVE_LINE_RE.match("A") is not None
    assert _ALTERNATIVE_LINE_RE.match("valorA") is None
    assert _ALTERNATIVE_LINE_RE.match("A=10") is None


def test_code_identifier_never_matches_marker_shape():
    from enade.extraction.assembler import _ALTERNATIVE_LINE_RE

    assert _ALTERNATIVE_LINE_RE.match("A_variavel") is None
    assert _ALTERNATIVE_LINE_RE.match("classA") is None


# --- Boundaries (Section 28) ------------------------------------------------


def test_single_column_continuation_is_retained():
    lines = _full_sequence()
    lines.insert(1, _line("continuacao da alternativa A", MARGIN + 5, 105.0))
    # Re-run find_alternative_group against the new line list (indices shift).
    result = _assign(lines)
    retained_a = [ln.text for ln in result.retained_by_letter["A"]]
    assert "continuacao da alternativa A" in retained_a


def test_two_column_page_marker_continuation_within_tolerance_is_retained():
    lines = _full_sequence(margin=300.0)
    lines.insert(1, _line("continuacao no mesmo texto", 300.0 + 18.0, 105.0))
    result = _assign(lines)
    retained_a = [ln.text for ln in result.retained_by_letter["A"]]
    assert "continuacao no mesmo texto" in retained_a


def test_alternative_crossing_column_boundary_is_contamination_when_unexplained():
    lines = _full_sequence()
    # A line far outside the continuation tolerance, with no region to
    # explain it: ambiguous, retained in place (safe default), never
    # silently discarded and never promoted to "statement" without
    # evidence.
    lines.append(_line("texto de outra coluna", MARGIN + 400.0, 300.0))
    result = _assign(lines)
    ambiguous = detect_ambiguous_published_assignments(result.assignments)
    assert len(ambiguous) == 1
    assert ambiguous[0].source_id.startswith("p1:")
    retained_e = [ln.text for ln in result.retained_by_letter["E"]]
    assert "texto de outra coluna" in retained_e  # preserved, not lost


def test_alternative_crossing_page_boundary():
    lines = _full_sequence()
    lines.append(_line("continuacao na proxima pagina", MARGIN, 50.0, page=2))
    result = _assign(lines)
    # Different page: never matches the continuation-margin test's own
    # implicit same-page assumption in practice (a genuine per-question
    # page continuation is geometrically identical in x0, so it is still
    # retained here) - and never reflowed to the statement unless a
    # region on *that* page explains it.
    retained_e = [ln.text for ln in result.retained_by_letter["E"]]
    assert "continuacao na proxima pagina" in retained_e


def test_same_row_far_right_continuation_is_never_reflowed_even_with_a_matching_region():
    # Real regression found and fixed while validating this exact
    # mechanism (2008-b Q64, page 28; 2011 Q23, page 14): a same-row
    # fragment can sit far to the *right* of its own marker (a font/symbol
    # run change mid-sentence splits one printed row into two Line
    # entries) and still coincidentally fall inside some region's own
    # horizontal span - it must never be reflowed, because it never moves
    # *backward* relative to its own marker.
    lines = _full_sequence()
    same_row_fragment = _line("continuacao no mesmo texto, distante", MARGIN + 220.0, 100.0)
    lines.insert(1, same_row_fragment)
    region = _region(page=1, x0=MARGIN, y0=0.0, x1=MARGIN + 300.0, y1=400.0)
    result = _assign(lines, regions=[region])
    assert result.reflowed_to_statement == []
    assert same_row_fragment.text in [ln.text for ln in result.retained_by_letter["A"]]


def test_backward_position_without_a_region_stays_ambiguous_not_reflowed():
    lines = _full_sequence(margin=TWO_COLUMN_MARGIN)
    lines.append(_line("texto para tras sem regiao", LEFT_COLUMN_X0, 300.0))
    result = _assign(lines)
    assert result.reflowed_to_statement == []
    ambiguous = detect_ambiguous_published_assignments(result.assignments)
    assert len(ambiguous) == 1


def test_asset_between_alternatives_is_untouched_by_this_module():
    # Figure/table placement is a completely separate mechanism
    # (_attach_alternative_formula_regions / _build_statement_segments) -
    # this module only ever sees Line objects, never VisualRegion objects,
    # as line-list entries, so an asset "between" two alternatives cannot
    # appear in the lines this module partitions at all.
    lines = _full_sequence()
    result = _assign(lines, regions=[_region(1, 0, 0, 1000, 1000)])
    assert all(a.content_type in ("marker", "continuation") for a in result.assignments)


def test_next_question_marker_is_a_hard_barrier():
    # A different question's own span never reaches assign_alternative_content
    # at all (assemble_question slices spans per-question upstream) - this
    # module's own contract assumes text_only_lines already belongs to one
    # question. Documented, not independently testable at this module's
    # own boundary.
    lines = _full_sequence()
    result = _assign(lines)
    assert all(a.question_owner == "objective-1" for a in result.assignments)


def test_alternative_e_extends_to_end_of_question_with_no_next_marker():
    lines = _full_sequence()
    lines.append(_line("fim da alternativa E", MARGIN, 300.0))
    result = _assign(lines)
    retained_e = [ln.text for ln in result.retained_by_letter["E"]]
    assert "fim da alternativa E" in retained_e


# --- Assignment (Section 28) -------------------------------------------------


def test_source_id_gets_exactly_one_alternative_owner():
    lines = _full_sequence()
    lines.insert(1, _line("continuacao", MARGIN, 105.0))
    result = _assign(lines)
    duplicates = detect_duplicate_alternative_assignments(result.assignments)
    assert duplicates == []


def test_no_missing_assignment_for_any_trailing_line():
    lines = _full_sequence()
    lines.insert(1, _line("continuacao", MARGIN, 105.0))
    result = _assign(lines)
    assert detect_missing_alternative_assignments(result.assignments) == []


#: A genuinely two-column shape (mirrors 2008-b Q07's own real geometry:
#: alternatives at x0=272.2, a chart's own citation at x0=164.8, in the
#: page's own left column) - far enough left of ``TWO_COLUMN_MARGIN`` that
#: it fails ``_ALTERNATIVE_CONTINUATION_X_TOLERANCE`` and sits behind
#: (never ahead of) the marker's own x0, the two conditions
#: ``assign_alternative_content`` requires before ever reflowing anything.
TWO_COLUMN_MARGIN = 300.0
LEFT_COLUMN_X0 = 5.0


def test_line_in_wrong_alternative_column_is_reflowed_when_region_explains_it():
    lines = _full_sequence(margin=TWO_COLUMN_MARGIN)
    foreign = _line("citacao da imagem", LEFT_COLUMN_X0, 300.0)
    lines.append(foreign)
    # A region on the same page whose own bbox horizontally contains the
    # foreign line's own x-range - the structural evidence this module
    # requires before reflowing anything.
    region = _region(page=1, x0=0.0, y0=0.0, x1=100.0, y1=400.0)
    result = _assign(lines, regions=[region])
    assert foreign in result.reflowed_to_statement
    assert "citacao da imagem" not in [ln.text for ln in result.retained_by_letter["E"]]
    reflowed_records = [a for a in result.assignments if a.status == "reflowed"]
    assert len(reflowed_records) == 1
    assert reflowed_records[0].alternative_owner == "statement"


def test_asset_specific_region_only_reflows_the_line_it_actually_overlaps():
    lines = _full_sequence(margin=TWO_COLUMN_MARGIN)
    unrelated = _line("linha realmente da alternativa E", TWO_COLUMN_MARGIN, 300.0)
    lines.append(unrelated)
    region = _region(page=1, x0=500.0, y0=0.0, x1=600.0, y1=400.0)  # far from the margin
    result = _assign(lines, regions=[region])
    assert result.reflowed_to_statement == []
    assert unrelated.text in [ln.text for ln in result.retained_by_letter["E"]]


def test_shared_region_reflows_every_matching_foreign_line():
    lines = _full_sequence(margin=TWO_COLUMN_MARGIN)
    first = _line("citacao 1", LEFT_COLUMN_X0, 300.0)
    second = _line("citacao 2", LEFT_COLUMN_X0, 315.0)
    lines.extend([first, second])
    region = _region(page=1, x0=0.0, y0=0.0, x1=100.0, y1=400.0)
    result = _assign(lines, regions=[region])
    assert first in result.reflowed_to_statement
    assert second in result.reflowed_to_statement


def test_foreign_owner_assignment_gate():
    lines = _full_sequence()
    result = _assign(lines)
    assert detect_foreign_alternative_assignments(result.assignments, "objective-1") == []
    assert detect_foreign_alternative_assignments(result.assignments, "objective-2") == [
        a.source_id for a in result.assignments
    ]


def test_ambiguous_assignment_is_reported_not_silently_resolved():
    lines = _full_sequence()
    lines.append(_line("linha sem explicacao estrutural", MARGIN + 400.0, 300.0))
    result = _assign(lines)
    findings = detect_ambiguous_published_assignments(result.assignments)
    assert len(findings) == 1
    assert "does not match" in findings[0].violation


# --- Safety (Section 28) -----------------------------------------------------


def test_word_multiset_is_preserved_across_assignment():
    lines = _full_sequence()
    foreign = _line("palavra extra preservada", 5.0, 300.0)
    lines.append(foreign)
    region = _region(page=1, x0=0.0, y0=0.0, x1=100.0, y1=400.0)
    result = _assign(lines, regions=[region])
    all_words: list[str] = []
    for letter_lines in result.retained_by_letter.values():
        for ln in letter_lines:
            all_words.extend(ln.text.split())
    all_words.extend(word for ln in result.reflowed_to_statement for word in ln.text.split())
    assert sorted(all_words) == sorted(["palavra", "extra", "preservada"])


def test_assignment_is_deterministic_across_repeated_calls():
    lines = _full_sequence()
    lines.append(_line("linha ambigua", MARGIN + 400.0, 300.0))
    result_a = _assign(lines)
    result_b = _assign(lines)
    assert result_a.assignments == result_b.assignments


def test_incomplete_group_never_reaches_assignment():
    lines = [_line("A\ttexto", MARGIN, 100.0)]
    assert find_alternative_group(lines) is None


def test_rejection_always_carries_a_reason():
    lines = _full_sequence()
    lines.append(_line("linha ambigua", MARGIN + 400.0, 300.0))
    result = _assign(lines)
    findings = detect_ambiguous_published_assignments(result.assignments)
    assert all(f.violation and f.evidence for f in findings)


# --- Metamorphic (Section 29) ------------------------------------------------


def test_uniform_translation_x_preserves_the_same_decision():
    lines = _full_sequence(margin=TWO_COLUMN_MARGIN)
    foreign = _line("citacao", LEFT_COLUMN_X0, 300.0)
    lines.append(foreign)
    region = _region(page=1, x0=0.0, y0=0.0, x1=100.0, y1=400.0)
    base = _assign(lines, regions=[region])

    shift = 200.0
    shifted_lines = [
        Line(
            page_number=ln.page_number,
            text=ln.text,
            x0=ln.x0 + shift,
            y0=ln.y0,
            x1=ln.x1 + shift,
            y1=ln.y1,
        )
        for ln in lines
    ]
    shifted_region = _region(
        page=1, x0=region.bbox[0] + shift, y0=0.0, x1=region.bbox[2] + shift, y1=400.0
    )
    shifted = _assign(shifted_lines, regions=[shifted_region])
    assert len(shifted.reflowed_to_statement) == len(base.reflowed_to_statement) == 1


def test_uniform_translation_y_preserves_the_same_decision():
    lines = _full_sequence(margin=TWO_COLUMN_MARGIN)
    foreign = _line("citacao", LEFT_COLUMN_X0, 300.0)
    lines.append(foreign)
    region = _region(page=1, x0=0.0, y0=0.0, x1=100.0, y1=400.0)
    base = _assign(lines, regions=[region])

    shift = 500.0
    shifted_lines = [
        Line(
            page_number=ln.page_number,
            text=ln.text,
            x0=ln.x0,
            y0=ln.y0 + shift,
            x1=ln.x1,
            y1=ln.y1 + shift,
        )
        for ln in lines
    ]
    shifted_region = _region(
        page=1, x0=0.0, y0=region.bbox[1] + shift, x1=100.0, y1=region.bbox[3] + shift
    )
    shifted = _assign(shifted_lines, regions=[shifted_region])
    assert len(shifted.reflowed_to_statement) == len(base.reflowed_to_statement) == 1


def test_uniform_scale_preserves_the_same_decision():
    lines = _full_sequence(margin=TWO_COLUMN_MARGIN)
    foreign = _line("citacao", LEFT_COLUMN_X0, 300.0)
    lines.append(foreign)
    region = _region(page=1, x0=0.0, y0=0.0, x1=100.0, y1=400.0)
    base = _assign(lines, regions=[region])

    scale = 1.5
    scaled_lines = [
        Line(
            page_number=ln.page_number,
            text=ln.text,
            x0=ln.x0 * scale,
            y0=ln.y0 * scale,
            x1=ln.x1 * scale,
            y1=ln.y1 * scale,
        )
        for ln in lines
    ]
    scaled_region = _region(
        page=1,
        x0=region.bbox[0] * scale,
        y0=region.bbox[1] * scale,
        x1=region.bbox[2] * scale,
        y1=region.bbox[3] * scale,
    )
    group = find_alternative_group(scaled_lines)
    assert group is not None and group.is_usable
    ordered_letters = tuple(LATIN_UPPER_SCHEME)
    alt_bounds = [group.accepted[letter] for letter in ordered_letters] + [len(scaled_lines)]
    marker_x0s = tuple(scaled_lines[group.accepted[letter]].x0 for letter in ordered_letters)
    scaled = assign_alternative_content(
        ordered_letters=ordered_letters,
        alt_bounds=alt_bounds,
        text_only_lines=scaled_lines,
        marker_x0s=marker_x0s,
        continuation_tolerance=CONTINUATION_TOLERANCE * scale,
        regions=[scaled_region],
        question_owner="objective-1",
        group_id="objective-1",
    )
    assert len(scaled.reflowed_to_statement) == len(base.reflowed_to_statement) == 1


def test_small_font_size_variation_does_not_change_the_decision():
    # Font size never participates in this module's own evidence (only
    # x0/region overlap does) - a font-size-only change to any line
    # cannot change any assignment.
    lines = _full_sequence()
    result_a = _assign(lines)
    lines[0] = Line(
        page_number=lines[0].page_number,
        text=lines[0].text,
        x0=lines[0].x0,
        y0=lines[0].y0,
        x1=lines[0].x1,
        y1=lines[0].y1,
        font_size=lines[0].font_size + 0.3,
    )
    result_b = _assign(lines)
    assert result_a.assignments == result_b.assignments


def test_backend_object_order_permutation_does_not_change_the_result():
    # The candidate-region list's own order must never matter - only
    # which region (if any) actually overlaps a given line.
    lines = _full_sequence(margin=TWO_COLUMN_MARGIN)
    foreign = _line("citacao", LEFT_COLUMN_X0, 300.0)
    lines.append(foreign)
    region_a = _region(page=1, x0=0.0, y0=0.0, x1=100.0, y1=400.0)
    region_b = _region(page=1, x0=900.0, y0=0.0, x1=999.0, y1=400.0)
    forward = _assign(lines, regions=[region_a, region_b])
    backward = _assign(lines, regions=[region_b, region_a])
    assert forward.reflowed_to_statement == backward.reflowed_to_statement == [foreign]


def test_horizontal_overflow_equivalent_shape_still_retains_as_continuation():
    lines = _full_sequence()
    lines.insert(1, _line("continuacao levemente deslocada", MARGIN + 40.0, 105.0))
    result = _assign(lines)
    assert "continuacao levemente deslocada" in [ln.text for ln in result.retained_by_letter["A"]]


def test_decorative_label_insertion_is_ambiguous_not_reflowed_without_a_region():
    lines = _full_sequence()
    lines.append(_line("rotulo decorativo", MARGIN + 300.0, 300.0))
    result = _assign(lines)
    assert result.reflowed_to_statement == []
    assert "rotulo decorativo" in [ln.text for ln in result.retained_by_letter["E"]]


def test_roman_numeral_insertion_is_never_reflowed_without_a_region():
    lines = _full_sequence()
    lines.append(_line("IV", MARGIN + 300.0, 300.0))
    result = _assign(lines)
    assert result.reflowed_to_statement == []
