"""CLI tests for the semantic-layer commands (PROMPT Fase 5A sections 24,
26): validate-taxonomy, validate-semantic-annotations, build-semantic-review.
Exercises the real, published pilot artifacts for the "clean" cases (never
a synthetic stand-in for the actual corpus this phase produced), and
synthetic broken fixtures for the negative cases.
"""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from enade.cli import app

runner = CliRunner()

REPO_ROOT = Path(__file__).resolve().parent.parent
REAL_TAXONOMY = REPO_ROOT / "data" / "taxonomy" / "computing-v1.yaml"
REAL_ANNOTATIONS = REPO_ROOT / "data" / "semantic" / "question-annotations-5a.json"


# --- validate-taxonomy -------------------------------------------------


def test_validate_taxonomy_passes_on_real_computing_v1():
    result = runner.invoke(app, ["validate-taxonomy", "--taxonomy-path", str(REAL_TAXONOMY)])
    assert result.exit_code == 0, result.stdout
    assert "OK" in result.stdout


def test_validate_taxonomy_missing_file_fails():
    result = runner.invoke(app, ["validate-taxonomy", "--taxonomy-path", "does-not-exist.yaml"])
    assert result.exit_code != 0


def test_validate_taxonomy_fails_on_broken_yaml(tmp_path: Path):
    broken = tmp_path / "broken-taxonomy.yaml"
    broken.write_text(
        "taxonomy_id: broken\nversion: '1.0.0'\nstatus: provisional\nnotice: x\n"
        "subjects:\n  - id: s1\n    name: S1\n    topics:\n      - id: t1\n"
        "        name: T1\n        parent_id: does-not-exist\n",
        encoding="utf-8",
    )
    result = runner.invoke(app, ["validate-taxonomy", "--taxonomy-path", str(broken)])
    assert result.exit_code != 0
    assert "FAIL" in result.stdout


def test_validate_taxonomy_never_writes(tmp_path: Path):
    before = REAL_TAXONOMY.read_bytes()
    runner.invoke(app, ["validate-taxonomy", "--taxonomy-path", str(REAL_TAXONOMY)])
    assert REAL_TAXONOMY.read_bytes() == before


# --- validate-semantic-annotations -------------------------------------


def test_validate_semantic_annotations_passes_on_real_pilot_set():
    result = runner.invoke(
        app,
        [
            "validate-semantic-annotations",
            "--taxonomy-path",
            str(REAL_TAXONOMY),
            "--annotations-path",
            str(REAL_ANNOTATIONS),
            "--project-root",
            str(REPO_ROOT),
        ],
    )
    assert result.exit_code == 0, result.stdout
    assert "0 diagnostic(s)" in result.stdout


def test_validate_semantic_annotations_missing_file_fails():
    result = runner.invoke(
        app,
        [
            "validate-semantic-annotations",
            "--annotations-path",
            "does-not-exist.json",
        ],
    )
    assert result.exit_code != 0


def test_validate_semantic_annotations_flags_nonexistent_topic(tmp_path: Path):
    real_md = (
        REPO_ROOT / "data" / "questions" / "2011" / "all-computing" / "enade-2011-computing-q01.md"
    )
    import hashlib

    source_hash = hashlib.sha256(real_md.read_bytes()).hexdigest()
    excerpt = "excerpt"
    broken_annotation = {
        "question_id": "enade-2011-computing-q01",
        "taxonomy_version": "computing-v1@1.0.0-pilot",
        "source_hash": source_hash,
        "component": "componente_especifico",
        "primary_topics": ["this-topic-does-not-exist"],
        "secondary_topics": [],
        "concepts": [],
        "context_tags": [],
        "cognitive_skills": ["apply"],
        "search_terms": [],
        "evidence": [
            {
                "source_kind": "statement",
                "source_locator": "statement",
                "source_sha256": source_hash,
                "text_excerpt": excerpt,
                "excerpt_sha256": hashlib.sha256(excerpt.encode()).hexdigest(),
            }
        ],
        "annotation_method": "manual_expert_reading_student_visible_content_only",
        "annotation_status": "proposed",
        "confidence": "high",
    }
    broken_path = tmp_path / "broken-annotations.json"
    broken_path.write_text(
        json.dumps({"schema_version": 1, "annotations": [broken_annotation]}), encoding="utf-8"
    )

    result = runner.invoke(
        app,
        [
            "validate-semantic-annotations",
            "--taxonomy-path",
            str(REAL_TAXONOMY),
            "--annotations-path",
            str(broken_path),
            "--project-root",
            str(REPO_ROOT),
        ],
    )
    assert result.exit_code != 0
    assert "topic_not_found" in result.stdout


def test_validate_semantic_annotations_never_writes():
    before = REAL_ANNOTATIONS.read_bytes()
    runner.invoke(
        app,
        [
            "validate-semantic-annotations",
            "--taxonomy-path",
            str(REAL_TAXONOMY),
            "--annotations-path",
            str(REAL_ANNOTATIONS),
            "--project-root",
            str(REPO_ROOT),
        ],
    )
    assert REAL_ANNOTATIONS.read_bytes() == before


# --- build-semantic-review ----------------------------------------------


def test_build_semantic_review_is_deterministic(tmp_path: Path):
    out_a = tmp_path / "review-a.md"
    out_b = tmp_path / "review-b.md"
    result_a = runner.invoke(
        app,
        [
            "build-semantic-review",
            "--taxonomy-path",
            str(REAL_TAXONOMY),
            "--annotations-path",
            str(REAL_ANNOTATIONS),
            "--output-path",
            str(out_a),
        ],
    )
    result_b = runner.invoke(
        app,
        [
            "build-semantic-review",
            "--taxonomy-path",
            str(REAL_TAXONOMY),
            "--annotations-path",
            str(REAL_ANNOTATIONS),
            "--output-path",
            str(out_b),
        ],
    )
    assert result_a.exit_code == 0
    assert result_b.exit_code == 0
    assert out_a.read_text(encoding="utf-8") == out_b.read_text(encoding="utf-8")


def test_build_semantic_review_never_writes_data_questions():
    from enade.inventory.pdfmeta import sha256_of_file

    questions_dir = REPO_ROOT / "data" / "questions"
    before = {p: sha256_of_file(p) for p in sorted(questions_dir.rglob("*")) if p.is_file()}
    runner.invoke(
        app,
        [
            "build-semantic-review",
            "--taxonomy-path",
            str(REAL_TAXONOMY),
            "--annotations-path",
            str(REAL_ANNOTATIONS),
        ],
    )
    after = {p: sha256_of_file(p) for p in sorted(questions_dir.rglob("*")) if p.is_file()}
    assert before == after


def test_build_semantic_review_never_includes_answer_standard_text():
    out_path = REPO_ROOT / "docs" / "semantic-pilot-review.md"
    runner.invoke(
        app,
        [
            "build-semantic-review",
            "--taxonomy-path",
            str(REAL_TAXONOMY),
            "--annotations-path",
            str(REAL_ANNOTATIONS),
            "--output-path",
            str(out_path),
        ],
    )
    content = out_path.read_text(encoding="utf-8")
    # The packet's own header disclaims (in prose) that the gabarito never
    # appears - that one sentence is expected and is not itself a leak.
    disclaimer = (
        "O gabarito e o padrão de resposta nunca aparecem neste pacote "
        "nem no modelo de anotação subjacente"
    )
    assert disclaimer in content
    body = content.replace(disclaimer, "")
    for banned in ("gabarito", "resposta correta", "answer_standard", "padrão de resposta"):
        assert banned.lower() not in body.lower()
