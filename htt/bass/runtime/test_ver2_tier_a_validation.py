from __future__ import annotations

import numpy as np
import pytest

from common.contracts import ArtifactManifest

from bass.background.bianchi_types import get_type
from bass.forward.ver2_solver_output import BassReleaseMetadata
from bass.hierarchy.integrator import IntegratorConfig
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


def _manifest(artifact_id: str) -> ArtifactManifest:
    return ArtifactManifest(
        artifact_id=artifact_id,
        artifact_path=f"artifacts/bass/{artifact_id.replace('.', '_')}.json",
        owner="BASS",
        implementation_scope="canonical_BASS",
        claim_tier="conditional",
        production_status="production_candidate",
        created_by="pytest",
        git_commit="test-commit",
        config_hash="cfg-hash",
        input_hashes=["species-hash"],
        code_version="ver2-test",
        schema_version="1.0.0",
        required_gates=["runtime", "propagator"],
        passed_gates=["runtime"],
    )


def _tier_a_release() -> BassReleaseMetadata:
    return BassReleaseMetadata(
        release_stage="validation_reference",
        run_label="tier-a-validation",
        config_hash="cfg-hash",
        code_version="ver2-test",
        schema_version="1.0.0",
        git_commit="test-commit",
        random_seed=42,
    )


def _tier_b_release() -> BassReleaseMetadata:
    return BassReleaseMetadata(
        release_stage="research_candidate",
        run_label="tier-b-smoke",
        config_hash="cfg-hash",
        code_version="ver2-test",
        schema_version="1.0.0",
        git_commit="test-commit",
        random_seed=42,
    )


def _tier_a_controls() -> RuntimeControlBlock:
    return RuntimeControlBlock(
        tier=SolverTier.TIER_A_ANGULAR,
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
        low_resolution_reference=False,
    )


def _tier_b_controls() -> RuntimeControlBlock:
    return RuntimeControlBlock(
        tier=SolverTier.TIER_B_PSTF,
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


def _tier_a_flags() -> SolverFeatureFlags:
    return SolverFeatureFlags(
        background_dynamics=FeatureStatus.EXACT,
        photon_transport=FeatureStatus.EXACT,
        thomson_collision=FeatureStatus.EXACT,
        visibility_history=FeatureStatus.EXACT,
        source_propagator=FeatureStatus.EXACT,
        checkpoint_restart=FeatureStatus.DISABLED,
    )


def _tier_b_flags() -> SolverFeatureFlags:
    return SolverFeatureFlags(
        background_dynamics=FeatureStatus.APPROXIMATE,
        photon_transport=FeatureStatus.APPROXIMATE,
        thomson_collision=FeatureStatus.APPROXIMATE,
        visibility_history=FeatureStatus.APPROXIMATE,
        source_propagator=FeatureStatus.APPROXIMATE,
        checkpoint_restart=FeatureStatus.DISABLED,
    )


def _integrator_config() -> IntegratorConfig:
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
        gamma_T_override=lambda eta: 500.0,
    )


from bass.background.einstein_bianchi import BianchiCosmology


def test_execute_tier_a_validation_solver_builds_reference_output() -> None:
    species = SpeciesBackgroundRegistry.from_planck2018()
    run = execute_tier_a_validation_solver(
        manifest=_manifest("bass.ver2.tier_a.validation"),
        bianchi_type="I",
        species=species,
        integrator_config=_integrator_config(),
        runtime_controls=_tier_a_controls(),
        feature_flags=_tier_a_flags(),
        release=_tier_a_release(),
        k_grid_mpc=np.array([1.0e-4, 2.0e-4], dtype=np.float64),
    )

    assert run.execution_plan.runtime_controls.tier is SolverTier.TIER_A_ANGULAR
    assert run.solver_output.metadata["solver_tier"] == "tier_a_angular"
    assert run.solver_output.metadata["propagator_mode"] == "flrw_validation"
    assert run.solver_output.metadata["validation_reference"] is True
    assert run.trace.reference_scope == "validation_only_angular_truth"
    assert run.trace.off_diagonal_strategy == "dense_matrix"
    assert set(run.trace.dl_reference) >= {"TT", "EE", "TE"}


def test_execute_tier_a_validation_solver_requires_tier_a_controls() -> None:
    species = SpeciesBackgroundRegistry.from_planck2018()
    with pytest.raises(ValueError, match="Tier A runtime controls"):
        execute_tier_a_validation_solver(
            manifest=_manifest("bass.ver2.tier_a.invalid"),
            bianchi_type="I",
            species=species,
            integrator_config=_integrator_config(),
            runtime_controls=_tier_b_controls(),
            feature_flags=_tier_a_flags(),
            release=_tier_a_release(),
            k_grid_mpc=np.array([1.0e-4, 2.0e-4], dtype=np.float64),
        )


def test_compare_tier_a_to_tier_b_reports_match_for_shared_bridge() -> None:
    species = SpeciesBackgroundRegistry.from_planck2018()
    tier_a_run = execute_tier_a_validation_solver(
        manifest=_manifest("bass.ver2.tier_a.compare"),
        bianchi_type="I",
        species=species,
        integrator_config=_integrator_config(),
        runtime_controls=_tier_a_controls(),
        feature_flags=_tier_a_flags(),
        release=_tier_a_release(),
        k_grid_mpc=np.array([1.0e-4, 2.0e-4], dtype=np.float64),
    )
    tier_b_run = execute_tier_b_solver(
        manifest=_manifest("bass.ver2.tier_b.compare"),
        bianchi_type="I",
        species=species,
        integrator_config=_integrator_config(),
        runtime_controls=_tier_b_controls(),
        feature_flags=_tier_b_flags(),
        release=_tier_b_release(),
        k_grid_mpc=np.array([1.0e-4, 2.0e-4], dtype=np.float64),
        cutoff_spec=CutoffCampaignSpec(
            cutoffs=(4, 6),
            closure_name="tier_b_tca",
            baseline_cutoff=4,
        ),
    )

    comparison = compare_tier_a_to_tier_b(tier_a_run, tier_b_run, tolerance=5.0e-2)
    assert comparison.ell_grid_match is True
    assert comparison.k_grid_match is True
    assert comparison.passed is True
    assert comparison.preferred_axis_delta_deg == pytest.approx(0.0)
    for channel in ("TT", "EE", "TE"):
        assert comparison.relative_l2_by_channel[channel] <= 5.0e-2
        assert comparison.max_abs_delta_by_channel[channel] >= 0.0
