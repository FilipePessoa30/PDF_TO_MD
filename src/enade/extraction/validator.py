"""The fidelity gate: decide `verified` vs `needs_review` for one question.

This module only ever performs *mechanical* checks (schema shape,
alternative sequence, asset counts/hashes, answer linkage) - its verdict is
``automatic_validation``, not ``extraction_status`` directly. Per PROMPT
section 12/13 (Phase 1B), passing every mechanical check is necessary but
not sufficient for ``extraction_status='verified'``: that additionally
requires a real human visual comparison against the rendered PDF
(``visual_validation``, applied afterwards - see to_question.py). A
question with mechanical warnings always routes to ``needs_review``
regardless of any visual check; a question with none is only ever
``extracted`` (automatic-clean, visual pending) until that separate,
evidence-based visual confirmation happens - this function never "forces"
verified to make a count look better.

Phase 1B added a blanket "code + multi-page statement needs manual
confirmation" reason here, because the two-column/code layout
reconstruction it distrusted was, at the time, genuinely broken (D5 - see
docs/decisions.md). That reason could never be satisfied: it fired on the
mere *shape* "has code and spans >1 page" regardless of correctness, so a
question matching that shape could never reach ``automatic_validation=
passed`` and therefore never ``verified``, even after Phase 1C fixed and
tested the underlying reconstruction (PROMPT section 22 explicitly expects
D5 to be promotable once fixed). Removed rather than special-cased per
question id: per-question fidelity is enforced the same way as every other
question in this corpus - a real, disclosed ``visual_validation`` entry,
not a permanent structural distrust rule.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from enade.extraction.assembler import ExtractedQuestion
from enade.extraction.assets import RenderedAsset
from enade.extraction.boundaries import QuestionKind
from enade.models.enums import AutomaticValidationStatus, ExtractionStatus

EXPECTED_ALTERNATIVE_LETTERS = ["A", "B", "C", "D", "E"]


@dataclass
class ValidationOutcome:
    status: ExtractionStatus
    automatic_validation: AutomaticValidationStatus
    reasons: list[str] = field(default_factory=list)


def evaluate_extraction(
    extracted: ExtractedQuestion,
    rendered_assets: list[RenderedAsset],
    *,
    has_answer: bool,
) -> ValidationOutcome:
    reasons: list[str] = list(extracted.warnings)

    if not extracted.plain_statement.strip():
        reasons.append("empty statement after chrome/figure filtering")

    if extracted.kind == QuestionKind.OBJECTIVE:
        letters = [a.letter for a in extracted.alternatives]
        if letters != EXPECTED_ALTERNATIVE_LETTERS:
            reasons.append(f"alternatives are not exactly A-E in order (found {letters})")
        for alt in extracted.alternatives:
            if not alt.text.strip():
                reasons.append(f"alternative {alt.letter} has empty text")

    expected_asset_count = len(extracted.figure_regions) + len(extracted.tables)
    if len(rendered_assets) != expected_asset_count:
        reasons.append(
            f"detected {len(extracted.figure_regions)} figure region(s) and "
            f"{len(extracted.tables)} table(s) but only "
            f"{len(rendered_assets)} were rendered to assets"
        )
    for asset in rendered_assets:
        if len(asset.sha256) != 64:
            reasons.append(f"asset {asset.asset_id} has an invalid sha256")
        if asset.width_px <= 0 or asset.height_px <= 0:
            reasons.append(f"asset {asset.asset_id} has degenerate dimensions")

    if not has_answer:
        reasons.append("no corresponding answer-key/answer-standard entry found")

    if reasons:
        return ValidationOutcome(
            status=ExtractionStatus.NEEDS_REVIEW,
            automatic_validation=AutomaticValidationStatus.FAILED,
            reasons=reasons,
        )
    return ValidationOutcome(
        status=ExtractionStatus.EXTRACTED,
        automatic_validation=AutomaticValidationStatus.PASSED,
        reasons=reasons,
    )
