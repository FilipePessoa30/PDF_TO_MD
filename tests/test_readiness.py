from __future__ import annotations

import json
from pathlib import Path

import pytest

from enade.extraction.markdown_writer import write_question_markdown
from enade.gold import GoldMaturity, build_gold_manifest
from enade.models.asset import Asset
from enade.models.enums import CourseCode
from enade.models.provenance import AnswerStandardReference, SourceOccurrence
from enade.models.question import Alternative, Question
from enade.readiness import assess_readiness


def _occurrence(**overrides) -> SourceOccurrence:
    base = dict(
        exam_id="enade-2021-b",
        pdf_sha256="a" * 64,
        source_path="2021/b1_prova.pdf",
        pages=[5],
        question_number=1,
        section="formacao-geral-objetiva",
    )
    base.update(overrides)
    return SourceOccurrence(**base)


def _objective(**overrides) -> Question:
    base = dict(
        id="enade-2021-cc-b-q01",
        exam_year=2021,
        source_occurrences=[_occurrence()],
        applicable_courses=[CourseCode.CC_BACHARELADO],
        section="formacao-geral-objetiva",
        question_number=1,
        question_type="multiple_choice",
        statement="Enunciado de teste suficientemente longo.",
        alternatives=[Alternative(letter="A", text="a"), Alternative(letter="B", text="b")],
        correct_answer="A",
        answer_validation_status="validated",
        extraction_status="verified",
        automatic_validation="passed",
        visual_validation="passed",
    )
    base.update(overrides)
    return Question(**base)


def _discursive(**overrides) -> Question:
    base = dict(
        id="enade-2021-cc-b-d01",
        exam_year=2021,
        source_occurrences=[_occurrence(question_number=1, section="formacao-geral-discursiva")],
        applicable_courses=[CourseCode.CC_BACHARELADO],
        section="formacao-geral-discursiva",
        question_number=1,
        question_type="discursive",
        statement="Enunciado discursivo de teste suficientemente longo.",
        alternatives=[],
        answer_validation_status="not_applicable",
        answer_standard=AnswerStandardReference(
            source_path="2021/b3_padrao.pdf",
            pdf_sha256="b" * 64,
            pages=[2],
            text="O respondente deve apresentar uma resposta coerente.",
        ),
        extraction_status="verified",
        automatic_validation="passed",
        visual_validation="passed",
    )
    base.update(overrides)
    return Question(**base)


def _build(
    course_dir: Path, tmp_path: Path, *, maturity=GoldMaturity.PROVISIONAL, structural_blockers=()
):
    prova_path, gabarito_path, padrao_path = (tmp_path / n for n in ("p.pdf", "g.pdf", "s.pdf"))
    for p in (prova_path, gabarito_path, padrao_path):
        if not p.exists():
            p.write_bytes(b"fake")
    return build_gold_manifest(
        exam_id="enade-2021-b",
        exam_year=2021,
        course="ciencia-da-computacao-bacharelado",
        corpus_commit="deadbeef" * 5,
        prova_path=prova_path,
        gabarito_path=gabarito_path,
        padrao_path=padrao_path,
        course_dir=course_dir,
        maturity=maturity,
        structural_blockers=structural_blockers,
    )


@pytest.fixture
def ready_course_dir(tmp_path: Path) -> Path:
    course_dir = tmp_path / "questions" / "2021" / "ciencia-da-computacao-bacharelado"
    course_dir.mkdir(parents=True)
    write_question_markdown(_objective(), course_dir)
    write_question_markdown(_discursive(), course_dir)
    return course_dir


def test_fully_verified_corpus_is_ready(ready_course_dir, tmp_path):
    manifest = _build(ready_course_dir, tmp_path)
    report = assess_readiness(manifest, ready_course_dir)
    assert report.ready is True
    assert report.classification == "READY_FOR_2011"
    assert report.blockers == ()
    assert report.verified_count == 2
    assert report.needs_review_count == 0


def test_needs_review_question_blocks_readiness(tmp_path):
    course_dir = tmp_path / "questions" / "2021" / "ciencia-da-computacao-bacharelado"
    course_dir.mkdir(parents=True)
    write_question_markdown(
        _objective(
            extraction_status="needs_review",
            automatic_validation="failed",
            visual_validation="not_performed",
        ),
        course_dir,
    )
    manifest = _build(course_dir, tmp_path)
    report = assess_readiness(manifest, course_dir)
    assert report.ready is False
    assert report.classification == "NOT_READY_FOR_2011"
    assert any(b.kind == "question_not_verified" for b in report.blockers)


def test_gold_hash_divergence_blocks_readiness(ready_course_dir, tmp_path):
    manifest = _build(ready_course_dir, tmp_path)
    md_path = ready_course_dir / "enade-2021-cc-b-q01.md"
    md_path.write_text(md_path.read_text(encoding="utf-8") + "\ntampered", encoding="utf-8")

    report = assess_readiness(manifest, ready_course_dir)
    assert report.ready is False
    assert any(b.kind.startswith("gold_divergence:") for b in report.blockers)


