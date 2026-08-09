"""Auditable log of every place canonical text was reconstructed from raw
library output rather than preserved verbatim (PROMPT section 15: "log de
transformacao auditavel quando o texto canonico diverge do texto bruto da
biblioteca").

Each entry says *what* changed and *why* (which mechanical/geometric
evidence justified it), tagged with a ``type`` so different kinds of
transformation stay distinguishable - only ``glyph_spacing_reconstruction``
(see spacing.py) is produced in this phase; dehyphenation/column-reordering
would be naturally distinct future types, never folded into this one.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class TransformationLogEntry:
    question: str
    type: str
    source_page: int
    method: str
    automatic: bool
    #: Human-readable specifics (e.g. "'ati'+'ngissem' -> 'atingissem'
    #: (gap=0.05pt, p.3)") - not required by PROMPT section 15's minimal
    #: example schema, but kept because the section also requires being
    #: "able to explain the transformation's origin", and a reviewer cannot
    #: do that from the tag alone.
    detail: str


def write_transformation_log_json(entries: list[TransformationLogEntry], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered = sorted(entries, key=lambda e: (e.question, e.source_page, e.detail))
    payload = [asdict(e) for e in ordered]
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
