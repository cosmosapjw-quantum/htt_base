"""Executable BF-05 validation evidence for the shipped BASS Tier-B path."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from functools import lru_cache
from typing import Literal

import numpy as np

from common.contracts import ArtifactManifest, SkySupport

from bass.background import CodazziProjectionError
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
    "build_representative_family_sweep_evidence",
    "build_type_i_reionization_probe_evidence",
    "build_type_i_runtime_validation_evidence",
    "representative_family_sweep_payload",
    "type_i_reionization_probe_payload",
    "type_i_runtime_validation_payload",
]


_REPRESENTATIVE_FAMILIES: tuple[str, ...] = ("I", "V", "VII_0", "VIII")
_REPRESENTATIVE_PROPAGATOR_REALIZATIONS: dict[str, tuple[str, str]] = {
    "I": ("bianchi_i_matrix_exact", "exact"),
    "V": ("class_b_open_matrix_approx", "approximate"),
    "VII_0": ("class_a_helical_matrix_approx", "approximate"),
    "VIII": ("class_a_semisimple_matrix_approx", "approximate"),
}
_REPRESENTATIVE_TILT_BLOCKERS: dict[str, str] = {
    "I": "codazzi_balanced_total_momentum",
    "V": "class_b_divergence_tilt_coupling",
    "VII_0": "class_a_helical_codazzi",
    "VIII": "class_a_semisimple_codazzi",
}


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


def _extended_low_z_integrator_config(
    *,
    species: SpeciesBackgroundRegistry,
    z_final: float,
    gamma_t_override,
) -> IntegratorConfig:
    return IntegratorConfig(
        L_max=4,
        eta_initial_mpc=0.5,
        eta_final_mpc=float(species.bg_table.eta_at_a(1.0 / (1.0 + float(z_final)))),
        n_output=64,
        rtol=1.0e-6,
        atol=1.0e-9,
        bianchi_cosmo=BianchiCosmology(
            structure=get_type("I"),
            beta=0.0,
        ),
        gamma_T_over_H_threshold=100.0,
        gamma_T_override=gamma_t_override,
    )


def _family_integrator_config(
    *,
    bianchi_type: str,
    beta: float,
    gamma_t_override,
) -> IntegratorConfig:
    return IntegratorConfig(
        L_max=4,
        eta_initial_mpc=0.5,
        eta_final_mpc=1.0,
        n_output=12,
        rtol=1.0e-6,
        atol=1.0e-9,
        bianchi_cosmo=BianchiCosmology(
            structure=get_type(bianchi_type),
            beta=float(beta),
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
    reionization_window_honesty = (
        tier_b.solver_output.metadata["visibility_reionization_mode"] == "tanh"
        and tier_b.solver_output.metadata["source_builder_low_z_probe_available"] is False
        and tier_b.solver_output.metadata["source_builder_low_z_probe_status"]
        == "not_covered_by_runtime_domain"
        and tier_b.solver_output.metadata["reionization_source_claim_status"]
        == "unavailable_due_to_runtime_domain"
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
        ExecutableCheckEvidence(
            check_id="tier_b_runtime_explicitly_flags_missing_late_time_reionization_window",
            category="regression",
            passed=bool(reionization_window_honesty),
            summary="The shipped Type-I runtime records that tanh reionization is enabled but the late-time low-z source window is not covered by the current runtime domain.",
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
            "late_time_reionization_window_missing",
        ),
        checks=checks,
        artifact_refs=("bass.validation.type_i_runtime_evidence", "bass.runtime.trace"),
        preferred_axis_delta_deg=float(comparison.preferred_axis_delta_deg),
        tier_a_tier_b_max_relative_l2=float(tier_bridge_max),
        cutoff_max_relative_delta=float(cutoff_max_delta),
        notes=(
            "This executable evidence is intentionally limited to the shipped Type-I native route.",
            "It validates the runtime/seed/cutoff/observer-neutral bridge without promoting non-Type-I exact propagators or full BiPoSH science claims.",
            "The shipped runtime does not yet cover the low-z reionization source window; that absence is treated as an explicit no-claim condition rather than hidden as a pass.",
        ),
    )


def _type_i_reionization_probe_bundle(
    *,
    z_probe: float,
    z_final: float,
) -> ExecutableCampaignEvidence:
    species_with_reion = SpeciesBackgroundRegistry.from_planck2018(
        recombination_warning_policy="ignore",
    )
    species_without_reion = SpeciesBackgroundRegistry.from_planck2018(
        recombination_warning_policy="ignore",
        apply_default_reionization=False,
    )
    k_grid = np.array([1.0e-4, 2.0e-4], dtype=np.float64)

    run_with_reion = execute_tier_b_solver(
        manifest=_manifest("bass.validation.type_i_reionization_probe"),
        bianchi_type="I",
        species=species_with_reion,
        integrator_config=_extended_low_z_integrator_config(
            species=species_with_reion,
            z_final=z_final,
            gamma_t_override=lambda eta: 1.0e15,
        ),
        runtime_controls=_runtime_controls(tier=SolverTier.TIER_B_PSTF),
        feature_flags=_feature_flags(tier=SolverTier.TIER_B_PSTF),
        release=_release("bf05-type-i-reionization-on", stage="research_executable"),
        k_grid_mpc=k_grid,
    )
    run_without_reion = execute_tier_b_solver(
        manifest=_manifest("bass.validation.type_i_reionization_probe"),
        bianchi_type="I",
        species=species_without_reion,
        integrator_config=_extended_low_z_integrator_config(
            species=species_without_reion,
            z_final=z_final,
            gamma_t_override=lambda eta: 1.0e15,
        ),
        runtime_controls=_runtime_controls(tier=SolverTier.TIER_B_PSTF),
        feature_flags=_feature_flags(tier=SolverTier.TIER_B_PSTF),
        release=_release("bf05-type-i-reionization-off", stage="research_executable"),
        k_grid_mpc=k_grid,
    )

    metadata_on = run_with_reion.solver_output.metadata
    metadata_off = run_without_reion.solver_output.metadata
    target_a = 1.0 / (1.0 + float(z_final))
    final_a_error = abs(float(run_with_reion.integration_result.a[-1]) - target_a) / target_a
    probe_available = (
        metadata_on["source_builder_low_z_probe_available"] is True
        and metadata_off["source_builder_low_z_probe_available"] is True
        and metadata_on["source_builder_low_z_probe_status"] == "available"
        and metadata_off["source_builder_low_z_probe_status"] == "available"
    )
    claim_statuses = (
        metadata_on["reionization_source_claim_status"] == "bounded_live_low_z_delta"
        and metadata_off["reionization_source_claim_status"] == "reionization_disabled"
        and metadata_on["visibility_reionization_mode"] == "tanh"
        and metadata_off["visibility_reionization_mode"] == "disabled"
    )
    low_z_visibility_delta = float(metadata_on["source_builder_low_z_visibility"]) - float(
        metadata_off["source_builder_low_z_visibility"]
    )
    low_z_gpi_delta = abs(float(metadata_on["source_builder_low_z_gpi_m0"])) - abs(
        float(metadata_off["source_builder_low_z_gpi_m0"])
    )
    regression_passed = (
        metadata_on["source_propagator_status"] == "exact"
        and metadata_on["source_propagator_realization"] == "bianchi_i_matrix_exact"
        and metadata_on["source_builder_low_z_probe_z"] == float(z_probe)
        and metadata_off["source_builder_low_z_probe_z"] == float(z_probe)
    )

    checks = (
        ExecutableCheckEvidence(
            check_id="extended_runtime_reaches_low_z_probe",
            category="baseline_reproduction",
            passed=bool(probe_available),
            summary="The extended Type-I runtime reaches the declared low-z probe and exposes live low-z source metadata in both reionization modes.",
        ),
        ExecutableCheckEvidence(
            check_id="reionization_mode_toggle_changes_claim_surface",
            category="adversarial_edge",
            passed=bool(claim_statuses),
            summary="Reionization on/off toggles keep the low-z probe available while preserving distinct claim-status and reionization-mode metadata.",
        ),
        ExecutableCheckEvidence(
            check_id="reionization_increases_low_z_visibility_source",
            category="physics_sanity",
            passed=low_z_visibility_delta > 0.0 and low_z_gpi_delta > 0.0,
            summary="Turning on homogeneous tanh reionization increases the low-z visibility carrier and the visibility-weighted combined-polter magnitude at the declared probe.",
            metric_name="delta_low_z_visibility",
            metric_value=float(low_z_visibility_delta),
            threshold=0.0,
        ),
        ExecutableCheckEvidence(
            check_id="extended_runtime_hits_declared_low_z_endpoint",
            category="numerical_stability",
            passed=float(final_a_error) <= 5.0e-6,
            summary="The extended Type-I runtime reaches the declared low-z endpoint without drifting away from the requested scale factor.",
            metric_name="relative_final_a_error",
            metric_value=float(final_a_error),
            threshold=5.0e-6,
        ),
        ExecutableCheckEvidence(
            check_id="extended_runtime_preserves_exact_type_i_propagator",
            category="regression",
            passed=bool(regression_passed),
            summary="The extended low-z run keeps the exact Type-I propagator and the declared low-z probe contract attached to the native route.",
        ),
    )
    status: ValidationOutcome = "pass" if all(check.passed for check in checks) else "fail"
    return ExecutableCampaignEvidence(
        campaign_id="validation.bass_type_i_extended_reionization_probe",
        status=status,
        bianchi_type="I",
        cutoffs=(4,),
        theorem_refs=("V8_bass_native_runtime_bridge",),
        null_manifest_refs=("null.bass.type_i_native_runtime",),
        injection_manifest_refs=("validation.injection.native_seed_startup",),
        runbook_refs=("runbook.bass_native_runtime",),
        no_claim_conditions=(
            "tier_a_validation_bridge_only",
            "non_type_i_exact_propagator_missing",
            "homogeneous_reionization_only",
            "direction_resolved_reionization_microphysics_missing",
        ),
        checks=checks,
        artifact_refs=("bass.validation.type_i_reionization_probe", "bass.runtime.trace"),
        preferred_axis_delta_deg=0.0,
        tier_a_tier_b_max_relative_l2=0.0,
        cutoff_max_relative_delta=0.0,
        notes=(
            "This executable evidence validates only an extended Type-I low-z probe path, not the shipped BF-05 default runtime gate.",
            "The probe is intentionally bounded to homogeneous tanh reionization wiring and does not promote direction-resolved microphysics claims.",
            "Passing this campaign does not promote non-Type-I exact propagators or full BiPoSH science claims.",
        ),
    )


@lru_cache(maxsize=16)
def _representative_family_orthogonal_run(
    bianchi_type: str,
):
    species = SpeciesBackgroundRegistry.from_planck2018(
        recombination_warning_policy="ignore",
    )
    return execute_tier_b_solver(
        manifest=_manifest(f"bass.validation.representative_family_sweep.{bianchi_type}.orthogonal"),
        bianchi_type=bianchi_type,
        species=species,
        integrator_config=_family_integrator_config(
            bianchi_type=bianchi_type,
            beta=0.0,
            gamma_t_override=lambda eta: 1.0e15,
        ),
        runtime_controls=_runtime_controls(tier=SolverTier.TIER_B_PSTF),
        feature_flags=_feature_flags(tier=SolverTier.TIER_B_PSTF),
        release=_release(
            f"prm02-{bianchi_type}-orthogonal",
            stage="research_executable",
        ),
        k_grid_mpc=np.array([1.0e-4, 2.0e-4], dtype=np.float64),
    )


@lru_cache(maxsize=16)
def _representative_family_tilt_failure(
    bianchi_type: str,
    tilt_probe_beta: float,
) -> str:
    species = SpeciesBackgroundRegistry.from_planck2018(
        recombination_warning_policy="ignore",
    )
    try:
        execute_tier_b_solver(
            manifest=_manifest(f"bass.validation.representative_family_sweep.{bianchi_type}.tilted"),
            bianchi_type=bianchi_type,
            species=species,
            integrator_config=_family_integrator_config(
                bianchi_type=bianchi_type,
                beta=float(tilt_probe_beta),
                gamma_t_override=lambda eta: 1.0e15,
            ),
            runtime_controls=_runtime_controls(tier=SolverTier.TIER_B_PSTF),
            feature_flags=_feature_flags(tier=SolverTier.TIER_B_PSTF),
            release=_release(
                f"prm02-{bianchi_type}-tilted",
                stage="research_executable",
            ),
            k_grid_mpc=np.array([1.0e-4, 2.0e-4], dtype=np.float64),
        )
    except CodazziProjectionError as exc:
        return str(exc)
    raise ValueError(
        "representative tilted branch unexpectedly executed without a controlled Codazzi block"
    )


def _representative_family_sweep_bundle(
    *,
    tilt_probe_beta: float,
) -> ExecutableCampaignEvidence:
    orthogonal_runs = {
        label: _representative_family_orthogonal_run(label)
        for label in _REPRESENTATIVE_FAMILIES
    }
    tilt_failures = {
        label: _representative_family_tilt_failure(label, float(tilt_probe_beta))
        for label in _REPRESENTATIVE_FAMILIES
    }

    orthogonal_runnable = all(
        run.solver_output.metadata["bianchi_branch"] == "orthogonal"
        and run.execution_plan.runtime_decision.propagation_status == "pending"
        and run.solver_output.metadata["solver_domain_scope"] == "all_11_bianchi_types"
        for run in orthogonal_runs.values()
    )
    algebra_aware_realizations = all(
        run.solver_output.metadata["source_propagator_realization"]
        == _REPRESENTATIVE_PROPAGATOR_REALIZATIONS[label][0]
        and run.solver_output.metadata["source_propagator_status"]
        == _REPRESENTATIVE_PROPAGATOR_REALIZATIONS[label][1]
        and run.solver_output.metadata["theory_family"] == f"{label}_orthogonal"
        for label, run in orthogonal_runs.items()
    )
    finite_outputs = all(
        np.all(np.isfinite(np.asarray(run.solver_output.alm_T["values"], dtype=np.float64)))
        and np.all(np.isfinite(np.asarray(run.solver_output.alm_E["values"], dtype=np.float64)))
        and bool(run.solver_output.metadata["propagator_ready"])
        for run in orthogonal_runs.values()
    )
    metadata_consistency = all(
        run.solver_output.metadata["tilt_boost_separation"] == "explicit_nonmerged"
        and run.solver_output.metadata["global_tilt_contract"]
        == "orthogonal_branch_zero_global_tilt"
        and run.solver_output.metadata["local_boost_contract"]
        == "observer_side_only_not_applied_in_bass_output"
        for run in orthogonal_runs.values()
    )
    tilt_block_honesty = all(
        _REPRESENTATIVE_TILT_BLOCKERS[label] in failure
        for label, failure in tilt_failures.items()
    )

    checks = (
        ExecutableCheckEvidence(
            check_id="representative_orthogonal_families_run_end_to_end",
            category="baseline_reproduction",
            passed=bool(orthogonal_runnable),
            summary="Representative orthogonal families I, V, VII_0, and VIII execute end-to-end on the bounded low-ell native Tier-B path.",
        ),
        ExecutableCheckEvidence(
            check_id="representative_tilted_branches_fail_controlledly",
            category="adversarial_edge",
            passed=bool(tilt_block_honesty),
            summary="Representative tilted branches remain explicit controlled blocks at the Codazzi stage instead of silently degrading into orthogonal or local-boost behavior.",
        ),
        ExecutableCheckEvidence(
            check_id="representative_family_realizations_are_algebra_aware",
            category="physics_sanity",
            passed=bool(algebra_aware_realizations),
            summary="Representative orthogonal family runs keep algebra-aware propagator realizations and theory-family metadata attached to the output payload.",
        ),
        ExecutableCheckEvidence(
            check_id="representative_family_outputs_stay_finite_on_bounded_low_ell_grid",
            category="numerical_stability",
            passed=bool(finite_outputs),
            summary="Representative orthogonal family runs keep bounded low-ell outputs finite and propagator-ready on the shipped native grid.",
        ),
        ExecutableCheckEvidence(
            check_id="representative_family_sweep_preserves_tilt_boost_contracts",
            category="regression",
            passed=bool(metadata_consistency),
            summary="Representative family sweep outputs keep global tilt, local boost, and orthogonal-branch contracts explicit and non-merged for downstream HTT/MIO/TSC consumers.",
        ),
    )
    status: ValidationOutcome = "pass" if all(check.passed for check in checks) else "fail"
    return ExecutableCampaignEvidence(
        campaign_id="validation.bass_representative_family_sweep",
        status=status,
        bianchi_type="I,V,VII_0,VIII",
        cutoffs=(4,),
        theorem_refs=("V8_bass_representative_family_sweep",),
        null_manifest_refs=("null.bass.representative_family_sweep",),
        injection_manifest_refs=("validation.injection.representative_family_seed_startup",),
        runbook_refs=("runbook.bass_representative_family_sweep",),
        no_claim_conditions=(
            "representative_family_sweep_only",
            "representative_tilted_runtime_blocked",
            "non_type_i_exact_propagator_missing",
            "late_time_reionization_window_missing",
            "direction_resolved_reionization_microphysics_missing",
        ),
        checks=checks,
        artifact_refs=("bass.validation.representative_family_sweep", "bass.runtime.trace"),
        preferred_axis_delta_deg=0.0,
        tier_a_tier_b_max_relative_l2=0.0,
        cutoff_max_relative_delta=0.0,
        notes=(
            "This campaign validates the bounded preliminary representative-family sweep only.",
            "Orthogonal branches are executable for I, V, VII_0, and VIII on the current native Tier-B route.",
            "Tilted representative branches remain explicit Codazzi-stage blocks on the current global-tilt runtime construction and are treated as no-claim conditions rather than silent fallbacks.",
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


@lru_cache(maxsize=8)
def build_representative_family_sweep_evidence(
    *,
    tilt_probe_beta: float = 1.0e-6,
) -> ExecutableCampaignEvidence:
    """Return executable evidence for the bounded representative preliminary sweep."""
    if tilt_probe_beta <= 0.0:
        raise ValueError("tilt_probe_beta must be positive")
    return _representative_family_sweep_bundle(
        tilt_probe_beta=float(tilt_probe_beta),
    )


@lru_cache(maxsize=8)
def build_type_i_reionization_probe_evidence(
    *,
    z_probe: float = 8.0,
    z_final: float = 4.0,
) -> ExecutableCampaignEvidence:
    """Return executable evidence for the bounded extended low-z Type-I probe."""
    if z_probe <= 0.0:
        raise ValueError("z_probe must be positive")
    if z_final >= z_probe:
        raise ValueError("z_final must be smaller than z_probe to cover the declared low-z probe")
    return _type_i_reionization_probe_bundle(
        z_probe=float(z_probe),
        z_final=float(z_final),
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


def representative_family_sweep_payload(
    *,
    tilt_probe_beta: float = 1.0e-6,
) -> dict[str, object]:
    """JSON-ready payload for the representative-family preliminary sweep evidence."""
    return asdict(
        build_representative_family_sweep_evidence(
            tilt_probe_beta=tilt_probe_beta,
        )
    )


def type_i_reionization_probe_payload(
    *,
    z_probe: float = 8.0,
    z_final: float = 4.0,
) -> dict[str, object]:
    """JSON-ready payload for the bounded extended low-z Type-I probe evidence."""
    return asdict(
        build_type_i_reionization_probe_evidence(
            z_probe=z_probe,
            z_final=z_final,
        )
    )
