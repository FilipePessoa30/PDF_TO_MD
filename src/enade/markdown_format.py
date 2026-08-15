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
#: An alternative whose own content is a formula image (PROMPT Phase 2E
#: section 10, e.g. 2011 Q14) embeds it the same way a statement figure
#: does - ``![alt](path)`` inline in its own line - matched here so the
#: path can be resolved back to the matching entry in ``Question.assets``
#: (the body carries only the portable path, never the full Asset
#: metadata - see ``_parse_body``/``parse_question_markdown``).
_ALTERNATIVE_ASSET_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")


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

    # An alternative embedding one or more formula images (PROMPT Phase
    # 2E section 10 / Phase 2F section 7) carries only the portable
    # path(s) in the body - resolve each back to the matching full Asset
    # entry already parsed from the front matter, the same source of
    # truth Question.assets itself uses. A path with no matching asset
    # entry is left unresolved (asset=None / block omitted from
    # content_blocks) rather than fabricating one - schema validation
    # then surfaces the mismatch, the same way a missing statement figure
    # would.
    assets_by_path = {a.get("path"): a for a in (data.get("assets") or [])}
    for alt in alternatives:
        asset_path = alt.pop("asset_path", None)
        alt["asset"] = assets_by_path.get(asset_path) if asset_path is not None else None
        raw_blocks = alt.pop("content_blocks_raw", None)
        if raw_blocks is None:
            alt["content_blocks"] = None
        else:
            resolved_blocks = []
            for block in raw_blocks:
                if block["type"] == "asset":
                    asset = assets_by_path.get(block["asset_path"])
                    if asset is not None:
                        resolved_blocks.append({"type": "asset", "asset_id": asset["id"]})
                else:
                    resolved_blocks.append(block)
            alt["content_blocks"] = resolved_blocks

    data = dict(data)
    data["statement"] = statement
    data["alternatives"] = alternatives
    return data


def _parse_body(body: str) -> tuple[str, list[dict[str, Any]]]:
    lines = body.splitlines()
    idx = 0
    while idx < len(lines) and not lines[idx].strip():
        idx += 1
    if idx < len(lines) and _HEADING_RE.match(lines[idx].strip()):
        idx += 1

    statement_lines: list[str] = []
    alternatives: list[dict[str, Any]] = []
    current_letter: str | None = None
    current_text: list[str] = []
    in_alternatives = False

    def flush_alternative() -> None:
        nonlocal current_letter, current_text
        if current_letter is not None:
            joined = " ".join(current_text).strip()
            matches = list(_ALTERNATIVE_ASSET_RE.finditer(joined))
            entry: dict[str, Any] = {"letter": current_letter}
            if len(matches) == 1 and matches[0].start() == 0:
                # Phase 2E's own single-asset rendering: the image is the
                # very first token, with only trailing punctuation (if
                # anything) after it - e.g. 2011 Q14's own alternatives.
                m = matches[0]
                remaining = (joined[: m.start()] + joined[m.end() :]).strip()
                entry["text"] = remaining or "."
                entry["asset_path"] = m.group(1)
            elif matches:
                # Phase 2F's own interleaved rendering: one or more images
                # sitting after real text - e.g. 2011 Q23's own D/E.
                blocks: list[dict[str, Any]] = []
                cursor = 0
                for m in matches:
                    pre = joined[cursor : m.start()].strip()
                    if pre:
                        blocks.append({"type": "paragraph", "text": pre})
                    blocks.append({"type": "asset", "asset_path": m.group(1)})
                    cursor = m.end()
                tail = joined[cursor:].strip()
                if tail:
                    blocks.append({"type": "paragraph", "text": tail})
                entry["text"] = (
                    " ".join(b["text"] for b in blocks if b["type"] == "paragraph") or "."
                )
                entry["content_blocks_raw"] = blocks
            else:
                entry["text"] = joined
            alternatives.append(entry)
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
        assets_by_id = {a.id: a for a in question.assets}
        parts += ["", "## Alternativas", ""]
        for alt in question.alternatives:
            if alt.content_blocks is not None:
                rendered_segments: list[str] = []
                for block in alt.content_blocks:
                    if block.type == "paragraph":
                        rendered_segments.append(block.text)
                    elif block.type == "asset":
                        asset = assets_by_id.get(block.asset_id)
                        if asset is not None:
                            rendered_segments.append(f"![Alternativa {alt.letter}]({asset.path})")
                parts.append(f"{alt.letter}. {' '.join(rendered_segments)}")
            elif alt.asset is not None:
                parts.append(
                    f"{alt.letter}. ![Alternativa {alt.letter}]({alt.asset.path}) {alt.text}"
                )
            else:
                parts.append(f"{alt.letter}. {alt.text}")
    return "\n".join(parts) + "\n"
