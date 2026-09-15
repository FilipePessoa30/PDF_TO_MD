"""Unit and metamorphic tests for geometric line-fragment reconstruction
(PROMPT Phase 3H, "Cluster D") - fragment_reconstruction.py.

Every fixture is synthetic (never a real corpus coordinate/page/question
ID/text - PROMPT section 18/24: "os testes nao podem depender de
coordenada fixa... question ID... ano... pagina fixa"). Real-corpus
validation (Q07/Q12/D40) lives in test_extraction_pipeline_2008.py.
"""

from __future__ import annotations

import pytest

from enade.extraction.fragment_reconstruction import (
    FONT_SIZE_TOLERANCE_PT,
    MAX_FRAGMENT_GAP_RATIO,
    LineFragmentRelation,
    RawLineFragment,
    compute_line_fragment_relation,
    group_line_fragments,
    merged_bbox_of,
)


def _frag(
    x0: float,
    x1: float,
    text: str,
    y0: float = 100.0,
    y1: float = 110.0,
    font_size: float = 10.0,
    mono: bool = False,
    page: int = 1,
) -> RawLineFragment:
    return RawLineFragment(
        page_number=page,
        x0=x0,
        y0=y0,
        x1=x1,
        y1=y1,
        raw_text=text,
        fonts=("TestFont",),
        font_size=font_size,
        is_monospace=mono,
    )


# --- compute_line_fragment_relation: intraline reconstruction ---------------


def test_join_with_space_when_trailing_space_and_small_gap():
    left = _frag(0.0, 40.0, "total ")  # documentary trailing space
    right = _frag(48.4, 90.0, "correspondente")  # gap = 8.4pt, ~0.84x font
    relation = compute_line_fragment_relation(left, right)
    assert relation.decision == "merge_with_space"
    assert relation.left_had_trailing_space is True
    assert relation.same_baseline is True
    assert relation.gap_within_ceiling is True


def test_preserve_separate_when_no_trailing_space():
    """A real table cell: no textual continuation, so no trailing space -
    even with an otherwise-plausible small gap, never merged.
    """
    left = _frag(0.0, 40.0, "127.0.0.0")  # no trailing space
    right = _frag(48.0, 90.0, "255.0.0.0")
    relation = compute_line_fragment_relation(left, right)
    assert relation.decision == "preserve_separate"
    assert relation.left_had_trailing_space is False


def test_preserve_separate_when_gap_too_large_even_with_trailing_space():
    """PROMPT: the gap ceiling is a safety net independent of the
    trailing-space signal - a genuine table row's own cell gap (2.5-4.1x
    font size in real corpus evidence) must never merge even if some
    coincidental trailing space existed.
    """
    left = _frag(0.0, 40.0, "total ", font_size=8.0)
    right = _frag(72.0, 110.0, "correspondente", font_size=8.0)  # gap=32pt = 4x font
    relation = compute_line_fragment_relation(left, right)
    assert relation.decision == "preserve_separate"
    assert relation.gap_within_ceiling is False


def test_ambiguous_case_baseline_matches_but_no_trailing_space_stays_separate():
    """Baseline matches and gap is plausible, but no documentary trailing
    space - PROMPT: never merge on geometry alone, no guessing.
    """
    left = _frag(0.0, 40.0, "total")  # NOT ending in a space
    right = _frag(48.4, 90.0, "correspondente")
    relation = compute_line_fragment_relation(left, right)
    assert relation.decision == "preserve_separate"
    assert relation.gap_within_ceiling is True
    assert relation.left_had_trailing_space is False


def test_different_baseline_never_merges_even_with_trailing_space_and_small_gap():
    """A genuine next printed line (different y0) must never be treated as
    a same-line fragment, regardless of how plausible the other signals
    look - this is what distinguishes fragmentation from an ordinary
    paragraph line-wrap.
    """
    left = _frag(0.0, 40.0, "total ", y0=100.0, y1=110.0)
    right = _frag(0.0, 90.0, "correspondente", y0=111.5, y1=121.5)  # next line down
    relation = compute_line_fragment_relation(left, right)
    assert relation.same_baseline is False
    assert relation.decision == "preserve_separate"


