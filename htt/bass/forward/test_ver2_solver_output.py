from __future__ import annotations

import numpy as np
import pytest

from common.contracts import ArtifactManifest

from bass.forward import (
    BassReleaseMetadata,
    build_solver_core_output,
    build_solver_core_output_from_native_result,
    build_solver_core_output_from_lowell_result,
    solver_core_output_from_payload,
    solver_core_output_to_payload,
)
from bass.hierarchy.integrator import IntegrationResult, IntegratorConfig
from bass.los import PropagatorMode, SourcePropagatorConfig
from bass.runtime import (
    CheckpointPolicy,
    ConstraintProjectionPolicy,
    CouplingMode,
    FeatureStatus,
    IntegratorFamily,
    RuntimeControlBlock,
    SolverFeatureFlags,
    SolverTier,
)
from bass.species.registry import SpeciesBackgroundRegistry


def _manifest(**overrides) -> ArtifactManifest:
    base = dict(
        artifact_id="bass.ver2.solver.output",
        artifact_path="artifacts/bass/ver2_solver_output.json",
        owner="BASS",
        implementation_scope="canonical_BASS",
        claim_tier="conditional",
        production_status="production_candidate",
        created_by="test-suite",
        git_commit="deadbeef",
        config_hash="cfg-hash",
        input_hashes=["bg", "rad"],
        code_version="0.0-test",
        schema_version="ver2-v0",
    )
    base.update(overrides)
    return ArtifactManifest(**base)


def _controls() -> RuntimeControlBlock:
    return RuntimeControlBlock(
        tier=SolverTier.TIER_B_PSTF,
        integrator_family=IntegratorFamily.IMEX_SPLIT,
        coupling_mode=CouplingMode.BACKGROUND_THEN_RADIATION,
        multipole_cutoff=6,
        rtol=1.0e-6,
        atol=1.0e-9,
        checkpoint=CheckpointPolicy(enabled=False),
        constraint_projection=ConstraintProjectionPolicy(enabled=False),
        random_seed=42,
    )


def _flags() -> SolverFeatureFlags:
    return SolverFeatureFlags(
        background_dynamics=FeatureStatus.APPROXIMATE,
        photon_transport=FeatureStatus.APPROXIMATE,
        thomson_collision=FeatureStatus.APPROXIMATE,
        visibility_history=FeatureStatus.APPROXIMATE,
        source_propagator=FeatureStatus.DISABLED,
        checkpoint_restart=FeatureStatus.DISABLED,
    )


def _live_flags() -> SolverFeatureFlags:
    return SolverFeatureFlags(
        background_dynamics=FeatureStatus.APPROXIMATE,
        photon_transport=FeatureStatus.APPROXIMATE,
        thomson_collision=FeatureStatus.APPROXIMATE,
        visibility_history=FeatureStatus.APPROXIMATE,
        source_propagator=FeatureStatus.APPROXIMATE,
        checkpoint_restart=FeatureStatus.DISABLED,
    )


def _synthetic_result() -> IntegrationResult:
    eta = np.linspace(10.0, 20.0, 10)
    l_max = 6
    size = (l_max + 1) ** 2
    t_tower = np.zeros((eta.size, size), dtype=float)
    e_tower = np.zeros((eta.size, size), dtype=float)
    # ell=0,m=0 -> index 0
    t_tower[:, 0] = np.linspace(1.0e-5, 3.0e-5, eta.size)
    # ell=2 offset 4, indices m=-2,0,+2 -> 4,6,8
    t_tower[:, 4] = np.linspace(-1.0e-6, -2.0e-6, eta.size)
    t_tower[:, 6] = np.linspace(2.0e-6, 4.0e-6, eta.size)
    t_tower[:, 8] = np.linspace(1.5e-6, 2.5e-6, eta.size)
    e_tower[:, 4] = np.linspace(0.5e-6, 0.8e-6, eta.size)
    e_tower[:, 6] = np.linspace(0.8e-6, 1.1e-6, eta.size)
    e_tower[:, 8] = np.linspace(0.6e-6, 0.9e-6, eta.size)
    return IntegrationResult(
        eta=eta,
        a=np.linspace(1.0e-3, 2.0e-3, eta.size),
        Sigma_plus=np.linspace(1.0e-5, 0.8e-5, eta.size),
        Sigma_minus=np.linspace(0.5e-5, 0.2e-5, eta.size),
        photon_T_tower=t_tower,
        photon_E_tower=e_tower,
        neutrino_reduced=np.zeros((eta.size, 4), dtype=float),
        critical_events={"z_eq": 3400.0, "z_star": 1089.0},
        config=IntegratorConfig(
            L_max=l_max,
            eta_initial_mpc=float(eta[0]),
            eta_final_mpc=float(eta[-1]),
            n_output=eta.size,
        ),
        solver_info={"status": 0, "message": "synthetic"},
        tca_active_mask=np.array([True, True, False, False, False], dtype=bool),
    )


