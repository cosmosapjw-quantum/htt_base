from __future__ import annotations

import json

import numpy as np
import pytest
import yaml

from common.contracts import ArtifactManifest, SkySupport, SolverCoreOutput

from bass.inference.__main__ import main
from bass.inference.live_binding import (
    FittingBlockedError,
    build_live_observer_boost_problem,
    build_type_i_native_validation_problem,
    run_type_i_native_validation_posterior,
)
from bass.observational import build_observable_vector_from_solver_output
from bass.spectrum.off_diagonal_covariance import assemble_bianchi_spectrum_covariance
from bass.validation import GATE_LADDER, make_gate_bundle
from bass.validation.publication_readiness import evaluate_publication_claim


def _synthetic_manifest() -> ArtifactManifest:
    return ArtifactManifest(
        artifact_id="bass.test.statistics_ready_live",
        artifact_path="artifacts/bass/test_statistics_ready_live.json",
        owner="BASS",
        implementation_scope="canonical_BASS",
        claim_tier="conditional",
        production_status="production_candidate",
        created_by="test-suite",
        git_commit="deadbeef",
        config_hash="statistics-ready-live",
        input_hashes=["synthetic"],
        code_version="0.0-test",
        schema_version="ver2-v1",
    )


def _synthetic_sky_support() -> SkySupport:
    return SkySupport(
        selection_mode="mock_calibrated",
        sky_support_hash="sky.statistics-ready-live",
        mask_hash="mask.statistics-ready-live",
        mock_coverage_status="adequate",
        scan_volume_hash="scan.statistics-ready-live",
    )


def _synthetic_gate_registry(*, drop_gate: str | None = None) -> dict[str, object]:
    registry = {
        gate: make_gate_bundle(
            gate,
            family="I",
            branch="orthogonal",
            backend="synthetic_harmonic_gaussian_regression",
            truncation={"ell_max": 4, "cutoff_status": "production"},
            residual_summary={"max_dimensionless_residual": 1.0e-10},
            known_limit_checks={"type_i_flrw_limit": True},
            forbidden_shortcut_checks={
                "no_hidden_isotropic_fallback": True,
                "no_local_boost_merged_into_global_tilt": True,
            },
            metadata={"fixture": "statistics_ready_live"},
        )
        for gate in GATE_LADDER[:-1]
    }
    if drop_gate is not None:
        registry.pop(drop_gate)
    return registry


def _alm_payload(values: np.ndarray, *, lmax: int) -> dict[str, object]:
    n_dir = 12
    directions = np.zeros((n_dir, 3), dtype=float)
    directions[:, 2] = 1.0
    return {
        "representation": "ver2_native_pstf_sphere_reconstruction",
        "coefficient_representation": "real_pstf_packed",
        "ell_max": int(lmax),
        "values": np.asarray(values, dtype=np.float64),
        "sphere_directions": directions,
        "sphere_weights": np.full(n_dir, 1.0 / n_dir, dtype=np.float64),
        "sphere_samples": np.linspace(-0.5, 0.5, n_dir, dtype=np.float64),
        "quadrature_rule": "synthetic_unit_z_regression_grid",
    }


def _synthetic_covariance(lmax: int) -> dict[str, object]:
    k_grid = np.array([1.0e-4, 2.0e-4, 4.0e-4], dtype=np.float64)
    shape = (k_grid.size, lmax + 1, 3)
    transfer_T = np.zeros(shape, dtype=np.float64)
    transfer_E = np.zeros(shape, dtype=np.float64)
    transfer_B = np.zeros(shape, dtype=np.float64)
    for ik, k_value in enumerate(k_grid):
        k_scale = 1.0 + 0.1 * ik + 0.01 * np.log10(k_value / k_grid[0])
        for ell in range(lmax + 1):
            ell_scale = 1.0 / (ell + 1.0)
            transfer_T[ik, ell, 0] = k_scale * ell_scale
            transfer_E[ik, ell, 0] = 0.35 * k_scale * ell_scale
            transfer_B[ik, ell, 0] = 0.08 * k_scale * ell_scale
            if ell >= 2:
                transfer_T[ik, ell, 1:] = (0.18 * k_scale * ell_scale, 0.14 * k_scale * ell_scale)
                transfer_E[ik, ell, 1:] = (0.06 * k_scale * ell_scale, 0.05 * k_scale * ell_scale)
                transfer_B[ik, ell, 1:] = (0.03 * k_scale * ell_scale, 0.025 * k_scale * ell_scale)
    return assemble_bianchi_spectrum_covariance(
        transfer_bundle={
            "transfer_T": transfer_T,
            "transfer_E": transfer_E,
            "transfer_B": transfer_B,
            "structure_label": "I",
            "preferred_axis": np.array([0.0, 0.0, 1.0], dtype=np.float64),
            "mode_coupling_matrix": np.eye(3, dtype=np.float64),
            "anisotropy_strength": 0.0,
            "rotation_strength": 0.0,
        },
        k_grid_mpc=k_grid,
        ell_max=lmax,
        off_diagonal_strategy="dense_matrix",
    )


