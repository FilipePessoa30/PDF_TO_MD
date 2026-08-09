from __future__ import annotations

from enade.extraction.figures import (
    MAX_ABSORPTION_GROWTH,
    _expand_with_labels,
    _merge_by_vertical_proximity,
    _rects_touch,
)


def test_rects_touch_true_within_padding():
    a = (0, 0, 10, 10)
    b = (15, 0, 25, 10)  # 5pt gap
    assert _rects_touch(a, b, padding=10) is True
    assert _rects_touch(a, b, padding=2) is False


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
