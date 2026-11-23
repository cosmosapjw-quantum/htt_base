"""Finite-dimensional moving Mori--Zwanzig projections (R101).

For a DECLARED evolution X'=A(s)X and a full-rank basis V(s), retain
a=L X, L=(V* W V)^-1 V* W, and q=(I-VL)X.  Here * means Hermitian
transpose. s may be time or another evolution coordinate with a supplied
generator. A family of fitted distributions alone supplies no such generator.

All derivatives use the same coordinate s; A and the connection have units
1/[s], and the memory kernel has units 1/[s]^2. No Markov, positivity, or
physical cosmological qualification follows from this linear decomposition.
No covariance jitter or silent rank truncation is performed.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
from scipy.integrate import solve_ivp
from scipy.linalg import cho_factor, cho_solve


@dataclass(frozen=True)
class ProjectionBlocks:
    basis: np.ndarray
    left: np.ndarray
    projector: np.ndarray
    complement: np.ndarray
    left_derivative: np.ndarray
    complement_derivative: np.ndarray
    resolved: np.ndarray
    return_from_hidden: np.ndarray
    drive_hidden: np.ndarray
    hidden: np.ndarray
    gram_condition: float


def _finite_matrix(value, name, shape=None):
    a = np.asarray(value)
    if a.ndim != 2 or (shape is not None and a.shape != shape):
        raise ValueError(f"{name} has invalid shape {a.shape}; expected {shape}")
    if not np.issubdtype(a.dtype, np.number) or not np.all(np.isfinite(a)):
        raise ValueError(f"{name} must be a finite numerical matrix")
    return np.asarray(a, dtype=np.result_type(a, np.float64))


def projection_blocks(generator, basis, basis_derivative, weight=None,
                      weight_derivative=None, *, max_condition=1e12):
    """Construct exact coupled resolved/hidden equations, including W' and V'.

    W must be Hermitian positive definite on the full finite state space.
    For singular empirical covariances choose their qualified positive support
    BEFORE calling; changing rank requires a new chart, not a pseudoinverse.
    max_condition is a numerical chart limit, not a physical acceptance gate.
    """
    v = _finite_matrix(basis, "basis")
    n, k = v.shape
    if not (0 < k <= n):
        raise ValueError("basis must have 1 <= columns <= rows")
    a = _finite_matrix(generator, "generator", (n, n))
    dv = _finite_matrix(basis_derivative, "basis_derivative", (n, k))
    w = np.eye(n) if weight is None else _finite_matrix(weight, "weight", (n, n))
    dw = np.zeros((n, n)) if weight_derivative is None else _finite_matrix(weight_derivative, "weight_derivative", (n, n))
    for name, mat in (("weight", w), ("weight_derivative", dw)):
        if not np.allclose(mat, mat.conj().T, rtol=1e-12, atol=1e-14):
            raise ValueError(f"{name} must be Hermitian")
    if not np.isfinite(max_condition) or max_condition < 1:
        raise ValueError("max_condition must be finite and >= 1")
    try:
        cho_factor(w, lower=True, check_finite=False)
        g = v.conj().T @ w @ v
        factor = cho_factor(g, lower=True, check_finite=False)
    except np.linalg.LinAlgError as exc:
        raise ValueError("positive weight and full-rank basis required") from exc
    condition = float(np.linalg.cond(g))
    if not np.isfinite(condition) or condition > max_condition:
        raise ValueError(f"basis Gram matrix exceeds chart condition limit: {condition}")
    left = cho_solve(factor, v.conj().T @ w, check_finite=False)
    dg = dv.conj().T @ w @ v + v.conj().T @ dw @ v + v.conj().T @ w @ dv
    dl = cho_solve(factor, dv.conj().T @ w + v.conj().T @ dw - dg @ left,
                   check_finite=False)
    p = v @ left
    q = np.eye(n) - p
    dq = -(dv @ left + v @ dl)
    return ProjectionBlocks(v, left, p, q, dl, dq,
                            left @ a @ v - left @ dv,
                            dl + left @ a,
                            q @ a @ v - q @ dv,
                            dq + q @ a, condition)


BlockFunction = Callable[[float], ProjectionBlocks]


def _propagate_hidden(end, start, initial, blocks: BlockFunction, rtol, atol):
    if not np.isfinite(start) or not np.isfinite(end) or end < start:
        raise ValueError("causal finite end >= start required")
    if not np.isfinite(rtol) or not np.isfinite(atol) or rtol <= 0 or atol <= 0:
        raise ValueError("finite positive integration tolerances required")
    # A callable may become complex after the initial point even if its initial
    # matrix and state are real. A real IVP dtype would silently discard phases.
    value = np.asarray(initial, dtype=np.complex128)
    if not np.all(np.isfinite(value)):
        raise ValueError("initial hidden state must be finite")
    if end == start:
        return value.copy()
    shape = value.shape
    def rhs(s, flat):
        return (blocks(s).hidden @ flat.reshape(shape)).ravel()
    sol = solve_ivp(rhs, (start, end), value.ravel(), method="DOP853", rtol=rtol, atol=atol)
    if not sol.success or not np.all(np.isfinite(sol.y[:, -1])):
        raise RuntimeError(f"hidden propagation failed: {sol.message}")
    return sol.y[:, -1].reshape(shape)


def memory_kernel(end: float, start: float, blocks: BlockFunction,
                  *, rtol=1e-10, atol=1e-12):
    """K(end,start)=(L'+LA)_end U_Q(end,start)(QAV-QV')_start.

    Only n*k driven columns are propagated, not an n*n fundamental matrix.
    This computes an exact finite-model kernel up to IVP integration error.
    """
    initial = blocks(start).drive_hidden
    propagated = _propagate_hidden(end, start, initial, blocks, rtol, atol)
    return blocks(end).return_from_hidden @ propagated


def initial_hidden_force(end: float, start: float, initial_state,
                         blocks: BlockFunction, *, rtol=1e-10, atol=1e-12):
    """Retain the generally nonzero initial hidden-state term in the GLE."""
    b = blocks(start)
    x = np.asarray(initial_state)
    if x.shape != (b.basis.shape[0],) or not np.all(np.isfinite(x)):
        raise ValueError("initial_state must be a finite state vector")
    q0 = b.complement @ x
    q = _propagate_hidden(end, start, q0, blocks, rtol, atol)
    return blocks(end).return_from_hidden @ q


def integrate_split(grid, initial_state, blocks: BlockFunction, *, rtol=1e-10, atol=1e-12):
    """Solve the exact resolved+explicit auxiliary realization on a fixed chart.

    This retains n hidden coordinates with constraints; it is a correctness
    reference/auxiliary realization, not an advertised dimension reduction.
    Returns (resolved[k,m], hidden[n,m], reconstructed[n,m]).
    """
    times = np.asarray(grid, dtype=float)
    if times.ndim != 1 or len(times) < 2 or not np.all(np.isfinite(times)) or np.any(np.diff(times) <= 0):
        raise ValueError("strictly increasing finite grid of at least two points required")
    if not np.isfinite(rtol) or not np.isfinite(atol) or rtol <= 0 or atol <= 0:
        raise ValueError("finite positive integration tolerances required")
    first = blocks(float(times[0]))
    x0 = np.asarray(initial_state)
    n, k = first.basis.shape
    if x0.shape != (n,) or not np.all(np.isfinite(x0)):
        raise ValueError("initial_state must be a finite state vector")
    y0 = np.asarray(np.concatenate((first.left @ x0, first.complement @ x0)),
                    dtype=np.complex128)
    def rhs(s, y):
        b = blocks(s)
        if b.basis.shape != (n, k):
            raise ValueError("projection rank/dimension changed; start a new chart")
        a, q = y[:k], y[k:]
        return np.concatenate((b.resolved @ a + b.return_from_hidden @ q,
                               b.drive_hidden @ a + b.hidden @ q))
    sol = solve_ivp(rhs, (times[0], times[-1]), y0, t_eval=times,
                    method="DOP853", rtol=rtol, atol=atol)
    if not sol.success or not np.all(np.isfinite(sol.y)):
        raise RuntimeError(f"split propagation failed: {sol.message}")
    aa, qq = sol.y[:k], sol.y[k:]
    xx = np.column_stack([blocks(float(s)).basis @ aa[:, i] + qq[:, i]
                          for i, s in enumerate(times)])
    return aa, qq, xx
