"""Tests for the Fase 5B reconciliation review packet builder (PROMPT
Fase 5B section 22): shows both the 5A historical and 5B proposed
classification, the change reason, and never the gabarito - determinism
and anti-leakage checked against the real, published 5B artifacts.
"""

from __future__ import annotations

import json
from pathlib import Path

from enade.semantic.annotation import QuestionAnnotation
from enade.semantic.artifacts import load_taxonomy
from enade.semantic.review import build_reconciliation_review_markdown

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_real_inputs():
    computing_v11 = load_taxonomy(REPO_ROOT / "data" / "taxonomy" / "computing-v1.1.yaml")
    general_ed = load_taxonomy(REPO_ROOT / "data" / "taxonomy" / "general-education-v1.yaml")

    payload_5a = json.loads(
        (REPO_ROOT / "data" / "semantic" / "question-annotations-5a.json").read_text(
            encoding="utf-8"
        )
    )
    annotations_5a_by_id = {a["question_id"]: a for a in payload_5a["annotations"]}

    payload_5b = json.loads(
        (REPO_ROOT / "data" / "semantic" / "question-annotations-5b.json").read_text(
            encoding="utf-8"
        )
    )
    annotations_5b = [QuestionAnnotation(**a) for a in payload_5b["annotations"]]

    migration_payload = json.loads(
        (REPO_ROOT / "data" / "semantic" / "migration-5a-to-5b.json").read_text(encoding="utf-8")
    )
    migration_by_id = {m["question_id"]: m for m in migration_payload["entries"]}

    return annotations_5b, annotations_5a_by_id, migration_by_id, [computing_v11, general_ed]


def test_reconciliation_review_is_deterministic():
    args = _load_real_inputs()
    a = build_reconciliation_review_markdown(*args)
    b = build_reconciliation_review_markdown(*args)
    assert a == b


def test_reconciliation_review_shows_both_5a_and_5b_classification_for_q14():
    annotations_5b, annotations_5a_by_id, migration_by_id, taxonomies = _load_real_inputs()
    markdown = build_reconciliation_review_markdown(
        annotations_5b, annotations_5a_by_id, migration_by_id, taxonomies
    )
    section = markdown.split("## enade-2011-computing-q14")[1].split("## enade-2011-computing-q23")[
        0
    ]
    assert "`needs_review`" in section  # 5A historical status
    assert "conjuntos-relacoes-e-funcoes" in section  # 5A historical topic
    assert "logica-proposicional" in section  # 5B proposed topic
    assert "inspecao visual" in section or "inspeção visual" in section.lower()


def test_reconciliation_review_never_mentions_the_gabarito():
    annotations_5b, annotations_5a_by_id, migration_by_id, taxonomies = _load_real_inputs()
    markdown = build_reconciliation_review_markdown(
        annotations_5b, annotations_5a_by_id, migration_by_id, taxonomies
    )
    disclaimer = "O gabarito e o padrão de resposta nunca aparecem aqui"
    assert disclaimer in markdown
    body = markdown.replace(disclaimer, "")
    for banned in ("gabarito", "correct_answer", "answer_standard", "padrão de resposta"):
        assert banned.lower() not in body.lower()


def test_reconciliation_review_explicitly_separates_technical_proposal_from_human_decision():
    annotations_5b, annotations_5a_by_id, migration_by_id, taxonomies = _load_real_inputs()
    markdown = build_reconciliation_review_markdown(
        annotations_5b, annotations_5a_by_id, migration_by_id, taxonomies
    )
    assert "proposta técnica" in markdown.lower()
    assert "decisão humana pendente" in markdown.lower()
    assert (
        "approve" in markdown
        and "correct" in markdown
        and "reject" in markdown
        and "defer" in markdown
    )


def test_reconciliation_review_covers_all_30_questions():
    annotations_5b, annotations_5a_by_id, migration_by_id, taxonomies = _load_real_inputs()
    markdown = build_reconciliation_review_markdown(
        annotations_5b, annotations_5a_by_id, migration_by_id, taxonomies
    )
    for annotation in annotations_5b:
        assert f"## {annotation.question_id}" in markdown
