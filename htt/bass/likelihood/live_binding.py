"""Live BF-06 bindings from BASS solver outputs into legacy likelihood shells.

These helpers do not promote BASS into the model-dependent inference owner.
They only ensure that the legacy FB-7/8 likelihood scaffolding binds to the
completed observer-neutral BASS physics path instead of accepting ad hoc
decomposition dictionaries as a de facto production input.
"""
from __future__ import annotations

from collections.abc import Mapping
from math import sqrt
from typing import Any

import numpy as np

from common.contracts import SolverCoreOutput

from bass.likelihood.cosmological_frame import CosmologicalFrameLikelihood
from bass.likelihood.observer_frame_adapter import (
    FlatObserverBoostPrior,
    ObserverFrameLikelihood,
)
from bass.observer.observer_boost import ObserverBoost
from bass.spectrum.off_diagonal_covariance import (
    build_dense_harmonic_covariance,
    extract_supported_harmonic_subspace,
)

__all__ = [
    "build_live_htt_decomposition_from_solver_output",
    "build_cosmological_frame_likelihood_from_solver_output",
    "build_observer_frame_likelihood_from_solver_output",
]

_SPECTRUM_KEYS = ("TT", "EE", "TE", "BB")
_SMALL_FLOAT = 1.0e-30


def _normalise_axis(vector: object, fallback: np.ndarray) -> np.ndarray:
    arr = np.asarray(vector, dtype=float)
    norm = float(np.linalg.norm(arr))
    if not np.isfinite(norm) or norm <= _SMALL_FLOAT:
        arr = np.asarray(fallback, dtype=float)
        norm = float(np.linalg.norm(arr))
    return arr / max(norm, _SMALL_FLOAT)


def _require_live_covariance_bundle(
    solver_output: SolverCoreOutput,
) -> Mapping[str, Any]:
    if solver_output.manifest.owner != "BASS":
        raise ValueError("live likelihood binding requires a BASS-owned solver output")
    if not bool(solver_output.metadata.get("observer_neutral", False)):
        raise ValueError("live likelihood binding requires observer-neutral solver output")
    covariance = solver_output.anisotropic_covariance
    if not isinstance(covariance, Mapping):
        raise ValueError(
            "live likelihood binding requires anisotropic_covariance metadata"
        )
    if "anisotropy_tensor" not in covariance:
        raise KeyError("anisotropic_covariance must include 'anisotropy_tensor'")
    if "preferred_axis" not in covariance:
        raise KeyError("anisotropic_covariance must include 'preferred_axis'")
    if "C_ell" not in covariance or not isinstance(covariance["C_ell"], Mapping):
        raise KeyError("anisotropic_covariance must include mapping 'C_ell'")
    return covariance


def _axis_precision(
    *,
    offdiag_strength: float,
    rotation_strength: float,
    solver_output: SolverCoreOutput,
) -> float:
    propagated = (
        1.0
        if str(
            solver_output.metadata.get(
                "propagator_readiness",
                "contract_only_unavailable",
            )
        )
        != "contract_only_unavailable"
        else 0.0
    )
    reconstruction = 1.0 if isinstance(solver_output.alm_T, Mapping) else 0.0
    return max(
        2.0,
        4.0 + 24.0 * max(offdiag_strength, 0.0) + 8.0 * max(rotation_strength, 0.0)
        + propagated + reconstruction,
    )


def _covariance_readiness(solver_output: SolverCoreOutput) -> str:
    covariance = solver_output.anisotropic_covariance
    if covariance is None or not isinstance(covariance, Mapping):
        return "missing"
    try:
        dense = build_dense_harmonic_covariance(covariance)
    except Exception:
        return str(solver_output.metadata.get("covariance_readiness", "proxy"))
    if int(dense.get("subspace_size", 0)) <= 0:
        return "missing"
    return "full"


