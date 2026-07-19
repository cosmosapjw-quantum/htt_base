"""PR-169 exact unsigned-leakage algebra and physical-promotion firewall.

The registered comparator is

``x_C = Sigma2 - V2 + Omega_tilt + DeltaOmega_k``

where ``V2`` is normalized vorticity squared (historically named ``W2`` in
the repository).  It is deliberately distinct from the Nilsson et al.
normalized Weyl-curvature variable ``W_N2``.

This module proves no Einstein-matter solution.  It provides exact rational
fixtures, typed receipt coherence, and total terminal routing.  A four-axis
algebraic PASS with any missing physical receipt terminates as
``algebraic_only``; CAS agreement cannot manufacture physical premises.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from typing import Iterable, Mapping, Sequence


SCHEMA_VERSION = "htt.pr169.unsigned_isotropy_leakage.v1"
REQUIRED_PHYSICAL_GATES = (
    "PHYS-G1-CONVENTIONS",
    "PHYS-G2-EXACT-MODEL-MAP",
    "PHYS-G3-CONSTRAINT-CLOSURE",
    "PHYS-G4-VORTICITY-TILT-COMPATIBILITY",
    "PHYS-G5-MATTER-DOMAIN",
    "PHYS-G6-DYNAMICAL-EXISTENCE",
    "PHYS-G7-COMPARATOR-SATURATION",
    "PHYS-G8-PROVENANCE-AND-INDEPENDENCE",
)
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class UnsignedLeakageError(ValueError):
    """Raised when a comparator or promotion contract fails closed."""


class ReceiptStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    MISSING = "MISSING"


class ProcessGateStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"


class ScientificResult(str, Enum):
    CONSTRUCTIVE = "constructive_constraint_and_admissibility_conditional"
    ALGEBRAIC_ONLY = "algebraic_only"
    NONE = "none"


class QuadraticSectorSymbol(str, Enum):
    V2 = "V2_normalized_vorticity_squared"
    W_N2 = "W_N2_normalized_weyl_curvature_squared"


def _fraction(value: object) -> Fraction:
    try:
        return Fraction(value)
    except (TypeError, ValueError, ZeroDivisionError) as exc:
        raise UnsignedLeakageError(f"not an exact rational: {value!r}") from exc


def _require_sha256(value: str, field: str) -> None:
    if not _SHA256.fullmatch(value):
        raise UnsignedLeakageError(f"{field} must be a lowercase SHA-256")


@dataclass(frozen=True)
class ComparatorPoint:
    """One exact point of the PR-126/127 comparator carrier."""

    sigma2: Fraction
    v2: Fraction
    omega_tilt: Fraction
    delta_omega_k: Fraction

    def __post_init__(self) -> None:
        for name in ("sigma2", "v2", "omega_tilt", "delta_omega_k"):
            object.__setattr__(self, name, _fraction(getattr(self, name)))
        for name in ("sigma2", "v2", "omega_tilt"):
            if getattr(self, name) < 0:
                raise UnsignedLeakageError(f"{name} must be nonnegative")

    def x_c(self) -> Fraction:
        return self.sigma2 - self.v2 + self.omega_tilt + self.delta_omega_k

    def m_unsigned(self) -> Fraction:
        return self.sigma2 + self.v2 + self.omega_tilt + abs(self.delta_omega_k)

    def inside_cap(self, cap: Fraction) -> bool:
        bound = _fraction(cap)
        if bound <= 0:
            raise UnsignedLeakageError("cap B must be positive")
        return (
            self.sigma2 <= bound
            and self.v2 <= bound
            and self.omega_tilt <= bound
            and abs(self.delta_omega_k) <= bound
        )

    def as_payload(self) -> dict[str, str]:
        return {
            "Sigma2": str(self.sigma2),
            "V2": str(self.v2),
            "Omega_tilt": str(self.omega_tilt),
            "DeltaOmega_k": str(self.delta_omega_k),
            "x_C": str(self.x_c()),
            "M_unsigned": str(self.m_unsigned()),
        }


def full_saturating_point(cap: Fraction) -> ComparatorPoint:
    bound = _fraction(cap)
    if bound <= 0:
        raise UnsignedLeakageError("cap B must be positive")
    return ComparatorPoint(bound, bound, bound, -bound)


def slice_saturating_point(cap: Fraction) -> ComparatorPoint:
    bound = _fraction(cap)
    if bound <= 0:
        raise UnsignedLeakageError("cap B must be positive")
    return ComparatorPoint(bound, bound, 0, 0)


def uncapped_cancellation_point(a: Fraction) -> ComparatorPoint:
    amplitude = _fraction(a)
    if amplitude <= 0:
        raise UnsignedLeakageError("uncapped family amplitude a must be positive")
    return ComparatorPoint(amplitude, amplitude, 0, 0)


def exact_ceiling_receipt(cap: Fraction = Fraction(3, 10)) -> dict[str, object]:
    """Return the registered exact fixture receipt.

    Universal upper-bound and attainment proofs are owned by the four-axis CAS
    contract.  This function independently exercises the exact production
    objects at the shared rational fixture.
    """

    bound = _fraction(cap)
    full = full_saturating_point(bound)
    sliced = slice_saturating_point(bound)
    uncapped = uncapped_cancellation_point(bound)
    if not full.inside_cap(bound) or not sliced.inside_cap(bound):
        raise UnsignedLeakageError("registered saturation fixture left the cap")
    if full.x_c() != 0 or full.m_unsigned() != 4 * bound:
        raise UnsignedLeakageError("full saturation fixture failed")
    if sliced.x_c() != 0 or sliced.m_unsigned() != 2 * bound:
        raise UnsignedLeakageError("slice saturation fixture failed")
    if uncapped.x_c() != 0 or uncapped.m_unsigned() != 2 * bound:
        raise UnsignedLeakageError("uncapped cancellation fixture failed")
    return {
        "schema": "htt.pr169.exact_ceiling_receipt.v1",
        "scalar_domain": "exact_ordered_rationals",
        "cap_B": str(bound),
        "full_ceiling": str(4 * bound),
        "slice_ceiling": str(2 * bound),
        "full_fixture": full.as_payload(),
        "slice_fixture": sliced.as_payload(),
        "uncapped_family_fixture": uncapped.as_payload(),
        "universal_claims_require_four_axis_cas": True,
        "physical_model_claim": False,
    }


def sign_mutant_x_c(point: ComparatorPoint) -> Fraction:
    """Registered mutant replacing ``-V2`` by ``+V2``."""

    return point.sigma2 + point.v2 + point.omega_tilt + point.delta_omega_k


def clip_signed_curvature(point: ComparatorPoint) -> ComparatorPoint:
    """Registered forbidden projection mutant for test purposes only."""

    return ComparatorPoint(
        point.sigma2,
        point.v2,
        point.omega_tilt,
        max(point.delta_omega_k, Fraction(0)),
    )


def require_typed_symbol_bridge(
    source: QuadraticSectorSymbol,
    target: QuadraticSectorSymbol,
    *,
    exact_derivation_sha256: str | None,
) -> dict[str, str]:
    """Require a content-addressed derivation for any cross-symbol bridge."""

    source = QuadraticSectorSymbol(source)
    target = QuadraticSectorSymbol(target)
    if source == target:
        return {"source": source.value, "target": target.value, "status": "IDENTITY"}
    if exact_derivation_sha256 is None:
        raise UnsignedLeakageError(
            "cross-symbol bridge is missing an exact-model derivation; "
            "Nilsson W_N2 cannot be substituted for repository V2"
        )
    _require_sha256(exact_derivation_sha256, "exact_derivation_sha256")
    return {
        "source": source.value,
        "target": target.value,
        "status": "DERIVED_EXTERNAL_BRIDGE_REQUIRES_PHYSICAL_BUNDLE",
        "exact_derivation_sha256": exact_derivation_sha256,
    }


@dataclass(frozen=True)
class PromotionCoherenceKey:
    model_id: str
    model_version: str
    witness_id: str
    state_hash: str
    convention_hash: str
    source_hashes: tuple[str, ...]
    pr169_contract_hash: str

    def __post_init__(self) -> None:
        for field in ("model_id", "model_version", "witness_id"):
            if not str(getattr(self, field)).strip():
                raise UnsignedLeakageError(f"{field} must be nonempty")
        _require_sha256(self.state_hash, "state_hash")
        _require_sha256(self.convention_hash, "convention_hash")
        _require_sha256(self.pr169_contract_hash, "pr169_contract_hash")
        if not self.source_hashes:
            raise UnsignedLeakageError("source_hashes must be nonempty")
        for value in self.source_hashes:
            _require_sha256(value, "source_hashes entry")

    def as_payload(self) -> dict[str, object]:
        return {
            "model_id": self.model_id,
            "model_version": self.model_version,
            "witness_id": self.witness_id,
            "state_hash": self.state_hash,
            "convention_hash": self.convention_hash,
            "source_hashes": list(self.source_hashes),
            "pr169_contract_hash": self.pr169_contract_hash,
        }


@dataclass(frozen=True)
class PhysicalPromotionReceipt:
    gate_id: str
    status: ReceiptStatus
    coherence_key: PromotionCoherenceKey
    evidence_hashes: tuple[str, ...]
    issuer: str
    evidence_class: str

    def __post_init__(self) -> None:
        if self.gate_id not in REQUIRED_PHYSICAL_GATES:
            raise UnsignedLeakageError(f"unknown physical gate {self.gate_id!r}")
        object.__setattr__(self, "status", ReceiptStatus(self.status))
        if not self.issuer.strip() or self.issuer == "self_asserted":
            raise UnsignedLeakageError("physical receipt issuer is missing or self-asserted")
        if self.evidence_class == "comparator_level":
            raise UnsignedLeakageError(
                "comparator-level evidence cannot satisfy a physical receipt"
            )
        if self.status is ReceiptStatus.PASS and not self.evidence_hashes:
            raise UnsignedLeakageError("PASS receipt requires evidence hashes")
        for value in self.evidence_hashes:
            _require_sha256(value, "evidence_hashes entry")


def adjudicate_physical_bundle(
    receipts: Sequence[PhysicalPromotionReceipt],
    *,
    expected_key: PromotionCoherenceKey | None = None,
) -> dict[str, object]:
    """Adjudicate all eight same-state physical receipts without defaults."""

    rows = list(receipts)
    by_gate: dict[str, PhysicalPromotionReceipt] = {}
    duplicates: list[str] = []
    mixed_coherence: list[str] = []
    for receipt in rows:
        if receipt.gate_id in by_gate:
            duplicates.append(receipt.gate_id)
        else:
            by_gate[receipt.gate_id] = receipt
        if expected_key is not None and receipt.coherence_key != expected_key:
            mixed_coherence.append(receipt.gate_id)
    missing = sorted(set(REQUIRED_PHYSICAL_GATES) - set(by_gate))
    failed = sorted(
        gate for gate, receipt in by_gate.items()
        if receipt.status is not ReceiptStatus.PASS
    )
    if duplicates or mixed_coherence:
        bundle_status = ReceiptStatus.FAIL
    elif missing:
        bundle_status = ReceiptStatus.MISSING
    elif failed:
        bundle_status = ReceiptStatus.FAIL
    else:
        keys = {receipt.coherence_key for receipt in rows}
        bundle_status = ReceiptStatus.PASS if len(keys) == 1 else ReceiptStatus.FAIL
        if len(keys) != 1:
            mixed_coherence = sorted(by_gate)
    result = (
        ScientificResult.CONSTRUCTIVE
        if bundle_status is ReceiptStatus.PASS
        else ScientificResult.ALGEBRAIC_ONLY
    )
    return {
        "schema": "htt.pr169.physical_promotion_bundle.v1",
        "required_gate_ids": list(REQUIRED_PHYSICAL_GATES),
        "received_gate_ids": sorted(by_gate),
        "missing_gate_ids": missing,
        "failed_gate_ids": failed,
        "duplicate_gate_ids": sorted(set(duplicates)),
        "mixed_coherence_gate_ids": sorted(set(mixed_coherence)),
        "bundle_status": bundle_status.value,
        "scientific_result_if_cas_passes": result.value,
        "constructive_promotion_allowed": bundle_status is ReceiptStatus.PASS,
    }


def classify_pr127_evidence(label: str, level: str | None) -> str:
    """Prevent PR-127's historical bare ``physical`` label from promotion."""

    if label == "physical" and level == "A_C_comparator_level":
        return "comparator_level_physical_not_pr169_admissible"
    return "algebraic_only_not_pr169_admissible"


