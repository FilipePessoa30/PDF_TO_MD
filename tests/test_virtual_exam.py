from __future__ import annotations

from enade.models.enums import CourseCode
from enade.models.provenance import SourceOccurrence
from enade.models.question import Alternative, Question
from enade.virtual_exam import materialize_virtual_exam_set, validate_virtual_exam_set


def _occurrence(number: int, section: str) -> SourceOccurrence:
    return SourceOccurrence(
        exam_id="enade-2011-unificado",
        pdf_sha256="a" * 64,
        source_path="2011/1_prova.pdf",
        pages=[number],
        question_number=number,
        section=section,
    )


def _objective(number: int, courses: list[CourseCode], section: str = "sec") -> Question:
    return Question(
        id=f"enade-2011-computing-q{number:02d}",
        exam_year=2011,
        source_occurrences=[_occurrence(number, section)],
        applicable_courses=courses,
        section=section,
        question_number=number,
        question_type="multiple_choice",
        statement="Enunciado de teste suficientemente longo para passar na validação mínima.",
        alternatives=[Alternative(letter="A", text="a"), Alternative(letter="B", text="b")],
        correct_answer="A",
        answer_validation_status="validated",
    )


def _discursive(number: int, courses: list[CourseCode], section: str = "sec-disc") -> Question:
    return Question(
        id=f"enade-2011-computing-d{number:02d}",
        exam_year=2011,
        source_occurrences=[_occurrence(number, section)],
        applicable_courses=courses,
        section=section,
        question_number=number,
        question_type="discursive",
        statement="Enunciado discursivo de teste suficientemente longo para passar na validação.",
        alternatives=[],
        answer_validation_status="not_applicable",
    )


def _bank() -> dict[str, Question]:
    questions: dict[str, Question] = {}
    for n in range(1, 6):
        q = _objective(n, [CourseCode.ALL_COMPUTING])
        questions[q.id] = q
    for n in range(1, 3):
        d = _discursive(n, [CourseCode.ALL_COMPUTING])
        questions[d.id] = d
    for n in range(31, 34):
        q = _objective(n, [CourseCode.CC_LICENCIATURA])
        questions[q.id] = q
    for n in range(36, 39):
        q = _objective(n, [CourseCode.CC_BACHARELADO])
        questions[q.id] = q
    return questions


def test_materialize_includes_shared_and_course_specific_questions():
    bank = _bank()
    exam_set = materialize_virtual_exam_set(bank, CourseCode.CC_LICENCIATURA)
    numbers = [q.question_number for q in exam_set.objectives]
    assert numbers == [1, 2, 3, 4, 5, 31, 32, 33]
    assert [q.question_number for q in exam_set.discursives] == [1, 2]
    assert exam_set.total == 10


def test_materialize_excludes_other_courses_specific_questions():
    bank = _bank()
    exam_set = materialize_virtual_exam_set(bank, CourseCode.CC_LICENCIATURA)
    assert all(q.question_number not in (36, 37, 38) for q in exam_set.objectives)


def test_materialize_is_a_view_not_a_copy():
    bank = _bank()
    lic = materialize_virtual_exam_set(bank, CourseCode.CC_LICENCIATURA)
    cc = materialize_virtual_exam_set(bank, CourseCode.CC_BACHARELADO)
    shared_lic = {q.id for q in lic.objectives if q.question_number <= 5}
    shared_cc = {q.id for q in cc.objectives if q.question_number <= 5}
    assert shared_lic == shared_cc  # same canonical question objects, no duplication


def test_validate_reports_wrong_counts():
    bank = _bank()
    exam_set = materialize_virtual_exam_set(bank, CourseCode.CC_LICENCIATURA)
    issues = validate_virtual_exam_set(exam_set, expected_objectives=35, expected_discursives=5)
    kinds = {i.kind for i in issues}
    assert "wrong_objective_count" in kinds
    assert "wrong_discursive_count" in kinds


def test_validate_passes_for_correctly_sized_set():
    bank = _bank()
    exam_set = materialize_virtual_exam_set(bank, CourseCode.CC_LICENCIATURA)
    issues = validate_virtual_exam_set(exam_set, expected_objectives=8, expected_discursives=2)
    assert issues == []


def test_validate_detects_out_of_order_questions():
    bank = _bank()
    exam_set = materialize_virtual_exam_set(bank, CourseCode.CC_LICENCIATURA)
    scrambled = exam_set.__class__(
        course=exam_set.course,
        objectives=tuple(reversed(exam_set.objectives)),
        discursives=exam_set.discursives,
    )
    issues = validate_virtual_exam_set(scrambled, expected_objectives=8, expected_discursives=2)
    assert any(i.kind == "out_of_order" for i in issues)


def test_validate_detects_cross_course_contamination():
    bank = _bank()
    # A question explicitly naming another course should never appear in a
    # different course's own materialized set in the first place, but the
    # validator must also catch it if it somehow does.
    contaminated = _objective(99, [CourseCode.CC_LICENCIATURA, CourseCode.SISTEMAS_INFORMACAO])
    bank[contaminated.id] = contaminated
    exam_set = materialize_virtual_exam_set(bank, CourseCode.CC_LICENCIATURA)
    issues = validate_virtual_exam_set(exam_set, expected_objectives=9, expected_discursives=2)
    assert any(i.kind == "cross_course_contamination" for i in issues)
