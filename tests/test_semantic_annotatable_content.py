"""Anti-leakage tests (PROMPT Fase 5A section 16/26): the semantic
annotation pipeline must never receive the answer key.
"""

from __future__ import annotations

import dataclasses

import pytest

from enade.markdown_format import load_question_markdown
from enade.semantic.annotatable_content import (
    AnnotatableAlternative,
    AnnotatableContent,
    extract_annotatable_content,
)


@pytest.fixture
def sample_question(tmp_path):
    from enade.markdown_format import render_question_markdown
    from enade.models.enums import AnswerValidationStatus, CourseCode, QuestionType
    from enade.models.provenance import SourceOccurrence
    from enade.models.question import Alternative, Question

    question = Question(
        id="enade-2099-computing-q01",
        exam_year=2099,
        source_occurrences=[
            SourceOccurrence(
                exam_id="enade-2099-computing",
                pdf_sha256="0" * 64,
                source_path="2099/b1_prova.pdf",
                pages=[1],
                question_number=1,
                section="componente-especifico-objetiva",
            )
        ],
        applicable_courses=[CourseCode.ALL_COMPUTING],
        section="componente-especifico-objetiva",
        question_number=1,
        question_type=QuestionType.MULTIPLE_CHOICE,
        statement="A pergunta de teste.",
        alternatives=[
            Alternative(letter="A", text="Primeira alternativa."),
            Alternative(letter="B", text="Segunda alternativa."),
        ],
        correct_answer="B",
        official_answer_source="2099/b2_gabarito.pdf",
        answer_validation_status=AnswerValidationStatus.VALIDATED,
    )
    path = tmp_path / f"{question.id}.md"
    path.write_text(render_question_markdown(question), encoding="utf-8")
    return load_question_markdown(path)


def test_annotatable_content_type_has_no_answer_key_field_at_all():
    # Type-level guarantee, not a runtime filter: an annotator cannot
    # read what does not exist on the object, even by mistake.
    field_names = {f.name for f in dataclasses.fields(AnnotatableContent)}
    leaking_names = {
        "correct_answer",
        "answer_standard",
        "official_answer_source",
        "answer_validation_status",
        "gabarito",
    }
    assert field_names.isdisjoint(leaking_names)


def test_annotatable_alternative_type_has_no_correctness_field():
    field_names = {f.name for f in dataclasses.fields(AnnotatableAlternative)}
    assert "is_correct" not in field_names
    assert "correct" not in field_names


def test_extract_annotatable_content_preserves_visible_content(sample_question):
    content = extract_annotatable_content(sample_question)
    assert content.question_id == "enade-2099-computing-q01"
    assert content.statement == "A pergunta de teste."
    assert [a.letter for a in content.alternatives] == ["A", "B"]
    assert [a.text for a in content.alternatives] == [
        "Primeira alternativa.",
        "Segunda alternativa.",
    ]


def test_extract_annotatable_content_never_exposes_the_correct_answer(sample_question):
    # sample_question.correct_answer == "B" - confirm the real Question
    # actually carries it (the fixture is meaningful), then confirm the
    # extracted content has no way to reveal it.
    assert sample_question.correct_answer == "B"
    content = extract_annotatable_content(sample_question)
    assert not hasattr(content, "correct_answer")
    assert not hasattr(content, "answer_standard")
    assert not hasattr(content, "official_answer_source")
    assert not hasattr(content, "answer_validation_status")


def test_extract_annotatable_content_repr_never_contains_the_correct_letter_marked_as_such(
    sample_question,
):
    content = extract_annotatable_content(sample_question)
    # Both letters are legitimately visible (A and B are printed on the
    # exam) - the leak this guards against is a *correctness* marker
    # anywhere in the object, never the mere existence of the letter "B".
    rendered = repr(content)
    assert "correct" not in rendered.lower()
