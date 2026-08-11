from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from enade.markdown_format import load_question_markdown
from enade.models.content_block import AssetBlock, CodeBlock, ParagraphBlock, TableBlock
from enade.models.enums import CourseCode
from enade.models.provenance import AnswerStandardReference, SourceOccurrence
from enade.models.question import Alternative, Question


def _occurrence(**overrides) -> SourceOccurrence:
    base = dict(
        exam_id="enade-2021-b",
        pdf_sha256="a" * 64,
        source_path="2021/b1_prova.pdf",
        pages=[14],
        question_number=12,
        section="componente-especifico",
    )
    base.update(overrides)
    return SourceOccurrence(**base)


def _question(**overrides) -> Question:
    base = dict(
        id="fixture-q",
        exam_year=2021,
        source_occurrences=[_occurrence()],
        applicable_courses=[CourseCode.CC_BACHARELADO],
        section="componente-especifico",
        question_number=12,
        question_type="multiple_choice",
        statement="Enunciado de teste.",
        alternatives=[Alternative(letter="A", text="a"), Alternative(letter="B", text="b")],
    )
    base.update(overrides)
    return Question(**base)


# --- fixture-file-based tests -------------------------------------------------


@pytest.mark.parametrize(
    "path", sorted((Path(__file__).parent / "fixtures" / "questions" / "valid").glob("*.md"))
)
def test_valid_question_fixtures_pass(path: Path):
    question = load_question_markdown(path)
    assert isinstance(question, Question)


@pytest.mark.parametrize(
    "path", sorted((Path(__file__).parent / "fixtures" / "questions" / "invalid").glob("*.md"))
)
def test_invalid_question_fixtures_fail(path: Path):
    with pytest.raises((ValidationError, ValueError)):
        load_question_markdown(path)


# --- direct model tests: multi-course / multi-occurrence / assets ------------


def test_question_supports_multiple_applicable_courses():
    q = _question(applicable_courses=[CourseCode.CC_BACHARELADO, CourseCode.SISTEMAS_INFORMACAO])
    assert len(q.applicable_courses) == 2


def test_question_all_computing_alone_is_valid():
    q = _question(applicable_courses=[CourseCode.ALL_COMPUTING])
    assert q.applicable_courses == [CourseCode.ALL_COMPUTING]


def test_question_all_computing_combined_with_other_course_is_rejected():
    with pytest.raises(ValidationError, match="all-computing"):
        _question(applicable_courses=[CourseCode.ALL_COMPUTING, CourseCode.SISTEMAS_INFORMACAO])


def test_question_applicable_courses_must_not_be_empty():
    with pytest.raises(ValidationError):
        _question(applicable_courses=[])


def test_question_supports_multiple_source_occurrences():
    q = _question(
        source_occurrences=[_occurrence(), _occurrence(exam_id="enade-2017-b", question_number=14)]
    )
    assert len(q.source_occurrences) == 2


def test_question_requires_at_least_one_source_occurrence():
    with pytest.raises(ValidationError):
        _question(source_occurrences=[])


def test_question_pending_states_are_the_default():
    q = _question()
    assert q.extraction_status.value == "pending"
    assert q.answer_validation_status.value == "pending"
    assert q.taxonomy_review_status.value == "pending"
    assert q.extraction_method.value == "pending"
    assert q.correct_answer is None
    assert q.difficulty is None


def test_discursive_question_must_not_have_alternatives():
    with pytest.raises(ValidationError, match="must not have alternatives"):
        _question(
            question_type="discursive",
            alternatives=[Alternative(letter="A", text="a")],
        )


def test_multiple_choice_question_needs_at_least_two_alternatives():
    with pytest.raises(ValidationError, match="at least 2 alternatives"):
        _question(alternatives=[Alternative(letter="A", text="a")])


def test_duplicate_alternative_letters_are_rejected():
    with pytest.raises(ValidationError, match="repeat a letter"):
        _question(
            alternatives=[Alternative(letter="A", text="a"), Alternative(letter="A", text="a2")]
        )


def test_correct_answer_must_reference_a_declared_alternative():
    # "C" matches the A-E letter pattern but only A/B are declared as alternatives.
    with pytest.raises(ValidationError, match="not one of the declared alternatives"):
        _question(correct_answer="C")


