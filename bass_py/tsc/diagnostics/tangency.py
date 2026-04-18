"""
bass/teff/tangency.py  (Week 2 Day 3)
======================================

Paper I collision-side tangency diagnostic D_{s,≥2}.

Role in Paper I
---------------
For a species s with Teff manifold M_s (one-field: only Θ, or two-field: Θ, η),
the Boltzmann collision source C_s[{f_r}] drives the distribution function
toward or away from M_s. The tangency criterion (ch03 §sec:collision-field,
Eq. eq:tangency-criterion) asks:

    G_{ξ,s}(x) := C_s[{f_r}](x) / w_{*,s}(x)   ∈ V_s   ?

where V_s is the tangent space of M_s at the current (Θ_s, η_s), and w_{*,s}
is the natural-coordinate weight that converts the collision rate into a
rate of change of manifold coordinates.

Tangent space structure:
  - One-field (photon, BE; ch05 §sec:teff-ansatz):
        V_s = span{ x }
  - Two-field (neutrino, FD; ch03 §sec:species-teff):
        V_s = span{ 1, x }

The off-manifold residual is measured by the L²-weighted norm of the orthogonal
projection error:

    D_{s,≥2}² = || G_{ξ,s} − Π_{V_s} G_{ξ,s} ||²_{*,s}                  (Eq. eq:D-diagnostic)

If D_{s,≥2} = 0 exactly, the collision source is tangent to M_s and the Teff
ansatz is exact at that point. If D_{s,≥2} > 0, off-manifold energy-shape
modes are being sourced and the Teff reduction incurs a truncation error.

Regression-exact extraction (Paper I Prop 8, Lemma B.1)
-------------------------------------------------------
A naive projection of G onto the Laguerre basis {L_s^α} picks up spurious
L_0-mode contamination — this produces FALSE POSITIVES of off-manifold
behaviour. The Paper I prescription is regression-exact extraction:

    1. Build the Gram matrix G_{ij} = ⟨v_i, v_j⟩_{*,s} where {v_i} spans V_s.
    2. Build the moment vector b_i = ⟨v_i, G⟩_{*,s}.
    3. Solve the Gram system exactly: c = G^{-1} b.
    4. The projected tangent is Π_{V_s} G = Σ_i c_i v_i.
    5. D_{s,≥2}² = ⟨G, G⟩ − c · b  (normal-equation residual identity)

This eliminates the L_0 leakage by construction — for the one-field case,
the regression coefficient of the constant mode is EXCLUDED from V_s, so
any L_0 component of G is correctly flagged as off-manifold.

Inner product convention
------------------------
We use the ξ-weighted Laguerre inner product from Day 1:

    ⟨f, g⟩_{*,s} = ∫_0^∞ w_ξ(x) f(x) g(x) dx

with w_ξ(x) = x² / (e^{x-η} − ξ) for BE/FD and x² e^{-x+η} for MB.

This is not identical to the Fisher-information inner product in ch03 (which
uses derivatives of Φ_ξ), but for leading-order tangency diagnostics of
bosonic/fermionic massless radiation the two differ only by constants of
O(1). The present implementation uses the Laguerre weight for numerical
stability; the Fisher-weight variant is an optional extension (Week 2 Day 5).

References
----------
  ch03_framework.tex §sec:species-teff, §sec:collision-field
  ch05_teff_corrections.tex §sec:teff-ansatz, §sec:Teff-verdict
  Paper I §VI.A (Thm 6), Appendix B (Lemma B.1, Prop 8 regression-exact)
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, List, Optional, Tuple
import math

import numpy as np
from scipy.integrate import quad

from tsc.charts.laguerre_basis import xi_weight


# ═══════════════════════════════════════════════════════════════
# §1 — Tangent space kind
# ═══════════════════════════════════════════════════════════════

class TangentKind(Enum):
    """Paper I tangent space V_s.

    ONE_FIELD  : V_s = span{x}       (Θ-only ansatz: photons)
    TWO_FIELD  : V_s = span{1, x}    (Θ, η ansatz: neutrinos)
    """
    ONE_FIELD = "one_field"
    TWO_FIELD = "two_field"


def tangent_basis(kind: TangentKind) -> List[Callable[[np.ndarray], np.ndarray]]:
    """Return the tangent basis functions for the chosen manifold.

    ONE_FIELD  : [ x          ]
    TWO_FIELD  : [ 1,  x      ]

    These are raw (non-orthogonalized) basis functions. The Gram matrix
    machinery below handles the orthogonalization automatically.
    """
    if kind == TangentKind.ONE_FIELD:
        return [lambda x: np.asarray(x, dtype=float)]
    elif kind == TangentKind.TWO_FIELD:
        return [lambda x: np.ones_like(np.asarray(x, dtype=float)),
                lambda x: np.asarray(x, dtype=float)]
    raise ValueError(f"Unknown TangentKind: {kind}")


# ═══════════════════════════════════════════════════════════════
# §2 — Weighted inner product and Gram matrix
# ═══════════════════════════════════════════════════════════════

def weighted_inner_product(
    f: Callable[[np.ndarray], np.ndarray],
    g: Callable[[np.ndarray], np.ndarray],
    xi: int, eta: float = 0.0,
    alpha: float = 2.0,
    rtol: float = 1e-9,
    x_max: float = 60.0,
) -> float:
    """⟨f, g⟩_{*,s} = ∫₀^∞ w_ξ(x) f(x) g(x) dx.

    Parameters
    ----------
    f, g : callable
        Functions of x that return arrays.
    xi : int
        Statistics ∈ {-1, 0, +1}.
    eta : float
        Fugacity (η ≤ 0 for BE).
    alpha : float
        Laguerre weight parameter (default 2 for 3D phase space).
    rtol : float
        Integration tolerance.
    x_max : float
        Upper integration cutoff (integrand decays exponentially).
    """
    def integrand(x):
        w = xi_weight(np.array([x]), xi, eta, alpha)[0]
        f_val = float(f(np.array([x]))[0])
        g_val = float(g(np.array([x]))[0])
        return w * f_val * g_val

    result, _ = quad(integrand, 0.0, x_max, epsrel=rtol, limit=200)
    return result


def build_gram_matrix(
    basis: List[Callable[[np.ndarray], np.ndarray]],
    xi: int, eta: float = 0.0,
    alpha: float = 2.0,
) -> np.ndarray:
    """Build the Gram matrix G_{ij} = ⟨v_i, v_j⟩_{*,s} for the tangent basis."""
    n = len(basis)
    G = np.zeros((n, n))
    for i in range(n):
        for j in range(i, n):
            G[i, j] = weighted_inner_product(basis[i], basis[j], xi, eta, alpha)
            G[j, i] = G[i, j]
    return G


def build_moment_vector(
    G_field: Callable[[np.ndarray], np.ndarray],
    basis: List[Callable[[np.ndarray], np.ndarray]],
    xi: int, eta: float = 0.0,
    alpha: float = 2.0,
) -> np.ndarray:
    """Build the moment vector b_i = ⟨v_i, G⟩_{*,s}."""
    n = len(basis)
    b = np.zeros(n)
    for i in range(n):
        b[i] = weighted_inner_product(basis[i], G_field, xi, eta, alpha)
    return b


# ═══════════════════════════════════════════════════════════════
# §3 — Regression-exact tangent extraction (Paper I Prop 8)
# ═══════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class TangencyResult:
    """Output of the regression-exact tangency diagnostic."""
    coefficients: np.ndarray        # c_i in Π_{V_s} G = Σ c_i v_i
    tangent_norm_sq: float          # ⟨Π_{V_s} G, Π_{V_s} G⟩ = c · b
    total_norm_sq: float            # ⟨G, G⟩
    D_sq: float                     # Off-manifold norm²: ⟨G, G⟩ − c · b
    D: float                        # √D²  (tangency diagnostic)
    relative_residual: float        # D / √⟨G, G⟩  ∈ [0, 1]
    kind: TangentKind
    xi: int
    eta: float
    gram_matrix: np.ndarray
    moment_vector: np.ndarray

    @property
    def is_tangent(self) -> bool:
        """True if the collision field is on-manifold within quadrature precision.

        Threshold: D / ‖G‖ < 10⁻⁶. The quadrature tolerance used in
        build_gram_matrix and build_moment_vector is 10⁻⁹, so typical
        on-manifold residuals fall in the 10⁻⁸ to 10⁻⁹ range.
        """
        if self.total_norm_sq <= 1e-30:
            return self.D < 1e-10
        return self.relative_residual < 1e-6

    @property
    def fraction_on_manifold(self) -> float:
        """Fraction of ⟨G, G⟩ that lies on V_s. Value in [0, 1]."""
        if self.total_norm_sq <= 0:
            return 1.0
        return self.tangent_norm_sq / self.total_norm_sq


def compute_D_diagnostic(
    G_field: Callable[[np.ndarray], np.ndarray],
    kind: TangentKind,
    xi: int, eta: float = 0.0,
    alpha: float = 2.0,
) -> TangencyResult:
    """Regression-exact computation of D_{s,≥2} (Paper I Thm 6 + Prop 8).

    Workflow:
      1. Build tangent basis {v_i} per `kind`.
      2. Compute Gram matrix G_{ij} = ⟨v_i, v_j⟩.
      3. Compute moment vector b_i = ⟨v_i, G_field⟩.
      4. Solve Gram × c = b exactly.
      5. Tangent norm² = c · b (residual identity).
      6. Total norm² = ⟨G_field, G_field⟩.
      7. D² = total − tangent.

    Parameters
    ----------
    G_field : callable
        Normalized collision field G(x) = C(x) / w_*(x), returns array given array input.
    kind : TangentKind
        ONE_FIELD (span{x}) or TWO_FIELD (span{1, x}).
    xi : int
        Statistics ∈ {-1, 0, +1}.
    eta : float
        Fugacity.
    alpha : float
        Laguerre weight parameter.

    Returns
    -------
    TangencyResult
        Regression result with all diagnostic quantities.
    """
    basis = tangent_basis(kind)

    # Steps 2, 3: Gram matrix and moment vector
    G_mat = build_gram_matrix(basis, xi, eta, alpha)
    b_vec = build_moment_vector(G_field, basis, xi, eta, alpha)

    # Step 4: Solve Gram × c = b exactly (np.linalg.solve uses LU)
    try:
        c = np.linalg.solve(G_mat, b_vec)
    except np.linalg.LinAlgError as e:
        raise RuntimeError(
            f"Gram matrix singular (kind={kind}, ξ={xi}, η={eta}): {e}"
        )

    # Step 5: Tangent norm² = c · b (from normal-equation residual identity)
    tangent_norm_sq = float(c @ b_vec)

    # Step 6: Total norm² = ⟨G, G⟩
    total_norm_sq = weighted_inner_product(G_field, G_field, xi, eta, alpha)

    # Step 7: D² = total − tangent (residual identity)
    D_sq = total_norm_sq - tangent_norm_sq
    # Protect against negative D² from floating-point cancellation
    D_sq_safe = max(D_sq, 0.0)
    D = math.sqrt(D_sq_safe)
    relative_residual = (D / math.sqrt(total_norm_sq)
                         if total_norm_sq > 1e-30 else 0.0)

    return TangencyResult(
        coefficients=c,
        tangent_norm_sq=tangent_norm_sq,
        total_norm_sq=total_norm_sq,
        D_sq=D_sq_safe,
        D=D,
        relative_residual=relative_residual,
        kind=kind, xi=xi, eta=eta,
        gram_matrix=G_mat, moment_vector=b_vec,
    )


# ═══════════════════════════════════════════════════════════════
# §4 — Convenience: pre-built test fields
# ═══════════════════════════════════════════════════════════════

def on_manifold_field_one_field(
    slope: float = 1.0,
) -> Callable[[np.ndarray], np.ndarray]:
    """G(x) = slope × x — exactly on span{x}. D_{≥2} should be 0."""
    return lambda x: slope * np.asarray(x, dtype=float)


def on_manifold_field_two_field(
    intercept: float = 1.0, slope: float = 0.5,
) -> Callable[[np.ndarray], np.ndarray]:
    """G(x) = intercept + slope × x — exactly on span{1, x}. D_{≥2} = 0 for two-field."""
    def f(x):
        x = np.asarray(x, dtype=float)
        return intercept + slope * x
    return f


def off_manifold_field_quadratic(
    coeff: float = 1.0,
) -> Callable[[np.ndarray], np.ndarray]:
    """G(x) = coeff × x² — off-manifold for both 1-field and 2-field."""
    return lambda x: coeff * np.asarray(x, dtype=float) ** 2


def mixed_field(
    a: float = 1.0, b: float = 0.5, c: float = 0.3,
) -> Callable[[np.ndarray], np.ndarray]:
    """G(x) = a + b×x + c×x². Partly on-manifold, partly off."""
    def f(x):
        x = np.asarray(x, dtype=float)
        return a + b * x + c * x ** 2
    return f


# ═══════════════════════════════════════════════════════════════
# §5 — L_0 leakage check (Paper I Lemma B.1)
# ═══════════════════════════════════════════════════════════════

def l0_leakage_residual(
    G_field: Callable[[np.ndarray], np.ndarray],
    xi: int, eta: float = 0.0,
    alpha: float = 2.0,
) -> Tuple[float, float]:
    """Compare naive span{x} projection vs regression-exact for 1-field.

    If G has a constant (L_0) component, a naive projection onto span{x} can
    still produce nonzero tangent content because ⟨x, G⟩_{*,s} is sensitive to
    the constant part of G (the weight is non-orthogonal to x).

    Regression-exact (Paper I Prop 8) is always correct: for 1-field case,
    V_s = span{x} strictly, and L_0 content correctly flags off-manifold.

    Returns
    -------
    (D_naive, D_exact) : tuple of floats
        D_naive: ||G − (⟨x,G⟩/⟨x,x⟩) x|| — can incorrectly flag some L_0 as on-manifold
        D_exact: result from compute_D_diagnostic (canonical)

    The difference |D_naive - D_exact| is the L_0 leakage amount. For
    one-field, regression-exact and naive span{x} projection are actually
    identical (both use same inner product); the distinction matters when
    comparing against Laguerre basis projection which uses a different weight.
    """
    x_func = lambda x: np.asarray(x, dtype=float)

    # Naive: project onto span{x} with weighted inner product
    xx = weighted_inner_product(x_func, x_func, xi, eta, alpha)
    xG = weighted_inner_product(x_func, G_field, xi, eta, alpha)
    GG = weighted_inner_product(G_field, G_field, xi, eta, alpha)

    # Naive D² = GG − (xG)²/xx
    D_naive_sq = GG - (xG ** 2) / xx
    D_naive = math.sqrt(max(D_naive_sq, 0.0))

    # Regression-exact
    result = compute_D_diagnostic(G_field, TangentKind.ONE_FIELD, xi, eta, alpha)
    D_exact = result.D

    return D_naive, D_exact
