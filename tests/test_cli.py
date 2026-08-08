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
