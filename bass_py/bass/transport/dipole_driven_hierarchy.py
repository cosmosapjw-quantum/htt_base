"""
bass/transport/dipole_driven_hierarchy.py  (Week 6-02)
======================================================

Extension of the W5-A multipole hierarchy with an ℓ=1 dipole drive:
(i) tilt-induced acceleration source A_1, (ii) Thomson Doppler coupling
to the baryon velocity v_b.

Scope
-----
Non-invasive wrapper around W5-A `multipole_hierarchy`. W5-A remains the
single source of truth for the streaming matrix, shear source at ℓ=2,
and the container conventions. This module:

  1. Adds a DipoleDrive configuration holding (A_1, BaryonCoupling?)
  2. Builds an AUGMENTED source vector = W5-A source + dipole drive
  3. Applies an effective DAMPING MODIFICATION at ℓ=1 when baryon
     coupling is on: +τ̇ extra damping (implicit in the drag kernel
     below, applied explicitly via an extra diagonal term)
  4. Provides `euler_step_dipole_driven` and
     `integrate_dipole_driven_to_steady_state` wrappers

Physics (Ma-Bertschinger / CAMB sign convention)
------------------------------------------------
The ℓ=1 photon equation in the homogeneous Bianchi limit reads

    Θ̇_1 + Γ Θ_1 = (k_eff / 3) Θ_0 − (2 k_eff / 3) Θ_2
                  − τ̇ (Θ_1 − v_b / 3)                      [Thomson]
                  + A_1 / 3                                  [tilt drive]

The Thomson term is the equal-and-opposite partner of the baryon Euler
drag in W6-01:  baryon side +(τ̇/R_b)(3Θ_1 − v_b); photon side
−τ̇(Θ_1 − v_b/3). Momentum of the combined fluid is conserved because
   R_b ρ_γ · (baryon drag) + ρ_γ · (photon drag) = 0
follows from R_b = 3 ρ_b / (4 ρ_γ) after the usual factors.

The ℓ=2 shear injection from W5-A is preserved (this module only
ADDS to ℓ=1 behavior). All other ℓ unchanged.

Backward compatibility
----------------------
If `DipoleDrive.acceleration_A_1 = 0` and `baryon_coupling is None`,
every function in this module reduces to its W5-A counterpart
bit-exactly. A dedicated test class
`TestW5ABackwardCompatibility` asserts this.

Not in scope (deferred)
-----------------------
- k-space gradient source (4/3)(k/S) A_k → W9 line-of-sight
- Self-consistent coupling of baryon v_b to Θ_1 → coupled solver at
  later W-phase (this module takes v_b as external)
- Polarization feedback (E_2) → W7
- Explicit second-order TCA closure → W6-04
- Tilted-Bianchi frame change of A_1 → W12

References
----------
- Ma-Bertschinger 1995 Eq. 63 (photon ℓ=1 in synchronous gauge)
- CAMB notes §7.3 (dipole equation with tight coupling)
- MASTER_PROMPT_LIST_bass_py_v1.1.md §3 W6-02
- ch05_teff_corrections.tex §thomson-coupling (NOTE: sign of baryon-
  side drag in that section matches this module's convention after
  the v1.1 correction; a manuscript retrofit check is pending)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from bass.collision.thomson_tensor import (
    AxisymmetricSTFTensor,
    SymmetryAxis,
)
from bass.runtime.canonical_decision import (
    CanonicalDecision,
    require_allow_reduction,
)
from bass.transport.multipole_hierarchy import (
    HierarchyParameters,
    HierarchyIntegrationResult,
    MultipoleState,
    build_source_vector,
    build_streaming_matrix,
    compute_steady_state_hierarchy,
    zero_state,
)


# ============================================================================
# Section 1 - BaryonCoupling: Thomson drag on the photon dipole
# ============================================================================

@dataclass(frozen=True)
class BaryonCoupling:
    """Thomson drag coupling of the photon ℓ=1 to the baryon velocity.

    The photon ℓ=1 equation picks up  −τ̇(Θ_1 − v_b/3)  when the
    baryon fluid is included. This is the EQUAL-AND-OPPOSITE partner of
    the baryon Euler drag +(τ̇/R_b)(3Θ_1 − v_b) in W6-01.

    Attributes
    ----------
    v_b : float
        Baryon bulk velocity (same convention as W6-01 `baryon_fluid`).
        Appears only in the combination v_b/3 on the photon side.
    tau_dot : float
        Conformal Thomson rate τ̇ = a n_e σ_T ≥ 0.
    """
    v_b: float
    tau_dot: float

    def __post_init__(self) -> None:
        if not np.isfinite(self.v_b):
            raise ValueError(f"v_b must be finite, got {self.v_b}")
        if not np.isfinite(self.tau_dot) or self.tau_dot < 0:
            raise ValueError(
                f"tau_dot must be non-negative finite, got {self.tau_dot}"
            )


# ============================================================================
# Section 2 - DipoleDrive: full ℓ=1 source configuration
# ============================================================================

@dataclass(frozen=True)
class DipoleDrive:
    """Configuration of the ℓ=1 photon dipole drive.

    Attributes
    ----------
    acceleration_A_1 : float
        Tilt-induced acceleration source at ℓ=1, entering the source
        vector as +A_1 / 3. In the v1.1 W6-02 scope this is treated as
        an EXTERNAL input; self-consistent coupling to the tilt PDE
        enters at W12.  Zero recovers the W5-A behavior on ℓ=1.
    baryon_coupling : BaryonCoupling | None
        If provided, activates the Thomson drag  −τ̇(Θ_1 − v_b/3).
        If None, no drag is applied at ℓ=1 and the hierarchy matches
        W5-A bit-exactly.
    """
    acceleration_A_1: float = 0.0
    baryon_coupling: Optional[BaryonCoupling] = None

    def __post_init__(self) -> None:
        if not np.isfinite(self.acceleration_A_1):
            raise ValueError(
                f"acceleration_A_1 must be finite, got {self.acceleration_A_1}"
            )

    @property
    def is_trivial(self) -> bool:
        """True iff this drive reduces to W5-A behavior at ℓ=1."""
        return (
            self.acceleration_A_1 == 0.0
            and self.baryon_coupling is None
        )


def no_dipole_drive() -> DipoleDrive:
    """Factory: trivial dipole drive (W5-A-equivalent behavior)."""
    return DipoleDrive(acceleration_A_1=0.0, baryon_coupling=None)


# ============================================================================
# Section 3 - Augmented source vector with dipole drive
# ============================================================================

def build_dipole_driven_source_vector(
    params: HierarchyParameters,
    drive: DipoleDrive,
) -> np.ndarray:
    """Source vector including ℓ=2 shear (W5-A) and ℓ=1 dipole drives.

    Components
    ----------
        b[0] = 0
        b[1] = A_1 / 3  +  τ̇ · v_b / 3         (if baryon_coupling)
        b[2] = Σ_2 · σ                          (W5-A unchanged)
        b[ℓ≥3] = 0

    The Thomson drag's v_b-dependent INHOMOGENEOUS piece (τ̇ v_b / 3)
    goes into the source vector; the Θ_1-dependent HOMOGENEOUS piece
    (−τ̇ Θ_1) goes into the damping modification in Section 4.
    """
    b = build_source_vector(params).copy()
    if params.ell_max >= 1:
        b[1] = b[1] + drive.acceleration_A_1 / 3.0
        if drive.baryon_coupling is not None:
            bc = drive.baryon_coupling
            b[1] = b[1] + bc.tau_dot * bc.v_b / 3.0
    return b


# ============================================================================
# Section 4 - Damping modification at ℓ=1 (Thomson drag homogeneous part)
# ============================================================================

def build_damping_vector(
    params: HierarchyParameters,
    drive: DipoleDrive,
) -> np.ndarray:
    """Per-ℓ effective damping vector Γ_ℓ.

    Starts from the uniform W5-A damping Γ across all ℓ, then adds
    the Thomson homogeneous contribution +τ̇ at ℓ=1 when baryon
    coupling is on:

        Γ_ℓ = Γ                  for ℓ ≠ 1 (or baryon_coupling = None)
        Γ_1 = Γ + τ̇              when baryon_coupling is present

    Note
    ----
    W5-A models Γ as uniform across ℓ by design (the single "species
    damping rate"). Thomson drag on the photon dipole introduces an
    ℓ-dependent contribution. Rather than changing the W5-A state
    representation, this module returns a vector to be used in place
    of the scalar Γ in the ODE step.
    """
    gamma_vec = np.full(params.ell_max + 1, params.damping_rate)
    if (
        params.ell_max >= 1
        and drive.baryon_coupling is not None
    ):
        gamma_vec[1] = gamma_vec[1] + drive.baryon_coupling.tau_dot
    return gamma_vec


# ============================================================================
# Section 5 - Euler step and analytic steady state
# ============================================================================

def _euler_step_dipole_driven_unchecked(
    state: MultipoleState,
    params: HierarchyParameters,
    drive: DipoleDrive,
    dt: float,
) -> MultipoleState:
    """Private Euler step with dipole drive and baryon coupling. No gate."""
    M = build_streaming_matrix(params.k_eff, params.ell_max)
    b = build_dipole_driven_source_vector(params, drive)
    gamma_vec = build_damping_vector(params, drive)
    dot = M @ state.amplitudes - gamma_vec * state.amplitudes + b
    new_amps = state.amplitudes + dt * dot
    return MultipoleState(amplitudes=new_amps, axis=state.axis)


def euler_step_dipole_driven(
    state: MultipoleState,
    params: HierarchyParameters,
    drive: DipoleDrive,
    dt: float,
    decision: CanonicalDecision,
) -> MultipoleState:
    """One explicit Euler step of the dipole-driven hierarchy.

    When `drive.is_trivial`, this is bit-exact to W5-A `euler_step_hierarchy`.

    Stability note
    --------------
    The additional damping +τ̇ at ℓ=1 TIGHTENS the stability bound at
    that component. If τ̇ ≫ Γ, dt must satisfy dt × τ̇ ≲ 2 to keep
    explicit Euler stable; caller's responsibility. The implicit
    integrators of W5-B handle this regime.
    """
    require_allow_reduction(decision, context="euler_step_dipole_driven")
    if dt <= 0:
        raise ValueError(f"dt must be positive, got {dt}")
    if state.ell_max != params.ell_max:
        raise ValueError(
            f"state.ell_max ({state.ell_max}) != params.ell_max "
            f"({params.ell_max})"
        )
    if state.axis != params.shear.axis:
        raise ValueError(
            f"state axis {state.axis} != shear axis {params.shear.axis}"
        )
    return _euler_step_dipole_driven_unchecked(state, params, drive, dt)


def compute_steady_state_dipole_driven(
    params: HierarchyParameters,
    drive: DipoleDrive,
    decision: CanonicalDecision,
) -> MultipoleState:
    """Analytic steady state: (Γ_vec - M) Θ_∞ = b, with Γ_vec diagonal.

    When `drive.is_trivial`, reduces to W5-A
    `compute_steady_state_hierarchy` output bit-exactly.
    """
    require_allow_reduction(
        decision, context="compute_steady_state_dipole_driven",
    )
    gamma_vec = build_damping_vector(params, drive)
    # Trivial-dynamics guard identical to W5-A
    if np.all(gamma_vec == 0.0) and params.k_eff == 0:
        raise ValueError(
            "Γ_vec = 0 and k_eff = 0 gives trivial null dynamics — no "
            "unique steady state"
        )
    if drive.is_trivial:
        # Delegate to W5-A for bit-exact equivalence.
        return compute_steady_state_hierarchy(params, decision)

    M = build_streaming_matrix(params.k_eff, params.ell_max)
    b = build_dipole_driven_source_vector(params, drive)
    # Solve (diag(γ) − M) Θ = b
    A = np.diag(gamma_vec) - M
    # Numpy's linsolve is the standard approach; for this small system
    # (ell_max ≤ 20) conditioning is normally fine.
    try:
        theta_ss = np.linalg.solve(A, b)
    except np.linalg.LinAlgError as exc:
        raise ValueError(
            f"Steady-state linsolve failed: {exc}. System may be "
            f"degenerate (check Γ_vec and k_eff)."
        ) from exc
    return MultipoleState(amplitudes=theta_ss, axis=params.shear.axis)


def integrate_dipole_driven_to_steady_state(
    initial: MultipoleState,
    params: HierarchyParameters,
    drive: DipoleDrive,
    dt: float,
    decision: CanonicalDecision,
    max_steps: int = 5000,
    tolerance: float = 1e-6,
) -> HierarchyIntegrationResult:
    """Explicit Euler driver to steady state with dipole drive.

    Convergence criterion identical to W5-A
    `integrate_hierarchy_to_steady_state`:
        ||Θ^(n+1) − Θ^(n)|| / max(||Θ^(n+1)||, 1e-30)  <  tolerance.
    """
    require_allow_reduction(
        decision, context="integrate_dipole_driven_to_steady_state",
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

    # Analytic target
    gamma_vec = build_damping_vector(params, drive)
    has_dynamics = bool(np.any(gamma_vec > 0)) or params.k_eff > 0
    if has_dynamics:
        target = compute_steady_state_dipole_driven(
            params, drive, decision,
        )
    else:
        target = zero_state(params.ell_max, initial.axis)

    state = initial
    residual = float("inf")
    converged = False
    steps_taken = 0

    for step in range(max_steps):
        new_state = _euler_step_dipole_driven_unchecked(
            state, params, drive, dt,
        )
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
# Section 6 - Diagnostics
# ============================================================================

def cfl_max_dt_dipole_driven(
    params: HierarchyParameters,
    drive: DipoleDrive,
) -> float:
    """Approximate explicit-Euler stability bound dt_max = 2 / λ_max.

    λ_max is bounded above by  max(Γ_ℓ) + k_eff. When baryon coupling
    is on, Γ_1 = Γ + τ̇ typically dominates.
    """
    gamma_vec = build_damping_vector(params, drive)
    denom = float(np.max(gamma_vec)) + params.k_eff
    if denom <= 0:
        return float("inf")
    return 2.0 / denom


def tight_coupling_photon_residual(
    state: MultipoleState,
    drive: DipoleDrive,
) -> float:
    """Residual (Θ_1 − v_b/3) / max(|v_b/3|, 1e-30).

    Mirror of `baryon_fluid.tight_coupling_residual` (which computes
    (3Θ_1 − v_b)/|3Θ_1|). At tight coupling both → 0.

    Returns NaN if no baryon coupling is defined.

    No W3 gate: pure diagnostic.
    """
    if drive.baryon_coupling is None:
        return float("nan")
    if state.ell_max < 1:
        return float("nan")
    theta_1 = float(state.amplitudes[1])
    v_b_over_3 = drive.baryon_coupling.v_b / 3.0
    denom = max(abs(v_b_over_3), 1e-30)
    return (theta_1 - v_b_over_3) / denom
