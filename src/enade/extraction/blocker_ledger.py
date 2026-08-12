"""Canonical, machine-readable ledger of readiness blockers (PROMPT Phase
2C section 3).

Phase 2B's own readiness gate reported "32 blocker(s)" as free-form printed
lines - real and accurate, but not a durable, individually-trackable
record: nothing stopped a blocker from silently vanishing between runs, or
a new one from being added without anyone noticing the total had changed.
This module gives each of those 32 (and any later addition) a stable id
and an explicit status, so a report can be *derived* from the ledger
rather than re-typed by hand, and a gate can assert the ledger's own
internal bookkeeping is consistent.

32 is never treated as an eternal truth - it is recorded once, as the
Phase 2B baseline (``PHASE_2B_BASELINE_COUNT``), and the ledger is free to
grow as investigation finds more blockers or shrink as they resolve.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

#: The blocker count Phase 2B's own readiness gate reported at the end of
#: that phase - a historical baseline value, not a target or a ceiling.
PHASE_2B_BASELINE_COUNT = 32

BlockerStatus = Literal[
    "open",
    "resolved",
    "resolved_by_structured_extraction",
    "resolved_by_visual_fallback",
    "source_ambiguity",
    "superseded",
    "not_reproducible",
]

_TERMINAL_STATUSES: frozenset[str] = frozenset(
    {
        "resolved",
        "resolved_by_structured_extraction",
        "resolved_by_visual_fallback",
        "superseded",
        "source_ambiguity",
        "not_reproducible",
    }
)


class Blocker(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1)
    question_id: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1)
    source_pages: list[int] = Field(default_factory=list)
    description: str = Field(..., min_length=1)
    cause: str = Field(..., min_length=1)
    status: BlockerStatus
    resolution: str | None = None
    evidence: str | None = None
    affected_assets: list[str] = Field(default_factory=list)
    regression_tests: list[str] = Field(default_factory=list)
    visual_validation: str | None = None
    #: Required, and must name another blocker's own id, when status is
    #: "superseded" - PROMPT Phase 2C section 3, rule 4.
    superseded_by: str | None = None

    @property
    def is_open(self) -> bool:
        return self.status == "open"

    @property
    def is_terminal(self) -> bool:
        return self.status in _TERMINAL_STATUSES


class BlockerLedger(BaseModel):
    model_config = ConfigDict(extra="forbid")

    baseline_count: int = PHASE_2B_BASELINE_COUNT
    blockers: list[Blocker] = Field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.blockers)

    @property
    def open_count(self) -> int:
        return sum(1 for b in self.blockers if b.status == "open")

    @property
    def resolved_count(self) -> int:
        return sum(
            1
            for b in self.blockers
            if b.status
            in ("resolved", "resolved_by_structured_extraction", "resolved_by_visual_fallback")
        )

    @property
    def superseded_count(self) -> int:
        return sum(1 for b in self.blockers if b.status == "superseded")

    @property
    def source_ambiguity_count(self) -> int:
        return sum(1 for b in self.blockers if b.status == "source_ambiguity")

    @property
    def not_reproducible_count(self) -> int:
        return sum(1 for b in self.blockers if b.status == "not_reproducible")

    def by_id(self, blocker_id: str) -> Blocker | None:
        return next((b for b in self.blockers if b.id == blocker_id), None)


class BlockerLedgerIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: str
    detail: str


def validate_ledger(ledger: BlockerLedger) -> list[BlockerLedgerIssue]:
    """PROMPT Phase 2C section 3's own consistency gates.

    Never raises - returns every violation found, so a caller can report
    all of them at once (matching this codebase's existing convention, see
    virtual_exam.py's validate_virtual_exam_set).
    """
    issues: list[BlockerLedgerIssue] = []

    ids = [b.id for b in ledger.blockers]
    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    if duplicates:
        issues.append(
            BlockerLedgerIssue(kind="duplicate_id", detail=f"duplicate blocker id(s): {duplicates}")
        )

    known_ids = set(ids)
    for blocker in ledger.blockers:
        if blocker.status == "superseded":
            if not blocker.superseded_by:
                issues.append(
                    BlockerLedgerIssue(
                        kind="missing_supersedes_reference",
                        detail=f"{blocker.id}: status=superseded but superseded_by is not set",
                    )
                )
            elif blocker.superseded_by not in known_ids:
                issues.append(
                    BlockerLedgerIssue(
                        kind="dangling_supersedes_reference",
                        detail=(
                            f"{blocker.id}: superseded_by={blocker.superseded_by!r} "
                            "does not match any blocker id in this ledger"
                        ),
                    )
                )
        if blocker.status in (
            "resolved",
            "resolved_by_structured_extraction",
            "resolved_by_visual_fallback",
        ):
            if not blocker.evidence:
                issues.append(
                    BlockerLedgerIssue(
                        kind="resolved_without_evidence",
                        detail=f"{blocker.id}: status={blocker.status!r} requires evidence",
                    )
                )
            if not blocker.regression_tests:
                issues.append(
                    BlockerLedgerIssue(
                        kind="resolved_without_test",
                        detail=(
                            f"{blocker.id}: status={blocker.status!r} requires at least one "
                            "regression test"
                        ),
                    )
                )
        if blocker.status == "resolved_by_visual_fallback" and not blocker.affected_assets:
            issues.append(
                BlockerLedgerIssue(
                    kind="visual_fallback_without_asset",
                    detail=(
                        f"{blocker.id}: status=resolved_by_visual_fallback requires at least "
                        "one asset in affected_assets"
                    ),
                )
            )

    accounted = (
        ledger.open_count
        + ledger.resolved_count
        + ledger.superseded_count
        + ledger.source_ambiguity_count
        + ledger.not_reproducible_count
    )
    if accounted != ledger.total:
        issues.append(
            BlockerLedgerIssue(
                kind="status_count_mismatch",
                detail=(
                    f"open({ledger.open_count}) + resolved({ledger.resolved_count}) + "
                    f"superseded({ledger.superseded_count}) + "
                    f"source_ambiguity({ledger.source_ambiguity_count}) + "
                    f"not_reproducible({ledger.not_reproducible_count}) = {accounted}, "
                    f"expected total = {ledger.total}"
                ),
            )
        )

    return issues


def load_blocker_ledger(path: Path) -> BlockerLedger:
    if not path.exists():
        return BlockerLedger()
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return BlockerLedger.model_validate(data)
