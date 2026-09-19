from __future__ import annotations

from pathlib import Path

from enade.extraction.source_availability import (
    REQUIRED_SEARCH_METHODS,
    SourceAvailabilityLedger,
    SourceAvailabilityRecord,
    SourceDocument,
    SourcePackage,
    is_confirmed_unavailable,
    load_source_availability,
    verify_source_hashes_match,
)


def _package(**overrides) -> SourcePackage:
    base = dict(
        source_package_id="pkg-test",
        coverage_claim="test package covering one padrao document",
        documents=[
            SourceDocument(
                path="2008/b3_padrao.pdf",
                sha256="a" * 64,
                role="padrao",
                page_count=6,
                acquisition_provenance="test fixture",
            )
        ],
    )
    base.update(overrides)
    return SourcePackage(**base)


def _record(**overrides) -> SourceAvailabilityRecord:
    base = dict(
        source_availability_id="sa-test-d09",
        subject_id="enade-2008-computing-d09",
        artifact_type="answer_standard",
        source_package_id="pkg-test",
        expected_source="2008/b3_padrao.pdf",
        source_hashes={"padrao": "a" * 64},
        pages_scanned=[1, 2, 3, 4, 5, 6],
        search_methods=["text", "rawdict", "texttrace", "images", "drawings"],
        expected_markers=["Questao 9"],
        observed_markers=["Questao 20", "Questao 39"],
        text_evidence="no marker found anywhere",
        image_evidence="every image attributed to a present question",
        drawing_evidence="zero drawings on every page",
        availability_status="source_unavailable_confirmed",
        review_status="reviewed",
        impact="answer_standard stays null",
        evidence="full negative search across all 6 pages",
    )
    base.update(overrides)
    return SourceAvailabilityRecord(**base)


def _ledger(*, records=None, packages=None) -> SourceAvailabilityLedger:
    return SourceAvailabilityLedger(
        source_packages=packages if packages is not None else [_package()],
        records=records if records is not None else [_record()],
    )


def test_load_source_availability_missing_file_returns_empty_ledger(tmp_path: Path):
    ledger = load_source_availability(tmp_path / "does-not-exist.yaml")
    assert ledger.source_packages == []
    assert ledger.records == []


def test_load_source_availability_reads_real_yaml(tmp_path: Path):
    path = tmp_path / "source-availability-2008.yaml"
    path.write_text(
        "schema_version: 1\n"
        "source_packages:\n"
        "  - source_package_id: pkg-test\n"
        "    coverage_claim: test\n"
        "    documents:\n"
        "      - path: 2008/b3_padrao.pdf\n"
        f"        sha256: {'a' * 64}\n"
        "        role: padrao\n"
        "        page_count: 6\n"
        "        acquisition_provenance: test\n"
        "records:\n"
        "  - source_availability_id: sa-test-d09\n"
        "    subject_id: enade-2008-computing-d09\n"
        "    artifact_type: answer_standard\n"
        "    source_package_id: pkg-test\n"
        "    expected_source: 2008/b3_padrao.pdf\n"
        f"    source_hashes: {{padrao: {'a' * 64}}}\n"
        "    pages_scanned: [1, 2, 3, 4, 5, 6]\n"
        "    search_methods: [text, rawdict, texttrace, images, drawings]\n"
        "    expected_markers: [Questao 9]\n"
        "    observed_markers: [Questao 20]\n"
        "    text_evidence: no marker found\n"
        "    image_evidence: every image attributed\n"
        "    drawing_evidence: zero drawings\n"
        "    availability_status: source_unavailable_confirmed\n"
        "    review_status: reviewed\n"
        "    impact: answer_standard stays null\n"
        "    evidence: full negative search\n",
        encoding="utf-8",
    )
    ledger = load_source_availability(path)
    assert len(ledger.source_packages) == 1
    assert len(ledger.records) == 1
    assert ledger.records[0].subject_id == "enade-2008-computing-d09"


def test_required_search_methods_covers_text_and_visual_evidence():
    # PROMPT Fase 3Z Section 9 - the D59 lesson: text-only was never
    # enough (D59's own rubric had zero text but a real embedded image).
    assert {"text", "rawdict", "texttrace", "images", "drawings"} == REQUIRED_SEARCH_METHODS


