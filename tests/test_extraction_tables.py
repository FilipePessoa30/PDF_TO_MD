from __future__ import annotations

from enade.extraction.layout import Line
from enade.extraction.tables import detect_tables, render_table_markdown


def _cell(
    page: int, y: float, x: float, text: str, width: float = 8.0, height: float = 14.0
) -> Line:
    return Line(page_number=page, text=text, x0=x, y0=y, x1=x + width, y1=y + height)


# A clean 4-column x 4-row (1 header + 3 data) table, no grid lines - the
# same shape as D3's real truth table (see docs/decisions.md, "Phase 1C" ADR).
_COLS = (30.0, 100.0, 170.0, 240.0)
_HEADERS = ("Nome", "Idade", "Cidade", "Nota")
_ROWS = (
    ("Ana", "20", "SP", "8.5"),
    ("Bruno", "22", "RJ", "7.0"),
    ("Carla", "19", "MG", "9.2"),
)


def _clean_table_lines(page: int = 1, y0: float = 100.0, row_gap: float = 20.0) -> list[Line]:
    lines: list[Line] = []
    for row_index, row in enumerate((_HEADERS, *_ROWS)):
        y = y0 + row_index * row_gap
        for x, text in zip(_COLS, row, strict=True):
            lines.append(_cell(page, y, x, text))
    return lines


def test_detects_clean_table_with_headers_and_multiple_rows_and_columns():
    tables = detect_tables(_clean_table_lines())
    assert len(tables) == 1
    table = tables[0]
    assert table.headers == list(_HEADERS)
    assert table.rows == [list(row) for row in _ROWS]


def test_detects_table_with_logical_symbols_and_vf_cells():
    cols = (40.0, 110.0, 180.0)
    headers = ("a", "b", "a ∧ ¬ b")
    rows = (
        ("F", "F", "V"),
        ("F", "V", "F"),
        ("V", "F", "V"),
    )
    lines = []
    for row_index, row in enumerate((headers, *rows)):
        y = 200.0 + row_index * 25.0
        for x, text in zip(cols, row, strict=True):
            lines.append(_cell(1, y, x, text))
    tables = detect_tables(lines)
    assert len(tables) == 1
    assert tables[0].headers == list(headers)
    assert tables[0].rows == [list(row) for row in rows]


def test_small_alignment_jitter_within_tolerance_still_clusters_correctly():
    lines = _clean_table_lines()
    jittered = [
        Line(
            page_number=ln.page_number,
            text=ln.text,
            x0=ln.x0 + (2.0 if i % 2 == 0 else -2.0),
            y0=ln.y0 + (1.0 if i % 3 == 0 else -1.0),
            x1=ln.x1 + (2.0 if i % 2 == 0 else -2.0),
            y1=ln.y1 + (1.0 if i % 3 == 0 else -1.0),
        )
        for i, ln in enumerate(lines)
    ]
    tables = detect_tables(jittered)
    assert len(tables) == 1
    assert tables[0].headers == list(_HEADERS)
    assert tables[0].rows == [list(row) for row in _ROWS]


def test_missing_token_leaves_a_blank_cell_never_fabricated():
    lines = _clean_table_lines()
    # Drop the "Cidade" cell (column index 2) from the second data row (row
    # index 2 overall: header=0, Ana=1, Bruno=2) - still >= MIN_CELLS_PER_ROW
    # (3 of 4 remain), so the row survives as a candidate row with one gap.
    lines = [ln for ln in lines if not (ln.y0 == 100.0 + 2 * 20.0 and ln.x0 == 170.0)]
    tables = detect_tables(lines)
    assert len(tables) == 1
    assert tables[0].rows[1] == ["Bruno", "22", "", "7.0"]


