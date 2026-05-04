"""VER2 electron-frame Thomson projection for the BASS S2 lane."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

import numpy as np

from bass.hierarchy.frame_contracts import FrameSplitMetadata, PhotonDirectionConvention
from bass.hierarchy.pstf_tensor import PSTFHierarchyState, zero_hierarchy
from bass.collision.polarization import PolarizationHierarchyState
from bass.collision.thomson_pstf import (
    EModeThomsonCollisionOperator,
    ThomsonPSTFCollisionOperator,
)
from bass.collision._tilted_layer_b_common import apply_axisymmetric_boost_to_tower
from bass.collision.tilted_eb_mixing import _b_mode_collision_tower, _boost_eb_towers
from bass.species.tilted import TiltedSpeciesBackground
from bass.validation import GateBundle, make_gate_bundle

__all__ = [
    "ElectronFrameRate",
    "ElectronFrameThomsonContext",
    "ProjectedThomsonSource",
    "ExactThomsonSource",
    "AngularStokesThomsonSource",
    "AngularStokesTemperatureCollision",
    "FullStokesMuellerKernel",
    "FullStokesTemperatureKernel",
    "SourceTerms",
    "build_full_stokes_mueller_kernel",
    "electron_frame_rate_factor",
    "build_full_stokes_temperature_kernel",
    "full_stokes_mueller_collision",
    "full_stokes_temperature_collision",
    "full_stokes_thomson_source",
    "exact_thomson_source",
    "exact_thomson_gate_bundle",
    "project_thomson_source",
    "project_thomson_source_stub",
    "rotate_screen_basis",
    "rotate_stokes_samples",
]


@dataclass(frozen=True)
class ElectronFrameRate:
    gamma_e: float
    factor: float
    direction_convention: PhotonDirectionConvention


@dataclass(frozen=True)
class ElectronFrameThomsonContext:
    """Metadata surface for projected Thomson scattering."""

    frame_metadata: FrameSplitMetadata = field(default_factory=FrameSplitMetadata)
    direction_convention: PhotonDirectionConvention = PhotonDirectionConvention.PROPAGATION
    projection_mode: str = "pstf_projected"
    operator_scope: str = "linear_classical_thomson"
    orthogonal_reference_operator: str = "ThomsonPSTFCollisionOperator"
    isotropic_null_mode_required: bool = True
    linearity_required: bool = True

    def __post_init__(self) -> None:
        if self.frame_metadata.collision_frame != "electron_frame":
            raise ValueError("Thomson collision must remain electron-frame in VER2")
        if self.projection_mode not in {"pstf_projected", "angular_grid"}:
            raise ValueError(f"unknown projection_mode {self.projection_mode!r}")
        if self.operator_scope != "linear_classical_thomson":
            raise ValueError("SK-02S2 freezes classical linear Thomson only")


@dataclass(frozen=True)
class ProjectedThomsonSource:
    """Projected Thomson collision source in the solver's PSTF basis."""

    temperature: PSTFHierarchyState
    polarization_E: PolarizationHierarchyState
    polarization_B: PSTFHierarchyState
    effective_rate: ElectronFrameRate
    frame_metadata: FrameSplitMetadata = field(default_factory=FrameSplitMetadata)
    source_ready: bool = True
    linearity_required: bool = True
    isotropic_null_mode_required: bool = True
    pure_quadrupole_response_required: bool = True
    operator_scope: str = "linear_classical_thomson_boosted_pstf"

    def __post_init__(self) -> None:
        if self.temperature.L != self.polarization_E.L:
            raise ValueError(
                "temperature and E-mode towers must share the same truncation depth"
            )
        if self.temperature.L != self.polarization_B.L:
            raise ValueError(
                "temperature and B-mode towers must share the same truncation depth"
            )
        if self.frame_metadata.collision_frame != "electron_frame":
            raise ValueError("projected Thomson source must remain electron-frame owned")
        if self.operator_scope not in {
            "linear_classical_thomson_boosted_pstf",
            "full_electron_frame_stokes",
            "full_stokes_scalarized_q_u_projected_pstf",
            "full_stokes_spin2_angular_polarization",
        }:
            raise ValueError(f"unknown projected Thomson operator_scope {self.operator_scope!r}")


@dataclass(frozen=True)
class ExactThomsonSource:
    """ver3 wrapper exposing scalar/directional Thomson source ownership."""

    projected: ProjectedThomsonSource
    scalar_monopole_input: float
    directional_temperature_norm: float
    polarization_quadrupole_norm: float
    effective_opacity: float
    source_split: str = "scalar_monopole_vs_directional_tensor"
    opacity_contract: str = "electron_frame_tilt_modulated"

    def __post_init__(self) -> None:
        if self.effective_opacity < 0.0 or not np.isfinite(self.effective_opacity):
            raise ValueError("effective_opacity must be non-negative finite")
        if self.source_split != "scalar_monopole_vs_directional_tensor":
            raise ValueError("exact Thomson split contract changed unexpectedly")
        if self.opacity_contract != "electron_frame_tilt_modulated":
            raise ValueError("exact Thomson opacity contract changed unexpectedly")

    @property
    def source_ready(self) -> bool:
        return bool(self.projected.source_ready)


@dataclass(frozen=True)
class AngularStokesThomsonSource:
    """Electron-frame angular Thomson operator over Stokes ``I,Q,U``.

    The arrays are defined on a common outgoing angular grid. ``source_*`` is
    the Rayleigh/Thomson in-scattering integral and ``collision_*`` is the full
    collision term ``opacity * (source - current)``. This is the authority path
    for full electron-frame Stokes checks; it is intentionally separate from
    the low-ell PSTF projection wrapper.
    """

    directions: np.ndarray
    basis_u: np.ndarray
    basis_v: np.ndarray
    weights: np.ndarray
    source_I: np.ndarray
    source_Q: np.ndarray
    source_U: np.ndarray
    collision_I: np.ndarray
    collision_Q: np.ndarray
    collision_U: np.ndarray
    effective_opacity: np.ndarray
    scalar_monopole_input: float
    directional_temperature_norm: float
    polarization_norm: float
    source_split: str = "angular_stokes_mueller_integral"
    opacity_contract: str = "electron_frame_tilt_modulated"
    operator_scope: str = "full_electron_frame_stokes"
    basis_transport_contract: str = "explicit_screen_basis_spin2_rotation"
    source_ready: bool = True

    def __post_init__(self) -> None:
        n = np.asarray(self.directions, dtype=np.float64)
        if n.ndim != 2 or n.shape[1] != 3:
            raise ValueError("directions must have shape (N,3)")
        size = n.shape[0]
        for name in (
            "basis_u",
            "basis_v",
        ):
            arr = np.asarray(getattr(self, name), dtype=np.float64)
            if arr.shape != (size, 3):
                raise ValueError(f"{name} must have shape ({size},3)")
            object.__setattr__(self, name, arr)
        for name in (
            "weights",
            "source_I",
            "source_Q",
            "source_U",
            "collision_I",
            "collision_Q",
            "collision_U",
            "effective_opacity",
        ):
            arr = np.asarray(getattr(self, name), dtype=np.float64)
            if arr.shape != (size,):
                raise ValueError(f"{name} must have shape ({size},)")
            if not np.all(np.isfinite(arr)):
                raise ValueError(f"{name} contains non-finite values")
            object.__setattr__(self, name, arr)
        if np.any(np.asarray(self.effective_opacity) < 0.0):
            raise ValueError("effective_opacity must be non-negative")
        if self.source_split != "angular_stokes_mueller_integral":
            raise ValueError("unexpected angular Stokes source split")
        if self.operator_scope != "full_electron_frame_stokes":
            raise ValueError("angular Stokes source must declare full Stokes scope")
        if self.basis_transport_contract != "explicit_screen_basis_spin2_rotation":
            raise ValueError("angular Stokes source must declare screen-basis spin-2 rotation")
        object.__setattr__(self, "directions", n)


