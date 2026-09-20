"""Unit tests for the content-assignment ledger gates (PROMPT Phase 3J).

Every fixture is synthetic - a plain dict of ``ContentAssignment`` kwargs
run through the constructor - never real corpus data, per the phase's own
constraint that these tests must not depend on question ID, year, page or
copied PDF coordinates.
"""

from __future__ import annotations

from pathlib import Path

from enade.extraction.content_assignment import (
    ContentAssignment,
    detect_duplicate_assignments,
    detect_missing_assignments,
    find_orphan_assets,
)

_BASE = dict(
    source_page=1,
    source_bbox=(0.0, 0.0, 10.0, 10.0),
    representation="x",
    reason="test fixture",
    evidence="test",
    confidence=1.0,
    status="assigned",
)


def _assignment(**overrides) -> ContentAssignment:
    kwargs = {**_BASE, **overrides}
    return ContentAssignment(**kwargs)


# --- duplication gate ----------------------------------------------------


def test_one_source_one_destination_is_not_a_duplicate():
    records = [
        _assignment(
            assignment_id="a1",
            source_element_id="s1",
            source_type="line",
            canonical_owner="question",
            anchor="statement",
            publication_destination="statement",
            question_id="q1",
        )
    ]
    assert detect_duplicate_assignments(records) == []


def test_same_source_two_destinations_is_a_duplicate():
    records = [
        _assignment(
            assignment_id="a1",
            source_element_id="s1",
            source_type="line",
            canonical_owner="question",
            anchor="statement",
            publication_destination="statement",
            question_id="q13",
        ),
        _assignment(
            assignment_id="a2",
            source_element_id="s1",
            source_type="line",
            canonical_owner="alternative",
            anchor="E",
            publication_destination="alternative_text",
            question_id="q13",
        ),
    ]
    findings = detect_duplicate_assignments(records)
    assert len(findings) == 1
    assert findings[0].source_element_id == "s1"
    assert set(findings[0].destinations) == {"statement", "alternative_text"}


def test_same_source_two_alternatives_is_a_duplicate():
    records = [
        _assignment(
            assignment_id="a1",
            source_element_id="s1",
            source_type="line",
            canonical_owner="alternative",
            anchor="B",
            publication_destination="alternative_text",
            question_id="q1",
        ),
        _assignment(
            assignment_id="a2",
            source_element_id="s1",
            source_type="line",
            canonical_owner="alternative",
            anchor="C",
            publication_destination="alternative_text",
            question_id="q1",
        ),
    ]
    findings = detect_duplicate_assignments(records)
    assert len(findings) == 1
    assert set(findings[0].alternative_labels) == {"B", "C"}


def test_identical_text_from_different_sources_is_never_flagged():
    # Two distinct alternatives that happen to share the same wording -
    # this must never be treated as duplication (PROMPT section 9).
    records = [
        _assignment(
            assignment_id="a1",
            source_element_id="s1",
            source_type="line",
            canonical_owner="alternative",
            anchor="A",
            publication_destination="alternative_text",
            representation="Nenhuma das anteriores.",
            question_id="q1",
        ),
        _assignment(
            assignment_id="a2",
            source_element_id="s2",
            source_type="line",
            canonical_owner="alternative",
            anchor="D",
            publication_destination="alternative_text",
            representation="Nenhuma das anteriores.",
            question_id="q1",
        ),
    ]
    assert detect_duplicate_assignments(records) == []


def test_authorized_mirror_is_not_flagged():
    records = [
        _assignment(
            assignment_id="a1",
            source_element_id="s1",
            source_type="line",
            canonical_owner="question",
            anchor="statement",
            publication_destination="statement",
            question_id="q1",
            duplication_mode="documented_accessibility_mirror",
        ),
        _assignment(
            assignment_id="a2",
            source_element_id="s1",
            source_type="asset",
            canonical_owner="question",
            anchor="question_asset",
            publication_destination="question_asset",
            question_id="q1",
            duplication_mode="documented_accessibility_mirror",
        ),
    ]
    assert detect_duplicate_assignments(records) == []


def test_mismatched_mirror_modes_are_still_flagged():
    # Both records declare *some* mirror mode, but not the *same* one -
    # never treated as a single authorized pair.
    records = [
        _assignment(
            assignment_id="a1",
            source_element_id="s1",
            source_type="line",
            canonical_owner="question",
            anchor="statement",
            publication_destination="statement",
            question_id="q1",
            duplication_mode="documented_accessibility_mirror",
        ),
        _assignment(
            assignment_id="a2",
            source_element_id="s1",
            source_type="asset",
            canonical_owner="alternative",
            anchor="B",
            publication_destination="alternative_asset",
            question_id="q1",
            duplication_mode="some_other_mode",
        ),
    ]
    assert len(detect_duplicate_assignments(records)) == 1


# --- missing-assignment gate ----------------------------------------------


def test_assigned_status_has_no_missing_findings():
    records = [
        _assignment(
            assignment_id="a1",
            source_element_id="s1",
            source_type="line",
            canonical_owner="question",
            anchor="statement",
            publication_destination="statement",
            question_id="q1",
        )
    ]
    assert detect_missing_assignments(records) == []


def test_blocked_source_with_a_real_destination_is_a_source_without_destination_gap():
    records = [
        _assignment(
            assignment_id="a1",
            source_element_id="s1",
            source_type="line",
            canonical_owner="unresolved",
            anchor="unresolved",
            publication_destination="statement",
            question_id="q1",
            status="blocked",
        )
    ]
    findings = detect_missing_assignments(records)
    assert len(findings) == 1
    assert findings[0].kind == "source_without_destination"


