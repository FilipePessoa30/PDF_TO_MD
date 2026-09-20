"""Phase-4A freeze - now a HISTORICAL snapshot (PROMPT Fase 4B section 24).

Fase 4A's own freeze certified a specific, then-current working-tree
state (HEAD ``22e3e88...``, 13 uncommitted files, the pre-refresh
content-assignment ledger). That HEAD was superseded when those 13 files
were committed externally as ``c3b3bd1...`` mid-session, and the
content-assignment ledger itself was regenerated in Fase 4B - so the
live-comparison gates this file used to run (HEAD match, per-manifest
"still matches disk" checks, "uncommitted set still exactly present")
would now correctly, but uselessly, fail forever: they were never wrong,
the world underneath them simply moved on, exactly as a freeze is
supposed to let you detect.

Rather than let this file flag *expected, understood* drift as a
regression, it is rewritten here to check only what a HISTORICAL record
should still guarantee: that ``phase-4a-freeze.json`` itself was never
silently edited after the fact, and that its own internally-recorded
claims are self-consistent. The *live* equivalent of every check this
file used to run now lives in ``tests/test_phase4b_freeze.py``, against
``data/manifests/phase-4b-freeze.json`` - the one active freeze from here
on. ``data/manifests/phase-4a-freeze.json`` itself is left byte-for-byte
unedited on disk (PROMPT: "nunca alterando silenciosamente a semantica do
antigo").
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
FREEZE_PATH = PROJECT_ROOT / "data" / "manifests" / "phase-4a-freeze.json"
NEW_FREEZE_PATH = PROJECT_ROOT / "data" / "manifests" / "phase-4b-freeze.json"

pytestmark = pytest.mark.skipif(not FREEZE_PATH.exists(), reason="phase-4a-freeze.json not present")


def _load() -> dict:
    return json.loads(FREEZE_PATH.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_freeze_file_is_still_present_and_valid_json():
    assert FREEZE_PATH.is_file()
    freeze = _load()
    assert freeze["schema_version"] == 1


def test_freeze_records_the_expected_branch_and_git_ancestry():
    # Pure content assertions about the historical record itself - no
    # live git/subprocess comparison, since this is no longer a live gate.
    freeze = _load()
    assert freeze["branch"] == "feat/enade-2008-cc-b-pilot"
    assert freeze["master"] == freeze["origin_master"]
    assert freeze["merge_base"] == freeze["master"]


def test_freeze_recorded_head_is_a_real_ancestor_commit_never_equality_with_current_head():
    # The recorded HEAD is a historical fact (an ancestor of the commit
    # that later absorbed those same files, c3b3bd1) - proven here to be
    # a real, existing commit reachable from the current HEAD, which is
    # enough to show it was not fabricated, without ever asserting
    # equality to the *current* HEAD (see module docstring).
    freeze = _load()
    assert len(freeze["head"]) == 40
    subprocess.run(
        ["git", "cat-file", "-e", f"{freeze['head']}^{{commit}}"],
        cwd=PROJECT_ROOT,
        check=True,
    )
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", freeze["head"], "HEAD"],
        cwd=PROJECT_ROOT,
    )
    assert result.returncode == 0, "the frozen HEAD is not an ancestor of the current HEAD"


def test_source_limitations_still_present_and_never_resolved():
    freeze = _load()
    subjects = {e["subject_id"] for e in freeze["source_limitations"]}
    assert subjects == {"enade-2008-computing-d09", "enade-2008-computing-d10"}
    for entry in freeze["source_limitations"]:
        assert entry["status"] == "source_unavailable_confirmed"


def test_readiness_2008b_matches_the_frozen_verdict():
    # A claim about what readiness looked like AT THAT TIME - still a
    # true historical fact regardless of what Fase 4B later did.
    freeze = _load()
    r = freeze["readiness"]["2008-b"]
    assert r["verdict"] == "READY_FOR_2008_ENGINEERING_TEST_WITH_SOURCE_LIMITATIONS"
    assert r["actionable_blockers"] == 0
    assert r["source_limitations"] == 2
    assert r["informational_findings"] == 0


def test_freeze_was_never_silently_edited_after_being_superseded():
    """The one gate this file still needs to be strict about: Fase 4A's
    own freeze must remain byte-for-byte what it was when Fase 4B took
    over - proven against the hash Fase 4B's own freeze recorded for it
    (tests/test_phase4b_freeze.py asserts the reverse direction: that
    recorded hash still matches this file).
    """
    if not NEW_FREEZE_PATH.exists():
        pytest.skip("phase-4b-freeze.json not present yet - nothing to cross-check against")
    new_freeze = json.loads(NEW_FREEZE_PATH.read_text(encoding="utf-8"))
    entry = new_freeze["historical_freezes"][0]
    assert entry["path"] == "data/manifests/phase-4a-freeze.json"
    assert _sha256(FREEZE_PATH) == entry["sha256"]


def test_freeze_is_marked_superseded_in_the_active_freeze():
    if not NEW_FREEZE_PATH.exists():
        pytest.skip("phase-4b-freeze.json not present yet - nothing to cross-check against")
    new_freeze = json.loads(NEW_FREEZE_PATH.read_text(encoding="utf-8"))
    assert new_freeze["supersedes"] == "data/manifests/phase-4a-freeze.json"
