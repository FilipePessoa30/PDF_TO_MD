"""CLI tests for the Fase 5B reconciliation commands (PROMPT Fase 5B
section 26): validate-semantic-migration, build-human-adjudication.
Exercises the real, published 5B artifacts for the clean cases, and
synthetic broken fixtures for the negative ones.
"""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from enade.cli import app

runner = CliRunner()

REPO_ROOT = Path(__file__).resolve().parent.parent
COMPUTING_V11 = REPO_ROOT / "data" / "taxonomy" / "computing-v1.1.yaml"
GENERAL_ED = REPO_ROOT / "data" / "taxonomy" / "general-education-v1.yaml"
PREDECESSOR_ANNOTATIONS = REPO_ROOT / "data" / "semantic" / "question-annotations-5a.json"
ANNOTATIONS_5B = REPO_ROOT / "data" / "semantic" / "question-annotations-5b.json"
MIGRATION = REPO_ROOT / "data" / "semantic" / "migration-5a-to-5b.json"
ADJUDICATION_TEMPLATE = REPO_ROOT / "data" / "semantic" / "human-adjudication-template-5b.json"


# --- validate-semantic-migration -----------------------------------------


def test_validate_semantic_migration_passes_on_the_real_5b_artifacts():
    result = runner.invoke(
        app,
        [
            "validate-semantic-migration",
            "--computing-taxonomy-path",
            str(COMPUTING_V11),
            "--general-education-taxonomy-path",
            str(GENERAL_ED),
            "--predecessor-annotations-path",
            str(PREDECESSOR_ANNOTATIONS),
            "--annotations-path",
            str(ANNOTATIONS_5B),
            "--migration-path",
            str(MIGRATION),
            "--project-root",
            str(REPO_ROOT),
        ],
    )
    assert result.exit_code == 0, result.stdout
    assert "0 diagnostic(s)" in result.stdout


def test_validate_semantic_migration_missing_file_fails():
    result = runner.invoke(
        app,
        ["validate-semantic-migration", "--migration-path", "does-not-exist.json"],
    )
    assert result.exit_code != 0


def test_validate_semantic_migration_flags_a_question_dropped_from_the_successor(tmp_path: Path):
    payload = json.loads(ANNOTATIONS_5B.read_text(encoding="utf-8"))
    payload["annotations"] = payload["annotations"][1:]  # drop the first question
    broken_annotations = tmp_path / "broken-5b.json"
    broken_annotations.write_text(json.dumps(payload), encoding="utf-8")

    broken_migration = json.loads(MIGRATION.read_text(encoding="utf-8"))
    broken_migration_path = tmp_path / "broken-migration.json"
    broken_migration_path.write_text(json.dumps(broken_migration), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "validate-semantic-migration",
            "--computing-taxonomy-path",
            str(COMPUTING_V11),
            "--general-education-taxonomy-path",
            str(GENERAL_ED),
            "--predecessor-annotations-path",
            str(PREDECESSOR_ANNOTATIONS),
            "--annotations-path",
            str(broken_annotations),
            "--migration-path",
            str(broken_migration_path),
            "--project-root",
            str(REPO_ROOT),
        ],
    )
    assert result.exit_code != 0
    assert "missing from successor" in result.stdout


def test_validate_semantic_migration_flags_missing_migration_reason(tmp_path: Path):
    migration_payload = json.loads(MIGRATION.read_text(encoding="utf-8"))
    migration_payload["entries"][0]["change_reason"] = ""
    broken_migration_path = tmp_path / "broken-migration.json"
    broken_migration_path.write_text(json.dumps(migration_payload), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "validate-semantic-migration",
            "--computing-taxonomy-path",
            str(COMPUTING_V11),
            "--general-education-taxonomy-path",
            str(GENERAL_ED),
            "--predecessor-annotations-path",
            str(PREDECESSOR_ANNOTATIONS),
            "--annotations-path",
            str(ANNOTATIONS_5B),
            "--migration-path",
            str(broken_migration_path),
            "--project-root",
            str(REPO_ROOT),
        ],
    )
    assert result.exit_code != 0
    assert "migration_without_reason" in result.stdout


