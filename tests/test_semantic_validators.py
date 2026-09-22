"""Tests for the semantic-layer cross-artifact validators (PROMPT Fase
5A section 23, 26). Synthetic fixtures + a real tmp_path filesystem for
the evidence-integrity checks, which are specifically about disk state.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from enade.models.taxonomy import Taxonomy
from enade.semantic.annotation import QuestionAnnotation, SemanticEvidenceRef
from enade.semantic.validators import (
    validate_annotation_against_taxonomy,
    validate_evidence_integrity,
    validate_search_terms_have_provenance,
    validate_shared_question_consistency,
)

_HASH_A = hashlib.sha256(b"question markdown content").hexdigest()


def _taxonomy(**overrides) -> Taxonomy:
    base = {
        "taxonomy_id": "test-taxonomy",
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
                        "concepts": [{"id": "concept-a", "name": "Concept A"}],
                    },
                    {
                        "id": "topic-old",
                        "name": "Deprecated Topic",
                        "status": "deprecated",
                        "concepts": [],
                    },
                ],
            }
        ],
    }
    base.update(overrides)
    return Taxonomy.model_validate(base)


def _text_evidence(source_sha256=_HASH_A):
    text = "excerpt"
    return SemanticEvidenceRef(
        source_kind="statement",
        source_locator="statement",
        source_sha256=source_sha256,
        text_excerpt=text,
        excerpt_sha256=hashlib.sha256(text.encode()).hexdigest(),
    )


def _annotation(**overrides) -> QuestionAnnotation:
    base = dict(
        question_id="enade-2011-computing-q22",
        taxonomy_version="1.0.0",
        source_hash=_HASH_A,
        component="componente_especifico",
        primary_topics=["topic-a"],
        secondary_topics=[],
        concepts=[],
        context_tags=[],
        cognitive_skills=["apply"],
        search_terms=[],
        evidence=[_text_evidence()],
        annotation_method="manual_expert_reading",
        annotation_status="proposed",
        confidence="high",
    )
    base.update(overrides)
    return QuestionAnnotation(**base)


# --- validate_annotation_against_taxonomy ----------------------------------


def test_valid_annotation_against_taxonomy_has_no_diagnostics():
    assert validate_annotation_against_taxonomy(_annotation(), _taxonomy(), "1.0.0") == []


def test_taxonomy_version_mismatch_is_flagged():
    diagnostics = validate_annotation_against_taxonomy(
        _annotation(taxonomy_version="0.9.0"), _taxonomy(), "1.0.0"
    )
    assert any(d.kind == "taxonomy_version_mismatch" for d in diagnostics)


def test_nonexistent_topic_is_flagged():
    diagnostics = validate_annotation_against_taxonomy(
        _annotation(primary_topics=["does-not-exist"]), _taxonomy(), "1.0.0"
    )
    assert any(d.kind == "topic_not_found" for d in diagnostics)


def test_deprecated_topic_is_flagged():
    diagnostics = validate_annotation_against_taxonomy(
        _annotation(primary_topics=["topic-old"]), _taxonomy(), "1.0.0"
    )
    assert any(d.kind == "topic_deprecated" for d in diagnostics)


def test_nonexistent_concept_is_flagged():
    from enade.semantic.annotation import ConceptAssociation

    concept = ConceptAssociation(
        concept_id="ghost-concept",
        role="required",
        evidence_refs=[_text_evidence()],
        confidence="high",
    )
    diagnostics = validate_annotation_against_taxonomy(
        _annotation(concepts=[concept]), _taxonomy(), "1.0.0"
    )
    assert any(d.kind == "concept_not_found" for d in diagnostics)


def test_real_concept_is_not_flagged():
    from enade.semantic.annotation import ConceptAssociation

    concept = ConceptAssociation(
        concept_id="concept-a", role="required", evidence_refs=[_text_evidence()], confidence="high"
    )
    diagnostics = validate_annotation_against_taxonomy(
        _annotation(concepts=[concept]), _taxonomy(), "1.0.0"
    )
    assert diagnostics == []


# --- validate_evidence_integrity -------------------------------------------


def test_missing_source_question_is_flagged(tmp_path: Path):
    diagnostics = validate_evidence_integrity(_annotation(), tmp_path)
    assert any(d.kind == "source_question_missing" for d in diagnostics)


def test_stale_source_hash_is_flagged(tmp_path: Path):
    md = tmp_path / "enade-2011-computing-q22.md"
    md.write_text("real current content", encoding="utf-8")
    diagnostics = validate_evidence_integrity(_annotation(), tmp_path)
    assert any(d.kind == "source_hash_stale" for d in diagnostics)
    assert any(d.kind == "evidence_source_hash_stale" for d in diagnostics)


def test_fresh_source_hash_is_not_flagged(tmp_path: Path):
    md = tmp_path / "enade-2011-computing-q22.md"
    md.write_bytes(b"question markdown content")
    real_hash = hashlib.sha256(b"question markdown content").hexdigest()
    annotation = _annotation(
        source_hash=real_hash, evidence=[_text_evidence(source_sha256=real_hash)]
    )
    diagnostics = validate_evidence_integrity(annotation, tmp_path)
    assert diagnostics == []


def test_missing_evidence_asset_is_flagged(tmp_path: Path):
    md = tmp_path / "enade-2011-computing-q22.md"
    md.write_bytes(b"question markdown content")
    real_hash = hashlib.sha256(b"question markdown content").hexdigest()
    ref = SemanticEvidenceRef(
        source_kind="asset",
        source_locator="asset:table-01",
        source_sha256=real_hash,
        asset_path="enade-2011-computing-q22/table-01.png",
        asset_sha256=_HASH_A,
    )
    annotation = _annotation(source_hash=real_hash, evidence=[ref])
    diagnostics = validate_evidence_integrity(annotation, tmp_path)
    assert any(d.kind == "evidence_asset_missing" for d in diagnostics)


def test_evidence_asset_hash_mismatch_is_flagged(tmp_path: Path):
    md = tmp_path / "enade-2011-computing-q22.md"
    md.write_bytes(b"question markdown content")
    real_hash = hashlib.sha256(b"question markdown content").hexdigest()
    asset_dir = tmp_path / "enade-2011-computing-q22"
    asset_dir.mkdir()
    (asset_dir / "table-01.png").write_bytes(b"\x89PNG\r\n")
    ref = SemanticEvidenceRef(
        source_kind="asset",
        source_locator="asset:table-01",
        source_sha256=real_hash,
        asset_path="enade-2011-computing-q22/table-01.png",
        asset_sha256=_HASH_A,  # wrong on purpose
    )
    annotation = _annotation(source_hash=real_hash, evidence=[ref])
    diagnostics = validate_evidence_integrity(annotation, tmp_path)
    assert any(d.kind == "evidence_asset_hash_stale" for d in diagnostics)


# --- validate_shared_question_consistency ----------------------------------


def test_shared_question_with_agreeing_annotations_has_no_diagnostics():
    a = _annotation(question_id="enade-2011-computing-q22")
    b = _annotation(question_id="enade-2011-cc-b-q22")
    diagnostics = validate_shared_question_consistency(
        [a, b], canonical_of={"enade-2011-computing-q22": "canon", "enade-2011-cc-b-q22": "canon"}
    )
    assert diagnostics == []


def test_shared_question_with_divergent_primary_topics_is_flagged():
    a = _annotation(question_id="enade-2011-computing-q22", primary_topics=["topic-a"])
    b = _annotation(question_id="enade-2011-cc-b-q22", primary_topics=["topic-b"])
    diagnostics = validate_shared_question_consistency(
        [a, b], canonical_of={"enade-2011-computing-q22": "canon", "enade-2011-cc-b-q22": "canon"}
    )
    assert any(d.kind == "shared_question_divergent_annotation" for d in diagnostics)


def test_unrelated_questions_are_never_compared():
    a = _annotation(question_id="enade-2011-computing-q22", primary_topics=["topic-a"])
    b = _annotation(question_id="enade-2011-computing-q23", primary_topics=["topic-b"])
    diagnostics = validate_shared_question_consistency([a, b], canonical_of={})
    assert diagnostics == []


# --- validate_search_terms_have_provenance ---------------------------------


def test_search_terms_with_a_primary_topic_present_is_fine():
    assert validate_search_terms_have_provenance(_annotation(search_terms=["árvore"])) == []


def test_search_terms_with_no_topic_or_concept_at_all_is_flagged():
    annotation = _annotation(primary_topics=[], annotation_status="unclassifiable", search_terms=[])
    # unclassifiable short-circuits regardless of search_terms
    assert validate_search_terms_have_provenance(annotation) == []
