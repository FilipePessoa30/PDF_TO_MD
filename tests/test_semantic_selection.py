"""Tests for the deterministic pilot-selection algorithm (PROMPT Fase 5A
sections 20, 26, 29): reproducibility, stratum coverage, population-change
detection. ``select_pilot_sample`` itself is exercised here as the
reusable, tested mechanism intended for a future full-corpus rollout (see
data/semantic/pilot-selection-5a.json's own ``method_notes`` for why the
30-question pilot itself was, in the end, manually curated instead).
"""

from __future__ import annotations

from enade.semantic.corpus_survey import QuestionSurveyEntry
from enade.semantic.selection import STRATA, select_pilot_sample


def _entry(question_id: str, **overrides) -> QuestionSurveyEntry:
    base = dict(
        question_id=question_id,
        target="2011",
        exam_year=2011,
        applicable_courses=("all-computing",),
        is_shared_across_courses=False,
        section="componente-especifico-objetiva",
        component="componente_especifico",
        question_type="multiple_choice",
        has_table=False,
        has_equation_asset=False,
        has_diagram_or_image_asset=False,
        has_alternative_asset=False,
        asset_count=0,
        has_answer_standard=True,
        likely_source_limitation=False,
        statement_word_count=50,
    )
    base.update(overrides)
    return QuestionSurveyEntry(**base)


def _population(n: int = 60) -> list[QuestionSurveyEntry]:
    entries = []
    for i in range(n):
        entries.append(
            _entry(
                f"enade-2011-computing-q{i:02d}",
                has_table=(i % 10 == 0),
                has_equation_asset=(i % 7 == 0),
                has_diagram_or_image_asset=(i % 5 == 0),
                has_alternative_asset=(i % 11 == 0),
                question_type="discursive" if i % 6 == 0 else "multiple_choice",
                component="formacao_geral" if i % 8 == 0 else "componente_especifico",
                likely_source_limitation=(i % 13 == 0),
                is_shared_across_courses=(i % 9 == 0),
                target=["2008-b", "2011", "2021-cc-b", "2021-cc-l", "2021-si"][i % 5],
            )
        )
    return entries


def test_selection_is_deterministic_for_the_same_seed():
    population = _population()
    a = select_pilot_sample(population, seed="test-seed-v1", target_size=30)
    b = select_pilot_sample(population, seed="test-seed-v1", target_size=30)
    assert a == b


def test_different_seeds_can_produce_different_samples():
    population = _population()
    a = select_pilot_sample(population, seed="seed-a", target_size=30)
    b = select_pilot_sample(population, seed="seed-b", target_size=30)
    assert a.selected_ids != b.selected_ids


def test_selected_size_matches_target():
    population = _population()
    result = select_pilot_sample(population, seed="x", target_size=30)
    assert len(result.selected_ids) == 30
    assert len(set(result.selected_ids)) == 30


def test_every_stratum_with_eligible_members_is_covered():
    population = _population()
    result = select_pilot_sample(population, seed="x", target_size=30)
    for name, predicate in STRATA:
        eligible = any(predicate(e) for e in population)
        if eligible:
            assert result.strata[name] > 0, f"stratum {name} has eligible members but 0 selected"


def test_eligible_population_reflects_the_real_input_size():
    population = _population(60)
    result = select_pilot_sample(population, seed="x", target_size=30)
    assert result.eligible_population == 60

    smaller_population = _population(40)
    result_smaller = select_pilot_sample(smaller_population, seed="x", target_size=30)
    assert result_smaller.eligible_population == 40


def test_altered_population_produces_a_different_recorded_eligible_population():
    # PROMPT section 26: "populacao alterada detectada" - a re-run against
    # a changed population must be observably different from the original
    # run, never silently identical.
    original = select_pilot_sample(_population(60), seed="x", target_size=30)
    altered = select_pilot_sample(_population(61), seed="x", target_size=30)
    assert original.eligible_population != altered.eligible_population


def test_a_shared_question_is_never_selected_twice():
    population = _population()
    result = select_pilot_sample(population, seed="x", target_size=30)
    assert len(result.selected_ids) == len(set(result.selected_ids))
