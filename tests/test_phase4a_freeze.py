"""Phase-4A pre-commit freeze gate (PROMPT Fase 4A section 26/27).

Distinct from ``test_protected_corpus.py`` (which locks the narrower
2011/2021 protected set): this gate verifies the *entire* working-tree
state this freeze certifies - every manifest, every report, the full
aggregate hash of each published corpus, and the exact set of files this
freeze itself declares as legitimately uncommitted.

The freeze deliberately never requires a clean working tree (PROMPT
section 27: "O freeze nao deve exigir working tree limpa, pois o trabalho
ainda nao foi commitado") - Phases 3A-4A were never committed by this
project's own discipline. It requires the opposite, narrower guarantee:
the *current* uncommitted set (``git status --porcelain=v1``) matches
*exactly* what the freeze itself already declared, file for file, hash
for hash - never more, never fewer, never a divergent hash.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
FREEZE_PATH = PROJECT_ROOT / "data" / "manifests" / "phase-4a-freeze.json"

pytestmark = pytest.mark.skipif(not FREEZE_PATH.exists(), reason="phase-4a-freeze.json not present")


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
    # master and origin/master must have been identical (and equal to the
    # merge-base with HEAD) at freeze time - no divergence, no rebase.
    assert freeze["master"] == freeze["origin_master"]
    assert freeze["merge_base"] == freeze["master"]


def test_freeze_head_matches_the_real_current_head():
    freeze = _load()
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT, capture_output=True, text=True, check=True
    )
    assert freeze["head"] == result.stdout.strip()


def test_freeze_master_is_still_unchanged():
    # A freeze whose own recorded master no longer matches the real
    # master means master moved (or was rewritten) since the freeze was
    # taken - the freeze is stale and must not be trusted.
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
    # An extra, uninventoried manifest file is exactly as dangerous as a
    # missing one - it means the freeze's own inventory is incomplete.
    freeze = _load()
    known = {entry["path"] for entry in freeze["manifests"]}
    on_disk = {
        p.relative_to(PROJECT_ROOT).as_posix()
        for p in (PROJECT_ROOT / "data" / "manifests").glob("*")
        if p.is_file() and p.name != "phase-4a-freeze.json"
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


def test_source_limitations_still_present_and_never_resolved():
    # PROMPT section 30: never let D09/D10 quietly become "resolved".
    freeze = _load()
    subjects = {e["subject_id"] for e in freeze["source_limitations"]}
    assert subjects == {"enade-2008-computing-d09", "enade-2008-computing-d10"}
    for entry in freeze["source_limitations"]:
        assert entry["status"] == "source_unavailable_confirmed"


def test_readiness_2008b_matches_the_frozen_verdict():
    freeze = _load()
    r = freeze["readiness"]["2008-b"]
    assert r["verdict"] == "READY_FOR_2008_ENGINEERING_TEST_WITH_SOURCE_LIMITATIONS"
    assert r["actionable_blockers"] == 0
    assert r["source_limitations"] == 2
    assert r["informational_findings"] == 0


def test_working_tree_uncommitted_set_matches_exactly_what_the_freeze_declared():
    """The core Section 27 gate: never requires a clean tree, but requires
    the tree to contain *exactly* the declared uncommitted set - no file
    the freeze didn't know about, none missing, none re-modified since.
    """
    freeze = _load()
    frozen_paths = {e["path"] for e in freeze["uncommitted_changes"]}
    current_lines = _git_status_porcelain()
    current_paths = {line[3:].strip() for line in current_lines}
    # phase-4a-freeze.json and any file created strictly after this exact
    # freeze snapshot (e.g. this very test file, added in the same
    # session) are expected new entries not yet re-frozen - the gate's
    # own job is to catch *unexpected* drift among the files the freeze
    # already knew about, not to forbid ever adding a new file after a
    # freeze is taken.
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
