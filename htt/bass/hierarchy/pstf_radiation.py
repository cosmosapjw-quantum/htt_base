"""VER2 radiation-state skeletons for the BASS S2 lane."""
from __future__ import annotations

from dataclasses import dataclass, field
from math import factorial, pi
from typing import Mapping

import numpy as np

from bass.collision.polarization import PolarizationHierarchyState, zero_polarization_hierarchy
from bass.hierarchy.frame_contracts import FrameSplitMetadata
from bass.hierarchy.contractions import stf_basis
from bass.hierarchy.pstf_tensor import PSTFHierarchyState, PSTFTensor, zero_hierarchy, zero_pstf

__all__ = [
    "RadiationNormalization",
    "TruncationMetadata",
    "RadiationPSTFState",
    "make_radiation_state",
    "project_from_angular_samples",
    "reconstruct_on_sphere",
]


@dataclass(frozen=True)
class RadiationNormalization:
    """Explicit normalization contract for `{I,E,B}` multipoles."""

    I0_to_rho_gamma: float = 1.0
    I2_to_pi_gamma: float = 1.0
    E2_convention: str = "explicit_solver_state"
    B2_convention: str = "explicit_solver_state"


@dataclass(frozen=True)
class TruncationMetadata:
    """Explicit low-`ell` truncation record."""

    L: int
    diagnostic_only: bool = False
    allow_L2_override: bool = False
    closure_name: str = "explicit_unset"
    closure_promotion_explicit: bool = True

    def __post_init__(self) -> None:
        if self.L < 2:
            raise ValueError(f"RadiationPSTFState requires L >= 2, got {self.L}")
        if self.L == 2 and not (self.diagnostic_only or self.allow_L2_override):
            raise ValueError(
                "L=2 is diagnostic-only in VER2 unless an explicit override is recorded"
            )
        if not self.closure_promotion_explicit:
            raise ValueError("closure promotion must be explicit in VER2 S2")


@dataclass(frozen=True)
class RadiationPSTFState:
    """Temperature/E/B low-`ell` PSTF bundle."""

    I: PSTFHierarchyState
    E: PolarizationHierarchyState
    B: PSTFHierarchyState
    normalization: RadiationNormalization = field(default_factory=RadiationNormalization)
    truncation: TruncationMetadata = field(default_factory=lambda: TruncationMetadata(L=6))
    frame_metadata: FrameSplitMetadata = field(default_factory=FrameSplitMetadata)

    def __post_init__(self) -> None:
        if self.I.L != self.E.L:
            raise ValueError(f"temperature and E towers must share L; got {self.I.L} vs {self.E.L}")
        if self.I.L != self.B.L:
            raise ValueError(f"temperature and B towers must share L; got {self.I.L} vs {self.B.L}")
        if self.truncation.L != self.I.L:
            raise ValueError(
                f"truncation metadata L={self.truncation.L} must match tower L={self.I.L}"
            )
        if self.frame_metadata.transport_frame != "n_frame":
            raise ValueError("radiation transport state must remain in the n^a frame")

    @property
    def L(self) -> int:
        return self.I.L


def make_radiation_state(
    L: int,
    *,
    diagnostic_only: bool = False,
    allow_L2_override: bool = False,
    closure_name: str = "explicit_unset",
) -> RadiationPSTFState:
    """Factory for an empty `{I,E,B}` radiation bundle."""
    truncation = TruncationMetadata(
        L=L,
        diagnostic_only=diagnostic_only,
        allow_L2_override=allow_L2_override,
        closure_name=closure_name,
    )
    return RadiationPSTFState(
        I=zero_hierarchy(L),
        E=zero_polarization_hierarchy(L),
        B=zero_hierarchy(L),
        truncation=truncation,
    )


def _odd_double_factorial(value: int) -> int:
    if value <= 0:
        return 1
    out = 1
    for current in range(value, 0, -2):
        out *= current
    return out


def _projection_normalization(ell: int) -> float:
    """Return the PSTF projection normalization ``N_ell``.

    SDD normalization:

        N_ell = 4π/(2ℓ+1) · ℓ! / (2ℓ-1)!!
    """
    return (4.0 * pi / float(2 * ell + 1)) * (
        factorial(ell) / float(_odd_double_factorial(2 * ell - 1))
    )


