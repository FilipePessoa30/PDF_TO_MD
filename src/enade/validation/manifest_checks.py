"""Audit a (possibly previously generated) :class:`SourceManifest` for problems.

Two independent things are checked:

1. Internal consistency of the manifest itself (unique exam ids, the stored
   ``summary`` actually matching the bundles it summarizes, duplicate
   content hashes, and re-surfacing the error/warning issues recorded at
   scan time).
2. Optionally, that the manifest still matches the filesystem it describes
   (files still exist, hashes still match) - this catches silent corpus
   drift between an ``enade inventory`` run and a later
   ``enade validate-manifest`` run.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from enade.inventory.manifest import SourceManifest
from enade.inventory.pdfmeta import sha256_of_file
from enade.inventory.scanner import build_summary


@dataclass
class ManifestValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def validate_manifest(manifest: SourceManifest) -> ManifestValidationResult:
    """Validate internal consistency of a manifest already loaded into memory."""
    result = ManifestValidationResult()

    for issue in manifest.issues:
        line = f"[{issue.kind}] {issue.path or '-'}: {issue.message}"
        (result.errors if issue.severity == "error" else result.warnings).append(line)

    seen_exam_ids: dict[str, int] = {}
    for bundle in manifest.bundles:
        seen_exam_ids[bundle.exam_id] = seen_exam_ids.get(bundle.exam_id, 0) + 1
    for exam_id, count in seen_exam_ids.items():
        if count > 1:
            result.errors.append(f"duplicate exam_id {exam_id!r} appears in {count} bundles")

    recomputed_summary = build_summary(manifest.bundles, manifest.orphan_files, manifest.issues)
    if recomputed_summary != manifest.summary:
        result.errors.append(
            f"summary does not match bundles/issues in this manifest: "
            f"stored={manifest.summary} recomputed={recomputed_summary}"
        )

    sha_to_paths: dict[str, list[str]] = {}
    for bundle in manifest.bundles:
        for slot in ("exam", "answer_key", "answer_standard"):
            doc = getattr(bundle, slot)
            if doc is not None:
                sha_to_paths.setdefault(doc.sha256, []).append(doc.source_path)
    for sha256, paths in sha_to_paths.items():
        if len(paths) > 1:
            result.warnings.append(f"identical sha256 {sha256[:12]}... shared by files: {paths}")

    return result


def check_manifest_matches_filesystem(manifest: SourceManifest, corpus_root: Path) -> list[str]:
    """Cross-check the manifest's recorded hashes against the files on disk."""
    problems: list[str] = []
    for bundle in manifest.bundles:
        for slot in ("exam", "answer_key", "answer_standard"):
            doc = getattr(bundle, slot)
            if doc is None:
                continue
            path = corpus_root / doc.source_path
            if not path.exists():
                problems.append(
                    f"{doc.source_path}: file referenced by the manifest no longer exists on disk"
                )
                continue
            actual_sha256 = sha256_of_file(path)
            if actual_sha256 != doc.sha256:
                problems.append(
                    f"{doc.source_path}: sha256 drifted (manifest={doc.sha256[:12]}..., "
                    f"disk={actual_sha256[:12]}...)"
                )
    return problems
