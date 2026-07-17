"""PR-124 typed theorem-signature registry (successor of the legacy v1
theorem registry).

The legacy registry ``docs/research_program/THEOREM_REGISTRY.yaml`` is
quarantined as a byte-stable reproduction surface for the frozen v9 report
lane: its byte hash is pinned here and active consumers must traverse this
typed successor instead.

The successor schema (``htt.theorem_registry.v2``) types every entry with:

- a pointer to its legacy id (every legacy id mapped exactly once);
- an evidence grade from the closed six-grade vocabulary
  (``published_proof`` / ``independent_derivation`` / ``checked_derivation``
  / ``numerical_test`` / ``sanity_anchor`` / ``specification``);
- a signature block (quantified variables, hypotheses, frame, perturbative
  order, domain) whose completeness is explicit: ``CHECKED`` or
  ``MIGRATION_PENDING``.

Counting rule (the derivation-lineage oracle's governance half):

- ``counts_toward_theorem_count`` is true ONLY for entries whose signature
  is CHECKED, whose evidence grade is one of {published_proof,
  independent_derivation, checked_derivation}, and whose legacy status is
  ACTIVE or ACTIVE_CONDITIONAL.
- sanity anchors, specifications, and numerical tests NEVER count; nor do
  SUPERSEDED/RETRACTED/WITHHELD/PLANNED entries; nor do MIGRATION_PENDING
  signatures. Re-evaluating one expression on a second engine never adds a
  derivation.
- All-parameter prose is generated only from CHECKED signatures; asking for
  it on any other entry raises.

This kills the historical overstatement in which the raw registry entry
count (65) was quotable as a "theorem count".
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Mapping, Sequence

import yaml

SCHEMA_VERSION = "htt.theorem_registry.v2"
LEGACY_REGISTRY_PATH = "docs/research_program/THEOREM_REGISTRY.yaml"
LEGACY_REGISTRY_SHA256 = (
    "266374abc05b179cf32e12020ced0624643f525cd42f8fcead05c9542c74f315"
)
SIGNATURES_V2_PATH = "docs/research_program/THEOREM_SIGNATURES_V2.yaml"

_LEGACY_STATUSES = frozenset(
    {"ACTIVE", "ACTIVE_CONDITIONAL", "SUPERSEDED", "RETRACTED", "WITHHELD",
     "PLANNED"}
)
_COUNTABLE_STATUSES = frozenset({"ACTIVE", "ACTIVE_CONDITIONAL"})


class TheoremSignatureError(ValueError):
    """Raised when the successor registry violates the v2 contract."""


class EvidenceGrade(str, Enum):
    PUBLISHED_PROOF = "published_proof"
    INDEPENDENT_DERIVATION = "independent_derivation"
    CHECKED_DERIVATION = "checked_derivation"
    NUMERICAL_TEST = "numerical_test"
    SANITY_ANCHOR = "sanity_anchor"
    SPECIFICATION = "specification"


COUNTABLE_GRADES = frozenset(
    {EvidenceGrade.PUBLISHED_PROOF, EvidenceGrade.INDEPENDENT_DERIVATION,
     EvidenceGrade.CHECKED_DERIVATION}
)


class SignatureStatus(str, Enum):
    CHECKED = "CHECKED"
    MIGRATION_PENDING = "MIGRATION_PENDING"


def _nonempty_str(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TheoremSignatureError(f"{field} must be a non-empty string")
    return value


def _str_list(value: object, field: str) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise TheoremSignatureError(f"{field} must be a list of strings")
    items = tuple(_nonempty_str(v, f"{field}[]") for v in value)
    if not items:
        raise TheoremSignatureError(f"{field} must be non-empty")
    return items


@dataclass(frozen=True)
class TheoremSignature:
    entry_id: str
    legacy_id: str
    title: str
    legacy_status: str
    evidence_grade: EvidenceGrade
    signature_status: SignatureStatus
    quantified_variables: tuple[str, ...]
    hypotheses: tuple[str, ...]
    frame: str
    perturbative_order: str
    domain: str
    grade_provenance: str
    sources: tuple[str, ...]

    @property
    def counts_toward_theorem_count(self) -> bool:
        return (
            self.signature_status is SignatureStatus.CHECKED
            and self.evidence_grade in COUNTABLE_GRADES
            and self.legacy_status in _COUNTABLE_STATUSES
        )

    def all_parameter_prose(self) -> str:
        """Render the all-parameter statement. CHECKED signatures only."""
        if self.signature_status is not SignatureStatus.CHECKED:
            raise TheoremSignatureError(
                f"{self.entry_id}: all-parameter prose may be generated only "
                "from a CHECKED signature (anti-drift rule)"
            )
        quantifier = ", ".join(self.quantified_variables)
        hypotheses = "; ".join(self.hypotheses)
        return (
            f"For all {quantifier} in domain [{self.domain}], under "
            f"hypotheses [{hypotheses}], in frame [{self.frame}] at order "
            f"[{self.perturbative_order}]: {self.title}."
        )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_legacy_registry(repo_root: Path) -> dict:
    """The legacy registry must exist and be byte-identical to the pin."""
    path = repo_root / LEGACY_REGISTRY_PATH
    if not path.is_file():
        raise TheoremSignatureError("legacy theorem registry missing")
    digest = sha256_file(path)
    if digest != LEGACY_REGISTRY_SHA256:
        raise TheoremSignatureError(
            "legacy theorem registry byte hash drifted: quarantine broken "
            f"(got {digest})"
        )
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    entries = data.get("entries")
    if not isinstance(entries, list) or not entries:
        raise TheoremSignatureError("legacy registry has no entries")
    return {
        "path": LEGACY_REGISTRY_PATH,
        "sha256": digest,
        "entry_count": len(entries),
        "entries": {str(e["id"]): e for e in entries},
    }


def _parse_entry(raw: Mapping, legacy: Mapping[str, Mapping]) -> TheoremSignature:
    entry_id = _nonempty_str(raw.get("id"), "id")
    legacy_id = _nonempty_str(raw.get("legacy_id"), f"{entry_id}.legacy_id")
    if legacy_id not in legacy:
        raise TheoremSignatureError(
            f"{entry_id}: legacy_id {legacy_id!r} not in the legacy registry"
        )
    legacy_entry = legacy[legacy_id]
    legacy_status = _nonempty_str(raw.get("legacy_status"),
                                  f"{entry_id}.legacy_status")
    if legacy_status not in _LEGACY_STATUSES:
        raise TheoremSignatureError(
            f"{entry_id}: unknown legacy status {legacy_status!r}"
        )
    if legacy_status != str(legacy_entry.get("status")):
        raise TheoremSignatureError(
            f"{entry_id}: legacy_status {legacy_status!r} does not match the "
            f"legacy registry ({legacy_entry.get('status')!r})"
        )
    try:
        grade = EvidenceGrade(str(raw.get("evidence_grade")))
    except ValueError as exc:
        raise TheoremSignatureError(
            f"{entry_id}: unknown evidence grade {raw.get('evidence_grade')!r}"
        ) from exc
    try:
        sig_status = SignatureStatus(str(raw.get("signature_status")))
    except ValueError as exc:
        raise TheoremSignatureError(
            f"{entry_id}: unknown signature status "
            f"{raw.get('signature_status')!r}"
        ) from exc

    signature = raw.get("signature")
    if sig_status is SignatureStatus.CHECKED:
        if not isinstance(signature, Mapping):
            raise TheoremSignatureError(
                f"{entry_id}: CHECKED entries need a full signature block"
            )
        quantified = _str_list(signature.get("quantified_variables"),
                               f"{entry_id}.quantified_variables")
        hypotheses = _str_list(signature.get("hypotheses"),
                               f"{entry_id}.hypotheses")
        frame = _nonempty_str(signature.get("frame"), f"{entry_id}.frame")
        order = _nonempty_str(signature.get("perturbative_order"),
                              f"{entry_id}.perturbative_order")
        domain = _nonempty_str(signature.get("domain"), f"{entry_id}.domain")
    else:
        if signature is not None:
            raise TheoremSignatureError(
                f"{entry_id}: MIGRATION_PENDING entries must not carry a "
                "partial signature block (type it fully or not at all)"
            )
        quantified = ("MIGRATION_PENDING",)
        hypotheses = ("MIGRATION_PENDING",)
        frame = "MIGRATION_PENDING"
        order = "MIGRATION_PENDING"
        domain = "MIGRATION_PENDING"

    return TheoremSignature(
        entry_id=entry_id,
        legacy_id=legacy_id,
        title=_nonempty_str(raw.get("title"), f"{entry_id}.title"),
        legacy_status=legacy_status,
        evidence_grade=grade,
        signature_status=sig_status,
        quantified_variables=quantified,
        hypotheses=hypotheses,
        frame=frame,
        perturbative_order=order,
        domain=domain,
        grade_provenance=_nonempty_str(raw.get("grade_provenance"),
                                       f"{entry_id}.grade_provenance"),
        sources=_str_list(raw.get("sources"), f"{entry_id}.sources"),
    )


@dataclass(frozen=True)
class SignatureRegistry:
    entries: tuple[TheoremSignature, ...]
    legacy_sha256: str
    legacy_entry_count: int

    def theorem_count(self) -> int:
        return sum(1 for e in self.entries if e.counts_toward_theorem_count)

    def countable_ids(self) -> tuple[str, ...]:
        return tuple(e.entry_id for e in self.entries
                     if e.counts_toward_theorem_count)

    def entry(self, entry_id: str) -> TheoremSignature:
        for e in self.entries:
            if e.entry_id == entry_id:
                return e
        raise TheoremSignatureError(f"unknown entry {entry_id!r}")

    def reject_overstated_count(self, claimed_count: int) -> None:
        """The old-overstatement negative gate: any claimed theorem count
        above the honest v2 count is rejected (the historical 65-entry
        quote fails here by construction)."""
        honest = self.theorem_count()
        if claimed_count > honest:
            raise TheoremSignatureError(
                f"claimed theorem count {claimed_count} exceeds the honest "
                f"v2 count {honest}: sanity anchors, specifications, "
                "numerical tests, superseded/retracted/withheld/planned "
                "entries, and unchecked signatures never count"
            )


def load_signature_registry(repo_root: Path) -> SignatureRegistry:
    legacy = verify_legacy_registry(repo_root)
    path = repo_root / SIGNATURES_V2_PATH
    if not path.is_file():
        raise TheoremSignatureError("THEOREM_SIGNATURES_V2.yaml missing")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, Mapping) or data.get("schema") != SCHEMA_VERSION:
        raise TheoremSignatureError(f"schema must be {SCHEMA_VERSION!r}")
    if str(data.get("legacy_registry_sha256")) != LEGACY_REGISTRY_SHA256:
        raise TheoremSignatureError(
            "successor registry pins a different legacy registry hash"
        )
    raw_entries = data.get("entries")
    if not isinstance(raw_entries, list) or not raw_entries:
        raise TheoremSignatureError("successor registry has no entries")

    legacy_entries: dict = legacy["entries"]
    entries = tuple(_parse_entry(raw, legacy_entries) for raw in raw_entries)

    seen: set[str] = set()
    mapped: set[str] = set()
    for e in entries:
        if e.entry_id in seen:
            raise TheoremSignatureError(f"duplicate entry id {e.entry_id!r}")
        seen.add(e.entry_id)
        if e.legacy_id in mapped:
            raise TheoremSignatureError(
                f"legacy id {e.legacy_id!r} mapped more than once"
            )
        mapped.add(e.legacy_id)
    missing = set(legacy_entries) - mapped
    if missing:
        raise TheoremSignatureError(
            f"legacy ids not mapped by the successor: {sorted(missing)}"
        )
    return SignatureRegistry(
        entries=entries,
        legacy_sha256=legacy["sha256"],
        legacy_entry_count=legacy["entry_count"],
    )