def test_monospace_fragment_never_merges():
    """PROMPT section 16: code/pseudocode keeps its own literal line
    breaks - never rejoined even if baseline/gap/trailing-space all align.
    """
    left = _frag(0.0, 40.0, "int x ", mono=True)
    right = _frag(48.0, 90.0, "= 1;", mono=True)
    relation = compute_line_fragment_relation(left, right)
    assert relation.both_non_monospace is False
    assert relation.decision == "preserve_separate"


def test_incompatible_font_size_never_merges():
    """A genuine typographic change (heading abutting body text) that
    happens to share a baseline must not be joined.
    """
    left = _frag(0.0, 40.0, "Title ", font_size=14.0)
    right = _frag(48.0, 90.0, "tail", font_size=9.0)
    relation = compute_line_fragment_relation(left, right)
    assert relation.font_size_compatible is False
    assert relation.decision == "preserve_separate"


def test_negative_gap_overlap_never_merges():
    """Overlapping bboxes are not a word-gap at all (e.g. a diacritic or
    annotation) - never treated as evidence of continuation.
    """
    left = _frag(0.0, 40.0, "total ")
    right = _frag(35.0, 90.0, "correspondente")  # x0 < left.x1: overlap
    relation = compute_line_fragment_relation(left, right)
    assert relation.gap_within_ceiling is False
    assert relation.decision == "preserve_separate"


def test_boundary_gap_at_exactly_the_ceiling_still_merges():
    font_size = 10.0
    left = _frag(0.0, 40.0, "total ", font_size=font_size)
    gap = MAX_FRAGMENT_GAP_RATIO * font_size
    right = _frag(40.0 + gap, 90.0, "correspondente", font_size=font_size)
    relation = compute_line_fragment_relation(left, right)
    assert relation.gap_within_ceiling is True
    assert relation.decision == "merge_with_space"


def test_gap_just_past_the_ceiling_does_not_merge():
    font_size = 10.0
    left = _frag(0.0, 40.0, "total ", font_size=font_size)
    gap = MAX_FRAGMENT_GAP_RATIO * font_size + 0.5
    right = _frag(40.0 + gap, 90.0, "correspondente", font_size=font_size)
    relation = compute_line_fragment_relation(left, right)
    assert relation.gap_within_ceiling is False
    assert relation.decision == "preserve_separate"


# --- group_line_fragments: chains, multiple lines, boundaries --------------


def test_chain_of_several_fragments_forms_one_group():
    """The real Q07 shape: 8 fragments on the same baseline, each (but the
    last) carrying a trailing space.
    """
    words = ["total ", "correspondente ", "aos ", "20% ", "de ", "maior ", "renda ", "foi,"]
    x = 0.0
    fragments = []
    for word in words:
        width = len(word) * 6.0
        fragments.append(_frag(x, x + width, word))
        x += width + 8.4
    groups = group_line_fragments(fragments)
    assert len(groups) == 1
    assert len(groups[0]) == len(words)


def test_two_independent_lines_on_the_page_never_cross_merge():
    line1 = [
        _frag(0.0, 40.0, "primeira ", y0=100, y1=110),
        _frag(48.4, 90.0, "linha.", y0=100, y1=110),
    ]
    line2 = [
        _frag(0.0, 40.0, "segunda ", y0=120, y1=130),
        _frag(48.4, 90.0, "linha.", y0=120, y1=130),
    ]
    groups = group_line_fragments(line1 + line2)
    assert len(groups) == 2
    assert {len(g) for g in groups} == {2}


def test_two_column_first_line_at_identical_baseline_never_cross_merges():
    """Real regression found against the protected 2021 corpus (page 19):
    two independent, side-by-side objective questions whose own first line
    each starts at the identical y0 right under their own 'QUESTAO N'
    marker - a genuine word-gap-sized gutter (~9.3pt at 12pt font) plus a
    trailing space on the left question's own wrapping first line
    satisfies every other merge condition by coincidence. Must never merge
    once a column boundary is supplied.
    """
    left = _frag(29.764, 280.120, "Quando um computador e multiprogramado, ele ", font_size=12.0)
    right = _frag(289.465, 539.773, "A biblioteca de colecoes da linguagem Java ", font_size=12.0)
    column_boundary = 289.465 - 5.0  # mirrors layout.py's own right-column margin convention
    groups = group_line_fragments([left, right], column_boundary=column_boundary)
    assert len(groups) == 2
    assert all(len(g) == 1 for g in groups)
    # Without the column-boundary guard, this exact shape would merge -
    # confirming the fix, not just a vacuous assertion.
    unguarded = group_line_fragments([left, right])
    assert len(unguarded) == 1


