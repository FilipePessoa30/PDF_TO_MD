"""Tests for the structural corpus survey (PROMPT Fase 5A sections 5, 9,
20, 28, 26). Runs against the real, published, protected corpus - never a
synthetic stand-in - since the whole point of this module is to describe
facts about that real corpus.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from enade.models.enums import CourseCode
from enade.semantic.corpus_survey import (
    PROTECTED_TARGETS,
    resolve_question_directory,
    survey_all_targets,
    target_of_question_id,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def survey():
    return survey_all_targets(REPO_ROOT)


def test_survey_covers_exactly_the_five_protected_targets(survey):
    assert set(survey.keys()) == set(PROTECTED_TARGETS.keys())


def test_survey_total_question_count_is_255(survey):
    total = sum(len(entries) for entries in survey.values())
    assert total == 255


def test_2008_booklet_mixes_shared_and_course_specific_questions(survey):
    # The 2008 "all-computing" directory is a single physical booklet, but
    # its own front matter shows it is NOT uniformly "shared": the
    # formação-geral (and some componente-específico) questions use the
    # ALL_COMPUTING alias, while most componente-específico questions
    # (q21-q38/d39-d40 Bacharelado, q41-q58/d59-d60 Engenharia da
    # Computação, q61-q78/d79-d80 Sistemas de Informação) each declare a
    # single, specific applicable_courses value - confirmed by reading the
    # real front matter, not assumed structurally.
    shared = [e for e in survey["2008-b"] if e.is_shared_across_courses]
    course_specific = [e for e in survey["2008-b"] if not e.is_shared_across_courses]
    assert len(shared) == 20
    assert len(course_specific) == 60
    for entry in shared:
        assert CourseCode.ALL_COMPUTING.value in entry.applicable_courses
    for entry in course_specific:
        assert CourseCode.ALL_COMPUTING.value not in entry.applicable_courses
        assert len(entry.applicable_courses) == 1


def test_2021_split_booklets_are_never_flagged_shared_by_the_structural_predicate(survey):
    # The real content-identical duplicates across 2021 course booklets
    # (e.g. cc-b-q25/cc-l-q25) are invisible to this structural flag by
    # construction - each split booklet's own questions carry only their
    # own single course code, never the ALL_COMPUTING alias. This is
    # exactly why the pilot selection required a manual, full-text-read
    # augmentation (see data/semantic/pilot-selection-5a.json).
    for target in ("2021-cc-b", "2021-cc-l", "2021-si"):
        for entry in survey[target]:
            assert entry.is_shared_across_courses is False


def test_component_split_matches_section_prefix(survey):
    for entries in survey.values():
        for entry in entries:
            if entry.section.startswith("formacao-geral"):
                assert entry.component == "formacao_geral"
            else:
                assert entry.component == "componente_especifico"


def test_question_ids_are_unique_across_the_whole_survey(survey):
    all_ids = [entry.question_id for entries in survey.values() for entry in entries]
    assert len(all_ids) == len(set(all_ids))


# --- target_of_question_id / resolve_question_directory --------------------


@pytest.mark.parametrize(
    ("question_id", "expected_target"),
    [
        ("enade-2008-computing-q14", "2008-b"),
        ("enade-2011-computing-q46", "2011"),
        ("enade-2021-cc-b-q25", "2021-cc-b"),
        ("enade-2021-cc-l-q25", "2021-cc-l"),
        ("enade-2021-si-q34", "2021-si"),
    ],
)
def test_target_of_question_id_resolves_correctly(question_id, expected_target):
    assert target_of_question_id(question_id) == expected_target


def test_target_of_question_id_rejects_unknown_prefix():
    with pytest.raises(ValueError, match="matches none of the 5 protected targets"):
        target_of_question_id("enade-2005-computing-q01")


def test_resolve_question_directory_points_at_a_real_existing_file():
    directory = resolve_question_directory("enade-2011-computing-q46", REPO_ROOT)
    assert (directory / "enade-2011-computing-q46.md").is_file()
