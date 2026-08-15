from __future__ import annotations

from pathlib import Path

from enade.extraction.blocker_ledger import (
    PHASE_2B_BASELINE_COUNT,
    Blocker,
    BlockerLedger,
    load_blocker_ledger,
    validate_ledger,
)


def _blocker(**overrides) -> Blocker:
    base = dict(
        id="test-blocker",
        question_id="enade-2011-computing-q01",
        category="test",
        description="a test blocker",
        cause="a test cause",
        status="open",
    )
    base.update(overrides)
    return Blocker(**base)


def test_load_blocker_ledger_reads_the_real_yaml():
    path = Path("data/manifests/blocker-ledger-2011.yaml")
    ledger = load_blocker_ledger(path)
    assert ledger.total >= PHASE_2B_BASELINE_COUNT
    assert ledger.baseline_count == PHASE_2B_BASELINE_COUNT
    assert validate_ledger(ledger) == []


def test_load_blocker_ledger_missing_file_returns_empty(tmp_path: Path):
    ledger = load_blocker_ledger(tmp_path / "does-not-exist.yaml")
    assert ledger.blockers == []
    assert ledger.total == 0


def test_validate_ledger_flags_duplicate_ids():
    ledger = BlockerLedger(blockers=[_blocker(id="dup"), _blocker(id="dup")])
    issues = validate_ledger(ledger)
    assert any(i.kind == "duplicate_id" for i in issues)


def test_validate_ledger_flags_superseded_without_reference():
    ledger = BlockerLedger(blockers=[_blocker(status="superseded", superseded_by=None)])
    issues = validate_ledger(ledger)
    assert any(i.kind == "missing_supersedes_reference" for i in issues)


def test_validate_ledger_flags_dangling_supersedes_reference():
    ledger = BlockerLedger(
        blockers=[_blocker(id="a", status="superseded", superseded_by="does-not-exist")]
    )
    issues = validate_ledger(ledger)
    assert any(i.kind == "dangling_supersedes_reference" for i in issues)


def test_validate_ledger_accepts_a_valid_supersedes_reference():
    ledger = BlockerLedger(
        blockers=[
            _blocker(id="a", status="superseded", superseded_by="b"),
            _blocker(id="b", status="open"),
        ]
    )
    issues = validate_ledger(ledger)
    assert not any(
        i.kind in ("missing_supersedes_reference", "dangling_supersedes_reference") for i in issues
    )


def test_validate_ledger_flags_resolved_without_evidence():
    ledger = BlockerLedger(
        blockers=[_blocker(status="resolved", evidence=None, regression_tests=["tests/test_x.py"])]
    )
    issues = validate_ledger(ledger)
    assert any(i.kind == "resolved_without_evidence" for i in issues)


def test_validate_ledger_flags_resolved_without_test():
    ledger = BlockerLedger(
        blockers=[_blocker(status="resolved", evidence="some evidence", regression_tests=[])]
    )
    issues = validate_ledger(ledger)
    assert any(i.kind == "resolved_without_test" for i in issues)


def test_validate_ledger_flags_visual_fallback_without_asset():
    ledger = BlockerLedger(
        blockers=[
            _blocker(
                status="resolved_by_visual_fallback",
                evidence="some evidence",
                regression_tests=["tests/test_x.py"],
                affected_assets=[],
            )
        ]
    )
    issues = validate_ledger(ledger)
    assert any(i.kind == "visual_fallback_without_asset" for i in issues)


def test_validate_ledger_accepts_a_well_formed_resolved_blocker():
    ledger = BlockerLedger(
        blockers=[
            _blocker(
                status="resolved_by_visual_fallback",
                evidence="some evidence",
                regression_tests=["tests/test_x.py"],
                affected_assets=["enade-2011-computing-q01/figure-01.png"],
            )
        ]
    )
    assert validate_ledger(ledger) == []


def test_ledger_status_counts_match_total_by_construction():
    ledger = BlockerLedger(
        blockers=[
            _blocker(id="a", status="open"),
            _blocker(id="b", status="resolved", evidence="e", regression_tests=["t"]),
            _blocker(id="c", status="source_ambiguity"),
            _blocker(id="d", status="not_reproducible"),
            _blocker(id="e", status="superseded", superseded_by="a"),
        ]
    )
    assert (
        ledger.open_count
        + ledger.resolved_count
        + ledger.superseded_count
        + ledger.source_ambiguity_count
        + ledger.not_reproducible_count
    ) == ledger.total
    assert validate_ledger(ledger) == []


def test_ledger_by_id_finds_a_known_blocker_and_returns_none_for_unknown():
    ledger = BlockerLedger(blockers=[_blocker(id="known")])
    assert ledger.by_id("known") is not None
    assert ledger.by_id("unknown") is None


def test_blocker_is_open_and_is_terminal_properties():
    open_blocker = _blocker(status="open")
    resolved_blocker = _blocker(status="resolved", evidence="e", regression_tests=["t"])
    assert open_blocker.is_open is True
    assert open_blocker.is_terminal is False
    assert resolved_blocker.is_open is False
    assert resolved_blocker.is_terminal is True


# --- Phase 2F: accepted_non_material_difference (see docs/decisions.md, "Phase 2F" ADR) ---


def test_accepted_non_material_difference_is_not_open_and_is_terminal():
    # PROMPT Phase 2F section 10: a documented, verified presentation-only
    # divergence (e.g. 2011 Q27's own pseudocode) must never block
    # readiness the way a genuine open blocker does, but it is also never
    # silently interchangeable with "resolved" - nothing was fixed.
    blocker = _blocker(
        status="accepted_non_material_difference",
        evidence="docs/decisions.md, Phase 2F ADR",
        regression_tests=["tests/test_x.py"],
    )
    assert blocker.is_open is False
    assert blocker.is_terminal is True


def test_accepted_non_material_difference_requires_evidence():
    ledger = BlockerLedger(
        blockers=[
            _blocker(
                status="accepted_non_material_difference",
                evidence=None,
                regression_tests=["tests/test_x.py"],
            )
        ]
    )
    issues = validate_ledger(ledger)
    assert any(i.kind == "resolved_without_evidence" for i in issues)


def test_accepted_non_material_difference_requires_regression_test():
    ledger = BlockerLedger(
        blockers=[
            _blocker(
                status="accepted_non_material_difference",
                evidence="some evidence",
                regression_tests=[],
            )
        ]
    )
    issues = validate_ledger(ledger)
    assert any(i.kind == "resolved_without_test" for i in issues)


def test_accepted_non_material_difference_counts_toward_the_ledger_total():
    ledger = BlockerLedger(
        blockers=[
            _blocker(id="a", status="open"),
            _blocker(
                id="b",
                status="accepted_non_material_difference",
                evidence="e",
                regression_tests=["t"],
            ),
        ]
    )
    assert ledger.accepted_non_material_difference_count == 1
    assert (
        ledger.open_count
        + ledger.resolved_count
        + ledger.superseded_count
        + ledger.source_ambiguity_count
        + ledger.not_reproducible_count
        + ledger.accepted_non_material_difference_count
    ) == ledger.total
    assert validate_ledger(ledger) == []


def test_accepted_non_material_difference_never_counted_as_resolved():
    # A distinct status/count from "resolved" - conflating the two would
    # misrepresent an accepted difference as a fix that was made.
    ledger = BlockerLedger(
        blockers=[
            _blocker(
                status="accepted_non_material_difference",
                evidence="e",
                regression_tests=["t"],
            )
        ]
    )
    assert ledger.resolved_count == 0
    assert ledger.accepted_non_material_difference_count == 1
