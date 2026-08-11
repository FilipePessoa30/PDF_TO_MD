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

Phase 1C (PROMPT section 13/15) added: (1) an explicit maturity/status,
since ``verify-gold: OK`` proves absence of drift, never "every question is
verified" - see ``GoldMaturity``; (2) verified/needs_review counts and the
unresolved question id list, computed from what is actually on disk;
(3) coverage of the official answer standard's own text and assets
(``GoldAnswerStandardEntry``), tracked separately from a question's own
content so tampering with either is independently detectable.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from pathlib import Path

from enade import __version__ as pipeline_version
from enade.inventory.pdfmeta import sha256_of_file
from enade.markdown_format import load_questions_directory
from enade.models.enums import ExtractionStatus
from enade.models.question import DATA_CONTRACT_VERSION, Question


class GoldMaturity(StrEnum):
    """PROMPT Phase 1C section 13: ``verify-gold: OK`` proves absence of
    drift, never "all questions are verified". ``PROVISIONAL`` is the only
    honest state while any question is not ``verified`` (or before this
    phase's gates have all been deliberately re-checked); promotion to
    ``VALIDATED`` is a conscious action (``enade build-gold --maturity
    validated``), never inferred automatically from a clean hash check
    alone. ``SUPERSEDED`` marks a manifest kept only for historical
    reference (e.g. after a later phase replaces it).
    """

    PROVISIONAL = "provisional"
    VALIDATED = "validated"
    SUPERSEDED = "superseded"


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
class GoldAnswerStandardEntry:
    """The official answer standard's own provenance and evidence for one
    discursive question (PROMPT Phase 1C section 15) - tracked separately
    from ``GoldQuestionEntry``, even though both ultimately live inside the
    same question's .md file, so "the question changed" and "the official
    rubric changed" are independently distinguishable, and tampering with a
    padrao-only asset file is detected even though the question's own
    ``Question.assets`` never referenced it.
    """

    question_id: str
    source_path: str
    pdf_sha256: str
    pages: tuple[int, ...]
    text_sha256: str
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
    #: Semantic version of the Question contract's *shape* - see
    #: ``enade.models.question.DATA_CONTRACT_VERSION``.
    data_contract_version: str
    maturity: str
    verified_count: int
    needs_review_count: int
    unresolved_question_ids: tuple[str, ...]
    #: Curated, human-disclosed list of specific still-open *structural*
    #: issues (PROMPT section 14) - deliberately not auto-derived from
    #: ``unresolved_question_ids``: a needs_review question can be an
    #: inherent, non-structural, already-documented ambiguity (e.g. Q20's
    #: l/1 finding, before it was resolved) rather than a pipeline-caused
    #: structural loss, and the two must stay distinguishable to whoever
    #: reads this manifest or runs ``enade assess-readiness``.
    structural_blockers: tuple[str, ...]
    questions: tuple[GoldQuestionEntry, ...]
    answer_standards: tuple[GoldAnswerStandardEntry, ...] = field(default_factory=tuple)


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
    maturity: GoldMaturity = GoldMaturity.PROVISIONAL,
    structural_blockers: tuple[str, ...] = (),
) -> GoldManifest:
    """Build a gold manifest from the Markdown/assets currently on disk
    under ``course_dir`` - never from in-memory pipeline state, so the
    manifest always reflects exactly what a reader (or `enade verify-gold`)
    would see on the filesystem.
    """
    questions = load_questions_directory(course_dir)

    entries: list[GoldQuestionEntry] = []
    answer_standard_entries: list[GoldAnswerStandardEntry] = []
    verified_count = 0
    unresolved_ids: list[str] = []

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

        if question.extraction_status == ExtractionStatus.VERIFIED:
            verified_count += 1
        else:
            unresolved_ids.append(question.id)

        if question.answer_standard is not None:
            padrao_asset_entries = tuple(
                GoldAssetEntry(
                    id=asset.id,
                    path=asset.path,
                    sha256=sha256_of_file(md_path.parent / asset.path),
                )
                for asset in question.answer_standard.assets
            )
            answer_standard_entries.append(
                GoldAnswerStandardEntry(
                    question_id=question.id,
                    source_path=question.answer_standard.source_path,
                    pdf_sha256=question.answer_standard.pdf_sha256,
                    pages=tuple(question.answer_standard.pages),
                    text_sha256=hashlib.sha256(
                        question.answer_standard.text.encode("utf-8")
                    ).hexdigest(),
                    assets=padrao_asset_entries,
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
        data_contract_version=DATA_CONTRACT_VERSION,
        maturity=maturity.value,
        verified_count=verified_count,
        needs_review_count=len(unresolved_ids),
        unresolved_question_ids=tuple(sorted(unresolved_ids)),
        structural_blockers=tuple(sorted(structural_blockers)),
        questions=tuple(entries),
        answer_standards=tuple(answer_standard_entries),
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
    answer_standards = tuple(
        GoldAnswerStandardEntry(
            question_id=a["question_id"],
            source_path=a["source_path"],
            pdf_sha256=a["pdf_sha256"],
            pages=tuple(a["pages"]),
            text_sha256=a["text_sha256"],
            assets=tuple(GoldAssetEntry(**asset) for asset in a.get("assets", [])),
        )
        for a in raw.get("answer_standards", [])
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
        data_contract_version=raw.get("data_contract_version", "unknown"),
        maturity=raw.get("maturity", GoldMaturity.PROVISIONAL.value),
        verified_count=raw.get("verified_count", 0),
        needs_review_count=raw.get("needs_review_count", 0),
        unresolved_question_ids=tuple(raw.get("unresolved_question_ids", ())),
        structural_blockers=tuple(raw.get("structural_blockers", ())),
        questions=questions,
        answer_standards=answer_standards,
    )


@dataclass
class GoldDivergence:
    kind: str
    detail: str


def verify_gold_manifest(manifest: GoldManifest, course_dir: Path) -> list[GoldDivergence]:
    """Compare ``manifest`` against what is currently on disk under
    ``course_dir``. Returns an empty list if everything matches.

    Detects: changed Markdown, changed/missing asset, missing question,
    unexpected extra question, hash mismatch (PROMPT section 18), and
    (Phase 1C, section 15) the same classes of divergence for each
    discursive question's official answer standard - its text and its own
    assets, never conflated with the question's own.
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

    manifest_as_ids = {e.question_id for e in manifest.answer_standards}
    disk_as_ids = {qid for qid, q in on_disk.items() if q.answer_standard is not None}
    for missing_id in sorted(manifest_as_ids - disk_as_ids):
        divergences.append(GoldDivergence("missing_answer_standard", missing_id))
    for extra_id in sorted(disk_as_ids - manifest_as_ids):
        divergences.append(GoldDivergence("unexpected_extra_answer_standard", extra_id))

    for as_entry in manifest.answer_standards:
        question = on_disk.get(as_entry.question_id)
        if question is None or question.answer_standard is None:
            continue  # already reported above

        md_path = _question_markdown_relpath(course_dir, question)
        actual_text_sha256 = hashlib.sha256(
            question.answer_standard.text.encode("utf-8")
        ).hexdigest()
        if actual_text_sha256 != as_entry.text_sha256:
            divergences.append(
                GoldDivergence("answer_standard_text_mismatch", as_entry.question_id)
            )

        manifest_asset_ids = {a.id for a in as_entry.assets}
        disk_asset_ids = {a.id for a in question.answer_standard.assets}
        for missing_asset in sorted(manifest_asset_ids - disk_asset_ids):
            divergences.append(
                GoldDivergence(
                    "missing_answer_standard_asset",
                    f"{as_entry.question_id}: asset {missing_asset}",
                )
            )
        for extra_asset in sorted(disk_asset_ids - manifest_asset_ids):
            divergences.append(
                GoldDivergence(
                    "unexpected_extra_answer_standard_asset",
                    f"{as_entry.question_id}: asset {extra_asset}",
                )
            )

        for asset_entry in as_entry.assets:
            asset_path = md_path.parent / asset_entry.path
            if not asset_path.exists():
                divergences.append(
                    GoldDivergence(
                        "missing_answer_standard_asset_file",
                        f"{as_entry.question_id}: {asset_entry.path}",
                    )
                )
                continue
            actual_asset_sha256 = sha256_of_file(asset_path)
            if actual_asset_sha256 != asset_entry.sha256:
                divergences.append(
                    GoldDivergence(
                        "answer_standard_asset_hash_mismatch",
                        f"{as_entry.question_id}: {asset_entry.path} expected {asset_entry.sha256}, "
                        f"got {actual_asset_sha256}",
                    )
                )

    return divergences
