from __future__ import annotations

import numpy as np

from bass.observational import (
    build_atlas_entry_lite,
    build_covariance_feature_summary,
    build_observable_vector_from_solver_output,
    build_sparse_covariance_proxy,
)
from common.contracts import ArtifactManifest, SkySupport
from bass.forward.ver2_solver_output import build_solver_core_output, BassReleaseMetadata
from bass.background.bianchi_types import get_type
from bass.background.einstein_bianchi import BianchiCosmology
from bass.hierarchy.integrator import IntegratorConfig
from bass.runtime.ver2_execution import (
    CheckpointPolicy,
    CouplingMode,
    ConstraintProjectionPolicy,
    FeatureStatus,
    IntegratorFamily,
    RuntimeControlBlock,
    SolverFeatureFlags,
    SolverTier,
    execute_tier_b_lowell_solver,
)
from bass.los.ver2_source_propagator import (
    ObserverFrameMetadata,
    PropagatorMode,
    SourcePropagatorConfig,
)
from bass.spectrum import CutoffCampaignSpec
from bass.species.registry import SpeciesBackgroundRegistry


def _manifest() -> ArtifactManifest:
    return ArtifactManifest(
        artifact_id="bass.solver.run0",
        artifact_path="artifacts/bass/solver_run0.json",
        owner="BASS",
        implementation_scope="bass_py",
        claim_tier="conditional",
        production_status="production_candidate",
        created_by="test-suite",
        git_commit="abc123",
        config_hash="cfg1",
        input_hashes=["seed:0"],
        code_version="0.0-test",
        schema_version="ver2-v1",
    )


def _sky_support() -> SkySupport:
    return SkySupport(
        selection_mode="mock_calibrated",
        sky_support_hash="sky123",
        mask_hash="mask123",
        mock_coverage_status="adequate",
        scan_volume_hash="scan123",
    )


