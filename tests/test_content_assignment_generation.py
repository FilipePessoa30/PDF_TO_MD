"""Integration tests for content-assignment ledger generation (PROMPT
Fase 4B) - runs the real extraction pipeline against the real, locally
cached 2008-b corpus, exactly like ``test_extraction_pipeline_2008.py``
(same rationale: a real regeneration is the only thing that can actually
prove determinism, zero duplication, and zero staleness). Skipped, not
failed, when that corpus is not present.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from enade.cli import _resolve_booklet_location
from enade.extraction.answer_key import parse_answer_key, parse_flat_item_gabarito
from enade.extraction.content_assignment import (
    ContentAssignment,
    _naive_alternative_text,
    detect_duplicate_assignments,
    detect_missing_assignments,
    generate_content_assignment_ledger,
    validate_ledger_against_corpus,
)
from enade.extraction.exam_profile import _RANGE_PATTERNS_2008_B
from enade.extraction.layout import Line
from enade.extraction.layout_overrides import load_layout_overrides
from enade.extraction.visual_audit import load_table_cell_verified_question_ids, load_visual_audit

PROJECT_ROOT = Path(__file__).parent.parent
CORPUS_ROOT = PROJECT_ROOT / "data" / "raw" / "geacc-enade"
PROVA_PATH = CORPUS_ROOT / "2008" / "b1_prova.pdf"
QUESTIONS_DIR = PROJECT_ROOT / "data" / "questions"
AUDIT_DIR = PROJECT_ROOT / "data" / "manifests"

pytestmark = pytest.mark.skipif(
    not PROVA_PATH.exists(),
    reason="geacc/enade corpus not cloned locally (run scripts/fetch_corpus.py)",
)


def _line(x: float, text: str) -> Line:
    return Line(page_number=1, text=text, x0=x, y0=100.0, x1=x + 100.0, y1=112.0)


def test_naive_alternative_text_strips_the_marker_prefix():
    lines = [_line(30.0, "A\tTexto da alternativa A.")]
    assert _naive_alternative_text(lines, [0, 1], 0) == "Texto da alternativa A."


def test_naive_alternative_text_joins_a_multi_line_alternative():
    lines = [_line(30.0, "A\tPrimeira linha."), _line(30.0, "Segunda linha.")]
    assert _naive_alternative_text(lines, [0, 2], 0) == "Primeira linha. Segunda linha."


def test_naive_alternative_text_empty_range_is_empty_string():
    assert _naive_alternative_text([_line(30.0, "A")], [0, 0], 0) == ""


def _generate() -> dict:
    # Mirrors `enade generate-content-assignment`'s own parameter
    # resolution verbatim (src/enade/cli.py generate_content_assignment_cmd)
    # rather than re-deriving it, so this test can never silently drift
    # from what the real CLI actually does.
    loc = _resolve_booklet_location(2008, "all-computing", CORPUS_ROOT)
    visual_audit_path = AUDIT_DIR / f"visual-audit-2008-{loc.file_slug}.json"
    visual_audit = load_visual_audit(visual_audit_path)
    table_cells = load_table_cell_verified_question_ids(visual_audit_path)
    overrides = load_layout_overrides(AUDIT_DIR / "layout-overrides.yaml")
    return generate_content_assignment_ledger(
        prova_path=loc.prova_path,
        gabarito_path=loc.gabarito_path,
        padrao_path=loc.padrao_path,
        corpus_root=CORPUS_ROOT,
        exam_year=2008,
        exam_id=loc.exam_id,
        questions_output_dir=QUESTIONS_DIR,
        course=None if loc.is_unified else loc.course_code,
        structure_profile=loc.structure_profile,
        structure_verification_page=11,
        structure_verification_patterns=_RANGE_PATTERNS_2008_B,
        output_dir_name=loc.course_code.value if loc.is_unified else None,
        answer_key_parser=parse_flat_item_gabarito if loc.is_unified else parse_answer_key,
        layout_overrides=overrides,
        visual_audit=visual_audit,
        table_cells_verified_ids=table_cells,
    )


@pytest.fixture(scope="module")
def generated_2008b_payload() -> dict:
    return _generate()


def test_generation_is_deterministic_across_two_independent_calls(generated_2008b_payload):
    second = _generate()
    assert json.dumps(generated_2008b_payload, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_generation_produces_ordered_deterministic_assignment_ids(generated_2008b_payload):
    ids = [r["assignment_id"] for r in generated_2008b_payload["assignments"]]
    assert ids == sorted(ids)
    assert len(ids) == len(set(ids))


def test_zero_duplicate_and_missing_findings_in_the_regenerated_ledger(generated_2008b_payload):
    assignments = [ContentAssignment(**r) for r in generated_2008b_payload["assignments"]]
    assert detect_duplicate_assignments(assignments) == []
    assert detect_missing_assignments(assignments) == []


def test_zero_corpus_validation_issues_against_the_published_2008b_corpus(generated_2008b_payload):
    course_dir = QUESTIONS_DIR / "2008" / "all-computing"
    assert validate_ledger_against_corpus(generated_2008b_payload, course_dir) == []


def _assets_for(payload: dict, question_id: str) -> list[dict]:
    return [
        r
        for r in payload["assignments"]
        if r["question_id"] == question_id and r["source_type"] == "asset"
    ]


def test_q08_has_exactly_five_distinct_raster_assets(generated_2008b_payload):
    assets = _assets_for(generated_2008b_payload, "enade-2008-computing-q08")
    assert len(assets) == 5
    assert len({a["representation"] for a in assets}) == 5
    assert all(a["canonical_owner"] == "question" for a in assets)
    assert all(a["publication_destination"] == "question_asset" for a in assets)


def test_q38_circuit_and_alternatives_are_separate_assets(generated_2008b_payload):
    assets = _assets_for(generated_2008b_payload, "enade-2008-computing-q38")
    assert len(assets) == 6  # 1 circuit + 5 alternative formulas
    assert len({a["representation"] for a in assets}) == 6


def test_q55_has_five_vector_alternative_assets(generated_2008b_payload):
    assets = _assets_for(generated_2008b_payload, "enade-2008-computing-q55")
    assert len(assets) == 5


def test_q45_has_its_own_asset(generated_2008b_payload):
    assets = _assets_for(generated_2008b_payload, "enade-2008-computing-q45")
    assert len(assets) >= 1


def test_d59_answer_standard_asset_is_out_of_scope_by_design(generated_2008b_payload):
    # PROMPT Fase 4B section 6: answer_standard was never part of this
    # ledger's own original contract (Fase 3J) - D59's own visual-only
    # rubric asset lives in a separate pipeline stage this generator never
    # instruments, and this must not silently change just because D59's
    # own question-level content is otherwise fully covered.
    assets = _assets_for(generated_2008b_payload, "enade-2008-computing-d59")
    assert assets == []


def test_no_asset_records_reference_a_suppressed_or_nonexistent_region(generated_2008b_payload):
    course_dir = QUESTIONS_DIR / "2008" / "all-computing"
    issues = validate_ledger_against_corpus(generated_2008b_payload, course_dir)
    assert not any(i.kind == "asset_file_missing" for i in issues)


def test_ambiguous_records_never_claim_assigned_status(generated_2008b_payload):
    # Every record this generator could not confidently attribute is
    # honestly marked - never silently defaulting back to "assigned".
    for r in generated_2008b_payload["assignments"]:
        if r["confidence"] == 0.0:
            assert r["status"] == "ambiguous"
