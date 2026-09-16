"""Document annotations: text that is structurally tied to one specific
part of a question (an item, an alternative, an asset) rather than being
ordinary running prose - PROMPT Phase 3J ("atribuição canônica de
conteúdo").

Root cause this module exists to fix (2008-b D60, page 26): a discursive
question's own per-item "(valor: X pontos)" scoring annotations are
typeset in a narrow column of their own, to the right of each item's own
text and its "RASCUNHO" scratch-answer label - not inline with the item's
own running text. ``layout.extract_page_lines``'s own column-major reading
order (correctly, for the *page's* two real content columns) places that
whole narrow annotation column *after* every other column on the page, so
all three annotations end up bunched together at the very end of the
question's own line list, in their own correct relative order (A's, then
B's, then C's) but geometrically detached from the items they belong to.
``assembler._build_statement_segments``'s own paragraph-merge heuristic
then does the wrong thing twice: it glues the *first* orphaned annotation
onto whichever line happens to precede it in that list (item C's own last
line - regardless of the fact that this annotation really belongs to A),
because the geometric "gap" between them is computed from raw y0/y1
values that are no longer monotonically increasing once column order and
list order diverge; the other two annotations, with a genuinely large gap
between them, are left as two disconnected trailing paragraphs.

This is a "wrong destination" bug (Section 6 of the Phase 3J prompt): the
annotation is detected correctly (its own text is intact, never lost) but
published in the wrong place, and worse, a *different* annotation's own
text is silently misattributed to the wrong item (item C published with
A's own 3,0-point value, not its real 4,0). Proximity in the buggy reading
order is not evidence of ownership - the fix reattaches each annotation to
the item whose own printed vertical span actually contains it, using each
item's own real geometry, never reading-order adjacency and never the
annotation's own text content beyond confirming it *is* a value
annotation in the first place (PROMPT section 17: "não use apenas o texto
'valor'... não associe pelo elemento geometricamente mais próximo sem
verificar a estrutura" - the structural check here is interval
containment against each item's own real y-range, not nearest-neighbor
distance).

Scope: only ``question_value`` annotations have a real, evidenced
positive *and* negative case in this corpus (D60 broken; D9/D10/D20/D39/
D40/D59/D79/D80 and every 2011/2021 discursive question already correct).
``AnnotationType`` declares the other types the Phase 3J prompt names
(``instruction``, ``figure_reference``, ...) so the architecture is
extensible, but no detection logic is implemented for them - inventing
one without a real corpus example would be exactly the kind of
speculative generality ``docs/generalization-contract.md`` (section 1.1)
warns against.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from enade.extraction.layout import Line

#: Declared for architectural extensibility (PROMPT Phase 3J section 16) -
#: only "question_value" has real detection logic this phase, backed by a
#: genuine positive case (D60) and genuine negative cases (D9/D10/D20/D39/
#: D40/D59/D79/D80, all already correctly attached).
AnnotationType = Literal[
    "question_value",
    "instruction",
    "figure_reference",
    "table_reference",
    "source_citation",
    "answer_area_label",
    "section_note",
    "chrome",
    "ambiguous",
]

#: A parenthesized scoring annotation: "(valor: 3,0 pontos)", "(valor: 10
#: pontos)", "(valor: 4,0 ponto)" - decimal separator, singular/plural and
#: whitespace vary across the corpus but the shape is otherwise fixed.
_VALUE_ANNOTATION_RE = re.compile(r"^\(valor:\s*[\d.,]+\s*pontos?\)$", re.IGNORECASE)

#: A discursive item's own marker line: a single letter A-E, optionally
#: followed by its own inline text - the same textual shape as
#: ``assembler._ALTERNATIVE_LINE_RE`` / ``alternative_groups.
#: _ALTERNATIVE_LINE_RE``, duplicated locally (rather than imported) so
#: this module never depends on the multiple-choice-only alternative
#: machinery: a discursive question's own lettered items (2-4 of them,
#: never required to reach E) are a structurally distinct concept from a
#: multiple-choice question's own 5-way alternative group, even though
#: both happen to share one text shape in this corpus.
_ITEM_MARKER_RE = re.compile(r"^([A-E])(?:[\t ](.*))?$")


@dataclass(frozen=True)
class DocumentAnnotation:
    """One detected annotation and how it was resolved.

    ``source_line_index`` is this annotation's own position in the
    *input* line list (before any reattachment) - the evidence trail
    Section 10 of the Phase 3J prompt asks the assignment ledger to be
    able to answer "where did this come from" with. ``owner_item_letter``
    is ``None`` only when no item markers were found at all (the
    annotation is left exactly where it was, in that case - see
    ``reattach_value_annotations``). ``reattached`` is coarse (index-range
    based against the owning item's own original [start, next-item-start)
    slice, not exact-adjacency based): when several annotations are
    bunched together at the very end of a list whose last item legitimately
    owns one of them, that one can read as "already in place" even though
    other, unrelated annotations originally sat between it and its own
    item's own real content - true for the published *content* (which is
    always rebuilt from scratch, never left partially unmoved), not
    necessarily for this one metadata flag's own precision.
    """

    annotation_type: AnnotationType
    text: str
    source_page: int
    source_line_index: int
    owner_item_letter: str | None
    reattached: bool


def find_item_markers(lines: list[Line]) -> list[tuple[str, int]]:
    """Return ``(letter, line_index)`` for the strictly increasing A, B, C,
    ... prefix of item markers found in ``lines``, in list order.

    Only the *first* occurrence of each expected next letter counts - a
    later, out-of-sequence letter-shaped line (ordinary prose starting
    with a capital letter, exactly the same false-positive shape
    ``alternative_groups`` already has to guard against) is silently
    skipped rather than restarting or aborting the sequence, since a
    discursive item list is always short (2-4 items in this corpus) and
    printed in strict order with no analogue of the multiple-choice
    margin/competing-candidate ambiguity that motivates the fuller
    ``AlternativeGroup`` machinery.
    """
    markers: list[tuple[str, int]] = []
    expected = ord("A")
    for i, ln in enumerate(lines):
        match = _ITEM_MARKER_RE.match(ln.text)
        if not match:
            continue
        letter = match.group(1)
        if ord(letter) == expected:
            markers.append((letter, i))
            expected += 1
        if expected > ord("E"):
            break
    return markers


def reattach_value_annotations(lines: list[Line]) -> tuple[list[Line], list[DocumentAnnotation]]:
    """Move each "(valor: ...)" annotation next to the item it structurally
    belongs to, and return the resulting line list plus a trace record.

    A true no-op (returns ``lines`` unchanged, by identity) whenever no
    line matches ``_VALUE_ANNOTATION_RE`` at all - the overwhelming
    majority of questions, objective and discursive alike, never reach
    the reordering logic below at all. Also produces byte-identical
    output when every annotation found is *already* structurally inside
    its owning item's own span (2008-b D80, D20, D40, D79's own separately
    -lined annotations; every fused-inline "... (valor: X pontos)" tail
    never matches ``_VALUE_ANNOTATION_RE`` as a whole line in the first
    place and is never touched at all) - the trace still records these,
    with ``reattached=False``, so the assignment ledger can tell "checked,
    already correct" apart from "never checked".
    """
    annotation_indices = [i for i, ln in enumerate(lines) if _VALUE_ANNOTATION_RE.match(ln.text)]
    if not annotation_indices:
        return lines, []

    item_markers = find_item_markers(lines)
    annotation_set = set(annotation_indices)

    if not item_markers:
        # No lettered items to attribute against (e.g. a single overall
        # "(valor: 10,0 pontos)" for a whole discursive question with no
        # per-item breakdown) - nothing to disambiguate against, left as is.
        trace = [
            DocumentAnnotation(
                annotation_type="question_value",
                text=lines[i].text,
                source_page=lines[i].page_number,
                source_line_index=i,
                owner_item_letter=None,
                reattached=False,
            )
            for i in annotation_indices
        ]
        return lines, trace

    marker_indices = [idx for _, idx in item_markers]

    # Item k "owns" every annotation whose own (page, y0) falls at or
    # after item k's own position and before item k+1's own position -
    # i.e. structural interval containment against each item's own real
    # geometry, never against the annotation's own position in the
    # (possibly column-scrambled) reading order.
    def _owner_of(i: int) -> int:
        key = (lines[i].page_number, lines[i].y0)
        owner = 0
        for k, idx in enumerate(marker_indices):
            if (lines[idx].page_number, lines[idx].y0) <= key:
                owner = k
            else:
                break
        return owner

    owners = {i: _owner_of(i) for i in annotation_indices}

    def _segment_end(owner: int) -> int:
        return marker_indices[owner + 1] if owner + 1 < len(marker_indices) else len(lines)

    result: list[Line] = [lines[i] for i in range(marker_indices[0]) if i not in annotation_set]
    for k, idx in enumerate(marker_indices):
        end = _segment_end(k)
        result.extend(lines[i] for i in range(idx, end) if i not in annotation_set)
        result.extend(lines[i] for i in annotation_indices if owners[i] == k)

    trace = [
        DocumentAnnotation(
            annotation_type="question_value",
            text=lines[i].text,
            source_page=lines[i].page_number,
            source_line_index=i,
            owner_item_letter=item_markers[owners[i]][0],
            reattached=not (marker_indices[owners[i]] <= i < _segment_end(owners[i])),
        )
        for i in annotation_indices
    ]
    return result, trace