def _validate_directions(directions: np.ndarray, *, atol: float = 1e-12) -> np.ndarray:
    dirs = np.asarray(directions, dtype=np.float64)
    if dirs.ndim != 2 or dirs.shape[1] != 3:
        raise ValueError(f"directions must have shape (N, 3), got {dirs.shape}")
    norms = np.linalg.norm(dirs, axis=1)
    if not np.all(np.isfinite(norms)):
        raise ValueError("directions must be finite")
    if np.max(np.abs(norms - 1.0)) > atol:
        raise ValueError("directions must lie on the unit sphere")
    return dirs


def _validate_weights(weights: np.ndarray, count: int, *, atol: float = 1e-12) -> np.ndarray:
    quad_weights = np.asarray(weights, dtype=np.float64)
    if quad_weights.shape != (count,):
        raise ValueError(f"weights must have shape ({count},), got {quad_weights.shape}")
    if not np.all(np.isfinite(quad_weights)):
        raise ValueError("weights must be finite")
    if np.any(quad_weights <= 0.0):
        raise ValueError("weights must be strictly positive")
    if abs(float(np.sum(quad_weights)) - 4.0 * pi) > atol:
        raise ValueError("weights must sum to 4π for PSTF projection")
    return quad_weights


def _tensor_power_rows(directions: np.ndarray, ell: int) -> np.ndarray:
    if ell == 0:
        return np.ones((directions.shape[0], 1), dtype=np.float64)
    rows = np.ones((directions.shape[0], 1), dtype=np.float64)
    for _ in range(ell):
        rows = np.einsum("ni,nj->nij", rows, directions).reshape(directions.shape[0], -1)
    return rows


def _sample_basis(directions: np.ndarray, ell: int) -> np.ndarray:
    return _tensor_power_rows(directions, ell) @ stf_basis(ell)


def _validate_quadrature_rule(
    directions: np.ndarray,
    weights: np.ndarray,
    L: int,
    *,
    rtol: float,
    atol: float,
) -> None:
    sampled = [_sample_basis(directions, ell) for ell in range(L + 1)]
    weighted = weights[:, None]
    for ell, phi in enumerate(sampled):
        gram = phi.T @ (weighted * phi)
        target = _projection_normalization(ell) * np.eye(2 * ell + 1)
        if not np.allclose(gram, target, rtol=rtol, atol=atol):
            raise ValueError(
                "discrete quadrature does not satisfy the PSTF normalization "
                f"contract at ell={ell}"
            )
    for ell_a in range(L + 1):
        for ell_b in range(ell_a + 1, L + 1):
            cross = sampled[ell_a].T @ (weighted * sampled[ell_b])
            if not np.allclose(cross, 0.0, rtol=0.0, atol=atol):
                raise ValueError(
                    "discrete quadrature does not preserve cross-rank PSTF "
                    f"orthogonality for ell=({ell_a}, {ell_b})"
                )


def _channel_samples(
    samples: Mapping[str, np.ndarray],
    key: str,
    count: int,
    *,
    dtype: np.dtype,
) -> np.ndarray:
    if key not in samples:
        return np.zeros(count, dtype=dtype)
    arr = np.asarray(samples[key], dtype=dtype)
    if arr.shape != (count,):
        raise ValueError(f"samples['{key}'] must have shape ({count},), got {arr.shape}")
    return arr


def _project_scalar_channel(
    channel_samples: np.ndarray,
    directions: np.ndarray,
    weights: np.ndarray,
    *,
    L: int,
) -> PSTFHierarchyState:
    tensors: list[PSTFTensor] = []
    weighted_samples = weights * channel_samples
    for ell in range(L + 1):
        phi = _sample_basis(directions, ell)
        coeffs = (phi.T @ weighted_samples) / _projection_normalization(ell)
        tensors.append(PSTFTensor(ell=ell, components=coeffs))
    return PSTFHierarchyState(L=L, tensors=tensors)


