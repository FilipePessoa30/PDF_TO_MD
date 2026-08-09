from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from enade.cli import app
from enade.inventory.manifest import read_manifest_yaml, write_manifest_yaml
from enade.inventory.scanner import scan_corpus
from enade.models.provenance import SourceRepository

runner = CliRunner()


def test_doctor_reports_environment():
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "Python >= 3.11" in result.stdout
    assert "pydantic" in result.stdout


def test_inventory_writes_manifest_and_matches_expected_shape(git_corpus: Path, tmp_path: Path):
    output = tmp_path / "manifest.yaml"
    result = runner.invoke(
        app, ["inventory", "--corpus-root", str(git_corpus), "--output", str(output)]
    )

    assert result.exit_code == 0, result.stdout
    assert output.exists()

    manifest = read_manifest_yaml(output)
    assert manifest.summary["bundles"] == 1
    assert "DIVERGES" in result.stdout  # our tiny fixture corpus is not the full 16-bundle corpus


def test_inventory_fails_clearly_when_corpus_root_missing(tmp_path: Path):
    result = runner.invoke(
        app,
        [
            "inventory",
            "--corpus-root",
            str(tmp_path / "does-not-exist"),
            "--output",
            str(tmp_path / "m.yaml"),
        ],
    )
    assert result.exit_code != 0


def test_validate_manifest_ok_for_freshly_generated_manifest(git_corpus: Path, tmp_path: Path):
    manifest_path = tmp_path / "manifest.yaml"
    repo = SourceRepository(
        repository_url="https://example.invalid/geacc/enade.git", ref="master", commit_sha="0" * 40
    )
    manifest = scan_corpus(git_corpus, repo, tool_version="test")
    write_manifest_yaml(manifest, manifest_path)

    result = runner.invoke(app, ["validate-manifest", "--manifest-path", str(manifest_path)])
    assert result.exit_code == 0, result.stdout
    assert "OK" in result.stdout


def test_validate_manifest_fails_on_tampered_manifest(git_corpus: Path, tmp_path: Path):
    manifest_path = tmp_path / "manifest.yaml"
    repo = SourceRepository(
        repository_url="https://example.invalid/geacc/enade.git", ref="master", commit_sha="0" * 40
    )
    manifest = scan_corpus(git_corpus, repo, tool_version="test")
    manifest.summary["bundles"] = 999
    write_manifest_yaml(manifest, manifest_path)

    result = runner.invoke(app, ["validate-manifest", "--manifest-path", str(manifest_path)])
    assert result.exit_code != 0
    assert "FAILED" in result.stdout


def test_validate_manifest_missing_file_fails(tmp_path: Path):
    result = runner.invoke(
        app, ["validate-manifest", "--manifest-path", str(tmp_path / "nope.yaml")]
    )
    assert result.exit_code != 0


def test_validate_schema_passes_on_real_fixtures():
    fixtures_dir = Path(__file__).parent / "fixtures"
    result = runner.invoke(app, ["validate-schema", "--fixtures-dir", str(fixtures_dir)])
    assert result.exit_code == 0, result.stdout
    assert "valid" in result.stdout


def test_validate_schema_fails_on_broken_fixture_set(tmp_path: Path):
    broken_dir = tmp_path / "fixtures"
    questions_valid = broken_dir / "questions" / "valid"
    questions_valid.mkdir(parents=True)
    (questions_valid / "broken.md").write_text("not even front matter", encoding="utf-8")

    result = runner.invoke(app, ["validate-schema", "--fixtures-dir", str(broken_dir)])
    assert result.exit_code != 0
    assert "FAIL" in result.stdout


