"""Machine-readable source-availability adjudication (PROMPT Fase 3Z).

Distinct from ``blocker_ledger.py``'s own ``source_unavailable`` status
(Fase 3T): that status is a single terminal label on a ``Blocker`` entry,
backed only by a free-text ``evidence`` string - sufficient to stop the
blocker itself from being reopened, but not itself a structured record a
readiness gate can mechanically re-verify. This module is the structured
evidence *behind* that label: a ``SourceAvailabilityRecord`` names exactly
which pages were scanned, which search methods were used, and what each
one found (or did not find) - so a future reader (or gate) never has to
re-parse a narrative paragraph to know whether the negative search was
actually exhaustive.

The central discipline this module exists to enforce (PROMPT Section 9,
"nao repetir o erro de D59"): 2008-b's own D59 answer standard was, for
three phases, wrongly treated as absent because its rubric had zero
extractable *text* - the rubric was a real, embedded raster image the
whole time, simply never searched for. A ``source_unavailable_confirmed``
verdict must never rest on a text-only (or even text+rawdict) search
again - ``is_confirmed_unavailable`` refuses to trust that label unless
the record's own ``search_methods`` cover text, rawdict, texttrace,
images, *and* drawings, with each of ``text_evidence``/``image_evidence``/
``drawing_evidence`` independently populated (an empty string is not
"checked, nothing found" - it is "not checked", which must never
silently pass this gate).
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

from enade.inventory.pdfmeta import sha256_of_file

SourceAvailabilityStatus = Literal[
    "available_and_extracted",
    "available_but_not_extracted",
    "source_unavailable_confirmed",
    "source_ambiguous",
    "source_not_checked",
    "source_hash_mismatch",
]

#: Every one of these must appear in a record's own ``search_methods``
#: before it may ever be trusted as ``source_unavailable_confirmed`` (see
#: ``is_confirmed_unavailable``) - text/rawdict alone (Fase 3T's own
#: original D09/D10 evidence) is exactly the gap the D59 lesson (module
#: docstring) requires closing.
REQUIRED_SEARCH_METHODS: frozenset[str] = frozenset(
    {"text", "rawdict", "texttrace", "images", "drawings"}
)


class SourceDocument(BaseModel):
    """One physical file inside a :class:`SourcePackage` (PROMPT Section 7)."""

    model_config = ConfigDict(extra="forbid")

    path: str = Field(..., min_length=1)
    sha256: str = Field(..., min_length=64, max_length=64)
    role: str = Field(..., min_length=1)
    page_count: int = Field(..., ge=1)
    acquisition_provenance: str = Field(..., min_length=1)


class SourcePackage(BaseModel):
    """The formal boundary of one exam booklet's own official documental
    package (PROMPT Section 7) - what ``source_unavailable_confirmed``
    is scoped against. Never claims "absent from anywhere in the world",
    only "absent from this exact, hash-locked set of files".
    """

    model_config = ConfigDict(extra="forbid")

    source_package_id: str = Field(..., min_length=1)
    documents: list[SourceDocument] = Field(default_factory=list)
    coverage_claim: str = Field(..., min_length=1)


class SourceAvailabilityRecord(BaseModel):
    """One subject/artifact's own documented availability adjudication
    (PROMPT Section 10). ``availability_status`` is a claim; whether that
    claim may be *trusted* by a gate is a separate question, answered by
    ``is_confirmed_unavailable`` below - never by reading this field alone.
    """

    model_config = ConfigDict(extra="forbid")

    source_availability_id: str = Field(..., min_length=1)
    subject_id: str = Field(..., min_length=1)
    artifact_type: str = Field(..., min_length=1)
    source_package_id: str = Field(..., min_length=1)
    expected_source: str = Field(..., min_length=1)
    #: Keyed by document role or path (matches ``SourceDocument`` entries
    #: in the referenced package) - kept alongside the record itself so a
    #: record's own claim is self-contained even if the package
    #: definition later changes.
    source_hashes: dict[str, str] = Field(default_factory=dict)
    pages_scanned: list[int] = Field(default_factory=list)
    search_methods: list[str] = Field(default_factory=list)
    expected_markers: list[str] = Field(default_factory=list)
    observed_markers: list[str] = Field(default_factory=list)
    text_evidence: str = ""
    image_evidence: str = ""
    drawing_evidence: str = ""
    availability_status: SourceAvailabilityStatus
    review_status: str = Field(..., min_length=1)
    impact: str = Field(..., min_length=1)
    evidence: str = Field(..., min_length=1)


class SourceAvailabilityLedger(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int = 1
    source_packages: list[SourcePackage] = Field(default_factory=list)
    records: list[SourceAvailabilityRecord] = Field(default_factory=list)

    def package_by_id(self, package_id: str) -> SourcePackage | None:
        return next((p for p in self.source_packages if p.source_package_id == package_id), None)

    def record_by_subject(
        self, subject_id: str, artifact_type: str | None = None
    ) -> SourceAvailabilityRecord | None:
        for record in self.records:
            if record.subject_id != subject_id:
                continue
            if artifact_type is not None and record.artifact_type != artifact_type:
                continue
            return record
        return None


def load_source_availability(path: Path) -> SourceAvailabilityLedger:
    """Read ``path``, or return an empty ledger if it does not exist -
    never an error, mirroring ``visual_audit.load_visual_audit`` (running
    the pipeline/readiness gate before any source-availability adjudication
    has happened is not a hard requirement).
    """
    if not path.exists():
        return SourceAvailabilityLedger()
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return SourceAvailabilityLedger.model_validate(raw)


class SourceAvailabilityIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: str
    detail: str


def is_confirmed_unavailable(
    record: SourceAvailabilityRecord, ledger: SourceAvailabilityLedger
) -> bool:
    """The completeness gate (PROMPT Sections 10/14/19): a record's own
    ``availability_status`` label is never trusted by itself. Every one of
    the following must hold, or this returns ``False`` (never raises) -
    the caller's own safe default is then "still blocking", never a
    waiver granted by omission:

    - status is literally ``source_unavailable_confirmed``;
    - ``review_status`` is ``"reviewed"`` (an unreviewed record can never
      grant a waiver, regardless of how complete its evidence looks);
    - the referenced :class:`SourcePackage` actually exists, and it
      contains a document whose own ``path`` matches ``expected_source``;
    - ``pages_scanned`` covers *every* page of that document, 1 through
      its own declared ``page_count`` - no gap, and no extra/duplicate
      entries either (PROMPT Section 19: "lista incompleta de paginas
      verificadas" must block the waiver, not just an empty list);
    - ``search_methods`` covers text, rawdict, texttrace, images, *and*
      drawings (``REQUIRED_SEARCH_METHODS`` - the D59 lesson, module
      docstring: a text-only search is never sufficient);
    - ``text_evidence``, ``image_evidence`` and ``drawing_evidence`` are
      each non-empty (an empty string means "not checked", never
      "checked, found nothing");
    - ``evidence`` (the full narrative) and ``source_hashes`` are present.
    """
    if record.availability_status != "source_unavailable_confirmed":
        return False
    if record.review_status != "reviewed":
        return False
    package = ledger.package_by_id(record.source_package_id)
    if package is None:
        return False
    document = next((d for d in package.documents if d.path == record.expected_source), None)
    if document is None:
        return False
    if set(record.pages_scanned) != set(range(1, document.page_count + 1)):
        return False
    if not REQUIRED_SEARCH_METHODS.issubset(set(record.search_methods)):
        return False
    if not record.text_evidence.strip():
        return False
    if not record.image_evidence.strip():
        return False
    if not record.drawing_evidence.strip():
        return False
    if not record.evidence.strip():
        return False
    return bool(record.source_hashes)


def verify_source_hashes_match(
    record: SourceAvailabilityRecord, ledger: SourceAvailabilityLedger, corpus_root: Path
) -> SourceAvailabilityIssue | None:
    """Section 18/19 - reversibility and tamper protection: re-hashes every
    document in the record's own referenced package against what is
    *actually* on disk right now. A waiver is scoped to one exact,
    hash-locked source; if that file has since been replaced (a corrected
    or newly-supplied document with the same name), the waiver must never
    continue to silently apply - this is what makes the policy reversible
    rather than a one-way, permanent exemption.

    Returns ``None`` when everything matches; a :class:`SourceAvailabilityIssue`
    otherwise (missing package, missing file, or hash mismatch) - the
    caller treats any non-``None`` result as "this waiver no longer
    applies, the subject reverts to blocking".
    """
    package = ledger.package_by_id(record.source_package_id)
    if package is None:
        return SourceAvailabilityIssue(
            kind="source_package_missing",
            detail=f"{record.source_availability_id}: no package {record.source_package_id!r}",
        )
    for doc in package.documents:
        doc_path = corpus_root / doc.path
        if not doc_path.exists():
            return SourceAvailabilityIssue(
                kind="source_document_missing",
                detail=(
                    f"{record.source_availability_id}: {doc.path} not found under {corpus_root}"
                ),
            )
        current_hash = sha256_of_file(doc_path)
        if current_hash != doc.sha256:
            return SourceAvailabilityIssue(
                kind="source_hash_mismatch",
                detail=(
                    f"{record.source_availability_id}: {doc.path} hash changed "
                    f"({doc.sha256} -> {current_hash}) - a source_unavailable_confirmed "
                    "waiver against the old file no longer applies"
                ),
            )
    return None
