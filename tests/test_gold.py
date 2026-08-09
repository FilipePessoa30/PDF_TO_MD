from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from enade.extraction.markdown_writer import write_question_markdown
from enade.gold import (
    build_gold_manifest,
    read_gold_manifest,
    verify_gold_manifest,
    write_gold_manifest,
)
from enade.models.asset import Asset
from enade.models.enums import CourseCode
from enade.models.provenance import SourceOccurrence
from enade.models.question import Alternative, Question


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


def _question(**overrides) -> Question:
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
        extraction_status="verified",
        automatic_validation="passed",
        visual_validation="passed",
    )
    base.update(overrides)
    return Question(**base)


@pytest.fixture
def gold_fixture(tmp_path: Path):
    """A minimal, self-contained gold corpus: one question with an asset,
    one without, written the same way the real pipeline writes them
    (co-located asset next to its .md file).
    """
    course_dir = tmp_path / "questions" / "2021" / "ciencia-da-computacao-bacharelado"
    course_dir.mkdir(parents=True)

    png_bytes = b"\x89PNG\r\n\x1a\nnot a real png, just fixture bytes"
    asset_dir = course_dir / "enade-2021-cc-b-q01"
    asset_dir.mkdir()
    (asset_dir / "figure-01.png").write_bytes(png_bytes)
    asset_sha256 = hashlib.sha256(png_bytes).hexdigest()

    q_with_asset = _question(
        assets=[
            Asset(
                id="figure-01",
                type="diagram",
                path="enade-2021-cc-b-q01/figure-01.png",
                source_page=5,
                extraction_method="raster_crop",
                sha256=asset_sha256,
            )
        ]
    )
    q_plain = _question(
        id="enade-2021-cc-b-q02",
        question_number=2,
        source_occurrences=[_occurrence(question_number=2, pages=[6])],
        extraction_status="needs_review",
        automatic_validation="failed",
        visual_validation="not_performed",
    )
    write_question_markdown(q_with_asset, course_dir)
    write_question_markdown(q_plain, course_dir)

    prova_path = tmp_path / "prova.pdf"
    gabarito_path = tmp_path / "gabarito.pdf"
    padrao_path = tmp_path / "padrao.pdf"
    prova_path.write_bytes(b"fake prova")
    gabarito_path.write_bytes(b"fake gabarito")
    padrao_path.write_bytes(b"fake padrao")

    manifest = build_gold_manifest(
        exam_id="enade-2021-b",
        exam_year=2021,
        course="ciencia-da-computacao-bacharelado",
        corpus_commit="deadbeef" * 5,
        prova_path=prova_path,
        gabarito_path=gabarito_path,
        padrao_path=padrao_path,
        course_dir=course_dir,
    )
    return manifest, course_dir


def test_build_gold_manifest_records_both_questions_and_asset(gold_fixture):
    manifest, _ = gold_fixture
    assert manifest.exam_id == "enade-2021-b"
    assert len(manifest.questions) == 2
    by_id = {q.id: q for q in manifest.questions}
    assert by_id["enade-2021-cc-b-q01"].extraction_status == "verified"
    assert len(by_id["enade-2021-cc-b-q01"].assets) == 1
    assert by_id["enade-2021-cc-b-q02"].extraction_status == "needs_review"
    assert by_id["enade-2021-cc-b-q02"].assets == ()


def test_gold_manifest_json_round_trips(gold_fixture, tmp_path):
    manifest, _ = gold_fixture
    path = tmp_path / "gold.json"
    write_gold_manifest(manifest, path)
    loaded = read_gold_manifest(path)
    assert loaded == manifest


def test_verify_gold_passes_when_nothing_changed(gold_fixture):
    manifest, course_dir = gold_fixture
    assert verify_gold_manifest(manifest, course_dir) == []


def test_verify_gold_detects_changed_markdown(gold_fixture):
    manifest, course_dir = gold_fixture
    md_path = course_dir / "enade-2021-cc-b-q02.md"
    md_path.write_text(md_path.read_text(encoding="utf-8") + "\ntampered", encoding="utf-8")

    divergences = verify_gold_manifest(manifest, course_dir)
    kinds = {d.kind for d in divergences}
    assert "markdown_hash_mismatch" in kinds


def test_verify_gold_detects_missing_question(gold_fixture):
    manifest, course_dir = gold_fixture
    (course_dir / "enade-2021-cc-b-q02.md").unlink()

    divergences = verify_gold_manifest(manifest, course_dir)
    assert any(d.kind == "missing_question" and "q02" in d.detail for d in divergences)


def test_verify_gold_detects_unexpected_extra_question(gold_fixture):
    manifest, course_dir = gold_fixture
    extra = _question(
        id="enade-2021-cc-b-q99",
        question_number=99,
        source_occurrences=[_occurrence(question_number=99, pages=[9])],
    )
    write_question_markdown(extra, course_dir)

    divergences = verify_gold_manifest(manifest, course_dir)
    assert any(d.kind == "unexpected_extra_question" and "q99" in d.detail for d in divergences)


def test_verify_gold_detects_asset_hash_mismatch(gold_fixture):
    manifest, course_dir = gold_fixture
    asset_path = course_dir / "enade-2021-cc-b-q01" / "figure-01.png"
    asset_path.write_bytes(b"different bytes entirely")

    divergences = verify_gold_manifest(manifest, course_dir)
    assert any(d.kind == "asset_hash_mismatch" for d in divergences)


def test_verify_gold_detects_missing_asset_file(gold_fixture):
    manifest, course_dir = gold_fixture
    (course_dir / "enade-2021-cc-b-q01" / "figure-01.png").unlink()

    divergences = verify_gold_manifest(manifest, course_dir)
    assert any(d.kind == "missing_asset_file" for d in divergences)
