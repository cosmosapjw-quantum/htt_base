from __future__ import annotations

from types import SimpleNamespace

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
from bass.forward.ver2_solver_output import _build_lowell_source_builder
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
from bass.validation.publication_readiness import evaluate_publication_claim


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
    assert output.metadata["family_backend_status"] == "full_mode"
    assert output.metadata["propagator_readiness"] == "approximate_family_kernel"
    assert output.metadata["propagator_exactness"] == "approximate_family_kernel"
    assert output.metadata["covariance_readiness"] == "proxy"
    assert output.metadata["source_builder_scope"] == "theta0_plus_combined_polter_visibility_lowell_bridge"
    assert output.metadata["propagator_mode"] == "anisotropic_forward"
    assert output.metadata["source_propagator_status"] == "approximate"
    assert output.metadata["source_propagator_realization"] == "type_viih_open_helical_projection"
    assert output.metadata["source_propagator_exactness"] == "algebraic_proxy_family_kernel"
    assert output.metadata["source_propagator_publication_output_claim_allowed"] is False
    assert output.metadata["source_propagator_statistics_claim_allowed"] is False
    assert output.metadata["source_builder_combined_polter"] is True
    assert output.metadata["source_builder_visibility_weighted_polter"] is True
    assert output.metadata["source_builder_scale_factor_owner"] == "integration_result"
    assert output.metadata["source_builder_runtime_z_min"] == pytest.approx(499.0)
    assert output.metadata["source_builder_runtime_z_max"] == pytest.approx(999.0)
    assert output.metadata["source_builder_visibility_max"] > 0.0
    assert output.metadata["source_builder_visibility_nonzero_sample_count"] > 0
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


def test_lowell_source_builder_exports_baryon_velocity_for_doppler_source() -> None:
    result = _synthetic_result()
    v_b = np.linspace(-0.2, 0.1, result.eta.size)
    result.baryon_local_history = np.column_stack(
        [np.zeros(result.eta.size, dtype=np.float64), v_b]
    )

    source_builder, metadata = _build_lowell_source_builder(
        result,
        species=SpeciesBackgroundRegistry.from_planck2018(),
        visibility_fn=lambda eta: 2.0,
    )
    eta_probe = float(result.eta[3])
    sample = source_builder(eta_probe, 1.0e-2)

    assert sample["v_b_m0"] == pytest.approx(v_b[3])
    assert sample["g_v_b_m0"] == pytest.approx(2.0 * v_b[3])
    assert metadata["source_builder_doppler_status"] == "baryon_local_history_slot1"
    assert metadata["source_builder_doppler_nonzero_sample_count"] == result.eta.size


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
    assert output.metadata["source_propagator_realization"] == "type_viih_open_helical_projection"
    assert output.metadata["source_propagator_exactness"] == "algebraic_proxy_family_kernel"
    assert output.metadata["source_propagator_publication_output_claim_allowed"] is False
    assert output.metadata["source_propagator_statistics_claim_allowed"] is False
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
    assert output.metadata["stochastic_channel_status"] == "placeholder"
    assert output.metadata["stochastic_block_reason"] == (
        "stochastic_lcdm_realization_injection_not_implemented"
    )
    assert output.metadata["checkpoint_enabled"] is False
    assert output.metadata["checkpoint_write_count"] == 0
    assert output.metadata["restart_used"] is False
    assert output.metadata["restart_checkpoint_path"] is None
    assert output.anisotropic_covariance is not None
    assert output.deterministic_template["kind"] == "tier_b_native_template"
    assert output.alm_T["representation"] == "ver2_native_pstf_sphere_reconstruction"
    assert output.alm_T["coefficient_representation"] == "ver2_native_pstf_final_slice"
    assert np.asarray(output.alm_T["sphere_directions"], dtype=np.float64).shape == (435, 3)
    assert np.asarray(output.alm_E["sphere_samples"], dtype=np.float64).shape == (435,)
    assert np.asarray(output.alm_B["sphere_samples"], dtype=np.float64).shape == (435,)


