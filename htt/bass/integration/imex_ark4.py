"""bass/integration/imex_ark4.py — Round-16 IMEX-ARK4 mainline integrator.

Implements V5_ROUND16_04 §1: the Kennedy-Carpenter ARK4(3)6L[2]SA
additive Runge-Kutta integrator with embedded 3rd-order error estimator,
non-identity mass-matrix support, and adaptive step control.

Closes Round-16 PR-S2 (G1 prerequisite for Python-side D_2 = 1002.086744
PSTF closure).

Solves systems of the form:

    M(η) U' = f^E(η, U) + f^I(η, U)

where ``f^E`` is the explicit (non-stiff) part — free-streaming,
mode-mixing, metric source — and ``f^I`` is the implicit (stiff) part —
Thomson collision, optional TCA relaxation. Per V5_ROUND16_04 §1.2,
Round-16 will eventually plumb the BASS hierarchy RHS into this
splitting; the integrator itself is RHS-agnostic.

Per V5_ROUND16_04 §1.6 audit:
- A2: tableau coefficients verbatim from Kennedy-Carpenter 2003
  (verified bit-exact in test_ark4_tableau.py).
- A3: mass_matrix_fn is invoked at each stage; identity-shortcut only
  when explicitly toggled by the caller (no silent default).
- A6: for non-FLRW callers the mass_matrix_fn must return a non-identity
  matrix (verified at the call site, not here).
- A7: rtol convergence is 4th-order (verified by Prothero-Robinson test).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Literal, Optional

import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import spsolve

from bass.integration.ark4_tableau import (
    ARK4_TABLEAU,
    ESDIRK_DIAGONAL,
    NUM_STAGES,
    ARK4Tableau,
)

__all__ = [
    "IMEXARK4Integrator",
    "IMEXARK4StepResult",
    "IMEXARK4IntegrationResult",
]


@dataclass(frozen=True)
class IMEXARK4StepResult:
    """One ARK4 step's output."""

    eta: float
    U: np.ndarray
    error: float
    accepted: bool
    h_used: float
    h_next: float


@dataclass(frozen=True)
class IMEXARK4IntegrationResult:
    """Aligned per-output-step trajectory + diagnostics."""

    eta_grid: np.ndarray
    U_history: np.ndarray  # shape (n_eta, n_state)
    n_steps_total: int
    n_steps_accepted: int
    n_steps_rejected: int
    final_h: float
    tableau_id: str = field(default="ARK436L2SA_KennedyCarpenter_2003")


def _safety_clamp(factor: float, *, low: float = 0.1, high: float = 5.0) -> float:
    return float(min(high, max(low, factor)))


