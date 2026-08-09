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
from dataclasses import dataclass, field

import pymupdf

from enade.extraction.boundaries import QuestionKind, QuestionSpan
from enade.extraction.chrome import is_chrome_line
from enade.extraction.figures import VisualRegion, detect_visual_regions
from enade.extraction.label_normalization import LabelCorrection
from enade.extraction.layout import Line
from enade.extraction.spacing import SpacingCorrection

_ALTERNATIVE_LINE_RE = re.compile(r"^([A-E])[\t ](.*)$")
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
#: Approximate width (points) of one monospace character, used only to
#: reconstruct relative indentation for preserved code/pseudocode blocks.
CODE_CHAR_WIDTH = 6.0
#: Matches the same "QUESTAO [DISCURSIVA] N" marker boundaries.py uses to
#: find a span's start - kept as its own pattern (rather than imported)
#: because it is applied differently here: stripped as a *prefix* from the
#: span's own first line, not searched for across a whole document.
_MARKER_PREFIX_RE = re.compile(r"(?i)^quest[aã]o\s+(discursiva\s+)?0*\d+\b[.:\s]*")


@dataclass
class ExtractedAlternative:
    letter: str
    text: str


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


StatementSegment = TextSegment | CodeSegment | FigureSegment


@dataclass
class ExtractedQuestion:
    kind: QuestionKind
    number: int
    start_page: int
    end_page: int
    statement_segments: list[StatementSegment]
    alternatives: list[ExtractedAlternative] = field(default_factory=list)
    figure_regions: list[VisualRegion] = field(default_factory=list)
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


def _line_in_region(line: Line, region: VisualRegion) -> bool:
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
    return (region.bbox[1] - REGION_Y_PADDING) <= line.y0 <= (region.bbox[3] + REGION_Y_PADDING)


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


def _find_region_insertion_index(lines: list[Line], region: VisualRegion) -> int:
    """Where would ``region`` sit if inserted into the already-ordered ``lines``?

    ``lines`` is assumed to already be in correct reading order (which, on a
    two-column page, is "all of the left column, then all of the right
    column" - NOT a pure y0 sort, see layout.py). A region is therefore
    placed right before the first line on its own page whose y0 is at or
    past the region's top edge, rather than by re-sorting everyone by y0
    (which would undo the column ordering and interleave text/figures from
    two different columns line-by-line).
    """
    for i, ln in enumerate(lines):
        if ln.page_number < region.page_number:
            continue
        if ln.page_number > region.page_number:
            return i
        if ln.y0 >= region.bbox[1]:
            return i
    return len(lines)


def _build_statement_segments(
    lines: list[Line], regions: list[VisualRegion]
) -> tuple[list[StatementSegment], list[int]]:
    """Merge text lines and figure regions into position-ordered segments.

    Text lines that fall inside a region's bbox are dropped (their content
    is represented by the figure itself, not duplicated as scrambled inline
    labels). Consecutive surviving lines are grouped into paragraphs using
    the vertical-gap heuristic; each region becomes its own segment at the
    point in the flow where it visually sits. Returns the segments plus the
    list of region indices that were actually placed (so the caller can
    tell whether every detected region ended up referenced).
    """
    insertions_at: dict[int, list[int]] = {}
    for region_index, region in enumerate(regions):
        idx = _find_region_insertion_index(lines, region)
        insertions_at.setdefault(idx, []).append(region_index)

    events: list[tuple[int, float, float, str, Line | int]] = []
    for i, ln in enumerate(lines):
        for region_index in insertions_at.get(i, []):
            region = regions[region_index]
            events.append(
                (region.page_number, region.bbox[1], region.bbox[3], "figure", region_index)
            )
        events.append((ln.page_number, ln.y0, ln.y1, "line", ln))
    for region_index in insertions_at.get(len(lines), []):
        region = regions[region_index]
        events.append((region.page_number, region.bbox[1], region.bbox[3], "figure", region_index))

    segments: list[StatementSegment] = []
    placed_regions: list[int] = []
    current_prose: list[str] = []
    current_code: list[Line] = []
    previous_end: tuple[int, float] | None = None

    def flush_prose() -> None:
        if current_prose:
            segments.append(TextSegment(text=" ".join(current_prose)))
            current_prose.clear()

    def flush_code() -> None:
        if current_code:
            base_x0 = min(ln.x0 for ln in current_code)
            rendered = []
            for ln in current_code:
                indent = max(0, round((ln.x0 - base_x0) / CODE_CHAR_WIDTH))
                rendered.append(" " * indent + ln.text)
            segments.append(CodeSegment(text="\n".join(rendered)))
            current_code.clear()

    def flush_all() -> None:
        flush_prose()
        flush_code()

    for page_number, y0, y1, kind, payload in events:
        if kind == "line":
            line = payload
            assert isinstance(line, Line)
            if any(_line_in_region(line, regions[i]) for i in range(len(regions))):
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
        else:
            event_region_index = payload
            assert isinstance(event_region_index, int)
            flush_all()
            segments.append(FigureSegment(region_index=event_region_index))
            placed_regions.append(event_region_index)
            previous_end = (page_number, y1)

    flush_all()
    return segments, placed_regions


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


