"""Unit/integration tests for the forward-reference-caption ownership
mechanism (PROMPT Phase 3E) - ``reference_captions.py``.

Covers the pattern's own narrowness (never matches ordinary prose
mentioning another question), the explicit rejection criteria (ambiguous,
nonexistent, backward, no-anchor - never a silent fallback), and the real
2008-b Q61/D60/Q62 shape end-to-end against a synthetic PDF.
"""

from __future__ import annotations

import pymupdf

from enade.extraction.boundaries import QuestionKind, QuestionSpan
from enade.extraction.figures import compute_decorative_baseline
from enade.extraction.layout import Line
from enade.extraction.reference_captions import (
    _detect_captions_in_span,
    _resolve_target,
    apply_forward_reference_transfers,
)


def _span(kind: QuestionKind, number: int, lines: list[Line], page: int = 1) -> QuestionSpan:
    return QuestionSpan(
        kind=kind, number=number, lines=tuple(lines), start_page=page, end_page=page
    )


def _line(text: str, x0: float, y0: float, x1: float, y1: float, page: int = 1) -> Line:
    return Line(page_number=page, text=text, x0=x0, y0=y0, x1=x1, y1=y1)


# --- _detect_captions_in_span: pattern narrowness --------------------------


def test_detects_figura_para_a_questao_caption():
    span = _span(QuestionKind.DISCURSIVE, 60, [_line("Figura para a questão 61", 100, 10, 200, 20)])
    found = _detect_captions_in_span(span)
    assert len(found) == 1
    _, caption = found[0]
    assert caption.reference_type == "figura"
    assert caption.referenced_number == 61
    assert caption.direction == "current"


def test_detects_tabela_diagrama_quadro_variants():
    variants = [
        ("Tabela para a questão 5", "tabela", 5),
        ("Diagrama referente à questão 3", "diagrama", 3),
        ("Quadro para a questão 2", "quadro", 2),
    ]
    for text, expected_type, expected_number in variants:
        span = _span(QuestionKind.OBJECTIVE, 1, [_line(text, 0, 0, 100, 10)])
        found = _detect_captions_in_span(span)
        assert len(found) == 1, text
        assert found[0][1].reference_type == expected_type
        assert found[0][1].referenced_number == expected_number


def test_does_not_match_ordinary_prose_mentioning_a_question_number():
    """PROMPT section 11: a real statement mentioning another question's
    number in free-form prose must never be mistaken for a reference
    caption - only an anchored, start-to-end caption line qualifies.
    """
    span = _span(
        QuestionKind.OBJECTIVE,
        10,
        [_line("Considerando a figura da questão 61 apresentada anteriormente,", 0, 0, 300, 10)],
    )
    assert _detect_captions_in_span(span) == []


def test_does_not_match_when_trailing_text_follows_the_number():
    span = _span(
        QuestionKind.OBJECTIVE,
        10,
        [_line("Figura para a questão 61 e 62", 0, 0, 300, 10)],
    )
    assert _detect_captions_in_span(span) == []


def test_split_leading_zero_number_still_resolves():
    span = _span(QuestionKind.OBJECTIVE, 1, [_line("Figura para a questão 007", 0, 0, 200, 10)])
    found = _detect_captions_in_span(span)
    assert len(found) == 1
    assert found[0][1].referenced_number == 7


# --- _resolve_target: explicit rejection, never a fuzzy fallback -----------


def test_resolve_target_unique_match():
    spans = [
        _span(QuestionKind.DISCURSIVE, 60, []),
        _span(QuestionKind.OBJECTIVE, 61, []),
    ]
    target, reason = _resolve_target(61, spans)
    assert reason is None
    assert target is spans[1]


def test_resolve_target_not_found_is_explicit_not_a_guess():
    spans = [_span(QuestionKind.OBJECTIVE, 61, [])]
    target, reason = _resolve_target(999, spans)
    assert target is None
    assert reason == "referenced_question_not_found"


