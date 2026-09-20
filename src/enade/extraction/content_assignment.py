"""The content-assignment ledger: one record per source element explaining
where it came from, who owns it, what it is anchored to, and where it was
published - PROMPT Phase 3J ("atribuição canônica de conteúdo").

This module is deliberately scoped to what this phase actually needed to
diagnose and fix (2008-b Q13 and D60) plus what the Section 20 scan of the
77 published questions could evidence, not a full, generic re-implementation
of every source/owner/destination combination the prompt enumerates as
*possible*. Building the untested remainder now would be exactly the kind
of speculative generality docs/generalization-contract.md (section 1.1)
warns against - the schema (``ContentAssignment``, ``SourceType``,
``Owner``, ``Destination``) declares every value the prompt names so nothing
needs to change shape later, but only the source types this corpus's own
pipeline already tracks with a stable identity (``line`` and ``asset``) are
ever actually produced.

Three principles this module follows (Sections 6-9 of the Phase 3J prompt):

1. Owner, anchor and destination are three separate fields, never
   collapsed into one. A line can be geometrically anchored to a figure
   (its own bbox sits right next to it) while its true owner is the
   question's own statement, not the figure - proximity is evidence for
   *anchor*, never a substitute for demonstrating *owner*.
2. Duplication is demonstrated by shared provenance (the same
   ``source_element_id``, i.e. the same underlying ``Line``/asset,
   appearing in two ``ContentAssignment`` records with different
   ``publication_destination``), never by text equality - two distinct
   alternatives may legitimately share identical wording.
3. Every gate here can only ever *report*, never silently repair -
   deciding which of two destinations is documentally correct is a
   judgment call for the general mechanism that produced the assignment in
   the first place (``assembler.py``/``annotations.py``), not for a gate
   that only sees the ledger after the fact.
"""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    import pymupdf

    from enade.extraction.answer_key import AnswerKeyParseResult
    from enade.extraction.exam_profile import ExamStructureProfile
    from enade.extraction.layout import Line
    from enade.extraction.layout_overrides import LayoutOverrideSet
    from enade.models.enums import CourseCode, VisualValidationStatus

#: Only "line" and "asset" are ever produced by this phase's own ledger
#: generation (assembler.py's own content_lines/figure_regions are the
#: only source elements with a stable per-run identity today). The rest
#: are declared for the schema's own extensibility (PROMPT section 6).
SourceType = Literal[
    "char",
    "span",
    "line",
    "fragment",
    "visual_region",
    "asset",
    "annotation",
    "caption",
    "alternative_marker",
]

Owner = Literal[
    "question",
    "alternative",
    "asset",
    "diagram",
    "answer_area",
    "document_chrome",
    "unresolved",
]

Destination = Literal[
    "statement",
    "alternative_text",
    "alternative_asset",
    "question_asset",
    "caption",
    "annotation",
    "answer_standard",
    "discarded_chrome",
    "blocked",
]


@dataclass(frozen=True)
class ContentAssignment:
    """One source element's own resolved (or still-unresolved) assignment."""

    assignment_id: str
    source_element_id: str
    source_type: SourceType
    source_page: int
    source_bbox: tuple[float, float, float, float]
    canonical_owner: Owner
    anchor: str
    publication_destination: Destination
    representation: str
    reason: str
    evidence: str
    confidence: float
    status: Literal["assigned", "blocked", "ambiguous"]
    #: The published question this assignment belongs to, e.g.
    #: "enade-2008-computing-q13" - not part of the prompt's own listed
    #: schema fields, but required to group records per question for the
    #: gates below and for a human reading the manifest.
    question_id: str = ""
    #: PROMPT section 8: a second representation of the *same*
    #: ``source_element_id`` (e.g. a canonical text plus its own visible
    #: copy baked into an asset's own image) is a duplicate only when
    #: undocumented. Every record sharing one source that also shares one
    #: non-``None`` ``duplication_mode`` is treated as an authorized
    #: mirror, not a defect - ``detect_duplicate_assignments`` never
    #: infers this itself; it only honors what the assignment already
    #: declares. ``None`` for every record this phase actually produced -
    #: no real, evidenced mirror case exists in this corpus yet (see
    #: content_assignment.py's own module docstring on not fabricating
    #: unevidenced capability).
    duplication_mode: str | None = None


