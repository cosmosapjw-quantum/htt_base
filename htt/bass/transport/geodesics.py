"""VER2 photon geodesic and screen-basis transport for the BASS S2 lane."""
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
    "photon_geodesic_rhs",
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


def _project_tangent_to_sphere(vec: np.ndarray, direction: np.ndarray) -> np.ndarray:
    e = _normalize(direction)
    arr = np.asarray(vec, dtype=np.float64)
    if arr.shape != (3,):
        raise ValueError(f"expected shape (3,), got {arr.shape}")
    return arr - float(np.dot(arr, e)) * e


def _ray_connection_drive(
    *,
    vector: np.ndarray,
    direction: np.ndarray,
    sigma_ab: np.ndarray,
    geometry: TetradGeometry | None,
) -> np.ndarray:
    sigma = np.asarray(sigma_ab, dtype=np.float64)
    if sigma.shape != (3, 3):
        raise ValueError(f"sigma_ab must have shape (3,3), got {sigma.shape}")
    e = _normalize(direction)
    vec = _normalize(vector)
    drive = -(sigma @ vec)
    if geometry is not None:
        drive -= np.einsum("abc,b,c->a", geometry.Gamma, e, vec, optimize=True)
    return np.asarray(drive, dtype=np.float64)


def _screen_basis_derivative(
    *,
    basis_vector: np.ndarray,
    companion_vector: np.ndarray,
    direction: np.ndarray,
    direction_derivative: np.ndarray,
    sigma_ab: np.ndarray,
    geometry: TetradGeometry | None,
) -> np.ndarray:
    e = _normalize(direction)
    s = _normalize(basis_vector)
    t = _normalize(companion_vector)
    raw = _ray_connection_drive(
        vector=s,
        direction=e,
        sigma_ab=sigma_ab,
        geometry=geometry,
    )
    # Preserve transversality and unit norm at the RHS level.
    raw = raw - e * (float(np.dot(e, raw)) + float(np.dot(s, direction_derivative)))
    raw = raw - s * float(np.dot(s, raw))
    # Preserve u·v = 0 by removing the companion component.
    raw = raw - t * float(np.dot(t, raw))
    return np.asarray(raw, dtype=np.float64)


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

    def __post_init__(self) -> None:
        for name in (
            "direction_derivative",
            "screen_u_derivative",
            "screen_v_derivative",
        ):
            arr = np.asarray(getattr(self, name), dtype=np.float64)
            if arr.shape != (3,):
                raise ValueError(f"{name} must have shape (3,), got {arr.shape}")
            object.__setattr__(self, name, arr)


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


def photon_geodesic_rhs(
    *,
    state: PhotonGeodesicState,
    H: float,
    sigma_ab: np.ndarray,
    geometry: TetradGeometry | None = None,
) -> PhotonGeodesicRhs:
    """Projected geodesic and screen-basis transport in the `n^a` frame.

    The hard-check energy equation remains

        d ln E / dτ = -H - σ_ab e^a e^b.

    Direction and screen transport use the same `sigma + spatial connection`
    drive and are projected back onto the unit sphere / screen bundle so the
    RHS preserves `|e| = 1`, `e·u = e·v = 0`, and `u·v = 0` to first order.
    """
    sigma = np.asarray(sigma_ab, dtype=np.float64)
    if sigma.shape != (3, 3):
        raise ValueError(f"sigma_ab must have shape (3,3), got {sigma.shape}")
    direction_derivative = _project_tangent_to_sphere(
        _ray_connection_drive(
            vector=state.direction,
            direction=state.direction,
            sigma_ab=sigma,
            geometry=geometry,
        ),
        state.direction,
    )
    screen_u_derivative = _screen_basis_derivative(
        basis_vector=state.screen_basis.u,
        companion_vector=state.screen_basis.v,
        direction=state.direction,
        direction_derivative=direction_derivative,
        sigma_ab=sigma,
        geometry=geometry,
    )
    screen_v_derivative = _screen_basis_derivative(
        basis_vector=state.screen_basis.v,
        companion_vector=state.screen_basis.u,
        direction=state.direction,
        direction_derivative=direction_derivative,
        sigma_ab=sigma,
        geometry=geometry,
    )
    return PhotonGeodesicRhs(
        log_energy_derivative=redshift_log_derivative(H, sigma_ab, state.direction),
        direction_derivative=direction_derivative,
        screen_u_derivative=screen_u_derivative,
        screen_v_derivative=screen_v_derivative,
        frame_metadata=state.frame_metadata,
    )


def photon_geodesic_rhs_stub(
    *,
    state: PhotonGeodesicState,
    H: float,
    sigma_ab: np.ndarray,
    geometry: TetradGeometry | None = None,
) -> PhotonGeodesicRhs:
    """Compatibility alias kept while call sites migrate to `photon_geodesic_rhs`."""
    return photon_geodesic_rhs(
        state=state,
        H=H,
        sigma_ab=sigma_ab,
        geometry=geometry,
    )
