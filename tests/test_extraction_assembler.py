from __future__ import annotations

from enade.extraction.assembler import (
    CodeSegment,
    FigureSegment,
    TextSegment,
    _build_statement_segments,
    _find_alternative_starts,
    _line_in_region,
    _strip_leading_marker,
    detect_broken_words,
)
from enade.extraction.figures import VisualRegion
from enade.extraction.layout import Line


def _line(page: int, y: float, text: str, x: float = 30.0, mono: bool = False) -> Line:
    return Line(page_number=page, text=text, x0=x, y0=y, x1=x + 200, y1=y + 12, is_monospace=mono)


def test_find_alternative_starts_ignores_capital_letter_in_prose():
    # Statement starts with "A chance..." - must not be mistaken for alternative A.
    lines = [
        _line(1, 10, "A chance de uma criança de baixa renda ter um futuro melhor"),
        _line(1, 25, "que a realidade em que nasceu."),
        _line(1, 40, "A\t Primeiro texto da alternativa A."),
        _line(1, 55, "B\t Texto da alternativa B."),
        _line(1, 70, "C\t Texto da alternativa C."),
        _line(1, 85, "D\t Texto da alternativa D."),
        _line(1, 100, "E\t Texto da alternativa E."),
    ]
    starts = _find_alternative_starts(lines)
    assert starts is not None
    assert starts["A"] == 2  # not index 0


def test_find_alternative_starts_returns_none_when_sequence_incomplete():
    lines = [
        _line(1, 10, "Enunciado sem alternativas completas."),
        _line(1, 25, "A\t alternativa a"),
        _line(1, 40, "B\t alternativa b"),
        # missing C, D, E
    ]
    assert _find_alternative_starts(lines) is None


def test_find_alternative_starts_picks_rightmost_valid_sequence():
    # A red herring "B tenta..." style label appears before the real sequence.
    lines = [
        _line(1, 10, "B tenta entrar em algo (rótulo de figura, não alternativa)."),
        _line(1, 25, "Enunciado real da questão."),
        _line(1, 40, "A\t alternativa a"),
        _line(1, 55, "B\t alternativa b"),
        _line(1, 70, "C\t alternativa c"),
        _line(1, 85, "D\t alternativa d"),
        _line(1, 100, "E\t alternativa e"),
    ]
    starts = _find_alternative_starts(lines)
    assert starts is not None
    assert starts["A"] == 2


def test_line_in_region_never_swallows_an_alternative_marker():
    region = VisualRegion(page_number=1, bbox=(0, 0, 500, 500), element_count=1)
    alt_line = _line(1, 10, "A\t Texto da alternativa A")
    assert _line_in_region(alt_line, region) is False


def test_line_in_region_true_for_geometric_containment():
    region = VisualRegion(page_number=1, bbox=(0, 100, 500, 200), element_count=1)
    label_line = _line(1, 150, "Rótulo do diagrama")
    assert _line_in_region(label_line, region) is True


def test_line_in_region_false_on_different_page():
    region = VisualRegion(page_number=1, bbox=(0, 100, 500, 200), element_count=1)
    label_line = _line(2, 150, "Rótulo em outra página")
    assert _line_in_region(label_line, region) is False


def test_detect_broken_words_flags_ligature_artifact():
    text = "Isso é uma questi onada com um problema de justi ficação."
    hits = detect_broken_words(text)
    assert hits  # at least one artifact found
    assert any("questi o" in h for h in hits)


def test_detect_broken_words_clean_text_has_no_hits():
    text = "Isso é uma questão normal sem nenhum artefato de extração."
    assert detect_broken_words(text) == []


def test_build_statement_segments_inserts_figure_at_correct_position():
    lines = [
        _line(1, 10, "Parágrafo antes da figura."),
        _line(1, 100, "Parágrafo depois da figura."),
    ]
    region = VisualRegion(page_number=1, bbox=(0, 40, 500, 80), element_count=1)
    segments, placed = _build_statement_segments(lines, [region])
    assert placed == [0]
    kinds = [type(s).__name__ for s in segments]
    assert kinds == ["TextSegment", "FigureSegment", "TextSegment"]
    assert segments[0].text == "Parágrafo antes da figura."
    assert isinstance(segments[1], FigureSegment)
    assert segments[2].text == "Parágrafo depois da figura."


def test_build_statement_segments_preserves_code_block_line_breaks():
    lines = [
        _line(1, 10, "Texto normal antes do código."),
        _line(1, 30, "void f() {", mono=True),
        _line(1, 45, "  return 1;", mono=True),
        _line(1, 60, "}", mono=True),
        _line(1, 80, "Texto normal depois do código."),
    ]
    segments, _ = _build_statement_segments(lines, [])
    code_segments = [s for s in segments if isinstance(s, CodeSegment)]
    assert len(code_segments) == 1
    assert "void f() {" in code_segments[0].text
    assert "\n" in code_segments[0].text  # line breaks preserved, not space-joined
    text_segments = [s for s in segments if isinstance(s, TextSegment)]
    assert len(text_segments) == 2


def test_strip_leading_marker_removes_prefix_and_keeps_remainder():
    lines = [
        _line(1, 10, "QuEStãO 01 A chance de uma criança de baixa renda"),
        _line(1, 25, "continuação do enunciado."),
    ]
    stripped = _strip_leading_marker(lines)
    assert len(stripped) == 2
    assert stripped[0].text == "A chance de uma criança de baixa renda"
    assert stripped[1] is lines[1]


def test_strip_leading_marker_drops_line_with_nothing_left():
    lines = [
        _line(1, 10, "QUESTÃO DISCURSIVA 3"),
        _line(1, 25, "Primeiro parágrafo real do enunciado."),
    ]
    stripped = _strip_leading_marker(lines)
    assert len(stripped) == 1
    assert stripped[0].text == "Primeiro parágrafo real do enunciado."


def test_strip_leading_marker_no_op_when_no_marker_present():
    lines = [_line(1, 10, "Texto que não começa com um marcador de questão.")]
    assert _strip_leading_marker(lines) == lines


def test_strip_leading_marker_no_op_on_empty_list():
    assert _strip_leading_marker([]) == []
