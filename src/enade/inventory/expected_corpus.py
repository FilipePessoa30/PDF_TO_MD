"""The corpus shape *observed previously* (per the Phase 0 brief), for comparison only.

This module must never influence what :mod:`enade.inventory.scanner` finds -
it exists purely so ``enade inventory`` can report whether the real,
freshly-discovered corpus matches what was expected, and call out any
divergence explicitly instead of silently trusting either source.
"""

from __future__ import annotations

from dataclasses import dataclass

from enade.inventory.manifest import SourceManifest

#: (year, course_letter) pairs expected per the Phase 0 brief.
#: course_letter is None for the 2011 unified "COMPUTACAO" booklet.
EXPECTED_BUNDLES: frozenset[tuple[int, str | None]] = frozenset(
    {
        (2005, "b"),
        (2005, "e"),
        (2008, "b"),
        (2008, "e"),
        (2011, None),
        (2014, "b"),
        (2014, "e"),
        (2014, "l"),
        (2017, "b"),
        (2017, "e"),
        (2017, "l"),
        (2017, "s"),
        (2019, "e"),
        (2021, "b"),
        (2021, "l"),
        (2021, "s"),
    }
)

EXPECTED_BUNDLE_COUNT = 16
EXPECTED_PDF_COUNT = 48
EXPECTED_DOCS_PER_BUNDLE = 3  # exam + answer_key + answer_standard


@dataclass
class CorpusComparison:
    matches_expected: bool
    missing_bundles: list[tuple[int, str | None]]
    unexpected_bundles: list[tuple[int, str | None]]
    notes: list[str]


def compare_with_expected(manifest: SourceManifest) -> CorpusComparison:
    found_bundles = {(b.year, b.course_letter) for b in manifest.bundles}
    missing = sorted(EXPECTED_BUNDLES - found_bundles)
    unexpected = sorted(found_bundles - EXPECTED_BUNDLES)

    notes: list[str] = []
    total_pdfs = manifest.summary.get("total_pdfs", 0)
    if total_pdfs != EXPECTED_PDF_COUNT:
        notes.append(
            f"total PDFs found ({total_pdfs}) != previously observed count ({EXPECTED_PDF_COUNT})"
        )
    if len(manifest.bundles) != EXPECTED_BUNDLE_COUNT:
        notes.append(
            f"bundle count found ({len(manifest.bundles)}) != previously observed count ({EXPECTED_BUNDLE_COUNT})"
        )
    for bundle in manifest.bundles:
        present = sum(
            1
            for slot in ("exam", "answer_key", "answer_standard")
            if getattr(bundle, slot) is not None
        )
        if present != EXPECTED_DOCS_PER_BUNDLE:
            notes.append(f"bundle {bundle.exam_id!r} has {present}/3 documents, not the expected 3")

    matches = not missing and not unexpected and not notes
    return CorpusComparison(
        matches_expected=matches,
        missing_bundles=missing,
        unexpected_bundles=unexpected,
        notes=notes,
    )