def test_native_output_promotes_auxiliary_b_mode_runtime_payload() -> None:
    size = (_controls().multipole_cutoff + 1) ** 2
    b_coefficients = np.zeros(size, dtype=np.float64)
    b_coefficients[6] = 2.5e-6
    canonical_projection = SimpleNamespace(
        hierarchy_state=SimpleNamespace(
            photon_polarization_block={
                "B": b_coefficients,
                "eta": np.array([0.1, 0.2], dtype=np.float64),
                "B_history": np.vstack([np.zeros(size, dtype=np.float64), b_coefficients]),
                "mode_label_blocks": {"m0": b_coefficients},
                "mode_label_history": {
                    "m0": np.vstack([np.zeros(size, dtype=np.float64), b_coefficients])
                },
            }
        ),
        sector_status={"ph_B": "layout_operator_auxiliary_b_mode_history"},
        metadata={
            "projection_mode": "single_live_mode_label_with_layout_auxiliary_local_matter_blocks",
            "b_history_available": True,
            "b_history_sample_count": 2,
            "b_mode_labels": ["m0"],
            "b_history_mode_labels": ["m0"],
            "resolved_sector_order": ("ph_I", "ph_E", "ph_B", "nu_I"),
            "matter_block_labels": {},
        },
        state_vector=np.zeros(size * 7, dtype=np.float64),
        covered_mode_labels=("m0",),
        zero_filled_mode_labels=(),
    )
    output = build_solver_core_output_from_native_result(
        manifest=_manifest(),
        bianchi_type="VII_h",
        result=_synthetic_result(),
        species=SpeciesBackgroundRegistry.from_planck2018(),
        runtime_controls=_controls(),
        feature_flags=_live_flags(),
        release=BassReleaseMetadata(
            release_stage="research_executable",
            run_label="tier-b-native-b-aux",
            config_hash="cfg-hash",
            code_version="0.0-test",
            schema_version="ver2-v0",
            git_commit="deadbeef",
            random_seed=42,
        ),
        k_grid_mpc=np.geomspace(1.0e-3, 2.0e-2, 5),
        canonical_projection=canonical_projection,
    )
    assert output.metadata["b_mode_runtime_available"] is True
    assert output.metadata["b_mode_payload_available"] is True
    assert output.metadata["b_mode_payload_status"] == "layout_operator_auxiliary_b_mode_history"
    assert output.alm_B["available"] is True
    assert output.metadata["canonical_projection_b_history_available"] is True
    assert output.metadata["canonical_projection_b_history_sample_count"] == 2
    assert output.metadata["canonical_projection_b_mode_labels"] == ["m0"]
    assert output.metadata["canonical_projection_b_history_mode_labels"] == ["m0"]
    assert output.metadata["layout_state_history_sample_count"] == 0
    assert output.metadata["layout_state_history_size"] == 0
    assert output.metadata["b_mode_projector_status"] == "not_run_b_history_eta_mismatch"


def test_native_output_with_matching_b_history_opens_polarization_publication_gate() -> None:
    result = _synthetic_result()
    size = (_controls().multipole_cutoff + 1) ** 2
    b_history = np.zeros((result.eta.size, size), dtype=np.float64)
    b_history[:, 7] = np.linspace(0.0, 2.5e-6, result.eta.size)
    b_coefficients = b_history[-1].copy()
    canonical_projection = SimpleNamespace(
        hierarchy_state=SimpleNamespace(
            photon_polarization_block={
                "B": b_coefficients,
                "eta": np.asarray(result.eta, dtype=np.float64),
                "B_history": b_history,
                "mode_label_blocks": {"m0": b_coefficients},
                "mode_label_history": {"m0": b_history},
            }
        ),
        sector_status={"ph_B": "layout_operator_auxiliary_b_mode_history"},
        metadata={
            "projection_mode": "single_live_mode_label_with_layout_auxiliary_local_matter_blocks",
            "b_history_available": True,
            "b_history_sample_count": result.eta.size,
            "b_mode_labels": ["m0"],
            "b_history_mode_labels": ["m0"],
            "resolved_sector_order": ("ph_I", "ph_E", "ph_B", "nu_I", "src"),
            "matter_block_labels": {},
        },
        state_vector=np.zeros(size * 7, dtype=np.float64),
        covered_mode_labels=("m0",),
        zero_filled_mode_labels=(),
    )
    output = build_solver_core_output_from_native_result(
        manifest=_manifest(),
        bianchi_type="VII_h",
        result=result,
        species=SpeciesBackgroundRegistry.from_planck2018(),
        runtime_controls=_controls(),
        feature_flags=_live_flags(),
        release=BassReleaseMetadata(
            release_stage="research_executable",
            run_label="tier-b-native-b-projector",
            config_hash="cfg-hash",
            code_version="0.0-test",
            schema_version="ver2-v0",
            git_commit="deadbeef",
            random_seed=42,
        ),
        k_grid_mpc=np.geomspace(1.0e-3, 2.0e-2, 5),
        canonical_projection=canonical_projection,
        thomson_mode="electron_frame_exact_wrapper",
    )
    assert output.metadata["exact_thomson_authority_path"] is True
    assert output.metadata["b_mode_runtime_available"] is True
    assert output.metadata["b_mode_output_support"] == "wigner_d_path_b"
    assert output.metadata["b_mode_projector_status"] == "computed_wigner_d_path_b"
    assert output.metadata["b_mode_projector_nonzero"] is True
    assert output.metadata["b_mode_projector_norm"] > 0.0
    decision = evaluate_publication_claim(
        "full_anisotropic_polarization_output",
        output_metadata=output.metadata,
    )
    assert decision.allowed is True


