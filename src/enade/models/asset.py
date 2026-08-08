"""Contract for visual assets (images, diagrams, tables, equations, ...).

Rule this contract exists to support (see docs/data-contract.md): a question
that visually depends on the PDF may not be considered ``verified`` unless
the element needed to answer it has been preserved as an Asset.
"""

from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

from enade.models.enums import AssetExtractionMethod, AssetType

ASSET_ID_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SHA256_PATTERN = r"^[0-9a-f]{64}$"


class Asset(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="slug unique within the owning question, e.g. 'figure-01'")
    type: AssetType
    path: str = Field(..., description="portable, relative path under data/assets/questions/")
    source_page: int = Field(..., ge=1)
    extraction_method: AssetExtractionMethod = AssetExtractionMethod.PENDING
    sha256: str | None = Field(default=None, pattern=SHA256_PATTERN)
    alt_text: str | None = None
    caption: str | None = None

    @field_validator("id")
    @classmethod
    def _validate_id(cls, v: str) -> str:
        if not ASSET_ID_PATTERN.match(v):
            raise ValueError(f"asset id {v!r} must be lowercase kebab-case")
        return v

    @field_validator("path")
    @classmethod
    def _validate_path(cls, v: str) -> str:
        normalized = v.replace("\\", "/")
        if normalized.startswith("/") or ".." in normalized.split("/"):
            raise ValueError(
                f"asset path {v!r} must be a relative, portable path (no '..' or leading '/')"
            )
        return normalized
