"""
bass/transport/implicit_hierarchy.py  (Week 5-B)
===================================================

Implicit time integrators for the multi-ℓ PSTF hierarchy in the stiff regime.

Motivation
----------
Explicit Euler's CFL bound dt < 2/(Γ + k_eff) becomes severe in the
pre-recombination regime where Γ = τ̇ ~ 10⁴ × H, forcing dt << timescale
of physical interest. Implicit methods decouple stability from accuracy.

Mathematical observation
------------------------
For frozen-background σ, the hierarchy equation

    dΘ/dt = (M - Γ I) Θ + b                                               (*)

with M = build_streaming_matrix(k_eff, L_max) and b = build_source_vector
is a LINEAR, TIME-INVARIANT ODE. The analytic solution is:

    Θ(t + h) = exp(A h) Θ(t) + A⁻¹ (exp(A h) - I) b                       (**)

where A = M - Γ I. Equation (**) is the EXACT solution at any h — the
matrix-exponential integrator thus serves as the validation oracle,
while backward Euler and Crank-Nicolson are approximations that match
at small h.

Three integrators implemented
-----------------------------
1. `backward_euler_step`  — (I - h A) Θ^(n+1) = Θ^n + h b
   Order 1, A-stable, L-stable. Reliable in stiff regime.

2. `crank_nicolson_step`  — trapezoidal rule (avg of explicit + implicit)
   Order 2, A-stable but NOT L-stable. Can exhibit oscillations in
   extremely stiff regime; accurate in mildly-stiff.

3. `exponential_step`     — Θ(t+h) = exp(A h) Θ + A⁻¹(exp(A h) - I) b
   Exact for linear time-invariant systems. Used as validation oracle;
   production solvers use it when A is small enough to fit in memory.

All three share the same signature and return `MultipoleState`, so
callers can swap implementations for benchmarking. The driver
`integrate_implicit_to_steady_state(...)` accepts a method enum.

Relation to W5-A explicit Euler
--------------------------------
At h → 0, all three methods converge to the explicit Euler RHS at
first order. At moderate h (h × Γ ~ 0.1), backward Euler loses some
accuracy but gains stability; Crank-Nicolson keeps 2nd-order accuracy;
exponential is exact. At h >> 1/(Γ + k_eff) (explicit would blow up),
backward Euler and exponential remain stable and approach the correct
steady-state, while explicit Euler diverges.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

import numpy as np
from scipy.linalg import expm

from bass.collision.thomson_tensor import AxisymmetricSTFTensor, SymmetryAxis
from bass.transport.multipole_hierarchy import (
    MultipoleState,
    HierarchyParameters,
    HierarchyIntegrationResult,
    build_streaming_matrix,
    build_source_vector,
    zero_state,
)
from bass.runtime.canonical_decision import (
    CanonicalDecision,
    require_allow_reduction,
)


# ============================================================================
# Section 1 - Method enum
# ============================================================================

class ImplicitMethod(Enum):
    """Integrator selection for the implicit driver.

    BACKWARD_EULER  : Order 1, A+L-stable. Default; most robust.
    CRANK_NICOLSON  : Order 2, A-stable (not L-stable).
    EXPONENTIAL     : Exact for linear time-invariant A.
    """
    BACKWARD_EULER = "backward_euler"
    CRANK_NICOLSON = "crank_nicolson"
    EXPONENTIAL = "exponential"


# ============================================================================
# Section 2 - System matrix assembly
# ============================================================================

def _assemble_system(
    params: HierarchyParameters,
) -> tuple:
    """Build (A, b) = (M - Γ I, shear source).

    Private helper used by all three step implementations. Uses the same
    streaming-matrix and source-vector builders as the explicit module.
    """
    L = params.ell_max
    M = build_streaming_matrix(params.k_eff, L)
    b = build_source_vector(params)
    A = M - params.damping_rate * np.eye(L + 1)
    return A, b


# ============================================================================
# Section 3 - Backward Euler
# ============================================================================

def _backward_euler_unchecked(
    state: MultipoleState,
    params: HierarchyParameters,
    dt: float,
) -> MultipoleState:
    """Private backward-Euler step. No gating, no shape checks."""
    A, b = _assemble_system(params)
    L = params.ell_max
    lhs = np.eye(L + 1) - dt * A
    rhs = state.amplitudes + dt * b
    new_amps = np.linalg.solve(lhs, rhs)
    return MultipoleState(amplitudes=new_amps, axis=state.axis)


def backward_euler_step(
    state: MultipoleState,
    params: HierarchyParameters,
    dt: float,
    decision: CanonicalDecision,
) -> MultipoleState:
    """One backward-Euler step of the hierarchy.

    Solves  (I - dt A) Θ^(n+1) = Θ^n + dt b

    Order 1 accurate, A-stable, L-stable. Always stable regardless of dt.

    Raises
    ------
    CanonicalBlockError if decision blocks.
    ValueError if dt ≤ 0 or shape mismatch.
    """
    require_allow_reduction(decision, context="backward_euler_step")
    _validate_step_inputs(state, params, dt)
    return _backward_euler_unchecked(state, params, dt)


# ============================================================================
# Section 4 - Crank-Nicolson (trapezoidal rule)
# ============================================================================

def _crank_nicolson_unchecked(
    state: MultipoleState,
    params: HierarchyParameters,
    dt: float,
) -> MultipoleState:
    """Private Crank-Nicolson step. No gating, no shape checks.

    Trapezoidal rule:
        (I - dt/2 A) Θ^(n+1) = (I + dt/2 A) Θ^n + dt b
    """
    A, b = _assemble_system(params)
    L = params.ell_max
    I = np.eye(L + 1)
    lhs = I - 0.5 * dt * A
    rhs = (I + 0.5 * dt * A) @ state.amplitudes + dt * b
    new_amps = np.linalg.solve(lhs, rhs)
    return MultipoleState(amplitudes=new_amps, axis=state.axis)


def crank_nicolson_step(
    state: MultipoleState,
    params: HierarchyParameters,
    dt: float,
    decision: CanonicalDecision,
) -> MultipoleState:
    """One Crank-Nicolson (trapezoidal) step of the hierarchy.

    Order 2 accurate, A-stable (not L-stable).

    Stability note: at very stiff dt × max|λ(A)| >> 1, Crank-Nicolson can
    show spurious oscillations that do not blow up but don't damp
    monotonically either. For hard stiff regimes, prefer backward Euler.
    """
    require_allow_reduction(decision, context="crank_nicolson_step")
    _validate_step_inputs(state, params, dt)
    return _crank_nicolson_unchecked(state, params, dt)


# ============================================================================
# Section 5 - Exponential integrator (EXACT for linear TI systems)
# ============================================================================

def _exponential_unchecked(
    state: MultipoleState,
    params: HierarchyParameters,
    dt: float,
) -> MultipoleState:
    """Private exponential-integrator step. No gating.

    Exact for the linear time-invariant system dΘ/dt = A Θ + b:

        Θ(t + h) = exp(A h) Θ(t) + φ₁(A h) h b

    where φ₁(z) = (exp(z) - 1)/z and for matrix A,
          φ₁(A h) h = A⁻¹ (exp(A h) - I)   when A is invertible.

    For robustness when A is near-singular (e.g., Γ = 0 and k_eff = 0),
    we use the augmented-matrix trick: the (L+2)×(L+2) block matrix

        [A  b]           [exp(Ah)  φ₁(Ah) h b]
        [0  0]  → expm → [  0           1    ]

    avoids the explicit A⁻¹ inversion.
    """
    A, b = _assemble_system(params)
    L = params.ell_max

    # Augmented matrix trick: embed (A, b) in an (L+2)x(L+2) block
    # so that expm handles the b-forcing without requiring A⁻¹.
    aug = np.zeros((L + 2, L + 2))
    aug[: L + 1, : L + 1] = A
    aug[: L + 1, L + 1] = b
    exp_aug = expm(aug * dt)
    # The top-right column of exp_aug is φ₁(A h) h b
    phi_b = exp_aug[: L + 1, L + 1]
    # The top-left block is exp(A h)
    exp_A = exp_aug[: L + 1, : L + 1]
    new_amps = exp_A @ state.amplitudes + phi_b
    return MultipoleState(amplitudes=new_amps, axis=state.axis)


def exponential_step(
    state: MultipoleState,
    params: HierarchyParameters,
    dt: float,
    decision: CanonicalDecision,
) -> MultipoleState:
    """One exact exponential-integrator step.

    For linear time-invariant A (frozen background), this is the
    ANALYTIC solution at any dt — no approximation, no stability bound.
    Used as the validation oracle for the other implicit methods.

    Cost scales as O((L+2)³) for the matrix exponential vs O(L³) for a
    linear solve — about 8× more expensive than backward Euler for
    typical L_max ~ 10. Use when exactness matters more than speed.
    """
    require_allow_reduction(decision, context="exponential_step")
    _validate_step_inputs(state, params, dt)
    return _exponential_unchecked(state, params, dt)


# ============================================================================
# Section 6 - Generic implicit driver
# ============================================================================

def integrate_implicit_to_steady_state(
    initial: MultipoleState,
    params: HierarchyParameters,
    dt: float,
    decision: CanonicalDecision,
    method: ImplicitMethod = ImplicitMethod.BACKWARD_EULER,
    max_steps: int = 1000,
    tolerance: float = 1e-8,
) -> HierarchyIntegrationResult:
    """Implicit integrator driver. Stops at relative-change convergence.

    Parameters
    ----------
    initial : MultipoleState
    params : HierarchyParameters
    dt : float
        Step size. Implicit methods do NOT require dt < dt_CFL, so `dt`
        can be chosen by accuracy considerations alone.
    decision : CanonicalDecision
    method : ImplicitMethod
        BACKWARD_EULER (default), CRANK_NICOLSON, or EXPONENTIAL.
    max_steps : int
    tolerance : float

    Returns
    -------
    HierarchyIntegrationResult
    """
    require_allow_reduction(
        decision, context="integrate_implicit_to_steady_state",
    )
    if dt <= 0:
        raise ValueError(f"dt must be positive, got {dt}")
    if max_steps < 1:
        raise ValueError(f"max_steps must be ≥ 1, got {max_steps}")
    if tolerance <= 0:
        raise ValueError(f"tolerance must be positive, got {tolerance}")
    if initial.ell_max != params.ell_max:
        raise ValueError(
            f"initial ell_max {initial.ell_max} != params ell_max "
            f"{params.ell_max}"
        )
    if initial.axis != params.shear.axis:
        raise ValueError(
            f"initial axis {initial.axis} != shear axis {params.shear.axis}"
        )

    # Pick unchecked stepper
    if method == ImplicitMethod.BACKWARD_EULER:
        step_fn = _backward_euler_unchecked
    elif method == ImplicitMethod.CRANK_NICOLSON:
        step_fn = _crank_nicolson_unchecked
    elif method == ImplicitMethod.EXPONENTIAL:
        step_fn = _exponential_unchecked
    else:
        raise ValueError(f"unknown method: {method}")

    # Analytic target via linsolve (same as explicit module)
    A, b = _assemble_system(params)
    L = params.ell_max
    # Steady state: A Θ_∞ + b = 0  →  Θ_∞ = -A⁻¹ b
    try:
        target_amps = np.linalg.solve(-A, b)
        target = MultipoleState(amplitudes=target_amps, axis=initial.axis)
    except np.linalg.LinAlgError:
        target = zero_state(L, initial.axis)

    state = initial
    residual = float("inf")
    converged = False
    steps_taken = 0

    for step in range(max_steps):
        new_state = step_fn(state, params, dt)
        delta = new_state.amplitudes - state.amplitudes
        denom = max(float(np.linalg.norm(new_state.amplitudes)), 1e-30)
        residual = float(np.linalg.norm(delta)) / denom
        state = new_state
        steps_taken = step + 1
        if residual < tolerance:
            converged = True
            break

    return HierarchyIntegrationResult(
        final_state=state,
        steps_taken=steps_taken,
        converged=converged,
        final_residual=residual,
        steady_state_target=target,
    )


# ============================================================================
# Section 7 - Input validation helper
# ============================================================================

def _validate_step_inputs(
    state: MultipoleState,
    params: HierarchyParameters,
    dt: float,
) -> None:
    """Shared input validation for single-step methods."""
    if dt <= 0:
        raise ValueError(f"dt must be positive, got {dt}")
    if state.ell_max != params.ell_max:
        raise ValueError(
            f"state ell_max {state.ell_max} != params ell_max "
            f"{params.ell_max}"
        )
    if state.axis != params.shear.axis:
        raise ValueError(
            f"state axis {state.axis} != shear axis {params.shear.axis}"
        )


# ============================================================================
# Section 8 - Stability diagnostic
# ============================================================================

def stability_function_ratio(
    method: ImplicitMethod,
    z: complex,
) -> complex:
    """Evaluate the method's stability function R(z) at complex z.

    Stability for dΘ/dt = λΘ means |R(dt × λ)| ≤ 1.

    BACKWARD_EULER : R(z) = 1/(1 - z)    (A+L-stable: |R| < 1 ∀ Re(z) < 0)
    CRANK_NICOLSON : R(z) = (1+z/2)/(1-z/2)   (A-stable, |R(∞)| = 1)
    EXPONENTIAL    : R(z) = exp(z)        (exact)
    """
    if method == ImplicitMethod.BACKWARD_EULER:
        return 1.0 / (1.0 - z)
    if method == ImplicitMethod.CRANK_NICOLSON:
        return (1.0 + 0.5 * z) / (1.0 - 0.5 * z)
    if method == ImplicitMethod.EXPONENTIAL:
        return np.exp(z)
    raise ValueError(f"unknown method: {method}")
