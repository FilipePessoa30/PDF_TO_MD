"""Tests for the general-education-v1 taxonomy (PROMPT Fase 5B section
8/9): a namespace genuinely separate from Computing, never absorbing
formacao geral into a Computing area, with the same structural rigor as
computing-v1/1.1 (Taxonomy's own validators already enforce id
uniqueness/acyclicity/alias-collision/ordering - these tests check the
Fase 5B-specific claims about its content and separation).
"""

from __future__ import annotations

from pathlib import Path

from enade.semantic.artifacts import load_taxonomy

REPO_ROOT = Path(__file__).resolve().parent.parent
GENERAL_ED_PATH = REPO_ROOT / "data" / "taxonomy" / "general-education-v1.yaml"
COMPUTING_V11_PATH = REPO_ROOT / "data" / "taxonomy" / "computing-v1.1.yaml"


def test_general_education_taxonomy_loads_and_validates():
    taxonomy = load_taxonomy(GENERAL_ED_PATH)
    assert taxonomy.taxonomy_id == "general-education-v1"
    assert taxonomy.status.value == "provisional"


def test_general_education_has_two_subjects_covering_the_real_9_topics():
    taxonomy = load_taxonomy(GENERAL_ED_PATH)
    subject_ids = {s.id for s in taxonomy.subjects}
    assert subject_ids == {"formacao-geral", "pedagogia-e-formacao-de-professores"}
    topic_count = sum(len(s.topics) for s in taxonomy.subjects)
    assert topic_count == 9


def test_no_id_is_shared_between_computing_and_general_education():
    """PROMPT section 8: a namespace separate from Computing - verified
    here as a hard non-overlap of every id across both documents, not
    just a documentation claim.
    """
    computing = load_taxonomy(COMPUTING_V11_PATH)
    general_ed = load_taxonomy(GENERAL_ED_PATH)
    computing_ids = {view.id for view in computing.flatten()}
    general_ed_ids = {view.id for view in general_ed.flatten()}
    overlap = computing_ids & general_ed_ids
    assert not overlap, f"id(s) shared between the two taxonomies: {overlap}"


def test_general_education_has_zero_concepts():
    """This pilot never needed a concept level for general-education
    topics (each of the 9 was distinguishable by topic alone) - a fact
    worth pinning so a future addition is a deliberate choice, not a
    silent drift.
    """
    taxonomy = load_taxonomy(GENERAL_ED_PATH)
    concept_count = sum(len(t.concepts) for s in taxonomy.subjects for t in s.topics)
    assert concept_count == 0


def test_every_topic_cites_a_real_source_reference():
    taxonomy = load_taxonomy(GENERAL_ED_PATH)
    for subject in taxonomy.subjects:
        for topic in subject.topics:
            assert topic.source_references, f"{topic.id} has no source_references"


def test_pedagogia_subject_is_distinct_from_formacao_geral():
    """PROMPT section 6/8: the 2 Licenciatura-pedagogy cases are a
    different domain from the 7 true formacao-geral cases - verified as
    two genuinely separate subjects, never merged into one bucket.
    """
    taxonomy = load_taxonomy(GENERAL_ED_PATH)
    by_id = {s.id: s for s in taxonomy.subjects}
    pedagogia_topics = {t.id for t in by_id["pedagogia-e-formacao-de-professores"].topics}
    formacao_geral_topics = {t.id for t in by_id["formacao-geral"].topics}
    assert pedagogia_topics == {
        "curriculo-e-sociologia-da-educacao",
        "demografia-aplicada-ao-planejamento-educacional",
    }
    assert pedagogia_topics.isdisjoint(formacao_geral_topics)
