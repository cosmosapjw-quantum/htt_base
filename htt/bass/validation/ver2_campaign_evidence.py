"""Executable BF-05 validation evidence for the shipped BASS Tier-B path."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from functools import lru_cache
from typing import Literal

import numpy as np

from common.contracts import ArtifactManifest, SkySupport

from bass.background.bianchi_types import get_type
from bass.background.einstein_bianchi import BianchiCosmology
from bass.forward.ver2_solver_output import BassReleaseMetadata
from bass.hierarchy.integrator import IntegratorConfig
from bass.hierarchy.pstf_tensor import unpack_hierarchy
from bass.observational import build_observable_vector_from_solver_output
from bass.runtime import (
    CheckpointPolicy,
    ConstraintProjectionPolicy,
    CouplingMode,
    FeatureStatus,
    IntegratorFamily,
    RuntimeControlBlock,
    SolverFeatureFlags,
    SolverTier,
    compare_tier_a_to_tier_b,
    execute_tier_a_validation_solver,
    execute_tier_b_solver,
)
from bass.spectrum import CutoffCampaignSpec
from bass.species.registry import SpeciesBackgroundRegistry

ValidationOutcome = Literal["pass", "warn", "fail"]

__all__ = [
    "ExecutableCheckEvidence",
    "ExecutableCampaignEvidence",
    "build_type_i_runtime_validation_evidence",
    "type_i_runtime_validation_payload",
]


@dataclass(frozen=True)
class ExecutableCheckEvidence:
    """One executable validation witness for the BF-05 runtime campaign."""

    check_id: str
    category: str
    passed: bool
    summary: str
    metric_name: str | None = None
    metric_value: float | None = None
    threshold: float | None = None
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.check_id:
            raise ValueError("check_id must be non-empty")
        if not self.category:
            raise ValueError("category must be non-empty")
        if not self.summary:
            raise ValueError("summary must be non-empty")
        if self.metric_name is None:
            if self.metric_value is not None or self.threshold is not None:
                raise ValueError(
                    "metric_value/threshold require metric_name to be present"
                )
            return
        if self.metric_value is None or self.threshold is None:
            raise ValueError(
                "metric_name requires both metric_value and threshold"
            )
        if not np.isfinite(self.metric_value):
            raise ValueError("metric_value must be finite")
        if not np.isfinite(self.threshold):
            raise ValueError("threshold must be finite")


@dataclass(frozen=True)
class ExecutableCampaignEvidence:
    """Machine-readable BF-05 evidence bundle for one executable campaign."""

    campaign_id: str
    status: ValidationOutcome
    bianchi_type: str
    cutoffs: tuple[int, ...]
    theorem_refs: tuple[str, ...]
    null_manifest_refs: tuple[str, ...]
    injection_manifest_refs: tuple[str, ...]
    runbook_refs: tuple[str, ...]
    no_claim_conditions: tuple[str, ...]
    checks: tuple[ExecutableCheckEvidence, ...]
    artifact_refs: tuple[str, ...]
    preferred_axis_delta_deg: float
    tier_a_tier_b_max_relative_l2: float
    cutoff_max_relative_delta: float
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.campaign_id:
            raise ValueError("campaign_id must be non-empty")
        if self.status not in {"pass", "warn", "fail"}:
            raise ValueError(f"unknown validation status {self.status!r}")
        if not self.bianchi_type:
            raise ValueError("bianchi_type must be non-empty")
        if not self.cutoffs:
            raise ValueError("cutoffs must be non-empty")
        if not self.theorem_refs:
            raise ValueError("theorem_refs must be non-empty")
        if not self.null_manifest_refs:
            raise ValueError("null_manifest_refs must be non-empty")
        if not self.injection_manifest_refs:
            raise ValueError("injection_manifest_refs must be non-empty")
        if not self.runbook_refs:
            raise ValueError("runbook_refs must be non-empty")
        if not self.no_claim_conditions:
            raise ValueError("no_claim_conditions must be non-empty")
        if not self.checks:
            raise ValueError("checks must be non-empty")
        if not self.artifact_refs:
            raise ValueError("artifact_refs must be non-empty")
        for name, value in (
            ("preferred_axis_delta_deg", self.preferred_axis_delta_deg),
            ("tier_a_tier_b_max_relative_l2", self.tier_a_tier_b_max_relative_l2),
            ("cutoff_max_relative_delta", self.cutoff_max_relative_delta),
        ):
            if not np.isfinite(value) or value < 0.0:
                raise ValueError(f"{name} must be finite and non-negative")

    @property
    def passed(self) -> bool:
        return self.status == "pass"


def _manifest(artifact_id: str) -> ArtifactManifest:
    return ArtifactManifest(
        artifact_id=artifact_id,
        artifact_path=f"artifacts/bass/{artifact_id.replace('.', '_')}.json",
        owner="BASS",
        implementation_scope="canonical_BASS",
        claim_tier="conditional",
        production_status="production_candidate",
        created_by="bf05_validation",
        git_commit="bf05-runtime-validation",
        config_hash="bf05-type-i-native-v1",
        input_hashes=("species.planck2018",),
        code_version="ver2-bf05",
        schema_version="1.0.0",
        required_gates=("runtime", "propagator", "validation"),
        passed_gates=("runtime", "propagator", "validation"),
    )


def _release(label: str, *, stage: str) -> BassReleaseMetadata:
    return BassReleaseMetadata(
        release_stage=stage,
        run_label=label,
        config_hash="bf05-type-i-native-v1",
        code_version="ver2-bf05",
        schema_version="1.0.0",
        git_commit="bf05-runtime-validation",
        random_seed=42,
    )


def _runtime_controls(*, tier: SolverTier) -> RuntimeControlBlock:
    if tier is SolverTier.TIER_A_ANGULAR:
        return RuntimeControlBlock(
            tier=tier,
            integrator_family=IntegratorFamily.IMPLICIT_RADAU,
            coupling_mode=CouplingMode.FULLY_COUPLED,
            multipole_cutoff=4,
            rtol=1.0e-6,
            atol=1.0e-9,
            checkpoint=CheckpointPolicy(enabled=False),
            constraint_projection=ConstraintProjectionPolicy(
                enabled=True,
                every_n_steps=4,
                status=FeatureStatus.EXACT,
            ),
            random_seed=42,
        )
    return RuntimeControlBlock(
        tier=tier,
        integrator_family=IntegratorFamily.IMEX_SPLIT,
        coupling_mode=CouplingMode.BACKGROUND_THEN_RADIATION,
        multipole_cutoff=4,
        rtol=1.0e-6,
        atol=1.0e-9,
        checkpoint=CheckpointPolicy(enabled=False),
        constraint_projection=ConstraintProjectionPolicy(
            enabled=True,
            every_n_steps=4,
            status=FeatureStatus.APPROXIMATE,
        ),
        random_seed=42,
    )


def _feature_flags(*, tier: SolverTier) -> SolverFeatureFlags:
    if tier is SolverTier.TIER_A_ANGULAR:
        exact = FeatureStatus.EXACT
        return SolverFeatureFlags(
            background_dynamics=exact,
            photon_transport=exact,
            thomson_collision=exact,
            visibility_history=exact,
            source_propagator=exact,
            checkpoint_restart=FeatureStatus.DISABLED,
        )
    approx = FeatureStatus.APPROXIMATE
    return SolverFeatureFlags(
        background_dynamics=approx,
        photon_transport=approx,
        thomson_collision=approx,
        visibility_history=approx,
        source_propagator=approx,
        checkpoint_restart=FeatureStatus.DISABLED,
    )


def _integrator_config(*, gamma_t_override) -> IntegratorConfig:
    return IntegratorConfig(
        L_max=4,
        eta_initial_mpc=0.5,
        eta_final_mpc=1.0,
        n_output=12,
        rtol=1.0e-6,
        atol=1.0e-9,
        bianchi_cosmo=BianchiCosmology(
            structure=get_type("I"),
            beta=0.0,
        ),
        gamma_T_over_H_threshold=100.0,
        gamma_T_override=gamma_t_override,
    )


def _sky_support() -> SkySupport:
    return SkySupport(
        selection_mode="mock_calibrated",
        sky_support_hash="sky.type_i.native.v1",
        mask_hash="mask.type_i.native.v1",
        mock_coverage_status="adequate",
        scan_volume_hash="scan.bass.native.type_i.v1",
    )


def _type_i_native_bundle(
    *,
    cutoffs: tuple[int, ...],
    tier_compare_tolerance: float,
    cutoff_delta_tolerance: float,
) -> ExecutableCampaignEvidence:
    species = SpeciesBackgroundRegistry.from_planck2018()
    k_grid = np.array([1.0e-4, 2.0e-4], dtype=np.float64)

    tier_a = execute_tier_a_validation_solver(
        manifest=_manifest("bass.validation.tier_a.reference"),
        bianchi_type="I",
        species=species,
        integrator_config=_integrator_config(gamma_t_override=lambda eta: 1.0e15),
        runtime_controls=_runtime_controls(tier=SolverTier.TIER_A_ANGULAR),
        feature_flags=_feature_flags(tier=SolverTier.TIER_A_ANGULAR),
        release=_release("bf05-tier-a", stage="validation_reference"),
        k_grid_mpc=k_grid,
    )
    tier_b = execute_tier_b_solver(
        manifest=_manifest("bass.validation.tier_b.native"),
        bianchi_type="I",
        species=species,
        integrator_config=_integrator_config(gamma_t_override=lambda eta: 1.0e15),
        runtime_controls=_runtime_controls(tier=SolverTier.TIER_B_PSTF),
        feature_flags=_feature_flags(tier=SolverTier.TIER_B_PSTF),
        release=_release("bf05-tier-b", stage="research_candidate"),
        k_grid_mpc=k_grid,
        cutoff_spec=CutoffCampaignSpec(
            cutoffs=tuple(int(value) for value in cutoffs),
            closure_name="tier_b_tca",
            baseline_cutoff=6 if 6 in cutoffs else cutoffs[0],
        ),
    )
    tier_b_no_startup = execute_tier_b_solver(
        manifest=_manifest("bass.validation.tier_b.seed_without_startup"),
        bianchi_type="I",
        species=species,
        integrator_config=_integrator_config(gamma_t_override=lambda eta: 1.0),
        runtime_controls=_runtime_controls(tier=SolverTier.TIER_B_PSTF),
        feature_flags=_feature_flags(tier=SolverTier.TIER_B_PSTF),
        release=_release("bf05-tier-b-no-startup", stage="research_candidate"),
        k_grid_mpc=k_grid,
    )
    comparison = compare_tier_a_to_tier_b(
        tier_a,
        tier_b,
        tolerance=float(tier_compare_tolerance),
    )
    observable = build_observable_vector_from_solver_output(
        tier_b.solver_output,
        sky_support=_sky_support(),
    )

    initial_T = unpack_hierarchy(
        tier_b_no_startup.integration_result.photon_T_tower[0],
        tier_b_no_startup.integration_result.L_max,
    )
    initial_E = unpack_hierarchy(
        tier_b_no_startup.integration_result.photon_E_tower[0],
        tier_b_no_startup.integration_result.L_max,
    )
    seed_survives = (
        tier_b_no_startup.trace.startup_state is None
        and tier_b_no_startup.trace.seed_projection.projection_ready
        and abs(float(initial_T.tensors[0].components[0])) > 0.0
        and abs(float(initial_T.tensors[1].components[1])) > 0.0
        and abs(float(initial_T.tensors[2].components[2])) > 0.0
        and abs(float(initial_E.tensors[2].components[2])) > 0.0
    )

    cutoff_max_delta = 0.0
    if tier_b.cutoff_campaign is not None:
        for cutoff, deltas in tier_b.cutoff_campaign.deltas.items():
            if cutoff == tier_b.cutoff_campaign.spec.baseline_cutoff:
                continue
            if deltas:
                cutoff_max_delta = max(
                    cutoff_max_delta,
                    max(float(delta.relative_delta) for delta in deltas),
                )

    tier_bridge_max = max(
        float(value) for value in comparison.relative_l2_by_channel.values()
    )
    baseline_passed = (
        observable.alm_features["observer_reconstruction_status"]
        == "sphere_reconstructed_from_pstf"
        and observable.biposh is not None
        and observable.biposh.get("null_proxy_status")
        == "consistent_with_isotropic_null"
        and observable.covariance_features is not None
        and observable.covariance_features.get("representation")
        == "low_ell_harmonic_sparse_basis"
    )
    regression_passed = (
        tier_b.trace.seed_projection.projection_ready
        and tier_b.trace.visibility_source.contract.events is not None
        and tier_b.integration_result.solver_info["tier_b_core_owner"]
        == "ver2_s1s2_native"
        and tier_b.solver_output.metadata["source_propagator_status"] == "exact"
        and tier_b.solver_output.metadata["source_propagator_realization"]
        == "bianchi_i_matrix_exact"
        and bool(tier_b.solver_output.metadata["propagator_ready"])
    )

    checks = (
        ExecutableCheckEvidence(
            check_id="type_i_observable_null_recovery",
            category="baseline_reproduction",
            passed=bool(baseline_passed),
            summary="Type-I native observable export preserves isotropic-null status after live PSTF sphere reconstruction.",
        ),
        ExecutableCheckEvidence(
            check_id="native_seed_projection_survives_without_startup",
            category="adversarial_edge",
            passed=bool(seed_survives),
            summary="Native seed injection remains non-trivial even when the startup manifold is disabled by the Gamma_T/H gate.",
        ),
        ExecutableCheckEvidence(
            check_id="tier_a_tier_b_type_i_bridge_matches",
            category="physics_sanity",
            passed=bool(comparison.passed),
            summary="Tier-A validation reference and native Tier-B Type-I bridge agree within the declared tolerance.",
            metric_name="max_relative_l2",
            metric_value=float(tier_bridge_max),
            threshold=float(tier_compare_tolerance),
        ),
        ExecutableCheckEvidence(
            check_id="tier_b_cutoff_campaign_stays_bounded",
            category="numerical_stability",
            passed=float(cutoff_max_delta) <= float(cutoff_delta_tolerance),
            summary="Executed default cutoff campaign remains bounded on the native Type-I route.",
            metric_name="max_relative_cutoff_delta",
            metric_value=float(cutoff_max_delta),
            threshold=float(cutoff_delta_tolerance),
        ),
        ExecutableCheckEvidence(
            check_id="tier_b_runtime_consumes_live_hooks_and_exact_type_i_propagator",
            category="regression",
            passed=bool(regression_passed),
            summary="Native Tier-B runtime still consumes live S1/S2 hooks and realizes the exact Type-I propagator path.",
        ),
    )
    status: ValidationOutcome = "pass" if all(check.passed for check in checks) else "fail"
    return ExecutableCampaignEvidence(
        campaign_id="validation.bass_native_runtime_bridge",
        status=status,
        bianchi_type="I",
        cutoffs=tuple(int(value) for value in cutoffs),
        theorem_refs=("V8_bass_native_runtime_bridge",),
        null_manifest_refs=("null.bass.type_i_native_runtime",),
        injection_manifest_refs=("validation.injection.native_seed_startup",),
        runbook_refs=("runbook.bass_native_runtime",),
        no_claim_conditions=(
            "tier_a_validation_bridge_only",
            "non_type_i_exact_propagator_missing",
        ),
        checks=checks,
        artifact_refs=("bass.validation.type_i_runtime_evidence", "bass.runtime.trace"),
        preferred_axis_delta_deg=float(comparison.preferred_axis_delta_deg),
        tier_a_tier_b_max_relative_l2=float(tier_bridge_max),
        cutoff_max_relative_delta=float(cutoff_max_delta),
        notes=(
            "This executable evidence is intentionally limited to the shipped Type-I native route.",
            "It validates the runtime/seed/cutoff/observer-neutral bridge without promoting non-Type-I exact propagators or full BiPoSH science claims.",
        ),
    )


@lru_cache(maxsize=8)
def build_type_i_runtime_validation_evidence(
    *,
    cutoffs: tuple[int, ...] = (4, 6),
    tier_compare_tolerance: float = 5.0e-2,
    cutoff_delta_tolerance: float = 7.5e-1,
) -> ExecutableCampaignEvidence:
    """Return executable BF-05 evidence for the current shipped Type-I path."""
    if tuple(sorted(cutoffs)) != tuple(cutoffs):
        raise ValueError("cutoffs must be strictly increasing")
    if any(int(value) < 4 for value in cutoffs):
        raise ValueError("BF-05 executable evidence requires cutoffs >= 4")
    if tier_compare_tolerance <= 0.0:
        raise ValueError("tier_compare_tolerance must be positive")
    if cutoff_delta_tolerance <= 0.0:
        raise ValueError("cutoff_delta_tolerance must be positive")
    return _type_i_native_bundle(
        cutoffs=tuple(int(value) for value in cutoffs),
        tier_compare_tolerance=float(tier_compare_tolerance),
        cutoff_delta_tolerance=float(cutoff_delta_tolerance),
    )


def type_i_runtime_validation_payload(
    *,
    cutoffs: tuple[int, ...] = (4, 6),
    tier_compare_tolerance: float = 5.0e-2,
    cutoff_delta_tolerance: float = 7.5e-1,
) -> dict[str, object]:
    """JSON-ready payload for the BF-05 executable Type-I validation evidence."""
    return asdict(
        build_type_i_runtime_validation_evidence(
            cutoffs=cutoffs,
            tier_compare_tolerance=tier_compare_tolerance,
            cutoff_delta_tolerance=cutoff_delta_tolerance,
        )
    )
