"""Tests for the Fase 5B semantic freeze's structural completeness
contract (PROMPT Fase 5B section 30, 26) - a different artifact shape
from Fase 5A's own (two taxonomies, ledger, migration log, adjudication
template), but the same never-claim-human-review discipline.
"""

from __future__ import annotations

from enade.semantic.freeze import validate_phase5b_freeze_completeness


def _complete_freeze(**overrides) -> dict:
    base = {
        "head": "4ca2a82be4e01188e09563f83e2bec1f2d0f3677",
        "predecessor_semantic_freeze_reference": {
            "path": "data/manifests/phase-5a-semantic-freeze.json",
            "sha256": "a" * 64,
        },
        "extraction_freeze_reference": {
            "path": "data/manifests/phase-4e-freeze.json",
            "sha256": "b" * 64,
        },
        "artifacts": {
            "taxonomy_computing": {"path": "data/taxonomy/computing-v1.1.yaml", "sha256": "c" * 64},
            "taxonomy_general_education": {
                "path": "data/taxonomy/general-education-v1.yaml",
                "sha256": "d" * 64,
            },
            "annotations": {
                "path": "data/semantic/question-annotations-5b.json",
                "sha256": "e" * 64,
            },
            "unresolved_cases_ledger": {
                "path": "data/semantic/unresolved-cases-ledger-5b.json",
                "sha256": "f" * 64,
            },
            "migration_log": {"path": "data/semantic/migration-5a-to-5b.json", "sha256": "1" * 64},
            "human_adjudication_template": {
                "path": "data/semantic/human-adjudication-template-5b.json",
                "sha256": "2" * 64,
            },
            "review_packet": {"path": "docs/semantic-pilot-review-5b.md", "sha256": "3" * 64},
        },
        "counts": {"annotation_count": 30},
        "quality_gates": {"pytest": "passed"},
        "semantic_maturity": "provisional_reconciled_pilot",
        "human_review_status": "not_yet_reviewed",
    }
    base.update(overrides)
    return base


def test_complete_5b_freeze_has_no_violations():
    assert validate_phase5b_freeze_completeness(_complete_freeze()) == []


def test_missing_predecessor_reference_is_flagged():
    freeze = _complete_freeze()
    del freeze["predecessor_semantic_freeze_reference"]
    violations = validate_phase5b_freeze_completeness(freeze)
    assert any("predecessor_semantic_freeze_reference" in v for v in violations)


def test_missing_extraction_reference_is_flagged():
    freeze = _complete_freeze()
    del freeze["extraction_freeze_reference"]
    violations = validate_phase5b_freeze_completeness(freeze)
    assert any("extraction_freeze_reference" in v for v in violations)


def test_missing_taxonomy_computing_artifact_is_flagged():
    freeze = _complete_freeze()
    del freeze["artifacts"]["taxonomy_computing"]
    violations = validate_phase5b_freeze_completeness(freeze)
    assert any("taxonomy_computing" in v for v in violations)


def test_missing_ledger_artifact_is_flagged():
    freeze = _complete_freeze()
    del freeze["artifacts"]["unresolved_cases_ledger"]
    violations = validate_phase5b_freeze_completeness(freeze)
    assert any("unresolved_cases_ledger" in v for v in violations)


def test_missing_migration_log_artifact_is_flagged():
    freeze = _complete_freeze()
    del freeze["artifacts"]["migration_log"]
    violations = validate_phase5b_freeze_completeness(freeze)
    assert any("migration_log" in v for v in violations)


def test_5a_style_artifact_keys_alone_do_not_satisfy_the_5b_shape():
    """The Fase 5A freeze's own artifact keys (pilot_selection,
    guidelines) are not what Fase 5B's freeze needs - a freeze that
    accidentally reused the 5A shape must still be rejected.
    """
    freeze = _complete_freeze()
    freeze["artifacts"] = {
        "taxonomy": {"path": "x", "sha256": "a" * 64},
        "annotations": {"path": "y", "sha256": "b" * 64},
        "pilot_selection": {"path": "z", "sha256": "c" * 64},
        "guidelines": {"path": "w", "sha256": "d" * 64},
        "review_packet": {"path": "v", "sha256": "e" * 64},
    }
    violations = validate_phase5b_freeze_completeness(freeze)
    assert violations != []


def test_reviewed_human_review_status_is_rejected():
    freeze = _complete_freeze()
    freeze["human_review_status"] = "reviewed"
    violations = validate_phase5b_freeze_completeness(freeze)
    assert any("human_review_status" in v for v in violations)


def test_empty_quality_gates_is_flagged():
    freeze = _complete_freeze()
    freeze["quality_gates"] = {}
    violations = validate_phase5b_freeze_completeness(freeze)
    assert any("quality_gates" in v for v in violations)
