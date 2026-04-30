"""Adversarial publication-claim readiness gates.

These helpers intentionally separate executable code paths from claims that
would appear in a paper abstract or release note. They are not documentation
labels: each decision is derived from family readiness, gate status, and output
metadata that the runtime already produces.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Any, Mapping

from bass.background.bianchi_types import ALL_BIANCHI_TYPES, TYPE_REGISTRY
from bass.forward.ver3_output_archive import validate_alm_archive
from bass.hierarchy.seed_factory import (
    RESIDUAL_BACKED_FAMILIES,
    STRONG_FAMILIES,
    TEMPLATE_CARD_FAMILIES,
)
from bass.los.family_backend_protocol import family_backend_status
from bass.validation.ver3_gate_stop import hard_gate_before_fitting

__all__ = [
    "FamilyReadinessRow",
    "PublicationClaimDecision",
    "PublicationClaimError",
    "build_family_readiness_manifest",
    "evaluate_publication_claim",
    "assert_publication_claim_allowed",
]


class PublicationClaimError(RuntimeError):
    """Raised when a headline claim is requested without evidence."""


@dataclass(frozen=True)
class FamilyReadinessRow:
    family: str
    registry_exists: bool
    background_ready: bool
    backend_status: str
    backend_evidence_status: str
    backend_evidence_passed: bool
    ic_status: str
    perturbation_ready: bool
    output_ready: bool
    statistics_usable: bool
    residual_evidence: Mapping[str, Any] = field(default_factory=dict)
    block_reasons: tuple[str, ...] = ()

    def as_payload(self) -> dict[str, Any]:
        return {
            "family": self.family,
            "registry_exists": bool(self.registry_exists),
            "background_ready": bool(self.background_ready),
            "backend_status": self.backend_status,
            "backend_evidence_status": self.backend_evidence_status,
            "backend_evidence_passed": bool(self.backend_evidence_passed),
            "ic_status": self.ic_status,
            "perturbation_ready": bool(self.perturbation_ready),
            "output_ready": bool(self.output_ready),
            "statistics_usable": bool(self.statistics_usable),
            "residual_evidence": dict(self.residual_evidence),
            "block_reasons": list(self.block_reasons),
        }


@dataclass(frozen=True)
class PublicationClaimDecision:
    claim_id: str
    allowed: bool
    evidence: Mapping[str, Any] = field(default_factory=dict)
    blockers: tuple[str, ...] = ()

    def as_payload(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "allowed": bool(self.allowed),
            "evidence": dict(self.evidence),
            "blockers": list(self.blockers),
        }


def _family_ic_status(family: str) -> str:
    if family in STRONG_FAMILIES:
        return "strong"
    if family in RESIDUAL_BACKED_FAMILIES:
        return "residual-backed"
    if family in TEMPLATE_CARD_FAMILIES:
        return "template-card"
    return "unknown"


def _residual_payload(value: object) -> dict[str, Any]:
    if hasattr(value, "as_payload"):
        payload = value.as_payload()
    else:
        payload = dict(value)  # type: ignore[arg-type]
    return dict(payload)


def _residual_values_finite(payload: Mapping[str, Any]) -> bool:
    values = payload.get("residual_values", {})
    if not isinstance(values, Mapping):
        return False
    for value in values.values():
        try:
            if not math.isfinite(float(value)):
                return False
        except (TypeError, ValueError):
            return False
    return True


def _family_backend_evidence(
    family: str,
    family_residual_packs: Mapping[str, object] | None,
) -> tuple[str, bool, dict[str, Any], tuple[str, ...]]:
    if family == "FLRW":
        return (
            "facade_anchor_not_residual_pack",
            True,
            {
                "evidence_scope": "FLRW facade anchor",
                "residual_pack_required": False,
            },
            (),
        )
    if family_residual_packs is None:
        return (
            "not_provided",
            False,
            {"residual_pack_required": True},
            ("backend_residual_pack_not_provided",),
        )
    if family not in family_residual_packs:
        return (
            "missing",
            False,
            {"residual_pack_required": True},
            ("backend_residual_pack_missing",),
        )
    payload = _residual_payload(family_residual_packs[family])
    passed = bool(payload.get("passed", False))
    missing = tuple(str(item) for item in payload.get("missing_residuals", ()))
    violated = tuple(str(item) for item in payload.get("violated_tolerances", ()))
    shortcut_violations = tuple(
        str(item) for item in payload.get("forbidden_shortcut_violations", ())
    )
    finite = _residual_values_finite(payload)
    verification_pass = bool(payload.get("verification_crosscheck_pass", False))
    evidence_passed = (
        passed
        and not missing
        and not violated
        and not shortcut_violations
        and finite
        and verification_pass
    )
    blockers: list[str] = []
    if not passed:
        blockers.append("backend_residual_pack_failed")
    if missing:
        blockers.append("backend_residuals_missing")
    if violated:
        blockers.append("backend_residuals_out_of_tolerance")
    if shortcut_violations:
        blockers.append("backend_forbidden_shortcut_violation")
    if not finite:
        blockers.append("backend_residuals_nonfinite")
    if not verification_pass:
        blockers.append("backend_verification_crosscheck_missing")
    evidence = {
        "family": payload.get("family", family),
        "branch": payload.get("branch"),
        "backend": payload.get("backend"),
        "residual_labels": list(payload.get("residual_labels", ())),
        "required_residuals": list(payload.get("required_residuals", ())),
        "missing_residuals": list(missing),
        "violated_tolerances": list(violated),
        "forbidden_shortcut_violations": list(shortcut_violations),
        "verification_crosscheck_pass": verification_pass,
    }
    return (
        "residual_pack_passed" if evidence_passed else "residual_pack_failed",
        evidence_passed,
        evidence,
        tuple(blockers),
    )


def _family_row(
    family: str,
    *,
    family_residual_packs: Mapping[str, object] | None,
) -> FamilyReadinessRow:
    registry_exists = family in TYPE_REGISTRY
    background_ready = registry_exists
    backend_status = family_backend_status(family)
    (
        backend_evidence_status,
        backend_evidence_passed,
        residual_evidence,
        evidence_blockers,
    ) = _family_backend_evidence(family, family_residual_packs)
    ic_status = _family_ic_status(family)
    perturbation_ready = bool(
        ic_status in {"strong", "residual-backed"}
        and backend_status == "full_mode"
        and backend_evidence_passed
    )
    output_ready = perturbation_ready
    blockers: list[str] = []
    if not registry_exists:
        blockers.append("family_not_registered")
    blockers.extend(evidence_blockers)
    if backend_status != "full_mode":
        blockers.append(f"backend_status={backend_status}")
    if ic_status not in {"strong", "residual-backed"}:
        blockers.append(f"ic_status={ic_status}")
    if not perturbation_ready:
        blockers.append("full_lowell_perturbation_evidence_missing")
    return FamilyReadinessRow(
        family=family,
        registry_exists=registry_exists,
        background_ready=background_ready,
        backend_status=backend_status,
        backend_evidence_status=backend_evidence_status,
        backend_evidence_passed=backend_evidence_passed,
        ic_status=ic_status,
        perturbation_ready=perturbation_ready,
        output_ready=output_ready,
        statistics_usable=False,
        residual_evidence=residual_evidence,
        block_reasons=tuple(blockers),
    )


def build_family_readiness_manifest(
    *,
    family_residual_packs: Mapping[str, object] | None = None,
) -> dict[str, FamilyReadinessRow]:
    """Return the 11-family + FLRW readiness matrix."""

    return {
        family: _family_row(
            family,
            family_residual_packs=family_residual_packs,
        )
        for family in ("FLRW", *ALL_BIANCHI_TYPES)
    }


def _all_family_blockers(
    manifest: Mapping[str, FamilyReadinessRow],
) -> tuple[str, ...]:
    blockers: list[str] = []
    for family, row in manifest.items():
        if family == "FLRW":
            continue
        if not (row.output_ready and row.perturbation_ready):
            blockers.append(
                f"{family}:"
                + ",".join(row.block_reasons or ("not_output_ready",))
            )
    return tuple(blockers)


def _metadata_bool(metadata: Mapping[str, Any], key: str) -> bool:
    return bool(metadata.get(key, False))


def evaluate_publication_claim(
    claim_id: str,
    *,
    family_manifest: Mapping[str, FamilyReadinessRow] | None = None,
    gate_registry: Mapping[str, object] | None = None,
    output_metadata: Mapping[str, Any] | None = None,
    archive_dir: str | None = None,
) -> PublicationClaimDecision:
    """Evaluate one headline claim against actual runtime evidence."""

    manifest = (
        build_family_readiness_manifest()
        if family_manifest is None
        else dict(family_manifest)
    )
    metadata = {} if output_metadata is None else dict(output_metadata)
    if claim_id == "publication_grade_11_family_solver":
        blockers = _all_family_blockers(manifest)
        return PublicationClaimDecision(
            claim_id=claim_id,
            allowed=not blockers,
            evidence={
                family: row.as_payload()
                for family, row in manifest.items()
                if family != "FLRW"
            },
            blockers=blockers,
        )
    if claim_id == "family_backend_residual_evidence":
        blockers = tuple(
            f"{family}:{','.join(row.block_reasons or ('backend_evidence_missing',))}"
            for family, row in manifest.items()
            if family != "FLRW" and not row.backend_evidence_passed
        )
        return PublicationClaimDecision(
            claim_id=claim_id,
            allowed=not blockers,
            evidence={
                family: row.as_payload()
                for family, row in manifest.items()
                if family != "FLRW"
            },
            blockers=blockers,
        )
    if claim_id == "full_anisotropic_polarization_output":
        thomson_mode = str(metadata.get("thomson_mode", ""))
        checks = {
            "exact_thomson": bool(
                metadata.get("exact_thomson_authority_path", False)
            )
            or thomson_mode
            in {
                "electron_frame_exact_wrapper",
                "exact_electron_frame",
                "electron_frame_tilted_layer_b_exact",
            }
            or (
                thomson_mode.startswith("electron_frame")
                and "exact" in thomson_mode
            ),
            "b_runtime": _metadata_bool(metadata, "b_mode_runtime_available"),
            "b_support": metadata.get("b_mode_output_support")
            in {"wigner_d_path_b", "evolved_b_mode"},
            "tilt_boost_split": metadata.get("tilt_boost_separation")
            == "explicit_nonmerged",
        }
        blockers = tuple(key for key, passed in checks.items() if not passed)
        return PublicationClaimDecision(
            claim_id=claim_id,
            allowed=not blockers,
            evidence=checks,
            blockers=blockers,
        )
    if claim_id == "statistics_ready_likelihood":
        gate_decision = (
            None
            if gate_registry is None
            else hard_gate_before_fitting(gate_registry).as_payload()
        )
        gate_allowed = bool(gate_decision and gate_decision["allowed"])
        statistics_decision = metadata.get("statistics_readiness_decision")
        statistics_decision_allowed = bool(
            isinstance(statistics_decision, Mapping)
            and statistics_decision.get("allowed", False)
        )
        checks = {
            "gate_allowed": gate_allowed,
            "covariance_full": metadata.get("covariance_readiness") == "full",
            "not_diagnostic_only": not bool(metadata.get("diagnostic_only", True)),
            "fitting_allowed": bool(metadata.get("fitting_allowed", False)),
            "statistics_decision_allowed": statistics_decision_allowed,
            "statistics_owner_is_inference": metadata.get("statistics_owner")
            == "bass.inference.live_binding",
        }
        blockers = tuple(key for key, passed in checks.items() if not passed)
        return PublicationClaimDecision(
            claim_id=claim_id,
            allowed=not blockers,
            evidence={
                "checks": checks,
                "gate_decision": gate_decision,
                "statistics_readiness_decision": statistics_decision,
            },
            blockers=blockers,
        )
    if claim_id == "harmonic_output_archive":
        if archive_dir is None:
            return PublicationClaimDecision(
                claim_id=claim_id,
                allowed=False,
                blockers=("archive_dir_missing",),
            )
        try:
            evidence = validate_alm_archive(archive_dir)
        except Exception as exc:
            return PublicationClaimDecision(
                claim_id=claim_id,
                allowed=False,
                evidence={"error": str(exc)},
                blockers=("archive_validation_failed",),
            )
        return PublicationClaimDecision(
            claim_id=claim_id,
            allowed=True,
            evidence=evidence,
        )
    if claim_id == "optimization_same_physics":
        checks = {
            "same_equations": metadata.get("optimization_same_equations") is True,
            "same_tolerance": metadata.get("optimization_same_tolerance") is True,
            "same_cutoff": metadata.get("optimization_same_cutoff") is True,
            "same_observable": metadata.get("optimization_same_observable") is True,
            "bit_identity_or_tight_bound": metadata.get(
                "optimization_identity_status"
            )
            in {"bit_identical", "within_declared_tolerance"},
        }
        blockers = tuple(key for key, passed in checks.items() if not passed)
        return PublicationClaimDecision(
            claim_id=claim_id,
            allowed=not blockers,
            evidence=checks,
            blockers=blockers,
        )
    raise KeyError(f"unknown publication claim {claim_id!r}")


def assert_publication_claim_allowed(
    claim_id: str,
    **kwargs: Any,
) -> PublicationClaimDecision:
    """Return a decision or raise with all blockers listed."""

    decision = evaluate_publication_claim(claim_id, **kwargs)
    if not decision.allowed:
        raise PublicationClaimError(
            f"{claim_id} not allowed; blockers={list(decision.blockers)!r}"
        )
    return decision
