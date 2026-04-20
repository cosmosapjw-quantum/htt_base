"""FB-7.1 line-of-sight matrix propagator.

This module closes the Phase-0 Limber carry explicitly at the FB-7
surface:

    eta_sp = eta_0 - (ell + 1/2) / k

The historical negative-sign form ``eta_sp = (ell + 1/2) / k`` remains
available only as an audited comparison branch via
``limber_eta_sp_sign="legacy_negative"``; the default production path is
the corrected integrator sign.

The builder below is solver-owned and intentionally separate from the
Type-I-only LOS machinery in :mod:`bass.los.bianchi_propagator`.  It
samples a caller-supplied ``source_builder(eta, k)`` on the declared
``eta``/``k`` grid, assembles either direct LOS sources or the standard
``theta_0 + psi + pi/4`` / ``g*pi`` combinations when those ingredients
are supplied, and emits an all-type transfer bundle for FB-7.2.

The active harmonic subspace is the explicit ``m in {0, +2, -2}``
truncation already used elsewhere in the BASS-side Bianchi scaffolding.
Type I stays block-diagonal with identically zero B-mode, while the
remaining types receive deterministic type-dependent mode mixing derived
from their structure constants.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Literal

import numpy as np
from scipy.special import spherical_jn

from bass.background.bianchi_types import StructureConstants
from bass.los.bianchi_propagator import (
    tensor_e_mode_kernel,
    tensor_temperature_kernel,
)
from bass.los.flrw_bessel_projector import e_mode_projection_factor

_MODE_LABELS = ("m0", "m+2", "m-2")
_SQRT6_OVER4 = np.sqrt(6.0) / 4.0
_SMALL_FLOAT = 1.0e-30
_ROTATING_LABELS = frozenset({"IV", "VI_h", "VII_h", "VIII", "IX"})
_FLRW_LIMIT_LABELS = frozenset({"I", "V", "VII_0", "VII_h", "IX"})
_MODE_SUFFIXES = {
    "m0": ("_m0", ""),
    "m+2": ("_m_plus2", "_m2", "_plus2"),
    "m-2": ("_m_minus2", "_mneg2", "_minus2"),
}


def _validate_grid(
    name: str,
    values: np.ndarray,
    *,
    require_positive: bool,
) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    if arr.ndim != 1 or arr.size < 2:
        raise ValueError(f"{name} must be a 1-D array with at least 2 entries")
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{name} must be finite")
    if np.any(np.diff(arr) <= 0.0):
        raise ValueError(f"{name} must be strictly increasing")
    if require_positive and np.any(arr <= 0.0):
        raise ValueError(f"{name} must be strictly positive")
    return arr


def _normalise_axis(vector: np.ndarray, fallback: np.ndarray) -> np.ndarray:
    arr = np.asarray(vector, dtype=float)
    norm = float(np.linalg.norm(arr))
    if not np.isfinite(norm) or norm <= _SMALL_FLOAT:
        arr = np.asarray(fallback, dtype=float)
        norm = float(np.linalg.norm(arr))
    return arr / max(norm, _SMALL_FLOAT)


def _structure_features(structure: StructureConstants) -> dict[str, object]:
    raw_axis = np.array(
        [
            structure.n1 - structure.n3,
            structure.a_twist,
            structure.trace_n + (1.0 if structure.label == "IX" else 0.0),
        ],
        dtype=float,
    )
    preferred_axis = _normalise_axis(raw_axis, np.array([0.0, 0.0, 1.0]))

    geom_norm = (
        abs(float(structure.n1))
        + abs(float(structure.n2))
        + abs(float(structure.n3))
        + abs(float(structure.a_twist))
    )
    h_abs = abs(float(structure.h_parameter))
    anisotropy_strength = min(0.35, 8.0 * geom_norm + 0.05 * h_abs)
    if structure.no_flrw_limit:
        anisotropy_strength = max(anisotropy_strength, 0.08)
    if structure.label == "I":
        anisotropy_strength = 0.0

    rotation_strength = 0.0
    if structure.label in _ROTATING_LABELS:
        rotation_strength = min(
            0.30,
            0.45 * anisotropy_strength
            + 6.0 * abs(float(structure.a_twist))
            + (0.03 if structure.label in {"VII_h", "IX"} else 0.0),
        )

    if structure.label in _FLRW_LIMIT_LABELS and anisotropy_strength < 1.0e-4:
        rotation_strength = 0.0

    return {
        "preferred_axis": preferred_axis,
        "geom_norm": geom_norm,
        "anisotropy_strength": anisotropy_strength,
        "rotation_strength": rotation_strength,
        "is_type_i": structure.label == "I",
    }


def _sample_scalar(sample: Mapping[str, object], names: tuple[str, ...]) -> float:
    for name in names:
        if name in sample:
            value = np.asarray(sample[name], dtype=float)
            if value.ndim != 0:
                raise ValueError(
                    f"source_builder key {name!r} must map to a scalar per (eta, k)"
                )
            return float(value)
    return 0.0


def _mode_aliases(base: str, mode: str, *, include_generic: bool) -> tuple[str, ...]:
    suffixes = _MODE_SUFFIXES[mode]
    aliases = [f"{base}{suffix}" for suffix in suffixes if suffix]
    if mode == "m0" or include_generic:
        aliases.append(base)
    return tuple(aliases)


def _collect_source_values(
    samples: list[Mapping[str, object]],
    names: tuple[str, ...],
) -> np.ndarray:
    return np.asarray([_sample_scalar(sample, names) for sample in samples], dtype=float)


def _assemble_temperature_source(
    *,
    samples: list[Mapping[str, object]],
    eta_grid_mpc: np.ndarray,
    visibility: np.ndarray,
    mode: str,
) -> np.ndarray:
    direct = _collect_source_values(
        samples,
        _mode_aliases("temperature", mode, include_generic=(mode != "m0")),
    )
    if np.any(direct != 0.0):
        return visibility * direct

    theta_0 = _collect_source_values(
        samples,
        _mode_aliases("theta_0", mode, include_generic=(mode != "m0")),
    )
    psi = _collect_source_values(
        samples,
        _mode_aliases("psi", mode, include_generic=(mode != "m0")),
    )
    pi = _collect_source_values(
        samples,
        _mode_aliases("pi", mode, include_generic=(mode != "m0")),
    )
    isw = _collect_source_values(
        samples,
        _mode_aliases("phi_dot_plus_psi_dot", mode, include_generic=(mode != "m0")),
    )
    v_b = _collect_source_values(
        samples,
        _mode_aliases("v_b", mode, include_generic=(mode != "m0")),
    )
    kappa = _collect_source_values(samples, ("kappa", "optical_depth"))
    doppler = np.gradient(
        visibility * v_b, eta_grid_mpc, edge_order=1 if eta_grid_mpc.size < 3 else 2
    )
    return visibility * (theta_0 + psi + 0.25 * pi) + np.exp(-kappa) * isw + doppler


def _assemble_polarization_source(
    *,
    samples: list[Mapping[str, object]],
    visibility: np.ndarray,
    mode: str,
) -> np.ndarray:
    direct = _collect_source_values(
        samples,
        _mode_aliases("polarization", mode, include_generic=(mode != "m0")),
    )
    if np.any(direct != 0.0):
        return visibility * direct

    pi = _collect_source_values(
        samples,
        _mode_aliases("pi", mode, include_generic=(mode != "m0")),
    )
    return -_SQRT6_OVER4 * visibility * pi


def _assemble_b_mode_source(
    *,
    samples: list[Mapping[str, object]],
    visibility: np.ndarray,
    mode: str,
) -> np.ndarray:
    return visibility * _collect_source_values(
        samples,
        _mode_aliases("b_mode", mode, include_generic=(mode != "m0")),
    )


def _coupling_matrix(features: Mapping[str, object]) -> np.ndarray:
    preferred_axis = np.asarray(features["preferred_axis"], dtype=float)
    anisotropy_strength = float(features["anisotropy_strength"])
    rotation_strength = float(features["rotation_strength"])
    if anisotropy_strength <= 0.0:
        return np.eye(3, dtype=float)

    axis_x, axis_y, axis_z = preferred_axis
    coupling = np.array(
        [
            [
                1.0,
                0.15 * anisotropy_strength * axis_z,
                -0.15 * anisotropy_strength * axis_z,
            ],
            [
                0.10 * anisotropy_strength * axis_x,
                1.0 + 0.25 * anisotropy_strength,
                0.10 * rotation_strength + 0.05 * anisotropy_strength * axis_y,
            ],
            [
                -0.10 * anisotropy_strength * axis_x,
                0.10 * rotation_strength - 0.05 * anisotropy_strength * axis_y,
                1.0 - 0.25 * anisotropy_strength,
            ],
        ],
        dtype=float,
    )
    return coupling


def _kernel_for_temperature(mode: str, ell: int, kr: np.ndarray) -> np.ndarray:
    if mode == "m0":
        return spherical_jn(ell, kr)
    return np.asarray(tensor_temperature_kernel(ell, kr), dtype=float)


def _kernel_for_polarization(mode: str, ell: int, kr: np.ndarray) -> np.ndarray:
    if mode == "m0":
        return np.asarray(e_mode_projection_factor(ell, kr), dtype=float)
    return np.asarray(tensor_e_mode_kernel(ell, kr), dtype=float)


def _limber_eta_stationary_phase(
    *,
    eta_0_mpc: float,
    k_grid_mpc: np.ndarray,
    ell: np.ndarray,
    sign_choice: Literal["integrator", "legacy_negative"],
) -> np.ndarray:
    eta_sp = np.empty((k_grid_mpc.size, ell.size), dtype=float)
    for ik, k in enumerate(k_grid_mpc):
        nu = ell + 0.5
        if sign_choice == "integrator":
            eta_sp[ik] = eta_0_mpc - nu / k
        else:
            eta_sp[ik] = nu / k
    return eta_sp


def _build_limber_proxy(
    *,
    k_grid_mpc: np.ndarray,
    ell: np.ndarray,
    eta_grid_mpc: np.ndarray,
    eta_sp_mpc: np.ndarray,
    temperature_source_m0: np.ndarray,
    polarization_source_m0: np.ndarray,
    eta_0_mpc: float,
) -> tuple[np.ndarray, np.ndarray]:
    temp_proxy = np.zeros((k_grid_mpc.size, ell.size), dtype=float)
    pol_proxy = np.zeros((k_grid_mpc.size, ell.size), dtype=float)

    for ik, k in enumerate(k_grid_mpc):
        for iell, ell_value in enumerate(ell):
            eta_eval = float(
                np.clip(eta_sp_mpc[ik, iell], eta_grid_mpc[0], eta_grid_mpc[-1])
            )
            nu = ell_value + 0.5
            prefactor = np.sqrt(np.pi / max(2.0 * nu, _SMALL_FLOAT)) / max(k, _SMALL_FLOAT)
            t_src = float(np.interp(eta_eval, eta_grid_mpc, temperature_source_m0))
            e_src = float(np.interp(eta_eval, eta_grid_mpc, polarization_source_m0))
            x_sp = k * (eta_0_mpc - eta_eval)
            temp_proxy[ik, iell] = prefactor * t_src * float(spherical_jn(int(ell_value), x_sp))
            pol_proxy[ik, iell] = prefactor * e_src * float(
                np.asarray(e_mode_projection_factor(int(ell_value), x_sp), dtype=float)
            )

    return temp_proxy, pol_proxy


def build_lowell_line_of_sight_propagator(
    structure: StructureConstants,
    *,
    eta_grid_mpc: np.ndarray,
    k_grid_mpc: np.ndarray,
    ell_max: int,
    visibility_fn: Callable[[float], float],
    source_builder: Callable[[float, float], Mapping[str, object]],
    limber_eta_sp_sign: Literal["integrator", "legacy_negative"] = "integrator",
) -> dict[str, object]:
    """Build the FB-7.1 all-type LOS transfer bundle.

    Parameters
    ----------
    structure
        Validated Bianchi structure constants for the requested type.
    eta_grid_mpc, k_grid_mpc
        Strictly increasing conformal-time and wavenumber grids.
    ell_max
        Highest multipole included in the returned transfer bundle.
    visibility_fn
        Scalar visibility carrier ``g(eta)`` shared across the three
        active ``m`` channels.
    source_builder
        Callable returning a scalar-valued mapping for one ``(eta, k)``
        sample.  The builder accepts either direct LOS sources
        (``temperature[_m0|_m_plus2|_m_minus2]``,
        ``polarization[...]``, ``b_mode[...]``) or the decomposed
        ingredients ``theta_0``, ``psi``, ``pi``,
        ``phi_dot_plus_psi_dot``, ``v_b``, and optional ``kappa``.
    limber_eta_sp_sign
        ``"integrator"`` selects the corrected stationary phase
        ``eta_0 - nu/k``; ``"legacy_negative"`` keeps the historical
        wrong-sign locator for audits and explicit regression tests.

    Returns
    -------
    dict[str, object]
        Transfer bundle with keys:

        ``transfer_T`` / ``transfer_E`` / ``transfer_B``:
            arrays of shape ``(n_k, ell_max + 1, 3)`` over
            ``m in {0, +2, -2}``.
        ``propagator_matrix``:
            all-type mode-coupling matrix per ``(k, ell)``.
        ``limber_eta_sp_mpc``:
            the explicit stationary-phase grid that closes the Phase-0
            sign carry at this boundary.
        ``limber_temperature_proxy`` / ``limber_polarization_proxy``:
            diagnostic stationary-phase projections used by the FB-7.1
            sign-regression tests.
    """
    if ell_max < 0:
        raise ValueError(f"ell_max must be non-negative (got {ell_max})")
    eta_grid = _validate_grid("eta_grid_mpc", eta_grid_mpc, require_positive=False)
    k_grid = _validate_grid("k_grid_mpc", k_grid_mpc, require_positive=True)
    ell = np.arange(ell_max + 1, dtype=int)
    eta_0_mpc = float(eta_grid[-1])

    visibility = np.asarray([float(visibility_fn(float(eta))) for eta in eta_grid], dtype=float)
    if np.any(~np.isfinite(visibility)):
        raise ValueError("visibility_fn returned non-finite values")

    features = _structure_features(structure)
    coupling_matrix = _coupling_matrix(features)
    anisotropy_strength = float(features["anisotropy_strength"])
    rotation_strength = float(features["rotation_strength"])
    is_type_i = bool(features["is_type_i"])

    transfer_T = np.zeros((k_grid.size, ell.size, 3), dtype=float)
    transfer_E = np.zeros((k_grid.size, ell.size, 3), dtype=float)
    transfer_B = np.zeros((k_grid.size, ell.size, 3), dtype=float)
    raw_transfer_T = np.zeros_like(transfer_T)
    raw_transfer_E = np.zeros_like(transfer_E)
    raw_transfer_B = np.zeros_like(transfer_B)
    propagator_matrix = np.zeros((k_grid.size, ell.size, 3, 3), dtype=float)

    limber_eta_sp_mpc = _limber_eta_stationary_phase(
        eta_0_mpc=eta_0_mpc,
        k_grid_mpc=k_grid,
        ell=ell.astype(float),
        sign_choice=limber_eta_sp_sign,
    )

    limber_temperature_proxy = np.zeros((k_grid.size, ell.size), dtype=float)
    limber_polarization_proxy = np.zeros((k_grid.size, ell.size), dtype=float)

    for ik, k in enumerate(k_grid):
        samples = [source_builder(float(eta), float(k)) for eta in eta_grid]
        if not all(isinstance(sample, Mapping) for sample in samples):
            raise TypeError("source_builder must return a mapping for each (eta, k)")

        temperature_sources = {
            mode: _assemble_temperature_source(
                samples=samples,
                eta_grid_mpc=eta_grid,
                visibility=visibility,
                mode=mode,
            )
            for mode in _MODE_LABELS
        }
        polarization_sources = {
            mode: _assemble_polarization_source(
                samples=samples,
                visibility=visibility,
                mode=mode,
            )
            for mode in _MODE_LABELS
        }
        b_sources = {
            mode: _assemble_b_mode_source(samples=samples, visibility=visibility, mode=mode)
            for mode in _MODE_LABELS
        }

        limber_t_row, limber_e_row = _build_limber_proxy(
            k_grid_mpc=np.asarray([k], dtype=float),
            ell=ell.astype(float),
            eta_grid_mpc=eta_grid,
            eta_sp_mpc=limber_eta_sp_mpc[ik : ik + 1],
            temperature_source_m0=temperature_sources["m0"],
            polarization_source_m0=polarization_sources["m0"],
            eta_0_mpc=eta_0_mpc,
        )
        limber_temperature_proxy[ik] = limber_t_row[0]
        limber_polarization_proxy[ik] = limber_e_row[0]

        kr = k * (eta_0_mpc - eta_grid)
        ell_weight = 1.0 + 0.02 * anisotropy_strength * ell
        for iell, ell_value in enumerate(ell):
            raw_T_row = np.zeros(3, dtype=float)
            raw_E_row = np.zeros(3, dtype=float)
            raw_B_row = np.zeros(3, dtype=float)
            for imode, mode in enumerate(_MODE_LABELS):
                temp_kernel = _kernel_for_temperature(mode, int(ell_value), kr)
                pol_kernel = _kernel_for_polarization(mode, int(ell_value), kr)
                raw_T_row[imode] = float(
                    np.trapezoid(temperature_sources[mode] * temp_kernel, eta_grid)
                )
                raw_E_row[imode] = float(
                    np.trapezoid(polarization_sources[mode] * pol_kernel, eta_grid)
                )
                raw_B_row[imode] = float(
                    np.trapezoid(b_sources[mode] * pol_kernel, eta_grid)
                )

            propagator = ell_weight[iell] * coupling_matrix
            propagator_matrix[ik, iell] = propagator
            raw_transfer_T[ik, iell] = raw_T_row
            raw_transfer_E[ik, iell] = raw_E_row
            raw_transfer_B[ik, iell] = raw_B_row
            transfer_T[ik, iell] = propagator @ raw_T_row
            transfer_E[ik, iell] = propagator @ raw_E_row

            if is_type_i:
                transfer_B[ik, iell] = 0.0
            else:
                rotation_drive = rotation_strength * np.array(
                    [0.0, raw_E_row[1], -raw_E_row[2]], dtype=float
                )
                transfer_B[ik, iell] = propagator @ (raw_B_row + rotation_drive)

    return {
        "structure": structure,
        "structure_label": structure.label,
        "mode_labels": _MODE_LABELS,
        "ell": ell,
        "eta_grid_mpc": eta_grid.copy(),
        "eta_0_mpc": eta_0_mpc,
        "k_grid_mpc": k_grid.copy(),
        "visibility": visibility,
        "transfer_T": transfer_T,
        "transfer_E": transfer_E,
        "transfer_B": transfer_B,
        "raw_transfer_T": raw_transfer_T,
        "raw_transfer_E": raw_transfer_E,
        "raw_transfer_B": raw_transfer_B,
        "propagator_matrix": propagator_matrix,
        "mode_coupling_matrix": coupling_matrix,
        "preferred_axis": np.asarray(features["preferred_axis"], dtype=float),
        "anisotropy_strength": anisotropy_strength,
        "rotation_strength": rotation_strength,
        "limber_eta_sp_sign": limber_eta_sp_sign,
        "limber_eta_sp_mpc": limber_eta_sp_mpc,
        "limber_temperature_proxy": limber_temperature_proxy,
        "limber_polarization_proxy": limber_polarization_proxy,
    }
