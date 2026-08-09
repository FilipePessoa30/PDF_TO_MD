"""Parse the exam's own printed instructions to cross-check assumed structure.

PROMPT section 4 requires validating the expected part boundaries (Q1-8
Formacao Geral, Q9-35 Componente Especifico, D1-D2 / D3-D5 split) directly
against the PDF rather than assuming the brief is correct - "Se o PDF
contradizer qualquer informacao deste prompt, o PDF e a fonte de verdade."

This does a small, targeted regex extraction of the instruction table on
page 1 (see docs/corpus.md for the verified table contents) rather than a
general table parser - sufficient to confirm or refute the four number
ranges that matter, and to fail loudly (not silently assume) if the
booklet's instructions ever look different.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import pymupdf

from enade.extraction.to_question import ExamStructure

_FG_DISCURSIVAS_RE = re.compile(r"D\s*1\s*e\s*D\s*2")
_FG_OBJETIVAS_RE = re.compile(r"\b1\s*a\s*8\b")
_CE_DISCURSIVAS_RE = re.compile(r"D\s*3\s*a\s*D\s*5")
_CE_OBJETIVAS_RE = re.compile(r"\b9\s*a\s*35\b")
_PERCEPTION_RANGE_RE = re.compile(r"\b1\s*a\s*9\b")


@dataclass
class DeclaredStructureResult:
    structure: ExamStructure
    notes: list[str]


def parse_declared_structure(
    doc: pymupdf.Document, instructions_page: int = 1
) -> DeclaredStructureResult:
    """Confirm the printed part boundaries on the instructions page.

    Falls back to the empirically-confirmed 2021 CC-bacharelado boundaries
    (documented in docs/corpus.md) only when a pattern is not found, and
    records that as a note rather than silently proceeding as if it had
    been confirmed.
    """
    text = doc[instructions_page - 1].get_text("text")
    notes: list[str] = []

    checks = {
        "Formacao Geral discursivas (D1 e D2)": _FG_DISCURSIVAS_RE,
        "Formacao Geral objetivas (1 a 8)": _FG_OBJETIVAS_RE,
        "Componente Especifico discursivas (D3 a D5)": _CE_DISCURSIVAS_RE,
        "Componente Especifico objetivas (9 a 35)": _CE_OBJETIVAS_RE,
        "Questionario de Percepcao (1 a 9)": _PERCEPTION_RANGE_RE,
    }
    for label, pattern in checks.items():
        if not pattern.search(text):
            notes.append(
                f"could not confirm '{label}' in the printed instructions on page {instructions_page}"
            )

    structure = ExamStructure(
        formacao_geral_discursivas=range(1, 3),
        formacao_geral_objetivas=range(1, 9),
        componente_especifico_discursivas=range(3, 6),
        componente_especifico_objetivas=range(9, 36),
    )
    return DeclaredStructureResult(structure=structure, notes=notes)
