"""Pilot audit metrics (PROMPT Fase 5A section 27).

Pure, read-only aggregation over an already-built annotation set - never
a quality/accuracy claim (there is no human gold for this pilot yet), and
never a step that itself annotates anything. Every count here is a
structural fact about the 30 already-produced annotations, reported so a
human reviewer can spot overly broad/narrow categories, gaps, and
concentration before deciding whether to expand the pilot.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from enade.models.taxonomy import Taxonomy
from enade.semantic.annotation import QuestionAnnotation
from enade.semantic.corpus_survey import QuestionSurveyEntry
from enade.semantic.selection import STRATA


@dataclass(frozen=True)
class PilotAudit:
    annotation_count: int
    status_counts: dict[str, int]
    confidence_counts: dict[str, int]
    questions_per_subject: dict[str, int]
    questions_per_topic: dict[str, int]
    concepts_per_question: dict[str, int]
    primary_topics_per_question: dict[str, int]
    stratum_coverage: dict[str, int]
    textual_evidence_count: int
    visual_evidence_count: int
    used_alias_bearing_node_ids: list[str]
    never_used_node_ids: list[str]
    flags: list[str] = field(default_factory=list)


def _subject_of_topic(taxonomy: Taxonomy, topic_id: str) -> str | None:
    for subject in taxonomy.subjects:
        for topic in subject.topics:
            if topic.id == topic_id:
                return subject.id
    return None


def build_pilot_audit(
    annotations: list[QuestionAnnotation],
    taxonomy: Taxonomy,
    survey_by_id: dict[str, QuestionSurveyEntry],
) -> PilotAudit:
    status_counts = Counter(a.annotation_status for a in annotations)
    confidence_counts = Counter(a.confidence for a in annotations)

    questions_per_subject: Counter[str] = Counter()
    questions_per_topic: Counter[str] = Counter()
    concepts_per_question: dict[str, int] = {}
    primary_topics_per_question: dict[str, int] = {}
    textual_evidence_count = 0
    visual_evidence_count = 0
    referenced_topic_ids: set[str] = set()
    referenced_concept_ids: set[str] = set()

    for a in annotations:
        concepts_per_question[a.question_id] = len(a.concepts)
        primary_topics_per_question[a.question_id] = len(a.primary_topics)
        all_topics = set(a.primary_topics) | set(a.secondary_topics)
        referenced_topic_ids |= all_topics
        for topic_id in all_topics:
            questions_per_topic[topic_id] += 1
            subject_id = _subject_of_topic(taxonomy, topic_id)
            if subject_id is not None:
                questions_per_subject[subject_id] += 1
        for concept in a.concepts:
            referenced_concept_ids.add(concept.concept_id)
        all_evidence = list(a.evidence) + [
            ref for concept in a.concepts for ref in concept.evidence_refs
        ]
        for ref in all_evidence:
            if ref.text_excerpt:
                textual_evidence_count += 1
            if ref.asset_path:
                visual_evidence_count += 1

    selected_ids = [a.question_id for a in annotations]
    stratum_coverage = {
        name: sum(1 for qid in selected_ids if qid in survey_by_id and pred(survey_by_id[qid]))
        for name, pred in STRATA
    }

    all_node_ids = {view.id for view in taxonomy.flatten()}
    # A subject is never referenced directly by an annotation (only its
    # topics/concepts are) - it counts as "used" iff at least one of its
    # own topics was referenced, otherwise every subject would trivially
    # show up as "never used" regardless of its topics' real usage.
    referenced_subject_ids = set(questions_per_subject)
    referenced_ids = referenced_topic_ids | referenced_concept_ids | referenced_subject_ids

    def _search_labels(node: object) -> list[str]:
        labels = list(getattr(node, "aliases", []) or [])
        labels += list(getattr(node, "keywords", []) or [])
        return labels

    used_alias_bearing_node_ids = sorted(
        view.id
        for view in taxonomy.flatten()
        if _search_labels(view.node) and view.id in referenced_ids
    )
    never_used_node_ids = sorted(all_node_ids - referenced_ids)

    flags: list[str] = []
    if status_counts.get("unclassifiable", 0) / max(len(annotations), 1) > 0.4:
        flags.append(
            f"{status_counts.get('unclassifiable', 0)}/{len(annotations)} questões piloto "
            "foram marcadas unclassifiable - proporção alta; revisar se reflete genuinamente "
            "o escopo do curso (formação geral / Licenciatura) ou se a taxonomia está incompleta."
        )
    if confidence_counts.get("low", 0) > 0:
        flags.append(
            f"{confidence_counts.get('low', 0)} anotação(ões) com confiança 'low' - "
            "dependência de conteúdo visual não totalmente verificável apenas pelo texto."
        )
    most_common_subject = questions_per_subject.most_common(1)
    if most_common_subject and most_common_subject[0][1] >= 5:
        flags.append(
            f"Área '{most_common_subject[0][0]}' concentra {most_common_subject[0][1]} das "
            f"{len(annotations)} questões classificadas - possível concentração temática "
            "do piloto, não necessariamente da taxonomia."
        )
    if len(never_used_node_ids) > len(all_node_ids) // 2:
        flags.append(
            f"{len(never_used_node_ids)}/{len(all_node_ids)} nós da taxonomia nunca foram "
            "referenciados pelo piloto - esperado dado que apenas 30/255 questões foram "
            "anotadas nesta fase; não é evidência de nó desnecessário."
        )

    return PilotAudit(
        annotation_count=len(annotations),
        status_counts={str(k): v for k, v in status_counts.items()},
        confidence_counts={str(k): v for k, v in confidence_counts.items()},
        questions_per_subject=dict(questions_per_subject),
        questions_per_topic=dict(questions_per_topic),
        concepts_per_question=concepts_per_question,
        primary_topics_per_question=primary_topics_per_question,
        stratum_coverage=stratum_coverage,
        textual_evidence_count=textual_evidence_count,
        visual_evidence_count=visual_evidence_count,
        used_alias_bearing_node_ids=used_alias_bearing_node_ids,
        never_used_node_ids=never_used_node_ids,
        flags=flags,
    )
