"""Parse the official "padrao de resposta" (grading rubric) PDF for discursives.

Structure confirmed empirically for ``2021/b3_padrao.pdf``: for each
Discursiva N, the document restates the question text (verbatim, from the
prova) and then shows a "PADRAO DE RESPOSTA" section with the actual
grading criteria. Only the rubric section is captured here - the restated
question text is intentionally discarded, since the question's real
``statement`` provenance must stay anchored to the prova (see PROMPT
section 33, "diferencie question source de answer source"), not to a
duplicate copy living in a different PDF.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import pymupdf

from enade.extraction.chrome import is_chrome_line
from enade.extraction.layout import Line, extract_document_lines

_DISCURSIVE_MARKER_RE = re.compile(r"(?i)^quest[aã]o\s+discursiva\s+0*(\d+)\b")
_RUBRIC_HEADING_RE = re.compile(r"(?i)^padr[aã]o\s+de\s+resposta$")
#: Same paragraph-break heuristic as assembler.py: a vertical gap this large
#: (points) between consecutive lines is a real paragraph boundary.
PARAGRAPH_GAP_THRESHOLD = 19.0


@dataclass(frozen=True)
class AnswerStandardEntry:
    number: int
    pages: list[int]
    text: str


@dataclass
class AnswerStandardParseResult:
    entries: dict[int, AnswerStandardEntry]
    warnings: list[str]


def _lines_to_paragraphs(lines: list[Line]) -> str:
    if not lines:
        return ""
    paragraphs: list[list[str]] = [[lines[0].text]]
    for previous, current in zip(lines, lines[1:], strict=False):
        same_page = previous.page_number == current.page_number
        gap = (current.y0 - previous.y1) if same_page else float("inf")
        if not same_page or gap >= PARAGRAPH_GAP_THRESHOLD:
            paragraphs.append([current.text])
        else:
            paragraphs[-1].append(current.text)
    return "\n\n".join(" ".join(p) for p in paragraphs)


def parse_answer_standard(doc: pymupdf.Document) -> AnswerStandardParseResult:
    lines = extract_document_lines(doc)
    warnings: list[str] = []
    entries: dict[int, AnswerStandardEntry] = {}

    current_number: int | None = None
    in_rubric = False
    buffer: list[Line] = []

    def flush() -> None:
        nonlocal buffer
        if current_number is not None and buffer:
            text = _lines_to_paragraphs(buffer)
            if text.strip():
                if current_number in entries:
                    warnings.append(
                        f"answer standard: duplicate rubric text for discursiva {current_number}"
                    )
                pages = sorted({ln.page_number for ln in buffer})
                entries[current_number] = AnswerStandardEntry(
                    number=current_number, pages=pages, text=text
                )
        buffer = []

    for line in lines:
        # Markers are checked *before* the chrome filter: "PADRAO DE RESPOSTA"
        # is (correctly) treated as chrome when it might leak into a question
        # statement elsewhere, but here it is the section marker this parser
        # is specifically looking for.
        marker = _DISCURSIVE_MARKER_RE.match(line.text)
        if marker:
            flush()
            current_number = int(marker.group(1))
            in_rubric = False
            continue
        if _RUBRIC_HEADING_RE.match(line.text.strip()):
            flush()
            in_rubric = True
            continue
        if is_chrome_line(line.text):
            continue
        if in_rubric and current_number is not None:
            buffer.append(line)

    flush()

    expected = set(range(1, 6))
    missing = expected - set(entries)
    if missing:
        warnings.append(
            f"answer standard: no rubric text found for discursiva(s) {sorted(missing)}"
        )

    return AnswerStandardParseResult(entries=entries, warnings=warnings)
