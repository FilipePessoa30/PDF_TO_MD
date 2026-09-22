"""Cross-artifact validators for the semantic layer (PROMPT Fase 5A
section 23) - each one *re-derives* ground truth from the real,
published corpus/taxonomy rather than trusting a claim already made
elsewhere. Every function here only ever reports; none of them repair or
promote an annotation's own status (the same discipline
``enade.extraction.content_assignment``'s own gates already follow).
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from enade.models.taxonomy import Taxonomy
from enade.semantic.annotation import QuestionAnnotation, source_file_sha256


@dataclass(frozen=True)
class Diagnostic:
    """One validator finding - always names the question and the field
    it concerns, per PROMPT section 23 ("diagnosticos por questao e
    campo"), never a bare count.
    """

    kind: str
    question_id: str
    field: str
    detail: str


def _flatten_ids_by_kind(taxonomy: Taxonomy) -> dict[str, set[str]]:
    by_kind: dict[str, set[str]] = {"subject": set(), "topic": set(), "concept": set()}
    for view in taxonomy.flatten():
        by_kind[view.kind].add(view.id)
    return by_kind


def validate_annotation_against_taxonomy(
    annotation: QuestionAnnotation, taxonomy: Taxonomy, taxonomy_version: str
) -> list[Diagnostic]:
    """PROMPT section 23: taxonomy version exists; every topic/concept id
    referenced actually exists in that taxonomy; no reference to a
    ``deprecated`` node.
    """
    diagnostics: list[Diagnostic] = []
    qid = annotation.question_id

    if annotation.taxonomy_version != taxonomy_version:
        diagnostics.append(
            Diagnostic(
                kind="taxonomy_version_mismatch",
                question_id=qid,
                field="taxonomy_version",
                detail=f"annotation declares {annotation.taxonomy_version!r}, loaded taxonomy is {taxonomy_version!r}",
            )
        )
        return diagnostics  # comparing ids across mismatched versions is meaningless

    ids_by_kind = _flatten_ids_by_kind(taxonomy)
    topic_and_subject_ids = ids_by_kind["subject"] | ids_by_kind["topic"]
    concept_ids = ids_by_kind["concept"]
    status_by_id = {view.id: view.node.status.value for view in taxonomy.flatten()}

    for field_name, topics in (
        ("primary_topics", annotation.primary_topics),
        ("secondary_topics", annotation.secondary_topics),
    ):
        for topic_id in topics:
            if topic_id not in topic_and_subject_ids:
                diagnostics.append(
                    Diagnostic(
                        kind="topic_not_found",
                        question_id=qid,
                        field=field_name,
                        detail=f"{topic_id!r} does not exist in taxonomy {taxonomy_version!r}",
                    )
                )
            elif status_by_id.get(topic_id) == "deprecated":
                diagnostics.append(
                    Diagnostic(
                        kind="topic_deprecated",
                        question_id=qid,
                        field=field_name,
                        detail=f"{topic_id!r} is deprecated in taxonomy {taxonomy_version!r}",
                    )
                )

    for concept in annotation.concepts:
        if concept.concept_id not in concept_ids:
            diagnostics.append(
                Diagnostic(
                    kind="concept_not_found",
                    question_id=qid,
                    field="concepts",
                    detail=f"{concept.concept_id!r} does not exist in taxonomy {taxonomy_version!r}",
                )
            )
        elif status_by_id.get(concept.concept_id) == "deprecated":
            diagnostics.append(
                Diagnostic(
                    kind="concept_deprecated",
                    question_id=qid,
                    field="concepts",
                    detail=f"{concept.concept_id!r} is deprecated in taxonomy {taxonomy_version!r}",
                )
            )

    return diagnostics


def validate_evidence_integrity(
    annotation: QuestionAnnotation, questions_dir: Path
) -> list[Diagnostic]:
    """PROMPT section 15/23: every evidence ref's ``source_sha256`` must
    match the *real*, current published Markdown file - never trust a
    hash recorded at annotation time forever. Also confirms the question
    itself still exists and that ``source_hash`` (the annotation's own
    top-level field) matches too - the same "source hash stale" check
    section 23 asks for.
    """
    diagnostics: list[Diagnostic] = []
    qid = annotation.question_id
    md_path = questions_dir / f"{qid}.md"

    if not md_path.is_file():
        diagnostics.append(
            Diagnostic(
                kind="source_question_missing",
                question_id=qid,
                field="question_id",
                detail=f"no published Markdown found at {md_path}",
            )
        )
        return diagnostics  # nothing else here is checkable without the file

    real_hash = source_file_sha256(md_path)
    if annotation.source_hash != real_hash:
        diagnostics.append(
            Diagnostic(
                kind="source_hash_stale",
                question_id=qid,
                field="source_hash",
                detail=f"annotation recorded {annotation.source_hash!r}, real file is {real_hash!r}",
            )
        )

    all_evidence = list(annotation.evidence) + [
        ref for concept in annotation.concepts for ref in concept.evidence_refs
    ]
    for i, ref in enumerate(all_evidence):
        if ref.source_sha256 != real_hash:
            diagnostics.append(
                Diagnostic(
                    kind="evidence_source_hash_stale",
                    question_id=qid,
                    field=f"evidence[{i}].source_sha256",
                    detail=f"recorded {ref.source_sha256!r}, real file is {real_hash!r}",
                )
            )
        if ref.asset_path is not None:
            asset_full_path = questions_dir / ref.asset_path
            if not asset_full_path.is_file():
                diagnostics.append(
                    Diagnostic(
                        kind="evidence_asset_missing",
                        question_id=qid,
                        field=f"evidence[{i}].asset_path",
                        detail=f"{asset_full_path} does not exist",
                    )
                )
            elif ref.asset_sha256 is not None:
                real_asset_hash = source_file_sha256(asset_full_path)
                if real_asset_hash != ref.asset_sha256:
                    diagnostics.append(
                        Diagnostic(
                            kind="evidence_asset_hash_stale",
                            question_id=qid,
                            field=f"evidence[{i}].asset_sha256",
                            detail=f"recorded {ref.asset_sha256!r}, real file is {real_asset_hash!r}",
                        )
                    )
    return diagnostics


def validate_shared_question_consistency(
    annotations: list[QuestionAnnotation], canonical_of: dict[str, str]
) -> list[Diagnostic]:
    """PROMPT section 10/23: a question shared canonically across
    courses must never receive divergent annotations under two different
    ids. ``canonical_of`` maps every question_id that appears in
    ``annotations`` to its own canonical identity (the identity function
    for a question that is not shared at all).
    """
    diagnostics: list[Diagnostic] = []
    by_canonical: dict[str, list[QuestionAnnotation]] = defaultdict(list)
    for annotation in annotations:
        canonical = canonical_of.get(annotation.question_id, annotation.question_id)
        by_canonical[canonical].append(annotation)

    for canonical, group in by_canonical.items():
        if len(group) < 2:
            continue
        primary_sets = {tuple(sorted(a.primary_topics)) for a in group}
        if len(primary_sets) > 1:
            ids = sorted(a.question_id for a in group)
            diagnostics.append(
                Diagnostic(
                    kind="shared_question_divergent_annotation",
                    question_id=canonical,
                    field="primary_topics",
                    detail=f"{ids} disagree on primary_topics: {sorted(primary_sets)}",
                )
            )
    return diagnostics


def validate_search_terms_have_provenance(annotation: QuestionAnnotation) -> list[Diagnostic]:
    """PROMPT section 17/23: every search term must derive from the
    taxonomy/annotation itself (a topic/concept id, its own name/alias,
    or explicit evidence) - never an independently invented string with
    no traceable origin. This function only checks internal consistency
    (search_terms is never empty while every topic/concept list is also
    empty, for a non-unclassifiable annotation); the full alias
    cross-check against the taxonomy happens in the CLI, which has both
    documents loaded together.
    """
    if annotation.annotation_status == "unclassifiable":
        return []
    if annotation.search_terms and not (
        annotation.primary_topics or annotation.secondary_topics or annotation.concepts
    ):
        return [
            Diagnostic(
                kind="search_terms_without_origin",
                question_id=annotation.question_id,
                field="search_terms",
                detail="search_terms is non-empty but no topic/concept exists to derive it from",
            )
        ]
    return []