def test_column_boundary_bucketed_past_the_real_margin_still_blocks_the_merge():
    """Real bug found and fixed this phase: detect_column_margins buckets
    its own returned margin to COLUMN_BUCKET_SIZE (5pt), which can round
    to a value numerically *past* the right column's own real x0 (2021
    p.19: real x0=289.465, bucketed margin=290.0) - a naive
    ``candidate.x0 >= column_boundary`` check would then wrongly let the
    merge through. layout.py's own ``_column_boundary_for_fragment_merge``
    applies the same COLUMN_RIGHT_MARGIN_TOLERANCE extract_page_lines
    itself already uses; this test pins the grouping function's own side
    of that contract using the raw (un-adjusted) bucketed value one would
    get from calling detect_column_margins directly, adjusted by the same
    published tolerance constant.
    """
    from enade.extraction.layout import COLUMN_RIGHT_MARGIN_TOLERANCE

    left = _frag(29.764, 280.120, "Quando um computador e multiprogramado, ele ", font_size=12.0)
    right = _frag(289.465, 539.773, "A biblioteca de colecoes da linguagem Java ", font_size=12.0)
    bucketed_margin = 290.0
    adjusted_boundary = bucketed_margin - COLUMN_RIGHT_MARGIN_TOLERANCE
    groups = group_line_fragments([left, right], column_boundary=adjusted_boundary)
    assert len(groups) == 2


def test_table_row_cells_never_merge_into_one_group():
    cells = [
        _frag(0.0, 34.0, "127.0.0.0", font_size=8.0),
        _frag(67.0, 101.0, "255.0.0.0", font_size=8.0),
        _frag(121.0, 155.0, "127.0.0.1", font_size=8.0),
    ]
    groups = group_line_fragments(cells)
    assert len(groups) == 3
    assert all(len(g) == 1 for g in groups)


def test_a_break_in_the_trailing_space_chain_splits_the_group():
    """Real evidence: the fragment *before* a genuine visual line's own end
    never carries a trailing space - a chain must stop there even if a
    further, unrelated fragment happens to sit further right on the same
    baseline.
    """
    a = _frag(0.0, 40.0, "primeira ", y0=100, y1=110)
    b = _frag(48.4, 90.0, "parte.", y0=100, y1=110)  # no trailing space: chain ends here
    c = _frag(98.4, 140.0, "outra", y0=100, y1=110)  # unrelated, same baseline
    groups = group_line_fragments([a, b, c])
    assert len(groups) == 2
    assert [f.raw_text for f in groups[0]] == ["primeira ", "parte."]
    assert [f.raw_text for f in groups[1]] == ["outra"]


def test_single_fragment_page_is_unaffected():
    groups = group_line_fragments([_frag(0.0, 40.0, "sozinha.")])
    assert len(groups) == 1
    assert len(groups[0]) == 1


def test_empty_fragment_list_returns_empty():
    assert group_line_fragments([]) == []


def test_merged_bbox_of_spans_every_fragment():
    group = [
        _frag(10.0, 40.0, "a ", y0=100.0, y1=110.0),
        _frag(45.0, 90.0, "b", y0=100.0, y1=110.0),
    ]
    assert merged_bbox_of(group) == (10.0, 100.0, 90.0, 110.0)


# --- Metamorphic tests (PROMPT section 24) ----------------------------------
#
# The relation/grouping must be a function of relative geometry alone -
# never a fixed coordinate, page, question ID, or real question text.


def test_translation_invariance_of_a_merge_decision():
    dx, dy = 733.0, -418.0
    left_a = _frag(0.0, 40.0, "total ")
    right_a = _frag(48.4, 90.0, "correspondente")
    left_b = _frag(0.0 + dx, 40.0 + dx, "total ", y0=100.0 + dy, y1=110.0 + dy)
    right_b = _frag(48.4 + dx, 90.0 + dx, "correspondente", y0=100.0 + dy, y1=110.0 + dy)
    relation_a = compute_line_fragment_relation(left_a, right_a)
    relation_b = compute_line_fragment_relation(left_b, right_b)
    assert relation_a.decision == relation_b.decision == "merge_with_space"
    assert relation_a.gap_ratio == pytest.approx(relation_b.gap_ratio)