def _synthetic_result_with_late_visibility_probe() -> IntegrationResult:
    result = _synthetic_result()
    eta = np.linspace(10.0, 40.0, 24)
    a = np.geomspace(1.0e-3, 1.0, eta.size)
    size = result.photon_T_tower.shape[1]
    t_tower = np.zeros((eta.size, size), dtype=float)
    e_tower = np.zeros((eta.size, size), dtype=float)
    t_tower[:, 0] = np.linspace(1.0e-5, 3.0e-5, eta.size)
    t_tower[:, 4] = np.linspace(-1.0e-6, -2.5e-6, eta.size)
    t_tower[:, 6] = np.linspace(2.0e-6, 4.0e-6, eta.size)
    t_tower[:, 8] = np.linspace(1.5e-6, 2.5e-6, eta.size)
    e_tower[:, 4] = np.linspace(0.5e-6, 0.9e-6, eta.size)
    e_tower[:, 6] = np.linspace(0.8e-6, 1.1e-6, eta.size)
    e_tower[:, 8] = np.linspace(0.6e-6, 0.95e-6, eta.size)
    return IntegrationResult(
        eta=eta,
        a=a,
        Sigma_plus=np.linspace(1.0e-5, 0.8e-5, eta.size),
        Sigma_minus=np.linspace(0.5e-5, 0.2e-5, eta.size),
        photon_T_tower=t_tower,
        photon_E_tower=e_tower,
        neutrino_reduced=np.zeros((eta.size, 4), dtype=float),
        critical_events={"z_eq": 3400.0, "z_star": 1089.0},
        config=result.config.__class__(
            L_max=result.config.L_max,
            eta_initial_mpc=float(eta[0]),
            eta_final_mpc=float(eta[-1]),
            n_output=eta.size,
        ),
        solver_info={"status": 0, "message": "synthetic-late"},
        tca_active_mask=np.array([True, True, False, False, False], dtype=bool),
    )


def test_solver_core_output_requires_bass_manifest_owner() -> None:
    with pytest.raises(ValueError, match="owned by BASS"):
        build_solver_core_output(
            manifest=_manifest(owner="HTT"),
            bianchi_type="I",
            tilt_enabled=False,
            harmonic_basis="pstf",
            eb_sign_convention="explicit_solver_state",
            thomson_mode="electron_frame_projected",
            runtime_controls=_controls(),
            feature_flags=_flags(),
            propagator=SourcePropagatorConfig(
                mode=PropagatorMode.ANISOTROPIC_FORWARD,
                temperature_transport=FeatureStatus.APPROXIMATE,
                polarization_rotation=FeatureStatus.APPROXIMATE,
            ),
            release=BassReleaseMetadata(
                release_stage="skeleton",
                run_label="tier-b-smoke",
                config_hash="cfg-hash",
                code_version="0.0-test",
                schema_version="ver2-v0",
                git_commit="deadbeef",
                random_seed=42,
            ),
        )


