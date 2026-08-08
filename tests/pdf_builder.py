"""Hand-rolled minimal PDF generator for tests.

No third-party PDF-writing dependency is needed just to produce a few
tiny fixture PDFs: we emit the minimal valid object/xref structure
ourselves. Each page can carry a short text string (drawn with the
built-in Helvetica base font) or be left blank, which is exactly what
tests/test_pdfmeta.py and tests/test_scanner.py need to exercise text-layer
detection both ways.
"""

from __future__ import annotations


def _escape_pdf_string(text: str) -> str:
    return text.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


def build_minimal_pdf(page_texts: list[str | None]) -> bytes:
    """Build a minimal, valid single/multi-page PDF as raw bytes.

    ``page_texts[i]`` is drawn verbatim (ASCII only) on page i, or the page
    is left with an empty content stream (no extractable text) if None.
    """
    if not page_texts:
        raise ValueError("page_texts must contain at least one page")

    n_pages = len(page_texts)
    font_obj = 3
    page_obj_nums = [4 + 2 * i for i in range(n_pages)]
    content_obj_nums = [5 + 2 * i for i in range(n_pages)]
    total_objects = 3 + 2 * n_pages

    kids_str = " ".join(f"{n} 0 R" for n in page_obj_nums)

    parts: list[bytes] = [b"%PDF-1.4\n"]
    offsets: dict[int, int] = {}

    def add_object(num: int, content: bytes) -> None:
        offsets[num] = sum(len(p) for p in parts)
        parts.append(f"{num} 0 obj\n".encode("ascii"))
        parts.append(content)
        parts.append(b"\nendobj\n")

    add_object(1, b"<< /Type /Catalog /Pages 2 0 R >>")
    add_object(2, f"<< /Type /Pages /Kids [{kids_str}] /Count {n_pages} >>".encode("ascii"))
    add_object(font_obj, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    for i, text in enumerate(page_texts):
        page_num = page_obj_nums[i]
        content_num = content_obj_nums[i]
        add_object(
            page_num,
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] "
                f"/Resources << /Font << /F1 {font_obj} 0 R >> >> "
                f"/Contents {content_num} 0 R >>"
            ).encode("ascii"),
        )
        if text:
            stream_body = f"BT /F1 12 Tf 20 100 Td ({_escape_pdf_string(text)}) Tj ET".encode(
                "ascii"
            )
        else:
            stream_body = b""
        stream_obj = (
            f"<< /Length {len(stream_body)} >>\nstream\n".encode("ascii")
            + stream_body
            + b"\nendstream"
        )
        add_object(content_num, stream_obj)

    xref_offset = sum(len(p) for p in parts)
    xref_lines = [f"xref\n0 {total_objects + 1}\n", "0000000000 65535 f \n"]
    for num in range(1, total_objects + 1):
        xref_lines.append(f"{offsets[num]:010d} 00000 n \n")
    xref_bytes = "".join(xref_lines).encode("ascii")

    trailer = f"trailer\n<< /Size {total_objects + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF".encode(
        "ascii"
    )

    return b"".join(parts) + xref_bytes + trailer
