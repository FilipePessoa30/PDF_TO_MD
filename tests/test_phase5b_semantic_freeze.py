"""Phase-5B semantic freeze gate (PROMPT Fase 5B section 30).

A successor of the semantic lineage ``phase-5a-semantic-freeze.json``
started - never edits it, only references it by hash. Both the
extraction freeze (``phase-4e-freeze.json``) and the Fase 5A semantic
freeze remain byte-identical and terminal in their own lineages; this is
the only freeze that certifies the Fase 5B reconciliation itself.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from enade.semantic.freeze import validate_phase5b_freeze_completeness

PROJECT_ROOT = Path(__file__).parent.parent
FREEZE_PATH = PROJECT_ROOT / "data" / "manifests" / "phase-5b-semantic-freeze.json"
PREDECESSOR_FREEZE_PATH = PROJECT_ROOT / "data" / "manifests" / "phase-5a-semantic-freeze.json"
EXTRACTION_FREEZE_PATH = PROJECT_ROOT / "data" / "manifests" / "phase-4e-freeze.json"

pytestmark = pytest.mark.skipif(
    not FREEZE_PATH.exists(), reason="phase-5b-semantic-freeze.json not present"
)


def _load() -> dict:
    return json.loads(FREEZE_PATH.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_freeze_satisfies_the_5b_completeness_contract():
    freeze = _load()
    violations = validate_phase5b_freeze_completeness(freeze)
    assert violations == [], f"freeze fails the completeness contract: {violations}"


def test_predecessor_semantic_freeze_reference_matches_the_real_file_unedited():
    freeze = _load()
    ref = freeze["predecessor_semantic_freeze_reference"]
    assert ref["path"] == "data/manifests/phase-5a-semantic-freeze.json"
    assert PREDECESSOR_FREEZE_PATH.is_file()
    assert _sha256(PREDECESSOR_FREEZE_PATH) == ref["sha256"]


def test_extraction_freeze_reference_matches_the_real_terminal_freeze_unedited():
    freeze = _load()
    ref = freeze["extraction_freeze_reference"]
    assert ref["path"] == "data/manifests/phase-4e-freeze.json"
    assert EXTRACTION_FREEZE_PATH.is_file()
    assert _sha256(EXTRACTION_FREEZE_PATH) == ref["sha256"]


def test_phase_5a_artifacts_recorded_as_verified_are_still_byte_identical():
    freeze = _load()
    for key, recorded_hash in freeze["phase_5a_artifacts_verified_byte_identical"].items():
        # Cross-check against the Fase 5A freeze's own recorded hash for
        # the same artifact, rather than trusting this file's own claim in
        # isolation.
        predecessor_freeze = json.loads(PREDECESSOR_FREEZE_PATH.read_text(encoding="utf-8"))
        assert recorded_hash == predecessor_freeze["artifacts"][key]["sha256"], (
            f"{key} hash recorded in phase-5b-semantic-freeze.json does not match "
            "the hash phase-5a-semantic-freeze.json itself recorded"
        )


def test_recorded_head_is_the_current_head_or_a_real_ancestor_of_it():
    freeze = _load()
    assert len(freeze["head"]) == 40
    current_head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()
    if freeze["head"] == current_head:
        return
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", freeze["head"], "HEAD"], cwd=PROJECT_ROOT
    )
    assert result.returncode == 0, (
        "the frozen HEAD is neither the current HEAD nor an ancestor of it"
    )


def test_master_was_never_touched():
    freeze = _load()
    result = subprocess.run(
        ["git", "rev-parse", "master"], cwd=PROJECT_ROOT, capture_output=True, text=True, check=True
    )
    assert freeze["master"] == result.stdout.strip()
    assert freeze["master"] == freeze["origin_master"]


@pytest.mark.parametrize(
    "artifact_key",
    [
        "taxonomy_computing",
        "taxonomy_general_education",
        "annotations",
        "unresolved_cases_ledger",
        "migration_log",
        "human_adjudication_template",
        "review_packet",
        "generalization_scan",
    ],
)
def test_every_artifact_exists_and_matches_its_recorded_sha256(artifact_key):
    freeze = _load()
    entry = freeze["artifacts"][artifact_key]
    path = PROJECT_ROOT / entry["path"]
    assert path.is_file(), f"{entry['path']} is missing"
    assert _sha256(path) == entry["sha256"], f"{entry['path']} drifted since the freeze was taken"


def test_annotation_count_matches_the_real_file():
    freeze = _load()
    annotations_path = PROJECT_ROOT / freeze["artifacts"]["annotations"]["path"]
    payload = json.loads(annotations_path.read_text(encoding="utf-8"))
    assert freeze["counts"]["annotation_count"] == len(payload["annotations"]) == 30


def test_counts_reflect_the_real_reconciliation_outcome():
    freeze = _load()
    counts = freeze["counts"]
    assert counts["unresolved_cases_reconciled"] == 12
    assert counts["previously_unclassifiable_now_classified"] == 10
    assert counts["previously_needs_review_now_resolved"] == 2
    assert counts["annotation_status_counts"]["proposed"] == counts["annotation_count"]
    assert "unclassifiable" not in counts["annotation_status_counts"]
    assert "needs_review" not in counts["annotation_status_counts"]


def test_quality_gates_pytest_entry_is_filled_in_and_passing():
    freeze = _load()
    pytest_gate = freeze["quality_gates"]["pytest"]
    assert pytest_gate["exit_code"] == 0
    assert pytest_gate["failed"] == 0
    assert isinstance(pytest_gate["passed"], int) and pytest_gate["passed"] > 0


def test_semantic_maturity_reflects_reconciliation_not_final_approval():
    freeze = _load()
    assert freeze["semantic_maturity"] == "provisional_reconciled_pilot"


def test_human_review_status_never_claims_the_pilot_was_reviewed():
    freeze = _load()
    assert freeze["human_review_status"] == "not_yet_reviewed"


def test_freeze_never_claims_full_corpus_rollout_authorization():
    freeze = _load()
    scope_notice = freeze["scope_notice"].lower()
    assert "nao certifica" in scope_notice or "não certifica" in scope_notice
    assert "rollout completo" in scope_notice


def test_no_extraction_corpus_path_appears_among_the_frozen_artifacts():
    freeze = _load()
    for entry in freeze["artifacts"].values():
        assert not entry["path"].startswith("data/questions/")


def test_freeze_never_creates_a_new_extraction_or_5a_freeze_file():
    """PROMPT section 4/30: phase-4e-freeze.json and
    phase-5a-semantic-freeze.json remain the terminal freezes of their
    own lineages - no phase-4f or phase-5a-v2 style file was created.
    """
    manifests_dir = PROJECT_ROOT / "data" / "manifests"
    assert not (manifests_dir / "phase-4f-freeze.json").exists()
    assert not (manifests_dir / "phase-5a-semantic-freeze-v2.json").exists()
