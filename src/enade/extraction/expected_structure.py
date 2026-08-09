"""The corpus shape *observed previously* for the 2021 CC pilot, for comparison only.

Mirrors ``enade.inventory.expected_corpus``: this must never influence what
the pipeline actually extracts, it only lets ``enade extract`` report
whether the real, freshly-extracted result matches what PROMPT section 4
described going in (35 objectives, 5 discursives, 9 excluded perception
items), and say so explicitly if it does not.
"""

from __future__ import annotations

from dataclasses import dataclass

from enade.extraction.pipeline import ExtractionResult

EXPECTED_OBJECTIVES = 35
EXPECTED_DISCURSIVES = 5
EXPECTED_TOTAL = EXPECTED_OBJECTIVES + EXPECTED_DISCURSIVES
EXPECTED_PERCEPTION_ITEMS = 9


@dataclass
class StructureComparison:
    matches_expected: bool
    notes: list[str]


def compare_with_expected(result: ExtractionResult) -> StructureComparison:
    notes: list[str] = []
    metrics = result.metrics

    if metrics.objectives_found != EXPECTED_OBJECTIVES:
        notes.append(
            f"objectives found ({metrics.objectives_found}) != previously observed ({EXPECTED_OBJECTIVES})"
        )
    if metrics.discursives_found != EXPECTED_DISCURSIVES:
        notes.append(
            f"discursives found ({metrics.discursives_found}) != previously observed ({EXPECTED_DISCURSIVES})"
        )
    if len(result.excluded_perception_pages) == 0:
        notes.append(
            "no Questionario de Percepcao page was detected/excluded - verify this booklet has one"
        )

    return StructureComparison(matches_expected=not notes, notes=notes)
