"""Protected-corpus path/hash gate (PROMPT Phase 3M section 4).

Reconciles the "270" vs "288" file counts cited across docs/phase-3a.md
through phase-3l-report.md: both were always correct, describing
different scopes of the *same* protected set - 270 is the question
Markdown/asset files under ``data/questions/2011`` and
``data/questions/2021``; 288 is that same 270 plus 18 derived manifests
(gold/visual-audit/blocker-ledger/exam-structure/extraction-audit/
transformation-log) for those two corpora. Neither figure ever shrank; no
protection was ever lost - see docs/phase-3m-report.md section D for the
full narrative.

This gate validates the actual *list* of paths (existence and SHA-256),
never just a count - a count alone would happily pass if one protected
file were silently replaced by an unrelated new one.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
MANIFEST_PATH = PROJECT_ROOT / "data" / "manifests" / "protected-files-2011-2021.json"
QUESTIONS_2011 = PROJECT_ROOT / "data" / "questions" / "2011"
QUESTIONS_2021 = PROJECT_ROOT / "data" / "questions" / "2021"

pytestmark = pytest.mark.skipif(
    not MANIFEST_PATH.exists(), reason="protected-files-2011-2021.json not present"
)


def _load_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def test_manifest_reconciles_270_question_files_plus_18_manifests_to_288():
    manifest = _load_manifest()
    assert manifest["total_files"] == 288
    assert manifest["question_file_count"] == 270
    assert manifest["manifest_file_count"] == 18
    assert len(manifest["files"]) == 288


def test_every_listed_path_exists_and_matches_its_recorded_sha256():
    manifest = _load_manifest()
    mismatches: list[str] = []
    missing: list[str] = []
    for entry in manifest["files"]:
        path = PROJECT_ROOT / entry["path"]
        if not path.is_file():
            missing.append(entry["path"])
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != entry["sha256"]:
            mismatches.append(f"{entry['path']}: expected {entry['sha256']}, got {actual}")
    assert not missing, f"protected file(s) missing from disk: {missing}"
    assert not mismatches, "protected file(s) changed (drift):\n" + "\n".join(mismatches)


def test_no_unlisted_question_file_exists_under_the_protected_2011_2021_corpora():
    """The manifest's own 270 question-file paths must be the *complete*
    set under ``data/questions/2011``/``data/questions/2021`` - a new file
    silently added there (a stray artifact of some future extraction run)
    must fail this gate exactly as loudly as a changed one would.
    """
    manifest = _load_manifest()
    listed = {entry["path"] for entry in manifest["files"] if entry["category"] != "manifest"}
    actual_files = {
        str(p.relative_to(PROJECT_ROOT)).replace("\\", "/")
        for root in (QUESTIONS_2011, QUESTIONS_2021)
        for p in root.rglob("*")
        if p.is_file()
    }
    assert actual_files == listed, (
        f"missing from manifest: {actual_files - listed}; "
        f"listed but absent on disk: {listed - actual_files}"
    )


def test_manifest_paths_use_forward_slashes_and_no_traversal():
    manifest = _load_manifest()
    for entry in manifest["files"]:
        assert "\\" not in entry["path"], entry["path"]
        assert ".." not in Path(entry["path"]).parts, entry["path"]
