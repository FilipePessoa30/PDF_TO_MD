"""The anti-leakage boundary for semantic annotation (PROMPT Fase 5A
section 16).

``AnnotatableContent`` is a type-level guarantee, not a runtime filter:
it structurally has no field that could carry ``correct_answer``,
``answer_standard``, ``official_answer_source`` or
``answer_validation_status`` - there is no attribute on this dataclass an
annotator (human or automated) could read to learn the answer, even by
mistake, because the class was never given one. ``extract_annotatable_content``
is the *only* place a :class:`~enade.models.question.Question` is allowed
to cross into the annotation pipeline; every other function in
``enade.semantic`` takes an ``AnnotatableContent``, never a ``Question``.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from enade.models.asset import Asset
from enade.models.content_block import ContentBlock
from enade.models.question import Question


@dataclass(frozen=True)
class AnnotatableAlternative:
    """Everything a student sees on one alternative - the letter and its
    own text/asset are visible to every test-taker; nothing here reveals
    which letter is correct.
    """

    letter: str
    text: str
    asset: Asset | None
    content_blocks: tuple[ContentBlock, ...] | None


@dataclass(frozen=True)
class AnnotatableContent:
    """Exactly what a student sees before answering - never the gabarito,
    never the padrao de resposta, never which alternative (if any) is
    correct. Deliberately has no ``correct_answer``/``answer_standard``/
    ``official_answer_source``/``answer_validation_status`` field at all.
    """

    question_id: str
    exam_year: int
    section: str
    question_type: str
    statement: str
    content_blocks: tuple[ContentBlock, ...] | None
    alternatives: tuple[AnnotatableAlternative, ...]
    assets: tuple[Asset, ...]
    applicable_courses: tuple[str, ...] = field(default_factory=tuple)


def extract_annotatable_content(question: Question) -> AnnotatableContent:
    """The one, single crossing point from the full :class:`Question`
    (which *does* carry the answer key) into the annotation pipeline.
    Reads only the fields a student would see before answering - never
    ``correct_answer``, ``answer_standard``, ``official_answer_source``,
    or ``answer_validation_status``, all of which exist on ``question``
    but are never referenced here.
    """
    return AnnotatableContent(
        question_id=question.id,
        exam_year=question.exam_year,
        section=question.section,
        question_type=question.question_type.value,
        statement=question.statement,
        content_blocks=tuple(question.content_blocks) if question.content_blocks else None,
        alternatives=tuple(
            AnnotatableAlternative(
                letter=alt.letter,
                text=alt.text,
                asset=alt.asset,
                content_blocks=tuple(alt.content_blocks) if alt.content_blocks else None,
            )
            for alt in question.alternatives
        ),
        assets=tuple(question.assets),
        applicable_courses=tuple(c.value for c in question.applicable_courses),
    )