def test_is_confirmed_unavailable_true_for_a_fully_evidenced_record():
    ledger = _ledger()
    assert is_confirmed_unavailable(ledger.records[0], ledger) is True


def test_is_confirmed_unavailable_false_when_a_search_method_is_missing():
    # Text/rawdict alone (Phase 3T's own original D09/D10 evidence, before
    # this module existed) is exactly the gap that hid D59 for three
    # phases - never sufficient on its own.
    ledger = _ledger(records=[_record(search_methods=["text", "rawdict"])])
    assert is_confirmed_unavailable(ledger.records[0], ledger) is False


def test_is_confirmed_unavailable_false_for_d59_shaped_evidence():
    # search_methods claims images/drawings were checked, but the
    # evidence field itself is empty - "not checked" must never pass as
    # "checked, found nothing".
    ledger = _ledger(records=[_record(image_evidence="")])
    assert is_confirmed_unavailable(ledger.records[0], ledger) is False
    ledger2 = _ledger(records=[_record(drawing_evidence="   ")])
    assert is_confirmed_unavailable(ledger2.records[0], ledger2) is False


def test_is_confirmed_unavailable_false_when_not_reviewed():
    ledger = _ledger(records=[_record(review_status="pending")])
    assert is_confirmed_unavailable(ledger.records[0], ledger) is False


def test_is_confirmed_unavailable_false_for_non_confirmed_status():
    for status in (
        "available_and_extracted",
        "available_but_not_extracted",
        "source_ambiguous",
        "source_not_checked",
        "source_hash_mismatch",
    ):
        ledger = _ledger(records=[_record(availability_status=status)])
        assert is_confirmed_unavailable(ledger.records[0], ledger) is False


def test_is_confirmed_unavailable_false_when_package_missing():
    record = _record(source_package_id="no-such-package")
    ledger = SourceAvailabilityLedger(source_packages=[_package()], records=[record])
    assert is_confirmed_unavailable(record, ledger) is False


def test_is_confirmed_unavailable_false_when_no_pages_scanned():
    ledger = _ledger(records=[_record(pages_scanned=[])])
    assert is_confirmed_unavailable(ledger.records[0], ledger) is False


def test_verify_source_hashes_match_none_when_hashes_match(tmp_path: Path):
    doc_path = tmp_path / "2008" / "b3_padrao.pdf"
    doc_path.parent.mkdir(parents=True)
    doc_path.write_bytes(b"fake padrao content")
    import hashlib

    real_hash = hashlib.sha256(b"fake padrao content").hexdigest()
    package = _package(
        documents=[
            SourceDocument(
                path="2008/b3_padrao.pdf",
                sha256=real_hash,
                role="padrao",
                page_count=6,
                acquisition_provenance="test",
            )
        ]
    )
    record = _record(source_hashes={"padrao": real_hash})
    ledger = SourceAvailabilityLedger(source_packages=[package], records=[record])
    assert verify_source_hashes_match(record, ledger, tmp_path) is None


def test_verify_source_hashes_match_detects_mismatch(tmp_path: Path):
    # PROMPT Fase 3Z Section 18/19 - reversibility: a document since
    # replaced (different bytes, same name) must invalidate the waiver.
    doc_path = tmp_path / "2008" / "b3_padrao.pdf"
    doc_path.parent.mkdir(parents=True)
    doc_path.write_bytes(b"a NEW padrao that now includes D09/D10")
    ledger = _ledger()  # declares sha256 "a"*64, which no longer matches
    issue = verify_source_hashes_match(ledger.records[0], ledger, tmp_path)
    assert issue is not None
    assert issue.kind == "source_hash_mismatch"


def test_verify_source_hashes_match_detects_missing_file(tmp_path: Path):
    ledger = _ledger()
    issue = verify_source_hashes_match(ledger.records[0], ledger, tmp_path)
    assert issue is not None
    assert issue.kind == "source_document_missing"


def test_verify_source_hashes_match_detects_missing_package():
    record = _record(source_package_id="no-such-package")
    ledger = SourceAvailabilityLedger(source_packages=[_package()], records=[record])
    issue = verify_source_hashes_match(record, ledger, Path("."))
    assert issue is not None
    assert issue.kind == "source_package_missing"
