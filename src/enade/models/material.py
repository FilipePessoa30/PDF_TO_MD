"""Contract for future study materials recommended after diagnosing errors.

No real material URLs are invented in Phase 0 - this module only defines
the shape future material catalog entries must have.
"""

from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

from enade.models.enums import MaterialType, VerificationStatus

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


class Material(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    type: MaterialType
    url: str | None = None
    language: str = "pt-BR"
    subjects: list[str] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    concepts: list[str] = Field(default_factory=list)
    prerequisites: list[str] = Field(default_factory=list)
    source: str | None = None
    verification_status: VerificationStatus = VerificationStatus.PENDING

    @field_validator("id")
    @classmethod
    def _id_slug(cls, v: str) -> str:
        if not SLUG_PATTERN.match(v):
            raise ValueError(f"material id {v!r} must be lowercase kebab-case")
        return v
