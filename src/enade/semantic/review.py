"""Human-review package builder (PROMPT Fase 5A section 22).

Renders ``docs/semantic-pilot-review.md``: one section per piloted
question, showing everything a reviewer needs to approve/correct/reject
an annotation *without opening the JSON* - and nothing else. In
particular this module never reads or renders the gabarito/answer
standard (there is nothing to filter: ``QuestionAnnotation`` itself has
no field capable of holding one, PROMPT section 16).

Building the review packet is a pure, read-only rendering step - it
never promotes ``annotation_status``/``review_status`` (PROMPT section
24: "review nunca promove status").
"""

from __future__ import annotations

from enade.models.taxonomy import Taxonomy
from enade.semantic.annotation import QuestionAnnotation
from enade.semantic.corpus_survey import target_of_question_id

#: PROTECTED_TARGETS key -> (exam year, human-readable course label).
_TARGET_LABELS: dict[str, tuple[int, str]] = {
    "2008-b": (2008, "Computação (livreto unificado)"),
    "2011": (2011, "Computação (livreto unificado)"),
    "2021-cc-b": (2021, "Ciência da Computação - Bacharelado"),
    "2021-cc-l": (2021, "Ciência da Computação - Licenciatura"),
    "2021-si": (2021, "Sistemas de Informação"),
}


def _label_for(node_id: str, taxonomy: Taxonomy) -> str:
    for view in taxonomy.flatten():
        if view.id == node_id:
            return f"{node_id} ({view.node.name})"
    return f"{node_id} (não encontrado na taxonomia)"


def _question_type_label(question_id: str) -> str:
    # Discursive question ids in this corpus always use a "-d##" segment,
    # multiple-choice ones a "-q##" segment (confirmed against every real
    # id in the pilot; never inferred from content).
    last_segment = question_id.rsplit("-", 1)[-1]
    return "discursiva" if last_segment.startswith("d") else "múltipla escolha"


def _render_question(annotation: QuestionAnnotation, taxonomy: Taxonomy) -> str:
    target = target_of_question_id(annotation.question_id)
    year, course_label = _TARGET_LABELS[target]
    qtype = _question_type_label(annotation.question_id)

    lines = [
        f"## {annotation.question_id}",
        "",
        f"- **Ano/curso:** {year} - {course_label}",
        f"- **Tipo:** {qtype}",
        f"- **Componente:** {annotation.component}",
        f"- **Status da anotação:** {annotation.annotation_status}",
        f"- **Status de revisão:** {annotation.review_status}",
        f"- **Confiança:** {annotation.confidence}",
    ]

    if annotation.annotation_status == "unclassifiable":
        lines.append("- **Tópico primário:** _(nenhum - unclassifiable)_")
    else:
        primary = ", ".join(_label_for(t, taxonomy) for t in annotation.primary_topics)
        lines.append(f"- **Tópico(s) primário(s):** {primary}")
        if annotation.secondary_topics:
            secondary = ", ".join(_label_for(t, taxonomy) for t in annotation.secondary_topics)
            lines.append(f"- **Tópico(s) secundário(s):** {secondary}")
        if annotation.concepts:
            lines.append("- **Conceitos:**")
            for concept in annotation.concepts:
                lines.append(
                    f"  - {_label_for(concept.concept_id, taxonomy)} "
                    f"(papel: {concept.role}, confiança: {concept.confidence})"
                )
        if annotation.context_tags:
            lines.append(
                f"- **Contexto (não avaliado centralmente):** {', '.join(annotation.context_tags)}"
            )
        if annotation.cognitive_skills:
            lines.append(
                f"- **Habilidade(s) cognitiva(s):** {', '.join(annotation.cognitive_skills)}"
            )
        if annotation.search_terms:
            lines.append(f"- **Termos de busca:** {', '.join(annotation.search_terms)}")

    if annotation.evidence:
        lines.append("- **Evidência:**")
        for ref in annotation.evidence:
            if ref.text_excerpt:
                lines.append(f'  - ({ref.source_kind}/{ref.source_locator}) "{ref.text_excerpt}"')
            else:
                lines.append(
                    f"  - ({ref.source_kind}/{ref.source_locator}) asset: {ref.asset_path}"
                )

    if annotation.notes:
        lines.append(f"- **Notas/dúvidas:** {annotation.notes}")

    lines.append("- **Decisão do revisor:** ☐ aprovar ☐ corrigir ☐ rejeitar")
    lines.append("")
    return "\n".join(lines)


def build_review_markdown(
    annotations: list[QuestionAnnotation], taxonomy: Taxonomy, taxonomy_version: str
) -> str:
    ordered = sorted(annotations, key=lambda a: a.question_id)
    header = [
        "# Pacote de revisão humana - piloto semântico (Fase 5A)",
        "",
        f"Taxonomia: `{taxonomy_version}` - {len(ordered)} questão(ões) piloto.",
        "",
        "Este pacote permite aprovar, corrigir ou rejeitar cada anotação sem abrir o "
        "JSON. Nenhuma anotação aqui foi humanamente revisada ainda - todas estão "
        "`proposed`, `needs_review` ou `unclassifiable` (nunca `reviewed`). O gabarito "
        "e o padrão de resposta nunca aparecem neste pacote nem no modelo de anotação "
        "subjacente (anti-leakage, PROMPT Fase 5A seção 16).",
        "",
        "---",
        "",
    ]
    body = [_render_question(a, taxonomy) for a in ordered]
    return "\n".join(header) + "\n---\n\n".join(body)


