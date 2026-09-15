"""Assemble a question's statement/alternatives/figures from its line span.

This is the module most directly responsible for the fidelity guarantees in
PROMPT sections 5/6/9/10/11/12: it decides what counts as chrome (dropped),
what counts as a figure (replaced by an explicit image placeholder at the
correct position in the text flow, never silently paraphrased from its
internal labels), and where the statement ends and the alternatives begin -
using a right-to-left search for the A/B/C/D/E sequence rather than
trusting the first capital letter it sees (see
``_find_alternative_starts`` for why: real statements in this corpus start
mid-sentence with capital letters like "A chance de uma crianca ...",
which is not alternative A).
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Literal

import pymupdf

from enade.extraction.boundaries import QuestionKind, QuestionSpan
from enade.extraction.chrome import is_chrome_line
from enade.extraction.figures import (
    UNBOUNDED_MERGE_X_TOLERANCE,
    VisualRegion,
    _dominant_left_margin,
    _is_marker_at_margin,
    detect_visual_regions,
    dominant_left_margin_by_text_length,
)
from enade.extraction.fragment_reconstruction import FragmentMergeTrace
from enade.extraction.label_normalization import LabelCorrection
from enade.extraction.layout import Line, extract_page_lines
from enade.extraction.layout_overrides import LayoutOverrideSet
from enade.extraction.ownership import QuestionRegion, question_key
from enade.extraction.spacing import SpacingCorrection
from enade.extraction.tables import DetectedTable, detect_tables

#: The trailing "[\t ](.*)" text is optional (PROMPT Phase 3A) - 2008-b's
#: own formula-image alternatives (e.g. Q38, Q55: a whole-alternative
#: boolean-algebra expression image, the same shape as 2011 Q14) print a
#: completely bare letter with *nothing* following on the same line, not
#: even a trailing space - unlike every alternative marker previously seen
#: in this corpus, which always has at least a tab/space before its own
#: text (however short). Group 2 is therefore ``None``, not "", when the
#: marker is bare - callers use ``match.group(2) or ""`` accordingly. Safe
#: to loosen generally: ``_find_alternative_starts`` already requires a
#: full, strictly-ordered A..E sequence before treating anything as a real
#: alternative-marker run, so an incidental bare letter elsewhere in prose
#: cannot be mistaken for one on its own.
_ALTERNATIVE_LINE_RE = re.compile(r"^([A-E])(?:[\t ](.*))?$")
#: A word ending in a common ligature-prone digraph, then a stray space, then
#: a lowercase continuation - the observed signature of a ligature-splitting
#: extraction artifact (see docs/decisions.md, "ligature-space artifacts").
_BROKEN_WORD_RE = re.compile(r"\b[a-zà-ÿ]{2,}(?:ti|fi|fl|ffi)\s[a-zà-ÿ]")
#: Paragraph break heuristic: a vertical gap this many points or more between
#: consecutive surviving lines on the same page is treated as a paragraph
#: boundary rather than a mid-paragraph line wrap.
PARAGRAPH_GAP_THRESHOLD = 19.0
#: Padding (points) added around a visual region's bbox before testing
#: whether a text line falls "inside" it, to also swallow tightly-adjacent
#: figure captions/labels.
REGION_Y_PADDING = 2.0
#: Same idea, horizontally. Deliberately small (smaller than any observed
#: inter-column gutter in this corpus, e.g. D5's page-17 gutter is ~15pt
#: between the left column's x1=276.4 and the right column's x0=291.5) -
#: a genuine figure label always has real horizontal overlap with the
#: region's own (already label-absorption-expanded) bbox, since absorption
#: unions the label's own x-range into it. Without this, a Y-range-only
#: check swallowed unrelated same-Y-band content from a *different* column
#: on a two-column page (D5's heapify() code sharing a Y-band with the
#: left column's tree diagram - see docs/decisions.md, "Phase 1C" ADR).
#:
#: EXPERIMENT (PROMPT Phase 3F, "Cluster A", reverted): several 2008-b
#: pages have a real inter-column/inter-figure gutter narrower than this
#: fixed padding (as little as ~4.3pt on D10's page, ~1.6pt on Q07's,
#: before any growth), letting a whole neighboring column's own unrelated
#: body text satisfy "touches" and get silently dropped as if it were
#: figure content (D10/Q02/Q07/Q12/Q45/Q54/Q63/Q75 - root-caused precisely
#: by direct instrumentation, see docs/phase-3f-report.md). Replacing the
#: fixed padding with a ratio requirement (touch only when the genuine,
#: unpadded X-overlap reaches >= 50% of the narrower of the line's own
#: width or the region's own width) fixed D10 and Q07 completely and Q12
#: partially, confirmed safe for 2011/2021 when gated - but broke two
#: *already-passing* 2008-b questions the same way: Q61's own real
#: "Figura para a questao 61" caption sits at the page's left margin
#: (x0=36.0-153.3), genuinely but only PARTIALLY overlapping its own wide
#: diagram (x0=121.2-474.3) by 32.1pt - a 27.4% ratio, LOWER than Q07's
#: own bad line's 37.8% ratio (108.4pt overlap against a much wider,
#: unrelated 286.8pt-wide line) that the same threshold needed to reject.
#: No single global ratio can correctly separate these two cases: Q61's
#: genuine, partially-offset caption must be *kept*, while Q07's
#: coincidental, high-absolute-overlap touch from an unrelated column must
#: be *rejected*, and Q61's own ratio is numerically smaller than Q07's.
#: A more targeted fix (test the ratio against each region's own
#: *pre-growth* raw bbox, only trusting growth's own extension within a
#: small, absorption-specific allowance, rather than the fully-grown
#: bbox) was reasoned through but not implemented/verified this phase -
#: recorded as the concrete next step rather than shipped half-verified.
REGION_X_PADDING = 5.0
#: Approximate width (points) of one monospace character, used only to
#: reconstruct relative indentation for preserved code/pseudocode blocks.
CODE_CHAR_WIDTH = 6.0
#: Matches the same "QUESTAO [DISCURSIVA] N" / "QUESTAO N [-] DISCURSIVA"
#: marker boundaries.py uses to find a span's start - kept as its own
#: pattern (rather than imported) because it is applied differently here:
#: stripped as a *prefix* from the span's own first line, not searched for
#: across a whole document. The trailing "- DISCURSIVA" form (PROMPT Phase
#: 3A - 2008-b's own shape) must be stripped here too, or its own bare
#: leftover text ("- DISCURSIVA") is wrongly kept and prepended to the
#: statement's real first line as if it were content.
_MARKER_PREFIX_RE = re.compile(
    r"(?i)^quest[aã]o\s+(discursiva\s+)?0*\d+\b(\s*[-–—]\s*discursiva)?[.:\s]*"
)


@dataclass
class ExtractedAlternative:
    letter: str
    text: str
    #: Index into ``ExtractedQuestion.figure_regions``, when this
    #: alternative's own content is (fully or partly) a small raster/vector
    #: formula image rather than text (PROMPT Phase 2E section 10) - e.g.
    #: 2011 Q14, where every alternative is only a boolean-algebra formula
    #: image with no other text. ``None`` for the overwhelming majority of
    #: alternatives, which are real text.
    figure_region_index: int | None = None
    #: Ordered text/asset segments, when this alternative's own content
    #: interleaves real text with one or more small inline formula images
    #: (PROMPT Phase 2F section 7) - e.g. 2011 Q23's own alternatives D/E,
    #: each "<text> <formula image> <text>". Distinct from
    #: ``figure_region_index`` (Phase 2E's own mechanism, for an
    #: alternative that is *only* an image with no text at all - Q14's own
    #: shape, left untouched). ``None`` for every alternative that is
    #: either plain text or a single whole-alternative asset.
    segments: list[TextSegment | FigureSegment] | None = None


@dataclass
class TextSegment:
    text: str


@dataclass
class CodeSegment:
    """A run of monospace-font lines, preserved verbatim (see PROMPT section 16)."""

    text: str  # newline-joined, with reconstructed relative indentation


@dataclass
class FigureSegment:
    region_index: int  # index into ExtractedQuestion.figure_regions


@dataclass
class TableSegment:
    table_index: int  # index into ExtractedQuestion.tables


StatementSegment = TextSegment | CodeSegment | FigureSegment | TableSegment


@dataclass
class ExtractedQuestion:
    kind: QuestionKind
    number: int
    start_page: int
    end_page: int
    statement_segments: list[StatementSegment]
    alternatives: list[ExtractedAlternative] = field(default_factory=list)
    figure_regions: list[VisualRegion] = field(default_factory=list)
    #: Geometrically-reconstructed grid tables (see tables.py) - a
    #: content-shape result, empty for the large majority of questions
    #: that have no table (PROMPT Phase 1C section 5).
    tables: list[DetectedTable] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    #: Every geometry-based faux-space merge that fed into this question's
    #: final statement/alternative text (see spacing.py) - the raw material
    #: for the auditable transformation log (PROMPT section 15).
    spacing_corrections: list[SpacingCorrection] = field(default_factory=list)
    #: Every known font-mangled label correction (see label_normalization.py)
    #: that fed into this question's final text - a distinct transformation
    #: type from spacing_corrections (PROMPT section 15).
    label_corrections: list[LabelCorrection] = field(default_factory=list)
    #: Every known symbol-font character substitution (see symbol_fonts.py)
    #: that fed into this question's final text - a distinct transformation
    #: type from both spacing_corrections and label_corrections.
    symbol_corrections: list[LabelCorrection] = field(default_factory=list)
    #: Every geometric line-fragment reconstruction (see
    #: fragment_reconstruction.py, PROMPT Phase 3H "Cluster D") that fed
    #: into this question's final text - a distinct transformation type
    #: from the three above (line-level rejoining, not word/glyph-level).
    fragment_merges: list[FragmentMergeTrace] = field(default_factory=list)

    @property
    def plain_statement(self) -> str:
        """Statement text with figures elided - for quality checks, not rendering."""
        return "\n\n".join(
            seg.text
            for seg in self.statement_segments
            if isinstance(seg, TextSegment | CodeSegment)
        )


#: A line's own geometric relationship to a visual region (PROMPT Phase
#: 3G): replaces a single boolean with enough information for each
#: consumer to apply its own policy (Section 8 of the prompt) instead of
#: one predicate trying to serve every consequence - text consumption,
#: ownership, reading order - at once. Every field is a plain geometric
#: observation; no field alone decides anything (see
#: ``_text_consumption_decision`` for the one policy this module actually
#: needs today).
LineRegionState = Literal[
    "outside",
    "touching",
    "partial_overlap",
    "center_inside",
    "baseline_inside",
    "contained",
    "boundary_crossing",
    "ambiguous",
]


@dataclass(frozen=True)
class LineRegionRelation:
    state: LineRegionState
    intersection_over_line_area: float
    intersection_over_region_area: float
    horizontal_overlap_ratio: float
    vertical_overlap_ratio: float
    center_inside: bool
    baseline_inside: bool
    left_overflow: float
    right_overflow: float
    top_overflow: float
    bottom_overflow: float
    #: Genuine (zero-padding) overlap, on both axes, against the region's
    #: own *raw*, pre-growth extent (``VisualRegion.raw_bbox``) - ``None``
    #: when the region carries no raw_bbox (built directly by test code,
    #: never by ``detect_visual_regions``, which always sets it).
    raw_intersects: bool | None
    #: True when this exact line was one of the candidates
    #: ``_expand_with_labels`` itself genuinely absorbed while growing this
    #: region (``VisualRegion.absorbed_label_bboxes``) - growth's own
    #: authoritative record, trusted directly rather than re-derived from
    #: geometry a second time (see ``compute_line_region_relation``'s own
    #: docstring for why re-deriving it from ``raw_bbox`` alone is not
    #: enough: a real caption can be absorbed through several incremental
    #: growth passes, ending up nowhere near the original raw extent).
    matches_absorbed_label: bool
    same_owner: bool | None


def _axis_overlap(a0: float, a1: float, b0: float, b1: float) -> float:
    return max(0.0, min(a1, b1) - max(a0, b0))


#: Tolerance (points) for matching a line's own bbox against one of a
#: region's ``absorbed_label_bboxes`` - both come from the exact same
#: ``Line.bbox``/candidate-rect values (label_candidates are themselves
#: built from Line coordinates), so this only needs to absorb ordinary
#: floating-point noise, never a real positional difference.
_ABSORBED_LABEL_MATCH_TOLERANCE = 0.5


def _rect_matches(
    a: tuple[float, float, float, float], b: tuple[float, float, float, float]
) -> bool:
    return all(abs(x - y) <= _ABSORBED_LABEL_MATCH_TOLERANCE for x, y in zip(a, b, strict=True))


def compute_line_region_relation(
    line: Line, region: VisualRegion, own_key: str | None = None
) -> LineRegionRelation:
    """The full geometric relationship between ``line`` and ``region``.

    Deliberately reports observations, not a verdict - PROMPT Phase 3G's
    own central lesson (Section 5/9): the Fase 3F experiment showed that
    D10/Q07's own bad lines and Q61/Q71's own genuine captions can share
    almost the same overlap *ratio* against a region's grown bbox (Q61's
    real caption: 27.4%; Q07's unrelated line: 37.8%) - no single boolean
    or threshold computed from the grown bbox alone can tell them apart.
    What does: Q61's caption genuinely overlaps the region's own *raw*,
    pre-growth extent (the real drawings that make up the figure, before
    any label-absorption growth or padding); Q07's line does not - its
    only "overlap" is with growth's own heuristic allowance. ``raw_intersects``
    carries exactly that distinction; callers combine it with ``state``
    per their own policy (see ``_text_consumption_decision``) instead of
    this function collapsing it into one answer for every use.
    """
    bbox = region.bbox
    h_overlap = _axis_overlap(line.x0, line.x1, bbox[0], bbox[2])
    v_overlap = _axis_overlap(line.y0, line.y1, bbox[1], bbox[3])
    line_w = max(line.x1 - line.x0, 1e-6)
    line_h = max(line.y1 - line.y0, 1e-6)
    region_w = max(bbox[2] - bbox[0], 1e-6)
    region_h = max(bbox[3] - bbox[1], 1e-6)
    intersection_area = h_overlap * v_overlap
    line_area = line_w * line_h
    region_area = region_w * region_h
    intersection_over_line = intersection_area / line_area
    intersection_over_region = intersection_area / region_area
    h_ratio = h_overlap / min(line_w, region_w)
    v_ratio = v_overlap / min(line_h, region_h)
    center_x = (line.x0 + line.x1) / 2
    center_y = (line.y0 + line.y1) / 2
    center_inside = bbox[0] <= center_x <= bbox[2] and bbox[1] <= center_y <= bbox[3]
    baseline_inside = bbox[0] <= line.x0 <= bbox[2] and bbox[1] <= line.y1 <= bbox[3]
    left_overflow = max(0.0, bbox[0] - line.x0)
    right_overflow = max(0.0, line.x1 - bbox[2])
    top_overflow = max(0.0, bbox[1] - line.y0)
    bottom_overflow = max(0.0, line.y1 - bbox[3])

    raw_intersects: bool | None = None
    if region.raw_bbox is not None:
        raw = region.raw_bbox
        raw_h = _axis_overlap(line.x0, line.x1, raw[0], raw[2])
        raw_v = _axis_overlap(line.y0, line.y1, raw[1], raw[3])
        # Require more than a rounding-noise sliver on each axis (the same
        # floor REGION_Y_PADDING already uses elsewhere as "not a real
        # measurement, just noise") - a real caption genuinely overlapping
        # its own diagram (Q61: 32.1pt) clears this trivially; a real body
        # line whose own bbox happens to graze a *different* region's raw
        # extent by a point or two (2008-b D40's own SQL schema code line,
        # 1.6pt into a neighboring diagram's own raw top edge) does not,
        # and stays visible instead of being wrongly hidden.
        raw_intersects = raw_h > REGION_Y_PADDING and raw_v > REGION_Y_PADDING

    matches_absorbed_label = any(
        _rect_matches(line.bbox, absorbed) for absorbed in region.absorbed_label_bboxes
    )

    same_owner = (
        None if (own_key is None or region.owner_key is None) else own_key == region.owner_key
    )

    state: LineRegionState
    if h_overlap <= 0 or v_overlap <= 0:
        # No genuine intersection at all - "touching" only within the
        # small, fixed padding that models rounding/rendering noise
        # (REGION_X_PADDING/REGION_Y_PADDING), "outside" otherwise.
        padded_y = (bbox[1] - REGION_Y_PADDING) <= line.y0 <= (bbox[3] + REGION_Y_PADDING)
        padded_x = line.x0 <= (bbox[2] + REGION_X_PADDING) and line.x1 >= (
            bbox[0] - REGION_X_PADDING
        )
        state = "touching" if (padded_x and padded_y) else "outside"
    elif intersection_over_line >= 0.98:
        state = "contained"
    elif center_inside and baseline_inside:
        state = "center_inside"
    elif baseline_inside:
        state = "baseline_inside"
    elif h_ratio >= 0.8 or v_ratio >= 0.8:
        state = "boundary_crossing"
    elif intersection_over_line > 0:
        state = "partial_overlap"
    else:
        state = "ambiguous"

    return LineRegionRelation(
        state=state,
        intersection_over_line_area=intersection_over_line,
        intersection_over_region_area=intersection_over_region,
        horizontal_overlap_ratio=h_ratio,
        vertical_overlap_ratio=v_ratio,
        center_inside=center_inside,
        baseline_inside=baseline_inside,
        left_overflow=left_overflow,
        right_overflow=right_overflow,
        top_overflow=top_overflow,
        bottom_overflow=bottom_overflow,
        raw_intersects=raw_intersects,
        matches_absorbed_label=matches_absorbed_label,
        same_owner=same_owner,
    )


#: PROMPT Phase 3G, Section 8, "Consumo de texto": removing a line from the
#: rendered Markdown is the one destructive, hard-to-reverse consequence
#: `_line_in_region` gates - it requires ``contained`` or a documented
#: equivalent (here: genuine overlap against the region's own *raw*
#: extent), never mere touching or partial overlap, and never a decision
#: left ``ambiguous`` (Section 10: ambiguous must never authorize
#: destructive consumption - the line simply stays visible, the safe
#: direction, rather than being silently dropped on weak evidence).
def _text_consumption_decision(
    relation: LineRegionRelation, is_small_formula: bool = False
) -> Literal["accepted", "ambiguous"]:
    if relation.state == "contained":
        return "accepted"
    if relation.raw_intersects:
        return "accepted"
    # Growth's own authoritative record (PROMPT Phase 3G): a real caption
    # or label can be absorbed through several incremental growth passes,
    # ending up nowhere near the region's own raw, pre-growth extent on
    # its own (2011 Q9/Q14/Q23/Q38's own real citations/labels - confirmed
    # by full regeneration that ``raw_intersects`` alone wrongly rejected
    # these, see docs/phase-3g-report.md). Trusting that this exact line
    # was one of the candidates growth itself chose to absorb, rather than
    # re-deriving "was this absorbed" from geometry a second time, tells
    # a genuine multi-hop absorption apart from a wide, unrelated line
    # that merely brushes the *resulting* bbox's own edge afterwards
    # without ever being part of growth's own candidate pool at all
    # (2008-b D10/Q07's own bad lines - neither is ever itself a label
    # candidate, only short neighboring word-fragments are).
    if relation.matches_absorbed_label:
        return "accepted"
    # A small-formula region (PROMPT Phase 2E/2C: a single inline symbol or
    # a few merged into one, e.g. 2011 Q38's own grammar-terminal image) is
    # already a narrow, size-capped class (SMALL_IMAGE_MAX_WIDTH/_HEIGHT) -
    # a line merely touching one is reliably a stray adjacent fragment of
    # the same unreadable formula noise, never an unrelated wide statement
    # line the way a large diagram's own grown bbox can be brushed by one
    # (the defect this stricter policy exists to fix). Any non-"outside"
    # relation is accepted here, matching this region class's own original,
    # already-validated behavior (unchanged for every other region shape).
    if is_small_formula and relation.state != "outside":
        return "accepted"
    return "ambiguous"


def _line_in_region(
    line: Line,
    region: VisualRegion,
    overrides: LayoutOverrideSet | None = None,
    pdf_sha256: str = "",
    own_key: str | None = None,
    body_margin_x0: float | None = None,
    contextual_relation_gate: bool = False,
) -> bool:
    if line.page_number != region.page_number:
        return False
    if overrides is not None and overrides.protects_from_region_membership(
        pdf_sha256, line.page_number, line.bbox
    ):
        return False

    if not contextual_relation_gate:
        # The exact, original behavior every booklet without
        # ``ExamStructureProfile.contextual_relation_gate`` set keeps -
        # PROMPT Phase 3G's own relation-based replacement (below) fixes
        # real 2008-b defects (D10/Q07/Q12/Q24/Q29/Q63) but was found, by
        # full regeneration, to also change legitimate output on several
        # already-validated 2011/2021 questions whose own growth/reading-
        # order shape this project has not yet characterized with the same
        # precision (Q9/Q12/Q23/Q38 and others - see
        # docs/phase-3g-report.md, "Experimento" section) - a byte-for-byte
        # change to a protected corpus is never accepted regardless of how
        # much of an improvement the new logic is elsewhere, so it is
        # gated exactly like ``caption_font_size_gate``/``owner_exclusion_gate``
        # rather than made the new unconditional default.
        if _ALTERNATIVE_LINE_RE.match(line.text):
            return False
        y_touches = (
            (region.bbox[1] - REGION_Y_PADDING) <= line.y0 <= (region.bbox[3] + REGION_Y_PADDING)
        )
        if not y_touches:
            return False
        x_touches = line.x0 <= (region.bbox[2] + REGION_X_PADDING) and line.x1 >= (
            region.bbox[0] - REGION_X_PADDING
        )
        return x_touches

    # A genuine alternative marker is never figure-interior, no matter how
    # tight the vertical spacing is on this particular page (observed: on
    # a densely-laid-out DER diagram question, alternative A's marker sits
    # only ~3pt below the diagram's own vector bounding box - well inside
    # a naive geometric containment test) - but a line merely *shaped*
    # like a marker ("A\t...") is not automatically one: a diagram's own
    # internal label (a state-machine input, an ER-diagram entity name)
    # can share that exact shape (PROMPT Phase 3G, "Cluster C" - 2008-b
    # Q24/Q29/Q63's own "A"/"B"/"C" labels). ``_is_marker_at_margin``
    # (figures.py) is the same evidence-based test already used to decide
    # whether a label-shaped candidate is eligible for growth absorption -
    # a real marker sits at the page's own established body-text margin;
    # a diagram-internal label essentially never does. Reusing it here
    # closes Cluster C without a second, separately-tuned heuristic: a
    # margin-shaped match is still protected outright (never even
    # evaluated geometrically against the region); anything else falls
    # through to the same geometric relation as any other line, which
    # correctly excludes it when it is genuinely part of the diagram.
    if _is_marker_at_margin(line.text, line.x0, body_margin_x0):
        return False
    relation = compute_line_region_relation(line, region, own_key)
    return _text_consumption_decision(relation, region.is_small_formula) == "accepted"


def _position_key(page_number: int, y: float) -> tuple[int, float]:
    return (page_number, y)


def _find_alternative_starts(lines: list[Line]) -> dict[str, int] | None:
    """Right-to-left search for the A/B/C/D/E marker sequence.

    Returns a dict of letter -> index into ``lines``, or None if a full,
    strictly ordered A..E sequence could not be found (caller must then
    treat "alternatives not confidently located" as a review case, not
    guess at a partial split).
    """
    positions: dict[str, list[int]] = {letter: [] for letter in "ABCDE"}
    for index, line in enumerate(lines):
        match = _ALTERNATIVE_LINE_RE.match(line.text)
        if match:
            positions[match.group(1)].append(index)

    if not positions["E"]:
        return None
    e_index = positions["E"][-1]

    result: dict[str, int] = {"E": e_index}
    upper_bound = e_index
    for letter in ("D", "C", "B", "A"):
        candidates = [i for i in positions[letter] if i < upper_bound]
        if not candidates:
            return None
        result[letter] = candidates[-1]
        upper_bound = result[letter]
    return result


def _find_region_insertion_index(lines: list[Line], region: VisualRegion | DetectedTable) -> int:
    """Where would ``region`` sit if inserted into the already-ordered ``lines``?

    ``lines`` is assumed to already be in correct reading order (which, on a
    two-column page, is "all of the left column, then all of the right
    column" - NOT a pure y0 sort, see layout.py). A region is therefore
    placed right before the first line on its own page whose y0 is at or
    past the region's top edge, rather than by re-sorting everyone by y0
    (which would undo the column ordering and interleave text/figures from
    two different columns line-by-line). Works identically for a detected
    table (see tables.py) - both types expose the same ``page_number``/
    ``bbox`` shape this function actually uses.
    """
    for i, ln in enumerate(lines):
        if ln.page_number < region.page_number:
            continue
        if ln.page_number > region.page_number:
            return i
        if ln.y0 >= region.bbox[1]:
            return i
    return len(lines)


#: A monospace line whose *entire* text (after leading/trailing tab/space)
#: is a bare integer - a standalone printed line-number gutter entry, never
#: a real C statement (PROMPT Phase 1C section 8.1). Ambiguous on its own
#: (a lone bare-digit line could in principle be real content), so it is
#: only trusted once it recurs (see ``_GUTTER_MIN_STANDALONE_COUNT`) - in
#: this corpus, chrome.py's own bare-1-3-digit page-number rule already
#: removes most standalone gutter lines upstream, before assembler.py ever
#: sees them, so this branch mainly guards the case where it doesn't
#: (a 4+ digit line number, or a future corpus without that chrome rule).
_GUTTER_ONLY_RE = re.compile(r"^[\t ]*\d+[\t ]*$")
#: A monospace line whose text *starts* with a bare integer followed by
#: real whitespace and then further content - a line-number gutter fused
#: with its own code by PyMuPDF's line grouping (observed: Q20's row 11,
#: "\t11 \t int funcao2(...)" - see docs/decisions.md, "Phase 1C" ADR).
#: No real C statement starts with a standalone integer token followed by
#: whitespace and unrelated code, so this pattern is unambiguous on its
#: own and needs no recurrence to be trusted - unlike ``_GUTTER_ONLY_RE``,
#: it is stripped even when it is the only such line in the run (as it was
#: for Q20, where chrome.py had already removed every *other* gutter line
#: before this one - the only one PyMuPDF fused with real code - was ever
#: seen here).
_GUTTER_PREFIX_RE = re.compile(r"^[\t ]*\d+[\t ]+")
#: See ``_GUTTER_ONLY_RE`` - a lone bare-digit line is left alone; two or
#: more recurring ones look like a systematic gutter, not a coincidence.
_GUTTER_MIN_STANDALONE_COUNT = 2


def _strip_line_number_gutter(code_lines: list[Line]) -> list[Line]:
    """Remove a printed line-number gutter from a run of code ``Line``s.

    Two physical shapes are handled, both purely from geometry/text-shape,
    never from the specific numbers involved: (1) the common case, where
    the gutter number is already its own separate ``Line`` (dropped
    entirely); (2) a gutter number fused by PyMuPDF into the same line as
    the code that follows it (its numeric prefix is stripped, and the
    remainder's indentation is reconstructed from the *other*, unaffected
    lines' own established indent levels - never from the corrupted
    merged line's own x0, which would otherwise drag every line's
    reconstructed indentation off by the gutter's own width).
    """
    numeric_only_all = frozenset(ln for ln in code_lines if _GUTTER_ONLY_RE.match(ln.text))
    merged = frozenset(
        ln for ln in code_lines if ln not in numeric_only_all and _GUTTER_PREFIX_RE.match(ln.text)
    )
    numeric_only = (
        numeric_only_all if len(numeric_only_all) >= _GUTTER_MIN_STANDALONE_COUNT else frozenset()
    )
    if not numeric_only and not merged:
        return code_lines

    unaffected = [ln for ln in code_lines if ln not in numeric_only and ln not in merged]
    if not unaffected:
        return code_lines
    baseline_x0 = min(ln.x0 for ln in unaffected)

    result: list[Line] = []
    for ln in code_lines:
        if ln in numeric_only:
            continue
        if ln in merged:
            match = _GUTTER_PREFIX_RE.match(ln.text)
            assert match is not None
            remainder = ln.text[match.end() :]
            stripped = remainder.lstrip(" \t")
            leading_ws = len(remainder) - len(stripped)
            result.append(
                Line(
                    page_number=ln.page_number,
                    text=stripped,
                    x0=baseline_x0 + leading_ws * CODE_CHAR_WIDTH,
                    y0=ln.y0,
                    x1=ln.x1,
                    y1=ln.y1,
                    is_monospace=ln.is_monospace,
                    font_size=ln.font_size,
                )
            )
        else:
            result.append(ln)
    return result


def _render_code_lines(code_lines: list[Line]) -> str:
    """Render a run of monospace ``Line``s into fenced-code text.

    Indentation is reconstructed from each line's own x0 relative to the
    run's leftmost line (PROMPT section 7.3 item 5/6). Real blank lines
    within the listing are also preserved (item 8) - never invented, never
    collapsed: a genuine blank line's vertical pitch to its neighbours is a
    multiple of the run's own modal (most common) line pitch, so a
    pitch of roughly 2x the mode means exactly one blank line sat between
    the two source lines, 3x means two, and so on. A page's first blank
    line was observed being silently collapsed for D5's heapify() listing
    (the blank line between "int e, d, max, aux;" and "e = left(i);" on
    page 17) before this reconstruction - see docs/decisions.md, "Phase
    1C" ADR.
    """
    base_x0 = min(ln.x0 for ln in code_lines)
    pitches = [code_lines[i + 1].y0 - code_lines[i].y0 for i in range(len(code_lines) - 1)]
    modal_pitch = Counter(round(p) for p in pitches).most_common(1)[0][0] if pitches else 0

    rendered: list[str] = []
    for i, ln in enumerate(code_lines):
        if i > 0 and modal_pitch > 0:
            pitch = ln.y0 - code_lines[i - 1].y0
            blank_lines = round(pitch / modal_pitch) - 1
            rendered.extend([""] * max(0, blank_lines))
        indent = max(0, round((ln.x0 - base_x0) / CODE_CHAR_WIDTH))
        rendered.append(" " * indent + ln.text)
    return "\n".join(rendered)


def _build_statement_segments(
    lines: list[Line],
    regions: list[VisualRegion],
    tables: list[DetectedTable] | None = None,
    overrides: LayoutOverrideSet | None = None,
    pdf_sha256: str = "",
    own_key: str | None = None,
    body_margin_by_page: dict[int, float | None] | None = None,
    contextual_relation_gate: bool = False,
) -> tuple[list[StatementSegment], list[int], list[int]]:
    """Merge text lines, figure regions and tables into position-ordered segments.

    Text lines that fall inside a region's bbox, or that were consumed by a
    detected table (see tables.py), are dropped (their content is
    represented by the figure/table itself, not duplicated as scrambled
    inline text). Consecutive surviving lines are grouped into paragraphs
    using the vertical-gap heuristic; each region/table becomes its own
    segment at the point in the flow where it visually sits. Returns the
    segments plus the list of region indices and table indices that were
    actually placed (so the caller can tell whether every detected
    region/table ended up referenced).
    """
    tables = tables or []
    table_consumed = frozenset(ln for table in tables for ln in table.consumed_lines)

    insertions_at: dict[int, list[tuple[str, int]]] = {}
    for region_index, region in enumerate(regions):
        idx = _find_region_insertion_index(lines, region)
        insertions_at.setdefault(idx, []).append(("figure", region_index))
    for table_index, table in enumerate(tables):
        idx = _find_region_insertion_index(lines, table)
        insertions_at.setdefault(idx, []).append(("table", table_index))

    events: list[tuple[int, float, float, str, Line | int]] = []
    for i, ln in enumerate(lines):
        for event_kind, index in insertions_at.get(i, []):
            if event_kind == "figure":
                region = regions[index]
                events.append((region.page_number, region.bbox[1], region.bbox[3], "figure", index))
            else:
                table = tables[index]
                events.append((table.page_number, table.bbox[1], table.bbox[3], "table", index))
        events.append((ln.page_number, ln.y0, ln.y1, "line", ln))
    for event_kind, index in insertions_at.get(len(lines), []):
        if event_kind == "figure":
            region = regions[index]
            events.append((region.page_number, region.bbox[1], region.bbox[3], "figure", index))
        else:
            table = tables[index]
            events.append((table.page_number, table.bbox[1], table.bbox[3], "table", index))

    segments: list[StatementSegment] = []
    placed_regions: list[int] = []
    placed_tables: list[int] = []
    current_prose: list[str] = []
    current_code: list[Line] = []
    previous_end: tuple[int, float] | None = None

    def flush_prose() -> None:
        if current_prose:
            segments.append(TextSegment(text=" ".join(current_prose)))
            current_prose.clear()

    def flush_code() -> None:
        if current_code:
            gutter_stripped = _strip_line_number_gutter(current_code)
            segments.append(CodeSegment(text=_render_code_lines(gutter_stripped)))
            current_code.clear()

    def flush_all() -> None:
        flush_prose()
        flush_code()

    for page_number, y0, y1, kind, payload in events:
        if kind == "line":
            line = payload
            assert isinstance(line, Line)
            margin = (body_margin_by_page or {}).get(line.page_number)
            if any(
                _line_in_region(
                    line,
                    regions[i],
                    overrides,
                    pdf_sha256,
                    own_key,
                    margin,
                    contextual_relation_gate,
                )
                for i in range(len(regions))
            ):
                continue
            if line in table_consumed:
                continue
            gap_breaks_run = previous_end is not None and (
                previous_end[0] != page_number or (y0 - previous_end[1]) >= PARAGRAPH_GAP_THRESHOLD
            )
            if line.is_monospace:
                if current_prose or (gap_breaks_run and current_code):
                    flush_all()
                current_code.append(line)
            else:
                if current_code or (gap_breaks_run and current_prose):
                    flush_all()
                current_prose.append(line.text)
            previous_end = (page_number, y1)
        elif kind == "figure":
            event_region_index = payload
            assert isinstance(event_region_index, int)
            flush_all()
            segments.append(FigureSegment(region_index=event_region_index))
            placed_regions.append(event_region_index)
            previous_end = (page_number, y1)
        else:
            event_table_index = payload
            assert isinstance(event_table_index, int)
            flush_all()
            segments.append(TableSegment(table_index=event_table_index))
            placed_tables.append(event_table_index)
            previous_end = (page_number, y1)

    flush_all()
    return segments, placed_regions, placed_tables


def detect_broken_words(text: str) -> list[str]:
    """Return the suspicious ligature-artifact snippets found in ``text``, if any."""
    return [m.group(0) for m in _BROKEN_WORD_RE.finditer(text)]


def _strip_leading_marker(lines: list[Line]) -> list[Line]:
    """Remove the "QUESTAO [DISCURSIVA] N" marker text from a span's own
    marker line, wherever it falls in ``lines``.

    A ``QuestionSpan`` always starts at its own marker line (that's how
    boundary detection finds it - see boundaries.py), so it is real content,
    not chrome, and survives chrome filtering. Left in place it leaks into
    the rendered statement as a literal prefix (e.g. "QuEStãO 01 A chance
    de uma criança..."), redundant with both the Markdown "# Questão N"
    heading and the front matter's own ``question_number`` field.

    Normally the marker line is ``lines[0]`` - but a forward-reference
    transfer (reference_captions.py, PROMPT Phase 3E) can prepend a caption
    and its own anchored content that was printed *above* the marker on the
    page (e.g. 2008-b's "Figura para a questao 61", printed before "QUESTAO
    61" itself), pushing the real marker line past index 0. The marker is
    therefore searched for across the whole list rather than assumed to be
    first; ``_MARKER_PREFIX_RE`` is anchored at the start of a line's own
    text and specific enough (literal "questao" + digits) that no other
    line in this corpus - a caption included - matches it by coincidence.
    """
    for i, line in enumerate(lines):
        match = _MARKER_PREFIX_RE.match(line.text)
        if not match:
            continue
        remainder = line.text[match.end() :].strip()
        if not remainder:
            return lines[:i] + lines[i + 1 :]
        stripped = Line(
            page_number=line.page_number,
            text=remainder,
            x0=line.x0,
            y0=line.y0,
            x1=line.x1,
            y1=line.y1,
            is_monospace=line.is_monospace,
            font_size=line.font_size,
            spacing_corrections=line.spacing_corrections,
            label_corrections=line.label_corrections,
            symbol_corrections=line.symbol_corrections,
            fragment_merges=line.fragment_merges,
        )
        return lines[:i] + [stripped] + lines[i + 1 :]
    return lines


#: An alternative's own text is "empty" (nothing but the marker and
#: trailing punctuation survived) - the shape ``_attach_alternative_
#: formula_regions`` looks for, never a question id.
_EMPTY_ALTERNATIVE_TEXT_RE = re.compile(r"^[\s.,;:]*$")


def _is_alternative_formula_candidate(region: VisualRegion) -> bool:
    """True only for a region plausibly one alternative's own inline
    formula, never a statement-level diagram or grammar block that
    happens to geometrically overlap an alternative's own row (PROMPT
    Phase 2F: 2011 Q23's own grammar-productions region, y-range
    293.6-445.2, was found - by direct inspection of a first,
    size-checking-only implementation - to overlap alternatives A/B/C's
    own rows too, incorrectly attaching the *entire diagram* to each as
    if it were their own small formula).

    Keys off ``VisualRegion.is_small_formula`` (provenance: was this
    region built from the small-formula candidate pool at all -
    figures.py's own ``_is_small_formula_candidate``), never the region's
    own *current* bbox size - re-checking size after merging rejected
    2011 Q14's own legitimate case: 5 per-alternative formulas merge into
    one region spanning all 5 rows before this function ever sees them,
    and that merged bbox's own height comfortably exceeds
    ``SMALL_IMAGE_MAX_HEIGHT`` even though every one of its 5 constituent
    elements was small (a regression caught by
    ``test_assemble_question_indexes_an_inline_alternative_asset_correctly_alongside_a_statement_figure``
    - Q14's own alternatives all went back to empty ("A. .") until this
    was fixed to check provenance instead of size).
    """
    return region.is_small_formula


def _attach_alternative_formula_regions(
    alternatives: list[ExtractedAlternative],
    text_only_lines: list[Line],
    alt_bounds: list[int],
    candidate_regions: list[VisualRegion],
) -> tuple[list[VisualRegion], set[int]]:
    """Reattach a per-alternative formula image to an alternative whose own
    text is empty after its marker (PROMPT Phase 2E section 10).

    2011 Q14's own 5 alternatives are each *only* a small raster/vector
    boolean-algebra formula (e.g. "(x+z)y + x-ybar-zbar"), never real
    text - the alternative-marker line leaves nothing behind but a
    trailing period. Several such per-alternative formula candidates,
    sitting close together in Y (well within figures.py's own
    ``SMALL_IMAGE_Y_MERGE_TOLERANCE``), merge into *one* region spanning
    multiple alternatives' own rows, since the general merge pass has no
    notion of an alternative boundary between them - leaving every
    alternative's own text empty and the merged formula stranded as one
    undifferentiated statement-level figure.

    For each empty alternative, this slices the candidate region with
    the largest Y-overlap against that alternative's own row (from its
    own marker line down to the next alternative's, or the end of the
    text for the last one) into a new, narrower ``VisualRegion`` scoped
    to just that row - "crop the whole visual line" (PROMPT Phase 2E
    section 7's own fallback guidance), never an attempt to reconstruct
    the formula's own components. Returns the new per-alternative
    regions (mutating each claimed alternative's own
    ``figure_region_index`` in place to point into this returned list)
    and the set of ``id()``s of original candidate regions that were
    sliced from, so the caller can exclude them from the statement's own
    figure placement - otherwise the same formula would render twice,
    once merged at the top of the statement and once per alternative.

    Triggered only by this geometric/textual shape - an alternative with
    no real text of its own, and a candidate region overlapping its
    row - never by question id, so this is inert for every alternative
    that has real text (the overwhelming majority of this corpus).
    """
    empty_indices = [
        i for i, alt in enumerate(alternatives) if _EMPTY_ALTERNATIVE_TEXT_RE.match(alt.text)
    ]
    if not empty_indices:
        return [], set()

    extra_regions: list[VisualRegion] = []
    consumed_ids: set[int] = set()
    for i in empty_indices:
        start_line = text_only_lines[alt_bounds[i]]
        next_index = alt_bounds[i + 1] if i + 1 < len(alt_bounds) else len(text_only_lines)
        row_y0 = start_line.y0
        row_y1 = (
            text_only_lines[next_index].y0
            if next_index < len(text_only_lines)
            else start_line.y1 + 1000.0  # last alternative: no next-line bound on this page
        )

        def _y_overlap(region: VisualRegion, y0: float = row_y0, y1: float = row_y1) -> float:
            return min(region.bbox[3], y1) - max(region.bbox[1], y0)

        candidates = [
            r
            for r in candidate_regions
            if r.page_number == start_line.page_number
            and _is_alternative_formula_candidate(r)
            and _y_overlap(r) > 0
        ]
        if not candidates:
            continue
        best = max(candidates, key=_y_overlap)
        slice_bbox = (
            best.bbox[0],
            max(best.bbox[1], row_y0),
            best.bbox[2],
            min(best.bbox[3], row_y1),
        )
        if slice_bbox[3] - slice_bbox[1] <= 0:
            continue
        extra_regions.append(
            VisualRegion(
                page_number=start_line.page_number,
                bbox=slice_bbox,
                element_count=1,
                has_raster_image=best.has_raster_image,
                owner_key=best.owner_key,
                owner_x_bounds=best.owner_x_bounds,
                is_small_formula=best.is_small_formula,
            )
        )
        consumed_ids.add(id(best))
        alternatives[i].figure_region_index = len(extra_regions) - 1
    return extra_regions, consumed_ids


#: How close (points) two items' own Y-ranges must overlap to be treated
#: as sitting on the same visual row, for ``_merge_alternative_reading_order``
#: - a small inline formula image often has a slightly different own y0
#: than the surrounding text (different font metrics/baseline), so a
#: region is matched to a row by *overlap*, never by an exact y0 match.
_SAME_ROW_OVERLAP_MIN = 0.0


def _merge_alternative_reading_order(
    lines: list[Line], regions: list[VisualRegion]
) -> list[Line | VisualRegion]:
    """Merge one alternative's own lines and any small-formula regions
    overlapping its row into a single reading-order sequence (PROMPT Phase
    2F section 7).

    ``extract_document_lines`` itself already splits one *visual* line into
    several ``Line`` objects wherever an inline image creates a horizontal
    gap (2011 Q23's own alternative D: "...linguagem sobre" / [Sigma] /
    "em que...", three separate ``Line``s at nearly - never exactly - the
    same y0, since an italic math glyph's own baseline metrics differ
    slightly from the surrounding body font). A region is anchored to
    whichever line's own Y-range it overlaps (never its own y0, which can
    sit slightly off from the text it visually shares a row with) and
    ordered just past that line's own x1, so it sorts between same-row
    text correctly; a region with no such overlap (Q23's own alternative
    E: the formula sits on its own row, between one text line above and a
    trailing "." on the same row below) is ordered by its own bbox
    position relative to the surrounding lines instead.
    """
    keyed: list[tuple[float, float, Line | VisualRegion]] = [(ln.y0, ln.x0, ln) for ln in lines]
    for region in regions:
        same_row = [
            ln
            for ln in lines
            if min(ln.y1, region.bbox[3]) - max(ln.y0, region.bbox[1]) > _SAME_ROW_OVERLAP_MIN
        ]
        if same_row:
            anchor = min(same_row, key=lambda ln: ln.y0)
            keyed.append((anchor.y0, region.bbox[0], region))
        else:
            keyed.append((region.bbox[1], region.bbox[0], region))
    keyed.sort(key=lambda t: (t[0], t[1]))
    return [item for _, _, item in keyed]


def _flush_alternative_text(
    text_buffer: list[str], segments: list[TextSegment | FigureSegment]
) -> list[str]:
    """Join and append ``text_buffer`` as one ``TextSegment`` (mutating
    ``segments`` in place), then return a fresh, empty buffer.

    A plain module-level helper, not a closure over the caller's own
    loop-local ``text_buffer``/``segments`` (ruff B023: a nested function
    redefined every outer-loop iteration is safe here in practice, since
    each iteration's own closure is used and discarded before the next
    begins, but explicit parameters are clearer and avoid the lint
    entirely).
    """
    if text_buffer:
        joined = " ".join(text_buffer).strip()
        if joined:
            segments.append(TextSegment(text=joined))
    return []


def _attach_alternative_inline_segments(
    alternatives: list[ExtractedAlternative],
    text_only_lines: list[Line],
    alt_bounds: list[int],
    candidate_regions: list[VisualRegion],
) -> tuple[list[VisualRegion], set[int]]:
    """Build an ordered text/asset segment list for an alternative whose
    own text is real but interleaves one or more small inline formula
    images (PROMPT Phase 2F section 7) - e.g. 2011 Q23's own alternatives
    D ("...sobre <Sigma> em que...") and E ("...regular <regex>.").

    Distinct from ``_attach_alternative_formula_regions`` (Phase 2E),
    which only handles an alternative with *no* real text at all (2011
    Q14's own shape) - this one is skipped entirely for an alternative
    that mechanism already claimed (``figure_region_index is not None``),
    and does nothing when no candidate region overlaps the alternative's
    own row (the overwhelming majority of alternatives in this corpus),
    leaving ``segments`` as ``None`` and ``text`` as the sole
    representation, unchanged.
    """
    extra_regions: list[VisualRegion] = []
    consumed_ids: set[int] = set()
    for i, alt in enumerate(alternatives):
        if alt.figure_region_index is not None:
            continue
        start_line = text_only_lines[alt_bounds[i]]
        next_index = alt_bounds[i + 1] if i + 1 < len(alt_bounds) else len(text_only_lines)
        row_y0 = start_line.y0
        row_y1 = (
            text_only_lines[next_index].y0
            if next_index < len(text_only_lines)
            else start_line.y1 + 1000.0
        )
        group = text_only_lines[alt_bounds[i] : next_index]

        def _y_overlap(region: VisualRegion, y0: float = row_y0, y1: float = row_y1) -> float:
            return min(region.bbox[3], y1) - max(region.bbox[1], y0)

        own_regions = [
            r
            for r in candidate_regions
            if r.page_number == start_line.page_number
            and _is_alternative_formula_candidate(r)
            and _y_overlap(r) > 0
        ]
        if not own_regions:
            continue

        ordered = _merge_alternative_reading_order(group, own_regions)
        segments: list[TextSegment | FigureSegment] = []
        text_buffer: list[str] = []

        for index, item in enumerate(ordered):
            if isinstance(item, VisualRegion):
                text_buffer = _flush_alternative_text(text_buffer, segments)
                extra_regions.append(item)
                consumed_ids.add(id(item))
                segments.append(FigureSegment(region_index=len(extra_regions) - 1))
            else:
                raw = item.text
                if index == 0:
                    match = _ALTERNATIVE_LINE_RE.match(raw)
                    raw = (match.group(2) or "").strip() if match is not None else raw.strip()
                else:
                    raw = raw.strip()
                if raw:
                    text_buffer.append(raw)
        _flush_alternative_text(text_buffer, segments)

        if any(isinstance(seg, FigureSegment) for seg in segments):
            alt.segments = segments
    return extra_regions, consumed_ids


def assemble_question(
    span: QuestionSpan,
    doc: pymupdf.Document,
    decorative_baseline: frozenset[tuple[int, int, int, int]],
    overrides: LayoutOverrideSet | None = None,
    pdf_sha256: str = "",
    question_regions_by_page: dict[int, list[QuestionRegion]] | None = None,
    region_merge_x_tolerance: float = UNBOUNDED_MERGE_X_TOLERANCE,
    caption_font_size_gate: bool = False,
    reference_transfer_target_keys: frozenset[str] = frozenset(),
    owner_exclusion_gate: bool = False,
    contextual_relation_gate: bool = False,
    fragment_reconstruction_gate: bool = False,
) -> ExtractedQuestion:
    warnings: list[str] = []

    # A coarse, not-yet-final pass: only used to bound the figure-region
    # search per page and to locate a preliminary alternatives cutoff (see
    # below) - both tolerant of the small differences the later table-aware
    # rescue pass (further down) can introduce, so there is no need to
    # duplicate that rescue logic here too.
    coarse_lines = [ln for ln in span.lines if not is_chrome_line(ln.text)]

    pages_in_span = sorted({ln.page_number for ln in coarse_lines}) or [span.start_page]

    # Region detection is per-page, but two different questions can share a
    # page (e.g. Q34 ends and Q35 begins on the same page 43). Without a
    # y-bound, a figure belonging to the *other* question on that shared
    # page would be wrongly attached here. Bound candidate regions to the
    # vertical range this span's own content_lines actually occupy on each
    # page (with a small tolerance for a figure sitting just outside its
    # nearest text line). Y alone is not sufficient on a two-column page,
    # though: two questions in different columns of the same page can
    # still have overlapping Y-ranges (e.g. both starting near the top of
    # their own column), so a left-column figure could satisfy a
    # right-column question's Y-bounds purely by coincidence (2011 unified
    # booklet, page 11: Q14's own Venn diagram - left column - was also
    # attached to Q15 - right column, no figure of its own - because both
    # questions' Y-ranges overlap near the top of the page). Also require
    # the region's own X-range to overlap this span's X-range.
    page_y_bounds: dict[int, tuple[float, float]] = {}
    page_x_bounds: dict[int, tuple[float, float]] = {}
    for ln in coarse_lines:
        lo, hi = page_y_bounds.get(ln.page_number, (ln.y0, ln.y1))
        page_y_bounds[ln.page_number] = (min(lo, ln.y0), max(hi, ln.y1))
        xlo, xhi = page_x_bounds.get(ln.page_number, (ln.x0, ln.x1))
        page_x_bounds[ln.page_number] = (min(xlo, ln.x0), max(xhi, ln.x1))
    y_tolerance = 15.0
    #: Smaller than y_tolerance: this corpus's real column gaps run ~9-12pt
    #: (e.g. page 5: 284.7 to 296.7), narrower than 15pt would reject, which
    #: let a region hugging its own column's edge bridge into the
    #: neighboring column's span (2011 unified booklet, Q6/Q7 sharing page
    #: 5: Q6's own infographic - x1=284.7 - was also attached to Q7 -
    #: x0=296.7 - a 12pt gap 15pt tolerance closed but a real column
    #: boundary never should). 5pt keeps slack for a figure whose bbox sits
    #: just outside its own span's text lines without reopening that gap.
    x_tolerance = 5.0

    own_key = question_key(span)

    # Computed once per page, reused by ``_line_in_region`` (via
    # ``_build_statement_segments``) to tell a genuine alternative marker
    # (sits at this margin) from a diagram-internal label that merely
    # looks like one (PROMPT Phase 3G, "Cluster C") - see
    # ``figures._is_marker_at_margin``, the same evidence already used to
    # protect a real marker from label-absorption growth. Falls back to
    # the text-length-based margin (``dominant_left_margin_by_text_length``)
    # when the width-based one finds nothing - a page whose real body
    # column is itself narrow (e.g. Q29's own side-panel-grammar-
    # productions page) has no line wide enough to agree on a margin by
    # width alone, which would otherwise leave every marker-shaped line
    # unconditionally protected again (the exact blanket exemption Cluster
    # C exists to narrow) purely because no margin evidence was available.
    def _page_body_margin(page_number: int) -> float | None:
        page_lines = extract_page_lines(
            doc[page_number - 1],
            page_number,
            fragment_reconstruction_gate=fragment_reconstruction_gate,
        )
        margin = _dominant_left_margin(page_lines)
        return margin if margin is not None else dominant_left_margin_by_text_length(page_lines)

    body_margin_by_page: dict[int, float | None] = {
        page_number: _page_body_margin(page_number) for page_number in pages_in_span
    }
    regions: list[VisualRegion] = []
    for page_number in pages_in_span:
        page_regions = detect_visual_regions(
            doc,
            page_number,
            decorative_baseline,
            region_merge_x_tolerance=region_merge_x_tolerance,
            caption_font_size_gate=caption_font_size_gate,
            overrides=overrides,
            pdf_sha256=pdf_sha256,
            question_regions=(question_regions_by_page or {}).get(page_number),
            fragment_reconstruction_gate=fragment_reconstruction_gate,
        )
        bounds = page_y_bounds.get(page_number)
        x_bounds = page_x_bounds.get(page_number)
        if bounds is None or x_bounds is None:
            continue
        y_min, y_max = bounds[0] - y_tolerance, bounds[1] + y_tolerance
        x_min, x_max = x_bounds[0] - x_tolerance, x_bounds[1] + x_tolerance
        # This y/x bounding box is the *only* inclusion test for every span
        # that never received a forward-reference transfer (every 2011/2021
        # span, and every 2008-b span except a transfer's own target) -
        # completely unchanged from before Phase 3E. It was never
        # reconciled with each region's own ``owner_key`` (computed by
        # figures.py from the same QuestionRegion geometry - see
        # ownership.py) because a span's own coarse bounding box never
        # needed to grow past what this heuristic already tolerates.
        #
        # A forward-reference transfer (reference_captions.py) can pull a
        # caption + its own anchored diagram from *before* a question's own
        # marker into its span, growing that span's own bounding box far
        # beyond what a fixed 15pt/5pt tolerance expects in either
        # direction: wide enough to spuriously overlap a neighboring
        # question's own owned region (2008-b Q61/Q63, sharing page 27:
        # Q61's own widened bbox overlapped Q63's own unrelated ER-diagram
        # region), and tall enough that the transferred diagram's own
        # region can start a few points above the transferred caption's own
        # topmost line - just past this tolerance - despite being Q61's own
        # correctly-owned region. Trusting ``owner_key`` outright would
        # over-correct: ``find_owner`` also has a nearest-in-column
        # fallback with no distance cap, which reaches for a span's own key
        # even when a candidate shares nothing real with it (e.g. a
        # per-page header/rule fragment invisible to
        # ``compute_decorative_baseline`` - that function only tracks
        # recurring *drawings*, never raster images - nearest-matched to
        # whichever question starts that column, then grown/label-absorbed
        # into that question's own real statement text - confirmed via
        # full regeneration on 2011's own Q4/Q25/Q39, previously excluded
        # by this exact y/x tolerance for reasons unrelated to ownership).
        # So this relaxation only ever applies to a span that was itself an
        # accepted transfer's own target - every other span, including
        # every 2011/2021 span (never a transfer target at all) and every
        # other 2008-b span, keeps exactly the original heuristic below.
        if own_key in reference_transfer_target_keys:
            own_region = next(
                (
                    r
                    for r in (question_regions_by_page or {}).get(page_number, [])
                    if r.question_key == own_key
                ),
                None,
            )

            def _overlaps_own_region(
                bbox: tuple[float, float, float, float],
                _own_region: QuestionRegion | None = own_region,
            ) -> bool:
                if _own_region is None:
                    return False
                return (
                    bbox[0] < _own_region.x1
                    and bbox[2] > _own_region.x0
                    and bbox[1] < _own_region.y1
                    and bbox[3] > _own_region.y0
                )

            regions.extend(
                r for r in page_regions if r.owner_key == own_key and _overlaps_own_region(r.bbox)
            )
        else:
            # The y/x tolerance alone has no concept of ownership - it was
            # never reconciled with ``owner_key`` because a span's own
            # coarse bounding box rarely grew wide enough to spuriously
            # reach a genuinely different question's own owned region. It
            # can: a real alternative that overflows into the next page
            # column (2008-b Q13's own alternative E, printed at the very
            # top of the right column because it did not fit below D in
            # the left column) widens this span's own page_y_bounds/
            # page_x_bounds enough to trivially satisfy the old tolerance
            # for a neighboring question's own owned region (Q12's own
            # control-flow-graph diagram, `owner=objective-12`, published
            # as Q13's own figure-01.png - confirmed byte-identical to
            # Q12's - despite the two questions sharing nothing).
            #
            # ``owner_exclusion_gate`` (PROMPT Phase 3F, opt-in - see
            # ``ExamStructureProfile``) rejects a region explicitly owned
            # by a *different* question outright, regardless of
            # bounding-box overlap - this can only ever remove a
            # previously wrongly-admitted region, never add one, since it
            # is purely an additional restriction on top of the tolerance
            # below. It is not the unconditional default because enabling
            # it for every booklet changed 2011's own Q34 (a genuinely
            # unowned region was, before this gate, counted as Q34's own
            # candidate by y/x proximity alone, changing which structural
            # warning fires) - see ``ExamStructureProfile.owner_exclusion_gate``.
            regions.extend(
                r
                for r in page_regions
                if (not owner_exclusion_gate or r.owner_key is None or r.owner_key == own_key)
                and y_min <= r.bbox[1] <= y_max
                and r.bbox[0] <= x_max
                and r.bbox[2] >= x_min
            )

    # A figure region can grow (via label absorption, see figures.py) far
    # enough to overlap the *start* of the alternatives section below the
    # statement. ``_line_in_region`` already protects an alternative's own
    # marker line (matches ``_ALTERNATIVE_LINE_RE``), but a multi-line
    # alternative's continuation lines (e.g. Q22's relational-schema
    # alternatives, each spanning 2-5 lines) carry no such marker and were
    # observed being silently swallowed by the DER diagram's region,
    # dropping most of alternative A's own text (Phase 1B audit finding,
    # see docs/decisions.md). Alternative content can never legitimately be
    # "inside" a statement figure, so once the alternatives section is
    # known to start (found here on the *unfiltered* lines, before any
    # region exclusion), every line from that point on is exempted from
    # region filtering entirely.
    alt_section_start: tuple[int, float] | None = None
    if span.kind == QuestionKind.OBJECTIVE:
        preliminary_starts = _find_alternative_starts(coarse_lines)
        if preliminary_starts is not None:
            a_line = coarse_lines[preliminary_starts["A"]]
            alt_section_start = _position_key(a_line.page_number, a_line.y0)

    def _in_alternatives_section(ln: Line) -> bool:
        return alt_section_start is not None and _position_key(ln.page_number, ln.y0) >= (
            alt_section_start
        )

    # Table detection (PROMPT Phase 1C section 5) runs on the *raw*,
    # pre-chrome span lines (minus anything already claimed by a figure
    # region) - not on the already chrome-filtered ``coarse_lines``. A
    # genuine table's own short numeric cells (e.g. D3's "1 2 3 4 5 6"
    # formula-numbering row) are, by *text* alone, indistinguishable from a
    # bare running page number or a "rascunho" scratch-margin ruler digit
    # (chrome.py's own evidence-based patterns for those - see
    # docs/decisions.md, "Phase 1C" ADR); the only thing that actually
    # tells them apart is that a table cell is part of a real, multi-row,
    # multi-column geometric grid alongside other substantial content,
    # which chrome furniture never is. So detection runs first, against
    # the wider raw candidate set, and any line it consumes is exempted
    # from chrome filtering below; every bare number that is *not* part of
    # a detected table (running page numbers, the rascunho ruler, an
    # isolated stray digit) is filtered exactly as before Phase 1C.
    def _line_region_excluded(ln: Line) -> bool:
        margin = body_margin_by_page.get(ln.page_number)
        return any(
            _line_in_region(ln, r, overrides, pdf_sha256, own_key, margin, contextual_relation_gate)
            for r in regions
        )

    raw_candidate_lines = [ln for ln in span.lines if not _line_region_excluded(ln)]
    detected_tables = detect_tables(raw_candidate_lines)
    table_consumed_lines = frozenset(ln for t in detected_tables for ln in t.consumed_lines)

    content_lines = _strip_leading_marker(
        [ln for ln in span.lines if ln in table_consumed_lines or not is_chrome_line(ln.text)]
    )

    text_only_lines = [
        ln
        for ln in content_lines
        if _in_alternatives_section(ln)
        or (not _line_region_excluded(ln) and ln not in table_consumed_lines)
    ]

    alternatives: list[ExtractedAlternative] = []
    statement_lines = content_lines
    statement_regions = regions
    statement_tables = detected_tables
    alt_figure_regions: list[VisualRegion] = []
    consumed_ids: set[int] = set()

    if span.kind == QuestionKind.OBJECTIVE:
        starts = _find_alternative_starts(text_only_lines)
        if starts is None:
            warnings.append(
                "could not locate a complete, strictly ordered A-E alternative sequence; "
                "treating entire span as statement"
            )
        else:
            cutoff_line = text_only_lines[starts["A"]]
            cutoff_key = _position_key(cutoff_line.page_number, cutoff_line.y0)
            statement_lines = [
                ln for ln in content_lines if _position_key(ln.page_number, ln.y0) < cutoff_key
            ]
            statement_regions = [
                r for r in regions if _position_key(r.page_number, r.bbox[1]) < cutoff_key
            ]
            statement_tables = [
                t for t in detected_tables if _position_key(t.page_number, t.bbox[1]) < cutoff_key
            ]

            ordered_letters = ["A", "B", "C", "D", "E"]
            alt_bounds = [starts[letter] for letter in ordered_letters] + [len(text_only_lines)]
            for i, letter in enumerate(ordered_letters):
                group = text_only_lines[alt_bounds[i] : alt_bounds[i + 1]]
                if not group:
                    warnings.append(f"alternative {letter} has no text")
                    continue
                first_match = _ALTERNATIVE_LINE_RE.match(group[0].text)
                assert first_match is not None  # guaranteed by _find_alternative_starts
                first_text = (first_match.group(2) or "").strip()
                rest_text = " ".join(ln.text.strip() for ln in group[1:])
                full_text = f"{first_text} {rest_text}".strip() if rest_text else first_text
                alternatives.append(ExtractedAlternative(letter=letter, text=full_text))

            alt_figure_regions, consumed_ids = _attach_alternative_formula_regions(
                alternatives, text_only_lines, alt_bounds, regions
            )

            # A second, distinct pattern (PROMPT Phase 2F section 7): an
            # alternative with *real* text that also interleaves one or
            # more small formula images (2011 Q23's own D/E) - skipped
            # entirely for any alternative the wholly-empty mechanism
            # above already claimed. Its own region indices are 0-based
            # within its own returned list, so they are offset past
            # alt_figure_regions's own count before the two lists merge.
            inline_regions, inline_consumed_ids = _attach_alternative_inline_segments(
                alternatives, text_only_lines, alt_bounds, regions
            )
            if inline_regions:
                base = len(alt_figure_regions)
                for alt in alternatives:
                    if alt.segments is not None:
                        alt.segments = [
                            FigureSegment(region_index=seg.region_index + base)
                            if isinstance(seg, FigureSegment)
                            else seg
                            for seg in alt.segments
                        ]
                alt_figure_regions = alt_figure_regions + inline_regions
                consumed_ids = consumed_ids | inline_consumed_ids

            if alt_figure_regions:
                statement_regions = [r for r in statement_regions if id(r) not in consumed_ids]

    segments, placed_region_indices, placed_table_indices = _build_statement_segments(
        statement_lines,
        statement_regions,
        statement_tables,
        overrides,
        pdf_sha256,
        own_key,
        body_margin_by_page,
        contextual_relation_gate,
    )

    # Computed against the pre-attachment statement_regions/consumed_ids
    # (PROMPT Phase 2E section 10): a region reattached to an alternative
    # was never meant to land in the statement flow, and one consumed by
    # that attachment was deliberately replaced by per-alternative slices,
    # not lost - neither is a real "could not place"/"dropped" finding.
    unplaced = set(range(len(statement_regions))) - set(placed_region_indices)
    if unplaced:
        warnings.append(
            f"{len(unplaced)} detected figure region(s) could not be placed in the statement flow"
        )

    if alt_figure_regions:
        base_index = len(statement_regions)
        for alt in alternatives:
            if alt.figure_region_index is not None:
                alt.figure_region_index += base_index
            if alt.segments is not None:
                alt.segments = [
                    FigureSegment(region_index=seg.region_index + base_index)
                    if isinstance(seg, FigureSegment)
                    else seg
                    for seg in alt.segments
                ]
        statement_regions = statement_regions + alt_figure_regions

    unplaced_tables = set(range(len(statement_tables))) - set(placed_table_indices)
    if unplaced_tables:
        warnings.append(
            f"{len(unplaced_tables)} detected table(s) could not be placed in the statement flow"
        )

    plain_text = "\n\n".join(seg.text for seg in segments if isinstance(seg, TextSegment))
    broken = detect_broken_words(plain_text)
    for alt in alternatives:
        broken.extend(detect_broken_words(alt.text))
    if broken:
        warnings.append(f"possible ligature/word-break artifact(s) detected: {broken}")

    if not plain_text.strip():
        warnings.append("empty statement after chrome/figure filtering")

    if span.kind == QuestionKind.OBJECTIVE and len(alternatives) not in (0, 5):
        warnings.append(f"expected 5 alternatives, found {len(alternatives)}")

    # A region consumed by an alternative attachment (PROMPT Phase 2E
    # section 10) was deliberately replaced by per-alternative slices, not
    # lost - excluded here the same way it is from the "unplaced" check
    # above.
    dropped_regions = [
        r for r in regions if r not in statement_regions and id(r) not in consumed_ids
    ]
    if dropped_regions:
        warnings.append(
            f"{len(dropped_regions)} figure region(s) fell after the alternatives cutoff "
            "and were excluded from the statement (unexpected layout - needs review)"
        )

    dropped_tables = [t for t in detected_tables if t not in statement_tables]
    if dropped_tables:
        warnings.append(
            f"{len(dropped_tables)} detected table(s) fell after the alternatives cutoff "
            "and were excluded from the statement (unexpected layout - needs review)"
        )

    spacing_corrections = [c for ln in content_lines for c in ln.spacing_corrections]
    label_corrections = [c for ln in content_lines for c in ln.label_corrections]
    symbol_corrections = [c for ln in content_lines for c in ln.symbol_corrections]
    fragment_merges = [c for ln in content_lines for c in ln.fragment_merges]

    return ExtractedQuestion(
        kind=span.kind,
        number=span.number,
        start_page=span.start_page,
        end_page=span.end_page,
        statement_segments=segments,
        alternatives=alternatives,
        figure_regions=statement_regions,
        tables=statement_tables,
        warnings=warnings,
        spacing_corrections=spacing_corrections,
        label_corrections=label_corrections,
        symbol_corrections=symbol_corrections,
        fragment_merges=fragment_merges,
    )
