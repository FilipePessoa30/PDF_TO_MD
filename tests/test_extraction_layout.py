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


def test_detect_column_margins_splits_at_widest_gap_not_top_two_by_frequency():
    # A column can have two recurring indentation levels (a paragraph
    # margin and a more-indented list-item margin) that are each more
    # frequent than the other column's own single margin. Picking "top 2 by
    # raw count" would wrongly pair the two same-column buckets together;
    # the widest-gap split must still find the real left/right boundary
    # (2011 unified booklet, pages 5/16/21/30 - see layout.py docstring).
    lines = []
    for i in range(6):
        lines.append(_line(295, i * 20, f"corpo da coluna direita {i}", x1=595))
    for i in range(4):
        lines.append(_line(315, 200 + i * 20, f"item indentado da direita {i}", x1=595))
    for i in range(4):
        lines.append(_line(30, i * 20, f"coluna esquerda mais curta {i}", x1=280))
    margins = detect_column_margins(lines)
    assert margins is not None
    left_margin, right_margin = margins
    assert left_margin == 30
    assert right_margin == 295


def test_merge_orphan_markers_only_pairs_within_the_same_column():
    # A right-column orphan marker must never merge with left-column text
    # just because it happens to be closer in Y alone (2011 unified
    # booklet, Q10: alternative B's marker merged with an unrelated
    # left-column fragment 4pt away in Y, instead of its own right-column
    # partner 7.6pt away - see layout.py docstring for the full story).
    margins = (30.0, 300.0)
    lines = [
        _line(300, 100, "B"),  # right-column orphan marker
        _line(28, 104, "fragmento da coluna esquerda não relacionado", x1=280),  # closer in Y only
        _line(300, 108, "155"),  # the real, same-column partner
    ]
    merged = _merge_orphan_markers(lines, margins)
    assert len(merged) == 2
    right_result = next(ln for ln in merged if ln.x0 >= 300)
    assert right_result.text.startswith("B\t")
    assert "155" in right_result.text
    left_result = next(ln for ln in merged if ln.x0 < 300)
    assert left_result.text == "fragmento da coluna esquerda não relacionado"


def test_detect_column_margins_excludes_chrome_lines_from_evidence():
    # A page-furniture header (e.g. a running title) repeats at the same
    # left margin on every page regardless of whether the body below it is
    # one or two columns - it must not, by itself, manufacture a false
    # left-column margin out of an otherwise single-column page (2011
    # unified booklet, page 18 / Discursiva 3 - see layout.py docstring).
    lines = [
        _line(28, 10, "2011"),  # chrome: exact year line
        _line(28, 30, "exame nacional de desempenho dos estudantes"),  # chrome: exact header line
        _line(
            28, 460, "desenvolva o algoritmo solicitado a seguir."
        ),  # single real body line, left
    ]
    for i in range(4):
        lines.append(_line(140, 60 + i * 20, f"parágrafo indentado ao redor da figura {i}", x1=440))
    assert detect_column_margins(lines) is None
