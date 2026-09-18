from __future__ import annotations

import pymupdf

from enade.extraction.answer_standard import (
    _rescue_table_row_numbers,
    find_answer_standard_images,
    parse_answer_standard,
)
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


# --- PROMPT Fase 3U: visual-only answer standards (2008-b D59) -------------


def _insert_image(page: pymupdf.Page, rect: tuple[float, float, float, float], color=(0, 0, 0)):
    pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 10, 10), False)
    pix.set_rect(pix.irect, color)
    page.insert_image(pymupdf.Rect(*rect), pixmap=pix)


def _blank_doc() -> pymupdf.Document:
    doc = pymupdf.open()
    doc.new_page(width=600, height=800)
    return doc


def test_parse_answer_standard_creates_visual_only_entry_for_zero_text_rubric():
    """The exact 2008-b D59 shape: "Questao 59" immediately followed (no
    text of any kind) by a real embedded image, then "Questao 60" - must
    produce a `text=""` entry whose own page_bounds correctly re-locates
    that image via find_answer_standard_images.
    """
    doc = _blank_doc()
    page = doc[0]
    page.insert_text((90, 200), "Questao 59", fontsize=12)
    _insert_image(page, (100, 220, 300, 400))
    page.insert_text((90, 420), "Questao 60", fontsize=12)
    result = parse_answer_standard(doc)
    assert 59 in result.entries
    entry = result.entries[59]
    assert entry.text == ""
    images = find_answer_standard_images(doc, entry)
    assert len(images) == 1
    assert images[0][0] == 1


def test_parse_answer_standard_never_creates_entry_for_zero_text_zero_image():
    """A marker with genuinely nothing after it (no text, no image) must
    still produce no entry at all - the pre-existing `missing` warning
    behavior, unchanged.
    """
    doc = _blank_doc()
    page = doc[0]
    page.insert_text((90, 200), "Questao 59", fontsize=12)
    page.insert_text((90, 420), "Questao 60", fontsize=12)
    result = parse_answer_standard(doc)
    assert 59 not in result.entries
    assert any("59" in w for w in result.warnings)


def test_parse_answer_standard_never_attributes_an_image_before_the_marker():
    """The exact D40-vs-D59 cross-contamination risk: an image sitting
    *before* the current marker's own line (i.e. belonging to the
    *previous* rubric) must never be swept into a later, zero-text entry.
    """
    doc = _blank_doc()
    page = doc[0]
    _insert_image(page, (100, 50, 300, 150))  # belongs to nothing/no marker yet
    page.insert_text((90, 200), "Questao 59", fontsize=12)
    page.insert_text((90, 420), "Questao 60", fontsize=12)
    result = parse_answer_standard(doc)
    # No text and no image *after* the marker and before the next one -
    # correctly produces no entry, never reaching backward for the earlier
    # image.
    assert 59 not in result.entries


def test_parse_answer_standard_visual_only_scoped_to_markers_own_page():
    """An image on a *different* page than the marker's own must never be
    attributed to a zero-text entry - the search is deliberately scoped to
    one page only (PROMPT Fase 3U: no real corpus case spans pages with
    zero text on all of them).
    """
    doc = pymupdf.open()
    doc.new_page(width=600, height=800)
    doc.new_page(width=600, height=800)
    page1 = doc[0]
    page1.insert_text((90, 700), "Questao 59", fontsize=12)
    page2 = doc[1]
    _insert_image(page2, (100, 50, 300, 150))
    page2.insert_text((90, 200), "Questao 60", fontsize=12)
    result = parse_answer_standard(doc)
    assert 59 not in result.entries


def test_find_answer_standard_images_orders_by_position_not_insertion_order():
    """PROMPT Fase 3U section 14: two images inserted in reverse visual
    order (bottom one first) must still be returned top-to-bottom.
    """
    from enade.extraction.answer_standard import AnswerStandardEntry

    doc = _blank_doc()
    page = doc[0]
    _insert_image(page, (100, 500, 200, 600))  # bottom image, inserted first
    _insert_image(page, (100, 100, 200, 200))  # top image, inserted second
    entry = AnswerStandardEntry(number=1, pages=[1], text="x", page_bounds={1: (0.0, 800.0)})
    images = find_answer_standard_images(doc, entry)
    assert len(images) == 2
    assert images[0][1][1] < images[1][1][1]  # first result is the topmost (smaller y0)
