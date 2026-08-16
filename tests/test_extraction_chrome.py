from __future__ import annotations

import pytest

from enade.extraction.chrome import is_chrome_line


@pytest.mark.parametrize(
    "text",
    [
        "23",
        "RASCUNHO",
        "Área livre",
        "CIÊNCIA DA COMPUTAÇÃO",
        "Bacharelado",
        "*R02202130*",
        "NOVEMBRO | 21",
        "ENADE2021",
        "GABARITO DEFINITIVO",
        "PADRÃO DE RESPOSTA",
        "   ",
        "",
        "1 2 3 4 5 6 7 8 9 10 11 12 13 14 15",
        "COMPONENTE ESPECÍFICO",
        "FORMAÇÃO GERAL",
    ],
)
def test_known_chrome_lines_are_detected(text):
    assert is_chrome_line(text) is True


def test_section_heading_does_not_leak_into_the_previous_questions_alternative():
    """Regression test: "Componente Especifico" sits at the top of the page
    where Discursiva 3 begins, but textually before its own marker line -
    without being recognized as chrome, it was appended to the previous
    question's (Q8's) last alternative text, e.g. "II, III e IV. COMPONENTE
    ESPECIFICO" (Phase 1B audit finding, see docs/decisions.md).
    """
    assert is_chrome_line("COMPONENTE ESPECÍFICO") is True
    assert is_chrome_line("Componente Específico") is True


@pytest.mark.parametrize(
    "text",
    [
        "A chance de uma criança de baixa renda ter um futuro melhor",
        "QUESTÃO 12",
        "A  Os repetidores não reconhecem quadros ou pacotes.",
        "O uso da estrutura de dados tipo Árvore Binária de Busca",
        "int left(int i) { return (2 * i + 1); }",
    ],
)
def test_real_content_lines_are_not_chrome(text):
    assert is_chrome_line(text) is False


# --- Phase 3B: 2008-b's own section-transition table (see
# docs/phase-3b-report.md) -----------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        "Número das Questões",
        "Múltipla Escolha",
        "Discursivas",
        "21 a 38",
        "39 e 40",
        "Perfil do curso",
        "Bacharelado em Ciência da Computação",
        "Bacharelado em Sistemas de Informação",
        "As questões de 21 a 40, a seguir, são específicas para os estudantes de cursos com perfis profissionais de",
    ],
)
def test_2008_b_transition_table_lines_are_chrome(text):
    assert is_chrome_line(text) is True


@pytest.mark.parametrize(
    "text",
    [
        "RASCUNHO – QUESTÃO 39 - A",
        "RASCUNHO – QUESTÃO 20 - B",
        "RASCUNHO – QUESTÃO 59",
        "rascunho - questão 80 - a",
    ],
)
def test_2008_b_rascunho_question_reference_is_chrome(text):
    assert is_chrome_line(text) is True


def test_rascunho_alone_as_an_alternative_marker_line_is_not_matched_by_the_new_regex():
    # "E\tRASCUNHO" (2008-b's own Q38, an alternative letter immediately
    # followed by the word RASCUNHO) must not be swallowed by the new
    # "RASCUNHO - QUESTAO N" regex - it has no question-number reference at
    # all, so it correctly falls through to being treated as real
    # (non-chrome) alternative content, same as before this phase.
    assert is_chrome_line("E\tRASCUNHO") is False