@dataclass(frozen=True)
class FullStokesMuellerKernel:
    """Cached full Stokes Thomson/Rayleigh Mueller kernel for one angular grid."""

    directions: np.ndarray
    basis_u: np.ndarray
    basis_v: np.ndarray
    weights: np.ndarray
    source_matrix: np.ndarray
    channel_order: tuple[str, str, str] = ("I", "Q", "U")

    def __post_init__(self) -> None:
        directions = np.asarray(self.directions, dtype=np.float64)
        if directions.ndim != 2 or directions.shape[1] != 3:
            raise ValueError("directions must have shape (N,3)")
        size = directions.shape[0]
        object.__setattr__(self, "directions", directions)
        for name in ("basis_u", "basis_v"):
            arr = np.asarray(getattr(self, name), dtype=np.float64)
            if arr.shape != (size, 3):
                raise ValueError(f"{name} must have shape ({size},3)")
            object.__setattr__(self, name, arr)
        weights = np.asarray(self.weights, dtype=np.float64)
        if weights.shape != (size,):
            raise ValueError(f"weights must have shape ({size},)")
        object.__setattr__(self, "weights", weights)
        source_matrix = np.asarray(self.source_matrix, dtype=np.float64)
        if source_matrix.shape != (3, 3, size, size):
            raise ValueError(
                f"source_matrix must have shape (3,3,{size},{size})"
            )
        if not np.all(np.isfinite(source_matrix)):
            raise ValueError("source_matrix contains non-finite values")
        object.__setattr__(self, "source_matrix", source_matrix)
        if tuple(self.channel_order) != ("I", "Q", "U"):
            raise ValueError("FullStokesMuellerKernel channel order is frozen to I,Q,U")


@dataclass(frozen=True)
class FullStokesTemperatureKernel:
    """Cached linear Stokes-to-temperature Thomson kernel for one angular grid."""

    directions: np.ndarray
    basis_u: np.ndarray
    basis_v: np.ndarray
    weights: np.ndarray
    source_from_I: np.ndarray
    source_from_Q: np.ndarray
    source_from_U: np.ndarray

    def __post_init__(self) -> None:
        directions = np.asarray(self.directions, dtype=np.float64)
        if directions.ndim != 2 or directions.shape[1] != 3:
            raise ValueError("directions must have shape (N,3)")
        size = directions.shape[0]
        object.__setattr__(self, "directions", directions)
        for name in ("basis_u", "basis_v"):
            arr = np.asarray(getattr(self, name), dtype=np.float64)
            if arr.shape != (size, 3):
                raise ValueError(f"{name} must have shape ({size},3)")
            object.__setattr__(self, name, arr)
        weights = np.asarray(self.weights, dtype=np.float64)
        if weights.shape != (size,):
            raise ValueError(f"weights must have shape ({size},)")
        object.__setattr__(self, "weights", weights)
        for name in ("source_from_I", "source_from_Q", "source_from_U"):
            matrix = np.asarray(getattr(self, name), dtype=np.float64)
            if matrix.shape != (size, size):
                raise ValueError(f"{name} must have shape ({size},{size})")
            if not np.all(np.isfinite(matrix)):
                raise ValueError(f"{name} contains non-finite values")
            object.__setattr__(self, name, matrix)


@dataclass(frozen=True)
class AngularStokesTemperatureCollision:
    """Temperature-channel projection of the full angular Stokes Thomson kernel."""

    source_I: np.ndarray
    collision_I: np.ndarray
    effective_opacity: np.ndarray
    operator_scope: str = "full_stokes_temperature_mueller_integral"

    def __post_init__(self) -> None:
        source_I = np.asarray(self.source_I, dtype=np.float64)
        collision_I = np.asarray(self.collision_I, dtype=np.float64)
        effective_opacity = np.asarray(self.effective_opacity, dtype=np.float64)
        if source_I.shape != collision_I.shape or source_I.shape != effective_opacity.shape:
            raise ValueError("temperature collision arrays must share shape")
        for name, arr in (
            ("source_I", source_I),
            ("collision_I", collision_I),
            ("effective_opacity", effective_opacity),
        ):
            if not np.all(np.isfinite(arr)):
                raise ValueError(f"{name} contains non-finite values")
            object.__setattr__(self, name, arr)
        if np.any(effective_opacity < 0.0):
            raise ValueError("effective_opacity must be non-negative")
        if self.operator_scope != "full_stokes_temperature_mueller_integral":
            raise ValueError("unexpected temperature Stokes operator scope")


@dataclass(frozen=True)
class SourceTerms:
    """Document-level directional Thomson source terms."""

    dI_dir: np.ndarray
    dP_dir: np.ndarray
    effective_opacity: float
    direction_convention: PhotonDirectionConvention
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        dI = np.asarray(self.dI_dir, dtype=np.float64)
        dP = np.asarray(self.dP_dir, dtype=np.float64)
        if dI.shape != dP.shape:
            raise ValueError(
                f"dI_dir and dP_dir must share shape, got {dI.shape} and {dP.shape}"
            )
        if not np.isfinite(self.effective_opacity) or self.effective_opacity < 0.0:
            raise ValueError("effective_opacity must be non-negative finite")
        object.__setattr__(self, "dI_dir", dI)
        object.__setattr__(self, "dP_dir", dP)
        object.__setattr__(self, "metadata", dict(self.metadata))


