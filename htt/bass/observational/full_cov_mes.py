"""VER2 full-covariance MES skeleton with explicit no-claim semantics."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from common.contracts import AtlasEntryLite, FullCovMESReport, ObservableVector

from bass.observational._manifest import derive_manifest, sky_support_metadata

__all__ = [
    "MesBoundBuildResult",
    "evaluate_mes_claim_gate",
    "build_full_cov_mes_report",
]


@dataclass(frozen=True)
class MesBoundBuildResult:
    report: FullCovMESReport
    covariance_claim_allowed: bool
    blocked_reasons: tuple[str, ...]


def evaluate_mes_claim_gate(
    atlas_entry: AtlasEntryLite,
    observable_vector: ObservableVector,
    *,
    parameter_block: str,
    singular_values: Sequence[float],
    rank_tolerance: float = 1.0e-12,
) -> tuple[bool, tuple[str, ...], int]:
    reasons: list[str] = []
    response = atlas_entry.response_blocks.get(parameter_block)
    if response in ({}, None):
        reasons.append("missing_response_block")
    if observable_vector.biposh is None and observable_vector.covariance_features is None:
        reasons.append("missing_covariance_features")
    rank = sum(float(value) > rank_tolerance for value in singular_values)
    if rank == 0:
        reasons.append("response_rank_deficient")
    return not reasons, tuple(reasons), rank


def build_full_cov_mes_report(
    atlas_entry: AtlasEntryLite,
    observable_vector: ObservableVector,
    *,
    parameter_block: str,
    diagonal_bound: float,
    singular_values: Sequence[float],
    covariance_assumption: str,
    dynamical_bound: float | None = None,
    covariance_bound: float | None = None,
    noise_radius: float = 1.0,
    nuisance_projection_status: str = "not_run",
    validity_radius: float | None = None,
    rank_tolerance: float = 1.0e-12,
    tsc_overlay_ref: str | None = None,
) -> MesBoundBuildResult:
    """Build a morphology-aware MES report without promoting rank failure."""
    allowed, blocked_reasons, response_rank = evaluate_mes_claim_gate(
        atlas_entry,
        observable_vector,
        parameter_block=parameter_block,
        singular_values=singular_values,
        rank_tolerance=rank_tolerance,
    )
    positive_svals = [float(value) for value in singular_values if float(value) > rank_tolerance]
    cov_bound = covariance_bound
    if allowed and cov_bound is None and positive_svals:
        cov_bound = float(noise_radius) / min(positive_svals)
    baseline_candidates = [float(diagonal_bound)]
    if dynamical_bound is not None:
        baseline_candidates.append(float(dynamical_bound))
    if allowed and cov_bound is not None:
        final_bound = min(*baseline_candidates, float(cov_bound))
        information_gain = max(float(diagonal_bound) / final_bound, 1.0)
        claim_tier = "conditional"
        failed_gates: tuple[str, ...] = ()
        passed_gates = ("response_rank_sufficient",)
        production_status = "diagnostic_only"
        projection_status = nuisance_projection_status
    else:
        final_bound = min(baseline_candidates)
        information_gain = 1.0
        claim_tier = "blocked"
        failed_gates = blocked_reasons
        passed_gates = ()
        projection_status = f"no_claim:{','.join(blocked_reasons)}"
        if "missing_covariance_features" in blocked_reasons:
            production_status = "blocked_missing_covariance"
        elif "missing_response_block" in blocked_reasons:
            production_status = "blocked_missing_atlas"
        else:
            production_status = "diagnostic_only"
        cov_bound = None
    manifest = derive_manifest(
        atlas_entry.manifest,
        artifact_id=f"{atlas_entry.atlas_id}.mes.{parameter_block}",
        artifact_path=f"artifacts/bass/{atlas_entry.atlas_id.replace('.', '_')}_mes_{parameter_block}.json",
        owner="BASS",
        implementation_scope="bass_py",
        claim_tier=claim_tier,
        production_status=production_status,
        caveats=(
            "rank_failure_returns_no_claim_not_weak_evidence",
            "covariance_upgrade_is_descriptive_until_validation_packet",
        ),
        required_gates=("response_rank_sufficient",),
        passed_gates=passed_gates,
        failed_gates=failed_gates,
        statistics_definitions={
            "surface": "FullCovMESReport",
            "parameter_block": parameter_block,
            "observable_channels": list(observable_vector.channels),
            "sky_support": sky_support_metadata(observable_vector.sky_support),
        },
        extra_input_hashes=(observable_vector.manifest.artifact_id,),
    )
    report = FullCovMESReport(
        parameter_block=parameter_block,
        diagonal_bound=float(diagonal_bound),
        covariance_bound=cov_bound,
        dynamical_bound=dynamical_bound,
        final_bound=float(final_bound),
        information_gain=float(information_gain),
        response_rank=response_rank,
        singular_values=[float(value) for value in singular_values],
        nuisance_projection_status=projection_status,
        observable_set=list(observable_vector.channels),
        covariance_assumption=covariance_assumption,
        validity_radius=validity_radius,
        manifest=manifest,
        tsc_overlay_ref=tsc_overlay_ref,
    )
    return MesBoundBuildResult(
        report=report,
        covariance_claim_allowed=allowed,
        blocked_reasons=blocked_reasons,
    )
