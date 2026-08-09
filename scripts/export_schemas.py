#!/usr/bin/env python3
"""Export JSON Schema documents for every canonical Pydantic contract.

Run after changing any model in src/enade/models/ to keep schemas/*.schema.json
in sync. This is a plain export step, not a build-time dependency - the
Pydantic models remain the single source of truth at runtime.
"""

from __future__ import annotations

import json
from pathlib import Path

from enade.inventory.manifest import SourceManifest
from enade.models.asset import Asset
from enade.models.material import Material
from enade.models.misconception import AlternativeDiagnostic, MisconceptionDefinition
from enade.models.provenance import AnswerStandardReference
from enade.models.question import Question
from enade.models.taxonomy import Taxonomy

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCHEMAS_DIR = PROJECT_ROOT / "schemas"

MODELS = {
    "question.schema.json": Question,
    "asset.schema.json": Asset,
    "taxonomy.schema.json": Taxonomy,
    "misconception-definition.schema.json": MisconceptionDefinition,
    "alternative-diagnostic.schema.json": AlternativeDiagnostic,
    "answer-standard-reference.schema.json": AnswerStandardReference,
    "material.schema.json": Material,
    "source-manifest.schema.json": SourceManifest,
}


def main() -> int:
    SCHEMAS_DIR.mkdir(parents=True, exist_ok=True)
    for filename, model in MODELS.items():
        schema = model.model_json_schema()
        out_path = SCHEMAS_DIR / filename
        out_path.write_text(
            json.dumps(schema, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(f"wrote {out_path.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
