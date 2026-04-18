"""
bass/transport/emode_hierarchy.py  (Week 7-01)
==============================================

E-mode polarization multipole hierarchy with spin-2 streaming coupling,
Thomson damping with ℓ=2 recoupling factor, and cross-coupling source
from external Θ_2 input.

Scope
-----
- Axisymmetric m=0 only (matches W5-A scalar baseline)
- ℓ ≥ 2 only (spin-2 requires ℓ ≥ |s| = 2; E_0, E_1 ≡ 0 structurally)
- Linear order — E-B decoupling (B-mode hierarchy deferred to W9)
- Source from external Θ_2 via Thomson cross-coupling at ℓ=2
- Self-consistent closure (Θ_2 ↔ E_2 bidirectional) → W7-02 scope

Equations (axisymmetric m=0)
----------------------------
    Ė_ℓ + k [α^E_ℓ E_{ℓ-1} − β^E_ℓ E_{ℓ+1}] = −Γ^E_ℓ E_ℓ + S^E_ℓ

Spin-2 streaming coefficients (Pontzen-Challinor 2007 Eq. 5.2):

    α^E_ℓ = √(ℓ² − 4) / (2ℓ + 1)            (ℓ ≥ 2; α^E_2 = 0)
    β^E_ℓ = √((ℓ+1)² − 4) / (2ℓ + 1)        (ℓ ≥ 2)

ℓ-dependent damping (document §3.3 collision formula for E-mode):

    Γ^E_2     = (2/5) Γ_T    [after absorbing (3/5) self-recoupling]
    Γ^E_ℓ≥3   = Γ_T          [uniform Thomson damping]

Cross-coupling source from external Θ_2 (ℓ=2 only):

    S^E_{ℓ=2} = − (3 / (5√6)) × Γ_T × Θ_2^external
    S^E_{ℓ≥3} = 0

Physical interpretation: Θ_2 > 0 drives E_2 < 0 via the coupling sign,
and the (−2/5) damping drags E_2 back toward zero. At isolated steady
state (k=0):

    E_2 = S_2 / Γ^E_2 = −(3/(5√6)) × (5/2) × Θ_2 = −(√6/4) Θ_2

which matches W6-04's subleading-S_E limit independently. This is the
**W6-04 ↔ W7-01 cross-check** test.

DampingProfile structure (v1.2 new pattern, Finding B.1/C.1)
-------------------------------------------------------------
EModeParameters introduces an explicit `ell2_damping_factor` (default
2/5) rather than embedding the factor implicitly. This prepares the
ground for the full `DampingProfile` refactoring scheduled at W7+ for
the temperature hierarchy (W5-A).

Not in scope (deferred)
-----------------------
- m ≠ 0 channels (B-mode mixing + rotation coefficients)
- B-mode hierarchy (coupling to E via shear at m=±1, ±2)
- Polter-based bidirectional recoupling (W7-02)
- Tilted-frame boost of spin-2 harmonics (W12)
- Polarization line-of-sight source g·Π (W8-03)

References
----------
- Pontzen & Challinor 2007 Eq. 5.2 (spin-2 streaming coefficients)
- CAMB notes §7.4 (polarization collision formula)
- Document §3.3 (textbook framework, collision block at ℓ=2)
- MASTER_PROMPT_LIST_bass_py_v1.2.md §4 W7-01
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import numpy as np

from bass.runtime.canonical_decision import (
    CanonicalDecision,
    require_allow_reduction,
)


# ============================================================================
# Section 1 - Spin-2 streaming coefficients
# ============================================================================

def pstf_emode_coupling_coeffs(ell: int, m: int = 0) -> Tuple[float, float]:
    """Spin-2 PSTF streaming coefficients (α^E_ℓ, β^E_ℓ) for axisymmetric m.

    For m = 0 (axisymmetric, Bianchi I diagonal shear):

        α^E_ℓ = √((ℓ² − m²)(ℓ² − 4)) / [ℓ(2ℓ+1)]
              = √(ℓ² − 4) / (2ℓ+1)                  (m=0 simplification)

        β^E_ℓ = √(((ℓ+1)² − m²)((ℓ+1)² − 4)) / [(ℓ+1)(2ℓ+1)]
              = √((ℓ+1)² − 4) / (2ℓ+1)              (m=0 simplification)

    Boundary: α^E_2 = 0 (spin-2 has no ℓ < 2 modes to couple from).

    Returns (α, β) as floats. Returns (0, 0) for ℓ < max(|m|, 2).
    """
    if ell < max(abs(m), 2):
        return 0.0, 0.0
    m_sq = m * m
    alpha_sq_num = (ell * ell - m_sq) * (ell * ell - 4)
    beta_sq_num = ((ell + 1) ** 2 - m_sq) * ((ell + 1) ** 2 - 4)
    # Guard against tiny negatives from floating-point
    alpha = np.sqrt(max(alpha_sq_num, 0.0)) / (ell * (2.0 * ell + 1.0))
    beta = np.sqrt(max(beta_sq_num, 0.0)) / ((ell + 1) * (2.0 * ell + 1.0))
    return float(alpha), float(beta)


# ============================================================================
# Section 2 - Parameter and state containers
# ============================================================================

@dataclass(frozen=True)
class EModeParameters:
    """E-mode hierarchy parameters with explicit damping profile.

    Attributes
    ----------
    thomson_rate : float
        Γ_T = a n_e σ_T, the conformal Thomson opacity (non-negative).
    k_eff : float
        Effective wavenumber k/S (non-negative).
    ell_max : int
        Maximum ℓ retained. Must be ≥ 2 (spin-2 requires ℓ ≥ 2).
    ell2_damping_factor : float
        Dimensionless factor multiplying Γ_T at ℓ=2 to account for the
        Thomson self-recoupling (3/5) × (E_2 - Θ_2/√6) absorbed into the
        damping vector. Default 2/5 = 1 − 3/5 (document §3.3).
        Exposed as parameter to support leading-order comparisons.

    Notes
    -----
    This parameterization is the v1.2 "DampingProfile" pattern prep:
    Thomson rate and ℓ-dependent factors are separate explicit fields,
    not implicit in a scalar `damping_rate`. The full retrofit to W5-A
    is scheduled per the v1.2 revision history.
    """
    thomson_rate: float
    k_eff: float
    ell_max: int
    ell2_damping_factor: float = 2.0 / 5.0

    def __post_init__(self) -> None:
        if not np.isfinite(self.thomson_rate) or self.thomson_rate < 0:
            raise ValueError(
                f"thomson_rate must be non-negative finite, "
                f"got {self.thomson_rate}"
            )
        if not np.isfinite(self.k_eff) or self.k_eff < 0:
            raise ValueError(
                f"k_eff must be non-negative finite, got {self.k_eff}"
            )
        if self.ell_max < 2:
            raise ValueError(
                f"ell_max must be ≥ 2 for spin-2 E-mode, got {self.ell_max}"
            )
        if (not np.isfinite(self.ell2_damping_factor)
                or self.ell2_damping_factor < 0):
            raise ValueError(
                f"ell2_damping_factor must be non-negative finite, "
                f"got {self.ell2_damping_factor}"
            )

    @property
    def state_dim(self) -> int:
        """Number of DOF: E_2, E_3, ..., E_{L_max}.  Equals ell_max − 1."""
        return self.ell_max - 1


@dataclass(frozen=True)
class EModeState:
    """E-mode multipole amplitudes E_ℓ for ℓ = 2, 3, ..., ell_max, m=0.

    Attributes
    ----------
    amplitudes : np.ndarray
        Shape (ell_max − 1,). amplitudes[i] = E_{i+2} for i = 0, ..., L_max−2.
    ell_max : int
        Maximum ℓ retained.
    """
    amplitudes: np.ndarray
    ell_max: int

    def __post_init__(self) -> None:
        if self.ell_max < 2:
            raise ValueError(
                f"ell_max must be ≥ 2, got {self.ell_max}"
            )
        expected_dim = self.ell_max - 1
        if self.amplitudes.shape != (expected_dim,):
            raise ValueError(
                f"amplitudes must have shape ({expected_dim},), "
                f"got {self.amplitudes.shape}"
            )
        if not np.all(np.isfinite(self.amplitudes)):
            raise ValueError("all amplitudes must be finite")

    def E_ell(self, ell: int) -> float:
        """Retrieve E_ℓ by physical index (ℓ ≥ 2)."""
        if ell < 2 or ell > self.ell_max:
            raise ValueError(
                f"ell must be in [2, {self.ell_max}], got {ell}"
            )
        return float(self.amplitudes[ell - 2])


def zero_emode_state(ell_max: int) -> EModeState:
    """Factory: zero E-mode state of given ell_max."""
    if ell_max < 2:
        raise ValueError(f"ell_max must be ≥ 2, got {ell_max}")
    return EModeState(
        amplitudes=np.zeros(ell_max - 1),
        ell_max=ell_max,
    )


# ============================================================================
# Section 3 - Streaming matrix
# ============================================================================

def build_emode_streaming_matrix(params: EModeParameters) -> np.ndarray:
    """Spin-2 streaming matrix M^E of shape (state_dim, state_dim).

    State index i corresponds to ℓ = i + 2. Entries:

        M^E[i, i-1] = +k_eff × α^E_{i+2}        (coupling from ℓ-1 below)
        M^E[i, i+1] = −k_eff × β^E_{i+2}        (coupling to ℓ+1 above)

    Boundary: M^E[0, *] has α^E_2 = 0 so the ℓ=1 coupling is identically
    zero (physically absent). The top row has β^E_{L_max} × E_{L_max+1}
    truncated (E_{L_max+1} ≡ 0).
    """
    dim = params.state_dim
    M = np.zeros((dim, dim))
    for i in range(dim):
        ell = i + 2
        alpha, beta = pstf_emode_coupling_coeffs(ell, m=0)
        if i - 1 >= 0:
            M[i, i - 1] = +params.k_eff * alpha
        if i + 1 < dim:
            M[i, i + 1] = -params.k_eff * beta
    return M


def build_emode_damping_vector(params: EModeParameters) -> np.ndarray:
    """Per-ℓ damping vector Γ^E_ℓ.

    Γ^E_2     = ell2_damping_factor × thomson_rate    (default 2/5 × Γ_T)
    Γ^E_ℓ≥3   = thomson_rate                          (uniform Γ_T)

    Returns vector of shape (state_dim,).
    """
    dim = params.state_dim
    gamma = np.full(dim, params.thomson_rate)
    if dim >= 1:  # at least E_2 exists
        gamma[0] = params.ell2_damping_factor * params.thomson_rate
    return gamma


def build_emode_source_vector(
    params: EModeParameters,
    theta_2_external: float = 0.0,
) -> np.ndarray:
    """External cross-coupling source vector s^E with entry at ℓ=2 only.

    s^E[ℓ=2] = − (3 / (5√6)) × Γ_T × Θ_2^external        (from document §3.3)
    s^E[ℓ≥3] = 0

    The sign is chosen so that Θ_2 > 0 drives E_2 < 0 at steady state,
    matching the subleading-S_E cross-coupling from W6-04 (E_2 = −√6/4 Θ_2).

    No W3 gate: pure algebra.
    """
    if not np.isfinite(theta_2_external):
        raise ValueError(
            f"theta_2_external must be finite, got {theta_2_external}"
        )
    dim = params.state_dim
    s = np.zeros(dim)
    if dim >= 1:
        sqrt6 = np.sqrt(6.0)
        coupling_coeff = 3.0 / (5.0 * sqrt6)  # absolute magnitude
        s[0] = -coupling_coeff * params.thomson_rate * theta_2_external
    return s


# ============================================================================
# Section 4 - Evolution and steady state
# ============================================================================

def _euler_step_emode_unchecked(
    state: EModeState,
    params: EModeParameters,
    theta_2_external: float,
    dt: float,
) -> EModeState:
    """Private Euler step. No gate, no shape checks."""
    M = build_emode_streaming_matrix(params)
    gamma = build_emode_damping_vector(params)
    s = build_emode_source_vector(params, theta_2_external)
    dot = M @ state.amplitudes - gamma * state.amplitudes + s
    new_amps = state.amplitudes + dt * dot
    return EModeState(amplitudes=new_amps, ell_max=state.ell_max)


def euler_step_emode(
    state: EModeState,
    params: EModeParameters,
    theta_2_external: float,
    dt: float,
    decision: CanonicalDecision,
) -> EModeState:
    """One forward-Euler step of the E-mode hierarchy.

    The full system:
        Ė_ℓ = [streaming] − Γ^E_ℓ E_ℓ + s^E_ℓ
    with s^E_2 = − (3/(5√6)) Γ_T × Θ_2^external and s^E_ℓ≥3 = 0.

    Stability (explicit-Euler CFL bound):
        dt × (max Γ^E + k_eff) ≲ 2
    """
    require_allow_reduction(decision, context="euler_step_emode")
    if dt <= 0:
        raise ValueError(f"dt must be positive, got {dt}")
    if state.ell_max != params.ell_max:
        raise ValueError(
            f"state.ell_max ({state.ell_max}) != params.ell_max "
            f"({params.ell_max})"
        )
    if not np.isfinite(theta_2_external):
        raise ValueError(
            f"theta_2_external must be finite, got {theta_2_external}"
        )
    return _euler_step_emode_unchecked(
        state, params, theta_2_external, dt,
    )


def compute_emode_steady_state(
    params: EModeParameters,
    theta_2_external: float,
    decision: CanonicalDecision,
) -> EModeState:
    """Analytic steady state from (diag(γ) − M) E = s.

    Equivalently: at Ė = 0,  [γ^E − M^E] · E = s^E, solved by linsolve.

    Raises
    ------
    ValueError if the system is singular (all Γ^E = 0 and k_eff = 0).
    """
    require_allow_reduction(decision, context="compute_emode_steady_state")
    if not np.isfinite(theta_2_external):
        raise ValueError(
            f"theta_2_external must be finite, got {theta_2_external}"
        )
    M = build_emode_streaming_matrix(params)
    gamma = build_emode_damping_vector(params)
    s = build_emode_source_vector(params, theta_2_external)
    if np.all(gamma == 0.0) and params.k_eff == 0.0:
        # Degenerate: no damping, no streaming. Steady state non-unique
        # unless source also vanishes (in which case zero state is a
        # trivial solution).
        if np.all(s == 0.0):
            return zero_emode_state(params.ell_max)
        raise ValueError(
            "trivial null dynamics (γ=0, k_eff=0) with non-zero source: "
            "no unique steady state"
        )
    A = np.diag(gamma) - M
    try:
        sol = np.linalg.solve(A, s)
    except np.linalg.LinAlgError as exc:
        raise ValueError(
            f"Steady-state linsolve failed: {exc}"
        ) from exc
    return EModeState(amplitudes=sol, ell_max=params.ell_max)


@dataclass(frozen=True)
class EModeIntegrationResult:
    """Outcome of integrate_emode_to_steady_state.

    Attributes
    ----------
    final_state : EModeState
    steps_taken : int
    converged : bool
    final_residual : float
        ||E^(n+1) − E^(n)|| / max(||E^(n+1)||, 1e-30) from the last step.
    steady_state_target : EModeState
        Analytic linsolve reference.
    """
    final_state: EModeState
    steps_taken: int
    converged: bool
    final_residual: float
    steady_state_target: EModeState


def integrate_emode_to_steady_state(
    initial: EModeState,
    params: EModeParameters,
    theta_2_external: float,
    dt: float,
    decision: CanonicalDecision,
    max_steps: int = 5000,
    tolerance: float = 1e-6,
) -> EModeIntegrationResult:
    """Explicit Euler driver to E-mode steady state."""
    require_allow_reduction(
        decision, context="integrate_emode_to_steady_state",
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

    gamma = build_emode_damping_vector(params)
    has_dynamics = bool(np.any(gamma > 0)) or params.k_eff > 0
    if has_dynamics:
        target = compute_emode_steady_state(
            params, theta_2_external, decision,
        )
    else:
        target = zero_emode_state(params.ell_max)

    state = initial
    residual = float("inf")
    converged = False
    steps_taken = 0

    for step in range(max_steps):
        new_state = _euler_step_emode_unchecked(
            state, params, theta_2_external, dt,
        )
        delta = new_state.amplitudes - state.amplitudes
        denom = max(float(np.linalg.norm(new_state.amplitudes)), 1e-30)
        residual = float(np.linalg.norm(delta)) / denom
        state = new_state
        steps_taken = step + 1
        if residual < tolerance:
            converged = True
            break

    return EModeIntegrationResult(
        final_state=state,
        steps_taken=steps_taken,
        converged=converged,
        final_residual=residual,
        steady_state_target=target,
    )


# ============================================================================
# Section 5 - Diagnostics
# ============================================================================

def cfl_max_dt_emode(params: EModeParameters) -> float:
    """Approximate explicit-Euler stability bound dt_max = 2 / λ_max.

    λ_max ≤ max(Γ^E) + k_eff. Returns 2 / (λ_max + 1e-300) to avoid
    div-by-zero; returns +inf when both Γ and k are zero.
    """
    gamma = build_emode_damping_vector(params)
    lambda_bound = float(np.max(gamma)) + params.k_eff
    if lambda_bound <= 0:
        return float("inf")
    return 2.0 / lambda_bound


def subleading_cross_check_ratio(
    state: EModeState,
    theta_2_external: float,
) -> float:
    """Deviation of E_2/Θ_2 from the W6-04 subleading target −√6/4.

    Returns (E_2 / Θ_2) / (−√6/4) − 1, zero iff the hierarchy is
    at the subleading-S_E limit. Returns NaN if Θ_2 = 0 or state has
    no ℓ=2 component (impossible for valid EModeState with ell_max ≥ 2).

    Used as a cross-check between W7-01 steady state and W6-04 TCA
    closure. At k_eff = 0 isolated ℓ=2, they must agree exactly.

    No W3 gate: pure diagnostic.
    """
    if state.ell_max < 2:
        return float("nan")
    if theta_2_external == 0.0:
        return float("nan")
    if not np.isfinite(theta_2_external):
        raise ValueError(
            f"theta_2_external must be finite, got {theta_2_external}"
        )
    E_2 = state.E_ell(2)
    target_ratio = -np.sqrt(6.0) / 4.0
    actual_ratio = E_2 / theta_2_external
    return float(actual_ratio / target_ratio - 1.0)
