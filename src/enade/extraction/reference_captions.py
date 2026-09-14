"""Explicit, documentary reference captions ("Figura para a questao N").

PROMPT Phase 3E: a caption that explicitly names its own owning question
number is documentary evidence that overrides purely geometric/textual
span-slicing - the asset it describes can be printed *before* its own
question's marker (2008-b page 27: Q61's own ITIL diagram sits between
D60's own marker and Q61's own marker, with an explicit "Figura para a
questao 61" caption, because there was no room for it after Q61's own
marker on the shared page). Marker-position-based span-slicing
(boundaries.py) has no way to know this by itself - a question's own span
is, by construction, everything between its own marker and the next one.

This module runs once, right after span-slicing and before any merge,
region detection, or text consumption (PROMPT Phase 3E section 10 - "a
reserva deve ocorrer antes dessas operacoes destrutivas"): it detects this
caption pattern, resolves its documented target, locates the one visual
region anchored to it (never guessed from the diagram's own meaning - only
from geometric proximity in the caption's own expected reading direction),
collects every line genuinely inside that region's own bbox (from
*whichever* span currently holds them - a wide asset spanning a detected
column boundary can have its own label lines split across two different
spans by the page's own column-based reading order), and physically moves
the caption plus those lines to the span it documents. Every other line -
real prose, real alternatives, real instructions belonging to the origin
span(s) - is left untouched (PROMPT: "Nenhuma reatribuicao pode transferir
conteudo que nao esteja diretamente ancorado por essa referencia").
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace

import pymupdf

from enade.extraction.assembler import _ALTERNATIVE_LINE_RE
from enade.extraction.boundaries import QuestionKind, QuestionSpan
from enade.extraction.chrome import is_chrome_line
from enade.extraction.figures import (
    DEFAULT_Y_MERGE_TOLERANCE,
    UNBOUNDED_MERGE_X_TOLERANCE,
    _merge_by_vertical_proximity,
    collect_page_candidates,
)
from enade.extraction.layout import Line

Rect = tuple[float, float, float, float]

#: "Figura para a questao 61", "Tabela para a questao 61", "Diagrama
#: referente a questao 61", "Quadro para a questao 61" - the reference
#: itself, not a generic mention of another question inside real body
#: prose (PROMPT section 11 - "frase da propria questao mencionando outro
#: numero" must never match this pattern; anchored to the *start* of the
#: line, not searched mid-sentence, is what keeps this narrow). The
#: trailing word boundary and lack of any qualifier after the number
#: rejects a coincidentally similar phrase that continues into unrelated
#: text on the same line.
_REFERENCE_CAPTION_RE = re.compile(
    r"(?i)^(figura|tabela|diagrama|quadro)\s+(?:para\s+a|referente\s+[àa])\s+"
    r"quest[ãa]o\s+0*(\d+)\s*$"
)
#: Padding (points) used when testing whether a line genuinely sits inside
#: the anchored region's own bbox - matches assembler.py's own
#: REGION_Y_PADDING/REGION_X_PADDING (a tight tolerance for rounding noise,
#: not a general-purpose fuzziness margin).
_ANCHOR_CONTAINMENT_PADDING = 3.0
#: Maximum vertical gap (points) between a caption line and the visual
#: region it anchors - generous enough for a caption sitting a full line
#: height above its own figure (confirmed real gap: ~3pt), but bounded so
#: a caption never reaches all the way down the page to an unrelated,
#: much later region.
MAX_CAPTION_TO_ASSET_GAP = 40.0


def _question_key(kind: QuestionKind, number: int) -> str:
    return f"{kind.value}-{number}"


@dataclass(frozen=True)
class ReferenceCaption:
    """One detected "X para a questao N" caption line - PROMPT Phase 3E
    section 6.
    """

    page_number: int
    text: str
    bbox: Rect
    reference_type: str  # "figura" | "tabela" | "diagrama" | "quadro"
    referenced_number: int
    origin_question_key: str
    #: "current" (N is the span that already contains this line - no
    #: transfer needed), "forward" (N's own span comes later in document
    #: order), "backward" (N's own span comes earlier - not transferred by
    #: this module; no confirmed real-corpus case, logged not guessed).
    direction: str


@dataclass(frozen=True)
class CaptionReferenceTransfer:
    """One transfer decision - PROMPT Phase 3E section 13 (ownership trace)."""

    caption: ReferenceCaption
    target_question_key: str | None
    candidate_asset_bbox: Rect | None
    transferred_line_count: int
    accepted: bool
    rejection_reason: str | None


def _detect_captions_in_span(span: QuestionSpan) -> list[tuple[int, ReferenceCaption]]:
    """Every reference caption found in ``span``'s own lines, paired with
    its own line index within ``span.lines`` (needed later to slice the
    transfer range).
    """
    found: list[tuple[int, ReferenceCaption]] = []
    own_key = _question_key(span.kind, span.number)
    for index, line in enumerate(span.lines):
        match = _REFERENCE_CAPTION_RE.match(line.text.strip())
        if not match:
            continue
        reference_type = match.group(1).lower()
        referenced_number = int(match.group(2))
        found.append(
            (
                index,
                ReferenceCaption(
                    page_number=line.page_number,
                    text=line.text,
                    bbox=line.bbox,
                    reference_type=reference_type,
                    referenced_number=referenced_number,
                    origin_question_key=own_key,
                    direction="current",  # resolved by the caller, which knows span order
                ),
            )
        )
    return found


def _resolve_target(
    referenced_number: int, spans_in_order: list[QuestionSpan]
) -> tuple[QuestionSpan | None, str | None]:
    """Find the span this caption's own number documents, among *any* kind
    (PROMPT section 7: "o numero da questao estiver documentalmente
    presente" - the caption text alone never says objective vs.
    discursive). Returns ``(span, None)`` on a unique match, or
    ``(None, rejection_reason)`` otherwise - never guesses.
    """
    matches = [s for s in spans_in_order if s.number == referenced_number]
    if not matches:
        return None, "referenced_question_not_found"
    if len(matches) > 1:
        return None, "ambiguous_question_kind"
    return matches[0], None


def _find_anchored_region(
    caption_line: Line,
    doc: pymupdf.Document,
    decorative_baseline: frozenset[tuple[int, int, int, int]],
    region_merge_x_tolerance: float,
) -> Rect | None:
    """The bbox of the one visual cluster this caption anchors - PROMPT
    section 9.

    Deliberately *not* ``figures.detect_visual_regions`` (which needs a
    known owner per candidate to keep unrelated same-page clusters from
    merging - PROMPT Phase 2D; passing ``question_regions=None`` here would
    let every candidate on the page collapse into one region regardless of
    owner, since ``_merge_overlapping_regions``'s own "same owner" check
    treats "both None" as equal - confirmed by direct instrumentation
    against 2008/b1_prova.pdf page 27, where this merged Q61's own ITIL
    diagram, Q63's own ER-diagram, and an unrelated small logo image into
    one bbox spanning nearly the whole page). This module has its own,
    narrower job: cluster raw candidates by Y/X proximity alone (the same
    ``_merge_by_vertical_proximity`` primitive, with no label absorption and
    no overlap-based secondary merge), then pick whichever resulting
    cluster sits closest below the caption, within ``MAX_CAPTION_TO_ASSET_GAP``
    - never by the asset's own visual *meaning*, and never when no
    candidate is close enough to be demonstrated (PROMPT section 7 rule 6).
    """
    page = doc[caption_line.page_number - 1]
    candidates = collect_page_candidates(page, caption_line.page_number, decorative_baseline)
    if not candidates:
        return None
    clusters = _merge_by_vertical_proximity(
        candidates, DEFAULT_Y_MERGE_TOLERANCE, x_tolerance=region_merge_x_tolerance
    )
    below = [bbox for bbox, _count, _has_image in clusters if bbox[1] >= caption_line.y0]
    if not below:
        return None
    closest = min(below, key=lambda bbox: bbox[1] - caption_line.y0)
    if (closest[1] - caption_line.y0) > MAX_CAPTION_TO_ASSET_GAP:
        return None
    return closest


def _line_within_bbox(line: Line, bbox: Rect, padding: float) -> bool:
    return (
        bbox[0] - padding <= line.x0
        and line.x1 <= bbox[2] + padding
        and bbox[1] - padding <= line.y0
        and line.y1 <= bbox[3] + padding
    )


def apply_forward_reference_transfers(
    spans: list[QuestionSpan],
    doc: pymupdf.Document,
    decorative_baseline: frozenset[tuple[int, int, int, int]],
    *,
    region_merge_x_tolerance: float = UNBOUNDED_MERGE_X_TOLERANCE,
) -> tuple[list[QuestionSpan], list[CaptionReferenceTransfer]]:
    """Detect and apply every valid forward-reference caption transfer.

    ``spans`` must be in original document/reading order (the order
    ``boundaries.detect_question_boundaries`` itself returns, *before* any
    later re-sort for processing) - direction ("forward" vs. "backward") is
    determined from each span's own position in this list, never from
    question numbers alone (2008-b's own combined numbering makes numeric
    comparison alone unreliable for discursive/objective interleaving).

    Returns a new spans list (same order, ``.lines``/``.start_page``/
    ``.end_page`` updated only for spans that gained or lost lines) plus a
    full trace of every caption found, accepted or rejected - PROMPT
    section 13.
    """
    span_index_by_key = {_question_key(s.kind, s.number): i for i, s in enumerate(spans)}
    # Mutable working copy of each span's own lines, keyed the same way -
    # transfers accumulate here before being materialized into new
    # QuestionSpan instances at the end (spans are frozen).
    working_lines: dict[str, list[Line]] = {
        _question_key(s.kind, s.number): list(s.lines) for s in spans
    }

    records: list[CaptionReferenceTransfer] = []

    for span in spans:
        own_key = _question_key(span.kind, span.number)
        for _, caption in _detect_captions_in_span(span):
            target_span, rejection = _resolve_target(caption.referenced_number, spans)
            if target_span is None:
                records.append(
                    CaptionReferenceTransfer(
                        caption=caption,
                        target_question_key=None,
                        candidate_asset_bbox=None,
                        transferred_line_count=0,
                        accepted=False,
                        rejection_reason=rejection,
                    )
                )
                continue

            target_key = _question_key(target_span.kind, target_span.number)
            if target_key == own_key:
                # "current" - the caption already sits in the span it
                # documents; nothing to transfer.
                continue

            direction = (
                "forward"
                if span_index_by_key[target_key] > span_index_by_key[own_key]
                else "backward"
            )
            if direction == "backward":
                records.append(
                    CaptionReferenceTransfer(
                        caption=replace(caption, direction=direction),
                        target_question_key=target_key,
                        candidate_asset_bbox=None,
                        transferred_line_count=0,
                        accepted=False,
                        rejection_reason="backward_reference_not_supported",
                    )
                )
                continue

            # Reconstruct a Line for the caption itself, using its own
            # recorded page/bbox (needed to search for an anchored region).
            caption_as_line = Line(
                page_number=caption.page_number,
                text=caption.text,
                x0=caption.bbox[0],
                y0=caption.bbox[1],
                x1=caption.bbox[2],
                y1=caption.bbox[3],
            )
            anchored_bbox = _find_anchored_region(
                caption_as_line,
                doc,
                decorative_baseline,
                region_merge_x_tolerance,
            )
            if anchored_bbox is None:
                records.append(
                    CaptionReferenceTransfer(
                        caption=replace(caption, direction=direction),
                        target_question_key=target_key,
                        candidate_asset_bbox=None,
                        transferred_line_count=0,
                        accepted=False,
                        rejection_reason="no_anchored_asset_found",
                    )
                )
                continue

            # Collect every line, from *any* span, genuinely inside the
            # anchored region's own bbox (PROMPT: a wide asset can have its
            # own label lines split across two spans by column-based
            # reading order) - never an alternative marker (PROMPT section
            # 8: never transfer an alternative), and never the caption
            # line itself twice.
            transferred: list[tuple[str, Line]] = []
            for key, lines in working_lines.items():
                for line in lines:
                    if line.page_number != caption.page_number:
                        continue
                    if _ALTERNATIVE_LINE_RE.match(line.text):
                        continue
                    if _line_within_bbox(line, anchored_bbox, _ANCHOR_CONTAINMENT_PADDING):
                        transferred.append((key, line))

            # Remove every transferred line (including the caption line
            # itself) from its own current span.
            source_keys = {own_key} | {k for k, _ in transferred}
            for key in source_keys:
                lines_here = working_lines[key]
                to_remove_texts_bboxes = {
                    (ln.page_number, ln.bbox, ln.text) for k, ln in transferred if k == key
                }
                if key == own_key:
                    to_remove_texts_bboxes.add((caption.page_number, caption.bbox, caption.text))
                working_lines[key] = [
                    ln
                    for ln in lines_here
                    if (ln.page_number, ln.bbox, ln.text) not in to_remove_texts_bboxes
                ]

            # Prepend (reading-order sorted) to the target span - the
            # asset and its own labels are printed *before* the target
            # question's own marker, so they belong at the very start of
            # its own content.
            moved_lines = sorted(
                [ln for _, ln in transferred] + [caption_as_line],
                key=lambda ln: (ln.page_number, ln.y0, ln.x0),
            )
            working_lines[target_key] = moved_lines + working_lines[target_key]

            records.append(
                CaptionReferenceTransfer(
                    caption=replace(caption, direction=direction),
                    target_question_key=target_key,
                    candidate_asset_bbox=anchored_bbox,
                    transferred_line_count=len(moved_lines),
                    accepted=True,
                    rejection_reason=None,
                )
            )

    new_spans: list[QuestionSpan] = []
    for span in spans:
        key = _question_key(span.kind, span.number)
        new_lines = tuple(working_lines[key])
        if new_lines == span.lines:
            new_spans.append(span)
            continue
        content_pages = sorted({ln.page_number for ln in new_lines if not is_chrome_line(ln.text)})
        all_pages = sorted({ln.page_number for ln in new_lines})
        pages = content_pages or all_pages or [span.start_page]
        new_spans.append(
            replace(
                span,
                lines=new_lines,
                start_page=pages[0],
                end_page=pages[-1],
            )
        )
    return new_spans, records
