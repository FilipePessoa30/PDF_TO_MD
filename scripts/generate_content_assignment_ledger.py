#!/usr/bin/env python3
"""Generate data/manifests/content-assignment-2008-b.json (PROMPT Phase 3J).

Re-runs the real extraction pipeline for 2008-b with a light, read-only
instrumentation hook on ``assembler.assemble_question`` (the same
technique used by every diagnostic script this project's own phases have
written - see docs/phase-3i-report.md section P) to capture each
question's own ``content_lines``/alternative boundaries/value annotations/
figure regions *before* they are merged into paragraph-level segments,
where individual line identity would otherwise be lost.

Deterministic by construction: every ``source_element_id`` is derived from
real, stable PDF geometry (``page:x0:y0``, rounded), never from a Python
object id or a list position - two independent runs produce byte-identical
output (see docs/phase-3j-report.md section X, "Reprodutibilidade").

Coverage is genuinely broad (every published 2008-b question's own lines
and figure regions), but the *kinds* of source element recorded are only
the ones this phase's own fix actually needed (``line``, ``asset``) - see
content_assignment.py's own module docstring for why the rest of the
schema's declared source types are not fabricated here.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from enade.cli import DEFAULT_AUDIT_DIR, _resolve_booklet_location
from enade.extraction import assembler as assembler_mod
from enade.extraction import pipeline as pipeline_mod
from enade.extraction.alternative_groups import find_alternative_group
from enade.extraction.annotations import reattach_value_annotations
from enade.extraction.answer_key import parse_answer_key, parse_flat_item_gabarito
from enade.extraction.chrome import is_chrome_line
from enade.extraction.content_assignment import ContentAssignment
from enade.extraction.layout_overrides import load_layout_overrides
from enade.extraction.pipeline import extract_exam
from enade.extraction.visual_audit import load_table_cell_verified_question_ids, load_visual_audit

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CORPUS_ROOT = PROJECT_ROOT / "data" / "raw" / "geacc-enade"
OUTPUT_PATH = PROJECT_ROOT / "data" / "manifests" / "content-assignment-2008-b.json"
YEAR = 2008
COURSE = "all-computing"

_orig_assemble_question = assembler_mod.assemble_question
_records: list[ContentAssignment] = []


def _line_id(question_id: str, page: int, x0: float, y0: float) -> str:
    return f"{question_id}:line:p{page}:{round(x0, 1)}:{round(y0, 1)}"


def _record_question(span, doc, decorative_baseline, **kwargs):
    extracted = _orig_assemble_question(span, doc, decorative_baseline, **kwargs)
    suffix = "q" if span.kind.value == "objective" else "d"
    question_id = f"enade-2008-computing-{suffix}{span.number:02d}"

    coarse_lines = [ln for ln in span.lines if not is_chrome_line(ln.text)]
    content_lines, value_annotations = reattach_value_annotations(coarse_lines)

    annotated_texts = {a.text for a in value_annotations}

    if span.kind.value == "objective":
        group = find_alternative_group(content_lines)
        if group is not None and group.is_usable:
            letters = ["A", "B", "C", "D", "E"]
            bounds = [group.accepted[letter] for letter in letters] + [len(content_lines)]
            cutoff = bounds[0]
            for i, ln in enumerate(content_lines):
                bbox = (ln.x0, ln.y0, ln.x1, ln.y1)
                if i < cutoff:
                    destination, owner, anchor = "statement", "question", "statement"
                else:
                    letter = next(letters[k] for k in range(5) if bounds[k] <= i < bounds[k + 1])
                    destination, owner, anchor = "alternative_text", "alternative", letter
                _records.append(
                    ContentAssignment(
                        assignment_id=f"{question_id}:{i}",
                        source_element_id=_line_id(question_id, ln.page_number, ln.x0, ln.y0),
                        source_type="line",
                        source_page=ln.page_number,
                        source_bbox=bbox,
                        canonical_owner=owner,
                        anchor=anchor,
                        publication_destination=destination,
                        representation=ln.text,
                        reason="reading-order index before/after the A-E cutoff"
                        if ln.text not in annotated_texts
                        else "value annotation reattached by geometric containment",
                        evidence="alternative_groups.find_alternative_group + assembler._reading_order_index",
                        confidence=1.0,
                        status="assigned",
                        question_id=question_id,
                    )
                )
        else:
            for ln in content_lines:
                _records.append(
                    ContentAssignment(
                        assignment_id=_line_id(question_id, ln.page_number, ln.x0, ln.y0),
                        source_element_id=_line_id(question_id, ln.page_number, ln.x0, ln.y0),
                        source_type="line",
                        source_page=ln.page_number,
                        source_bbox=(ln.x0, ln.y0, ln.x1, ln.y1),
                        canonical_owner="question",
                        anchor="statement",
                        publication_destination="statement",
                        representation=ln.text,
                        reason="no resolved alternative group - whole span treated as statement",
                        evidence="alternative_groups.find_alternative_group",
                        confidence=0.5 if group is not None else 1.0,
                        status="assigned",
                        question_id=question_id,
                    )
                )
    else:
        for ln in content_lines:
            is_annotation = ln.text in annotated_texts
            _records.append(
                ContentAssignment(
                    assignment_id=f"{question_id}:p{ln.page_number}:{round(ln.y0, 1)}",
                    source_element_id=_line_id(question_id, ln.page_number, ln.x0, ln.y0),
                    source_type="annotation" if is_annotation else "line",
                    source_page=ln.page_number,
                    source_bbox=(ln.x0, ln.y0, ln.x1, ln.y1),
                    canonical_owner="question",
                    anchor="statement",
                    publication_destination="annotation" if is_annotation else "statement",
                    representation=ln.text,
                    reason="discursive item text"
                    if not is_annotation
                    else "value annotation reattached by geometric containment against item start positions",
                    evidence="annotations.reattach_value_annotations",
                    confidence=1.0,
                    status="assigned",
                    question_id=question_id,
                )
            )

    for region_index, region in enumerate(extracted.figure_regions):
        x0, y0, x1, y1 = region.bbox
        _records.append(
            ContentAssignment(
                assignment_id=f"{question_id}:asset:{region_index}",
                source_element_id=f"{question_id}:asset:p{region.page_number}:{round(x0, 1)}:{round(y0, 1)}",
                source_type="asset",
                source_page=region.page_number,
                source_bbox=(x0, y0, x1, y1),
                canonical_owner="question",
                anchor="question_asset",
                publication_destination="question_asset",
                representation=f"figure-{region_index + 1:02d}.png",
                reason="owner_exclusion_gate-consistent figure region already attached by assemble_question",
                evidence="figures.detect_visual_regions",
                confidence=1.0,
                status="assigned",
                question_id=question_id,
            )
        )

    return extracted


def main() -> None:
    assembler_mod.assemble_question = _record_question
    pipeline_mod.assemble_question = _record_question

    # Reuse the CLI's own booklet-location/answer-key/visual-audit/layout-
    # override resolution verbatim (rather than re-deriving it here) - an
    # earlier version of this script hand-built these parameters and
    # silently regenerated the *real* corpus with the wrong gabarito
    # parser and no visual-audit file loaded (every one of the 77
    # published questions came back with correct_answer=null and
    # visual_validation=not_performed), caught only by a routine
    # `git status` check and reverted before being reported anywhere.
    # Writing to a throwaway temp directory below is the second,
    # independent safeguard against that ever reaching the real corpus
    # again.
    loc = _resolve_booklet_location(YEAR, COURSE, CORPUS_ROOT)
    visual_audit_path = DEFAULT_AUDIT_DIR / f"visual-audit-{YEAR}-{loc.file_slug}.json"
    visual_audit = load_visual_audit(visual_audit_path)
    table_cells_verified_ids = load_table_cell_verified_question_ids(visual_audit_path)
    layout_overrides = load_layout_overrides(DEFAULT_AUDIT_DIR / "layout-overrides.yaml")

    with tempfile.TemporaryDirectory(prefix="content_assignment_ledger_") as tmp_dir:
        extract_exam(
            prova_path=loc.prova_path,
            gabarito_path=loc.gabarito_path,
            padrao_path=loc.padrao_path,
            corpus_root=CORPUS_ROOT,
            exam_year=YEAR,
            course=None if loc.is_unified else loc.course_code,
            exam_id=loc.exam_id,
            questions_output_dir=Path(tmp_dir),
            visual_audit=visual_audit,
            table_cells_verified_ids=table_cells_verified_ids,
            structure_profile=loc.structure_profile,
            output_dir_name=loc.course_code.value if loc.is_unified else None,
            answer_key_parser=parse_flat_item_gabarito if loc.is_unified else parse_answer_key,
            layout_overrides=layout_overrides,
        )

    payload = {
        "schema_version": 1,
        "generated_by": "PROMPT Phase 3J - scripts/generate_content_assignment_ledger.py",
        "assignment_count": len(_records),
        "assignments": [
            {
                "assignment_id": r.assignment_id,
                "source_element_id": r.source_element_id,
                "source_type": r.source_type,
                "source_page": r.source_page,
                "source_bbox": list(r.source_bbox),
                "canonical_owner": r.canonical_owner,
                "anchor": r.anchor,
                "publication_destination": r.publication_destination,
                "representation": r.representation,
                "reason": r.reason,
                "evidence": r.evidence,
                "confidence": r.confidence,
                "status": r.status,
                "question_id": r.question_id,
            }
            for r in sorted(_records, key=lambda r: r.assignment_id)
        ],
    }
    OUTPUT_PATH.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Wrote {len(_records)} assignment record(s) to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
