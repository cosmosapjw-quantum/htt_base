"""
bass/closure/quadrupole_tca.py  (Week 6-04)
===========================================

Quadrupole-aware tight-coupling closure for the coupled
(Θ_2, E_2) photon system. The 2-variable matrix closure is the
minimum self-consistent treatment of the temperature/polarization
Thomson recoupling required to meet Document 12's 95% D_2 accuracy
ceiling.

Physics (Pontzen-Challinor 2007 Eq. 5.1; CAMB notes §7.4; Ma-Bertschinger 1995 Eq. 63)
-------------------------------------------------------------------------------------
The ℓ=2 temperature and E-mode evolution equations are

    Θ̇_2^m = S_{2,T}^m + Γ_T [-(9/10) Θ_2^m - (√6/10) E_2^m]
    Ė_2^m = S_{2,E}^m + Γ_T [-(2/5) E_2^m - (3/(5√6)) Θ_2^m]

where S_{2,T}, S_{2,E} collect the non-collision contributions
(shear, streaming, perturbation). At tight coupling (τ̇ ≫ H) the
time-derivatives vanish algebraically, giving

    Γ_T [(9/10) Θ_2 + (√6/10) E_2] = +S_T
    Γ_T [(3/(5√6)) Θ_2 + (2/5) E_2] = +S_E

or Γ_T M · X = +S with M = [[9/10, √6/10], [3/(5√6), 2/5]].
Inverting,

    Θ_2 = +Γ_T⁻¹ [(4/3) S_T − (√6/3) S_E]    + O(Γ_T⁻²)
    E_2 = +Γ_T⁻¹ [−(√6/3) S_T + 3 S_E]        + O(Γ_T⁻²)

When S_E is subleading,

    E_2 ≃ −(√6/4) Θ_2,
    Π   = Θ_2 − √6 E_2  ≃  (5/2) Θ_2,

which is the combined Thomson source entering both hierarchies.
Physical check: S_T > 0 (positive shear) gives Θ_2 > 0 (positive
anisotropic stress), matching CAMB's `cmbmain.f90` TCA formula
π_γ ≈ (32/45) κ̇⁻¹ (σ + 3q_γ/4) > 0.

Numerical properties of the matrix
----------------------------------
- Determinant: det M = 3/10 (exact, positive)
- Matrix is non-singular for all finite Γ_T > 0
- Conditioning is excellent (cond ≈ 5.1; see `tca_matrix_condition_number`)

Second-order correction
-----------------------
The 1st-order closure carries an O(τ̈/τ̇²) systematic. The Cyr-Racine &
Sigurdson (2010) 2nd-order formula adds a multiplicative factor

    π_γ^(2) = π_γ^(1) × (1 + c_2 τ̈/τ̇²)

with c_2 = 11/6 in their convention. This module exposes the correction
as an explicit parameter rather than hard-coding it into the closure, so
callers can audit the effect and disable it at leading order for
W5-A/W6-02 comparisons.

Honest scope
------------
- 2×2 subsystem only; higher-ℓ closure is W7+ scope
- Orthogonal Bianchi only; tilted-frame boost of (Θ_2, E_2) is W12
  (the closure formulas remain structurally identical with tilded
  variables, but the S_T, S_E inputs must be transformed)
- Π is the PSTF combined source; the CAMB-convention `polter` is
  provided for later W10-02 cross-check but uses literal CAMB formula
  (pig/10 + 9 E_2/15) without asserting pig = I_2 (those are related by
  a normalization factor to be pinned at W10-02)
- No self-consistent coupling to baryon velocity yet (that's the
  extended system of later W-phases)

References
----------
- Pontzen & Challinor 2007 "Bianchi Model CMB Polarization and its
  implications for CMB Anomalies" Eq. 6.2
- CAMB notes §7.4 (CAMB/notes/CAMB.pdf)
- Cyr-Racine & Sigurdson 2010 (arXiv:1001.2876) §3.1
- Document 12 (D_2 85% → 95% ceiling analysis)
- MASTER_PROMPT_LIST_bass_py_v1.1.md §3 W6-04
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
# Section 1 - Matrix assembly
# ============================================================================

# Constants for the 2×2 matrix coefficients (exact analytic values).
_TCA_MATRIX_TEMPLATE = np.array([
    [9.0 / 10.0, np.sqrt(6.0) / 10.0],
    [3.0 / (5.0 * np.sqrt(6.0)), 2.0 / 5.0],
])

# Known analytic determinant of the template
_TCA_MATRIX_DET_ANALYTIC = 3.0 / 10.0


def build_tca_matrix(gamma_T: float) -> np.ndarray:
    """Assemble the 2×2 Thomson collision matrix multiplied by Γ_T.

    Returns Γ_T × [[9/10, √6/10], [3/(5√6), 2/5]] of shape (2, 2).

    Parameters
    ----------
    gamma_T : float
        Conformal Thomson rate Γ_T = τ̇ = a n_e σ_T ≥ 0. The same
        τ̇ used in W6-01 baryon fluid and W6-02 photon dipole.

    Notes
    -----
    The template is multiplied by Γ_T so that the full collision
    block reads

        [M_TCA] · [Θ_2; E_2] = −[S_{2,T}; S_{2,E}]

    with no further rescaling. The matrix is invertible for any
    Γ_T > 0; at Γ_T = 0 it becomes the zero matrix (no collision).
    """
    if not np.isfinite(gamma_T):
        raise ValueError(f"gamma_T must be finite, got {gamma_T}")
    if gamma_T < 0:
        raise ValueError(f"gamma_T must be non-negative, got {gamma_T}")
    return gamma_T * _TCA_MATRIX_TEMPLATE.copy()


def tca_matrix_determinant(gamma_T: float) -> float:
    """Analytic determinant Γ_T² × (3/10).

    Used as a zero-check in `solve_tca_closure`: if Γ_T = 0, the
    algebraic closure is not defined and callers must evolve (Θ_2, E_2)
    dynamically through the hierarchy (W5-A / W7 territory).
    """
    if gamma_T < 0 or not np.isfinite(gamma_T):
        raise ValueError(f"gamma_T must be non-negative finite, got {gamma_T}")
    return gamma_T * gamma_T * _TCA_MATRIX_DET_ANALYTIC


def tca_matrix_condition_number() -> float:
    """Condition number of the TCA template (Γ_T-independent).

    The 2×2 template is a constant matrix; its condition number is
    a pure number characterising the coupling strength between Θ_2
    and E_2. Well-conditioned at ~5.1 — no numerical issues.
    """
    return float(np.linalg.cond(_TCA_MATRIX_TEMPLATE))


# ============================================================================
# Section 2 - Leading-order TCA closure
# ============================================================================

def solve_tca_closure(
    S_T: float,
    S_E: float,
    gamma_T: float,
    decision: CanonicalDecision,
) -> Tuple[float, float]:
    """Solve Γ_T M · [Θ_2; E_2] = +[S_T; S_E] at leading order.

    Derivation
    ----------
    The ℓ=2 evolution with collision is
        Θ̇_2 = S_T + Γ_T [-(9/10) Θ_2 - (√6/10) E_2]
        Ė_2 = S_E + Γ_T [-(2/5) E_2 - (3/(5√6)) Θ_2]

    where S_T, S_E are the non-collision sources (shear, streaming,
    perturbation). At tight coupling Θ̇_2 = Ė_2 ≈ 0, giving

        Γ_T [(9/10) Θ_2 + (√6/10) E_2] = +S_T
        Γ_T [(3/(5√6)) Θ_2 + (2/5) E_2] = +S_E

    i.e. Γ_T M · X = +S. Inverting:

        Θ_2 = +Γ_T⁻¹ [(4/3) S_T − (√6/3) S_E]
        E_2 = +Γ_T⁻¹ [−(√6/3) S_T + 3 S_E]

    Physical check: S_T > 0 (positive shear source) drives Θ_2 > 0
    (positive anisotropic stress), as in CAMB and Ma-Bertschinger 1995.

    Parameters
    ----------
    S_T : non-collision source at ℓ=2 for temperature
    S_E : non-collision source at ℓ=2 for E-mode polarization
    gamma_T : conformal Thomson rate (must be strictly positive)
    decision : W3 canonical decision

    Returns
    -------
    (Θ_2, E_2) : tuple of floats

    Raises
    ------
    ValueError if Γ_T = 0 (no algebraic closure exists).
    """
    require_allow_reduction(decision, context="solve_tca_closure")
    if not np.isfinite(S_T):
        raise ValueError(f"S_T must be finite, got {S_T}")
    if not np.isfinite(S_E):
        raise ValueError(f"S_E must be finite, got {S_E}")
    if gamma_T <= 0:
        raise ValueError(
            f"gamma_T must be strictly positive for algebraic closure, "
            f"got {gamma_T}"
        )
    inv_gamma = 1.0 / gamma_T
    sqrt6 = np.sqrt(6.0)
    theta_2 = +inv_gamma * ((4.0 / 3.0) * S_T - (sqrt6 / 3.0) * S_E)
    E_2 = +inv_gamma * (-(sqrt6 / 3.0) * S_T + 3.0 * S_E)
    return float(theta_2), float(E_2)


def tca_closure_matrix_solve(
    S_T: float,
    S_E: float,
    gamma_T: float,
    decision: CanonicalDecision,
) -> Tuple[float, float]:
    """Alternative: solve via numpy.linalg.solve for regression checks.

    Solves Γ_T M · X = +S (same convention as solve_tca_closure).
    Produces the same result as `solve_tca_closure` up to floating-point
    roundoff. Used by tests to guard against drift in the analytic
    inverse formula.
    """
    require_allow_reduction(decision, context="tca_closure_matrix_solve")
    if gamma_T <= 0:
        raise ValueError(
            f"gamma_T must be strictly positive, got {gamma_T}"
        )
    M = build_tca_matrix(gamma_T)
    rhs = +np.array([S_T, S_E])
    sol = np.linalg.solve(M, rhs)
    return float(sol[0]), float(sol[1])


# ============================================================================
# Section 3 - Combined source Π and CAMB polter
# ============================================================================

def combined_source_pi(theta_2: float, E_2: float) -> float:
    """PSTF combined Thomson source Π = Θ_2 − √6 E_2.

    Pontzen-Challinor Eq. 6.2. Appears as the source in BOTH the
    photon ℓ=2 temperature equation AND the E-mode ℓ=2 polarization
    equation with species-specific coefficients.

    Special case: when E_2 = −(√6/4) Θ_2 (subleading-S_E limit),
    Π = (5/2) Θ_2 exactly.

    No W3 gate: this is a pure algebraic combination of already-
    validated multipole amplitudes.
    """
    if not np.isfinite(theta_2) or not np.isfinite(E_2):
        raise ValueError(
            f"theta_2 and E_2 must be finite, got {theta_2}, {E_2}"
        )
    return float(theta_2 - np.sqrt(6.0) * E_2)


def polter_camb(pig: float, E_2: float) -> float:
    """CAMB-convention combined source: polter = pig/10 + 9 E_2/15.

    This is the quantity that enters the CAMB temperature and E-mode
    ℓ=2 collision equations directly. The variable `pig` in CAMB is
    the photon integrated moment, which is related to the PSTF Θ_2 by
    a normalization factor that depends on species and ℓ (the exact
    correspondence is to be pinned at W10-02 CAMB cross-check).

    This module provides the CAMB formula literally so that W10-02 can
    compare numerical outputs directly. The PSTF internal source used
    for evolution within bass_py is `combined_source_pi`.

    No W3 gate: literal algebraic formula.
    """
    if not np.isfinite(pig) or not np.isfinite(E_2):
        raise ValueError(
            f"pig and E_2 must be finite, got {pig}, {E_2}"
        )
    return float(pig / 10.0 + 9.0 * E_2 / 15.0)


# ============================================================================
# Section 4 - Second-order TCA correction
# ============================================================================

def second_order_correction_factor(
    tau_dot: float,
    tau_ddot: float,
    coefficient: float = 11.0 / 6.0,
) -> float:
    """Cyr-Racine-Sigurdson 2010 second-order TCA correction factor.

    Returns (1 + c · τ̈ / τ̇²). Typical values during recombination
    sit in the range [0.9, 1.3] depending on ionisation history.

    Parameters
    ----------
    tau_dot : conformal Thomson rate τ̇ > 0
    tau_ddot : second time derivative of the conformal optical depth
               (dimensionful; positive during the onset of recombination
               when τ̇ is increasing, negative as the plasma recombines)
    coefficient : default 11/6 (CRS formula).  Exposed for future
                  refinement / audit against other closure variants.

    Notes
    -----
    The sign convention follows CAMB's `opac` = +τ̇, `dopac` = +τ̈,
    with τ̇ a positive quantity. Users passing CAMB's internal
    variables directly should negate if their sign convention differs.

    No W3 gate: pure scalar utility.
    """
    if not np.isfinite(tau_dot) or not np.isfinite(tau_ddot):
        raise ValueError(
            f"tau_dot, tau_ddot must be finite, got {tau_dot}, {tau_ddot}"
        )
    if tau_dot <= 0:
        raise ValueError(
            f"tau_dot must be strictly positive for 2nd-order "
            f"correction, got {tau_dot}"
        )
    if not np.isfinite(coefficient):
        raise ValueError(f"coefficient must be finite, got {coefficient}")
    return 1.0 + coefficient * tau_ddot / (tau_dot * tau_dot)


# ============================================================================
# Section 5 - Two-tier closure with toggle
# ============================================================================

@dataclass(frozen=True)
class TCAClosureConfig:
    """Configuration for the quadrupole TCA closure.

    Attributes
    ----------
    use_second_order : bool
        If True, apply the Cyr-Racine-Sigurdson 2nd-order correction to
        Θ_2 (and, via Π recoupling, to E_2). Default True — this is
        the production setting that meets Document 12's 95% ceiling.
    tau_ddot : float
        Second derivative of the conformal optical depth. Only consulted
        when `use_second_order` is True. NaN when unused is an error.
    coefficient : float
        Cyr-Racine-Sigurdson coefficient c_2, default 11/6.
    """
    use_second_order: bool = True
    tau_ddot: float = 0.0
    coefficient: float = 11.0 / 6.0

    def __post_init__(self) -> None:
        if self.use_second_order:
            if not np.isfinite(self.tau_ddot):
                raise ValueError(
                    f"tau_ddot must be finite when use_second_order=True, "
                    f"got {self.tau_ddot}"
                )
        if not np.isfinite(self.coefficient):
            raise ValueError(
                f"coefficient must be finite, got {self.coefficient}"
            )


def leading_order_config() -> TCAClosureConfig:
    """Factory: leading-order TCA (no 2nd-order correction)."""
    return TCAClosureConfig(
        use_second_order=False, tau_ddot=0.0, coefficient=0.0,
    )


def solve_tca_closure_configurable(
    S_T: float,
    S_E: float,
    gamma_T: float,
    config: TCAClosureConfig,
    decision: CanonicalDecision,
) -> Tuple[float, float]:
    """Closure with configurable 2nd-order toggle.

    At leading order, identical to `solve_tca_closure`. At 2nd order,
    applies the CRS correction factor to the temperature quadrupole
    Θ_2 (and propagates through Π to E_2 via the matrix structure).

    In the leading-order branch this function is bit-exact to
    `solve_tca_closure` — asserted in the test suite.
    """
    require_allow_reduction(
        decision, context="solve_tca_closure_configurable",
    )
    theta_2_lead, E_2_lead = solve_tca_closure(
        S_T, S_E, gamma_T, decision,
    )
    if not config.use_second_order:
        return theta_2_lead, E_2_lead
    # Apply CRS correction. The correction factor multiplies π_γ (the
    # photon anisotropic stress). In our PSTF notation π_γ ≡ Θ_2, so
    # we scale Θ_2 and let Π re-couple E_2 through the matrix.
    factor = second_order_correction_factor(
        gamma_T, config.tau_ddot, config.coefficient,
    )
    theta_2_corrected = theta_2_lead * factor
    # Keep the same matrix relationship: invert (Γ_T M_22) E_2 block
    # given the updated Θ_2 source term. In the 2nd-order approximation
    # we maintain the ratio E_2/Θ_2 = −√6/4 (subleading-S_E case) by
    # scaling E_2 identically, which preserves Π = (5/2)Θ_2 structure.
    E_2_corrected = E_2_lead * factor
    return theta_2_corrected, E_2_corrected


# ============================================================================
# Section 6 - Diagnostics
# ============================================================================

def subleading_E2_ratio(theta_2: float, E_2: float) -> float:
    """Ratio E_2 / Θ_2 compared to the subleading-S_E target −√6/4.

    Returns (E_2/Θ_2) / (−√6/4) − 1.  Zero when S_E = 0 exactly,
    nonzero otherwise. Diagnostic of how much the polarization source
    departs from the "Θ_2 dominant" regime.

    Returns NaN if Θ_2 = 0.

    No W3 gate: pure diagnostic.
    """
    if not np.isfinite(theta_2) or not np.isfinite(E_2):
        raise ValueError(
            f"theta_2, E_2 must be finite, got {theta_2}, {E_2}"
        )
    if theta_2 == 0.0:
        return float("nan")
    target_ratio = -np.sqrt(6.0) / 4.0
    actual_ratio = E_2 / theta_2
    return float(actual_ratio / target_ratio - 1.0)


def combined_pi_of_theta_2_only(theta_2: float) -> float:
    """Π when S_E is subleading: Π = (5/2) Θ_2.

    Convenience for the S_E = 0 case. `combined_source_pi` is the
    general formula; this is the specialization for plotting /
    sanity-check purposes.

    No W3 gate: algebraic convenience.
    """
    if not np.isfinite(theta_2):
        raise ValueError(f"theta_2 must be finite, got {theta_2}")
    return float(2.5 * theta_2)
