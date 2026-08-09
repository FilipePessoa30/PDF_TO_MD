"""Gold corpus manifest: a regression-lock over an already-audited set of
canonical Markdown questions (PROMPT Phase 1B section 16-18).

"Gold" does not mean immutable forever - it means "the currently audited
set used for regression tests" (section 17). When a real error is found
later, it gets fixed, documented, and the lock deliberately updated via
``enade build-gold`` again; ``enade verify-gold`` must never silently
accept a hash that no longer matches, and this module never writes the
manifest as a side effect of anything else (no auto-update during a normal
pipeline run or test suite).

The manifest does not duplicate the Markdown/asset content itself - only
their identity (sha256) and provenance, referencing the canonical files
that already exist under ``data/questions/``.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from enade import __version__ as pipeline_version
from enade.inventory.pdfmeta import sha256_of_file
from enade.markdown_format import load_questions_directory
from enade.models.question import Question


@dataclass(frozen=True)
class GoldAssetEntry:
    id: str
    path: str
    sha256: str


@dataclass(frozen=True)
class GoldQuestionEntry:
    id: str
    markdown_path: str
    markdown_sha256: str
    extraction_status: str
    automatic_validation: str
    visual_validation: str
    assets: tuple[GoldAssetEntry, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class GoldManifest:
    exam_id: str
    exam_year: int
    course: str
    corpus_commit: str
    prova_sha256: str
    gabarito_sha256: str
    padrao_sha256: str
    pipeline_version: str
    questions: tuple[GoldQuestionEntry, ...]


def _question_markdown_relpath(course_dir: Path, question: Question) -> Path:
    return course_dir / f"{question.id}.md"


def build_gold_manifest(
    *,
    exam_id: str,
    exam_year: int,
    course: str,
    corpus_commit: str,
    prova_path: Path,
    gabarito_path: Path,
    padrao_path: Path,
    course_dir: Path,
) -> GoldManifest:
    """Build a gold manifest from the Markdown/assets currently on disk
    under ``course_dir`` - never from in-memory pipeline state, so the
    manifest always reflects exactly what a reader (or `enade verify-gold`)
    would see on the filesystem.
    """
    questions = load_questions_directory(course_dir)

    entries: list[GoldQuestionEntry] = []
    for question_id in sorted(questions):
        question = questions[question_id]
        md_path = _question_markdown_relpath(course_dir, question)
        asset_entries = tuple(
            GoldAssetEntry(
                id=asset.id,
                path=asset.path,
                sha256=sha256_of_file(md_path.parent / asset.path),
            )
            for asset in question.assets
        )
        entries.append(
            GoldQuestionEntry(
                id=question.id,
                markdown_path=md_path.name,
                markdown_sha256=sha256_of_file(md_path),
                extraction_status=question.extraction_status.value,
                automatic_validation=question.automatic_validation.value,
                visual_validation=question.visual_validation.value,
                assets=asset_entries,
            )
        )

    return GoldManifest(
        exam_id=exam_id,
        exam_year=exam_year,
        course=course,
        corpus_commit=corpus_commit,
        prova_sha256=sha256_of_file(prova_path),
        gabarito_sha256=sha256_of_file(gabarito_path),
        padrao_sha256=sha256_of_file(padrao_path),
        pipeline_version=pipeline_version,
        questions=tuple(entries),
    )


def write_gold_manifest(manifest: GoldManifest, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(manifest)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_gold_manifest(path: Path) -> GoldManifest:
    raw = json.loads(path.read_text(encoding="utf-8"))
    questions = tuple(
        GoldQuestionEntry(
            id=q["id"],
            markdown_path=q["markdown_path"],
            markdown_sha256=q["markdown_sha256"],
            extraction_status=q["extraction_status"],
            automatic_validation=q["automatic_validation"],
            visual_validation=q["visual_validation"],
            assets=tuple(GoldAssetEntry(**a) for a in q.get("assets", [])),
        )
        for q in raw["questions"]
    )
    return GoldManifest(
        exam_id=raw["exam_id"],
        exam_year=raw["exam_year"],
        course=raw["course"],
        corpus_commit=raw["corpus_commit"],
        prova_sha256=raw["prova_sha256"],
        gabarito_sha256=raw["gabarito_sha256"],
        padrao_sha256=raw["padrao_sha256"],
        pipeline_version=raw["pipeline_version"],
        questions=questions,
    )


@dataclass
class GoldDivergence:
    kind: str
    detail: str


def verify_gold_manifest(manifest: GoldManifest, course_dir: Path) -> list[GoldDivergence]:
    """Compare ``manifest`` against what is currently on disk under
    ``course_dir``. Returns an empty list if everything matches.

    Detects: changed Markdown, changed/missing asset, missing question,
    unexpected extra question, hash mismatch (PROMPT section 18).
    """
    divergences: list[GoldDivergence] = []

    on_disk = load_questions_directory(course_dir)
    manifest_ids = {q.id for q in manifest.questions}
    disk_ids = set(on_disk)

    for missing_id in sorted(manifest_ids - disk_ids):
        divergences.append(GoldDivergence("missing_question", missing_id))
    for extra_id in sorted(disk_ids - manifest_ids):
        divergences.append(GoldDivergence("unexpected_extra_question", extra_id))

    for entry in manifest.questions:
        question = on_disk.get(entry.id)
        if question is None:
            continue  # already reported as missing_question above

        md_path = _question_markdown_relpath(course_dir, question)
        if not md_path.exists():
            divergences.append(GoldDivergence("missing_markdown_file", entry.id))
            continue
        actual_md_sha256 = sha256_of_file(md_path)
        if actual_md_sha256 != entry.markdown_sha256:
            divergences.append(
                GoldDivergence(
                    "markdown_hash_mismatch",
                    f"{entry.id}: expected {entry.markdown_sha256}, got {actual_md_sha256}",
                )
            )

        manifest_asset_ids = {a.id for a in entry.assets}
        disk_asset_ids = {a.id for a in question.assets}
        for missing_asset in sorted(manifest_asset_ids - disk_asset_ids):
            divergences.append(
                GoldDivergence("missing_asset", f"{entry.id}: asset {missing_asset}")
            )
        for extra_asset in sorted(disk_asset_ids - manifest_asset_ids):
            divergences.append(
                GoldDivergence("unexpected_extra_asset", f"{entry.id}: asset {extra_asset}")
            )

        for asset_entry in entry.assets:
            asset_path = md_path.parent / asset_entry.path
            if not asset_path.exists():
                divergences.append(
                    GoldDivergence("missing_asset_file", f"{entry.id}: {asset_entry.path}")
                )
                continue
            actual_asset_sha256 = sha256_of_file(asset_path)
            if actual_asset_sha256 != asset_entry.sha256:
                divergences.append(
                    GoldDivergence(
                        "asset_hash_mismatch",
                        f"{entry.id}: {asset_entry.path} expected {asset_entry.sha256}, "
                        f"got {actual_asset_sha256}",
                    )
                )

    return divergences
