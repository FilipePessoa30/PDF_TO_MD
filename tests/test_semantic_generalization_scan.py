"""Tests for the diagnostic-only generalization/compatibility scan
(PROMPT Fase 5A section 28, 26): synthetic fixtures for controlled
matching, plus a real-corpus sanity run confirming it never mutates
anything and never claims to be an annotation.
"""

from __future__ import annotations

from pathlib import Path

from enade.markdown_format import load_questions_directory
from enade.models.taxonomy import Taxonomy
from enade.semantic.artifacts import load_taxonomy
from enade.semantic.corpus_survey import PROTECTED_TARGETS, QuestionSurveyEntry, survey_all_targets
from enade.semantic.generalization_scan import candidate_topics_for_text, scan_corpus

REPO_ROOT = Path(__file__).resolve().parent.parent


def _taxonomy() -> Taxonomy:
    return Taxonomy.model_validate(
        {
            "taxonomy_id": "scan-test",
            "version": "1.0.0",
            "status": "provisional",
            "notice": "test",
            "subjects": [
                {
                    "id": "subject-redes",
                    "name": "Redes",
                    "topics": [
                        {
                            "id": "topic-cloud",
                            "name": "Computação em Nuvem",
                            "concepts": [
                                {
                                    "id": "concept-saas",
                                    "name": "SaaS",
                                    "keywords": ["software como servico"],
                                }
                            ],
                        }
                    ],
                }
            ],
        }
    )


def test_candidate_topics_matches_normalized_substring():
    taxonomy = _taxonomy()
    text = "O modelo de Software Como Serviço permite acesso via navegador."
    assert candidate_topics_for_text(text, taxonomy) == ["topic-cloud"]


def test_candidate_topics_ignores_accent_and_case_differences():
    taxonomy = _taxonomy()
    text = "SOFTWARE COMO SERVIÇO é um modelo de nuvem."
    assert "topic-cloud" in candidate_topics_for_text(text, taxonomy)


def test_candidate_topics_empty_when_no_match():
    taxonomy = _taxonomy()
    text = "Este enunciado fala sobre poesia e direitos humanos."
    assert candidate_topics_for_text(text, taxonomy) == []


def test_scan_corpus_never_flags_formacao_geral_as_a_coverage_gap():
    taxonomy = _taxonomy()
    survey_entry = QuestionSurveyEntry(
        question_id="q-fg",
        target="2011",
        exam_year=2011,
        applicable_courses=("all-computing",),
        is_shared_across_courses=False,
        section="formacao-geral-objetiva",
        component="formacao_geral",
        question_type="multiple_choice",
        has_table=False,
        has_equation_asset=False,
        has_diagram_or_image_asset=False,
        has_alternative_asset=False,
        asset_count=0,
        has_answer_standard=True,
        likely_source_limitation=False,
        statement_word_count=10,
    )

    class _FakeAlt:
        text = ""

    class _FakeQuestion:
        statement = "Um poema sobre a vida."
        alternatives: list = []

    result = scan_corpus({"q-fg": _FakeQuestion()}, {"q-fg": survey_entry}, taxonomy)
    assert result.questions_with_no_candidate == []


def test_scan_corpus_real_run_is_read_only_and_diagnostic_only():
    before = {
        p: p.read_bytes()
        for target, rel in PROTECTED_TARGETS.items()
        for p in sorted((REPO_ROOT / rel).rglob("*.md"))
    }

    taxonomy = load_taxonomy(REPO_ROOT / "data" / "taxonomy" / "computing-v1.yaml")
    questions_by_id = {}
    for _target, rel in PROTECTED_TARGETS.items():
        for qid, q in load_questions_directory(REPO_ROOT / rel).items():
            questions_by_id[qid] = q
    survey = survey_all_targets(REPO_ROOT)
    survey_by_id = {e.question_id: e for entries in survey.values() for e in entries}

    result = scan_corpus(questions_by_id, survey_by_id, taxonomy)

    assert result.total_questions == 255
    # Diagnostic result exposes no annotation-shaped field at all.
    assert not hasattr(result, "primary_topics")
    assert not hasattr(result, "annotations")

    after = {
        p: p.read_bytes()
        for target, rel in PROTECTED_TARGETS.items()
        for p in sorted((REPO_ROOT / rel).rglob("*.md"))
    }
    assert before == after
