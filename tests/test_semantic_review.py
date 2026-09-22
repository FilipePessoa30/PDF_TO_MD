"""Tests for the human-review packet builder (PROMPT Fase 5A section 22,
26): rendering correctness on synthetic fixtures, plus determinism and
anti-leakage checks against the real, published pilot artifacts.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from enade.models.taxonomy import Taxonomy
from enade.semantic.annotation import QuestionAnnotation, SemanticEvidenceRef
from enade.semantic.artifacts import load_annotations, load_taxonomy
from enade.semantic.review import build_review_markdown

REPO_ROOT = Path(__file__).resolve().parent.parent
_HASH = hashlib.sha256(b"x").hexdigest()


def _taxonomy() -> Taxonomy:
    return Taxonomy.model_validate(
        {
            "taxonomy_id": "review-test",
            "version": "1.0.0",
            "status": "provisional",
            "notice": "test",
            "subjects": [
                {
                    "id": "subject-a",
                    "name": "Assunto A",
                    "topics": [{"id": "topic-a", "name": "Tópico A", "concepts": []}],
                }
            ],
        }
    )


def _text_evidence() -> SemanticEvidenceRef:
    excerpt = "trecho de evidência"
    return SemanticEvidenceRef(
        source_kind="statement",
        source_locator="statement",
        source_sha256=_HASH,
        text_excerpt=excerpt,
        excerpt_sha256=hashlib.sha256(excerpt.encode()).hexdigest(),
    )


def test_classified_question_renders_topic_and_evidence():
    annotation = QuestionAnnotation(
        question_id="enade-2011-computing-q01",
        taxonomy_version="1.0.0",
        source_hash=_HASH,
        component="componente_especifico",
        primary_topics=["topic-a"],
        cognitive_skills=["apply"],
        evidence=[_text_evidence()],
        annotation_method="manual",
        annotation_status="proposed",
        confidence="high",
    )
    markdown = build_review_markdown([annotation], _taxonomy(), "1.0.0")
    assert "enade-2011-computing-q01" in markdown
    assert "topic-a (Tópico A)" in markdown
    assert "trecho de evidência" in markdown
    assert "aprovar" in markdown


def test_unclassifiable_question_renders_without_topics():
    annotation = QuestionAnnotation(
        question_id="enade-2011-computing-q02",
        taxonomy_version="1.0.0",
        source_hash=_HASH,
        component="formacao_geral",
        primary_topics=[],
        evidence=[_text_evidence()],
        annotation_method="manual",
        annotation_status="unclassifiable",
        confidence="high",
    )
    markdown = build_review_markdown([annotation], _taxonomy(), "1.0.0")
    assert "nenhum - unclassifiable" in markdown


def test_review_ordering_is_deterministic_by_question_id():
    common = dict(
        taxonomy_version="1.0.0",
        source_hash=_HASH,
        component="componente_especifico",
        primary_topics=["topic-a"],
        annotation_method="manual",
        annotation_status="proposed",
        confidence="high",
        evidence=[_text_evidence()],
    )
    a = QuestionAnnotation(question_id="enade-2011-computing-q09", **common)
    b = QuestionAnnotation(question_id="enade-2011-computing-q01", **common)
    markdown = build_review_markdown([a, b], _taxonomy(), "1.0.0")
    assert markdown.index("enade-2011-computing-q01") < markdown.index("enade-2011-computing-q09")


def test_review_never_mentions_reviewed_status_for_pilot_annotations():
    annotation = QuestionAnnotation(
        question_id="enade-2011-computing-q01",
        taxonomy_version="1.0.0",
        source_hash=_HASH,
        component="componente_especifico",
        primary_topics=["topic-a"],
        evidence=[_text_evidence()],
        annotation_method="manual",
        annotation_status="proposed",
        confidence="high",
    )
    markdown = build_review_markdown([annotation], _taxonomy(), "1.0.0")
    assert "Status de revisão:** reviewed" not in markdown


def test_build_review_markdown_is_deterministic_on_real_pilot_artifacts():
    taxonomy = load_taxonomy(REPO_ROOT / "data" / "taxonomy" / "computing-v1.yaml")
    annotations, _groups = load_annotations(
        REPO_ROOT / "data" / "semantic" / "question-annotations-5a.json"
    )
    a = build_review_markdown(annotations, taxonomy, "computing-v1@1.0.0-pilot")
    b = build_review_markdown(annotations, taxonomy, "computing-v1@1.0.0-pilot")
    assert a == b
    assert "gabarito" not in a.replace(
        "O gabarito e o padrão de resposta nunca aparecem neste pacote "
        "nem no modelo de anotação subjacente",
        "",
    )
