"""Render detected visual regions to PNG crops and compute their provenance.

Per PROMPT section 12: fidelity to visual appearance is the goal, not
"extract embedded image objects" - most figures in this corpus are vector
graphics (diagrams, charts, trees, circuits), so the region is rendered by
rasterizing the page at a fixed zoom and cropping to the region's bounding
box (plus a small padding margin), rather than trying to re-export
individual vector paths.

Asset *type* classification is intentionally coarse and conservative: a
region built from at least one real embedded raster image is tagged
``image``; everything else (the overwhelming majority in this corpus -
trees, graphs, circuits, charts, tables) is tagged ``diagram``. Telling a
chart apart from a table apart from a diagram automatically, reliably,
without inventing a classification, is out of scope for this phase - see
docs/decisions.md.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import pymupdf

from enade.extraction.figures import VisualRegion
from enade.extraction.tables import DetectedTable
from enade.models.enums import AssetExtractionMethod, AssetType

#: Padding (points) added around a region's bbox (vertically) before
#: rendering, so thin strokes right at the detected edge aren't clipped.
RENDER_PADDING = 4.0
#: Render zoom factor (2.0 => 144 DPI at this PDF's native 72 DPI base).
RENDER_ZOOM = 3.0
#: Horizontal margin (points) kept from each page edge when widening a
#: crop to the page's content width (see ``render_region``: a figure's own
#: bbox is often narrower than the page, so full-width paragraph lines
#: that happen to share its vertical band get clipped left/right if the
#: crop only spans the figure itself - observed on this booklet's Q3, Q5,
#: Q11. Cropping to content width instead shows those lines in full rather
#: than as truncated fragments; it never removes anything, only shows more).
#:
#: On a two-column page this same widening reaches straight across into the
#: *other* column's own unrelated content, since it has no notion of which
#: column a region belongs to (2011 unified booklet: Questao 23's own
#: automaton crop was found, by direct visual inspection, to also contain
#: Questao 22's own truth table - see docs/decisions.md, Phase 2D ADR).
#: ``_render_bbox``'s own ``column_bounds`` parameter (populated from
#: ``VisualRegion.owner_x_bounds``, see ownership.py) caps this widening to
#: the region's own owning question whenever an owner is known, leaving
#: single-column pages (2021) unaffected - there, a question's own text
#: already reaches close to the full content width, so the owner-bounds cap
#: and the plain page-content-width fallback below coincide.
PAGE_CONTENT_MARGIN = 15.0


@dataclass(frozen=True)
class RenderedAsset:
    asset_id: str
    asset_type: AssetType
    relative_path: str
    absolute_path: Path
    source_page: int
    sha256: str
    width_px: int
    height_px: int
    extraction_method: AssetExtractionMethod = AssetExtractionMethod.RASTER_CROP


def _render_bbox(
    doc: pymupdf.Document,
    page_number: int,
    bbox: tuple[float, float, float, float],
    output_path: Path,
    relative_path: str,
    asset_id: str,
    asset_type: AssetType,
    column_bounds: tuple[float, float] | None = None,
) -> RenderedAsset:
    page = doc[page_number - 1]
    content_x0 = page.rect.x0 + PAGE_CONTENT_MARGIN
    content_x1 = page.rect.x1 - PAGE_CONTENT_MARGIN
    if column_bounds is not None:
        content_x0 = max(content_x0, column_bounds[0])
        content_x1 = min(content_x1, column_bounds[1])
    clip = pymupdf.Rect(
        min(bbox[0], content_x0),
        bbox[1] - RENDER_PADDING,
        max(bbox[2], content_x1),
        bbox[3] + RENDER_PADDING,
    )
    clip = clip & page.rect  # clamp to the physical page

    matrix = pymupdf.Matrix(RENDER_ZOOM, RENDER_ZOOM)
    pixmap = page.get_pixmap(matrix=matrix, clip=clip)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    pixmap.save(str(output_path))

    sha256 = hashlib.sha256(output_path.read_bytes()).hexdigest()

    return RenderedAsset(
        asset_id=asset_id,
        asset_type=asset_type,
        relative_path=relative_path,
        absolute_path=output_path,
        source_page=page_number,
        sha256=sha256,
        width_px=pixmap.width,
        height_px=pixmap.height,
    )


def render_region(
    doc: pymupdf.Document,
    region: VisualRegion,
    output_path: Path,
    relative_path: str,
    asset_id: str,
) -> RenderedAsset:
    """Render one visual region to a PNG file at ``output_path`` (absolute).

    ``relative_path`` is the portable path recorded in the ``Asset`` model
    (e.g. ``2021-cc-b-q17/figure-01.png``, relative to the question's own
    .md file - the two live as siblings under the same course directory) -
    kept separate from ``output_path`` because the latter is a real
    filesystem location and the former must stay project-relative and
    OS-independent (see docs/data-contract.md, "Assets").
    """
    asset_type = AssetType.IMAGE if region.has_raster_image else AssetType.DIAGRAM
    return _render_bbox(
        doc,
        region.page_number,
        region.bbox,
        output_path,
        relative_path,
        asset_id,
        asset_type,
        column_bounds=region.owner_x_bounds,
    )


def render_table_region(
    doc: pymupdf.Document,
    table: DetectedTable,
    output_path: Path,
    relative_path: str,
    asset_id: str,
) -> RenderedAsset:
    """Render a detected table's bbox to a PNG crop - the mandatory visual
    fallback for structured table content (PROMPT Phase 1C section 5.2):
    this is rendered unconditionally whenever a table is detected,
    regardless of whether its structured (Markdown) reconstruction is
    later confirmed cell-by-cell.
    """
    return _render_bbox(
        doc, table.page_number, table.bbox, output_path, relative_path, asset_id, AssetType.TABLE
    )


def render_answer_standard_asset(
    doc: pymupdf.Document,
    page_number: int,
    bbox: tuple[float, float, float, float],
    output_path: Path,
    relative_path: str,
    asset_id: str,
) -> RenderedAsset:
    """Render one image embedded in the official answer standard (padrao de
    resposta) PDF - e.g. D4's worked-out circuit diagrams (PROMPT Phase 1C
    section 9). ``doc`` here is the padrao document, never the prova - see
    ``answer_standard.find_answer_standard_images``, which already scopes
    ``bbox`` to the rubric's own text region so this never re-captures a
    reprint of the question's own figure.
    """
    return _render_bbox(
        doc, page_number, bbox, output_path, relative_path, asset_id, AssetType.DIAGRAM
    )
