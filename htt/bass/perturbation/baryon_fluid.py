"""
bass/perturbation/baryon_fluid.py  (Week 6-01)
==============================================

First-order baryon fluid perturbations on an orthogonal Bianchi background.
State: (δ_b, v_b). Continuity + Euler equations with Thomson drag coupling
to the photon dipole. Scalar k-mode callers may also provide the
perturbative baryon sound speed and comoving wavenumber, which activates
the Ma-Bertschinger pressure-gradient term.

Scope
-----
- Orthogonal Bianchi background (no tilt in baryons at this stage)
- Homogeneous-limit evolution: gradient terms D_a → 0 at first order
- Isotropic Thomson collision (anisotropic visibility is W8+ scope)
- CDM is a separate module (W6-03); photon dipole evolution is W6-02
- Frozen-background metric perturbations (Φ̇, Ψ) are external inputs

Equations (homogeneous Bianchi limit, scalar amplitudes on shear axis)
----------------------------------------------------------------------
    δ̇_b = −3 Φ̇                                          [continuity]
    v̇_b + H v_b = c_s,b² k δ_b +(τ̇ / R_b)(3 Θ_1^γ − v_b) [Euler]

For the homogeneous Bianchi limit used by older callers, set
``c_s,b² = 0`` or ``k = 0``. That preserves the original no-gradient
equation exactly while letting the FLRW scalar limit carry the physical
baryon pressure source.

Sign convention for the Thomson drag: PLUS sign drives v_b TOWARD 3 Θ_1^γ
(Ma-Bertschinger 1995 Eq. 29; CAMB notes §7.3). If v_b < 3 Θ_1^γ, the
drag accelerates baryons; if v_b > 3 Θ_1^γ, it decelerates them.
Momentum is transferred from photons (faster) to baryons (slower), as
physically required.

Conventions
-----------
- v_b            : baryon bulk velocity along the shear symmetry axis
- Θ_1^γ          : photon PSTF dipole amplitude (W5-A convention);
                   at tight coupling v_b = 3 Θ_1^γ.
- R_b = 3ρ_b / (4ρ_γ) : baryon-to-photon momentum ratio (dimensionless)
- τ̇ = a n_e σ_T       : conformal Thomson rate (positive, units 1/time)
- H                    : conformal Hubble rate (positive, units 1/time)

Tight coupling limit
--------------------
τ̇ / H → ∞ ⇒ (3 Θ_1^γ − v_b) → 0, i.e. v_b → 3 Θ_1^γ. Sound speed
c_s² = 1 / [3(1 + R_b)] is a property of the combined baryon-photon
fluid (emerges in W6-02+ photon-dipole coupling, not in this module).

Momentum conservation
---------------------
Total baryon + photon momentum is conserved by Thomson scattering. With
the v_b = 3 Θ_1^γ lock convention, the companion photon-dipole equation
(W6-02 scope) has the equal-and-opposite drag −τ̇(Θ_1^γ − v_b/3), so
that R_b ρ_γ v̇_b + ρ_γ Θ̇_1^γ vanishes from the collision block after
ρ_b/ρ_γ = 4 R_b / 3 substitution. The sign convention here (+(τ̇/R_b)·
(3Θ − v_b) on baryons, corresponding −τ̇·(Θ − v_b/3) on photons) is
Ma-Bertschinger / CAMB standard.

Honest scope
------------
First-order baryon fluid on orthogonal Bianchi with homogeneous-limit
equations. The full k-gradient source D_a Ψ enters at W9 line-of-sight
and does NOT appear in this module's evolution. Local peculiar velocity
W_R v_loc (R-TILT-02) is a separate object inserted at W12, not here.

References
----------
- ch05_teff_corrections.tex §thomson-coupling (Eq. photon-dipole, Eq.
  baryon-euler)
- Ma-Bertschinger 1995 (synchronous gauge reference equations)
- CAMB notes §7.3 (tight coupling closure and R_b definition)
- MASTER_PROMPT_LIST_bass_py.md §3 W6-01
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np

from bass.runtime.canonical_decision import (
    CanonicalDecision,
    require_allow_reduction,
)


# ============================================================================
# Section 1 - Symmetry axis enum (local copy of the transport convention)
# ============================================================================

class SymmetryAxis(Enum):
    """Which spatial axis the background shear selects as its principal axis.

    Baryon velocity v_b and photon dipole Θ_1 are both scalar amplitudes
    along this axis in the axisymmetric first-order treatment.
    """
    X = "x"
    Y = "y"
    Z = "z"


# ============================================================================
# Section 2 - BaryonFluidState container
# ============================================================================

@dataclass(frozen=True)
class BaryonFluidState:
    """First-order baryon fluid state on orthogonal Bianchi.

    Attributes
    ----------
    delta_b : float
        Baryon density contrast δρ_b / ρ̄_b.
    v_b : float
        Baryon bulk velocity along the shear symmetry axis. Same units as
        the photon PSTF dipole Θ_1^γ times 3, i.e. at tight coupling
        v_b == 3 · Θ_1^γ exactly.
    axis : SymmetryAxis
        Shared symmetry axis with the background shear.
    """
    delta_b: float
    v_b: float
    axis: SymmetryAxis = SymmetryAxis.Z

    def __post_init__(self) -> None:
        if not np.isfinite(self.delta_b):
            raise ValueError(f"delta_b must be finite, got {self.delta_b}")
        if not np.isfinite(self.v_b):
            raise ValueError(f"v_b must be finite, got {self.v_b}")


def zero_baryon_state(axis: SymmetryAxis = SymmetryAxis.Z) -> BaryonFluidState:
    """Factory: zero baryon state (unperturbed)."""
    return BaryonFluidState(delta_b=0.0, v_b=0.0, axis=axis)


# ============================================================================
# Section 3 - BaryonParameters container
# ============================================================================

@dataclass(frozen=True)
class BaryonParameters:
    """Thermodynamic/collision parameters for the baryon fluid.

    Attributes
    ----------
    R_b : float
        Baryon-to-photon momentum ratio R_b = 3 ρ_b / (4 ρ_γ). Must be
        positive.
    tau_dot : float
        Conformal Thomson rate τ̇ = a n_e σ_T. Must be non-negative. Zero
        corresponds to the post-recombination limit where the fluid
        equations become free (no drag).
    H : float
        Conformal Hubble rate. Must be non-negative.
    sound_speed_sq : float
        Perturbative baryon sound speed squared in units of c². Defaults
        to zero for the homogeneous Bianchi limit.
    k_comoving : float
        Scalar-mode comoving wavenumber [Mpc⁻¹]. Defaults to zero for
        the homogeneous Bianchi limit.

    Notes
    -----
    R_b temperature scaling (first order in Ω_b h², cosmology-dependent):
        R_b(a) ≈ 3 Ω_b,0 / (4 Ω_γ,0) · a
    For Planck 2018 values, R_b at recombination is roughly 0.6. That
    scaling is NOT enforced here; callers supply R_b at the relevant η.
    """
    R_b: float
    tau_dot: float
    H: float
    sound_speed_sq: float = 0.0
    k_comoving: float = 0.0

    def __post_init__(self) -> None:
        if not np.isfinite(self.R_b) or self.R_b <= 0:
            raise ValueError(f"R_b must be positive finite, got {self.R_b}")
        if not np.isfinite(self.tau_dot) or self.tau_dot < 0:
            raise ValueError(
                f"tau_dot must be non-negative finite, got {self.tau_dot}"
            )
        if not np.isfinite(self.H) or self.H < 0:
            raise ValueError(
                f"H must be non-negative finite, got {self.H}"
            )
        if not np.isfinite(self.sound_speed_sq) or self.sound_speed_sq < 0:
            raise ValueError(
                "sound_speed_sq must be non-negative finite, "
                f"got {self.sound_speed_sq}"
            )
        if not np.isfinite(self.k_comoving) or self.k_comoving < 0:
            raise ValueError(
                f"k_comoving must be non-negative finite, got {self.k_comoving}"
            )


def make_baryon_parameters(
    rho_b: float,
    rho_gamma: float,
    n_e_sigma_T: float,
    scale_factor: float,
    H_conformal: float,
    decision: CanonicalDecision,
    sound_speed_sq: float = 0.0,
    k_comoving: float = 0.0,
) -> BaryonParameters:
    """Factory: derive (R_b, τ̇, H) from primitive quantities.

    R_b = 3 ρ_b / (4 ρ_γ),   τ̇ = a × (n_e σ_T).

    Parameters
    ----------
    rho_b        : baryon mass density (same units as ρ_γ)
    rho_gamma    : photon energy density
    n_e_sigma_T  : proper electron number density × σ_T, i.e. the
                   reciprocal of the proper mean free path (units 1/length)
    scale_factor : a, dimensionless
    H_conformal  : conformal Hubble rate ℋ = ȧ/a in conformal time
    decision     : canonical W3 decision gate
    """
    require_allow_reduction(decision, context="make_baryon_parameters")
    if rho_gamma <= 0:
        raise ValueError(
            f"rho_gamma must be positive, got {rho_gamma}"
        )
    if rho_b <= 0:
        raise ValueError(f"rho_b must be positive, got {rho_b}")
    if scale_factor <= 0:
        raise ValueError(
            f"scale_factor must be positive, got {scale_factor}"
        )
    R_b = 3.0 * rho_b / (4.0 * rho_gamma)
    tau_dot = scale_factor * n_e_sigma_T
    return BaryonParameters(
        R_b=R_b,
        tau_dot=tau_dot,
        H=H_conformal,
        sound_speed_sq=sound_speed_sq,
        k_comoving=k_comoving,
    )


# ============================================================================
# Section 4 - Continuity equation RHS
# ============================================================================

def baryon_continuity_rhs(
    state: BaryonFluidState,
    phi_dot: float,
    decision: CanonicalDecision,
) -> float:
    """Homogeneous-Bianchi continuity: δ̇_b = −3 Φ̇.

    The spatial gradient term −k v_b (in Fourier space) or −D_a v_b^a
    vanishes at first order in the homogeneous limit because D_a acting
    on the zeroth-order background is zero.  The k-mode gradient re-enters
    at line-of-sight (W9); it does NOT belong to this module.

    Parameters
    ----------
    state      : current baryon state (only δ_b is used; v_b is unused in
                 the homogeneous limit)
    phi_dot    : metric perturbation time derivative Φ̇ (external input)
    decision   : canonical W3 decision gate

    Returns
    -------
    dot_delta_b : float
        d(δ_b)/dη in conformal time.
    """
    require_allow_reduction(decision, context="baryon_continuity_rhs")
    if not np.isfinite(phi_dot):
        raise ValueError(f"phi_dot must be finite, got {phi_dot}")
    # State is validated by its own __post_init__; no further checks.
    return -3.0 * phi_dot


# ============================================================================
# Section 5 - Euler equation RHS
# ============================================================================

def baryon_euler_rhs(
    state: BaryonFluidState,
    theta_1_photon: float,
    params: BaryonParameters,
    decision: CanonicalDecision,
) -> float:
    """Baryon Euler RHS with optional scalar pressure gradient.

    Homogeneous-Bianchi callers use ``sound_speed_sq = k_comoving = 0``,
    giving the legacy equation
    ``v̇_b + H v_b = +(τ̇/R_b)(3 Θ_1^γ − v_b)``. FLRW scalar k-mode
    callers supply nonzero values and recover the MB-95 term
    ``+ c_s,b² k δ_b`` in the velocity variable ``v_b = θ_b/k``.

    Returns v̇_b (the time derivative of the baryon velocity).

    Parameters
    ----------
    state          : current baryon state (δ_b is unused in the Euler eq.)
    theta_1_photon : photon PSTF dipole amplitude Θ_1^γ (external input;
                     at W6-02 this is resolved self-consistently)
    params         : (R_b, τ̇, H)
    decision       : canonical W3 decision gate

    Returns
    -------
    dot_v_b : float
        d(v_b)/dη in conformal time.
    """
    require_allow_reduction(decision, context="baryon_euler_rhs")
    if not np.isfinite(theta_1_photon):
        raise ValueError(
            f"theta_1_photon must be finite, got {theta_1_photon}"
        )
    pressure = params.sound_speed_sq * params.k_comoving * state.delta_b
    # Thomson drag drives v_b → 3 Θ_1^γ; the lock residual (3Θ − v_b)
    # times (+τ̇/R_b) gives positive v̇_b when v_b lags photons.
    drag = (params.tau_dot / params.R_b) * (
        3.0 * theta_1_photon - state.v_b
    )
    return -params.H * state.v_b + pressure + drag


# ============================================================================
# Section 6 - Combined RHS step (forward Euler)
# ============================================================================

def baryon_step(
    state: BaryonFluidState,
    theta_1_photon: float,
    phi_dot: float,
    params: BaryonParameters,
    dt: float,
    decision: CanonicalDecision,
) -> BaryonFluidState:
    """Explicit-Euler step of the baryon fluid equations.

    Uses forward Euler:
        δ_b(η + dt) = δ_b(η) + dt × baryon_continuity_rhs(...)
        v_b(η + dt) = v_b(η) + dt × baryon_euler_rhs(...)

    Stability
    ---------
    In the stiff regime τ̇ ≫ H, forward Euler requires
        dt × (τ̇ / R_b) ≲ 2
    Use the implicit integrators of W5-B (bass.transport.implicit_hierarchy)
    for stiff timesteps; a baryon-specific implicit helper is not provided
    in W6-01 to keep scope minimal.
    """
    require_allow_reduction(decision, context="baryon_step")
    if dt <= 0:
        raise ValueError(f"dt must be positive, got {dt}")
    dot_delta = baryon_continuity_rhs(state, phi_dot, decision)
    dot_v = baryon_euler_rhs(state, theta_1_photon, params, decision)
    return BaryonFluidState(
        delta_b=state.delta_b + dt * dot_delta,
        v_b=state.v_b + dt * dot_v,
        axis=state.axis,
    )


# ============================================================================
# Section 7 - Tight-coupling steady-state solver
# ============================================================================

def tight_coupling_v_b_steady_state(
    theta_1_photon: float,
    params: BaryonParameters,
    decision: CanonicalDecision,
) -> float:
    """Analytic steady-state v_b balancing expansion drag and Thomson drag.

    At steady state (v̇_b = 0):
        H v_b = +(τ̇/R_b)(3 Θ_1^γ − v_b)
    ⇒   v_b [H + τ̇/R_b] = (τ̇/R_b) · 3 Θ_1^γ
    ⇒   v_b = (τ̇/R_b) · 3 Θ_1^γ / (H + τ̇/R_b)

    In the tight-coupling limit τ̇/R_b ≫ H: v_b → 3 Θ_1^γ.
    In the free-streaming limit τ̇ = 0: v_b = 0 (expansion drag only).

    The denominator H + τ̇/R_b is strictly non-negative for H ≥ 0 and
    τ̇ ≥ 0 (enforced by BaryonParameters.__post_init__); the only
    degenerate case is H = τ̇ = 0, where all dynamics vanishes and no
    unique steady state exists.
    """
    require_allow_reduction(
        decision, context="tight_coupling_v_b_steady_state",
    )
    if not np.isfinite(theta_1_photon):
        raise ValueError(
            f"theta_1_photon must be finite, got {theta_1_photon}"
        )
    tau_over_R = params.tau_dot / params.R_b
    denom = params.H + tau_over_R
    if denom < 1e-300:
        # Both H = 0 and τ̇ = 0: no dynamics at all.
        return float("nan")
    return tau_over_R * 3.0 * theta_1_photon / denom


def tight_coupling_residual(
    state: BaryonFluidState, theta_1_photon: float,
) -> float:
    """Measure of departure from tight coupling lock.

    Returns
    -------
    residual : float
        (3 Θ_1^γ − v_b) / max(|3 Θ_1^γ|, 1e-30)

    Interpretation: |residual| ≪ 1 means the fluids are locked; |residual|
    ~ 1 means they are decoupled.

    No W3 gate: this is a pure diagnostic with no physical evolution.
    """
    denom = max(abs(3.0 * theta_1_photon), 1e-30)
    return (3.0 * theta_1_photon - state.v_b) / denom