def test_validated_status_requires_a_correct_answer():
    with pytest.raises(ValidationError, match="requires a correct_answer"):
        _question(answer_validation_status="validated", correct_answer=None)


def test_ocr_confidence_requires_ocr_or_hybrid_method():
    with pytest.raises(ValidationError, match="ocr_confidence may only be set"):
        _question(extraction_method="text_layer", ocr_confidence=0.9)

    q = _question(extraction_method="ocr", ocr_confidence=0.42)
    assert q.ocr_confidence == 0.42


def test_alternative_diagnostics_must_reference_a_declared_alternative():
    # "C" matches the A-E letter pattern but only A/B are declared as alternatives.
    with pytest.raises(ValidationError, match="undeclared alternative"):
        _question(alternative_diagnostics={"C": {"misconception_id": "some-misconception"}})


def test_alternative_diagnostics_must_not_target_the_correct_answer():
    with pytest.raises(ValidationError, match="must not target the correct answer"):
        _question(
            correct_answer="A",
            answer_validation_status="validated",
            alternative_diagnostics={"A": {"misconception_id": "some-misconception"}},
        )


def test_duplicate_asset_ids_are_rejected():
    with pytest.raises(ValidationError, match="repeat an id"):
        _question(
            assets=[
                {"id": "figure-01", "type": "image", "path": "a.png", "source_page": 1},
                {"id": "figure-01", "type": "image", "path": "b.png", "source_page": 2},
            ]
        )


def test_question_id_must_be_kebab_case():
    with pytest.raises(ValidationError, match="kebab-case"):
        _question(id="Not Valid ID")


# --- Phase 1A: answer_standard (see docs/decisions.md, "Phase 1A" ADR 11) ---


def test_discursive_question_can_carry_an_answer_standard():
    q = _question(
        question_type="discursive",
        alternatives=[],
        answer_standard=AnswerStandardReference(
            source_path="2021/b3_padrao.pdf",
            pdf_sha256="b" * 64,
            pages=[3],
            text="O respondente deve descrever corretamente o algoritmo pedido.",
        ),
    )
    assert q.answer_standard is not None
    assert q.answer_standard.pages == [3]
    assert "algoritmo" in q.answer_standard.text


def test_answer_standard_defaults_to_none_and_is_backward_compatible():
    q = _question()
    assert q.answer_standard is None


def test_answer_standard_is_never_folded_into_the_rendered_statement():
    from enade.markdown_format import render_question_markdown

    q = _question(
        question_type="discursive",
        alternatives=[],
        answer_standard=AnswerStandardReference(
            source_path="2021/b3_padrao.pdf",
            pdf_sha256="b" * 64,
            pages=[3],
            text="ESTE TEXTO DE GABARITO NAO DEVE APARECER NO CORPO DO MARKDOWN.",
        ),
        statement="Enunciado visivel ao estudante.",
    )
    rendered = render_question_markdown(q)
    body = rendered.split("---", 2)[2]
    assert "ESTE TEXTO DE GABARITO" not in body


# --- Phase 1C: answer_standard.assets (see docs/decisions.md, "Phase 1C" ADR) -


def test_answer_standard_can_carry_its_own_assets():
    ref = AnswerStandardReference(
        source_path="2021/b3_padrao.pdf",
        pdf_sha256="b" * 64,
        pages=[5, 6],
        text="O respondente deve descrever a tabela verdade e desenhar o diagrama.",
        assets=[
            {
                "id": "padrao-01",
                "type": "diagram",
                "path": "fixture-d04/answer-standard/padrao-01.png",
                "source_page": 5,
            }
        ],
    )
    assert len(ref.assets) == 1
    assert ref.assets[0].id == "padrao-01"


def test_answer_standard_assets_default_to_empty_and_backward_compatible():
    ref = AnswerStandardReference(
        source_path="2021/b3_padrao.pdf", pdf_sha256="b" * 64, pages=[3], text="texto"
    )
    assert ref.assets == []


