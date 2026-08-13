from __future__ import annotations

import pymupdf
import pytest

from enade.extraction.assets import PAGE_CONTENT_MARGIN, _render_bbox
from enade.models.enums import AssetType


@pytest.fixture
def blank_doc() -> pymupdf.Document:
    doc = pymupdf.open()
    doc.new_page(width=580.0, height=780.0)
    return doc


def test_render_bbox_widens_to_full_page_content_width_without_column_bounds(
    blank_doc: pymupdf.Document, tmp_path
):
    # Baseline behavior (PROMPT Phase 1B/2A: Q3/Q5/Q11) - unchanged when no
    # column_bounds is given, e.g. every 2021 single-column call site.
    rendered = _render_bbox(
        blank_doc,
        1,
        (250.0, 100.0, 260.0, 110.0),
        tmp_path / "out.png",
        "out.png",
        "figure-01",
        AssetType.DIAGRAM,
    )
    page = blank_doc[0]
    expected_width_pt = page.rect.width - 2 * PAGE_CONTENT_MARGIN
    from enade.extraction.assets import RENDER_ZOOM

    assert rendered.width_px == pytest.approx(expected_width_pt * RENDER_ZOOM, abs=2)


def test_render_bbox_caps_widening_to_column_bounds(blank_doc: pymupdf.Document, tmp_path):
    """Regression test: 2011 Questao 23 (page 14) - a narrow region crop
    was found, by direct visual inspection, to widen all the way across to
    Questao 22's own left column (root cause: PAGE_CONTENT_MARGIN-based
    widening has no notion of columns) - see docs/decisions.md, Phase 2D
    ADR. When ``column_bounds`` is supplied (the owning question's own
    x-range), the render must never widen past it, even though the plain
    page-content-width fallback would have gone further.
    """
    from enade.extraction.assets import RENDER_ZOOM

    column_bounds = (296.0, 556.0)  # right column only, e.g. Questao 23's own territory
    rendered = _render_bbox(
        blank_doc,
        1,
        (300.0, 100.0, 400.0, 110.0),
        tmp_path / "out.png",
        "out.png",
        "figure-01",
        AssetType.DIAGRAM,
        column_bounds=column_bounds,
    )
    expected_width_pt = column_bounds[1] - column_bounds[0]
    assert rendered.width_px == pytest.approx(expected_width_pt * RENDER_ZOOM, abs=2)


def test_render_bbox_column_bounds_never_widens_past_page_edges(
    blank_doc: pymupdf.Document, tmp_path
):
    # A column_bounds wider than the page's own content width must not
    # itself widen the crop past the physical page - the two caps combine
    # (whichever is narrower wins), never just one or the other.
    from enade.extraction.assets import RENDER_ZOOM

    rendered = _render_bbox(
        blank_doc,
        1,
        (250.0, 100.0, 260.0, 110.0),
        tmp_path / "out.png",
        "out.png",
        "figure-01",
        AssetType.DIAGRAM,
        column_bounds=(-500.0, 2000.0),
    )
    page = blank_doc[0]
    expected_width_pt = page.rect.width - 2 * PAGE_CONTENT_MARGIN
    assert rendered.width_px == pytest.approx(expected_width_pt * RENDER_ZOOM, abs=2)