def test_solver_core_output_builder_attaches_required_metadata() -> None:
    output = build_solver_core_output(
        manifest=_manifest(),
        bianchi_type="VII_h",
        tilt_enabled=True,
        harmonic_basis="pstf",
        eb_sign_convention="explicit_solver_state",
        thomson_mode="electron_frame_projected",
        runtime_controls=_controls(),
        feature_flags=_flags(),
        propagator=SourcePropagatorConfig(
            mode=PropagatorMode.ANISOTROPIC_FORWARD,
            temperature_transport=FeatureStatus.APPROXIMATE,
            polarization_rotation=FeatureStatus.APPROXIMATE,
        ),
        release=BassReleaseMetadata(
            release_stage="skeleton",
            run_label="tier-b-smoke",
            config_hash="cfg-hash",
            code_version="0.0-test",
            schema_version="ver2-v0",
            git_commit="deadbeef",
            random_seed=42,
        ),
        deterministic_template={"kind": "pending"},
    )
    assert output.metadata["bianchi_type"] == "VII_h"
    assert output.metadata["bianchi_branch"] == "tilted"
    assert output.metadata["solver_domain_scope"] == "all_11_bianchi_types"
    assert output.metadata["global_tilt_contract"] == "model_matter_frame_state"
    assert output.metadata["local_boost_contract"] == "observer_side_only_not_applied_in_bass_output"
    assert output.metadata["tilt_boost_separation"] == "explicit_nonmerged"
    assert output.metadata["theory_family"] == "VII_h_tilted"
    assert output.metadata["observer_neutral"] is True
    assert output.metadata["multipole_cutoff"] == 6
    assert output.metadata["requested_integrator_family"] == "imex_split"
    assert output.metadata["resolved_solver_method"] == "IMEX_MIDPOINT_BDF"
    assert output.metadata["executor_realization"] == "native_imex_midpoint_bdf_split"
    assert output.metadata["tilt_background_owner"] == "fixed_velocity_closure"
    assert output.metadata["off_axis_support"] is False
    assert output.metadata["covariance_readiness"] == "missing"
    assert output.metadata["neutrino_background_readiness"] == "massless_only"
    assert output.metadata["reionization_history_readiness"] == "homogeneous_tanh_only"


def test_native_output_promotes_massive_neutrino_runtime_metadata() -> None:
    species = SpeciesBackgroundRegistry.from_planck2018(
        Sigma_mnu=0.12,
        recombination_warning_policy="ignore",
    )
    output = build_solver_core_output_from_native_result(
        manifest=_manifest(),
        bianchi_type="I",
        result=_synthetic_result(),
        species=species,
        runtime_controls=_controls(),
        feature_flags=_live_flags(),
        release=BassReleaseMetadata(
            release_stage="research_candidate",
            run_label="tier-b-native",
            config_hash="cfg-hash",
            code_version="0.0-test",
            schema_version="ver2-v0",
            git_commit="deadbeef",
            random_seed=42,
        ),
        k_grid_mpc=np.array([1.0e-4, 2.0e-4], dtype=np.float64),
    )
    assert output.metadata["neutrino_background_readiness"] == "massive_fd_background_and_hierarchy"
    assert output.metadata["massive_neutrino_support"] is True
    assert output.metadata["massive_neutrino_block_reason"] is None
    assert output.metadata["massive_neutrino_mass_eV"] == pytest.approx(0.04)


def test_solver_core_output_payload_roundtrips() -> None:
    output = build_solver_core_output(
        manifest=_manifest(),
        bianchi_type="I",
        tilt_enabled=False,
        harmonic_basis="pstf",
        eb_sign_convention="explicit_solver_state",
        thomson_mode="electron_frame_projected",
        runtime_controls=_controls(),
        feature_flags=_flags(),
        propagator=SourcePropagatorConfig(
            mode=PropagatorMode.FLRW_VALIDATION,
            temperature_transport=FeatureStatus.EXACT,
            polarization_rotation=FeatureStatus.DISABLED,
            flrw_validation_only=True,
            kernel_family="flrw_scalar_validation",
        ),
        release=BassReleaseMetadata(
            release_stage="skeleton",
            run_label="tier-a-validation",
            config_hash="cfg-hash",
            code_version="0.0-test",
            schema_version="ver2-v0",
            git_commit="deadbeef",
            random_seed=42,
        ),
        deterministic_template={"kind": "pending"},
    )
    payload = solver_core_output_to_payload(output)
    restored = solver_core_output_from_payload(payload)
    assert restored.metadata == output.metadata
    assert restored.manifest.artifact_id == output.manifest.artifact_id


