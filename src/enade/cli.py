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
from pathlib import Path

import typer

from enade import __version__
from enade.extraction.audit import build_audit_row, write_audit_csv, write_audit_json
from enade.extraction.expected_structure import (
    compare_with_expected as compare_extraction_with_expected,
)
from enade.extraction.pipeline import extract_exam
from enade.inventory.expected_corpus import compare_with_expected
from enade.inventory.filenames import COURSE_LETTER_MAP
from enade.inventory.git_metadata import GitMetadataError, read_source_repository
from enade.inventory.manifest import read_manifest_yaml, write_manifest_yaml
from enade.inventory.pdfmeta import sha256_of_file
from enade.inventory.scanner import scan_corpus
from enade.markdown_format import load_question_markdown
from enade.models.enums import CourseCode
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
DEFAULT_ASSETS_DIR = PROJECT_ROOT / "data" / "assets" / "questions"
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
    assets_dir: Path = typer.Option(
        DEFAULT_ASSETS_DIR, help="output directory for rendered assets"
    ),
    audit_dir: Path = typer.Option(DEFAULT_AUDIT_DIR, help="output directory for the audit report"),
) -> None:
    """Extract one exam booklet (prova+gabarito+padrao) into canonical Markdown.

    PROMPT-scoped to a single booklet at a time by design (Phase 1A does not
    batch across the corpus) - locates ``<corpus_root>/<year>/<letter>{1,2,3}_*.pdf``
    using the same course-letter convention as ``enade inventory``.
    """
    try:
        course_code = CourseCode(course)
    except ValueError:
        typer.echo(f"unknown course {course!r}; expected one of {[c.value for c in CourseCode]}")
        raise typer.Exit(code=1) from None

    letter = COURSE_TO_LETTER.get(course_code)
    if letter is None:
        typer.echo(
            f"course {course!r} has no known source-filename letter (e.g. 'all-computing' is not supported)"
        )
        raise typer.Exit(code=1)

    year_dir = corpus_root / str(year)
    prova_path = year_dir / f"{letter}1_prova.pdf"
    gabarito_path = year_dir / f"{letter}2_gabarito.pdf"
    padrao_path = year_dir / f"{letter}3_padrao.pdf"
    for p in (prova_path, gabarito_path, padrao_path):
        if not p.exists():
            typer.echo(f"expected source file not found: {p}")
            raise typer.Exit(code=1)

    try:
        repository = read_source_repository(corpus_root)
    except GitMetadataError as exc:
        typer.echo(f"could not read git metadata for {corpus_root}: {exc}")
        raise typer.Exit(code=1) from exc

    exam_id = f"enade-{year}-{letter}"
    typer.echo(f"Extracting {exam_id} ({course_code.value}) from {prova_path.name} ...")
    typer.echo(f"  corpus commit: {repository.commit_sha[:12]} (ref={repository.ref})")

    result = extract_exam(
        prova_path=prova_path,
        gabarito_path=gabarito_path,
        padrao_path=padrao_path,
        corpus_root=corpus_root,
        exam_year=year,
        course=course_code,
        exam_id=exam_id,
        questions_output_dir=questions_dir,
        assets_output_dir=assets_dir,
    )

    m = result.metrics
    typer.echo("")
    typer.echo(
        f"Found {m.questions_found} questions ({m.objectives_found} objective, {m.discursives_found} discursive)"
    )
    typer.echo(f"  verified: {m.verified}   needs_review: {m.needs_review}")
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
    any_review = False
    for question_id, warnings in sorted(result.per_question_warnings.items()):
        if warnings:
            any_review = True
            typer.echo(f"  {question_id}:")
            for w in warnings:
                typer.echo(f"    - {w}")
    if not any_review:
        typer.echo("  (none)")

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
    csv_path = audit_dir / f"extraction-audit-{year}-{letter}.csv"
    json_path = audit_dir / f"extraction-audit-{year}-{letter}.json"
    write_audit_csv(rows, csv_path)
    write_audit_json(rows, json_path)
    typer.echo("")
    typer.echo(f"Audit report: {csv_path}")
    typer.echo(f"Audit report: {json_path}")


@app.command(name="audit-extraction")
def audit_extraction_cmd(
    questions_dir: Path = typer.Option(
        ..., help="directory of already-extracted question .md files to audit"
    ),
    corpus_root: Path = typer.Option(
        DEFAULT_CORPUS_ROOT, help="corpus root for PDF hash cross-check"
    ),
    assets_dir: Path = typer.Option(
        DEFAULT_ASSETS_DIR, help="base directory question asset paths are relative to"
    ),
) -> None:
    """Re-validate already-extracted questions: schema + source/asset provenance."""
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
                asset_path = assets_dir / asset.path
                if not asset_path.exists():
                    problems.append(f"asset file missing: {asset.path}")
                    continue
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


if __name__ == "__main__":
    app()
