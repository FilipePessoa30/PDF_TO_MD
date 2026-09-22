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
