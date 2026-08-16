from __future__ import annotations

from pathlib import Path

import pymupdf
import pytest
from pydantic import ValidationError

from enade.extraction.boundaries import QuestionKind
from enade.extraction.exam_profile import (
    _RANGE_PATTERNS_2008_B,
    ExamStructureProfile,
    load_exam_structure_profile,
    verify_declared_profile,
)
from tests.pdf_builder import build_minimal_pdf


def _profile_data(**overrides):
    base = dict(
        year=2011,
        exam_type="unified",
        exam_id="enade-2011-unificado",
        id_shorthand="computing",
        sections=[
            {
                "id": "formacao-geral-objetiva",
                "kind": "objective",
                "range": [1, 8],
                "applicable_courses": ["all-computing"],
            },
            {
                "id": "componente-especifico-objetiva",
                "kind": "objective",
                "range": [31, 35],
                "applicable_courses": ["ciencia-da-computacao-licenciatura"],
            },
        ],
    )
    base.update(overrides)
    return base


def test_resolve_finds_the_owning_section():
    profile = ExamStructureProfile.model_validate(_profile_data())
    section = profile.resolve(QuestionKind.OBJECTIVE, 5)
    assert section is not None
    assert section.id == "formacao-geral-objetiva"


def test_resolve_returns_none_for_uncovered_number():
    profile = ExamStructureProfile.model_validate(_profile_data())
    assert profile.resolve(QuestionKind.OBJECTIVE, 99) is None


def test_resolve_is_kind_specific():
    profile = ExamStructureProfile.model_validate(_profile_data())
    assert profile.resolve(QuestionKind.DISCURSIVE, 5) is None


def test_overlapping_ranges_of_the_same_kind_are_rejected():
    data = _profile_data(
        sections=[
            {
                "id": "a",
                "kind": "objective",
                "range": [1, 10],
                "applicable_courses": ["all-computing"],
            },
            {
                "id": "b",
                "kind": "objective",
                "range": [8, 15],
                "applicable_courses": ["engenharia-da-computacao"],
            },
        ]
    )
    with pytest.raises(ValidationError, match="claimed by"):
        ExamStructureProfile.model_validate(data)


def test_all_computing_cannot_combine_with_an_explicit_course():
    data = _profile_data(
        sections=[
            {
                "id": "a",
                "kind": "objective",
                "range": [1, 10],
                "applicable_courses": ["all-computing", "sistemas-de-informacao"],
            }
        ]
    )
    with pytest.raises(ValidationError, match="all-computing"):
        ExamStructureProfile.model_validate(data)


def test_range_start_after_end_is_rejected():
    data = _profile_data(
        sections=[
            {
                "id": "a",
                "kind": "objective",
                "range": [10, 1],
                "applicable_courses": ["all-computing"],
            }
        ]
    )
    with pytest.raises(ValidationError, match="start"):
        ExamStructureProfile.model_validate(data)


def test_different_kinds_may_share_the_same_numbers():
    # Objective 1-8 and discursive 1-2 legitimately overlap in *number* -
    # they are different sequences, so this must not be rejected as overlap.
    data = _profile_data(
        sections=[
            {
                "id": "formacao-geral-objetiva",
                "kind": "objective",
                "range": [1, 8],
                "applicable_courses": ["all-computing"],
            },
            {
                "id": "formacao-geral-discursiva",
                "kind": "discursive",
                "range": [1, 2],
                "applicable_courses": ["all-computing"],
            },
        ]
    )
    profile = ExamStructureProfile.model_validate(data)
    assert profile.resolve(QuestionKind.OBJECTIVE, 1) is not None
    assert profile.resolve(QuestionKind.DISCURSIVE, 1) is not None


def test_load_exam_structure_profile_reads_the_real_2011_yaml():
    path = Path("data/manifests/exam-structure-2011.yaml")
    profile = load_exam_structure_profile(path)
    assert profile.exam_id == "enade-2011-unificado"
    assert profile.id_shorthand == "computing"
    assert len(profile.sections) == 8
    assert profile.resolve(QuestionKind.OBJECTIVE, 50) is not None


def test_verify_declared_profile_confirms_matching_instructions_page():
    text = (
        "Partes\n1 a 8\nDiscursiva 1 e Discursiva 2\n9 a 30\n"
        "Discursiva 3 a Discursiva 5\n31 a 35\n36 a 40\n41 a 45\n46 a 50\n1 a 9\n"
    )
    doc = pymupdf.open(stream=build_minimal_pdf([text]), filetype="pdf")
    assert verify_declared_profile(doc) == []


def test_verify_declared_profile_notes_missing_ranges():
    doc = pymupdf.open(stream=build_minimal_pdf(["nada relevante aqui"]), filetype="pdf")
    notes = verify_declared_profile(doc)
    assert len(notes) == 9
    assert all("could not confirm" in n for n in notes)


def test_source_letter_defaults_to_none():
    profile = ExamStructureProfile.model_validate(_profile_data())
    assert profile.source_letter is None


def test_source_letter_can_be_declared():
    profile = ExamStructureProfile.model_validate(_profile_data(source_letter="b"))
    assert profile.source_letter == "b"


def test_combined_numbering_defaults_to_false():
    profile = ExamStructureProfile.model_validate(_profile_data())
    assert profile.combined_numbering is False


def test_combined_numbering_can_be_declared_true():
    profile = ExamStructureProfile.model_validate(_profile_data(combined_numbering=True))
    assert profile.combined_numbering is True


def test_verify_declared_profile_accepts_an_explicit_pattern_set():
    """PROMPT Phase 3A: a booklet whose instructions page uses different
    wording (2008-b) passes its own pattern set rather than being checked
    against 2011's - see ``_RANGE_PATTERNS_2008_B``'s own docstring.
    """
    text = "Bacharelado em Ciencia da Computacao\n21 a 38\n39 e 40\n"
    doc = pymupdf.open(stream=build_minimal_pdf([text]), filetype="pdf")
    notes = verify_declared_profile(doc, patterns=_RANGE_PATTERNS_2008_B)
    # Only the CC-Bacharelado pair is present in this fixture text - the
    # Engenharia/SI ranges are legitimately still unconfirmed.
    assert len(notes) == 4
    assert not any("Ciencia da Computacao" in n for n in notes)


def test_verify_declared_profile_2008_b_pattern_set_confirms_the_real_pdf():
    """The 2008-b prova's own Componente Especifico transition page (11,
    plain selectable text - unlike page 1's image-only cover) really does
    print all three course-specific ranges this pattern set checks for.
    """
    doc = pymupdf.open("data/raw/geacc-enade/2008/b1_prova.pdf")
    notes = verify_declared_profile(doc, instructions_page=11, patterns=_RANGE_PATTERNS_2008_B)
    assert notes == []
