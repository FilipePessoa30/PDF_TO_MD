from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from enade.inventory.manifest import manifest_to_yaml_dict, read_manifest_yaml, write_manifest_yaml
from enade.inventory.pdfmeta import sha256_of_file
from enade.inventory.scanner import scan_corpus
from enade.models.provenance import SourceRepository
from enade.validation.manifest_checks import check_manifest_matches_filesystem, validate_manifest
from tests.conftest import write_pdf

REPO = SourceRepository(
    repository_url="https://example.invalid/geacc/enade.git", ref="master", commit_sha="0" * 40
)


def test_write_then_read_manifest_round_trips(tmp_path: Path, synthetic_corpus: Path):
    manifest = scan_corpus(synthetic_corpus, REPO, tool_version="test")
    out_path = tmp_path / "manifest.yaml"

    write_manifest_yaml(manifest, out_path)
    reloaded = read_manifest_yaml(out_path)

    assert manifest_to_yaml_dict(manifest, include_generated_at=False) == manifest_to_yaml_dict(
        reloaded, include_generated_at=False
    )


def test_read_static_manifest_fixture_is_valid(fixtures_dir: Path):
    manifest = read_manifest_yaml(fixtures_dir / "manifest" / "minimal-manifest.yaml")
    result = validate_manifest(manifest)

    assert result.ok, result.errors
    assert len(result.warnings) == 1  # the recorded exam_without_answer_standard issue


def test_validate_manifest_flags_tampered_summary(fixtures_dir: Path):
    manifest = read_manifest_yaml(fixtures_dir / "manifest" / "minimal-manifest.yaml")
    manifest.summary["bundles"] = 999  # simulate a hand-edited / corrupted manifest

    result = validate_manifest(manifest)

    assert not result.ok
    assert any("summary" in e for e in result.errors)


def test_validate_manifest_flags_duplicate_exam_id(fixtures_dir: Path):
    manifest = read_manifest_yaml(fixtures_dir / "manifest" / "minimal-manifest.yaml")
    duplicate = manifest.bundles[0].model_copy(deep=True)
    manifest.bundles.append(duplicate)

    result = validate_manifest(manifest)

    assert not result.ok
    assert any("duplicate exam_id" in e for e in result.errors)


def test_check_manifest_matches_filesystem_detects_missing_file(
    tmp_path: Path, synthetic_corpus: Path
):
    manifest = scan_corpus(synthetic_corpus, REPO, tool_version="test")
    (synthetic_corpus / "2005" / "b1_prova.pdf").unlink()

    problems = check_manifest_matches_filesystem(manifest, synthetic_corpus)

    assert any("no longer exists" in p for p in problems)


def test_check_manifest_matches_filesystem_detects_sha256_drift(synthetic_corpus: Path):
    manifest = scan_corpus(synthetic_corpus, REPO, tool_version="test")
    write_pdf(synthetic_corpus / "2005" / "b1_prova.pdf", ["CONTENT WAS SILENTLY CHANGED"])

    problems = check_manifest_matches_filesystem(manifest, synthetic_corpus)

    assert any("sha256 drifted" in p for p in problems)


def test_check_manifest_matches_filesystem_ok_when_untouched(synthetic_corpus: Path):
    manifest = scan_corpus(synthetic_corpus, REPO, tool_version="test")
    problems = check_manifest_matches_filesystem(manifest, synthetic_corpus)
    assert problems == []


def test_sha256_of_file_matches_manifest_record(synthetic_corpus: Path):
    manifest = scan_corpus(synthetic_corpus, REPO, tool_version="test")
    bundle = next(b for b in manifest.bundles if b.year == 2005 and b.course_letter == "b")
    assert bundle.exam is not None

    actual = sha256_of_file(synthetic_corpus / bundle.exam.source_path)
    assert actual == bundle.exam.sha256


@pytest.mark.parametrize("missing_field", ["repository", "bundles"])
def test_read_manifest_yaml_rejects_missing_required_fields(
    tmp_path: Path, fixtures_dir: Path, missing_field: str
):
    import yaml

    data = yaml.safe_load(
        (fixtures_dir / "manifest" / "minimal-manifest.yaml").read_text(encoding="utf-8")
    )
    del data[missing_field]
    broken_path = tmp_path / "broken.yaml"
    broken_path.write_text(yaml.safe_dump(data), encoding="utf-8")

    with pytest.raises(ValidationError):
        read_manifest_yaml(broken_path)
