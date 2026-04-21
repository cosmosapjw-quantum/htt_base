from __future__ import annotations

import numpy as np
import pytest

from common.contracts import ArtifactManifest

from bass.background.bianchi_types import get_type
from bass.background.einstein_bianchi import BianchiCosmology
from bass.forward.ver2_solver_output import (
    BassReleaseMetadata,
    solver_core_output_to_payload,
)
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
    execute_tier_b_solver,
    execute_tier_b_lowell_solver,
)
from bass.spectrum import CutoffCampaignSpec
from bass.species.registry import SpeciesBackgroundRegistry


def _manifest() -> ArtifactManifest:
    return ArtifactManifest(
        artifact_id="bass.ver2.tier_b.smoke",
        artifact_path="artifacts/bass/ver2_tier_b_smoke.json",
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


def _release() -> BassReleaseMetadata:
    return BassReleaseMetadata(
        release_stage="research_candidate",
        run_label="tier-b-smoke",
        config_hash="cfg-hash",
        code_version="ver2-test",
        schema_version="1.0.0",
        git_commit="test-commit",
        random_seed=42,
    )


def _runtime_controls() -> RuntimeControlBlock:
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


def _feature_flags() -> SolverFeatureFlags:
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


def test_execute_tier_b_solver_consumes_live_s1_s2_s3_hooks() -> None:
    species = SpeciesBackgroundRegistry.from_planck2018()
    run = execute_tier_b_solver(
        manifest=_manifest(),
        bianchi_type="I",
        species=species,
        integrator_config=_integrator_config(),
        runtime_controls=_runtime_controls(),
        feature_flags=_feature_flags(),
        release=_release(),
        k_grid_mpc=np.array([1.0e-4, 2.0e-4], dtype=np.float64),
        cutoff_spec=CutoffCampaignSpec(
            cutoffs=(4, 6),
            closure_name="tier_b_tca",
            baseline_cutoff=4,
        ),
    )

    assert run.execution_plan.runtime_decision.owner == "BASS"
    assert run.execution_plan.runtime_decision.propagation_status == "validated"
    assert run.trace.seed_projection.projection_ready is True
    assert np.isfinite(run.trace.startup_gate.gamma_T_over_H)
    assert run.trace.startup_gate.threshold == 100.0
    assert run.trace.thomson_probe.source_ready is True
    assert run.trace.visibility_source.contract.events is not None
    assert run.trace.geodesic_probe.direction_derivative.shape == (3,)
    assert run.integration_result.solver_info["tier_b_core_owner"] == "ver2_s1s2_native"
    assert run.solver_output.metadata["propagator_ready"] is True
    assert run.solver_output.metadata["tier_b_core_owner"] == "ver2_s1s2_native"
    assert run.solver_output.metadata["source_builder_scope"] == "theta0_plus_pi_quadrupole_ver2_native"
    assert run.solver_output.alm_T["representation"] == "ver2_native_pstf_final_slice"
    assert run.cutoff_campaign is not None
    assert set(run.cutoff_campaign.runtime_seconds) == {4, 6}
    assert run.cutoff_campaign.deltas[4][0].relative_delta == 0.0


def test_execute_tier_b_solver_is_deterministic_for_same_inputs() -> None:
    species = SpeciesBackgroundRegistry.from_planck2018()
    kwargs = dict(
        manifest=_manifest(),
        bianchi_type="I",
        species=species,
        integrator_config=_integrator_config(),
        runtime_controls=_runtime_controls(),
        feature_flags=_feature_flags(),
        release=_release(),
        k_grid_mpc=np.array([1.0e-4, 2.0e-4], dtype=np.float64),
    )
    run_1 = execute_tier_b_solver(**kwargs)
    run_2 = execute_tier_b_solver(**kwargs)

    payload_1 = solver_core_output_to_payload(run_1.solver_output)
    payload_2 = solver_core_output_to_payload(run_2.solver_output)

    assert payload_1["metadata"] == payload_2["metadata"]
    assert payload_1["deterministic_template"] == payload_2["deterministic_template"]
    np.testing.assert_allclose(
        np.asarray(payload_1["alm_T"]["values"], dtype=np.float64),
        np.asarray(payload_2["alm_T"]["values"], dtype=np.float64),
    )
    np.testing.assert_allclose(
        np.asarray(payload_1["alm_E"]["values"], dtype=np.float64),
        np.asarray(payload_2["alm_E"]["values"], dtype=np.float64),
    )


def test_execute_tier_b_lowell_solver_is_a_compatibility_alias(monkeypatch: pytest.MonkeyPatch) -> None:
    import bass.hierarchy.integrator as legacy_integrator

    def _boom(*args, **kwargs):
        raise AssertionError("legacy Lowell integrator should not be touched on the production route")

    monkeypatch.setattr(legacy_integrator, "LowellBianchiIntegrator", _boom)

    species = SpeciesBackgroundRegistry.from_planck2018()
    run = execute_tier_b_lowell_solver(
        manifest=_manifest(),
        bianchi_type="I",
        species=species,
        integrator_config=_integrator_config(),
        runtime_controls=_runtime_controls(),
        feature_flags=_feature_flags(),
        release=_release(),
        k_grid_mpc=np.array([1.0e-4, 2.0e-4], dtype=np.float64),
    )

    assert run.integration_result.solver_info["tier_b_core_owner"] == "ver2_s1s2_native"
