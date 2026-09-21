"""Unit tests for the freeze structural-completeness contract (PROMPT
Fase 4E, hardening finding F7). Pure fixtures - never reads or writes any
real ``data/manifests/phase-*-freeze.json`` file; ``tests/test_phase4e_freeze.py``
is the one that applies this contract to the real, active freeze.
"""

from __future__ import annotations

import json
from pathlib import Path

from enade.freeze_contract import validate_freeze_completeness

_GOOD_READINESS_ENTRY = {
    "verdict": "READY_FOR_2008_ENGINEERING_TEST_WITH_SOURCE_LIMITATIONS",
    "actionable_blockers": 0,
    "source_limitations": 2,
    "informational_findings": 0,
}


def test_well_formed_freeze_has_zero_violations():
    freeze = {
        "readiness": {"2008-b": _GOOD_READINESS_ENTRY},
        "quality_gates": {"pytest": {"total": 949, "passed": 949}},
    }
    assert validate_freeze_completeness(freeze) == []


def test_empty_readiness_dict_is_a_violation():
    freeze = {"readiness": {}, "quality_gates": {"pytest": {}}}
    violations = validate_freeze_completeness(freeze)
    assert any("readiness" in v for v in violations)


def test_empty_quality_gates_dict_is_a_violation():
    freeze = {"readiness": {"2008-b": _GOOD_READINESS_ENTRY}, "quality_gates": {}}
    violations = validate_freeze_completeness(freeze)
    assert any("quality_gates" in v for v in violations)


def test_missing_readiness_field_is_a_violation():
    incomplete = dict(_GOOD_READINESS_ENTRY)
    del incomplete["actionable_blockers"]
    freeze = {"readiness": {"2008-b": incomplete}, "quality_gates": {"pytest": {}}}
    violations = validate_freeze_completeness(freeze)
    assert any("actionable_blockers" in v for v in violations)


def test_readiness_entry_that_is_not_a_dict_is_a_violation():
    freeze = {"readiness": {"2008-b": "READY"}, "quality_gates": {"pytest": {}}}
    violations = validate_freeze_completeness(freeze)
    assert any("2008-b" in v for v in violations)


def test_missing_top_level_keys_are_violations():
    assert validate_freeze_completeness({}) != []


def test_phase_4c_freezes_own_known_gap_is_detected_from_a_frozen_copy():
    # PROMPT Fase 4E section 18: revalidate the F7 finding directly,
    # never presumed from the Fase 4D report alone - reads the real,
    # unedited phase-4c-freeze.json (never writes to it) and confirms
    # this contract genuinely flags the exact gap Fase 4D discovered.
    path = Path(__file__).parent.parent / "data" / "manifests" / "phase-4c-freeze.json"
    freeze = json.loads(path.read_text(encoding="utf-8"))
    assert freeze["readiness"] == {}
    assert freeze["quality_gates"] == {}
    violations = validate_freeze_completeness(freeze)
    assert len(violations) == 2  # readiness empty + quality_gates empty, nothing else wrong


def test_phase_4b_freeze_passes_the_contract_it_was_never_checked_against():
    # A sanity check that this contract is not so strict it would have
    # rejected a freeze that was, in fact, filled in correctly.
    path = Path(__file__).parent.parent / "data" / "manifests" / "phase-4b-freeze.json"
    freeze = json.loads(path.read_text(encoding="utf-8"))
    assert validate_freeze_completeness(freeze) == []