@dataclass(frozen=True)
class DuplicateAssignmentFinding:
    source_element_id: str
    destinations: tuple[str, ...]
    owners: tuple[str, ...]
    question_ids: tuple[str, ...]
    alternative_labels: tuple[str, ...]
    reason: str


@dataclass(frozen=True)
class MissingAssignmentFinding:
    kind: Literal[
        "source_without_destination",
        "annotation_without_owner",
        "asset_without_owner",
        "content_block_without_source",
        "destination_without_source",
    ]
    source_element_id: str
    question_id: str
    reason: str


def detect_duplicate_assignments(
    assignments: list[ContentAssignment],
) -> list[DuplicateAssignmentFinding]:
    """PROMPT section 11: same source, more than one destination/owner/
    alternative - never resolved here, only reported.

    Grouped by ``source_element_id`` alone (never by text), per the
    module's own second principle above.
    """
    by_source: dict[str, list[ContentAssignment]] = defaultdict(list)
    for a in assignments:
        by_source[a.source_element_id].append(a)

    findings: list[DuplicateAssignmentFinding] = []
    for source_id, group in by_source.items():
        destinations = {a.publication_destination for a in group}
        owners = {a.canonical_owner for a in group}
        alt_labels = {a.anchor for a in group if a.canonical_owner == "alternative"}
        if len(destinations) <= 1 and len(owners) <= 1 and len(alt_labels) <= 1:
            continue
        modes = {a.duplication_mode for a in group}
        if len(modes) == 1 and None not in modes:
            continue  # every record agrees on one authorized mirror mode
        findings.append(
            DuplicateAssignmentFinding(
                source_element_id=source_id,
                destinations=tuple(sorted(destinations)),
                owners=tuple(sorted(owners)),
                question_ids=tuple(sorted({a.question_id for a in group})),
                alternative_labels=tuple(sorted(alt_labels)),
                reason=(
                    f"source {source_id!r} published to {len(destinations)} distinct "
                    f"destination(s) / {len(owners)} distinct owner(s)"
                ),
            )
        )
    return findings


def detect_missing_assignments(
    assignments: list[ContentAssignment],
) -> list[MissingAssignmentFinding]:
    """PROMPT section 12: a legitimate element with no destination, or a
    destination that no longer traces back to any real source - the
    complementary check to duplication (a naive fix for the latter can
    silently turn into the former, see the module's own third principle).
    """
    findings: list[MissingAssignmentFinding] = []
    for a in assignments:
        if a.status == "blocked" and a.publication_destination != "blocked":
            findings.append(
                MissingAssignmentFinding(
                    kind="source_without_destination",
                    source_element_id=a.source_element_id,
                    question_id=a.question_id,
                    reason=a.reason,
                )
            )
        elif a.source_type == "annotation" and a.canonical_owner == "unresolved":
            findings.append(
                MissingAssignmentFinding(
                    kind="annotation_without_owner",
                    source_element_id=a.source_element_id,
                    question_id=a.question_id,
                    reason=a.reason,
                )
            )
        elif a.source_type == "asset" and a.canonical_owner == "unresolved":
            findings.append(
                MissingAssignmentFinding(
                    kind="asset_without_owner",
                    source_element_id=a.source_element_id,
                    question_id=a.question_id,
                    reason=a.reason,
                )
            )
    return findings


# --- Generation (PROMPT Fase 3J, restored and generalized in Fase 4B) -----
#
# Moved here from the former scripts/generate_content_assignment_ledger.py
# (a corpus-hardcoded, one-off script) so this ledger has a single,
# reusable, general home - the same tier-1 preference ("função geral
# reutilizável no módulo existente") this project already applies to every
# other declarative mechanism. ``enade generate-content-assignment`` (cli.py)
# is now the only supported entry point; the old script is retired.


def _naive_alternative_text(text_only_lines: list, alt_bounds: list[int], index: int) -> str:
    """Reconstructs one alternative's own text using *only* a naive,
    index-bounded slice of ``text_only_lines`` between two marker
    positions - deliberately the same shape as the pre-Phase-2E per-letter
    loop this ledger's own generation has always approximated with. Never
    the source of truth for what was actually published - see
    ``generate_content_assignment_ledger``'s own docstring for why this is
    compared against, never substituted for, ``ExtractedAlternative.text``.
    """
    marker_re = re.compile(r"^([A-E])(?:[\t ](.*))?$")
    lines = text_only_lines[alt_bounds[index] : alt_bounds[index + 1]]
    if not lines:
        return ""
    match = marker_re.match(lines[0].text)
    first_text = (match.group(2) or "").strip() if match else lines[0].text.strip()
    rest_text = " ".join(ln.text.strip() for ln in lines[1:])
    return f"{first_text} {rest_text}".strip() if rest_text else first_text


