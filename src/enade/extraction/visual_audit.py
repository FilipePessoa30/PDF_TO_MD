"""Load the human visual-audit record (PROMPT section 7/12) as a lookup the
pipeline can apply per question.

This file is *never written by the pipeline*. It is authored by whoever
performs the actual visual comparison against the rendered PDF - one entry
per question, each with a real justification (``notes``) - and the pipeline
only ever reads already-present entries and applies them; it never invents,
bulk-fills, or infers a status for a question missing from the file
(PROMPT section 14: no mass status promotion). A question absent from this
file simply stays ``visual_validation=not_performed``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from enade.models.enums import VisualValidationStatus

_STATUS_BY_VALUE = {status.value: status for status in VisualValidationStatus}


def load_visual_audit(path: Path) -> dict[str, VisualValidationStatus]:
    """Read ``path`` (a JSON object of ``{question_id: {"status": ..., "notes": ...}}``).

    Returns an empty mapping - never an error - if the file does not exist,
    so running the pipeline before any visual audit has happened is not a
    hard requirement; every question then correctly stays not-performed.
    """
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    result: dict[str, VisualValidationStatus] = {}
    for question_id, entry in raw.items():
        status_value = entry["status"] if isinstance(entry, dict) else entry
        result[question_id] = _STATUS_BY_VALUE[status_value]
    return result


def load_table_cell_verified_question_ids(path: Path) -> frozenset[str]:
    """Read the same visual-audit file's optional ``"tables_verified": true`` flag.

    A ``TableBlock`` (see models/content_block.py) starts life as
    ``needs_review`` no matter how clean its geometric reconstruction looks
    - promoting it to ``verified`` requires the *same* kind of disclosed,
    evidence-based human/reviewer visual comparison as ``visual_validation``
    (PROMPT Phase 1C section 5.4/16), just scoped to "was every cell
    actually checked against the rendered page", not merely "does the
    question overall look right". Reusing the visual-audit file (rather
    than inventing a parallel manifest) keeps one place per question for
    "what was actually inspected, and when" - see docs/decisions.md,
    "Phase 1C" ADR.
    """
    if not path.exists():
        return frozenset()
    raw = json.loads(path.read_text(encoding="utf-8"))
    return frozenset(
        question_id
        for question_id, entry in raw.items()
        if isinstance(entry, dict) and entry.get("tables_verified") is True
    )


@dataclass(frozen=True)
class VisualAuditCoverage:
    """How completely a visual-audit file covers a corpus's canonical question ids.

    PROMPT Phase 2B section 3: a "not_performed count" alone is not a
    trustworthy signal by itself - it must reconcile exactly against the
    canonical id set (``set(audited_ids) | not_performed == canonical_ids``,
    with no unexpected or duplicate entries) before any coverage claim
    (e.g. "55/55 audited") can be trusted machine-readably rather than by
    hand-counted prose.
    """

    canonical_ids: frozenset[str]
    audited_ids: frozenset[str]
    unexpected_ids: frozenset[str]
    duplicate_ids: frozenset[str]
    passed_count: int
    failed_count: int
    not_performed_count: int

    @property
    def total(self) -> int:
        return self.passed_count + self.failed_count + self.not_performed_count

    @property
    def fully_covered(self) -> bool:
        """True only when every canonical id has an explicit passed/failed
        entry (no ``not_performed``), with no unexpected or duplicate ids -
        the precondition for ever claiming a complete visual audit."""
        return self.not_performed_count == 0 and not self.unexpected_ids and not self.duplicate_ids


def assess_visual_audit_coverage(path: Path, canonical_ids: frozenset[str]) -> VisualAuditCoverage:
    """Reconcile a visual-audit file against the corpus's own canonical id set.

    Never raises on a malformed or missing file in the ways that matter for
    a coverage claim - a missing file simply means every canonical id is
    ``not_performed``, and a duplicate JSON key (last-value-wins under
    ordinary ``json.loads``, so silently invisible otherwise) is instead
    surfaced as a ``duplicate_ids`` entry.
    """
    duplicate_ids: set[str] = set()

    def _track_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
        seen: set[str] = set()
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in seen:
                duplicate_ids.add(key)
            seen.add(key)
            result[key] = value
        return result

    raw: dict[str, object] = {}
    if path.exists():
        raw = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_track_duplicates)

    audited_ids = frozenset(raw.keys())
    unexpected_ids = audited_ids - canonical_ids

    passed_count = 0
    failed_count = 0
    for question_id, entry in raw.items():
        if question_id not in canonical_ids:
            continue
        status_value = entry["status"] if isinstance(entry, dict) else entry
        if status_value == VisualValidationStatus.PASSED.value:
            passed_count += 1
        elif status_value == VisualValidationStatus.FAILED.value:
            failed_count += 1

    not_performed_count = len(canonical_ids - audited_ids)

    return VisualAuditCoverage(
        canonical_ids=canonical_ids,
        audited_ids=audited_ids,
        unexpected_ids=unexpected_ids,
        duplicate_ids=frozenset(duplicate_ids),
        passed_count=passed_count,
        failed_count=failed_count,
        not_performed_count=not_performed_count,
    )
