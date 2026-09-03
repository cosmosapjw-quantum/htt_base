"""Scale-aware generic SO(3) orbit completion for an actual STF2/STF3 pair.

This is finite-dimensional algebra, not a physical response or likelihood.
The sixteen contractions add information relative to ordinary power/bispectrum,
not relative to their input Q/O tensors. Nonfree or ill-conditioned strata are
reported as unavailable; no axis or missing tensor is manufactured.
"""
from __future__ import annotations

from itertools import combinations_with_replacement, permutations
import math
from typing import Mapping

import numpy as np

SCHEMA = "MES_SCALED_KRYLOV16_V1"
TRIPLES = tuple(combinations_with_replacement(range(3), 3))
DEFAULT_CONDITION_LIMIT = 1.0e6
DEFAULT_ATOL = 1.0e-10


class OrbitInputError(ValueError):
    """The supplied numerical object violates its declared representation."""


class OrbitChartUnavailable(OrbitInputError):
    """Original tensors must be retained; this chart is not admissible."""


def _real_array(value: object, shape: tuple[int, ...], name: str) -> np.ndarray:
    a = np.asarray(value)
    if a.shape != shape or a.dtype.kind not in "fiu":
        raise OrbitInputError(f"{name}: expected a real numeric array {shape}")
    a = np.asarray(a, dtype=np.float64)
    if not np.all(np.isfinite(a)):
        raise OrbitInputError(f"{name}: nonfinite input")
    return a


def _unit(a: np.ndarray, name: str) -> tuple[np.ndarray, float]:
    scale = float(np.max(np.abs(a)))
    if scale == 0.0:
        raise OrbitChartUnavailable(f"{name}: zero tensor has no unit-shape chart")
    z = a / scale
    n = float(np.sqrt(np.sum(z * z)))
    amplitude = scale * n
    if not math.isfinite(amplitude) or amplitude <= 0:
        raise OrbitInputError(f"{name}: norm is outside representable range")
    return z / n, amplitude


def _pair(q: object, o: object) -> tuple[np.ndarray, np.ndarray, float, float]:
    q, qn = _unit(_real_array(q, (3, 3), "Q"), "Q")
    o, on = _unit(_real_array(o, (3, 3, 3), "O"), "O")
    if (
        np.max(np.abs(q - q.T)) > DEFAULT_ATOL
        or abs(float(np.trace(q))) > DEFAULT_ATOL
    ):
        raise OrbitInputError("Q is not symmetric trace-free")
    if any(
        np.max(np.abs(o - o.transpose(p))) > DEFAULT_ATOL
        for p in permutations(range(3))
    ):
        raise OrbitInputError("O is not fully symmetric")
    if np.max(np.abs(np.einsum("iik->k", o))) > DEFAULT_ATOL:
        raise OrbitInputError("O is not trace-free")
    return q, o, qn, on


def _condition_limit(value: float) -> float:
    if (
        isinstance(value, bool)
        or not math.isfinite(float(value))
        or float(value) <= 1
    ):
        raise OrbitInputError(
            "condition_limit must be finite and greater than one"
        )
    return float(value)


def krylov16(
    q: object,
    o: object,
    *,
    condition_limit: float = DEFAULT_CONDITION_LIMIT,
) -> dict:
    """Return 16 contractions of unit Q/O plus their two positive amplitudes.

    Normalization is explicitly invertible. The numerical signature is not
    mislabeled as sixteen raw dimensional polynomial values.
    """
    limit = _condition_limit(condition_limit)
    q, o, qn, on = _pair(q, o)
    v = np.einsum("ijk,jk->i", o, q)
    k = np.column_stack((v, q @ v, q @ q @ v))
    sv = np.linalg.svd(k, compute_uv=False)
    if sv[0] == 0 or sv[-1] <= sv[0] / limit:
        raise OrbitChartUnavailable(
            "K=[v,Qv,Q^2v] is singular or outside the fixed conditioning domain"
        )
    s2 = float(np.sum(q * q))
    s3 = float(np.trace(q @ q @ q))
    moments = [
        float(v @ v),
        float(v @ q @ v),
        float(v @ q @ q @ v),
    ]
    contractions = [
        float(np.einsum("abc,a,b,c", o, k[:, i], k[:, j], k[:, l]))
        for i, j, l in TRIPLES
    ]
    return {
        "schema": SCHEMA,
        "action_group": "SO3",
        "q_frobenius_amplitude": qn,
        "o_frobenius_amplitude": on,
        "normalization": "CONTRACTIONS_OF_UNIT_FROBENIUS_Q_AND_O",
        "values": [
            s2,
            s3,
            *moments,
            float(np.linalg.det(k)),
            *contractions,
        ],
        "triple_order": [list(t) for t in TRIPLES],
        "condition_limit": limit,
        "measured_k_condition": float(sv[0] / sv[-1]),
        "claim": (
            "GENERIC_OBSERVABLE_ORBIT_REPRESENTATION_"
            "NOT_PHYSICAL_SOURCE_IDENTIFICATION"
        ),
    }


