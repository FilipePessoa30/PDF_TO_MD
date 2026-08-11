from __future__ import annotations

from enade.extraction.assembler import ExtractedAlternative, ExtractedQuestion, TextSegment
from enade.extraction.assets import RenderedAsset
from enade.extraction.boundaries import QuestionKind
from enade.extraction.validator import evaluate_extraction
from enade.models.enums import (
    AssetExtractionMethod,
    AssetType,
    AutomaticValidationStatus,
    ExtractionStatus,
)

_FULL_ALTS = [ExtractedAlternative(letter=letter, text=f"texto {letter}") for letter in "ABCDE"]


def _extracted(**overrides) -> ExtractedQuestion:
    base = dict(
        kind=QuestionKind.OBJECTIVE,
        number=1,
        start_page=1,
        end_page=1,
        statement_segments=[TextSegment(text="Enunciado completo.")],
        alternatives=list(_FULL_ALTS),
        figure_regions=[],
        warnings=[],
    )
    base.update(overrides)
    return ExtractedQuestion(**base)


def test_clean_objective_question_passes_automatic_validation():
    """A clean automatic pass alone is "extracted", never "verified" - that
    additionally requires a real visual comparison against the PDF (PROMPT
    section 12/13, Phase 1B), applied afterwards in to_question.py.
    """
    outcome = evaluate_extraction(_extracted(), rendered_assets=[], has_answer=True)
    assert outcome.status == ExtractionStatus.EXTRACTED
    assert outcome.automatic_validation == AutomaticValidationStatus.PASSED
    assert outcome.reasons == []


def test_assembler_warnings_carry_over_as_needs_review():
    outcome = evaluate_extraction(
        _extracted(warnings=["something looked off"]), rendered_assets=[], has_answer=True
    )
    assert outcome.status == ExtractionStatus.NEEDS_REVIEW
    assert "something looked off" in outcome.reasons


def test_missing_answer_forces_needs_review():
    outcome = evaluate_extraction(_extracted(), rendered_assets=[], has_answer=False)
    assert outcome.status == ExtractionStatus.NEEDS_REVIEW
    assert any("answer" in r for r in outcome.reasons)


def test_wrong_alternative_count_forces_needs_review():
    outcome = evaluate_extraction(
        _extracted(alternatives=_FULL_ALTS[:3]), rendered_assets=[], has_answer=True
    )
    assert outcome.status == ExtractionStatus.NEEDS_REVIEW
    assert any("A-E" in r for r in outcome.reasons)


def test_empty_alternative_text_forces_needs_review():
    bad_alts = list(_FULL_ALTS[:4]) + [ExtractedAlternative(letter="E", text="   ")]
    outcome = evaluate_extraction(
        _extracted(alternatives=bad_alts), rendered_assets=[], has_answer=True
    )
    assert outcome.status == ExtractionStatus.NEEDS_REVIEW


def test_missing_rendered_asset_for_detected_region_forces_needs_review():
    from enade.extraction.figures import VisualRegion

    region = VisualRegion(page_number=1, bbox=(0, 0, 10, 10), element_count=1)
    outcome = evaluate_extraction(
        _extracted(figure_regions=[region]), rendered_assets=[], has_answer=True
    )
    assert outcome.status == ExtractionStatus.NEEDS_REVIEW
    assert any("rendered to assets" in r for r in outcome.reasons)


def _asset(sha256: str = "a" * 64, width: int = 100, height: int = 100) -> RenderedAsset:
    return RenderedAsset(
        asset_id="figure-01",
        asset_type=AssetType.DIAGRAM,
        relative_path="q/figure-01.png",
        absolute_path=None,  # type: ignore[arg-type]
        source_page=1,
        sha256=sha256,
        width_px=width,
        height_px=height,
        extraction_method=AssetExtractionMethod.RASTER_CROP,
    )


def test_invalid_asset_sha256_forces_needs_review():
    outcome = evaluate_extraction(
        _extracted(), rendered_assets=[_asset(sha256="not-a-hash")], has_answer=True
    )
    assert outcome.status == ExtractionStatus.NEEDS_REVIEW
    assert any("sha256" in r for r in outcome.reasons)


def test_degenerate_asset_dimensions_force_needs_review():
    outcome = evaluate_extraction(_extracted(), rendered_assets=[_asset(width=0)], has_answer=True)
    assert outcome.status == ExtractionStatus.NEEDS_REVIEW
    assert any("dimensions" in r for r in outcome.reasons)


def test_empty_statement_forces_needs_review():
    outcome = evaluate_extraction(
        _extracted(statement_segments=[TextSegment(text="   ")]),
        rendered_assets=[],
        has_answer=True,
    )
    assert outcome.status == ExtractionStatus.NEEDS_REVIEW
    assert any("empty statement" in r for r in outcome.reasons)


def test_multipage_code_block_does_not_by_itself_force_needs_review():
    """A code block spanning multiple pages is not, by itself, a mechanical
    defect (see docs/decisions.md, "Phase 1C" ADR): Phase 1B's blanket
    distrust rule here was a permanent, unsatisfiable block on ever
    reaching ``verified`` for any such question, superseded once Phase 1C
    fixed and tested the underlying two-column/code reconstruction (D5).
    Per-question fidelity is now enforced via the real, disclosed
    ``visual_validation`` audit, not a structural shape check here.
    """
    from enade.extraction.assembler import CodeSegment

    extracted = _extracted(
        start_page=1,
        end_page=2,
        statement_segments=[TextSegment(text="intro"), CodeSegment(text="void f() {}")],
    )
    outcome = evaluate_extraction(extracted, rendered_assets=[], has_answer=True)
    assert outcome.status == ExtractionStatus.EXTRACTED
    assert outcome.automatic_validation == AutomaticValidationStatus.PASSED
    assert outcome.reasons == []


def test_discursive_question_does_not_require_alternatives():
    extracted = _extracted(kind=QuestionKind.DISCURSIVE, alternatives=[])
    outcome = evaluate_extraction(extracted, rendered_assets=[], has_answer=True)
    assert outcome.status == ExtractionStatus.EXTRACTED
    assert outcome.automatic_validation == AutomaticValidationStatus.PASSED
