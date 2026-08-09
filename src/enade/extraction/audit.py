"""Machine-readable per-question audit report (PROMPT section 24).

Generated automatically from the actually-extracted data - never hand
edited, never a source of truth (the Question records / Markdown files
are). CSV and JSON are both written so the report is usable either as a
spreadsheet or by other tooling.
"""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from enade.models.question import Question


@dataclass(frozen=True)
class AuditRow:
    id: str
    exam_year: int
    kind: str
    number: int
    section: str
    start_page: int
    end_page: int
    num_alternatives: int
    has_assets: bool
    num_assets: int
    answer: str
    answer_validation_status: str
    answer_standard_available: bool
    extraction_method: str
    extraction_status: str
    warning_count: int
    warnings: str


def build_audit_row(question: Question, warnings: list[str]) -> AuditRow:
    occurrence = question.source_occurrences[0]
    return AuditRow(
        id=question.id,
        exam_year=question.exam_year,
        kind=question.question_type.value,
        number=question.question_number,
        section=question.section,
        start_page=min(occurrence.pages),
        end_page=max(occurrence.pages),
        num_alternatives=len(question.alternatives),
        has_assets=bool(question.assets),
        num_assets=len(question.assets),
        answer=question.correct_answer or "",
        answer_validation_status=question.answer_validation_status.value,
        answer_standard_available=question.answer_standard is not None,
        extraction_method=question.extraction_method.value,
        extraction_status=question.extraction_status.value,
        warning_count=len(warnings),
        warnings="; ".join(warnings),
    )


def write_audit_csv(rows: list[AuditRow], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(asdict(rows[0]).keys()) if rows else []
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in sorted(rows, key=lambda r: (r.kind, r.number)):
            writer.writerow(asdict(row))


def write_audit_json(rows: list[AuditRow], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = [asdict(row) for row in sorted(rows, key=lambda r: (r.kind, r.number))]
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False, sort_keys=False) + "\n", encoding="utf-8"
    )
