"""Corpus discovery: filename parsing, PDF metadata, scanning, manifest I/O."""

from enade.inventory.expected_corpus import CorpusComparison, compare_with_expected
from enade.inventory.filenames import ParsedFilename, parse_filename, parse_year_directory
from enade.inventory.git_metadata import GitMetadataError, read_source_repository
from enade.inventory.manifest import (
    DocumentRecord,
    ExamBundle,
    InventoryIssue,
    SourceManifest,
    manifest_to_yaml_dict,
    read_manifest_yaml,
    write_manifest_yaml,
)
from enade.inventory.pdfmeta import PdfMetadata, extract_pdf_metadata, sha256_of_file
from enade.inventory.scanner import scan_corpus

__all__ = [
    "CorpusComparison",
    "DocumentRecord",
    "ExamBundle",
    "GitMetadataError",
    "InventoryIssue",
    "ParsedFilename",
    "PdfMetadata",
    "SourceManifest",
    "compare_with_expected",
    "extract_pdf_metadata",
    "manifest_to_yaml_dict",
    "parse_filename",
    "parse_year_directory",
    "read_manifest_yaml",
    "read_source_repository",
    "scan_corpus",
    "sha256_of_file",
    "write_manifest_yaml",
]
