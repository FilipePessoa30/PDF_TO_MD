from __future__ import annotations

import pymupdf

from enade.extraction.answer_key import (
    AnswerKeyValueKind,
    parse_answer_key,
    parse_flat_item_gabarito,
)
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


def test_parse_flat_item_gabarito_reads_bare_number_value_pairs():
    # 2011 unified booklet gabarito shape: "ITEM"/"GABARITO" header, then a
    # flat sequence of <number>/<value> pairs with no "QUESTAO" prefix at
    # all - a genuinely different document shape from parse_answer_key's.
    doc = _gabarito_pdf(["ITEM", "GABARITO", "1", "D", "2", "A", "3", "E"])
    result = parse_flat_item_gabarito(doc)
    assert result.warnings == []
    for number, letter in ((1, "D"), (2, "A"), (3, "E")):
        entry = result.lookup(QuestionKind.OBJECTIVE, number)
        assert entry is not None
        assert entry.value_kind == AnswerKeyValueKind.LETTER
        assert entry.letter == letter


def test_parse_flat_item_gabarito_detects_annulled_item():
    doc = _gabarito_pdf(["ITEM", "GABARITO", "13", "ANULADA"])
    result = parse_flat_item_gabarito(doc)
    entry = result.lookup(QuestionKind.OBJECTIVE, 13)
    assert entry is not None
    assert entry.value_kind == AnswerKeyValueKind.ANNULLED
    assert entry.letter is None


def test_parse_flat_item_gabarito_skips_stray_non_numeric_tokens():
    # A running header repeated mid-table (observed between items 22 and
    # 23 in the real 2011 gabarito) must not shift the number/value
    # pairing - it is simply skipped, never consumed as a value.
    doc = _gabarito_pdf(
        ["ITEM", "GABARITO", "22", "C", "GABARITO DAS QUESTOES", "COMPUTACAO", "23", "C"]
    )
    result = parse_flat_item_gabarito(doc)
    assert result.warnings == []
    entry_22 = result.lookup(QuestionKind.OBJECTIVE, 22)
    entry_23 = result.lookup(QuestionKind.OBJECTIVE, 23)
    assert entry_22 is not None and entry_22.letter == "C"
    assert entry_23 is not None and entry_23.letter == "C"


def test_parse_flat_item_gabarito_every_entry_is_objective():
    doc = _gabarito_pdf(["ITEM", "GABARITO", "1", "A"])
    result = parse_flat_item_gabarito(doc)
    assert result.lookup(QuestionKind.DISCURSIVE, 1) is None
    assert result.lookup(QuestionKind.OBJECTIVE, 1) is not None


def test_parse_flat_item_gabarito_tolerates_a_trailing_dash_after_the_number():
    # 2008-b's own flat gabarito shape (PROMPT Phase 3A, confirmed against
    # the real PDF): "1 -" / "C" pairs, not 2011's bare "1" / "D".
    doc = _gabarito_pdf(["COMPUTACAO", "1 -", "C", "2 -", "E"])
    result = parse_flat_item_gabarito(doc)
    assert result.warnings == []
    entry = result.lookup(QuestionKind.OBJECTIVE, 1)
    assert entry is not None
    assert entry.letter == "C"
    assert result.lookup(QuestionKind.OBJECTIVE, 2).letter == "E"  # type: ignore[union-attr]


def test_parse_flat_item_gabarito_a_discursiva_value_reclassifies_the_entry_as_discursive():
    # 2008-b interleaves discursive items in the same flat sequence, marked
    # only by the printed value "Discursiva" (never a letter) - PROMPT
    # Phase 3A. Never guessed from the item number; only the gabarito's own
    # printed value decides.
    doc = _gabarito_pdf(["8 -", "C", "9 -", "Discursiva", "10 -", "Discursiva", "11 -", "C"])
    result = parse_flat_item_gabarito(doc)
    assert result.warnings == []
    assert result.lookup(QuestionKind.OBJECTIVE, 9) is None
    d9 = result.lookup(QuestionKind.DISCURSIVE, 9)
    assert d9 is not None
    assert d9.value_kind == AnswerKeyValueKind.NOT_MACHINE_GRADED
    d10 = result.lookup(QuestionKind.DISCURSIVE, 10)
    assert d10 is not None
    assert result.lookup(QuestionKind.OBJECTIVE, 8) is not None
    assert result.lookup(QuestionKind.OBJECTIVE, 11) is not None


def test_parse_flat_item_gabarito_duplicate_detection_is_kind_aware():
    # An objective 9 and a discursive 9 are two different real questions in
    # 2008-b's combined numbering (PROMPT Phase 3A) - never a duplicate.
    doc = _gabarito_pdf(["9 -", "Discursiva"])
    result = parse_flat_item_gabarito(doc)
    assert result.warnings == []


def test_parse_flat_item_gabarito_reads_the_real_2008_b_gabarito():
    doc = pymupdf.open("data/raw/geacc-enade/2008/b2_gabarito.pdf")
    result = parse_flat_item_gabarito(doc)
    assert result.warnings == []
    assert len(result.entries) == 80
    discursive_numbers = sorted(
        e.number for e in result.entries if e.kind == QuestionKind.DISCURSIVE
    )
    assert discursive_numbers == [9, 10, 20, 39, 40, 59, 60, 79, 80]
    annulled = [e.number for e in result.entries if e.value_kind == AnswerKeyValueKind.ANNULLED]
    assert annulled == [44]
