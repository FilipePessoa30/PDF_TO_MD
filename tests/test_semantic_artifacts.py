"""Tests for the semantic-layer artifact load/save helpers (PROMPT Fase
5A section 25): round-trips against real fixtures plus the actually
published pilot artifacts.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from enade.semantic.artifacts import canonical_of_from_groups, load_annotations, load_taxonomy

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_load_taxonomy_reads_the_real_computing_v1():
    taxonomy = load_taxonomy(REPO_ROOT / "data" / "taxonomy" / "computing-v1.yaml")
    assert taxonomy.taxonomy_id == "computing-v1"
    assert len(taxonomy.subjects) > 0


def test_load_annotations_reads_the_real_pilot_set():
    annotations, groups = load_annotations(
        REPO_ROOT / "data" / "semantic" / "question-annotations-5a.json"
    )
    assert len(annotations) == 30
    assert len(groups) == 2


def test_canonical_of_from_groups_maps_every_member_to_the_lexicographic_min():
    groups = [["b-id", "a-id"], ["z-id", "y-id", "x-id"]]
    canonical_of = canonical_of_from_groups(groups)
    assert canonical_of == {
        "b-id": "a-id",
        "a-id": "a-id",
        "z-id": "x-id",
        "y-id": "x-id",
        "x-id": "x-id",
    }


def test_canonical_of_from_groups_empty_list_is_empty_map():
    assert canonical_of_from_groups([]) == {}


def test_load_annotations_round_trips_a_minimal_synthetic_file(tmp_path: Path):
    excerpt = "trecho de teste"
    payload = {
        "schema_version": 1,
        "shared_question_groups": [["q-a", "q-b"]],
        "annotations": [
            {
                "question_id": "q-a",
                "taxonomy_version": "test@1.0.0",
                "source_hash": hashlib.sha256(b"content").hexdigest(),
                "component": "componente_especifico",
                "primary_topics": ["topic-a"],
                "secondary_topics": [],
                "concepts": [],
                "context_tags": [],
                "cognitive_skills": ["apply"],
                "search_terms": [],
                "evidence": [
                    {
                        "source_kind": "statement",
                        "source_locator": "statement",
                        "source_sha256": hashlib.sha256(b"content").hexdigest(),
                        "text_excerpt": excerpt,
                        "excerpt_sha256": hashlib.sha256(excerpt.encode()).hexdigest(),
                    }
                ],
                "annotation_method": "manual",
                "annotation_status": "proposed",
                "confidence": "high",
            }
        ],
    }
    path = tmp_path / "synthetic.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    annotations, groups = load_annotations(path)
    assert len(annotations) == 1
    assert annotations[0].question_id == "q-a"
    assert groups == [["q-a", "q-b"]]
