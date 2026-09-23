"""Corpus/freeze protection gate for Fase 5B (PROMPT section 4/27/32):
every Fase 5A artifact this phase was told to treat as historical must
remain byte-for-byte unedited, the 4E/5A freezes must still pass their
own gates, and no `data/questions`/gold file may have drifted.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
FREEZE_5A_PATH = REPO_ROOT / "data" / "manifests" / "phase-5a-semantic-freeze.json"
FREEZE_4E_PATH = REPO_ROOT / "data" / "manifests" / "phase-4e-freeze.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_phase_4e_freeze_is_byte_identical():
    freeze_5a = json.loads(FREEZE_5A_PATH.read_text(encoding="utf-8"))
    ref = freeze_5a["extraction_freeze_reference"]
    assert _sha256(FREEZE_4E_PATH) == ref["sha256"]


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
def test_every_5a_frozen_artifact_is_byte_identical(artifact_key):
    freeze_5a = json.loads(FREEZE_5A_PATH.read_text(encoding="utf-8"))
    entry = freeze_5a["artifacts"][artifact_key]
    path = REPO_ROOT / entry["path"]
    assert path.is_file(), f"{entry['path']} is missing"
    assert _sha256(path) == entry["sha256"], f"{entry['path']} drifted since the Fase 5A freeze"


def test_phase_5a_freeze_file_itself_is_never_edited():
    """A meta-check: this freeze is Fase 5A's own historical artifact and
    is never listed among its own certified artifacts (it certifies
    others, not itself) - Fase 5B's own freeze (phase-5b-semantic-freeze)
    is the one that references phase-5a-semantic-freeze.json by hash.
    """
    freeze_5b_path = REPO_ROOT / "data" / "manifests" / "phase-5b-semantic-freeze.json"
    if not freeze_5b_path.exists():
        pytest.skip("phase-5b-semantic-freeze.json not present yet")
    freeze_5b = json.loads(freeze_5b_path.read_text(encoding="utf-8"))
    ref = freeze_5b["predecessor_semantic_freeze_reference"]
    assert _sha256(FREEZE_5A_PATH) == ref["sha256"]


def test_no_data_questions_file_changed_since_phase_4e():
    """Re-derives the same per-target aggregate hash
    ``tests/test_phase4e_freeze.py`` already checks, as an independent
    Fase 5B-owned confirmation that this phase never touched the corpus.
    """
    freeze_4e = json.loads(FREEZE_4E_PATH.read_text(encoding="utf-8"))
    targets = {
        "2008-b": "data/questions/2008/all-computing",
        "2011": "data/questions/2011/all-computing",
        "2021-ciencia-da-computacao-bacharelado": "data/questions/2021/ciencia-da-computacao-bacharelado",
        "2021-ciencia-da-computacao-licenciatura": "data/questions/2021/ciencia-da-computacao-licenciatura",
        "2021-sistemas-de-informacao": "data/questions/2021/sistemas-de-informacao",
    }
    for label, subdir in targets.items():
        root = REPO_ROOT / subdir
        files = sorted(
            (p for p in root.rglob("*") if p.is_file() and p.suffix in (".md", ".png")),
            key=lambda p: p.relative_to(REPO_ROOT).as_posix(),
        )
        lines = [f"{_sha256(p)}  {p.relative_to(REPO_ROOT).as_posix()}" for p in files]
        actual = hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()
        assert freeze_4e["question_outputs"][label] == actual, f"{label} corpus drifted"


def test_no_gold_manifest_changed_since_phase_4e():
    freeze_4e = json.loads(FREEZE_4E_PATH.read_text(encoding="utf-8"))
    for entry in freeze_4e["manifests"]:
        path = REPO_ROOT / entry["path"]
        assert path.is_file(), f"{entry['path']} is missing"
        assert _sha256(path) == entry["sha256"], f"{entry['path']} drifted since Fase 4E"


def test_working_tree_never_touches_data_questions():
    """A live git check: no path under data/questions appears in the
    working tree diff at all during this phase.
    """
    result = subprocess.run(
        ["git", "status", "--porcelain=v1", "--", "data/questions"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "", f"unexpected data/questions changes: {result.stdout}"
