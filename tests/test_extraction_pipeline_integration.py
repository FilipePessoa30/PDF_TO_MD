"""End-to-end integration tests against the real 2021 CC bacharelado booklet.

Building a full synthetic 40-question exam booklet (two-column pages,
monospace code, embedded images, multi-page questions, a real gabarito/
padrao trio) to exercise the pipeline end-to-end would not meaningfully
test anything the unit tests in tests/test_extraction_*.py don't already
cover in isolation, and risks testing the fixture instead of reality. This
suite instead runs the real pipeline against the real, locally-cached
corpus (see PROMPT section 28: "Use questoes reais somente quando
necessario e mantenha rastreabilidade") and asserts the structural
invariants Phase 1A's acceptance criteria actually depend on. It is
skipped (not failed) when the corpus cache is not present, so the rest of
the suite still runs in an environment that hasn't fetched it.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from enade.extraction.pipeline import extract_exam
from enade.markdown_format import load_questions_directory
from enade.models.enums import CourseCode, ExtractionStatus

CORPUS_ROOT = Path(__file__).parent.parent / "data" / "raw" / "geacc-enade"
PROVA_PATH = CORPUS_ROOT / "2021" / "b1_prova.pdf"
GABARITO_PATH = CORPUS_ROOT / "2021" / "b2_gabarito.pdf"
PADRAO_PATH = CORPUS_ROOT / "2021" / "b3_padrao.pdf"

pytestmark = pytest.mark.skipif(
    not PROVA_PATH.exists(),
    reason="geacc/enade corpus not cloned locally (run scripts/fetch_corpus.py)",
)


@pytest.fixture(scope="module")
def extraction_result(tmp_path_factory: pytest.TempPathFactory):
    out_dir = tmp_path_factory.mktemp("pipeline_integration")
    return extract_exam(
        prova_path=PROVA_PATH,
        gabarito_path=GABARITO_PATH,
        padrao_path=PADRAO_PATH,
        corpus_root=CORPUS_ROOT,
        exam_year=2021,
        course=CourseCode.CC_BACHARELADO,
        exam_id="enade-2021-b",
        questions_output_dir=out_dir / "questions",
        assets_output_dir=out_dir / "assets",
    ), out_dir


def test_finds_exactly_the_documented_structure(extraction_result):
    result, _ = extraction_result
    m = result.metrics
    assert m.objectives_found == 35
    assert m.discursives_found == 5
    assert m.questions_found == 40
    assert result.excluded_perception_pages == [44]


def test_no_duplicate_question_ids(extraction_result):
    result, _ = extraction_result
    ids = [q.id for q in result.questions]
    assert len(ids) == len(set(ids))


def test_every_question_id_follows_the_documented_convention(extraction_result):
    result, _ = extraction_result
    for q in result.questions:
        assert q.id.startswith("enade-2021-cc-b-")
        assert q.id[-2:].isdigit()


def test_all_objective_answers_are_linked_from_the_real_gabarito(extraction_result):
    result, _ = extraction_result
    objectives = [q for q in result.questions if q.question_type.value == "multiple_choice"]
    assert len(objectives) == 35
    for q in objectives:
        assert q.answer_validation_status.value in ("validated", "annulled")
        if q.answer_validation_status.value == "validated":
            assert q.correct_answer in {"A", "B", "C", "D", "E"}


def test_annulled_questions_29_and_33_have_no_correct_answer(extraction_result):
    result, _ = extraction_result
    by_number = {
        q.question_number: q for q in result.questions if q.question_type.value == "multiple_choice"
    }
    for number in (29, 33):
        assert by_number[number].answer_validation_status.value == "annulled"
        assert by_number[number].correct_answer is None


def test_all_discursive_questions_have_an_answer_standard_linked(extraction_result):
    result, _ = extraction_result
    discursives = [q for q in result.questions if q.question_type.value == "discursive"]
    assert len(discursives) == 5
    for q in discursives:
        assert q.answer_standard is not None
        assert q.answer_standard.text.strip()
        assert q.answer_standard.source_path == "2021/b3_padrao.pdf"


def test_source_pages_are_within_the_prova_page_range(extraction_result):
    result, _ = extraction_result
    for q in result.questions:
        occurrence = q.source_occurrences[0]
        assert occurrence.source_path == "2021/b1_prova.pdf"
        assert all(1 <= p <= 48 for p in occurrence.pages)
        assert occurrence.pdf_sha256 == result.questions[0].source_occurrences[0].pdf_sha256


def test_asset_files_exist_and_hashes_match(extraction_result):
    result, out_dir = extraction_result
    any_assets = False
    for q in result.questions:
        for asset in q.assets:
            any_assets = True
            asset_path = out_dir / "assets" / asset.path
            assert asset_path.exists()
            import hashlib

            assert hashlib.sha256(asset_path.read_bytes()).hexdigest() == asset.sha256
    assert any_assets  # sanity: this booklet does have figures


def test_written_markdown_round_trips_through_the_loader(extraction_result):
    result, out_dir = extraction_result
    questions_dir = out_dir / "questions" / "2021" / "ciencia-da-computacao-bacharelado"
    loaded = load_questions_directory(questions_dir)
    assert len(loaded) == 40
    for q in result.questions:
        assert loaded[q.id].statement == q.statement
        assert loaded[q.id].correct_answer == q.correct_answer


def test_needs_review_never_silently_becomes_verified(extraction_result):
    result, _ = extraction_result
    # Every question flagged with warnings must be needs_review, never verified.
    for q in result.questions:
        warnings = result.per_question_warnings.get(q.id, [])
        if warnings:
            assert q.extraction_status == ExtractionStatus.NEEDS_REVIEW
        else:
            assert q.extraction_status == ExtractionStatus.VERIFIED


def test_pipeline_is_idempotent_on_a_second_run_over_unchanged_source(extraction_result, tmp_path):
    _, out_dir = extraction_result
    # Re-run into the SAME output directories used by the module-scoped fixture.
    second = extract_exam(
        prova_path=PROVA_PATH,
        gabarito_path=GABARITO_PATH,
        padrao_path=PADRAO_PATH,
        corpus_root=CORPUS_ROOT,
        exam_year=2021,
        course=CourseCode.CC_BACHARELADO,
        exam_id="enade-2021-b",
        questions_output_dir=out_dir / "questions",
        assets_output_dir=out_dir / "assets",
    )
    assert second.metrics.files_written == 0
    assert second.metrics.files_unchanged == 40
