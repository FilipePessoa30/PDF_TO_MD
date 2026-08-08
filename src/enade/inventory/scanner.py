"""Walk a corpus directory tree and build a :class:`SourceManifest`.

This is the only place in the codebase that touches the filesystem layout
of the raw corpus. It composes ``filenames.py`` (string parsing) and
``pdfmeta.py`` (binary inspection) and is deliberately tolerant: anything
unexpected becomes an :class:`InventoryIssue`, not an exception, so one bad
file never aborts the whole inventory.

Determinism: entries are discovered via ``sorted()`` at every level, and
the resulting bundles/orphans/issues are sorted again in
``manifest.manifest_to_yaml_dict``. Running this twice against an unchanged
corpus directory therefore always yields the same semantic manifest.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from enade.inventory.filenames import parse_filename, parse_year_directory
from enade.inventory.manifest import DocumentRecord, ExamBundle, InventoryIssue, SourceManifest
from enade.inventory.pdfmeta import extract_pdf_metadata
from enade.models.enums import DocType
from enade.models.provenance import SourceRepository

#: Files/directories expected at the corpus root that are not year directories.
IGNORED_ROOT_ENTRIES = {"README.md", "LICENSE", ".git", ".gitignore", ".gitattributes"}

_SLOT_BY_DOCTYPE = {
    DocType.EXAM: "exam",
    DocType.ANSWER_KEY: "answer_key",
    DocType.ANSWER_STANDARD: "answer_standard",
}
_LABEL_BY_SLOT = {
    "exam": "prova",
    "answer_key": "gabarito",
    "answer_standard": "padrao de resposta",
}


def _make_exam_id(year: int, course_letter: str | None) -> str:
    return f"enade-{year}-{course_letter}" if course_letter else f"enade-{year}-unificado"


def scan_corpus(
    corpus_root: Path, repository: SourceRepository, *, tool_version: str
) -> SourceManifest:
    """Build a full :class:`SourceManifest` by scanning ``corpus_root``."""
    issues: list[InventoryIssue] = []
    orphan_files: list[DocumentRecord] = []
    bundles: dict[tuple[int, str | None], ExamBundle] = {}

    root_entries = sorted(p.name for p in corpus_root.iterdir())
    for name in root_entries:
        entry = corpus_root / name
        if entry.is_dir():
            if name in IGNORED_ROOT_ENTRIES:
                continue
            year = parse_year_directory(name)
            if year is None:
                issues.append(
                    InventoryIssue(
                        kind="unexpected_directory",
                        severity="warning",
                        message=f"directory {name!r} at corpus root is not a 4-digit year",
                        path=name,
                    )
                )
                continue
            _scan_year_directory(entry, corpus_root, year, bundles, orphan_files, issues)
        elif name not in IGNORED_ROOT_ENTRIES:
            issues.append(
                InventoryIssue(
                    kind="unexpected_root_entry",
                    severity="warning",
                    message=f"unexpected file {name!r} at corpus root",
                    path=name,
                )
            )

    final_bundles = _finalize_bundles(bundles, issues)

    summary = build_summary(final_bundles, orphan_files, issues)

    return SourceManifest(
        generated_at=datetime.now(UTC),
        tool_version=tool_version,
        repository=repository,
        corpus_root=str(corpus_root),
        bundles=final_bundles,
        orphan_files=orphan_files,
        issues=issues,
        summary=summary,
    )


def _scan_year_directory(
    year_dir: Path,
    corpus_root: Path,
    year: int,
    bundles: dict[tuple[int, str | None], ExamBundle],
    orphan_files: list[DocumentRecord],
    issues: list[InventoryIssue],
) -> None:
    for entry in sorted(year_dir.iterdir()):
        rel_path = entry.relative_to(corpus_root).as_posix()
        if entry.is_dir():
            issues.append(
                InventoryIssue(
                    kind="unexpected_directory",
                    severity="warning",
                    message=f"unexpected subdirectory {rel_path!r} inside a year directory",
                    path=rel_path,
                )
            )
            continue
        if entry.suffix.lower() != ".pdf":
            issues.append(
                InventoryIssue(
                    kind="unexpected_file_type",
                    severity="warning",
                    message=f"non-PDF file {rel_path!r} found inside a year directory",
                    path=rel_path,
                )
            )
            continue

        parsed = parse_filename(entry.name)
        meta = extract_pdf_metadata(entry)
        warnings = [*parsed.warnings, *meta.warnings]

        doc = DocumentRecord(
            source_path=rel_path,
            filename=entry.name,
            year=year,
            course_letter=parsed.course_letter,
            course_codes=list(parsed.course_codes),
            sequence=parsed.sequence,
            document_type=parsed.document_type,
            sha256=meta.sha256,
            file_size_bytes=meta.file_size_bytes,
            page_count=meta.page_count,
            has_text_layer=meta.has_text_layer,
            text_layer_char_count=meta.text_layer_char_count,
            encrypted=meta.encrypted,
            readable=meta.readable,
            parse_warnings=warnings,
        )

        if not meta.readable:
            issues.append(
                InventoryIssue(
                    kind="unreadable_pdf",
                    severity="error",
                    message="; ".join(meta.warnings) or "failed to read PDF",
                    path=rel_path,
                )
            )

        if not parsed.matched or parsed.document_type is None:
            issues.append(
                InventoryIssue(
                    kind="unexpected_filename",
                    severity="warning",
                    message="; ".join(parsed.warnings)
                    or "filename did not match the expected pattern",
                    path=rel_path,
                )
            )
            orphan_files.append(doc)
            continue

        for warning in parsed.warnings:
            issues.append(
                InventoryIssue(
                    kind="filename_warning", severity="warning", message=warning, path=rel_path
                )
            )

        key = (year, parsed.course_letter)
        bundle = bundles.get(key)
        if bundle is None:
            bundle = ExamBundle(
                exam_id=_make_exam_id(year, parsed.course_letter),
                year=year,
                course_letter=parsed.course_letter,
                course_codes=list(parsed.course_codes),
                is_unified_booklet=parsed.is_unified_booklet,
            )
            bundles[key] = bundle

        slot = _SLOT_BY_DOCTYPE[parsed.document_type]
        existing = getattr(bundle, slot)
        if existing is not None:
            issues.append(
                InventoryIssue(
                    kind="duplicate_document",
                    severity="error",
                    message=(
                        f"both {existing.source_path!r} and {rel_path!r} map to the {slot!r} slot "
                        f"of exam bundle {bundle.exam_id!r}"
                    ),
                    path=rel_path,
                )
            )
            orphan_files.append(doc)
            continue
        setattr(bundle, slot, doc)


def _finalize_bundles(
    bundles: dict[tuple[int, str | None], ExamBundle], issues: list[InventoryIssue]
) -> list[ExamBundle]:
    final_bundles: list[ExamBundle] = []
    for key in sorted(bundles, key=lambda k: (k[0], k[1] or "")):
        bundle = bundles[key]
        missing = [
            slot
            for slot in ("exam", "answer_key", "answer_standard")
            if getattr(bundle, slot) is None
        ]
        bundle.missing = missing
        final_bundles.append(bundle)

        has_exam = "exam" not in missing
        if has_exam:
            if "answer_key" in missing:
                issues.append(
                    InventoryIssue(
                        kind="exam_without_answer_key",
                        severity="error",
                        message=f"exam bundle {bundle.exam_id!r} has a prova but no gabarito",
                        path=bundle.exam.source_path if bundle.exam else None,
                    )
                )
            if "answer_standard" in missing:
                issues.append(
                    InventoryIssue(
                        kind="exam_without_answer_standard",
                        severity="warning",
                        message=f"exam bundle {bundle.exam_id!r} has a prova but no padrao de resposta",
                        path=bundle.exam.source_path if bundle.exam else None,
                    )
                )
        else:
            if "answer_key" not in missing:
                issues.append(
                    InventoryIssue(
                        kind="answer_key_without_exam",
                        severity="error",
                        message=f"exam bundle {bundle.exam_id!r} has a gabarito but no prova",
                        path=bundle.answer_key.source_path if bundle.answer_key else None,
                    )
                )
            if "answer_standard" not in missing:
                issues.append(
                    InventoryIssue(
                        kind="answer_standard_without_exam",
                        severity="error",
                        message=f"exam bundle {bundle.exam_id!r} has a padrao de resposta but no prova",
                        path=bundle.answer_standard.source_path if bundle.answer_standard else None,
                    )
                )
    return final_bundles


def build_summary(
    bundles: list[ExamBundle], orphan_files: list[DocumentRecord], issues: list[InventoryIssue]
) -> dict[str, int]:
    years = {b.year for b in bundles}
    exams = sum(1 for b in bundles if b.exam is not None)
    answer_keys = sum(1 for b in bundles if b.answer_key is not None)
    answer_standards = sum(1 for b in bundles if b.answer_standard is not None)
    return {
        "years": len(years),
        "bundles": len(bundles),
        "exams": exams,
        "answer_keys": answer_keys,
        "answer_standards": answer_standards,
        "total_pdfs": exams + answer_keys + answer_standards + len(orphan_files),
        "orphan_files": len(orphan_files),
        "errors": sum(1 for i in issues if i.severity == "error"),
        "warnings": sum(1 for i in issues if i.severity == "warning"),
    }
