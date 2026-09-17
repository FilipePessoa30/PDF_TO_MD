from __future__ import annotations

import pymupdf
import pytest

from enade.extraction.assets import (
    PAGE_CONTENT_MARGIN,
    _render_bbox,
    render_region,
    render_table_region,
)
from enade.extraction.figures import VisualRegion
from enade.extraction.tables import DetectedTable
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


def test_render_table_region_caps_widening_to_column_bounds(blank_doc: pymupdf.Document, tmp_path):
    """Regression test: 2011 Questao 22 -> Questao 23 (page 14, PROMPT
    Phase 2E section 7). Questao 22's own ``table-01.png`` was found, by
    direct pixel inspection, to widen all the way across to Questao 23's
    own automaton diagram and grammar on the right column -
    ``render_table_region`` had no ``column_bounds`` parameter at all,
    unlike ``render_region`` (fixed in Phase 2D for the same defect class
    on Q9/Q23). A ``DetectedTable``'s own bbox is already correctly
    confined to its owning question's own lines (``detect_tables`` runs on
    one question's own span only) - the leak was entirely in this
    function's own unconditional page-content-width widening.
    """
    from enade.extraction.assets import RENDER_ZOOM

    table = DetectedTable(
        page_number=1,
        bbox=(112.9, 152.6, 201.5, 395.5),
        headers=["A", "B", "C", "D", "S"],
        rows=[["0", "0", "0", "0", "1"]],
        consumed_lines=frozenset(),
    )
    column_bounds = (8.5, 221.5)  # Questao 22's own left column only
    rendered = render_table_region(
        blank_doc,
        table,
        tmp_path / "table-01.png",
        "table-01.png",
        "table-01",
        column_bounds=column_bounds,
    )
    page = blank_doc[0]
    # The render clip is the intersection of column_bounds and the plain
    # page-content-width fallback (whichever side is narrower wins on each
    # edge) - here column_bounds[1]=221.5 is the narrower right edge
    # (vs. the page's own default 565.0), so it caps the render; the left
    # edge stays at the page's own default margin either way.
    expected_x0 = max(page.rect.x0 + PAGE_CONTENT_MARGIN, column_bounds[0])
    expected_x1 = min(page.rect.x1 - PAGE_CONTENT_MARGIN, column_bounds[1])
    assert expected_x1 < page.rect.x1 - PAGE_CONTENT_MARGIN  # sanity: cap is the binding one
    expected_width_pt = expected_x1 - expected_x0
    assert rendered.width_px == pytest.approx(expected_width_pt * RENDER_ZOOM, abs=2)


def test_render_table_region_widens_to_full_page_without_column_bounds(
    blank_doc: pymupdf.Document, tmp_path
):
    # Unchanged pre-Phase-2E behavior when no column_bounds is supplied.
    from enade.extraction.assets import RENDER_ZOOM

    table = DetectedTable(
        page_number=1,
        bbox=(112.9, 152.6, 201.5, 395.5),
        headers=["A"],
        rows=[["0"]],
        consumed_lines=frozenset(),
    )
    rendered = render_table_region(
        blank_doc, table, tmp_path / "table-01.png", "table-01.png", "table-01"
    )
    page = blank_doc[0]
    expected_width_pt = page.rect.width - 2 * PAGE_CONTENT_MARGIN
    assert rendered.width_px == pytest.approx(expected_width_pt * RENDER_ZOOM, abs=2)


# --- PROMPT Fase 3S: declared inline-formula regions render as `equation` ---


def test_render_region_diagram_unaffected_by_new_equation_field(
    blank_doc: pymupdf.Document, tmp_path
):
    # Baseline (every region in the corpus except Q45's own new one):
    # `is_declared_inline_formula` defaults to False, so behavior is
    # completely unchanged - vector content still renders as `diagram`.
    region = VisualRegion(page_number=1, bbox=(100.0, 100.0, 200.0, 150.0), element_count=3)
    rendered = render_region(
        blank_doc, region, tmp_path / "figure-01.png", "figure-01.png", "figure-01"
    )
    assert rendered.asset_type == AssetType.DIAGRAM


def test_render_region_image_unaffected_by_new_equation_field(
    blank_doc: pymupdf.Document, tmp_path
):
    region = VisualRegion(
        page_number=1, bbox=(100.0, 100.0, 200.0, 150.0), element_count=1, has_raster_image=True
    )
    rendered = render_region(
        blank_doc, region, tmp_path / "figure-01.png", "figure-01.png", "figure-01"
    )
    assert rendered.asset_type == AssetType.IMAGE


def test_render_region_declared_inline_formula_renders_as_equation(
    blank_doc: pymupdf.Document, tmp_path
):
    """PROMPT Fase 3S: a region built from a ``declare_inline_formula_region``
    override (2008-b Q45's own "f(x) = sqrt(x)") renders as ``equation``,
    regardless of ``has_raster_image`` (always False for a pure vector
    drawing, never a real embedded raster image).
    """
    region = VisualRegion(
        page_number=1,
        bbox=(100.0, 100.0, 130.0, 112.0),
        element_count=9,
        has_raster_image=False,
        is_small_formula=True,
        is_declared_inline_formula=True,
    )
    rendered = render_region(
        blank_doc, region, tmp_path / "figure-02.png", "figure-02.png", "figure-02"
    )
    assert rendered.asset_type == AssetType.EQUATION


def test_render_region_declared_inline_formula_crop_stays_tight(
    blank_doc: pymupdf.Document, tmp_path
):
    """A declared inline formula's own ``owner_x_bounds`` (set by
    ``assembler._build_declared_inline_formula_regions`` to a small,
    fixed padding around the formula's own bbox) must actually cap the
    render width - never widened to the page's own full content width the
    way every other region already is (PROMPT Fase 3S, Section 17: the
    crop must contain "somente o contexto minimo necessario").
    """
    from enade.extraction.assets import RENDER_ZOOM

    region = VisualRegion(
        page_number=1,
        bbox=(200.0, 100.0, 230.0, 112.0),
        element_count=9,
        is_declared_inline_formula=True,
        owner_x_bounds=(194.0, 236.0),
    )
    rendered = render_region(
        blank_doc, region, tmp_path / "figure-02.png", "figure-02.png", "figure-02"
    )
    page = blank_doc[0]
    full_page_width_pt = page.rect.width - 2 * PAGE_CONTENT_MARGIN
    assert rendered.width_px < full_page_width_pt * RENDER_ZOOM
    expected_width_pt = 236.0 - 194.0
    assert rendered.width_px == pytest.approx(expected_width_pt * RENDER_ZOOM, abs=2)