def test_resolve_target_ambiguous_kind_is_rejected():
    """2008-b uses combined numbering across objective/discursive - a bare
    number alone can match both kinds. Never guessed.
    """
    spans = [
        _span(QuestionKind.OBJECTIVE, 9, []),
        _span(QuestionKind.DISCURSIVE, 9, []),
    ]
    target, reason = _resolve_target(9, spans)
    assert target is None
    assert reason == "ambiguous_question_kind"


# --- apply_forward_reference_transfers: full mechanism ---------------------


def _doc_with_drawing(rect: pymupdf.Rect) -> pymupdf.Document:
    doc = pymupdf.open()
    page = doc.new_page()
    page.draw_rect(rect, color=(0, 0, 0), fill=(0, 0, 0))
    return doc


def test_forward_reference_transfers_caption_and_anchored_labels_to_target():
    """The core 2008-b Q61/D60 shape: D60 (origin) ends with a caption +
    diagram labels that document Q61 (target, later in document order).
    Both the caption and its anchored labels must move to Q61's own span,
    and D60 must lose them - nothing else.
    """
    doc = _doc_with_drawing(pymupdf.Rect(50, 50, 150, 150))
    caption = _line("Figura para a questão 61", 60, 30, 140, 40)
    label = _line("Estágios do ciclo de vida", 60, 55, 140, 65)
    d60_lines = [
        _line("Enunciado real de D60.", 60, 10, 140, 20),
        caption,
        label,
    ]
    q61_lines = [_line("A figura acima ilustra o modelo.", 60, 160, 140, 170)]
    spans = [
        _span(QuestionKind.DISCURSIVE, 60, d60_lines),
        _span(QuestionKind.OBJECTIVE, 61, q61_lines),
    ]
    baseline = compute_decorative_baseline(doc)
    new_spans, records = apply_forward_reference_transfers(spans, doc, baseline)

    assert len(records) == 1
    record = records[0]
    assert record.accepted is True
    assert record.target_question_key == "objective-61"
    assert record.transferred_line_count == 2  # caption + label, not the drawing itself

    d60_new = next(s for s in new_spans if s.number == 60 and s.kind == QuestionKind.DISCURSIVE)
    q61_new = next(s for s in new_spans if s.number == 61 and s.kind == QuestionKind.OBJECTIVE)
    d60_texts = [ln.text for ln in d60_new.lines]
    q61_texts = [ln.text for ln in q61_new.lines]
    assert d60_texts == ["Enunciado real de D60."]
    assert caption.text in q61_texts
    assert label.text in q61_texts
    assert "A figura acima ilustra o modelo." in q61_texts


def test_current_reference_is_a_no_op():
    """A caption already sitting in the span it documents needs no
    transfer at all.
    """
    doc = _doc_with_drawing(pymupdf.Rect(50, 50, 150, 150))
    caption = _line("Figura para a questão 61", 60, 30, 140, 40)
    span = _span(QuestionKind.OBJECTIVE, 61, [caption])
    baseline = compute_decorative_baseline(doc)
    new_spans, records = apply_forward_reference_transfers([span], doc, baseline)
    assert records == []
    assert new_spans[0].lines == span.lines


def test_backward_reference_is_rejected_not_transferred():
    """PROMPT: no confirmed real-corpus backward case - explicitly logged
    and refused, never silently applied.
    """
    doc = _doc_with_drawing(pymupdf.Rect(50, 50, 150, 150))
    q61_lines = [_line("Enunciado da questão 61.", 60, 10, 140, 20)]
    d60_lines = [
        _line("Enunciado de D60.", 60, 10, 140, 20, page=2),
        _line("Figura para a questão 61", 60, 30, 140, 40, page=2),
    ]
    spans = [
        _span(QuestionKind.OBJECTIVE, 61, q61_lines, page=1),
        _span(QuestionKind.DISCURSIVE, 60, d60_lines, page=2),
    ]
    baseline = compute_decorative_baseline(doc)
    new_spans, records = apply_forward_reference_transfers(spans, doc, baseline)
    assert len(records) == 1
    assert records[0].accepted is False
    assert records[0].rejection_reason == "backward_reference_not_supported"
    # Nothing moved.
    assert new_spans[1].lines == tuple(d60_lines)


