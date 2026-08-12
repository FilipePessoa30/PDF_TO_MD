from __future__ import annotations

import json
from pathlib import Path

from enade.extraction.visual_audit import assess_visual_audit_coverage


def _write(tmp_path: Path, data: dict) -> Path:
    path = tmp_path / "visual-audit.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_missing_file_means_every_id_not_performed(tmp_path: Path):
    canonical = frozenset({"q01", "q02", "q03"})
    cov = assess_visual_audit_coverage(tmp_path / "missing.json", canonical)
    assert cov.total == 3
    assert cov.not_performed_count == 3
    assert cov.passed_count == 0
    assert cov.failed_count == 0
    assert cov.fully_covered is False


def test_fully_covered_when_every_canonical_id_has_a_verdict(tmp_path: Path):
    canonical = frozenset({"q01", "q02"})
    path = _write(
        tmp_path,
        {"q01": {"status": "passed"}, "q02": {"status": "failed"}},
    )
    cov = assess_visual_audit_coverage(path, canonical)
    assert cov.total == 2
    assert cov.passed_count == 1
    assert cov.failed_count == 1
    assert cov.not_performed_count == 0
    assert cov.fully_covered is True


def test_partial_coverage_sums_to_canonical_count(tmp_path: Path):
    canonical = frozenset({"q01", "q02", "q03", "q04", "q05"})
    path = _write(tmp_path, {"q01": {"status": "passed"}, "q02": {"status": "failed"}})
    cov = assess_visual_audit_coverage(path, canonical)
    assert cov.total == len(canonical) == 5
    assert cov.not_performed_count == 3


def test_unexpected_id_is_reported_and_excluded_from_total(tmp_path: Path):
    canonical = frozenset({"q01"})
    path = _write(tmp_path, {"q01": {"status": "passed"}, "q99": {"status": "passed"}})
    cov = assess_visual_audit_coverage(path, canonical)
    assert cov.unexpected_ids == frozenset({"q99"})
    assert cov.total == 1  # q99 never counted - it isn't a canonical id
    assert cov.fully_covered is False


def test_duplicate_json_key_is_detected(tmp_path: Path):
    canonical = frozenset({"q01"})
    path = tmp_path / "visual-audit.json"
    # Hand-write the JSON text so the duplicate key survives to disk -
    # a dict literal would silently drop it before we ever get to write().
    path.write_text('{"q01": {"status": "passed"}, "q01": {"status": "failed"}}', encoding="utf-8")
    cov = assess_visual_audit_coverage(path, canonical)
    assert cov.duplicate_ids == frozenset({"q01"})
    assert cov.fully_covered is False


def test_status_string_shorthand_is_accepted(tmp_path: Path):
    canonical = frozenset({"q01"})
    path = _write(tmp_path, {"q01": "passed"})
    cov = assess_visual_audit_coverage(path, canonical)
    assert cov.passed_count == 1


def test_real_2011_manifest_reconciles_to_exactly_55():
    from enade.markdown_format import load_questions_directory

    canonical = frozenset(load_questions_directory(Path("data/questions/2011/all-computing")))
    cov = assess_visual_audit_coverage(
        Path("data/manifests/visual-audit-2011-computing.json"), canonical
    )
    assert cov.total == 55
    assert cov.unexpected_ids == frozenset()
    assert cov.duplicate_ids == frozenset()
