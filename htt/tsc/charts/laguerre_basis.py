"""
bass/teff/laguerre_basis.py  (Week 2 Day 1)
============================================

Generalized Laguerre polynomials and ξ-parameterized statistics families.

Role in Paper I
---------------
The Teff manifold (ch03 §sec:species-teff, Paper I §II) is

    f_s(x, ê) = Φ_{ξ_s}(x / Θ_s(ê))               (one-field)
    f_s(x, ê) = Φ_{ξ_s}(x / Θ_s(ê) − η_s(ê))      (two-field)

where x = E/(k_B T_0) > 0 is the dimensionless energy, Θ_s(ê) is the
direction-dependent normalized temperature, and Φ_ξ(z) = 1/(e^z − ξ) is
the equilibrium occupation function with ξ ∈ {+1 (BE), -1 (FD), 0 (MB)}.

Energy-integrated moments of the exponential family reduce to integrals of
the form ∫₀^∞ x^n Φ_ξ(x/Θ) dx. Expanding around the equilibrium Θ = 1, the
natural orthogonal basis is the generalized Laguerre polynomials L_s^α(x)
with weight w(x) = x^α e^{-x} on [0, ∞).

Why x-variable, not y = x − μ
-----------------------------
The alternative variable y = x − η(ê) develops a direction-dependent domain
pathology when η acquires angular structure: y can become negative for some
ê, breaking the Laguerre orthogonality domain x > 0. The x-variable avoids
this pathology (x = E/k_BT₀ > 0 for all E > 0), regardless of η(ê).
This is ch03 §sec:species-teff (energy variable).

Mathematical identities implemented
-----------------------------------
1. Recurrence:   (s+1) L_{s+1}^α = (2s + 1 + α − x) L_s^α − (s + α) L_{s-1}^α
2. Rodrigues:    L_s^α(x) = (1/s!) x^{-α} e^x d^s/dx^s [x^{s+α} e^{-x}]
3. Derivative:   d/dx L_s^α(x) = − L_{s-1}^{α+1}(x)
4. Orthogonality: ∫₀^∞ x^α e^{-x} L_s^α L_{s'}^α dx = Γ(s+α+1)/s! δ_{ss'}

Statistics moments I_{ξ,n}(Θ) = ∫₀^∞ x^n Φ_ξ(x/Θ) dx
----------------------------------------------------
For Θ = 1:
    BE (ξ=+1):  I_{+,n} = Γ(n+1) ζ(n+1)                for n ≥ 1
    FD (ξ=-1):  I_{-,n} = (1 − 2^{-n}) Γ(n+1) ζ(n+1)  for n ≥ 1
    MB (ξ=0):   I_{0,n} = Γ(n+1) = n!                  for n ≥ 0

For general Θ:  I_{ξ,n}(Θ) = Θ^{n+1} I_{ξ,n}(1).

References
----------
  ch03_framework.tex §sec:species-teff, §sec:Teff-manifold
  ch05_teff_corrections.tex §sec:teff-ansatz, §sec:Theta-field
  Abramowitz & Stegun §22 (generalized Laguerre polynomials)
  Gradshteyn & Ryzhik §3.411 (Bose/Fermi moment integrals)
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Union, Optional
import math

import numpy as np
from scipy.special import gamma, zeta
from scipy.integrate import quad


_LOG_FLOAT64_MAX = float(np.log(np.finfo(np.float64).max))


def _mb_exp_minus(z: np.ndarray) -> np.ndarray:
    """Return ``exp(-z)`` without overflow warnings.

    For very negative ``z`` the exact result exceeds float64 range, so
    the mathematically correct float64 return value is ``inf``.
    """
    z_arr = np.asarray(z, dtype=float)
    result = np.empty_like(z_arr, dtype=float)
    finite = np.isfinite(z_arr)
    result[~finite] = np.nan
    safe = finite & (z_arr > -_LOG_FLOAT64_MAX)
    result[safe] = np.exp(-z_arr[safe])
    result[finite & ~safe] = np.inf
    return result


def _fd_occupation(z: np.ndarray) -> np.ndarray:
    """Stable Fermi-Dirac occupation ``1 / (exp(z) + 1)``."""
    z_arr = np.asarray(z, dtype=float)
    result = np.empty_like(z_arr, dtype=float)
    finite = np.isfinite(z_arr)
    result[~finite] = np.nan
    nonneg = finite & (z_arr >= 0.0)
    exp_neg = np.exp(-z_arr[nonneg])
    result[nonneg] = exp_neg / (1.0 + exp_neg)
    neg = finite & ~nonneg
    exp_pos = np.exp(z_arr[neg])
    result[neg] = 1.0 / (1.0 + exp_pos)
    return result


def _be_occupation(z: np.ndarray) -> np.ndarray:
    """Stable Bose-Einstein occupation ``1 / (exp(z) - 1)``."""
    z_arr = np.asarray(z, dtype=float)
    result = np.empty_like(z_arr, dtype=float)
    finite = np.isfinite(z_arr)
    result[~finite] = np.nan
    near_zero = finite & (np.abs(z_arr) <= 1.0e-14)
    result[near_zero] = np.inf
    large_pos = finite & (z_arr >= 50.0)
    exp_neg = np.exp(-z_arr[large_pos])
    result[large_pos] = exp_neg / np.maximum(1.0 - exp_neg, 1.0e-300)
    regular = finite & ~(near_zero | large_pos)
    result[regular] = 1.0 / np.expm1(z_arr[regular])
    return result


# ═══════════════════════════════════════════════════════════════
# §1 — Generalized Laguerre polynomials
# ═══════════════════════════════════════════════════════════════

def laguerre_L(
    s: int, alpha: float, x: Union[float, np.ndarray],
) -> Union[float, np.ndarray]:
    """Generalized Laguerre polynomial L_s^α(x) via stable forward recurrence.

    The recurrence
        (s+1) L_{s+1}^α(x) = (2s + 1 + α − x) L_s^α(x) − (s + α) L_{s-1}^α(x)
    with
        L_0^α(x) = 1,   L_1^α(x) = 1 + α − x
    is numerically stable for α ≥ 0 and x in the typical cosmological range
    x ∈ [0, ~10].

    Parameters
    ----------
    s : int
        Polynomial order ≥ 0.
    alpha : float
        Weight parameter α > −1 (required for orthogonality on [0, ∞)).
    x : float or array
        Evaluation point(s) x ≥ 0.

    Returns
    -------
    L : same type as x
        L_s^α(x).
    """
    if s < 0:
        raise ValueError(f"Laguerre order must be s ≥ 0, got s = {s}")
    if alpha <= -1:
        raise ValueError(
            f"Laguerre weight parameter must be α > −1, got α = {alpha}"
        )

    x_arr = np.asarray(x, dtype=float)

    if s == 0:
        return np.ones_like(x_arr) if x_arr.ndim > 0 else 1.0
    if s == 1:
        result = 1.0 + alpha - x_arr
        return result if x_arr.ndim > 0 else float(result)

    # Forward recurrence
    L_prev = np.ones_like(x_arr)                  # L_0
    L_curr = 1.0 + alpha - x_arr                  # L_1
    for k in range(1, s):
        L_next = ((2.0 * k + 1.0 + alpha - x_arr) * L_curr
                  - (k + alpha) * L_prev) / (k + 1.0)
        L_prev = L_curr
        L_curr = L_next

    return L_curr if x_arr.ndim > 0 else float(L_curr)


def laguerre_L_derivative(
    s: int, alpha: float, x: Union[float, np.ndarray],
) -> Union[float, np.ndarray]:
    """Derivative d/dx L_s^α(x) = − L_{s-1}^{α+1}(x).

    For s = 0, the derivative is identically zero.
    """
    if s == 0:
        x_arr = np.asarray(x, dtype=float)
        return np.zeros_like(x_arr) if x_arr.ndim > 0 else 0.0
    return -laguerre_L(s - 1, alpha + 1.0, x)


def laguerre_weight(
    alpha: float, x: Union[float, np.ndarray],
) -> Union[float, np.ndarray]:
    """Laguerre measure weight w(x) = x^α e^{-x} on [0, ∞)."""
    x_arr = np.asarray(x, dtype=float)
    # Handle x=0 for α > 0 (gives 0) and α = 0 (gives 1)
    result = np.where(
        x_arr > 0,
        np.power(np.maximum(x_arr, 1e-300), alpha) * np.exp(-x_arr),
        0.0 if alpha > 0 else np.exp(-x_arr),
    )
    return result if x_arr.ndim > 0 else float(result)


def laguerre_norm_squared(s: int, alpha: float) -> float:
    """Orthogonality normalization ⟨L_s^α, L_s^α⟩_w = Γ(s+α+1) / s!"""
    if s < 0 or alpha <= -1:
        raise ValueError(f"Invalid (s, α) = ({s}, {alpha})")
    return gamma(s + alpha + 1.0) / math.factorial(s)


# ═══════════════════════════════════════════════════════════════
# §2 — Statistics family (BE/FD/MB) via ξ parameterization
# ═══════════════════════════════════════════════════════════════

class Xi(Enum):
    """Quantum-statistics parameter ξ ∈ {+1, -1, 0}."""
    BE = +1    # Bose-Einstein (photons)
    FD = -1    # Fermi-Dirac (neutrinos)
    MB = 0     # Maxwell-Boltzmann (classical limit)


def occupation_Phi(xi: int, z: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
    """Equilibrium occupation Φ_ξ(z) = 1/(e^z − ξ).

    For ξ = 0 (MB), this reduces to Φ_0(z) = e^{−z}.

    Note that for ξ = +1 (BE), Φ_+ diverges as z → 0⁺; caller must supply
    z > 0 for BE evaluation.
    """
    z_arr = np.asarray(z, dtype=float)
    if xi == 0:
        result = _mb_exp_minus(z_arr)
    elif xi == +1:
        result = _be_occupation(z_arr)
    elif xi == -1:
        result = _fd_occupation(z_arr)
    else:
        raise ValueError(f"ξ must be one of {{-1, 0, +1}}, got {xi}")
    return result if z_arr.ndim > 0 else float(result)


def moment_I(xi: int, n: int, Theta: float = 1.0) -> float:
    """Statistics moment I_{ξ,n}(Θ) = ∫₀^∞ x^n Φ_ξ(x/Θ) dx.

    Closed-form evaluation for n ≥ 1:
        BE (ξ=+1):  I_{+,n}(Θ) = Θ^{n+1} Γ(n+1) ζ(n+1)
        FD (ξ=-1):  I_{-,n}(Θ) = Θ^{n+1} (1 − 2^{-n}) Γ(n+1) ζ(n+1)
        MB (ξ=0):   I_{0,n}(Θ) = Θ^{n+1} Γ(n+1)

    For BE, n = 0 diverges logarithmically (not implemented; would need
    chemical potential cutoff).

    Parameters
    ----------
    xi : int
        Statistics parameter, one of {-1, 0, +1}.
    n : int
        Moment order ≥ 0.
    Theta : float, optional
        Temperature scaling (default 1). Scales as Θ^{n+1}.
    """
    if xi not in (-1, 0, +1):
        raise ValueError(f"ξ must be ±1 or 0, got {xi}")
    if n < 0:
        raise ValueError(f"Moment order n must be ≥ 0, got {n}")
    if Theta <= 0:
        raise ValueError(f"Θ must be > 0, got {Theta}")

    # BE, n=0: ∫ Φ_+ dx = ∫ 1/(e^x − 1) dx diverges at x=0 (logarithmic)
    if xi == +1 and n == 0:
        raise ValueError(
            "BE moment I_{+,0} diverges logarithmically at x → 0. "
            "Physical applications include a chemical-potential cutoff; "
            "use moment_I_numeric with an explicit lower bound."
        )

    scale = Theta ** (n + 1)

    if xi == 0:
        # MB: ∫ x^n e^{-x} dx = Γ(n+1) = n!
        return scale * gamma(n + 1.0)
    elif xi == +1:
        # BE: Γ(n+1) ζ(n+1)
        return scale * gamma(n + 1.0) * float(zeta(n + 1.0))
    else:  # xi == -1
        # FD: (1 − 2^{-n}) Γ(n+1) ζ(n+1)
        # Special case n=0: ∫ 1/(e^x + 1) dx = ln 2
        if n == 0:
            return scale * math.log(2.0)
        return scale * (1.0 - 2.0 ** (-n)) * gamma(n + 1.0) * float(zeta(n + 1.0))


def moment_I_numeric(
    xi: int, n: int, Theta: float = 1.0,
    x_lower: float = 0.0, x_upper: float = np.inf,
) -> float:
    """Numerical evaluation of I_{ξ,n}(Θ) for cases needing bounds.

    Used to verify closed-form moment_I() and to handle BE n=0 case with
    explicit lower cutoff.
    """
    if xi not in (-1, 0, +1):
        raise ValueError(f"ξ must be ±1 or 0, got {xi}")

    def integrand(x):
        return x**n * occupation_Phi(xi, x / Theta)

    result, _ = quad(integrand, x_lower, x_upper, limit=200)
    return result


# ═══════════════════════════════════════════════════════════════
# §3 — Paper I basis: combines Laguerre polynomials with ξ statistics
# ═══════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class PaperIBasis:
    """Laguerre-type basis for the Paper I Teff exponential family.

    The basis is specified by:
      ξ : statistics parameter ∈ {-1, 0, +1}
      α : Laguerre weight parameter (typically α = 2 for photon number
          or α = 3 for photon energy phase-space weight)
      s_max : maximum polynomial order retained (truncation)

    For photons (ξ = +1), the relevant phase-space weight in the cosmological
    distribution function includes x² (from 4π p² dp ∝ p² dp in natural units),
    so the natural Laguerre parameter is α = 2 when expanding around Φ_+.

    Methods provide:
      - evaluate: L_s^α(x) at given x
      - moment_weighted: ∫₀^∞ x^β e^{-x} L_s^α L_{s'}^α dx (cross moments)
      - occupation_moment: ∫₀^∞ x^β Φ_ξ(x/Θ) dx × Laguerre factor
    """
    xi: int
    alpha: float = 2.0
    s_max: int = 4

    def __post_init__(self):
        if self.xi not in (-1, 0, +1):
            raise ValueError(f"ξ must be ±1 or 0, got {self.xi}")
        if self.alpha <= -1:
            raise ValueError(f"α must be > −1, got {self.alpha}")
        if self.s_max < 0:
            raise ValueError(f"s_max must be ≥ 0, got {self.s_max}")

    def evaluate(self, s: int, x: Union[float, np.ndarray]):
        """L_s^α(x) at the basis's α parameter."""
        if s > self.s_max:
            raise IndexError(
                f"Requested s = {s} exceeds basis s_max = {self.s_max}"
            )
        return laguerre_L(s, self.alpha, x)

    def weight(self, x: Union[float, np.ndarray]):
        """x^α e^{-x}."""
        return laguerre_weight(self.alpha, x)

    def norm_squared(self, s: int) -> float:
        """Γ(s + α + 1) / s!"""
        return laguerre_norm_squared(s, self.alpha)

    def occupation_moment(self, n: int, Theta: float = 1.0) -> float:
        """I_{ξ,n}(Θ) at this basis's ξ."""
        return moment_I(self.xi, n, Theta)

    def statistics_name(self) -> str:
        return {-1: "FD", 0: "MB", +1: "BE"}[self.xi]


# ═══════════════════════════════════════════════════════════════
# §4 — Fugacity-dependent moments I_n(ξ, η)  (Week 2 Day 1 extension)
# ═══════════════════════════════════════════════════════════════
#
# The two-field (Θ, η) Teff ansatz (Paper I §II.B, ch03 §sec:species-teff
# two-field) requires moments of the form
#
#     I_n(ξ, η) = ∫₀^∞ x^n / (e^{x−η} − ξ) dx
#
# For η = 0, these reduce to the closed-form `moment_I` above.
# For η ≠ 0 (admissible only for FD and MB; BE requires η ≤ 0),
# we compute numerically with a singularity-aware integration split.


def xi_moment(
    n: int, xi: int, eta: float = 0.0,
    rtol: float = 1e-10,
) -> float:
    """ξ-moment I_n(ξ, η) = ∫₀^∞ x^n / (e^{x−η} − ξ) dx.

    For η = 0, falls back to the analytical `moment_I(xi, n, 1.0)`.
    For η ≠ 0 the integral is evaluated numerically.

    Parameters
    ----------
    n : int
        Moment order. For BE with η = 0 requires n ≥ 1.
    xi : int
        Statistics parameter ∈ {-1, 0, +1}.
    eta : float, optional
        Fugacity. For BE must satisfy η ≤ 0.
    rtol : float, optional
        Numerical tolerance for η ≠ 0 case.

    Returns
    -------
    float
        I_n(ξ, η).
    """
    if xi not in (-1, 0, +1):
        raise ValueError(f"xi must be ∈ {{-1, 0, +1}}, got {xi}")
    if xi == +1 and eta > 1e-15:
        raise ValueError(
            f"BE admissibility requires η ≤ 0; got η = {eta}"
        )

    if abs(eta) < 1e-15:
        # Analytical closed form at η = 0
        return moment_I(xi, n, Theta=1.0)

    # Numerical integration for η ≠ 0 (FD or BE with shifted fugacity).
    if xi == +1:
        integrand = lambda x: x ** n * occupation_Phi(+1, x - eta)
    elif xi == -1:
        integrand = lambda x: x ** n * occupation_Phi(-1, x - eta)
    else:  # MB: ∫ x^n e^{-(x-η)} dx = e^η Γ(n+1)
        if eta > _LOG_FLOAT64_MAX:
            return float("inf")
        return math.exp(eta) * float(gamma(n + 1))

    x_split = max(1.0, 2.0 * abs(eta))
    I1, _ = quad(integrand, 0.0, x_split, epsrel=rtol, limit=200)
    I2, _ = quad(integrand, x_split, np.inf, epsrel=rtol, limit=200)
    return I1 + I2


# ═══════════════════════════════════════════════════════════════
# §5 — Physical spectral-stiffness ratios
# ═══════════════════════════════════════════════════════════════
#
# The shear-source coefficient Σ_2^{(s)} (ch05 Eq. eq:shear-source) drives
# the quadrupole response of species s to spacetime shear:
#
#     Σ_2^{(s)} = (8/15) × I_4(ξ, η) / I_3(ξ, η)
#
# Canonical values at η = 0:
#     BE:  I_4/I_3 = 24 ζ(5) / (π⁴/15) ≈ 3.8322,  Σ_2 ≈ 2.0438
#     FD:  I_4/I_3 ≈ 4.1068,                       Σ_2 ≈ 2.1903
#     MB:  I_4/I_3 = 4,                            Σ_2 = 32/15 ≈ 2.1333


def I4_over_I3(xi: int, eta: float = 0.0) -> float:
    """Spectral-stiffness ratio I_4(ξ, η) / I_3(ξ, η).

    Canonical values at η = 0:
        BE:  24 ζ(5) / (π⁴/15) ≈ 3.8322
        FD:  (15/16) × 24 ζ(5) / (7π⁴/120) ≈ 4.1068
        MB:  4! / 3! = 4
    """
    return xi_moment(4, xi, eta) / xi_moment(3, xi, eta)


def shear_source_coeff(xi: int, eta: float = 0.0) -> float:
    """Shear-source coefficient Σ_2^{(s)} = (8/15) × I_4/I_3 (ch05 §sec:shear-source).

    This is the coefficient multiplying σ_ab in the quadrupole source term
    for a massless species with one-field Teff ansatz.
    """
    return (8.0 / 15.0) * I4_over_I3(xi, eta)


# ═══════════════════════════════════════════════════════════════
# §6 — Laguerre inner product under ξ-weight + Gram matrix
# ═══════════════════════════════════════════════════════════════
#
# Under MB weight (ξ = 0, w(x) = x^α e^{-x}), the L_s^α are orthogonal.
# Under BE or FD weight (w(x) = x^α / (e^{x-η} − ξ)), they are NOT
# orthogonal. We provide the Gram matrix for Gram-Schmidt orthogonalization
# against any physical weight.


def xi_weight(x, xi: int, eta: float = 0.0, alpha: float = 2.0) -> np.ndarray:
    """The ξ-weighted Laguerre measure:

        w(x) = x^α / (e^{x−η} − ξ)   for BE/FD
        w(x) = x^α e^{−x+η}          for MB

    Parameters
    ----------
    x : array-like
        Evaluation points (x > 0).
    xi : int
        Statistics ∈ {-1, 0, +1}.
    eta : float
        Fugacity (η ≤ 0 for BE).
    alpha : float
        Laguerre parameter (default 2 for 3D phase space).

    Returns
    -------
    w : array
        Weight values.
    """
    x_arr = np.asarray(x, dtype=float)
    if xi == 0:
        return (x_arr ** alpha) * _mb_exp_minus(x_arr - eta)
    return (x_arr ** alpha) * occupation_Phi(xi, x_arr - eta)


def laguerre_inner_product(
    s1: int, s2: int,
    xi: int, eta: float = 0.0,
    alpha: float = 2.0,
    rtol: float = 1e-9,
) -> float:
    """⟨L_{s1}^α, L_{s2}^α⟩_{ξ,η} = ∫₀^∞ w_{ξ,η}(x) L_{s1}^α(x) L_{s2}^α(x) dx.

    Parameters
    ----------
    s1, s2 : int
        Polynomial orders.
    xi : int
        Statistics.
    eta : float
        Fugacity.
    alpha : float
        Laguerre parameter.
    rtol : float
        Integration tolerance.
    """
    def integrand(x):
        L1 = laguerre_L(s1, alpha, x)
        L2 = laguerre_L(s2, alpha, x)
        w = float(xi_weight(x, xi, eta=eta, alpha=alpha))
        return w * L1 * L2

    x_max = 50.0 + 2.0 * abs(eta) + 3.0 * max(s1, s2)
    result, _ = quad(integrand, 0.0, x_max, epsrel=rtol, limit=200)
    return result


def gram_matrix(
    n_basis: int,
    xi: int, eta: float = 0.0,
    alpha: float = 2.0,
) -> np.ndarray:
    """Gram matrix G_{s,s'} = ⟨L_s^α, L_{s'}^α⟩_{ξ,η} for s, s' ∈ [0, n_basis).

    Returns
    -------
    G : ndarray shape (n_basis, n_basis)
        Symmetric (and under MB, diagonal) Gram matrix.
    """
    G = np.zeros((n_basis, n_basis))
    for i in range(n_basis):
        for j in range(i, n_basis):
            G[i, j] = laguerre_inner_product(i, j, xi, eta, alpha)
            G[j, i] = G[i, j]
    return G


def verify_mb_orthogonality(
    n_basis: int = 5, alpha: float = 2.0, rtol: float = 1e-6,
) -> tuple:
    """Cross-check Laguerre MB orthogonality: ⟨L_s^α, L_{s'}^α⟩_{MB} = (Γ(s+α+1)/s!) δ_{ss'}.

    For MB (ξ = 0, η = 0), the weight x^α e^{-x} is the standard Laguerre
    weight. The Gram matrix should be diagonal with entries Γ(s+α+1)/s!.

    Returns
    -------
    (is_orthogonal, gram, diag_expected) : tuple
        is_orthogonal  : bool — True iff off-diagonal entries small.
        gram           : ndarray — computed Gram matrix.
        diag_expected  : ndarray — analytical diagonal [Γ(s+α+1)/s!].
    """
    G = gram_matrix(n_basis, xi=0, eta=0.0, alpha=alpha)
    diag_expected = np.array([laguerre_norm_squared(s, alpha)
                              for s in range(n_basis)])

    # Diagonal agreement
    diag_rel_err = np.abs(np.diag(G) - diag_expected) / diag_expected
    if np.any(diag_rel_err > rtol):
        return False, G, diag_expected

    # Off-diagonal smallness (relative to geometric mean of diagonal pair)
    off_diag_max_ratio = 0.0
    for i in range(n_basis):
        for j in range(n_basis):
            if i != j:
                ratio = abs(G[i, j]) / math.sqrt(diag_expected[i] * diag_expected[j])
                off_diag_max_ratio = max(off_diag_max_ratio, ratio)

    return off_diag_max_ratio < rtol, G, diag_expected


# ═══════════════════════════════════════════════════════════════
# §7 — Reference stiffness table (cached for downstream consumption)
# ═══════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class SpectralStiffness:
    """Cached spectral-stiffness values at η = 0 per statistics family."""
    statistics_name: str           # 'BE', 'FD', or 'MB'
    xi: int
    eta: float
    I3: float
    I4: float
    I4_over_I3: float
    Sigma_2: float                 # shear source coefficient (8/15) × I_4/I_3


def build_stiffness_table() -> dict:
    """Reference table of spectral ratios at η = 0 for BE, FD, MB.

    Returns
    -------
    dict[str, SpectralStiffness]
        Keyed by 'BE', 'FD', 'MB'.
    """
    result = {}
    for stat_name, xi in [('BE', +1), ('FD', -1), ('MB', 0)]:
        I3 = xi_moment(3, xi, 0.0)
        I4 = xi_moment(4, xi, 0.0)
        ratio = I4 / I3
        result[stat_name] = SpectralStiffness(
            statistics_name=stat_name,
            xi=xi, eta=0.0,
            I3=I3, I4=I4,
            I4_over_I3=ratio,
            Sigma_2=(8.0 / 15.0) * ratio,
        )
    return result