def test_is_git_ignored_distinguishes_scratch_from_tracked_paths():
    """Regression test for the Phase 1B asset-trackability gate (PROMPT
    section 2): `enade audit-extraction` must FAIL a question whose asset
    file would silently never make it into a commit. Probes real paths in
    THIS repository against the real .gitignore rather than a synthetic
    fixture repo, since the whole point is to catch drift in the actual
    rules a future `git add` would honor.
    """
    from enade.cli import PROJECT_ROOT, _is_git_ignored

    ignored_probe = PROJECT_ROOT / ".scratch" / "_gitignore_probe.txt"
    tracked_probe = PROJECT_ROOT / "data" / "questions" / "_gitignore_probe.md"
    try:
        ignored_probe.parent.mkdir(parents=True, exist_ok=True)
        ignored_probe.write_text("probe", encoding="utf-8")
        tracked_probe.write_text("probe", encoding="utf-8")

        assert _is_git_ignored(ignored_probe) is True
        assert _is_git_ignored(tracked_probe) is False
    finally:
        ignored_probe.unlink(missing_ok=True)
        tracked_probe.unlink(missing_ok=True)
        if ignored_probe.parent.exists() and not any(ignored_probe.parent.iterdir()):
            ignored_probe.parent.rmdir()


def test_audit_extraction_fails_when_asset_is_gitignored(tmp_path: Path):
    """A question whose declared asset resolves to a path .gitignore would
    exclude must fail the audit, even though the file exists on disk with a
    matching hash - existence + hash match alone is not "trackable".
    """
    import hashlib

    from enade.cli import PROJECT_ROOT

    # A real, currently-ignored location inside this repo (see .gitignore's
    # Python-cache rule) - the asset "exists" and can be hash-verified, but
    # would never survive a `git add .`.
    course_dir = PROJECT_ROOT / "__pycache__" / "_gitignore_regression_probe"
    asset_path = course_dir / "enade-2099-x-q01" / "figure-01.png"
    md_path = course_dir / "enade-2099-x-q01.md"
    try:
        asset_path.parent.mkdir(parents=True, exist_ok=True)
        png_bytes = b"\x89PNG\r\n\x1a\nnot a real png, just probe bytes"
        asset_path.write_bytes(png_bytes)
        sha = hashlib.sha256(png_bytes).hexdigest()
        md_path.write_text(
            f"""---
id: enade-2099-x-q01
exam_year: 2099
source_occurrences:
- exam_id: enade-2099-x
  pdf_sha256: {"a" * 64}
  source_path: 2099/x1_prova.pdf
  pages: [1]
  question_number: 1
  section: componente-especifico-objetiva
applicable_courses: [ciencia-da-computacao-bacharelado]
section: componente-especifico-objetiva
question_number: 1
question_type: multiple_choice
correct_answer: A
official_answer_source: 2099/x2_gabarito.pdf
answer_validation_status: validated
answer_standard: null
assets:
- id: figure-01
  type: diagram
  path: enade-2099-x-q01/figure-01.png
  source_page: 1
  extraction_method: raster_crop
  sha256: {sha}
  alt_text: null
  caption: null
subjects: []
topics: []
concepts: []
keywords: []
competencies: []
prerequisites: []
difficulty: null
alternative_diagnostics: {{}}
extraction_method: text_layer
ocr_confidence: null
extraction_status: extracted
taxonomy_review_status: pending
---

# Questão 1

Enunciado de sondagem.

![fig](enade-2099-x-q01/figure-01.png)

## Alternativas

A. um
B. dois
C. três
D. quatro
E. cinco
""",
            encoding="utf-8",
        )

        result = runner.invoke(
            app,
            [
                "audit-extraction",
                "--questions-dir",
                str(course_dir),
                "--corpus-root",
                str(tmp_path),
            ],
        )
        assert result.exit_code != 0
        assert "gitignored" in result.stdout
    finally:
        asset_path.unlink(missing_ok=True)
        md_path.unlink(missing_ok=True)
        if asset_path.parent.exists():
            asset_path.parent.rmdir()
        if course_dir.exists():
            course_dir.rmdir()
