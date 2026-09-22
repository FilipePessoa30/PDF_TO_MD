"""Diagnostic-only compatibility scan (PROMPT Fase 5A section 28).

Runs the taxonomy against all five protected booklets (255 questions),
never just the 30-question pilot - but this module never produces or
persists an automatic annotation for the non-piloted questions. It is a
coarse, case-insensitive keyword-match heuristic (each topic/concept's
own structured ``name``/``aliases``/``keywords`` fields - never TF-IDF,
never an embedding, never an LLM, per PROMPT section 32) used only to
report structural coverage facts a human can use to plan a future,
explicitly separate expansion of the pilot.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass

from enade.models.question import Question
from enade.models.taxonomy import Taxonomy
from enade.semantic.corpus_survey import QuestionSurveyEntry


def _normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c)).lower()


@dataclass(frozen=True)
class TopicKeywords:
    topic_id: str
    subject_id: str
    labels: tuple[str, ...]


def _topic_keyword_index(taxonomy: Taxonomy) -> list[TopicKeywords]:
    index = []
    for subject in taxonomy.subjects:
        for topic in subject.topics:
            labels = {topic.name, *topic.aliases}
            for concept in topic.concepts:
                labels.add(concept.name)
                labels.update(concept.aliases)
                labels.update(concept.keywords)
            # A label shorter than 5 normalized characters (e.g. a bare
            # acronym like "SI") produces too many false positives in a
            # plain substring scan - excluded from the heuristic, never
            # from the taxonomy itself.
            normalized_labels = tuple(
                sorted({_normalize(label) for label in labels if len(_normalize(label)) >= 5})
            )
            if normalized_labels:
                index.append(TopicKeywords(topic.id, subject.id, normalized_labels))
    return index


def candidate_topics_for_text(text: str, taxonomy: Taxonomy) -> list[str]:
    normalized_text = _normalize(text)
    hits = []
    for entry in _topic_keyword_index(taxonomy):
        if any(label in normalized_text for label in entry.labels):
            hits.append(entry.topic_id)
    return sorted(hits)


@dataclass(frozen=True)
class GeneralizationScanResult:
    total_questions: int
    questions_with_no_candidate: list[str]
    dominant_areas: dict[str, int]
    questions_needing_visual_evidence: list[str]
    shared_questions: list[str]
    likely_needs_review: list[str]
    method_note: str = (
        "Escaneamento diagnostico por correspondencia de substring (nome/aliases/"
        "keywords normalizados de cada topico/conceito) - nunca TF-IDF, nunca "
        "embeddings, nunca LLM (PROMPT Fase 5A secao 32). Nao produz nem persiste "
        "nenhuma anotacao automatica; usado apenas para orientar uma expansao "
        "futura, explicitamente separada, do piloto."
    )


def scan_corpus(
    questions_by_id: dict[str, Question],
    survey_by_id: dict[str, QuestionSurveyEntry],
    taxonomy: Taxonomy,
) -> GeneralizationScanResult:
    keyword_index = _topic_keyword_index(taxonomy)
    subject_of_topic = {entry.topic_id: entry.subject_id for entry in keyword_index}

    no_candidate: list[str] = []
    area_hits: dict[str, int] = {}
    needs_visual: list[str] = []
    shared: list[str] = []
    needs_review: list[str] = []

    for question_id, question in sorted(questions_by_id.items()):
        survey_entry = survey_by_id.get(question_id)
        text = question.statement
        for alt in question.alternatives:
            text += " " + alt.text
        candidates = candidate_topics_for_text(text, taxonomy)

        if survey_entry is not None and survey_entry.component == "formacao_geral":
            # Formação geral is expected to have no Computing candidate -
            # never counted as a coverage gap.
            pass
        elif not candidates:
            no_candidate.append(question_id)

        for topic_id in candidates:
            subject_id = subject_of_topic[topic_id]
            area_hits[subject_id] = area_hits.get(subject_id, 0) + 1

        if survey_entry is not None:
            if (
                survey_entry.has_table
                or survey_entry.has_equation_asset
                or survey_entry.has_diagram_or_image_asset
            ):
                needs_visual.append(question_id)
            if survey_entry.is_shared_across_courses:
                shared.append(question_id)
            # Coarse "likely needs human review" signal: alternatives are
            # themselves images (no textual grounding at all for the
            # multiple-choice answer options) or the candidate topics span
            # more than one taxonomy area (possible ambiguity/overlap).
            distinct_areas = {subject_of_topic[t] for t in candidates}
            if survey_entry.has_alternative_asset or len(distinct_areas) > 1:
                needs_review.append(question_id)

    return GeneralizationScanResult(
        total_questions=len(questions_by_id),
        questions_with_no_candidate=sorted(no_candidate),
        dominant_areas=dict(sorted(area_hits.items(), key=lambda kv: (-kv[1], kv[0]))),
        questions_needing_visual_evidence=sorted(needs_visual),
        shared_questions=sorted(shared),
        likely_needs_review=sorted(needs_review),
    )
