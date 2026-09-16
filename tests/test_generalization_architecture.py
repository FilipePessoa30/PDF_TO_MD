"""PROMPT Phase 3F - the generalization contract's own enforceable half.

A written contract (docs/generalization-contract.md) is only as good as an
automated check that keeps it true. This module is that check: it inspects
the actual source tree, not a description of it, so a future change that
reintroduces a year/question-ID/page-number branch into the core pipeline,
or a network/LLM dependency into the runtime path, fails a test rather than
silently drifting from what the contract promises.

Two invariants are covered, matching docs/generalization-contract.md
sections "Generalizacao do nucleo" and section 17 of the Phase 3F prompt
("teste sem IA em runtime"):

1. No core extraction module branches on a hardcoded year, question
   number/ID, or page number (year/hash/page are legitimate as plain
   *data* - a profile field, an override record, a CLI argument - but
   never as a condition inside the extraction logic itself).
2. No core extraction module imports a network or generative-AI client
   library, and the project's own declared runtime dependencies
   (pyproject.toml) contain none either.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

EXTRACTION_DIR = Path(__file__).parent.parent / "src" / "enade" / "extraction"
CAPABILITIES_PATH = (
    Path(__file__).parent.parent / "data" / "manifests" / "extraction-capabilities.json"
)

#: Files intentionally exempt from the "no year/ID/page branching" check -
#: each is the one legitimate place such a value exists as *data*, never as
#: a hidden central-logic condition. ``exam_profile.py`` declares ``year:
#: int`` and per-section applicable-course lists as plain profile fields;
#: ``layout_overrides.py`` declares ``page``/``pdf_sha256`` as plain fields
#: on a documented, evidenced override record (PROMPT section 5, "override
#: documental") - both are read, never branched on with a hardcoded
#: literal, but the AST check below cannot tell "field declaration" apart
#: from "comparison" as cheaply as an explicit exemption can, so these two
#: are inspected by the dedicated tests further down instead.
_EXEMPT_FROM_IDENTITY_BRANCH_CHECK = {"exam_profile.py", "layout_overrides.py"}

#: Attribute/name suffixes that, when compared against a literal with
#: ``==``/``!=``, indicate a hardcoded identity/year/page branch in central
#: logic - PROMPT Phase 3F section 8 ("proibicoes na logica central").
_IDENTITY_SUFFIXES = (
    "year",
    "question_id",
    "question_number",
    "page_number",
    "source_page",
)

#: Import names that would mean the core pipeline can reach a network or a
#: generative-AI service at runtime - PROMPT Phase 3F section 17 ("teste
#: sem IA em runtime"). Deliberately broad (matches by prefix on the
#: dotted module path) rather than an exhaustive enumeration of every SDK,
#: since the property being tested is "no such capability exists", not
#: "these particular fifteen packages are absent".
_FORBIDDEN_IMPORT_PREFIXES = (
    "openai",
    "anthropic",
    "google.generativeai",
    "cohere",
    "langchain",
    "llama_index",
    "transformers",
    "requests",
    "httpx",
    "urllib.request",
    "urllib3",
    "http.client",
    "socket",
    "grpc",
    "boto3",
    "botocore",
)


def _iter_core_source_files() -> list[Path]:
    return sorted(p for p in EXTRACTION_DIR.glob("*.py") if p.name != "__init__.py")


def _literal_value(node: ast.expr) -> object | None:
    if isinstance(node, ast.Constant):
        return node.value
    return None


def _identity_suffix_name(node: ast.expr) -> str | None:
    """The dotted-path suffix of ``node`` (e.g. "span.number" -> "number"),
    or ``None`` if it isn't a plain name/attribute access at all (a call
    result, a subscript, etc. - never what a hardcoded identity branch
    looks like).
    """
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Name):
        return node.id
    return None


def _find_identity_branches(tree: ast.AST, path: Path) -> list[str]:
    findings: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue
        if len(node.ops) != 1 or not isinstance(node.ops[0], (ast.Eq, ast.NotEq)):
            continue
        left, right = node.left, node.comparators[0]
        for value_side, literal_side in ((left, right), (right, left)):
            literal = _literal_value(literal_side)
            if literal is None or isinstance(literal, bool):
                continue
            suffix = _identity_suffix_name(value_side)
            if suffix is None:
                continue
            if suffix == "number" and not isinstance(literal, int):
                continue
            if any(suffix == s or suffix.endswith("_" + s) for s in _IDENTITY_SUFFIXES) or (
                suffix == "number" and isinstance(literal, int)
            ):
                findings.append(
                    f"{path.name}:{node.lineno}: comparison against identity-like field "
                    f"{suffix!r} (literal {literal!r}) - year/question/page identity must "
                    "never gate central extraction logic, only profiles/overrides/CLI args"
                )
    return findings


def test_core_extraction_modules_never_branch_on_hardcoded_identity():
    all_findings: list[str] = []
    for path in _iter_core_source_files():
        if path.name in _EXEMPT_FROM_IDENTITY_BRANCH_CHECK:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        all_findings.extend(_find_identity_branches(tree, path))
    assert not all_findings, "hardcoded identity branch(es) found in core logic:\n" + "\n".join(
        all_findings
    )


def test_exam_profile_year_field_is_plain_data_never_a_branch():
    """The one exemption above, verified directly rather than trusted
    blindly: ``year`` exists on ``ExamStructureProfile`` as a declared
    field, and nothing in the module compares it (or any other profile
    field) against a hardcoded literal.
    """
    path = EXTRACTION_DIR / "exam_profile.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    findings = _find_identity_branches(tree, path)
    assert not findings, findings


def test_layout_overrides_fields_are_plain_data_never_a_branch():
    """Same exemption, same direct verification, for the override
    record's own ``page``/``pdf_sha256`` fields (PROMPT section 5:
    legitimate only as declared, evidenced data on one override entry -
    matched against, never used as an ``if`` condition inside the parser).
    """
    path = EXTRACTION_DIR / "layout_overrides.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    findings = _find_identity_branches(tree, path)
    assert not findings, findings


def _iter_imports(tree: ast.AST) -> list[str]:
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
    return modules


def test_core_extraction_modules_import_no_network_or_llm_library():
    all_findings: list[str] = []
    for path in _iter_core_source_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for module in _iter_imports(tree):
            if any(
                module == prefix or module.startswith(prefix + ".")
                for prefix in _FORBIDDEN_IMPORT_PREFIXES
            ):
                all_findings.append(f"{path.name}: imports forbidden module {module!r}")
    assert not all_findings, "network/LLM import(s) found in core logic:\n" + "\n".join(
        all_findings
    )


def test_declared_runtime_dependencies_contain_no_llm_or_network_client():
    """PROMPT Phase 3F section 17: the project's own declared dependency
    list (pyproject.toml) - what actually gets installed at runtime - is
    itself free of any generative-AI or generic HTTP client library.
    Complements the import-based check above: that check can only catch a
    library actually *used* by the core; this one catches one merely
    *available* to be imported by mistake later.
    """
    pyproject = Path(__file__).parent.parent / "pyproject.toml"
    text = pyproject.read_text(encoding="utf-8")
    lowered = text.lower()
    for name in (
        "openai",
        "anthropic",
        "cohere",
        "langchain",
        "llama-index",
        "llama_index",
        "transformers",
        "google-generativeai",
    ):
        assert name not in lowered, f"forbidden dependency {name!r} declared in pyproject.toml"


# --- Capability registry (docs/generalization-contract.md, PROMPT section 7) --


_REQUIRED_CAPABILITY_FIELDS = {
    "capability_id",
    "description",
    "trigger_features",
    "parameters",
    "scope",
    "generalization_level",
    "positive_fixtures",
    "negative_fixtures",
    "real_cases",
    "protected_cases",
    "failure_behavior",
    "profile_dependency",
    "runtime_ai_dependency",
}
_VALID_GENERALIZATION_LEVELS = {"G0", "G1", "G2", "G3", "G4", "not_implemented"}


def _load_capabilities() -> list[dict[str, object]]:
    data = json.loads(CAPABILITIES_PATH.read_text(encoding="utf-8"))
    capabilities = data["capabilities"]
    assert isinstance(capabilities, list) and capabilities
    return capabilities


def test_capability_registry_entries_have_every_required_field():
    for entry in _load_capabilities():
        missing = _REQUIRED_CAPABILITY_FIELDS - entry.keys()
        assert not missing, f"{entry.get('capability_id')}: missing field(s) {missing}"


def test_capability_registry_generalization_levels_are_valid():
    for entry in _load_capabilities():
        assert entry["generalization_level"] in _VALID_GENERALIZATION_LEVELS, entry["capability_id"]


def test_capability_registry_declares_no_runtime_ai_dependency():
    """PROMPT section 7: every registered capability must explicitly state
    it has no generative-AI runtime dependency - the registry's own
    per-capability half of the no-LLM-runtime guarantee.
    """
    for entry in _load_capabilities():
        assert entry["runtime_ai_dependency"] == "none", entry["capability_id"]


def test_capability_registry_never_cites_a_question_id_as_a_trigger():
    """A capability's own trigger_features must describe an observable
    document characteristic (font size, geometry, a textual pattern) -
    never a specific question ID/number, which would make it G0 in
    disguise regardless of what generalization_level it claims.
    """
    import re

    id_like = re.compile(r"\bQ\d+\b|\bD\d+\b|question[_ ]?id", re.IGNORECASE)
    for entry in _load_capabilities():
        for feature in entry["trigger_features"]:
            assert not id_like.search(feature), (
                f"{entry['capability_id']}: trigger_features mentions a specific "
                f"question identity, not an observable characteristic: {feature!r}"
            )


# --- Phase 3L architecture preservation (PROMPT Phase 3M section 15) --------
#
# Phase 3L retired the page/hash-locked ``force_zoned_reading_order_page``
# override in favor of structural eligibility (reading_zones.assess_
# eligibility) computed only inside assembler._canonical_content_lines, on
# one question's own already-sliced span - never a whole page. These tests
# fail immediately, rather than letting a future edit silently drift, if
# that page/hash selector or a zoning parameter on a geometric consumer
# (figures.py/layout.py) is ever reintroduced.


def test_layout_overrides_has_no_page_hash_zoning_selector():
    """``LayoutOverrideSet.forces_zoned_reading_order`` (Phase 3K) was
    removed entirely in Phase 3L - no method on the override set may ever
    again select a page/hash for zone-aware reordering; that decision is
    now made purely from document structure, never a page/hash lookup.
    """
    path = EXTRACTION_DIR / "layout_overrides.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    method_names = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    }
    assert "forces_zoned_reading_order" not in method_names


def _function_param_names(tree: ast.AST, function_name: str) -> set[str]:
    params: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            args = node.args
            for arg in (*args.posonlyargs, *args.args, *args.kwonlyargs):
                params.add(arg.arg)
    return params


def test_geometric_consumers_accept_no_zoning_parameter():
    """``figures.detect_visual_regions`` and ``layout.extract_page_lines``/
    ``extract_document_lines`` must never again accept a zoning-related
    parameter (``zoned_reading_order_gate``/``_mode`` or similar) - region/
    label detection and document-level boundary detection are always fed
    the stable, page-wide geometric order; the zone-aware reorder is
    consulted only from ``assembler._canonical_content_lines``, on one
    question's own already-sliced span (see reading_zones.py's own module
    docstring, "PageLineViews" separation).
    """
    targets = [
        (EXTRACTION_DIR / "figures.py", "detect_visual_regions"),
        (EXTRACTION_DIR / "layout.py", "extract_page_lines"),
        (EXTRACTION_DIR / "layout.py", "extract_document_lines"),
    ]
    findings: list[str] = []
    for path, func_name in targets:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        params = _function_param_names(tree, func_name)
        zoning_params = {p for p in params if "zon" in p.lower()}
        if zoning_params:
            findings.append(
                f"{path.name}::{func_name} accepts zoning parameter(s): {zoning_params}"
            )
    assert not findings, "\n".join(findings)


def test_only_assembler_module_imports_reading_zones():
    """``reading_zones`` (the zone-aware reorder) is consulted from exactly
    one module - ``assembler.py`` - never from ``figures.py``/``layout.py``/
    ``pipeline.py``'s own document-level or table-rendering line extraction,
    which must always see the stable, page-wide order (PROMPT Phase 3L
    section D/H's own regression: threading a zone-aware order into any of
    those regressed dozens of already-correct 2008-b pages, since their own
    label-absorption/boundary logic uses list *position* as an implicit
    geometric proxy).
    """
    importers: list[str] = []
    for path in _iter_core_source_files():
        if path.name == "reading_zones.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        if any(module.endswith("reading_zones") for module in _iter_imports(tree)):
            importers.append(path.name)
    assert importers == ["assembler.py"], importers
