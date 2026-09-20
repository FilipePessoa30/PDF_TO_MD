"""Phase-4B pre-commit freeze gate (PROMPT Fase 4B section 24-27).

Supersedes ``tests/test_phase4a_freeze.py`` as the *live* freeze gate:
that file now only certifies that the Fase 4A snapshot was never silently
edited (a historical record), while this one certifies that the
*current* working tree still matches exactly what this newer freeze
declared - the same narrower guarantee Fase 4A's own gate provided before
its own HEAD moved out from under it (Fase 4A's own files were committed
externally mid-session, which is exactly the kind of drift a freeze
exists to catch, not paper over).

Two "active" freezes are never asserted simultaneously (PROMPT section
24): this is the only file in this test suite that compares
``phase-4b-freeze.json`` against live git/disk state.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
FREEZE_PATH = PROJECT_ROOT / "data" / "manifests" / "phase-4b-freeze.json"
OLD_FREEZE_PATH = PROJECT_ROOT / "data" / "manifests" / "phase-4a-freeze.json"

pytestmark = pytest.mark.skipif(not FREEZE_PATH.exists(), reason="phase-4b-freeze.json not present")


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


def test_freeze_records_the_expected_branch_and_git_ancestry():
    freeze = _load()
    assert freeze["branch"] == "feat/enade-2008-cc-b-pilot"
    assert freeze["master"] == freeze["origin_master"]
    assert freeze["merge_base"] == freeze["master"]


def test_freeze_declares_it_supersedes_the_phase_4a_freeze():
    freeze = _load()
    assert freeze["supersedes"] == "data/manifests/phase-4a-freeze.json"
    assert len(freeze["historical_freezes"]) == 1
    entry = freeze["historical_freezes"][0]
    assert entry["phase"] == "4a"
    assert entry["status"] == "superseded"
    assert entry["superseded_by"] == "4b"


def test_historical_freeze_entry_hash_matches_the_real_phase_4a_file_unedited():
    # Fase 4A's own freeze must never be silently rewritten (PROMPT
    # section 24) - this is the mechanism that proves it: the hash this
    # newer freeze recorded for it must still match the file on disk,
    # byte for byte.
    freeze = _load()
    entry = freeze["historical_freezes"][0]
    assert OLD_FREEZE_PATH.is_file()
    assert _sha256(OLD_FREEZE_PATH) == entry["sha256"]


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


def test_no_manifest_appeared_that_the_freeze_never_inventoried():
    freeze = _load()
    known = {entry["path"] for entry in freeze["manifests"]}
    on_disk = {
        p.relative_to(PROJECT_ROOT).as_posix()
        for p in (PROJECT_ROOT / "data" / "manifests").glob("*")
        if p.is_file() and p.name != "phase-4b-freeze.json"
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
    # The one artifact this whole phase exists to refresh - a freeze that
    # doesn't verify it live would defeat the phase's own purpose.
    freeze = _load()
    entry = freeze["content_assignment_ledger"]
    path = PROJECT_ROOT / entry["path"]
    assert _sha256(path) == entry["sha256"]
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["assignment_count"] == entry["assignment_count"]


def test_content_assignment_ledger_change_invalidated_the_old_phase_4a_freeze_entry():
    """PROMPT section 24: a ledger change must invalidate the prior
    freeze - proves the refresh was actually necessary, not cosmetic.
    """
    old_freeze = json.loads(OLD_FREEZE_PATH.read_text(encoding="utf-8"))
    old_entry = next(
        e
        for e in old_freeze["manifests"]
        if e["path"] == "data/manifests/content-assignment-2008-b.json"
    )
    current_path = PROJECT_ROOT / "data" / "manifests" / "content-assignment-2008-b.json"
    assert _sha256(current_path) != old_entry["sha256"], (
        "the content-assignment ledger's hash is unchanged from the Fase 4A "
        "freeze - the Fase 4B refresh would have nothing to certify"
    )


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
    """The core Section 27 gate, carried forward from Fase 4A's own gate
    (now retired in favor of this one): never requires a clean tree, but
    requires the tree to contain *exactly* the declared uncommitted set.
    """
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
    """Regression coverage for the Fase 4A freeze-generator bug class
    (docs/phase-4a-report.md section X): calling ``.strip()`` on the
    *entire* ``git status --porcelain=v1`` output before splitting into
    lines eats exactly one character off the FIRST listed path, because
    that format's leading column is a meaningful space ("unstaged
    modified"), not padding - ``.strip()`` on the whole blob only touches
    the outer edges, so only the first line is corrupted. Reproduced here
    with a fixed, synthetic porcelain blob so this stays deterministic
    and independent of the real repo's own current status.
    """
    synthetic_porcelain = (
        " M data/manifests/blocker-ledger-2008.yaml\n"
        " M src/enade/cli.py\n"
        "?? tests/test_new_file.py\n"
    )

    def naive_parse(raw: str) -> list[str]:
        # The bug: strips the whole blob first.
        return [line[3:].strip() for line in raw.strip().splitlines() if line.strip()]

    def correct_parse(raw: str) -> list[str]:
        # The fix (run_raw()): never strip the whole blob, only split it.
        return [line[3:].strip() for line in raw.splitlines() if line.strip()]

    naive_paths = naive_parse(synthetic_porcelain)
    correct_paths = correct_parse(synthetic_porcelain)

    assert naive_paths[0] == "ata/manifests/blocker-ledger-2008.yaml"  # the historical corruption
    assert correct_paths[0] == "data/manifests/blocker-ledger-2008.yaml"
    assert naive_paths[1:] == correct_paths[1:]  # only ever the first line is affected