def test_shifted_column_does_not_fabricate_an_extra_column():
    lines = _clean_table_lines()
    # Shift "Carla" row's "MG" cell (column index 2) far enough (+30pt,
    # well past COLUMN_X_TOLERANCE) that it can no longer be attributed to
    # the real column - it must not silently invent a 5th column, and the
    # real column's cell for that row must stay blank rather than guessed.
    shifted = []
    for ln in lines:
        if ln.y0 == 100.0 + 3 * 20.0 and ln.x0 == 170.0:
            shifted.append(
                Line(
                    page_number=ln.page_number,
                    text=ln.text,
                    x0=ln.x0 + 30.0,
                    y0=ln.y0,
                    x1=ln.x1 + 30.0,
                    y1=ln.y1,
                )
            )
        else:
            shifted.append(ln)
    tables = detect_tables(shifted)
    assert len(tables) == 1
    table = tables[0]
    assert len(table.headers) == 4  # never grew a 5th column for the orphan cell
    assert table.rows[2] == ["Carla", "19", "", "9.2"]


def test_incomplete_row_in_the_middle_breaks_the_run():
    lines = _clean_table_lines()
    # Insert a genuinely incomplete row (only 1 cell - below
    # MIN_CELLS_PER_ROW) between the header/data run and a trailing row;
    # the trailing row then has only itself (< MIN_TABLE_ROWS) and must not
    # be folded into the preceding table.
    lines.append(_cell(1, 100.0 + 4 * 20.0, 30.0, "Nota de rodapé"))
    lines.extend(
        _cell(1, 100.0 + 5 * 20.0, x, text)
        for x, text in zip(_COLS, ("Davi", "21", "PR", "6.0"), strict=True)
    )
    tables = detect_tables(lines)
    assert len(tables) == 1  # only the original 4-row run
    assert tables[0].rows == [list(row) for row in _ROWS]


def test_non_rectangular_region_is_a_conservative_failure():
    # Every row uses entirely different, non-recurring x-positions - no
    # real shared column grid, so nothing should be reported as a table.
    lines = [
        _cell(1, 100.0, 30.0, "a"),
        _cell(1, 100.0, 300.0, "b"),
        _cell(1, 100.0, 500.0, "c"),
        _cell(1, 130.0, 45.0, "d"),
        _cell(1, 130.0, 320.0, "e"),
        _cell(1, 130.0, 520.0, "f"),
        _cell(1, 160.0, 60.0, "g"),
        _cell(1, 160.0, 340.0, "h"),
        _cell(1, 160.0, 540.0, "i"),
    ]
    assert detect_tables(lines) == []


def test_conflicting_same_row_same_column_cells_are_rejected():
    lines = _clean_table_lines()
    # Add a second, bogus cell landing in the exact same row/column slot as
    # an existing one - an ambiguous/misaligned grid must be rejected
    # outright, never silently picking one of the two.
    lines.append(_cell(1, 100.0, 30.0, "Duplicado"))
    assert detect_tables(lines) == []


def test_too_few_rows_is_not_a_table():
    lines = _clean_table_lines()[:8]  # header + 1 data row only (2 rows total)
    assert detect_tables(lines) == []


def test_tables_are_grouped_per_page_never_merged_across_pages():
    page1 = _clean_table_lines(page=1)
    page2 = _clean_table_lines(page=2, y0=100.0)
    tables = detect_tables(page1 + page2)
    assert len(tables) == 2
    assert {t.page_number for t in tables} == {1, 2}


def test_detection_is_deterministic():
    lines = _clean_table_lines()
    first = detect_tables(lines)
    second = detect_tables(lines)
    assert first == second


def test_render_table_markdown_produces_valid_gfm_pipe_table():
    tables = detect_tables(_clean_table_lines())
    rendered = render_table_markdown(tables[0])
    lines = rendered.splitlines()
    assert lines[0] == "| Nome | Idade | Cidade | Nota |"
    assert lines[1] == "| --- | --- | --- | --- |"
    assert lines[2] == "| Ana | 20 | SP | 8.5 |"
    assert len(lines) == 2 + len(_ROWS)


def test_render_table_markdown_escapes_pipe_characters_in_cell_text():
    lines = _clean_table_lines()
    lines[0] = Line(
        page_number=1, text="A | B", x0=lines[0].x0, y0=lines[0].y0, x1=lines[0].x1, y1=lines[0].y1
    )
    tables = detect_tables(lines)
    rendered = render_table_markdown(tables[0])
    assert "A \\| B" in rendered
