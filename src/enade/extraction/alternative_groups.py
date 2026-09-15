"""Structural detection of the A-E alternative marker sequence as one group,
rather than five independent tokens (PROMPT Phase 3I).

## Root cause this replaces (investigated in Phase 3H, confirmed in Phase 3I)

The previous mechanism (``assembler._find_alternative_starts``) does a purely
textual, right-to-left search: for each letter, take the *last* line whose
own text matches ``^([A-E])(?:[\\t ](.*))?$`` before the next higher letter's
own chosen position. This works for the overwhelming majority of questions,
where each letter has exactly one such line on the page - but it has no
notion of a "marker candidate competing with another candidate for the same
letter", so when a question's own real prose happens to contain a *second*
line that also starts with a bare capital letter A-E followed by a space
(never a coincidence found in a diagram - Cluster C already keeps diagram-
internal labels out of ``text_only_lines`` entirely, see module docstring
below - but a perfectly ordinary paragraph wrap can produce this shape), it
silently prefers whichever one sits later in reading order, without ever
checking whether that candidate actually *looks* like the other four.

Confirmed real case (2008-b Q71, page 30): alternative B's own prose wraps
across two printed lines - "...dos módulos B e" / "C é maior e o
acoplamento do projeto é maior." - and that second line, read alone, matches
the marker shape (`"C  é maior..."`) exactly as well as the *real* C marker
sitting elsewhere on the page. The old algorithm's blind "last match wins"
rule picked the wrong one, swallowing C's own real opening lines into B's
own alternative text.

## The structural, non-semantic signal

Every real marker in this corpus sits at (very nearly) the same horizontal
position - the alternatives' own left margin, which line-wrapped body prose
never coincidentally reproduces (a continuation line's own left edge is
offset by the marker's own width, exactly as the false C candidate above
sits ~18pt to the right of the real markers' shared x0). This is the *same*
category of structural evidence ``figures._is_marker_at_margin`` already
uses for a different purpose (Cluster C) - never the marker's own printed
letter or a dictionary/semantic judgment of the surrounding text.

Because a genuine multi-candidate collision is rare, the reference margin
for a given question is derived from the candidates themselves (the mode of
their own x0, rounded to a small bucket) rather than from a separate,
page-wide "body margin" signal - this keeps the mechanism self-contained
and correct even on a page where the page-wide dominant margin belongs to a
*different* question sharing that page (2008-b page 30 also carries Q70's
own alternatives in a different column).

## What this does NOT do

- It never promotes a bare token to an alternative in isolation - a letter
  is only accepted once the *whole* A-E sequence resolves together.
- It never consults the answer key/gabarito to pick among candidates.
- It never invents a missing label to complete a sequence.

## Margin is a refinement on top of reading order, never a replacement

The pre-existing "last candidate before the next letter wins" rule already
correctly rejects the single most common false-candidate shape in this
corpus: a statement's own prose that happens to start with a bare capital
letter (module docstring precedent: "A chance de uma crianca..." must never
be mistaken for alternative A). That prose line and the real markers
typically share the *same* left margin in this corpus (alternatives are not
extra-indented relative to the statement), so margin alone cannot tell them
apart - only reading order can (the real marker always sits closer to the
next one) - confirmed by two further real cases found while validating this
exact mechanism (2008-b Q28's own "A que classes corresponderiam..." and
Q52's own "A partir dessas informações, assinale..." each sit at the very
same margin as their own page's real markers, and an earlier, stricter
version of this algorithm that treated "2+ on-margin candidates" as
unresolvable wrongly excluded both questions entirely - PROMPT's own
"nenhum caso aprovado pode regredir"). Margin is therefore consulted only
when it actually *partitions* a letter's own candidates into a genuine,
strict on-margin subset (at least one candidate excluded) - reading order
still breaks every remaining tie, both within that subset and when margin
does not partition at all (every candidate on-margin, or none). This means
``AlternativeGroupStatus`` keeps an ``"ambiguous"`` value for architectural
completeness (PROMPT section 12's own tri-state requirement) and
``AlternativeGroup.competing`` still records every multi-candidate letter
for audit, but no rule in this module currently *produces* ``"ambiguous"``
- every real multi-candidate collision found in the full 2008-b/2011/2021
corpus resolves deterministically via on-margin-then-reading-order, and
inventing a stricter trigger without a real corpus case to justify it would
itself violate the "nao introduza uma capacidade sem exemplo positivo e
negativo real" principle (docs/generalization-contract.md section 1.1).
phase.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import Literal

from enade.extraction.layout import Line

#: Same shape as ``assembler._ALTERNATIVE_LINE_RE`` - duplicated rather than
#: imported to keep this module self-contained (mirrors
#: ``fragment_reconstruction.py``'s own style) and because assembler.py
#: itself imports from this module, which would make the reverse import
#: circular.
_ALTERNATIVE_LINE_RE = re.compile(r"^([A-E])(?:[\t ](.*))?$")

#: The only label scheme this corpus (2008-b/2011/2021) has ever required -
#: five, strictly-ordered, upper-case Latin letters. PROMPT section 7 asks
#: for a "declarative label scheme" interface without pretending more
#: schemes are implemented than the corpus actually needs; a profile-level
#: ``alternative_label_schemes``/``expected_alternative_count`` field is
#: intentionally not added here, since nothing in this corpus varies it -
#: adding an unexercised knob would be speculative generality, not
#: generalization (see docs/generalization-contract.md section 1.1: "nao
#: introduza uma capacidade sem pelo menos um exemplo positivo e um
#: negativo").
LabelScheme = tuple[str, ...]
LATIN_UPPER_SCHEME: LabelScheme = ("A", "B", "C", "D", "E")

#: Tolerance (points) for treating two candidates' own x0 as "the same
#: margin" - mirrors ``figures._MARGIN_TOLERANCE`` (duplicated, not
#: imported, for the same self-containment reason as the regex above).
MARGIN_TOLERANCE = 5.0

AlternativeGroupStatus = Literal["resolved", "ambiguous", "incomplete"]


@dataclass(frozen=True)
class AlternativeMarkerCandidate:
    """One line whose own text matches the marker shape for ``letter`` -
    PROMPT Phase 3I section 6, "AlternativeMarkerCandidate". Not yet a
    decision - a question can (and, rarely, does) have more than one
    candidate for the same letter; see ``AlternativeGroup.competing``.
    """

    letter: str
    line_index: int
    x0: float
    y0: float
    page_number: int


@dataclass(frozen=True)
class AlternativeGroup:
    """The outcome of evaluating every marker-shaped line on a question's
    own ``text_only_lines`` *as one group*, rather than five independent
    tokens - PROMPT Phase 3I section 8.

    ``accepted`` has the exact shape ``assembler._find_alternative_starts``
    used to return (letter -> index into the caller's own line list), so it
    is a drop-in replacement at the call site. ``status`` is the tri-state
    PROMPT section 12 requires: ``"resolved"`` (safe to use), ``"ambiguous"``
    (reserved for a genuinely unresolved competing-candidate tie - see the
    module docstring's own "Margin is a refinement..." section for why no
    rule in this module currently produces it, given the full corpus's own
    evidence), or ``"incomplete"`` (the full A-E sequence was never found at
    all - the pre-existing, already-correct "no sequence" case).
    """

    label_scheme: LabelScheme
    status: AlternativeGroupStatus
    accepted: dict[str, int]
    reference_margin: float | None
    #: letter -> every candidate line-index found for it (including the
    #: one ultimately accepted) - populated only for letters with more
    #: than one candidate, for audit/trace purposes (PROMPT section 12:
    #: "registre a decisão").
    competing: dict[str, tuple[int, ...]]

    @property
    def is_usable(self) -> bool:
        return self.status == "resolved"


#: The mode must be backed by at least this many candidates before it is
#: trusted as a real margin at all - see ``_reference_margin``'s own
#: docstring for the real corpus shape (2011 Q39) that requires this.
_MIN_MARGIN_VOTES = 2


def _reference_margin(candidates: list[AlternativeMarkerCandidate]) -> float | None:
    """The most common x0 (rounded to whole points) among every candidate
    found for this question, regardless of letter - real markers in a
    normal, vertically-stacked A-E list vastly outnumber any coincidental
    text-shape collision (5 real votes vs. at most 1 false one), so the
    mode is a robust, self-contained reference even without a separate
    page-wide margin signal.

    Real regression found and fixed this phase (2011 Q39, page 25): some
    questions lay their own five alternatives out *horizontally*, one
    per column on the same row ("A I.  B II.  C I e III. ..."), each at
    its own genuinely distinct x0 - there is no shared margin at all, so
    every candidate's own x0 is unique and the "mode" degenerates to
    whichever one happens to be encountered first, with no real
    statistical backing. Requiring at least ``_MIN_MARGIN_VOTES`` real
    votes before trusting the result treats that case as "no reference
    margin available" (``None``), which correctly makes every letter's
    own resolution defer entirely to reading order - never a data point
    the algorithm invents confidence for.
    """
    if not candidates:
        return None
    votes = Counter(round(c.x0) for c in candidates)
    margin, count = votes.most_common(1)[0]
    return float(margin) if count >= _MIN_MARGIN_VOTES else None


def find_alternative_group(lines: list[Line]) -> AlternativeGroup | None:
    """Evaluate every marker-shaped line in ``lines`` as one A-E group.

    Returns ``None`` when letter E never occurs at all (mirrors
    ``_find_alternative_starts``'s own "not even a partial sequence"
    case). Otherwise always returns a group - callers must check
    ``status``/``is_usable`` before trusting ``accepted`` (an
    ``"incomplete"`` or ``"ambiguous"`` group's own ``accepted`` dict may
    be partial or contain a placeholder guess for an ambiguous letter, and
    must be treated exactly like "no sequence found").
    """
    candidates_by_letter: dict[str, list[AlternativeMarkerCandidate]] = {
        letter: [] for letter in LATIN_UPPER_SCHEME
    }
    for index, line in enumerate(lines):
        match = _ALTERNATIVE_LINE_RE.match(line.text)
        if match:
            candidates_by_letter[match.group(1)].append(
                AlternativeMarkerCandidate(
                    letter=match.group(1),
                    line_index=index,
                    x0=line.x0,
                    y0=line.y0,
                    page_number=line.page_number,
                )
            )

    last_letter = LATIN_UPPER_SCHEME[-1]
    if not candidates_by_letter[last_letter]:
        return None

    reference_margin = _reference_margin(
        [c for candidates in candidates_by_letter.values() for c in candidates]
    )

    accepted: dict[str, int] = {}
    competing: dict[str, tuple[int, ...]] = {}
    upper_bound = len(lines)
    for letter in reversed(LATIN_UPPER_SCHEME):
        own_candidates = [c for c in candidates_by_letter[letter] if c.line_index < upper_bound]
        if not own_candidates:
            return AlternativeGroup(
                label_scheme=LATIN_UPPER_SCHEME,
                status="incomplete",
                accepted=accepted,
                reference_margin=reference_margin,
                competing=competing,
            )
        if len(own_candidates) == 1:
            chosen = own_candidates[0]
        else:
            competing[letter] = tuple(c.line_index for c in own_candidates)
            on_margin = [
                c
                for c in own_candidates
                if reference_margin is not None
                and abs(round(c.x0) - reference_margin) <= MARGIN_TOLERANCE
            ]
            # Prefer the on-margin subset only when margin actually
            # partitions this letter's own candidates (a genuine, strict
            # subset - at least one candidate excluded). Real evidence
            # from every multi-candidate case found in the full corpus
            # (2008-b Q28/Q52/Q71, 2011/2021's own "prose starting with a
            # bare capital letter" shape) shows this is never a two-way
            # tie once margin is applied: reading order (last candidate
            # before the next letter) always resolves the remainder
            # correctly, exactly as the pre-existing mechanism already
            # did - a bare "on-margin count > 1" is common (two ordinary
            # prose sentences can easily share the page's own body
            # margin) and must not, by itself, block the question.
            pool = (
                on_margin if on_margin and len(on_margin) < len(own_candidates) else own_candidates
            )
            chosen = pool[-1]
        accepted[letter] = chosen.line_index
        upper_bound = chosen.line_index

    return AlternativeGroup(
        label_scheme=LATIN_UPPER_SCHEME,
        status="resolved",
        accepted=accepted,
        reference_margin=reference_margin,
        competing=competing,
    )
