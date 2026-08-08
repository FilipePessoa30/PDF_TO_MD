from __future__ import annotations

from pathlib import Path

import pytest

from enade.markdown_format import (
    MarkdownFormatError,
    load_question_markdown,
    load_questions_directory,
    parse_question_markdown,
    render_question_markdown,
)


def test_load_all_valid_question_fixtures(fixtures_dir: Path):
    valid_dir = fixtures_dir / "questions" / "valid"
    md_files = sorted(valid_dir.glob("*.md"))
    assert len(md_files) >= 6  # sanity: fixtures actually exist

    for path in md_files:
        question = load_question_markdown(path)
        assert question.statement.strip()


def test_render_then_parse_round_trips(fixtures_dir: Path):
    original = load_question_markdown(
        fixtures_dir / "questions" / "valid" / "q-multiple-choice-basic.md"
    )

    rendered = render_question_markdown(original)
    reparsed_data = parse_question_markdown(rendered)

    assert reparsed_data["id"] == original.id
    assert reparsed_data["statement"] == original.statement
    assert reparsed_data["alternatives"] == [a.model_dump() for a in original.alternatives]


def test_front_matter_must_not_declare_statement_or_alternatives():
    text = "\n".join(
        [
            "---",
            "id: x",
            "statement: should not be here",
            "---",
            "# Questão 1",
            "body",
        ]
    )
    with pytest.raises(MarkdownFormatError):
        parse_question_markdown(text)


def test_missing_closing_front_matter_delimiter_raises():
    text = "---\nid: x\n# no closing delimiter"
    with pytest.raises(MarkdownFormatError):
        parse_question_markdown(text)


def test_missing_front_matter_entirely_raises():
    with pytest.raises(MarkdownFormatError):
        parse_question_markdown("# Questão 1\nsome text")


def test_load_questions_directory_detects_duplicate_id(fixtures_dir: Path):
    with pytest.raises(MarkdownFormatError, match="duplicate question id"):
        load_questions_directory(fixtures_dir / "questions" / "duplicate_id")


def test_load_questions_directory_ok_for_valid_set(fixtures_dir: Path):
    questions = load_questions_directory(fixtures_dir / "questions" / "valid")
    assert len(questions) == len(list((fixtures_dir / "questions" / "valid").glob("*.md")))
