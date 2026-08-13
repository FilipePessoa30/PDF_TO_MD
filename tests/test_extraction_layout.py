from __future__ import annotations

from enade.extraction.layout import Line, _merge_orphan_markers, detect_column_margins
from enade.extraction.layout_overrides import LayoutOverride, LayoutOverrideSet


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


def test_merge_orphan_markers_respects_a_matching_override():
    # A table-header cell that would otherwise merge as an orphan marker
    # stays a standalone line when a hash-and-bbox-locked override covers
    # it (PROMPT Phase 2B section 6, Level 3 - see layout_overrides.py).
    lines = [
        _line(112.0, 119.8, "A", x1=119.5),
        _line(300.0, 500.0, "conteúdo qualquer que poderia virar parceiro", x1=550),
    ]
    override_set = LayoutOverrideSet(
        overrides=[
            LayoutOverride(
                pdf_sha256="deadbeef" * 8,
                page=1,
                bbox=(100.0, 115.0, 215.0, 138.0),
                rule="exclude_from_orphan_marker_merge",
                question_id="enade-2011-computing-q22",
                reason="test",
                evidence="test",
                status="reviewed",
            )
        ]
    )
    merged = _merge_orphan_markers(
        lines, margins=None, overrides=override_set, pdf_sha256="deadbeef" * 8
    )
    assert len(merged) == 2
    assert any(ln.text == "A" for ln in merged)  # never merged - stayed standalone


def test_merge_orphan_markers_ignores_override_for_a_different_pdf_hash():
    lines = [_line(112.0, 119.8, "A", x1=119.5), _line(113.0, 121.0, "B rótulo qualquer", x1=250)]
    override_set = LayoutOverrideSet(
        overrides=[
            LayoutOverride(
                pdf_sha256="deadbeef" * 8,
                page=1,
                bbox=(100.0, 115.0, 215.0, 138.0),
                rule="exclude_from_orphan_marker_merge",
                question_id="enade-2011-computing-q22",
                reason="test",
                evidence="test",
                status="reviewed",
            )
        ]
    )
    # Same bbox/page, but a different pdf_sha256 than the override declares -
    # normal orphan-marker behavior applies (the merge happens as usual).
    merged = _merge_orphan_markers(
        lines, margins=None, overrides=override_set, pdf_sha256="cafebabe" * 8
    )
    assert len(merged) == 1
    assert merged[0].text.startswith("A\t")


def test_merge_orphan_markers_applies_a_matching_fraction_merge_override():
    # PROMPT Phase 2D section 8 (positive case): Q10's own stacked
    # two-line fraction - marker "A", numerator "61" above, denominator
    # "73" below (the general search already finds "73" as the closest
    # partner) - the override supplies the numerator explicitly.
    marker = _line(300.7, 309.8, "A", x1=321.0)
    numerator = _line(330.0, 302.2, "61", x1=341.2)
    denominator = _line(330.0, 317.5, "73", x1=341.2)
    override_set = LayoutOverrideSet(
        overrides=[
            LayoutOverride(
                pdf_sha256="deadbeef" * 8,
                page=1,
                bbox=(298.0, 307.0, 323.0, 326.0),
                secondary_bbox=numerator.bbox,
                rule="force_fraction_merge",
                question_id="enade-2011-computing-q10",
                reason="test",
                evidence="test",
                status="reviewed",
            )
        ]
    )
    merged = _merge_orphan_markers(
        [marker, numerator, denominator],
        margins=None,
        overrides=override_set,
        pdf_sha256="deadbeef" * 8,
    )
    assert len(merged) == 1
    assert merged[0].text == "A\t61/73"


