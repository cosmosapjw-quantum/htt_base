"""Nuisance-projected response-rank diagnostics."""
from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np
from numpy.typing import ArrayLike, NDArray


def _as_2d(value: ArrayLike, name: str) -> NDArray[np.float64]:
    array = np.asarray(value, dtype=float)
    if array.ndim == 1:
        array = array[:, None]
    if array.ndim != 2:
        raise ValueError(f"{name} must be one- or two-dimensional")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must contain finite values")
    return array


def _covariance_inv_sqrt(covariance: ArrayLike) -> NDArray[np.float64]:
    cov = np.asarray(covariance, dtype=float)
    if cov.ndim != 2 or cov.shape[0] != cov.shape[1]:
        raise ValueError("covariance must be square")
    if not np.all(np.isfinite(cov)):
        raise ValueError("covariance must contain finite values")
    cov = (cov + cov.T) / 2.0
    evals, evecs = np.linalg.eigh(cov)
    scale = max(float(np.max(np.abs(evals))), 1.0)
    if float(np.min(evals)) <= 1.0e-12 * scale:
        raise ValueError("covariance must be positive definite")
    return (evecs / np.sqrt(evals)) @ evecs.T


def _projector_orthogonal_to(
    whitened_nuisance: NDArray[np.float64] | None,
    tolerance: float,
    dimension: int,
) -> NDArray[np.float64]:
    if whitened_nuisance is None or whitened_nuisance.size == 0:
        return np.eye(dimension)
    u, singular_values, _ = np.linalg.svd(whitened_nuisance, full_matrices=False)
    if singular_values.size == 0:
        return np.eye(dimension)
    threshold = tolerance * max(float(singular_values[0]), 1.0)
    rank = int(np.sum(singular_values > threshold))
    if rank == 0:
        return np.eye(dimension)
    basis = u[:, :rank]
    return np.eye(dimension) - basis @ basis.T


@dataclass(frozen=True)
class NuisanceProjectedRankAudit:
    """Diagnostic response-rank report after nuisance projection."""

    target_dimension: int
    projected_rank: int
    singular_values: tuple[float, ...]
    rank_tolerance: float
    condition_number: float
    full_rank: bool
    no_claim_reasons: tuple[str, ...]
    owner: str = "HTT"
    implementation_scope: str = "htt"
    claim_tier: str = "diagnostic_only"
    transfer_source: str = "none"
    native_solver_result: bool = False
    family_identification: bool = False

    def as_payload(self) -> dict[str, object]:
        return {
            "owner": self.owner,
            "implementation_scope": self.implementation_scope,
            "claim_tier": self.claim_tier,
            "transfer_source": self.transfer_source,
            "native_solver_result": self.native_solver_result,
            "family_identification": self.family_identification,
            "target_dimension": self.target_dimension,
            "projected_rank": self.projected_rank,
            "singular_values": list(self.singular_values),
            "rank_tolerance": self.rank_tolerance,
            "condition_number": self.condition_number,
            "full_rank": self.full_rank,
            "no_claim_reasons": list(self.no_claim_reasons),
            "definition": (
                "rank of C^{-1/2}-whitened target response after projection "
                "orthogonal to nuisance response"
            ),
            "caveats": [
                "diagnostic rank precondition only",
                "not evidence",
                "not native solver validation",
                "not family or geometry evidence",
            ],
        }


def nuisance_projected_rank(
    target_response: ArrayLike,
    nuisance_response: ArrayLike | None,
    covariance: ArrayLike,
    tolerance: float = 1.0e-10,
) -> NuisanceProjectedRankAudit:
    """Return rank diagnostics after whitening and nuisance projection."""

    tolerance_value = float(tolerance)
    if not math.isfinite(tolerance_value) or tolerance_value <= 0.0:
        raise ValueError("tolerance must be positive finite")
    target = _as_2d(target_response, "target_response")
    whitening = _covariance_inv_sqrt(covariance)
    if whitening.shape[0] != target.shape[0]:
        raise ValueError("target_response and covariance dimensions must match")
    nuisance = None
    if nuisance_response is not None:
        nuisance = _as_2d(nuisance_response, "nuisance_response")
        if nuisance.shape[0] != target.shape[0]:
            raise ValueError("nuisance_response and covariance dimensions must match")
        nuisance = whitening @ nuisance
    projector = _projector_orthogonal_to(nuisance, tolerance_value, whitening.shape[0])
    projected = projector @ whitening @ target
    singular_values = np.linalg.svd(projected, compute_uv=False)
    leading = max(float(singular_values[0]) if singular_values.size else 0.0, 1.0)
    threshold = tolerance_value * leading
    rank = int(np.sum(singular_values > threshold))
    target_dimension = int(target.shape[1])
    full_rank = rank == target_dimension
    if singular_values.size and float(singular_values[-1]) > threshold:
        condition = float(singular_values[0] / singular_values[-1])
    else:
        condition = float("inf")
    reasons: list[str] = []
    if not full_rank:
        reasons.append("rank_deficient_after_nuisance_projection")
    return NuisanceProjectedRankAudit(
        target_dimension=target_dimension,
        projected_rank=rank,
        singular_values=tuple(float(value) for value in singular_values),
        rank_tolerance=tolerance_value,
        condition_number=condition,
        full_rank=full_rank,
        no_claim_reasons=tuple(reasons),
    )


__all__ = ["NuisanceProjectedRankAudit", "nuisance_projected_rank"]
