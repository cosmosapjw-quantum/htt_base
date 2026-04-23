from __future__ import annotations

import numpy as np
import pytest

from bass.inference.live_binding import build_type_i_native_validation_problem
from bass.likelihood.live_binding import (
    build_cosmological_frame_likelihood_from_solver_output,
    build_observer_frame_likelihood_from_solver_output,
)
from bass.observer.observer_boost import ObserverBoost


@pytest.fixture(scope="module")
def _live_problem():
    return build_type_i_native_validation_problem(11)


def test_live_cosmological_frame_likelihood_binds_to_solver_output(_live_problem) -> None:
    likelihood = build_cosmological_frame_likelihood_from_solver_output(
        _live_problem.solver_output
    )
    assert likelihood.htt_decomposition["binding_origin"] == "solver_core_output"
    assert (
        likelihood.htt_decomposition["solver_output_ref"]
        == _live_problem.solver_output.manifest.artifact_id
    )
    assert bool(likelihood.htt_decomposition["live_bass_binding"]) is True
    assert likelihood.htt_decomposition["model_branch"] == "orthogonal"
    assert (
        likelihood.htt_decomposition["global_tilt_contract"]
        == "orthogonal_branch_zero_global_tilt"
    )
    assert (
        likelihood.htt_decomposition["local_boost_contract"]
        == "observer_side_only_not_applied_in_bass_output"
    )
    assert likelihood.htt_decomposition["tilt_boost_separation"] == "explicit_nonmerged"
    assert likelihood.htt_decomposition["covariance_readiness"] == "full"
    assert likelihood.htt_decomposition["fitting_ready"] is True
    assert likelihood.htt_decomposition["backend_lookup_resolution_status"] == "frozen_v5_formula_set"
    assert likelihood.htt_decomposition["backend_verification_crosscheck_pass"] is True
    assert likelihood.htt_decomposition["backend_reduced_local_evaluator_available"] is True
    assert likelihood.htt_decomposition["backend_reduced_harmonic_evaluator_available"] is True
    assert likelihood.htt_decomposition["b_mode_runtime_available"] is False
    assert likelihood.htt_decomposition["live_mode_label_harmonic_history_owner"] == (
        "ver2_native_integrator.main_state_mode_label_harmonics"
    )
    assert likelihood.htt_decomposition["live_mode_label_harmonic_history_integration_scheme"] == (
        "main_state_coevolved"
    )
    assert set(likelihood.htt_decomposition["live_mode_label_harmonic_history_mode_labels"]) == {
        "m0",
        "m+2",
        "m-2",
    }
    assert set(likelihood.htt_decomposition["canonical_projection_covered_mode_labels"]) == {
        "m0",
        "m+2",
        "m-2",
    }
    assert set(likelihood.htt_decomposition["canonical_projection_source_mode_labels"]) == {
        "m0",
        "m+2",
        "m-2",
    }
    assert set(likelihood.htt_decomposition["canonical_projection_source_history_mode_labels"]) == {
        "m0",
        "m+2",
        "m-2",
    }
    assert set(likelihood.htt_decomposition["canonical_projection_matter_mode_labels"]) == {
        "m0",
        "m+2",
        "m-2",
    }
    assert set(likelihood.htt_decomposition["canonical_projection_matter_history_mode_labels"]) == {
        "m0",
        "m+2",
        "m-2",
    }
    assert likelihood.harmonic_gaussian_ready is True
    assert np.isfinite(likelihood.log_prob({}))


def test_live_observer_frame_likelihood_accepts_live_solver_output(_live_problem) -> None:
    likelihood = build_observer_frame_likelihood_from_solver_output(
        _live_problem.solver_output
    )
    value = likelihood.log_prob({"observer_boost": ObserverBoost(rapidity=0.0)})
    assert np.isfinite(value)