def generate_content_assignment_ledger(
    *,
    prova_path: Path,
    gabarito_path: Path,
    padrao_path: Path,
    corpus_root: Path,
    exam_year: int,
    exam_id: str,
    questions_output_dir: Path,
    course: CourseCode | None = None,
    structure_profile: ExamStructureProfile | None = None,
    structure_verification_page: int = 1,
    structure_verification_patterns: dict | None = None,
    output_dir_name: str | None = None,
    answer_key_parser: Callable[[pymupdf.Document], AnswerKeyParseResult] | None = None,
    layout_overrides: LayoutOverrideSet | None = None,
    visual_audit: dict[str, VisualValidationStatus] | None = None,
    table_cells_verified_ids: frozenset[str] | None = None,
) -> dict:
    """Re-run the real extraction pipeline for one booklet with a light,
    read-only instrumentation hook on ``assembler.assemble_question`` (the
    same technique this project's own diagnostic scripts have always
    used - see docs/phase-3i-report.md section P), capturing each
    question's own lines/figure regions *before* they are merged into
    paragraph-level segments, where individual line identity would
    otherwise be lost. Writes nothing - the caller decides where (if
    anywhere) the returned payload is persisted, so a ``--check`` run can
    build the exact same candidate a ``--write`` run would without ever
    touching the real manifest.

    Deterministic by construction: every ``source_element_id`` is derived
    from real, stable PDF geometry (``page:x0:y0``, rounded), never from a
    Python object id or a list position - two independent calls produce
    byte-identical output.

    PROMPT Fase 4B's own generalization over the original Fase 3J script:
    the per-letter alternative attribution below is a *naive*, index-
    bounded approximation (every line between one marker and the next
    belongs to that marker's own letter) - correct for a simple,
    vertically-stacked alternative list, but silently wrong wherever a
    specialized mechanism governs a question's own alternatives (a
    declared raster-photograph group, a declared vector formula, or the
    reflow-to-statement rule) - each of those excludes/reassigns lines
    relative to naive index order. Rather than reimplementing any of
    those mechanisms a second time here (a real risk of drifting out of
    sync with the assembler's own logic again), this function compares
    the naive reconstruction against ``ExtractedAlternative.text`` - the
    assembler's own actual, final, published value, already correctly
    computed by whichever mechanism applies - and marks every line
    assignment for a letter where the two disagree as ``status="ambiguous"``,
    ``canonical_owner="unresolved"``, with a reason naming the divergence
    (never a question ID) - honest under-confidence, never a silently
    wrong owner. This generalizes to any future mechanism the assembler
    might gain, with no new branch needed here.
    """
    import tempfile

    from enade.extraction import assembler as assembler_mod
    from enade.extraction import pipeline as pipeline_mod
    from enade.extraction.alternative_groups import find_alternative_group
    from enade.extraction.annotations import reattach_value_annotations
    from enade.extraction.boundaries import _MARKER_RE as _QUESTION_MARKER_RE
    from enade.extraction.chrome import is_chrome_line
    from enade.extraction.pipeline import extract_exam
    from enade.extraction.to_question import COURSE_ID_SHORTHAND

    records: list[ContentAssignment] = []
    orig_assemble_question = assembler_mod.assemble_question

    if structure_profile is not None:
        shorthand = structure_profile.id_shorthand
    else:
        assert course is not None
        shorthand = COURSE_ID_SHORTHAND[course]

    def _line_id(question_id: str, page: int, x0: float, y0: float, x1: float, y1: float) -> str:
        # PROMPT Fase 4B, Section 8 - identity derived from the full,
        # stable source_bbox, never x0/y0 alone: two genuinely distinct
        # lines (found empirically on 2008-b Q24, page 12 - the raw
        # "II" item marker and a *separately* orphan-marker-merged "A\tII"
        # line reported by layout.extract_page_lines's own real output,
        # both anchored at the same x0/y0 by construction - min(x0) of a
        # merge always keeps whichever operand is smaller) would otherwise
        # collide onto one shared identity, hiding a real, distinct pair
        # of assignments behind a false "duplicate" finding.
        return f"{question_id}:line:p{page}:{round(x0, 1)}:{round(y0, 1)}:{round(x1, 1)}:{round(y1, 1)}"

    # Deliberately loosely typed (**kwargs) to forward whichever keyword
    # arguments assemble_question's own real signature currently declares,
    # without this hook needing to be updated every time that signature
    # grows - the same monkeypatch-instrumentation shape this project's own
    # diagnostic scripts have always used (docs/phase-3i-report.md section
    # P). Assigned onto assembler_mod/pipeline_mod below, which mypy can
    # only check structurally against the real callable's own signature -
    # never expressible without losing that forwarding generality.
    def _record_question(span, doc, decorative_baseline, **kwargs):  # type: ignore[no-untyped-def]
        extracted = orig_assemble_question(span, doc, decorative_baseline, **kwargs)
        suffix = "q" if span.kind.value == "objective" else "d"
        question_id = f"enade-{exam_year}-{shorthand}-{suffix}{span.number:02d}"

        coarse_lines = [ln for ln in span.lines if not is_chrome_line(ln.text)]
        content_lines, value_annotations = reattach_value_annotations(coarse_lines)
        annotated_texts = {a.text for a in value_annotations}
        # The final, authoritative statement text actually published (PROMPT
        # Fase 4B) - a line naively assumed to land in "statement" (every
        # line before the alternative cutoff, or every line of a
        # discursive) is only ever recorded as such if its own text
        # actually survives somewhere in this string. A line legitimately
        # excluded by a real, individually-verified mechanism (e.g.
        # force_region_membership - already visible in its own asset) is
        # never silently mislabeled "statement" here; it is marked
        # ambiguous/unresolved instead, generically, with no mechanism
        # named and no question ID involved.
        final_statement_text = " ".join(
            seg.text for seg in extracted.statement_segments if hasattr(seg, "text")
        )
        # A line legitimately reconstructed into a structured Markdown
        # table (TableSegment - tables.py's own DetectedTable) never
        # appears verbatim in final_statement_text (its own cell text is
        # reformatted into a table row) - checked by real line identity
        # (membership in the table's own consumed_lines), never by text
        # matching, since a cell's own text is exactly the kind of short,
        # generic string ("S0", "S1") a substring check could false-match
        # on anyway.
        tabled_lines: frozenset = frozenset().union(*(t.consumed_lines for t in extracted.tables))

        def _survives_in_statement(line: Line) -> bool:
            stripped = line.text.strip()
            if not stripped:
                return False
            if line in tabled_lines:
                return True
            # The "Questao N"/"Questao Discursiva N" marker line itself is
            # never part of statement_segments - it becomes the Markdown
            # heading ("# Questao N"), a different, always-legitimate
            # destination this generator does not otherwise model. Exempted
            # by the same marker pattern boundaries.py itself uses to
            # detect it (never a question-specific check).
            if _QUESTION_MARKER_RE.search(stripped):
                return True
            return stripped in final_statement_text

        if span.kind.value == "objective":
            group = find_alternative_group(content_lines)
            if group is not None and group.is_usable:
                letters = ["A", "B", "C", "D", "E"]
                bounds = [group.accepted[letter] for letter in letters] + [len(content_lines)]
                cutoff = bounds[0]
                final_text_by_letter = {alt.letter: alt.text for alt in extracted.alternatives}
                diverges_by_letter = {
                    letter: _naive_alternative_text(content_lines, bounds, k).strip()
                    != final_text_by_letter.get(letter, "").strip()
                    for k, letter in enumerate(letters)
                }
                for i, ln in enumerate(content_lines):
                    bbox = (ln.x0, ln.y0, ln.x1, ln.y1)
                    if i < cutoff:
                        if _survives_in_statement(ln):
                            destination, owner, anchor = "statement", "question", "statement"
                            status, confidence, extra_reason = "assigned", 1.0, ""
                        else:
                            destination, owner, anchor = "blocked", "unresolved", "statement"
                            status, confidence = "ambiguous", 0.0
                            extra_reason = (
                                " - line text not found in the assembler's own final published "
                                "statement text; a real, individually-verified exclusion "
                                "mechanism (never this generator) governs this line - see the "
                                "question's own asset(s) for where the content is actually shown"
                            )
                    else:
                        letter = next(
                            letters[k] for k in range(5) if bounds[k] <= i < bounds[k + 1]
                        )
                        anchor = letter
                        if diverges_by_letter[letter]:
                            destination, owner = "blocked", "unresolved"
                            status, confidence = "ambiguous", 0.0
                            extra_reason = (
                                " - naive per-line text does not match the assembler's own "
                                "final, published alternative text; a specialized attachment "
                                "mechanism governs this alternative's own content, and this "
                                "generator does not reconstruct line-level attribution for it "
                                "(see the question's own Markdown/assets for the authoritative "
                                "content)"
                            )
                        else:
                            destination, owner = "alternative_text", "alternative"
                            status, confidence, extra_reason = "assigned", 1.0, ""
                    records.append(
                        ContentAssignment(
                            assignment_id=f"{question_id}:{i}",
                            source_element_id=_line_id(
                                question_id, ln.page_number, ln.x0, ln.y0, ln.x1, ln.y1
                            ),
                            source_type="line",
                            source_page=ln.page_number,
                            source_bbox=bbox,
                            canonical_owner=owner,
                            anchor=anchor,
                            publication_destination=destination,
                            representation=ln.text,
                            reason=(
                                (
                                    "reading-order index before/after the A-E cutoff"
                                    if ln.text not in annotated_texts
                                    else "value annotation reattached by geometric containment"
                                )
                                + extra_reason
                            ),
                            evidence="alternative_groups.find_alternative_group + assembler._reading_order_index"
                            + (
                                " + ExtractedAlternative.text divergence check"
                                if i >= cutoff
                                else " + statement_segments survival check"
                            ),
                            confidence=confidence,
                            status=status,
                            question_id=question_id,
                        )
                    )
            else:
                for ln in content_lines:
                    survives = _survives_in_statement(ln)
                    records.append(
                        ContentAssignment(
                            assignment_id=_line_id(
                                question_id, ln.page_number, ln.x0, ln.y0, ln.x1, ln.y1
                            ),
                            source_element_id=_line_id(
                                question_id, ln.page_number, ln.x0, ln.y0, ln.x1, ln.y1
                            ),
                            source_type="line",
                            source_page=ln.page_number,
                            source_bbox=(ln.x0, ln.y0, ln.x1, ln.y1),
                            canonical_owner="question" if survives else "unresolved",
                            anchor="statement",
                            publication_destination="statement" if survives else "blocked",
                            representation=ln.text,
                            reason=(
                                "no resolved alternative group - whole span treated as statement"
                                if survives
                                else "no resolved alternative group, and line text not found in "
                                "the assembler's own final published statement text - a real "
                                "exclusion mechanism (never this generator) governs this line"
                            ),
                            evidence="alternative_groups.find_alternative_group"
                            + ("" if survives else " + statement_segments survival check"),
                            confidence=(0.5 if group is not None else 1.0) if survives else 0.0,
                            status="assigned" if survives else "ambiguous",
                            question_id=question_id,
                        )
                    )
        else:
            for ln in content_lines:
                is_annotation = ln.text in annotated_texts
                survives = is_annotation or _survives_in_statement(ln)
                records.append(
                    ContentAssignment(
                        # Two-column discursive layouts (a bullet/label glyph
                        # column and its own text column, e.g. D10's "-" bullets
                        # or D40's truth-table cells) legitimately place distinct
                        # lines at the same page/y0 - the same identity-collision
                        # class fixed for source_element_id (see _line_id), now
                        # fixed here too by including x0.
                        assignment_id=f"{question_id}:p{ln.page_number}:{round(ln.x0, 1)}:{round(ln.y0, 1)}",
                        source_element_id=_line_id(
                            question_id, ln.page_number, ln.x0, ln.y0, ln.x1, ln.y1
                        ),
                        source_type="annotation" if is_annotation else "line",
                        source_page=ln.page_number,
                        source_bbox=(ln.x0, ln.y0, ln.x1, ln.y1),
                        canonical_owner="question" if survives else "unresolved",
                        anchor="statement",
                        publication_destination=(
                            "annotation"
                            if is_annotation
                            else ("statement" if survives else "blocked")
                        ),
                        representation=ln.text,
                        reason=(
                            "discursive item text"
                            if not is_annotation
                            else "value annotation reattached by geometric containment against item start positions"
                        )
                        if survives
                        else "line text not found in the assembler's own final published "
                        "statement text - a real exclusion mechanism (never this generator) "
                        "governs this line",
                        evidence="annotations.reattach_value_annotations"
                        + ("" if survives else " + statement_segments survival check"),
                        confidence=1.0 if survives else 0.0,
                        status="assigned" if survives else "ambiguous",
                        question_id=question_id,
                    )
                )

        for region_index, region in enumerate(extracted.figure_regions):
            x0, y0, x1, y1 = region.bbox
            records.append(
                ContentAssignment(
                    assignment_id=f"{question_id}:asset:{region_index}",
                    source_element_id=(
                        f"{question_id}:asset:p{region.page_number}:{round(x0, 1)}:{round(y0, 1)}"
                    ),
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

    assembler_mod.assemble_question = _record_question  # type: ignore[assignment]
    pipeline_mod.assemble_question = _record_question  # type: ignore[assignment]
    try:
        with tempfile.TemporaryDirectory(prefix="content_assignment_ledger_") as tmp_dir:
            extract_exam(
                prova_path=prova_path,
                gabarito_path=gabarito_path,
                padrao_path=padrao_path,
                corpus_root=corpus_root,
                exam_year=exam_year,
                course=course,
                exam_id=exam_id,
                questions_output_dir=Path(tmp_dir),
                visual_audit=visual_audit,
                table_cells_verified_ids=table_cells_verified_ids,
                structure_profile=structure_profile,
                structure_verification_page=structure_verification_page,
                structure_verification_patterns=structure_verification_patterns,
                output_dir_name=output_dir_name,
                **(
                    {"answer_key_parser": answer_key_parser}
                    if answer_key_parser is not None
                    else {}
                ),
                layout_overrides=layout_overrides,
            )
    finally:
        assembler_mod.assemble_question = orig_assemble_question
        pipeline_mod.assemble_question = orig_assemble_question

    return {
        "schema_version": 1,
        "generated_by": "enade generate-content-assignment (PROMPT Fase 3J, generalized Fase 4B)",
        "assignment_count": len(records),
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
            for r in sorted(records, key=lambda r: r.assignment_id)
        ],
    }


@dataclass(frozen=True)
class AssetAssignmentIssue:
    kind: Literal[
        "asset_file_missing",
        "asset_hash_mismatch",
        "asset_not_referenced_in_markdown",
        "owner_question_not_published",
    ]
    question_id: str
    detail: str


def validate_ledger_against_corpus(
    payload: dict, published_questions_dir: Path
) -> list[AssetAssignmentIssue]:
    """PROMPT Fase 4B section 16 - cross-checks every ``asset``-type
    record against what is *actually* on disk right now: the question's
    own Markdown must exist and must reference the file, and the file
    itself must exist. Never repairs anything - only reports, same
    discipline as ``detect_duplicate_assignments``/``detect_missing_assignments``.
    """
    issues: list[AssetAssignmentIssue] = []
    md_cache: dict[str, str | None] = {}

    def _markdown_text(question_id: str) -> str | None:
        if question_id not in md_cache:
            md_path = published_questions_dir / f"{question_id}.md"
            md_cache[question_id] = (
                md_path.read_text(encoding="utf-8") if md_path.is_file() else None
            )
        return md_cache[question_id]

    for record in payload["assignments"]:
        if record["source_type"] != "asset":
            continue
        question_id = record["question_id"]
        md_text = _markdown_text(question_id)
        if md_text is None:
            issues.append(
                AssetAssignmentIssue(
                    kind="owner_question_not_published",
                    question_id=question_id,
                    detail=f"{record['assignment_id']}: no Markdown file for {question_id}",
                )
            )
            continue
        asset_name = record["representation"]
        asset_path = published_questions_dir / question_id / asset_name
        if not asset_path.is_file():
            issues.append(
                AssetAssignmentIssue(
                    kind="asset_file_missing",
                    question_id=question_id,
                    detail=f"{record['assignment_id']}: {asset_path} does not exist",
                )
            )
            continue
        if f"{question_id}/{asset_name}" not in md_text:
            issues.append(
                AssetAssignmentIssue(
                    kind="asset_not_referenced_in_markdown",
                    question_id=question_id,
                    detail=(
                        f"{record['assignment_id']}: {question_id}/{asset_name} not referenced "
                        f"in {question_id}.md"
                    ),
                )
            )
    return issues
