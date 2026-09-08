"""Map-free l=2/3 real-harmonic to observer-space Cartesian STF bridge.

The bridge consumes an exact :class:`ObservableIrrepCarrier`.  It cannot
construct a direction, a tensor, or a physical state from a scalar feature.
The formulas use orthonormal Condon--Shortley harmonics and the real-map
convention ``a_l0 Y_l0 + 2 Re(a_lm Y_lm)``.
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Sequence

import numpy as np

from common.observable_irrep_state import (
    ObservableIrrepCarrier,
    ObservableIrrepState,
    build_cartesian_stf_irrep_block,
    build_real_harmonic_irrep_block,
)


OBSERVABLE_STF_BASIS = "CARTESIAN_STF2_STF3_GALACTIC_CONDON_SHORTLEY_V1"
STF2_COMPONENT_LAYOUT = ("Qxx", "Qyy", "Qxy", "Qxz", "Qyz")
STF3_COMPONENT_LAYOUT = (
    "Oxxx",
    "Oxxy",
    "Oxxz",
    "Oxyy",
    "Oxyz",
    "Oyyy",
    "Oyyz",
)
ROUNDTRIP_ATOL = 2.0e-13


def _projection_identity() -> str:
    payload = {
        "basis": OBSERVABLE_STF_BASIS,
        "convention": "ORTHONORMAL_CONDON_SHORTLEY_REAL_MAP",
        "harmonic_layout": "m0_real_then_m1..mell_real_imag",
        "stf2_layout": list(STF2_COMPONENT_LAYOUT),
        "stf3_layout": list(STF3_COMPONENT_LAYOUT),
        "version": 1,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
        "ascii"
    )
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


PROJECTION_IDENTITY = _projection_identity()


def _vector(value: object, dimension: int, *, label: str) -> np.ndarray:
    try:
        array = np.asarray(value, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a finite real vector") from exc
    if array.shape != (dimension,) or not np.all(np.isfinite(array)):
        raise ValueError(f"{label} must be a finite real vector of length {dimension}")
    return array


def stf2_components_to_tensor(components: object) -> np.ndarray:
    """Decode the registered five-coordinate symmetric trace-free layout."""

    qxx, qyy, qxy, qxz, qyz = _vector(components, 5, label="STF2 components")
    return np.asarray(
        [
            [qxx, qxy, qxz],
            [qxy, qyy, qyz],
            [qxz, qyz, -qxx - qyy],
        ],
        dtype=np.float64,
    )


def stf2_tensor_to_components(tensor: object) -> np.ndarray:
    """Encode a symmetric trace-free rank-two tensor without a trace slot."""

    array = np.asarray(tensor, dtype=np.float64)
    if array.shape != (3, 3) or not np.all(np.isfinite(array)):
        raise ValueError("STF2 tensor must be a finite 3x3 array")
    scale = max(1.0, float(np.max(np.abs(array))))
    if not np.allclose(array, array.T, rtol=0.0, atol=ROUNDTRIP_ATOL * scale):
        raise ValueError("STF2 tensor must be symmetric")
    if abs(float(np.trace(array))) > ROUNDTRIP_ATOL * scale:
        raise ValueError("STF2 tensor must be trace-free")
    return np.asarray(
        [array[0, 0], array[1, 1], array[0, 1], array[0, 2], array[1, 2]],
        dtype=np.float64,
    )


def stf3_components_to_tensor(components: object) -> np.ndarray:
    """Decode seven independent components into a symmetric STF rank-three tensor."""

    oxxx, oxxy, oxxz, oxyy, oxyz, oyyy, oyyz = _vector(
        components, 7, label="STF3 components"
    )
    oxzz = -oxxx - oxyy
    oyzz = -oxxy - oyyy
    ozzz = -oxxz - oyyz
    output = np.empty((3, 3, 3), dtype=np.float64)
    values = {
        (0, 0, 0): oxxx,
        (0, 0, 1): oxxy,
        (0, 0, 2): oxxz,
        (0, 1, 1): oxyy,
        (0, 1, 2): oxyz,
        (0, 2, 2): oxzz,
        (1, 1, 1): oyyy,
        (1, 1, 2): oyyz,
        (1, 2, 2): oyzz,
        (2, 2, 2): ozzz,
    }
    for i in range(3):
        for j in range(3):
            for k in range(3):
                output[i, j, k] = values[tuple(sorted((i, j, k)))]
    return output


def stf3_tensor_to_components(tensor: object) -> np.ndarray:
    """Encode a fully symmetric trace-free rank-three Cartesian tensor."""

    array = np.asarray(tensor, dtype=np.float64)
    if array.shape != (3, 3, 3) or not np.all(np.isfinite(array)):
        raise ValueError("STF3 tensor must be a finite 3x3x3 array")
    scale = max(1.0, float(np.max(np.abs(array))))
    for permutation in ((1, 0, 2), (2, 1, 0), (0, 2, 1), (2, 0, 1), (1, 2, 0)):
        if not np.allclose(
            array,
            np.transpose(array, permutation),
            rtol=0.0,
            atol=ROUNDTRIP_ATOL * scale,
        ):
            raise ValueError("STF3 tensor must be fully symmetric")
    trace = np.einsum("iik->k", array)
    if float(np.max(np.abs(trace))) > ROUNDTRIP_ATOL * scale:
        raise ValueError("STF3 tensor must be trace-free on every index pair")
    return np.asarray(
        [
            array[0, 0, 0],
            array[0, 0, 1],
            array[0, 0, 2],
            array[0, 1, 1],
            array[0, 1, 2],
            array[1, 1, 1],
            array[1, 1, 2],
        ],
        dtype=np.float64,
    )


def real_harmonic_l2_to_stf(components: object) -> np.ndarray:
    """Project ``(a20, Re a21, Im a21, Re a22, Im a22)`` to ``Q_ab``."""

    a20, a21r, a21i, a22r, a22i = _vector(
        components, 5, label="l=2 real harmonic block"
    )
    a = math.sqrt(5.0 / (16.0 * math.pi)) * a20
    c = math.sqrt(15.0 / (32.0 * math.pi))
    d = math.sqrt(15.0 / (8.0 * math.pi))
    return stf2_components_to_tensor(
        (
            -a + 2.0 * c * a22r,
            -a - 2.0 * c * a22r,
            -2.0 * c * a22i,
            -d * a21r,
            d * a21i,
        )
    )


def stf2_to_real_harmonic(tensor: object) -> np.ndarray:
    """Invert :func:`real_harmonic_l2_to_stf` on the registered STF space."""

    qxx, qyy, qxy, qxz, qyz = stf2_tensor_to_components(tensor)
    a = math.sqrt(5.0 / (16.0 * math.pi))
    c = math.sqrt(15.0 / (32.0 * math.pi))
    d = math.sqrt(15.0 / (8.0 * math.pi))
    return np.asarray(
        [
            -(qxx + qyy) / (2.0 * a),
            -qxz / d,
            qyz / d,
            (qxx - qyy) / (4.0 * c),
            -qxy / (2.0 * c),
        ],
        dtype=np.float64,
    )


def real_harmonic_l3_to_stf(components: object) -> np.ndarray:
    """Project the seven registered l=3 real harmonic coordinates to ``O_abc``."""

    a30, a31r, a31i, a32r, a32i, a33r, a33i = _vector(
        components, 7, label="l=3 real harmonic block"
    )
    e = math.sqrt(7.0 / (16.0 * math.pi))
    f = math.sqrt(21.0 / (64.0 * math.pi))
    g = math.sqrt(105.0 / (32.0 * math.pi))
    h = math.sqrt(35.0 / (64.0 * math.pi))
    return stf3_components_to_tensor(
        (
            2.0 * f * a31r - 2.0 * h * a33r,
            -(2.0 / 3.0) * f * a31i + 2.0 * h * a33i,
            -e * a30 + (2.0 / 3.0) * g * a32r,
            (2.0 / 3.0) * f * a31r + 2.0 * h * a33r,
            -(2.0 / 3.0) * g * a32i,
            -2.0 * f * a31i - 2.0 * h * a33i,
            -e * a30 - (2.0 / 3.0) * g * a32r,
        )
    )


def stf3_to_real_harmonic(tensor: object) -> np.ndarray:
    """Invert :func:`real_harmonic_l3_to_stf` on the registered STF space."""

    oxxx, oxxy, oxxz, oxyy, oxyz, oyyy, oyyz = stf3_tensor_to_components(
        tensor
    )
    e = math.sqrt(7.0 / (16.0 * math.pi))
    f = math.sqrt(21.0 / (64.0 * math.pi))
    g = math.sqrt(105.0 / (32.0 * math.pi))
    h = math.sqrt(35.0 / (64.0 * math.pi))
    return np.asarray(
        [
            -(oxxz + oyyz) / (2.0 * e),
            3.0 * (oxxx + oxyy) / (8.0 * f),
            -3.0 * (oxxy + oyyy) / (8.0 * f),
            3.0 * (oxxz - oyyz) / (4.0 * g),
            -3.0 * oxyz / (2.0 * g),
            3.0 * (oxyy - oxxx / 3.0) / (8.0 * h),
            3.0 * (oxxy - oyyy / 3.0) / (8.0 * h),
        ],
        dtype=np.float64,
    )


def project_planck_carrier_to_observable_irreps(
    carrier: ObservableIrrepCarrier,
) -> ObservableIrrepState:
    """Project one exact retained carrier row into typed observer-space Q/O blocks."""

    if type(carrier) is not ObservableIrrepCarrier:
        raise TypeError("carrier must be an exact ObservableIrrepCarrier")
    # Accessing the seal rejects mutated carrier content before projection.
    carrier.content_id
    harmonic_l2 = build_real_harmonic_irrep_block(carrier=carrier, ell=2)
    harmonic_l3 = build_real_harmonic_irrep_block(carrier=carrier, ell=3)
    q_tensor = real_harmonic_l2_to_stf(harmonic_l2.components)
    o_tensor = real_harmonic_l3_to_stf(harmonic_l3.components)
    q_block = build_cartesian_stf_irrep_block(
        parent=harmonic_l2,
        components=tuple(stf2_tensor_to_components(q_tensor)),
        basis=OBSERVABLE_STF_BASIS,
        projection_identity=PROJECTION_IDENTITY,
    )
    o_block = build_cartesian_stf_irrep_block(
        parent=harmonic_l3,
        components=tuple(stf3_tensor_to_components(o_tensor)),
        basis=OBSERVABLE_STF_BASIS,
        projection_identity=PROJECTION_IDENTITY,
    )
    support = q_block.support
    return ObservableIrrepState(
        blocks=(q_block, o_block),
        frame=support.frame,
        basis=support.basis,
        units=support.units,
        source_identity=support.source_identity,
        operator_identity=support.operator_identity,
        row_identity=support.row_identity,
    )


__all__ = [
    "OBSERVABLE_STF_BASIS",
    "PROJECTION_IDENTITY",
    "ROUNDTRIP_ATOL",
    "STF2_COMPONENT_LAYOUT",
    "STF3_COMPONENT_LAYOUT",
    "project_planck_carrier_to_observable_irreps",
    "real_harmonic_l2_to_stf",
    "real_harmonic_l3_to_stf",
    "stf2_components_to_tensor",
    "stf2_tensor_to_components",
    "stf2_to_real_harmonic",
    "stf3_components_to_tensor",
    "stf3_tensor_to_components",
    "stf3_to_real_harmonic",
]