def test_native_output_blocks_readiness_when_backend_verification_bundle_is_unresolved() -> None:
    unresolved_mode_ops = SimpleNamespace(
        metadata={
            "lookup_resolution_status": "unresolved_lookup",
            "verification_crosscheck_pass": False,
            "verification_reference": None,
            "operator_payload_status": "geometry_opacity_coupled_sparse_blocks",
            "contract_release_status": "backend-contract-complete",
        },
        operator_kernel_family="class_b_helical_matrix_approx",
        layout_metadata={"exact_family_operator_available": False},
        seed_provenance_mode="template_card_family_adapted",
    )
    output = build_solver_core_output_from_native_result(
        manifest=_manifest(),
        bianchi_type="VII_h",
        result=_synthetic_result(),
        species=SpeciesBackgroundRegistry.from_planck2018(),
        runtime_controls=_controls(),
        feature_flags=_live_flags(),
        release=BassReleaseMetadata(
            release_stage="research_executable",
            run_label="tier-b-native-backend-unresolved",
            config_hash="cfg-hash",
            code_version="0.0-test",
            schema_version="ver2-v0",
            git_commit="deadbeef",
            random_seed=42,
        ),
        k_grid_mpc=np.geomspace(1.0e-3, 2.0e-2, 5),
        mode_ops=unresolved_mode_ops,
    )
    assert output.metadata["backend_lookup_resolution_status"] == "unresolved_lookup"
    assert output.metadata["backend_verification_crosscheck_pass"] is False
    assert output.metadata["backend_reduced_local_evaluator_available"] is False
    assert output.metadata["backend_reduced_harmonic_evaluator_available"] is False
    assert output.metadata["backend_reduced_source_evaluator_available"] is False
    assert output.metadata["propagator_readiness"] == "contract_only_unavailable"
    assert output.metadata["propagator_exactness"] == "contract_only_unavailable"
    assert output.metadata["propagator_ready"] is False


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
    assert output.metadata["family_backend_status"] == "full_mode"
    assert output.metadata["source_propagator_status"] == "exact"
    assert output.metadata["source_propagator_requested_status"] == "approximate"
    assert output.metadata["source_propagator_rotation_status"] == "disabled"
    assert output.metadata["source_propagator_realization"] == "bianchi_i_matrix_exact"
    assert output.metadata["source_propagator_exactness"] == "exact_type_i_matrix"
    assert output.metadata["source_propagator_publication_output_claim_allowed"] is True
    assert output.metadata["source_propagator_statistics_claim_allowed"] is False
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
        ("II", "type_ii_nilpotent_projection"),
        ("III", "type_iii_hyperbolic_projection"),
        ("IV", "type_iv_solvable_projection"),
        ("V", "type_v_open_hyperbolic_projection"),
        ("VI_0", "type_vi0_directional_projection"),
        ("VI_h", "type_vih_negative_h_projection"),
        ("VII_0", "type_vii0_helical_projection"),
        ("VII_h", "type_viih_open_helical_projection"),
        ("VIII", "type_viii_sl2r_noncompact_projection"),
        ("IX", "type_ix_compact_su2_projection"),
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
    if bianchi_type == "II":
        assert output.metadata["source_propagator_nil_transport_status"] == (
            "type_ii_nilpotent_projection"
        )
        assert output.metadata["source_propagator_polarization_basis_transport"] == (
            "spin2_nil_shear_rotation"
        )
        assert output.metadata["source_propagator_nil_structure_scale"] > 0.0
        assert output.metadata["source_propagator_nil_mode_mixing_norm"] > 0.0
    if bianchi_type == "III":
        assert output.metadata["source_propagator_typeiii_transport_status"] == (
            "type_iii_hyperbolic_projection"
        )
        assert output.metadata["source_propagator_typeiii_branch_flag"] == "VI_-1_special"
        assert output.metadata["source_propagator_polarization_basis_transport"] == (
            "spin2_hyperbolic_branch_rotation"
        )
        assert output.metadata["source_propagator_typeiii_h_parameter"] == pytest.approx(-1.0)
        assert output.metadata["source_propagator_typeiii_hyperbolic_scale"] > 0.0
        assert output.metadata["source_propagator_typeiii_twist_scale"] > 0.0
        assert 0.0 < output.metadata["source_propagator_typeiii_open_attenuation_min"] < 1.0
        assert output.metadata["source_propagator_typeiii_mode_mixing_norm"] > 0.0
    if bianchi_type == "IV":
        assert output.metadata["source_propagator_typeiv_transport_status"] == (
            "type_iv_solvable_projection"
        )
        assert output.metadata["source_propagator_typeiv_coordinate_order"] == (
            "n3_dominated_then_a_twist"
        )
        assert output.metadata["source_propagator_polarization_basis_transport"] == (
            "spin2_solvable_edge_rotation"
        )
        assert output.metadata["source_propagator_typeiv_structure_scale"] > 0.0
        assert output.metadata["source_propagator_typeiv_n3_scale"] > 0.0
        assert output.metadata["source_propagator_typeiv_twist_scale"] > 0.0
        assert 0.0 < output.metadata["source_propagator_typeiv_privileged_weight"] < 1.0
        assert 0.0 < output.metadata["source_propagator_typeiv_edge_attenuation_min"] < 1.0
        assert output.metadata["source_propagator_typeiv_mode_mixing_norm"] > 0.0
    if bianchi_type == "V":
        assert output.metadata["source_propagator_typev_transport_status"] == (
            "type_v_open_hyperbolic_projection"
        )
        assert output.metadata["source_propagator_typev_chart_metadata"] == "open_chart"
        assert output.metadata["source_propagator_polarization_basis_transport"] == (
            "open_hyperbolic_parallel_transport"
        )
        assert output.metadata["source_propagator_typev_curvature_scale"] > 0.0
        assert 0.0 < output.metadata["source_propagator_typev_open_envelope_min"] <= 1.0
        assert 0.0 < output.metadata["source_propagator_typev_open_envelope_max"] <= 1.0
        assert output.metadata["source_propagator_typev_open_anchor_deviation_max"] > 0.0
        assert output.metadata["source_propagator_typev_mode_mixing_norm"] == pytest.approx(0.0)
    if bianchi_type == "VI_0":
        assert output.metadata["source_propagator_vi0_transport_status"] == (
            "type_vi0_directional_projection"
        )
        assert output.metadata["source_propagator_polarization_basis_transport"] == (
            "parity_even_directional_transport"
        )
        assert output.metadata["source_propagator_vi0_structure_scale"] > 0.0
        assert output.metadata["source_propagator_vi0_mode_mixing_norm"] > 0.0
    if bianchi_type == "VI_h":
        assert output.metadata["source_propagator_vih_transport_status"] == (
            "type_vih_negative_h_projection"
        )
        assert output.metadata["source_propagator_vih_branch_flag"] == "negative_h_branch"
        assert output.metadata["source_propagator_polarization_basis_transport"] == (
            "spin2_negative_h_branch_rotation"
        )
        assert output.metadata["source_propagator_vih_h_parameter"] < 0.0
        assert output.metadata["source_propagator_vih_h_parameter"] != pytest.approx(-1.0)
        assert output.metadata["source_propagator_vih_structure_scale"] > 0.0
        assert output.metadata["source_propagator_vih_twist_scale"] > 0.0
        assert 0.0 < output.metadata["source_propagator_vih_h_twist_scale"] < 1.0
        assert -1.0 < output.metadata["source_propagator_vih_directional_imbalance"] < 1.0
        assert 0.0 < output.metadata["source_propagator_vih_open_attenuation_min"] < 1.0
        assert output.metadata["source_propagator_vih_mode_mixing_norm"] > 0.0
    if bianchi_type == "VII_0":
        assert output.metadata["source_propagator_helical_transport_status"] == (
            "type_vii0_helical_projection"
        )
        assert output.metadata["source_propagator_polarization_basis_transport"] == (
            "spin2_helical_rotation"
        )
        assert output.metadata["source_propagator_helical_pitch"] > 0.0
        assert output.metadata["source_propagator_helicity_mode_mixing_norm"] > 0.0
    if bianchi_type == "VII_h":
        assert output.metadata["source_propagator_viih_transport_status"] == (
            "type_viih_open_helical_projection"
        )
        assert output.metadata["source_propagator_polarization_basis_transport"] == (
            "spin2_open_helical_rotation"
        )
        assert output.metadata["source_propagator_viih_helical_pitch"] > 0.0
        assert output.metadata["source_propagator_viih_twist_scale"] > 0.0
        assert 0.0 < output.metadata["source_propagator_viih_open_attenuation_min"] < 1.0
        assert output.metadata["source_propagator_viih_mode_mixing_norm"] > 0.0
    if bianchi_type == "VIII":
        assert output.metadata["source_propagator_typeviii_transport_status"] == (
            "type_viii_sl2r_noncompact_projection"
        )
        assert output.metadata["source_propagator_typeviii_branch_flag"] == (
            "noncompact_branch"
        )
        assert output.metadata["source_propagator_polarization_basis_transport"] == (
            "spin2_sl2r_noncompact_rotation"
        )
        assert output.metadata["source_propagator_typeviii_structure_scale"] > 0.0
        assert 0.0 < output.metadata["source_propagator_typeviii_negative_axis_weight"] < 1.0
        assert -1.0 <= output.metadata["source_propagator_typeviii_positive_axis_split"] <= 1.0
        assert output.metadata["source_propagator_typeviii_disc_radius_x_eq_tanh_xi"] == pytest.approx(
            np.tanh(1.5)
        )
        assert 0.0 < output.metadata["source_propagator_typeviii_noncompact_attenuation_min"] < 1.0
        assert output.metadata["source_propagator_typeviii_mode_mixing_norm"] > 0.0
        assert tuple(output.metadata["source_propagator_typeviii_series_tags"]) == (
            "trivial",
            "discrete_positive",
            "discrete_negative",
        )
        assert (
            output.metadata["source_propagator_typeviii_continuous_series_tag"]
            == "continuous_principal"
        )
    if bianchi_type == "IX":
        assert output.metadata["source_propagator_typeix_transport_status"] == (
            "type_ix_compact_su2_projection"
        )
        assert output.metadata["source_propagator_typeix_branch_flag"] == "compact_su2_branch"
        assert output.metadata["source_propagator_polarization_basis_transport"] == (
            "spin2_compact_su2_rotation"
        )
        assert output.metadata["source_propagator_typeix_curvature_scale"] > 0.0
        assert output.metadata["source_propagator_typeix_positive_axis_anisotropy_split"] == (
            pytest.approx(0.0)
        )
        assert output.metadata["source_propagator_typeix_discrete_j"] == 2
        assert output.metadata["source_propagator_typeix_spectral_eigenvalue_jj1"] == 6
        assert output.metadata["source_propagator_typeix_invariant_volume"] == pytest.approx(
            8.0 * np.pi ** 2
        )
        assert output.metadata["source_propagator_typeix_wigner_d_j2_unit_amplitude"] == (
            pytest.approx(np.sqrt(5.0 / (8.0 * np.pi ** 2)))
        )
        assert output.metadata["source_propagator_typeix_compact_phase_max"] > 0.0
        assert output.metadata["source_propagator_typeix_spectral_envelope_min"] == (
            pytest.approx(1.0)
        )
        assert output.metadata["source_propagator_typeix_spectral_envelope_max"] == (
            pytest.approx(1.0)
        )
        assert tuple(output.metadata["source_propagator_typeix_discrete_representation_labels"]) == (
            "D^2_-2,0",
            "D^2_0,0",
            "D^2_+2,0",
        )


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
