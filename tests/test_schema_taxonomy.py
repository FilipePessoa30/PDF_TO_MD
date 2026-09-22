from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from enade.models.taxonomy import Taxonomy


@pytest.mark.parametrize(
    "path", sorted((Path(__file__).parent / "fixtures" / "taxonomy" / "valid").glob("*.yaml"))
)
def test_valid_taxonomy_fixtures_pass(path: Path):
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    taxonomy = Taxonomy.model_validate(data)
    assert taxonomy.subjects


@pytest.mark.parametrize(
    "path", sorted((Path(__file__).parent / "fixtures" / "taxonomy" / "invalid").glob("*.yaml"))
)
def test_invalid_taxonomy_fixtures_fail(path: Path):
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    with pytest.raises(ValidationError):
        Taxonomy.model_validate(data)


def test_demo_taxonomy_in_data_dir_is_valid_and_marked_as_demo():
    demo_path = Path(__file__).parent.parent / "data" / "taxonomy" / "demo-taxonomy.yaml"
    data = yaml.safe_load(demo_path.read_text(encoding="utf-8"))
    taxonomy = Taxonomy.model_validate(data)

    assert taxonomy.status.value == "demo"
    assert "not" in taxonomy.notice.lower() or "não" in taxonomy.notice.lower()


def test_taxonomy_allows_a_concept_to_be_referenced_across_subjects_as_a_prerequisite():
    data = {
        "version": "0.0.1",
        "status": "demo",
        "notice": "test",
        "subjects": [
            {
                "id": "subject-a",
                "name": "Subject A",
                "topics": [
                    {
                        "id": "topic-a",
                        "name": "Topic A",
                        "concepts": [{"id": "concept-a", "name": "A"}],
                    }
                ],
            },
            {
                "id": "subject-b",
                "name": "Subject B",
                "topics": [
                    {
                        "id": "topic-b",
                        "name": "Topic B",
                        "concepts": [
                            {"id": "concept-b", "name": "B", "prerequisites": ["concept-a"]}
                        ],
                    }
                ],
            },
        ],
    }
    taxonomy = Taxonomy.model_validate(data)
    assert taxonomy.subjects[1].topics[0].concepts[0].prerequisites == ["concept-a"]


def test_taxonomy_rejects_self_referencing_prerequisite():
    data = {
        "version": "0.0.1",
        "status": "demo",
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
                            {"id": "concept-a", "name": "A", "prerequisites": ["concept-a"]}
                        ],
                    }
                ],
            }
        ],
    }
    with pytest.raises(ValidationError, match="self-reference"):
        Taxonomy.model_validate(data)


# --- PROMPT Fase 5A section 8/26: richer per-node contract ----------------


def _minimal_taxonomy(**overrides) -> dict:
    base = {
        "taxonomy_id": "test-taxonomy",
        "version": "0.0.1",
        "status": "provisional",
        "notice": "test",
        "subjects": [
            {
                "id": "subject-a",
                "name": "Subject A",
                "topics": [{"id": "topic-a", "name": "Topic A", "concepts": []}],
            }
        ],
    }
    base.update(overrides)
    return base


def test_related_id_must_exist():
    data = _minimal_taxonomy()
    data["subjects"][0]["related_ids"] = ["does-not-exist"]
    with pytest.raises(ValidationError, match="unresolved related_ids"):
        Taxonomy.model_validate(data)


def test_related_id_self_reference_is_rejected():
    data = _minimal_taxonomy()
    data["subjects"][0]["related_ids"] = ["subject-a"]
    with pytest.raises(ValidationError, match="self-reference"):
        Taxonomy.model_validate(data)


def test_related_id_to_a_real_different_node_is_accepted():
    data = _minimal_taxonomy()
    data["subjects"][0]["topics"][0]["related_ids"] = ["subject-a"]
    taxonomy = Taxonomy.model_validate(data)
    assert taxonomy.subjects[0].topics[0].related_ids == ["subject-a"]


