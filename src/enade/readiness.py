"""Readiness gate: a separate, substantive question from ``verify-gold``
(PROMPT Phase 1C section 14).

``enade verify-gold`` only proves *absence of drift* against a locked
manifest - it says nothing about whether the underlying corpus is actually
trustworthy enough to build on. This module answers that second, harder
question directly: given everything currently on disk (not just hashes),
is this course's extracted corpus ``READY_FOR_2011`` (safe to use as the
template for processing the next booklet) or ``NOT_READY_FOR_2011``?

Deliberately never a bare pass/fail count: every reason a corpus is not
ready is returned as an explicit, individually-readable
:class:`ReadinessBlocker`, so a caller (human or the next phase) knows
exactly what would need to change, not just that something is wrong.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from enade.extraction.blocker_ledger import load_blocker_ledger, validate_ledger
from enade.extraction.visual_audit import VisualAuditCoverage, assess_visual_audit_coverage
from enade.gold import GoldDivergence, GoldManifest, verify_gold_manifest
from enade.markdown_format import load_questions_directory
from enade.models.enums import AnswerValidationStatus, ExtractionStatus, QuestionType


@dataclass(frozen=True)
class ReadinessBlocker:
    kind: str
    detail: str
    #: True for a pipeline-caused structural loss; False for an inherent,
    #: already-documented ambiguity in the source document itself (PROMPT
    #: section 14: "uma ambiguidade inerente e visualmente preservada, como
    #: Q20, pode ser classificada separadamente de perda estrutural causada
    #: pelo pipeline"). Currently every blocker this module can detect is
    #: structural by construction - see ``assess_readiness``'s docstring
    #: for why a non-structural exception is not modeled as its own field
    #: yet: no question in this corpus currently needs one.
    structural: bool = True


@dataclass(frozen=True)
class ReadinessReport:
    ready: bool
    blockers: tuple[ReadinessBlocker, ...]
    total_questions: int
    verified_count: int
    needs_review_count: int
    gold_maturity: str
    gold_divergences: tuple[GoldDivergence, ...] = field(default_factory=tuple)
    visual_audit_coverage: VisualAuditCoverage | None = None

    @property
    def classification(self) -> str:
        return "READY_FOR_2011" if self.ready else "NOT_READY_FOR_2011"


def assess_readiness(
    manifest: GoldManifest,
    course_dir: Path,
    visual_audit_path: Path | None = None,
    blocker_ledger_path: Path | None = None,
) -> ReadinessReport:
    """Compute a :class:`ReadinessReport` for the questions under
    ``course_dir`` against the locked ``manifest``.

    Considers (PROMPT section 14): gold hash integrity, structural
    blockers already recorded on the manifest, automatic and visual
    validation, asset integrity, answer linkage, and answer-standard
    coverage for discursive questions - never test-pass-count alone.

    ``visual_audit_path``, when given (PROMPT Phase 2B section 3/15), adds
    one more, corpus-level check on top of the existing per-question
    ``question_not_verified`` blockers: whether the audit *file itself*
    reconciles exactly against this corpus's own canonical id set (no
    question missing a verdict, no unexpected or duplicate id). Optional
    and off by default so a course that predates this check (2021, audited
    entirely through per-question ``visual_validation`` already baked into
    each Question at extraction time) is not retroactively required to
    keep a separate audit-file coverage record it never needed.

    ``blocker_ledger_path`` (PROMPT Phase 2C section 3/25), when given,
    makes the canonical blocker ledger (see blocker_ledger.py) a readiness
    input in its own right: the ledger's own internal consistency gate
    (``validate_ledger``) must pass, and every ``open`` blocker it records
    is surfaced here too - so a blocker cannot be marked resolved in the
    ledger while readiness still fails for an unrelated reason (an
    inconsistent, drifted ledger), nor can a blocker the ledger still
    calls ``open`` be silently absent from a NOT_READY report.

    On "non-structural" exceptions (PROMPT Phase 2F section 10/18): the
    blocker ledger's own ``accepted_non_material_difference`` status (see
    blocker_ledger.py) is the first live case - a question whose own
    ``extraction_status`` will never reach ``verified`` through any code
    fix (e.g. 2011 Q34's own deliberately-conservative structural-warning
    false positive), but whose content has been independently,
    individually confirmed correct and formally adjudicated, not silently
    ignored. The ledger is loaded *before* the per-question loop
    specifically so a ``question_not_verified`` finding for a
    ledger-covered question can be marked ``structural=False`` right when
    it is created - a derived consequence of an already-adjudicated gap,
    never hidden, but never counted toward ``ready`` either. Every other
    blocker this function raises is `structural=True` unless the ledger
    says otherwise for that exact question.
    """
    blockers: list[ReadinessBlocker] = []

    divergences = verify_gold_manifest(manifest, course_dir)
    for d in divergences:
        blockers.append(ReadinessBlocker(kind=f"gold_divergence:{d.kind}", detail=d.detail))

    for blocker_id in manifest.structural_blockers:
        blockers.append(
            ReadinessBlocker(
                kind="recorded_structural_blocker",
                detail=f"{blocker_id}: still listed in the gold manifest's structural_blockers",
            )
        )

    # Loaded early (PROMPT Phase 2F): question ids whose own non-
    # verification is already formally adjudicated as a non-material
    # difference, not a real defect - consulted below when a
    # question_not_verified finding is created for that same question.
    accepted_difference_question_ids: set[str] = set()
    if blocker_ledger_path is not None:
        early_ledger = load_blocker_ledger(blocker_ledger_path)
        accepted_difference_question_ids = {
            b.question_id
            for b in early_ledger.blockers
            if b.status == "accepted_non_material_difference"
        }

    questions = load_questions_directory(course_dir)
    verified_count = 0
    needs_review_count = 0

    visual_coverage: VisualAuditCoverage | None = None
    if visual_audit_path is not None:
        visual_coverage = assess_visual_audit_coverage(
            visual_audit_path, frozenset(questions.keys())
        )
        if not visual_coverage.fully_covered:
            blockers.append(
                ReadinessBlocker(
                    kind="visual_audit_incomplete",
                    detail=(
                        f"{visual_coverage.passed_count + visual_coverage.failed_count}/"
                        f"{len(questions)} questions have an explicit visual-audit verdict "
                        f"({visual_coverage.not_performed_count} not_performed"
                        + (
                            f", unexpected ids: {sorted(visual_coverage.unexpected_ids)}"
                            if visual_coverage.unexpected_ids
                            else ""
                        )
                        + (
                            f", duplicate ids: {sorted(visual_coverage.duplicate_ids)}"
                            if visual_coverage.duplicate_ids
                            else ""
                        )
                        + ")"
                    ),
                )
            )

    for question_id in sorted(questions):
        question = questions[question_id]

        if question.extraction_status == ExtractionStatus.VERIFIED:
            verified_count += 1
        else:
            needs_review_count += 1
            blockers.append(
                ReadinessBlocker(
                    kind="question_not_verified",
                    detail=f"{question_id}: extraction_status={question.extraction_status.value}",
                    structural=question_id not in accepted_difference_question_ids,
                )
            )

        for asset in question.assets:
            if not asset.sha256:
                blockers.append(
                    ReadinessBlocker(
                        kind="asset_missing_hash", detail=f"{question_id}: asset {asset.id}"
                    )
                )

        if question.question_type == QuestionType.MULTIPLE_CHOICE:
            if question.answer_validation_status not in (
                AnswerValidationStatus.VALIDATED,
                AnswerValidationStatus.ANNULLED,
            ):
                blockers.append(
                    ReadinessBlocker(
                        kind="answer_not_resolved",
                        detail=f"{question_id}: answer_validation_status="
                        f"{question.answer_validation_status.value}",
                    )
                )
        elif question.question_type == QuestionType.DISCURSIVE:
            if question.answer_standard is None:
                blockers.append(
                    ReadinessBlocker(kind="missing_answer_standard", detail=question_id)
                )
            else:
                for asset in question.answer_standard.assets:
                    if not asset.sha256:
                        blockers.append(
                            ReadinessBlocker(
                                kind="answer_standard_asset_missing_hash",
                                detail=f"{question_id}: asset {asset.id}",
                            )
                        )

    if blocker_ledger_path is not None:
        ledger = early_ledger
        for issue in validate_ledger(ledger):
            blockers.append(
                ReadinessBlocker(kind=f"blocker_ledger_invalid:{issue.kind}", detail=issue.detail)
            )
        for blocker in ledger.blockers:
            if blocker.is_open:
                blockers.append(
                    ReadinessBlocker(
                        kind="blocker_ledger_open",
                        detail=f"{blocker.id} ({blocker.question_id}): {blocker.description}",
                    )
                )

    # A non-structural blocker (PROMPT Phase 2F: a question_not_verified
    # finding already covered by an accepted_non_material_difference
    # ledger entry) is reported - never hidden - but never counted toward
    # readiness; only a genuine structural finding blocks it.
    return ReadinessReport(
        ready=not any(b.structural for b in blockers),
        blockers=tuple(blockers),
        total_questions=len(questions),
        verified_count=verified_count,
        needs_review_count=needs_review_count,
        gold_maturity=manifest.maturity,
        gold_divergences=tuple(divergences),
        visual_audit_coverage=visual_coverage,
    )
