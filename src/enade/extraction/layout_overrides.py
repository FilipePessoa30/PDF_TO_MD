"""Declarative, hash-locked exceptions to general layout heuristics.

PROMPT Phase 2B section 6 (fix hierarchy), Level 3: when a genuinely
document-specific case cannot be safely resolved by a general (Level 1) or
declarative-profile (Level 2) rule - because every general discriminator
tried also matches unrelated content elsewhere in the corpus - the
alternative is a narrow, auditable override rather than either a
hardcoded ``if question_id == ...`` in the parser or silently accepting a
false positive.

An override is locked to the exact source PDF's SHA-256: if the source
file is ever replaced (a corpus refresh, a corrected re-scan), every
override referencing the old hash simply stops matching and must be
re-reviewed - it can never silently misapply to different content.

Ships with three entries (2011 unified booklet): Q22's truth-table header
"A B C D S" (``exclude_from_orphan_marker_merge``), a spurious
figure-region suppression for Q13's page (``suppress_visual_region``), and
protection for Q23's own mid-sentence text fragments that trail an inline
symbol image (``protect_from_label_absorption``) - see docs/decisions.md,
Phase 2B ADR, for why each needed Level 3 rather than a general fix.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class LayoutOverride(BaseModel):
    pdf_sha256: str
    page: int
    bbox: tuple[float, float, float, float]
    rule: str
    question_id: str
    reason: str
    evidence: str
    status: str
    #: Used only by ``force_fraction_merge`` (PROMPT Phase 2D section 8/12):
    #: the bbox of the second physical line to merge in, alongside the
    #: primary ``bbox`` (the orphan marker's own bbox). Unused/None for
    #: every other rule kind.
    secondary_bbox: tuple[float, float, float, float] | None = None


class LayoutOverrideSet(BaseModel):
    overrides: list[LayoutOverride] = Field(default_factory=list)

    def excludes_from_orphan_marker(
        self, pdf_sha256: str, page: int, bbox: tuple[float, float, float, float]
    ) -> bool:
        """True if some override locks out orphan-marker treatment for a
        line at ``bbox`` on ``page`` of the PDF identified by ``pdf_sha256``.

        Containment, not overlap: the candidate line's own bbox must sit
        fully inside the override's declared bbox - a deliberately tight
        match so an override can never accidentally reach a neighboring
        line it was not written for.
        """
        x0, y0, x1, y1 = bbox
        for override in self.overrides:
            if override.rule != "exclude_from_orphan_marker_merge":
                continue
            if override.pdf_sha256 != pdf_sha256 or override.page != page:
                continue
            ox0, oy0, ox1, oy1 = override.bbox
            if x0 >= ox0 and y0 >= oy0 and x1 <= ox1 and y1 <= oy1:
                return True
        return False

    def suppresses_region(
        self, pdf_sha256: str, page: int, bbox: tuple[float, float, float, float]
    ) -> bool:
        """True if some override suppresses a detected visual region at
        ``bbox`` on ``page`` of the PDF identified by ``pdf_sha256`` -
        e.g. a wrongly-grown figure region that has already been
        determined (by direct visual inspection, PROMPT Phase 2B section
        8) to contain no legitimate figure content at all.

        Matched by the candidate region's own center point falling inside
        the override's declared bbox - deliberately looser than
        ``excludes_from_orphan_marker``'s tight containment, since a
        region grown by iterative label absorption is not guaranteed to
        reproduce byte-identical bounds if the absorption logic itself
        changes later; the override still only matches a region that is
        substantially the same defect it was written for.
        """
        x0, y0, x1, y1 = bbox
        center_x, center_y = (x0 + x1) / 2, (y0 + y1) / 2
        for override in self.overrides:
            if override.rule != "suppress_visual_region":
                continue
            if override.pdf_sha256 != pdf_sha256 or override.page != page:
                continue
            ox0, oy0, ox1, oy1 = override.bbox
            if ox0 <= center_x <= ox1 and oy0 <= center_y <= oy1:
                return True
        return False

    def protects_from_label_absorption(
        self, pdf_sha256: str, page: int, bbox: tuple[float, float, float, float]
    ) -> bool:
        """True if some override protects a text line at ``bbox`` on
        ``page`` from being absorbed as a figure label.

        For a mid-sentence text fragment that trails an inline symbol
        image (2011 Q23: the alphabet/regex notation is a small raster
        image, so the sentence's own continuation after that image starts
        at an x0 that matches neither of the page's two detected column
        margins - the existing two-column body-text protection only
        recognizes a line by its *starting* x0, not by belonging to the
        same physical row as an already-protected line - leaving it
        eligible for absorption into the automaton diagram's region).

        Containment, like ``excludes_from_orphan_marker``: the candidate
        line's own bbox must sit fully inside the override's bbox.
        """
        x0, y0, x1, y1 = bbox
        for override in self.overrides:
            if override.rule != "protect_from_label_absorption":
                continue
            if override.pdf_sha256 != pdf_sha256 or override.page != page:
                continue
            ox0, oy0, ox1, oy1 = override.bbox
            if x0 >= ox0 and y0 >= oy0 and x1 <= ox1 and y1 <= oy1:
                return True
        return False

    def excludes_from_region_candidates(
        self, pdf_sha256: str, page: int, bbox: tuple[float, float, float, float]
    ) -> bool:
        """True if some override excludes an image/drawing at ``bbox`` on
        ``page`` from ever seeding or joining a candidate visual region.

        For a tiny inline symbol image chain-merged (via
        ``_merge_by_vertical_proximity``'s vertical-proximity sweep) into
        an unrelated, larger figure below it (2011 Q23: three small
        alphabet/epsilon symbol images at y0 131-165 merge, each within
        the 18pt tolerance of the next, into the automaton diagram
        starting at y0=177 - anchoring the whole region's top edge back
        up into the statement's own text, which then gets excluded from
        the rendered statement as "inside a region" independent of the
        separate label-absorption protection above). Dropping the
        candidate before clustering even begins is the only point that
        actually prevents this, since the tiny images are individually
        far under ``MIN_REGION_HEIGHT`` and would never form a region of
        their own once excluded from the merge.

        Containment, like the other rules above.
        """
        x0, y0, x1, y1 = bbox
        for override in self.overrides:
            if override.rule != "exclude_from_region_candidates":
                continue
            if override.pdf_sha256 != pdf_sha256 or override.page != page:
                continue
            ox0, oy0, ox1, oy1 = override.bbox
            if x0 >= ox0 and y0 >= oy0 and x1 <= ox1 and y1 <= oy1:
                return True
        return False

    def fraction_merge_partner(
        self, pdf_sha256: str, page: int, marker_bbox: tuple[float, float, float, float]
    ) -> tuple[float, float, float, float] | None:
        """The bbox of a second physical line to merge into this orphan
        marker's own text, if one is declared (PROMPT Phase 2D section 8).

        2011 Q10: each alternative's own answer is a stacked two-line
        fraction (a numerator line above the marker's own baseline, a
        denominator below - PyMuPDF never emits a slash glyph). The
        general orphan-marker merge (layout.py's own
        ``_merge_orphan_markers``) already finds the denominator - closer
        to the marker in every observed case - as the marker's primary
        partner; this override supplies the *numerator*, which would
        otherwise be left as a standalone bare-digit line for chrome.py's
        running-page-number heuristic to strip.

        A general (Level 1) second-pass search for this exact shape was
        tried and rejected (PROMPT Phase 2C ADR 30): on 2021's own Q34
        (a Dijkstra graph node-label listing, five independent
        single-letter-node + single-digit-value pairs set close together),
        the same opposite-side search spliced unrelated neighboring pairs
        into spurious fractions. This override is deliberately the
        opposite of that: it supplies *no* search heuristic at all, only
        five explicit, hash-and-bbox-locked (marker bbox -> numerator
        bbox) pairs for 2011's own Q10 - it can never match any other
        line, on any other page, in any other document, regardless of
        shape.

        Containment, like the other rules above: ``marker_bbox`` must sit
        fully inside the override's own declared ``bbox``.
        """
        x0, y0, x1, y1 = marker_bbox
        for override in self.overrides:
            if override.rule != "force_fraction_merge" or override.secondary_bbox is None:
                continue
            if override.pdf_sha256 != pdf_sha256 or override.page != page:
                continue
            ox0, oy0, ox1, oy1 = override.bbox
            if x0 >= ox0 and y0 >= oy0 and x1 <= ox1 and y1 <= oy1:
                return override.secondary_bbox
        return None

    def protects_from_region_membership(
        self, pdf_sha256: str, page: int, bbox: tuple[float, float, float, float]
    ) -> bool:
        """True if some override keeps a text line at ``bbox`` on ``page``
        out of a visual region's own text-exclusion check, even though its
        geometry touches the region's (possibly growth-capped) bbox
        (PROMPT Phase 2D section 12).

        Distinct from ``protects_from_label_absorption``, which stops a
        line from *expanding* a region during label-absorption growth: a
        line can end up geometrically inside a region's final bbox
        without ever having been an absorption candidate itself, simply
        because growth capped by ``MAX_ABSORPTION_GROWTH`` (figures.py)
        happened to land past its own top edge (2011 Q12: item IV's own
        opening line sits ~0.9pt inside a region whose growth was capped
        110pt from an unrelated image's own edge, not because item IV was
        itself absorbed - protecting it from absorption alone does not
        change the region's own final bbox). This rule addresses the
        text-exclusion side directly, regardless of why the geometry
        overlaps.

        Containment, like the other rules above.
        """
        x0, y0, x1, y1 = bbox
        for override in self.overrides:
            if override.rule != "protect_from_region_membership":
                continue
            if override.pdf_sha256 != pdf_sha256 or override.page != page:
                continue
            ox0, oy0, ox1, oy1 = override.bbox
            if x0 >= ox0 and y0 >= oy0 and x1 <= ox1 and y1 <= oy1:
                return True
        return False

    def forces_single_column(self, pdf_sha256: str, page: int) -> bool:
        """True if some override forces naive (y0, x0) reading order for
        the whole page, bypassing ``detect_column_margins`` entirely.

        For a genuinely single-column page whose indented content (a
        centered/quoted poem, in 2011 Q1's case: 14 lines all sharing one
        consistent x0 offset from the body margin) happens to clear
        ``detect_column_margins``'s own evidence threshold, misreading it
        as a second column running in parallel with the real body text.
        Unlike this corpus's genuine two-column pages (where both
        "columns"' content spans roughly the same Y-range in parallel),
        the indented block here occupies a Y-range nested *inside* the
        surrounding single-column flow - but no geometric discriminator
        for that distinction was tried and verified safe here (given the
        session's repeated experience that plausible-looking general
        column-detection tweaks tend to have non-obvious false positives
        elsewhere in a two-year corpus); a page-level override was used
        instead. ``bbox``/``question_id`` are unused for this rule kind
        and left as the schema's own placeholder values.
        """
        for override in self.overrides:
            if override.rule != "force_single_column_page":
                continue
            if override.pdf_sha256 == pdf_sha256 and override.page == page:
                return True
        return False


def load_layout_overrides(path: Path) -> LayoutOverrideSet:
    """Load an override set, or an empty one if ``path`` does not exist -
    the override mechanism is opt-in per caller, never a hard requirement.
    """
    if not path.exists():
        return LayoutOverrideSet()
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return LayoutOverrideSet.model_validate(data)
