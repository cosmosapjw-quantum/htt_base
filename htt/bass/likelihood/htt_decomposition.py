"""FB-7.3 HTT decomposition with explicit P0-triad resolution.

The HTT boundary keeps the P0 triad visible instead of hiding it inside
the later likelihood builder:

1. prior alignment,
2. tangency response,
3. beta-gate allow/block status.

The on-disk Lowell ``§14.2`` locator supplied in the historical prompt
is absent in this worktree and remains an explicit audit gap.  The
resolution order implemented here therefore follows the Phase-FB-META-7
audit contract and the downstream FB-8 dependency pin rather than an
invented locator.
"""
from __future__ import annotations

from collections.abc import Mapping

import numpy as np

from bass.runtime.canonical_decision import CanonicalDecision
from tsc.diagnostics.tangency import TangencyResult

_SMALL_FLOAT = 1.0e-30


def _normalise_axis(vector: np.ndarray, fallback: np.ndarray) -> np.ndarray:
    arr = np.asarray(vector, dtype=float)
    norm = float(np.linalg.norm(arr))
    if not np.isfinite(norm) or norm <= _SMALL_FLOAT:
        arr = np.asarray(fallback, dtype=float)
        norm = float(np.linalg.norm(arr))
    return arr / max(norm, _SMALL_FLOAT)


def _extract_prior_axis(
    prior_alignment: Mapping[str, object], fallback: np.ndarray
) -> np.ndarray:
    for key in ("axis_vector", "preferred_axis", "prior_axis", "direction"):
        if key in prior_alignment:
            return _normalise_axis(np.asarray(prior_alignment[key], dtype=float), fallback)
    return _normalise_axis(np.asarray(fallback, dtype=float), np.array([0.0, 0.0, 1.0]))


def _fibonacci_sphere(n_points: int) -> np.ndarray:
    n = max(int(n_points), 8)
    idx = np.arange(n, dtype=float)
    phi = np.pi * (3.0 - np.sqrt(5.0))
    y = 1.0 - 2.0 * (idx + 0.5) / n
    radius = np.sqrt(np.maximum(0.0, 1.0 - y * y))
    theta = phi * idx
    return np.column_stack((radius * np.cos(theta), radius * np.sin(theta), y))


def build_htt_decomposition(
    *,
    directional_covariance: Mapping[str, np.ndarray],
    prior_alignment: Mapping[str, object],
    tangency_result: TangencyResult,
    beta_gate: CanonicalDecision,
) -> dict[str, object]:
    """Resolve the FB-7.3 HTT-facing decomposition and P0 triad.

    Parameters
    ----------
    directional_covariance
        FB-7.2 output bundle.  At minimum it must provide
        ``anisotropy_tensor`` and ``preferred_axis``; the diagonal
        spectra ``C_ell`` are forwarded when present so FB-7.4 can
        evaluate the cosmological-frame likelihood without reopening the
        decomposition boundary.
    prior_alignment
        Prior-supplied axis information.  The mapping may carry
        ``axis_vector`` / ``preferred_axis`` plus optional tuning keys
        ``alignment_tolerance_cos`` and ``direction_grid_size``.
    tangency_result
        Existing TSC tangency diagnostic.  Its scalar diagnostics are
        consumed here; no new tangency heuristic is introduced.
    beta_gate
        Existing canonical allow/block verdict.  If it blocks
        reduction, the FB-7.3 decomposition preserves that decision and
        zeroes the effective anisotropy amplitude instead of reopening
        a hidden beta policy.
    """
    if "anisotropy_tensor" not in directional_covariance:
        raise KeyError("directional_covariance must include 'anisotropy_tensor'")
    tensor = np.asarray(directional_covariance["anisotropy_tensor"], dtype=float)
    if tensor.shape != (3, 3):
        raise ValueError("anisotropy_tensor must have shape (3, 3)")
    if not np.all(np.isfinite(tensor)):
        raise ValueError("anisotropy_tensor must be finite")
    tensor = 0.5 * (tensor + tensor.T)

    preferred_axis = _normalise_axis(
        np.asarray(
            directional_covariance.get("preferred_axis", np.array([0.0, 0.0, 1.0])),
            dtype=float,
        ),
        np.array([0.0, 0.0, 1.0]),
    )
    prior_axis = _extract_prior_axis(prior_alignment, preferred_axis)

    evals, evecs = np.linalg.eigh(tensor)
    dominant_axis = _normalise_axis(evecs[:, int(np.argmax(evals))], preferred_axis)
    alignment_cosine = abs(float(np.dot(prior_axis, dominant_axis)))
    tangency_fraction = float(tangency_result.fraction_on_manifold)
    tangency_fraction = min(max(tangency_fraction, 0.0), 1.0)
    tangent_axis = _normalise_axis(
        tangency_fraction * prior_axis + (1.0 - tangency_fraction) * dominant_axis,
        dominant_axis,
    )

    tolerance = float(prior_alignment.get("alignment_tolerance_cos", 0.97))
    if not tangency_result.is_tangent:
        triad_status = "dominant_fallback"
        resolved_axis = dominant_axis
    elif not beta_gate.allow_reduction:
        triad_status = "beta_gate_blocked"
        resolved_axis = prior_axis
    elif alignment_cosine >= tolerance:
        triad_status = "prior_locked"
        resolved_axis = prior_axis
    else:
        triad_status = "tangent_realigned"
        resolved_axis = tangent_axis

    offdiag_strength = float(
        directional_covariance.get("offdiag_strength", np.linalg.norm(tensor))
    )
    effective_amplitude = (
        offdiag_strength * tangency_fraction if beta_gate.allow_reduction else 0.0
    )
    axis_precision = max(
        2.0,
        6.0
        + 8.0 * alignment_cosine
        + 18.0 * effective_amplitude
        + (3.0 if tangency_result.is_tangent else 0.0),
    )

    direction_grid_size = int(prior_alignment.get("direction_grid_size", 64))
    direction_grid_unit_vectors = _fibonacci_sphere(direction_grid_size)
    quadratic_scores = np.einsum(
        "ni,ij,nj->n",
        direction_grid_unit_vectors,
        tensor,
        direction_grid_unit_vectors,
    )
    direction_grid_scores = (
        axis_precision * (direction_grid_unit_vectors @ resolved_axis) + quadratic_scores
    )

    return {
        "resolved_axis": resolved_axis,
        "prior_axis": prior_axis,
        "preferred_axis": preferred_axis,
        "dominant_axis": dominant_axis,
        "tangent_axis": tangent_axis,
        "triad_status": triad_status,
        "resolution_sequence": ("prior_alignment", "tangency", "beta_gate"),
        "alignment_cosine": alignment_cosine,
        "alignment_tolerance_cos": tolerance,
        "tangency_is_tangent": bool(tangency_result.is_tangent),
        "tangency_fraction_on_manifold": tangency_fraction,
        "tangency_relative_residual": float(tangency_result.relative_residual),
        "beta_gate_pass": bool(beta_gate.allow_reduction),
        "beta_gate_labels": tuple(sorted(label.value for label in beta_gate.emitted_labels)),
        "beta_gate_diagnostics": dict(beta_gate.diagnostics),
        "effective_amplitude": effective_amplitude,
        "axis_precision": axis_precision,
        "anisotropy_tensor": tensor,
        "direction_grid_unit_vectors": direction_grid_unit_vectors,
        "direction_grid_scores": direction_grid_scores,
        "directional_covariance": directional_covariance,
        "spectra_reference": directional_covariance.get("C_ell", {}),
    }