def _runtime_controls() -> RuntimeControlBlock:
    return RuntimeControlBlock(
        tier=SolverTier.TIER_A_ANGULAR,
        integrator_family=IntegratorFamily.EXPLICIT_RK,
        coupling_mode=CouplingMode.BACKGROUND_THEN_RADIATION,
        multipole_cutoff=8,
        rtol=1.0e-6,
        atol=1.0e-8,
        checkpoint=CheckpointPolicy(enabled=False),
        constraint_projection=ConstraintProjectionPolicy(
            enabled=False,
            status=FeatureStatus.DISABLED,
        ),
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


def _propagator() -> SourcePropagatorConfig:
    return SourcePropagatorConfig(
        mode=PropagatorMode.ANISOTROPIC_FORWARD,
        temperature_transport=FeatureStatus.APPROXIMATE,
        polarization_rotation=FeatureStatus.APPROXIMATE,
        flrw_validation_only=False,
        observer_frame=ObserverFrameMetadata(
            observer_frame="normal_tetrad",
            screen_basis_convention="explicit_screen_basis",
            harmonic_basis="m_explicit",
            eb_sign_convention="cmb",
        ),
    )


def _covariance_bundle() -> dict[str, object]:
    ell = np.arange(9, dtype=int)
    diagonal = np.vstack(
        [
            np.linspace(1.0, 0.2, ell.size),
            np.linspace(0.8, 0.15, ell.size),
            np.linspace(0.6, 0.1, ell.size),
        ]
    )
    block = np.zeros((ell.size, ell.size), dtype=float)
    block[2, 4] = block[4, 2] = 0.03
    block[3, 5] = block[5, 3] = 0.02
    return {
        "structure_label": "VII_h",
        "ell": ell,
        "C_ell": {
            "TT": diagonal.sum(axis=0),
            "TE": 0.2 * diagonal.sum(axis=0),
            "EE": 0.5 * diagonal.sum(axis=0),
            "BB": np.zeros_like(ell, dtype=float),
        },
        "diagonal_by_mode": {
            "TT": diagonal,
            "TE": 0.2 * diagonal,
            "EE": 0.5 * diagonal,
            "BB": np.zeros_like(diagonal),
        },
        "off_diagonal_blocks": {
            "TT": {"m0": block, "m+2": 0.5 * block, "m-2": 0.5 * block},
            "TE": {"m0": 0.1 * block, "m+2": 0.05 * block, "m-2": 0.05 * block},
            "EE": {"m0": 0.3 * block, "m+2": 0.15 * block, "m-2": 0.15 * block},
            "BB": {"m0": np.zeros_like(block), "m+2": np.zeros_like(block), "m-2": np.zeros_like(block)},
        },
        "preferred_axis": np.array([0.0, 0.0, 1.0]),
        "anisotropy_tensor": np.diag([0.2, -0.1, -0.1]),
        "offdiag_strength": 0.12,
        "rotation_strength": 0.03,
    }


def _solver_output() -> object:
    return build_solver_core_output(
        manifest=_manifest(),
        bianchi_type="VII_h",
        tilt_enabled=True,
        harmonic_basis="m_explicit",
        eb_sign_convention="cmb",
        thomson_mode="electron_frame",
        runtime_controls=_runtime_controls(),
        feature_flags=_feature_flags(),
        propagator=_propagator(),
        release=BassReleaseMetadata(
            release_stage="skeleton",
            run_label="test-run",
            config_hash="cfg1",
            code_version="0.0-test",
            schema_version="ver2-v1",
            git_commit="abc123",
        ),
        deterministic_template={"Ahat": 0.2, "delta_chi2": 0.0},
        anisotropic_covariance=_covariance_bundle(),
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


def _tier_b_flags() -> SolverFeatureFlags:
    return SolverFeatureFlags(
        background_dynamics=FeatureStatus.APPROXIMATE,
        photon_transport=FeatureStatus.APPROXIMATE,
        thomson_collision=FeatureStatus.APPROXIMATE,
        visibility_history=FeatureStatus.APPROXIMATE,
        source_propagator=FeatureStatus.APPROXIMATE,
        checkpoint_restart=FeatureStatus.DISABLED,
    )


def _tier_b_release() -> BassReleaseMetadata:
    return BassReleaseMetadata(
        release_stage="research_candidate",
        run_label="observable-tier-b-smoke",
        config_hash="cfg-hash",
        code_version="ver2-test",
        schema_version="1.0.0",
        git_commit="test-commit",
        random_seed=42,
    )


def _tier_b_manifest() -> ArtifactManifest:
    return ArtifactManifest(
        artifact_id="bass.ver2.o_lane.smoke",
        artifact_path="artifacts/bass/ver2_o_lane_smoke.json",
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
        passed_gates=["runtime", "propagator"],
    )


def _tier_b_config() -> IntegratorConfig:
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


def test_observable_vector_builder_attaches_sky_support_and_manifest():
    observable = build_observable_vector_from_solver_output(
        _solver_output(),
        sky_support=_sky_support(),
    )
    assert observable.manifest.owner == "BASS"
    assert observable.manifest.production_status == "diagnostic_only"
    assert observable.sky_support.selection_mode == "mock_calibrated"
    assert "BiPoSH" in observable.channels
    assert "template" in observable.channels
    assert observable.scan_volume["scan_volume_hash"]
    assert observable.biposh is not None
    assert observable.biposh["representation"] == "sparse_mode_block_proxy"
    assert observable.alm_features["bianchi_branch"] == "tilted"
    assert observable.alm_features["global_tilt_contract"] == "model_matter_frame_state"
    assert (
        observable.alm_features["local_boost_contract"]
        == "observer_side_only_not_applied_in_bass_output"
    )
    assert observable.alm_features["tilt_boost_separation"] == "explicit_nonmerged"
    assert observable.scan_volume["solver_domain_scope"] == "all_11_bianchi_types"
    assert (
        observable.alm_features["observer_reconstruction_status"]
        == "unreported"
    )
    assert observable.alm_features["covariance_readiness"] == "proxy"
    assert observable.alm_features["fitting_ready"] is False
    assert (
        observable.covariance_features["local_global_degeneracy"]["status"]
        == "observer_source_discrimination_pending"
    )


def test_covariance_proxy_and_feature_summary_record_guards():
    covariance = _covariance_bundle()
    sparse = build_sparse_covariance_proxy(
        covariance,
        harmonic_convention="m_explicit",
    )
    summary = build_covariance_feature_summary(
        covariance,
        harmonic_convention="m_explicit",
    )
    assert sparse["unique_index_count"] > 0
    assert "mode_block_proxy_not_full_biposh" in sparse["caveats"]
    assert sparse["supports_full_biposh"] is False
    assert sparse["supports_basis_reduced_morphology"] is False
    assert summary["psd_guard"]["passed"] is True
    assert summary["symmetry_guard"]["passed"] is True
    assert summary["invariant_guard"]["passed"] is True


def test_atlas_entry_lite_builder_carries_observable_reference():
    solver_output = _solver_output()
    observable = build_observable_vector_from_solver_output(
        solver_output,
        sky_support=_sky_support(),
    )
    atlas = build_atlas_entry_lite(solver_output, observable)
    assert atlas.manifest.owner == "BASS"
    assert atlas.observable_vector_ref == observable.manifest.artifact_id
    assert atlas.theory_family == "VII_h_tilted"
    assert atlas.tilt_params["enabled"] is True
    assert atlas.kinematic_params["local_boost_applied"] is False
    assert atlas.manifest.production_status == "diagnostic_only"
    assert atlas.validity_domain["sky_support"]["sky_support_hash"] == "sky123"
    assert atlas.validity_domain["bianchi_branch"] == "tilted"
    assert atlas.validity_domain["global_tilt_contract"] == "model_matter_frame_state"
    assert (
        atlas.validity_domain["local_global_degeneracy"]["status"]
        == "observer_source_discrimination_pending"
    )
    assert atlas.validity_domain["basis_reduction_status"] == "mode_proxy_only"


def test_live_tier_b_type_i_observable_marks_isotropic_null_proxy() -> None:
    species = SpeciesBackgroundRegistry.from_planck2018()
    run = execute_tier_b_lowell_solver(
        manifest=_tier_b_manifest(),
        bianchi_type="I",
        species=species,
        integrator_config=_tier_b_config(),
        runtime_controls=_tier_b_controls(),
        feature_flags=_tier_b_flags(),
        release=_tier_b_release(),
        k_grid_mpc=np.array([1.0e-4, 2.0e-4], dtype=np.float64),
        cutoff_spec=CutoffCampaignSpec(
            cutoffs=(4,),
            closure_name="tier_b_tca",
            baseline_cutoff=4,
        ),
    )
    observable = build_observable_vector_from_solver_output(
        run.solver_output,
        sky_support=_sky_support(),
    )
    atlas = build_atlas_entry_lite(run.solver_output, observable)
    assert observable.manifest.production_status == "production_candidate"
    assert observable.biposh is not None
    assert observable.biposh["representation"] == "low_ell_harmonic_sparse_basis"
    assert observable.biposh["unique_index_count"] == 0
    assert observable.biposh["null_proxy_status"] == "consistent_with_isotropic_null"
    assert observable.biposh["supports_basis_reduced_morphology"] is True
    assert observable.biposh["angular_reconstruction_guard"]["passed"] is True
    assert observable.covariance_features is not None
    assert observable.covariance_features["representation"] == "low_ell_harmonic_sparse_basis"
    assert observable.covariance_features["supports_basis_reduced_morphology"] is True
    assert observable.covariance_features["supports_harmonic_gaussian"] is True
    assert (
        observable.covariance_features["harmonic_gaussian_covariance"]["representation"]
        == "low_ell_harmonic_dense_gaussian"
    )
    assert observable.covariance_features["basis_reduction_status"] == "sphere_supported_harmonic_sparse"
    assert observable.covariance_features["null_proxy_status"] == "consistent_with_isotropic_null"
    assert observable.covariance_features["local_global_degeneracy"]["status"] == "not_applicable_isotropic"
    assert observable.alm_features["backend_lookup_resolution_status"] == "frozen_v5_formula_set"
    assert observable.alm_features["backend_verification_crosscheck_pass"] is True
    assert observable.alm_features["backend_reduced_local_evaluator_available"] is True
    assert observable.alm_features["backend_reduced_harmonic_evaluator_available"] is True
    assert observable.alm_features["b_mode_runtime_available"] is False
    assert observable.alm_features["live_mode_label_harmonic_history_owner"] == (
        "ver2_native_integrator.reduced_mode_label_harmonics"
    )
    assert observable.alm_features["live_mode_label_harmonic_history_integration_scheme"] == (
        "predictor_corrector_trapezoidal"
    )
    assert set(observable.alm_features["live_mode_label_harmonic_history_mode_labels"]) == {
        "m0",
        "m+2",
        "m-2",
    }
    assert set(observable.alm_features["canonical_projection_covered_mode_labels"]) == {
        "m0",
        "m+2",
        "m-2",
    }
    assert set(observable.alm_features["canonical_projection_source_mode_labels"]) == {
        "m0",
        "m+2",
        "m-2",
    }
    assert set(observable.alm_features["canonical_projection_source_history_mode_labels"]) == {
        "m0",
        "m+2",
        "m-2",
    }
    assert set(observable.alm_features["canonical_projection_matter_mode_labels"]) == {
        "m0",
        "m+2",
        "m-2",
    }
    assert set(observable.alm_features["canonical_projection_matter_history_mode_labels"]) == {
        "m0",
        "m+2",
        "m-2",
    }
    assert observable.alm_features["covariance_readiness"] == "full"
    assert observable.alm_features["fitting_ready"] is True
    assert (
        observable.alm_features["observer_reconstruction_status"]
        == "sphere_reconstructed_from_pstf"
    )
    assert observable.alm_features["bianchi_branch"] == "orthogonal"
    assert observable.alm_features["global_tilt_contract"] == "orthogonal_branch_zero_global_tilt"
    assert (
        observable.alm_features["local_boost_contract"]
        == "observer_side_only_not_applied_in_bass_output"
    )
    assert observable.alm_features["observer_quadrature_points"] == 231
    assert (
        observable.alm_features["observer_quadrature_rule"]
        == "gauss_legendre_x_uniform_phi_tensor_product"
    )
    assert "basis_reduced_covariance_not_full_biposh" in observable.manifest.caveats
    assert "no_posterior_or_evidence_semantics" not in observable.manifest.caveats
    assert "proxy_morphology_not_full_biposh" not in observable.manifest.caveats
    assert atlas.theory_family == "I_orthogonal"
    assert atlas.manifest.production_status == "production_candidate"
    assert atlas.validity_domain["basis_reduction_status"] == "sphere_supported_harmonic_sparse"
    assert atlas.validity_domain["bianchi_branch"] == "orthogonal"
    assert atlas.validity_domain["angular_reconstruction_guard"]["passed"] is True
