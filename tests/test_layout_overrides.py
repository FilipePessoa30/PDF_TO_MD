from __future__ import annotations

from pathlib import Path

from enade.extraction.layout_overrides import (
    LayoutOverride,
    LayoutOverrideSet,
    load_layout_overrides,
)


def _override(**overrides) -> LayoutOverride:
    base = dict(
        pdf_sha256="a" * 64,
        page=14,
        bbox=(100.0, 115.0, 215.0, 138.0),
        rule="exclude_from_orphan_marker_merge",
        question_id="enade-2011-computing-q22",
        reason="test",
        evidence="test",
        status="reviewed",
    )
    base.update(overrides)
    return LayoutOverride(**base)


def test_line_inside_bbox_on_matching_page_and_hash_is_excluded():
    overrides = LayoutOverrideSet(overrides=[_override()])
    assert overrides.excludes_from_orphan_marker("a" * 64, 14, (112.0, 119.0, 119.0, 134.0))


def test_wrong_pdf_hash_does_not_match():
    overrides = LayoutOverrideSet(overrides=[_override()])
    assert not overrides.excludes_from_orphan_marker("b" * 64, 14, (112.0, 119.0, 119.0, 134.0))


def test_wrong_page_does_not_match():
    overrides = LayoutOverrideSet(overrides=[_override()])
    assert not overrides.excludes_from_orphan_marker("a" * 64, 15, (112.0, 119.0, 119.0, 134.0))


def test_line_outside_bbox_does_not_match():
    overrides = LayoutOverrideSet(overrides=[_override()])
    # Same page/hash, but far outside the declared bbox.
    assert not overrides.excludes_from_orphan_marker("a" * 64, 14, (400.0, 500.0, 410.0, 512.0))


def test_line_only_partially_inside_bbox_does_not_match():
    overrides = LayoutOverrideSet(overrides=[_override()])
    # x1 (220) extends past the override's own x1 (215) - not full containment.
    assert not overrides.excludes_from_orphan_marker("a" * 64, 14, (112.0, 119.0, 220.0, 134.0))


def test_non_matching_rule_is_ignored():
    overrides = LayoutOverrideSet(overrides=[_override(rule="some_other_rule")])
    assert not overrides.excludes_from_orphan_marker("a" * 64, 14, (112.0, 119.0, 119.0, 134.0))


def test_missing_file_returns_empty_set(tmp_path: Path):
    overrides = load_layout_overrides(tmp_path / "does-not-exist.yaml")
    assert overrides.overrides == []
    assert not overrides.excludes_from_orphan_marker("a" * 64, 1, (0.0, 0.0, 1.0, 1.0))


def test_load_layout_overrides_reads_the_real_yaml():
    # Q13's own suppress_visual_region entry was removed in Phase 2C,
    # superseded by the ownership model (ownership.py) - see
    # docs/decisions.md, Phase 2C ADR, and the NOTE left in its place in
    # layout-overrides.yaml.
    path = Path("data/manifests/layout-overrides.yaml")
    overrides = load_layout_overrides(path)
    assert len(overrides.overrides) >= 2
    q22 = next(o for o in overrides.overrides if o.question_id == "enade-2011-computing-q22")
    assert q22.page == 14
    assert q22.rule == "exclude_from_orphan_marker_merge"
    assert q22.status == "reviewed"
    assert not any(
        o.question_id == "enade-2011-computing-q13" and o.rule == "suppress_visual_region"
        for o in overrides.overrides
    )


def _region_override(**overrides) -> LayoutOverride:
    base = dict(
        pdf_sha256="a" * 64,
        page=10,
        bbox=(0.0, 250.0, 300.0, 650.0),
        rule="suppress_visual_region",
        question_id="enade-2011-computing-q13",
        reason="test",
        evidence="test",
        status="reviewed",
    )
    base.update(overrides)
    return LayoutOverride(**base)


def test_region_center_inside_bbox_is_suppressed():
    overrides = LayoutOverrideSet(overrides=[_region_override()])
    # Matches the real spurious region's own bbox from Q13's investigation.
    assert overrides.suppresses_region("a" * 64, 10, (28.0, 294.0, 287.0, 609.0))


