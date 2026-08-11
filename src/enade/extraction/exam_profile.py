"""Declarative exam structure profiles for booklets that do not fit the
single-(course, ExamStructure) shape ``declared_structure.py`` models.

PROMPT Phase 2A section 10: the 2011 unified "COMPUTACAO" caderno has
question ranges shared by four courses at once, plus four disjoint
course-specific ranges within the *same* PDF - not representable as one
course + four fixed part boundaries. Rather than branching the extractor on
``if year == 2011``, the shape of the booklet is data
(``data/manifests/exam-structure-2011.yaml``), loaded and validated here;
``pipeline.extract_exam`` stays agnostic to how many sections or courses a
given booklet has by consulting whatever profile it is handed.

Every range in the shipped 2011 profile was confirmed against the real PDF
text (see the YAML file's own header comment and docs/corpus.md) - this
module additionally cross-checks the *loaded* profile against the PDF at
run time (``verify_declared_profile``), the same "confirm, do not silently
assume" discipline ``declared_structure.py`` already applies to 2021.
"""

from __future__ import annotations

import re
from pathlib import Path

import pymupdf
import yaml
from pydantic import BaseModel, Field, model_validator

from enade.extraction.boundaries import QuestionKind
from enade.models.enums import CourseCode


class SectionRange(BaseModel):
    """One contiguous run of question numbers sharing a section id and applicability."""

    id: str
    kind: QuestionKind
    #: ``range`` in the YAML source - aliased because a field named ``range``
    #: would shadow the builtin ``range`` type used by the ``numbers`` property below.
    number_range: tuple[int, int] = Field(..., alias="range")
    applicable_courses: list[CourseCode] = Field(..., min_length=1)

    @property
    def numbers(self) -> range:
        start, end = self.number_range
        return range(start, end + 1)

    @model_validator(mode="after")
    def _validate_range_order(self) -> SectionRange:
        start, end = self.number_range
        if start > end:
            raise ValueError(f"section {self.id!r}: range start {start} > end {end}")
        return self


class ExamStructureProfile(BaseModel):
    """A whole booklet's declarative part boundaries, independent of any one course."""

    year: int
    exam_type: str
    exam_id: str
    id_shorthand: str
    sections: list[SectionRange] = Field(..., min_length=1)

    @model_validator(mode="after")
    def _validate_sections(self) -> ExamStructureProfile:
        for kind in (QuestionKind.OBJECTIVE, QuestionKind.DISCURSIVE):
            claimed: set[int] = set()
            for section in self.sections:
                if section.kind != kind:
                    continue
                numbers = set(section.numbers)
                overlap = claimed & numbers
                if overlap:
                    raise ValueError(
                        f"{kind.value}: question number(s) {sorted(overlap)} claimed by "
                        "more than one section"
                    )
                claimed |= numbers
        for section in self.sections:
            if (
                CourseCode.ALL_COMPUTING in section.applicable_courses
                and len(section.applicable_courses) > 1
            ):
                raise ValueError(
                    f"section {section.id!r} range {section.number_range}: 'all-computing' "
                    "cannot be combined with an explicit course code"
                )
        return self

    def resolve(self, kind: QuestionKind, number: int) -> SectionRange | None:
        """Return the section owning ``(kind, number)``, or None if no section claims it."""
        for section in self.sections:
            if section.kind == kind and number in section.numbers:
                return section
        return None


def load_exam_structure_profile(path: Path) -> ExamStructureProfile:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return ExamStructureProfile.model_validate(data)


#: Range-pair patterns cross-checked against the 2011 instructions-page
#: table (page 1). Each is a literal "<n> a <m>" substring as printed -
#: ``\s*`` absorbs the table-cell line breaks PyMuPDF's plain text
#: extraction leaves in place (e.g. "Discursiva 3 \na Discursiva 5").
_RANGE_PATTERNS: dict[str, re.Pattern[str]] = {
    "Formacao Geral objetivas (1 a 8)": re.compile(r"\b1\s*a\s*8\b"),
    "Formacao Geral discursivas (Discursiva 1 e Discursiva 2)": re.compile(
        r"(?i)discursiva\s*1\s*e\s*discursiva\s*2"
    ),
    "Componente Especifico Comum objetivas (9 a 30)": re.compile(r"\b9\s*a\s*30\b"),
    "Componente Especifico Comum discursivas (Discursiva 3 a Discursiva 5)": re.compile(
        r"(?i)discursiva\s*3\s*a\s*discursiva\s*5"
    ),
    "Licenciatura (31 a 35)": re.compile(r"\b31\s*a\s*35\b"),
    "Ciencia da Computacao (36 a 40)": re.compile(r"\b36\s*a\s*40\b"),
    "Engenharia de Computacao (41 a 45)": re.compile(r"\b41\s*a\s*45\b"),
    "Sistemas de Informacao (46 a 50)": re.compile(r"\b46\s*a\s*50\b"),
    "Questionario de percepcao (1 a 9)": re.compile(r"\b1\s*a\s*9\b"),
}


def verify_declared_profile(doc: pymupdf.Document, instructions_page: int = 1) -> list[str]:
    """Confirm the profile's ranges are actually printed on the instructions page.

    Returns a note per pattern that could not be confirmed - never raises,
    matching ``declared_structure.parse_declared_structure``'s
    fail-loud-but-not-blocking discipline (PROMPT: "documente a estrutura
    real" rather than silently trusting the YAML).
    """
    text = doc[instructions_page - 1].get_text("text")
    return [
        f"could not confirm '{label}' in the printed instructions on page {instructions_page}"
        for label, pattern in _RANGE_PATTERNS.items()
        if not pattern.search(text)
    ]
