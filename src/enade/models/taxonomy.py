"""Hierarchical taxonomy contract: subject -> topic -> concept.

A concept carries its own keywords, aliases and prerequisite concept ids,
so we can distinguish e.g. "Arvores" (topic) from "Arvores Binarias" and
"Arvores Balanceadas" (concepts), rather than relying on flat free-text
keywords alone (see PROMPT section 13).

IMPORTANT: any :class:`Taxonomy` instance built in this phase is a small
demonstration fixture used to validate the schema shape. It is explicitly
*not* the scientific/definitive Computing taxonomy - see
``status`` and docs/taxonomy.md.
"""

from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from enade.models.enums import TaxonomyStatus

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def _validate_slug(v: str, kind: str) -> str:
    if not SLUG_PATTERN.match(v):
        raise ValueError(f"{kind} id {v!r} must be lowercase kebab-case")
    return v


class Concept(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    aliases: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    prerequisites: list[str] = Field(default_factory=list, description="ids of other concepts")

    @field_validator("id")
    @classmethod
    def _id_slug(cls, v: str) -> str:
        return _validate_slug(v, "concept")


class Topic(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    concepts: list[Concept] = Field(default_factory=list)

    @field_validator("id")
    @classmethod
    def _id_slug(cls, v: str) -> str:
        return _validate_slug(v, "topic")


class Subject(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    topics: list[Topic] = Field(default_factory=list)

    @field_validator("id")
    @classmethod
    def _id_slug(cls, v: str) -> str:
        return _validate_slug(v, "subject")


class Taxonomy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str
    status: TaxonomyStatus
    notice: str = Field(
        ...,
        min_length=1,
        description="Human-readable disclaimer about the maturity/completeness of this taxonomy.",
    )
    subjects: list[Subject] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_ids_unique_and_prerequisites_resolve(self) -> Taxonomy:
        all_ids: set[str] = set()
        concept_ids: set[str] = set()
        duplicates: set[str] = set()

        def register(node_id: str) -> None:
            if node_id in all_ids:
                duplicates.add(node_id)
            all_ids.add(node_id)

        for subject in self.subjects:
            register(subject.id)
            for topic in subject.topics:
                register(topic.id)
                for concept in topic.concepts:
                    register(concept.id)
                    concept_ids.add(concept.id)

        if duplicates:
            raise ValueError(f"duplicate taxonomy ids: {sorted(duplicates)}")

        unresolved: list[str] = []
        for subject in self.subjects:
            for topic in subject.topics:
                for concept in topic.concepts:
                    for prereq in concept.prerequisites:
                        if prereq == concept.id:
                            unresolved.append(f"{concept.id} -> {prereq} (self-reference)")
                        elif prereq not in concept_ids:
                            unresolved.append(f"{concept.id} -> {prereq}")
        if unresolved:
            raise ValueError(f"unresolved concept prerequisites: {unresolved}")

        return self
