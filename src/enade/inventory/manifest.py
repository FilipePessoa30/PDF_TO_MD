"""The source manifest: a machine-readable inventory of the raw PDF corpus.

Structure: :class:`SourceManifest` is a flat list of :class:`ExamBundle`
(one per year+course "sitting"), each grouping up to three physical
documents (exam/answer_key/answer_standard), plus a list of orphan files
and a list of detected issues (missing pairs, unexpected names, ...).

Determinism: :func:`manifest_to_yaml_dict` renders a manifest to plain
dict/list data with everything sorted by stable keys, so serializing the
same semantic content twice always yields byte-identical YAML. The one
inherently time-varying field, ``generated_at``, is deliberately excluded
from the "semantic" comparison used by determinism tests (see
docs/decisions.md).
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field

from enade.models.enums import CourseCode, DocType
from enade.models.provenance import SourceRepository

MANIFEST_SCHEMA_VERSION = "1.0"
SHA256_PATTERN = r"^[0-9a-f]{64}$"


class DocumentRecord(BaseModel):
    """Everything discovered about one physical PDF file."""

    model_config = ConfigDict(extra="forbid")

    source_path: str
    filename: str
    year: int
    course_letter: str | None
    course_codes: list[CourseCode]
    sequence: int | None
    document_type: DocType | None
    sha256: str = Field(..., pattern=SHA256_PATTERN)
    file_size_bytes: int
    page_count: int
    has_text_layer: bool
    text_layer_char_count: int
    encrypted: bool
    readable: bool
    parse_warnings: list[str] = Field(default_factory=list)


class ExamBundle(BaseModel):
    """One year+course exam sitting: up to 3 documents (exam/key/standard)."""

    model_config = ConfigDict(extra="forbid")

    exam_id: str
    year: int
    course_letter: str | None
    course_codes: list[CourseCode]
    is_unified_booklet: bool
    exam: DocumentRecord | None = None
    answer_key: DocumentRecord | None = None
    answer_standard: DocumentRecord | None = None
    missing: list[str] = Field(default_factory=list)


class InventoryIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: str
    severity: str  # "warning" | "error"
    message: str
    path: str | None = None


class SourceManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = MANIFEST_SCHEMA_VERSION
    generated_at: datetime
    tool_version: str
    repository: SourceRepository
    corpus_root: str
    bundles: list[ExamBundle]
    orphan_files: list[DocumentRecord] = Field(default_factory=list)
    issues: list[InventoryIssue] = Field(default_factory=list)
    summary: dict[str, int] = Field(default_factory=dict)


def _bundle_sort_key(bundle: ExamBundle) -> tuple[int, str]:
    return (bundle.year, bundle.course_letter or "")


def _document_sort_key(doc: DocumentRecord) -> str:
    return doc.source_path


def _issue_sort_key(issue: InventoryIssue) -> tuple[str, str, str]:
    return (issue.kind, issue.path or "", issue.message)


def manifest_to_yaml_dict(
    manifest: SourceManifest, *, include_generated_at: bool = True
) -> dict[str, Any]:
    """Render a manifest to a plain, deterministically ordered dict.

    Pass ``include_generated_at=False`` to get the "semantic" view used for
    determinism comparisons (two runs over the same PDFs should match on
    everything except the wall-clock timestamp).
    """
    data = manifest.model_dump(mode="json")
    data["bundles"] = sorted(data["bundles"], key=lambda b: (b["year"], b["course_letter"] or ""))
    data["orphan_files"] = sorted(data["orphan_files"], key=lambda d: d["source_path"])
    data["issues"] = sorted(
        data["issues"], key=lambda i: (i["kind"], i["path"] or "", i["message"])
    )
    data["summary"] = dict(sorted(data["summary"].items()))
    if not include_generated_at:
        data.pop("generated_at", None)
        data.pop("tool_version", None)
    return data


def write_manifest_yaml(manifest: SourceManifest, path: Path) -> None:
    data = manifest_to_yaml_dict(manifest)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        yaml.safe_dump(data, fh, sort_keys=False, allow_unicode=True, default_flow_style=False)


def read_manifest_yaml(path: Path) -> SourceManifest:
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return SourceManifest.model_validate(data)