def _statistics_ready_solver_output(*, drop_gate: str | None = None) -> SolverCoreOutput:
    lmax = 4
    size = (lmax + 1) ** 2
    values_T = np.linspace(0.01, 0.25, size, dtype=np.float64)
    values_E = np.linspace(0.02, 0.12, size, dtype=np.float64)
    values_B = np.linspace(0.0, 0.04, size, dtype=np.float64)
    metadata = {
        "bianchi_type": "I",
        "bianchi_branch": "orthogonal",
        "theory_family": "I_orthogonal",
        "harmonic_basis": "real_pstf_packed",
        "eb_sign_convention": "cmb",
        "multipole_cutoff": lmax,
        "tilt_enabled": False,
        "observer_neutral": True,
        "thomson_mode": "electron_frame_exact_wrapper",
        "exact_thomson_authority_path": True,
        "exact_thomson_gate_passed": True,
        "exact_thomson_operator_scope": "linear_classical_thomson_boosted_pstf",
        "source_propagator_realization": "type_i_exact_matrix",
        "propagator_readiness": "type_i_exact_matrix",
        "propagator_exactness": "exact_type_i_branch",
        "seed_injection_mode": "family_specific_adiabatic_regular",
        "visibility_tau_reion": 0.054,
        "map_output_support": "not_implemented",
        "tilt_boost_separation": "explicit_nonmerged",
        "global_tilt_contract": "orthogonal_branch_zero_global_tilt",
        "local_boost_contract": "observer_side_only_not_applied_in_bass_output",
        "frame_split_contract": "global_tilt_solver_state_local_boost_output_only",
        "family_backend_status": "full_mode",
        "production_cutoff_status": "production_cutoff",
        "stochastic_channel_status": "disabled_zero_component",
        "b_mode_runtime_available": True,
        "b_mode_output_support": "wigner_d_path_b",
        "gate_registry": _synthetic_gate_registry(drop_gate=drop_gate),
    }
    return SolverCoreOutput(
        alm_T=_alm_payload(values_T, lmax=lmax),
        alm_E=_alm_payload(values_E, lmax=lmax),
        alm_B=_alm_payload(values_B, lmax=lmax),
        map_T=None,
        map_Q=None,
        map_U=None,
        deterministic_template={"kind": "statistics_ready_regression"},
        anisotropic_covariance=_synthetic_covariance(lmax),
        metadata=metadata,
        manifest=_synthetic_manifest(),
    )


def test_build_type_i_native_validation_problem_is_bound_to_live_bass_outputs() -> None:
    problem = build_type_i_native_validation_problem(21)
    assert problem.solver_output.manifest.owner == "BASS"
    assert problem.observable_vector.manifest.owner == "BASS"
    assert problem.solver_output.metadata["tier_b_core_owner"] == "ver2_s1s2_native"
    assert problem.solver_output.metadata["theory_family"] == "I_orthogonal"
    assert problem.observable_vector.alm_features["bianchi_branch"] == "orthogonal"
    assert (
        problem.observable_vector.alm_features["local_boost_contract"]
        == "observer_side_only_not_applied_in_bass_output"
    )
    assert problem.dataset_kind == "type_i_native_validation"
    assert problem.covariance_readiness == "full"
    assert problem.fitting_ready is False
    assert problem.solver_output.metadata["fitting_gate_enforced"] is True
    assert problem.solver_output.metadata["fitting_gate_allowed"] is False
    assert problem.solver_output.metadata["fitting_allowed"] is False
    assert problem.solver_output.metadata["diagnostic_only"] is True
    assert "production_cutoff_gate" in problem.gate_decision.missing_gates
    assert problem.solver_output.metadata["production_cutoff_status"] == "development_cutoff"
    with pytest.raises(FittingBlockedError):
        problem.log_likelihood(np.zeros(3, dtype=float))