def electron_frame_rate_factor(
    *,
    gamma_e: float,
    v_dot_direction: float,
    convention: PhotonDirectionConvention = PhotonDirectionConvention.PROPAGATION,
) -> ElectronFrameRate:
    """Return the exact electron-frame scattering-rate factor.

    For propagation direction `e^a`, the factor is `γ_e (1 - v·e)`.
    For observed sky direction `n_sky = -e`, the factor is `γ_e (1 + v·n_sky)`.
    """
    if gamma_e < 1.0:
        raise ValueError(f"gamma_e must be >= 1, got {gamma_e!r}")
    if convention is PhotonDirectionConvention.PROPAGATION:
        factor = gamma_e * (1.0 - float(v_dot_direction))
    else:
        factor = gamma_e * (1.0 + float(v_dot_direction))
    return ElectronFrameRate(
        gamma_e=float(gamma_e),
        factor=float(factor),
        direction_convention=convention,
    )


def _effective_rate(
    *,
    context: ElectronFrameThomsonContext,
    direction: np.ndarray | None,
    tilted_electron: TiltedSpeciesBackground | None,
) -> ElectronFrameRate:
    if tilted_electron is None or tilted_electron.beta == 0.0:
        return ElectronFrameRate(
            gamma_e=1.0,
            factor=1.0,
            direction_convention=context.direction_convention,
        )
    if direction is None:
        raise ValueError("nonzero tilted_electron requires an explicit photon direction")
    direction_arr = np.asarray(direction, dtype=np.float64)
    if direction_arr.shape != (3,):
        raise ValueError(f"direction must have shape (3,), got {direction_arr.shape}")
    direction_norm = float(np.linalg.norm(direction_arr))
    if direction_norm == 0.0:
        raise ValueError("direction must be non-zero when tilted_electron is supplied")
    direction_hat = direction_arr / direction_norm
    v_vec = tilted_electron.beta * np.asarray(tilted_electron.v_hat_e, dtype=np.float64)
    return electron_frame_rate_factor(
        gamma_e=tilted_electron.gamma,
        v_dot_direction=float(np.dot(v_vec, direction_hat)),
        convention=context.direction_convention,
    )


def _coerce_unit_directions(value: object, *, name: str) -> np.ndarray:
    arr = np.asarray(value, dtype=np.float64)
    if arr.ndim != 2 or arr.shape[1] != 3:
        raise ValueError(f"{name} must have shape (N,3), got {arr.shape}")
    if arr.shape[0] == 0:
        raise ValueError(f"{name} must contain at least one direction")
    norms = np.linalg.norm(arr, axis=1)
    if np.any(~np.isfinite(norms)) or np.any(norms <= 0.0):
        raise ValueError(f"{name} contains non-finite or zero directions")
    return arr / norms[:, None]


