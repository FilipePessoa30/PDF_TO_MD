"""Materialize the "virtual exam" each student of a unified booklet actually sees.

PROMPT Phase 2A section 9: the 2011 caderno stores 55 *canonical* questions
(50 objective + 5 discursive), but no single student ever answers all 55 -
each of the four courses sharing the booklet answers exactly the questions
``all-computing`` shares plus its own course-specific block. This module
reconstructs that per-course view from the canonical corpus without
duplicating any question - it is a read-only filter/view, never a second
copy of the data.
"""

from __future__ import annotations

from dataclasses import dataclass

from enade.models.enums import CourseCode, QuestionType
from enade.models.question import Question


@dataclass(frozen=True)
class VirtualExamSet:
    course: CourseCode
    objectives: tuple[Question, ...]
    discursives: tuple[Question, ...]

    @property
    def total(self) -> int:
        return len(self.objectives) + len(self.discursives)


def materialize_virtual_exam_set(
    questions: dict[str, Question], course: CourseCode
) -> VirtualExamSet:
    """Filter the canonical question bank down to one course's own exam.

    A question is included if ``course`` is directly in its
    ``applicable_courses`` or if the question is shared via the
    ``all-computing`` alias. Objectives and discursives are each returned
    sorted by ``question_number`` - the corpus's own canonical order, not a
    guess (PROMPT: "ordem oficial e preservada").
    """
    applicable = [
        q
        for q in questions.values()
        if course in q.applicable_courses or CourseCode.ALL_COMPUTING in q.applicable_courses
    ]
    objectives = tuple(
        sorted(
            (q for q in applicable if q.question_type == QuestionType.MULTIPLE_CHOICE),
            key=lambda q: q.question_number,
        )
    )
    discursives = tuple(
        sorted(
            (q for q in applicable if q.question_type == QuestionType.DISCURSIVE),
            key=lambda q: q.question_number,
        )
    )
    return VirtualExamSet(course=course, objectives=objectives, discursives=discursives)


@dataclass(frozen=True)
class VirtualExamSetIssue:
    kind: str
    detail: str


def validate_virtual_exam_set(
    exam_set: VirtualExamSet,
    *,
    expected_objectives: int,
    expected_discursives: int,
) -> list[VirtualExamSetIssue]:
    """Check a materialized set for the invariants PROMPT section 9 requires.

    Never raises - returns every violation found, so a caller can report
    all of them at once rather than stopping at the first.
    """
    issues: list[VirtualExamSetIssue] = []

    if len(exam_set.objectives) != expected_objectives:
        issues.append(
            VirtualExamSetIssue(
                "wrong_objective_count",
                f"{exam_set.course.value}: {len(exam_set.objectives)} objectives, "
                f"expected {expected_objectives}",
            )
        )
    if len(exam_set.discursives) != expected_discursives:
        issues.append(
            VirtualExamSetIssue(
                "wrong_discursive_count",
                f"{exam_set.course.value}: {len(exam_set.discursives)} discursives, "
                f"expected {expected_discursives}",
            )
        )

    for group_name, group in (
        ("objectives", exam_set.objectives),
        ("discursives", exam_set.discursives),
    ):
        numbers = [q.question_number for q in group]
        if len(set(numbers)) != len(numbers):
            duplicates = sorted({n for n in numbers if numbers.count(n) > 1})
            issues.append(
                VirtualExamSetIssue(
                    "duplicate_question",
                    f"{exam_set.course.value} {group_name}: duplicate number(s) {duplicates}",
                )
            )
        if numbers != sorted(numbers):
            issues.append(
                VirtualExamSetIssue(
                    "out_of_order",
                    f"{exam_set.course.value} {group_name}: not in ascending question_number order",
                )
            )

    for q in exam_set.objectives + exam_set.discursives:
        other_explicit = {
            c
            for c in q.applicable_courses
            if c != CourseCode.ALL_COMPUTING and c != exam_set.course
        }
        if other_explicit:
            issues.append(
                VirtualExamSetIssue(
                    "cross_course_contamination",
                    f"{exam_set.course.value}: {q.id} also explicitly names "
                    f"{sorted(c.value for c in other_explicit)}",
                )
            )

    return issues