def route_terminal_result(
    cas_status: str,
    physical_bundle_status: str,
    *,
    semantic_gate_pass: bool,
    artifact_gate_pass: bool,
) -> dict[str, str | bool]:
    """Total process/science routing with failure precedence."""

    if not semantic_gate_pass or not artifact_gate_pass:
        process = ProcessGateStatus.FAIL
        result = ScientificResult.NONE
    elif cas_status in {"CAS_BLOCKED", "CAS_CONFLICT"}:
        process = ProcessGateStatus.BLOCKED
        result = ScientificResult.NONE
    elif cas_status != "CAS_4AXIS_PASS":
        process = ProcessGateStatus.FAIL
        result = ScientificResult.NONE
    elif physical_bundle_status == ReceiptStatus.PASS.value:
        process = ProcessGateStatus.PASS
        result = ScientificResult.CONSTRUCTIVE
    elif physical_bundle_status in {
        ReceiptStatus.FAIL.value,
        ReceiptStatus.MISSING.value,
    }:
        process = ProcessGateStatus.PASS
        result = ScientificResult.ALGEBRAIC_ONLY
    else:
        process = ProcessGateStatus.FAIL
        result = ScientificResult.NONE
    return {
        "process_gate_status": process.value,
        "scientific_result": result.value,
        "accepted": process is ProcessGateStatus.PASS,
        "public_use": False,
    }


def require_no_unresolved_consumer_hits(
    records: Iterable[Mapping[str, object]],
) -> None:
    unresolved = [
        str(row.get("path", "<unknown>"))
        for row in records
        if row.get("classification") in {"active_claim", "unclassified"}
        and row.get("disposition") != "remediated"
    ]
    if unresolved:
        raise UnsignedLeakageError(
            f"unresolved PR-169 consumer claims remain: {sorted(unresolved)}"
        )

