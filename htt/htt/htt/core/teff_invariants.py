"""Quadrature-free full-sky moments for T(n)/T0 = 1 + d.n + n.S.n.

Here d is dimensionless real 3-vector; S is dimensionless real symmetric
tracefree 3x3 temperature quadrupole (NOT the dimensional velocity shear).
The polynomial moment identity is exact. Physical positivity, transport
closure, instrument response and posterior calibration are separate inputs.
"""
from __future__ import annotations

import numpy as np


def _inputs(d, S):
    d = np.asarray(d, dtype=float)
    S = np.asarray(S, dtype=float)
    if d.shape != (3,) or S.shape != (3, 3):
        raise ValueError("Expected d shape (3,) and S shape (3,3)")
    if not np.all(np.isfinite(d)) or not np.all(np.isfinite(S)):
        raise ValueError("All coefficients must be finite")
    scale = max(1.0, float(np.linalg.norm(S)))
    if np.max(np.abs(S - S.T)) > 1e-12 * scale:
        raise ValueError("S must be symmetric")
    if abs(float(np.trace(S))) > 1e-12 * scale:
        raise ValueError("S must be tracefree")
    return d, S


def invariants(d, S):
    d, S = _inputs(d, S)
    S2 = S @ S
    return {
        "d2": float(d @ d),
        "trS2": float(np.trace(S2)),
        "dSd": float(d @ S @ d),
        "trS3": float(np.trace(S2 @ S)),
        "dS2d": float(d @ S2 @ d),
    }


def fourth_moment(d, S):
    """Return <(T/T0)^4> for normalized full-sphere measure dOmega/(4pi)."""
    v = invariants(d, S)
    d2, q2 = v["d2"], v["trS2"]
    return (1.0 + 2*d2 + (4/5)*q2 + (8/5)*v["dSd"]
            + (32/105)*v["trS3"] + d2*d2/5 + (4/35)*d2*q2
            + (16/35)*v["dS2d"] + (4/105)*q2*q2)


def temperature_variance(d, S):
    """Return exact <(T/T0 - 1)^2>."""
    v = invariants(d, S)
    return v["d2"]/3 + (2/15)*v["trS2"]


def fourth_moment_gradient(d, S):
    """Return grad_d and STF grad_S, with dF = gd.dd + tr(gS.T dS).

    Matrix gradient uses the Frobenius pairing on symmetric tracefree
    perturbations. Convert with an explicitly normalized basis before
    multiplying a covariance stored in five-coordinate quadrupole form.
    """
    d, S = _inputs(d, S)
    d2, q2 = float(d @ d), float(np.trace(S @ S))
    dd = np.outer(d, d)
    gd = (4*d + (16/5)*(S @ d) + (4/5)*d2*d
          + (8/35)*q2*d + (32/35)*(S @ S @ d))
    gS = ((8/5)*S + (8/5)*dd + (32/35)*(S @ S)
          + (8/35)*d2*S + (16/35)*(S @ dd + dd @ S)
          + (16/105)*q2*S)
    gS -= np.trace(gS)*np.eye(3)/3
    return gd, gS


def sufficient_positivity_margin(d, S):
    """Positive return guarantees T(n)>0; nonpositive is inconclusive."""
    d, S = _inputs(d, S)
    return 1.0 - float(np.linalg.norm(d)) - float(np.max(np.abs(np.linalg.eigvalsh(S))))


def bolometric_temperature_ratio(d, S, *, require_sufficient_positive=True):
    """Return T_bol/T0 = <(T/T0)^4>^(1/4).

    T_bol is a full-sky intensity-equivalent temperature, not the
    direction-dependent effective temperature. This default conservatively
    enforces a sufficient positivity domain; it is not a necessary test.
    """
    if require_sufficient_positive and sufficient_positivity_margin(d, S) <= 0:
        raise ValueError("Sufficient positivity certificate not satisfied")
    return fourth_moment(d, S)**0.25


def legacy_coefficients(A, W, Q, V):
    """Exact adapter to legacy TeffMomentMap.theta_field(A,W,Q,V)."""
    d = np.array([W, 0.0, A], dtype=float)
    S = np.array([[-Q/2, 0.0, V/2], [0.0, -Q/2, 0.0],
                  [V/2, 0.0, Q]], dtype=float)
    return d, S


def orthonormal_stf_basis():
    """Five Frobenius-orthonormal real STF matrices in a fixed basis."""
    E = np.zeros((5, 3, 3))
    E[0] = np.diag([1, -1, 0])/np.sqrt(2)
    E[1] = np.diag([1, 1, -2])/np.sqrt(6)
    for i, (a, b) in enumerate(((0, 1), (0, 2), (1, 2)), start=2):
        E[i, a, b] = E[i, b, a] = 1/np.sqrt(2)
    return E


def fourth_moment_coordinate_jacobian(d, S):
    """Gradient in [dx,dy,dz,s1,...,s5], S=sum(sj Ej) with basis above."""
    gd, gS = fourth_moment_gradient(d, S)
    return np.concatenate((gd, np.einsum("ij,kij->k", gS, orthonormal_stf_basis())))