def _label_for_any(node_id: str, taxonomies: list[Taxonomy]) -> str:
    for taxonomy in taxonomies:
        for view in taxonomy.flatten():
            if view.id == node_id:
                return f"{node_id} ({view.node.name})"
    return f"{node_id} (não encontrado nas taxonomias carregadas)"


def _render_reconciliation_question(
    annotation_5b: QuestionAnnotation,
    annotation_5a: dict,
    migration_entry: dict,
    taxonomies: list[Taxonomy],
) -> str:
    qid = annotation_5b.question_id
    target = target_of_question_id(qid)
    year, course_label = _TARGET_LABELS[target]
    qtype = _question_type_label(qid)

    def _fmt_topics(topics: list[str]) -> str:
        return ", ".join(_label_for_any(t, taxonomies) for t in topics) if topics else "_(nenhum)_"

    lines = [
        f"## {qid}",
        "",
        f"- **Ano/curso:** {year} - {course_label}",
        f"- **Tipo:** {qtype}",
        f"- **Componente:** {annotation_5b.component}",
        "",
        "**Classificação Fase 5A (histórica):**",
        f"- status: `{annotation_5a['annotation_status']}`",
        f"- tópico(s) primário(s): {_fmt_topics(annotation_5a['primary_topics'])}",
        "",
        "**Classificação Fase 5B (proposta técnica):**",
        f"- taxonomia: `{annotation_5b.taxonomy_version}`",
        f"- status: `{annotation_5b.annotation_status}`",
        f"- tópico(s) primário(s): {_fmt_topics(annotation_5b.primary_topics)}",
        f"- tópico(s) secundário(s): {_fmt_topics(annotation_5b.secondary_topics)}",
    ]
    if annotation_5b.concepts:
        lines.append("- conceitos:")
        for concept in annotation_5b.concepts:
            lines.append(
                f"  - {_label_for_any(concept.concept_id, taxonomies)} "
                f"(papel: {concept.role}, confiança: {concept.confidence})"
            )
    if annotation_5b.context_tags:
        lines.append(
            f"- contexto (não avaliado centralmente): {', '.join(annotation_5b.context_tags)}"
        )
    lines.append(
        f"- habilidade(s) cognitiva(s): {', '.join(annotation_5b.cognitive_skills) or '_(nenhuma)_'}"
    )
    lines.append(f"- confiança: `{annotation_5b.confidence}`")

    lines.append("")
    lines.append(f"**Motivo da mudança (5A → 5B):** {migration_entry['change_reason']}")

    if annotation_5b.evidence:
        lines.append("")
        lines.append("**Evidências:**")
        for ref in annotation_5b.evidence:
            if ref.text_excerpt:
                lines.append(f'- ({ref.source_kind}/{ref.source_locator}) "{ref.text_excerpt}"')
            else:
                lines.append(f"- ({ref.source_kind}/{ref.source_locator}) asset: {ref.asset_path}")

    if annotation_5b.notes:
        lines.append("")
        lines.append(f"**Notas técnicas:** {annotation_5b.notes}")

    lines.append("")
    lines.append(
        "**Decisão humana pendente (preencher apenas em "
        "`data/semantic/human-adjudication-template-5b.json`, nunca aqui):** "
        "☐ approve ☐ correct ☐ reject ☐ defer"
    )
    lines.append("")
    return "\n".join(lines)


def build_reconciliation_review_markdown(
    annotations_5b: list[QuestionAnnotation],
    annotations_5a_by_id: dict[str, dict],
    migration_by_id: dict[str, dict],
    taxonomies: list[Taxonomy],
) -> str:
    """PROMPT Fase 5B section 22 - the reconciliation review packet.
    Clearly separates 'proposta técnica' (everything computed here) from
    'decisão humana pendente' (which lives only in the adjudication
    template, never filled in by this function).
    """
    ordered = sorted(annotations_5b, key=lambda a: a.question_id)
    header = [
        "# Pacote de revisão humana - reconciliação do piloto (Fase 5B)",
        "",
        f"{len(ordered)} questão(ões) - reconciliação adversarial das 30 anotações "
        "do piloto da Fase 5A, com foco nos 12 casos não-`proposed` "
        "(10 `unclassifiable` + 2 `needs_review`) e auditoria das 18 `proposed`.",
        "",
        "Toda decisão marcada abaixo como 'proposta técnica' é apenas isso - uma "
        "proposta. Nenhuma anotação aqui foi humanamente revisada; nenhuma tem "
        "`review_status='reviewed'`. A decisão humana real (approve/correct/reject/"
        "defer) só pode ser registrada em "
        "`data/semantic/human-adjudication-template-5b.json`, nunca neste "
        "documento. O gabarito e o padrão de resposta nunca aparecem aqui.",
        "",
        "---",
        "",
    ]
    body = [
        _render_reconciliation_question(
            a, annotations_5a_by_id[a.question_id], migration_by_id[a.question_id], taxonomies
        )
        for a in ordered
    ]
    return "\n".join(header) + "\n---\n\n".join(body)
