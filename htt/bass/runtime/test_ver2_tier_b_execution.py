from __future__ import annotations

import numpy as np
import pytest

from common.contracts import ArtifactManifest

from bass.background import CodazziProjectionError
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
    load_tier_b_restart_checkpoint,
    resume_tier_b_solver_from_checkpoint,
)
from bass.spectrum import CutoffCampaignSpec
from bass.species.registry import SpeciesBackgroundRegistry
from bass.hierarchy.pstf_tensor import unpack_hierarchy


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


def _runtime_controls_with_owner(owner: str) -> RuntimeControlBlock:
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
        tilt_background_owner=owner,
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


def _checkpoint_feature_flags() -> SolverFeatureFlags:
    return SolverFeatureFlags(
        background_dynamics=FeatureStatus.APPROXIMATE,
        photon_transport=FeatureStatus.APPROXIMATE,
        thomson_collision=FeatureStatus.APPROXIMATE,
        visibility_history=FeatureStatus.APPROXIMATE,
        source_propagator=FeatureStatus.APPROXIMATE,
        checkpoint_restart=FeatureStatus.APPROXIMATE,
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
        gamma_T_override=lambda eta: 1.0e15,
    )


def _family_integrator_config(
    bianchi_type: str,
    *,
    beta: float = 0.0,
    v_hat_e: tuple[float, float, float] = (1.0, 0.0, 0.0),
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
            v_hat_e=v_hat_e,
        ),
        gamma_T_over_H_threshold=100.0,
        gamma_T_override=lambda eta: 1.0e15,
    )


def _representative_tilt_direction(bianchi_type: str) -> tuple[float, float, float]:
    return {
        "V": (1.0, 0.0, 0.0),
        "VII_0": (1.0, 0.0, 0.0),
        "VIII": (0.0, 1.0, 0.0),
    }.get(bianchi_type, (1.0, 0.0, 0.0))


def _low_z_integrator_config(
    species: SpeciesBackgroundRegistry,
    *,
    z_final: float = 4.0,
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
        gamma_T_override=lambda eta: 1.0e15,
    )


