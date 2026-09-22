"""Unit tests for the semantic annotation contract (PROMPT Fase 5A
section 11-19, 23, 26). Every fixture is synthetic - never real corpus
data - per the same discipline ``tests/test_content_assignment.py``
already established.
"""

from __future__ import annotations

import hashlib

import pytest
from pydantic import ValidationError

from enade.semantic.annotation import ConceptAssociation, QuestionAnnotation, SemanticEvidenceRef

_HASH_A = hashlib.sha256(b"question markdown content").hexdigest()
_HASH_B = hashlib.sha256(b"different content").hexdigest()


def _text_evidence(text: str = "Considere a seguinte tabela verdade", source_sha256=_HASH_A):
    return SemanticEvidenceRef(
        source_kind="statement",
        source_locator="statement",
        source_sha256=source_sha256,
        text_excerpt=text,
        excerpt_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
    )


def _visual_evidence(source_sha256=_HASH_A):
    return SemanticEvidenceRef(
        source_kind="asset",
        source_locator="asset:table-01",
        source_sha256=source_sha256,
        asset_path="enade-2011-computing-q22/table-01.png",
        asset_sha256=_HASH_B,
    )


def _annotation(**overrides) -> QuestionAnnotation:
    base = dict(
        question_id="enade-2011-computing-q22",
        taxonomy_version="computing-v1@1.0.0-pilot",
        source_hash=_HASH_A,
        component="componente_especifico",
        primary_topics=["arvores-e-estruturas-hierarquicas"],
        secondary_topics=[],
        concepts=[],
        context_tags=[],
        cognitive_skills=["apply"],
        search_terms=["árvore binária"],
        evidence=[_text_evidence()],
        annotation_method="manual_expert_reading",
        annotation_status="proposed",
        confidence="high",
    )
    base.update(overrides)
    return QuestionAnnotation(**base)


# --- SemanticEvidenceRef ---------------------------------------------------


def test_text_evidence_is_valid():
    ref = _text_evidence()
    assert ref.text_excerpt is not None


def test_visual_evidence_is_valid():
    ref = _visual_evidence()
    assert ref.asset_path is not None


def test_evidence_with_neither_text_nor_asset_is_rejected():
    with pytest.raises(ValidationError, match="text_excerpt or an asset_path"):
        SemanticEvidenceRef(
            source_kind="statement",
            source_locator="statement",
            source_sha256=_HASH_A,
        )


def test_excerpt_sha256_must_match_the_real_excerpt():
    with pytest.raises(ValidationError, match="does not match"):
        SemanticEvidenceRef(
            source_kind="statement",
            source_locator="statement",
            source_sha256=_HASH_A,
            text_excerpt="real text",
            excerpt_sha256=hashlib.sha256(b"a different text").hexdigest(),
        )


def test_asset_path_without_asset_sha256_is_rejected():
    with pytest.raises(ValidationError, match="must both be set"):
        SemanticEvidenceRef(
            source_kind="asset",
            source_locator="asset:table-01",
            source_sha256=_HASH_A,
            asset_path="q/table-01.png",
        )


def test_excerpt_over_max_length_is_rejected():
    with pytest.raises(ValidationError):
        SemanticEvidenceRef(
            source_kind="statement",
            source_locator="statement",
            source_sha256=_HASH_A,
            text_excerpt="x" * 301,
            excerpt_sha256=hashlib.sha256(("x" * 301).encode()).hexdigest(),
        )


def test_bbox_is_optional():
    ref = _text_evidence()
    assert ref.bbox is None


# --- QuestionAnnotation: primary topic / unclassifiable --------------------


def test_annotation_with_a_primary_topic_is_valid():
    annotation = _annotation()
    assert annotation.primary_topics


def test_annotation_without_any_primary_topic_requires_unclassifiable():
    with pytest.raises(ValidationError, match="unclassifiable"):
        _annotation(primary_topics=[], annotation_status="proposed")


def test_unclassifiable_with_topics_populated_is_contradictory():
    with pytest.raises(ValidationError, match="must not carry"):
        _annotation(annotation_status="unclassifiable")


def test_unclassifiable_with_no_topics_is_valid():
    annotation = _annotation(primary_topics=[], annotation_status="unclassifiable")
    assert annotation.annotation_status == "unclassifiable"


def test_topic_cannot_be_both_primary_and_secondary():
    with pytest.raises(ValidationError, match="both primary and secondary"):
        _annotation(
            primary_topics=["arvores-e-estruturas-hierarquicas"],
            secondary_topics=["arvores-e-estruturas-hierarquicas"],
        )


# --- status / review ------------------------------------------------------


def test_invalid_annotation_status_is_rejected():
    with pytest.raises(ValidationError):
        _annotation(annotation_status="approved-by-ai")


def test_invalid_confidence_is_rejected():
    with pytest.raises(ValidationError):
        _annotation(confidence="very-high")


def test_review_status_reviewed_without_reviewer_note_is_rejected():
    with pytest.raises(ValidationError, match="reviewer:"):
        _annotation(review_status="reviewed")


def test_review_status_reviewed_with_reviewer_note_is_accepted():
    annotation = _annotation(review_status="reviewed", notes="reviewer: filipe.sousa")
    assert annotation.review_status == "reviewed"


def test_review_status_defaults_to_pending():
    annotation = _annotation()
    assert annotation.review_status == "pending"


# --- anti-leakage (section 16), also see test_semantic_annotatable_content --


def test_answer_standard_evidence_at_top_level_is_rejected():
    ref = SemanticEvidenceRef(
        source_kind="answer_standard",
        source_locator="answer_standard",
        source_sha256=_HASH_A,
        text_excerpt="gabarito text",
        excerpt_sha256=hashlib.sha256(b"gabarito text").hexdigest(),
    )
    with pytest.raises(ValidationError, match="answer_standard"):
        _annotation(evidence=[ref])


def test_answer_standard_evidence_inside_a_concept_is_also_rejected():
    ref = SemanticEvidenceRef(
        source_kind="answer_standard",
        source_locator="answer_standard",
        source_sha256=_HASH_A,
        text_excerpt="gabarito text",
        excerpt_sha256=hashlib.sha256(b"gabarito text").hexdigest(),
    )
    concept = ConceptAssociation(
        concept_id="some-concept", role="required", evidence_refs=[ref], confidence="high"
    )
    with pytest.raises(ValidationError, match="answer_standard"):
        _annotation(concepts=[concept])


# --- concepts ---------------------------------------------------------------


def test_concept_requires_at_least_one_evidence_ref():
    with pytest.raises(ValidationError):
        ConceptAssociation(concept_id="x", role="required", evidence_refs=[], confidence="high")


def test_concept_association_is_valid_with_evidence():
    concept = ConceptAssociation(
        concept_id="arvore-binaria",
        role="required",
        evidence_refs=[_text_evidence()],
        confidence="medium",
    )
    annotation = _annotation(concepts=[concept])
    assert annotation.concepts[0].concept_id == "arvore-binaria"


def test_invalid_question_id_shape_is_rejected():
    with pytest.raises(ValidationError, match="kebab-case"):
        _annotation(question_id="Enade_2011_Q22")