def _project_polarized_channel(
    channel_samples: np.ndarray,
    directions: np.ndarray,
    weights: np.ndarray,
    *,
    L: int,
    low_rank_tol: float,
) -> PSTFHierarchyState:
    tower = _project_scalar_channel(channel_samples, directions, weights, L=L)
    for ell in (0, 1):
        if ell > L:
            break
        if np.max(np.abs(tower.tensors[ell].components)) > low_rank_tol:
            raise ValueError(
                "polarization samples carry forbidden ell<2 support under the "
                "PSTF E/B contract"
            )
    tensors = [zero_pstf(ell) if ell < 2 else tower.tensors[ell] for ell in range(L + 1)]
    return PSTFHierarchyState(L=L, tensors=tensors)


def project_from_angular_samples(
    samples: Mapping[str, np.ndarray],
    directions: np.ndarray,
    weights: np.ndarray,
    *,
    L: int,
    normalization: RadiationNormalization | None = None,
    truncation: TruncationMetadata | None = None,
    frame_metadata: FrameSplitMetadata | None = None,
    quadrature_rtol: float = 1e-10,
    quadrature_atol: float = 1e-10,
    polarization_low_rank_tol: float = 1e-10,
) -> RadiationPSTFState:
    """Project angular samples onto the PSTF radiation tower.

    This follows the SDD projection contract directly:

        c_{ell m} = N_ell^{-1} ∫ dΩ F(e) Q_{ell m}(e)

    where ``Q_{ell m}(e)`` is the contraction of the orthonormal STF basis
    tensor with ``e^{A_ell}``. The caller must provide a discrete quadrature
    rule exact enough to reproduce the same orthogonality relations up to the
    requested truncation order; otherwise the function raises instead of
    silently downgrading to a least-squares proxy.
    """
    if L < 2:
        raise ValueError(f"RadiationPSTFState requires L >= 2, got {L}")
    dirs = _validate_directions(directions)
    quad_weights = _validate_weights(weights, dirs.shape[0])
    _validate_quadrature_rule(
        dirs,
        quad_weights,
        L,
        rtol=quadrature_rtol,
        atol=quadrature_atol,
    )
    channel_dtype = np.complex128 if any(np.iscomplexobj(samples[key]) for key in samples) else np.float64
    count = dirs.shape[0]
    intensity_samples = _channel_samples(samples, "I", count, dtype=channel_dtype)
    e_samples = _channel_samples(samples, "E", count, dtype=channel_dtype)
    b_samples = _channel_samples(samples, "B", count, dtype=channel_dtype)
    tower_I = _project_scalar_channel(intensity_samples, dirs, quad_weights, L=L)
    tower_E = _project_polarized_channel(
        e_samples,
        dirs,
        quad_weights,
        L=L,
        low_rank_tol=polarization_low_rank_tol,
    )
    tower_B = _project_polarized_channel(
        b_samples,
        dirs,
        quad_weights,
        L=L,
        low_rank_tol=polarization_low_rank_tol,
    )
    if truncation is None:
        truncation = TruncationMetadata(
            L=L,
            diagnostic_only=False,
            allow_L2_override=(L == 2),
            closure_name="quadrature_projection",
        )
    if normalization is None:
        normalization = RadiationNormalization()
    if frame_metadata is None:
        frame_metadata = FrameSplitMetadata()
    return RadiationPSTFState(
        I=tower_I,
        E=PolarizationHierarchyState(E=tower_E),
        B=tower_B,
        normalization=normalization,
        truncation=truncation,
        frame_metadata=frame_metadata,
    )


def _reconstruct_channel(
    tower: PSTFHierarchyState,
    directions: np.ndarray,
    *,
    min_ell: int = 0,
) -> np.ndarray:
    dtype = np.complex128 if any(np.iscomplexobj(t.components) for t in tower.tensors) else np.float64
    result = np.zeros(directions.shape[0], dtype=dtype)
    for ell in range(min_ell, tower.L + 1):
        phi = _sample_basis(directions, ell)
        result = result + phi @ np.asarray(tower.tensors[ell].components, dtype=dtype)
    return result


def reconstruct_on_sphere(
    state: RadiationPSTFState,
    directions: np.ndarray,
) -> dict[str, np.ndarray]:
    """Reconstruct `{I,E,B}` angular samples from the PSTF radiation tower."""
    dirs = _validate_directions(directions)
    return {
        "I": _reconstruct_channel(state.I, dirs, min_ell=0),
        "E": _reconstruct_channel(state.E.E, dirs, min_ell=2),
        "B": _reconstruct_channel(state.B, dirs, min_ell=2),
    }