def test_build_solver_core_output_from_lowell_result_attaches_live_covariance() -> None:
    output = build_solver_core_output_from_lowell_result(
        manifest=_manifest(),
        bianchi_type="VII_h",
        result=_synthetic_result(),
        species=SpeciesBackgroundRegistry.from_planck2018(),
        runtime_controls=_controls(),
        feature_flags=_live_flags(),
        release=BassReleaseMetadata(
            release_stage="research_executable",
            run_label="tier-b-live",
            config_hash="cfg-hash",
            code_version="0.0-test",
            schema_version="ver2-v0",
            git_commit="deadbeef",
            random_seed=42,
        ),
        k_grid_mpc=np.geomspace(1.0e-3, 2.0e-2, 5),
    )
    assert output.metadata["propagator_ready"] is True
    assert output.metadata["propagator_readiness"] == "approximate_family_kernel"
    assert output.metadata["propagator_exactness"] == "approximate_family_kernel"
    assert output.metadata["covariance_readiness"] == "proxy"
    assert output.metadata["source_builder_scope"] == "theta0_plus_combined_polter_visibility_lowell_bridge"
    assert output.metadata["propagator_mode"] == "anisotropic_forward"
    assert output.metadata["source_propagator_status"] == "approximate"
    assert output.metadata["source_propagator_realization"] == "class_b_helical_matrix_approx"
    assert output.metadata["source_builder_combined_polter"] is True
    assert output.metadata["source_builder_visibility_weighted_polter"] is True
    assert output.metadata["visibility_reionization_mode"] == "tanh"
    assert output.metadata["source_builder_low_z_probe_status"] == "not_covered_by_runtime_domain"
    assert output.metadata["reionization_source_claim_status"] == "unavailable_due_to_runtime_domain"
    assert output.anisotropic_covariance is not None
    assert output.deterministic_template["kind"] == "tier_b_lowell_template"
    assert output.alm_T["representation"] == "lowell_pstf_sphere_reconstruction"
    assert output.alm_T["coefficient_representation"] == "lowell_pstf_final_slice"
    assert output.alm_T["quadrature_rule"] == "gauss_legendre_x_uniform_phi_tensor_product"
    assert np.asarray(output.alm_T["sphere_samples"], dtype=np.float64).shape == (435,)
    assert np.asarray(output.alm_T["values"], dtype=np.float64).shape == ((output.alm_T["ell_max"] + 1) ** 2,)