def test_scale_invariance_of_the_gap_ratio():
    """Scaling both the gap and the font size by the same factor (as a
    higher-DPI render of the same document would) must not change the
    ratio-based ceiling decision.
    """
    for scale in (0.5, 1.0, 2.0, 3.0):
        font_size = 10.0 * scale
        left = _frag(0.0, 40.0 * scale, "total ", font_size=font_size)
        gap = 8.4 * scale
        right = _frag(40.0 * scale + gap, 90.0 * scale, "correspondente", font_size=font_size)
        relation = compute_line_fragment_relation(left, right)
        assert relation.decision == "merge_with_space", f"failed at scale={scale}"
        assert relation.gap_ratio == pytest.approx(0.84, abs=0.01)


def test_font_size_variation_keeps_the_same_classification():
    """The same *relative* shape (gap ~0.85x font, trailing space present)
    must classify identically at very different absolute font sizes -
    never a fixed absolute point threshold.
    """
    for font_size in (6.0, 9.96, 24.0):
        left = _frag(0.0, 40.0, "total ", font_size=font_size)
        right = _frag(40.0 + 0.85 * font_size, 90.0, "correspondente", font_size=font_size)
        relation = compute_line_fragment_relation(left, right)
        assert relation.decision == "merge_with_space", f"failed at font_size={font_size}"

    for font_size in (6.0, 9.96, 24.0):
        left = _frag(0.0, 40.0, "127.0.0.0", font_size=font_size)  # no trailing space
        right = _frag(40.0 + 3.0 * font_size, 90.0, "255.0.0.0", font_size=font_size)
        relation = compute_line_fragment_relation(left, right)
        assert relation.decision == "preserve_separate", f"failed at font_size={font_size}"


def test_fragmentation_depth_two_three_four_spans_all_reconstruct_fully():
    """PROMPT section 24: fragmentation into two, three, and four spans."""
    for n in (2, 3, 4):
        words = [f"palavra{i} " for i in range(n - 1)] + ["final."]
        x = 0.0
        fragments = []
        for word in words:
            width = len(word) * 6.0
            fragments.append(_frag(x, x + width, word, font_size=10.0))
            x += width + 8.5
        groups = group_line_fragments(fragments)
        assert len(groups) == 1, f"failed at n={n}"
        assert len(groups[0]) == n


def test_content_stream_order_does_not_affect_the_result():
    """Fragments arriving out of x-order (as PyMuPDF's own block/line
    traversal order need not match visual left-to-right order) must still
    group and sort correctly - grouping sorts by x0 internally.
    """
    ordered = ["total ", "correspondente ", "aos"]
    x = 0.0
    fragments = []
    for word in ordered:
        width = len(word) * 6.0
        fragments.append(_frag(x, x + width, word))
        x += width + 8.4
    shuffled = [fragments[2], fragments[0], fragments[1]]
    groups = group_line_fragments(shuffled)
    assert len(groups) == 1
    assert [f.raw_text for f in groups[0]] == ordered


# --- LineFragmentRelation is a real, inspectable structure ------------------


def test_relation_never_collapses_evidence_before_returning():
    relation = compute_line_fragment_relation(_frag(0.0, 40.0, "a "), _frag(48.0, 90.0, "b"))
    assert isinstance(relation, LineFragmentRelation)
    assert hasattr(relation, "same_baseline")
    assert hasattr(relation, "horizontal_gap")
    assert hasattr(relation, "gap_ratio")
    assert hasattr(relation, "left_had_trailing_space")
    assert hasattr(relation, "font_size_compatible")
    assert hasattr(relation, "both_non_monospace")


def test_font_size_tolerance_constant_is_used_symmetrically():
    left = _frag(0.0, 40.0, "a ", font_size=10.0)
    right_ok = _frag(48.0, 90.0, "b", font_size=10.0 + FONT_SIZE_TOLERANCE_PT)
    right_bad = _frag(48.0, 90.0, "b", font_size=10.0 + FONT_SIZE_TOLERANCE_PT + 0.1)
    assert compute_line_fragment_relation(left, right_ok).font_size_compatible is True
    assert compute_line_fragment_relation(left, right_bad).font_size_compatible is False
