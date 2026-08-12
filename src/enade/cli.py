"""Minimal CLI for Phase 0: environment checks, corpus inventory, validation.

enade doctor              - check the local environment
enade inventory           - scan the raw corpus and write the manifest
enade validate-manifest   - audit a manifest for inconsistencies
enade validate-schema     - validate fixtures against the data contracts
"""

from __future__ import annotations

import importlib.metadata
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import typer

from enade import __version__
from enade.extraction.answer_key import parse_answer_key, parse_flat_item_gabarito
from enade.extraction.audit import build_audit_row, write_audit_csv, write_audit_json
from enade.extraction.exam_profile import ExamStructureProfile, load_exam_structure_profile
from enade.extraction.expected_structure import (
    compare_with_expected as compare_extraction_with_expected,
)
from enade.extraction.layout_overrides import load_layout_overrides
from enade.extraction.pipeline import extract_exam
from enade.extraction.transformation_log import write_transformation_log_json
from enade.extraction.visual_audit import (
    load_table_cell_verified_question_ids,
    load_visual_audit,
)
from enade.gold import (
    GoldMaturity,
    build_gold_manifest,
    read_gold_manifest,
    verify_gold_manifest,
    write_gold_manifest,
)
from enade.inventory.expected_corpus import compare_with_expected
from enade.inventory.filenames import COURSE_LETTER_MAP
from enade.inventory.git_metadata import GitMetadataError, read_source_repository
from enade.inventory.manifest import read_manifest_yaml, write_manifest_yaml
from enade.inventory.pdfmeta import sha256_of_file
from enade.inventory.scanner import scan_corpus
from enade.markdown_format import load_question_markdown
from enade.models.enums import CourseCode, VisualValidationStatus
from enade.readiness import assess_readiness
from enade.validation.manifest_checks import check_manifest_matches_filesystem, validate_manifest
from enade.validation.schema_checks import (
    validate_fixtures_directory,
    validate_misconception_catalog_file,
    validate_question_markdown_file,
    validate_taxonomy_yaml_file,
)

