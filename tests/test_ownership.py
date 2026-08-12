from __future__ import annotations

from enade.extraction.boundaries import QuestionKind, QuestionSpan
from enade.extraction.layout import Line
from enade.extraction.ownership import (
    QuestionRegion,
    compute_question_regions,
    detect_contamination,
    find_owner,
    question_key,
)


def _line(page: int, y: float, text: str, x: float = 30.0, width: float = 200.0) -> Line:
    return Line(page_number=page, text=text, x0=x, y0=y, x1=x + width, y1=y + 12)


def _span(kind: QuestionKind, number: int, lines: list[Line]) -> QuestionSpan:
    pages = sorted({ln.page_number for ln in lines})
    return QuestionSpan(
        kind=kind, number=number, lines=tuple(lines), start_page=pages[0], end_page=pages[-1]
    )


def test_compute_question_regions_two_questions_same_column():
    span_a = _span(
        QuestionKind.OBJECTIVE,
        24,
        [_line(1, 100, "Questao 24 texto"), _line(1, 120, "mais texto 24")],
    )
    span_b = _span(
        QuestionKind.OBJECTIVE,
        25,
        [_line(1, 200, "Questao 25 texto"), _line(1, 220, "mais texto 25")],
    )
    by_page = compute_question_regions([span_a, span_b])
    regions = by_page[1]
    assert len(regions) == 2
    assert regions[0].question_key == "objective-24"
    assert regions[0].y0 == 100 and regions[0].y1 == 132  # y0 of last line + its own height
    assert regions[1].question_key == "objective-25"
    assert regions[1].y0 == 200


def test_compute_question_regions_two_questions_different_columns():
    span_left = _span(QuestionKind.OBJECTIVE, 9, [_line(1, 100, "esquerda", x=30, width=250)])
    span_right = _span(QuestionKind.OBJECTIVE, 10, [_line(1, 100, "direita", x=300, width=250)])
    by_page = compute_question_regions([span_left, span_right])
    regions = by_page[1]
    keys = {r.question_key for r in regions}
    assert keys == {"objective-9", "objective-10"}
    left = next(r for r in regions if r.question_key == "objective-9")
    right = next(r for r in regions if r.question_key == "objective-10")
    assert left.x1 < right.x0  # no horizontal overlap between the two columns


def test_compute_question_regions_multipage_question_has_one_region_per_page():
    span = _span(
        QuestionKind.DISCURSIVE,
        3,
        [_line(1, 600, "fim da pagina 1"), _line(2, 80, "inicio da pagina 2")],
    )
    by_page = compute_question_regions([span])
    assert 1 in by_page and 2 in by_page
    assert by_page[1][0].question_key == "discursive-3"
    assert by_page[2][0].question_key == "discursive-3"


def test_compute_question_regions_excludes_chrome_lines():
    span = _span(
        QuestionKind.OBJECTIVE,
        1,
        [_line(1, 10, "2011"), _line(1, 100, "conteudo real da questao")],
    )
    by_page = compute_question_regions([span])
    # Chrome ("2011") must not pull the region's own y0 up to the header.
    assert by_page[1][0].y0 == 100


def test_find_owner_containment_wins():
    regions = [
        QuestionRegion("objective-24", 1, x0=30, y0=100, x1=280, y1=300),
        QuestionRegion("objective-25", 1, x0=300, y0=100, x1=550, y1=300),
    ]
    owner = find_owner(regions, x=150, y=200)
    assert owner is not None
    assert owner.question_key == "objective-24"


def test_find_owner_falls_back_to_nearest_in_same_column():
    # A figure candidate sitting just below its owner's last line, outside
    # the tight line-bbox (the common real-world case - see module docstring).
    regions = [
        QuestionRegion("objective-24", 1, x0=30, y0=100, x1=280, y1=300),
        QuestionRegion("objective-25", 1, x0=300, y0=100, x1=550, y1=300),
    ]
    owner = find_owner(regions, x=150, y=310)  # just below Q24's own y1, same column
    assert owner is not None
    assert owner.question_key == "objective-24"


def test_find_owner_never_crosses_into_the_wrong_column():
    # Even though Q25's own y-range is numerically identical, x=150 is in
    # Q24's own column - must never resolve to Q25 just by y-proximity.
    regions = [
        QuestionRegion("objective-24", 1, x0=30, y0=100, x1=280, y1=200),
        QuestionRegion("objective-25", 1, x0=300, y0=100, x1=550, y1=200),
    ]
    owner = find_owner(regions, x=150, y=100)
    assert owner is not None
    assert owner.question_key == "objective-24"


def test_find_owner_empty_regions_returns_none():
    assert find_owner([], x=10, y=10) is None


def test_question_region_clip_hard_limits_growth():
    # A region that has grown (via label absorption elsewhere) far past its
    # owner's own bbox must be clamped back to owner.bbox + margin - this is
    # what stops Q24's own runaway growth from ever reaching Q25/Q26's
    # territory in the rendered crop, even if absorption logic itself still
    # wants to include them.
    owner = QuestionRegion("objective-24", 1, x0=30, y0=100, x1=280, y1=300)
    overgrown = (10.0, 50.0, 500.0, 600.0)
    clipped = owner.clip(overgrown, margin=20.0)
    assert clipped == (30 - 20.0, 100 - 20.0, 280 + 20.0, 300 + 20.0)


def test_question_region_clip_leaves_a_contained_rect_untouched():
    owner = QuestionRegion("objective-6", 1, x0=28.5, y0=119.7, x1=287.4, y1=366.3)
    already_inside = (30.0, 130.0, 280.0, 350.0)
    assert owner.clip(already_inside, margin=20.0) == already_inside


def test_detect_contamination_flags_real_overlap_into_a_neighbor():
    regions = [
        QuestionRegion("objective-24", 1, x0=30, y0=100, x1=280, y1=300),
        QuestionRegion("objective-25", 1, x0=300, y0=100, x1=550, y1=300),
    ]
    # An asset "owned" by Q24 that actually spans into Q25's own column.
    asset_bbox = (30.0, 100.0, 400.0, 300.0)
    findings = detect_contamination("objective-24", asset_bbox, regions)
    assert len(findings) == 1
    assert findings[0].intersecting_question_key == "objective-25"
    assert findings[0].intersection_area > 0


def test_detect_contamination_no_finding_when_asset_stays_in_owner_territory():
    regions = [
        QuestionRegion("objective-24", 1, x0=30, y0=100, x1=280, y1=300),
        QuestionRegion("objective-25", 1, x0=300, y0=100, x1=550, y1=300),
    ]
    asset_bbox = (35.0, 110.0, 275.0, 290.0)
    assert detect_contamination("objective-24", asset_bbox, regions) == []


def test_detect_contamination_ignores_trivial_overlap_below_threshold():
    regions = [
        QuestionRegion("objective-24", 1, x0=30, y0=100, x1=280, y1=300),
        QuestionRegion("objective-25", 1, x0=279, y0=299, x1=550, y1=320),  # corner sliver only
    ]
    asset_bbox = (30.0, 100.0, 280.0, 300.0)
    assert (
        detect_contamination("objective-24", asset_bbox, regions, min_intersection_area=25.0) == []
    )


def test_question_key_matches_kind_and_number():
    span = _span(QuestionKind.DISCURSIVE, 3, [_line(1, 10, "x")])
    assert question_key(span) == "discursive-3"