def _interop_summary(solver_output: SolverCoreOutput) -> dict[str, Any]:
    return {
        "bianchi_type": solver_output.metadata.get("bianchi_type"),
        "model_branch": solver_output.metadata.get("bianchi_branch"),
        "solver_domain_scope": solver_output.metadata.get("solver_domain_scope"),
        "theory_family": solver_output.metadata.get("theory_family"),
        "global_tilt_contract": solver_output.metadata.get("global_tilt_contract"),
        "local_boost_contract": solver_output.metadata.get("local_boost_contract"),
        "tilt_boost_separation": solver_output.metadata.get("tilt_boost_separation"),
        "frame_split_contract": solver_output.metadata.get("frame_split_contract"),
        "constraint_backend_contract": solver_output.metadata.get("constraint_backend_contract"),
        "backend_lookup_resolution_status": solver_output.metadata.get(
            "backend_lookup_resolution_status"
        ),
        "backend_verification_crosscheck_pass": bool(
            solver_output.metadata.get("backend_verification_crosscheck_pass", False)
        ),
        "backend_reduced_local_evaluator_available": bool(
            solver_output.metadata.get("backend_reduced_local_evaluator_available", False)
        ),
        "backend_reduced_harmonic_evaluator_available": bool(
            solver_output.metadata.get("backend_reduced_harmonic_evaluator_available", False)
        ),
        "backend_reduced_source_evaluator_available": bool(
            solver_output.metadata.get("backend_reduced_source_evaluator_available", False)
        ),
        "b_mode_runtime_available": bool(
            solver_output.metadata.get("b_mode_runtime_available", False)
        ),
        "canonical_projection_covered_mode_labels": list(
            solver_output.metadata.get("canonical_projection_covered_mode_labels", [])
        ),
        "canonical_projection_b_mode_labels": list(
            solver_output.metadata.get("canonical_projection_b_mode_labels", [])
        ),
        "canonical_projection_b_history_mode_labels": list(
            solver_output.metadata.get("canonical_projection_b_history_mode_labels", [])
        ),
        "canonical_projection_source_mode_labels": list(
            solver_output.metadata.get("canonical_projection_source_mode_labels", [])
        ),
        "canonical_projection_source_history_mode_labels": list(
            solver_output.metadata.get("canonical_projection_source_history_mode_labels", [])
        ),
        "canonical_projection_matter_mode_labels": list(
            solver_output.metadata.get("canonical_projection_matter_mode_labels", [])
        ),
        "canonical_projection_matter_history_mode_labels": list(
            solver_output.metadata.get("canonical_projection_matter_history_mode_labels", [])
        ),
        "live_mode_label_harmonic_history_owner": solver_output.metadata.get(
            "live_mode_label_harmonic_history_owner"
        ),
        "live_mode_label_harmonic_history_integration_scheme": solver_output.metadata.get(
            "live_mode_label_harmonic_history_integration_scheme"
        ),
        "live_mode_label_harmonic_history_sample_count": int(
            solver_output.metadata.get("live_mode_label_harmonic_history_sample_count", 0)
        ),
        "live_mode_label_harmonic_history_mode_labels": list(
            solver_output.metadata.get("live_mode_label_harmonic_history_mode_labels", [])
        ),
        "live_mode_label_harmonic_history_residual_mode_labels": list(
            solver_output.metadata.get("live_mode_label_harmonic_history_residual_mode_labels", [])
        ),
        "live_mode_label_harmonic_history_nonzero_mode_labels": list(
            solver_output.metadata.get("live_mode_label_harmonic_history_nonzero_mode_labels", [])
        ),
        "live_mode_label_harmonic_history_sector_norms": dict(
            solver_output.metadata.get("live_mode_label_harmonic_history_sector_norms", {})
        ),
        "layout_state_history_sample_count": int(
            solver_output.metadata.get("layout_state_history_sample_count", 0)
        ),
        "layout_state_history_size": int(
            solver_output.metadata.get("layout_state_history_size", 0)
        ),
        "geometry_params": solver_output.metadata.get("geometry_params"),
        "kinematic_params": solver_output.metadata.get("kinematic_params"),
        "tilt_params": solver_output.metadata.get("tilt_params"),
    }