def test_live_binding_opens_statistics_ready_claim_only_with_all_evidence() -> None:
    solver_output = _statistics_ready_solver_output()
    observable = build_observable_vector_from_solver_output(
        solver_output,
        sky_support=_synthetic_sky_support(),
    )
    assert observable.manifest.production_status == "production_candidate"
    assert observable.alm_features["covariance_readiness"] == "full"
    assert observable.alm_features["harmonic_gaussian_ready"] is True

    stochastic_zero = np.zeros((4 + 1) ** 2, dtype=np.float64)
    problem = build_live_observer_boost_problem(
        solver_output=solver_output,
        observable_vector=observable,
        stochastic_alm_T=stochastic_zero,
        stochastic_alm_E=stochastic_zero,
        stochastic_alm_B=stochastic_zero,
    )

    assert problem.fitting_ready is True
    assert problem.statistics_decision.allowed is True
    assert problem.solver_output.metadata["fitting_gate_enforced"] is True
    assert problem.solver_output.metadata["fitting_allowed"] is True
    assert problem.solver_output.metadata["diagnostic_only"] is False
    assert problem.solver_output.metadata["statistics_claim_allowed"] is True
    assert (
        problem.solver_output.metadata["statistics_owner"]
        == "bass.inference.live_binding"
    )
    assert (
        problem.likelihood.cosmo_likelihood.htt_decomposition["diagnostic_only"]
        is True
    )
    assert np.isfinite(problem.log_likelihood(np.zeros(3, dtype=np.float64)))

    decision = evaluate_publication_claim(
        "statistics_ready_likelihood",
        gate_registry=solver_output.metadata["gate_registry"],
        output_metadata=solver_output.metadata,
    )
    assert decision.allowed is True


def test_live_binding_blocks_statistics_claim_when_lower_gate_fails() -> None:
    solver_output = _statistics_ready_solver_output(drop_gate="exact_thomson_gate")
    observable = build_observable_vector_from_solver_output(
        solver_output,
        sky_support=_synthetic_sky_support(),
    )
    problem = build_live_observer_boost_problem(
        solver_output=solver_output,
        observable_vector=observable,
    )

    assert problem.fitting_ready is False
    assert problem.statistics_decision.allowed is False
    assert "gate_allowed" in problem.statistics_decision.blockers
    assert "exact_thomson_gate" in problem.gate_decision.missing_gates
    assert problem.solver_output.metadata["diagnostic_only"] is True
    with pytest.raises(FittingBlockedError):
        problem.log_likelihood(np.zeros(3, dtype=np.float64))

    decision = evaluate_publication_claim(
        "statistics_ready_likelihood",
        gate_registry=solver_output.metadata["gate_registry"],
        output_metadata=solver_output.metadata,
    )
    assert decision.allowed is False
    assert "gate_allowed" in decision.blockers


def test_run_type_i_native_validation_posterior_blocks_on_development_cutoff() -> None:
    with pytest.raises(FittingBlockedError) as exc:
        run_type_i_native_validation_posterior(
            seed=22,
            n_walkers=24,
            n_steps=40,
            burnin=10,
            parallel=False,
        )
    assert "production_cutoff_gate" in exc.value.gate_decision.missing_gates


def test_cli_accepts_type_i_native_validation_dataset_kind(tmp_path) -> None:
    config = {
        "dataset": {
            "kind": "type_i_native_validation",
        },
        "sampler": {
            "n_walkers": 24,
            "n_steps": 40,
            "burnin": 10,
            "parallel": False,
        },
        "outputs": {
            "summary_json": str(tmp_path / "bf06_live.json"),
            "summary_markdown": str(tmp_path / "bf06_live.md"),
            "posterior_dir": str(tmp_path / "posteriors"),
        },
    }
    path = tmp_path / "bf06_live.yaml"
    path.write_text(yaml.safe_dump(config), encoding="utf-8")
    exit_code = main(["--config", str(path), "--seed", "23"])
    assert exit_code in {0, 1}
    assert (tmp_path / "bf06_live.json").exists()
    assert (tmp_path / "bf06_live.md").exists()
    assert not (tmp_path / "posteriors" / "type_i_native_validation.npz").exists()
    payload = json.loads((tmp_path / "bf06_live.json").read_text(encoding="utf-8"))
    assert payload["posterior"]["binding_origin"] == "solver_core_output"
    assert payload["dataset"]["kind"] == "type_i_native_validation"
    assert payload["dataset"]["observable_production_status"] == "production_candidate"
    assert payload["posterior"]["fitting_ready"] is False
    assert payload["posterior"]["sampler"] == "blocked_by_fitting_gate"
    assert "production_cutoff_gate" in payload["posterior"]["diagnostics"]["missing_gates"]
