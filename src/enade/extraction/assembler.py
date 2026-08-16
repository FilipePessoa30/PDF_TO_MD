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

import pymupdf

from enade.extraction.boundaries import QuestionKind, QuestionSpan
from enade.extraction.chrome import is_chrome_line
from enade.extraction.figures import VisualRegion, detect_visual_regions
from enade.extraction.label_normalization import LabelCorrection
from enade.extraction.layout import Line
from enade.extraction.layout_overrides import LayoutOverrideSet
from enade.extraction.ownership import QuestionRegion
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

    @property
    def plain_statement(self) -> str:
        """Statement text with figures elided - for quality checks, not rendering."""
        return "\n\n".join(
            seg.text
            for seg in self.statement_segments
            if isinstance(seg, TextSegment | CodeSegment)
        )


def _line_in_region(
    line: Line,
    region: VisualRegion,
    overrides: LayoutOverrideSet | None = None,
    pdf_sha256: str = "",
) -> bool:
    # An alternative marker line is never figure-interior, no matter how
    # tight the vertical spacing is on this particular page (observed: on
    # a densely-laid-out DER diagram question, alternative A's marker sits
    # only ~3pt below the diagram's own vector bounding box - well inside
    # a naive geometric containment test). Alternative-boundary detection
    # must take precedence over figure-region geometry, or the "A" marker
    # silently disappears and the whole alternative sequence breaks.
    if _ALTERNATIVE_LINE_RE.match(line.text):
        return False
    if line.page_number != region.page_number:
        return False
    if overrides is not None and overrides.protects_from_region_membership(
        pdf_sha256, line.page_number, line.bbox
    ):
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
            if any(
                _line_in_region(line, regions[i], overrides, pdf_sha256)
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
    """Remove the "QUESTAO [DISCURSIVA] N" marker text from a span's first line.

    A ``QuestionSpan`` always starts at its own marker line (that's how
    boundary detection finds it - see boundaries.py), so it is real content,
    not chrome, and survives chrome filtering. Left in place it leaks into
    the rendered statement as a literal prefix (e.g. "QuEStãO 01 A chance
    de uma criança..."), redundant with both the Markdown "# Questão N"
    heading and the front matter's own ``question_number`` field.
    """
    if not lines:
        return lines
    first = lines[0]
    match = _MARKER_PREFIX_RE.match(first.text)
    if not match:
        return lines
    remainder = first.text[match.end() :].strip()
    if not remainder:
        return lines[1:]
    stripped_first = Line(
        page_number=first.page_number,
        text=remainder,
        x0=first.x0,
        y0=first.y0,
        x1=first.x1,
        y1=first.y1,
        is_monospace=first.is_monospace,
        spacing_corrections=first.spacing_corrections,
        label_corrections=first.label_corrections,
        symbol_corrections=first.symbol_corrections,
    )
    return [stripped_first, *lines[1:]]


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

    regions: list[VisualRegion] = []
    for page_number in pages_in_span:
        page_regions = detect_visual_regions(
            doc,
            page_number,
            decorative_baseline,
            overrides=overrides,
            pdf_sha256=pdf_sha256,
            question_regions=(question_regions_by_page or {}).get(page_number),
        )
        bounds = page_y_bounds.get(page_number)
        x_bounds = page_x_bounds.get(page_number)
        if bounds is None or x_bounds is None:
            continue
        y_min, y_max = bounds[0] - y_tolerance, bounds[1] + y_tolerance
        x_min, x_max = x_bounds[0] - x_tolerance, x_bounds[1] + x_tolerance
        regions.extend(
            r
            for r in page_regions
            if y_min <= r.bbox[1] <= y_max and r.bbox[0] <= x_max and r.bbox[2] >= x_min
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
    raw_candidate_lines = [
        ln
        for ln in span.lines
        if not any(_line_in_region(ln, r, overrides, pdf_sha256) for r in regions)
    ]
    detected_tables = detect_tables(raw_candidate_lines)
    table_consumed_lines = frozenset(ln for t in detected_tables for ln in t.consumed_lines)

    content_lines = _strip_leading_marker(
        [ln for ln in span.lines if ln in table_consumed_lines or not is_chrome_line(ln.text)]
    )

    text_only_lines = [
        ln
        for ln in content_lines
        if _in_alternatives_section(ln)
        or (
            not any(_line_in_region(ln, r, overrides, pdf_sha256) for r in regions)
            and ln not in table_consumed_lines
        )
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
        statement_lines, statement_regions, statement_tables, overrides, pdf_sha256
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
    )
