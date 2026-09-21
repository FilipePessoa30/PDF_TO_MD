"""Integration tests for the table-visual-fallback asset coverage gap
(PROMPT Fase 4D, finding F6) - runs the real extraction pipeline against
the real, locally cached 2011 corpus, the smallest protected booklet that
actually contains a table with a mandatory visual-fallback crop
(``enade-2011-computing-q22/table-01.png`` - see
``to_question.render_statement_markdown``'s own docstring, PROMPT Phase
1C section 5.2: "D3-class content must never leave the reader with only
a structured guess and no way to check it against the original", so the
image is generated *unconditionally* alongside the structured GFM table,
never only when reconstruction fails).

2008-b (``tests/test_content_assignment_generation.py``) never exercises
this path at all - it has zero tables with a fallback asset - so its own
"zero orphans" result proved nothing about this mechanism (Fase 4C's own
review, Section F6). This file exists specifically to close that gap.
Skipped, not failed, when the 2011 corpus is not present.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from enade.cli import _resolve_booklet_location
from enade.extraction.answer_key import parse_flat_item_gabarito
from enade.extraction.content_assignment import (
    ContentAssignment,
    detect_duplicate_assignments,
    detect_missing_assignments,
    find_orphan_assets,
    generate_content_assignment_ledger,
)
from enade.extraction.layout_overrides import load_layout_overrides
from enade.extraction.visual_audit import load_table_cell_verified_question_ids, load_visual_audit

PROJECT_ROOT = Path(__file__).parent.parent
CORPUS_ROOT = PROJECT_ROOT / "data" / "raw" / "geacc-enade"
PROVA_PATH = CORPUS_ROOT / "2011" / "1_prova.pdf"
QUESTIONS_DIR = PROJECT_ROOT / "data" / "questions"
AUDIT_DIR = PROJECT_ROOT / "data" / "manifests"
TARGET_QUESTION = "enade-2011-computing-q22"
TARGET_ASSET = "table-01.png"

pytestmark = pytest.mark.skipif(
    not PROVA_PATH.exists(), reason="geacc/enade 2011 corpus not cloned locally"
)


def _generate() -> dict:
    loc = _resolve_booklet_location(2011, "all-computing", CORPUS_ROOT)
    visual_audit_path = AUDIT_DIR / f"visual-audit-2011-{loc.file_slug}.json"
    visual_audit = load_visual_audit(visual_audit_path)
    table_cells = load_table_cell_verified_question_ids(visual_audit_path)
    overrides = load_layout_overrides(AUDIT_DIR / "layout-overrides.yaml")
    return generate_content_assignment_ledger(
        prova_path=loc.prova_path,
        gabarito_path=loc.gabarito_path,
        padrao_path=loc.padrao_path,
        corpus_root=CORPUS_ROOT,
        exam_year=2011,
        exam_id=loc.exam_id,
        questions_output_dir=QUESTIONS_DIR,
        course=None if loc.is_unified else loc.course_code,
        structure_profile=loc.structure_profile,
        output_dir_name=loc.course_code.value if loc.is_unified else None,
        answer_key_parser=parse_flat_item_gabarito,
        layout_overrides=overrides,
        visual_audit=visual_audit,
        table_cells_verified_ids=table_cells,
    )


@pytest.fixture(scope="module")
def generated_2011_payload() -> dict:
    return _generate()


def _record_for_target(payload: dict) -> dict:
    matches = [
        r
        for r in payload["assignments"]
        if r["question_id"] == TARGET_QUESTION
        and r["source_type"] == "asset"
        and r["representation"] == TARGET_ASSET
    ]
    assert len(matches) == 1, (
        f"expected exactly one ledger record for {TARGET_QUESTION}/{TARGET_ASSET}, found {len(matches)}"
    )
    return matches[0]


def test_table_fallback_asset_has_a_ledger_record(generated_2011_payload):
    # The whole point of F6: before the fix, this record simply did not
    # exist - _record_question only ever enumerated figure_regions, never
    # extracted.tables' own mandatory visual-fallback asset.
    record = _record_for_target(generated_2011_payload)
    assert record["canonical_owner"] == "question"
    assert record["publication_destination"] == "question_asset"
    assert record["status"] == "assigned"
    assert record["confidence"] == 1.0


def test_table_fallback_asset_is_tagged_as_a_derived_representation(generated_2011_payload):
    # PROMPT Fase 4D section 6/8: a visual fallback is never a primary,
    # independent piece of content the way a figure_region asset is - it
    # is a derived, secondary view of the SAME semantic unit (the table)
    # that is also rendered as a structured GFM table right next to it.
    # Collapsing both into an indistinguishable "asset" would lose that
    # relationship for any future audit.
    record = _record_for_target(generated_2011_payload)
    assert record["representation_role"] == "visual_fallback"
    # The anchor traces back to which table (by structural index) this
    # crop derives from - never a bare position with no semantic meaning.
    assert record["anchor"].startswith("table:")


def test_every_other_asset_defaults_to_primary_representation_role(generated_2011_payload):
    # Backward compatibility: every pre-existing asset kind (figure
    # regions) is unaffected by the new field - defaults to "primary",
    # never silently reclassified.
    for r in generated_2011_payload["assignments"]:
        if r["source_type"] == "asset" and r["representation"] != TARGET_ASSET:
            assert r["representation_role"] == "primary"
    for r in generated_2011_payload["assignments"]:
        if r["source_type"] in ("line", "annotation"):
            assert r["representation_role"] == "primary"


def test_table_fallback_asset_id_is_geometry_derived_never_positional(generated_2011_payload):
    record = _record_for_target(generated_2011_payload)
    assert record["assignment_id"] == record["source_element_id"]
    # Same discipline as every other asset: page + full bbox, never a
    # bare enumerate() index over extracted.tables.
    assert ":p" in record["source_element_id"]
    parts = record["source_element_id"].split(":")
    assert len(parts) >= 4


def test_table_primary_lines_carry_a_reciprocal_table_anchor(generated_2011_payload):
    # PROMPT Fase 4E section 5: "Este fallback representa qual unidade
    # primaria?" is answerable from the fallback's own anchor
    # (table:<index>) - but the REVERSE query ("quais registros primarios
    # pertencem a esta tabela?") must also be answerable directly from the
    # published ledger, never only by re-deriving tabled_lines yourself.
    # Confirmed empirically before this fix: Q22's own header-letter lines
    # ("A","B","C","D","S" - its real, structured, table-consumed content)
    # carried the generic anchor="statement", identical to every other
    # unrelated statement line, with no way to tell they belong to
    # table:0 specifically.
    fallback = _record_for_target(generated_2011_payload)
    table_anchor = fallback["anchor"]
    assert table_anchor.startswith("table:")
    primary_table_lines = [
        r
        for r in generated_2011_payload["assignments"]
        if r["question_id"] == TARGET_QUESTION
        and r["source_type"] == "line"
        and r["representation_role"] == "primary"
        and r["anchor"] == table_anchor
    ]
    assert len(primary_table_lines) > 0, (
        "no primary line record references the same table anchor as its own fallback - "
        "the primary <-> derived relationship is not demonstrable from the ledger alone"
    )
    # The reciprocal tag is never applied to unrelated statement content -
    # only to lines the table itself actually consumed.
    header_letters = {r["representation"] for r in primary_table_lines}
    assert header_letters == {"A", "B", "C", "D", "S"}


def test_zero_orphan_assets_against_the_published_2011_corpus(generated_2011_payload):
    course_dir = QUESTIONS_DIR / "2011" / "all-computing"
    issues = find_orphan_assets(generated_2011_payload, course_dir)
    assert issues == [], f"unexpected orphan(s) remain: {[i.detail for i in issues]}"


def test_zero_duplicate_and_missing_findings_for_2011(generated_2011_payload):
    assignments = [ContentAssignment(**r) for r in generated_2011_payload["assignments"]]
    assert detect_duplicate_assignments(assignments) == []
    assert detect_missing_assignments(assignments) == []


def test_generation_is_deterministic_across_two_independent_calls():
    import json

    first = _generate()
    second = _generate()
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_a_true_orphan_is_still_detected_when_synthetically_introduced(
    generated_2011_payload, tmp_path
):
    # Regression guard for Section 23's own success criterion: fixing F6
    # must never make the gate blind to a *real* orphan. Copies the real
    # 2011 question directory into an isolated tmp_path and adds one
    # genuinely untracked PNG - never touches the real corpus.
    import shutil

    course_dir = QUESTIONS_DIR / "2011" / "all-computing"
    isolated = tmp_path / "all-computing"
    shutil.copytree(course_dir / TARGET_QUESTION, isolated / TARGET_QUESTION)
    (isolated / TARGET_QUESTION / "figure-99.png").write_bytes(b"\x89PNG\r\n")
    issues = find_orphan_assets(generated_2011_payload, isolated)
    orphan_paths = {i.detail for i in issues if i.kind == "asset_not_in_ledger"}
    assert any("figure-99.png" in d for d in orphan_paths)


def test_no_asset_record_is_double_counted_as_both_figure_and_table_fallback(
    generated_2011_payload,
):
    # PROMPT Fase 4E section 16: could the same real region ever be
    # enumerated both as a figure_region asset and a table-fallback
    # asset? Structurally no - assembler.py's own raw_candidate_lines
    # (fed into detect_tables()) already excludes every line consumed by
    # a visual region (_line_region_excluded), so a table can never be
    # detected over ground a figure region already claimed. Verified here
    # against real data rather than a fabricated fixture (an artificial
    # fixture would misrepresent a scenario the real pipeline cannot
    # produce): no two asset records for the same question ever share an
    # identical source_bbox, regardless of source_type/representation_role.
    by_question: dict[str, list[dict]] = {}
    for r in generated_2011_payload["assignments"]:
        if r["source_type"] == "asset":
            by_question.setdefault(r["question_id"], []).append(r)
    for question_id, assets in by_question.items():
        bboxes = [tuple(a["source_bbox"]) for a in assets]
        assert len(bboxes) == len(set(bboxes)), (
            f"{question_id}: two asset records share an identical bbox - "
            "a figure_region and a table fallback may have been double-counted"
        )