def test_validate_semantic_migration_never_writes():
    before = ANNOTATIONS_5B.read_bytes()
    runner.invoke(
        app,
        [
            "validate-semantic-migration",
            "--computing-taxonomy-path",
            str(COMPUTING_V11),
            "--general-education-taxonomy-path",
            str(GENERAL_ED),
            "--predecessor-annotations-path",
            str(PREDECESSOR_ANNOTATIONS),
            "--annotations-path",
            str(ANNOTATIONS_5B),
            "--migration-path",
            str(MIGRATION),
            "--project-root",
            str(REPO_ROOT),
        ],
    )
    assert ANNOTATIONS_5B.read_bytes() == before


# --- build-human-adjudication ---------------------------------------------


def test_build_human_adjudication_is_deterministic(tmp_path: Path):
    out_a = tmp_path / "adj-a.json"
    out_b = tmp_path / "adj-b.json"
    result_a = runner.invoke(
        app,
        [
            "build-human-adjudication",
            "--annotations-path",
            str(ANNOTATIONS_5B),
            "--output-path",
            str(out_a),
        ],
    )
    result_b = runner.invoke(
        app,
        [
            "build-human-adjudication",
            "--annotations-path",
            str(ANNOTATIONS_5B),
            "--output-path",
            str(out_b),
        ],
    )
    assert result_a.exit_code == 0
    assert result_b.exit_code == 0
    assert out_a.read_text(encoding="utf-8") == out_b.read_text(encoding="utf-8")


def test_build_human_adjudication_refuses_to_overwrite_a_real_human_decision(tmp_path: Path):
    existing = json.loads(ADJUDICATION_TEMPLATE.read_text(encoding="utf-8"))
    existing["entries"][0]["human_decision"] = "approve"
    existing["entries"][0]["reviewer"] = "Test Reviewer"
    existing["entries"][0]["reviewed_at"] = "2026-01-01"
    protected_path = tmp_path / "protected.json"
    protected_path.write_text(json.dumps(existing), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "build-human-adjudication",
            "--annotations-path",
            str(ANNOTATIONS_5B),
            "--output-path",
            str(protected_path),
        ],
    )
    assert result.exit_code != 0
    assert "refusing to overwrite" in result.stdout

    reloaded = json.loads(protected_path.read_text(encoding="utf-8"))
    assert reloaded["entries"][0]["human_decision"] == "approve"


def test_build_human_adjudication_force_overwrites_even_with_a_human_decision(tmp_path: Path):
    existing = json.loads(ADJUDICATION_TEMPLATE.read_text(encoding="utf-8"))
    existing["entries"][0]["human_decision"] = "approve"
    existing["entries"][0]["reviewer"] = "Test Reviewer"
    existing["entries"][0]["reviewed_at"] = "2026-01-01"
    protected_path = tmp_path / "protected.json"
    protected_path.write_text(json.dumps(existing), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "build-human-adjudication",
            "--annotations-path",
            str(ANNOTATIONS_5B),
            "--output-path",
            str(protected_path),
            "--force",
        ],
    )
    assert result.exit_code == 0
    reloaded = json.loads(protected_path.read_text(encoding="utf-8"))
    assert all(e["human_decision"] is None for e in reloaded["entries"])


def test_build_human_adjudication_all_entries_have_null_human_fields():
    result = runner.invoke(app, ["build-human-adjudication"])
    assert result.exit_code == 0
    payload = json.loads(ADJUDICATION_TEMPLATE.read_text(encoding="utf-8"))
    for entry in payload["entries"]:
        assert entry["human_decision"] is None
        assert entry["reviewer"] is None
        assert entry["reviewed_at"] is None