def build_live_htt_decomposition_from_solver_output(
    solver_output: SolverCoreOutput,
    *,
    direction_grid_size: int = 64,
) -> dict[str, Any]:
    """Return a legacy-shaped decomposition sourced from live BASS output only."""
    covariance = _require_live_covariance_bundle(solver_output)
    tensor = np.asarray(covariance["anisotropy_tensor"], dtype=float)
    if tensor.shape != (3, 3):
        raise ValueError(
            f"anisotropy_tensor must have shape (3, 3); got {tensor.shape}"
        )
    tensor = 0.5 * (tensor + tensor.T)
    preferred_axis = _normalise_axis(
        covariance["preferred_axis"],
        np.array([0.0, 0.0, 1.0], dtype=float),
    )
    offdiag_strength = float(covariance.get("offdiag_strength", 0.0))
    rotation_strength = float(covariance.get("rotation_strength", 0.0))
    effective_amplitude = float(
        max(
            offdiag_strength,
            rotation_strength,
            sqrt(max(float(np.sum(tensor * tensor)), 0.0)),
        )
    )
    axis_precision = _axis_precision(
        offdiag_strength=offdiag_strength,
        rotation_strength=rotation_strength,
        solver_output=solver_output,
    )
    ell = np.asarray(
        covariance.get(
            "ell",
            np.arange(
                max(
                    (
                        len(np.asarray(covariance["C_ell"].get(key, ()), dtype=float))
                        for key in _SPECTRUM_KEYS
                    ),
                    default=0,
                ),
                dtype=int,
            ),
        ),
        dtype=int,
    )
    harmonic_covariance = build_dense_harmonic_covariance(covariance)
    support = tuple(harmonic_covariance["support"])  # type: ignore[index]
    alm_reference = {
        "T": extract_supported_harmonic_subspace(solver_output.alm_T, support),
        "E": extract_supported_harmonic_subspace(solver_output.alm_E, support),
        "B": extract_supported_harmonic_subspace(solver_output.alm_B, support),
    }
    alm_reference_packed = {
        "alm_T": np.asarray(solver_output.alm_T["values"], dtype=float),
        "alm_E": np.asarray(solver_output.alm_E["values"], dtype=float),
        "alm_B": np.asarray(solver_output.alm_B["values"], dtype=float),
    }
    return {
        "resolved_axis": preferred_axis,
        "prior_axis": preferred_axis,
        "preferred_axis": preferred_axis,
        "dominant_axis": preferred_axis,
        "tangent_axis": preferred_axis,
        "triad_status": "solver_output_bound",
        "resolution_sequence": ("solver_core_output", "anisotropic_covariance"),
        "alignment_cosine": 1.0,
        "alignment_tolerance_cos": 1.0,
        "tangency_is_tangent": True,
        "tangency_fraction_on_manifold": 1.0,
        "tangency_relative_residual": 0.0,
        "beta_gate_pass": str(
            solver_output.metadata.get(
                "propagator_readiness",
                "contract_only_unavailable",
            )
        )
        != "contract_only_unavailable",
        "beta_gate_labels": (),
        "beta_gate_diagnostics": {
            "binding_origin": "solver_core_output",
            "solver_output_ref": solver_output.manifest.artifact_id,
        },
        "effective_amplitude": effective_amplitude,
        "axis_precision": axis_precision,
        "anisotropy_tensor": tensor,
        "direction_grid_unit_vectors": np.asarray(
            covariance.get("direction_grid_unit_vectors", np.zeros((int(direction_grid_size), 3))),
            dtype=float,
        ),
        "direction_grid_scores": np.asarray(
            covariance.get("direction_grid_scores", np.zeros(int(direction_grid_size))),
            dtype=float,
        ),
        "directional_covariance": {
            "ell": ell,
            "preferred_axis": preferred_axis,
            "anisotropy_tensor": tensor,
            "offdiag_strength": offdiag_strength,
            "rotation_strength": rotation_strength,
            "C_ell": {
                key: np.asarray(covariance["C_ell"].get(key, np.zeros(ell.size)), dtype=float)
                for key in _SPECTRUM_KEYS
            },
        },
        "harmonic_covariance": harmonic_covariance,
        "harmonic_support": support,
        "harmonic_support_modes": tuple(
            f"(ell={int(row['ell'])},m={int(row['m'])})" for row in support
        ),
        "alm_reference": alm_reference,
        "alm_reference_packed": alm_reference_packed,
        "spectra_reference": {
            key: np.asarray(covariance["C_ell"].get(key, np.zeros(ell.size)), dtype=float)
            for key in _SPECTRUM_KEYS
        },
        "propagator_readiness": solver_output.metadata.get("propagator_readiness"),
        "propagator_exactness": solver_output.metadata.get("propagator_exactness"),
        "covariance_readiness": _covariance_readiness(solver_output),
        "fitting_ready": _covariance_readiness(solver_output) == "full",
        "tilt_background_owner": solver_output.metadata.get("tilt_background_owner"),
        "requested_integrator_family": solver_output.metadata.get("requested_integrator_family"),
        "resolved_solver_method": solver_output.metadata.get("resolved_solver_method"),
        "executor_realization": solver_output.metadata.get("executor_realization"),
        **_interop_summary(solver_output),
        "binding_origin": "solver_core_output",
        "solver_output_ref": solver_output.manifest.artifact_id,
        "live_bass_binding": True,
        "diagnostic_only": _covariance_readiness(solver_output) != "full",
    }


def build_cosmological_frame_likelihood_from_solver_output(
    solver_output: SolverCoreOutput,
    *,
    tier: str = "low_ell",
) -> CosmologicalFrameLikelihood:
    """Bind the FB-7 likelihood shell to a live BASS solver output."""
    return CosmologicalFrameLikelihood(
        htt_decomposition=build_live_htt_decomposition_from_solver_output(solver_output),
        tier=tier,  # type: ignore[arg-type]
    )


def build_observer_frame_likelihood_from_solver_output(
    solver_output: SolverCoreOutput,
    *,
    tier: str = "low_ell",
    boost_prior: object | None = None,
) -> ObserverFrameLikelihood:
    """Bind the FB-8 observer wrapper to a live BASS solver output."""
    if boost_prior is None:
        boost_prior = FlatObserverBoostPrior((ObserverBoost(rapidity=0.0),))
    return ObserverFrameLikelihood(
        cosmo_likelihood=build_cosmological_frame_likelihood_from_solver_output(
            solver_output,
            tier=tier,
        ),
        boost_prior=boost_prior,  # type: ignore[arg-type]
    )