def test_answer_standard_assets_reject_duplicate_ids():
    with pytest.raises(ValidationError, match="repeat an id"):
        AnswerStandardReference(
            source_path="2021/b3_padrao.pdf",
            pdf_sha256="b" * 64,
            pages=[5],
            text="texto",
            assets=[
                {"id": "padrao-01", "type": "diagram", "path": "a.png", "source_page": 5},
                {"id": "padrao-01", "type": "diagram", "path": "b.png", "source_page": 5},
            ],
        )


def test_answer_standard_assets_are_never_mixed_with_question_assets():
    q = _question(
        question_type="discursive",
        alternatives=[],
        assets=[{"id": "figure-01", "type": "diagram", "path": "figure-01.png", "source_page": 16}],
        answer_standard=AnswerStandardReference(
            source_path="2021/b3_padrao.pdf",
            pdf_sha256="b" * 64,
            pages=[5],
            text="texto",
            assets=[
                {
                    "id": "figure-01",  # same id, different namespace - must not collide
                    "type": "diagram",
                    "path": "answer-standard/padrao-01.png",
                    "source_page": 5,
                }
            ],
        ),
    )
    assert len(q.assets) == 1
    assert len(q.answer_standard.assets) == 1
    assert q.assets[0].path != q.answer_standard.assets[0].path


# --- Phase 1C: content_blocks (see docs/decisions.md, "Phase 1C" ADR 12) -----


def test_content_blocks_defaults_to_none_and_is_backward_compatible():
    q = _question()
    assert q.content_blocks is None


def test_content_blocks_preserves_paragraph_table_code_asset_order():
    q = _question(
        question_type="discursive",
        alternatives=[],
        assets=[
            {
                "id": "table-crop-01",
                "type": "table",
                "path": "table-crop-01.png",
                "source_page": 14,
            }
        ],
        content_blocks=[
            ParagraphBlock(text="Considere a tabela a seguir."),
            TableBlock(
                headers=["p", "q"],
                rows=[["V", "F"], ["F", "V"]],
                validation_status="verified",
            ),
            ParagraphBlock(text="E o trecho de código a seguir:"),
            CodeBlock(text="funcao f(x)\n    retorne x\nfim funcao"),
            AssetBlock(asset_id="table-crop-01"),
        ],
    )
    assert [b.type for b in q.content_blocks] == [
        "paragraph",
        "table",
        "paragraph",
        "code",
        "asset",
    ]


def test_content_blocks_asset_block_must_reference_declared_asset():
    with pytest.raises(ValidationError, match="undeclared asset id"):
        _question(
            content_blocks=[AssetBlock(asset_id="does-not-exist")],
        )


def test_content_blocks_unverified_table_requires_visual_fallback_asset_block():
    with pytest.raises(ValidationError, match="no AssetBlock"):
        _question(
            content_blocks=[
                TableBlock(rows=[["V", "F"]], validation_status="needs_review"),
            ],
        )


def test_content_blocks_unverified_table_is_valid_with_visual_fallback_asset_block():
    q = _question(
        assets=[{"id": "crop-01", "type": "table", "path": "crop-01.png", "source_page": 14}],
        content_blocks=[
            TableBlock(rows=[["V", "F"]], validation_status="needs_review"),
            AssetBlock(asset_id="crop-01"),
        ],
    )
    assert q.content_blocks[0].validation_status.value == "needs_review"


def test_content_blocks_verified_table_does_not_require_visual_fallback_asset_block():
    q = _question(
        content_blocks=[
            TableBlock(rows=[["V", "F"]], validation_status="verified"),
        ],
    )
    assert q.content_blocks[0].validation_status.value == "verified"


def test_content_blocks_round_trips_through_rendered_markdown():
    from enade.markdown_format import parse_question_markdown, render_question_markdown

    q = _question(
        assets=[{"id": "crop-01", "type": "table", "path": "crop-01.png", "source_page": 14}],
        content_blocks=[
            ParagraphBlock(text="Antes da tabela."),
            TableBlock(rows=[["V", "F"]], validation_status="needs_review"),
            AssetBlock(asset_id="crop-01"),
        ],
    )
    rendered = render_question_markdown(q)
    data = parse_question_markdown(rendered)
    round_tripped = Question.model_validate(data)
    assert round_tripped.content_blocks == q.content_blocks