def test_duplicate_alias_across_two_nodes_is_rejected():
    data = _minimal_taxonomy()
    data["subjects"][0]["aliases"] = ["Redes"]
    data["subjects"][0]["topics"][0]["aliases"] = ["redes"]  # same after normalization
    with pytest.raises(ValidationError, match="colliding normalized aliases"):
        Taxonomy.model_validate(data)


def test_alias_normalization_catches_accent_and_case_differences():
    from enade.models.taxonomy import normalize_alias

    assert normalize_alias("Álgebra Booleana") == normalize_alias("algebra booleana")
    assert normalize_alias("  Redes   de Computadores ") == normalize_alias("redes de computadores")


def test_a_node_may_list_its_own_name_as_an_alias_without_colliding_with_itself():
    data = _minimal_taxonomy()
    data["subjects"][0]["aliases"] = ["Subject A"]
    taxonomy = Taxonomy.model_validate(data)
    assert taxonomy.subjects[0].aliases == ["Subject A"]


def test_deprecated_node_status_is_accepted_and_preserved():
    data = _minimal_taxonomy()
    data["subjects"][0]["topics"][0]["status"] = "deprecated"
    taxonomy = Taxonomy.model_validate(data)
    assert taxonomy.subjects[0].topics[0].status.value == "deprecated"


def test_invalid_node_status_is_rejected():
    data = _minimal_taxonomy()
    data["subjects"][0]["status"] = "not-a-real-status"
    with pytest.raises(ValidationError):
        Taxonomy.model_validate(data)


def test_invalid_taxonomy_document_status_is_rejected():
    data = _minimal_taxonomy(status="not-a-real-maturity")
    with pytest.raises(ValidationError):
        Taxonomy.model_validate(data)


def test_deterministic_ordering_is_enforced_when_taxonomy_id_is_set():
    data = _minimal_taxonomy()
    # "subject-0" sorts *before* "subject-a" (ASCII '0' < 'a') - appending
    # it after subject-a genuinely breaks sorted-by-id order.
    data["subjects"].append({"id": "subject-0", "name": "Sorts before subject-a", "topics": []})
    with pytest.raises(ValidationError, match="non-deterministic"):
        Taxonomy.model_validate(data)


def test_deterministic_ordering_is_not_enforced_without_taxonomy_id():
    # PROMPT Fase 5A section 8: never retroactively broken for
    # pre-existing documents (data/taxonomy/demo-taxonomy.yaml) that
    # never declare taxonomy_id.
    data = _minimal_taxonomy()
    del data["taxonomy_id"]
    data["subjects"].append(
        {"id": "subject-aardvark", "name": "Comes alphabetically before subject-a", "topics": []}
    )
    taxonomy = Taxonomy.model_validate(data)
    assert len(taxonomy.subjects) == 2


def test_flatten_yields_every_node_with_correct_level_and_parent_id():
    data = _minimal_taxonomy()
    data["subjects"][0]["topics"][0]["concepts"] = [{"id": "concept-a", "name": "Concept A"}]
    taxonomy = Taxonomy.model_validate(data)
    views = list(taxonomy.flatten())
    by_id = {v.id: v for v in views}
    assert by_id["subject-a"].level == 0
    assert by_id["subject-a"].parent_id is None
    assert by_id["topic-a"].level == 1
    assert by_id["topic-a"].parent_id == "subject-a"
    assert by_id["concept-a"].level == 2
    assert by_id["concept-a"].parent_id == "topic-a"


def test_source_reference_needs_only_a_title():
    # A node justified purely by corpus recurrence (section 9) has no
    # institutional document to cite - only `title` is required.
    data = _minimal_taxonomy()
    data["subjects"][0]["source_references"] = [
        {"title": "Recorrência real no corpus: 13 ocorrências em 2008-b/2021"}
    ]
    taxonomy = Taxonomy.model_validate(data)
    assert taxonomy.subjects[0].source_references[0].url is None