def _default_screen_basis(directions: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    dirs = _coerce_unit_directions(directions, name="directions")
    u = np.empty_like(dirs)
    v = np.empty_like(dirs)
    z_ref = np.array([0.0, 0.0, 1.0], dtype=np.float64)
    x_ref = np.array([1.0, 0.0, 0.0], dtype=np.float64)
    for i, direction in enumerate(dirs):
        ref = z_ref if abs(float(np.dot(direction, z_ref))) < 0.9 else x_ref
        u_i = ref - float(np.dot(ref, direction)) * direction
        u_i /= np.linalg.norm(u_i)
        v_i = np.cross(direction, u_i)
        v_i /= np.linalg.norm(v_i)
        u[i] = u_i
        v[i] = v_i
    return u, v


def _validate_screen_basis(
    directions: np.ndarray,
    basis_u: object | None,
    basis_v: object | None,
) -> tuple[np.ndarray, np.ndarray]:
    dirs = _coerce_unit_directions(directions, name="directions")
    if basis_u is None or basis_v is None:
        if basis_u is not None or basis_v is not None:
            raise ValueError("basis_u and basis_v must be supplied together")
        return _default_screen_basis(dirs)
    u = np.asarray(basis_u, dtype=np.float64).copy()
    v = np.asarray(basis_v, dtype=np.float64).copy()
    if u.shape != dirs.shape or v.shape != dirs.shape:
        raise ValueError("basis_u and basis_v must match directions shape")
    for label, arr in (("basis_u", u), ("basis_v", v)):
        norms = np.linalg.norm(arr, axis=1)
        if np.any(~np.isfinite(norms)) or np.any(norms <= 0.0):
            raise ValueError(f"{label} contains non-finite or zero vectors")
        arr /= norms[:, None]
    if np.max(np.abs(np.sum(dirs * u, axis=1))) > 1.0e-10:
        raise ValueError("basis_u must be transverse to directions")
    if np.max(np.abs(np.sum(dirs * v, axis=1))) > 1.0e-10:
        raise ValueError("basis_v must be transverse to directions")
    if np.max(np.abs(np.sum(u * v, axis=1))) > 1.0e-10:
        raise ValueError("basis_u and basis_v must be orthogonal")
    return u, v


def rotate_screen_basis(
    directions: object,
    basis_u: object,
    basis_v: object,
    angle: float | np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Rotate each transverse screen basis about its photon direction.

    The returned basis keeps ``v = direction x u``. This is the local
    polarization-basis transport primitive needed for spin-2 Stokes
    covariance checks.
    """

    dirs = _coerce_unit_directions(directions, name="directions")
    u, v = _validate_screen_basis(dirs, basis_u, basis_v)
    angles = np.asarray(angle, dtype=np.float64)
    if angles.shape == ():
        angles = np.full(dirs.shape[0], float(angles), dtype=np.float64)
    if angles.shape != (dirs.shape[0],):
        raise ValueError(f"angle must be scalar or shape ({dirs.shape[0]},)")
    if not np.all(np.isfinite(angles)):
        raise ValueError("angle contains non-finite values")
    c = np.cos(angles)[:, None]
    s = np.sin(angles)[:, None]
    rotated_u = c * u + s * v
    rotated_v = c * v - s * u
    return _validate_screen_basis(dirs, rotated_u, rotated_v)


def rotate_stokes_samples(
    Q: object,
    U: object,
    old_u: object,
    old_v: object,
    new_u: object,
    new_v: object,
) -> tuple[np.ndarray, np.ndarray]:
    """Rotate Stokes ``Q,U`` samples between two transverse screen bases."""

    old_u_arr = np.asarray(old_u, dtype=np.float64)
    old_v_arr = np.asarray(old_v, dtype=np.float64)
    new_u_arr = np.asarray(new_u, dtype=np.float64)
    new_v_arr = np.asarray(new_v, dtype=np.float64)
    if not (
        old_u_arr.shape == old_v_arr.shape == new_u_arr.shape == new_v_arr.shape
        and old_u_arr.ndim == 2
        and old_u_arr.shape[1] == 3
    ):
        raise ValueError("screen basis arrays must all have shape (N,3)")
    count = old_u_arr.shape[0]
    q_arr = np.asarray(Q, dtype=np.float64)
    u_arr = np.asarray(U, dtype=np.float64)
    if q_arr.shape != (count,) or u_arr.shape != (count,):
        raise ValueError(f"Q and U must have shape ({count},)")
    if np.any(~np.isfinite(q_arr)) or np.any(~np.isfinite(u_arr)):
        raise ValueError("Q/U contain non-finite values")
    q_out = np.empty(count, dtype=np.float64)
    u_out = np.empty(count, dtype=np.float64)
    for idx in range(count):
        q_out[idx], u_out[idx] = _rotate_stokes(
            float(q_arr[idx]),
            float(u_arr[idx]),
            old_u_arr[idx],
            old_v_arr[idx],
            new_u_arr[idx],
            new_v_arr[idx],
        )
    return q_out, u_out


def _scatter_one_stokes_component(
    *,
    incoming_value: tuple[float, float, float],
    incoming: np.ndarray,
    outgoing: np.ndarray,
    incoming_u: np.ndarray,
    incoming_v: np.ndarray,
    outgoing_u: np.ndarray,
    outgoing_v: np.ndarray,
) -> tuple[float, float, float]:
    a_in, b_in, a_out, b_out, mu = _scattering_plane_basis(
        incoming=incoming,
        outgoing=outgoing,
        incoming_u=incoming_u,
        outgoing_u=outgoing_u,
    )
    q_sc, u_sc = _rotate_stokes(
        incoming_value[1],
        incoming_value[2],
        incoming_u,
        incoming_v,
        a_in,
        b_in,
    )
    mu2 = mu * mu
    sin2 = max(0.0, 1.0 - mu2)
    I_scattered = (1.0 + mu2) * incoming_value[0] + sin2 * q_sc
    Q_scattered = sin2 * incoming_value[0] + (1.0 + mu2) * q_sc
    U_scattered = 2.0 * mu * u_sc
    q_out, u_out = _rotate_stokes(
        Q_scattered,
        U_scattered,
        a_out,
        b_out,
        outgoing_u,
        outgoing_v,
    )
    return I_scattered, q_out, u_out


def build_full_stokes_mueller_kernel(
    *,
    directions: object,
    weights: object,
    basis_u: object | None = None,
    basis_v: object | None = None,
) -> FullStokesMuellerKernel:
    """Precompute the full linear Stokes Thomson/Rayleigh kernel."""

    dirs = _coerce_unit_directions(directions, name="directions")
    u_basis, v_basis = _validate_screen_basis(dirs, basis_u, basis_v)
    size = dirs.shape[0]
    weights_arr = np.asarray(weights, dtype=np.float64)
    if weights_arr.shape != (size,):
        raise ValueError(f"weights must have shape ({size},)")
    if np.any(~np.isfinite(weights_arr)) or np.any(weights_arr < 0.0):
        raise ValueError("weights must be finite non-negative solid-angle weights")
    source_matrix = np.zeros((3, 3, size, size), dtype=np.float64)
    basis_stokes = (
        (1.0, 0.0, 0.0),
        (0.0, 1.0, 0.0),
        (0.0, 0.0, 1.0),
    )
    norm = 3.0 / (16.0 * np.pi)
    for out_idx in range(size):
        outgoing = dirs[out_idx]
        out_u = u_basis[out_idx]
        out_v = v_basis[out_idx]
        for in_idx in range(size):
            incoming = dirs[in_idx]
            weight = norm * float(weights_arr[in_idx])
            for in_channel, stokes_basis in enumerate(basis_stokes):
                scattered = _scatter_one_stokes_component(
                    incoming_value=stokes_basis,
                    incoming=incoming,
                    outgoing=outgoing,
                    incoming_u=u_basis[in_idx],
                    incoming_v=v_basis[in_idx],
                    outgoing_u=out_u,
                    outgoing_v=out_v,
                )
                for out_channel, value in enumerate(scattered):
                    source_matrix[out_channel, in_channel, out_idx, in_idx] = (
                        weight * float(value)
                    )
    return FullStokesMuellerKernel(
        directions=dirs,
        basis_u=u_basis,
        basis_v=v_basis,
        weights=weights_arr,
        source_matrix=source_matrix,
    )


def build_full_stokes_temperature_kernel(
    *,
    directions: object,
    weights: object,
    basis_u: object | None = None,
    basis_v: object | None = None,
) -> FullStokesTemperatureKernel:
    """Precompute the temperature row of the full Stokes Mueller integral.

    This preserves the angular Stokes physics of :func:`full_stokes_thomson_source`
    for the intensity collision channel while avoiding the Python scattering
    loop inside every hierarchy RHS evaluation.
    """

    mueller = build_full_stokes_mueller_kernel(
        directions=directions,
        weights=weights,
        basis_u=basis_u,
        basis_v=basis_v,
    )
    return FullStokesTemperatureKernel(
        directions=mueller.directions,
        basis_u=mueller.basis_u,
        basis_v=mueller.basis_v,
        weights=mueller.weights,
        source_from_I=mueller.source_matrix[0, 0],
        source_from_Q=mueller.source_matrix[0, 1],
        source_from_U=mueller.source_matrix[0, 2],
    )


def _angular_effective_opacity(
    *,
    directions: np.ndarray,
    Gamma_T: float,
    tilted_electron: TiltedSpeciesBackground | None,
    direction_convention: PhotonDirectionConvention,
) -> np.ndarray:
    if tilted_electron is None or tilted_electron.beta == 0.0:
        return np.full(directions.shape[0], float(Gamma_T), dtype=np.float64)
    v_vec = tilted_electron.beta * np.asarray(
        tilted_electron.v_hat_e,
        dtype=np.float64,
    )
    effective_opacity = np.empty(directions.shape[0], dtype=np.float64)
    for idx, direction in enumerate(directions):
        rate = electron_frame_rate_factor(
            gamma_e=tilted_electron.gamma,
            v_dot_direction=float(np.dot(v_vec, direction)),
            convention=direction_convention,
        )
        effective_opacity[idx] = float(Gamma_T) * rate.factor
    return effective_opacity


def full_stokes_temperature_collision(
    *,
    kernel: FullStokesTemperatureKernel,
    I: object,
    Q: object,
    U: object,
    Gamma_T: float,
    tilted_electron: TiltedSpeciesBackground | None = None,
    direction_convention: PhotonDirectionConvention = PhotonDirectionConvention.PROPAGATION,
) -> AngularStokesTemperatureCollision:
    """Apply a cached full-Stokes kernel to the temperature collision channel."""

    size = kernel.directions.shape[0]
    I_arr = np.asarray(I, dtype=np.float64)
    Q_arr = np.asarray(Q, dtype=np.float64)
    U_arr = np.asarray(U, dtype=np.float64)
    for name, arr in (("I", I_arr), ("Q", Q_arr), ("U", U_arr)):
        if arr.shape != (size,):
            raise ValueError(f"{name} must have shape ({size},)")
        if np.any(~np.isfinite(arr)):
            raise ValueError(f"{name} contains non-finite values")
    if not np.isfinite(float(Gamma_T)) or float(Gamma_T) < 0.0:
        raise ValueError("Gamma_T must be non-negative finite")
    source_I = (
        kernel.source_from_I @ I_arr
        + kernel.source_from_Q @ Q_arr
        + kernel.source_from_U @ U_arr
    )
    effective_opacity = _angular_effective_opacity(
        directions=kernel.directions,
        Gamma_T=float(Gamma_T),
        tilted_electron=tilted_electron,
        direction_convention=direction_convention,
    )
    collision_I = effective_opacity * (source_I - I_arr)
    return AngularStokesTemperatureCollision(
        source_I=source_I,
        collision_I=collision_I,
        effective_opacity=effective_opacity,
    )


def full_stokes_mueller_collision(
    *,
    kernel: FullStokesMuellerKernel,
    I: object,
    Q: object,
    U: object,
    Gamma_T: float,
    tilted_electron: TiltedSpeciesBackground | None = None,
    direction_convention: PhotonDirectionConvention = PhotonDirectionConvention.PROPAGATION,
) -> AngularStokesThomsonSource:
    """Apply a cached full Stokes Mueller kernel to all Stokes channels."""

    size = kernel.directions.shape[0]
    channels = []
    for name, payload in (("I", I), ("Q", Q), ("U", U)):
        arr = np.asarray(payload, dtype=np.float64)
        if arr.shape != (size,):
            raise ValueError(f"{name} must have shape ({size},)")
        if np.any(~np.isfinite(arr)):
            raise ValueError(f"{name} contains non-finite values")
        channels.append(arr)
    if not np.isfinite(float(Gamma_T)) or float(Gamma_T) < 0.0:
        raise ValueError("Gamma_T must be non-negative finite")
    incoming = np.stack(channels, axis=0)
    source = np.zeros_like(incoming)
    for out_channel in range(3):
        for in_channel in range(3):
            source[out_channel] = (
                source[out_channel]
                + kernel.source_matrix[out_channel, in_channel] @ incoming[in_channel]
            )
    effective_opacity = _angular_effective_opacity(
        directions=kernel.directions,
        Gamma_T=float(Gamma_T),
        tilted_electron=tilted_electron,
        direction_convention=direction_convention,
    )
    collision = effective_opacity[None, :] * (source - incoming)
    monopole = float(
        np.sum(kernel.weights * channels[0]) / max(np.sum(kernel.weights), 1.0e-300)
    )
    return AngularStokesThomsonSource(
        directions=kernel.directions,
        basis_u=kernel.basis_u,
        basis_v=kernel.basis_v,
        weights=kernel.weights,
        source_I=source[0],
        source_Q=source[1],
        source_U=source[2],
        collision_I=collision[0],
        collision_Q=collision[1],
        collision_U=collision[2],
        effective_opacity=effective_opacity,
        scalar_monopole_input=monopole,
        directional_temperature_norm=float(np.linalg.norm(channels[0] - monopole)),
        polarization_norm=float(
            np.sqrt(np.dot(channels[1], channels[1]) + np.dot(channels[2], channels[2]))
        ),
    )


def _rotate_stokes(
    Q: float,
    U: float,
    old_u: np.ndarray,
    old_v: np.ndarray,
    new_u: np.ndarray,
    new_v: np.ndarray,
) -> tuple[float, float]:
    cu = float(np.dot(new_u, old_u))
    su = float(np.dot(new_u, old_v))
    cv = float(np.dot(new_v, old_u))
    sv = float(np.dot(new_v, old_v))
    q_new = float(Q) * (cu * cu - su * su) + float(U) * (2.0 * cu * su)
    u_new = float(Q) * (cu * cv - su * sv) + float(U) * (cu * sv + su * cv)
    return q_new, u_new


def _scattering_plane_basis(
    *,
    incoming: np.ndarray,
    outgoing: np.ndarray,
    incoming_u: np.ndarray,
    outgoing_u: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, float]:
    mu = float(np.clip(np.dot(incoming, outgoing), -1.0, 1.0))
    sin2 = max(0.0, 1.0 - mu * mu)
    if sin2 <= 1.0e-24:
        a_in = incoming_u - float(np.dot(incoming_u, incoming)) * incoming
        if np.linalg.norm(a_in) <= 1.0e-14:
            a_in, _ = _default_screen_basis(incoming.reshape(1, 3))
            a_in = a_in[0]
        a_in /= np.linalg.norm(a_in)
        a_out = outgoing_u - float(np.dot(outgoing_u, outgoing)) * outgoing
        if np.linalg.norm(a_out) <= 1.0e-14:
            a_out, _ = _default_screen_basis(outgoing.reshape(1, 3))
            a_out = a_out[0]
        a_out /= np.linalg.norm(a_out)
    else:
        sin_theta = float(np.sqrt(sin2))
        a_in = (outgoing - mu * incoming) / sin_theta
        a_out = (incoming - mu * outgoing) / sin_theta
    b_in = np.cross(incoming, a_in)
    b_in /= np.linalg.norm(b_in)
    b_out = np.cross(outgoing, a_out)
    b_out /= np.linalg.norm(b_out)
    return a_in, b_in, a_out, b_out, mu


def full_stokes_thomson_source(
    *,
    directions: object,
    weights: object,
    I: object,
    Q: object,
    U: object,
    Gamma_T: float,
    basis_u: object | None = None,
    basis_v: object | None = None,
    tilted_electron: TiltedSpeciesBackground | None = None,
    direction_convention: PhotonDirectionConvention = PhotonDirectionConvention.PROPAGATION,
) -> AngularStokesThomsonSource:
    """Evaluate the full electron-frame Thomson/Rayleigh Stokes integral.

    The kernel is the classical Mueller matrix in the scattering-plane basis,
    rotated from and back to each direction's screen basis. The quadrature
    weights are solid-angle weights and should sum to ``4π`` for exact monopole
    normalization.
    """

    dirs = _coerce_unit_directions(directions, name="directions")
    u_basis, v_basis = _validate_screen_basis(dirs, basis_u, basis_v)
    size = dirs.shape[0]
    weights_arr = np.asarray(weights, dtype=np.float64)
    if weights_arr.shape != (size,):
        raise ValueError(f"weights must have shape ({size},)")
    if np.any(~np.isfinite(weights_arr)) or np.any(weights_arr < 0.0):
        raise ValueError("weights must be finite non-negative solid-angle weights")
    I_arr = np.asarray(I, dtype=np.float64)
    Q_arr = np.asarray(Q, dtype=np.float64)
    U_arr = np.asarray(U, dtype=np.float64)
    for name, arr in (("I", I_arr), ("Q", Q_arr), ("U", U_arr)):
        if arr.shape != (size,):
            raise ValueError(f"{name} must have shape ({size},)")
        if np.any(~np.isfinite(arr)):
            raise ValueError(f"{name} contains non-finite values")
    if not np.isfinite(float(Gamma_T)) or float(Gamma_T) < 0.0:
        raise ValueError("Gamma_T must be non-negative finite")

    source_I = np.zeros(size, dtype=np.float64)
    source_Q = np.zeros(size, dtype=np.float64)
    source_U = np.zeros(size, dtype=np.float64)
    norm = 3.0 / (16.0 * np.pi)
    for out_idx in range(size):
        outgoing = dirs[out_idx]
        out_u = u_basis[out_idx]
        out_v = v_basis[out_idx]
        for in_idx in range(size):
            incoming = dirs[in_idx]
            a_in, b_in, a_out, b_out, mu = _scattering_plane_basis(
                incoming=incoming,
                outgoing=outgoing,
                incoming_u=u_basis[in_idx],
                outgoing_u=out_u,
            )
            q_sc, u_sc = _rotate_stokes(
                float(Q_arr[in_idx]),
                float(U_arr[in_idx]),
                u_basis[in_idx],
                v_basis[in_idx],
                a_in,
                b_in,
            )
            mu2 = mu * mu
            sin2 = max(0.0, 1.0 - mu2)
            I_scattered = (1.0 + mu2) * float(I_arr[in_idx]) + sin2 * q_sc
            Q_scattered = sin2 * float(I_arr[in_idx]) + (1.0 + mu2) * q_sc
            U_scattered = 2.0 * mu * u_sc
            q_out, u_out = _rotate_stokes(
                Q_scattered,
                U_scattered,
                a_out,
                b_out,
                out_u,
                out_v,
            )
            weight = norm * float(weights_arr[in_idx])
            source_I[out_idx] += weight * I_scattered
            source_Q[out_idx] += weight * q_out
            source_U[out_idx] += weight * u_out

    effective_opacity = _angular_effective_opacity(
        directions=dirs,
        Gamma_T=float(Gamma_T),
        tilted_electron=tilted_electron,
        direction_convention=direction_convention,
    )

    collision_I = effective_opacity * (source_I - I_arr)
    collision_Q = effective_opacity * (source_Q - Q_arr)
    collision_U = effective_opacity * (source_U - U_arr)
    monopole = float(np.sum(weights_arr * I_arr) / max(np.sum(weights_arr), 1.0e-300))
    return AngularStokesThomsonSource(
        directions=dirs,
        basis_u=u_basis,
        basis_v=v_basis,
        weights=weights_arr,
        source_I=source_I,
        source_Q=source_Q,
        source_U=source_U,
        collision_I=collision_I,
        collision_Q=collision_Q,
        collision_U=collision_U,
        effective_opacity=effective_opacity,
        scalar_monopole_input=monopole,
        directional_temperature_norm=float(np.linalg.norm(I_arr - monopole)),
        polarization_norm=float(np.sqrt(np.dot(Q_arr, Q_arr) + np.dot(U_arr, U_arr))),
    )


def project_thomson_source(
    context: ElectronFrameThomsonContext,
    *,
    temperature_state: PSTFHierarchyState,
    polarization_state: PolarizationHierarchyState,
    v_b_real_sph: np.ndarray,
    Gamma_T: float,
    direction: np.ndarray | None = None,
    tilted_electron: TiltedSpeciesBackground | None = None,
    b_state: PSTFHierarchyState | None = None,
) -> ProjectedThomsonSource:
    """Project the classical electron-frame Thomson source into PSTF towers.

    Orthogonal runs reuse the established LB-4 operators directly. Tilted runs
    dispatch to the shipped Layer-B boost path rather than collapsing to an
    FLRW-only scalar shortcut.
    """
    if not np.isfinite(Gamma_T) or Gamma_T < 0.0:
        raise ValueError(f"Gamma_T must be non-negative finite, got {Gamma_T!r}")
    if context.frame_metadata.no_flrw_only_collision_shortcut is not True:
        raise ValueError("VER2 collision path forbids FLRW-only shortcuts")
    if temperature_state.L != polarization_state.L:
        raise ValueError(
            f"temperature L={temperature_state.L} must match polarization L={polarization_state.L}"
        )
    b_mode_state = zero_hierarchy(temperature_state.L) if b_state is None else b_state.copy()
    if b_mode_state.L != temperature_state.L:
        raise ValueError(
            f"b_state.L={b_mode_state.L} must match temperature L={temperature_state.L}"
        )
    rate = _effective_rate(
        context=context,
        direction=direction,
        tilted_electron=tilted_electron,
    )
    effective_gamma = float(Gamma_T) * rate.factor
    t_op = ThomsonPSTFCollisionOperator()
    e_op = EModeThomsonCollisionOperator()
    if tilted_electron is None or tilted_electron.beta == 0.0:
        temperature = t_op.evaluate_tower(
            temperature_state,
            polarization_state,
            np.asarray(v_b_real_sph, dtype=np.float64),
            effective_gamma,
        )
        polarization_E = e_op.evaluate_tower(
            polarization_state,
            np.asarray(temperature_state.tensors[2].components, dtype=np.float64),
            effective_gamma,
        )
        polarization_B = zero_hierarchy(temperature_state.L)
    else:
        v_b_arr = np.asarray(v_b_real_sph, dtype=np.float64)
        boosted_temperature = apply_axisymmetric_boost_to_tower(
            temperature_state,
            beta=tilted_electron.beta,
            v_hat_e=tilted_electron.v_hat_e,
        )
        boosted_polarization = PolarizationHierarchyState(
            E=apply_axisymmetric_boost_to_tower(
                polarization_state.E,
                beta=tilted_electron.beta,
                v_hat_e=tilted_electron.v_hat_e,
            )
        )
        pi_2_e_frame = np.asarray(
            boosted_temperature.tensors[2].components,
            dtype=np.float64,
        )
        collision_e_frame_temperature = t_op.evaluate_tower(
            boosted_temperature,
            boosted_polarization,
            v_b_arr,
            effective_gamma,
        )
        temperature = apply_axisymmetric_boost_to_tower(
            collision_e_frame_temperature,
            beta=-tilted_electron.beta,
            v_hat_e=tilted_electron.v_hat_e,
        )

        boosted_e_state, boosted_b_state = _boost_eb_towers(
            polarization_state,
            b_mode_state,
            beta=tilted_electron.beta,
            v_hat_e=tilted_electron.v_hat_e,
        )
        collision_e_frame_E = e_op.evaluate_tower(
            boosted_e_state,
            pi_2_e_frame,
            effective_gamma,
        )
        collision_e_frame_B = _b_mode_collision_tower(
            boosted_b_state,
            effective_gamma,
        )
        restored_E_state, restored_B_state = _boost_eb_towers(
            collision_e_frame_E,
            collision_e_frame_B,
            beta=-tilted_electron.beta,
            v_hat_e=tilted_electron.v_hat_e,
        )
        polarization_E = restored_E_state
        polarization_B = restored_B_state
    return ProjectedThomsonSource(
        temperature=temperature,
        polarization_E=polarization_E,
        polarization_B=polarization_B,
        effective_rate=rate,
        frame_metadata=context.frame_metadata,
    )


def _directional_exact_thomson_source(
    e_dir: np.ndarray,
    I_dir: np.ndarray,
    I0: float | np.ndarray,
    P_dir: np.ndarray,
    I2: float | np.ndarray,
    E2_pol: float | np.ndarray,
    opacity_data: Mapping[str, object],
) -> SourceTerms:
    if not isinstance(opacity_data, Mapping):
        raise ValueError("opacity_data must be a mapping")
    direction = np.asarray(e_dir, dtype=np.float64)
    if direction.shape != (3,):
        raise ValueError(f"e_dir must have shape (3,), got {direction.shape}")
    direction_norm = float(np.linalg.norm(direction))
    if direction_norm == 0.0:
        raise ValueError("e_dir must be non-zero")
    direction_hat = direction / direction_norm
    I_arr = np.asarray(I_dir, dtype=np.float64)
    P_arr = np.asarray(P_dir, dtype=np.float64)
    I0_arr, I2_arr, E2_arr = np.broadcast_arrays(
        np.asarray(I0, dtype=np.float64),
        np.asarray(I2, dtype=np.float64),
        np.asarray(E2_pol, dtype=np.float64),
    )
    if I_arr.shape != P_arr.shape:
        raise ValueError(f"I_dir and P_dir must share shape, got {I_arr.shape} and {P_arr.shape}")
    if I_arr.shape != I0_arr.shape:
        I0_arr = np.broadcast_to(I0_arr, I_arr.shape)
        I2_arr = np.broadcast_to(I2_arr, I_arr.shape)
        E2_arr = np.broadcast_to(E2_arr, I_arr.shape)
    convention = PhotonDirectionConvention(
        opacity_data.get("direction_convention", PhotonDirectionConvention.PROPAGATION)
    )
    gamma_e = float(opacity_data.get("gamma_e", 1.0))
    v_dot_direction = float(opacity_data.get("v_dot_direction", 0.0))
    rate = electron_frame_rate_factor(
        gamma_e=gamma_e,
        v_dot_direction=v_dot_direction,
        convention=convention,
    )
    base_opacity = float(opacity_data.get("Gamma_T", 0.0))
    if not np.isfinite(base_opacity) or base_opacity < 0.0:
        raise ValueError("opacity_data['Gamma_T'] must be non-negative finite")
    effective_opacity = base_opacity * rate.factor
    dI_dir = effective_opacity * ((I0_arr + I2_arr) - I_arr)
    dP_dir = effective_opacity * (E2_arr - P_arr)
    return SourceTerms(
        dI_dir=dI_dir,
        dP_dir=dP_dir,
        effective_opacity=effective_opacity,
        direction_convention=convention,
        metadata={
            "direction_norm": direction_norm,
            "direction_hat": direction_hat.tolist(),
            "scalar_monopole_input": float(np.mean(I0_arr)),
            "quadrupole_input_norm": float(np.linalg.norm(I2_arr)),
            "polarization_source_norm": float(np.linalg.norm(E2_arr)),
            "source_split": "scalar_monopole_vs_directional_tensor",
        },
    )


def exact_thomson_source(
    context: ElectronFrameThomsonContext | np.ndarray,
    *args,
    **kwargs,
) -> ExactThomsonSource | SourceTerms:
    """ver3 exact Thomson wrapper with explicit scalar/directional separation."""

    if isinstance(context, ElectronFrameThomsonContext):
        temperature_state = kwargs["temperature_state"]
        polarization_state = kwargs["polarization_state"]
        v_b_real_sph = kwargs["v_b_real_sph"]
        Gamma_T = kwargs["Gamma_T"]
        direction = kwargs.get("direction")
        tilted_electron = kwargs.get("tilted_electron")
        b_state = kwargs.get("b_state")
        projected = project_thomson_source(
            context,
            temperature_state=temperature_state,
            polarization_state=polarization_state,
            v_b_real_sph=v_b_real_sph,
            Gamma_T=Gamma_T,
            direction=direction,
            tilted_electron=tilted_electron,
            b_state=b_state,
        )
        scalar_monopole_input = float(temperature_state.tensors[0].components[0])
        directional_norm = 0.0
        for ell in range(1, temperature_state.L + 1):
            directional_norm += float(
                np.dot(
                    temperature_state.tensors[ell].components,
                    temperature_state.tensors[ell].components,
                )
            )
        polarization_quadrupole_norm = float(
            np.linalg.norm(polarization_state.E.tensors[2].components)
        )
        return ExactThomsonSource(
            projected=projected,
            scalar_monopole_input=scalar_monopole_input,
            directional_temperature_norm=float(np.sqrt(directional_norm)),
            polarization_quadrupole_norm=polarization_quadrupole_norm,
            effective_opacity=float(Gamma_T) * projected.effective_rate.factor,
        )

    if len(args) != 6:
        raise TypeError(
            "directional exact_thomson_source expects "
            "(e_dir, I_dir, I0, P_dir, I2, E2_pol, opacity_data)"
        )
    return _directional_exact_thomson_source(
        np.asarray(context, dtype=np.float64),
        args[0],
        args[1],
        args[2],
        args[3],
        args[4],
        args[5],
    )


def _angular_stokes_gate_bundle(
    source: AngularStokesThomsonSource,
    *,
    family: str,
    branch: str,
    backend: str,
    truncation: Mapping[str, object] | None,
) -> GateBundle:
    weights_sum = float(np.sum(source.weights))
    quadrature_normalization_ok = bool(
        abs(weights_sum - 4.0 * np.pi) <= 1.0e-10 * max(1.0, 4.0 * np.pi)
    )
    opacity_finite = bool(
        np.all(np.isfinite(source.effective_opacity))
        and np.all(source.effective_opacity >= 0.0)
    )
    basis_orthonormal = bool(
        np.max(np.abs(np.sum(source.directions * source.basis_u, axis=1))) <= 1.0e-10
        and np.max(np.abs(np.sum(source.directions * source.basis_v, axis=1))) <= 1.0e-10
        and np.max(np.abs(np.sum(source.basis_u * source.basis_v, axis=1))) <= 1.0e-10
    )
    tilted_rate = bool(
        np.ptp(source.effective_opacity) > 1.0e-14
        or (
            source.effective_opacity.size
            and abs(float(np.mean(source.effective_opacity)) - float(source.effective_opacity[0]))
            > 1.0e-14
        )
    )
    full_tilted_stokes_authority = source.operator_scope == "full_electron_frame_stokes"
    tilted_branch = str(branch) != "orthogonal"
    tilted_rate_contract_ok = (not tilted_branch) or tilted_rate
    exact_scope_supported = (not tilted_branch) or full_tilted_stokes_authority
    return make_gate_bundle(
        "exact_thomson_gate",
        family=family,
        branch=branch,
        backend=backend,
        truncation={} if truncation is None else dict(truncation),
        residual_summary={
            "scalar_monopole_input": float(source.scalar_monopole_input),
            "directional_temperature_norm": float(source.directional_temperature_norm),
            "polarization_norm": float(source.polarization_norm),
            "effective_opacity_min": float(np.min(source.effective_opacity)),
            "effective_opacity_max": float(np.max(source.effective_opacity)),
            "source_I_norm": float(np.linalg.norm(source.source_I)),
            "source_Q_norm": float(np.linalg.norm(source.source_Q)),
            "source_U_norm": float(np.linalg.norm(source.source_U)),
        },
        known_limit_checks={
            "isotropic_null_mode_required": True,
            "pure_quadrupole_response_required": True,
            "linearity_required": True,
            "full_tilted_stokes_authority": full_tilted_stokes_authority,
            "screen_basis_rotation_contract_declared": (
                source.basis_transport_contract
                == "explicit_screen_basis_spin2_rotation"
            ),
            "tilted_branch_requires_full_stokes_authority": not tilted_branch
            or full_tilted_stokes_authority,
            "tilted_branch_requires_directional_opacity": tilted_rate_contract_ok,
            "angular_quadrature_weights_normalized": quadrature_normalization_ok,
            "screen_basis_orthonormal": basis_orthonormal,
        },
        forbidden_shortcut_checks={
            "no_flrw_only_collision_shortcut": True,
            "electron_frame_owned": True,
            "no_boosted_pstf_wrapper_marketed_as_full_tilted_thomson": bool(
                exact_scope_supported
            ),
        },
        metadata={
            "source_split": source.source_split,
            "opacity_contract": source.opacity_contract,
            "operator_scope": source.operator_scope,
            "basis_transport_contract": source.basis_transport_contract,
            "tilted_rate_detected": tilted_rate,
            "angular_grid_size": int(source.directions.shape[0]),
            "weights_sum": weights_sum,
        },
        passed=bool(
            source.source_ready
            and opacity_finite
            and quadrature_normalization_ok
            and basis_orthonormal
            and exact_scope_supported
            and tilted_rate_contract_ok
        ),
        opened_claim="exact collision contract frozen",
    )


def exact_thomson_gate_bundle(
    source: ExactThomsonSource | AngularStokesThomsonSource,
    *,
    family: str = "unspecified",
    branch: str = "orthogonal",
    backend: str = "electron_frame_tilt_modulated",
    truncation: Mapping[str, object] | None = None,
) -> GateBundle:
    """Emit the machine-readable PR-06 exact-Thomson gate bundle."""

    if isinstance(source, AngularStokesThomsonSource):
        return _angular_stokes_gate_bundle(
            source,
            family=family,
            branch=branch,
            backend=backend,
            truncation=truncation,
        )

    tilted_rate = bool(
        abs(float(source.projected.effective_rate.factor) - 1.0) > 1.0e-14
        or abs(float(source.projected.effective_rate.gamma_e) - 1.0) > 1.0e-14
    )
    full_tilted_stokes_authority = (
        source.projected.operator_scope == "full_electron_frame_stokes"
    )
    tilted_branch = str(branch) != "orthogonal"
    exact_scope_supported = (not tilted_branch and not tilted_rate) or full_tilted_stokes_authority
    return make_gate_bundle(
        "exact_thomson_gate",
        family=family,
        branch=branch,
        backend=backend,
        truncation={} if truncation is None else dict(truncation),
        residual_summary={
            "scalar_monopole_input": float(source.scalar_monopole_input),
            "directional_temperature_norm": float(source.directional_temperature_norm),
            "polarization_quadrupole_norm": float(source.polarization_quadrupole_norm),
            "effective_opacity": float(source.effective_opacity),
        },
        known_limit_checks={
            "isotropic_null_mode_required": source.projected.isotropic_null_mode_required,
            "pure_quadrupole_response_required": source.projected.pure_quadrupole_response_required,
            "linearity_required": source.projected.linearity_required,
            "full_tilted_stokes_authority": full_tilted_stokes_authority,
            "tilted_branch_requires_full_stokes_authority": not tilted_branch
            or full_tilted_stokes_authority,
        },
        forbidden_shortcut_checks={
            "no_flrw_only_collision_shortcut": (
                source.projected.frame_metadata.no_flrw_only_collision_shortcut
            ),
            "electron_frame_owned": (
                source.projected.frame_metadata.collision_frame == "electron_frame"
            ),
            "no_boosted_pstf_wrapper_marketed_as_full_tilted_thomson": bool(
                exact_scope_supported
            ),
        },
        metadata={
            "source_split": source.source_split,
            "opacity_contract": source.opacity_contract,
            "operator_scope": source.projected.operator_scope,
            "tilted_rate_detected": tilted_rate,
        },
        passed=bool(
            np.isfinite(source.effective_opacity)
            and source.effective_opacity >= 0.0
            and exact_scope_supported
        ),
        opened_claim="exact collision contract frozen",
    )


def project_thomson_source_stub(
    context: ElectronFrameThomsonContext,
    **kwargs,
) -> ProjectedThomsonSource:
    """Compatibility alias kept while call sites migrate to `project_thomson_source`."""
    return project_thomson_source(context, **kwargs)
