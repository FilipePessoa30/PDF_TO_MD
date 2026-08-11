"""Parse the official gabarito (answer key) PDF.

Structure confirmed empirically for the 2021 Ciencia da Computacao gabarito
(``2021/b2_gabarito.pdf``, a single densely-tabular page): a flat
``QUESTAO (DISCURSIVA )?N`` -> value sequence, where value is a single
letter A-E, ``***`` (discursive - not machine-graded, see the answer
standard instead), or ``ANULADA`` (officially annulled by INEP; two real
examples exist in this booklet: Q29 and Q33). PROMPT section 18 requires
this to be the *only* source of ``correct_answer`` - never inferred from
the question text - and any unexpected code must be reported, not guessed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

import pymupdf

from enade.extraction.boundaries import QuestionKind

_ENTRY_MARKER_RE = re.compile(r"(?i)^quest[aã]o\s+(discursiva\s+)?0*(\d+)$")
_LETTER_RE = re.compile(r"^[A-E]$")
_BARE_ITEM_RE = re.compile(r"^0*(\d{1,3})$")


class AnswerKeyValueKind(StrEnum):
    LETTER = "letter"
    ANNULLED = "annulled"
    NOT_MACHINE_GRADED = "not_machine_graded"  # "***" - discursive
    UNRECOGNIZED = "unrecognized"


@dataclass(frozen=True)
class AnswerKeyEntry:
    kind: QuestionKind
    number: int
    value_kind: AnswerKeyValueKind
    raw_value: str
    letter: str | None = None


@dataclass
class AnswerKeyParseResult:
    entries: list[AnswerKeyEntry]
    warnings: list[str]

    def lookup(self, kind: QuestionKind, number: int) -> AnswerKeyEntry | None:
        for entry in self.entries:
            if entry.kind == kind and entry.number == number:
                return entry
        return None


def parse_answer_key(doc: pymupdf.Document) -> AnswerKeyParseResult:
    """Parse every ``QUESTAO [DISCURSIVA] N`` / value pair in the gabarito PDF."""
    warnings: list[str] = []
    tokens: list[str] = []
    for page_index in range(doc.page_count):
        text = doc[page_index].get_text("text")
        for raw_line in text.splitlines():
            stripped = raw_line.strip()
            if stripped:
                tokens.append(stripped)

    entries: list[AnswerKeyEntry] = []
    i = 0
    while i < len(tokens):
        match = _ENTRY_MARKER_RE.match(tokens[i])
        if not match:
            i += 1
            continue
        kind = QuestionKind.DISCURSIVE if match.group(1) else QuestionKind.OBJECTIVE
        number = int(match.group(2))
        if i + 1 >= len(tokens):
            warnings.append(f"gabarito: marker for {kind.value} {number} has no following value")
            break
        raw_value = tokens[i + 1]
        entries.append(_classify(kind, number, raw_value, warnings))
        i += 2

    seen: set[tuple[QuestionKind, int]] = set()
    for entry in entries:
        key = (entry.kind, entry.number)
        if key in seen:
            warnings.append(f"gabarito: duplicate entry for {entry.kind.value} {entry.number}")
        seen.add(key)

    return AnswerKeyParseResult(entries=entries, warnings=warnings)


def parse_flat_item_gabarito(doc: pymupdf.Document) -> AnswerKeyParseResult:
    """Parse a flat ``ITEM`` -> ``GABARITO`` table gabarito.

    Structure confirmed empirically for the 2011 unified booklet gabarito
    (``2011/2_gabarito.pdf``, a single page): a bare ``<number>`` / ``<value>``
    sequence with no "QUESTAO" prefix at all - every entry is implicitly
    objective (the unified booklet's gabarito only ever lists the 50
    multiple-choice items; discursive answers come from the padrao de
    resposta, never a machine-checkable letter, so there is nothing for a
    "DISCURSIVA" marker to disambiguate here). This is a genuinely
    different document shape from ``parse_answer_key``'s "QUESTAO
    [DISCURSIVA] N" marker format used by every other year in this corpus
    (see docs/corpus.md) - a separate function, not a year-specific branch
    bolted onto the same one.

    Any non-numeric token between pairs (running headers repeated
    mid-table, observed between items 22 and 23) is simply skipped rather
    than assumed to be a value - the pairing only ever advances from a
    token that itself matches the bare-item pattern, so stray text cannot
    shift the numbering.
    """
    warnings: list[str] = []
    tokens: list[str] = []
    for page_index in range(doc.page_count):
        text = doc[page_index].get_text("text")
        for raw_line in text.splitlines():
            stripped = raw_line.strip()
            if stripped:
                tokens.append(stripped)

    entries: list[AnswerKeyEntry] = []
    i = 0
    while i < len(tokens):
        match = _BARE_ITEM_RE.match(tokens[i])
        if not match:
            i += 1
            continue
        number = int(match.group(1))
        if i + 1 >= len(tokens):
            warnings.append(f"gabarito: item {number} has no following value")
            break
        raw_value = tokens[i + 1]
        entries.append(_classify(QuestionKind.OBJECTIVE, number, raw_value, warnings))
        i += 2

    seen: set[int] = set()
    for entry in entries:
        if entry.number in seen:
            warnings.append(f"gabarito: duplicate entry for item {entry.number}")
        seen.add(entry.number)

    return AnswerKeyParseResult(entries=entries, warnings=warnings)


def _classify(
    kind: QuestionKind, number: int, raw_value: str, warnings: list[str]
) -> AnswerKeyEntry:
    normalized = raw_value.strip().upper()
    if _LETTER_RE.match(normalized):
        return AnswerKeyEntry(
            kind=kind,
            number=number,
            value_kind=AnswerKeyValueKind.LETTER,
            raw_value=raw_value,
            letter=normalized,
        )
    if normalized == "ANULADA":
        return AnswerKeyEntry(
            kind=kind, number=number, value_kind=AnswerKeyValueKind.ANNULLED, raw_value=raw_value
        )
    if normalized in ("***", "*"):
        return AnswerKeyEntry(
            kind=kind,
            number=number,
            value_kind=AnswerKeyValueKind.NOT_MACHINE_GRADED,
            raw_value=raw_value,
        )
    warnings.append(
        f"gabarito: unrecognized value {raw_value!r} for {kind.value} {number} - not guessing"
    )
    return AnswerKeyEntry(
        kind=kind, number=number, value_kind=AnswerKeyValueKind.UNRECOGNIZED, raw_value=raw_value
    )
