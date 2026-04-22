"""ver3 Tier-A ray/screen-basis transport contracts."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

import numpy as np

from bass.collision.electron_frame import SourceTerms, exact_thomson_source
from bass.hierarchy.frame_contracts import FrameSplitMetadata
from bass.transport.geodesics import (
    PhotonGeodesicState,
    ScreenBasisState,
    photon_geodesic_rhs,
)

__all__ = [
    "TierAState",
    "TierARayRhs",
    "TierAScreenBasisRhs",
    "ray_rhs",
    "screen_basis_rhs",
    "collision_source_tierA",
]


def _coerce_vector3(value: np.ndarray, *, name: str) -> np.ndarray:
    arr = np.asarray(value, dtype=np.float64)
    if arr.shape != (3,):
        raise ValueError(f"{name} must have shape (3,), got {arr.shape}")
    return arr


@dataclass(frozen=True)
class TierAState:
    eta: float
    ray_direction: np.ndarray
    screen_basis: ScreenBasisState
    phase: float
    I_dir: np.ndarray
    P_dir: np.ndarray
    source_history: Mapping[str, object] = field(default_factory=dict)
    energy: float = 1.0
    frame_metadata: FrameSplitMetadata = field(default_factory=FrameSplitMetadata)

    def __post_init__(self) -> None:
        ray_direction = _coerce_vector3(self.ray_direction, name="TierAState.ray_direction")
        if not np.isfinite(float(self.eta)):
            raise ValueError("TierAState.eta must be finite")
        if not np.isfinite(float(self.phase)):
            raise ValueError("TierAState.phase must be finite")
        if not np.isfinite(float(self.energy)) or float(self.energy) <= 0.0:
            raise ValueError("TierAState.energy must be positive finite")
        I_dir = np.asarray(self.I_dir, dtype=np.float64)
        P_dir = np.asarray(self.P_dir, dtype=np.float64)
        if I_dir.shape != P_dir.shape:
            raise ValueError(
                f"TierAState I_dir and P_dir must share shape, got {I_dir.shape} and {P_dir.shape}"
            )
        geodesic = PhotonGeodesicState(
            energy=float(self.energy),
            direction=ray_direction,
            screen_basis=self.screen_basis,
            frame_metadata=self.frame_metadata,
        )
        object.__setattr__(self, "ray_direction", geodesic.direction)
        object.__setattr__(self, "I_dir", I_dir)
        object.__setattr__(self, "P_dir", P_dir)
        object.__setattr__(self, "source_history", dict(self.source_history))


@dataclass(frozen=True)
class TierARayRhs:
    direction_dot: np.ndarray
    energy_dot: float
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "direction_dot", _coerce_vector3(self.direction_dot, name="TierARayRhs.direction_dot"))
        object.__setattr__(self, "metadata", dict(self.metadata))


@dataclass(frozen=True)
class TierAScreenBasisRhs:
    basis_dot_u: np.ndarray
    basis_dot_v: np.ndarray
    phase_dot: float
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "basis_dot_u", _coerce_vector3(self.basis_dot_u, name="TierAScreenBasisRhs.basis_dot_u"))
        object.__setattr__(self, "basis_dot_v", _coerce_vector3(self.basis_dot_v, name="TierAScreenBasisRhs.basis_dot_v"))
        if not np.isfinite(float(self.phase_dot)):
            raise ValueError("TierAScreenBasisRhs.phase_dot must be finite")
        object.__setattr__(self, "metadata", dict(self.metadata))


def _photon_state(ray_state: TierAState) -> PhotonGeodesicState:
    return PhotonGeodesicState(
        energy=float(ray_state.energy),
        direction=np.asarray(ray_state.ray_direction, dtype=np.float64),
        screen_basis=ray_state.screen_basis,
        frame_metadata=ray_state.frame_metadata,
    )


def _bg_kinematics(bg: Mapping[str, object]) -> tuple[float, np.ndarray, object | None]:
    if not isinstance(bg, Mapping):
        raise ValueError("bg must be a mapping")
    H = float(bg["H"])
    sigma_ab = np.asarray(bg["sigma_ab"], dtype=np.float64)
    if sigma_ab.shape != (3, 3):
        raise ValueError(f"bg['sigma_ab'] must have shape (3,3), got {sigma_ab.shape}")
    geometry = bg.get("geometry")
    return H, sigma_ab, geometry


def ray_rhs(eta: float, ray_state: TierAState, bg: Mapping[str, object]) -> TierARayRhs:
    """Tier-A ray transport signature frozen by the ver3 note."""

    del eta
    H, sigma_ab, geometry = _bg_kinematics(bg)
    rhs = photon_geodesic_rhs(
        state=_photon_state(ray_state),
        H=H,
        sigma_ab=sigma_ab,
        geometry=geometry,
    )
    return TierARayRhs(
        direction_dot=rhs.direction_derivative,
        energy_dot=float(ray_state.energy) * float(rhs.log_energy_derivative),
        metadata={
            "transport_frame": ray_state.frame_metadata.transport_frame,
            "direction_convention": ray_state.frame_metadata.direction_convention.value,
        },
    )


def screen_basis_rhs(
    eta: float,
    ray_state: TierAState,
    bg: Mapping[str, object],
) -> TierAScreenBasisRhs:
    """Tier-A screen-basis transport with explicit phase evolution."""

    del eta
    H, sigma_ab, geometry = _bg_kinematics(bg)
    rhs = photon_geodesic_rhs(
        state=_photon_state(ray_state),
        H=H,
        sigma_ab=sigma_ab,
        geometry=geometry,
    )
    phase_dot = 0.5 * (
        float(np.dot(ray_state.screen_basis.v, rhs.screen_u_derivative))
        - float(np.dot(ray_state.screen_basis.u, rhs.screen_v_derivative))
    )
    return TierAScreenBasisRhs(
        basis_dot_u=rhs.screen_u_derivative,
        basis_dot_v=rhs.screen_v_derivative,
        phase_dot=phase_dot,
        metadata={
            "polarization_phase_convention": ray_state.frame_metadata.polarization_phase_convention.value,
            "transport_frame": ray_state.frame_metadata.transport_frame,
        },
    )


def collision_source_tierA(
    eta: float,
    ray_state: TierAState,
    bg: Mapping[str, object],
    electron_frame_data: Mapping[str, object],
) -> SourceTerms:
    """Direction-resolved Tier-A collision source owned by the electron frame."""

    del eta, bg
    if not isinstance(electron_frame_data, Mapping):
        raise ValueError("electron_frame_data must be a mapping")
    opacity_data = dict(electron_frame_data.get("opacity_data", {}))
    if "Gamma_T" not in opacity_data and "Gamma_T" in electron_frame_data:
        opacity_data["Gamma_T"] = electron_frame_data["Gamma_T"]
    opacity_data.setdefault(
        "direction_convention",
        ray_state.frame_metadata.direction_convention,
    )
    return exact_thomson_source(
        ray_state.ray_direction,
        ray_state.I_dir,
        electron_frame_data.get("I0", 0.0),
        ray_state.P_dir,
        electron_frame_data.get("I2", 0.0),
        electron_frame_data.get("E2_pol", 0.0),
        opacity_data,
    )