def test_build_solver_core_output_from_native_result_attaches_native_provenance() -> None:
    output = build_solver_core_output_from_native_result(
        manifest=_manifest(),
        bianchi_type="VII_h",
        result=_synthetic_result(),
        species=SpeciesBackgroundRegistry.from_planck2018(),
        runtime_controls=_controls(),
        feature_flags=_live_flags(),
        release=BassReleaseMetadata(
            release_stage="research_executable",
            run_label="tier-b-native",
            config_hash="cfg-hash",
            code_version="0.0-test",
            schema_version="ver2-v0",
            git_commit="deadbeef",
            random_seed=42,
        ),
        k_grid_mpc=np.geomspace(1.0e-3, 2.0e-2, 5),
    )
    assert output.metadata["propagator_ready"] is True
    assert output.metadata["propagator_readiness"] == "approximate_family_kernel"
    assert output.metadata["propagator_exactness"] == "approximate_family_kernel"
    assert output.metadata["covariance_readiness"] == "proxy"
    assert output.metadata["source_builder_scope"] == "theta0_plus_combined_polter_visibility_ver2_native"
    assert output.metadata["tier_b_core_owner"] == "ver2_s1s2_native"
    assert output.metadata["solver_method"] == "LSODA"
    assert output.metadata["resolved_solver_method"] == "LSODA"
    assert output.metadata["executor_realization"] == "runtime_family_direct"
    assert output.metadata["solver_family_realization"] == "runtime_family_direct"
    assert output.metadata["neutrino_hierarchy_mode"] == "reduced_summary_only"
    assert output.metadata["seed_k_comoving"] == pytest.approx(0.0)
    assert output.metadata["startup_manifold_applied"] is False
    assert output.metadata["propagator_mode"] == "anisotropic_forward"
    assert output.metadata["source_propagator_status"] == "approximate"
    assert output.metadata["source_propagator_requested_status"] == "approximate"
    assert output.metadata["source_propagator_rotation_status"] == "approximate"
    assert output.metadata["source_propagator_realization"] == "class_b_helical_matrix_approx"
    assert output.metadata["source_builder_combined_polter"] is True
    assert output.metadata["source_builder_visibility_weighted_polter"] is True
    assert output.metadata["bianchi_branch"] == "orthogonal"
    assert output.metadata["bianchi_class_label"] == "B"
    assert output.metadata["global_tilt_contract"] == "orthogonal_branch_zero_global_tilt"
    assert output.metadata["theory_family"] == "VII_h_orthogonal"
    assert output.metadata["geometry_params"]["type_label"] == "VII_h"
    assert output.metadata["kinematic_params"]["branch"] == "orthogonal"
    assert output.metadata["tilt_params"]["enabled"] is False
    assert output.metadata["gate_registry"]["output_split_gate"].gate_name == "output_split_gate"
    assert output.anisotropic_covariance is not None
    assert output.deterministic_template["kind"] == "tier_b_native_template"
    assert output.alm_T["representation"] == "ver2_native_pstf_sphere_reconstruction"
    assert output.alm_T["coefficient_representation"] == "ver2_native_pstf_final_slice"
    assert np.asarray(output.alm_T["sphere_directions"], dtype=np.float64).shape == (435, 3)
    assert np.asarray(output.alm_E["sphere_samples"], dtype=np.float64).shape == (435,)
    assert np.asarray(output.alm_B["sphere_samples"], dtype=np.float64).shape == (435,)


def test_build_solver_core_output_from_native_result_promotes_type_i_exact_backend() -> None:
    output = build_solver_core_output_from_native_result(
        manifest=_manifest(),
        bianchi_type="I",
        result=_synthetic_result(),
        species=SpeciesBackgroundRegistry.from_planck2018(),
        runtime_controls=_controls(),
        feature_flags=_live_flags(),
        release=BassReleaseMetadata(
            release_stage="research_executable",
            run_label="tier-b-native-typei",
            config_hash="cfg-hash",
            code_version="0.0-test",
            schema_version="ver2-v0",
            git_commit="deadbeef",
            random_seed=42,
        ),
        k_grid_mpc=np.geomspace(1.0e-3, 2.0e-2, 5),
    )
    assert output.metadata["propagator_readiness"] == "exact"
    assert output.metadata["propagator_exactness"] == "exact"
    assert output.metadata["source_propagator_status"] == "exact"
    assert output.metadata["source_propagator_requested_status"] == "approximate"
    assert output.metadata["source_propagator_rotation_status"] == "disabled"
    assert output.metadata["source_propagator_realization"] == "bianchi_i_matrix_exact"
    assert output.metadata["bianchi_branch"] == "orthogonal"
    assert output.metadata["bianchi_class_label"] == "A"
    assert output.metadata["global_tilt_contract"] == "orthogonal_branch_zero_global_tilt"
    assert output.metadata["theory_family"] == "I_orthogonal"
    assert output.alm_T["representation"] == "ver2_native_pstf_sphere_reconstruction"
    assert output.alm_T["coefficient_representation"] == "ver2_native_pstf_final_slice"


