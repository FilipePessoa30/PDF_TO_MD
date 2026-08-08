"""Parse/render the per-question Markdown format defined in docs/markdown-format.md.

Design: YAML front matter carries every :class:`~enade.models.question.Question`
field *except* ``statement`` and ``alternatives`` - those two are authored as
plain Markdown in the body, since that is what a human editor actually wants
to read/write. This module is the single source of truth reconciling the two
halves back into one validated :class:`Question`.

Phase 0 does not use this to extract real questions; it exists so the format
can be exercised end-to-end against small fixtures (tests/fixtures/questions).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from enade.models.question import Question

FRONT_MATTER_DELIMITER = "---"

_HEADING_RE = re.compile(r"^#\s+Quest[aã]o\s+(?P<number>\d+)\s*$", re.IGNORECASE)
_ALTERNATIVES_HEADING_RE = re.compile(r"^##\s+Alternativas\s*$", re.IGNORECASE)
_ALTERNATIVE_LINE_RE = re.compile(r"^(?P<letter>[A-E])[.)]\s+(?P<text>.+)$")


class MarkdownFormatError(ValueError):
    """Raised when a .md question file does not follow the documented format."""


def parse_question_markdown(text: str) -> dict[str, Any]:
    """Parse raw Markdown text into a dict suitable for ``Question.model_validate``."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != FRONT_MATTER_DELIMITER:
        raise MarkdownFormatError("file must start with a '---' YAML front matter block")
    try:
        end_idx = lines.index(FRONT_MATTER_DELIMITER, 1)
    except ValueError as exc:
        raise MarkdownFormatError("front matter is not closed with a second '---'") from exc

    front_matter_text = "\n".join(lines[1:end_idx])
    body = "\n".join(lines[end_idx + 1 :]).strip("\n")

    data = yaml.safe_load(front_matter_text) or {}
    if not isinstance(data, dict):
        raise MarkdownFormatError("front matter must be a YAML mapping")
    if "statement" in data or "alternatives" in data:
        raise MarkdownFormatError(
            "'statement' and 'alternatives' belong in the Markdown body, not the front matter"
        )

    statement, alternatives = _parse_body(body)
    data = dict(data)
    data["statement"] = statement
    data["alternatives"] = alternatives
    return data


def _parse_body(body: str) -> tuple[str, list[dict[str, str]]]:
    lines = body.splitlines()
    idx = 0
    while idx < len(lines) and not lines[idx].strip():
        idx += 1
    if idx < len(lines) and _HEADING_RE.match(lines[idx].strip()):
        idx += 1

    statement_lines: list[str] = []
    alternatives: list[dict[str, str]] = []
    current_letter: str | None = None
    current_text: list[str] = []
    in_alternatives = False

    def flush_alternative() -> None:
        nonlocal current_letter, current_text
        if current_letter is not None:
            alternatives.append({"letter": current_letter, "text": " ".join(current_text).strip()})
        current_letter = None
        current_text = []

    for line in lines[idx:]:
        stripped = line.strip()
        if not in_alternatives and _ALTERNATIVES_HEADING_RE.match(stripped):
            in_alternatives = True
            continue
        if in_alternatives:
            match = _ALTERNATIVE_LINE_RE.match(stripped)
            if match:
                flush_alternative()
                current_letter = match.group("letter")
                current_text = [match.group("text").strip()]
            elif stripped:
                current_text.append(stripped)
            continue
        statement_lines.append(line)

    flush_alternative()
    statement = "\n".join(statement_lines).strip()
    return statement, alternatives


def load_question_markdown(path: Path) -> Question:
    """Parse and validate a .md question file into a canonical :class:`Question`."""
    data = parse_question_markdown(path.read_text(encoding="utf-8"))
    return Question.model_validate(data)


def load_questions_directory(directory: Path) -> dict[str, Question]:
    """Load every ``*.md`` question in ``directory``, keyed by id.

    Raises :class:`MarkdownFormatError` if two files declare the same id -
    canonical question ids must be unique across the corpus.
    """
    questions: dict[str, Question] = {}
    for path in sorted(directory.glob("*.md")):
        question = load_question_markdown(path)
        if question.id in questions:
            raise MarkdownFormatError(f"duplicate question id {question.id!r} found in {path.name}")
        questions[question.id] = question
    return questions


def render_question_markdown(question: Question) -> str:
    """Render a :class:`Question` back into the documented Markdown format."""
    front_matter = question.model_dump(mode="json", exclude={"statement", "alternatives"})
    front_matter_yaml = yaml.safe_dump(
        front_matter, sort_keys=False, allow_unicode=True, default_flow_style=False
    ).rstrip("\n")

    parts = [
        FRONT_MATTER_DELIMITER,
        front_matter_yaml,
        FRONT_MATTER_DELIMITER,
        "",
        f"# Questão {question.question_number}",
        "",
        question.statement,
    ]
    if question.alternatives:
        parts += ["", "## Alternativas", ""]
        parts += [f"{alt.letter}. {alt.text}" for alt in question.alternatives]
    return "\n".join(parts) + "\n"
