"""VER2 descriptive x/Q/Pi/F/G report plumbing."""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping

from common.departure_contracts import BudgetSpec, DepartureBundle, DepartureReport
from common.contracts import ObservableVector

from bass.observational._manifest import derive_manifest, sky_support_metadata

__all__ = ["DepartureBuildResult", "build_descriptive_departure_report"]


_LEGACY_COMMON_BUDGET_POLICY = "MES_linear"
_LEGACY_COMMON_BUDGET_KIND = "linear_MES"


@dataclass(frozen=True)
class DepartureBuildResult:
    report: DepartureReport
    claim_language_allowed: bool
    blocked_reasons: tuple[str, ...]


def _numerator(bundle: DepartureBundle, numerator_policy: str) -> float:
    if numerator_policy == "signed":
        return float(bundle.x_signed)
    if numerator_policy == "absolute":
        return abs(float(bundle.x_signed))
    return float(bundle.x_positive)


def _local_global_status(observable_vector: ObservableVector) -> str | None:
    features = observable_vector.covariance_features
    if not isinstance(features, dict):
        return None
    degeneracy = features.get("local_global_degeneracy")
    if not isinstance(degeneracy, dict):
        return None
    status = degeneracy.get("status")
    return str(status) if status is not None else None


def _validate_legacy_common_budget_policy(
    budget: BudgetSpec,
    denominator_policy: str,
) -> None:
    if denominator_policy != _LEGACY_COMMON_BUDGET_POLICY:
        raise ValueError(
            "legacy COMMON BudgetSpec supports only MES_linear denominator_policy; "
            "use the MIO BudgetSpec contract for transfer, atlas, or observational "
            "budget policies"
        )
    if str(budget.kind) != _LEGACY_COMMON_BUDGET_KIND:
        raise ValueError(
            "legacy COMMON BudgetSpec.kind must be linear_MES when "
            "denominator_policy is MES_linear"
        )


def build_descriptive_departure_report(
    observable_vector: ObservableVector,
    *,
    bundle: DepartureBundle,
    budget: BudgetSpec,
    numerator_policy: str = "positive_part",
    denominator_policy: str | None = None,
    claim_gate_passed: bool = False,
    occupancy_certified: bool = False,
    pi_curve_ref: str | None = None,
    g_values: Mapping[str, float] | None = None,
    component_filling: Mapping[str, float] | None = None,
    channel_filling: Mapping[str, float] | None = None,
    tsc_overlay_ref: str | None = None,
) -> DepartureBuildResult:
    """Build a descriptive xQPiFG shell without merging semantics."""
    if observable_vector.manifest.owner != "BASS":
        raise ValueError("Departure report plumbing expects a BASS observable vector")
    if denominator_policy is None or not str(denominator_policy).strip():
        raise ValueError("denominator_policy must be explicit")
    denominator_policy = str(denominator_policy).strip()
    _validate_legacy_common_budget_policy(budget, denominator_policy)
    blocked_reasons: list[str] = []
    if bundle.x_signed < 0.0:
        blocked_reasons.append("negative_sector")
    if not budget.is_admissible_ceiling:
        blocked_reasons.append("ceiling_not_admissible")
    if not claim_gate_passed:
        blocked_reasons.append("claim_gate_not_passed")
    if not occupancy_certified:
        blocked_reasons.append("occupancy_not_certified")

    x_value = float(bundle.x_signed)
    U_value = float(budget.value)
    if not math.isfinite(U_value) or U_value <= 0.0:
        raise ValueError("BudgetSpec.value must be positive finite")
    q_value = _numerator(bundle, numerator_policy) / U_value
    caveats = ["report_is_descriptive_until_claim_gates_pass"]
    local_global_status = _local_global_status(observable_vector)
    if "negative_sector" in blocked_reasons:
        F_status = "invalid_negative_sector"
        F_value = None
        caveats.append("negative_sector_blocks_certified_occupancy")
    elif "ceiling_not_admissible" in blocked_reasons:
        F_status = "invalid_ceiling_not_admissible"
        F_value = None
        caveats.append("ceiling_not_admissible_for_certified_filling")
    elif not claim_gate_passed or not occupancy_certified:
        F_status = "linear_proxy_score"
        F_value = max(q_value, 0.0)
        caveats.append("uncertified_filling_downgraded_to_proxy_score")
    else:
        F_status = "certified_occupancy"
        if component_filling:
            F_value = min(max(sum(float(v) for v in component_filling.values()), 0.0), 1.0)
        else:
            F_value = min(max(q_value, 0.0), 1.0)
    if local_global_status not in {None, "not_applicable_isotropic"}:
        caveats.append("local_global_degeneracy_unresolved")
    reconstruction_status = observable_vector.alm_features.get("observer_reconstruction_status")
    if reconstruction_status == "final_slice_only_no_sphere_reconstruction":
        caveats.append("observer_reconstruction_bridge_pending")
    claim_language_allowed = not blocked_reasons
    manifest = derive_manifest(
        observable_vector.manifest,
        artifact_id=f"{observable_vector.manifest.artifact_id}.departure_report",
        artifact_path=f"artifacts/common/{observable_vector.manifest.artifact_id.replace('.', '_')}_departure_report.json",
        owner="COMMON",
        implementation_scope="common",
        claim_tier="conditional" if claim_language_allowed else "exploratory",
        production_status="diagnostic_only",
        caveats=tuple(caveats),
        statistics_definitions={
            "surface": "DepartureReport",
            "sky_support": sky_support_metadata(observable_vector.sky_support),
            "comparator_policy": bundle.comparator,
            "local_global_degeneracy_status": local_global_status,
        },
        extra_input_hashes=(observable_vector.manifest.artifact_id,),
    )
    report = DepartureReport(
        comparator_policy=bundle.comparator,
        bundle_B={
            "Sigma2": float(bundle.Sigma2_std),
            "W2": float(bundle.W2_std),
            "Omega_tilt": float(bundle.Omega_tilt),
            "Omega_k_aniso": float(bundle.Omega_k_aniso),
        },
        x_value=x_value,
        numerator_policy=numerator_policy,
        denominator_policy=denominator_policy,
        U_value=U_value,
        Q_value=float(q_value),
        F_value=None if F_value is None else float(F_value),
        F_status=F_status,
        Pi_curve_ref=pi_curve_ref,
        G_values={key: float(value) for key, value in (g_values or {}).items()},
        component_filling={
            key: float(value) for key, value in (component_filling or {}).items()
        },
        channel_filling={
            key: float(value) for key, value in (channel_filling or {}).items()
        },
        caveats=caveats,
        manifest=manifest,
        tsc_overlay_ref=tsc_overlay_ref,
    )
    return DepartureBuildResult(
        report=report,
        claim_language_allowed=claim_language_allowed,
        blocked_reasons=tuple(blocked_reasons),
    )
