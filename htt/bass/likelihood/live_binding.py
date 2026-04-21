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
    propagated = 1.0 if bool(solver_output.metadata.get("propagator_ready", False)) else 0.0
    reconstruction = 1.0 if isinstance(solver_output.alm_T, Mapping) else 0.0
    return max(
        2.0,
        4.0 + 24.0 * max(offdiag_strength, 0.0) + 8.0 * max(rotation_strength, 0.0)
        + propagated + reconstruction,
    )


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
        "beta_gate_pass": bool(solver_output.metadata.get("propagator_ready", False)),
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
        "spectra_reference": {
            key: np.asarray(covariance["C_ell"].get(key, np.zeros(ell.size)), dtype=float)
            for key in _SPECTRUM_KEYS
        },
        "binding_origin": "solver_core_output",
        "solver_output_ref": solver_output.manifest.artifact_id,
        "live_bass_binding": True,
        "diagnostic_only": True,
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
