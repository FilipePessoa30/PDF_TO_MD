from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from enade.markdown_format import load_question_markdown
from enade.models.enums import CourseCode
from enade.models.provenance import SourceOccurrence
from enade.models.question import Alternative, Question


def _occurrence(**overrides) -> SourceOccurrence:
    base = dict(
        exam_id="enade-2021-b",
        pdf_sha256="a" * 64,
        source_path="2021/b1_prova.pdf",
        pages=[14],
        question_number=12,
        section="componente-especifico",
    )
    base.update(overrides)
    return SourceOccurrence(**base)


def _question(**overrides) -> Question:
    base = dict(
        id="fixture-q",
        exam_year=2021,
        source_occurrences=[_occurrence()],
        applicable_courses=[CourseCode.CC_BACHARELADO],
        section="componente-especifico",
        question_number=12,
        question_type="multiple_choice",
        statement="Enunciado de teste.",
        alternatives=[Alternative(letter="A", text="a"), Alternative(letter="B", text="b")],
    )
    base.update(overrides)
    return Question(**base)


# --- fixture-file-based tests -------------------------------------------------


@pytest.mark.parametrize(
    "path", sorted((Path(__file__).parent / "fixtures" / "questions" / "valid").glob("*.md"))
)
def test_valid_question_fixtures_pass(path: Path):
    question = load_question_markdown(path)
    assert isinstance(question, Question)


@pytest.mark.parametrize(
    "path", sorted((Path(__file__).parent / "fixtures" / "questions" / "invalid").glob("*.md"))
)
def test_invalid_question_fixtures_fail(path: Path):
    with pytest.raises((ValidationError, ValueError)):
        load_question_markdown(path)


# --- direct model tests: multi-course / multi-occurrence / assets ------------


def test_question_supports_multiple_applicable_courses():
    q = _question(applicable_courses=[CourseCode.CC_BACHARELADO, CourseCode.SISTEMAS_INFORMACAO])
    assert len(q.applicable_courses) == 2


def test_question_all_computing_alone_is_valid():
    q = _question(applicable_courses=[CourseCode.ALL_COMPUTING])
    assert q.applicable_courses == [CourseCode.ALL_COMPUTING]


def test_question_all_computing_combined_with_other_course_is_rejected():
    with pytest.raises(ValidationError, match="all-computing"):
        _question(applicable_courses=[CourseCode.ALL_COMPUTING, CourseCode.SISTEMAS_INFORMACAO])


def test_question_applicable_courses_must_not_be_empty():
    with pytest.raises(ValidationError):
        _question(applicable_courses=[])


def test_question_supports_multiple_source_occurrences():
    q = _question(
        source_occurrences=[_occurrence(), _occurrence(exam_id="enade-2017-b", question_number=14)]
    )
    assert len(q.source_occurrences) == 2


def test_question_requires_at_least_one_source_occurrence():
    with pytest.raises(ValidationError):
        _question(source_occurrences=[])


def test_question_pending_states_are_the_default():
    q = _question()
    assert q.extraction_status.value == "pending"
    assert q.answer_validation_status.value == "pending"
    assert q.taxonomy_review_status.value == "pending"
    assert q.extraction_method.value == "pending"
    assert q.correct_answer is None
    assert q.difficulty is None


def test_discursive_question_must_not_have_alternatives():
    with pytest.raises(ValidationError, match="must not have alternatives"):
        _question(
            question_type="discursive",
            alternatives=[Alternative(letter="A", text="a")],
        )


def test_multiple_choice_question_needs_at_least_two_alternatives():
    with pytest.raises(ValidationError, match="at least 2 alternatives"):
        _question(alternatives=[Alternative(letter="A", text="a")])


def test_duplicate_alternative_letters_are_rejected():
    with pytest.raises(ValidationError, match="repeat a letter"):
        _question(
            alternatives=[Alternative(letter="A", text="a"), Alternative(letter="A", text="a2")]
        )


def test_correct_answer_must_reference_a_declared_alternative():
    # "C" matches the A-E letter pattern but only A/B are declared as alternatives.
    with pytest.raises(ValidationError, match="not one of the declared alternatives"):
        _question(correct_answer="C")


def test_validated_status_requires_a_correct_answer():
    with pytest.raises(ValidationError, match="requires a correct_answer"):
        _question(answer_validation_status="validated", correct_answer=None)


def test_ocr_confidence_requires_ocr_or_hybrid_method():
    with pytest.raises(ValidationError, match="ocr_confidence may only be set"):
        _question(extraction_method="text_layer", ocr_confidence=0.9)

    q = _question(extraction_method="ocr", ocr_confidence=0.42)
    assert q.ocr_confidence == 0.42


def test_alternative_diagnostics_must_reference_a_declared_alternative():
    # "C" matches the A-E letter pattern but only A/B are declared as alternatives.
    with pytest.raises(ValidationError, match="undeclared alternative"):
        _question(alternative_diagnostics={"C": {"misconception_id": "some-misconception"}})


def test_alternative_diagnostics_must_not_target_the_correct_answer():
    with pytest.raises(ValidationError, match="must not target the correct answer"):
        _question(
            correct_answer="A",
            answer_validation_status="validated",
            alternative_diagnostics={"A": {"misconception_id": "some-misconception"}},
        )


def test_duplicate_asset_ids_are_rejected():
    with pytest.raises(ValidationError, match="repeat an id"):
        _question(
            assets=[
                {"id": "figure-01", "type": "image", "path": "a.png", "source_page": 1},
                {"id": "figure-01", "type": "image", "path": "b.png", "source_page": 2},
            ]
        )


def test_question_id_must_be_kebab_case():
    with pytest.raises(ValidationError, match="kebab-case"):
        _question(id="Not Valid ID")
