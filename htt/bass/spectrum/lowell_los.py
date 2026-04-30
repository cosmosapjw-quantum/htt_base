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


def _type_vii0_helical_pitch(structure: StructureConstants) -> float:
    """Return the real helical pitch for the Type VII_0 Euclidean branch."""

    if structure.label != "VII_0":
        return 0.0
    if (not structure.is_class_a) or abs(float(structure.n2)) > 1.0e-14:
        return 0.0
    product = float(structure.n1) * float(structure.n3)
    if product <= 0.0:
        return 0.0
    return float(np.sqrt(product))


def _rotate_tensor_pair(
    plus: np.ndarray,
    minus: np.ndarray,
    phase: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Rotate the real ``m=+2/-2`` pair by the supplied helical phase."""

    c = np.cos(phase)
    s = np.sin(phase)
    return c * plus - s * minus, s * plus + c * minus


def _rotate_and_attenuate_tensor_pair(
    plus: np.ndarray,
    minus: np.ndarray,
    phase: np.ndarray,
    attenuation: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    rotated_plus, rotated_minus = _rotate_tensor_pair(plus, minus, phase)
    return attenuation * rotated_plus, attenuation * rotated_minus


def _type_ii_nilpotent_scale(structure: StructureConstants) -> float:
    """Return the central nilpotent scale for the Type II branch."""

    if structure.label != "II":
        return 0.0
    if (not structure.is_class_a) or abs(float(structure.n2)) > 1.0e-14 or abs(float(structure.n3)) > 1.0e-14:
        return 0.0
    scale = abs(float(structure.n1))
    if scale <= _SMALL_FLOAT:
        return 0.0
    return scale


def _nilpotent_profile(
    structure: StructureConstants,
    *,
    eta_grid_mpc: np.ndarray,
    eta_0_mpc: float,
) -> tuple[np.ndarray, np.ndarray, float, str]:
    scale = _type_ii_nilpotent_scale(structure)
    eta = np.asarray(eta_grid_mpc, dtype=float)
    if scale <= _SMALL_FLOAT:
        zeros = np.zeros_like(eta, dtype=float)
        return zeros, zeros, 0.0, "identity"
    distance = np.maximum(float(eta_0_mpc) - eta, 0.0)
    span = max(float(np.max(distance)), _SMALL_FLOAT)
    shear = scale * distance / span
    phase = 0.5 * scale * distance
    return shear, phase, scale, "type_ii_nilpotent_source_integrated"


def _type_ii_projection_profiles(
    structure: StructureConstants,
    *,
    k_grid_mpc: np.ndarray,
    ell: np.ndarray,
    eta_grid_mpc: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, float, str]:
    scale = _type_ii_nilpotent_scale(structure)
    k_arr = np.asarray(k_grid_mpc, dtype=float)
    ell_arr = np.asarray(ell, dtype=float)
    if scale <= _SMALL_FLOAT:
        zeros = np.zeros((k_arr.size, ell_arr.size), dtype=float)
        return zeros, zeros, 0.0, "identity"
    eta_arr = np.asarray(eta_grid_mpc, dtype=float)
    eta_span = max(float(eta_arr[-1] - eta_arr[0]), _SMALL_FLOAT)
    distance = np.empty((k_arr.size, ell_arr.size), dtype=float)
    for ik, k in enumerate(k_arr):
        distance[ik] = np.clip(
            (ell_arr + 0.5) / max(float(k), _SMALL_FLOAT),
            0.0,
            eta_span,
        )
    shear = scale * distance / eta_span
    phase = 0.5 * scale * distance
    return shear, phase, scale, "type_ii_nilpotent_projection"


def _apply_nilpotent_source_coupling(
    sources: dict[str, np.ndarray],
    shear: np.ndarray,
) -> None:
    scalar = np.asarray(sources["m0"], dtype=float)
    sources["m+2"] = np.asarray(sources["m+2"], dtype=float) + 0.5 * shear * scalar
    sources["m-2"] = np.asarray(sources["m-2"], dtype=float) - 0.5 * shear * scalar


def apply_type_ii_nilpotent_transfer_coupling(
    structure: StructureConstants,
    *,
    transfer_T: np.ndarray,
    transfer_E: np.ndarray,
    transfer_B: np.ndarray,
    k_grid_mpc: np.ndarray,
    ell: np.ndarray,
    eta_grid_mpc: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, object]]:
    """Apply nilpotent Type-II scalar/tensor and E/B transfer coupling."""

    t_arr = np.asarray(transfer_T, dtype=float).copy()
    e_arr = np.asarray(transfer_E, dtype=float).copy()
    b_arr = np.asarray(transfer_B, dtype=float).copy()
    shear, phase, scale, status = _type_ii_projection_profiles(
        structure,
        k_grid_mpc=np.asarray(k_grid_mpc, dtype=float),
        ell=np.asarray(ell, dtype=float),
        eta_grid_mpc=np.asarray(eta_grid_mpc, dtype=float),
    )
    if scale <= _SMALL_FLOAT:
        return t_arr, e_arr, b_arr, {
            "nil_transport_status": status,
            "nil_structure_scale": 0.0,
            "nil_shear_max": 0.0,
            "nil_phase_max": 0.0,
            "nil_mode_mixing_norm": 0.0,
        }

    before = np.concatenate(
        [t_arr.ravel(), e_arr.ravel(), b_arr.ravel()]
    )
    t_arr[..., 1] += 0.5 * shear * t_arr[..., 0]
    t_arr[..., 2] -= 0.5 * shear * t_arr[..., 0]
    e_arr[..., 1] += 0.5 * shear * e_arr[..., 0]
    e_arr[..., 2] -= 0.5 * shear * e_arr[..., 0]
    b_arr[..., 1] += 0.5 * shear * b_arr[..., 0]
    b_arr[..., 2] -= 0.5 * shear * b_arr[..., 0]

    c2 = np.cos(2.0 * phase)
    s2 = np.sin(2.0 * phase)
    e_plus = c2 * e_arr[..., 1] - s2 * b_arr[..., 1]
    b_plus = s2 * e_arr[..., 1] + c2 * b_arr[..., 1]
    e_minus = c2 * e_arr[..., 2] - s2 * b_arr[..., 2]
    b_minus = s2 * e_arr[..., 2] + c2 * b_arr[..., 2]
    e_arr[..., 1] = e_plus
    e_arr[..., 2] = e_minus
    b_arr[..., 1] = b_plus
    b_arr[..., 2] = b_minus

    after = np.concatenate(
        [t_arr.ravel(), e_arr.ravel(), b_arr.ravel()]
    )
    mixing_norm = float(np.linalg.norm(after - before) / max(float(np.linalg.norm(before)), _SMALL_FLOAT))
    return t_arr, e_arr, b_arr, {
        "nil_transport_status": status,
        "nil_structure_scale": float(scale),
        "nil_shear_max": float(np.max(np.abs(shear))),
        "nil_phase_max": float(np.max(np.abs(phase))),
        "nil_mode_mixing_norm": mixing_norm,
        "nil_polarization_basis_transport": "spin2_nil_shear_rotation",
        "polarization_basis_transport": "spin2_nil_shear_rotation",
    }


def _type_vi0_directional_parameters(
    structure: StructureConstants,
) -> tuple[float, float]:
    """Return scale and imbalance for the Type VI_0 mixed-sign branch."""

    if structure.label != "VI_0":
        return 0.0, 0.0
    if (not structure.is_class_a) or abs(float(structure.n2)) > 1.0e-14:
        return 0.0, 0.0
    n1 = float(structure.n1)
    n3 = float(structure.n3)
    if n1 <= 0.0 or n3 >= 0.0:
        return 0.0, 0.0
    abs_n1 = abs(n1)
    abs_n3 = abs(n3)
    scale = abs_n1 + abs_n3
    if scale <= _SMALL_FLOAT:
        return 0.0, 0.0
    imbalance = (abs_n1 - abs_n3) / scale
    return scale, imbalance


def _vi0_directional_profile(
    structure: StructureConstants,
    *,
    eta_grid_mpc: np.ndarray,
    eta_0_mpc: float,
) -> tuple[np.ndarray, float, float, str]:
    scale, imbalance = _type_vi0_directional_parameters(structure)
    eta = np.asarray(eta_grid_mpc, dtype=float)
    if scale <= _SMALL_FLOAT:
        return np.zeros_like(eta, dtype=float), 0.0, 0.0, "identity"
    distance = np.maximum(float(eta_0_mpc) - eta, 0.0)
    span = max(float(np.max(distance)), _SMALL_FLOAT)
    shear = scale * distance / span
    return shear, scale, imbalance, "type_vi0_directional_source_integrated"


def _type_vi0_projection_profiles(
    structure: StructureConstants,
    *,
    k_grid_mpc: np.ndarray,
    ell: np.ndarray,
    eta_grid_mpc: np.ndarray,
) -> tuple[np.ndarray, float, float, str]:
    scale, imbalance = _type_vi0_directional_parameters(structure)
    k_arr = np.asarray(k_grid_mpc, dtype=float)
    ell_arr = np.asarray(ell, dtype=float)
    if scale <= _SMALL_FLOAT:
        return np.zeros((k_arr.size, ell_arr.size), dtype=float), 0.0, 0.0, "identity"
    eta_arr = np.asarray(eta_grid_mpc, dtype=float)
    eta_span = max(float(eta_arr[-1] - eta_arr[0]), _SMALL_FLOAT)
    distance = np.empty((k_arr.size, ell_arr.size), dtype=float)
    for ik, k in enumerate(k_arr):
        distance[ik] = np.clip(
            (ell_arr + 0.5) / max(float(k), _SMALL_FLOAT),
            0.0,
            eta_span,
        )
    shear = scale * distance / eta_span
    return shear, scale, imbalance, "type_vi0_directional_projection"


def _apply_vi0_directional_source_coupling(
    sources: dict[str, np.ndarray],
    shear: np.ndarray,
    imbalance: float,
) -> None:
    scalar = np.asarray(sources["m0"], dtype=float)
    plus_weight = 0.5 * (1.0 + float(imbalance))
    minus_weight = 0.5 * (1.0 - float(imbalance))
    sources["m+2"] = np.asarray(sources["m+2"], dtype=float) + plus_weight * shear * scalar
    sources["m-2"] = np.asarray(sources["m-2"], dtype=float) + minus_weight * shear * scalar


def apply_type_vi0_directional_transfer_coupling(
    structure: StructureConstants,
    *,
    transfer_T: np.ndarray,
    transfer_E: np.ndarray,
    transfer_B: np.ndarray,
    k_grid_mpc: np.ndarray,
    ell: np.ndarray,
    eta_grid_mpc: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, object]]:
    """Apply parity-even Type VI_0 directional scalar-to-tensor coupling."""

    t_arr = np.asarray(transfer_T, dtype=float).copy()
    e_arr = np.asarray(transfer_E, dtype=float).copy()
    b_arr = np.asarray(transfer_B, dtype=float).copy()
    shear, scale, imbalance, status = _type_vi0_projection_profiles(
        structure,
        k_grid_mpc=np.asarray(k_grid_mpc, dtype=float),
        ell=np.asarray(ell, dtype=float),
        eta_grid_mpc=np.asarray(eta_grid_mpc, dtype=float),
    )
    if scale <= _SMALL_FLOAT:
        return t_arr, e_arr, b_arr, {
            "vi0_transport_status": status,
            "vi0_structure_scale": 0.0,
            "vi0_directional_imbalance": 0.0,
            "vi0_shear_max": 0.0,
            "vi0_mode_mixing_norm": 0.0,
            "vi0_polarization_basis_transport": "identity",
        }

    before = np.concatenate([t_arr.ravel(), e_arr.ravel(), b_arr.ravel()])
    plus_weight = 0.5 * (1.0 + float(imbalance))
    minus_weight = 0.5 * (1.0 - float(imbalance))
    t_arr[..., 1] += plus_weight * shear * t_arr[..., 0]
    t_arr[..., 2] += minus_weight * shear * t_arr[..., 0]
    e_arr[..., 1] += plus_weight * shear * e_arr[..., 0]
    e_arr[..., 2] += minus_weight * shear * e_arr[..., 0]
    b_arr[..., 1] += plus_weight * shear * b_arr[..., 0]
    b_arr[..., 2] += minus_weight * shear * b_arr[..., 0]
    after = np.concatenate([t_arr.ravel(), e_arr.ravel(), b_arr.ravel()])
    mixing_norm = float(
        np.linalg.norm(after - before)
        / max(float(np.linalg.norm(before)), _SMALL_FLOAT)
    )
    return t_arr, e_arr, b_arr, {
        "vi0_transport_status": status,
        "vi0_structure_scale": float(scale),
        "vi0_directional_imbalance": float(imbalance),
        "vi0_shear_max": float(np.max(np.abs(shear))),
        "vi0_mode_mixing_norm": mixing_norm,
        "vi0_polarization_basis_transport": "parity_even_directional_transport",
        "polarization_basis_transport": "parity_even_directional_transport",
    }


_TYPEIII_BRANCH_FLAG = "VI_-1_special"


def _type_iii_hyperbolic_parameters(
    structure: StructureConstants,
) -> tuple[float, float, float]:
    """Return hyperbolic scale, twist scale, and h for Type III.

    Type III is the class-B ``VI_{h=-1}`` special branch with
    ``n1 > 0, n3 < 0`` and ``a_twist^2 = -n1*n3``. The branch scale
    combines the mixed-sign curvature root with the class-B twist; it is
    zero unless the algebra satisfies the Type-III invariants.
    """

    if structure.label != "III":
        return 0.0, 0.0, 0.0
    n1 = float(structure.n1)
    n3 = float(structure.n3)
    twist = float(structure.a_twist)
    h_value = float(structure.h_parameter)
    if n1 <= 0.0 or n3 >= 0.0 or twist <= 0.0:
        return 0.0, 0.0, h_value
    if abs(h_value + 1.0) > 1.0e-8:
        return 0.0, 0.0, h_value
    curvature_root = float(np.sqrt(abs(n1 * n3)))
    scale = curvature_root + twist
    return float(scale), twist, h_value


def _type_iii_projection_profiles(
    structure: StructureConstants,
    *,
    k_grid_mpc: np.ndarray,
    ell: np.ndarray,
    eta_grid_mpc: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, float, float, float, str]:
    scale, twist, h_value = _type_iii_hyperbolic_parameters(structure)
    k_arr = np.asarray(k_grid_mpc, dtype=float)
    ell_arr = np.asarray(ell, dtype=float)
    if scale <= _SMALL_FLOAT:
        zeros = np.zeros((k_arr.size, ell_arr.size), dtype=float)
        return zeros, zeros, np.ones_like(zeros), 0.0, 0.0, h_value, "identity"
    eta_arr = np.asarray(eta_grid_mpc, dtype=float)
    eta_span = max(float(eta_arr[-1] - eta_arr[0]), _SMALL_FLOAT)
    distance = np.empty((k_arr.size, ell_arr.size), dtype=float)
    for ik, k in enumerate(k_arr):
        distance[ik] = np.clip(
            (ell_arr + 0.5) / max(float(k), _SMALL_FLOAT),
            0.0,
            eta_span,
        )
    shear = scale * distance / eta_span
    phase = 0.5 * scale * distance
    attenuation = np.exp(-twist * distance / eta_span)
    return (
        shear,
        phase,
        attenuation,
        scale,
        twist,
        h_value,
        "type_iii_hyperbolic_projection",
    )


def apply_type_iii_hyperbolic_transfer_coupling(
    structure: StructureConstants,
    *,
    transfer_T: np.ndarray,
    transfer_E: np.ndarray,
    transfer_B: np.ndarray,
    k_grid_mpc: np.ndarray,
    ell: np.ndarray,
    eta_grid_mpc: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, object]]:
    """Apply the Type-III ``VI_{h=-1}`` hyperbolic branch transport."""

    t_arr = np.asarray(transfer_T, dtype=float).copy()
    e_arr = np.asarray(transfer_E, dtype=float).copy()
    b_arr = np.asarray(transfer_B, dtype=float).copy()
    shear, phase, attenuation, scale, twist, h_value, status = _type_iii_projection_profiles(
        structure,
        k_grid_mpc=np.asarray(k_grid_mpc, dtype=float),
        ell=np.asarray(ell, dtype=float),
        eta_grid_mpc=np.asarray(eta_grid_mpc, dtype=float),
    )
    if scale <= _SMALL_FLOAT:
        return t_arr, e_arr, b_arr, {
            "typeiii_transport_status": status,
            "typeiii_branch_flag": _TYPEIII_BRANCH_FLAG,
            "typeiii_h_parameter": float(h_value),
            "typeiii_hyperbolic_scale": 0.0,
            "typeiii_twist_scale": 0.0,
            "typeiii_shear_max": 0.0,
            "typeiii_phase_max": 0.0,
            "typeiii_open_attenuation_min": 1.0,
            "typeiii_mode_mixing_norm": 0.0,
            "typeiii_polarization_basis_transport": "identity",
        }

    before = np.concatenate([t_arr.ravel(), e_arr.ravel(), b_arr.ravel()])
    t_arr[..., 1] = attenuation * (t_arr[..., 1] + 0.5 * shear * t_arr[..., 0])
    t_arr[..., 2] = attenuation * (t_arr[..., 2] - 0.5 * shear * t_arr[..., 0])
    e_arr[..., 1] = attenuation * (e_arr[..., 1] + 0.5 * shear * e_arr[..., 0])
    e_arr[..., 2] = attenuation * (e_arr[..., 2] - 0.5 * shear * e_arr[..., 0])
    b_arr[..., 1] = attenuation * (b_arr[..., 1] + 0.5 * shear * b_arr[..., 0])
    b_arr[..., 2] = attenuation * (b_arr[..., 2] - 0.5 * shear * b_arr[..., 0])

    c2 = np.cos(2.0 * phase)
    s2 = np.sin(2.0 * phase)
    e_plus = c2 * e_arr[..., 1] - s2 * b_arr[..., 1]
    b_plus = s2 * e_arr[..., 1] + c2 * b_arr[..., 1]
    e_minus = c2 * e_arr[..., 2] - s2 * b_arr[..., 2]
    b_minus = s2 * e_arr[..., 2] + c2 * b_arr[..., 2]
    e_arr[..., 1] = e_plus
    e_arr[..., 2] = e_minus
    b_arr[..., 1] = b_plus
    b_arr[..., 2] = b_minus

    after = np.concatenate([t_arr.ravel(), e_arr.ravel(), b_arr.ravel()])
    mixing_norm = float(
        np.linalg.norm(after - before)
        / max(float(np.linalg.norm(before)), _SMALL_FLOAT)
    )
    return t_arr, e_arr, b_arr, {
        "typeiii_transport_status": status,
        "typeiii_branch_flag": _TYPEIII_BRANCH_FLAG,
        "typeiii_h_parameter": float(h_value),
        "typeiii_hyperbolic_scale": float(scale),
        "typeiii_twist_scale": float(twist),
        "typeiii_shear_max": float(np.max(np.abs(shear))),
        "typeiii_phase_max": float(np.max(np.abs(phase))),
        "typeiii_open_attenuation_min": float(np.min(attenuation)),
        "typeiii_mode_mixing_norm": mixing_norm,
        "typeiii_polarization_basis_transport": "spin2_hyperbolic_branch_rotation",
        "polarization_basis_transport": "spin2_hyperbolic_branch_rotation",
    }


_TYPEIV_COORDINATE_ORDER = "n3_dominated_then_a_twist"


def _type_iv_solvable_parameters(
    structure: StructureConstants,
) -> tuple[float, float, float, float]:
    """Return solvable scale, twist, n3, and privileged-axis weight.

    Type IV is the class-B rank-one solvable branch with ``n3 > 0`` and
    ``a_twist > 0``. It has no FLRW limit, so the projection must not
    collapse to isotropic radial weighting. The returned weight keeps the
    n3-dominated coordinate order explicit in the tensor-channel coupling.
    """

    if structure.label != "IV":
        return 0.0, 0.0, 0.0, 0.0
    n3 = float(structure.n3)
    twist = float(structure.a_twist)
    if n3 <= 0.0 or twist <= 0.0:
        return 0.0, twist, n3, 0.0
    scale = n3 + twist
    privileged_weight = n3 / max(scale, _SMALL_FLOAT)
    return float(scale), twist, n3, float(privileged_weight)


def _type_iv_projection_profiles(
    structure: StructureConstants,
    *,
    k_grid_mpc: np.ndarray,
    ell: np.ndarray,
    eta_grid_mpc: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, float, float, float, float, str]:
    scale, twist, n3, privileged_weight = _type_iv_solvable_parameters(structure)
    k_arr = np.asarray(k_grid_mpc, dtype=float)
    ell_arr = np.asarray(ell, dtype=float)
    if scale <= _SMALL_FLOAT:
        zeros = np.zeros((k_arr.size, ell_arr.size), dtype=float)
        return zeros, zeros, np.ones_like(zeros), 0.0, twist, n3, privileged_weight, "identity"
    eta_arr = np.asarray(eta_grid_mpc, dtype=float)
    eta_span = max(float(eta_arr[-1] - eta_arr[0]), _SMALL_FLOAT)
    distance = np.empty((k_arr.size, ell_arr.size), dtype=float)
    for ik, k in enumerate(k_arr):
        distance[ik] = np.clip(
            (ell_arr + 0.5) / max(float(k), _SMALL_FLOAT),
            0.0,
            eta_span,
        )
    shear = scale * distance / eta_span
    phase = twist * distance
    attenuation = np.exp(-(twist + 0.5 * n3) * distance / eta_span)
    return (
        shear,
        phase,
        attenuation,
        scale,
        twist,
        n3,
        privileged_weight,
        "type_iv_solvable_projection",
    )


def apply_type_iv_solvable_transfer_coupling(
    structure: StructureConstants,
    *,
    transfer_T: np.ndarray,
    transfer_E: np.ndarray,
    transfer_B: np.ndarray,
    k_grid_mpc: np.ndarray,
    ell: np.ndarray,
    eta_grid_mpc: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, object]]:
    """Apply Type-IV rank-one solvable tensor and spin-2 transport."""

    t_arr = np.asarray(transfer_T, dtype=float).copy()
    e_arr = np.asarray(transfer_E, dtype=float).copy()
    b_arr = np.asarray(transfer_B, dtype=float).copy()
    (
        shear,
        phase,
        attenuation,
        scale,
        twist,
        n3,
        privileged_weight,
        status,
    ) = _type_iv_projection_profiles(
        structure,
        k_grid_mpc=np.asarray(k_grid_mpc, dtype=float),
        ell=np.asarray(ell, dtype=float),
        eta_grid_mpc=np.asarray(eta_grid_mpc, dtype=float),
    )
    if scale <= _SMALL_FLOAT:
        return t_arr, e_arr, b_arr, {
            "typeiv_transport_status": status,
            "typeiv_coordinate_order": _TYPEIV_COORDINATE_ORDER,
            "typeiv_structure_scale": 0.0,
            "typeiv_n3_scale": float(n3),
            "typeiv_twist_scale": float(twist),
            "typeiv_privileged_weight": float(privileged_weight),
            "typeiv_shear_max": 0.0,
            "typeiv_phase_max": 0.0,
            "typeiv_edge_attenuation_min": 1.0,
            "typeiv_mode_mixing_norm": 0.0,
            "typeiv_polarization_basis_transport": "identity",
        }

    before = np.concatenate([t_arr.ravel(), e_arr.ravel(), b_arr.ravel()])
    plus_weight = 0.5 + 0.5 * privileged_weight
    minus_weight = 0.5 * (1.0 - privileged_weight)
    t_arr[..., 1] = attenuation * (t_arr[..., 1] + plus_weight * shear * t_arr[..., 0])
    t_arr[..., 2] = attenuation * (t_arr[..., 2] - minus_weight * shear * t_arr[..., 0])
    e_arr[..., 1] = attenuation * (e_arr[..., 1] + plus_weight * shear * e_arr[..., 0])
    e_arr[..., 2] = attenuation * (e_arr[..., 2] - minus_weight * shear * e_arr[..., 0])
    b_arr[..., 1] = attenuation * (b_arr[..., 1] + plus_weight * shear * b_arr[..., 0])
    b_arr[..., 2] = attenuation * (b_arr[..., 2] - minus_weight * shear * b_arr[..., 0])

    c2 = np.cos(2.0 * phase)
    s2 = np.sin(2.0 * phase)
    e_plus = c2 * e_arr[..., 1] - s2 * b_arr[..., 1]
    b_plus = s2 * e_arr[..., 1] + c2 * b_arr[..., 1]
    e_minus = c2 * e_arr[..., 2] - s2 * b_arr[..., 2]
    b_minus = s2 * e_arr[..., 2] + c2 * b_arr[..., 2]
    e_arr[..., 1] = e_plus
    e_arr[..., 2] = e_minus
    b_arr[..., 1] = b_plus
    b_arr[..., 2] = b_minus

    after = np.concatenate([t_arr.ravel(), e_arr.ravel(), b_arr.ravel()])
    mixing_norm = float(
        np.linalg.norm(after - before)
        / max(float(np.linalg.norm(before)), _SMALL_FLOAT)
    )
    return t_arr, e_arr, b_arr, {
        "typeiv_transport_status": status,
        "typeiv_coordinate_order": _TYPEIV_COORDINATE_ORDER,
        "typeiv_structure_scale": float(scale),
        "typeiv_n3_scale": float(n3),
        "typeiv_twist_scale": float(twist),
        "typeiv_privileged_weight": float(privileged_weight),
        "typeiv_shear_max": float(np.max(np.abs(shear))),
        "typeiv_phase_max": float(np.max(np.abs(phase))),
        "typeiv_edge_attenuation_min": float(np.min(attenuation)),
        "typeiv_mode_mixing_norm": mixing_norm,
        "typeiv_polarization_basis_transport": "spin2_solvable_edge_rotation",
        "polarization_basis_transport": "spin2_solvable_edge_rotation",
    }


def _type_v_open_envelope(
    structure: StructureConstants,
    *,
    k_grid_mpc: np.ndarray,
) -> tuple[np.ndarray, float, str]:
    """Return the leading open-hyperbolic envelope for the Type V branch."""

    if structure.label != "V":
        return np.ones_like(k_grid_mpc, dtype=np.float64), 0.0, "identity"
    scale = float(structure.a_twist)
    if scale <= _SMALL_FLOAT:
        return np.ones_like(k_grid_mpc, dtype=np.float64), 0.0, "identity"
    k = np.maximum(np.asarray(k_grid_mpc, dtype=np.float64), _SMALL_FLOAT)
    envelope = 1.0 / np.sqrt(1.0 + (scale / k) ** 2)
    return envelope, scale, "type_v_open_hyperbolic_projection"


def apply_type_v_open_hyperbolic_transfer_envelope(
    structure: StructureConstants,
    *,
    transfer_T: np.ndarray,
    transfer_E: np.ndarray,
    transfer_B: np.ndarray,
    k_grid_mpc: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, object]]:
    """Apply Type V open-FLRW curvature envelope without intrinsic m-mixing."""

    t_arr = np.asarray(transfer_T, dtype=np.float64).copy()
    e_arr = np.asarray(transfer_E, dtype=np.float64).copy()
    b_arr = np.asarray(transfer_B, dtype=np.float64).copy()
    envelope, scale, status = _type_v_open_envelope(
        structure,
        k_grid_mpc=np.asarray(k_grid_mpc, dtype=np.float64),
    )
    envelope_3d = envelope[:, None, None]
    t_arr *= envelope_3d
    e_arr *= envelope_3d
    b_arr *= envelope_3d
    metadata = {
        "typev_transport_status": status,
        "typev_chart_metadata": "open_chart",
        "typev_curvature_scale": float(scale),
        "typev_open_envelope_min": float(np.min(envelope)),
        "typev_open_envelope_max": float(np.max(envelope)),
        "typev_open_anchor_deviation_max": float(np.max(np.abs(1.0 - envelope))),
        "typev_mode_mixing_norm": 0.0,
        "typev_polarization_basis_transport": "open_hyperbolic_parallel_transport",
        "polarization_basis_transport": "open_hyperbolic_parallel_transport",
    }
    return t_arr, e_arr, b_arr, metadata


_TYPEVIH_BRANCH_FLAG = "negative_h_branch"


def _type_vih_negative_h_parameters(
    structure: StructureConstants,
) -> tuple[float, float, float, float, float]:
    """Return scale, twist, h, imbalance, and h-twist scale for Type VI_h."""

    h_value = float(structure.h_parameter)
    if structure.label != "VI_h":
        return 0.0, 0.0, h_value, 0.0, 0.0
    n1 = float(structure.n1)
    n3 = float(structure.n3)
    twist = float(structure.a_twist)
    if n1 <= 0.0 or n3 >= 0.0 or twist <= 0.0 or h_value >= 0.0:
        return 0.0, twist, h_value, 0.0, 0.0
    if abs(h_value + 1.0) <= 1.0e-8:
        return 0.0, twist, h_value, 0.0, 0.0
    abs_n1 = abs(n1)
    abs_n3 = abs(n3)
    directional_scale = abs_n1 + abs_n3
    if directional_scale <= _SMALL_FLOAT:
        return 0.0, twist, h_value, 0.0, 0.0
    h_twist_scale = 1.0 / (1.0 + abs(h_value))
    curvature_root = float(np.sqrt(abs(n1 * n3)))
    scale = curvature_root + h_twist_scale * directional_scale + twist
    imbalance = (abs_n1 - abs_n3) / directional_scale
    return float(scale), twist, h_value, float(imbalance), float(h_twist_scale)


def _type_vih_projection_profiles(
    structure: StructureConstants,
    *,
    k_grid_mpc: np.ndarray,
    ell: np.ndarray,
    eta_grid_mpc: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, float, float, float, float, float, str]:
    scale, twist, h_value, imbalance, h_twist_scale = _type_vih_negative_h_parameters(
        structure
    )
    k_arr = np.asarray(k_grid_mpc, dtype=float)
    ell_arr = np.asarray(ell, dtype=float)
    if scale <= _SMALL_FLOAT:
        zeros = np.zeros((k_arr.size, ell_arr.size), dtype=float)
        return (
            zeros,
            zeros,
            np.ones_like(zeros),
            0.0,
            twist,
            h_value,
            0.0,
            h_twist_scale,
            "identity",
        )
    eta_arr = np.asarray(eta_grid_mpc, dtype=float)
    eta_span = max(float(eta_arr[-1] - eta_arr[0]), _SMALL_FLOAT)
    distance = np.empty((k_arr.size, ell_arr.size), dtype=float)
    for ik, k in enumerate(k_arr):
        distance[ik] = np.clip(
            (ell_arr + 0.5) / max(float(k), _SMALL_FLOAT),
            0.0,
            eta_span,
        )
    distance_fraction = distance / eta_span
    shear = scale * distance_fraction
    phase = 0.5 * (scale + twist * np.sqrt(abs(h_value))) * distance
    attenuation = np.exp(-twist * (1.0 + abs(h_value)) * distance_fraction)
    return (
        shear,
        phase,
        attenuation,
        scale,
        twist,
        h_value,
        imbalance,
        h_twist_scale,
        "type_vih_negative_h_projection",
    )


def apply_type_vih_negative_h_transfer_coupling(
    structure: StructureConstants,
    *,
    transfer_T: np.ndarray,
    transfer_E: np.ndarray,
    transfer_B: np.ndarray,
    k_grid_mpc: np.ndarray,
    ell: np.ndarray,
    eta_grid_mpc: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, object]]:
    """Apply Type VI_h negative-h mixed-sign branch transport."""

    t_arr = np.asarray(transfer_T, dtype=float).copy()
    e_arr = np.asarray(transfer_E, dtype=float).copy()
    b_arr = np.asarray(transfer_B, dtype=float).copy()
    (
        shear,
        phase,
        attenuation,
        scale,
        twist,
        h_value,
        imbalance,
        h_twist_scale,
        status,
    ) = _type_vih_projection_profiles(
        structure,
        k_grid_mpc=np.asarray(k_grid_mpc, dtype=float),
        ell=np.asarray(ell, dtype=float),
        eta_grid_mpc=np.asarray(eta_grid_mpc, dtype=float),
    )
    if scale <= _SMALL_FLOAT:
        return t_arr, e_arr, b_arr, {
            "vih_transport_status": status,
            "vih_branch_flag": _TYPEVIH_BRANCH_FLAG,
            "vih_h_parameter": float(h_value),
            "vih_structure_scale": 0.0,
            "vih_twist_scale": float(twist),
            "vih_h_twist_scale": float(h_twist_scale),
            "vih_directional_imbalance": 0.0,
            "vih_shear_max": 0.0,
            "vih_phase_max": 0.0,
            "vih_open_attenuation_min": 1.0,
            "vih_mode_mixing_norm": 0.0,
            "vih_polarization_basis_transport": "identity",
        }

    before = np.concatenate([t_arr.ravel(), e_arr.ravel(), b_arr.ravel()])
    plus_weight = 0.5 * (1.0 + float(imbalance))
    minus_weight = 0.5 * (1.0 - float(imbalance))
    t_arr[..., 1] = attenuation * (t_arr[..., 1] + plus_weight * shear * t_arr[..., 0])
    t_arr[..., 2] = attenuation * (t_arr[..., 2] - minus_weight * shear * t_arr[..., 0])
    e_arr[..., 1] = attenuation * (e_arr[..., 1] + plus_weight * shear * e_arr[..., 0])
    e_arr[..., 2] = attenuation * (e_arr[..., 2] - minus_weight * shear * e_arr[..., 0])
    b_arr[..., 1] = attenuation * (b_arr[..., 1] + plus_weight * shear * b_arr[..., 0])
    b_arr[..., 2] = attenuation * (b_arr[..., 2] - minus_weight * shear * b_arr[..., 0])

    c2 = np.cos(2.0 * phase)
    s2 = np.sin(2.0 * phase)
    e_plus = c2 * e_arr[..., 1] - s2 * b_arr[..., 1]
    b_plus = s2 * e_arr[..., 1] + c2 * b_arr[..., 1]
    e_minus = c2 * e_arr[..., 2] - s2 * b_arr[..., 2]
    b_minus = s2 * e_arr[..., 2] + c2 * b_arr[..., 2]
    e_arr[..., 1] = e_plus
    e_arr[..., 2] = e_minus
    b_arr[..., 1] = b_plus
    b_arr[..., 2] = b_minus

    after = np.concatenate([t_arr.ravel(), e_arr.ravel(), b_arr.ravel()])
    mixing_norm = float(
        np.linalg.norm(after - before)
        / max(float(np.linalg.norm(before)), _SMALL_FLOAT)
    )
    return t_arr, e_arr, b_arr, {
        "vih_transport_status": status,
        "vih_branch_flag": _TYPEVIH_BRANCH_FLAG,
        "vih_h_parameter": float(h_value),
        "vih_structure_scale": float(scale),
        "vih_twist_scale": float(twist),
        "vih_h_twist_scale": float(h_twist_scale),
        "vih_directional_imbalance": float(imbalance),
        "vih_shear_max": float(np.max(np.abs(shear))),
        "vih_phase_max": float(np.max(np.abs(phase))),
        "vih_open_attenuation_min": float(np.min(attenuation)),
        "vih_mode_mixing_norm": mixing_norm,
        "vih_polarization_basis_transport": "spin2_negative_h_branch_rotation",
        "polarization_basis_transport": "spin2_negative_h_branch_rotation",
    }


_TYPEVIII_BRANCH_FLAG = "noncompact_branch"
_TYPEVIII_DISC_RADIUS = float(np.tanh(1.5))


def _type_viii_sl2r_parameters(
    structure: StructureConstants,
) -> tuple[float, float, float, float]:
    """Return SL(2,R) scale, negative-axis weight, positive-axis split, disc radius."""

    if structure.label != "VIII":
        return 0.0, 0.0, 0.0, _TYPEVIII_DISC_RADIUS
    n1 = float(structure.n1)
    n2 = float(structure.n2)
    n3 = float(structure.n3)
    if n1 >= 0.0 or n2 <= 0.0 or n3 <= 0.0:
        return 0.0, 0.0, 0.0, _TYPEVIII_DISC_RADIUS
    neg = abs(n1)
    pos = n2 + n3
    scale = neg + pos
    if scale <= _SMALL_FLOAT:
        return 0.0, 0.0, 0.0, _TYPEVIII_DISC_RADIUS
    negative_axis_weight = neg / scale
    positive_axis_split = (n3 - n2) / max(pos, _SMALL_FLOAT)
    return (
        float(scale),
        float(negative_axis_weight),
        float(positive_axis_split),
        _TYPEVIII_DISC_RADIUS,
    )


def _type_viii_projection_profiles(
    structure: StructureConstants,
    *,
    k_grid_mpc: np.ndarray,
    ell: np.ndarray,
    eta_grid_mpc: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, float, float, float, float, str]:
    scale, negative_axis_weight, positive_axis_split, disc_radius = (
        _type_viii_sl2r_parameters(structure)
    )
    k_arr = np.asarray(k_grid_mpc, dtype=float)
    ell_arr = np.asarray(ell, dtype=float)
    if scale <= _SMALL_FLOAT:
        zeros = np.zeros((k_arr.size, ell_arr.size), dtype=float)
        return (
            zeros,
            zeros,
            np.ones_like(zeros),
            0.0,
            0.0,
            0.0,
            disc_radius,
            "identity",
        )
    eta_arr = np.asarray(eta_grid_mpc, dtype=float)
    eta_span = max(float(eta_arr[-1] - eta_arr[0]), _SMALL_FLOAT)
    distance = np.empty((k_arr.size, ell_arr.size), dtype=float)
    for ik, k in enumerate(k_arr):
        distance[ik] = np.clip(
            (ell_arr + 0.5) / max(float(k), _SMALL_FLOAT),
            0.0,
            eta_span,
        )
    distance_fraction = distance / eta_span
    shear = scale * disc_radius * distance_fraction
    phase = 0.5 * scale * (1.0 + negative_axis_weight) * distance
    attenuation = np.exp(-scale * negative_axis_weight * distance_fraction)
    return (
        shear,
        phase,
        attenuation,
        scale,
        negative_axis_weight,
        positive_axis_split,
        disc_radius,
        "type_viii_sl2r_noncompact_projection",
    )


def apply_type_viii_sl2r_noncompact_transfer_coupling(
    structure: StructureConstants,
    *,
    transfer_T: np.ndarray,
    transfer_E: np.ndarray,
    transfer_B: np.ndarray,
    k_grid_mpc: np.ndarray,
    ell: np.ndarray,
    eta_grid_mpc: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, object]]:
    """Apply Type VIII SL(2,R) noncompact branch transport."""

    t_arr = np.asarray(transfer_T, dtype=float).copy()
    e_arr = np.asarray(transfer_E, dtype=float).copy()
    b_arr = np.asarray(transfer_B, dtype=float).copy()
    (
        shear,
        phase,
        attenuation,
        scale,
        negative_axis_weight,
        positive_axis_split,
        disc_radius,
        status,
    ) = _type_viii_projection_profiles(
        structure,
        k_grid_mpc=np.asarray(k_grid_mpc, dtype=float),
        ell=np.asarray(ell, dtype=float),
        eta_grid_mpc=np.asarray(eta_grid_mpc, dtype=float),
    )
    if scale <= _SMALL_FLOAT:
        return t_arr, e_arr, b_arr, {
            "typeviii_transport_status": status,
            "typeviii_branch_flag": _TYPEVIII_BRANCH_FLAG,
            "typeviii_structure_scale": 0.0,
            "typeviii_negative_axis_weight": 0.0,
            "typeviii_positive_axis_split": 0.0,
            "typeviii_disc_radius_x_eq_tanh_xi": float(disc_radius),
            "typeviii_shear_max": 0.0,
            "typeviii_phase_max": 0.0,
            "typeviii_noncompact_attenuation_min": 1.0,
            "typeviii_mode_mixing_norm": 0.0,
            "typeviii_series_tags": ("trivial", "discrete_positive", "discrete_negative"),
            "typeviii_continuous_series_tag": "continuous_principal",
            "typeviii_polarization_basis_transport": "identity",
        }

    before = np.concatenate([t_arr.ravel(), e_arr.ravel(), b_arr.ravel()])
    plus_weight = 0.5 * (1.0 - negative_axis_weight) * (1.0 + positive_axis_split)
    minus_weight = negative_axis_weight + 0.5 * (1.0 - negative_axis_weight) * (
        1.0 - positive_axis_split
    )
    t_arr[..., 1] = attenuation * (t_arr[..., 1] + plus_weight * shear * t_arr[..., 0])
    t_arr[..., 2] = attenuation * (t_arr[..., 2] - minus_weight * shear * t_arr[..., 0])
    e_arr[..., 1] = attenuation * (e_arr[..., 1] + plus_weight * shear * e_arr[..., 0])
    e_arr[..., 2] = attenuation * (e_arr[..., 2] - minus_weight * shear * e_arr[..., 0])
    b_arr[..., 1] = attenuation * (b_arr[..., 1] + plus_weight * shear * b_arr[..., 0])
    b_arr[..., 2] = attenuation * (b_arr[..., 2] - minus_weight * shear * b_arr[..., 0])

    c2 = np.cos(2.0 * phase)
    s2 = np.sin(2.0 * phase)
    e_plus = c2 * e_arr[..., 1] - s2 * b_arr[..., 1]
    b_plus = s2 * e_arr[..., 1] + c2 * b_arr[..., 1]
    e_minus = c2 * e_arr[..., 2] - s2 * b_arr[..., 2]
    b_minus = s2 * e_arr[..., 2] + c2 * b_arr[..., 2]
    e_arr[..., 1] = e_plus
    e_arr[..., 2] = e_minus
    b_arr[..., 1] = b_plus
    b_arr[..., 2] = b_minus

    after = np.concatenate([t_arr.ravel(), e_arr.ravel(), b_arr.ravel()])
    mixing_norm = float(
        np.linalg.norm(after - before)
        / max(float(np.linalg.norm(before)), _SMALL_FLOAT)
    )
    return t_arr, e_arr, b_arr, {
        "typeviii_transport_status": status,
        "typeviii_branch_flag": _TYPEVIII_BRANCH_FLAG,
        "typeviii_structure_scale": float(scale),
        "typeviii_negative_axis_weight": float(negative_axis_weight),
        "typeviii_positive_axis_split": float(positive_axis_split),
        "typeviii_disc_radius_x_eq_tanh_xi": float(disc_radius),
        "typeviii_shear_max": float(np.max(np.abs(shear))),
        "typeviii_phase_max": float(np.max(np.abs(phase))),
        "typeviii_noncompact_attenuation_min": float(np.min(attenuation)),
        "typeviii_mode_mixing_norm": mixing_norm,
        "typeviii_series_tags": ("trivial", "discrete_positive", "discrete_negative"),
        "typeviii_continuous_series_tag": "continuous_principal",
        "typeviii_polarization_basis_transport": "spin2_sl2r_noncompact_rotation",
        "polarization_basis_transport": "spin2_sl2r_noncompact_rotation",
    }


def _type_viih_open_helical_parameters(
    structure: StructureConstants,
) -> tuple[float, float, float]:
    """Return effective pitch, open twist, and h for Type VII_h."""

    if structure.label != "VII_h":
        return 0.0, 0.0, 0.0
    product = float(structure.n1) * float(structure.n3)
    twist = float(structure.a_twist)
    h_value = float(structure.h_parameter)
    if product <= 0.0 or twist <= 0.0 or h_value < 0.0:
        return 0.0, 0.0, 0.0
    pitch = np.sqrt(product) * (1.0 + np.sqrt(h_value))
    return float(pitch), twist, h_value


def _viih_open_helical_profile(
    structure: StructureConstants,
    *,
    eta_grid_mpc: np.ndarray,
    eta_0_mpc: float,
) -> tuple[np.ndarray, np.ndarray, float, float, float, str]:
    pitch, twist, h_value = _type_viih_open_helical_parameters(structure)
    eta = np.asarray(eta_grid_mpc, dtype=float)
    if pitch <= _SMALL_FLOAT:
        ones = np.ones_like(eta, dtype=float)
        zeros = np.zeros_like(eta, dtype=float)
        return zeros, ones, 0.0, 0.0, 0.0, "identity"
    distance = np.maximum(float(eta_0_mpc) - eta, 0.0)
    span = max(float(np.max(distance)), _SMALL_FLOAT)
    phase = pitch * distance
    attenuation = np.exp(-twist * distance / span)
    return phase, attenuation, pitch, twist, h_value, "type_viih_open_helical_source_integrated"


def _type_viih_projection_profiles(
    structure: StructureConstants,
    *,
    k_grid_mpc: np.ndarray,
    ell: np.ndarray,
    eta_grid_mpc: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, float, float, float, str]:
    pitch, twist, h_value = _type_viih_open_helical_parameters(structure)
    k_arr = np.asarray(k_grid_mpc, dtype=float)
    ell_arr = np.asarray(ell, dtype=float)
    if pitch <= _SMALL_FLOAT:
        zeros = np.zeros((k_arr.size, ell_arr.size), dtype=float)
        return zeros, np.ones_like(zeros), 0.0, 0.0, 0.0, "identity"
    eta_arr = np.asarray(eta_grid_mpc, dtype=float)
    eta_span = max(float(eta_arr[-1] - eta_arr[0]), _SMALL_FLOAT)
    distance = np.empty((k_arr.size, ell_arr.size), dtype=float)
    for ik, k in enumerate(k_arr):
        distance[ik] = np.clip(
            (ell_arr + 0.5) / max(float(k), _SMALL_FLOAT),
            0.0,
            eta_span,
        )
    phase = pitch * distance
    attenuation = np.exp(-twist * distance / eta_span)
    return phase, attenuation, pitch, twist, h_value, "type_viih_open_helical_projection"


def apply_type_viih_open_helical_transfer_rotation(
    structure: StructureConstants,
    *,
    transfer_T: np.ndarray,
    transfer_E: np.ndarray,
    transfer_B: np.ndarray,
    k_grid_mpc: np.ndarray,
    ell: np.ndarray,
    eta_grid_mpc: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, object]]:
    """Apply open helical Type VII_h transport to tensor and polarization rows."""

    t_arr = np.asarray(transfer_T, dtype=float).copy()
    e_arr = np.asarray(transfer_E, dtype=float).copy()
    b_arr = np.asarray(transfer_B, dtype=float).copy()
    phase, attenuation, pitch, twist, h_value, status = _type_viih_projection_profiles(
        structure,
        k_grid_mpc=np.asarray(k_grid_mpc, dtype=float),
        ell=np.asarray(ell, dtype=float),
        eta_grid_mpc=np.asarray(eta_grid_mpc, dtype=float),
    )
    if pitch <= _SMALL_FLOAT:
        return t_arr, e_arr, b_arr, {
            "viih_transport_status": status,
            "viih_helical_pitch": 0.0,
            "viih_twist_scale": 0.0,
            "viih_h_parameter": 0.0,
            "viih_phase_max": 0.0,
            "viih_open_attenuation_min": 1.0,
            "viih_mode_mixing_norm": 0.0,
            "viih_polarization_basis_transport": "identity",
        }

    before = np.concatenate(
        [t_arr[..., 1:].ravel(), e_arr[..., 1:].ravel(), b_arr[..., 1:].ravel()]
    )
    t_arr[..., 1], t_arr[..., 2] = _rotate_and_attenuate_tensor_pair(
        t_arr[..., 1],
        t_arr[..., 2],
        phase,
        attenuation,
    )
    e_plus, e_minus = _rotate_and_attenuate_tensor_pair(
        e_arr[..., 1],
        e_arr[..., 2],
        phase,
        attenuation,
    )
    b_plus, b_minus = _rotate_and_attenuate_tensor_pair(
        b_arr[..., 1],
        b_arr[..., 2],
        phase,
        attenuation,
    )
    c2 = np.cos(2.0 * phase)
    s2 = np.sin(2.0 * phase)
    e_arr[..., 1] = c2 * e_plus - s2 * b_plus
    b_arr[..., 1] = s2 * e_plus + c2 * b_plus
    e_arr[..., 2] = c2 * e_minus - s2 * b_minus
    b_arr[..., 2] = s2 * e_minus + c2 * b_minus
    after = np.concatenate(
        [t_arr[..., 1:].ravel(), e_arr[..., 1:].ravel(), b_arr[..., 1:].ravel()]
    )
    mixing_norm = float(
        np.linalg.norm(after - before)
        / max(float(np.linalg.norm(before)), _SMALL_FLOAT)
    )
    return t_arr, e_arr, b_arr, {
        "viih_transport_status": status,
        "viih_helical_pitch": float(pitch),
        "viih_twist_scale": float(twist),
        "viih_h_parameter": float(h_value),
        "viih_phase_max": float(np.max(np.abs(phase))),
        "viih_open_attenuation_min": float(np.min(attenuation)),
        "viih_mode_mixing_norm": mixing_norm,
        "viih_polarization_basis_transport": "spin2_open_helical_rotation",
        "polarization_basis_transport": "spin2_open_helical_rotation",
    }


def _helical_phase_profile(
    structure: StructureConstants,
    *,
    eta_grid_mpc: np.ndarray,
    eta_0_mpc: float,
) -> tuple[np.ndarray, float, str]:
    pitch = _type_vii0_helical_pitch(structure)
    if pitch <= _SMALL_FLOAT:
        return np.zeros_like(eta_grid_mpc, dtype=float), 0.0, "identity"
    phase = pitch * (float(eta_0_mpc) - np.asarray(eta_grid_mpc, dtype=float))
    return phase, pitch, "type_vii0_helical_source_integrated"


def _type_vii0_projection_phase_matrix(
    structure: StructureConstants,
    *,
    k_grid_mpc: np.ndarray,
    ell: np.ndarray,
    eta_grid_mpc: np.ndarray,
) -> tuple[np.ndarray, float, str]:
    """Stationary-phase helical angle used by matrix-path projections."""

    pitch = _type_vii0_helical_pitch(structure)
    if pitch <= _SMALL_FLOAT:
        return (
            np.zeros((k_grid_mpc.size, ell.size), dtype=float),
            0.0,
            "identity",
        )
    eta_arr = np.asarray(eta_grid_mpc, dtype=float)
    eta_span = float(eta_arr[-1] - eta_arr[0])
    distance = np.empty((k_grid_mpc.size, ell.size), dtype=float)
    ell_arr = np.asarray(ell, dtype=float)
    for ik, k in enumerate(np.asarray(k_grid_mpc, dtype=float)):
        distance[ik] = np.clip(
            (ell_arr + 0.5) / max(float(k), _SMALL_FLOAT),
            0.0,
            eta_span,
        )
    return pitch * distance, pitch, "type_vii0_helical_projection"


def apply_type_vii0_helical_transfer_rotation(
    structure: StructureConstants,
    *,
    transfer_T: np.ndarray,
    transfer_E: np.ndarray,
    transfer_B: np.ndarray,
    k_grid_mpc: np.ndarray,
    ell: np.ndarray,
    eta_grid_mpc: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, object]]:
    """Apply real-helicity and spin-2 transport for Type VII_0 transfer rows.

    The arrays use the local BASS storage order ``(m0, m+2, m-2)``.  Type I
    and non-VII_0 callers receive an exact copy with identity metadata.
    """

    t_arr = np.asarray(transfer_T, dtype=float).copy()
    e_arr = np.asarray(transfer_E, dtype=float).copy()
    b_arr = np.asarray(transfer_B, dtype=float).copy()
    phase, pitch, status = _type_vii0_projection_phase_matrix(
        structure,
        k_grid_mpc=np.asarray(k_grid_mpc, dtype=float),
        ell=np.asarray(ell, dtype=float),
        eta_grid_mpc=np.asarray(eta_grid_mpc, dtype=float),
    )
    if pitch <= _SMALL_FLOAT:
        return t_arr, e_arr, b_arr, {
            "helical_transport_status": status,
            "helical_pitch": 0.0,
            "helical_phase_max": 0.0,
            "polarization_basis_transport": "identity",
            "helicity_mode_mixing_norm": 0.0,
        }

    before = np.concatenate(
        [t_arr[..., 1:].ravel(), e_arr[..., 1:].ravel(), b_arr[..., 1:].ravel()]
    )
    t_plus, t_minus = _rotate_tensor_pair(t_arr[..., 1], t_arr[..., 2], phase)
    e_plus, e_minus = _rotate_tensor_pair(e_arr[..., 1], e_arr[..., 2], phase)
    b_plus, b_minus = _rotate_tensor_pair(b_arr[..., 1], b_arr[..., 2], phase)
    c2 = np.cos(2.0 * phase)
    s2 = np.sin(2.0 * phase)
    e_plus_spin = c2 * e_plus - s2 * b_plus
    b_plus_spin = s2 * e_plus + c2 * b_plus
    e_minus_spin = c2 * e_minus - s2 * b_minus
    b_minus_spin = s2 * e_minus + c2 * b_minus

    t_arr[..., 1] = t_plus
    t_arr[..., 2] = t_minus
    e_arr[..., 1] = e_plus_spin
    e_arr[..., 2] = e_minus_spin
    b_arr[..., 1] = b_plus_spin
    b_arr[..., 2] = b_minus_spin
    after = np.concatenate(
        [t_arr[..., 1:].ravel(), e_arr[..., 1:].ravel(), b_arr[..., 1:].ravel()]
    )
    scale = max(float(np.linalg.norm(before)), _SMALL_FLOAT)
    mixing_norm = float(np.linalg.norm(after - before) / scale)
    return t_arr, e_arr, b_arr, {
        "helical_transport_status": status,
        "helical_pitch": float(pitch),
        "helical_phase_max": float(np.max(np.abs(phase))),
        "polarization_basis_transport": "spin2_helical_rotation",
        "helicity_mode_mixing_norm": mixing_norm,
    }


_TYPEIX_BRANCH_FLAG = "compact_su2_branch"
_TYPEIX_J = 2
_TYPEIX_SPECTRAL_EIGENVALUE = _TYPEIX_J * (_TYPEIX_J + 1)
_TYPEIX_INVARIANT_VOLUME = float(8.0 * np.pi ** 2)
_TYPEIX_J2_UNIT_AMPLITUDE = float(np.sqrt(5.0 / _TYPEIX_INVARIANT_VOLUME))


def _type_ix_compact_parameters(
    structure: StructureConstants,
) -> tuple[float, float] | None:
    """Return compact curvature scale and positive-axis anisotropy split."""

    if structure.label != "IX" or not structure.is_class_a:
        return None
    n_diag = np.asarray(structure.n_diag, dtype=float)
    if np.any(n_diag <= 0.0):
        return None
    curvature_scale = float(np.mean(n_diag))
    if curvature_scale <= _SMALL_FLOAT:
        return None
    anisotropy_split = float((np.max(n_diag) - np.min(n_diag)) / curvature_scale)
    return curvature_scale, anisotropy_split


def _type_ix_projection_profiles(
    structure: StructureConstants,
    *,
    k_grid_mpc: np.ndarray,
    ell: np.ndarray,
    eta_grid_mpc: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, float, float, str]:
    params = _type_ix_compact_parameters(structure)
    if params is None:
        shape = (np.asarray(k_grid_mpc, dtype=float).size, np.asarray(ell, dtype=float).size)
        return (
            np.zeros(shape, dtype=float),
            np.ones(shape, dtype=float),
            np.ones(shape, dtype=float),
            0.0,
            0.0,
            "identity",
        )
    curvature_scale, anisotropy_split = params
    eta_arr = np.asarray(eta_grid_mpc, dtype=float)
    eta_span = float(eta_arr[-1] - eta_arr[0])
    ell_arr = np.asarray(ell, dtype=float)
    distance = np.empty((np.asarray(k_grid_mpc, dtype=float).size, ell_arr.size), dtype=float)
    for ik, k_value in enumerate(np.asarray(k_grid_mpc, dtype=float)):
        distance[ik] = np.clip(
            (ell_arr + 0.5) / max(float(k_value), _SMALL_FLOAT),
            0.0,
            eta_span,
        )
    compact_phase = curvature_scale * distance
    wigner_d_j2_profile = 0.5 * (3.0 * np.cos(compact_phase) ** 2 - 1.0)
    spectral_envelope = np.clip(
        1.0 + 0.25 * anisotropy_split * wigner_d_j2_profile,
        0.25,
        1.75,
    )
    return (
        compact_phase,
        wigner_d_j2_profile,
        spectral_envelope,
        curvature_scale,
        anisotropy_split,
        "type_ix_compact_su2_projection",
    )


def apply_type_ix_compact_su2_transfer_coupling(
    structure: StructureConstants,
    *,
    transfer_T: np.ndarray,
    transfer_E: np.ndarray,
    transfer_B: np.ndarray,
    k_grid_mpc: np.ndarray,
    ell: np.ndarray,
    eta_grid_mpc: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, object]]:
    """Apply compact SU(2) Wigner-D transport for Type IX tensor rows."""

    t_arr = np.asarray(transfer_T, dtype=float).copy()
    e_arr = np.asarray(transfer_E, dtype=float).copy()
    b_arr = np.asarray(transfer_B, dtype=float).copy()
    (
        compact_phase,
        wigner_d_j2_profile,
        spectral_envelope,
        curvature_scale,
        anisotropy_split,
        status,
    ) = _type_ix_projection_profiles(
        structure,
        k_grid_mpc=np.asarray(k_grid_mpc, dtype=float),
        ell=np.asarray(ell, dtype=float),
        eta_grid_mpc=np.asarray(eta_grid_mpc, dtype=float),
    )
    if curvature_scale <= _SMALL_FLOAT:
        return t_arr, e_arr, b_arr, {
            "typeix_transport_status": status,
            "typeix_branch_flag": None,
            "typeix_curvature_scale": 0.0,
            "typeix_positive_axis_anisotropy_split": 0.0,
            "typeix_discrete_j": _TYPEIX_J,
            "typeix_spectral_eigenvalue_jj1": _TYPEIX_SPECTRAL_EIGENVALUE,
            "typeix_invariant_volume": _TYPEIX_INVARIANT_VOLUME,
            "typeix_wigner_d_j2_unit_amplitude": _TYPEIX_J2_UNIT_AMPLITUDE,
            "typeix_compact_phase_max": 0.0,
            "typeix_spectral_envelope_min": 1.0,
            "typeix_spectral_envelope_max": 1.0,
            "typeix_wigner_d_j2_profile_min": 1.0,
            "typeix_wigner_d_j2_profile_max": 1.0,
            "typeix_mode_mixing_norm": 0.0,
            "typeix_discrete_representation_labels": ("D^2_-2,0", "D^2_0,0", "D^2_+2,0"),
            "polarization_basis_transport": "identity",
        }

    before = np.concatenate(
        [t_arr[..., 1:].ravel(), e_arr[..., 1:].ravel(), b_arr[..., 1:].ravel()]
    )
    t_plus, t_minus = _rotate_and_attenuate_tensor_pair(
        t_arr[..., 1],
        t_arr[..., 2],
        compact_phase,
        spectral_envelope,
    )
    e_plus, e_minus = _rotate_and_attenuate_tensor_pair(
        e_arr[..., 1],
        e_arr[..., 2],
        compact_phase,
        spectral_envelope,
    )
    b_plus, b_minus = _rotate_and_attenuate_tensor_pair(
        b_arr[..., 1],
        b_arr[..., 2],
        compact_phase,
        spectral_envelope,
    )
    c2 = np.cos(2.0 * compact_phase)
    s2 = np.sin(2.0 * compact_phase)
    e_plus_spin = c2 * e_plus - s2 * b_plus
    b_plus_spin = s2 * e_plus + c2 * b_plus
    e_minus_spin = c2 * e_minus - s2 * b_minus
    b_minus_spin = s2 * e_minus + c2 * b_minus

    t_arr[..., 1] = t_plus
    t_arr[..., 2] = t_minus
    e_arr[..., 1] = e_plus_spin
    e_arr[..., 2] = e_minus_spin
    b_arr[..., 1] = b_plus_spin
    b_arr[..., 2] = b_minus_spin
    after = np.concatenate(
        [t_arr[..., 1:].ravel(), e_arr[..., 1:].ravel(), b_arr[..., 1:].ravel()]
    )
    scale = max(float(np.linalg.norm(before)), _SMALL_FLOAT)
    mixing_norm = float(np.linalg.norm(after - before) / scale)
    return t_arr, e_arr, b_arr, {
        "typeix_transport_status": status,
        "typeix_branch_flag": _TYPEIX_BRANCH_FLAG,
        "typeix_curvature_scale": float(curvature_scale),
        "typeix_positive_axis_anisotropy_split": float(anisotropy_split),
        "typeix_discrete_j": _TYPEIX_J,
        "typeix_spectral_eigenvalue_jj1": _TYPEIX_SPECTRAL_EIGENVALUE,
        "typeix_invariant_volume": _TYPEIX_INVARIANT_VOLUME,
        "typeix_wigner_d_j2_unit_amplitude": _TYPEIX_J2_UNIT_AMPLITUDE,
        "typeix_compact_phase_max": float(np.max(np.abs(compact_phase))),
        "typeix_spectral_envelope_min": float(np.min(spectral_envelope)),
        "typeix_spectral_envelope_max": float(np.max(spectral_envelope)),
        "typeix_wigner_d_j2_profile_min": float(np.min(wigner_d_j2_profile)),
        "typeix_wigner_d_j2_profile_max": float(np.max(wigner_d_j2_profile)),
        "typeix_mode_mixing_norm": mixing_norm,
        "typeix_discrete_representation_labels": ("D^2_-2,0", "D^2_0,0", "D^2_+2,0"),
        "typeix_polarization_basis_transport": "spin2_compact_su2_rotation",
        "polarization_basis_transport": "spin2_compact_su2_rotation",
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
    helical_phase, helical_pitch, helical_status = _helical_phase_profile(
        structure,
        eta_grid_mpc=eta_grid,
        eta_0_mpc=eta_0_mpc,
    )
    helical_transport_active = helical_pitch > _SMALL_FLOAT
    helical_c2 = np.cos(2.0 * helical_phase)
    helical_s2 = np.sin(2.0 * helical_phase)
    nil_shear, nil_phase, nil_scale, nil_status = _nilpotent_profile(
        structure,
        eta_grid_mpc=eta_grid,
        eta_0_mpc=eta_0_mpc,
    )
    nil_transport_active = nil_scale > _SMALL_FLOAT
    nil_c2 = np.cos(2.0 * nil_phase)
    nil_s2 = np.sin(2.0 * nil_phase)
    vi0_shear, vi0_scale, vi0_imbalance, vi0_status = _vi0_directional_profile(
        structure,
        eta_grid_mpc=eta_grid,
        eta_0_mpc=eta_0_mpc,
    )
    vi0_transport_active = vi0_scale > _SMALL_FLOAT
    (
        viih_phase,
        viih_attenuation,
        viih_pitch,
        viih_twist,
        viih_h_value,
        viih_status,
    ) = _viih_open_helical_profile(
        structure,
        eta_grid_mpc=eta_grid,
        eta_0_mpc=eta_0_mpc,
    )
    viih_transport_active = viih_pitch > _SMALL_FLOAT
    viih_c2 = np.cos(2.0 * viih_phase)
    viih_s2 = np.sin(2.0 * viih_phase)

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
        if nil_transport_active:
            _apply_nilpotent_source_coupling(temperature_sources, nil_shear)
            _apply_nilpotent_source_coupling(polarization_sources, nil_shear)
            _apply_nilpotent_source_coupling(b_sources, nil_shear)
        if vi0_transport_active:
            _apply_vi0_directional_source_coupling(
                temperature_sources,
                vi0_shear,
                vi0_imbalance,
            )
            _apply_vi0_directional_source_coupling(
                polarization_sources,
                vi0_shear,
                vi0_imbalance,
            )
            _apply_vi0_directional_source_coupling(
                b_sources,
                vi0_shear,
                vi0_imbalance,
            )
        if viih_transport_active:
            temperature_sources["m+2"], temperature_sources["m-2"] = (
                _rotate_and_attenuate_tensor_pair(
                    temperature_sources["m+2"],
                    temperature_sources["m-2"],
                    viih_phase,
                    viih_attenuation,
                )
            )
            polarization_sources["m+2"], polarization_sources["m-2"] = (
                _rotate_and_attenuate_tensor_pair(
                    polarization_sources["m+2"],
                    polarization_sources["m-2"],
                    viih_phase,
                    viih_attenuation,
                )
            )
            b_sources["m+2"], b_sources["m-2"] = _rotate_and_attenuate_tensor_pair(
                b_sources["m+2"],
                b_sources["m-2"],
                viih_phase,
                viih_attenuation,
            )
        if helical_transport_active:
            temperature_sources["m+2"], temperature_sources["m-2"] = _rotate_tensor_pair(
                temperature_sources["m+2"],
                temperature_sources["m-2"],
                helical_phase,
            )
            polarization_sources["m+2"], polarization_sources["m-2"] = _rotate_tensor_pair(
                polarization_sources["m+2"],
                polarization_sources["m-2"],
                helical_phase,
            )
            b_sources["m+2"], b_sources["m-2"] = _rotate_tensor_pair(
                b_sources["m+2"],
                b_sources["m-2"],
                helical_phase,
            )

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
                    np.trapezoid(
                        (
                            polarization_sources[mode] * helical_c2
                            - b_sources[mode] * helical_s2
                        )
                        * pol_kernel
                        if helical_transport_active and mode != "m0"
                        else polarization_sources[mode] * pol_kernel,
                        eta_grid,
                    )
                )
                if helical_transport_active and mode != "m0":
                    b_integrand = (
                        polarization_sources[mode] * helical_s2
                        + b_sources[mode] * helical_c2
                    ) * pol_kernel
                elif viih_transport_active and mode != "m0":
                    raw_E_row[imode] = float(
                        np.trapezoid(
                            (
                                polarization_sources[mode] * viih_c2
                                - b_sources[mode] * viih_s2
                            )
                            * pol_kernel,
                            eta_grid,
                        )
                    )
                    b_integrand = (
                        polarization_sources[mode] * viih_s2
                        + b_sources[mode] * viih_c2
                    ) * pol_kernel
                elif nil_transport_active and mode != "m0":
                    raw_E_row[imode] = float(
                        np.trapezoid(
                            (
                                polarization_sources[mode] * nil_c2
                                - b_sources[mode] * nil_s2
                            )
                            * pol_kernel,
                            eta_grid,
                        )
                    )
                    b_integrand = (
                        polarization_sources[mode] * nil_s2
                        + b_sources[mode] * nil_c2
                    ) * pol_kernel
                else:
                    b_integrand = b_sources[mode] * pol_kernel
                raw_B_row[imode] = float(np.trapezoid(b_integrand, eta_grid))

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

    helicity_mode_mixing_norm = 0.0
    if helical_transport_active:
        helicity_mode_mixing_norm = float(
            np.linalg.norm(raw_transfer_B[..., 1:])
            / max(float(np.linalg.norm(raw_transfer_E[..., 1:])), _SMALL_FLOAT)
        )
    nil_mode_mixing_norm = 0.0
    if nil_transport_active:
        nil_tensor = np.concatenate(
            [
                raw_transfer_T[..., 1:].ravel(),
                raw_transfer_E[..., 1:].ravel(),
                raw_transfer_B[..., 1:].ravel(),
            ]
        )
        nil_scalar = np.concatenate(
            [
                raw_transfer_T[..., 0].ravel(),
                raw_transfer_E[..., 0].ravel(),
            ]
        )
        nil_mode_mixing_norm = float(
            np.linalg.norm(nil_tensor)
            / max(float(np.linalg.norm(nil_scalar)), _SMALL_FLOAT)
        )
    vi0_mode_mixing_norm = 0.0
    if vi0_transport_active:
        vi0_tensor = np.concatenate(
            [
                raw_transfer_T[..., 1:].ravel(),
                raw_transfer_E[..., 1:].ravel(),
            ]
        )
        vi0_scalar = np.concatenate(
            [
                raw_transfer_T[..., 0].ravel(),
                raw_transfer_E[..., 0].ravel(),
            ]
        )
        vi0_mode_mixing_norm = float(
            np.linalg.norm(vi0_tensor)
            / max(float(np.linalg.norm(vi0_scalar)), _SMALL_FLOAT)
        )
    viih_mode_mixing_norm = 0.0
    if viih_transport_active:
        viih_tensor = np.concatenate(
            [
                raw_transfer_T[..., 1:].ravel(),
                raw_transfer_E[..., 1:].ravel(),
                raw_transfer_B[..., 1:].ravel(),
            ]
        )
        viih_mode_mixing_norm = float(
            np.linalg.norm(viih_tensor)
            / max(float(np.linalg.norm(raw_transfer_T[..., 0])), _SMALL_FLOAT)
        )
    polarization_basis_transport = "identity"
    if helical_transport_active:
        polarization_basis_transport = "spin2_helical_rotation"
    elif viih_transport_active:
        polarization_basis_transport = "spin2_open_helical_rotation"
    elif nil_transport_active:
        polarization_basis_transport = "spin2_nil_shear_rotation"
    elif vi0_transport_active:
        polarization_basis_transport = "parity_even_directional_transport"

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
        "helical_transport_status": helical_status,
        "helical_pitch": float(helical_pitch),
        "helical_phase_max": float(np.max(np.abs(helical_phase))),
        "polarization_basis_transport": (
            polarization_basis_transport
        ),
        "helicity_mode_mixing_norm": helicity_mode_mixing_norm,
        "nil_transport_status": nil_status,
        "nil_structure_scale": float(nil_scale),
        "nil_shear_max": float(np.max(np.abs(nil_shear))),
        "nil_phase_max": float(np.max(np.abs(nil_phase))),
        "nil_mode_mixing_norm": nil_mode_mixing_norm,
        "nil_polarization_basis_transport": (
            "spin2_nil_shear_rotation" if nil_transport_active else "identity"
        ),
        "vi0_transport_status": vi0_status,
        "vi0_structure_scale": float(vi0_scale),
        "vi0_directional_imbalance": float(vi0_imbalance),
        "vi0_shear_max": float(np.max(np.abs(vi0_shear))),
        "vi0_mode_mixing_norm": vi0_mode_mixing_norm,
        "vi0_polarization_basis_transport": (
            "parity_even_directional_transport"
            if vi0_transport_active
            else "identity"
        ),
        "viih_transport_status": viih_status,
        "viih_helical_pitch": float(viih_pitch),
        "viih_twist_scale": float(viih_twist),
        "viih_h_parameter": float(viih_h_value),
        "viih_phase_max": float(np.max(np.abs(viih_phase))),
        "viih_open_attenuation_min": float(np.min(viih_attenuation)),
        "viih_mode_mixing_norm": viih_mode_mixing_norm,
        "viih_polarization_basis_transport": (
            "spin2_open_helical_rotation"
            if viih_transport_active
            else "identity"
        ),
        "limber_eta_sp_sign": limber_eta_sp_sign,
        "limber_eta_sp_mpc": limber_eta_sp_mpc,
        "limber_temperature_proxy": limber_temperature_proxy,
        "limber_polarization_proxy": limber_polarization_proxy,
    }