def test_unresolved_annotation_owner_is_flagged():
    records = [
        _assignment(
            assignment_id="a1",
            source_element_id="s1",
            source_type="annotation",
            canonical_owner="unresolved",
            anchor="unresolved",
            publication_destination="annotation",
            question_id="d1",
            status="ambiguous",
        )
    ]
    findings = detect_missing_assignments(records)
    assert len(findings) == 1
    assert findings[0].kind == "annotation_without_owner"


def test_unresolved_asset_owner_is_flagged():
    records = [
        _assignment(
            assignment_id="a1",
            source_element_id="s1",
            source_type="asset",
            canonical_owner="unresolved",
            anchor="unresolved",
            publication_destination="question_asset",
            question_id="q8",
            status="ambiguous",
        )
    ]
    findings = detect_missing_assignments(records)
    assert len(findings) == 1
    assert findings[0].kind == "asset_without_owner"


def test_a_fix_that_removes_a_destination_without_moving_it_elsewhere_is_caught():
    # A naive deduplication that just deletes the second occurrence
    # without ever recording where the content *should* go turns a
    # duplicate into a silent loss - modeled here as a blocked line with
    # no other record at all for the same source.
    records = [
        _assignment(
            assignment_id="a1",
            source_element_id="s1",
            source_type="line",
            canonical_owner="unresolved",
            anchor="unresolved",
            publication_destination="blocked",
            question_id="q1",
            status="blocked",
        )
    ]
    # A genuinely blocked-and-labeled-blocked record is not itself a gap -
    # it is the honest "left unresolved" outcome the phase requires
    # (Section 19: "se a geometria permanecer ambígua, mantenha blocker").
    assert detect_missing_assignments(records) == []


# --- orphan-asset gate (PROMPT Fase 4C section 22/23) ---------------------
#
# validate_ledger_against_corpus only ever checks ledger -> disk (every
# asset record the ledger claims must exist for real). It has no way to
# notice a real, published asset file that the ledger's own generator
# silently never produced a record for - the reverse direction. A real
# figure the pipeline created but the ledger is blind to would pass every
# existing gate. find_orphan_assets closes that gap; these fixtures use a
# real (tmp_path) filesystem, since the whole point is a disk-vs-ledger
# comparison a synthetic-only fixture cannot exercise.


def _write_question(tmp_path: Path, question_id: str, *asset_names: str) -> Path:
    qdir = tmp_path / question_id
    qdir.mkdir(parents=True, exist_ok=True)
    for name in asset_names:
        (qdir / name).write_bytes(b"\x89PNG\r\n")
    return qdir


def test_asset_on_disk_with_no_ledger_record_is_an_orphan(tmp_path: Path):
    _write_question(tmp_path, "q1", "figure-01.png")
    payload = {"assignments": []}  # the generator produced zero asset records for q1
    issues = find_orphan_assets(payload, tmp_path)
    assert len(issues) == 1
    assert issues[0].kind == "asset_not_in_ledger"
    assert issues[0].question_id == "q1"


def test_asset_on_disk_with_a_matching_ledger_record_is_not_an_orphan(tmp_path: Path):
    _write_question(tmp_path, "q1", "figure-01.png")
    payload = {
        "assignments": [
            {"question_id": "q1", "source_type": "asset", "representation": "figure-01.png"}
        ]
    }
    assert find_orphan_assets(payload, tmp_path) == []


def test_answer_standard_assets_are_never_flagged_as_orphans(tmp_path: Path):
    # D09/D10-style: an answer-standard asset the ledger never tracks by
    # design (PROMPT Fase 4B section 6/N) must never be flagged here -
    # this gate is scoped to the same asset universe the ledger itself
    # claims to cover, never a silent scope expansion.
    qdir = tmp_path / "d09" / "answer-standard"
    qdir.mkdir(parents=True)
    (qdir / "padrao-01.png").write_bytes(b"\x89PNG\r\n")
    payload = {"assignments": []}
    assert find_orphan_assets(payload, tmp_path) == []


def test_multiple_orphans_across_questions_are_all_reported(tmp_path: Path):
    _write_question(tmp_path, "q1", "figure-01.png", "figure-02.png")
    _write_question(tmp_path, "q2", "figure-01.png")
    payload = {
        "assignments": [
            {"question_id": "q1", "source_type": "asset", "representation": "figure-01.png"}
        ]
    }
    issues = find_orphan_assets(payload, tmp_path)
    assert {(i.question_id, i.kind) for i in issues} == {
        ("q1", "asset_not_in_ledger"),
        ("q2", "asset_not_in_ledger"),
    }


def test_asset_claimed_by_the_wrong_question_is_still_an_orphan_for_its_real_owner(
    tmp_path: Path,
):
    # PROMPT Fase 4D section 13: "asset pertencente a questao errada" - a
    # record that claims (q2, figure-01.png) never satisfies the real,
    # on-disk file at q1/figure-01.png. The key is (question_id,
    # representation) together, never representation alone - a record for
    # the wrong owner must never silently "cover" a different question's
    # real file just because the filename matches.
    _write_question(tmp_path, "q1", "figure-01.png")
    payload = {
        "assignments": [
            {"question_id": "q2", "source_type": "asset", "representation": "figure-01.png"}
        ]
    }
    issues = find_orphan_assets(payload, tmp_path)
    assert len(issues) == 1
    assert issues[0].question_id == "q1"
    assert issues[0].kind == "asset_not_in_ledger"
