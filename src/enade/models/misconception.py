"""Contract for diagnosing conceptual errors from wrong alternatives.

Two levels are modeled:

- :class:`MisconceptionDefinition` - a small, reusable catalog entry (future
  home: data/taxonomy/misconceptions.yaml). Not populated for the whole
  corpus in Phase 0.
- :class:`AlternativeDiagnostic` - the link from one wrong alternative letter
  on one question to a misconception + the concepts it implicates. This is
  what a Question's ``alternative_diagnostics`` field is keyed by letter.

Future pipeline this unlocks: wrong answer -> misconception -> concept ->
prerequisite -> study material -> a new practice question.
"""

from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


class MisconceptionDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="e.g. 'assumes-tree-is-balanced'")
    title: str
    description: str
    related_concepts: list[str] = Field(default_factory=list)
    status: str = Field(default="draft", description="'draft' or 'reviewed'")

    @field_validator("id")
    @classmethod
    def _validate_id(cls, v: str) -> str:
        if not SLUG_PATTERN.match(v):
            raise ValueError(f"misconception id {v!r} must be lowercase kebab-case")
        return v

    @field_validator("status")
    @classmethod
    def _validate_status(cls, v: str) -> str:
        allowed = {"draft", "reviewed"}
        if v not in allowed:
            raise ValueError(f"status must be one of {sorted(allowed)}, got {v!r}")
        return v


class AlternativeDiagnostic(BaseModel):
    """Diagnosis attached to a single wrong alternative of a question."""

    model_config = ConfigDict(extra="forbid")

    misconception_id: str
    concepts: list[str] = Field(default_factory=list)
    explanation: str | None = None

    @field_validator("misconception_id")
    @classmethod
    def _validate_misconception_id(cls, v: str) -> str:
        if not SLUG_PATTERN.match(v):
            raise ValueError(f"misconception_id {v!r} must be lowercase kebab-case")
        return v
