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
    ],
)
def test_known_chrome_lines_are_detected(text):
    assert is_chrome_line(text) is True


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
