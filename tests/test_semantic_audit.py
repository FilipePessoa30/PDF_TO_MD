"""Tests for the pilot audit metrics (PROMPT Fase 5A section 27):
synthetic fixtures for controlled counting, plus a sanity check against
the real, published pilot artifacts.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from enade.models.taxonomy import Taxonomy
from enade.semantic.annotation import ConceptAssociation, QuestionAnnotation, SemanticEvidenceRef
from enade.semantic.artifacts import load_annotations, load_taxonomy
from enade.semantic.audit import build_pilot_audit
from enade.semantic.corpus_survey import QuestionSurveyEntry, survey_all_targets

REPO_ROOT = Path(__file__).resolve().parent.parent
_HASH = hashlib.sha256(b"x").hexdigest()


def _taxonomy() -> Taxonomy:
    return Taxonomy.model_validate(
        {
            "taxonomy_id": "audit-test",
            "version": "1.0.0",
            "status": "provisional",
            "notice": "test",
            "subjects": [
                {
                    "id": "subject-a",
                    "name": "Subject A",
                    "topics": [
                        {
                            "id": "topic-a",
                            "name": "Topic A",
                            "concepts": [
                                {"id": "concept-a", "name": "Concept A", "keywords": ["kw-a"]}
                            ],
                        },
                        {"id": "topic-b", "name": "Topic B", "concepts": []},
                    ],
                }
            ],
        }
    )


def _text_evidence() -> SemanticEvidenceRef:
    excerpt = "excerpt"
    return SemanticEvidenceRef(
        source_kind="statement",
        source_locator="statement",
        source_sha256=_HASH,
        text_excerpt=excerpt,
        excerpt_sha256=hashlib.sha256(excerpt.encode()).hexdigest(),
    )


def _survey_entry(question_id: str) -> QuestionSurveyEntry:
    return QuestionSurveyEntry(
        question_id=question_id,
        target="2011",
        exam_year=2011,
        applicable_courses=("all-computing",),
        is_shared_across_courses=False,
        section="componente-especifico-objetiva",
        component="componente_especifico",
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


def test_build_pilot_audit_counts_basic_metrics():
    concept = ConceptAssociation(
        concept_id="concept-a", role="required", evidence_refs=[_text_evidence()], confidence="high"
    )
    annotation_1 = QuestionAnnotation(
        question_id="q-1",
        taxonomy_version="1.0.0",
        source_hash=_HASH,
        component="componente_especifico",
        primary_topics=["topic-a"],
        concepts=[concept],
        cognitive_skills=["apply"],
        evidence=[_text_evidence()],
        annotation_method="manual",
        annotation_status="proposed",
        confidence="high",
    )
    annotation_2 = QuestionAnnotation(
        question_id="q-2",
        taxonomy_version="1.0.0",
        source_hash=_HASH,
        component="componente_especifico",
        primary_topics=[],
        secondary_topics=[],
        concepts=[],
        cognitive_skills=[],
        evidence=[],
        annotation_method="manual",
        annotation_status="unclassifiable",
        confidence="high",
    )
    survey_by_id = {"q-1": _survey_entry("q-1"), "q-2": _survey_entry("q-2")}

    audit = build_pilot_audit([annotation_1, annotation_2], _taxonomy(), survey_by_id)

    assert audit.annotation_count == 2
    assert audit.status_counts == {"proposed": 1, "unclassifiable": 1}
    assert audit.concepts_per_question == {"q-1": 1, "q-2": 0}
    assert audit.primary_topics_per_question == {"q-1": 1, "q-2": 0}
    assert audit.questions_per_topic == {"topic-a": 1}
    assert audit.questions_per_subject == {"subject-a": 1}
    assert audit.textual_evidence_count == 2  # top-level + concept evidence
    assert audit.visual_evidence_count == 0
    assert "concept-a" in audit.used_alias_bearing_node_ids
    assert "topic-b" in audit.never_used_node_ids


def test_build_pilot_audit_runs_clean_on_the_real_pilot_artifacts():
    taxonomy = load_taxonomy(REPO_ROOT / "data" / "taxonomy" / "computing-v1.yaml")
    annotations, _groups = load_annotations(
        REPO_ROOT / "data" / "semantic" / "question-annotations-5a.json"
    )
    survey = survey_all_targets(REPO_ROOT)
    survey_by_id = {e.question_id: e for entries in survey.values() for e in entries}

    audit = build_pilot_audit(annotations, taxonomy, survey_by_id)

    assert audit.annotation_count == 30
    assert sum(audit.status_counts.values()) == 30
    assert audit.status_counts.get("reviewed", 0) == 0
