"""End-to-end integration tests against the real 2008-b unified booklet
(PROMPT Phase 3A/3B).

Same rationale as test_extraction_pipeline_integration.py's own docstring:
runs the real pipeline against the real, locally-cached corpus rather than a
synthetic fixture, and is skipped (not failed) when that corpus is not
present. This suite's own reason for existing is narrower and more
pointed - it is the regression test for the Phase 3B ownership/chrome fixes
that resolved the Q21/Q22/Q23 cross-question contamination (see
docs/phase-3b-report.md, section G): a single question that the data
contract refuses to build (Q8/Q38/Q55's own unstructured image
alternatives) must not derail the whole extraction, and a region that only
looks close to Q21 or Q23 must never be attributed to them just because it
sits nearby.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from enade.extraction.answer_key import parse_flat_item_gabarito
from enade.extraction.exam_profile import _RANGE_PATTERNS_2008_B, load_exam_structure_profile
from enade.extraction.pipeline import extract_exam
from enade.models.enums import QuestionType

CORPUS_ROOT = Path(__file__).parent.parent / "data" / "raw" / "geacc-enade"
PROVA_PATH = CORPUS_ROOT / "2008" / "b1_prova.pdf"
GABARITO_PATH = CORPUS_ROOT / "2008" / "b2_gabarito.pdf"
PADRAO_PATH = CORPUS_ROOT / "2008" / "b3_padrao.pdf"
PROFILE_PATH = Path(__file__).parent.parent / "data" / "manifests" / "exam-structure-2008.yaml"

pytestmark = pytest.mark.skipif(
    not PROVA_PATH.exists(),
    reason="geacc/enade corpus not cloned locally (run scripts/fetch_corpus.py)",
)


@pytest.fixture(scope="module")
def extraction_result(tmp_path_factory: pytest.TempPathFactory):
    out_dir = tmp_path_factory.mktemp("pipeline_2008_integration")
    profile = load_exam_structure_profile(PROFILE_PATH)
    result = extract_exam(
        prova_path=PROVA_PATH,
        gabarito_path=GABARITO_PATH,
        padrao_path=PADRAO_PATH,
        corpus_root=CORPUS_ROOT,
        exam_year=2008,
        exam_id=profile.exam_id,
        questions_output_dir=out_dir / "questions",
        structure_profile=profile,
        structure_verification_page=11,
        structure_verification_patterns=_RANGE_PATTERNS_2008_B,
        output_dir_name="all-computing",
        answer_key_parser=parse_flat_item_gabarito,
    )
    return result, out_dir


def test_all_80_academic_questions_are_accounted_for(extraction_result):
    """77 published + 3 explicitly excluded (unstructured image
    alternatives, PROMPT Phase 3A) = 80 - never silently fewer.
    """
    result, _ = extraction_result
    published_ids = {q.id for q in result.questions}
    assert len(published_ids) == 77
    for excluded_number in (8, 38, 55):
        exclusion_note = f"objective {excluded_number}: could not build a valid Question"
        assert any(exclusion_note in w for w in result.structural_warnings), (
            f"objective {excluded_number} must be loudly excluded, not silently missing"
        )


def test_q21_statement_is_complete_and_uncontaminated(extraction_result):
    result, _ = extraction_result
    questions_by_number = {
        q.question_number: q
        for q in result.questions
        if q.question_type == QuestionType.MULTIPLE_CHOICE
    }
    q21 = questions_by_number[21]
    assert "EMPREGADO" in q21.statement
    assert "sobrenome" in q21.statement
    assert "Árvore-B+" in q21.statement
    # Never contains Q22's or Q23's own real content (PROMPT Phase 3B
    # section 12 - the exact bug this test exists to catch: Q21's own
    # rendered figure/statement previously included the entirety of Q22
    # and part of Q23).
    assert "tradutor" not in q21.statement  # Q22's own statement
    assert "EMPREGADO" not in q21.statement or "Pessoa" not in q21.statement  # Q23 uses "Pessoa"
    assert "banco de dados relacional" not in q21.statement  # Q23's own opening


def test_q22_statement_is_complete_and_not_lost(extraction_result):
    result, _ = extraction_result
    questions_by_number = {
        q.question_number: q
        for q in result.questions
        if q.question_type == QuestionType.MULTIPLE_CHOICE
    }
    q22 = questions_by_number[22]
    assert "software tradutor" in q22.statement
    assert "velocidade de execução" in q22.statement
    # Never contaminated by the page-11 instructions table this bug used to
    # leak (PROMPT Phase 3B section D/M).
    assert "Número das Questões" not in q22.statement
    assert "21 a 38" not in q22.statement


def test_q23_statement_is_complete_and_uncontaminated(extraction_result):
    result, _ = extraction_result
    questions_by_number = {
        q.question_number: q
        for q in result.questions
        if q.question_type == QuestionType.MULTIPLE_CHOICE
    }
    q23 = questions_by_number[23]
    assert "banco de dados relacional" in q23.statement
    assert "Pessoa" in q23.statement
    # Never contains Q21's own content.
    assert "EMPREGADO" not in q23.statement
    assert "sobrenome" not in q23.statement
