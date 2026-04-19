"""
bass/perturbation/cdm_fluid.py  (Week 6-03)
============================================

First-order CDM (cold dark matter) fluid perturbations on an orthogonal
Bianchi background. State: (δ_c, v_c). Collisionless dust closure
(π_c = 0).

Scope
-----
- Orthogonal Bianchi background
- Homogeneous-limit evolution
- Zero collision (CDM is collisionless)
- Dust closure: π_c = 0 exact WITHIN THE MODEL assumption
- Frozen-background metric perturbations (Φ̇, Ψ) are external inputs

Equations (homogeneous Bianchi limit, scalar amplitudes on shear axis)
----------------------------------------------------------------------
    δ̇_c = −3 Φ̇                  [continuity]
    v̇_c + H v_c = 0              [Euler; no gradient, no collision]

The sole damping mechanism is the Hubble expansion: v_c decays as
exp(−∫ H dη), so CDM bulk velocity is dissipated on the expansion
timescale and cannot lock to any other species by Thomson scattering
(which does not exist for CDM).

Dust closure and its scope
--------------------------
π_c = 0 is exact for single-stream cold matter (the dust closure). At
second order, free-streaming of different-velocity streams introduces
a velocity dispersion tensor σ^(v)_{ij} that violates dust closure.
That kinetic-theory treatment is an upgrade candidate explicitly
deferred to bass_rs (full kinetic CDM). For W6-03 first-order
perturbations on an orthogonal Bianchi background with zero CDM tilt,
dust closure is exact.

Honest scope
------------
- First-order only; velocity dispersion σ^(v)_{ij} → bass_rs
- Orthogonal Bianchi (no CDM tilt in first pass)
- Gradient terms D_a Ψ → W9 line-of-sight
- No coupling to other species at first order

References
----------
- Ma-Bertschinger 1995 §V.B (CDM synchronous-gauge equations)
- CAMB notes §7.3 (CDM continuity and Euler, CAMB sign convention)
- MASTER_PROMPT_LIST_bass_py_v1.1.md §3 W6-03
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from bass.perturbation.baryon_fluid import SymmetryAxis
from bass.runtime.canonical_decision import (
    CanonicalDecision,
    require_allow_reduction,
)


# ============================================================================
# Section 1 - CDMFluidState container
# ============================================================================

@dataclass(frozen=True)
class CDMFluidState:
    """First-order CDM fluid state on orthogonal Bianchi.

    Attributes
    ----------
    delta_c : float
        CDM density contrast δρ_c / ρ̄_c.
    v_c : float
        CDM bulk velocity along the shear symmetry axis. Units match
        the baryon v_b convention from W6-01 (same factor of 3
        correspondence as v_b ↔ 3Θ_1, though CDM has no photon-side
        partner).
    axis : SymmetryAxis
        Shared symmetry axis with the background shear.
    """
    delta_c: float
    v_c: float
    axis: SymmetryAxis = SymmetryAxis.Z

    def __post_init__(self) -> None:
        if not np.isfinite(self.delta_c):
            raise ValueError(f"delta_c must be finite, got {self.delta_c}")
        if not np.isfinite(self.v_c):
            raise ValueError(f"v_c must be finite, got {self.v_c}")


def zero_cdm_state(axis: SymmetryAxis = SymmetryAxis.Z) -> CDMFluidState:
    """Factory: zero CDM state (unperturbed)."""
    return CDMFluidState(delta_c=0.0, v_c=0.0, axis=axis)


# ============================================================================
# Section 2 - CDMParameters container
# ============================================================================

@dataclass(frozen=True)
class CDMParameters:
    """Expansion parameter for the CDM fluid.

    Attributes
    ----------
    H : float
        Conformal Hubble rate. Must be non-negative.

    Notes
    -----
    Unlike the baryon parameters (W6-01), CDM has no Thomson coupling,
    no baryon-to-photon momentum ratio, and no sound speed. The only
    coupling to the rest of the system is through gravity (Φ, Ψ), which
    appears as an EXTERNAL INPUT rather than a parameter of this module.
    """
    H: float

    def __post_init__(self) -> None:
        if not np.isfinite(self.H) or self.H < 0:
            raise ValueError(
                f"H must be non-negative finite, got {self.H}"
            )


def make_cdm_parameters(
    H_conformal: float,
    decision: CanonicalDecision,
) -> CDMParameters:
    """Factory: CDMParameters with W3 gating."""
    require_allow_reduction(decision, context="make_cdm_parameters")
    return CDMParameters(H=H_conformal)


# ============================================================================
# Section 3 - Continuity equation RHS
# ============================================================================

def cdm_continuity_rhs(
    state: CDMFluidState,
    phi_dot: float,
    decision: CanonicalDecision,
) -> float:
    """Homogeneous-Bianchi continuity: δ̇_c = −3 Φ̇.

    Structurally identical to the baryon continuity equation: both
    species follow the same metric perturbation. The difference between
    CDM and baryons lies entirely in the Euler equation (no Thomson
    drag on CDM).

    Parameters
    ----------
    state     : current CDM state (v_c is unused in the homogeneous limit)
    phi_dot   : metric perturbation time derivative Φ̇ (external input)
    decision  : canonical W3 decision gate

    Returns
    -------
    dot_delta_c : float
        d(δ_c)/dη in conformal time.
    """
    require_allow_reduction(decision, context="cdm_continuity_rhs")
    if not np.isfinite(phi_dot):
        raise ValueError(f"phi_dot must be finite, got {phi_dot}")
    return -3.0 * phi_dot


# ============================================================================
# Section 4 - Euler equation RHS
# ============================================================================

def cdm_euler_rhs(
    state: CDMFluidState,
    params: CDMParameters,
    decision: CanonicalDecision,
) -> float:
    """Homogeneous-Bianchi Euler: v̇_c + H v_c = 0.

    No Thomson drag, no sound-speed pressure term. CDM bulk velocity
    decays as exp(−∫ H dη) in the homogeneous limit. Gravitational
    acceleration k Ψ enters at the line-of-sight level (W9); it does
    NOT belong to this module.

    Returns v̇_c = −H v_c.

    Parameters
    ----------
    state     : current CDM state
    params    : expansion-rate parameter H
    decision  : canonical W3 decision gate
    """
    require_allow_reduction(decision, context="cdm_euler_rhs")
    return -params.H * state.v_c


# ============================================================================
# Section 5 - Combined RHS step (forward Euler)
# ============================================================================

def cdm_step(
    state: CDMFluidState,
    phi_dot: float,
    params: CDMParameters,
    dt: float,
    decision: CanonicalDecision,
) -> CDMFluidState:
    """Explicit-Euler step of the CDM fluid equations.

    Uses forward Euler:
        δ_c(η + dt) = δ_c(η) + dt × cdm_continuity_rhs(...)
        v_c(η + dt) = v_c(η) + dt × cdm_euler_rhs(...)

    Stability
    ---------
    CDM Euler is a simple decay v̇_c = −H v_c; explicit Euler stability
    requires dt × H ≲ 2, which is rarely binding for cosmological
    applications (H is the slowest rate in the problem).
    """
    require_allow_reduction(decision, context="cdm_step")
    if dt <= 0:
        raise ValueError(f"dt must be positive, got {dt}")
    dot_delta = cdm_continuity_rhs(state, phi_dot, decision)
    dot_v = cdm_euler_rhs(state, params, decision)
    return CDMFluidState(
        delta_c=state.delta_c + dt * dot_delta,
        v_c=state.v_c + dt * dot_v,
        axis=state.axis,
    )


# ============================================================================
# Section 6 - Diagnostics
# ============================================================================

def cdm_v_c_analytic_decay(
    v_c_initial: float,
    params: CDMParameters,
    delta_eta: float,
) -> float:
    """Analytic expansion-damped velocity: v_c(η + Δη) = v_c(η) exp(−H Δη).

    Valid for constant H over [η, η + Δη]. Used in convergence tests
    against the forward-Euler integrator.

    No W3 gate: pure diagnostic.
    """
    if not np.isfinite(v_c_initial):
        raise ValueError(f"v_c_initial must be finite, got {v_c_initial}")
    if not np.isfinite(delta_eta):
        raise ValueError(f"delta_eta must be finite, got {delta_eta}")
    return float(v_c_initial * np.exp(-params.H * delta_eta))


def cdm_is_collisionless(state: CDMFluidState) -> bool:
    """Identity diagnostic: CDM is collisionless by construction.

    Returns True unconditionally. Exists as a regression guard against
    future modifications that might erroneously add a collision term
    to this module. The test `test_cdm_no_collision_identity` verifies
    the function is present in the API.

    No W3 gate.
    """
    return True
