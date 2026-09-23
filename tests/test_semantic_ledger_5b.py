"""Tests for the 12-case unresolved-cases ledger (PROMPT Fase 5B section
6, 26, 27): every case has a record, a valid cause, a resolution with
evidence, and causes are not applied uniformly without individual
inspection.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LEDGER_PATH = REPO_ROOT / "data" / "semantic" / "unresolved-cases-ledger-5b.json"

_TEN_UNCLASSIFIABLE = {
    "enade-2008-computing-d09",
    "enade-2008-computing-q04",
    "enade-2011-computing-q01",
    "enade-2011-computing-q31",
    "enade-2011-computing-q33",
    "enade-2021-cc-b-d01",
    "enade-2021-si-d01",
    "enade-2021-cc-b-q01",
    "enade-2021-si-d02",
    "enade-2021-si-q05",
}
_TWO_NEEDS_REVIEW = {"enade-2011-computing-q14", "enade-2011-computing-q23"}


def _ledger() -> dict:
    return json.loads(LEDGER_PATH.read_text(encoding="utf-8"))


def test_ledger_has_exactly_the_12_real_cases():
    ledger = _ledger()
    ids = {r["question_id"] for r in ledger["records"]}
    assert ids == _TEN_UNCLASSIFIABLE | _TWO_NEEDS_REVIEW
    assert ledger["record_count"] == 12


def test_every_record_reports_the_real_5a_status():
    ledger = _ledger()
    by_id = {r["question_id"]: r for r in ledger["records"]}
    for qid in _TEN_UNCLASSIFIABLE:
        assert by_id[qid]["phase5a_status"] == "unclassifiable"
    for qid in _TWO_NEEDS_REVIEW:
        assert by_id[qid]["phase5a_status"] == "needs_review"


def test_every_record_has_a_cause_from_the_allowed_list():
    ledger = _ledger()
    allowed = set(ledger["allowed_causes"])
    for record in ledger["records"]:
        assert record["candidate_cause"] in allowed


def test_causes_are_not_all_identical_without_individual_inspection():
    """PROMPT section 6: 'Nao classifique todos os dez casos com a mesma
    causa sem inspecao individual.' At least two distinct causes must
    appear across the 12 real cases.
    """
    ledger = _ledger()
    causes = Counter(r["candidate_cause"] for r in ledger["records"])
    assert len(causes) >= 2


def test_the_two_licenciatura_pedagogy_cases_use_cross_domain_not_general_education():
    """q31/q33 are componente_especifico of Licenciatura, not
    formacao_geral - a real, individually-verified distinction (PROMPT
    section 6/8), not the same bucket as the 8 true formacao-geral cases.
    """
    ledger = _ledger()
    by_id = {r["question_id"]: r for r in ledger["records"]}
    for qid in ("enade-2011-computing-q31", "enade-2011-computing-q33"):
        assert by_id[qid]["candidate_cause"] == "cross_domain_question"
        assert by_id[qid]["component"] == "componente_especifico"


def test_needs_review_cases_have_distinct_causes_reflecting_real_difference():
    """q14 was a genuine annotation error (topic was wrong); q23 was
    merely under-evidenced (topic was already right) - these are
    different situations and must not share a cause.
    """
    ledger = _ledger()
    by_id = {r["question_id"]: r for r in ledger["records"]}
    assert by_id["enade-2011-computing-q14"]["candidate_cause"] == "annotation_error"
    assert by_id["enade-2011-computing-q23"]["candidate_cause"] == "insufficient_evidence"
    assert (
        by_id["enade-2011-computing-q14"]["candidate_cause"]
        != by_id["enade-2011-computing-q23"]["candidate_cause"]
    )


def test_every_record_has_a_non_empty_resolution_and_evidence_reviewed():
    ledger = _ledger()
    for record in ledger["records"]:
        assert record["resolution"].strip()
        assert record["evidence_reviewed"].strip()
        assert record["recommended_human_action"].strip()
        assert "remaining_ambiguity" in record


def test_every_record_has_the_real_source_hash():
    ledger = _ledger()
    for record in ledger["records"]:
        assert len(record["source_hash"]) == 64


def test_no_case_missing_a_diagnostic_field():
    required_fields = {
        "question_id",
        "phase5a_status",
        "component",
        "source_hash",
        "candidate_cause",
        "evidence_reviewed",
        "taxonomy_candidates",
        "decision",
        "resolution",
        "remaining_ambiguity",
        "recommended_human_action",
    }
    ledger = _ledger()
    for record in ledger["records"]:
        missing = required_fields - set(record)
        assert not missing, f"{record['question_id']} missing field(s): {missing}"
