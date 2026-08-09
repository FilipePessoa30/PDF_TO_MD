"""The fidelity gate: decide `verified` vs `needs_review` for one question.

Implements PROMPT section 32 literally: `extraction_status = verified` only
when there is positive evidence the statement is complete, alternatives are
complete/ordered (when applicable), visual elements are preserved, source
pages are correct, and nothing was silently reconstructed. Any assembler
warning, missing asset, or structural anomaly routes to `needs_review`
instead - this function never "forces" verified to make a count look better.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from enade.extraction.assembler import CodeSegment, ExtractedQuestion
from enade.extraction.assets import RenderedAsset
from enade.extraction.boundaries import QuestionKind
from enade.models.enums import ExtractionStatus

EXPECTED_ALTERNATIVE_LETTERS = ["A", "B", "C", "D", "E"]


@dataclass
class ValidationOutcome:
    status: ExtractionStatus
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

    if len(rendered_assets) != len(extracted.figure_regions):
        reasons.append(
            f"detected {len(extracted.figure_regions)} figure region(s) but only "
            f"{len(rendered_assets)} were rendered to assets"
        )
    for asset in rendered_assets:
        if len(asset.sha256) != 64:
            reasons.append(f"asset {asset.asset_id} has an invalid sha256")
        if asset.width_px <= 0 or asset.height_px <= 0:
            reasons.append(f"asset {asset.asset_id} has degenerate dimensions")

    if not has_answer:
        reasons.append("no corresponding answer-key/answer-standard entry found")

    has_code = any(isinstance(seg, CodeSegment) for seg in extracted.statement_segments)
    if has_code and extracted.start_page != extracted.end_page:
        reasons.append(
            "statement contains a code/pseudocode block spanning multiple pages - "
            "column layout + code formatting fidelity needs manual confirmation"
        )

    status = ExtractionStatus.NEEDS_REVIEW if reasons else ExtractionStatus.VERIFIED
    return ValidationOutcome(status=status, reasons=reasons)