def _checkpoint_runtime_controls(path_template: str) -> RuntimeControlBlock:
    return RuntimeControlBlock(
        tier=SolverTier.TIER_B_PSTF,
        integrator_family=IntegratorFamily.IMEX_SPLIT,
        coupling_mode=CouplingMode.BACKGROUND_THEN_RADIATION,
        multipole_cutoff=4,
        rtol=1.0e-6,
        atol=1.0e-9,
        checkpoint=CheckpointPolicy(
            enabled=True,
            every_n_steps=4,
            path_template=path_template,
        ),
        constraint_projection=ConstraintProjectionPolicy(
            enabled=True,
            every_n_steps=4,
            status=FeatureStatus.APPROXIMATE,
        ),
        random_seed=42,
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
    assert run.execution_plan.runtime_decision.propagation_status == "pending"
    assert run.trace.seed_projection.projection_ready is True
    assert np.isfinite(run.trace.startup_gate.gamma_T_over_H)
    assert run.trace.startup_gate.threshold == 100.0
    assert run.trace.startup_state is not None
    initial_T = unpack_hierarchy(run.integration_result.photon_T_tower[0], run.integration_result.L_max)
    initial_E = unpack_hierarchy(run.integration_result.photon_E_tower[0], run.integration_result.L_max)
    initial_nu = unpack_hierarchy(run.integration_result.neutrino_tower[0], run.integration_result.L_max)
    assert initial_T.tensors[1].components[1] != 0.0
    assert initial_T.tensors[2].components[2] == pytest.approx(run.trace.startup_state.theta_2)
    assert initial_E.tensors[2].components[2] == pytest.approx(run.trace.startup_state.E_2)
    assert initial_nu.tensors[0].components[0] == pytest.approx(run.integration_result.neutrino_reduced[0, 0])
    assert initial_nu.tensors[1].components[1] == pytest.approx(run.integration_result.neutrino_reduced[0, 1])
    assert initial_nu.tensors[2].components[2] == pytest.approx(run.integration_result.neutrino_reduced[0, 2])
    assert initial_nu.tensors[3].components[3] == pytest.approx(run.integration_result.neutrino_reduced[0, 3])
    assert run.trace.thomson_probe.source_ready is True
    assert run.trace.visibility_source.contract.events is not None
    assert run.trace.geodesic_probe.direction_derivative.shape == (3,)
    assert run.integration_result.solver_info["solver_method"] == "IMEX_MIDPOINT_BDF"
    assert run.integration_result.solver_info["requested_integrator_family"] == "imex_split"
    assert run.integration_result.solver_info["resolved_solver_method"] == "IMEX_MIDPOINT_BDF"
    assert run.integration_result.solver_info["executor_realization"] == "native_imex_midpoint_bdf_split"
    assert run.integration_result.solver_info["solver_family_realization"] == "native_imex_midpoint_bdf_split"
    assert run.integration_result.solver_info["tier_b_core_owner"] == "ver2_s1s2_native"
    assert run.integration_result.solver_info["seed_factory_owner"] == "family_backend.seed_factory"
    assert run.integration_result.solver_info["seed_factory_mode"] == "flrw_like_regular"
    assert run.integration_result.solver_info["seed_family"] == "I"
    assert run.integration_result.solver_info["seed_branch"] == "orthogonal"
    assert run.integration_result.solver_info["layout_operator_consumed"] is True
    assert run.integration_result.solver_info["layout_collision_operator_source"] == "mode_ops.A_coll_diagonal"
    assert run.integration_result.solver_info["layout_source_template_consumed"] is True
    assert run.integration_result.solver_info["layout_source_template_channel"] == "canonical_projection.src_block"
    assert run.integration_result.solver_info["layout_source_block_norm"] > 0.0
    assert run.integration_result.solver_info["layout_source_block_owner"] == "mode_ops_source_template"
    assert run.integration_result.solver_info["layout_source_history_sample_count"] == len(
        run.integration_result.eta
    )
    assert run.integration_result.solver_info["startup_manifold_applied"] is True
    assert run.solver_output.metadata["propagator_ready"] is True
    assert run.solver_output.metadata["propagator_readiness"] == "exact"
    assert run.solver_output.metadata["propagator_exactness"] == "exact"
    assert run.solver_output.metadata["covariance_readiness"] == "proxy"
    assert run.solver_output.metadata["source_propagator_status"] == "exact"
    assert run.solver_output.metadata["source_propagator_requested_status"] == "approximate"
    assert run.solver_output.metadata["source_propagator_rotation_status"] == "disabled"
    assert run.solver_output.metadata["source_propagator_realization"] == "bianchi_i_matrix_exact"
    assert run.solver_output.metadata["tier_b_core_owner"] == "ver2_s1s2_native"
    assert run.solver_output.metadata["neutrino_hierarchy_mode"] == "full_pstf_with_reduced_summary_export"
    assert run.solver_output.metadata["solver_method"] == "IMEX_MIDPOINT_BDF"
    assert run.solver_output.metadata["requested_integrator_family"] == "imex_split"
    assert run.solver_output.metadata["resolved_solver_method"] == "IMEX_MIDPOINT_BDF"
    assert run.solver_output.metadata["executor_realization"] == "native_imex_midpoint_bdf_split"
    assert run.solver_output.metadata["seed_factory_owner"] == "family_backend.seed_factory"
    assert run.solver_output.metadata["seed_factory_mode"] == "flrw_like_regular"
    assert run.solver_output.metadata["layout_contract_consumed"] is True
    assert run.solver_output.metadata["layout_operator_consumed"] is True
    assert run.solver_output.metadata["layout_collision_operator_source"] == "mode_ops.A_coll_diagonal"
    assert run.solver_output.metadata["layout_source_template_consumed"] is True
    assert run.solver_output.metadata["layout_source_template_channel"] == "canonical_projection.src_block"
    assert run.solver_output.metadata["layout_source_block_norm"] > 0.0
    assert run.solver_output.metadata["layout_source_block_owner"] == "mode_ops_source_template"
    assert run.solver_output.metadata["layout_source_history_sample_count"] == len(
        run.integration_result.eta
    )
    assert run.solver_output.metadata["layout_sector_order"] == [
        "ph_I",
        "ph_E",
        "ph_B",
        "nu_I",
        "baryon",
        "cdm",
        "src",
    ]
    assert run.solver_output.metadata["runtime_resolved_sector_order"] == (
        "ph_I",
        "ph_E",
        "nu_I",
    )
    assert run.solver_output.metadata["canonical_projection_available"] is True
    assert run.solver_output.metadata["canonical_projection_mode"] == (
        "single_live_mode_label_with_zero_filled_residual_layout"
    )
    assert run.solver_output.metadata["canonical_projection_covered_mode_labels"] == ["m0"]
    assert run.solver_output.metadata["canonical_projection_sector_status"]["src"] == (
        "mode_ops_source_template"
    )
    assert run.solver_output.metadata["b_mode_runtime_available"] is False
    assert run.solver_output.metadata["b_mode_payload_status"] == "zero_filled_layout_contract_only"
    assert run.solver_output.metadata["tilt_background_owner"] == "fixed_velocity_closure"
    assert run.solver_output.metadata["off_axis_support"] is False
    assert run.solver_output.metadata["off_axis_fallback_applied"] is False
    assert run.solver_output.metadata["source_builder_scope"] == "theta0_plus_combined_polter_visibility_ver2_native"
    assert run.solver_output.metadata["source_builder_combined_polter"] is True
    assert run.solver_output.metadata["source_builder_visibility_weighted_polter"] is True
    assert run.solver_output.metadata["visibility_reionization_mode"] == "tanh"
    assert run.solver_output.metadata["source_builder_low_z_probe_available"] is False
    assert run.solver_output.metadata["source_builder_low_z_probe_status"] == "not_covered_by_runtime_domain"
    assert run.solver_output.metadata["reionization_source_claim_status"] == "unavailable_due_to_runtime_domain"
    assert run.solver_output.metadata["startup_manifold_applied"] is True
    assert run.solver_output.alm_T["representation"] == "ver2_native_pstf_sphere_reconstruction"
    assert run.solver_output.alm_T["coefficient_representation"] == "ver2_native_pstf_final_slice"
    assert np.asarray(run.solver_output.alm_T["sphere_directions"], dtype=np.float64).shape == (231, 3)
    assert run.cutoff_campaign is not None
    assert set(run.cutoff_campaign.runtime_seconds) == {4, 6}
    assert run.cutoff_campaign.deltas[4][0].relative_delta == 0.0
    registry = run.solver_output.metadata["gate_registry"]
    assert registry["output_split_gate"].gate_name == "output_split_gate"
    assert registry["tilt_boost_separation_gate"].passed is True
    assert registry["ic_provenance_gate"].passed is True
    assert registry["production_cutoff_gate"].passed is True
    assert registry["background_core_gate"].known_limit_checks["samples"] > 0
    assert registry["background_core_gate"].metadata["matter_model_tag"] == (
        run.trace.background_monitor.matter_model_tag
    )
    assert run.trace.canonical_projection.covered_mode_labels == ("m0",)
    assert run.trace.canonical_projection.sector_status["ph_B"] == "zero_filled_not_evolved"
    assert run.integration_result.neutrino_tower is not None


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


@pytest.mark.parametrize(
    ("bianchi_type", "realization", "status"),
    (
        ("I", "bianchi_i_matrix_exact", "exact"),
        ("V", "class_b_open_matrix_approx", "approximate"),
        ("VII_0", "class_a_helical_matrix_approx", "approximate"),
        ("VIII", "class_a_semisimple_matrix_approx", "approximate"),
    ),
)
def test_representative_orthogonal_families_execute_with_expected_propagator_realizations(
    bianchi_type: str,
    realization: str,
    status: str,
) -> None:
    species = SpeciesBackgroundRegistry.from_planck2018(recombination_warning_policy="ignore")
    run = execute_tier_b_solver(
        manifest=_manifest(),
        bianchi_type=bianchi_type,
        species=species,
        integrator_config=_family_integrator_config(bianchi_type),
        runtime_controls=_runtime_controls(),
        feature_flags=_feature_flags(),
        release=_release(),
        k_grid_mpc=np.array([1.0e-4, 2.0e-4], dtype=np.float64),
    )
    assert run.solver_output.metadata["bianchi_branch"] == "orthogonal"
    assert run.solver_output.metadata["solver_domain_scope"] == "all_11_bianchi_types"
    assert run.solver_output.metadata["theory_family"] == f"{bianchi_type}_orthogonal"
    assert run.solver_output.metadata["source_propagator_realization"] == realization
    assert run.solver_output.metadata["source_propagator_status"] == status
    expected_readiness = "exact" if status == "exact" else "approximate_family_kernel"
    assert run.solver_output.metadata["propagator_readiness"] == expected_readiness
    assert run.solver_output.metadata["propagator_exactness"] == expected_readiness
    assert run.solver_output.metadata["tilt_boost_separation"] == "explicit_nonmerged"
    assert run.solver_output.metadata["global_tilt_contract"] == "orthogonal_branch_zero_global_tilt"
    assert run.execution_plan.runtime_decision.propagation_status == "pending"


@pytest.mark.parametrize(
    ("bianchi_type", "required_policy"),
    (
        ("I", "codazzi_balanced_total_momentum"),
    ),
)
def test_representative_tilted_family_sweep_is_controlledly_blocked(
    bianchi_type: str,
    required_policy: str,
) -> None:
    species = SpeciesBackgroundRegistry.from_planck2018(recombination_warning_policy="ignore")
    with pytest.raises(CodazziProjectionError, match=required_policy):
        execute_tier_b_solver(
            manifest=_manifest(),
            bianchi_type=bianchi_type,
            species=species,
            integrator_config=_family_integrator_config(
                bianchi_type,
                beta=1.0e-6,
                v_hat_e=_representative_tilt_direction(bianchi_type),
            ),
            runtime_controls=_runtime_controls(),
            feature_flags=_feature_flags(),
            release=_release(),
            k_grid_mpc=np.array([1.0e-4, 2.0e-4], dtype=np.float64),
    )


def _seed_projection_tol(run) -> float:
    q_norm = float(np.linalg.norm(run.trace.background_monitor.initial_conditions.matter.q))
    return max(1.0e-10, 1.0e-12 * max(q_norm, 1.0))


@pytest.mark.parametrize(
    ("bianchi_type", "realization", "v_hat_e"),
    (
        ("V", "class_b_open_matrix_approx", (1.0, 0.0, 0.0)),
        ("VII_0", "class_a_helical_matrix_approx", (1.0, 0.0, 0.0)),
        ("VIII", "class_a_semisimple_matrix_approx", (0.0, 1.0, 0.0)),
    ),
)
def test_representative_tilted_executable_families_execute_with_bounded_runtime_contracts(
    bianchi_type: str,
    realization: str,
    v_hat_e: tuple[float, float, float],
) -> None:
    species = SpeciesBackgroundRegistry.from_planck2018(recombination_warning_policy="ignore")
    run = execute_tier_b_solver(
        manifest=_manifest(),
        bianchi_type=bianchi_type,
        species=species,
        integrator_config=_family_integrator_config(bianchi_type, beta=1.0e-6, v_hat_e=v_hat_e),
        runtime_controls=_runtime_controls(),
        feature_flags=_feature_flags(),
        release=_release(),
        k_grid_mpc=np.array([1.0e-4, 2.0e-4], dtype=np.float64),
    )

    assert run.solver_output.metadata["bianchi_branch"] == "tilted"
    assert run.solver_output.metadata["theory_family"] == f"{bianchi_type}_tilted"
    assert run.solver_output.metadata["global_tilt_contract"] == "model_matter_frame_state"
    assert run.solver_output.metadata["tilt_boost_separation"] == "explicit_nonmerged"
    assert run.solver_output.metadata["source_propagator_realization"] == realization
    assert run.solver_output.metadata["source_propagator_status"] == "approximate"
    assert run.solver_output.metadata["propagator_readiness"] == "approximate_family_kernel"
    assert run.solver_output.metadata["tilt_background_owner"] == "fixed_velocity_closure"
    assert run.trace.seed_projection.projection_ready is True
    assert run.trace.seed_projection.projection_mode == "background_codazzi_project"
    assert np.linalg.norm(run.trace.seed_projection.momentum_residual_after) <= _seed_projection_tol(run)
    assert run.execution_plan.runtime_decision.propagation_status == "pending"


def test_nonperturbative_tilt_owner_is_wired_into_runtime_background_and_collision() -> None:
    species = SpeciesBackgroundRegistry.from_planck2018(recombination_warning_policy="ignore")
    run = execute_tier_b_solver(
        manifest=_manifest(),
        bianchi_type="V",
        species=species,
        integrator_config=_family_integrator_config("V", beta=1.0e-3, v_hat_e=(1.0, 0.0, 0.0)),
        runtime_controls=_runtime_controls_with_owner("nonperturbative_tilt_rhs"),
        feature_flags=_feature_flags(),
        release=_release(),
        k_grid_mpc=np.array([1.0e-4, 2.0e-4], dtype=np.float64),
    )

    assert run.trace.background_monitor.matter_model_tag == "tilted_species_registry_dynamic_rapidity"
    assert run.solver_output.metadata["tilt_background_owner"] == "nonperturbative_tilt_rhs"
    assert (
        run.solver_output.metadata["tilt_background_owner_status"]
        == "production_dynamic_nonperturbative_rapidity"
    )
    assert (
        run.solver_output.metadata["nonperturbative_tilt_rhs_status"]
        == "runtime_wired_dynamic_rapidity_owner"
    )
    assert run.trace.thomson_probe.opacity_contract == "electron_frame_tilt_modulated"
    assert run.trace.background_monitor.tilt_rapidity[0] > 0.0
    assert run.trace.background_monitor.tilt_rapidity[-1] <= run.trace.background_monitor.tilt_rapidity[0]


def test_off_axis_tilted_runtime_path_executes_without_fallback() -> None:
    species = SpeciesBackgroundRegistry.from_planck2018(recombination_warning_policy="ignore")
    off_axis = (1.0 / np.sqrt(2.0), 1.0 / np.sqrt(2.0), 0.0)
    run = execute_tier_b_solver(
        manifest=_manifest(),
        bianchi_type="V",
        species=species,
        integrator_config=_family_integrator_config("V", beta=1.0e-6, v_hat_e=off_axis),
        runtime_controls=_runtime_controls(),
        feature_flags=_feature_flags(),
        release=_release(),
        k_grid_mpc=np.array([1.0e-4, 2.0e-4], dtype=np.float64),
    )

    assert run.solver_output.metadata["bianchi_branch"] == "tilted"
    assert run.solver_output.metadata["off_axis_support"] is True
    assert run.solver_output.metadata["off_axis_fallback_applied"] is False
    assert run.solver_output.metadata["off_axis_block_reason"] is None
    assert str(run.integration_result.solver_info["seed_injection_mode"]).startswith(
        "offaxis_tilted_regular_adiabatic_seed"
    )
    assert run.trace.thomson_probe.source_ready is True
    initial_T = unpack_hierarchy(run.integration_result.photon_T_tower[0], run.integration_result.L_max)
    assert np.linalg.norm(np.delete(initial_T.tensors[2].components, 2)) > 0.0


def test_execute_tier_b_solver_can_reach_low_z_reionization_probe_with_extended_eta_domain() -> None:
    species = SpeciesBackgroundRegistry.from_planck2018(recombination_warning_policy="ignore")
    z_final = 4.0
    run = execute_tier_b_solver(
        manifest=_manifest(),
        bianchi_type="I",
        species=species,
        integrator_config=_low_z_integrator_config(species, z_final=z_final),
        runtime_controls=_runtime_controls(),
        feature_flags=_feature_flags(),
        release=_release(),
        k_grid_mpc=np.array([1.0e-4, 2.0e-4], dtype=np.float64),
    )

    assert run.integration_result.eta[-1] == pytest.approx(
        species.bg_table.eta_at_a(1.0 / (1.0 + z_final)),
        rel=5.0e-4,
    )
    assert run.integration_result.a[-1] == pytest.approx(1.0 / (1.0 + z_final), rel=5.0e-6)
    assert run.solver_output.metadata["source_builder_low_z_probe_available"] is True
    assert run.solver_output.metadata["source_builder_low_z_probe_status"] == "available"
    assert run.solver_output.metadata["reionization_source_claim_status"] == "bounded_live_low_z_delta"
    assert run.solver_output.metadata["source_builder_low_z_gpi_m0"] is not None


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


def test_execute_tier_b_solver_injects_seed_even_without_startup_manifold() -> None:
    species = SpeciesBackgroundRegistry.from_planck2018()
    cfg = _integrator_config()
    cfg.gamma_T_override = lambda eta: 1.0
    run = execute_tier_b_solver(
        manifest=_manifest(),
        bianchi_type="I",
        species=species,
        integrator_config=cfg,
        runtime_controls=_runtime_controls(),
        feature_flags=_feature_flags(),
        release=_release(),
        k_grid_mpc=np.array([1.0e-4, 2.0e-4], dtype=np.float64),
    )
    initial_T = unpack_hierarchy(run.integration_result.photon_T_tower[0], run.integration_result.L_max)
    initial_E = unpack_hierarchy(run.integration_result.photon_E_tower[0], run.integration_result.L_max)
    assert run.trace.startup_state is None
    assert run.trace.seed_projection.projection_ready is True
    assert initial_T.tensors[0].components[0] != 0.0
    assert initial_T.tensors[1].components[1] != 0.0
    assert initial_T.tensors[2].components[2] != 0.0
    assert initial_E.tensors[2].components[2] != 0.0


def test_tier_b_checkpoint_resume_reproduces_checkpointed_run(tmp_path) -> None:
    species = SpeciesBackgroundRegistry.from_planck2018()
    path_template = str(tmp_path / "checkpoint_step_{step}.npz")
    controls = _checkpoint_runtime_controls(path_template)
    kwargs = dict(
        manifest=_manifest(),
        bianchi_type="I",
        species=species,
        integrator_config=_integrator_config(),
        runtime_controls=controls,
        feature_flags=_checkpoint_feature_flags(),
        release=_release(),
        k_grid_mpc=np.array([1.0e-4, 2.0e-4], dtype=np.float64),
    )
    full_run = execute_tier_b_solver(**kwargs)

    checkpoint_paths = tuple(full_run.integration_result.solver_info["checkpoint_paths"])
    assert checkpoint_paths
    mid_checkpoint = checkpoint_paths[0]
    checkpoint = load_tier_b_restart_checkpoint(mid_checkpoint)
    assert checkpoint.step_index == 4
    assert checkpoint.structure_label == "I"
    np.testing.assert_allclose(checkpoint.structure_n_diag, np.array([0.0, 0.0, 0.0]))
    assert checkpoint.structure_a_twist == 0.0
    assert checkpoint.tilt_rapidity == 0.0
    np.testing.assert_allclose(checkpoint.tilt_direction, np.array([1.0, 0.0, 0.0]))
    assert checkpoint.direction_convention == "propagation_direction"
    assert checkpoint.n_output == 12
    assert checkpoint.solver_method == "BDF"
    resumed = resume_tier_b_solver_from_checkpoint(
        checkpoint_path=mid_checkpoint,
        **kwargs,
    )

    np.testing.assert_allclose(
        full_run.integration_result.eta,
        resumed.integration_result.eta,
    )
    np.testing.assert_allclose(
        full_run.integration_result.photon_T_tower,
        resumed.integration_result.photon_T_tower,
    )
    np.testing.assert_allclose(
        full_run.integration_result.photon_E_tower,
        resumed.integration_result.photon_E_tower,
    )
    np.testing.assert_allclose(
        np.asarray(full_run.solver_output.alm_T["values"], dtype=np.float64),
        np.asarray(resumed.solver_output.alm_T["values"], dtype=np.float64),
    )
    assert resumed.integration_result.solver_info["restart_used"] is True
    assert resumed.solver_output.metadata["restart_used"] is True


def test_tier_b_checkpoint_rejects_tilt_metadata_mismatch(tmp_path) -> None:
    species = SpeciesBackgroundRegistry.from_planck2018()
    path_template = str(tmp_path / "checkpoint_step_{step}.npz")
    controls = _checkpoint_runtime_controls(path_template)
    base_config = _integrator_config()
    full_run = execute_tier_b_solver(
        manifest=_manifest(),
        bianchi_type="I",
        species=species,
        integrator_config=base_config,
        runtime_controls=controls,
        feature_flags=_checkpoint_feature_flags(),
        release=_release(),
        k_grid_mpc=np.array([1.0e-4, 2.0e-4], dtype=np.float64),
    )
    checkpoint_path = tuple(full_run.integration_result.solver_info["checkpoint_paths"])[0]

    mismatched_config = _integrator_config()
    mismatched_config.bianchi_cosmo = BianchiCosmology(
        structure=get_type("I"),
        beta=0.05,
        v_hat_e=(0.0, 1.0, 0.0),
    )
    with pytest.raises(ValueError, match="tilt_rapidity|tilt_direction"):
        resume_tier_b_solver_from_checkpoint(
            checkpoint_path=checkpoint_path,
            manifest=_manifest(),
            bianchi_type="I",
            species=species,
            integrator_config=mismatched_config,
            runtime_controls=controls,
            feature_flags=_checkpoint_feature_flags(),
            release=_release(),
            k_grid_mpc=np.array([1.0e-4, 2.0e-4], dtype=np.float64),
        )
