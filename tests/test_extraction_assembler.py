from __future__ import annotations

from enade.extraction.assembler import (
    CodeSegment,
    FigureSegment,
    TextSegment,
    _build_statement_segments,
    _find_alternative_starts,
    _line_in_region,
    _render_code_lines,
    _strip_leading_marker,
    _strip_line_number_gutter,
    detect_broken_words,
)
from enade.extraction.figures import VisualRegion
from enade.extraction.layout import Line


def _line(
    page: int, y: float, text: str, x: float = 30.0, mono: bool = False, width: float = 200.0
) -> Line:
    return Line(page_number=page, text=text, x0=x, y0=y, x1=x + width, y1=y + 12, is_monospace=mono)


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
    segments, placed, placed_tables = _build_statement_segments(lines, [region])
    assert placed == [0]
    assert placed_tables == []
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
    segments, _, _ = _build_statement_segments(lines, [])
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


# --- Phase 1C: code reconstruction (blank lines, indentation) ----------------


def test_render_code_lines_preserves_a_real_blank_line():
    # Mirrors D5's heapify() listing (page 17): a real blank line sits
    # between "int e, d, max, aux;" and "e = left(i);" - modal line pitch
    # here is 15pt, and the gap to the next line is ~30pt (2x), i.e.
    # exactly one blank line, not a paragraph-style artifact to collapse.
    lines = [
        _line(1, 100.0, "void heapify(int *a, int n, int i)", x=290.0, mono=True),
        _line(1, 115.0, "{", x=290.0, mono=True),
        _line(1, 130.0, "   int e, d, max, aux;", x=290.0, mono=True),
        _line(1, 160.0, "   e = left(i);", x=290.0, mono=True),  # +30, not +15
        _line(1, 175.0, "   d = right(i);", x=290.0, mono=True),
    ]
    rendered = _render_code_lines(lines)
    assert rendered.splitlines() == [
        "void heapify(int *a, int n, int i)",
        "{",
        "   int e, d, max, aux;",
        "",
        "   e = left(i);",
        "   d = right(i);",
    ]


def test_render_code_lines_does_not_invent_blank_lines_for_normal_pitch():
    lines = [
        _line(1, 100.0, "int a = 1;", x=290.0, mono=True),
        _line(1, 115.0, "int b = 2;", x=290.0, mono=True),
        _line(1, 130.0, "int c = 3;", x=290.0, mono=True),
    ]
    rendered = _render_code_lines(lines)
    assert rendered.splitlines() == ["int a = 1;", "int b = 2;", "int c = 3;"]


def test_render_code_lines_reconstructs_relative_indentation():
    lines = [
        _line(1, 100.0, "void f() {", x=290.0, mono=True),
        _line(1, 115.0, "return 1;", x=296.0, mono=True),  # +6pt = 1 char
        _line(1, 130.0, "}", x=290.0, mono=True),
    ]
    rendered = _render_code_lines(lines)
    assert rendered.splitlines() == ["void f() {", " return 1;", "}"]


# --- Phase 1C: region containment respects column separation (D5) ------------


def test_line_in_region_ignores_same_y_band_content_in_a_different_column():
    # A figure region confined to the left column (x in [29, 276]) must not
    # swallow a code line at the same Y sitting in the right column (x
    # starting at 291.5) - see docs/decisions.md, "Phase 1C" ADR (D5's
    # heapify() body was silently dropped this way before the fix).
    region = VisualRegion(page_number=1, bbox=(29.0, 100.0, 276.4, 462.7), element_count=16)
    code_line = _line(1, 200.0, "int e, d, max, aux;", x=291.5, mono=True, width=100.0)
    assert _line_in_region(code_line, region) is False


def test_line_in_region_still_true_for_a_genuine_same_column_label():
    region = VisualRegion(page_number=1, bbox=(29.0, 100.0, 276.4, 350.0), element_count=16)
    label_line = _line(1, 320.0, "Processo A", x=32.6, width=50.0)
    assert _line_in_region(label_line, region) is True


def test_strip_leading_marker_no_op_on_empty_list():
    assert _strip_leading_marker([]) == []


# --- Phase 1C: line-number gutter removal (Q20) -------------------------------


def _gutter_line(y: float, number: str, sep: str = "\t") -> Line:
    text = f"{sep}{number}"
    return Line(page_number=1, text=text, x0=29.8, y0=y, x1=52.0, y1=y + 20.4, is_monospace=True)


def _code_line(y: float, text: str, x: float = 65.8) -> Line:
    return Line(
        page_number=1, text=text, x0=x, y0=y, x1=x + len(text) * 7.2, y1=y + 20.4, is_monospace=True
    )


def test_strip_line_number_gutter_removes_standalone_gutter_lines():
    lines = [
        _gutter_line(100.0, "1"),
        _code_line(100.0, "#include <stdio.h>"),
        _gutter_line(120.4, "2"),
        _code_line(120.4, "#define TAM 10"),
        _gutter_line(140.8, "3"),
        _code_line(140.8, "int f(int x){"),
    ]
    stripped = _strip_line_number_gutter(lines)
    assert [ln.text for ln in stripped] == [
        "#include <stdio.h>",
        "#define TAM 10",
        "int f(int x){",
    ]


def test_strip_line_number_gutter_handles_a_line_merged_with_its_gutter_number():
    # Mirrors Q20's real row 11: PyMuPDF fused the gutter number into the
    # same physical Line as the code that follows it - the merged line's
    # own x0 (29.8, dragged left by the gutter) must not become the new
    # indentation baseline for the rest of the block (see docs/decisions.md).
    lines = [
        _gutter_line(100.0, "1"),
        _code_line(100.0, "int f(int x){"),
        _gutter_line(120.4, "2"),
        _code_line(120.4, "}"),
        Line(
            page_number=1,
            text="\t11 \t int g(int x, int y){",
            x0=29.8,
            y0=140.8,
            x1=250.0,
            y1=161.2,
            is_monospace=True,
        ),
    ]
    stripped = _strip_line_number_gutter(lines)
    assert [ln.text for ln in stripped] == ["int f(int x){", "}", "int g(int x, int y){"]
    merged_result = stripped[-1]
    assert merged_result.x0 == 65.8  # reconstructed from the unaffected lines' own baseline


def test_strip_line_number_gutter_leaves_a_lone_numeric_line_untouched():
    # Only one bare-digit line, no corroborating recurrence and no
    # unaffected non-gutter-shaped lines to establish a baseline from -
    # left alone rather than guessed away (PROMPT section 8.1).
    lines = [_gutter_line(100.0, "1")]
    assert _strip_line_number_gutter(lines) == lines


def test_strip_line_number_gutter_no_op_when_nothing_gutter_shaped():
    lines = [_code_line(100.0, "int x = 1;"), _code_line(120.4, "int y = 2;")]
    assert _strip_line_number_gutter(lines) == lines


def test_render_code_lines_after_gutter_removal_has_correct_indentation():
    lines = [
        _code_line(100.0, "int f(int x){", x=65.8),
        _code_line(120.4, "return x;", x=101.8),
        _code_line(140.8, "}", x=65.8),
    ]
    rendered = _render_code_lines(_strip_line_number_gutter(lines))
    assert rendered.splitlines() == ["int f(int x){", "      return x;", "}"]
