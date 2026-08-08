from __future__ import annotations

from pathlib import Path

from enade.inventory.pdfmeta import extract_pdf_metadata, sha256_of_file
from tests.conftest import write_pdf


def test_sha256_is_deterministic_and_content_sensitive(tmp_path: Path):
    path_a = write_pdf(tmp_path / "a.pdf", ["HELLO"])
    path_b = write_pdf(tmp_path / "b.pdf", ["HELLO"])
    path_c = write_pdf(tmp_path / "c.pdf", ["DIFFERENT TEXT"])

    hash_a1 = sha256_of_file(path_a)
    hash_a2 = sha256_of_file(path_a)
    hash_b = sha256_of_file(path_b)
    hash_c = sha256_of_file(path_c)

    assert hash_a1 == hash_a2
    assert hash_a1 == hash_b  # identical content -> identical hash
    assert hash_a1 != hash_c
    assert len(hash_a1) == 64


def test_extract_pdf_metadata_detects_usable_text_layer(tmp_path: Path):
    path = write_pdf(tmp_path / "with_text.pdf", ["PROVA DE TESTE " * 10])
    meta = extract_pdf_metadata(path)

    assert meta.readable
    assert meta.page_count == 1
    assert meta.has_text_layer is True
    assert meta.text_layer_char_count > 0
    assert meta.encrypted is False


def test_extract_pdf_metadata_detects_missing_text_layer(tmp_path: Path):
    path = write_pdf(tmp_path / "blank.pdf", [None, None, None])
    meta = extract_pdf_metadata(path)

    assert meta.readable
    assert meta.page_count == 3
    assert meta.has_text_layer is False
    assert meta.text_layer_char_count == 0


def test_extract_pdf_metadata_handles_unreadable_file_gracefully(tmp_path: Path):
    path = tmp_path / "not_a_pdf.pdf"
    path.write_bytes(b"this is definitely not a PDF file")

    meta = extract_pdf_metadata(path)

    assert meta.readable is False
    assert meta.page_count == 0
    assert meta.has_text_layer is False
    assert meta.warnings
    # hashing must still succeed even when parsing fails, for provenance purposes.
    assert len(meta.sha256) == 64
