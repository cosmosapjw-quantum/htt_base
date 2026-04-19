"""
bass/transport/visibility_polter_source.py  (Week 8-03)
=======================================================

Line-of-sight (LOS) visibility-weighted polarization source:

    Source node at recombination:    g(η) · Π(η)

where  g(η) = τ̇(η) e^{-κ(η)}  is the Thomson visibility (W8-01 /
W8-02 extended for reionization) and  Π = Θ_2 − √6 E_2  is the PSTF
combined quadrupole source (W6-04 algebraic closure).

Scope (narrow, declared)
------------------------
Document 12 ceiling item 2/3. This module assembles ONLY the
g · Π product needed at recombination as a LOS integrand node.
Full LOS quadrature (Bessel weighting, ISW, Doppler) is deferred
to W9-01. Bianchi-I direction-dependent extension is W11+.

What IS in scope
----------------
* g · Π evaluated at arbitrary z within the recombination table
* Three independent paths for Π, cross-checked at machine precision
  - Path A: combined_source_pi(Θ_2, E_2)  (W6-04 direct algebra)
  - Path B: (5/2) · Θ_2                   (analytic subleading limit)
  - Path C: solve_tca_closure(S_T, S_E, Γ_T) → (Θ_2, E_2) → Π
* Optional CAMB polter = pig/10 + 9 E_2/15 co-evaluation
  (normalization constant vs PSTF Π pinned at W10-02)
* Peak and trapezoidal-integral diagnostics (z-space, pedagogical)
* Light flat-ΛCDM η(z) utility (upgraded at W9-01)

What is NOT in scope (deferred)
-------------------------------
* Full LOS integral  ∫ dη S_T(η) j_ℓ[k(η_0 − η)]      → W9-01
* ISW term  e^{−κ}(Ψ̇ + Φ̇)                           → W9-02
* Doppler term  d(g · v_b)/dη                          → W9-01
* Bianchi-I tilted-frame g · Π                         → W11+
* m ≠ 0 polter recoupling                              → future
* PSTF-to-CAMB polter normalization constant           → W10-02

Physical sign contract (v1.2 pattern)
-------------------------------------
1. g(z) > 0 for all z in the table range.
2. At subleading limit (S_E = 0):  Π has the SAME sign as Θ_2,
   with magnitude |Π| = (5/2) |Θ_2|.
3. g · Π peaks near the surface of last scattering (z ≈ 1089),
   NOT near reionization (z ≈ 7), when Θ_2(z) is slowly varying.
4. CAMB polter and PSTF Π share the sign of their common E_2
   dependence (both are positive in E_2 when pig / Θ_2 > 0).

References
----------
- Document §3 line-of-sight source assembly
- Ma-Bertschinger 1995, Eq. 63-64 (synchronous LOS)
- Lewis & Challinor 2002, CMB polarization
- Pontzen-Challinor 2007 Eq. 6.2 (PSTF Π convention)
- W6-04 quadrupole_tca (algebraic closure)
- W7-02 polter_recoupling (dynamical loop)
- W8-01 recombination_ingest (Thomson rate / optical depth splines)
- W8-02 reionization (tanh extension of κ, g)
- MASTER_PROMPT_LIST_bass_py_v1.2.md §4 W8-03
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional, Tuple, Union

import numpy as np
from scipy.integrate import quad

from bass.closure.quadrupole_tca import (
    build_tca_matrix,
    combined_source_pi,
    polter_camb,
    solve_tca_closure,
)
from bass.recombination.recombination_ingest import (
    RecombinationInterp,
    find_visibility_peak,
)
from bass.recombination.reionization import CosmologyForRecombination
from bass.runtime.canonical_decision import CanonicalDecision


# ============================================================================
# Section 0 - Physical constants
# ============================================================================

C_M_PER_S = 299_792_458.0
MPC_IN_METERS = 3.085_677_581_491_367e22
C_IN_MPC_PER_S = C_M_PER_S / MPC_IN_METERS  # ≈ 9.716e-15 Mpc/s


# ============================================================================
# Section 1 - Configuration
# ============================================================================

@dataclass(frozen=True)
class VisibilityPolterConfig:
    """Immutable configuration for the LOS visibility-polter source node.

    Parameters
    ----------
    recomb_interp : RecombinationInterp
        Cubic-spline interpolators built from a recombination table.
        Caller is responsible for ensuring reionization has been
        folded in via `extend_table_with_reionization` when relevant.
    use_camb_polter : bool, default False
        When False, evaluate g · Π with PSTF Π = Θ_2 − √6 E_2.
        When True, evaluate g · polter_camb(pig, E_2) with CAMB's
        convention (pig/10 + 9 E_2/15). Both are exposed so that
        W10-02 CAMB V-gate can compare directly without re-wiring.
    polter_camb_normalization : Optional[float], default None
        Reserved for W10-02. Not applied in this module. Present in
        the dataclass so that API consumers can keep one call site.

    Notes
    -----
    No W3 gate. This module performs pure data transformation and
    interpolation; no σ²-reduction operations.
    """
    recomb_interp: RecombinationInterp
    use_camb_polter: bool = False
    polter_camb_normalization: Optional[float] = None

    def __post_init__(self) -> None:
        if not isinstance(self.use_camb_polter, bool):
            raise TypeError(
                f"use_camb_polter must be bool, got "
                f"{type(self.use_camb_polter).__name__}"
            )
        if (
            self.polter_camb_normalization is not None
            and not np.isfinite(self.polter_camb_normalization)
        ):
            raise ValueError(
                "polter_camb_normalization must be finite or None"
            )

    @property
    def is_camb_mode(self) -> bool:
        return self.use_camb_polter


# ============================================================================
# Section 2 - Pure Π combiners (three independent paths)
# ============================================================================

def pi_pstf(theta_2: float, E_2: float) -> float:
    """PSTF combined source Π = Θ_2 − √6 E_2  (Path A).

    Thin re-export of `quadrupole_tca.combined_source_pi` so that
    downstream callers can address all three paths through this module.
    No W3 gate: pure algebra.
    """
    return combined_source_pi(theta_2, E_2)


def pi_subleading_limit(theta_2: float) -> float:
    """Π in the subleading-S_E limit: Π = (5/2) Θ_2  (Path B).

    Derivation. At isolated ℓ=2 tight coupling with S_E = 0, the
    TCA closure gives E_2 = −(√6/4) Θ_2 (W6-04 §3). Substituting
    into Π = Θ_2 − √6 E_2:

        Π = Θ_2 − √6 · (−√6/4) Θ_2 = (1 + 6/4) Θ_2 = (5/2) Θ_2.

    No W3 gate: analytic identity.
    """
    if not np.isfinite(theta_2):
        raise ValueError(f"theta_2 must be finite, got {theta_2}")
    return float(2.5 * theta_2)


def pi_from_tca_sources(
    S_T: float,
    S_E: float,
    gamma_T: float,
    decision: CanonicalDecision,
) -> float:
    """Π obtained by solving the TCA closure for (Θ_2, E_2) then combining
    (Path C).

    Given Thomson rate Γ_T and source doublet (S_T, S_E), solve

        Γ_T M (Θ_2, E_2)^T = (S_T, S_E)^T        (W6-04 §3, sign-v1.2)

    for (Θ_2, E_2) and return Π = Θ_2 − √6 E_2. This path exercises
    the full W6-04 matrix, giving an independent numerical result
    that must agree with Path A at machine precision.

    W3 gate: required. Caller must supply a `CanonicalDecision`
    produced by `bass.runtime.canonical_decision.make_canonical_decision`.
    Direct construction is not a sanctioned path.
    """
    theta_2, E_2 = solve_tca_closure(S_T, S_E, gamma_T, decision)
    return combined_source_pi(theta_2, E_2)


def pi_closed_form_from_sources(
    S_T: float,
    S_E: float,
    gamma_T: float,
) -> float:
    """Π as a closed-form function of the source doublet (Path D).

    Derivation. W6-04 gives  Γ_T M (Θ_2, E_2)^T = (S_T, S_E)^T  with

        M = [[9/10, √6/10], [3/(5√6), 2/5]],    det M = 3/10.

    Inverting and substituting into Π = Θ_2 − √6 E_2 yields a purely
    algebraic closed form that does NOT call `np.linalg.solve`:

        Π = (10 / (3 Γ_T)) · (S_T − √6 S_E).

    Validation limits.
    * At S_E = 0: Π = (10/(3Γ_T)) S_T, equivalent to (5/2) Θ_2 via
      the subleading amplification S_T = (3/4) Γ_T Θ_2.
    * At Θ_2 = 0 (pure E source): S_T = (√6/10) Γ_T E_2, S_E =
      (2/5) Γ_T E_2 ⇒ formula gives −√6 E_2, matching Π definition.

    This is the independent Path D used in
    `four_path_pi_residual_general` for genuine non-trivial
    cross-checks. No W3 gate.
    """
    if not (np.isfinite(S_T) and np.isfinite(S_E) and np.isfinite(gamma_T)):
        raise ValueError("S_T, S_E, gamma_T must be finite")
    if gamma_T <= 0:
        raise ValueError(f"gamma_T must be positive, got {gamma_T}")
    return float((10.0 / (3.0 * gamma_T)) * (S_T - np.sqrt(6.0) * S_E))


def polter_camb_at(pig: float, E_2: float) -> float:
    """CAMB-convention combined source polter = pig/10 + 9 E_2/15.

    Thin re-export of `quadrupole_tca.polter_camb` at module level for
    W10-02 V-gate consumers. No W3 gate.
    """
    return polter_camb(pig, E_2)


# ============================================================================
# Section 3 - Visibility-weighted Π
# ============================================================================

def g_weighted_pi_pstf(
    z: Union[float, np.ndarray],
    theta_2: Union[float, np.ndarray],
    E_2: Union[float, np.ndarray],
    config: VisibilityPolterConfig,
) -> np.ndarray:
    """Evaluate  g(z) · Π_PSTF(z)  with Π = Θ_2 − √6 E_2.

    Both `z` and the multipole inputs may be scalar or vector; they are
    broadcast pairwise. The visibility is pulled from
    `config.recomb_interp.query_visibility(z)`.

    No W3 gate: pure combination.
    """
    z_arr = np.atleast_1d(np.asarray(z, dtype=float))
    theta_arr = np.atleast_1d(np.asarray(theta_2, dtype=float))
    E_arr = np.atleast_1d(np.asarray(E_2, dtype=float))
    # Broadcast against visibility grid
    g_arr = config.recomb_interp.query_visibility(z_arr)
    g_arr = np.atleast_1d(g_arr)
    # Manual Π to keep scalar-broadcast semantics
    pi_arr = theta_arr - np.sqrt(6.0) * E_arr
    result = g_arr * pi_arr
    if np.ndim(z) == 0 and np.ndim(theta_2) == 0 and np.ndim(E_2) == 0:
        return float(result[0])
    return result


def g_weighted_polter_camb(
    z: Union[float, np.ndarray],
    pig: Union[float, np.ndarray],
    E_2: Union[float, np.ndarray],
    config: VisibilityPolterConfig,
) -> np.ndarray:
    """Evaluate  g(z) · polter_CAMB(pig, E_2)  with polter = pig/10 + 9 E_2/15.

    Exposed in parallel with `g_weighted_pi_pstf` so that W10-02 CAMB
    V-gate can compare outputs directly. The PSTF-to-CAMB
    normalization constant is not applied here (W10-02 deliverable).
    """
    z_arr = np.atleast_1d(np.asarray(z, dtype=float))
    pig_arr = np.atleast_1d(np.asarray(pig, dtype=float))
    E_arr = np.atleast_1d(np.asarray(E_2, dtype=float))
    g_arr = config.recomb_interp.query_visibility(z_arr)
    g_arr = np.atleast_1d(g_arr)
    polter_arr = pig_arr / 10.0 + 9.0 * E_arr / 15.0
    result = g_arr * polter_arr
    if np.ndim(z) == 0 and np.ndim(pig) == 0 and np.ndim(E_2) == 0:
        return float(result[0])
    return result


def g_weighted_pi_on_grid(
    z_grid: np.ndarray,
    theta_2_of_z: Callable[[np.ndarray], np.ndarray],
    E_2_of_z: Callable[[np.ndarray], np.ndarray],
    config: VisibilityPolterConfig,
) -> np.ndarray:
    """Assemble  (g · Π)(z_grid)  given callable Θ_2(z) and E_2(z).

    The two callables are arbitrary — caller supplies whatever
    external evolution history (W5-A output, analytic profile, test
    fixture, ...). Shape returned: same as `z_grid`.

    In CAMB-polter mode, `theta_2_of_z` is interpreted as pig(z) and
    E_2(z) is unchanged.
    """
    z_grid = np.asarray(z_grid, dtype=float)
    theta_arr = np.asarray(theta_2_of_z(z_grid), dtype=float)
    E_arr = np.asarray(E_2_of_z(z_grid), dtype=float)
    if theta_arr.shape != z_grid.shape or E_arr.shape != z_grid.shape:
        raise ValueError(
            "theta_2_of_z / E_2_of_z must return arrays of the same "
            "shape as z_grid"
        )
    if config.use_camb_polter:
        return g_weighted_polter_camb(z_grid, theta_arr, E_arr, config)
    return g_weighted_pi_pstf(z_grid, theta_arr, E_arr, config)


# ============================================================================
# Section 4 - Diagnostics
# ============================================================================

def gpi_peak_in_z(
    theta_2_of_z: Callable[[np.ndarray], np.ndarray],
    E_2_of_z: Callable[[np.ndarray], np.ndarray],
    config: VisibilityPolterConfig,
    z_search_lo: float = 800.0,
    z_search_hi: float = 1400.0,
    n_samples: int = 2000,
) -> Tuple[float, float]:
    """Locate the peak of  (g · Π)(z)  on a dense grid.

    Returns (z_peak, gpi_peak). Uses a dense linear sample and picks
    the argmax; no parabolic refinement (Π variation is not
    necessarily quadratic and can be monotone).

    For slowly-varying Θ_2, E_2 the peak should coincide with the
    visibility peak at the surface of last scattering (z ≈ 1085–1090).
    """
    interp = config.recomb_interp
    z_lo = max(z_search_lo, interp.table.z_min)
    z_hi = min(z_search_hi, interp.table.z_max)
    if z_lo >= z_hi:
        raise ValueError(
            f"invalid search range [{z_lo}, {z_hi}]"
        )
    z_grid = np.linspace(z_lo, z_hi, n_samples)
    gpi_grid = g_weighted_pi_on_grid(
        z_grid, theta_2_of_z, E_2_of_z, config,
    )
    # For peak of |g·Π| (sign-agnostic)
    idx = int(np.argmax(np.abs(gpi_grid)))
    return float(z_grid[idx]), float(gpi_grid[idx])


def gpi_integral_trap_in_z(
    z_grid: np.ndarray,
    theta_2_vals: np.ndarray,
    E_2_vals: np.ndarray,
    config: VisibilityPolterConfig,
) -> float:
    """Trapezoidal integral of  (g · Π)(z)  over the given z_grid.

    Pedagogical / diagnostic only. This is ∫ g·Π dz, NOT the physical
    LOS quadrature (which integrates over η with Bessel weighting;
    that is W9-01). The z-space integral is sign-preserving and
    useful for regression: integration of a fixed (Θ_2, E_2) profile
    against a fixed visibility table should reproduce the same
    number at machine precision across test runs.

    z_grid must be monotone. Array lengths must match.
    """
    z_grid = np.asarray(z_grid, dtype=float)
    theta_arr = np.asarray(theta_2_vals, dtype=float)
    E_arr = np.asarray(E_2_vals, dtype=float)
    if not (z_grid.shape == theta_arr.shape == E_arr.shape):
        raise ValueError(
            "z_grid, theta_2_vals, E_2_vals must share shape"
        )
    if z_grid.ndim != 1 or z_grid.size < 2:
        raise ValueError("z_grid must be 1-D with length >= 2")
    if config.use_camb_polter:
        integrand = g_weighted_polter_camb(
            z_grid, theta_arr, E_arr, config,
        )
    else:
        integrand = g_weighted_pi_pstf(
            z_grid, theta_arr, E_arr, config,
        )
    return float(np.trapezoid(np.atleast_1d(integrand), z_grid))


# ============================================================================
# Section 5 - Physical sign assertions (v1.2 pattern)
# ============================================================================

def assert_visibility_positive(
    config: VisibilityPolterConfig,
    n_samples: int = 500,
    atol: float = 1.0e-30,
) -> None:
    """Verify g(z) ≥ 0 across the table range.

    Thomson rate τ̇ ≥ 0 and e^{−κ} ≥ 0 pointwise, so g ≥ 0 is a
    physical requirement. Note that at very high κ (deep opacity,
    z ≫ z_*), e^{−κ} underflows to exactly 0 in floating point —
    that is PHYSICAL (nothing reaches us from beyond the opaque
    wall) and not an assertion violation. Only negative g (spline
    undershoot in a broken table) fires the assertion.
    """
    interp = config.recomb_interp
    z_grid = np.linspace(interp.table.z_min, interp.table.z_max, n_samples)
    g_vals = interp.query_visibility(z_grid)
    mn = float(np.min(g_vals))
    if mn < -atol:
        raise AssertionError(
            f"g(z) has negative region: min = {mn:.3e} "
            f"over [{interp.table.z_min}, {interp.table.z_max}]"
        )


def assert_pi_sign_matches_theta2_at_subleading(
    theta_2: float,
    atol: float = 1e-14,
) -> None:
    """At subleading limit (S_E=0), Π = (5/2) Θ_2 must share Θ_2's sign.

    This is a structural check: the polarization return channel cannot
    flip the sign of the net source at isolated ℓ=2 tight coupling.
    """
    if abs(theta_2) < atol:
        return  # zero state; nothing to check
    E_2_subleading = -(np.sqrt(6.0) / 4.0) * theta_2
    pi_direct = combined_source_pi(theta_2, E_2_subleading)
    pi_analytic = pi_subleading_limit(theta_2)
    if not np.isclose(pi_direct, pi_analytic, rtol=1e-14, atol=atol):
        raise AssertionError(
            f"Π paths disagree at subleading: "
            f"direct={pi_direct:.12e}, analytic={pi_analytic:.12e}"
        )
    if np.sign(pi_direct) != np.sign(theta_2):
        raise AssertionError(
            f"Π sign {np.sign(pi_direct)} does not match Θ_2 sign "
            f"{np.sign(theta_2)} at subleading limit"
        )


def assert_gpi_peak_near_last_scattering(
    config: VisibilityPolterConfig,
    theta_2_fn: Optional[Callable[[np.ndarray], np.ndarray]] = None,
    E_2_fn: Optional[Callable[[np.ndarray], np.ndarray]] = None,
    z_expected: float = 1089.0,
    z_tolerance: float = 50.0,
) -> None:
    """For slowly varying (Θ_2, E_2), |g·Π| peaks near z_expected.

    Default test profile is a constant Θ_2 = 1, E_2 = 0, so the peak
    of |g·Π| coincides with the peak of g. The expected z is 1089
    without reionization, shifted to ≈ 1085 with reion (both inside
    ±50 tolerance).

    Fixture tier restriction
    ------------------------
    This assertion encodes PHYSICAL expectations (Planck 2018 z_* ≈
    1089.95 ± 0.27). Use only with the R2 HyRec-derived fixture.
    The R0 synthetic fixture (make_synthetic_tanh_table) has a peak
    at z ≈ 1361 and will fail this assertion at tight tolerance; that
    behavior is correct — the synthetic is a shape-only fixture and
    must not be used for physics-range asserts.
    """
    if theta_2_fn is None:
        theta_2_fn = lambda z: np.ones_like(np.asarray(z, dtype=float))
    if E_2_fn is None:
        E_2_fn = lambda z: np.zeros_like(np.asarray(z, dtype=float))
    z_peak, _ = gpi_peak_in_z(theta_2_fn, E_2_fn, config)
    if abs(z_peak - z_expected) > z_tolerance:
        raise AssertionError(
            f"g·Π peak at z={z_peak:.1f} outside "
            f"[{z_expected - z_tolerance:.1f}, "
            f"{z_expected + z_tolerance:.1f}]"
        )


# ============================================================================
# Section 6 - Three-way cross-check residual
# ============================================================================

def three_way_pi_residual_at_subleading(
    theta_2: float,
    gamma_T: float,
    decision: CanonicalDecision,
) -> dict:
    """Evaluate Π from three independent paths at subleading limit.

    At  S_E = 0,  S_T = (3/4) Γ_T Θ_2  (equivalent to amplification
    factor 4/3 ⇒ steady Θ_2 given), the three paths are:

        A. direct PSTF : Π_A = Θ_2 − √6 E_2   with E_2 = −(√6/4) Θ_2
        B. analytic    : Π_B = (5/2) Θ_2
        C. TCA solve   : Π_C = solve(S_T, 0, Γ_T) → Π

    All three collapse to the same analytic expression (5/2)Θ_2 by
    construction. Residual is expected at exact floating-point
    equality for non-zero inputs; this test guards against
    regressions in any of the three formulas.

    Returns
    -------
    dict with keys: pi_A, pi_B, pi_C, residual_AB, residual_BC,
    residual_AC, residual_max.
    """
    if not np.isfinite(theta_2) or not np.isfinite(gamma_T):
        raise ValueError("theta_2 and gamma_T must be finite")
    if gamma_T <= 0:
        raise ValueError(f"gamma_T must be positive, got {gamma_T}")

    sqrt6 = np.sqrt(6.0)
    # At subleading, E_2 = -(sqrt(6)/4) Θ_2 and S_T = (3/4) Γ_T Θ_2
    E_2_sub = -(sqrt6 / 4.0) * theta_2
    S_T_sub = (3.0 / 4.0) * gamma_T * theta_2

    pi_A = combined_source_pi(theta_2, E_2_sub)
    pi_B = pi_subleading_limit(theta_2)
    pi_C = pi_from_tca_sources(S_T_sub, 0.0, gamma_T, decision)

    d_AB = abs(pi_A - pi_B)
    d_BC = abs(pi_B - pi_C)
    d_AC = abs(pi_A - pi_C)

    return {
        "pi_A": pi_A,
        "pi_B": pi_B,
        "pi_C": pi_C,
        "residual_AB": float(d_AB),
        "residual_BC": float(d_BC),
        "residual_AC": float(d_AC),
        "residual_max": float(max(d_AB, d_BC, d_AC)),
    }


def four_path_pi_residual_general(
    S_T: float,
    S_E: float,
    gamma_T: float,
    decision: CanonicalDecision,
) -> dict:
    """Evaluate Π from four independent paths at arbitrary sources.

    Paths used here (all consume the same (S_T, S_E, Γ_T)):

        A. numerical solve  : (Θ_2,E_2) = np.linalg.solve(M, src); Π_A = Θ_2−√6 E_2
        B. explicit inverse : apply the 2×2 analytic M⁻¹ by hand, then combine
        C. closed form      : Π_C = (10/(3Γ_T)) (S_T − √6 S_E)
        D. residual check   : Π_D = Θ_2 − √6 E_2 (recomputation from Path A
                              values, guards against any accidental mutation)

    Path B is the one-line analytic inverse; Path C collapses the
    inverse ⊕ combiner into a single scalar formula; Path A uses
    LAPACK. Agreement at ~1e-14 absolute is the target (general
    2×2 inversion accumulates a few ULPs beyond exact).

    W3 gate: required. Caller supplies a canonical decision; Path A
    passes it through to `solve_tca_closure`.

    Returns
    -------
    dict with keys: pi_A, pi_B, pi_C, pi_D, residual_max,
    theta_2, E_2 (from Path A).
    """
    if not (np.isfinite(S_T) and np.isfinite(S_E) and np.isfinite(gamma_T)):
        raise ValueError("S_T, S_E, gamma_T must be finite")
    if gamma_T <= 0:
        raise ValueError(f"gamma_T must be positive, got {gamma_T}")

    sqrt6 = np.sqrt(6.0)

    # Path A: numerical solve (LAPACK)
    theta_2, E_2 = solve_tca_closure(S_T, S_E, gamma_T, decision)
    pi_A = combined_source_pi(theta_2, E_2)

    # Path B: explicit analytic 2x2 inverse
    #   M⁻¹ = (10/3) [[2/5, -√6/10], [-3/(5√6), 9/10]]
    inv_det_times_gammaT = 10.0 / (3.0 * gamma_T)
    theta_B = inv_det_times_gammaT * (
        (2.0 / 5.0) * S_T - (sqrt6 / 10.0) * S_E
    )
    E_B = inv_det_times_gammaT * (
        -(3.0 / (5.0 * sqrt6)) * S_T + (9.0 / 10.0) * S_E
    )
    pi_B = float(theta_B - sqrt6 * E_B)

    # Path C: closed form
    pi_C = pi_closed_form_from_sources(S_T, S_E, gamma_T)

    # Path D: recompute from Path A outputs (sanity)
    pi_D = float(theta_2 - sqrt6 * E_2)

    vals = [pi_A, pi_B, pi_C, pi_D]
    residuals = [abs(a - b) for i, a in enumerate(vals)
                 for b in vals[i + 1:]]

    return {
        "pi_A": pi_A,
        "pi_B": pi_B,
        "pi_C": pi_C,
        "pi_D": pi_D,
        "residual_max": float(max(residuals)),
        "theta_2": theta_2,
        "E_2": E_2,
    }


# ============================================================================
# Section 7 - η(z) light utility (flat ΛCDM)
# ============================================================================

def conformal_time_at_z(
    z: float,
    cosmology: CosmologyForRecombination,
    z_upper: float = 1.0e4,
    quad_limit: int = 200,
) -> float:
    """Conformal time η(z) in Mpc, flat ΛCDM, integrated from z to z_upper.

    Definition
    ----------
        η(z) = ∫_z^{z_upper}   dz' / H(z')         [in seconds]

    converted to Mpc via  c / Mpc_m  ≈ 9.716e-15 Mpc/s.

    Parameters
    ----------
    z : float
        Lower limit of integration (target redshift). Must satisfy
        z >= 0 and z < z_upper.
    cosmology : CosmologyForRecombination
        Supplies H_of_z(z) in 1/s.
    z_upper : float, default 1e4
        Surrogate for z → ∞. At flat ΛCDM with Ω_m ~ 0.3, the integrand
        falls as z^{−3/2} so the tail contribution above z = 1e4 is
        below 1e-6 fractional. Caller may raise for higher accuracy.
    quad_limit : int, default 200
        Subdivision limit passed to scipy.integrate.quad.

    Returns
    -------
    float
        Conformal time η(z) in Mpc. Positive.

    Scope
    -----
    Flat ΛCDM only (uses cosmology.H_of_z). No curvature. No dark
    radiation or exotic species beyond what the cosmology container
    encodes. Upgrade to production-grade quadrature and curvature
    handling scheduled for W9-01.
    """
    if not (0.0 <= z < z_upper):
        raise ValueError(
            f"require 0 <= z < z_upper; got z={z}, z_upper={z_upper}"
        )

    def integrand(zp: float) -> float:
        H_per_s = float(cosmology.H_of_z(np.atleast_1d(zp))[0])
        return 1.0 / H_per_s

    seconds, _ = quad(integrand, z, z_upper, limit=quad_limit)
    return C_IN_MPC_PER_S * seconds


def conformal_lookback_at_z(
    z: float,
    cosmology: CosmologyForRecombination,
    z_upper: float = 1.0e4,
    quad_limit: int = 200,
) -> float:
    """Lookback conformal time η(0) − η(z) in Mpc, flat ΛCDM.

    This is the quantity that enters j_ℓ[k(η_0 − η)] in the LOS
    integral (W9-01). Computed as

        ∫_0^z   dz' / H(z')        × (c / Mpc).
    """
    if not (0.0 <= z < z_upper):
        raise ValueError(
            f"require 0 <= z < z_upper; got z={z}, z_upper={z_upper}"
        )

    def integrand(zp: float) -> float:
        H_per_s = float(cosmology.H_of_z(np.atleast_1d(zp))[0])
        return 1.0 / H_per_s

    seconds, _ = quad(integrand, 0.0, z, limit=quad_limit)
    return C_IN_MPC_PER_S * seconds


# ============================================================================
# Section 8 - Scope guards
# ============================================================================

class OutOfScopeError(NotImplementedError):
    """Raised when a caller requests LOS machinery beyond W8-03."""


def full_los_integral(*args, **kwargs):
    """Not implemented in W8-03; scheduled for W9-01.

    The full LOS integral requires Bessel-weighted quadrature over
    conformal time with gravitational potentials and Doppler terms.
    W8-03 assembles only the g · Π node.
    """
    raise OutOfScopeError(
        "full_los_integral is W9-01; W8-03 provides only the g·Π node"
    )


def isw_source(*args, **kwargs):
    """Not implemented in W8-03; scheduled for W9-02."""
    raise OutOfScopeError(
        "isw_source requires Φ̇, Ψ̇ evolution (W9-02)"
    )


def doppler_source(*args, **kwargs):
    """Not implemented in W8-03; scheduled for W9-01."""
    raise OutOfScopeError(
        "doppler_source requires v_b evolution spline (W9-01)"
    )
