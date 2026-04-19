"""
bass/closure/polter_recoupling.py  (Week 7-02)
===============================================

Polarization recoupling at ℓ=2: the Θ-side counterpart of W7-01 that
closes the bidirectional Θ_2 ↔ E_2 Thomson loop in the dynamical
temperature hierarchy.

Scope
-----
Non-invasive wrapper around W5-A temperature hierarchy (mirror of how
W6-02 wraps W5-A with ℓ=1 dipole drive). Adds polarization feedback at
ℓ=2 by:

  1. Reducing the effective damping at ℓ=2: Γ_T → (9/10) Γ_T
  2. Adding cross-coupling source at ℓ=2: -(√6/10) Γ_T × E_2^external

The E-side (W7-01) already handles the analogous modifications:
  Γ^E_2 = (2/5) Γ_T,  S^E_2 = -(3/(5√6)) Γ_T × Θ_2^external

Together, W5-A + W7-02 (for Θ) and W7-01 (for E), at tight-coupling
isolated ℓ=2 limit, reproduce W6-04's algebraic closure EXACTLY.

Physics (document §3.3 ℓ=2 collision formula)
----------------------------------------------
The temperature ℓ=2 collision is

    D Θ_2 / Dη |_coll = Γ_T [−Θ_2 + (1/10)(Θ_2 − √6 E_2)]
                      = −(9/10) Γ_T Θ_2 − (√6/10) Γ_T E_2

The first term replaces the W5-A uniform damping at ℓ=2 (factor 9/10
reduction from the polarization return channel). The second term is
the cross-coupling from E_2.

CAMB polter correspondence
--------------------------
CAMB defines  polter = pig/10 + 9 E_2/15  which enters both Θ_2 and
E_2 equations. In our PSTF convention, the polter analog at ℓ=2 is
the combined source Π = Θ_2 − √6 E_2. They are related by a
normalization constant (pinned at W10-02).

Not in scope (deferred)
-----------------------
- Joint (Θ, E) ODE solver stepping both hierarchies simultaneously → W9
- Tilted-frame boost of ℓ=2 recoupling → W12
- Line-of-sight polarization source g·Π → W8-03
- m ≠ 0 polarization recoupling → future when m≠0 is activated

References
----------
- Document §3.3 (textbook framework, collision at ℓ=2)
- Pontzen-Challinor 2007 Eq. 5.1 (temperature collision)
- W6-04 quadrupole TCA (algebraic closure)
- W7-01 E-mode hierarchy (E-side recoupling)
- MASTER_PROMPT_LIST_bass_py_v1.2.md §4 W7-02
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from bass.closure.quadrupole_tca import (
    combined_source_pi,
    polter_camb as polter_camb_formula,
    solve_tca_closure,
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
    euler_step_hierarchy,
    zero_state,
)


# ============================================================================
# Section 1 - PolterRecoupling configuration
# ============================================================================

@dataclass(frozen=True)
class PolterRecoupling:
    """Polarization recoupling at ℓ=2 driving the Θ hierarchy from E_2.

    Attributes
    ----------
    E_2_external : float
        External E-mode amplitude at ℓ=2, typically from a W7-01
        EModeState. Drives the Θ_2 equation via cross-coupling source.
    thomson_rate : float
        Γ_T = a n_e σ_T, the conformal Thomson opacity (non-negative).
        Used both for the (9/10) damping reduction at ℓ=2 and the
        magnitude of the E_2 cross-coupling source.
    has_polarization : bool, default True
        If False, no modification is applied (Θ hierarchy reduces to
        pure W5-A behavior — useful for isolating polarization effects
        in validation studies).
    """
    E_2_external: float = 0.0
    thomson_rate: float = 0.0
    has_polarization: bool = True

    def __post_init__(self) -> None:
        if not np.isfinite(self.E_2_external):
            raise ValueError(
                f"E_2_external must be finite, got {self.E_2_external}"
            )
        if not np.isfinite(self.thomson_rate) or self.thomson_rate < 0:
            raise ValueError(
                f"thomson_rate must be non-negative finite, "
                f"got {self.thomson_rate}"
            )

    @property
    def is_trivial(self) -> bool:
        """True iff this recoupling leaves the hierarchy bit-exact W5-A."""
        return (not self.has_polarization) or (self.thomson_rate == 0.0)


def no_polter_recoupling() -> PolterRecoupling:
    """Factory: trivial recoupling (W5-A-equivalent behavior)."""
    return PolterRecoupling(
        E_2_external=0.0, thomson_rate=0.0, has_polarization=False,
    )


# ============================================================================
# Section 2 - Polter utility (CAMB formula re-export)
# ============================================================================

def polter_camb(pig: float, E_2: float) -> float:
    """CAMB polter combined source: polter = pig/10 + 9 E_2 / 15.

    Thin re-export of `quadrupole_tca.polter_camb` for callers who
    want to consume the closure utilities via `bass.closure.polter_recoupling`
    exclusively.

    No W3 gate: pure algebra.
    """
    return polter_camb_formula(pig, E_2)


# ============================================================================
# Section 3 - Damping vector modification at ℓ=2
# ============================================================================

def build_polter_damping_vector(
    params: HierarchyParameters,
    recoupling: PolterRecoupling,
) -> np.ndarray:
    """Per-ℓ effective damping vector with ℓ=2 polarization reduction.

    Starts from the W5-A uniform damping Γ across all ℓ, then reduces
    the ℓ=2 entry by factor (9/10) when polarization is active:

        Γ_ℓ = Γ                  for ℓ ≠ 2 (or recoupling is trivial)
        Γ_2 = (9/10) × Γ         when recoupling is active

    Note
    ----
    The (9/10) factor comes from the (1/10) polarization return in the
    Thomson collision formula (document §3.3):

        collision = Γ_T × [-Θ_2 + (1/10)(Θ_2 - √6 E_2)]
                  = -Γ_T × (9/10) × Θ_2 + cross-coupling

    The cross-coupling from E_2 is placed in the source vector
    (Section 4) rather than the damping vector.
    """
    gamma_vec = np.full(params.ell_max + 1, params.damping_rate)
    if (
        params.ell_max >= 2
        and not recoupling.is_trivial
    ):
        gamma_vec[2] = (9.0 / 10.0) * params.damping_rate
    return gamma_vec


# ============================================================================
# Section 4 - Source vector modification at ℓ=2
# ============================================================================

def build_polter_driven_source_vector(
    params: HierarchyParameters,
    recoupling: PolterRecoupling,
) -> np.ndarray:
    """Source vector b with W5-A shear at ℓ=2 plus polarization cross-coupling.

    Components
    ----------
        b[ℓ≠2] : unchanged from W5-A
        b[2]   : Σ_2 σ + (polter contribution)

    The polter contribution at ℓ=2 is:

        -(√6 / 10) × Γ_T × E_2^external

    This is the term that enters the Θ_2 equation as an external drive
    from the polarization channel. Its sign is chosen so that positive
    E_2 reduces |Θ_2| at steady state (negative feedback when Θ_2 > 0
    and E_2 = -(√6/4) Θ_2 < 0).

    No W3 gate: pure algebra.
    """
    b = build_source_vector(params).copy()
    if (
        params.ell_max >= 2
        and not recoupling.is_trivial
    ):
        sqrt6 = np.sqrt(6.0)
        polter_source = (
            -(sqrt6 / 10.0) * recoupling.thomson_rate
            * recoupling.E_2_external
        )
        b[2] = b[2] + polter_source
    return b


# ============================================================================
# Section 5 - Euler step and steady state
# ============================================================================

def _euler_step_polter_driven_unchecked(
    state: MultipoleState,
    params: HierarchyParameters,
    recoupling: PolterRecoupling,
    dt: float,
) -> MultipoleState:
    """Private Euler step with polter recoupling. No gate, no checks."""
    M = build_streaming_matrix(params.k_eff, params.ell_max)
    b = build_polter_driven_source_vector(params, recoupling)
    gamma_vec = build_polter_damping_vector(params, recoupling)
    dot = M @ state.amplitudes - gamma_vec * state.amplitudes + b
    new_amps = state.amplitudes + dt * dot
    return MultipoleState(amplitudes=new_amps, axis=state.axis)


def euler_step_polter_driven(
    state: MultipoleState,
    params: HierarchyParameters,
    recoupling: PolterRecoupling,
    dt: float,
    decision: CanonicalDecision,
) -> MultipoleState:
    """One explicit Euler step of the polter-recoupled Θ hierarchy.

    When `recoupling.is_trivial`, this is bit-exact to W5-A
    `euler_step_hierarchy`.
    """
    require_allow_reduction(decision, context="euler_step_polter_driven")
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
    return _euler_step_polter_driven_unchecked(
        state, params, recoupling, dt,
    )


def compute_steady_state_polter_driven(
    params: HierarchyParameters,
    recoupling: PolterRecoupling,
    decision: CanonicalDecision,
) -> MultipoleState:
    """Analytic steady state (diag(γ) - M) Θ = b with polter recoupling.

    When `recoupling.is_trivial`, reduces to W5-A
    `compute_steady_state_hierarchy` output bit-exactly.
    """
    require_allow_reduction(
        decision, context="compute_steady_state_polter_driven",
    )
    if recoupling.is_trivial:
        return compute_steady_state_hierarchy(params, decision)

    gamma_vec = build_polter_damping_vector(params, recoupling)
    M = build_streaming_matrix(params.k_eff, params.ell_max)
    b = build_polter_driven_source_vector(params, recoupling)
    if np.all(gamma_vec == 0.0) and params.k_eff == 0.0:
        raise ValueError(
            "Γ = 0 and k_eff = 0 gives trivial null dynamics — no "
            "unique steady state"
        )
    A = np.diag(gamma_vec) - M
    try:
        theta_ss = np.linalg.solve(A, b)
    except np.linalg.LinAlgError as exc:
        raise ValueError(
            f"Polter-driven steady-state linsolve failed: {exc}"
        ) from exc
    return MultipoleState(amplitudes=theta_ss, axis=params.shear.axis)


def integrate_polter_driven_to_steady_state(
    initial: MultipoleState,
    params: HierarchyParameters,
    recoupling: PolterRecoupling,
    dt: float,
    decision: CanonicalDecision,
    max_steps: int = 5000,
    tolerance: float = 1e-6,
) -> HierarchyIntegrationResult:
    """Explicit Euler driver to steady state with polter recoupling."""
    require_allow_reduction(
        decision, context="integrate_polter_driven_to_steady_state",
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

    gamma_vec = build_polter_damping_vector(params, recoupling)
    has_dynamics = bool(np.any(gamma_vec > 0)) or params.k_eff > 0
    if has_dynamics:
        target = compute_steady_state_polter_driven(
            params, recoupling, decision,
        )
    else:
        target = zero_state(params.ell_max, initial.axis)

    state = initial
    residual = float("inf")
    converged = False
    steps_taken = 0

    for step in range(max_steps):
        new_state = _euler_step_polter_driven_unchecked(
            state, params, recoupling, dt,
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
# Section 6 - W6-04 joint consistency check
# ============================================================================

def joint_w604_consistency_residual(
    theta_2: float,
    E_2: float,
    S_T: float,
    S_E: float,
    gamma_T: float,
) -> float:
    """Residual of (Θ_2, E_2) against W6-04 algebraic closure.

    Computes ||Γ_T M X − S|| / max(||S||, 1e-30) where
        M = [[9/10, √6/10], [3/(5√6), 2/5]]
        X = [Θ_2, E_2]
        S = [S_T, S_E]

    At tight-coupling steady state, this residual is machine-precision
    zero. At non-tight regimes (running hierarchies dynamically), it
    quantifies the departure from algebraic closure.

    Use cases:
    1. Validate that a joint (Θ_2, E_2) pair from running W5A+W7-02 and
       W7-01 hierarchies agrees with W6-04 at tight coupling.
    2. Diagnostic for the "closure residual" of an approximate algorithm.

    No W3 gate: pure diagnostic.
    """
    if not np.isfinite(theta_2) or not np.isfinite(E_2):
        raise ValueError(
            f"theta_2 and E_2 must be finite, got {theta_2}, {E_2}"
        )
    if not np.isfinite(S_T) or not np.isfinite(S_E):
        raise ValueError(
            f"S_T and S_E must be finite, got {S_T}, {S_E}"
        )
    if gamma_T < 0 or not np.isfinite(gamma_T):
        raise ValueError(
            f"gamma_T must be non-negative finite, got {gamma_T}"
        )
    sqrt6 = np.sqrt(6.0)
    lhs_T = gamma_T * ((9.0 / 10.0) * theta_2 + (sqrt6 / 10.0) * E_2)
    lhs_E = gamma_T * ((3.0 / (5.0 * sqrt6)) * theta_2 + (2.0 / 5.0) * E_2)
    res_T = lhs_T - S_T
    res_E = lhs_E - S_E
    residual_norm = float(np.sqrt(res_T * res_T + res_E * res_E))
    source_norm = max(float(np.sqrt(S_T * S_T + S_E * S_E)), 1e-30)
    return residual_norm / source_norm


# ============================================================================
# Section 7 - Diagnostics
# ============================================================================

def cfl_max_dt_polter_driven(
    params: HierarchyParameters,
    recoupling: PolterRecoupling,
) -> float:
    """Approximate explicit-Euler stability bound 2 / (max(Γ) + k).

    When recoupling is active, Γ_2 is REDUCED by (9/10), so the CFL
    bound slightly relaxes at ℓ=2. But max(Γ_ℓ) is still dominated by
    the uniform Γ elsewhere, so the bound is essentially unchanged.
    """
    gamma_vec = build_polter_damping_vector(params, recoupling)
    denom = float(np.max(gamma_vec)) + params.k_eff
    if denom <= 0:
        return float("inf")
    return 2.0 / denom