def test_nonexistent_referenced_question_is_rejected():
    doc = _doc_with_drawing(pymupdf.Rect(50, 50, 150, 150))
    span = _span(QuestionKind.DISCURSIVE, 60, [_line("Figura para a questão 999", 60, 30, 140, 40)])
    baseline = compute_decorative_baseline(doc)
    _new_spans, records = apply_forward_reference_transfers([span], doc, baseline)
    assert len(records) == 1
    assert records[0].accepted is False
    assert records[0].rejection_reason == "referenced_question_not_found"


def test_no_anchored_asset_found_is_rejected_not_guessed():
    """A caption with no nearby drawing/image at all must never fall back
    to "nearest marker" or any other guess.
    """
    doc = pymupdf.open()
    doc.new_page()  # no drawing at all
    d60_lines = [_line("Figura para a questão 61", 60, 30, 140, 40)]
    q61_lines = [_line("Enunciado da questão 61.", 60, 160, 140, 170)]
    spans = [
        _span(QuestionKind.DISCURSIVE, 60, d60_lines),
        _span(QuestionKind.OBJECTIVE, 61, q61_lines),
    ]
    baseline = compute_decorative_baseline(doc)
    new_spans, records = apply_forward_reference_transfers(spans, doc, baseline)
    assert len(records) == 1
    assert records[0].accepted is False
    assert records[0].rejection_reason == "no_anchored_asset_found"
    # D60 keeps its own (unresolved) caption line - never silently dropped.
    d60_new = next(s for s in new_spans if s.number == 60)
    assert d60_new.lines == tuple(d60_lines)


def test_alternative_marker_is_never_swept_into_a_transfer():
    """PROMPT section 8: an alternative can never be transferred, even if
    it geometrically falls inside the anchored region's own bbox.
    """
    doc = _doc_with_drawing(pymupdf.Rect(50, 50, 150, 150))
    caption = _line("Figura para a questão 61", 60, 30, 140, 40)
    fake_alternative = _line("A\tuma alternativa real", 60, 55, 140, 65)
    d60_lines = [caption, fake_alternative]
    q61_lines = [_line("Enunciado da questão 61.", 60, 160, 140, 170)]
    spans = [
        _span(QuestionKind.DISCURSIVE, 60, d60_lines),
        _span(QuestionKind.OBJECTIVE, 61, q61_lines),
    ]
    baseline = compute_decorative_baseline(doc)
    new_spans, records = apply_forward_reference_transfers(spans, doc, baseline)
    assert records[0].accepted is True
    d60_new = next(s for s in new_spans if s.number == 60)
    q61_new = next(s for s in new_spans if s.number == 61)
    assert fake_alternative.text in [ln.text for ln in d60_new.lines]
    assert fake_alternative.text not in [ln.text for ln in q61_new.lines]


def test_transfer_is_deterministic_across_repeated_runs():
    doc = _doc_with_drawing(pymupdf.Rect(50, 50, 150, 150))
    caption = _line("Figura para a questão 61", 60, 30, 140, 40)
    label = _line("Rótulo do diagrama", 60, 55, 140, 65)
    d60_lines = [_line("Enunciado real de D60.", 60, 10, 140, 20), caption, label]
    q61_lines = [_line("A figura acima ilustra o modelo.", 60, 160, 140, 170)]
    spans = [
        _span(QuestionKind.DISCURSIVE, 60, d60_lines),
        _span(QuestionKind.OBJECTIVE, 61, q61_lines),
    ]
    baseline = compute_decorative_baseline(doc)
    result_a = apply_forward_reference_transfers(spans, doc, baseline)
    result_b = apply_forward_reference_transfers(spans, doc, baseline)
    assert result_a == result_b