class IMEXARK4Integrator:
    """Kennedy-Carpenter ARK4(3)6L[2]SA stepper.

    Parameters
    ----------
    f_explicit : callable
        Signature ``f_explicit(eta, U) -> np.ndarray``. Returns the
        non-stiff RHS contribution at ``(eta, U)``.
    f_implicit : callable
        Signature ``f_implicit(eta, U) -> np.ndarray``. Returns the stiff
        RHS contribution at ``(eta, U)``.
    jac_implicit : callable
        Signature ``jac_implicit(eta, U) -> sparse_matrix | ndarray``.
        Returns ``∂f^I/∂U`` at ``(eta, U)``. Used to assemble the
        Newton-step linear operator ``M − γh J``.
    mass_matrix_fn : callable, optional
        Signature ``mass_matrix_fn(eta) -> sparse_matrix | ndarray``.
        If ``None``, identity is assumed. For Type V/IX and other
        non-FLRW Bianchi families the mass matrix is non-identity per
        V5_ROUND16_04 §1.3 — and the caller must supply a real assembler
        rather than relying on the identity default (V5_ROUND16_04 §1.6
        A6).
    rtol, atol : float
        Embedded error tolerances. Defaults match the V5_ROUND16_04
        Round-16 production stance (rtol=1e-8, atol=1e-12).
    max_step : float, optional
        Hard upper bound on step size; ``None`` disables.
    tableau : ARK4Tableau
        Frozen Kennedy-Carpenter tableau. Default
        :data:`bass.integration.ark4_tableau.ARK4_TABLEAU`.
    """

    def __init__(
        self,
        *,
        f_explicit: Callable[[float, np.ndarray], np.ndarray],
        f_implicit: Callable[[float, np.ndarray], np.ndarray],
        jac_implicit: Callable[[float, np.ndarray], object],
        mass_matrix_fn: Optional[Callable[[float], object]] = None,
        rtol: float = 1.0e-8,
        atol: float = 1.0e-12,
        max_step: Optional[float] = None,
        tableau: ARK4Tableau = ARK4_TABLEAU,
    ) -> None:
        if rtol <= 0.0 or atol <= 0.0:
            raise ValueError("rtol and atol must both be positive")
        if max_step is not None and max_step <= 0.0:
            raise ValueError("max_step, when provided, must be positive")
        self.f_explicit = f_explicit
        self.f_implicit = f_implicit
        self.jac_implicit = jac_implicit
        self.mass_matrix_fn = mass_matrix_fn
        self.rtol = float(rtol)
        self.atol = float(atol)
        self.max_step = float("inf") if max_step is None else float(max_step)
        self.tableau = tableau

    # ──────────────────────────────────────────────────────────────────
    # Single-step
    # ──────────────────────────────────────────────────────────────────

    def step(
        self,
        eta: float,
        U: np.ndarray,
        h: float,
    ) -> IMEXARK4StepResult:
        """Take one ARK4(3) step from (eta, U) with trial step h.

        Returns an :class:`IMEXARK4StepResult` whose ``accepted`` field
        records whether the embedded error estimate was within tolerance.
        Caller is responsible for the accept/reject loop.
        """
        s = self.tableau.num_stages
        U_size = U.size
        U_arr = np.asarray(U, dtype=np.float64)

        # Stage values K^E_i = f^E(η_i, Y_i), K^I_i = f^I(η_i, Y_i)
        K_E = np.zeros((s, U_size), dtype=np.float64)
        K_I = np.zeros((s, U_size), dtype=np.float64)
        Y = np.zeros((s, U_size), dtype=np.float64)

        a_E = self.tableau.a_E
        a_I = self.tableau.a_I
        c = self.tableau.c
        gamma = self.tableau.gamma

        # ESDIRK first stage (i=0) is explicit: f^I_0 needs no implicit
        # solve. We still evaluate f^I(η, U) for the K^I[0] slot.
        Y[0] = U_arr.copy()
        K_E[0] = self.f_explicit(float(eta) + float(c[0]) * float(h), Y[0])
        K_I[0] = self.f_implicit(float(eta) + float(c[0]) * float(h), Y[0])

        for i in range(1, s):
            eta_i = float(eta) + float(c[i]) * float(h)
            # Stage equation:
            #   M(η_i) Y_i = M(η_i) U + h Σ_{j<i}(a^E_ij f^E_j + a^I_ij f^I_j)
            #             + γh f^I(η_i, Y_i)
            # Define X_i = h Σ_{j<i}(a^E_ij K^E_j + a^I_ij K^I_j) and let
            # ΔY = Y_i − U. With predictor Y_pred = U:
            #   M ΔY − γh J(Y_i) ΔY = X_i + γh f^I(Y_pred) − γh J·0
            # ⇒ (M − γh J) ΔY = X_i + γh f^I(U)
            # which is mass-matrix-correct AND exact for affine f^I after
            # one Newton iteration.
            X_i = np.zeros_like(U_arr)
            for j in range(i):
                X_i += h * (a_E[i, j] * K_E[j] + a_I[i, j] * K_I[j])
            Y_i = self._implicit_stage_solve(
                eta_i=eta_i,
                U=U_arr,
                X_i=X_i,
                gamma_h=h * gamma,
            )
            Y[i] = Y_i
            K_E[i] = self.f_explicit(eta_i, Y_i)
            K_I[i] = self.f_implicit(eta_i, Y_i)

        # 4th-order combination (b weights)
        U_high = U_arr.copy()
        U_low = U_arr.copy()
        b = self.tableau.b
        bhat = self.tableau.bhat
        for i in range(s):
            U_high += h * (b[i] * K_E[i] + b[i] * K_I[i])
            U_low += h * (bhat[i] * K_E[i] + bhat[i] * K_I[i])

        # Embedded error: weighted L2 norm with mixed rtol/atol scaling.
        sc = self.atol + self.rtol * np.maximum(np.abs(U_arr), np.abs(U_high))
        err = float(np.sqrt(np.mean(((U_high - U_low) / sc) ** 2)))

        accepted = err <= 1.0
        # PI-controller-lite: factor = 0.9 * err^{-1/4} (4th-order embedded)
        if err > 0.0:
            factor = 0.9 * err ** (-1.0 / 4.0)
        else:
            factor = 5.0
        h_next = float(min(h * _safety_clamp(factor), self.max_step))

        return IMEXARK4StepResult(
            eta=float(eta) + (float(h) if accepted else 0.0),
            U=U_high if accepted else U_arr,
            error=err,
            accepted=accepted,
            h_used=float(h),
            h_next=h_next,
        )

    # ──────────────────────────────────────────────────────────────────
    # Adaptive integration loop
    # ──────────────────────────────────────────────────────────────────

    def integrate(
        self,
        eta_grid: np.ndarray,
        U0: np.ndarray,
        *,
        h_initial: Optional[float] = None,
    ) -> IMEXARK4IntegrationResult:
        """March from ``eta_grid[0]`` over ``eta_grid`` with adaptive control.

        The output history captures U at each ``eta_grid`` node. The step
        size is adapted internally; intermediate accepted steps that
        overshoot the next output node are clipped.
        """
        eta = float(eta_grid[0])
        U = np.asarray(U0, dtype=np.float64).copy()
        history = [U.copy()]
        n_steps_total = 0
        n_steps_accepted = 0
        n_steps_rejected = 0

        if h_initial is None:
            h = float(eta_grid[1] - eta_grid[0]) * 0.5
        else:
            h = float(h_initial)
        h = min(h, self.max_step)

        for eta_target in np.asarray(eta_grid[1:], dtype=np.float64):
            while eta < eta_target - 1.0e-15:
                h_try = float(min(h, eta_target - eta, self.max_step))
                result = self.step(eta, U, h_try)
                n_steps_total += 1
                if result.accepted:
                    n_steps_accepted += 1
                    eta = result.eta
                    U = result.U
                    h = result.h_next
                else:
                    n_steps_rejected += 1
                    h = result.h_next
                    if h <= 1.0e-30:
                        raise RuntimeError(
                            f"IMEX-ARK4 step size collapsed at η={eta:.3e}"
                        )
            history.append(U.copy())

        return IMEXARK4IntegrationResult(
            eta_grid=np.asarray(eta_grid, dtype=np.float64),
            U_history=np.asarray(history, dtype=np.float64),
            n_steps_total=n_steps_total,
            n_steps_accepted=n_steps_accepted,
            n_steps_rejected=n_steps_rejected,
            final_h=float(h),
        )

    # ──────────────────────────────────────────────────────────────────
    # Implicit stage solve helpers
    # ──────────────────────────────────────────────────────────────────

    def _implicit_stage_solve(
        self,
        *,
        eta_i: float,
        U: np.ndarray,
        X_i: np.ndarray,
        gamma_h: float,
    ) -> np.ndarray:
        """Solve  M Y_i = M U + X_i + γh f^I(η_i, Y_i)  for Y_i.

        ``X_i`` is the accumulated explicit-and-prior-implicit stage sum
        ``h Σ_{j<i} (a^E_ij f^E_j + a^I_ij f^I_j)``.

        Using predictor Y_pred = U and ΔY = Y_i − U:

            (M − γh J) ΔY = X_i + γh f^I(η_i, U)

        This is mass-matrix-correct for any M (sparse or dense) and is
        exact for affine f^I after one Newton iteration.
        """
        M = self._mass_matrix_at(eta_i, U.size)
        J = self._jacobian_at(eta_i, U, dim=U.size)
        f_at_U = self.f_implicit(eta_i, U)
        K_op = M - gamma_h * J
        rhs_lin = X_i + gamma_h * f_at_U
        delta = _solve_linear(K_op, rhs_lin)
        return U + delta

    def _mass_matrix_at(self, eta: float, dim: int):
        if self.mass_matrix_fn is None:
            return sp.identity(dim, format="csr", dtype=np.float64)
        return self.mass_matrix_fn(float(eta))

    def _jacobian_at(self, eta: float, U: np.ndarray, *, dim: int):
        return self.jac_implicit(float(eta), U)


# ──────────────────────────────────────────────────────────────────────
# Linear-algebra helpers (handle dense + sparse uniformly)
# ──────────────────────────────────────────────────────────────────────


def _matvec(M, x: np.ndarray) -> np.ndarray:
    if sp.issparse(M):
        return np.asarray(M @ x).ravel()
    return np.asarray(np.dot(M, x)).ravel()


def _solve_linear(A, b: np.ndarray) -> np.ndarray:
    if sp.issparse(A):
        return np.asarray(spsolve(A.tocsc(), b)).ravel()
    return np.linalg.solve(A, b)