def test_recorded_structural_blocker_blocks_readiness(ready_course_dir, tmp_path):
    manifest = _build(ready_course_dir, tmp_path, structural_blockers=("enade-2021-cc-b-d01",))
    report = assess_readiness(manifest, ready_course_dir)
    assert report.ready is False
    assert any(b.kind == "recorded_structural_blocker" for b in report.blockers)


def test_discursive_without_answer_standard_blocks_readiness(tmp_path):
    course_dir = tmp_path / "questions" / "2021" / "ciencia-da-computacao-bacharelado"
    course_dir.mkdir(parents=True)
    write_question_markdown(_discursive(answer_standard=None), course_dir)
    manifest = _build(course_dir, tmp_path)
    report = assess_readiness(manifest, course_dir)
    assert report.ready is False
    assert any(b.kind == "missing_answer_standard" for b in report.blockers)


def test_objective_with_pending_answer_blocks_readiness(tmp_path):
    course_dir = tmp_path / "questions" / "2021" / "ciencia-da-computacao-bacharelado"
    course_dir.mkdir(parents=True)
    write_question_markdown(
        _objective(correct_answer=None, answer_validation_status="unknown"), course_dir
    )
    manifest = _build(course_dir, tmp_path)
    report = assess_readiness(manifest, course_dir)
    assert report.ready is False
    assert any(b.kind == "answer_not_resolved" for b in report.blockers)


def test_annulled_objective_answer_does_not_block_readiness(tmp_path):
    course_dir = tmp_path / "questions" / "2021" / "ciencia-da-computacao-bacharelado"
    course_dir.mkdir(parents=True)
    write_question_markdown(
        _objective(correct_answer=None, answer_validation_status="annulled"), course_dir
    )
    manifest = _build(course_dir, tmp_path)
    report = assess_readiness(manifest, course_dir)
    assert report.ready is True
    assert report.blockers == ()


def test_asset_with_missing_hash_blocks_readiness(tmp_path):
    course_dir = tmp_path / "questions" / "2021" / "ciencia-da-computacao-bacharelado"
    course_dir.mkdir(parents=True)
    png_bytes = b"\x89PNG fixture"
    asset_dir = course_dir / "enade-2021-cc-b-q01"
    asset_dir.mkdir()
    (asset_dir / "figure-01.png").write_bytes(png_bytes)
    write_question_markdown(
        _objective(
            assets=[
                Asset(
                    id="figure-01",
                    type="diagram",
                    path="enade-2021-cc-b-q01/figure-01.png",
                    source_page=5,
                    extraction_method="raster_crop",
                    sha256=None,
                )
            ]
        ),
        course_dir,
    )
    manifest = _build(course_dir, tmp_path)
    report = assess_readiness(manifest, course_dir)
    assert report.ready is False
    assert any(b.kind == "asset_missing_hash" for b in report.blockers)


def test_report_carries_gold_maturity_through(ready_course_dir, tmp_path):
    manifest = _build(ready_course_dir, tmp_path, maturity=GoldMaturity.VALIDATED)
    report = assess_readiness(manifest, ready_course_dir)
    assert report.gold_maturity == "validated"


def test_visual_audit_path_omitted_skips_the_coverage_check(ready_course_dir, tmp_path):
    manifest = _build(ready_course_dir, tmp_path)
    report = assess_readiness(manifest, ready_course_dir)
    assert report.visual_audit_coverage is None
    assert not any(b.kind == "visual_audit_incomplete" for b in report.blockers)


def test_incomplete_visual_audit_blocks_readiness(ready_course_dir, tmp_path):
    manifest = _build(ready_course_dir, tmp_path)
    audit_path = tmp_path / "visual-audit.json"
    audit_path.write_text(
        json.dumps({"enade-2021-cc-b-q01": {"status": "passed"}}), encoding="utf-8"
    )
    report = assess_readiness(manifest, ready_course_dir, visual_audit_path=audit_path)
    assert report.ready is False
    assert report.visual_audit_coverage is not None
    assert report.visual_audit_coverage.fully_covered is False
    assert any(b.kind == "visual_audit_incomplete" for b in report.blockers)


def test_fully_covered_visual_audit_does_not_block_readiness(ready_course_dir, tmp_path):
    manifest = _build(ready_course_dir, tmp_path)
    audit_path = tmp_path / "visual-audit.json"
    audit_path.write_text(
        json.dumps(
            {
                "enade-2021-cc-b-q01": {"status": "passed"},
                "enade-2021-cc-b-d01": {"status": "passed"},
            }
        ),
        encoding="utf-8",
    )
    report = assess_readiness(manifest, ready_course_dir, visual_audit_path=audit_path)
    assert report.ready is True
    assert report.visual_audit_coverage is not None
    assert report.visual_audit_coverage.fully_covered is True
