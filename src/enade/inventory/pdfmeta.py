"""Low-level PDF metadata extraction: hashing, page count, text layer detection.

Deliberately minimal and defensive: any single malformed/encrypted PDF
must produce a diagnostic result, never crash the whole inventory run.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PdfReadError

#: Average non-whitespace characters per page below which we consider the
#: text layer "present but not usable" (e.g. a handful of stray glyphs from
#: a scanned page, rather than a real digitized text layer).
MIN_AVG_CHARS_PER_PAGE_FOR_USABLE_TEXT = 20

CHUNK_SIZE = 1024 * 1024


@dataclass(frozen=True)
class PdfMetadata:
    path: str
    sha256: str
    file_size_bytes: int
    page_count: int
    encrypted: bool
    has_text_layer: bool
    text_layer_char_count: int
    readable: bool
    warnings: tuple[str, ...] = field(default_factory=tuple)


def sha256_of_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def extract_pdf_metadata(path: Path) -> PdfMetadata:
    """Compute hash, size, page count and text-layer usability for one PDF."""
    file_size = path.stat().st_size
    sha256 = sha256_of_file(path)
    warnings: list[str] = []

    try:
        reader = PdfReader(str(path))
        encrypted = reader.is_encrypted
        if encrypted:
            # Public ENADE PDFs are not expected to be encrypted; if one is,
            # we still record what we can rather than failing outright.
            try:
                reader.decrypt("")
            except Exception:  # noqa: BLE001 - best-effort, non-fatal
                warnings.append("PDF is encrypted and could not be opened with an empty password")

        page_count = len(reader.pages)
        char_count = 0
        page_read_errors = 0
        for page in reader.pages:
            try:
                text = page.extract_text() or ""
            except Exception as exc:  # noqa: BLE001 - keep scanning other pages
                page_read_errors += 1
                warnings.append(f"failed to extract text from a page: {exc}")
                continue
            char_count += len(text.strip())

        if page_read_errors:
            warnings.append(f"{page_read_errors} page(s) failed text extraction")

        avg_chars_per_page = char_count / page_count if page_count else 0.0
        has_text_layer = avg_chars_per_page >= MIN_AVG_CHARS_PER_PAGE_FOR_USABLE_TEXT

        return PdfMetadata(
            path=str(path),
            sha256=sha256,
            file_size_bytes=file_size,
            page_count=page_count,
            encrypted=encrypted,
            has_text_layer=has_text_layer,
            text_layer_char_count=char_count,
            readable=True,
            warnings=tuple(warnings),
        )
    except (PdfReadError, OSError, ValueError) as exc:
        warnings.append(f"failed to open/parse PDF: {exc}")
        return PdfMetadata(
            path=str(path),
            sha256=sha256,
            file_size_bytes=file_size,
            page_count=0,
            encrypted=False,
            has_text_layer=False,
            text_layer_char_count=0,
            readable=False,
            warnings=tuple(warnings),
        )