def test_native_output_records_reionization_low_z_source_delta() -> None:
    runtime_controls = _controls()
    result = _synthetic_result_with_late_visibility_probe()
    release = BassReleaseMetadata(
        release_stage="research_executable",
        run_label="tier-b-native-reionization",
        config_hash="cfg-hash",
        code_version="0.0-test",
        schema_version="ver2-v0",
        git_commit="deadbeef",
        random_seed=42,
    )
    output_no_reion = build_solver_core_output_from_native_result(
        manifest=_manifest(),
        bianchi_type="VII_h",
        result=result,
        species=SpeciesBackgroundRegistry.from_planck2018(apply_default_reionization=False),
        runtime_controls=runtime_controls,
        feature_flags=_live_flags(),
        release=release,
        k_grid_mpc=np.geomspace(1.0e-3, 2.0e-2, 5),
    )
    output_with_reion = build_solver_core_output_from_native_result(
        manifest=_manifest(),
        bianchi_type="VII_h",
        result=result,
        species=SpeciesBackgroundRegistry.from_planck2018(),
        runtime_controls=runtime_controls,
        feature_flags=_live_flags(),
        release=release,
        k_grid_mpc=np.geomspace(1.0e-3, 2.0e-2, 5),
    )
    assert output_no_reion.metadata["visibility_reionization_mode"] == "disabled"
    assert output_with_reion.metadata["visibility_reionization_mode"] == "tanh"
    assert output_no_reion.metadata["source_builder_low_z_probe_available"] is True
    assert output_with_reion.metadata["source_builder_low_z_probe_available"] is True
    assert output_no_reion.metadata["source_builder_low_z_probe_status"] == "available"
    assert output_with_reion.metadata["source_builder_low_z_probe_status"] == "available"
    assert output_no_reion.metadata["reionization_source_claim_status"] == "reionization_disabled"
    assert output_with_reion.metadata["reionization_source_claim_status"] == "bounded_live_low_z_delta"
    assert output_with_reion.metadata["visibility_tau_reion"] > 0.0
    assert output_with_reion.metadata["source_builder_low_z_gpi_m0"] > output_no_reion.metadata["source_builder_low_z_gpi_m0"]


@pytest.mark.parametrize(
    ("bianchi_type", "expected_realization"),
    [
        ("V", "class_b_open_matrix_approx"),
        ("VII_0", "class_a_helical_matrix_approx"),
        ("VIII", "class_a_semisimple_matrix_approx"),
    ],
)
def test_native_output_uses_algebra_aware_non_type_i_family(
    bianchi_type: str,
    expected_realization: str,
) -> None:
    output = build_solver_core_output_from_native_result(
        manifest=_manifest(),
        bianchi_type=bianchi_type,
        result=_synthetic_result(),
        species=SpeciesBackgroundRegistry.from_planck2018(),
        runtime_controls=_controls(),
        feature_flags=_live_flags(),
        release=BassReleaseMetadata(
            release_stage="research_executable",
            run_label=f"tier-b-native-{bianchi_type}",
            config_hash="cfg-hash",
            code_version="0.0-test",
            schema_version="ver2-v0",
            git_commit="deadbeef",
            random_seed=42,
        ),
        k_grid_mpc=np.geomspace(1.0e-3, 2.0e-2, 5),
    )
    assert output.metadata["source_propagator_realization"] == expected_realization


def test_tier_b_exact_source_propagator_requires_explicit_propagator_config() -> None:
    exact_flags = SolverFeatureFlags(
        background_dynamics=FeatureStatus.APPROXIMATE,
        photon_transport=FeatureStatus.APPROXIMATE,
        thomson_collision=FeatureStatus.APPROXIMATE,
        visibility_history=FeatureStatus.APPROXIMATE,
        source_propagator=FeatureStatus.EXACT,
        checkpoint_restart=FeatureStatus.DISABLED,
    )
    with pytest.raises(ValueError, match="exact source propagation requires an explicit propagator config"):
        build_solver_core_output_from_native_result(
            manifest=_manifest(),
            bianchi_type="VII_h",
            result=_synthetic_result(),
            species=SpeciesBackgroundRegistry.from_planck2018(),
            runtime_controls=_controls(),
            feature_flags=exact_flags,
            release=BassReleaseMetadata(
                release_stage="research_executable",
                run_label="tier-b-native-exact",
                config_hash="cfg-hash",
                code_version="0.0-test",
                schema_version="ver2-v0",
                git_commit="deadbeef",
            ),
            k_grid_mpc=np.geomspace(1.0e-3, 2.0e-2, 5),
        )
