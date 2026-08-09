"""Write a Question to its canonical Markdown file, idempotently.

Reuses the Phase 0 ``enade.markdown_format`` renderer (single source of
truth for the on-disk format - PROMPT section 14 forbids inventing a second,
incompatible format). Writes are staged (temp file + atomic replace) and
skipped entirely when the rendered content is byte-identical to what is
already on disk, so re-running the pipeline over an unchanged source does
not touch file mtimes or create noisy diffs (PROMPT section 22).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from enade.markdown_format import render_question_markdown
from enade.models.question import Question


@dataclass(frozen=True)
class WriteResult:
    path: Path
    changed: bool


def write_question_markdown(question: Question, output_dir: Path) -> WriteResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{question.id}.md"
    content = render_question_markdown(question)

    if path.exists() and path.read_text(encoding="utf-8") == content:
        return WriteResult(path=path, changed=False)

    tmp_path = path.with_name(path.name + ".tmp")
    tmp_path.write_text(content, encoding="utf-8")
    tmp_path.replace(path)
    return WriteResult(path=path, changed=True)
