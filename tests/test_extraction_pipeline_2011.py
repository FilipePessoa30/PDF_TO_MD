"""Focused end-to-end regression test(s) against the real 2011 unified
booklet (PROMPT Phase 3I).

Narrower in scope than test_extraction_pipeline_2008.py/
test_extraction_pipeline_integration.py on purpose: 2011's own corpus is
gold-locked and protected (see docs/phase-3i-report.md) - this file exists
only to pin the one real regression this phase found and fixed against it,
not to duplicate a full integration suite. Skipped (not failed) when the
corpus is not present, matching the established pattern.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from enade.extraction.exam_profile import load_exam_structure_profile
from enade.extraction.pipeline import extract_exam
from enade.models.enums import QuestionType

CORPUS_ROOT = Path(__file__).parent.parent / "data" / "raw" / "geacc-enade"
PROVA_PATH = CORPUS_ROOT / "2011" / "1_prova.pdf"
GABARITO_PATH = CORPUS_ROOT / "2011" / "2_gabarito.pdf"
PADRAO_PATH = CORPUS_ROOT / "2011" / "3_padrao.pdf"
PROFILE_PATH = Path(__file__).parent.parent / "data" / "manifests" / "exam-structure-2011.yaml"

pytestmark = pytest.mark.skipif(
    not PROVA_PATH.exists(),
    reason="geacc/enade corpus not cloned locally (run scripts/fetch_corpus.py)",
)


@pytest.fixture(scope="module")
def extraction_result(tmp_path_factory: pytest.TempPathFactory):
    out_dir = tmp_path_factory.mktemp("pipeline_2011_regression")
    profile = load_exam_structure_profile(PROFILE_PATH)
    result = extract_exam(
        prova_path=PROVA_PATH,
        gabarito_path=GABARITO_PATH,
        padrao_path=PADRAO_PATH,
        corpus_root=CORPUS_ROOT,
        exam_year=2011,
        exam_id=profile.exam_id,
        questions_output_dir=out_dir / "questions",
        structure_profile=profile,
        output_dir_name="all-computing",
    )
    return result


def test_q39_alternatives_are_not_regressed_by_the_horizontal_grid_shape(extraction_result):
    """Real regression found and fixed this phase (PROMPT Phase 3I,
    alternative_groups._reference_margin): Q39's own five alternatives are
    laid out horizontally on one row ("A I.  B II.  C I e III. ..."), each
    at its own genuinely distinct x0 - no shared margin exists at all. A
    naive mode computation without a minimum-vote requirement mistook a
    single-occurrence x0 (coincidentally the *first-collected* letter's
    own false candidate - a judged item's own text starting with the
    capitalized word "A especificação...") as if it were a real,
    consensus-backed margin, wrongly preferring it over the real, later
    marker and corrupting both the statement and alternative A. Requiring
    at least two real votes before trusting the mode fixes this without
    reopening the Q71/Q28/Q52 fixes this same mechanism exists for.
    """
    result = extraction_result
    questions_by_number = {
        q.question_number: q
        for q in result.questions
        if q.question_type == QuestionType.MULTIPLE_CHOICE
    }
    q39 = questions_by_number[39]
    assert q39.statement.endswith("É correto apenas o que se afirma em")
    alternative_a = next(a for a in q39.alternatives if a.letter == "A")
    assert alternative_a.text == "I."


def test_q23_alternative_e_trailing_period_after_inline_formula_is_preserved(extraction_result):
    """Preservation test (PROMPT Phase 3M): Q23's own alternative E ends
    with an inline "expressao regular" formula image followed by a lone
    "." sitting ~150pt to the right of alternative E's own marker,
    immediately after that inline image. ``assembler._in_alternatives_
    section`` was narrowed this phase to stop granting its own blanket
    exemption to a line inside a *large* diagram/photo region disjoint
    from the alternative sequence (fixing 2008-b Q75's own diagram-label
    bleed) - this period must stay exempted regardless, since it never
    touches a large region at all, only its own small-formula asset
    (``_attach_alternative_formula_regions`` decides that asset's own
    attachment, not this exemption).
    """
    result = extraction_result
    questions_by_number = {
        q.question_number: q
        for q in result.questions
        if q.question_type == QuestionType.MULTIPLE_CHOICE
    }
    q23 = questions_by_number[23]
    alternative_e = next(a for a in q23.alternatives if a.letter == "E")
    assert alternative_e.text.endswith(".")
    assert "representada pela expressão regular" in alternative_e.text