def assemble_question(
    span: QuestionSpan,
    doc: pymupdf.Document,
    decorative_baseline: frozenset[tuple[int, int, int, int]],
) -> ExtractedQuestion:
    warnings: list[str] = []

    content_lines = _strip_leading_marker([ln for ln in span.lines if not is_chrome_line(ln.text)])

    pages_in_span = sorted({ln.page_number for ln in content_lines}) or [span.start_page]

    # Region detection is per-page, but two different questions can share a
    # page (e.g. Q34 ends and Q35 begins on the same page 43). Without a
    # y-bound, a figure belonging to the *other* question on that shared
    # page would be wrongly attached here. Bound candidate regions to the
    # vertical range this span's own content_lines actually occupy on each
    # page (with a small tolerance for a figure sitting just outside its
    # nearest text line).
    page_y_bounds: dict[int, tuple[float, float]] = {}
    for ln in content_lines:
        lo, hi = page_y_bounds.get(ln.page_number, (ln.y0, ln.y1))
        page_y_bounds[ln.page_number] = (min(lo, ln.y0), max(hi, ln.y1))
    y_tolerance = 15.0

    regions: list[VisualRegion] = []
    for page_number in pages_in_span:
        page_regions = detect_visual_regions(doc, page_number, decorative_baseline)
        bounds = page_y_bounds.get(page_number)
        if bounds is None:
            continue
        y_min, y_max = bounds[0] - y_tolerance, bounds[1] + y_tolerance
        regions.extend(r for r in page_regions if y_min <= r.bbox[1] <= y_max)

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
        preliminary_starts = _find_alternative_starts(content_lines)
        if preliminary_starts is not None:
            a_line = content_lines[preliminary_starts["A"]]
            alt_section_start = _position_key(a_line.page_number, a_line.y0)

    def _in_alternatives_section(ln: Line) -> bool:
        return alt_section_start is not None and _position_key(ln.page_number, ln.y0) >= (
            alt_section_start
        )

    text_only_lines = [
        ln
        for ln in content_lines
        if _in_alternatives_section(ln) or not any(_line_in_region(ln, r) for r in regions)
    ]

    alternatives: list[ExtractedAlternative] = []
    statement_lines = content_lines
    statement_regions = regions

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

            ordered_letters = ["A", "B", "C", "D", "E"]
            alt_bounds = [starts[letter] for letter in ordered_letters] + [len(text_only_lines)]
            for i, letter in enumerate(ordered_letters):
                group = text_only_lines[alt_bounds[i] : alt_bounds[i + 1]]
                if not group:
                    warnings.append(f"alternative {letter} has no text")
                    continue
                first_match = _ALTERNATIVE_LINE_RE.match(group[0].text)
                assert first_match is not None  # guaranteed by _find_alternative_starts
                first_text = first_match.group(2).strip()
                rest_text = " ".join(ln.text.strip() for ln in group[1:])
                full_text = f"{first_text} {rest_text}".strip() if rest_text else first_text
                alternatives.append(ExtractedAlternative(letter=letter, text=full_text))

    segments, placed_region_indices = _build_statement_segments(statement_lines, statement_regions)

    unplaced = set(range(len(statement_regions))) - set(placed_region_indices)
    if unplaced:
        warnings.append(
            f"{len(unplaced)} detected figure region(s) could not be placed in the statement flow"
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

    dropped_regions = [r for r in regions if r not in statement_regions]
    if dropped_regions:
        warnings.append(
            f"{len(dropped_regions)} figure region(s) fell after the alternatives cutoff "
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
        warnings=warnings,
        spacing_corrections=spacing_corrections,
        label_corrections=label_corrections,
        symbol_corrections=symbol_corrections,
    )
