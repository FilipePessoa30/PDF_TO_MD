"""Geometric reconstruction of PyMuPDF-fragmented physical lines (PROMPT
Phase 3H, "Cluster D").

## Root cause (investigated in Phase 3H via direct instrumentation)

PyMuPDF's own ``page.get_text("dict")`` groups glyphs into "lines" using an
internal heuristic that does not always match one *visual* printed line to
one "line" dict entry: on several 2008-b pages, one continuous, single-space
-justified sentence is reported as a chain of several "line" entries - one
per word or short phrase - each sharing the *exact* same baseline (y0/y1)
as its neighbours, separated only by a small horizontal gap.

Confirmed by direct instrumentation against ``b1_prova.pdf``:

- Page 4 (Q07): "De acordo com o mesmo grafico, o percentual da renda" is
  followed on the *same* baseline (y0=657.972, y1=667.932) by eight further
  "line" entries - "total", "correspondente", "aos", "20%", "de", "maior",
  "renda", "foi," - each a separate dict-mode line, gaps ~8.4pt apart.
- Page 8 (Q12): "base", "na", "complexidade", "ciclomatica." - same
  baseline (y0=507.612, y1=517.572), gaps ~9.2pt apart.

Each of these short fragments, taken alone, is short enough and close
enough to a nearby figure to be individually swallowed as a "label
candidate" by ``figures.py``'s own label-absorption growth (see
``docs/phase-3g-report.md``, Q07/Q12's own residual defects) - the fix
belongs at the *source* of the fragmentation, not as another absorption
special case downstream.

## The geometric AND documentary signal (never semantic)

Two independent pieces of evidence, both present in the PDF's own decoded
glyph stream - never a dictionary, spellchecker, or language model (PROMPT:
"e proibido corrigir por conhecimento linguistico"):

1. **Baseline identity**: genuinely fragmented pieces of one physical line
   share the *exact* same y0/y1 (to sub-point precision) - a real,
   sequential line-wrap (the next printed line down) always has a
   different, lower y0.
2. **A literal trailing space glyph**: every fragment except the last one
   on a genuinely continuous line carries its own trailing space character
   in the *raw*, pre-normalization span text (before any correction or
   ``.rstrip()`` this module's own caller may apply) - confirmed present on
   every one of the Q07/Q12 fragments above, and confirmed *absent* on
   every cell of a real table row measured for comparison (2008-b Q54's
   own routing table, page 23: "127.0.0.0", "255.0.0.0", "127.0.0.1", ...,
   none of which carry a trailing space - these are separately positioned
   tokens with no textual continuation, not a split sentence). This is the
   *same* category of evidence ``spacing.py`` already relies on (a real
   character the font's own decode table places in the stream) - the
   opposite polarity of ``spacing.py``'s own ligature-injected-space
   defect (there, a spurious space breaks one real word into two; here, a
   genuine word-boundary space's own presence is exactly what is missing
   from the *next* fragment onward once PyMuPDF's own line clustering
   splits the sentence apart).

The horizontal gap itself is used only as a *secondary* safety bound, not
the primary signal: measured across the same real pages, genuine
same-sentence fragment gaps sit at ~0.84-0.92x the shared font size, while
a real table row's own cell-to-cell gaps sit at ~2.5-4.1x the font size -
an order-of-magnitude-class separation matching ``spacing.py``'s own
established methodology. ``MAX_FRAGMENT_GAP_RATIO`` sits well inside that
margin, so it can only ever *reject* a merge the trailing-space signal
would otherwise allow, never approve one the trailing space does not
already support.

## What this does NOT do

- It never merges two fragments whose baselines differ (a genuine next
  printed line is always left alone - see ``layout.py``'s own paragraph/
  line-wrap handling for that separate concern).
- It never merges a monospace (code/pseudocode) fragment - PROMPT section
  16: "sempre preserve... pseudocodigo; codigo" keeps its own literal line
  breaks.
- It never inserts a space where the raw glyph stream does not already
  place one, and never removes one either - the join is either
  ``"merge_with_space"`` (documentary trailing space present) or
  ``"preserve_separate"`` (kept exactly as PyMuPDF reported it) - there is
  no dictionary-driven "merge without space" case in this mechanism (that
  is a *different*, already-solved problem - see spacing.py's own
  ligature-space correction, which operates *within* one already-assembled
  line's own word geometry, not across dict-mode line boundaries).
- If the evidence is ambiguous (baseline matches but no trailing space, or
  a trailing space but the gap exceeds the safety ceiling), fragments are
  preserved separately - never destructively joined on a guess (PROMPT:
  "quando a reconstrucao nao for demonstravel, preserve os fragments").
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

#: Two fragments' own y0 (and separately y1) must match within this many
#: points to count as "the same baseline" - genuinely fragmented pieces of
#: one PyMuPDF-reported physical line come out bit-identical to 3 decimal
#: places in every real case measured (Q07/Q12); 0.05pt leaves a small
#: margin for floating-point noise while comfortably excluding the closest
#: real near-miss found (2008-b Q29's own diagram-label row, whose own
#: baseline sits 0.445pt from an adjacent prose line's own baseline -
#: confirmed by direct instrumentation this is NOT a real match, and is
#: independently rejected by the gap-ceiling check below regardless).
BASELINE_TOLERANCE_PT = 0.05

#: Two adjacent fragments' own font sizes must match within this many
#: points - guards against merging across a genuine typographic change
#: (e.g. a bold heading abutting body text) that happens to share a
#: baseline by coincidence. No real corpus case required loosening this.
FONT_SIZE_TOLERANCE_PT = 0.5

#: A horizontal gap above this multiple of the shared font size is never a
#: same-sentence word gap in this corpus's own measured evidence (real
#: fragment gaps: ~0.84-0.92x; real table-cell gaps: ~2.5-4.1x - see module
#: docstring). Purely a safety ceiling; the trailing-space signal is what
#: actually authorizes a merge.
MAX_FRAGMENT_GAP_RATIO = 1.5


@dataclass(frozen=True)
class RawLineFragment:
    """One raw PyMuPDF dict-mode "line" entry, before any text correction.

    This is the finest fragment granularity this codebase tracks
    downstream of the PDF's own content stream - ``layout.py`` does not
    carry individual chars/spans past this module (see
    ``docs/phase-3h-report.md`` section F for why this granularity matches
    the defect actually observed: every real fragmentation case found this
    phase splits between whole dict-mode "line" entries, never mid-span).
    """

    page_number: int
    x0: float
    y0: float
    x1: float
    y1: float
    #: Joined span text exactly as PyMuPDF reported it - NOT yet
    #: right-stripped. A trailing space here is documentary evidence (see
    #: module docstring), so callers must pass the untouched join, not a
    #: caller-normalized version.
    raw_text: str
    fonts: tuple[str, ...]
    font_size: float
    is_monospace: bool

    @property
    def bbox(self) -> tuple[float, float, float, float]:
        return (self.x0, self.y0, self.x1, self.y1)


LineFragmentDecision = Literal["merge_with_space", "preserve_separate"]


@dataclass(frozen=True)
class LineFragmentRelation:
    """The full geometric/documentary relation between two horizontally
    adjacent fragments sharing (or not) the same baseline - PROMPT Phase
    3H section 8, "FragmentRelation". Every signal is kept, never collapsed
    into the boolean ``decision`` before it is inspectable.
    """

    same_baseline: bool
    horizontal_gap: float
    gap_ratio: float
    gap_within_ceiling: bool
    left_had_trailing_space: bool
    font_size_compatible: bool
    both_non_monospace: bool
    decision: LineFragmentDecision


def compute_line_fragment_relation(
    left: RawLineFragment, right: RawLineFragment
) -> LineFragmentRelation:
    """Relation of ``right`` immediately following ``left`` in x-order.

    ``"merge_with_space"`` requires *every* one of: same page, matching
    baseline, both non-monospace, compatible font size, a positive gap
    within the safety ceiling, AND a literal trailing space on ``left``'s
    own raw text - never any one signal alone (see module docstring for
    why the gap ratio alone cannot discriminate a real table row).
    """
    same_page = left.page_number == right.page_number
    same_baseline = (
        same_page
        and abs(left.y0 - right.y0) <= BASELINE_TOLERANCE_PT
        and abs(left.y1 - right.y1) <= BASELINE_TOLERANCE_PT
    )
    gap = right.x0 - left.x1
    reference_font_size = max(left.font_size, right.font_size, 1.0)
    gap_ratio = gap / reference_font_size
    gap_within_ceiling = 0.0 <= gap <= MAX_FRAGMENT_GAP_RATIO * reference_font_size
    font_size_compatible = abs(left.font_size - right.font_size) <= FONT_SIZE_TOLERANCE_PT
    both_non_monospace = not left.is_monospace and not right.is_monospace
    left_had_trailing_space = left.raw_text.endswith(" ")

    decision: LineFragmentDecision = "preserve_separate"
    if (
        same_baseline
        and both_non_monospace
        and font_size_compatible
        and gap_within_ceiling
        and left_had_trailing_space
    ):
        decision = "merge_with_space"

    return LineFragmentRelation(
        same_baseline=same_baseline,
        horizontal_gap=gap,
        gap_ratio=gap_ratio,
        gap_within_ceiling=gap_within_ceiling,
        left_had_trailing_space=left_had_trailing_space,
        font_size_compatible=font_size_compatible,
        both_non_monospace=both_non_monospace,
        decision=decision,
    )


@dataclass(frozen=True)
class FragmentMergeTrace:
    """One deterministic, auditable record of a physical-line
    reconstruction decision - PROMPT Phase 3H section 15, "fragment-
    reconstruction trace". Participates in the same transformation-log
    mechanism as ``spacing.SpacingCorrection``/label_normalization's
    ``LabelCorrection`` (see ``transformation_log.py``).
    """

    page_number: int
    fragment_bboxes: tuple[tuple[float, float, float, float], ...]
    fragment_texts: tuple[str, ...]
    merged_bbox: tuple[float, float, float, float]

    def describe(self) -> str:
        joined = " + ".join(repr(t.strip()) for t in self.fragment_texts)
        return f"{len(self.fragment_bboxes)} fragments merged on p.{self.page_number}: {joined}"


def group_line_fragments(
    fragments: list[RawLineFragment],
    column_boundary: float | None = None,
) -> list[list[RawLineFragment]]:
    """Partition ``fragments`` (already restricted to one page) into the
    groups that should each form one physical line.

    Fragments are clustered by (near-identical) baseline, then walked in
    left-to-right (x0) order within each cluster, greedily merging every
    adjacent pair whose ``compute_line_fragment_relation`` returns
    ``"merge_with_space"``. A cluster whose members never satisfy the merge
    condition yields one singleton group per fragment - i.e. behaves
    exactly as if this mechanism did not exist (PROMPT: disabled behavior
    must be byte-identical to before).

    ``column_boundary`` (this page's own detected right-column left edge,
    from ``detect_column_margins`` run on the page's own *unmerged*
    fragments - see ``layout.py``) is required to reject a genuine
    same-baseline false positive found by direct instrumentation against
    the protected 2021 corpus: two independent, side-by-side objective
    questions whose own first line each happens to start at the identical
    y0 (immediately under their own "QUESTAO N" marker) can sit only a
    normal word-gap apart (the column *gutter*, not the wide gap between
    the two columns' own recurring left margins - MIN_COLUMN_SEPARATION
    governs the latter, not a single row's own visual gutter), with the
    left question's own last word of its own first (wrapping) line
    carrying a genuine trailing space - satisfying every other merge
    condition by coincidence. Never merging across this page's own
    already-established column boundary closes this without weakening the
    trailing-space/gap/baseline evidence that correctly handles every real
    fragmentation case found this phase.
    """
    baseline_groups: dict[tuple[float, float], list[RawLineFragment]] = {}
    for frag in fragments:
        key = _matching_baseline_key(frag, baseline_groups)
        baseline_groups.setdefault(key, []).append(frag)

    result: list[list[RawLineFragment]] = []
    for members in baseline_groups.values():
        members_sorted = sorted(members, key=lambda f: f.x0)
        current_group = [members_sorted[0]]
        for candidate in members_sorted[1:]:
            relation = compute_line_fragment_relation(current_group[-1], candidate)
            crosses_column_boundary = (
                column_boundary is not None
                and current_group[-1].x0 < column_boundary <= candidate.x0
            )
            if relation.decision == "merge_with_space" and not crosses_column_boundary:
                current_group.append(candidate)
            else:
                result.append(current_group)
                current_group = [candidate]
        result.append(current_group)
    return result


def _matching_baseline_key(
    frag: RawLineFragment,
    baseline_groups: dict[tuple[float, float], list[RawLineFragment]],
) -> tuple[float, float]:
    """Find an existing baseline bucket within tolerance, or start a new one.

    Linear scan over the page's own (typically small) number of distinct
    baselines - simplicity over a spatial index, matching this codebase's
    own established style for page-scoped geometry (e.g. ``figures.py``'s
    own region-merge loops).
    """
    for key in baseline_groups:
        if (
            abs(key[0] - frag.y0) <= BASELINE_TOLERANCE_PT
            and abs(key[1] - frag.y1) <= BASELINE_TOLERANCE_PT
        ):
            return key
    return (frag.y0, frag.y1)


def merged_bbox_of(group: list[RawLineFragment]) -> tuple[float, float, float, float]:
    return (
        min(f.x0 for f in group),
        min(f.y0 for f in group),
        max(f.x1 for f in group),
        max(f.y1 for f in group),
    )
