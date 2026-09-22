"""Load/save helpers for the semantic layer's own JSON/YAML artifacts
(PROMPT Fase 5A section 25) - shared by the CLI commands and tests so
the on-disk shape (``schema_version``/``taxonomy_version``/
``shared_question_groups``/``annotations``) is defined in exactly one
place.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from enade.models.taxonomy import Taxonomy
from enade.semantic.annotation import QuestionAnnotation


def load_taxonomy(path: Path) -> Taxonomy:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return Taxonomy.model_validate(data)


def load_annotations(path: Path) -> tuple[list[QuestionAnnotation], list[list[str]]]:
    """Returns ``(annotations, shared_question_groups)``.

    ``shared_question_groups`` is a list of question-id groups that were
    manually confirmed (by reading the real, published statement text) to
    be verbatim-identical across two or more course booklets (PROMPT Fase
    5A section 10) - never inferred structurally, since the corpus's own
    "shared" signal (the ``ALL_COMPUTING`` course alias) cannot detect a
    duplication across two already-split 2021 booklets.
    """
    payload = json.loads(path.read_text(encoding="utf-8"))
    annotations = [QuestionAnnotation(**entry) for entry in payload["annotations"]]
    groups = [list(group) for group in payload.get("shared_question_groups", [])]
    return annotations, groups


def canonical_of_from_groups(groups: list[list[str]]) -> dict[str, str]:
    """Expands each shared-question group into a ``member -> canonical_id``
    map (the canonical id is the group's own lexicographically-first
    member - stable and deterministic, never a synthetic counter that
    would shift if a group's membership changes).
    """
    canonical_of: dict[str, str] = {}
    for group in groups:
        canonical_id = min(group)
        for member in group:
            canonical_of[member] = canonical_id
    return canonical_of
