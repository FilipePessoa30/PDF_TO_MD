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


def test_trailing_discursiva_marker_form_is_recognized():
    """2008-b's own discursive shape (PROMPT Phase 3A): the kind word comes
    *after* the number ("QUESTAO 9 - DISCURSIVA"), the mirror image of
    2021's "QUESTAO DISCURSIVA 1". Both must resolve to the same kind.
    """
    lines = [_line(1, 10, "QUESTÃO 9 – DISCURSIVA"), _line(1, 30, "Enunciado.")]
    result = detect_question_boundaries(lines)
    assert len(result.spans) == 1
    assert result.spans[0].kind == QuestionKind.DISCURSIVE
    assert result.spans[0].number == 9


def test_trailing_discursiva_marker_tolerates_em_dash_and_lower_case():
    """2008-b's own Q59 marker uses an em dash (U+2014) and lower-case
    "Discursiva", unlike every other discursive marker in the same booklet
    (en dash, upper case) - confirmed by direct codepoint inspection of the
    source PDF, not assumed uniform.
    """
    lines = [_line(1, 10, "QUESTÃO 59 — Discursiva"), _line(1, 30, "Enunciado.")]
    result = detect_question_boundaries(lines)
    assert len(result.spans) == 1
    assert result.spans[0].kind == QuestionKind.DISCURSIVE
    assert result.spans[0].number == 59


def test_plain_objective_marker_with_no_trailing_text_is_unaffected():
    lines = [_line(1, 10, "QUESTÃO 21"), _line(1, 30, "Enunciado.")]
    result = detect_question_boundaries(lines)
    assert result.spans[0].kind == QuestionKind.OBJECTIVE
    assert result.spans[0].number == 21


def test_combined_numbering_does_not_flag_interleaved_discursives_as_gaps():
    """PROMPT Phase 3A: a booklet whose discursive markers interleave the
    same printed number stream as its objectives (2008-b's Q9/Q10, Q20,
    Q39/Q40...) must not have every interleaving reported as a "gap" -
    that would misreport correct, complete numbering as broken.
    """
    lines = [
        _line(1, 10, "QUESTÃO 8"),
        _line(1, 30, "Enunciado objetiva 8."),
        _line(2, 10, "QUESTÃO 9 – DISCURSIVA"),
        _line(2, 30, "Enunciado discursiva 9."),
        _line(3, 10, "QUESTÃO 10 – DISCURSIVA"),
        _line(3, 30, "Enunciado discursiva 10."),
        _line(4, 10, "QUESTÃO 11"),
        _line(4, 30, "Enunciado objetiva 11."),
    ]
    result = detect_question_boundaries(lines, combined_numbering=True)
    assert result.warnings == []


def test_combined_numbering_still_detects_a_real_gap():
    lines = [
        _line(1, 10, "QUESTÃO 8"),
        _line(1, 30, "Enunciado objetiva 8."),
        # 9 missing entirely
        _line(2, 10, "QUESTÃO 10 – DISCURSIVA"),
        _line(2, 30, "Enunciado discursiva 10."),
    ]
    result = detect_question_boundaries(lines, combined_numbering=True)
    assert any("gap" in w and "combined" in w for w in result.warnings)


def test_combined_numbering_still_detects_a_real_duplicate():
    lines = [
        _line(1, 10, "QUESTÃO 9 – DISCURSIVA"),
        _line(1, 30, "Enunciado discursiva 9 (primeira vez)."),
        _line(2, 10, "QUESTÃO 9 – DISCURSIVA"),
        _line(2, 30, "Enunciado discursiva 9 (duplicada)."),
    ]
    result = detect_question_boundaries(lines, combined_numbering=True)
    assert any("duplicate" in w and "combined" in w for w in result.warnings)


def test_separate_numbering_default_is_unchanged_by_combined_numbering_param():
    """default (combined_numbering=False) must reproduce the exact prior
    per-kind gap behaviour - 2011/2021's own discursive 1..5 stream is
    unaffected by this Phase 3A addition.
    """
    lines = [
        _line(1, 10, "QUESTÃO DISCURSIVA 1"),
        _line(1, 30, "Enunciado."),
        _line(2, 10, "QUESTÃO DISCURSIVA 3"),  # discursive 2 missing
        _line(2, 30, "Enunciado."),
    ]
    result = detect_question_boundaries(lines)
    assert any("discursive" in w and "gap" in w for w in result.warnings)


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


def test_incidental_mention_of_perception_questionnaire_is_not_a_perception_page():
    """Regression test: a Phase 1B faux-space fix correctly reconstructed
    "questi onario" -> "questionario" on the real 2021 booklet's cover page,
    which incidentally carries a structure-table row label reading exactly
    "Questionário de Percepção da Prova" (identical text to the real section
    heading, just without any of the reused QUESTAO 01..09 markers next to
    it). That page must not be excluded as if it were the actual
    questionnaire - it has real question markers of its own that must stay
    in the academic question bank.
    """
    lines = [
        _line(1, 10, "Questionário de Percepção da Prova"),  # table row label, not a heading
        _line(1, 30, "5. As respostas do questionário de percepção da prova deverão ser..."),
        _line(2, 10, "QUESTÃO DISCURSIVA 1"),
        _line(2, 30, "Enunciado real da discursiva 1."),
    ]
    result = detect_question_boundaries(lines)
    assert result.perception_pages == []
    assert len(result.spans) == 1
    assert result.spans[0].kind == QuestionKind.DISCURSIVE
    # the discursive's own page (2) must never have been excluded
    assert any(ln.page_number == 2 for ln in result.spans[0].lines)


def test_perception_page_is_excluded_with_the_2008_b_sobre_a_prova_wording():
    """2008-b's own questionnaire heading reads "...PERCEPCAO SOBRE A PROVA"
    (PROMPT Phase 3A, confirmed against the real PDF), not 2021's "...DA
    PROVA" - both must be recognized as the same heading, or this page's
    reused QUESTAO 1..9 markers silently double-count Formacao Geral's own
    Q1..Q9 (the real bug this regression test catches).
    """
    lines = [
        _line(1, 10, "QUESTÃO 1"),
        _line(1, 30, "Enunciado real da questão 1."),
        _line(2, 10, "QUESTÃO 1"),  # reused numbering inside the questionnaire
        _line(2, 30, "Qual o grau de dificuldade desta prova?"),
        _line(2, 200, "QUESTIONÁRIO DE PERCEPÇÃO SOBRE A PROVA"),
    ]
    result = detect_question_boundaries(lines)
    assert result.perception_pages == [2]
    assert len(result.spans) == 1
    assert result.spans[0].number == 1
    assert all(ln.page_number != 2 for ln in result.spans[0].lines)


def test_perception_heading_alone_without_reused_markers_is_not_excluded():
    """A bare heading-shaped line with no co-located QUESTAO N markers on the
    same page is not enough evidence to exclude the page - see module
    docstring on why the heading text alone is ambiguous.
    """
    lines = [
        _line(1, 10, "QUESTÃO 1"),
        _line(1, 30, "Enunciado real da questão 1."),
        _line(2, 10, "Questionário de Percepção da Prova"),  # heading text, no markers nearby
        _line(2, 30, "Texto de rodapé qualquer."),
    ]
    result = detect_question_boundaries(lines)
    assert result.perception_pages == []


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
