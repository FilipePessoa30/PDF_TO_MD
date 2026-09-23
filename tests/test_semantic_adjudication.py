"""Tests for the human-adjudication template contract (PROMPT Fase 5B
section 21, 26, 27): pending template is valid, partial fills are
rejected, reject/defer never carries a human topic list, and the real
persisted 5B template is fully untouched.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from enade.semantic.adjudication import (
    HumanAdjudicationEntry,
    build_adjudication_template,
    is_template_untouched,
)
from enade.semantic.annotation import QuestionAnnotation, SemanticEvidenceRef

REPO_ROOT = Path(__file__).resolve().parent.parent
_HASH_A = "a" * 64


def _proposed_decision() -> dict:
    return {
        "taxonomy_version": "computing-v1@1.1.0-pilot",
        "annotation_status": "proposed",
        "primary_topics": ["topic-a"],
        "secondary_topics": [],
        "concepts": [],
        "confidence": "high",
    }


def test_pending_entry_with_all_human_fields_null_is_valid():
    entry = HumanAdjudicationEntry(question_id="q1", proposed_decision=_proposed_decision())
    assert entry.human_decision is None
    assert is_template_untouched(json.loads(entry.model_dump_json()))


def test_fully_filled_approve_entry_is_valid():
    entry = HumanAdjudicationEntry(
        question_id="q1",
        proposed_decision=_proposed_decision(),
        human_decision="approve",
        human_primary_topics=["topic-a"],
        human_notes="looks right",
        reviewer="Jane Doe",
        reviewed_at="2026-01-01",
    )
    assert entry.human_decision == "approve"


def test_partial_fill_decision_without_reviewer_is_rejected():
    with pytest.raises(ValidationError, match="must be filled in together"):
        HumanAdjudicationEntry(
            question_id="q1",
            proposed_decision=_proposed_decision(),
            human_decision="approve",
        )


def test_partial_fill_reviewer_without_decision_is_rejected():
    with pytest.raises(ValidationError, match="must be filled in together"):
        HumanAdjudicationEntry(
            question_id="q1",
            proposed_decision=_proposed_decision(),
            reviewer="Jane Doe",
        )


def test_partial_fill_missing_reviewed_at_is_rejected():
    with pytest.raises(ValidationError, match="must be filled in together"):
        HumanAdjudicationEntry(
            question_id="q1",
            proposed_decision=_proposed_decision(),
            human_decision="approve",
            reviewer="Jane Doe",
        )


def test_reject_decision_with_human_topics_is_rejected():
    with pytest.raises(ValidationError, match="must not carry"):
        HumanAdjudicationEntry(
            question_id="q1",
            proposed_decision=_proposed_decision(),
            human_decision="reject",
            human_primary_topics=["topic-a"],
            reviewer="Jane Doe",
            reviewed_at="2026-01-01",
        )


def test_defer_decision_with_human_concepts_is_rejected():
    with pytest.raises(ValidationError, match="must not carry"):
        HumanAdjudicationEntry(
            question_id="q1",
            proposed_decision=_proposed_decision(),
            human_decision="defer",
            human_concepts=["concept-a"],
            reviewer="Jane Doe",
            reviewed_at="2026-01-01",
        )


def test_correct_decision_may_carry_human_topics():
    entry = HumanAdjudicationEntry(
        question_id="q1",
        proposed_decision=_proposed_decision(),
        human_decision="correct",
        human_primary_topics=["topic-b"],
        reviewer="Jane Doe",
        reviewed_at="2026-01-01",
    )
    assert entry.human_primary_topics == ["topic-b"]


def test_invalid_human_decision_value_is_rejected():
    with pytest.raises(ValidationError):
        HumanAdjudicationEntry(
            question_id="q1",
            proposed_decision=_proposed_decision(),
            human_decision="looks_good_to_me",
            reviewer="Jane Doe",
            reviewed_at="2026-01-01",
        )


def _annotation(qid: str) -> QuestionAnnotation:
    excerpt = "trecho"
    return QuestionAnnotation(
        question_id=qid,
        taxonomy_version="computing-v1@1.1.0-pilot",
        source_hash=_HASH_A,
        component="componente_especifico",
        primary_topics=["topic-a"],
        concepts=[],
        annotation_method="manual",
        annotation_status="proposed",
        confidence="high",
        evidence=[
            SemanticEvidenceRef(
                source_kind="statement",
                source_locator="statement",
                source_sha256=_HASH_A,
                text_excerpt=excerpt,
                excerpt_sha256=__import__("hashlib").sha256(excerpt.encode()).hexdigest(),
            )
        ],
    )


def test_build_adjudication_template_produces_one_entry_per_annotation_sorted_by_id():
    annotations = [_annotation("q-2"), _annotation("q-1")]
    entries = build_adjudication_template(annotations)
    assert [e["question_id"] for e in entries] == ["q-1", "q-2"]
    assert all(is_template_untouched(e) for e in entries)


def test_build_adjudication_template_entries_all_validate():
    entries = build_adjudication_template([_annotation("q-1")])
    for entry in entries:
        HumanAdjudicationEntry(**entry)


# --- real, persisted artifact ------------------------------------------


def test_real_5b_adjudication_template_is_fully_untouched():
    path = REPO_ROOT / "data" / "semantic" / "human-adjudication-template-5b.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["entry_count"] == 30
    for entry in payload["entries"]:
        parsed = HumanAdjudicationEntry(**entry)
        assert is_template_untouched(json.loads(parsed.model_dump_json()))
