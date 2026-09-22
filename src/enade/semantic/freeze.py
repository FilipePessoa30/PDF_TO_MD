"""Structural completeness contract for the semantic-layer freeze
(PROMPT Fase 5A section 30).

This is a deliberately SEPARATE lineage from the extraction freeze
(``data/manifests/phase-4e-freeze.json``, ``enade.freeze_contract``):
``phase-4e-freeze.json`` remains the terminal freeze of the extraction
layer - this module never edits it, never supersedes it, never produces
a ``phase-4f-freeze.json``. It only records a hash reference to it, so a
future reader can detect if the extraction layer's own frozen state ever
changed underneath the semantic layer.

Mirrors ``enade.freeze_contract``'s spirit (a freeze that fails this
check must never be promoted as the active semantic freeze) but with a
shape specific to the semantic artifacts this phase produces - never the
extraction freeze's own ``readiness``/``quality_gates`` shape, which does
not apply here.
"""

from __future__ import annotations

#: Every semantic freeze must name at least these artifacts, each with
#: its own {"path", "sha256"} - PROMPT section 30's explicit list
#: (taxonomia, anotacoes, selecao, diretrizes, pacote de revisao).
REQUIRED_ARTIFACT_KEYS = frozenset(
    {"taxonomy", "annotations", "pilot_selection", "guidelines", "review_packet"}
)

#: A semantic freeze may never claim the pilot was humanly approved
#: (PROMPT section 30: "nunca afirme que o piloto foi humanamente
#: aprovado") - enforced structurally by only ever allowing these values.
ALLOWED_HUMAN_REVIEW_STATUS = frozenset({"not_yet_reviewed"})


def validate_semantic_freeze_completeness(freeze: dict) -> list[str]:
    """Returns human-readable violations; an empty list means the freeze
    is structurally complete enough to be promoted to the active semantic
    freeze. Purely structural - never re-derives or second-guesses the
    verdicts themselves.
    """
    violations: list[str] = []

    if not freeze.get("head"):
        violations.append("head must be a non-empty commit hash")

    extraction_ref = freeze.get("extraction_freeze_reference")
    if not isinstance(extraction_ref, dict) or not extraction_ref.get("sha256"):
        violations.append(
            "extraction_freeze_reference must be a dict with a non-empty 'sha256' "
            "(hash of phase-4e-freeze.json at the time this freeze was built)"
        )

    artifacts = freeze.get("artifacts")
    if not isinstance(artifacts, dict) or not artifacts:
        violations.append("artifacts must be a non-empty dict")
    else:
        missing = REQUIRED_ARTIFACT_KEYS - set(artifacts)
        if missing:
            violations.append(f"artifacts missing required key(s): {sorted(missing)}")
        for name, entry in artifacts.items():
            if not isinstance(entry, dict) or not entry.get("sha256") or not entry.get("path"):
                violations.append(f"artifacts[{name!r}] must have non-empty 'path' and 'sha256'")

    counts = freeze.get("counts")
    if not isinstance(counts, dict) or not counts:
        violations.append("counts must be a non-empty dict")

    quality_gates = freeze.get("quality_gates")
    if not isinstance(quality_gates, dict) or not quality_gates:
        violations.append("quality_gates must be a non-empty dict")

    if not freeze.get("semantic_maturity"):
        violations.append("semantic_maturity must be a non-empty string")

    human_review_status = freeze.get("human_review_status")
    if human_review_status not in ALLOWED_HUMAN_REVIEW_STATUS:
        violations.append(
            f"human_review_status must be one of {sorted(ALLOWED_HUMAN_REVIEW_STATUS)} "
            f"(got: {human_review_status!r}) - this pilot has not been humanly reviewed"
        )

    return violations
