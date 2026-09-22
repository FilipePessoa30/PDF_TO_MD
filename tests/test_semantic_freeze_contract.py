"""Tests for the semantic freeze's structural completeness contract
(PROMPT Fase 5A section 30, 26).
"""

from __future__ import annotations

from enade.semantic.freeze import validate_semantic_freeze_completeness


def _complete_freeze(**overrides) -> dict:
    base = {
        "head": "8e272cc0dd53031ddddc78d3f88c7efdce073a8f",
        "extraction_freeze_reference": {
            "path": "data/manifests/phase-4e-freeze.json",
            "sha256": "a" * 64,
        },
        "artifacts": {
            "taxonomy": {"path": "data/taxonomy/computing-v1.yaml", "sha256": "b" * 64},
            "annotations": {
                "path": "data/semantic/question-annotations-5a.json",
                "sha256": "c" * 64,
            },
            "pilot_selection": {
                "path": "data/semantic/pilot-selection-5a.json",
                "sha256": "d" * 64,
            },
            "guidelines": {
                "path": "docs/semantic-annotation-guidelines.md",
                "sha256": "e" * 64,
            },
            "review_packet": {"path": "docs/semantic-pilot-review.md", "sha256": "f" * 64},
        },
        "counts": {"annotation_count": 30},
        "quality_gates": {"pytest": "passed"},
        "semantic_maturity": "provisional_pilot",
        "human_review_status": "not_yet_reviewed",
    }
    base.update(overrides)
    return base


def test_complete_freeze_has_no_violations():
    assert validate_semantic_freeze_completeness(_complete_freeze()) == []


def test_missing_head_is_flagged():
    freeze = _complete_freeze()
    freeze["head"] = ""
    violations = validate_semantic_freeze_completeness(freeze)
    assert any("head" in v for v in violations)


def test_missing_extraction_freeze_reference_is_flagged():
    freeze = _complete_freeze()
    del freeze["extraction_freeze_reference"]
    violations = validate_semantic_freeze_completeness(freeze)
    assert any("extraction_freeze_reference" in v for v in violations)


def test_missing_required_artifact_is_flagged():
    freeze = _complete_freeze()
    del freeze["artifacts"]["taxonomy"]
    violations = validate_semantic_freeze_completeness(freeze)
    assert any("taxonomy" in v for v in violations)


def test_artifact_missing_sha256_is_flagged():
    freeze = _complete_freeze()
    freeze["artifacts"]["taxonomy"] = {"path": "x"}
    violations = validate_semantic_freeze_completeness(freeze)
    assert any("taxonomy" in v for v in violations)


def test_empty_counts_is_flagged():
    freeze = _complete_freeze()
    freeze["counts"] = {}
    violations = validate_semantic_freeze_completeness(freeze)
    assert any("counts" in v for v in violations)


def test_empty_quality_gates_is_flagged():
    freeze = _complete_freeze()
    freeze["quality_gates"] = {}
    violations = validate_semantic_freeze_completeness(freeze)
    assert any("quality_gates" in v for v in violations)


def test_missing_semantic_maturity_is_flagged():
    freeze = _complete_freeze()
    freeze["semantic_maturity"] = ""
    violations = validate_semantic_freeze_completeness(freeze)
    assert any("semantic_maturity" in v for v in violations)


def test_reviewed_human_review_status_is_rejected():
    """PROMPT section 30: never claim the pilot was humanly approved."""
    freeze = _complete_freeze()
    freeze["human_review_status"] = "reviewed"
    violations = validate_semantic_freeze_completeness(freeze)
    assert any("human_review_status" in v for v in violations)


def test_approved_human_review_status_is_rejected():
    freeze = _complete_freeze()
    freeze["human_review_status"] = "approved"
    violations = validate_semantic_freeze_completeness(freeze)
    assert any("human_review_status" in v for v in violations)
