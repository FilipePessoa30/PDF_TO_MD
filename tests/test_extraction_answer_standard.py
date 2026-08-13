from __future__ import annotations

from enade.extraction.answer_standard import _rescue_table_row_numbers
from enade.extraction.layout import Line


def _line(page: int, y: float, text: str, x: float = 90.0, width: float = 40.0) -> Line:
    return Line(page_number=page, text=text, x0=x, y0=y, x1=x + width, y1=y + 12)


def test_rescue_recovers_a_real_bit_width_table_row():
    # 2011 D5's own answer standard: "Rotulo Linha Palavra" (header, kept
    # already) followed by "13 17 2" (a real data row, chrome-stripped by
    # is_chrome_line before this rescue runs) - see docs/decisions.md,
    # Phase 2D ADR.
    header = _line(1, 300.0, "Rotulo Linha Palavra", x=90.0, width=200.0)
    cell_a = _line(1, 320.0, "13", x=95.0)
    cell_b = _line(1, 320.0, "17", x=127.0)
    cell_c = _line(1, 320.0, "2", x=164.0)
    buffer = [header]
    raw_lines = [header, cell_a, cell_b, cell_c]
    rescued = _rescue_table_row_numbers(raw_lines, buffer)
    assert {ln.text for ln in rescued} == {"13", "17", "2"}


def test_rescue_never_recovers_a_lone_page_number():
    # A single bare-number line - indistinguishable from a running page
    # number - must never be rescued on its own.
    header = _line(1, 300.0, "Texto qualquer", x=28.0, width=200.0)
    page_number_footer = _line(1, 740.0, "5", x=285.0, width=10.0)
    buffer = [header]
    raw_lines = [header, page_number_footer]
    assert _rescue_table_row_numbers(raw_lines, buffer) == []


def test_rescue_ignores_numbers_already_in_the_buffer():
    header = _line(1, 300.0, "Rotulo Palavra", x=90.0, width=200.0)
    cell_a = _line(1, 320.0, "30", x=95.0)
    cell_b = _line(1, 320.0, "2", x=135.0)
    # cell_a is already in the buffer (not chrome-filtered for some other
    # reason) - it must not be double-counted or duplicated in the result.
    buffer = [header, cell_a]
    raw_lines = [header, cell_a, cell_b]
    rescued = _rescue_table_row_numbers(raw_lines, buffer)
    assert [ln.text for ln in rescued] == ["2"]


def test_rescue_respects_row_y_tolerance():
    # Two bare numbers far apart in Y are two different, unrelated rows -
    # or one is a genuine page footer - never merged into one "row".
    header = _line(1, 300.0, "Rotulo Palavra", x=90.0, width=200.0)
    cell_a = _line(1, 320.0, "13", x=95.0)
    unrelated_number = _line(1, 700.0, "9", x=95.0)
    buffer = [header]
    raw_lines = [header, cell_a, unrelated_number]
    rescued = _rescue_table_row_numbers(raw_lines, buffer)
    assert rescued == []
