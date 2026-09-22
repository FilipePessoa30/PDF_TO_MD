"""Structural (never semantic) survey of the published corpus - PROMPT
Fase 5A sections 5, 9, 20, 28.

Reads only what is already true of a published :class:`Question` object
(section, type, applicable_courses, asset types, content_blocks,
answer_standard presence) - never invents a topic, never reads statement
text to guess a subject. Used for two, deliberately separate purposes:

1. Grounding evidence for taxonomy design and the pilot's own stratified
   sampling (section 9's "recorrência real no corpus" criterion, section
   20's stratification dimensions) - computed once, read by a human (this
   agent) deciding taxonomy structure and pilot composition.
2. The read-only "generalization scan" (section 28) run diagnostically
   against all five protected booklets, without ever publishing an
   annotation - a pure coverage report.

Never writes to ``data/questions``. Never produces or persists a semantic
annotation.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from enade.markdown_format import load_questions_directory
from enade.models.content_block import AssetBlock, TableBlock
from enade.models.enums import AssetType, CourseCode, QuestionType
from enade.models.question import Question

#: The prefix every "formacao geral" section id starts with, across every
#: booklet this corpus contains (confirmed by direct inspection of every
#: real ``section:`` value published in 2008-b/2011/2021 - never assumed).
_FORMACAO_GERAL_PREFIX = "formacao-geral"


@dataclass(frozen=True)
class QuestionSurveyEntry:
    """One question's own structural facts - no interpretation, no topic."""

    question_id: str
    target: str
    exam_year: int
    applicable_courses: tuple[str, ...]
    is_shared_across_courses: bool
    section: str
    component: str  # "formacao_geral" | "componente_especifico"
    question_type: str
    has_table: bool
    has_equation_asset: bool
    has_diagram_or_image_asset: bool
    has_alternative_asset: bool
    asset_count: int
    has_answer_standard: bool
    likely_source_limitation: bool
    statement_word_count: int


def _component_of(section: str) -> str:
    return (
        "formacao_geral" if section.startswith(_FORMACAO_GERAL_PREFIX) else "componente_especifico"
    )


def _alternative_has_asset(question: Question) -> bool:
    for alt in question.alternatives:
        if alt.asset is not None:
            return True
        if alt.content_blocks is not None and any(
            isinstance(b, AssetBlock) for b in alt.content_blocks
        ):
            return True
    return False


def survey_question(question: Question, target: str) -> QuestionSurveyEntry:
    """Pure function of an already-validated :class:`Question` - never
    touches the filesystem itself (the caller resolves ``target``/loads
    the question).
    """
    asset_types = {a.type for a in question.assets}
    content_blocks = question.content_blocks or []
    has_table = any(isinstance(b, TableBlock) for b in content_blocks)
    is_discursive = question.question_type == QuestionType.DISCURSIVE
    return QuestionSurveyEntry(
        question_id=question.id,
        target=target,
        exam_year=question.exam_year,
        applicable_courses=tuple(c.value for c in question.applicable_courses),
        # PROMPT Fase 5A section 10: a question shared across courses in
        # this corpus is represented by the single ALL_COMPUTING alias
        # (2008-b/2011's own unified booklets), never by a multi-element
        # applicable_courses list (Question's own validator forbids
        # combining the alias with explicit codes, so len > 1 never
        # actually occurs in real data - confirmed empirically: 0/255).
        is_shared_across_courses=CourseCode.ALL_COMPUTING in question.applicable_courses,
        section=question.section,
        component=_component_of(question.section),
        question_type=question.question_type.value,
        has_table=has_table,
        has_equation_asset=AssetType.EQUATION in asset_types,
        has_diagram_or_image_asset=bool(
            asset_types & {AssetType.DIAGRAM, AssetType.GRAPH, AssetType.IMAGE}
        ),
        has_alternative_asset=_alternative_has_asset(question),
        asset_count=len(question.assets),
        has_answer_standard=question.answer_standard is not None,
        # A discursive item with no answer_standard at all is the one
        # structural signature a documented source_unavailable case
        # (D09/D10, PROMPT Fase 3Z) always has - never used to *claim*
        # source_unavailable_confirmed status by itself (that status lives
        # exclusively in source-availability-2008.yaml, verified with full
        # forensic evidence); this is only a coarse stratification hint so
        # the pilot sample can deliberately include such a case.
        likely_source_limitation=is_discursive and question.answer_standard is None,
        statement_word_count=len(question.statement.split()),
    )


def survey_directory(questions_dir: Path, target: str) -> list[QuestionSurveyEntry]:
    questions = load_questions_directory(questions_dir)
    return [survey_question(q, target) for _, q in sorted(questions.items())]


#: The five protected booklets this survey (and every other Fase 5A
#: diagnostic) is scoped to - never a sixth, never a different year
#: (PROMPT Fase 5A section 32: "nao processe 2005").
PROTECTED_TARGETS: dict[str, str] = {
    "2008-b": "data/questions/2008/all-computing",
    "2011": "data/questions/2011/all-computing",
    "2021-cc-b": "data/questions/2021/ciencia-da-computacao-bacharelado",
    "2021-cc-l": "data/questions/2021/ciencia-da-computacao-licenciatura",
    "2021-si": "data/questions/2021/sistemas-de-informacao",
}


def survey_all_targets(project_root: Path) -> dict[str, list[QuestionSurveyEntry]]:
    return {
        target: survey_directory(project_root / rel, target)
        for target, rel in PROTECTED_TARGETS.items()
    }


#: question_id prefix -> PROTECTED_TARGETS key, ordered longest-prefix-first
#: so "enade-2021-cc-b-" is checked before a hypothetical shorter overlap.
_QUESTION_ID_PREFIX_TO_TARGET: tuple[tuple[str, str], ...] = (
    ("enade-2008-", "2008-b"),
    ("enade-2011-", "2011"),
    ("enade-2021-cc-b-", "2021-cc-b"),
    ("enade-2021-cc-l-", "2021-cc-l"),
    ("enade-2021-si-", "2021-si"),
)


def target_of_question_id(question_id: str) -> str:
    """The ``PROTECTED_TARGETS`` key (e.g. ``"2021-cc-b"``) a question_id
    belongs to, derived from its own prefix - never guessed.
    """
    for prefix, target in _QUESTION_ID_PREFIX_TO_TARGET:
        if question_id.startswith(prefix):
            return target
    raise ValueError(f"question_id {question_id!r} matches none of the 5 protected targets")


def resolve_question_directory(question_id: str, project_root: Path) -> Path:
    """The one real directory a published question's own Markdown (and
    sibling assets) live under, derived from its ``question_id`` prefix -
    never guessed, never resolved by searching the filesystem.
    """
    return project_root / PROTECTED_TARGETS[target_of_question_id(question_id)]
