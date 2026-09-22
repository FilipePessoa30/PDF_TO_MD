"""Deterministic, stratified pilot sample selection (PROMPT Fase 5A
section 20). Never uses ``random``/``random.Random`` - a hash-based rank
is reproducible across Python versions/platforms by construction (no
dependency on any particular PRNG algorithm remaining stable), which
``random.Random(seed)`` alone does not guarantee.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from dataclasses import dataclass, field

from enade.semantic.corpus_survey import QuestionSurveyEntry

#: One (name, predicate) pair per PROMPT section 20 stratification
#: dimension actually computable from QuestionSurveyEntry - "níveis
#: diferentes de confiança esperada" is deliberately not a structural
#: predicate (confidence is a judgment made only once a question is
#: actually read, section 21) and is instead confirmed post-hoc, by
#: inspection of the real selected sample (docs/phase-5a-report.md
#: section P).
Stratum = tuple[str, Callable[[QuestionSurveyEntry], bool]]

STRATA: list[Stratum] = [
    ("target:2008-b", lambda e: e.target == "2008-b"),
    ("target:2011", lambda e: e.target == "2011"),
    ("target:2021-cc-b", lambda e: e.target == "2021-cc-b"),
    ("target:2021-cc-l", lambda e: e.target == "2021-cc-l"),
    ("target:2021-si", lambda e: e.target == "2021-si"),
    ("type:multiple_choice", lambda e: e.question_type == "multiple_choice"),
    ("type:discursive", lambda e: e.question_type == "discursive"),
    ("component:formacao_geral", lambda e: e.component == "formacao_geral"),
    ("component:componente_especifico", lambda e: e.component == "componente_especifico"),
    (
        "text_only",
        lambda e: e.asset_count == 0 and not e.has_table,
    ),
    ("has_table", lambda e: e.has_table),
    ("has_equation_asset", lambda e: e.has_equation_asset),
    ("has_diagram_or_image_asset", lambda e: e.has_diagram_or_image_asset),
    ("has_alternative_asset", lambda e: e.has_alternative_asset),
    ("source_limitation", lambda e: e.likely_source_limitation),
    ("shared_across_courses", lambda e: e.is_shared_across_courses),
]


@dataclass(frozen=True)
class PilotSelection:
    selection_method: str
    seed: str
    eligible_population: int
    strata: dict[str, int]
    selected_ids: list[str]
    exclusions: list[str] = field(default_factory=list)


def _rank_key(seed: str, question_id: str) -> str:
    return hashlib.sha256(f"{seed}:{question_id}".encode()).hexdigest()


def select_pilot_sample(
    entries: list[QuestionSurveyEntry], *, seed: str, target_size: int = 30
) -> PilotSelection:
    """Greedy, deterministic set cover over :data:`STRATA`, then filled
    to ``target_size`` by global rank - reproducible for a fixed
    ``entries``/``seed``/``target_size`` regardless of dict/set iteration
    order (every intermediate collection is explicitly sorted before use).
    """
    by_id = {e.question_id: e for e in entries}
    ranked_ids = sorted(by_id, key=lambda qid: _rank_key(seed, qid))

    selected: list[str] = []
    selected_set: set[str] = set()

    for _, predicate in STRATA:
        if any(predicate(by_id[qid]) for qid in selected):
            continue  # already covered by a previously selected question
        for qid in ranked_ids:
            if qid in selected_set:
                continue
            if predicate(by_id[qid]):
                selected.append(qid)
                selected_set.add(qid)
                break

    for qid in ranked_ids:
        if len(selected) >= target_size:
            break
        if qid not in selected_set:
            selected.append(qid)
            selected_set.add(qid)

    strata_counts = {
        name: sum(1 for qid in selected if predicate(by_id[qid])) for name, predicate in STRATA
    }

    return PilotSelection(
        selection_method="deterministic_stratified_set_cover_then_global_hash_rank",
        seed=seed,
        eligible_population=len(entries),
        strata=strata_counts,
        selected_ids=sorted(selected),
        exclusions=[],
    )
