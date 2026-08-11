from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from enade.extraction.markdown_writer import write_question_markdown
from enade.gold import (
    GoldMaturity,
    build_gold_manifest,
    read_gold_manifest,
    verify_gold_manifest,
    write_gold_manifest,
)
from enade.models.asset import Asset
from enade.models.enums import CourseCode
from enade.models.provenance import AnswerStandardReference, SourceOccurrence
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


# --- Phase 1C: maturity/status, counts, data-contract version (section 13) ---


def test_gold_manifest_defaults_to_provisional_maturity(gold_fixture):
    manifest, _ = gold_fixture
    assert manifest.maturity == GoldMaturity.PROVISIONAL.value


def test_gold_manifest_records_verified_and_needs_review_counts(gold_fixture):
    manifest, _ = gold_fixture
    assert manifest.verified_count == 1  # q01
    assert manifest.needs_review_count == 1  # q02
    assert manifest.unresolved_question_ids == ("enade-2021-cc-b-q02",)


def test_gold_manifest_carries_data_contract_and_pipeline_versions(gold_fixture):
    manifest, _ = gold_fixture
    assert manifest.data_contract_version
    assert manifest.pipeline_version


def test_build_gold_manifest_accepts_explicit_maturity_and_blockers(tmp_path):
    course_dir = tmp_path / "questions" / "2021" / "ciencia-da-computacao-bacharelado"
    course_dir.mkdir(parents=True)
    write_question_markdown(_question(), course_dir)
    prova_path, gabarito_path, padrao_path = (tmp_path / n for n in ("p.pdf", "g.pdf", "s.pdf"))
    for p in (prova_path, gabarito_path, padrao_path):
        p.write_bytes(b"fake")

    manifest = build_gold_manifest(
        exam_id="enade-2021-b",
        exam_year=2021,
        course="ciencia-da-computacao-bacharelado",
        corpus_commit="deadbeef" * 5,
        prova_path=prova_path,
        gabarito_path=gabarito_path,
        padrao_path=padrao_path,
        course_dir=course_dir,
        maturity=GoldMaturity.VALIDATED,
        structural_blockers=("enade-2021-cc-b-d03",),
    )
    assert manifest.maturity == GoldMaturity.VALIDATED.value
    assert manifest.structural_blockers == ("enade-2021-cc-b-d03",)


def test_gold_manifest_maturity_and_counts_round_trip(gold_fixture, tmp_path):
    manifest, _ = gold_fixture
    path = tmp_path / "gold.json"
    write_gold_manifest(manifest, path)
    loaded = read_gold_manifest(path)
    assert loaded == manifest
    assert loaded.maturity == manifest.maturity
    assert loaded.verified_count == manifest.verified_count
    assert loaded.unresolved_question_ids == manifest.unresolved_question_ids


# --- Phase 1C: answer_standard text/assets coverage (section 15) -------------


@pytest.fixture
def gold_fixture_with_answer_standard(tmp_path: Path):
    course_dir = tmp_path / "questions" / "2021" / "ciencia-da-computacao-bacharelado"
    course_dir.mkdir(parents=True)

    png_bytes = b"\x89PNG\r\n\x1a\nfake padrao diagram bytes"
    asset_dir = course_dir / "enade-2021-cc-b-d04" / "answer-standard"
    asset_dir.mkdir(parents=True)
    (asset_dir / "padrao-01.png").write_bytes(png_bytes)
    asset_sha256 = hashlib.sha256(png_bytes).hexdigest()

    d04 = _question(
        id="enade-2021-cc-b-d04",
        question_number=4,
        question_type="discursive",
        alternatives=[],
        source_occurrences=[_occurrence(question_number=4, pages=[16])],
        answer_standard=AnswerStandardReference(
            source_path="2021/b3_padrao.pdf",
            pdf_sha256="b" * 64,
            pages=[5, 6],
            text="O respondente deve descrever a tabela verdade e desenhar o diagrama.",
            assets=[
                Asset(
                    id="padrao-01",
                    type="diagram",
                    path="enade-2021-cc-b-d04/answer-standard/padrao-01.png",
                    source_page=5,
                    extraction_method="raster_crop",
                    sha256=asset_sha256,
                )
            ],
        ),
    )
    write_question_markdown(d04, course_dir)

    prova_path, gabarito_path, padrao_path = (tmp_path / n for n in ("p.pdf", "g.pdf", "s.pdf"))
    for p in (prova_path, gabarito_path, padrao_path):
        p.write_bytes(b"fake")

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


def test_gold_manifest_covers_answer_standard_text_and_assets(gold_fixture_with_answer_standard):
    manifest, _ = gold_fixture_with_answer_standard
    assert len(manifest.answer_standards) == 1
    entry = manifest.answer_standards[0]
    assert entry.question_id == "enade-2021-cc-b-d04"
    assert entry.pages == (5, 6)
    assert len(entry.assets) == 1
    assert entry.assets[0].id == "padrao-01"


def test_verify_gold_passes_when_answer_standard_unchanged(gold_fixture_with_answer_standard):
    manifest, course_dir = gold_fixture_with_answer_standard
    assert verify_gold_manifest(manifest, course_dir) == []


def test_verify_gold_detects_tampered_answer_standard_asset(gold_fixture_with_answer_standard):
    manifest, course_dir = gold_fixture_with_answer_standard
    asset_path = course_dir / "enade-2021-cc-b-d04" / "answer-standard" / "padrao-01.png"
    asset_path.write_bytes(b"tampered padrao asset bytes")

    divergences = verify_gold_manifest(manifest, course_dir)
    assert any(d.kind == "answer_standard_asset_hash_mismatch" for d in divergences)


def test_verify_gold_detects_missing_answer_standard_asset_file(gold_fixture_with_answer_standard):
    manifest, course_dir = gold_fixture_with_answer_standard
    (course_dir / "enade-2021-cc-b-d04" / "answer-standard" / "padrao-01.png").unlink()

    divergences = verify_gold_manifest(manifest, course_dir)
    assert any(d.kind == "missing_answer_standard_asset_file" for d in divergences)


def test_verify_gold_detects_answer_standard_text_tampering(gold_fixture_with_answer_standard):
    manifest, course_dir = gold_fixture_with_answer_standard
    md_path = course_dir / "enade-2021-cc-b-d04.md"
    tampered = md_path.read_text(encoding="utf-8").replace(
        "descrever a tabela verdade", "descrever a tabela verdade FALSIFICADA"
    )
    md_path.write_text(tampered, encoding="utf-8")

    divergences = verify_gold_manifest(manifest, course_dir)
    kinds = {d.kind for d in divergences}
    # Tampering the .md file also changes its own hash - both the whole-file
    # and the answer-standard-specific text check must independently notice.
    assert "markdown_hash_mismatch" in kinds
    assert "answer_standard_text_mismatch" in kinds


def test_verify_gold_answer_standard_assets_never_collide_with_question_assets(
    gold_fixture_with_answer_standard,
):
    manifest, _ = gold_fixture_with_answer_standard
    entry = manifest.answer_standards[0]
    question_entry = next(q for q in manifest.questions if q.id == entry.question_id)
    assert question_entry.assets == ()  # d04 itself has no question-level asset in this fixture
    assert len(entry.assets) == 1
