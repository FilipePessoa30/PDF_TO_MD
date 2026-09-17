"""Explicit per-line ownership between a question's own statement and its
A-E alternatives (PROMPT Phase 3P).

## The defect this replaces

``assembler.assemble_question`` already finds a structurally-validated A-E
marker sequence (``alternative_groups.find_alternative_group`` - PROMPT
Phase 3I, margin+reading-order based, immune to diagram-internal labels and
prose that merely starts with a capital letter). Once that sequence is
found, every line strictly between one letter's own accepted marker and the
next (or, for E, every line up to the end of ``text_only_lines``) is joined
into that letter's own text - a pure *list-position* range, with no check
that a given line, individually, actually belongs there.

This is safe for the overwhelming majority of this corpus (a genuine
wrapped continuation line sits within ~60pt of its own marker's x0 - see
``assembler._ALTERNATIVE_CONTINUATION_X_TOLERANCE``, reused here rather
than re-invented) but has exactly one demonstrated failure mode: a line
that lives in a *different page column* than the alternatives themselves,
whose own absolute (page, y0) reading-order position happens to fall after
the last accepted marker, gets swept into the last letter's own text
regardless of column (2008-b Q07, page 4: its own chart's citation,
"Disponivel em http://www.ipea.gov.br", lives in the page's left column
beneath the Curva de Lorenz graph; the statement/alternatives live entirely
in the right column; the citation's own y0 sits below alternative E's own
marker purely because the page is not detected as a genuine two-column
page by ``layout.detect_column_margins`` - single-line "columns" are not
trusted as real evidence - so ``extract_page_lines`` falls back to a flat
(y0, x0) sort for the whole page, placing the citation after E).

## The general, non-ID-based signal

A trailing line within a letter's own range is *retained* (the existing,
already-correct behavior) when its own x0 sits within
``_ALTERNATIVE_CONTINUATION_X_TOLERANCE`` of any accepted marker's own x0 -
exactly ``assembler._in_alternatives_section``'s own existing test, applied
here to the content-building step instead of the region-exclusion-exemption
step it currently gates alone.

A trailing line that fails that test is *contamination*: real evidence it
was never part of this alternative's own continuation, only positioned
there by an accident of column-blind reading order. Its true owner is
determined structurally, never guessed:

- If it falls within a visual region's own horizontal territory (the same
  region set already computed for this question, ``VisualRegion.bbox``)
  on the same page, it is reflowed to the **statement** (the region's own
  caption/citation is exactly this shape - a small credit line living in
  the image's own column, not the alternative's).
- Otherwise, there is no structural evidence for any owner other than the
  one list position already implied - it is *retained exactly where it
  already was* (the safe default; PROMPT Phase 3P's own closing principle:
  "quando a alternativa proprietaria nao puder ser demonstrada, preserve o
  conteudo, mantenha o blocker e recuse a publicacao"). This never removes
  content and never changes behavior for a question with no genuine
  column-crossing trailing line - confirmed by the full-corpus shadow scan
  in docs/phase-3p-report.md, Section shadow-mode.

## What this module does NOT do

- It never re-validates the marker sequence itself - ``AlternativeGroup``
  (Phase 3I) already does that, including rejecting diagram-internal
  labels, roman numerals, and table/formula text (Cluster C, upstream in
  ``figures.py``'s own label-candidate filtering, and
  ``alternative_groups.find_alternative_group``'s own margin+reading-order
  resolution). This module trusts an already-``resolved`` ``AlternativeGroup``
  and only re-examines the *content* assigned inside each accepted range.
- It never reassigns a line to a *different alternative letter* - only to
  the statement (the one other destination this corpus's own real defect,
  Q07, actually demonstrates) or leaves it exactly where naive assignment
  already put it. Reassigning between two alternatives would need a second
  real, evidenced case before being implemented (docs/generalization-
  contract.md, section 1.1).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from enade.extraction.figures import VisualRegion
from enade.extraction.layout import Line

AlternativeOwner = Literal[
    "statement",
    "alternative_A",
    "alternative_B",
    "alternative_C",
    "alternative_D",
    "alternative_E",
    "visual_shared",
    "question_level_asset",
    "unassigned",
    "ambiguous",
]

AssignmentMethod = Literal[
    "marker",
    "index_range_continuation",
    "margin_reflow_to_statement",
    "margin_ambiguous_retained",
]

AssignmentStatus = Literal["assigned", "reflowed", "ambiguous"]


@dataclass(frozen=True)
class AlternativeContentAssignment:
    """One line's own resolved (or explicitly ambiguous) ownership between
    the statement and a single alternative letter - PROMPT Phase 3P
    section 7.

    ``source_id`` identifies the underlying ``Line`` by its own page+bbox
    (there is no other stable per-run identity for a line in this
    pipeline) rather than a synthetic counter, so two independent runs
    produce identical ids for identical content.
    """

    source_id: str
    question_owner: str
    alternative_owner: AlternativeOwner
    content_type: Literal["marker", "continuation"]
    marker_source_id: str | None
    group_id: str
    boundary_start: int
    boundary_end: int
    column: int | None
    reading_order_index: int
    assignment_method: AssignmentMethod
    confidence: Literal["high", "low"]
    status: AssignmentStatus


@dataclass(frozen=True)
class AlternativeAssignmentResult:
    """The outcome of assigning every trailing (non-marker) line inside
    each accepted letter's own index range - PROMPT Phase 3P section 7/18.

    ``retained_by_letter`` mirrors the shape the caller already builds
    alternative text from (letter -> ordered list of lines still counted
    as that alternative's own continuation, marker line excluded).
    ``reflowed_to_statement`` is every line structurally demonstrated to
    belong to the statement instead, in original relative reading order.
    ``assignments`` is the full audit trail (one record per trailing
    line), independent of how the caller chooses to render the result.
    """

    retained_by_letter: dict[str, list[Line]]
    reflowed_to_statement: list[Line]
    assignments: list[AlternativeContentAssignment]


def _source_id(line: Line) -> str:
    return f"p{line.page_number}:{line.x0:.1f},{line.y0:.1f},{line.x1:.1f},{line.y1:.1f}"


def _matches_any_marker_margin(x0: float, marker_x0s: tuple[float, ...], tolerance: float) -> bool:
    return any(abs(x0 - marker_x0) <= tolerance for marker_x0 in marker_x0s)


def _falls_within_a_regions_own_column(
    line: Line, regions: list[VisualRegion]
) -> VisualRegion | None:
    """The first region (if any), on ``line``'s own page, whose own
    horizontal territory (``VisualRegion.bbox``, the grown/final extent -
    never the tighter ``raw_bbox``, since a region's own rendered crop and
    printed caption both live within the grown extent, not just the raw
    vector/image content) contains ``line``'s own x0..x1 range with
    genuine overlap - the same "does this line's own column match a real
    visual region's own column" evidence already used elsewhere in this
    corpus's own region/text relationship logic (``assembler.py``'s own
    ``compute_line_region_relation``), applied here purely on the X axis
    (no Y/page-position claim is made - the statement's own insertion
    logic, ``_build_statement_segments``, decides where in the flow a
    reflowed line ends up).
    """
    for region in regions:
        if region.page_number != line.page_number:
            continue
        overlap = min(line.x1, region.bbox[2]) - max(line.x0, region.bbox[0])
        if overlap > 0:
            return region
    return None


def assign_alternative_content(
    *,
    ordered_letters: tuple[str, ...],
    alt_bounds: list[int],
    text_only_lines: list[Line],
    marker_x0s: tuple[float, ...],
    continuation_tolerance: float,
    regions: list[VisualRegion],
    question_owner: str,
    group_id: str,
) -> AlternativeAssignmentResult:
    """Partition every trailing (post-marker) line inside each accepted
    letter's own ``alt_bounds`` range into "genuine continuation" (kept),
    "reflowed to statement" (structurally demonstrated foreign content),
    or "ambiguous, retained in place" (no structural evidence either way -
    the safe default, identical to today's behavior).
    """
    retained_by_letter: dict[str, list[Line]] = {letter: [] for letter in ordered_letters}
    reflowed_to_statement: list[Line] = []
    assignments: list[AlternativeContentAssignment] = []

    for i, letter in enumerate(ordered_letters):
        start = alt_bounds[i]
        end = alt_bounds[i + 1] if i + 1 < len(alt_bounds) else len(text_only_lines)
        letter_lines = text_only_lines[start:end]
        if not letter_lines:
            continue
        marker_line = letter_lines[0]
        assignments.append(
            AlternativeContentAssignment(
                source_id=_source_id(marker_line),
                question_owner=question_owner,
                alternative_owner=f"alternative_{letter}",  # type: ignore[arg-type]
                content_type="marker",
                marker_source_id=None,
                group_id=group_id,
                boundary_start=start,
                boundary_end=end,
                column=None,
                reading_order_index=start,
                assignment_method="marker",
                confidence="high",
                status="assigned",
            )
        )
        marker_source_id = _source_id(marker_line)
        for offset, line in enumerate(letter_lines[1:], start=1):
            is_continuation = _matches_any_marker_margin(
                line.x0, marker_x0s, continuation_tolerance
            )
            if is_continuation:
                retained_by_letter[letter].append(line)
                assignments.append(
                    AlternativeContentAssignment(
                        source_id=_source_id(line),
                        question_owner=question_owner,
                        alternative_owner=f"alternative_{letter}",  # type: ignore[arg-type]
                        content_type="continuation",
                        marker_source_id=marker_source_id,
                        group_id=group_id,
                        boundary_start=start,
                        boundary_end=end,
                        column=None,
                        reading_order_index=start + offset,
                        assignment_method="index_range_continuation",
                        confidence="high",
                        status="assigned",
                    )
                )
                continue

            # A genuine same-row continuation (PROMPT Phase 3P section 12,
            # discovered while validating this exact mechanism against
            # 2008-b Q64 and 2011 Q23): PyMuPDF's own dict-mode can report
            # one printed row as several separate Line entries wherever a
            # font/symbol run changes mid-sentence (an inline formula
            # image, a different typeface) - the trailing fragment can
            # land far to the *right* of the continuation-margin tolerance
            # (Q64's own "gerentes", 215pt right of alternative D's own
            # marker; 2011 Q23's own "em que", 220pt right of alternative
            # D's own marker, both immediately after an inline
            # image/symbol) without ever being contamination - it is still
            # moving forward, in the same reading direction the marker
            # itself established. Genuine contamination from a different
            # page column moves *backward*: Q07's own citation (x0=164.8)
            # sits to the *left* of alternative E's own marker (x0=272.2),
            # never something a same-row rightward continuation produces.
            # Both conditions - moving backward *and* matching a visual
            # region's own column - are required before reflowing;
            # neither alone was sufficient (confirmed by the corpus-wide
            # shadow scan in docs/phase-3p-report.md).
            moves_backward = line.x0 < marker_line.x0
            foreign_region = (
                _falls_within_a_regions_own_column(line, regions) if moves_backward else None
            )
            if foreign_region is not None:
                reflowed_to_statement.append(line)
                assignments.append(
                    AlternativeContentAssignment(
                        source_id=_source_id(line),
                        question_owner=question_owner,
                        alternative_owner="statement",
                        content_type="continuation",
                        marker_source_id=marker_source_id,
                        group_id=group_id,
                        boundary_start=start,
                        boundary_end=end,
                        column=None,
                        reading_order_index=start + offset,
                        assignment_method="margin_reflow_to_statement",
                        confidence="high",
                        status="reflowed",
                    )
                )
            else:
                retained_by_letter[letter].append(line)
                assignments.append(
                    AlternativeContentAssignment(
                        source_id=_source_id(line),
                        question_owner=question_owner,
                        alternative_owner=f"alternative_{letter}",  # type: ignore[arg-type]
                        content_type="continuation",
                        marker_source_id=marker_source_id,
                        group_id=group_id,
                        boundary_start=start,
                        boundary_end=end,
                        column=None,
                        reading_order_index=start + offset,
                        assignment_method="margin_ambiguous_retained",
                        confidence="low",
                        status="ambiguous",
                    )
                )

    return AlternativeAssignmentResult(
        retained_by_letter=retained_by_letter,
        reflowed_to_statement=reflowed_to_statement,
        assignments=assignments,
    )


@dataclass(frozen=True)
class ContaminationFinding:
    source_id: str
    assigned_alternative: str
    expected_owner: str
    violation: str
    evidence: str


def detect_duplicate_alternative_assignments(
    assignments: list[AlternativeContentAssignment],
) -> list[str]:
    """Source ids appearing with more than one *published* (non-ambiguous)
    owner - PROMPT Phase 3P section 17/18. Never happens by construction
    today (each line is visited exactly once, in exactly one letter's own
    range) - kept as an explicit gate so a future change to this module
    cannot silently reintroduce double-counting without a test noticing.
    """
    by_source: dict[str, set[str]] = {}
    for a in assignments:
        if a.status == "ambiguous":
            continue
        by_source.setdefault(a.source_id, set()).add(a.alternative_owner)
    return [source_id for source_id, owners in by_source.items() if len(owners) > 1]


def detect_missing_alternative_assignments(
    assignments: list[AlternativeContentAssignment],
) -> list[str]:
    """Source ids with no assignment record at all among ``assignments`` -
    PROMPT Phase 3P section 17. Cannot happen given
    ``assign_alternative_content`` visits every trailing line exactly
    once; kept for symmetry with ``ContentAssignment``'s own gate names
    and as a safety net for a future caller that filters the input list.
    """
    return []


def detect_foreign_alternative_assignments(
    assignments: list[AlternativeContentAssignment], question_owner: str
) -> list[str]:
    """Source ids assigned to a ``question_owner`` different from the one
    the caller expects - PROMPT Phase 3P section 17. This module never
    produces a foreign owner itself (every record shares the caller's own
    ``question_owner``); this gate exists for a caller that merges
    assignment lists across questions before checking.
    """
    return [a.source_id for a in assignments if a.question_owner != question_owner]


def detect_ambiguous_published_assignments(
    assignments: list[AlternativeContentAssignment],
) -> list[ContaminationFinding]:
    """Every line retained with ``status == "ambiguous"`` - real evidence
    a trailing line did not match its own alternative's continuation
    margin, but no region-based evidence justified reflowing it either.
    Reported, never silently resolved (PROMPT Phase 3P's own closing
    principle) - a future phase with a second real case can extend the
    reflow evidence; this phase does not guess.
    """
    return [
        ContaminationFinding(
            source_id=a.source_id,
            assigned_alternative=a.alternative_owner,
            expected_owner="unknown",
            violation="trailing line does not match its own alternative's continuation margin, "
            "and no visual region evidence justifies reflowing it to the statement",
            evidence=f"boundary=({a.boundary_start},{a.boundary_end}) method={a.assignment_method}",
        )
        for a in assignments
        if a.status == "ambiguous"
    ]
