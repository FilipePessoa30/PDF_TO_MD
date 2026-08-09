"""Thin, read-only wrapper around a source PDF (prova/gabarito/padrao).

Deliberately minimal: this only opens the file and exposes what downstream
extraction stages need (page count, page access, hash, path). It never
writes to the PDF and never mutates upstream files.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import TracebackType

import pymupdf

from enade.inventory.pdfmeta import sha256_of_file


@dataclass(frozen=True)
class PdfIdentity:
    """Provenance facts about a PDF, computed once at open time."""

    path: Path
    source_path: str  # relative to the corpus root, e.g. "2021/b1_prova.pdf"
    sha256: str
    page_count: int


class PdfDocument:
    """Context-managed handle on an opened PDF, plus its identity/hash."""

    def __init__(self, path: Path, corpus_root: Path) -> None:
        self._path = path
        self._doc = pymupdf.open(str(path))
        self.identity = PdfIdentity(
            path=path,
            source_path=path.relative_to(corpus_root).as_posix(),
            sha256=sha256_of_file(path),
            page_count=self._doc.page_count,
        )

    @property
    def raw(self) -> pymupdf.Document:
        return self._doc

    def page(self, page_number: int) -> pymupdf.Page:
        """1-indexed page access."""
        return self._doc[page_number - 1]

    def close(self) -> None:
        self._doc.close()

    def __enter__(self) -> PdfDocument:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()
