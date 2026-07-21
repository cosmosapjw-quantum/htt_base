"""PR-175: cross-engine Bianchi invariant mechanics from structure constants.

hypothesis_only / public_use=false / ceiling roadmap_rescue_v1:C2.

Two INDEPENDENT engines compute the spatial Ricci scalar of the eleven
canonical rational Bianchi representatives (unit left-invariant metric)
from the structure constants, and both are compared with the EXTERNAL
Ellis-MacCallum anchor formula
    R* = -(1/2)(n1^2+n2^2+n3^2) + (n1 n2 + n2 n3 + n3 n1) - 6 a^2.

Engine A: exact symbolic Koszul frame-connection chain (sympy rationals).
Engine B: numerical coordinate-realization chain — coframe from
ad-matrix exponentials in canonical coordinates of the second kind,
Christoffel symbols via COMPLEX-STEP first derivatives, curvature via
central differences of Christoffels.

Invariant values never rank types, never match an atlas entry, and never
identify a Bianchi family (kill condition). No production consumer.
"""

from __future__ import annotations

import json
from fractions import Fraction

import numpy as np
import sympy as sp

# Canonical rational representatives: Ellis-MacCallum n=diag(n1,n2,n3),
# a-vector a_b=(a,0,0); class B has n1=0.
CANONICAL_TYPES: dict[str, dict] = {
    "I": {"n": (0, 0, 0), "a": 0},
    "II": {"n": (1, 0, 0), "a": 0},
    "VI_0": {"n": (1, -1, 0), "a": 0},
    "VII_0": {"n": (1, 1, 0), "a": 0},
    "VIII": {"n": (1, 1, -1), "a": 0},
    "IX": {"n": (1, 1, 1), "a": 0},
    "V": {"n": (0, 0, 0), "a": 1},
    "IV": {"n": (0, 0, 1), "a": 1},
    "III": {"n": (0, 1, -1), "a": 1},
    "VI_h": {"n": (0, 1, -1), "a": Fraction(1, 2), "h": Fraction(-1, 4)},
    "VII_h": {"n": (0, 1, 1), "a": Fraction(1, 2), "h": Fraction(1, 4)},
}

PREREGISTERED_POINT = (0.3, -0.7, 0.51)
COMPLEX_STEP = 1.0e-200
CENTRAL_STEP = 1.0e-5
ENGINE_B_TOL = 1.0e-6


def anchor_ricci_scalar(name: str) -> Fraction:
    """External Ellis-MacCallum anchor formula (never derived in-engine)."""
    entry = CANONICAL_TYPES[name]
    n1, n2, n3 = (Fraction(v) for v in entry["n"])
    a = Fraction(entry["a"])
    return (
        -Fraction(1, 2) * (n1**2 + n2**2 + n3**2)
        + (n1 * n2 + n2 * n3 + n3 * n1)
        - 6 * a**2
    )


def structure_constants(name: str):
    """C^a_{bc} = eps_{bcd} n^{da} + a_b delta^a_c - a_c delta^a_b (exact)."""
    entry = CANONICAL_TYPES[name]
    n = sp.diag(*[sp.Rational(v) for v in entry["n"]])
    a_vec = [sp.Rational(entry["a"]), 0, 0]
    eps = [[[sp.Integer(int((i - j) * (j - k) * (k - i) / 2)) for k in range(3)]
            for j in range(3)] for i in range(3)]
    C = [[[sp.Integer(0)] * 3 for _ in range(3)] for _ in range(3)]
    for a in range(3):
        for b in range(3):
            for c in range(3):
                val = sum(eps[b][c][d] * n[d, a] for d in range(3))
                val += a_vec[b] * (1 if a == c else 0)
                val -= a_vec[c] * (1 if a == b else 0)
                C[a][b][c] = sp.nsimplify(val)
    return C


def engine_a_ricci_scalar(name: str) -> Fraction:
    """Exact Koszul frame chain: C -> Gamma -> Riemann -> Ricci -> R."""
    C = structure_constants(name)
    # Gamma^c_{ab} = (1/2)(C^c_{ab} - C^a_{bc} + C^b_{ca}) on the
    # orthonormal frame (indices raised/lowered with delta).
    G = [[[sp.Rational(1, 2) * (C[c][a][b] - C[a][b][c] + C[b][c][a])
           for b in range(3)] for a in range(3)] for c in range(3)]
    # R^d_{c ab} = Gamma^e_{bc} Gamma^d_{ae} - Gamma^e_{ac} Gamma^d_{be}
    #              - C^e_{ab} Gamma^d_{ec}
    ricci = sp.zeros(3, 3)
    for b in range(3):
        for c in range(3):
            total = sp.Integer(0)
            for a in range(3):
                term = sp.Integer(0)
                for e in range(3):
                    term += G[e][b][c] * G[a][a][e]
                    term -= G[e][a][c] * G[a][b][e]
                    term -= C[e][a][b] * G[a][e][c]
                total += term
            ricci[b, c] = sp.simplify(total)
    scalar = sp.simplify(sum(ricci[i, i] for i in range(3)))
    return Fraction(int(sp.fraction(scalar)[0]), int(sp.fraction(scalar)[1]))


