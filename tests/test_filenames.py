from __future__ import annotations

import pytest

from enade.inventory.filenames import parse_filename, parse_year_directory
from enade.models.enums import CourseCode, DocType


@pytest.mark.parametrize(
    ("filename", "expected_letter", "expected_course", "expected_doctype", "expected_seq"),
    [
        ("b1_prova.pdf", "b", CourseCode.CC_BACHARELADO, DocType.EXAM, 1),
        ("l2_gabarito.pdf", "l", CourseCode.CC_LICENCIATURA, DocType.ANSWER_KEY, 2),
        ("e3_padrao.pdf", "e", CourseCode.ENGENHARIA_COMPUTACAO, DocType.ANSWER_STANDARD, 3),
        ("s1_prova.pdf", "s", CourseCode.SISTEMAS_INFORMACAO, DocType.EXAM, 1),
    ],
)
def test_parse_filename_known_courses(
    filename, expected_letter, expected_course, expected_doctype, expected_seq
):
    parsed = parse_filename(filename)
    assert parsed.matched
    assert parsed.course_letter == expected_letter
    assert parsed.course_codes == (expected_course,)
    assert parsed.document_type == expected_doctype
    assert parsed.sequence == expected_seq
    assert parsed.warnings == ()
    assert not parsed.is_unified_booklet


def test_parse_filename_2011_unified_booklet_has_no_letter():
    parsed = parse_filename("1_prova.pdf")
    assert parsed.matched
    assert parsed.course_letter is None
    assert parsed.course_codes == (CourseCode.ALL_COMPUTING,)
    assert parsed.document_type == DocType.EXAM
    assert parsed.is_unified_booklet


def test_parse_filename_unknown_course_letter_is_flagged_not_crashed():
    parsed = parse_filename("z1_prova.pdf")
    assert parsed.matched
    assert parsed.course_codes == ()
    assert any("unknown course letter" in w for w in parsed.warnings)


def test_parse_filename_sequence_mismatch_is_a_warning_not_a_failure():
    # gabarito is expected to be sequence 2; here it's mislabeled as 1.
    parsed = parse_filename("b1_gabarito.pdf")
    assert parsed.matched
    assert parsed.document_type == DocType.ANSWER_KEY
    assert any("does not match the expected" in w for w in parsed.warnings)


@pytest.mark.parametrize(
    "filename",
    [
        "prova.pdf",  # missing sequence number
        "b1_prova.docx",  # wrong extension
        "b_prova.pdf",  # missing sequence digit
        "readme.txt",
    ],
)
def test_parse_filename_unexpected_names_do_not_match(filename):
    parsed = parse_filename(filename)
    assert not parsed.matched
    assert parsed.warnings


def test_parse_filename_unknown_doctype_word_does_not_match():
    parsed = parse_filename("b1_relatorio.pdf")
    assert not parsed.matched
    assert any("unknown document type" in w for w in parsed.warnings)


@pytest.mark.parametrize(
    ("name", "expected_year"),
    [("2005", 2005), ("2021", 2021), ("misc", None), ("20", None), ("20211", None)],
)
def test_parse_year_directory(name, expected_year):
    assert parse_year_directory(name) == expected_year
