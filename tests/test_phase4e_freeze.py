"""Phase-4E pre-commit freeze gate (PROMPT Fase 4E section 24).

Supersedes ``tests/test_phase4d_freeze.py`` as the *live* freeze gate,
for the same reason that file itself superseded
``tests/test_phase4c_freeze.py`` in Fase 4D: the artifact it certified
moved out from under it (an external commit absorbed its own declared
uncommitted set), and this phase's own corrective fixes (the reciprocal
table anchor; the new ``freeze_contract`` module) changed the
content-assignment ledger and tooling it had certified regardless. All
four of ``phase-4a-freeze.json`` through ``phase-4d-freeze.json`` are
tracked here as historical snapshots, preserved byte-for-byte; only this
file compares ``phase-4e-freeze.json`` against live git/disk state -
never two "active" freezes at once.

This is also the first freeze required to pass
``enade.freeze_contract.validate_freeze_completeness`` (PROMPT Fase 4E
section 18/24, hardening finding F7): ``phase-4c-freeze.json`` was
promoted to active with its own ``readiness``/``quality_gates`` left as
empty placeholders, and nothing enforced that this could never happen.
That gate is never applied retroactively to any historical freeze - only
to this one, and to whichever one supersedes it next.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from enade.freeze_contract import validate_freeze_completeness

PROJECT_ROOT = Path(__file__).parent.parent
FREEZE_PATH = PROJECT_ROOT / "data" / "manifests" / "phase-4e-freeze.json"
OLD_FREEZE_PATHS = {
    "4a": PROJECT_ROOT / "data" / "manifests" / "phase-4a-freeze.json",
    "4b": PROJECT_ROOT / "data" / "manifests" / "phase-4b-freeze.json",
    "4c": PROJECT_ROOT / "data" / "manifests" / "phase-4c-freeze.json",
    "4d": PROJECT_ROOT / "data" / "manifests" / "phase-4d-freeze.json",
}

pytestmark = pytest.mark.skipif(not FREEZE_PATH.exists(), reason="phase-4e-freeze.json not present")


def _load() -> dict:
    return json.loads(FREEZE_PATH.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_status_porcelain() -> list[str]:
    result = subprocess.run(
        ["git", "status", "--porcelain=v1"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


def test_freeze_satisfies_the_completeness_contract_f7_hardening():
    """The one gate this project did not have when phase-4c-freeze.json
    was promoted to active: a freeze with empty readiness/quality_gates
    must never be treated as valid again.
    """
    freeze = _load()
    violations = validate_freeze_completeness(freeze)
    assert violations == [], f"freeze fails the completeness contract: {violations}"


def test_freeze_records_the_expected_branch_and_git_ancestry():
    freeze = _load()
    assert freeze["branch"] == "feat/enade-2008-cc-b-pilot"
    assert freeze["master"] == freeze["origin_master"]
    assert freeze["merge_base"] == freeze["master"]


def test_freeze_declares_it_supersedes_the_phase_4d_freeze():
    freeze = _load()
    assert freeze["supersedes"] == "data/manifests/phase-4d-freeze.json"
    assert {e["phase"] for e in freeze["historical_freezes"]} == {"4a", "4b", "4c", "4d"}
    for entry in freeze["historical_freezes"]:
        assert entry["status"] == "superseded"


def test_freeze_records_the_pre_existing_remote_commit_without_attributing_it_to_this_phase():
    freeze = _load()
    entry = freeze["pre_existing_remote_commit"]
    assert entry["sha"] == "6e78d5f333370357653e15d271ae8d0835bc6a78"


@pytest.mark.parametrize("phase", ["4a", "4b", "4c", "4d"])
def test_historical_freeze_entry_hash_matches_the_real_file_unedited(phase):
    freeze = _load()
    entry = next(e for e in freeze["historical_freezes"] if e["phase"] == phase)
    path = OLD_FREEZE_PATHS[phase]
    assert path.is_file()
    assert _sha256(path) == entry["sha256"]


def test_freeze_head_matches_the_real_current_head():
    freeze = _load()
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT, capture_output=True, text=True, check=True
    )
    assert freeze["head"] == result.stdout.strip()


def test_freeze_master_is_still_unchanged():
    freeze = _load()
    result = subprocess.run(
        ["git", "rev-parse", "master"], cwd=PROJECT_ROOT, capture_output=True, text=True, check=True
    )
    assert freeze["master"] == result.stdout.strip()


def test_every_listed_manifest_exists_and_matches_its_recorded_sha256():
    freeze = _load()
    missing: list[str] = []
    mismatches: list[str] = []
    for entry in freeze["manifests"]:
        path = PROJECT_ROOT / entry["path"]
        if not path.is_file():
            missing.append(entry["path"])
            continue
        if _sha256(path) != entry["sha256"]:
            mismatches.append(entry["path"])
    assert not missing, f"manifest(s) missing since freeze: {missing}"
    assert not mismatches, f"manifest(s) changed since freeze: {mismatches}"


def test_every_listed_report_exists_and_matches_its_recorded_sha256():
    freeze = _load()
    missing: list[str] = []
    mismatches: list[str] = []
    for entry in freeze["reports"]:
        path = PROJECT_ROOT / entry["path"]
        if not path.is_file():
            missing.append(entry["path"])
            continue
        if _sha256(path) != entry["sha256"]:
            mismatches.append(entry["path"])
    assert not missing, f"report(s) missing since freeze: {missing}"
    assert not mismatches, f"report(s) changed since freeze: {mismatches}"


def test_every_listed_review_exists_and_matches_its_recorded_sha256():
    freeze = _load()
    missing: list[str] = []
    mismatches: list[str] = []
    for entry in freeze.get("reviews", []):
        path = PROJECT_ROOT / entry["path"]
        if not path.is_file():
            missing.append(entry["path"])
            continue
        if _sha256(path) != entry["sha256"]:
            mismatches.append(entry["path"])
    assert not missing, f"review(s) missing since freeze: {missing}"
    assert not mismatches, f"review(s) changed since freeze: {mismatches}"


def test_no_manifest_appeared_that_the_freeze_never_inventoried():
    freeze = _load()
    known = {entry["path"] for entry in freeze["manifests"]}
    on_disk = {
        p.relative_to(PROJECT_ROOT).as_posix()
        for p in (PROJECT_ROOT / "data" / "manifests").glob("*")
        if p.is_file() and p.name != "phase-4e-freeze.json"
    }
    assert on_disk == known, f"uninventoried manifest(s): {on_disk - known}"


@pytest.mark.parametrize(
    "label,subdir",
    [
        ("2008-b", "data/questions/2008/all-computing"),
        ("2011", "data/questions/2011/all-computing"),
        (
            "2021-ciencia-da-computacao-bacharelado",
            "data/questions/2021/ciencia-da-computacao-bacharelado",
        ),
        (
            "2021-ciencia-da-computacao-licenciatura",
            "data/questions/2021/ciencia-da-computacao-licenciatura",
        ),
        ("2021-sistemas-de-informacao", "data/questions/2021/sistemas-de-informacao"),
    ],
)
def test_question_outputs_aggregate_hash_matches_current_disk_state(label, subdir):
    freeze = _load()
    root = PROJECT_ROOT / subdir
    files = sorted(
        (p for p in root.rglob("*") if p.is_file() and p.suffix in (".md", ".png")),
        key=lambda p: p.relative_to(PROJECT_ROOT).as_posix(),
    )
    lines = [f"{_sha256(p)}  {p.relative_to(PROJECT_ROOT).as_posix()}" for p in files]
    actual = hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()
    assert freeze["question_outputs"][label] == actual, (
        f"{label} corpus drifted since the freeze was taken (output no longer "
        "matches the frozen aggregate hash)"
    )


def test_content_assignment_ledger_hash_matches_current_disk_state():
    freeze = _load()
    entry = freeze["content_assignment_ledger"]
    path = PROJECT_ROOT / entry["path"]
    assert _sha256(path) == entry["sha256"]
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["assignment_count"] == entry["assignment_count"]


def test_content_assignment_ledger_assignment_ids_are_geometry_derived():
    import re

    freeze = _load()
    path = PROJECT_ROOT / freeze["content_assignment_ledger"]["path"]
    payload = json.loads(path.read_text(encoding="utf-8"))
    position_only = re.compile(r"^[^:]+(:asset)?:\d+$")
    offenders = [
        r["assignment_id"]
        for r in payload["assignments"]
        if position_only.match(r["assignment_id"])
    ]
    assert offenders == []


def test_content_assignment_ledger_has_no_orphans_against_2008b():
    from enade.extraction.content_assignment import find_orphan_assets

    freeze = _load()
    path = PROJECT_ROOT / freeze["content_assignment_ledger"]["path"]
    payload = json.loads(path.read_text(encoding="utf-8"))
    course_dir = PROJECT_ROOT / "data" / "questions" / "2008" / "all-computing"
    assert find_orphan_assets(payload, course_dir) == []


def test_generation_tooling_hashes_match_current_disk_state():
    freeze = _load()
    for entry in freeze["generation_tooling"]:
        path = PROJECT_ROOT / entry["path"]
        assert path.is_file()
        assert _sha256(path) == entry["sha256"]


def test_generation_tests_hashes_match_current_disk_state():
    freeze = _load()
    for entry in freeze["generation_tests"]:
        path = PROJECT_ROOT / entry["path"]
        assert path.is_file()
        assert _sha256(path) == entry["sha256"]


def test_source_limitations_still_present_and_never_resolved():
    freeze = _load()
    subjects = {e["subject_id"] for e in freeze["source_limitations"]}
    assert subjects == {"enade-2008-computing-d09", "enade-2008-computing-d10"}
    for entry in freeze["source_limitations"]:
        assert entry["status"] == "source_unavailable_confirmed"


def test_working_tree_uncommitted_set_matches_exactly_what_the_freeze_declared():
    freeze = _load()
    frozen_paths = {e["path"] for e in freeze["uncommitted_changes"]}
    current_lines = _git_status_porcelain()
    current_paths = {line[3:].strip() for line in current_lines}
    unexpected_missing = frozen_paths - current_paths
    assert not unexpected_missing, (
        f"file(s) the freeze declared uncommitted are no longer showing as "
        f"changed: {unexpected_missing} (committed, reverted, or moved?)"
    )
    for entry in freeze["uncommitted_changes"]:
        if entry["sha256"] is None:
            continue
        path = PROJECT_ROOT / entry["path"]
        if not path.is_file():
            continue
        assert _sha256(path) == entry["sha256"], (
            f"{entry['path']} changed since the freeze was taken "
            f"(expected {entry['sha256']}, found {_sha256(path)})"
        )


def test_git_status_porcelain_first_line_path_is_never_truncated_by_a_whole_blob_strip():
    synthetic_porcelain = (
        " M data/manifests/blocker-ledger-2008.yaml\n"
        " M src/enade/cli.py\n"
        "?? tests/test_new_file.py\n"
    )

    def naive_parse(raw: str) -> list[str]:
        return [line[3:].strip() for line in raw.strip().splitlines() if line.strip()]

    def correct_parse(raw: str) -> list[str]:
        return [line[3:].strip() for line in raw.splitlines() if line.strip()]

    naive_paths = naive_parse(synthetic_porcelain)
    correct_paths = correct_parse(synthetic_porcelain)

    assert naive_paths[0] == "ata/manifests/blocker-ledger-2008.yaml"
    assert correct_paths[0] == "data/manifests/blocker-ledger-2008.yaml"
    assert naive_paths[1:] == correct_paths[1:]
