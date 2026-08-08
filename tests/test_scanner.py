from __future__ import annotations

from pathlib import Path

from enade.inventory.manifest import manifest_to_yaml_dict
from enade.inventory.scanner import scan_corpus
from enade.models.enums import CourseCode
from enade.models.provenance import SourceRepository
from tests.conftest import write_pdf

REPO = SourceRepository(
    repository_url="https://example.invalid/geacc/enade.git",
    ref="master",
    commit_sha="0" * 40,
)


def _bundle_key(manifest, year, letter):
    for bundle in manifest.bundles:
        if bundle.year == year and bundle.course_letter == letter:
            return bundle
    raise AssertionError(f"no bundle found for year={year} letter={letter!r}")


def test_scanner_groups_complete_trio(synthetic_corpus: Path):
    manifest = scan_corpus(synthetic_corpus, REPO, tool_version="test")
    bundle = _bundle_key(manifest, 2005, "b")

    assert bundle.exam is not None
    assert bundle.answer_key is not None
    assert bundle.answer_standard is not None
    assert bundle.missing == []
    assert bundle.course_codes == [CourseCode.CC_BACHARELADO]
    assert bundle.is_unified_booklet is False


def test_scanner_detects_2011_unified_booklet(synthetic_corpus: Path):
    manifest = scan_corpus(synthetic_corpus, REPO, tool_version="test")
    bundle = _bundle_key(manifest, 2011, None)

    assert bundle.is_unified_booklet is True
    assert bundle.course_codes == [CourseCode.ALL_COMPUTING]
    assert bundle.missing == []


def test_scanner_detects_exam_without_answer_key(synthetic_corpus: Path):
    manifest = scan_corpus(synthetic_corpus, REPO, tool_version="test")
    bundle = _bundle_key(manifest, 2008, "e")

    assert bundle.exam is not None
    assert bundle.answer_key is None
    assert "answer_key" in bundle.missing
    assert any(
        i.kind == "exam_without_answer_key" and i.severity == "error" for i in manifest.issues
    )
    assert any(i.kind == "exam_without_answer_standard" for i in manifest.issues)


def test_scanner_detects_answer_key_without_exam(synthetic_corpus: Path):
    manifest = scan_corpus(synthetic_corpus, REPO, tool_version="test")
    bundle = _bundle_key(manifest, 2014, "l")

    assert bundle.exam is None
    assert bundle.answer_key is not None
    assert any(
        i.kind == "answer_key_without_exam" and i.severity == "error" for i in manifest.issues
    )


def test_scanner_detects_orphan_files(synthetic_corpus: Path):
    manifest = scan_corpus(synthetic_corpus, REPO, tool_version="test")

    orphan_names = {doc.filename for doc in manifest.orphan_files}
    assert "x9_relatorio.pdf" in orphan_names
    assert any(i.kind == "unexpected_filename" for i in manifest.issues)


def test_scanner_detects_unexpected_directory_and_root_entry(synthetic_corpus: Path):
    manifest = scan_corpus(synthetic_corpus, REPO, tool_version="test")

    assert any(i.kind == "unexpected_directory" and i.path == "misc" for i in manifest.issues)
    assert any(i.kind == "unexpected_root_entry" and i.path == "notes.txt" for i in manifest.issues)


def test_scanner_ignores_git_metadata_directory(synthetic_corpus: Path):
    manifest = scan_corpus(synthetic_corpus, REPO, tool_version="test")
    assert not any(i.path == ".git" for i in manifest.issues)


def test_scanner_summary_counts(synthetic_corpus: Path):
    manifest = scan_corpus(synthetic_corpus, REPO, tool_version="test")

    assert manifest.summary["bundles"] == 4  # 2005/b, 2008/e, 2011/unified, 2014/l
    assert manifest.summary["orphan_files"] == 1
    assert manifest.summary["errors"] == 2  # exam_without_answer_key, answer_key_without_exam
    assert manifest.summary["warnings"] == 4


def test_scanner_is_deterministic(synthetic_corpus: Path):
    manifest_1 = scan_corpus(synthetic_corpus, REPO, tool_version="test")
    manifest_2 = scan_corpus(synthetic_corpus, REPO, tool_version="test")

    dict_1 = manifest_to_yaml_dict(manifest_1, include_generated_at=False)
    dict_2 = manifest_to_yaml_dict(manifest_2, include_generated_at=False)
    assert dict_1 == dict_2


def test_scanner_detects_duplicate_document_mapping(tmp_path: Path):
    root = tmp_path / "corpus"
    write_pdf(root / "2021" / "b1_prova.pdf", ["FIRST COPY"])
    # Different filename, but the zero-padded sequence still parses to the
    # same (year, course_letter, doctype) slot as b1_prova.pdf above. Using
    # a case difference here would not be a reliable collision on
    # case-insensitive filesystems (e.g. Windows/NTFS, default macOS/APFS).
    write_pdf(root / "2021" / "b01_prova.pdf", ["SECOND COPY, SAME SLOT"])

    manifest = scan_corpus(root, REPO, tool_version="test")

    assert any(i.kind == "duplicate_document" for i in manifest.issues)
    # the loser of the collision is recorded as an orphan, not silently dropped.
    assert len(manifest.orphan_files) == 1
