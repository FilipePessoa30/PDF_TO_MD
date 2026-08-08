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
