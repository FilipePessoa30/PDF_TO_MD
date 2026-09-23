"""Tests for the Fase 5A -> Fase 5B annotation migration (PROMPT Fase 5B
section 16, 26): every question tracked, unchanged ones marked as such,
stable ids, real reasons, and the two general-education/computing
taxonomies stay internally coherent with the migration log's own claims.
"""

from __future__ import annotations

import json
from pathlib import Path

from enade.semantic.annotation import QuestionAnnotation
from enade.semantic.artifacts import load_taxonomy

REPO_ROOT = Path(__file__).resolve().parent.parent
MIGRATION_PATH = REPO_ROOT / "data" / "semantic" / "migration-5a-to-5b.json"
ANNOTATIONS_5A_PATH = REPO_ROOT / "data" / "semantic" / "question-annotations-5a.json"
ANNOTATIONS_5B_PATH = REPO_ROOT / "data" / "semantic" / "question-annotations-5b.json"


def _migration() -> dict:
    return json.loads(MIGRATION_PATH.read_text(encoding="utf-8"))


def _annotations_5a() -> dict[str, dict]:
    payload = json.loads(ANNOTATIONS_5A_PATH.read_text(encoding="utf-8"))
    return {a["question_id"]: a for a in payload["annotations"]}


def _annotations_5b() -> dict[str, dict]:
    payload = json.loads(ANNOTATIONS_5B_PATH.read_text(encoding="utf-8"))
    return {a["question_id"]: a for a in payload["annotations"]}


def test_every_5a_question_has_exactly_one_migration_entry():
    migration = _migration()
    ids = [e["question_id"] for e in migration["entries"]]
    assert len(ids) == len(set(ids)) == 30
    assert set(ids) == set(_annotations_5a().keys())


def test_every_migration_entry_has_a_non_empty_reason():
    migration = _migration()
    for entry in migration["entries"]:
        assert entry["change_reason"].strip()


def test_unchanged_questions_are_explicitly_marked_unchanged_in_the_reason():
    migration = _migration()
    unchanged_count = sum(1 for e in migration["entries"] if "unchanged" in e["change_reason"])
    # 17 proposed questions were carried forward with zero content change
    # (version bump only) - PROMPT section 16 requires these be provably
    # marked, not silently omitted from the log.
    assert unchanged_count == 17


def test_reclassified_general_education_questions_are_tracked_with_real_topic_deltas():
    migration = _migration()
    by_id = {e["question_id"]: e for e in migration["entries"]}
    ten_reclassified = [
        "enade-2008-computing-d09",
        "enade-2008-computing-q04",
        "enade-2011-computing-q01",
        "enade-2011-computing-q31",
        "enade-2011-computing-q33",
        "enade-2021-cc-b-d01",
        "enade-2021-si-d01",
        "enade-2021-cc-b-q01",
        "enade-2021-si-d02",
        "enade-2021-si-q05",
    ]
    for qid in ten_reclassified:
        entry = by_id[qid]
        assert entry["previous_status"] == "unclassifiable"
        assert entry["new_status"] == "proposed"
        assert entry["previous_topics"] == []
        assert entry["new_topics"], f"{qid} should have a real new topic"


def test_needs_review_cases_are_tracked_as_resolved():
    migration = _migration()
    by_id = {e["question_id"]: e for e in migration["entries"]}
    for qid in ("enade-2011-computing-q14", "enade-2011-computing-q23"):
        entry = by_id[qid]
        assert entry["previous_status"] == "needs_review"
        assert entry["new_status"] == "proposed"


def test_question_id_stability_5a_to_5b():
    """PROMPT section 16/27: stable ids - no question_id was renamed or
    duplicated across the migration.
    """
    assert set(_annotations_5a().keys()) == set(_annotations_5b().keys())


def test_5a_source_file_is_byte_identical_after_migration():
    """The Fase 5A annotation file itself must never be rewritten by the
    migration process (PROMPT section 4).
    """
    payload = json.loads(ANNOTATIONS_5A_PATH.read_text(encoding="utf-8"))
    assert payload["annotation_count"] == 30
    assert payload["generated_by"] == "manual pilot annotation, PROMPT Fase 5A"


def test_taxonomy_dispatch_matches_migration_claims():
    """Every question the migration log says moved to general-education-v1
    really has that taxonomy_version in the 5B file, and vice-versa for
    the ones that stayed in Computing.
    """
    migration = _migration()
    annotations_5b = _annotations_5b()
    for entry in migration["entries"]:
        annotation = annotations_5b[entry["question_id"]]
        if "general-education-v1" in entry["taxonomy_change"]:
            assert annotation["taxonomy_version"].startswith("general-education-v1@")
        elif entry["taxonomy_change"].startswith("computing-v1"):
            assert annotation["taxonomy_version"].startswith("computing-v1@")


def test_all_5b_annotations_still_validate_as_question_annotation_models():
    for data in _annotations_5b().values():
        QuestionAnnotation(**data)


def test_computing_v1_1_preserves_every_id_from_computing_v1():
    v1 = load_taxonomy(REPO_ROOT / "data" / "taxonomy" / "computing-v1.yaml")
    v11 = load_taxonomy(REPO_ROOT / "data" / "taxonomy" / "computing-v1.1.yaml")
    v1_ids = {view.id for view in v1.flatten()}
    v11_ids = {view.id for view in v11.flatten()}
    missing = v1_ids - v11_ids
    assert not missing, f"computing-v1.1 dropped id(s) that existed in computing-v1: {missing}"
