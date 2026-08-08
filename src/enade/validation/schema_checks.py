"""Validate fixture files against the canonical Pydantic data contracts.

This backs ``enade validate-schema``: it walks a directory of example
Markdown questions / YAML taxonomy / YAML material / YAML misconception
fixtures and reports, per file, whether it satisfies its contract. It does
*not* validate the corpus or the manifest - see validation/manifest_checks.py
for that.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml
from pydantic import ValidationError

from enade.markdown_format import MarkdownFormatError, load_question_markdown
from enade.models.material import Material
from enade.models.misconception import MisconceptionDefinition
from enade.models.taxonomy import Taxonomy


@dataclass
class FixtureValidationResult:
    path: Path
    kind: str
    ok: bool
    error: str | None = None


def validate_question_markdown_file(path: Path) -> FixtureValidationResult:
    try:
        load_question_markdown(path)
    except (MarkdownFormatError, ValidationError, yaml.YAMLError) as exc:
        return FixtureValidationResult(path=path, kind="question", ok=False, error=str(exc))
    return FixtureValidationResult(path=path, kind="question", ok=True)


def validate_taxonomy_yaml_file(path: Path) -> FixtureValidationResult:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        Taxonomy.model_validate(data)
    except (ValidationError, yaml.YAMLError) as exc:
        return FixtureValidationResult(path=path, kind="taxonomy", ok=False, error=str(exc))
    return FixtureValidationResult(path=path, kind="taxonomy", ok=True)


def validate_material_yaml_file(path: Path) -> FixtureValidationResult:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        Material.model_validate(data)
    except (ValidationError, yaml.YAMLError) as exc:
        return FixtureValidationResult(path=path, kind="material", ok=False, error=str(exc))
    return FixtureValidationResult(path=path, kind="material", ok=True)


def validate_misconception_yaml_file(path: Path) -> FixtureValidationResult:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        MisconceptionDefinition.model_validate(data)
    except (ValidationError, yaml.YAMLError) as exc:
        return FixtureValidationResult(path=path, kind="misconception", ok=False, error=str(exc))
    return FixtureValidationResult(path=path, kind="misconception", ok=True)


def validate_misconception_catalog_file(path: Path) -> FixtureValidationResult:
    """Validate a catalog file shaped as ``{misconceptions: [MisconceptionDefinition, ...]}``."""
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        entries = data.get("misconceptions", []) if isinstance(data, dict) else []
        for entry in entries:
            MisconceptionDefinition.model_validate(entry)
    except (ValidationError, yaml.YAMLError) as exc:
        return FixtureValidationResult(
            path=path, kind="misconception-catalog", ok=False, error=str(exc)
        )
    return FixtureValidationResult(path=path, kind="misconception-catalog", ok=True)


def validate_fixtures_directory(root: Path) -> list[FixtureValidationResult]:
    """Validate every fixture expected to be *valid* under ``root``.

    Expected layout (see tests/fixtures/):
        questions/valid/*.md          -> Question (via the Markdown format)
        taxonomy/valid/*.yaml         -> Taxonomy
        materials/valid/*.yaml        -> Material
        misconceptions/valid/*.yaml   -> MisconceptionDefinition

    Sibling ``invalid/`` directories exist for negative testing (see
    tests/test_schema_*.py) and are intentionally not walked here: a
    fixture designed to fail validation should not make ``enade
    validate-schema`` report a failure.
    """
    results: list[FixtureValidationResult] = []

    questions_dir = root / "questions" / "valid"
    if questions_dir.is_dir():
        for md_path in sorted(questions_dir.glob("*.md")):
            results.append(validate_question_markdown_file(md_path))

    taxonomy_dir = root / "taxonomy" / "valid"
    if taxonomy_dir.is_dir():
        for yaml_path in sorted(taxonomy_dir.glob("*.yaml")):
            results.append(validate_taxonomy_yaml_file(yaml_path))

    materials_dir = root / "materials" / "valid"
    if materials_dir.is_dir():
        for yaml_path in sorted(materials_dir.glob("*.yaml")):
            results.append(validate_material_yaml_file(yaml_path))

    misconceptions_dir = root / "misconceptions" / "valid"
    if misconceptions_dir.is_dir():
        for yaml_path in sorted(misconceptions_dir.glob("*.yaml")):
            results.append(validate_misconception_yaml_file(yaml_path))

    return results
