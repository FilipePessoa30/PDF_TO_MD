"""Parse source PDF filenames and directory names into structured facts.

Convention observed in the geacc/enade corpus (confirmed by reading its
README.md, see docs/corpus.md):

- Each year is a top-level directory named with 4 digits, e.g. ``2021/``.
- Each file is named ``<letter><seq>_<doctype>.pdf`` where:
    - ``letter`` identifies the course: b=bacharelado CC, l=licenciatura CC,
      e=engenharia da computacao, s=sistemas de informacao. It is *absent*
      for the 2011 unified "COMPUTACAO" booklet (see docs/corpus.md).
    - ``seq`` is 1 for prova, 2 for gabarito, 3 for padrao (redundant with
      doctype, used here only as a consistency check).
    - ``doctype`` is one of ``prova`` | ``gabarito`` | ``padrao``.

This module only does *string* parsing. It never opens a PDF and never
guesses at content - unexpected names are reported, not coerced.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from enade.models.enums import CourseCode, DocType

FILENAME_PATTERN = re.compile(r"^(?P<letter>[a-zA-Z])?(?P<seq>[0-9]+)_(?P<doctype>[a-zA-Z]+)\.pdf$")
YEAR_DIR_PATTERN = re.compile(r"^(?P<year>[0-9]{4})$")

COURSE_LETTER_MAP: dict[str, CourseCode] = {
    "b": CourseCode.CC_BACHARELADO,
    "l": CourseCode.CC_LICENCIATURA,
    "e": CourseCode.ENGENHARIA_COMPUTACAO,
    "s": CourseCode.SISTEMAS_INFORMACAO,
}

DOC_TYPE_WORD_MAP: dict[str, DocType] = {
    "prova": DocType.EXAM,
    "gabarito": DocType.ANSWER_KEY,
    "padrao": DocType.ANSWER_STANDARD,
}

# Expected sequence number per doc type, used only to flag surprises.
EXPECTED_SEQUENCE_BY_DOCTYPE: dict[DocType, int] = {
    DocType.EXAM: 1,
    DocType.ANSWER_KEY: 2,
    DocType.ANSWER_STANDARD: 3,
}


@dataclass(frozen=True)
class ParsedFilename:
    """Result of parsing a single PDF filename."""

    filename: str
    matched: bool
    course_letter: str | None = None
    course_codes: tuple[CourseCode, ...] = ()
    sequence: int | None = None
    document_type: DocType | None = None
    warnings: tuple[str, ...] = field(default_factory=tuple)

    @property
    def is_unified_booklet(self) -> bool:
        """True for filenames with no course letter (the 2011 case)."""
        return self.matched and self.course_letter is None


def parse_filename(filename: str) -> ParsedFilename:
    """Parse a PDF filename into course/doctype facts.

    Never raises: unrecognized filenames come back with ``matched=False``
    and an explanatory warning, so callers can surface them as orphans /
    unexpected names instead of crashing the whole inventory run.
    """
    match = FILENAME_PATTERN.match(filename)
    if not match:
        return ParsedFilename(
            filename=filename,
            matched=False,
            warnings=(
                f"filename {filename!r} does not match the expected '<letter?><seq>_<doctype>.pdf' pattern",
            ),
        )

    letter_raw = match.group("letter")
    seq = int(match.group("seq"))
    doctype_word = match.group("doctype").lower()
    warnings: list[str] = []

    document_type = DOC_TYPE_WORD_MAP.get(doctype_word)
    if document_type is None:
        return ParsedFilename(
            filename=filename,
            matched=False,
            sequence=seq,
            warnings=(f"unknown document type word {doctype_word!r} in filename {filename!r}",),
        )

    course_letter: str | None = None
    course_codes: tuple[CourseCode, ...] = ()
    if letter_raw is None:
        # No course letter: the unified-booklet convention (2011).
        course_codes = (CourseCode.ALL_COMPUTING,)
    else:
        course_letter = letter_raw.lower()
        code = COURSE_LETTER_MAP.get(course_letter)
        if code is None:
            warnings.append(f"unknown course letter {letter_raw!r} in filename {filename!r}")
        else:
            course_codes = (code,)

    expected_seq = EXPECTED_SEQUENCE_BY_DOCTYPE[document_type]
    if seq != expected_seq:
        warnings.append(
            f"sequence number {seq} in {filename!r} does not match the expected "
            f"{expected_seq} for document type {document_type.value!r}"
        )

    return ParsedFilename(
        filename=filename,
        matched=True,
        course_letter=course_letter,
        course_codes=course_codes,
        sequence=seq,
        document_type=document_type,
        warnings=tuple(warnings),
    )


def parse_year_directory(name: str) -> int | None:
    """Return the 4-digit year encoded by a top-level directory name, or None."""
    match = YEAR_DIR_PATTERN.match(name)
    if not match:
        return None
    return int(match.group("year"))
