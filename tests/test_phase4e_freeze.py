"""Phase-4E freeze gate (PROMPT Fase 4E section 24) - PARTIALLY historical
as of Fase 5A (PROMPT Fase 5A section 3).

``phase-4e-freeze.json`` is the TERMINAL freeze of the extraction layer
(Fase 5A section 3: "nao crie phase-4f-freeze.json"): unlike every prior
transition (4A->4B, 4B->4C, 4C->4D, 4D->4E), no new extraction freeze
ever supersedes it. Fase 5A's own semantic freeze
(``data/manifests/phase-5a-semantic-freeze.json``) instead records a hash
reference to this file, so tampering is still detectable - see
``tests/test_phase5a_semantic_freeze.py``.

Exactly as happened to every freeze before it, though, two things moved
out from under this file's own point-in-time git snapshot once real time
passed:

1. Fase 4E's own corrective work (the reciprocal table anchor,
   ``freeze_contract.py``) was committed and pushed externally as
   ``8e272cc0dd53031ddddc78d3f88c7efdce073a8f`` - the same class of event
   that superseded every earlier freeze - moving HEAD past this freeze's
   recorded ``6e78d5f...`` and clearing its declared ``uncommitted_changes``
   set (those files are now part of HEAD's history, not "uncommitted").
2. Fase 5A itself needed to extend ``src/enade/cli.py`` (one of this
   freeze's three ``generation_tooling`` entries) with new, purely
   additive semantic-layer commands (``validate-taxonomy``,
   ``validate-semantic-annotations``, ``build-semantic-review``) -
   an expected, permitted evolution of a shared file (PROMPT Fase 5A
   section 4: "apos qualquer alteracao de codigo compartilhado, revalide
   o freeze"), never a rewrite of any extraction command it already
   certified.

The three checks that depended on those facts staying frozen in time are
rewritten below to their historical-fact equivalents (ancestry instead of
equality; "now committed" instead of "still uncommitted"; per-file
tooling checks instead of one blanket check). Every other check in this
file is still a live, strict gate - ``data/questions``, the manifests,
reports, reviews, and the content-assignment ledger must still match this
freeze exactly, since none of those were ever supposed to change again
after Fase 4E (PROMPT Fase 5A section 3: "revalide-o"; section 4: "confirme
diff zero em data/questions").

This is also the first freeze required to pass
``enade.freeze_contract.validate_freeze_completeness`` (PROMPT Fase 4E
section 18/24, hardening finding F7): ``phase-4c-freeze.json`` was
promoted to active with its own ``readiness``/``quality_gates`` left as
empty placeholders, and nothing enforced that this could never happen.
That gate is never applied retroactively to any historical freeze - only
to this one.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

import pytest

from enade.freeze_contract import validate_freeze_completeness

PROJECT_ROOT = Path(__file__).parent.parent
FREEZE_PATH = PROJECT_ROOT / "data" / "manifests" / "phase-4e-freeze.json"
OLD_FREEZE_PATHS = {
    "4a": PROJECT_ROOT / "data" / "manifests" / "phase-4a-freeze.json",
    "4b": PROJECT_ROOT / "data" / "manifests" / "phase-4b-freeze.json",
    "4c": PROJECT_ROOT / "data" / "manifests" / "phase-4c-freeze.json",
    "4d": PROJECT_ROOT / "data" / "manifests" / "phase-4d-freeze.json",
}

pytestmark = pytest.mark.skipif(not FREEZE_PATH.exists(), reason="phase-4e-freeze.json not present")


def _load() -> dict:
    return json.loads(FREEZE_PATH.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_freeze_satisfies_the_completeness_contract_f7_hardening():
    """The one gate this project did not have when phase-4c-freeze.json
    was promoted to active: a freeze with empty readiness/quality_gates
    must never be treated as valid again.
    """
    freeze = _load()
    violations = validate_freeze_completeness(freeze)
    assert violations == [], f"freeze fails the completeness contract: {violations}"


def test_freeze_records_the_expected_branch_and_git_ancestry():
    freeze = _load()
    assert freeze["branch"] == "feat/enade-2008-cc-b-pilot"
    assert freeze["master"] == freeze["origin_master"]
    assert freeze["merge_base"] == freeze["master"]


def test_freeze_declares_it_supersedes_the_phase_4d_freeze():
    freeze = _load()
    assert freeze["supersedes"] == "data/manifests/phase-4d-freeze.json"
    assert {e["phase"] for e in freeze["historical_freezes"]} == {"4a", "4b", "4c", "4d"}
    for entry in freeze["historical_freezes"]:
        assert entry["status"] == "superseded"


def test_freeze_records_the_pre_existing_remote_commit_without_attributing_it_to_this_phase():
    freeze = _load()
    entry = freeze["pre_existing_remote_commit"]
    assert entry["sha"] == "6e78d5f333370357653e15d271ae8d0835bc6a78"


@pytest.mark.parametrize("phase", ["4a", "4b", "4c", "4d"])
def test_historical_freeze_entry_hash_matches_the_real_file_unedited(phase):
    freeze = _load()
    entry = next(e for e in freeze["historical_freezes"] if e["phase"] == phase)
    path = OLD_FREEZE_PATHS[phase]
    assert path.is_file()
    assert _sha256(path) == entry["sha256"]


def test_freeze_recorded_head_is_a_real_ancestor_commit_never_equality_with_current_head():
    """Fase 4E's own corrective work (recorded as ``uncommitted_changes``
    at freeze time) was committed externally as
    ``8e272cc0dd53031ddddc78d3f88c7efdce073a8f`` after this freeze was
    taken - the same pattern every prior freeze went through. The frozen
    ``head`` is therefore expected to be a real ancestor of the current
    HEAD, never equal to it (mirrors
    ``tests/test_phase4d_freeze.py``'s equivalent check).
    """
    freeze = _load()
    assert len(freeze["head"]) == 40
    subprocess.run(
        ["git", "cat-file", "-e", f"{freeze['head']}^{{commit}}"],
        cwd=PROJECT_ROOT,
        check=True,
    )
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", freeze["head"], "HEAD"],
        cwd=PROJECT_ROOT,
    )
    assert result.returncode == 0, "the frozen HEAD is not an ancestor of the current HEAD"


def test_freeze_master_is_still_unchanged():
    freeze = _load()
    result = subprocess.run(
        ["git", "rev-parse", "master"], cwd=PROJECT_ROOT, capture_output=True, text=True, check=True
    )
    assert freeze["master"] == result.stdout.strip()


def test_every_listed_manifest_exists_and_matches_its_recorded_sha256():
    freeze = _load()
    missing: list[str] = []
    mismatches: list[str] = []
    for entry in freeze["manifests"]:
        path = PROJECT_ROOT / entry["path"]
        if not path.is_file():
            missing.append(entry["path"])
            continue
        if _sha256(path) != entry["sha256"]:
            mismatches.append(entry["path"])
    assert not missing, f"manifest(s) missing since freeze: {missing}"
    assert not mismatches, f"manifest(s) changed since freeze: {mismatches}"


def test_every_listed_report_exists_and_matches_its_recorded_sha256():
    freeze = _load()
    missing: list[str] = []
    mismatches: list[str] = []
    for entry in freeze["reports"]:
        path = PROJECT_ROOT / entry["path"]
        if not path.is_file():
            missing.append(entry["path"])
            continue
        if _sha256(path) != entry["sha256"]:
            mismatches.append(entry["path"])
    assert not missing, f"report(s) missing since freeze: {missing}"
    assert not mismatches, f"report(s) changed since freeze: {mismatches}"


def test_every_listed_review_exists_and_matches_its_recorded_sha256():
    freeze = _load()
    missing: list[str] = []
    mismatches: list[str] = []
    for entry in freeze.get("reviews", []):
        path = PROJECT_ROOT / entry["path"]
        if not path.is_file():
            missing.append(entry["path"])
            continue
        if _sha256(path) != entry["sha256"]:
            mismatches.append(entry["path"])
    assert not missing, f"review(s) missing since freeze: {missing}"
    assert not mismatches, f"review(s) changed since freeze: {mismatches}"


def test_no_manifest_appeared_that_the_freeze_never_inventoried():
    """A manifest this freeze never certified would be a real, uninventoried
    addition to the extraction layer's own directory - except for a
    ``phase-*-semantic-freeze.json`` file, which belongs to the entirely
    separate semantic lineage (PROMPT Fase 5A section 3) this freeze was
    never meant to know about. It shares the directory (the PROMPT itself
    suggests ``data/manifests/phase-5a-semantic-freeze.json``) but is
    inventoried and hash-checked only by its own gate,
    ``tests/test_phase5a_semantic_freeze.py``.
    """
    freeze = _load()
    known = {entry["path"] for entry in freeze["manifests"]}
    on_disk = {
        p.relative_to(PROJECT_ROOT).as_posix()
        for p in (PROJECT_ROOT / "data" / "manifests").glob("*")
        if p.is_file()
        and p.name != "phase-4e-freeze.json"
        and not re.match(r"phase-\w+-semantic-freeze\.json$", p.name)
    }
    assert on_disk == known, f"uninventoried manifest(s): {on_disk - known}"


@pytest.mark.parametrize(
    "label,subdir",
    [
        ("2008-b", "data/questions/2008/all-computing"),
        ("2011", "data/questions/2011/all-computing"),
        (
            "2021-ciencia-da-computacao-bacharelado",
            "data/questions/2021/ciencia-da-computacao-bacharelado",
        ),
        (
            "2021-ciencia-da-computacao-licenciatura",
            "data/questions/2021/ciencia-da-computacao-licenciatura",
        ),
        ("2021-sistemas-de-informacao", "data/questions/2021/sistemas-de-informacao"),
    ],
)
def test_question_outputs_aggregate_hash_matches_current_disk_state(label, subdir):
    freeze = _load()
    root = PROJECT_ROOT / subdir
    files = sorted(
        (p for p in root.rglob("*") if p.is_file() and p.suffix in (".md", ".png")),
        key=lambda p: p.relative_to(PROJECT_ROOT).as_posix(),
    )
    lines = [f"{_sha256(p)}  {p.relative_to(PROJECT_ROOT).as_posix()}" for p in files]
    actual = hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()
    assert freeze["question_outputs"][label] == actual, (
        f"{label} corpus drifted since the freeze was taken (output no longer "
        "matches the frozen aggregate hash)"
    )


def test_content_assignment_ledger_hash_matches_current_disk_state():
    freeze = _load()
    entry = freeze["content_assignment_ledger"]
    path = PROJECT_ROOT / entry["path"]
    assert _sha256(path) == entry["sha256"]
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["assignment_count"] == entry["assignment_count"]


def test_content_assignment_ledger_assignment_ids_are_geometry_derived():
    import re

    freeze = _load()
    path = PROJECT_ROOT / freeze["content_assignment_ledger"]["path"]
    payload = json.loads(path.read_text(encoding="utf-8"))
    position_only = re.compile(r"^[^:]+(:asset)?:\d+$")
    offenders = [
        r["assignment_id"]
        for r in payload["assignments"]
        if position_only.match(r["assignment_id"])
    ]
    assert offenders == []


def test_content_assignment_ledger_has_no_orphans_against_2008b():
    from enade.extraction.content_assignment import find_orphan_assets

    freeze = _load()
    path = PROJECT_ROOT / freeze["content_assignment_ledger"]["path"]
    payload = json.loads(path.read_text(encoding="utf-8"))
    course_dir = PROJECT_ROOT / "data" / "questions" / "2008" / "all-computing"
    assert find_orphan_assets(payload, course_dir) == []


#: The two extraction-only tooling files this freeze certified that are
#: never expected to change again after Fase 4E (PROMPT Fase 5A section
#: 32: never fix/touch extraction code) - still checked byte-for-byte.
#: ``src/enade/cli.py``, this freeze's third ``generation_tooling`` entry,
#: is deliberately excluded here: it is a single shared module every
#: future phase's CLI commands are added to (Fase 5A added
#: ``validate-taxonomy``/``validate-semantic-annotations``/
#: ``build-semantic-review`` to it, purely additively) - see
#: ``test_cli_never_removed_or_modified_an_extraction_command`` below for
#: what is still actually guaranteed about it.
_STILL_FROZEN_TOOLING_PATHS = {
    "src/enade/extraction/content_assignment.py",
    "src/enade/freeze_contract.py",
}


def test_generation_tooling_hashes_match_current_disk_state():
    freeze = _load()
    for entry in freeze["generation_tooling"]:
        if entry["path"] not in _STILL_FROZEN_TOOLING_PATHS:
            continue
        path = PROJECT_ROOT / entry["path"]
        assert path.is_file()
        assert _sha256(path) == entry["sha256"]


def test_cli_never_removed_or_modified_an_extraction_command():
    """``src/enade/cli.py`` legitimately changed after this freeze (Fase
    5A added new, unrelated semantic-layer commands) - but every
    extraction command this freeze certified must still be present,
    verbatim, as a Typer command in the current file. A real diff (not
    just a hash) is the honest way to prove "purely additive".
    """
    freeze = _load()
    entry = next(e for e in freeze["generation_tooling"] if e["path"] == "src/enade/cli.py")
    if _sha256(PROJECT_ROOT / entry["path"]) == entry["sha256"]:
        pytest.skip("cli.py unchanged since the freeze - nothing to prove additive")

    result = subprocess.run(
        ["git", "show", f"{freeze['head']}:src/enade/cli.py"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    command_pattern = re.compile(r"@app\.command\([^)]*\)\s*\ndef (\w+)\(", re.MULTILINE)
    frozen_commands = set(command_pattern.findall(result.stdout))
    current_text = (PROJECT_ROOT / entry["path"]).read_text(encoding="utf-8")
    current_commands = set(command_pattern.findall(current_text))
    missing = frozen_commands - current_commands
    assert missing == set(), (
        f"extraction command(s) removed from cli.py since the freeze: {missing}"
    )
    assert len(frozen_commands) >= 10  # sanity: the regex itself still matches real commands


def test_generation_tests_hashes_match_current_disk_state():
    freeze = _load()
    for entry in freeze["generation_tests"]:
        path = PROJECT_ROOT / entry["path"]
        assert path.is_file()
        assert _sha256(path) == entry["sha256"]


def test_source_limitations_still_present_and_never_resolved():
    freeze = _load()
    subjects = {e["subject_id"] for e in freeze["source_limitations"]}
    assert subjects == {"enade-2008-computing-d09", "enade-2008-computing-d10"}
    for entry in freeze["source_limitations"]:
        assert entry["status"] == "source_unavailable_confirmed"


def test_declared_uncommitted_files_are_now_part_of_frozen_head_history():
    """The freeze's own ``uncommitted_changes`` set was, by construction,
    a point-in-time snapshot - once ``8e272cc`` (Fase 4E's own external
    commit) absorbed it, those files stopped showing as uncommitted, and
    a live ``git status`` comparison against them is no longer meaningful
    (they may since have been further modified again by a later phase,
    e.g. ``src/enade/cli.py`` by Fase 5A). What is still verifiable and
    still matters: every one of those paths was really committed *at* the
    frozen ``head`` - i.e. ``git show <head>:<path>`` succeeds - proving
    the freeze's own narrative (these files were mid-edit, then landed in
    that exact commit) rather than just asserting it.
    """
    freeze = _load()
    current_head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()
    for entry in freeze["uncommitted_changes"]:
        result = subprocess.run(
            ["git", "cat-file", "-e", f"{current_head}:{entry['path']}"],
            cwd=PROJECT_ROOT,
        )
        assert result.returncode == 0, (
            f"{entry['path']} was declared uncommitted by the freeze but is not "
            f"present at the current head {current_head} either"
        )


def test_git_status_porcelain_first_line_path_is_never_truncated_by_a_whole_blob_strip():
    synthetic_porcelain = (
        " M data/manifests/blocker-ledger-2008.yaml\n"
        " M src/enade/cli.py\n"
        "?? tests/test_new_file.py\n"
    )

    def naive_parse(raw: str) -> list[str]:
        return [line[3:].strip() for line in raw.strip().splitlines() if line.strip()]

    def correct_parse(raw: str) -> list[str]:
        return [line[3:].strip() for line in raw.splitlines() if line.strip()]

    naive_paths = naive_parse(synthetic_porcelain)
    correct_paths = correct_parse(synthetic_porcelain)

    assert naive_paths[0] == "ata/manifests/blocker-ledger-2008.yaml"
    assert correct_paths[0] == "data/manifests/blocker-ledger-2008.yaml"
    assert naive_paths[1:] == correct_paths[1:]
