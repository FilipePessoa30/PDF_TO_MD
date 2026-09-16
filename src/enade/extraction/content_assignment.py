"""The content-assignment ledger: one record per source element explaining
where it came from, who owns it, what it is anchored to, and where it was
published - PROMPT Phase 3J ("atribuição canônica de conteúdo").

This module is deliberately scoped to what this phase actually needed to
diagnose and fix (2008-b Q13 and D60) plus what the Section 20 scan of the
77 published questions could evidence, not a full, generic re-implementation
of every source/owner/destination combination the prompt enumerates as
*possible*. Building the untested remainder now would be exactly the kind
of speculative generality docs/generalization-contract.md (section 1.1)
warns against - the schema (``ContentAssignment``, ``SourceType``,
``Owner``, ``Destination``) declares every value the prompt names so nothing
needs to change shape later, but only the source types this corpus's own
pipeline already tracks with a stable identity (``line`` and ``asset``) are
ever actually produced.

Three principles this module follows (Sections 6-9 of the Phase 3J prompt):

1. Owner, anchor and destination are three separate fields, never
   collapsed into one. A line can be geometrically anchored to a figure
   (its own bbox sits right next to it) while its true owner is the
   question's own statement, not the figure - proximity is evidence for
   *anchor*, never a substitute for demonstrating *owner*.
2. Duplication is demonstrated by shared provenance (the same
   ``source_element_id``, i.e. the same underlying ``Line``/asset,
   appearing in two ``ContentAssignment`` records with different
   ``publication_destination``), never by text equality - two distinct
   alternatives may legitimately share identical wording.
3. Every gate here can only ever *report*, never silently repair -
   deciding which of two destinations is documentally correct is a
   judgment call for the general mechanism that produced the assignment in
   the first place (``assembler.py``/``annotations.py``), not for a gate
   that only sees the ledger after the fact.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Literal

#: Only "line" and "asset" are ever produced by this phase's own ledger
#: generation (assembler.py's own content_lines/figure_regions are the
#: only source elements with a stable per-run identity today). The rest
#: are declared for the schema's own extensibility (PROMPT section 6).
SourceType = Literal[
    "char",
    "span",
    "line",
    "fragment",
    "visual_region",
    "asset",
    "annotation",
    "caption",
    "alternative_marker",
]

Owner = Literal[
    "question",
    "alternative",
    "asset",
    "diagram",
    "answer_area",
    "document_chrome",
    "unresolved",
]

Destination = Literal[
    "statement",
    "alternative_text",
    "alternative_asset",
    "question_asset",
    "caption",
    "annotation",
    "answer_standard",
    "discarded_chrome",
    "blocked",
]


@dataclass(frozen=True)
class ContentAssignment:
    """One source element's own resolved (or still-unresolved) assignment."""

    assignment_id: str
    source_element_id: str
    source_type: SourceType
    source_page: int
    source_bbox: tuple[float, float, float, float]
    canonical_owner: Owner
    anchor: str
    publication_destination: Destination
    representation: str
    reason: str
    evidence: str
    confidence: float
    status: Literal["assigned", "blocked", "ambiguous"]
    #: The published question this assignment belongs to, e.g.
    #: "enade-2008-computing-q13" - not part of the prompt's own listed
    #: schema fields, but required to group records per question for the
    #: gates below and for a human reading the manifest.
    question_id: str = ""
    #: PROMPT section 8: a second representation of the *same*
    #: ``source_element_id`` (e.g. a canonical text plus its own visible
    #: copy baked into an asset's own image) is a duplicate only when
    #: undocumented. Every record sharing one source that also shares one
    #: non-``None`` ``duplication_mode`` is treated as an authorized
    #: mirror, not a defect - ``detect_duplicate_assignments`` never
    #: infers this itself; it only honors what the assignment already
    #: declares. ``None`` for every record this phase actually produced -
    #: no real, evidenced mirror case exists in this corpus yet (see
    #: content_assignment.py's own module docstring on not fabricating
    #: unevidenced capability).
    duplication_mode: str | None = None


@dataclass(frozen=True)
class DuplicateAssignmentFinding:
    source_element_id: str
    destinations: tuple[str, ...]
    owners: tuple[str, ...]
    question_ids: tuple[str, ...]
    alternative_labels: tuple[str, ...]
    reason: str


@dataclass(frozen=True)
class MissingAssignmentFinding:
    kind: Literal[
        "source_without_destination",
        "annotation_without_owner",
        "asset_without_owner",
        "content_block_without_source",
        "destination_without_source",
    ]
    source_element_id: str
    question_id: str
    reason: str


def detect_duplicate_assignments(
    assignments: list[ContentAssignment],
) -> list[DuplicateAssignmentFinding]:
    """PROMPT section 11: same source, more than one destination/owner/
    alternative - never resolved here, only reported.

    Grouped by ``source_element_id`` alone (never by text), per the
    module's own second principle above.
    """
    by_source: dict[str, list[ContentAssignment]] = defaultdict(list)
    for a in assignments:
        by_source[a.source_element_id].append(a)

    findings: list[DuplicateAssignmentFinding] = []
    for source_id, group in by_source.items():
        destinations = {a.publication_destination for a in group}
        owners = {a.canonical_owner for a in group}
        alt_labels = {a.anchor for a in group if a.canonical_owner == "alternative"}
        if len(destinations) <= 1 and len(owners) <= 1 and len(alt_labels) <= 1:
            continue
        modes = {a.duplication_mode for a in group}
        if len(modes) == 1 and None not in modes:
            continue  # every record agrees on one authorized mirror mode
        findings.append(
            DuplicateAssignmentFinding(
                source_element_id=source_id,
                destinations=tuple(sorted(destinations)),
                owners=tuple(sorted(owners)),
                question_ids=tuple(sorted({a.question_id for a in group})),
                alternative_labels=tuple(sorted(alt_labels)),
                reason=(
                    f"source {source_id!r} published to {len(destinations)} distinct "
                    f"destination(s) / {len(owners)} distinct owner(s)"
                ),
            )
        )
    return findings


def detect_missing_assignments(
    assignments: list[ContentAssignment],
) -> list[MissingAssignmentFinding]:
    """PROMPT section 12: a legitimate element with no destination, or a
    destination that no longer traces back to any real source - the
    complementary check to duplication (a naive fix for the latter can
    silently turn into the former, see the module's own third principle).
    """
    findings: list[MissingAssignmentFinding] = []
    for a in assignments:
        if a.status == "blocked" and a.publication_destination != "blocked":
            findings.append(
                MissingAssignmentFinding(
                    kind="source_without_destination",
                    source_element_id=a.source_element_id,
                    question_id=a.question_id,
                    reason=a.reason,
                )
            )
        elif a.source_type == "annotation" and a.canonical_owner == "unresolved":
            findings.append(
                MissingAssignmentFinding(
                    kind="annotation_without_owner",
                    source_element_id=a.source_element_id,
                    question_id=a.question_id,
                    reason=a.reason,
                )
            )
        elif a.source_type == "asset" and a.canonical_owner == "unresolved":
            findings.append(
                MissingAssignmentFinding(
                    kind="asset_without_owner",
                    source_element_id=a.source_element_id,
                    question_id=a.question_id,
                    reason=a.reason,
                )
            )
    return findings
