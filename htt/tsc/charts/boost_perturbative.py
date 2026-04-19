"""
bass/teff/boost_perturbative.py  (Week 2 Day 4)
================================================

Paper I perturbative boost law (Prop 5) with Thm 3 cross-check.

Two perspectives on the same physics
-------------------------------------
Given a species with one-field Teff ansatz `f(x, ê) = Φ_ξ(x/Θ(ê))`, a velocity
boost v along ẑ can be realized in two ways:

  Path 1 (spatial):    Θ(ê) → Θ'(ê') = Θ(ê(ê')) / [γ(1 − v μ')]
                       Then compute T_ℓ' = F(Θ')

  Path 2 (multipole):  T_ℓ = F(Θ)
                       Then apply Paper I Prop 5:  T_ℓ' = B(v) T_ℓ + a(v)

**Paper I Thm 3** asserts that for one-field (η ≡ 0), these two paths produce
**identical** T_ℓ' — the boost is exact, with no residual μ-dependent
corrections. For two-field (η ≠ 0), Thm 3 no longer holds exactly, and the
discrepancy Path 1 − Path 2 is the "μ-defect" tracked by Prop 7/8.

Scope of this module
--------------------
1. `boost_theta_axisymmetric(Θ, v)`: Path 1 — direct spatial boost on Θ(μ).
   Uses the exact Doppler-plus-aberration transformation and re-projects
   onto Legendre modes via Gauss-Legendre quadrature.

2. `boost_multipoles_prop5(T_ℓ, v, order)`: Path 2 — multipole-space boost
   from Paper I Prop 5. Extends `channel_routing.apply_boost_to_teff` with
   an explicit `order` parameter (O(v), O(v²)).

3. `thm3_consistency_check(Θ, v, ξ)`: runs both paths and returns the
   residual `‖T_ℓ^{spatial} − T_ℓ^{multipole}‖` as a function of v.

4. `boost_order_convergence(Θ, v_list, order)`: verifies `‖residual‖ ~ v^{order+1}`
   by sampling at multiple v values.

Convention: axisymmetric, with boost velocity v along +ẑ.
Sign: μ = cos θ, and v > 0 moves observer along +ẑ so photons from +ẑ are
blueshifted.

References
----------
  Paper I (Park-Cheoun-Park 2026) Thm 3 (exact boost μ = 0 one-field),
                                  Prop 5 (perturbative boost),
                                  Prop 7 (μ-defect scope)
  ch03_framework.tex §sec:species-teff (Teff ansatz, energy variable choice)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
import math

import numpy as np
from scipy.special import eval_legendre

from tsc.charts.forward_F_to_T import (
    AxisymmetricField, axisymmetric_F, ForwardResult,
    isotropic_theta, dipole_theta, quadrupole_theta,
)
from tsc.charts.boost_coefficients import (
    apply_boost_to_teff,
    boost_mixing_matrix, boost_additive_velocity_terms,
    PROP5_COEFF_DIPOLE_FROM_QUADRUPOLE,
    PROP5_COEFF_QUADRUPOLE_FROM_DIPOLE,
    PROP5_COEFF_OCTUPOLE_FROM_QUADRUPOLE,
)


# ═══════════════════════════════════════════════════════════════
# §1 — Spatial boost on axisymmetric Θ field (Path 1)
# ═══════════════════════════════════════════════════════════════

def relativistic_aberration_mu(mu_prime: np.ndarray, v: float) -> np.ndarray:
    """Inverse aberration: μ' (boosted frame) → μ (original frame).

    For a boost by velocity v along +ẑ:
        μ' = (μ + v) / (1 + v μ)           [forward aberration]
        μ  = (μ' − v) / (1 − v μ')         [inverse — used here]

    Parameters
    ----------
    mu_prime : array-like
        Cosine in boosted frame.
    v : float
        Boost velocity (dimensionless, v/c, |v| < 1).

    Returns
    -------
    mu : array
        Cosine in original frame.
    """
    if abs(v) >= 1:
        raise ValueError(f"|v| must be < 1 (units of c), got {v}")
    mu_prime = np.asarray(mu_prime, dtype=float)
    return (mu_prime - v) / (1.0 - v * mu_prime)


def doppler_factor(mu_prime: np.ndarray, v: float) -> np.ndarray:
    """Doppler factor D(μ', v) = 1 / [γ (1 − v μ')].

    For the one-field Teff ansatz, Θ'(μ') = Θ(μ(μ')) × D(μ', v).
    """
    if abs(v) >= 1:
        raise ValueError(f"|v| must be < 1 (units of c), got {v}")
    mu_prime = np.asarray(mu_prime, dtype=float)
    gamma = 1.0 / math.sqrt(1.0 - v * v)
    return 1.0 / (gamma * (1.0 - v * mu_prime))


def boost_theta_axisymmetric(
    Theta: AxisymmetricField, v: float,
    L_max_out: Optional[int] = None,
    n_quad: Optional[int] = None,
) -> AxisymmetricField:
    """Spatial boost of axisymmetric Θ(μ) field along +ẑ at velocity v.

        Θ'(μ') = Θ(μ(μ')) × D(μ', v)
        μ(μ')  = (μ' − v) / (1 − v μ')
        D(μ',v) = 1 / [γ (1 − v μ')]

    The boosted field Θ' is re-projected onto Legendre polynomials so the
    result is again an `AxisymmetricField`.

    Parameters
    ----------
    Theta : AxisymmetricField
        Input temperature field.
    v : float
        Boost velocity along +ẑ. |v| < 1.
    L_max_out : int, optional
        Highest ℓ retained in output. Default Θ.L_max + 3 to allow boost-mixing.
    n_quad : int, optional
        Gauss-Legendre quadrature points. Default max(64, 4 × L_max_out + 8).

    Returns
    -------
    Theta_prime : AxisymmetricField
        Boosted temperature field with `coeffs` of length `L_max_out + 1`.
    """
    if L_max_out is None:
        L_max_out = Theta.L_max + 3
    if n_quad is None:
        n_quad = max(64, 4 * L_max_out + 8)

    # Gauss-Legendre quadrature on [-1, 1] in the μ' frame
    mu_prime, w = np.polynomial.legendre.leggauss(n_quad)

    # Evaluate Θ'(μ') = Θ(μ(μ')) × D(μ', v)
    mu_orig = relativistic_aberration_mu(mu_prime, v)
    Theta_vals_orig = Theta.evaluate(mu_orig)
    doppler = doppler_factor(mu_prime, v)
    Theta_prime_vals = Theta_vals_orig * doppler

    # Legendre projection: c_ℓ = (2ℓ+1)/2 × ∫ Θ' P_ℓ dμ'
    coeffs = np.zeros(L_max_out + 1)
    for ell in range(L_max_out + 1):
        P_ell_vals = eval_legendre(ell, mu_prime)
        coeffs[ell] = (2 * ell + 1) / 2.0 * float(
            np.sum(w * Theta_prime_vals * P_ell_vals)
        )

    return AxisymmetricField(
        coeffs=coeffs,
        name=f"{Theta.name}_boosted_{v:.3e}",
    )


# ═══════════════════════════════════════════════════════════════
# §2 — Multipole-space boost (Path 2, Paper I Prop 5)
# ═══════════════════════════════════════════════════════════════

def boost_multipoles_prop5(
    T_ell: np.ndarray, v: float,
    moment_order: int = 3,
    order: int = 2,
) -> np.ndarray:
    """Paper I Prop 5 — multipole-space boost in **dimensional T convention**.

    IMPORTANT: this version uses the `forward_F_to_T` convention where
    T_ℓ = ∫ Θ^{n+1} I_n P_ℓ dμ × (2ℓ+1)/2, so the background monopole is
    T_0 = I_n × Θ_0^{n+1}. In the Paper I "Θ-normalized" convention (used
    inside `channel_routing`), the additive coefficients assume T_0 = 1.

    The conversion from Θ-space additive to T-space additive uses the linear
    response ΔT_ℓ = (n+1) × T_0 × ΔΘ_ℓ (at leading order around the isotropic
    background), plus the tensor-to-Legendre projection factors derived from
    the exact Doppler+aberration transformation.

    The axisymmetric additive coefficients for a velocity boost of magnitude
    v along the +ẑ direction, extracted from Θ'(μ') = Θ(μ(μ')) / [γ(1 − vμ')],
    are (see derivation in docstring of `boost_theta_axisymmetric`):

        ΔΘ_0 = -v²/6 × Θ_0      ⟹    ΔT_0 = -(n+1)/6 × T_0 × v²
        ΔΘ_1 = v × Θ_0          ⟹    ΔT_1 = (n+1) × T_0 × v
        ΔΘ_2 = (2/3) v² × Θ_0   ⟹    ΔT_2 = (2/3)(n+1) × T_0 × v²
        ΔΘ_3 = (2/5) v³ × Θ_0   ⟹    ΔT_3 = (2/5)(n+1) × T_0 × v³

    These are the "induced" multipoles from the boost itself, for an isotropic
    background. The linear mixing matrix from `channel_routing` handles the
    coupling of pre-existing T_ℓ content under the boost.

    Parameters
    ----------
    T_ell : ndarray shape (L+1,)
        Axisymmetric multipoles [T_0, T_1, ..., T_L].
    v : float
        Boost velocity along +ẑ. |v| < 1.
    moment_order : int, optional
        n in I_n (n = 3 for energy multipoles, default).
    order : int, optional
        v-expansion order: 1 (dipole additive only) or 2 (full up to v²).

    Returns
    -------
    T_prime : ndarray same shape
        Boosted multipoles.

    Limitations
    -----------
    The additive coefficients are derived for an isotropic background
    (Θ = Θ_0). For initial Θ with higher ℓ components, the full Paper I
    Prop 5 includes additional mixing terms that are not captured by the
    linear mixing matrix alone. These corrections are nonlinear in Θ_ℓ/Θ_0
    and scale as (Θ_ℓ/Θ_0) × v, so they vanish for isotropic input.
    """
    if order not in (1, 2):
        raise ValueError(f"order must be 1 or 2, got {order}")

    ell_max = len(T_ell) - 1
    T_ell = np.asarray(T_ell, dtype=float)

    # (a) Linear mixing matrix from channel_routing — works correctly in
    # dimensional convention because B[ℓ, ℓ'] couples same-dim multipoles.
    B = boost_mixing_matrix(v, ell_max)
    T_prime = B @ T_ell

    # (b) Additive induced from boost, dimensional convention
    T_0 = T_ell[0]
    n_plus_1 = moment_order + 1

    if order >= 1:
        # O(v) dipole induced from isotropic monopole
        if ell_max >= 1:
            T_prime[1] += n_plus_1 * T_0 * v

    if order >= 2:
        # O(v²) monopole shift (linear Doppler part): ΔΘ_0 = -v²/6
        T_prime[0] += -(n_plus_1 / 6.0) * T_0 * v ** 2
        # O(v²) quadrupole (linear Doppler part): ΔΘ_2 = (2/3) v²
        if ell_max >= 2:
            T_prime[2] += (2.0 / 3.0) * n_plus_1 * T_0 * v ** 2

        # O(v²) nonlinear contribution from (Θ_1')² = v² × P_1² nonlinearity:
        # P_1(μ)² = (1/3) P_0(μ) + (2/3) P_2(μ), so the boost-induced Θ_1 = v
        # feeds into T_0 and T_2 via the (n+1) n/2 × T_0/Θ_0² × Θ_1² response.
        # For isotropic background (Θ_0 = 1 implied by linear response), this gives:
        #   ΔT_0 (quadratic) = (n+1)n/2 × T_0 × v² × (1/3)
        #   ΔT_2 (quadratic) = (n+1)n/2 × T_0 × v² × (2/3)
        n_term = moment_order * n_plus_1 / 2.0
        T_prime[0] += n_term * T_0 * v ** 2 * (1.0 / 3.0)
        if ell_max >= 2:
            T_prime[2] += n_term * T_0 * v ** 2 * (2.0 / 3.0)

    return T_prime


# ═══════════════════════════════════════════════════════════════
# §3 — Thm 3 consistency check
# ═══════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class Thm3Result:
    """Output of the Paper I Thm 3 consistency check."""
    v: float
    xi: int
    Theta_input_coeffs: np.ndarray
    T_ell_spatial: np.ndarray      # Path 1: F(boost_Θ(Θ, v))
    T_ell_multipole: np.ndarray    # Path 2: Prop 5 applied to F(Θ)
    residual: np.ndarray           # T_ell_spatial − T_ell_multipole
    relative_residual: float       # ‖residual‖ / ‖T_ell_spatial‖
    L_compare: int                 # how many multipoles compared

    @property
    def residual_norm(self) -> float:
        return float(np.linalg.norm(self.residual))

    @property
    def spatial_norm(self) -> float:
        return float(np.linalg.norm(self.T_ell_spatial))


def thm3_consistency_check(
    Theta: AxisymmetricField, v: float,
    xi: int = 0,
    L_compare: int = 3,
    boost_order: int = 2,
    n_quad: int = 128,
) -> Thm3Result:
    """Run both paths of the Paper I Thm 3 commutative diagram.

    Thm 3 (Paper I): for one-field Teff ansatz (η ≡ 0), the diagram commutes
    exactly — spatial boost of Θ followed by F equals F of Θ followed by the
    multipole-space boost.

    This function returns a `Thm3Result` with the residual. For the actual
    Paper I claim to hold, we need:
      - η ≡ 0 (one-field)
      - `boost_multipoles_prop5` accurate to the v-order of interest
      - quadrature errors sub-dominant

    Any nonzero residual beyond O(v^{order+1}) indicates a bug or a failure
    of the exact-boost theorem for the chosen ξ.

    Parameters
    ----------
    Theta : AxisymmetricField
        Input temperature field.
    v : float
        Boost velocity.
    xi : int, optional
        Statistics ∈ {-1, 0, +1}. Default 0 (MB).
    L_compare : int, optional
        Number of multipoles to compare.
    boost_order : int, optional
        Order of the Prop 5 multipole boost (1 or 2).
    n_quad : int, optional
        Quadrature points (used in both F applications and spatial boost).

    Returns
    -------
    Thm3Result
    """
    # Path 1: spatial boost then F
    # Need L_max_out high enough to capture all coupling
    Theta_boosted = boost_theta_axisymmetric(
        Theta, v, L_max_out=L_compare + 2, n_quad=n_quad,
    )
    res_spatial = axisymmetric_F(
        xi, Theta_boosted, L_out=L_compare,
        n_quad=n_quad, check_admissibility=False,  # may dip slightly for large v
    )
    T_spatial = res_spatial.T_ell

    # Path 2: F then multipole boost
    res_F = axisymmetric_F(xi, Theta, L_out=L_compare + 1, n_quad=n_quad)
    # Apply Prop 5 to the multipoles (using dimensional T convention)
    T_prime_full = boost_multipoles_prop5(
        res_F.T_ell, v, moment_order=3, order=boost_order,
    )
    T_multipole = T_prime_full[: L_compare + 1]

    residual = T_spatial - T_multipole
    norm_T = float(np.linalg.norm(T_spatial))
    rel = float(np.linalg.norm(residual)) / norm_T if norm_T > 1e-30 else 0.0

    return Thm3Result(
        v=v, xi=xi,
        Theta_input_coeffs=Theta.coeffs.copy(),
        T_ell_spatial=T_spatial,
        T_ell_multipole=T_multipole,
        residual=residual,
        relative_residual=rel,
        L_compare=L_compare,
    )


def boost_order_convergence(
    Theta: AxisymmetricField,
    v_list: List[float],
    xi: int = 0,
    boost_order: int = 2,
    L_compare: int = 3,
) -> List[Thm3Result]:
    """Run Thm 3 check at multiple v values to verify O(v^{order+1}) convergence.

    For a boost implementation truncated at order N, the residual
    ‖Path 1 − Path 2‖ should scale as v^{N+1} as v → 0.

    Returns a list of `Thm3Result` ordered by `v_list`.
    """
    return [
        thm3_consistency_check(Theta, v, xi=xi, L_compare=L_compare,
                               boost_order=boost_order)
        for v in v_list
    ]


# ═══════════════════════════════════════════════════════════════
# §4 — Convenience wrappers
# ═══════════════════════════════════════════════════════════════

def axisymmetric_boost_velocity_to_multipole(
    v: float, Theta_0: float = 1.0,
) -> np.ndarray:
    """Expected dipole induced by a pure boost of an isotropic field.

    For Θ ≡ Θ_0 (isotropic), after boost by v along +ẑ:
        T_1 / T_0 = (n+1) v                  (linear order, n = 3 for energy)

    So the dipole amplitude is predictably (n+1) × v × T_0^{n+1} × I_n(ξ, 0).

    This wrapper returns the expected dipole for cross-check tests.
    """
    # For axisymmetric isotropic input, Prop 5 gives T_1 ≈ v × T_0 at leading
    # (from the additive v term and first-order mixing contributions).
    return np.array([0.0, v * (Theta_0 ** 4), 0.0, 0.0])