app = typer.Typer(add_completion=False, no_args_is_help=True, help=__doc__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_CORPUS_ROOT = PROJECT_ROOT / "data" / "raw" / "geacc-enade"
DEFAULT_MANIFEST_PATH = PROJECT_ROOT / "data" / "manifests" / "source-exams.yaml"
DEFAULT_FIXTURES_DIR = PROJECT_ROOT / "tests" / "fixtures"
DEFAULT_TAXONOMY_PATH = PROJECT_ROOT / "data" / "taxonomy" / "demo-taxonomy.yaml"
DEFAULT_MISCONCEPTIONS_PATH = PROJECT_ROOT / "data" / "taxonomy" / "demo-misconceptions.yaml"
DEFAULT_QUESTIONS_DIR = PROJECT_ROOT / "data" / "questions"
DEFAULT_AUDIT_DIR = PROJECT_ROOT / "data" / "manifests"

#: CourseCode -> source filename letter (inverse of COURSE_LETTER_MAP).
COURSE_TO_LETTER = {code: letter for letter, code in COURSE_LETTER_MAP.items()}

REQUIRED_PACKAGES = ["pydantic", "pypdf", "yaml", "typer"]
MIN_PYTHON = (3, 11)


def _echo_check(label: str, ok: bool, detail: str = "") -> None:
    mark = "[OK]  " if ok else "[FAIL]"
    suffix = f" - {detail}" if detail else ""
    typer.echo(f"{mark} {label}{suffix}")


@app.command()
def doctor() -> None:
    """Check that the local environment is ready to run the pipeline."""
    problems = 0

    py_ok = sys.version_info[:2] >= MIN_PYTHON
    _echo_check("Python >= 3.11", py_ok, f"found {sys.version.split()[0]}")
    problems += 0 if py_ok else 1

    git_path = shutil.which("git")
    if git_path:
        version = subprocess.run(
            ["git", "--version"], text=True, capture_output=True, check=False
        ).stdout.strip()
        _echo_check("git available", True, version)
    else:
        _echo_check("git available", False, "git executable not found on PATH")
        problems += 1

    for mod_name in REQUIRED_PACKAGES:
        dist_name = "PyYAML" if mod_name == "yaml" else mod_name
        try:
            __import__(mod_name)
            version = importlib.metadata.version(dist_name)
            _echo_check(f"python package '{dist_name}'", True, f"v{version}")
        except Exception as exc:  # noqa: BLE001
            _echo_check(f"python package '{dist_name}'", False, str(exc))
            problems += 1

    corpus_present = (DEFAULT_CORPUS_ROOT / ".git").exists()
    if corpus_present:
        try:
            repo = read_source_repository(DEFAULT_CORPUS_ROOT)
            _echo_check(
                "source corpus cloned",
                True,
                f"{repo.repository_url} @ {repo.commit_sha[:12]} (ref={repo.ref})",
            )
        except GitMetadataError as exc:
            _echo_check("source corpus cloned", False, str(exc))
    else:
        typer.echo(
            f"[WARN] source corpus not found at {DEFAULT_CORPUS_ROOT} "
            f"- run 'python scripts/fetch_corpus.py' first"
        )

    manifest_present = DEFAULT_MANIFEST_PATH.exists()
    typer.echo(
        f"[{'OK' if manifest_present else 'WARN'}]  manifest at {DEFAULT_MANIFEST_PATH}"
        f"{'' if manifest_present else ' not generated yet - run `enade inventory`'}"
    )

    typer.echo("")
    if problems:
        typer.echo(f"doctor: {problems} problem(s) found")
        raise typer.Exit(code=1)
    typer.echo("doctor: environment looks OK")


@app.command()
def inventory(
    corpus_root: Path = typer.Option(
        DEFAULT_CORPUS_ROOT, help="path to the cloned geacc/enade corpus"
    ),
    output: Path = typer.Option(DEFAULT_MANIFEST_PATH, help="where to write the manifest YAML"),
) -> None:
    """Scan the raw corpus and write data/manifests/source-exams.yaml."""
    if not corpus_root.exists():
        typer.echo(
            f"corpus root {corpus_root} does not exist - run 'python scripts/fetch_corpus.py' first"
        )
        raise typer.Exit(code=1)

    try:
        repository = read_source_repository(corpus_root)
    except GitMetadataError as exc:
        typer.echo(f"could not read git metadata for {corpus_root}: {exc}")
        raise typer.Exit(code=1) from exc

    typer.echo(
        f"Scanning {corpus_root} (commit {repository.commit_sha[:12]}, ref={repository.ref}) ..."
    )
    manifest = scan_corpus(corpus_root, repository, tool_version=__version__)
    write_manifest_yaml(manifest, output)

    typer.echo(f"Wrote {output}")
    typer.echo(f"Summary: {manifest.summary}")

    errors = [i for i in manifest.issues if i.severity == "error"]
    warnings = [i for i in manifest.issues if i.severity == "warning"]
    for issue in errors:
        typer.echo(f"  [ERROR]   {issue.kind} {issue.path or ''}: {issue.message}")
    for issue in warnings:
        typer.echo(f"  [WARNING] {issue.kind} {issue.path or ''}: {issue.message}")

    comparison = compare_with_expected(manifest)
    typer.echo("")
    if comparison.matches_expected:
        typer.echo("Corpus shape matches the structure previously observed in the Phase 0 brief.")
    else:
        typer.echo(
            "Corpus shape DIVERGES from the structure previously observed in the Phase 0 brief:"
        )
        for year, letter in comparison.missing_bundles:
            typer.echo(f"  - expected but not found: year={year} course_letter={letter!r}")
        for year, letter in comparison.unexpected_bundles:
            typer.echo(
                f"  - found but not previously expected: year={year} course_letter={letter!r}"
            )
        for note in comparison.notes:
            typer.echo(f"  - {note}")

    if errors:
        raise typer.Exit(code=1)


@app.command(name="validate-manifest")
def validate_manifest_cmd(
    manifest_path: Path = typer.Option(DEFAULT_MANIFEST_PATH, help="manifest YAML to validate"),
    corpus_root: Path | None = typer.Option(
        None, help="if given, also cross-check the manifest hashes against the filesystem"
    ),
) -> None:
    """Audit a manifest for internal inconsistencies (and optional filesystem drift)."""
    if not manifest_path.exists():
        typer.echo(f"manifest not found: {manifest_path} - run 'enade inventory' first")
        raise typer.Exit(code=1)

    manifest = read_manifest_yaml(manifest_path)
    result = validate_manifest(manifest)

    for warning in result.warnings:
        typer.echo(f"  [WARNING] {warning}")
    for error in result.errors:
        typer.echo(f"  [ERROR]   {error}")

    drift: list[str] = []
    if corpus_root is not None:
        drift = check_manifest_matches_filesystem(manifest, corpus_root)
        for problem in drift:
            typer.echo(f"  [ERROR]   filesystem drift: {problem}")

    typer.echo("")
    if result.ok and not drift:
        typer.echo(f"validate-manifest: OK ({len(result.warnings)} warning(s))")
    else:
        typer.echo(f"validate-manifest: FAILED ({len(result.errors) + len(drift)} error(s))")
        raise typer.Exit(code=1)


@app.command(name="validate-schema")
def validate_schema_cmd(
    fixtures_dir: Path = typer.Option(
        DEFAULT_FIXTURES_DIR, help="directory containing 'valid' fixture subtrees"
    ),
) -> None:
    """Validate fixtures + demo taxonomy against the canonical data contracts."""
    results = validate_fixtures_directory(fixtures_dir)

    if DEFAULT_TAXONOMY_PATH.exists():
        results.append(validate_taxonomy_yaml_file(DEFAULT_TAXONOMY_PATH))
    if DEFAULT_MISCONCEPTIONS_PATH.exists():
        results.append(validate_misconception_catalog_file(DEFAULT_MISCONCEPTIONS_PATH))

    if not results:
        typer.echo(f"no fixtures found under {fixtures_dir}")
        raise typer.Exit(code=1)

    failed = 0
    for result in results:
        try:
            rel = result.path.relative_to(PROJECT_ROOT)
        except ValueError:
            rel = result.path
        if result.ok:
            typer.echo(f"[OK]   {result.kind:12s} {rel}")
        else:
            failed += 1
            typer.echo(f"[FAIL] {result.kind:12s} {rel}: {result.error}")

    typer.echo("")
    typer.echo(f"validate-schema: {len(results) - failed}/{len(results)} fixture(s) valid")
    if failed:
        raise typer.Exit(code=1)


@dataclass(frozen=True)
class BookletLocation:
    """Where one booklet's source PDFs live and how its output is named.

    Resolved once, in one place, for every command that needs to locate a
    booklet - ``extract``, ``build-gold``, ``verify-gold``,
    ``assess-readiness`` - so the ``course=all-computing`` (unified
    booklet, PROMPT Phase 2A) dispatch logic exists exactly once rather
    than being re-derived per command.
    """

    course_code: CourseCode
    is_unified: bool
    prova_path: Path
    gabarito_path: Path
    padrao_path: Path
    exam_id: str
    file_slug: str
    structure_profile: ExamStructureProfile | None
    output_dir_name: str


@dataclass(frozen=True)
class BookletNaming:
    """The naming half of ``BookletLocation`` - no PDF paths, no filesystem
    checks beyond reading a unified booklet's own (small) structure profile.
    Used by commands that only ever touch already-extracted Markdown
    (``verify-gold``, ``assess-readiness``) and have no reason to require
    the raw corpus PDFs to be present.
    """

    course_code: CourseCode
    is_unified: bool
    exam_id: str
    file_slug: str
    structure_profile: ExamStructureProfile | None
    output_dir_name: str


def _resolve_booklet_naming(year: int, course: str) -> BookletNaming:
    try:
        course_code = CourseCode(course)
    except ValueError:
        typer.echo(f"unknown course {course!r}; expected one of {[c.value for c in CourseCode]}")
        raise typer.Exit(code=1) from None

    is_unified = course_code == CourseCode.ALL_COMPUTING
    if not is_unified and COURSE_TO_LETTER.get(course_code) is None:
        typer.echo(f"course {course!r} has no known source-filename letter")
        raise typer.Exit(code=1)

    if is_unified:
        profile_path = DEFAULT_AUDIT_DIR / f"exam-structure-{year}.yaml"
        if not profile_path.exists():
            typer.echo(f"no unified-booklet structure profile found at {profile_path}")
            raise typer.Exit(code=1)
        structure_profile = load_exam_structure_profile(profile_path)
        exam_id = structure_profile.exam_id
        file_slug = structure_profile.id_shorthand
    else:
        structure_profile = None
        letter = COURSE_TO_LETTER[course_code]
        exam_id = f"enade-{year}-{letter}"
        file_slug = letter

    return BookletNaming(
        course_code=course_code,
        is_unified=is_unified,
        exam_id=exam_id,
        file_slug=file_slug,
        structure_profile=structure_profile,
        output_dir_name=course_code.value,
    )


def _resolve_booklet_location(year: int, course: str, corpus_root: Path) -> BookletLocation:
    """Locate a booklet's source PDFs and naming, or exit(1) with a clear message."""
    naming = _resolve_booklet_naming(year, course)
    year_dir = corpus_root / str(year)
    if naming.is_unified:
        prova_path = year_dir / "1_prova.pdf"
        gabarito_path = year_dir / "2_gabarito.pdf"
        padrao_path = year_dir / "3_padrao.pdf"
    else:
        letter = naming.file_slug
        prova_path = year_dir / f"{letter}1_prova.pdf"
        gabarito_path = year_dir / f"{letter}2_gabarito.pdf"
        padrao_path = year_dir / f"{letter}3_padrao.pdf"

    for p in (prova_path, gabarito_path, padrao_path):
        if not p.exists():
            typer.echo(f"expected source file not found: {p}")
            raise typer.Exit(code=1)

    return BookletLocation(
        course_code=naming.course_code,
        is_unified=naming.is_unified,
        prova_path=prova_path,
        gabarito_path=gabarito_path,
        padrao_path=padrao_path,
        exam_id=naming.exam_id,
        file_slug=naming.file_slug,
        structure_profile=naming.structure_profile,
        output_dir_name=naming.output_dir_name,
    )


@app.command()
def extract(
    year: int = typer.Option(..., help="exam year, e.g. 2021"),
    course: str = typer.Option(..., help="course code, e.g. ciencia-da-computacao-bacharelado"),
    corpus_root: Path = typer.Option(
        DEFAULT_CORPUS_ROOT, help="path to the cloned geacc/enade corpus"
    ),
    questions_dir: Path = typer.Option(
        DEFAULT_QUESTIONS_DIR, help="output directory for Markdown questions"
    ),
    audit_dir: Path = typer.Option(DEFAULT_AUDIT_DIR, help="output directory for the audit report"),
    visual_audit_file: Path | None = typer.Option(
        None,
        help="JSON file of {question_id: {status, notes}} human visual-audit results "
        "(default: data/manifests/visual-audit-<year>-<letter>.json if present)",
    ),
) -> None:
    """Extract one exam booklet (prova+gabarito+padrao) into canonical Markdown.

    PROMPT-scoped to a single booklet at a time by design (Phase 1A does not
    batch across the corpus) - locates ``<corpus_root>/<year>/<letter>{1,2,3}_*.pdf``
    using the same course-letter convention as ``enade inventory``.

    ``course=all-computing`` selects a *unified* multi-course booklet
    instead (PROMPT Phase 2A): source files are looked up without a course
    letter (``<corpus_root>/<year>/{1,2,3}_*.pdf``, e.g. 2011's single
    "COMPUTACAO" caderno) and a declarative
    ``data/manifests/exam-structure-<year>.yaml`` profile drives each
    question's section/applicable-courses/id - see ``exam_profile.py``.
    Nothing about the extractor itself branches on year; this dispatch is
    the one place that decides which shape a given booklet is.
    """
    loc = _resolve_booklet_location(year, course, corpus_root)
    course_code, is_unified = loc.course_code, loc.is_unified
    prova_path, gabarito_path, padrao_path = loc.prova_path, loc.gabarito_path, loc.padrao_path
    exam_id, file_slug, structure_profile = loc.exam_id, loc.file_slug, loc.structure_profile

    try:
        repository = read_source_repository(corpus_root)
    except GitMetadataError as exc:
        typer.echo(f"could not read git metadata for {corpus_root}: {exc}")
        raise typer.Exit(code=1) from exc

    typer.echo(f"Extracting {exam_id} ({course_code.value}) from {prova_path.name} ...")
    typer.echo(f"  corpus commit: {repository.commit_sha[:12]} (ref={repository.ref})")

    resolved_visual_audit_file = visual_audit_file or (
        DEFAULT_AUDIT_DIR / f"visual-audit-{year}-{file_slug}.json"
    )
    visual_audit = load_visual_audit(resolved_visual_audit_file)
    if visual_audit:
        typer.echo(
            f"  visual audit: {len(visual_audit)} entries loaded from {resolved_visual_audit_file}"
        )
    table_cells_verified_ids = load_table_cell_verified_question_ids(resolved_visual_audit_file)
    layout_overrides = load_layout_overrides(DEFAULT_AUDIT_DIR / "layout-overrides.yaml")

    result = extract_exam(
        prova_path=prova_path,
        gabarito_path=gabarito_path,
        padrao_path=padrao_path,
        corpus_root=corpus_root,
        exam_year=year,
        course=None if is_unified else course_code,
        exam_id=exam_id,
        questions_output_dir=questions_dir,
        visual_audit=visual_audit,
        table_cells_verified_ids=table_cells_verified_ids,
        structure_profile=structure_profile,
        output_dir_name=course_code.value if is_unified else None,
        answer_key_parser=parse_flat_item_gabarito if is_unified else parse_answer_key,
        layout_overrides=layout_overrides,
    )

    m = result.metrics
    typer.echo("")
    typer.echo(
        f"Found {m.questions_found} questions ({m.objectives_found} objective, {m.discursives_found} discursive)"
    )
    typer.echo(
        f"  verified: {m.verified}   needs_review: {m.needs_review}   "
        f"extracted (pending visual audit): {m.extracted_pending_visual}"
    )
    typer.echo(f"  assets rendered: {m.total_assets}   alternatives: {m.total_alternatives}")
    typer.echo(f"  answers linked: {m.answers_linked}/{m.objectives_found}")
    typer.echo(f"  answer standards linked: {m.answer_standards_linked}/{m.discursives_found}")
    typer.echo(f"  files written: {m.files_written}   unchanged: {m.files_unchanged}")
    typer.echo(f"  pages processed: {m.pages_processed}   elapsed: {m.elapsed_seconds:.2f}s")
    typer.echo(f"  excluded perception page(s): {result.excluded_perception_pages}")

    if result.structural_warnings:
        typer.echo("")
        typer.echo("structural warnings:")
        for warning in result.structural_warnings:
            typer.echo(f"  - {warning}")

    typer.echo("")
    typer.echo("questions needing review:")
    questions_by_id = {q.id: q for q in result.questions}
    any_review = False
    for question_id in sorted(questions_by_id):
        warnings = list(result.per_question_warnings.get(question_id, []))
        question = questions_by_id[question_id]
        if question.visual_validation == VisualValidationStatus.FAILED:
            warnings.append("visual audit failed (see visual-audit file notes)")
        if warnings:
            any_review = True
            typer.echo(f"  {question_id}:")
            for w in warnings:
                typer.echo(f"    - {w}")
    if not any_review:
        typer.echo("  (none)")

    # `expected_structure.py` records what was previously observed for the
    # single-course 2021 shape (35 obj/5 disc) - not meaningful for a
    # unified booklet's own, structurally different question count, so this
    # comparison is skipped there (the structure profile's own zero-warning
    # cross-check against the PDF already serves the same "matches what we
    # expected" role for that shape - see exam_profile.verify_declared_profile).
    if not is_unified:
        comparison = compare_extraction_with_expected(result)
        typer.echo("")
        if comparison.matches_expected:
            typer.echo("Structure matches what was previously observed for this booklet.")
        else:
            typer.echo("Structure DIVERGES from what was previously observed:")
            for note in comparison.notes:
                typer.echo(f"  - {note}")

    audit_dir.mkdir(parents=True, exist_ok=True)
    rows = [
        build_audit_row(q, result.per_question_warnings.get(q.id, [])) for q in result.questions
    ]
    csv_path = audit_dir / f"extraction-audit-{year}-{file_slug}.csv"
    json_path = audit_dir / f"extraction-audit-{year}-{file_slug}.json"
    write_audit_csv(rows, csv_path)
    write_audit_json(rows, json_path)
    typer.echo("")
    typer.echo(f"Audit report: {csv_path}")
    typer.echo(f"Audit report: {json_path}")

    transformation_log_path = audit_dir / f"transformation-log-{year}-{file_slug}.json"
    write_transformation_log_json(result.transformation_log, transformation_log_path)
    typer.echo(
        f"Transformation log: {transformation_log_path} "
        f"({len(result.transformation_log)} entr{'y' if len(result.transformation_log) == 1 else 'ies'})"
    )


def _is_git_ignored(path: Path) -> bool:
    """True if ``path`` would be excluded from `git add` by current .gitignore rules.

    Canonical assets must be trackable (see docs/decisions.md, Phase 1B) -
    a passing hash/existence check is not enough on its own if the file
    would silently never make it into a commit.
    """
    result = subprocess.run(
        ["git", "check-ignore", "--quiet", str(path)],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
    )
    return result.returncode == 0


@app.command(name="audit-extraction")
def audit_extraction_cmd(
    questions_dir: Path = typer.Option(
        ..., help="directory of already-extracted question .md files to audit"
    ),
    corpus_root: Path = typer.Option(
        DEFAULT_CORPUS_ROOT, help="corpus root for PDF hash cross-check"
    ),
) -> None:
    """Re-validate already-extracted questions: schema + source/asset provenance.

    Asset paths are resolved relative to each question's own .md file - the
    same way any standard Markdown viewer resolves `![...](path)` - not
    against a separate assets root, so this check also catches a link a
    human opening the file in an editor would see as broken.
    """
    md_files = sorted(questions_dir.rglob("*.md"))
    if not md_files:
        typer.echo(f"no question files found under {questions_dir}")
        raise typer.Exit(code=1)

    failed = 0
    seen_ids: dict[str, Path] = {}
    for path in md_files:
        problems: list[str] = []
        schema_result = validate_question_markdown_file(path)
        if not schema_result.ok:
            problems.append(f"schema: {schema_result.error}")
        else:
            question = load_question_markdown(path)
            if question.id in seen_ids:
                problems.append(f"duplicate id (also used by {seen_ids[question.id].name})")
            seen_ids[question.id] = path

            for occurrence in question.source_occurrences:
                pdf_path = corpus_root / occurrence.source_path
                if not pdf_path.exists():
                    problems.append(f"source PDF missing: {occurrence.source_path}")
                    continue
                actual_sha256 = sha256_of_file(pdf_path)
                if actual_sha256 != occurrence.pdf_sha256:
                    problems.append(f"sha256 drift for {occurrence.source_path}")

            for asset in question.assets:
                asset_path = path.parent / asset.path
                if not asset_path.exists():
                    problems.append(f"asset file missing: {asset.path}")
                    continue
                if _is_git_ignored(asset_path):
                    problems.append(f"asset is gitignored (must be trackable): {asset.path}")
                if asset.sha256:
                    actual_sha256 = sha256_of_file(asset_path)
                    if actual_sha256 != asset.sha256:
                        problems.append(f"asset sha256 drift: {asset.path}")

        if problems:
            failed += 1
            typer.echo(f"[FAIL] {path.name}")
            for problem in problems:
                typer.echo(f"    - {problem}")
        else:
            typer.echo(f"[OK]   {path.name}")

    typer.echo("")
    typer.echo(f"audit-extraction: {len(md_files) - failed}/{len(md_files)} OK")
    if failed:
        raise typer.Exit(code=1)


@app.command(name="build-gold")
def build_gold_cmd(
    year: int = typer.Option(..., help="exam year, e.g. 2021"),
    course: str = typer.Option(..., help="course code, e.g. ciencia-da-computacao-bacharelado"),
    corpus_root: Path = typer.Option(
        DEFAULT_CORPUS_ROOT, help="path to the cloned geacc/enade corpus"
    ),
    questions_dir: Path = typer.Option(
        DEFAULT_QUESTIONS_DIR, help="directory of already-extracted question .md files"
    ),
    gold_dir: Path = typer.Option(DEFAULT_AUDIT_DIR, help="output directory for the gold manifest"),
    maturity: GoldMaturity = typer.Option(
        GoldMaturity.PROVISIONAL,
        help="corpus maturity to record (PROMPT Phase 1C section 13) - "
        "'validated' is a deliberate claim, never the default",
    ),
    structural_blocker: list[str] = typer.Option(
        [],
        "--structural-blocker",
        help="a still-open structural issue id to record (repeatable); "
        "omit entirely once none remain",
    ),
) -> None:
    """Lock the current on-disk Markdown/assets as the gold regression set
    (PROMPT section 16-18). Deliberate and explicit only - never run as a
    side effect of ``extract``, ``audit-extraction``, or the test suite.
    Re-run this only after intentionally accepting a real, reviewed change.
    """
    loc = _resolve_booklet_location(year, course, corpus_root)

    try:
        repository = read_source_repository(corpus_root)
    except GitMetadataError as exc:
        typer.echo(f"could not read git metadata for {corpus_root}: {exc}")
        raise typer.Exit(code=1) from exc

    course_dir = questions_dir / str(year) / loc.output_dir_name
    manifest = build_gold_manifest(
        exam_id=loc.exam_id,
        exam_year=year,
        course=loc.course_code.value,
        corpus_commit=repository.commit_sha,
        prova_path=loc.prova_path,
        gabarito_path=loc.gabarito_path,
        padrao_path=loc.padrao_path,
        course_dir=course_dir,
        maturity=maturity,
        structural_blockers=tuple(structural_blocker),
    )

    typer.echo(
        f"Gold manifest: {len(manifest.questions)} questions "
        f"({manifest.verified_count} verified, {manifest.needs_review_count} needs_review) "
        f"- maturity={manifest.maturity}"
    )
    for q in manifest.questions:
        if q.extraction_status != "verified":
            typer.echo(f"  - {q.id}: {q.extraction_status}")
    if manifest.structural_blockers:
        typer.echo(f"Structural blockers recorded: {list(manifest.structural_blockers)}")
    typer.echo(
        f"Answer standards covered: {len(manifest.answer_standards)} "
        f"({sum(len(a.assets) for a in manifest.answer_standards)} padrao asset(s))"
    )

    gold_path = gold_dir / f"gold-{year}-{loc.file_slug}.json"
    write_gold_manifest(manifest, gold_path)
    typer.echo(f"Wrote {gold_path}")


@app.command(name="verify-gold")
def verify_gold_cmd(
    year: int = typer.Option(..., help="exam year, e.g. 2021"),
    course: str = typer.Option(..., help="course code, e.g. ciencia-da-computacao-bacharelado"),
    questions_dir: Path = typer.Option(
        DEFAULT_QUESTIONS_DIR, help="directory of already-extracted question .md files"
    ),
    gold_dir: Path = typer.Option(DEFAULT_AUDIT_DIR, help="directory containing the gold manifest"),
) -> None:
    """Detect drift between the locked gold manifest and what is currently
    on disk (PROMPT section 18): changed Markdown, changed/missing asset,
    missing question, unexpected extra question, hash mismatch. Exits
    non-zero on any divergence - never silently accepts a changed hash.
    """
    naming = _resolve_booklet_naming(year, course)

    gold_path = gold_dir / f"gold-{year}-{naming.file_slug}.json"
    if not gold_path.exists():
        typer.echo(f"no gold manifest found at {gold_path} (run `enade build-gold` first)")
        raise typer.Exit(code=1)

    manifest = read_gold_manifest(gold_path)
    course_dir = questions_dir / str(year) / naming.output_dir_name
    divergences = verify_gold_manifest(manifest, course_dir)

    if not divergences:
        typer.echo(f"verify-gold: OK ({len(manifest.questions)} questions match {gold_path})")
        # PROMPT Phase 1C section 13: this proves absence of drift, never
        # "every question is verified" - the two are deliberately never
        # conflated in this output. See `enade assess-readiness` for the
        # separate, substantive readiness question.
        typer.echo(
            f"  maturity={manifest.maturity} "
            f"verified={manifest.verified_count} needs_review={manifest.needs_review_count} "
            f"(verify-gold only checks hashes - see `enade assess-readiness` for readiness)"
        )
        return

    typer.echo(f"verify-gold: {len(divergences)} divergence(s) found against {gold_path}")
    for d in divergences:
        typer.echo(f"  [{d.kind}] {d.detail}")
    raise typer.Exit(code=1)


@app.command(name="assess-readiness")
def assess_readiness_cmd(
    year: int = typer.Option(..., help="exam year, e.g. 2021"),
    course: str = typer.Option(..., help="course code, e.g. ciencia-da-computacao-bacharelado"),
    questions_dir: Path = typer.Option(
        DEFAULT_QUESTIONS_DIR, help="directory of already-extracted question .md files"
    ),
    gold_dir: Path = typer.Option(DEFAULT_AUDIT_DIR, help="directory containing the gold manifest"),
    ready_label: str = typer.Option(
        "READY_FOR_2011",
        help="label printed when ready - override for a booklet whose readiness doesn't "
        "mean 'ready to process 2011' (e.g. 2011 itself: READY_FOR_LEGACY_LAYOUT_TEST)",
    ),
    not_ready_label: str = typer.Option("NOT_READY_FOR_2011", help="label printed when not ready"),
) -> None:
    """Readiness gate, separate from hash verification (PROMPT Phase 1C
    section 14): considers gold integrity, structural blockers, automatic
    and visual validation, asset integrity, answer linkage, and
    answer-standard coverage. Prints READY_FOR_2011/NOT_READY_FOR_2011 (or
    the ``--ready-label``/``--not-ready-label`` override) and every
    individual blocker - never a bare pass/fail count. Exits non-zero when
    not ready.
    """
    naming = _resolve_booklet_naming(year, course)

    gold_path = gold_dir / f"gold-{year}-{naming.file_slug}.json"
    if not gold_path.exists():
        typer.echo(f"no gold manifest found at {gold_path} (run `enade build-gold` first)")
        raise typer.Exit(code=1)

    manifest = read_gold_manifest(gold_path)
    course_dir = questions_dir / str(year) / naming.output_dir_name
    visual_audit_path = DEFAULT_AUDIT_DIR / f"visual-audit-{year}-{naming.file_slug}.json"
    blocker_ledger_path = DEFAULT_AUDIT_DIR / f"blocker-ledger-{year}.yaml"
    report = assess_readiness(
        manifest,
        course_dir,
        visual_audit_path=visual_audit_path,
        blocker_ledger_path=blocker_ledger_path if blocker_ledger_path.exists() else None,
    )

    typer.echo(f"assess-readiness: {ready_label if report.ready else not_ready_label}")
    typer.echo(
        f"  {report.verified_count}/{report.total_questions} verified, "
        f"{report.needs_review_count} needs_review, gold maturity={report.gold_maturity}"
    )
    if report.visual_audit_coverage is not None:
        cov = report.visual_audit_coverage
        typer.echo(
            f"  visual audit: {cov.passed_count} passed, {cov.failed_count} failed, "
            f"{cov.not_performed_count} not_performed (fully_covered={cov.fully_covered})"
        )
    if report.blockers:
        typer.echo(f"  {len(report.blockers)} blocker(s):")
        for b in report.blockers:
            kind = "structural" if b.structural else "non-structural"
            typer.echo(f"    - [{b.kind}, {kind}] {b.detail}")
    else:
        typer.echo("  no blockers")

    if not report.ready:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
