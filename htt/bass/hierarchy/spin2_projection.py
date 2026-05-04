"""Spin-2 harmonic projection for angular Stokes Q/U samples.

This module is the non-scalar polarization projection primitive needed by
the tilted full-Stokes Thomson path.  It intentionally lives beside the
older PSTF scalar angular projector instead of replacing it wholesale:
callers can validate the spin-2 transform before promoting it into a
runtime RHS.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from math import factorial, pi, sqrt
from typing import TYPE_CHECKING, Any, Mapping

import numpy as np

from bass.hierarchy.pstf_tensor import (
    PSTFHierarchyState,
    PSTFTensor,
)

if TYPE_CHECKING:
    from bass.collision.polarization import PolarizationHierarchyState

__all__ = [
    "Spin2ProjectionKernel",
    "Spin2ProjectionMetadata",
    "Spin2ProjectionResult",
    "build_spin2_projection_kernel",
    "spherical_screen_basis",
    "spin_weighted_spherical_harmonic",
    "project_spin2_qu_to_eb",
    "project_spin2_qu_to_eb_with_kernel",
    "reconstruct_spin2_qu_from_eb",
    "reconstruct_spin2_qu_from_eb_with_kernel",
]


@dataclass(frozen=True)
class Spin2ProjectionKernel:
    """Precomputed spin-2 harmonic matrices for one angular grid."""

    L: int
    directions: np.ndarray
    weights: np.ndarray
    basis_u: np.ndarray
    basis_v: np.ndarray
    spherical_u: np.ndarray
    spherical_v: np.ndarray
    theta: np.ndarray
    phi: np.ndarray
    y_plus2_by_ell: tuple[np.ndarray | None, ...]
    y_minus2_by_ell: tuple[np.ndarray | None, ...]
    metadata: "Spin2ProjectionMetadata"

    def __post_init__(self) -> None:
        if self.L < 2:
            raise ValueError(f"spin-2 kernel requires L >= 2, got {self.L}")
        directions = _validate_directions(self.directions)
        weights = _validate_weights(self.weights, directions.shape[0])
        basis_u, basis_v = _validate_screen_basis(directions, self.basis_u, self.basis_v)
        spherical_u, spherical_v = _validate_screen_basis(
            directions,
            self.spherical_u,
            self.spherical_v,
        )
        theta = np.asarray(self.theta, dtype=np.float64)
        phi = np.asarray(self.phi, dtype=np.float64)
        if theta.shape != (directions.shape[0],) or phi.shape != (directions.shape[0],):
            raise ValueError("kernel theta/phi must both have shape (N,)")
        if len(self.y_plus2_by_ell) != self.L + 1:
            raise ValueError("y_plus2_by_ell length must be L+1")
        if len(self.y_minus2_by_ell) != self.L + 1:
            raise ValueError("y_minus2_by_ell length must be L+1")
        for ell in range(2, self.L + 1):
            expected = (2 * ell + 1, directions.shape[0])
            for name, table in (
                ("y_plus2_by_ell", self.y_plus2_by_ell[ell]),
                ("y_minus2_by_ell", self.y_minus2_by_ell[ell]),
            ):
                if table is None:
                    raise ValueError(f"{name}[{ell}] must not be None")
                arr = np.asarray(table, dtype=np.complex128)
                if arr.shape != expected:
                    raise ValueError(f"{name}[{ell}] must have shape {expected}")
        if self.metadata.L != self.L:
            raise ValueError("kernel metadata L must match kernel L")
        object.__setattr__(self, "directions", directions)
        object.__setattr__(self, "weights", weights)
        object.__setattr__(self, "basis_u", basis_u)
        object.__setattr__(self, "basis_v", basis_v)
        object.__setattr__(self, "spherical_u", spherical_u)
        object.__setattr__(self, "spherical_v", spherical_v)
        object.__setattr__(self, "theta", theta)
        object.__setattr__(self, "phi", phi)


@dataclass(frozen=True)
class Spin2ProjectionMetadata:
    """Explicit convention record for a spin-2 Q/U -> E/B projection."""

    L: int
    basis_contract: str = "spherical_screen_basis_spin2_harmonic"
    coefficient_convention: str = "goldberg_spin_weighted_y_bass_real_alm"
    eb_convention: str = "aE=-(a_plus2+a_minus2)/2,aB=i(a_plus2-a_minus2)/2"
    quadrature_contract: str = "spin2_orthonormality_checked"
    low_rank_contract: str = "spin2_modes_start_at_ell2"

    def __post_init__(self) -> None:
        if self.L < 2:
            raise ValueError(f"spin-2 projection requires L >= 2, got {self.L}")


@dataclass(frozen=True)
class Spin2ProjectionResult:
    """Projected E/B towers from angular Stokes Q/U samples."""

    E: Any
    B: PSTFHierarchyState
    metadata: Spin2ProjectionMetadata = field(
        default_factory=lambda: Spin2ProjectionMetadata(L=2)
    )

    def __post_init__(self) -> None:
        if self.E.L != self.B.L:
            raise ValueError("spin-2 E and B towers must share L")
        if self.metadata.L != self.E.L:
            raise ValueError(
                f"metadata L={self.metadata.L} must match tower L={self.E.L}"
            )


def _validate_directions(directions: object, *, atol: float = 1.0e-12) -> np.ndarray:
    dirs = np.asarray(directions, dtype=np.float64)
    if dirs.ndim != 2 or dirs.shape[1] != 3:
        raise ValueError(f"directions must have shape (N,3), got {dirs.shape}")
    if not np.all(np.isfinite(dirs)):
        raise ValueError("directions must be finite")
    norms = np.linalg.norm(dirs, axis=1)
    if np.max(np.abs(norms - 1.0)) > atol:
        raise ValueError("directions must lie on the unit sphere")
    return dirs


def _validate_weights(weights: object, count: int, *, atol: float = 1.0e-12) -> np.ndarray:
    quad_weights = np.asarray(weights, dtype=np.float64)
    if quad_weights.shape != (count,):
        raise ValueError(f"weights must have shape ({count},), got {quad_weights.shape}")
    if not np.all(np.isfinite(quad_weights)):
        raise ValueError("weights must be finite")
    if np.any(quad_weights <= 0.0):
        raise ValueError("weights must be strictly positive")
    if abs(float(np.sum(quad_weights)) - 4.0 * pi) > atol:
        raise ValueError("weights must sum to 4*pi for spin-2 projection")
    return quad_weights


def _validate_screen_basis(
    directions: np.ndarray,
    basis_u: object,
    basis_v: object,
    *,
    atol: float = 1.0e-10,
) -> tuple[np.ndarray, np.ndarray]:
    u = np.asarray(basis_u, dtype=np.float64)
    v = np.asarray(basis_v, dtype=np.float64)
    if u.shape != directions.shape or v.shape != directions.shape:
        raise ValueError("screen basis arrays must both have shape (N,3)")
    for name, arr in (("basis_u", u), ("basis_v", v)):
        if not np.all(np.isfinite(arr)):
            raise ValueError(f"{name} must be finite")
        norms = np.linalg.norm(arr, axis=1)
        if np.max(np.abs(norms - 1.0)) > atol:
            raise ValueError(f"{name} must be unit normalized")
    if np.max(np.abs(np.sum(directions * u, axis=1))) > atol:
        raise ValueError("basis_u must be transverse to directions")
    if np.max(np.abs(np.sum(directions * v, axis=1))) > atol:
        raise ValueError("basis_v must be transverse to directions")
    if np.max(np.abs(np.sum(u * v, axis=1))) > atol:
        raise ValueError("basis_u and basis_v must be orthogonal")
    handedness = np.cross(directions, u)
    if np.max(np.abs(handedness - v)) > 1.0e-8:
        raise ValueError("screen basis must satisfy basis_v = direction x basis_u")
    return u, v


def _rotate_stokes_one(
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


def _rotate_stokes_samples(
    Q: np.ndarray,
    U: np.ndarray,
    old_u: np.ndarray,
    old_v: np.ndarray,
    new_u: np.ndarray,
    new_v: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    q_out = np.empty_like(Q, dtype=np.float64)
    u_out = np.empty_like(U, dtype=np.float64)
    for idx in range(Q.shape[0]):
        q_out[idx], u_out[idx] = _rotate_stokes_one(
            float(Q[idx]),
            float(U[idx]),
            old_u[idx],
            old_v[idx],
            new_u[idx],
            new_v[idx],
        )
    return q_out, u_out


def _theta_phi_from_directions(directions: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    z = np.clip(directions[:, 2], -1.0, 1.0)
    theta = np.arccos(z)
    phi = np.mod(np.arctan2(directions[:, 1], directions[:, 0]), 2.0 * pi)
    return theta, phi


def spherical_screen_basis(directions: object) -> tuple[np.ndarray, np.ndarray]:
    """Return the canonical ``(theta_hat, phi_hat)`` screen basis.

    The basis is right-handed with ``phi_hat = direction x theta_hat``.
    At the coordinate poles the azimuth is conventionally fixed to
    ``phi=0``; tensor-product Gauss-Legendre rules used by the solver do
    not place samples exactly on those poles.
    """

    dirs = _validate_directions(directions)
    rho = np.linalg.norm(dirs[:, :2], axis=1)
    theta_hat = np.empty_like(dirs)
    phi_hat = np.empty_like(dirs)
    regular = rho > 1.0e-14

    theta_hat[regular, 0] = dirs[regular, 2] * dirs[regular, 0] / rho[regular]
    theta_hat[regular, 1] = dirs[regular, 2] * dirs[regular, 1] / rho[regular]
    theta_hat[regular, 2] = -rho[regular]
    phi_hat[regular, 0] = -dirs[regular, 1] / rho[regular]
    phi_hat[regular, 1] = dirs[regular, 0] / rho[regular]
    phi_hat[regular, 2] = 0.0

    if np.any(~regular):
        pole_sign = np.where(dirs[~regular, 2] >= 0.0, 1.0, -1.0)
        theta_hat[~regular] = np.column_stack(
            [pole_sign, np.zeros_like(pole_sign), np.zeros_like(pole_sign)]
        )
        phi_hat[~regular] = np.array([0.0, 1.0, 0.0], dtype=np.float64)

    return _validate_screen_basis(dirs, theta_hat, phi_hat)


def _wigner_small_d(ell: int, m: int, mp: int, theta: np.ndarray) -> np.ndarray:
    prefactor = sqrt(
        factorial(ell + m)
        * factorial(ell - m)
        * factorial(ell + mp)
        * factorial(ell - mp)
    )
    cos_half = np.cos(0.5 * theta)
    sin_half = np.sin(0.5 * theta)
    values = np.zeros_like(theta, dtype=np.float64)
    k_min = max(0, m - mp)
    k_max = min(ell + m, ell - mp)
    for k in range(k_min, k_max + 1):
        denominator = (
            factorial(ell + m - k)
            * factorial(k)
            * factorial(mp - m + k)
            * factorial(ell - mp - k)
        )
        sign = (-1.0) ** (k - m + mp)
        values = values + (
            sign
            * prefactor
            / float(denominator)
            * cos_half ** (2 * ell + m - mp - 2 * k)
            * sin_half ** (mp - m + 2 * k)
        )
    return values


def spin_weighted_spherical_harmonic(
    ell: int,
    m: int,
    spin: int,
    theta: object,
    phi: object,
) -> np.ndarray:
    """Evaluate Goldberg spin-weighted harmonics ``_sY_lm``.

    The convention is
    ``_sY_lm = (-1)^s sqrt((2l+1)/(4*pi)) d^l_{m,-s}(theta) exp(i m phi)``.
    The projection only needs ``s = +/-2`` but the formula is valid for
    any integer ``|s| <= ell``.
    """

    if ell < 0:
        raise ValueError("ell must be non-negative")
    if abs(m) > ell:
        raise ValueError("|m| must be <= ell")
    if abs(spin) > ell:
        theta_arr = np.asarray(theta, dtype=np.float64)
        return np.zeros_like(theta_arr, dtype=np.complex128)
    theta_arr = np.asarray(theta, dtype=np.float64)
    phi_arr = np.asarray(phi, dtype=np.float64)
    if theta_arr.shape != phi_arr.shape:
        raise ValueError("theta and phi must share shape")
    if not np.all(np.isfinite(theta_arr)) or not np.all(np.isfinite(phi_arr)):
        raise ValueError("theta and phi must be finite")
    norm = ((-1.0) ** spin) * sqrt(float(2 * ell + 1) / (4.0 * pi))
    return norm * _wigner_small_d(ell, m, -spin, theta_arr) * np.exp(1j * m * phi_arr)


def _validate_spin2_quadrature(
    theta: np.ndarray,
    phi: np.ndarray,
    weights: np.ndarray,
    L: int,
    *,
    atol: float,
) -> None:
    for spin in (-2, 2):
        modes: list[np.ndarray] = []
        labels: list[tuple[int, int]] = []
        for ell in range(2, L + 1):
            for m in range(-ell, ell + 1):
                modes.append(spin_weighted_spherical_harmonic(ell, m, spin, theta, phi))
                labels.append((ell, m))
        basis = np.stack(modes, axis=1)
        gram = basis.conj().T @ (weights[:, None] * basis)
        if not np.allclose(gram, np.eye(len(labels)), rtol=0.0, atol=atol):
            err = float(np.max(np.abs(gram - np.eye(len(labels)))))
            raise ValueError(
                "discrete quadrature does not preserve spin-2 harmonic "
                f"orthonormality for spin={spin}; max error={err:.3e}"
            )


def _spin2_harmonic_tables(
    theta: np.ndarray,
    phi: np.ndarray,
    L: int,
) -> tuple[tuple[np.ndarray | None, ...], tuple[np.ndarray | None, ...]]:
    plus_tables: list[np.ndarray | None] = [None, None]
    minus_tables: list[np.ndarray | None] = [None, None]
    for ell in range(2, L + 1):
        plus_rows = []
        minus_rows = []
        for m in range(-ell, ell + 1):
            plus_rows.append(spin_weighted_spherical_harmonic(ell, m, 2, theta, phi))
            minus_rows.append(spin_weighted_spherical_harmonic(ell, m, -2, theta, phi))
        plus_tables.append(np.stack(plus_rows, axis=0))
        minus_tables.append(np.stack(minus_rows, axis=0))
    return tuple(plus_tables), tuple(minus_tables)


def build_spin2_projection_kernel(
    directions: object,
    weights: object,
    *,
    L: int,
    basis_u: object | None = None,
    basis_v: object | None = None,
    quadrature_atol: float = 1.0e-10,
    metadata: Spin2ProjectionMetadata | None = None,
) -> Spin2ProjectionKernel:
    """Build a reusable spin-2 projection kernel for one angular grid."""

    if L < 2:
        raise ValueError(f"spin-2 projection requires L >= 2, got {L}")
    dirs = _validate_directions(directions)
    quad_weights = _validate_weights(weights, dirs.shape[0])
    spherical_u, spherical_v = spherical_screen_basis(dirs)
    if basis_u is None and basis_v is None:
        input_u, input_v = spherical_u, spherical_v
    elif basis_u is None or basis_v is None:
        raise ValueError("basis_u and basis_v must be supplied together")
    else:
        input_u, input_v = _validate_screen_basis(dirs, basis_u, basis_v)
    theta, phi = _theta_phi_from_directions(dirs)
    _validate_spin2_quadrature(
        theta,
        phi,
        quad_weights,
        L,
        atol=quadrature_atol,
    )
    y_plus, y_minus = _spin2_harmonic_tables(theta, phi, L)
    if metadata is None:
        metadata = Spin2ProjectionMetadata(L=L)
    return Spin2ProjectionKernel(
        L=L,
        directions=dirs,
        weights=quad_weights,
        basis_u=input_u,
        basis_v=input_v,
        spherical_u=spherical_u,
        spherical_v=spherical_v,
        theta=theta,
        phi=phi,
        y_plus2_by_ell=y_plus,
        y_minus2_by_ell=y_minus,
        metadata=metadata,
    )


def _bass_real_tower_to_complex_modes(
    tower: PSTFHierarchyState,
    ell: int,
) -> dict[int, complex]:
    arr = np.asarray(tower.tensors[ell].components, dtype=np.float64)
    out: dict[int, complex] = {0: complex(arr[ell])}
    sqrt2 = sqrt(2.0)
    for m in range(1, ell + 1):
        sign = (-1.0) ** m
        out[m] = complex((sign / sqrt2) * (arr[ell + m] - 1j * arr[ell - m]))
        out[-m] = ((-1.0) ** m) * np.conj(out[m])
    return out


def _complex_modes_to_bass_real_tensor(
    ell: int,
    modes: Mapping[int, complex],
    *,
    imaginary_atol: float,
) -> PSTFTensor:
    arr = np.zeros(2 * ell + 1, dtype=np.float64)
    m0 = complex(modes[0])
    if abs(m0.imag) > imaginary_atol:
        raise ValueError(f"ell={ell}, m=0 coefficient has non-negligible imaginary part")
    arr[ell] = m0.real
    sqrt2 = sqrt(2.0)
    for m in range(1, ell + 1):
        positive = complex(modes[m])
        negative = complex(modes[-m])
        reality_error = negative - ((-1.0) ** m) * np.conj(positive)
        if abs(reality_error) > imaginary_atol:
            raise ValueError(
                f"ell={ell}, m={m} violates real-field harmonic reality by "
                f"{abs(reality_error):.3e}"
            )
        sign = (-1.0) ** m
        arr[ell + m] = sqrt2 * sign * positive.real
        arr[ell - m] = -sqrt2 * sign * positive.imag
    return PSTFTensor(ell=ell, components=arr)


def _coerce_qu_channel(name: str, values: object, count: int) -> np.ndarray:
    arr = np.asarray(values, dtype=np.float64)
    if arr.shape != (count,):
        raise ValueError(f"{name} must have shape ({count},), got {arr.shape}")
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{name} must be finite")
    return arr


def project_spin2_qu_to_eb(
    Q: object,
    U: object,
    directions: object,
    weights: object,
    *,
    L: int,
    basis_u: object | None = None,
    basis_v: object | None = None,
    quadrature_atol: float = 1.0e-10,
    imaginary_atol: float = 1.0e-9,
    metadata: Spin2ProjectionMetadata | None = None,
) -> Spin2ProjectionResult:
    """Project angular Stokes Q/U samples onto spin-2 E/B towers."""

    kernel = build_spin2_projection_kernel(
        directions,
        weights,
        L=L,
        basis_u=basis_u,
        basis_v=basis_v,
        quadrature_atol=quadrature_atol,
        metadata=metadata,
    )
    return project_spin2_qu_to_eb_with_kernel(
        Q,
        U,
        kernel,
        imaginary_atol=imaginary_atol,
    )


def project_spin2_qu_to_eb_with_kernel(
    Q: object,
    U: object,
    kernel: Spin2ProjectionKernel,
    *,
    imaginary_atol: float = 1.0e-9,
) -> Spin2ProjectionResult:
    """Project angular Q/U samples using a precomputed spin-2 kernel."""

    dirs = kernel.directions
    q_samples = _coerce_qu_channel("Q", Q, dirs.shape[0])
    u_samples = _coerce_qu_channel("U", U, dirs.shape[0])
    if not (
        np.array_equal(kernel.basis_u, kernel.spherical_u)
        and np.array_equal(kernel.basis_v, kernel.spherical_v)
    ):
        q_samples, u_samples = _rotate_stokes_samples(
            q_samples,
            u_samples,
            kernel.basis_u,
            kernel.basis_v,
            kernel.spherical_u,
            kernel.spherical_v,
        )

    p_plus = q_samples + 1j * u_samples
    p_minus = q_samples - 1j * u_samples
    e_tensors = [PSTFTensor(ell=0, components=np.zeros(1))]
    e_tensors.append(PSTFTensor(ell=1, components=np.zeros(3)))
    b_tensors = [PSTFTensor(ell=0, components=np.zeros(1))]
    b_tensors.append(PSTFTensor(ell=1, components=np.zeros(3)))

    for ell in range(2, kernel.L + 1):
        e_modes: dict[int, complex] = {}
        b_modes: dict[int, complex] = {}
        y_plus_table = kernel.y_plus2_by_ell[ell]
        y_minus_table = kernel.y_minus2_by_ell[ell]
        assert y_plus_table is not None
        assert y_minus_table is not None
        for m in range(-ell, ell + 1):
            y_plus = y_plus_table[m + ell]
            y_minus = y_minus_table[m + ell]
            a_plus = np.sum(kernel.weights * p_plus * np.conj(y_plus))
            a_minus = np.sum(kernel.weights * p_minus * np.conj(y_minus))
            e_modes[m] = complex(-0.5 * (a_plus + a_minus))
            b_modes[m] = complex(0.5j * (a_plus - a_minus))
        e_tensors.append(
            _complex_modes_to_bass_real_tensor(
                ell,
                e_modes,
                imaginary_atol=imaginary_atol,
            )
        )
        b_tensors.append(
            _complex_modes_to_bass_real_tensor(
                ell,
                b_modes,
                imaginary_atol=imaginary_atol,
            )
        )

    e_tower = PSTFHierarchyState(L=kernel.L, tensors=e_tensors)
    b_tower = PSTFHierarchyState(L=kernel.L, tensors=b_tensors)
    return Spin2ProjectionResult(
        E=_wrap_polarization_tower(e_tower),
        B=b_tower,
        metadata=kernel.metadata,
    )


def _wrap_polarization_tower(tower: PSTFHierarchyState) -> "PolarizationHierarchyState":
    from bass.collision.polarization import PolarizationHierarchyState

    return PolarizationHierarchyState(E=tower)


def _coerce_e_tower(E: object) -> PSTFHierarchyState:
    if isinstance(E, PSTFHierarchyState):
        if E.L < 2:
            raise ValueError("E tower requires L >= 2")
        return E
    wrapped = getattr(E, "E", None)
    if isinstance(wrapped, PSTFHierarchyState):
        if wrapped.L < 2:
            raise ValueError("E tower requires L >= 2")
        return wrapped
    raise TypeError(
        "E must be PolarizationHierarchyState-like or PSTFHierarchyState, "
        f"got {type(E).__name__}"
    )


def reconstruct_spin2_qu_from_eb(
    E: "PolarizationHierarchyState | PSTFHierarchyState",
    B: PSTFHierarchyState,
    directions: object,
    *,
    basis_u: object | None = None,
    basis_v: object | None = None,
    imaginary_atol: float = 1.0e-9,
) -> dict[str, np.ndarray]:
    """Reconstruct angular Stokes Q/U samples from spin-2 E/B towers."""

    e_tower = _coerce_e_tower(E)
    dirs = _validate_directions(directions)
    reconstruction_weights = np.full(
        dirs.shape[0],
        4.0 * pi / float(dirs.shape[0]),
        dtype=np.float64,
    )
    kernel = build_spin2_projection_kernel(
        dirs,
        reconstruction_weights,
        L=e_tower.L,
        basis_u=basis_u,
        basis_v=basis_v,
        quadrature_atol=1.0e300,
    )
    return reconstruct_spin2_qu_from_eb_with_kernel(
        E,
        B,
        kernel,
        imaginary_atol=imaginary_atol,
    )


def reconstruct_spin2_qu_from_eb_with_kernel(
    E: "PolarizationHierarchyState | PSTFHierarchyState",
    B: PSTFHierarchyState,
    kernel: Spin2ProjectionKernel,
    *,
    imaginary_atol: float = 1.0e-9,
) -> dict[str, np.ndarray]:
    """Reconstruct angular Q/U samples using a precomputed spin-2 kernel."""

    e_tower = _coerce_e_tower(E)
    if e_tower.L != B.L:
        raise ValueError("E and B towers must share L")
    if e_tower.L != kernel.L:
        raise ValueError(f"E/B L={e_tower.L} must match kernel L={kernel.L}")
    p_plus = np.zeros(kernel.directions.shape[0], dtype=np.complex128)
    p_minus = np.zeros(kernel.directions.shape[0], dtype=np.complex128)
    for ell in range(2, e_tower.L + 1):
        e_modes = _bass_real_tower_to_complex_modes(e_tower, ell)
        b_modes = _bass_real_tower_to_complex_modes(B, ell)
        y_plus_table = kernel.y_plus2_by_ell[ell]
        y_minus_table = kernel.y_minus2_by_ell[ell]
        assert y_plus_table is not None
        assert y_minus_table is not None
        for m in range(-ell, ell + 1):
            y_plus = y_plus_table[m + ell]
            y_minus = y_minus_table[m + ell]
            p_plus = p_plus - (e_modes[m] + 1j * b_modes[m]) * y_plus
            p_minus = p_minus - (e_modes[m] - 1j * b_modes[m]) * y_minus

    q_complex = 0.5 * (p_plus + p_minus)
    u_complex = (p_plus - p_minus) / (2.0j)
    if (
        float(np.max(np.abs(q_complex.imag))) > imaginary_atol
        or float(np.max(np.abs(u_complex.imag))) > imaginary_atol
    ):
        raise ValueError("reconstructed Q/U carry non-negligible imaginary residuals")
    q_samples = q_complex.real
    u_samples = u_complex.real
    if not (
        np.array_equal(kernel.basis_u, kernel.spherical_u)
        and np.array_equal(kernel.basis_v, kernel.spherical_v)
    ):
        q_samples, u_samples = _rotate_stokes_samples(
            q_samples,
            u_samples,
            kernel.spherical_u,
            kernel.spherical_v,
            kernel.basis_u,
            kernel.basis_v,
        )
    return {"Q": q_samples, "U": u_samples}
