"""Structural completeness contract for pilot pre-commit freeze manifests
(``data/manifests/phase-*-freeze.json``) - PROMPT Fase 4E, hardening
finding F7.

``phase-4c-freeze.json`` was promoted to "active freeze" with its own
``readiness``/``quality_gates`` fields left as empty placeholder dicts
(``{}``) - never filled in with the real verdicts the phase itself had
already produced. Nothing enforced that a freeze claiming to certify a
phase's own gates must actually *contain* their results before being
trusted as the active one. This module is the general, reusable check
that closes that gap for every *future* freeze - it is never applied
retroactively to ``phase-4c-freeze.json`` itself, which remains a
historical snapshot, preserved exactly as it was (PROMPT: "vale para
freezes futuros, nao retroativamente para 4C").

A freeze that fails this check must never be promoted to the active one.
"""

from __future__ import annotations

#: Every readiness entry (one per target, e.g. "2008-b") must carry at
#: least these fields - the same shape ``enade assess-readiness`` itself
#: has always printed (PROMPT Phase 1C section 14) - or a reader has no
#: way to tell whether an empty-looking entry means "ready with nothing
#: to report" or "never actually recorded".
REQUIRED_READINESS_FIELDS = frozenset(
    {"verdict", "actionable_blockers", "source_limitations", "informational_findings"}
)


def validate_freeze_completeness(freeze: dict) -> list[str]:
    """Returns human-readable violations; an empty list means the freeze
    is structurally complete enough to be promoted to the active one.

    Checks only *structural* completeness (the fields exist and are
    non-empty with the right shape) - never re-derives or second-guesses
    the actual verdicts themselves, which is the freeze generator's own
    job, not this contract's.
    """
    violations: list[str] = []

    readiness = freeze.get("readiness")
    if not isinstance(readiness, dict) or not readiness:
        violations.append(f"readiness must be a non-empty dict (got: {readiness!r})")
    else:
        for target, entry in readiness.items():
            if not isinstance(entry, dict):
                violations.append(f"readiness[{target!r}] must be a dict")
                continue
            missing = REQUIRED_READINESS_FIELDS - set(entry)
            if missing:
                violations.append(f"readiness[{target!r}] missing field(s): {sorted(missing)}")

    quality_gates = freeze.get("quality_gates")
    if not isinstance(quality_gates, dict) or not quality_gates:
        violations.append(f"quality_gates must be a non-empty dict (got: {quality_gates!r})")

    return violations