def test_region_center_outside_bbox_is_not_suppressed():
    overrides = LayoutOverrideSet(overrides=[_region_override()])
    assert not overrides.suppresses_region("a" * 64, 10, (400.0, 700.0, 450.0, 720.0))


def test_region_suppression_respects_pdf_hash():
    overrides = LayoutOverrideSet(overrides=[_region_override()])
    assert not overrides.suppresses_region("b" * 64, 10, (28.0, 294.0, 287.0, 609.0))


def test_region_suppression_respects_page():
    overrides = LayoutOverrideSet(overrides=[_region_override()])
    assert not overrides.suppresses_region("a" * 64, 11, (28.0, 294.0, 287.0, 609.0))


def test_orphan_marker_override_does_not_suppress_regions():
    # A rule mismatch: an exclude_from_orphan_marker_merge override must
    # never accidentally also suppress a visual region.
    overrides = LayoutOverrideSet(overrides=[_override(page=10, bbox=(0.0, 250.0, 300.0, 650.0))])
    assert not overrides.suppresses_region("a" * 64, 10, (28.0, 294.0, 287.0, 609.0))


def _protect_override(**overrides) -> LayoutOverride:
    base = dict(
        pdf_sha256="a" * 64,
        page=14,
        bbox=(540.0, 125.0, 560.0, 148.0),
        rule="protect_from_label_absorption",
        question_id="enade-2011-computing-q23",
        reason="test",
        evidence="test",
        status="reviewed",
    )
    base.update(overrides)
    return LayoutOverride(**base)


def test_line_inside_protect_bbox_is_protected():
    overrides = LayoutOverrideSet(overrides=[_protect_override()])
    assert overrides.protects_from_label_absorption("a" * 64, 14, (547.3, 129.7, 555.7, 143.0))


def test_line_outside_protect_bbox_is_not_protected():
    overrides = LayoutOverrideSet(overrides=[_protect_override()])
    assert not overrides.protects_from_label_absorption("a" * 64, 14, (0.0, 0.0, 10.0, 10.0))


def test_protect_override_respects_pdf_hash():
    overrides = LayoutOverrideSet(overrides=[_protect_override()])
    assert not overrides.protects_from_label_absorption("b" * 64, 14, (547.3, 129.7, 555.7, 143.0))


def _exclude_candidate_override(**overrides) -> LayoutOverride:
    base = dict(
        pdf_sha256="a" * 64,
        page=14,
        bbox=(488.0, 129.0, 550.0, 146.0),
        rule="exclude_from_region_candidates",
        question_id="enade-2011-computing-q23",
        reason="test",
        evidence="test",
        status="reviewed",
    )
    base.update(overrides)
    return LayoutOverride(**base)


def test_image_inside_exclude_candidate_bbox_is_excluded():
    overrides = LayoutOverrideSet(overrides=[_exclude_candidate_override()])
    assert overrides.excludes_from_region_candidates("a" * 64, 14, (490.3, 131.3, 547.1, 143.7))


def test_image_outside_exclude_candidate_bbox_is_not_excluded():
    overrides = LayoutOverrideSet(overrides=[_exclude_candidate_override()])
    assert not overrides.excludes_from_region_candidates("a" * 64, 14, (0.0, 0.0, 10.0, 10.0))


def test_the_three_rules_are_mutually_exclusive():
    # A protect_from_label_absorption override must never also exclude a
    # region candidate or an orphan marker, and vice versa - each rule
    # kind only ever answers its own question.
    protect = _protect_override()
    exclude_candidate = _exclude_candidate_override()
    orphan = _override(page=14)
    overrides = LayoutOverrideSet(overrides=[protect, exclude_candidate, orphan])
    bbox = (547.3, 129.7, 555.7, 143.0)
    assert overrides.protects_from_label_absorption("a" * 64, 14, bbox)
    assert not overrides.excludes_from_region_candidates("a" * 64, 14, bbox)
    assert not overrides.suppresses_region("a" * 64, 14, bbox)
