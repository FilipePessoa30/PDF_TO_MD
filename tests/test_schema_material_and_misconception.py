from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from enade.models.material import Material
from enade.models.misconception import AlternativeDiagnostic, MisconceptionDefinition


@pytest.mark.parametrize(
    "path", sorted((Path(__file__).parent / "fixtures" / "materials" / "valid").glob("*.yaml"))
)
def test_valid_material_fixtures_pass(path: Path):
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    material = Material.model_validate(data)
    assert material.verification_status.value == "pending"
    assert material.url is None  # Phase 0 must not invent real material URLs


@pytest.mark.parametrize(
    "path", sorted((Path(__file__).parent / "fixtures" / "misconceptions" / "valid").glob("*.yaml"))
)
def test_valid_misconception_fixtures_pass(path: Path):
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    MisconceptionDefinition.model_validate(data)


def test_demo_misconceptions_catalog_is_valid():
    catalog_path = Path(__file__).parent.parent / "data" / "taxonomy" / "demo-misconceptions.yaml"
    data = yaml.safe_load(catalog_path.read_text(encoding="utf-8"))
    entries = [MisconceptionDefinition.model_validate(e) for e in data["misconceptions"]]
    assert len(entries) >= 2
    ids = [e.id for e in entries]
    assert len(ids) == len(set(ids))


def test_material_id_must_be_kebab_case():
    with pytest.raises(ValidationError):
        Material.model_validate(
            {"id": "Not Valid", "title": "x", "type": "article", "verification_status": "pending"}
        )


def test_misconception_definition_requires_known_status():
    with pytest.raises(ValidationError):
        MisconceptionDefinition.model_validate(
            {
                "id": "some-misconception",
                "title": "t",
                "description": "d",
                "status": "not-a-real-status",
            }
        )


def test_alternative_diagnostic_minimal_shape():
    diagnostic = AlternativeDiagnostic.model_validate(
        {"misconception_id": "assumes-tree-is-balanced", "concepts": ["arvore-de-busca"]}
    )
    assert diagnostic.explanation is None
