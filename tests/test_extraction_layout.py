from __future__ import annotations

from enade.extraction.layout import Line, _merge_orphan_markers, detect_column_margins


def _line(x0: float, y0: float, text: str, x1: float | None = None) -> Line:
    return Line(
        page_number=1, text=text, x0=x0, y0=y0, x1=x1 if x1 is not None else x0 + 150, y1=y0 + 12
    )


def test_detect_column_margins_finds_two_column_layout():
    lines = []
    for i in range(6):
        lines.append(_line(30, i * 20, f"linha esquerda numero {i} com texto suficiente", x1=280))
        lines.append(_line(290, i * 20, f"linha direita numero {i} com texto suficiente", x1=540))
    margins = detect_column_margins(lines)
    assert margins is not None
    left_margin, right_margin = margins
    assert left_margin == 30
    assert right_margin == 290


def test_detect_column_margins_none_for_single_column_page():
    lines = [_line(30, i * 20, f"parágrafo único linha {i}", x1=530) for i in range(6)]
    assert detect_column_margins(lines) is None


def test_detect_column_margins_ignores_short_figure_labels():
    # A handful of short labels at a different x should not trigger a false
    # column split on an otherwise single-column page.
    lines = [_line(30, i * 20, f"parágrafo linha {i} com bastante texto", x1=530) for i in range(6)]
    lines.append(_line(300, 50, "rótulo"))  # short, width < MIN_COLUMN_LINE_WIDTH
    lines.append(_line(310, 70, "outro"))
    assert detect_column_margins(lines) is None


def test_merge_orphan_markers_joins_bare_letter_with_nearby_line():
    lines = [
        _line(30, 100, "C"),  # orphan marker, no text
        _line(47, 98, "Texto da alternativa C que ficou separado."),
    ]
    merged = _merge_orphan_markers(lines)
    assert len(merged) == 1
    assert merged[0].text.startswith("C\t")
    assert "Texto da alternativa C" in merged[0].text


def test_merge_orphan_markers_leaves_normal_lines_untouched():
    lines = [_line(30, 10, "A\t Texto já junto, nada a fazer.")]
    merged = _merge_orphan_markers(lines)
    assert merged == lines


def test_merge_orphan_markers_ignores_distant_candidates():
    lines = [
        _line(30, 10, "C"),
        _line(30, 500, "Texto muito distante, não deve ser unido."),
    ]
    merged = _merge_orphan_markers(lines)
    # No plausible partner within tolerance - orphan line is kept as-is, not lost.
    assert len(merged) == 2
