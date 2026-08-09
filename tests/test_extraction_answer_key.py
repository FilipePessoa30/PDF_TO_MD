from __future__ import annotations

import pymupdf

from enade.extraction.answer_key import AnswerKeyValueKind, parse_answer_key
from enade.extraction.boundaries import QuestionKind
from tests.pdf_builder import build_minimal_pdf


def _gabarito_pdf(lines: list[str]) -> pymupdf.Document:
    text = "\n".join(lines)
    return pymupdf.open(stream=build_minimal_pdf([text]), filetype="pdf")


def test_parse_answer_key_letters_and_discursive_markers():
    doc = _gabarito_pdf(
        [
            "QUESTAO DISCURSIVA 1",
            "***",
            "QUESTAO 1",
            "E",
            "QUESTAO 2",
            "C",
        ]
    )
    result = parse_answer_key(doc)
    assert result.warnings == []
    d1 = result.lookup(QuestionKind.DISCURSIVE, 1)
    assert d1 is not None
    assert d1.value_kind == AnswerKeyValueKind.NOT_MACHINE_GRADED

    q1 = result.lookup(QuestionKind.OBJECTIVE, 1)
    assert q1 is not None
    assert q1.value_kind == AnswerKeyValueKind.LETTER
    assert q1.letter == "E"

    q2 = result.lookup(QuestionKind.OBJECTIVE, 2)
    assert q2 is not None
    assert q2.letter == "C"


def test_parse_answer_key_detects_annulled_question():
    doc = _gabarito_pdf(["QUESTAO 1", "ANULADA"])
    result = parse_answer_key(doc)
    entry = result.lookup(QuestionKind.OBJECTIVE, 1)
    assert entry is not None
    assert entry.value_kind == AnswerKeyValueKind.ANNULLED
    assert entry.letter is None


def test_parse_answer_key_reports_unrecognized_value_without_guessing():
    doc = _gabarito_pdf(["QUESTAO 1", "XPTO"])
    result = parse_answer_key(doc)
    entry = result.lookup(QuestionKind.OBJECTIVE, 1)
    assert entry is not None
    assert entry.value_kind == AnswerKeyValueKind.UNRECOGNIZED
    assert entry.letter is None
    assert any("unrecognized" in w for w in result.warnings)


def test_parse_answer_key_detects_duplicate_entries():
    doc = _gabarito_pdf(["QUESTAO 1", "A", "QUESTAO 1", "B"])
    result = parse_answer_key(doc)
    assert any("duplicate" in w for w in result.warnings)


def test_lookup_returns_none_for_missing_question():
    doc = _gabarito_pdf(["QUESTAO 1", "A"])
    result = parse_answer_key(doc)
    assert result.lookup(QuestionKind.OBJECTIVE, 99) is None
