"""VER2 photon geodesic and screen-basis skeletons for the BASS S2 lane."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from bass.background.geometry import TetradGeometry
from bass.hierarchy.frame_contracts import FrameSplitMetadata

__all__ = [
    "ScreenBasisState",
    "PhotonGeodesicState",
    "PhotonGeodesicRhs",
    "redshift_log_derivative",
    "hard_redshift_check",
    "photon_geodesic_rhs_stub",
]


def _normalize(vec: np.ndarray) -> np.ndarray:
    arr = np.asarray(vec, dtype=np.float64)
    norm = float(np.linalg.norm(arr))
    if arr.shape != (3,):
        raise ValueError(f"expected shape (3,), got {arr.shape}")
    if norm == 0.0:
        raise ValueError("zero-length direction or screen-basis vector")
    return arr / norm


@dataclass(frozen=True)
class ScreenBasisState:
    """Explicit screen basis and phase-convention record."""

    u: np.ndarray
    v: np.ndarray
    frame_metadata: FrameSplitMetadata = field(default_factory=FrameSplitMetadata)

    def __post_init__(self) -> None:
        u = _normalize(self.u)
        v = _normalize(self.v)
        if abs(float(np.dot(u, v))) > 1e-12:
            raise ValueError("screen basis must be orthonormal")
        object.__setattr__(self, "u", u)
        object.__setattr__(self, "v", v)


@dataclass(frozen=True)
class PhotonGeodesicState:
    """Minimal geodesic state for the S2 skeleton surface."""

    energy: float
    direction: np.ndarray
    screen_basis: ScreenBasisState
    frame_metadata: FrameSplitMetadata = field(default_factory=FrameSplitMetadata)

    def __post_init__(self) -> None:
        if not np.isfinite(self.energy) or self.energy <= 0.0:
            raise ValueError(f"photon energy must be positive finite, got {self.energy!r}")
        direction = _normalize(self.direction)
        if abs(float(np.dot(direction, self.screen_basis.u))) > 1e-12:
            raise ValueError("screen basis u must be transverse to propagation direction")
        if abs(float(np.dot(direction, self.screen_basis.v))) > 1e-12:
            raise ValueError("screen basis v must be transverse to propagation direction")
        object.__setattr__(self, "direction", direction)


@dataclass(frozen=True)
class PhotonGeodesicRhs:
    """Skeleton RHS bundle for one geodesic step."""

    log_energy_derivative: float
    direction_derivative: np.ndarray
    screen_u_derivative: np.ndarray
    screen_v_derivative: np.ndarray
    frame_metadata: FrameSplitMetadata


def redshift_log_derivative(
    H: float,
    sigma_ab: np.ndarray,
    direction: np.ndarray,
) -> float:
    """Return `d ln E / dτ = -H - σ_ab e^a e^b`."""
    sigma = np.asarray(sigma_ab, dtype=np.float64)
    e = _normalize(direction)
    return -float(H) - float(e @ sigma @ e)


def hard_redshift_check(
    H: float,
    sigma_ab: np.ndarray,
    direction: np.ndarray,
) -> float:
    """Return `d ln(aE)/dτ`, which must equal `-σ_ab e^a e^b`."""
    return redshift_log_derivative(H, sigma_ab, direction) + float(H)


def photon_geodesic_rhs_stub(
    *,
    state: PhotonGeodesicState,
    H: float,
    sigma_ab: np.ndarray,
    geometry: TetradGeometry | None = None,
) -> PhotonGeodesicRhs:
    """Skeleton geodesic RHS.

    The full direction and screen-basis transport depend on the spacetime
    connection and polarization rotation rate. `SK-02S2` freezes the
    contract and the hard redshift formula only; direction/screen transport
    remain zero-derivative placeholders until the executable solver packet.
    """
    _ = geometry
    zeros = np.zeros(3, dtype=np.float64)
    return PhotonGeodesicRhs(
        log_energy_derivative=redshift_log_derivative(H, sigma_ab, state.direction),
        direction_derivative=zeros.copy(),
        screen_u_derivative=zeros.copy(),
        screen_v_derivative=zeros.copy(),
        frame_metadata=state.frame_metadata,
    )