def reconstruct_krylov16(
    packet: Mapping[str, object],
) -> tuple[np.ndarray, np.ndarray]:
    """Reconstruct one proper-oriented representative, not an absolute sky frame."""
    if packet.get("schema") != SCHEMA or packet.get("action_group") != "SO3":
        raise OrbitInputError("wrong schema or rotation group")
    if packet.get("normalization") != "CONTRACTIONS_OF_UNIT_FROBENIUS_Q_AND_O":
        raise OrbitInputError("normalization identity mismatch")
    if packet.get("triple_order") != [list(t) for t in TRIPLES]:
        raise OrbitInputError("triple ordering mismatch")
    values = _real_array(packet.get("values"), (16,), "signature")
    limit = _condition_limit(
        packet.get("condition_limit", DEFAULT_CONDITION_LIMIT)
    )
    qn = float(packet["q_frobenius_amplitude"])
    on = float(packet["o_frobenius_amplitude"])
    if not all(math.isfinite(x) and x > 0 for x in (qn, on)):
        raise OrbitInputError("amplitudes must be finite and positive")
    s2, s3, m0, m1, m2, kap = values[:6]
    if abs(s2 - 1.0) > DEFAULT_ATOL or m0 <= 0 or kap == 0:
        raise OrbitChartUnavailable(
            "signature is outside the normalized cyclic chart"
        )
    if 6 * s3 * s3 > s2**3 + DEFAULT_ATOL:
        raise OrbitInputError("STF characteristic discriminant is negative")
    m3 = s2 * m1 / 2 + s3 * m0 / 3
    m4 = s2 * m2 / 2 + s3 * m1 / 3
    gram = np.array([
        [m0, m1, m2],
        [m1, m2, m3],
        [m2, m3, m4],
    ])
    eig = np.linalg.eigvalsh(gram)
    if eig[-1] <= 0 or eig[0] <= eig[-1] / limit**2:
        raise OrbitChartUnavailable(
            "Gram matrix is nonpositive or ill-conditioned"
        )
    if not np.isclose(
        np.linalg.det(gram),
        kap * kap,
        rtol=1e-7,
        atol=1e-14 * max(m0, 1e-30) ** 3,
    ):
        raise OrbitInputError("Gram determinant and oriented volume disagree")
    basis = np.linalg.cholesky(gram).T
    if kap < 0:
        basis[2] *= -1
    inverse = np.linalg.inv(basis)
    companion = np.array([
        [0.0, 0.0, s3 / 3],
        [1.0, 0.0, s2 / 2],
        [0.0, 1.0, 0.0],
    ])
    q = basis @ companion @ inverse
    tc = np.zeros((3, 3, 3))
    for triple, value in zip(TRIPLES, values[6:]):
        for perm in set(permutations(triple)):
            tc[perm] = value
    o = np.einsum("ia,jb,kc,ijk->abc", inverse, inverse, inverse, tc)
    # Do not repair an inconsistent signature by silently projecting it.
    if np.max(np.abs(q - q.T)) > 1e-7 or abs(float(np.trace(q))) > 1e-7:
        raise OrbitInputError("reconstructed Q fails symmetry/trace closure")
    if np.max(np.abs(np.einsum("iik->k", o))) > 1e-7:
        raise OrbitInputError("reconstructed O fails trace closure")
    if not np.isclose(np.sum(q*q), 1.0, rtol=1e-7, atol=1e-10):
        raise OrbitInputError("reconstructed Q normalization mismatch")
    if not np.isclose(np.sum(o*o), 1.0, rtol=1e-7, atol=1e-10):
        raise OrbitInputError("reconstructed O normalization mismatch")

    # The decoded trilinear coordinates must lie in the image of the Krylov
    # construction.  Existing moment checks fix B=[v,Qv,Q^2v], but without
    # this syzygy a forged STF3 tensor can preserve those moments while using
    # a different actual contraction v=O:Q.
    reconstructed_v = np.einsum("ijk,jk->i", o, q)
    expected_v = basis[:, 0]
    v_scale = max(
        float(np.linalg.norm(reconstructed_v)),
        float(np.linalg.norm(expected_v)),
        1.0,
    )
    if float(np.linalg.norm(reconstructed_v - expected_v)) > (
        1e-7 * v_scale + 1e-10
    ):
        raise OrbitInputError(
            "reconstructed O:Q vector disagrees with Krylov moment frame"
        )
    return q * qn, o * on


def ordinary_power_bispectrum(q: object, o: object) -> np.ndarray:
    """Four ordinary quadratic/cubic invariants; deliberately not separating."""
    q = _real_array(q, (3, 3), "Q")
    o = _real_array(o, (3, 3, 3), "O")
    return np.array([
        np.sum(q*q),
        np.sum(o*o),
        np.trace(q@q@q),
        np.einsum("ij,ikl,jkl", q, o, o),
    ])


def pstf_mes_ceilings(
    *,
    c2: float,
    c3: float,
    t0: float,
    epsilon1: float,
) -> dict:
    """Algebraic original-PSTF MES functions; physical premises are caller-owned.

    C_l must be in the square of the same temperature unit used for T0.
    epsilon1 is explicitly a residual PSTF dipole norm, not an observed dipole.
    """
    vals = (c2, c3, t0, epsilon1)
    if any(
        isinstance(v, bool) or not math.isfinite(float(v))
        for v in vals
    ):
        raise OrbitInputError("MES inputs must be finite real numbers")
    c2, c3, t0, epsilon1 = map(float, vals)
    if c2 < 0 or c3 < 0 or t0 <= 0 or epsilon1 < 0:
        raise OrbitInputError(
            "C_l and residual norm must be nonnegative and T0 positive"
        )
    eps2 = math.sqrt(75 * c2 / (8 * math.pi)) / t0
    eps3 = math.sqrt(245 * c3 / (8 * math.pi)) / t0
    bs = (5 / 3) * epsilon1 + 3 * eps2 + (3 / 7) * eps3
    bw = (10 / 3) * epsilon1 + (2 / 15) * eps2
    return {
        "epsilon1_pstf": epsilon1,
        "epsilon2_pstf": eps2,
        "epsilon3_pstf": eps3,
        "U_sigma": 1.5 * bs * bs,
        "U_omega": 1.5 * bw * bw,
        "role": (
            "CONDITIONAL_ONE_WAY_PSTF_NORM_FUNCTION_"
            "NOT_AN_INDEPENDENT_OBSERVATION"
        ),
    }
