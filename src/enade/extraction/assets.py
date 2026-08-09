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


def render_region(
    doc: pymupdf.Document,
    region: VisualRegion,
    output_path: Path,
    relative_path: str,
    asset_id: str,
) -> RenderedAsset:
    """Render one visual region to a PNG file at ``output_path`` (absolute).

    ``relative_path`` is the portable path recorded in the ``Asset`` model
    (e.g. ``2021-cc-b-q17/figure-01.png``, relative to ``data/assets/questions/``)
    - kept separate from ``output_path`` because the latter is a real
    filesystem location and the former must stay project-relative and
    OS-independent (see docs/data-contract.md, "Assets").
    """
    page = doc[region.page_number - 1]
    content_x0 = page.rect.x0 + PAGE_CONTENT_MARGIN
    content_x1 = page.rect.x1 - PAGE_CONTENT_MARGIN
    clip = pymupdf.Rect(
        min(region.bbox[0], content_x0),
        region.bbox[1] - RENDER_PADDING,
        max(region.bbox[2], content_x1),
        region.bbox[3] + RENDER_PADDING,
    )
    clip = clip & page.rect  # clamp to the physical page

    matrix = pymupdf.Matrix(RENDER_ZOOM, RENDER_ZOOM)
    pixmap = page.get_pixmap(matrix=matrix, clip=clip)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    pixmap.save(str(output_path))

    sha256 = hashlib.sha256(output_path.read_bytes()).hexdigest()
    asset_type = AssetType.IMAGE if region.has_raster_image else AssetType.DIAGRAM

    return RenderedAsset(
        asset_id=asset_id,
        asset_type=asset_type,
        relative_path=relative_path,
        absolute_path=output_path,
        source_page=region.page_number,
        sha256=sha256,
        width_px=pixmap.width,
        height_px=pixmap.height,
    )
