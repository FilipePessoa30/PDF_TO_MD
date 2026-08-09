from __future__ import annotations

from enade.extraction.boundaries import QuestionKind, detect_question_boundaries
from enade.extraction.layout import Line


def _line(page: int, y: float, text: str, x: float = 30.0) -> Line:
    return Line(page_number=page, text=text, x0=x, y0=y, x1=x + 200, y1=y + 12)


def test_detects_objective_and_discursive_markers():
    lines = [
        _line(1, 10, "QUESTÃO DISCURSIVA 1"),
        _line(1, 30, "Enunciado da discursiva um."),
        _line(2, 10, "QUESTÃO 1"),
        _line(2, 30, "Enunciado da questão um."),
        _line(2, 50, "A\t alternativa a"),
        _line(2, 65, "B\t alternativa b"),
        _line(2, 80, "C\t alternativa c"),
        _line(2, 95, "D\t alternativa d"),
        _line(2, 110, "E\t alternativa e"),
    ]
    result = detect_question_boundaries(lines)
    assert result.warnings == []
    kinds_numbers = {(s.kind, s.number) for s in result.spans}
    assert kinds_numbers == {(QuestionKind.DISCURSIVE, 1), (QuestionKind.OBJECTIVE, 1)}


def test_marker_is_case_insensitive_and_tolerates_mangled_case():
    lines = [_line(1, 10, "QuEStãO diSCuRSiVa 01"), _line(1, 30, "texto")]
    result = detect_question_boundaries(lines)
    assert len(result.spans) == 1
    assert result.spans[0].kind == QuestionKind.DISCURSIVE
    assert result.spans[0].number == 1


def test_perception_questionnaire_page_is_fully_excluded():
    lines = [
        _line(1, 10, "QUESTÃO 1"),
        _line(1, 30, "Enunciado real da questão 1."),
        _line(2, 10, "QUESTÃO 1"),  # reused numbering inside the questionnaire
        _line(2, 30, "Qual o grau de dificuldade desta prova?"),
        _line(2, 200, "QUESTIONÁRIO DE PERCEPÇÃO DA PROVA"),
    ]
    result = detect_question_boundaries(lines)
    assert result.perception_pages == [2]
    assert len(result.spans) == 1
    assert result.spans[0].number == 1
    assert all(ln.page_number != 2 for ln in result.spans[0].lines)


def test_incidental_mention_of_questao_mid_sentence_is_not_a_marker():
    lines = [
        _line(1, 10, "QUESTÃO 1"),
        _line(1, 30, "Responda cada questão discursiva em, no máximo, 15 linhas."),
    ]
    result = detect_question_boundaries(lines)
    assert len(result.spans) == 1
    assert result.spans[0].number == 1


def test_question_spans_multiple_pages_until_next_marker():
    lines = [
        _line(1, 10, "QUESTÃO 1"),
        _line(1, 30, "Início do enunciado na página 1."),
        _line(2, 10, "Continuação na página 2."),
        _line(2, 30, "A\t alt a"),
        _line(2, 45, "B\t alt b"),
        _line(2, 60, "C\t alt c"),
        _line(2, 75, "D\t alt d"),
        _line(2, 90, "E\t alt e"),
        _line(3, 10, "QUESTÃO 2"),
        _line(3, 30, "Segunda questão."),
    ]
    result = detect_question_boundaries(lines)
    q1 = next(s for s in result.spans if s.number == 1)
    assert q1.start_page == 1
    assert q1.end_page == 2
    assert all(ln.page_number in (1, 2) for ln in q1.lines)


def test_detects_gap_in_numbering():
    lines = [
        _line(1, 10, "QUESTÃO 1"),
        _line(1, 30, "texto"),
        _line(2, 10, "QUESTÃO 3"),
        _line(2, 30, "texto"),
    ]
    result = detect_question_boundaries(lines)
    assert any("gap" in w for w in result.warnings)


def test_detects_duplicate_numbering():
    lines = [
        _line(1, 10, "QUESTÃO 1"),
        _line(1, 30, "primeira"),
        _line(2, 10, "QUESTÃO 1"),
        _line(2, 30, "segunda (não é percepção, sem marcador de seção)"),
    ]
    result = detect_question_boundaries(lines)
    assert any("duplicate" in w for w in result.warnings)


def test_no_markers_found_returns_empty_with_warning():
    lines = [_line(1, 10, "Nada de questões aqui.")]
    result = detect_question_boundaries(lines)
    assert result.spans == []
    assert result.warnings
