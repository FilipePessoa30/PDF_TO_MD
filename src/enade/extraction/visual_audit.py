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
