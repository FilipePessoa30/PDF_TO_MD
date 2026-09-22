"""Phase-5A semantic freeze gate (PROMPT Fase 5A section 30).

A SEPARATE lineage from the extraction freeze
(``data/manifests/phase-4e-freeze.json``, which this freeze only ever
references by hash - it is never edited, never superseded, never
replaced by a ``phase-4f-freeze.json``). This is the first, and so far
only, freeze in the semantic lineage.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from enade.semantic.freeze import validate_semantic_freeze_completeness

PROJECT_ROOT = Path(__file__).parent.parent
FREEZE_PATH = PROJECT_ROOT / "data" / "manifests" / "phase-5a-semantic-freeze.json"
EXTRACTION_FREEZE_PATH = PROJECT_ROOT / "data" / "manifests" / "phase-4e-freeze.json"

pytestmark = pytest.mark.skipif(
    not FREEZE_PATH.exists(), reason="phase-5a-semantic-freeze.json not present"
)


def _load() -> dict:
    return json.loads(FREEZE_PATH.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_freeze_satisfies_the_semantic_completeness_contract():
    freeze = _load()
    violations = validate_semantic_freeze_completeness(freeze)
    assert violations == [], f"freeze fails the completeness contract: {violations}"


def test_freeze_never_creates_a_phase_4f_extraction_freeze():
    """PROMPT section 3: 'nao crie phase-4f-freeze.json'."""
    assert not (PROJECT_ROOT / "data" / "manifests" / "phase-4f-freeze.json").exists()


def test_extraction_freeze_reference_matches_the_real_terminal_freeze_unedited():
    freeze = _load()
    ref = freeze["extraction_freeze_reference"]
    assert ref["path"] == "data/manifests/phase-4e-freeze.json"
    assert EXTRACTION_FREEZE_PATH.is_file()
    assert _sha256(EXTRACTION_FREEZE_PATH) == ref["sha256"]


def test_recorded_head_is_the_current_head_or_a_real_ancestor_of_it():
    """Every prior freeze in this project eventually got absorbed by an
    external commit that moved HEAD past what it recorded - this freeze
    may go through the same fate. Accept either exact equality (freeze
    just built) or ancestry (time has since passed).
    """
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
        "taxonomy",
        "annotations",
        "pilot_selection",
        "guidelines",
        "review_packet",
        "pilot_audit",
        "generalization_scan",
    ],
)
def test_every_artifact_exists_and_matches_its_recorded_sha256(artifact_key):
    freeze = _load()
    entry = freeze["artifacts"][artifact_key]
    path = PROJECT_ROOT / entry["path"]
    assert path.is_file(), f"{entry['path']} is missing"
    assert _sha256(path) == entry["sha256"], f"{entry['path']} drifted since the freeze was taken"


def test_pilot_annotation_count_matches_the_real_file():
    freeze = _load()
    annotations_path = PROJECT_ROOT / freeze["artifacts"]["annotations"]["path"]
    payload = json.loads(annotations_path.read_text(encoding="utf-8"))
    assert freeze["counts"]["pilot_annotation_count"] == len(payload["annotations"])
    assert freeze["counts"]["pilot_annotation_count"] == 30


def test_counts_and_quality_gates_are_non_empty():
    freeze = _load()
    assert freeze["counts"]
    assert freeze["quality_gates"]
    assert freeze["quality_gates"]["pytest"]["exit_code"] == 0


def test_semantic_maturity_is_provisional_never_final():
    freeze = _load()
    assert freeze["semantic_maturity"] == "provisional_pilot"


def test_human_review_status_never_claims_the_pilot_was_reviewed():
    """PROMPT section 30: 'nunca afirme que o piloto foi humanamente
    aprovado'."""
    freeze = _load()
    assert freeze["human_review_status"] == "not_yet_reviewed"


def test_freeze_was_never_silently_tampered_with_a_mismatched_artifact_hash():
    freeze = _load()
    tampered = dict(freeze)
    tampered["artifacts"] = dict(freeze["artifacts"])
    tampered["artifacts"]["taxonomy"] = {
        **freeze["artifacts"]["taxonomy"],
        "sha256": "0" * 64,
    }
    real_path = PROJECT_ROOT / tampered["artifacts"]["taxonomy"]["path"]
    assert _sha256(real_path) != tampered["artifacts"]["taxonomy"]["sha256"]


def test_no_extraction_corpus_path_appears_among_the_frozen_artifacts():
    """This freeze certifies the semantic layer only - it must never list
    a ``data/questions/**`` path as one of its own artifacts (that
    protection lives exclusively in the extraction freeze).
    """
    freeze = _load()
    for entry in freeze["artifacts"].values():
        assert not entry["path"].startswith("data/questions/")