def test_merge_orphan_markers_fraction_override_never_matches_unrelated_pairs():
    # PROMPT Phase 2D section 8 (negative case): a 2021-Q34-shaped page -
    # independent single-letter-node + single-digit-value pairs from a
    # Dijkstra graph listing. No force_fraction_merge override is declared
    # for this (different) pdf_sha256, so the general merge must behave
    # exactly as before: each marker pairs only with its own closest
    # partner, never splicing in a neighboring pair's own value.
    lines = [
        _line(29.8, 406.0, "C", x1=40.0),
        _line(45.0, 406.0, "8", x1=52.0),
        _line(60.0, 406.0, "A", x1=70.0),
        _line(75.0, 406.0, "2", x1=82.0),
        _line(90.0, 406.0, "B", x1=100.0),
        _line(105.0, 406.0, "5", x1=112.0),
    ]
    override_set = LayoutOverrideSet(
        overrides=[
            LayoutOverride(
                pdf_sha256="deadbeef" * 8,  # a *different* PDF than the one below
                page=1,
                bbox=(298.0, 307.0, 323.0, 326.0),
                secondary_bbox=(330.0, 302.2, 341.2, 315.5),
                rule="force_fraction_merge",
                question_id="enade-2011-computing-q10",
                reason="test",
                evidence="test",
                status="reviewed",
            )
        ]
    )
    merged = _merge_orphan_markers(
        lines, margins=None, overrides=override_set, pdf_sha256="2021-b1-hash"
    )
    # Every marker still merges with only its own single closest partner -
    # no fraction-shaped splice, no cross-pair contamination.
    texts = sorted(ln.text for ln in merged if "\t" in ln.text)
    assert texts == ["A\t2", "B\t5", "C\t8"]


def test_detect_column_margins_rejects_non_overlapping_y_ranges():
    # An indented epigraph/poem block that sits entirely *before* the body
    # paragraph in Y (never running in parallel with it) must not be read
    # as a genuine second column, even though it clears every other
    # geometric threshold (2011 unified booklet, Questao 1's poem on page
    # 2 and Discursiva 4's epigraph on page 19 - see layout.py docstring
    # and docs/decisions.md, Phase 2B ADR 25).
    lines = []
    for i in range(4):
        lines.append(_line(140, i * 18, f"linha indentada do epigrafe {i}", x1=440))
    for i in range(6):
        lines.append(_line(28, 300 + i * 18, f"paragrafo do corpo principal {i}", x1=500))
    assert detect_column_margins(lines) is None


def test_detect_column_margins_accepts_overlapping_y_ranges():
    # Sanity check for the same discriminator's other side: genuine
    # side-by-side columns, whose Y-ranges overlap throughout, must still
    # be detected.
    lines = []
    for i in range(6):
        lines.append(_line(30, i * 20, f"coluna esquerda numero {i} com texto suficiente", x1=280))
        lines.append(_line(295, i * 20, f"coluna direita numero {i} com texto suficiente", x1=595))
    margins = detect_column_margins(lines)
    assert margins is not None
    assert margins == (30, 295)


def test_extract_page_lines_force_single_column_keeps_natural_order(tmp_path):
    # A minimal synthetic PDF with an indented "poem" block (3+ lines at a
    # consistent offset, enough to normally trigger column detection)
    # nested between two ordinary body-margin lines - the exact shape of
    # 2011 Q1's own defect (see layout_overrides.py docstring).
    import pymupdf

    from enade.extraction.layout import extract_page_lines
    from enade.extraction.layout_overrides import LayoutOverride, LayoutOverrideSet

    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((28, 68), "QUESTAO 1", fontsize=11)
    page.insert_text((173, 100), "Linha de poema um bem comprida para largura", fontsize=11)
    page.insert_text((173, 115), "Linha de poema dois bem comprida para largura", fontsize=11)
    page.insert_text((173, 130), "Linha de poema tres bem comprida para largura", fontsize=11)
    page.insert_text((28, 300), "No poema a autora sugere que isso aqui termine", fontsize=11)

    override_set = LayoutOverrideSet(
        overrides=[
            LayoutOverride(
                pdf_sha256="deadbeef" * 8,
                page=1,
                bbox=(0.0, 0.0, 0.0, 0.0),
                rule="force_single_column_page",
                question_id="enade-2011-computing-q01",
                reason="test",
                evidence="test",
                status="reviewed",
            )
        ]
    )
    lines = extract_page_lines(page, 1, overrides=override_set, pdf_sha256="deadbeef" * 8)
    texts = [ln.text for ln in lines]
    assert texts == [
        "QUESTAO 1",
        "Linha de poema um bem comprida para largura",
        "Linha de poema dois bem comprida para largura",
        "Linha de poema tres bem comprida para largura",
        "No poema a autora sugere que isso aqui termine",
    ]