def _ad_matrices(name: str) -> list[np.ndarray]:
    """(ad_a)^c_b = C^c_{ab} as float matrices."""
    C = structure_constants(name)
    mats = []
    for a in range(3):
        mat = np.zeros((3, 3))
        for c in range(3):
            for b in range(3):
                mat[c, b] = float(C[c][a][b])
        mats.append(mat)
    return mats


def _expm(mat: np.ndarray) -> np.ndarray:
    """Scaling-and-squaring Taylor expm (complex-safe, dependency-light)."""
    norm = np.max(np.abs(mat))
    squarings = max(0, int(np.ceil(np.log2(norm / 0.5))) if norm > 0.5 else 0)
    scaled = mat / (2**squarings)
    term = np.eye(3, dtype=mat.dtype)
    result = np.eye(3, dtype=mat.dtype)
    for k in range(1, 24):
        term = term @ scaled / k
        result = result + term
    for _ in range(squarings):
        result = result @ result
    return result


def _coframe(name: str, x: np.ndarray) -> np.ndarray:
    """W with theta^a = W[a, i] dx^i in canonical coordinates of the
    second kind: g = exp(x1 X1) exp(x2 X2) exp(x3 X3)."""
    ad1, ad2, ad3 = _ad_matrices(name)
    e3 = _expm(-x[2] * ad3)
    e2 = _expm(-x[1] * ad2)
    W = np.zeros((3, 3), dtype=np.result_type(x.dtype, float))
    W[:, 0] = (e3 @ e2)[:, 0]
    W[:, 1] = e3[:, 1]
    W[:, 2] = np.array([0.0, 0.0, 1.0], dtype=W.dtype)
    return W


def _metric(name: str, x: np.ndarray) -> np.ndarray:
    W = _coframe(name, x)
    return W.T @ W


def _metric_derivative(name: str, x: np.ndarray) -> np.ndarray:
    """dg[k, i, j] = d g_ij / d x_k via complex step (machine exact)."""
    dg = np.zeros((3, 3, 3))
    for k in range(3):
        xc = x.astype(complex)
        xc[k] += 1j * COMPLEX_STEP
        dg[k] = np.imag(_metric(name, xc)) / COMPLEX_STEP
    return dg


def _christoffel(name: str, x: np.ndarray) -> np.ndarray:
    g = _metric(name, x.astype(float))
    ginv = np.linalg.inv(g)
    dg = _metric_derivative(name, x)
    gamma = np.zeros((3, 3, 3))
    for i in range(3):
        for j in range(3):
            for k in range(3):
                gamma[i, j, k] = 0.5 * sum(
                    ginv[i, m] * (dg[j, m, k] + dg[k, m, j] - dg[m, j, k])
                    for m in range(3)
                )
    return gamma


def engine_b_ricci_scalar(name: str, point=PREREGISTERED_POINT) -> float:
    """Numerical coordinate chain, independent of the Koszul algebra."""
    x0 = np.array(point, dtype=float)
    dgamma = np.zeros((3, 3, 3, 3))
    for k in range(3):
        xp = x0.copy()
        xm = x0.copy()
        xp[k] += CENTRAL_STEP
        xm[k] -= CENTRAL_STEP
        dgamma[k] = (
            _christoffel(name, xp) - _christoffel(name, xm)
        ) / (2 * CENTRAL_STEP)
    gamma = _christoffel(name, x0)
    ricci = np.zeros((3, 3))
    for j in range(3):
        for l_idx in range(3):
            total = 0.0
            for k in range(3):
                total += dgamma[k][k][l_idx][j] - dgamma[l_idx][k][k][j]
                for m in range(3):
                    total += (
                        gamma[k, k, m] * gamma[m, l_idx, j]
                        - gamma[k, l_idx, m] * gamma[m, k, j]
                    )
            ricci[j, l_idx] = total
    ginv = np.linalg.inv(_metric(name, x0))
    return float(np.sum(ginv * ricci))


def run_oracle() -> dict:
    rows = {}
    ok = True
    for name in CANONICAL_TYPES:
        anchor = anchor_ricci_scalar(name)
        exact = engine_a_ricci_scalar(name)
        numeric = engine_b_ricci_scalar(name)
        engines_agree = abs(numeric - float(exact)) <= ENGINE_B_TOL
        anchor_match = exact == anchor
        ok = ok and engines_agree and anchor_match
        rows[name] = {
            "anchor": str(anchor),
            "engine_a_exact": str(exact),
            "engine_b_numeric": numeric,
            "engine_gap_abs": abs(numeric - float(exact)),
            "engines_agree": engines_agree,
            "anchor_match": anchor_match,
        }
    return {
        "schema": "htt.pr175.invariant_oracle.v1",
        "types": rows,
        "all_consistent": ok,
        "interpretation": (
            "Cross-engine geometry mechanics on canonical representatives; "
            "invariants never rank, atlas-match, or identify a Bianchi "
            "family."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run_oracle(), sort_keys=True, default=float))
