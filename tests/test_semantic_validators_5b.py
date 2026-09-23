"""Tests for the Fase 5B additions to the semantic validators (PROMPT
Fase 5B section 14/15/25): generic-keyword taxonomy audit, migration
reason enforcement, id-meaning-preserved across taxonomy versions,
context-vs-primary-topic overlap, and the alternative-only distractor
guard.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from enade.models.taxonomy import Taxonomy
from enade.semantic.annotation import ConceptAssociation, QuestionAnnotation, SemanticEvidenceRef
from enade.semantic.validators import (
    validate_context_not_used_as_primary_topic,
    validate_migration_entries_have_reason,
    validate_no_taxonomy_id_meaning_changed,
    validate_primary_evidence_not_alternative_only,
    validate_taxonomy_keywords_are_not_bare_generic_terms,
)

_HASH = hashlib.sha256(b"x").hexdigest()


def _taxonomy(**concept_overrides) -> Taxonomy:
    concept = {"id": "concept-a", "name": "Concept A", "keywords": ["ambiente"]}
    concept.update(concept_overrides)
    return Taxonomy.model_validate(
        {
            "taxonomy_id": "test-taxonomy",
            "version": "1.0.0",
            "status": "provisional",
            "notice": "test",
            "subjects": [
                {
                    "id": "subject-a",
                    "name": "Subject A",
                    "topics": [{"id": "topic-a", "name": "Topic A", "concepts": [concept]}],
                }
            ],
        }
    )


# --- generic keyword denylist -------------------------------------------


def test_bare_generic_dictionary_word_is_flagged():
    diags = validate_taxonomy_keywords_are_not_bare_generic_terms(_taxonomy(keywords=["ambiente"]))
    assert any(d.kind == "generic_keyword_without_context" for d in diags)


def test_multi_word_phrase_built_from_a_generic_word_is_not_flagged():
    diags = validate_taxonomy_keywords_are_not_bare_generic_terms(
        _taxonomy(keywords=["entrada e saida do sistema"])
    )
    assert diags == []


@pytest.mark.parametrize("acronym", ["SQL", "DER", "TDA", "SaaS", "CDMA", "CID", "IoT"])
def test_short_technical_acronym_is_never_flagged_just_for_being_short(acronym):
    diags = validate_taxonomy_keywords_are_not_bare_generic_terms(_taxonomy(keywords=[acronym]))
    assert diags == []


def test_generic_word_via_alias_is_also_flagged():
    taxonomy = Taxonomy.model_validate(
        {
            "taxonomy_id": "test-taxonomy",
            "version": "1.0.0",
            "status": "provisional",
            "notice": "test",
            "subjects": [
                {"id": "subject-a", "name": "Subject A", "aliases": ["sistema"], "topics": []}
            ],
        }
    )
    diags = validate_taxonomy_keywords_are_not_bare_generic_terms(taxonomy)
    assert any(d.kind == "generic_keyword_without_context" for d in diags)


# --- migration reason ----------------------------------------------------


def test_migration_entry_with_reason_is_not_flagged():
    entries = [{"question_id": "q1", "change_reason": "unchanged - audited, no defect found."}]
    assert validate_migration_entries_have_reason(entries) == []


def test_migration_entry_with_empty_reason_is_flagged():
    entries = [{"question_id": "q1", "change_reason": ""}]
    diags = validate_migration_entries_have_reason(entries)
    assert any(d.kind == "migration_without_reason" for d in diags)


def test_migration_entry_with_missing_reason_key_is_flagged():
    entries = [{"question_id": "q1"}]
    diags = validate_migration_entries_have_reason(entries)
    assert any(d.kind == "migration_without_reason" for d in diags)


# --- id meaning preserved --------------------------------------------------


def test_unchanged_node_across_versions_is_not_flagged():
    old = _taxonomy()
    new = _taxonomy()
    assert validate_no_taxonomy_id_meaning_changed(old, new) == []


def test_renamed_node_under_the_same_id_is_flagged():
    old = _taxonomy()
    new = Taxonomy.model_validate(
        {
            "taxonomy_id": "test-taxonomy",
            "version": "1.1.0",
            "status": "provisional",
            "notice": "test",
            "subjects": [
                {
                    "id": "subject-a",
                    "name": "Subject A",
                    "topics": [
                        {
                            "id": "topic-a",
                            "name": "Totally Different Meaning",
                            "concepts": [{"id": "concept-a", "name": "Concept A", "keywords": []}],
                        }
                    ],
                }
            ],
        }
    )
    diags = validate_no_taxonomy_id_meaning_changed(old, new)
    assert any(d.kind == "taxonomy_id_reused_with_different_meaning" for d in diags)


def test_node_added_in_new_version_is_never_flagged():
    old = _taxonomy()
    new = Taxonomy.model_validate(
        {
            "taxonomy_id": "test-taxonomy",
            "version": "1.1.0",
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
                                {"id": "concept-a", "name": "Concept A", "keywords": ["ambiente"]},
                                {"id": "concept-b", "name": "Concept B", "keywords": []},
                            ],
                        }
                    ],
                }
            ],
        }
    )
    assert validate_no_taxonomy_id_meaning_changed(old, new) == []


def test_node_removed_in_new_version_is_never_flagged_by_this_check():
    old = _taxonomy()
    new = Taxonomy.model_validate(
        {
            "taxonomy_id": "test-taxonomy",
            "version": "1.1.0",
            "status": "provisional",
            "notice": "test",
            "subjects": [{"id": "subject-a", "name": "Subject A", "topics": []}],
        }
    )
    assert validate_no_taxonomy_id_meaning_changed(old, new) == []


# --- context vs primary topic --------------------------------------------


def _annotation(**overrides) -> QuestionAnnotation:
    excerpt = "excerpt"
    base = dict(
        question_id="q1",
        taxonomy_version="test@1.0.0",
        source_hash=_HASH,
        component="componente_especifico",
        primary_topics=["topic-a"],
        secondary_topics=[],
        concepts=[],
        context_tags=[],
        annotation_method="manual",
        annotation_status="proposed",
        confidence="high",
        evidence=[
            SemanticEvidenceRef(
                source_kind="statement",
                source_locator="statement",
                source_sha256=_HASH,
                text_excerpt=excerpt,
                excerpt_sha256=hashlib.sha256(excerpt.encode()).hexdigest(),
            )
        ],
    )
    base.update(overrides)
    return QuestionAnnotation(**base)


def test_context_tag_disjoint_from_topics_is_not_flagged():
    annotation = _annotation(primary_topics=["topic-a"], context_tags=["topic-b"])
    assert validate_context_not_used_as_primary_topic(annotation) == []


def test_context_tag_matching_primary_topic_is_flagged():
    annotation = _annotation(primary_topics=["topic-a"], context_tags=["topic-a"])
    diags = validate_context_not_used_as_primary_topic(annotation)
    assert any(d.kind == "context_used_as_primary_topic" for d in diags)


def test_context_tag_matching_secondary_topic_is_flagged():
    annotation = _annotation(
        primary_topics=["topic-a"], secondary_topics=["topic-b"], context_tags=["topic-b"]
    )
    diags = validate_context_not_used_as_primary_topic(annotation)
    assert any(d.kind == "context_used_as_primary_topic" for d in diags)


# --- primary evidence must not come only from alternatives ---------------


def test_evidence_from_the_statement_is_never_flagged(tmp_path: Path):
    qdir = tmp_path
    (qdir / "q1.md").write_text(
        "# Q1\n\nO enunciado fala sobre redes de computadores.\n\n## Alternativas\n\nA. x\n",
        encoding="utf-8",
    )
    annotation = _annotation(
        evidence=[
            SemanticEvidenceRef(
                source_kind="statement",
                source_locator="statement",
                source_sha256=_HASH,
                text_excerpt="redes de computadores",
                excerpt_sha256=hashlib.sha256(b"redes de computadores").hexdigest(),
            )
        ]
    )
    diags = validate_primary_evidence_not_alternative_only(annotation, qdir)
    assert diags == []


def test_evidence_found_only_inside_alternatives_is_flagged(tmp_path: Path):
    qdir = tmp_path
    (qdir / "q1.md").write_text(
        "# Q1\n\nEnunciado genérico sem pistas.\n\n## Alternativas\n\nA. CDMA e FDMA\n",
        encoding="utf-8",
    )
    excerpt = "CDMA e FDMA"
    annotation = _annotation(
        evidence=[
            SemanticEvidenceRef(
                source_kind="statement",
                source_locator="statement",
                source_sha256=_HASH,
                text_excerpt=excerpt,
                excerpt_sha256=hashlib.sha256(excerpt.encode()).hexdigest(),
            )
        ]
    )
    diags = validate_primary_evidence_not_alternative_only(annotation, qdir)
    assert any(d.kind == "primary_topic_grounded_only_in_alternatives" for d in diags)


def test_visual_only_evidence_is_exempt(tmp_path: Path):
    qdir = tmp_path
    (qdir / "q1.md").write_text("# Q1\n\nEnunciado.\n\n## Alternativas\n\nA. x\n", encoding="utf-8")
    annotation = _annotation(
        evidence=[
            SemanticEvidenceRef(
                source_kind="asset",
                source_locator="asset:figure-01",
                source_sha256=_HASH,
                asset_path="q1/figure-01.png",
                asset_sha256=_HASH,
            )
        ]
    )
    diags = validate_primary_evidence_not_alternative_only(annotation, qdir)
    assert diags == []


def test_unclassifiable_annotation_is_never_checked_for_alternative_only_evidence(tmp_path: Path):
    annotation = _annotation(
        primary_topics=[], secondary_topics=[], concepts=[], annotation_status="unclassifiable"
    )
    diags = validate_primary_evidence_not_alternative_only(annotation, tmp_path)
    assert diags == []


def test_required_concept_evidence_counts_towards_the_statement_check(tmp_path: Path):
    qdir = tmp_path
    (qdir / "q1.md").write_text(
        "# Q1\n\nFala sobre árvores binárias no enunciado.\n\n## Alternativas\n\nA. x\n",
        encoding="utf-8",
    )
    excerpt = "árvores binárias"
    annotation = _annotation(
        evidence=[],
        concepts=[
            ConceptAssociation(
                concept_id="concept-a",
                role="required",
                confidence="high",
                evidence_refs=[
                    SemanticEvidenceRef(
                        source_kind="statement",
                        source_locator="statement",
                        source_sha256=_HASH,
                        text_excerpt=excerpt,
                        excerpt_sha256=hashlib.sha256(excerpt.encode()).hexdigest(),
                    )
                ],
            )
        ],
    )
    diags = validate_primary_evidence_not_alternative_only(annotation, qdir)
    assert diags == []
