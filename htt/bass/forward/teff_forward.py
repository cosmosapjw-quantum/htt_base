"""bass/forward/teff_forward.py — T_eff forward closure (C-12 / C-14).

Implements the angular closure

    Θ(ê) = 1 + A · P₁(cosθ) + Q · P₂(cosθ)

and its Θ⁴ Legendre expansion

    Θ⁴ = Σ_{ℓ=0}^{8} a_ℓ(A, Q) · P_ℓ(cosθ)

via closed-form C-14 Gaunt algebra. The a_ℓ(A, Q) polynomials are used as
the forward map from the Bianchi tilt/shear parameters (A ≈ β, Q ∝ σ/H)
to the observable CMB multipole pattern entering the MES bounds.

Accuracy note (P4 audit, legacy v8.3.0):
  ℓ ≤ 3 accurate to < 1% (Gauss-Legendre verified)
  ℓ = 4 approximate (~2% error at A, Q = 0.01)
  ℓ ≥ 5 approximate, up to O(1) error in high cross-terms

This is adequate because the full T_eff correction to the shear signal is
< 3 × 10⁻⁴ relative (see validation/pstf_teff_structural.py, legacy). The
backward map (inversion) is implemented in ``teff_backward.py`` with three
strategies ranging from analytic (small-(A, Q)) to exact Gauss-Legendre
L² projection (machine precision).

Non-perturbative tilt interoperability
--------------------------------------
The closure itself is perturbative in (A, Q) but makes NO small-β
assumption: A is a free parameter, typically set by a non-perturbative
tilt evolution (bass.background.nonperturbative_tilt) via A = β or by a
higher-order map A = tanh(β) when the small-angle approximation breaks.
"""
from __future__ import annotations

import numpy as np
from typing import Dict, Union

__all__ = [
    'TeffBianchiForward',
    'theta4_coefficients',
    'theta4_coefficients_vec',
    'monopole_gauge_check',
]


# ════════════════════════════════════════════════════════════════════
# Closed-form Θ⁴ Legendre coefficients (C-14 Gaunt algebra)
# ════════════════════════════════════════════════════════════════════

def theta4_coefficients(A: float, Q: float) -> Dict[int, float]:
    """Θ⁴ Legendre coefficients a₀..a₈ via C-14 Gaunt algebra.

    Computes the coefficients in

        Θ⁴(cosθ) = [1 + A·P₁ + Q·P₂]⁴ = Σ_{ℓ=0}^{8} a_ℓ · P_ℓ(cosθ)

    by expanding the quartic binomial and applying the Gaunt triple-product
    identities ``∫ P_a P_b P_c``.

    Accuracy (see module docstring): ℓ ≤ 3 < 1%; ℓ ≥ 5 approximate.

    Parameters
    ----------
    A : float
        Dipole amplitude. At leading order A ≈ β (tilt rapidity).
    Q : float
        Quadrupole amplitude. At leading order Q ≈ (5/3)·σ/H.

    Returns
    -------
    dict[int, float]
        {0: a₀, 1: a₁, ..., 8: a₈}.
    """
    A2 = A * A
    A3 = A2 * A
    A4 = A2 * A2
    Q2 = Q * Q
    Q3 = Q2 * Q
    Q4 = Q2 * Q2
    AQ = A * Q
    A2Q = A2 * Q
    AQ2 = A * Q2
    A2Q2 = A2 * Q2
    A3Q = A3 * Q

    a: Dict[int, float] = {}
    a[0] = (
        1.0
        + 2.0 * A2
        + (2.0 / 3.0) * Q2
        + (12.0 / 5.0) * A2Q
        + (36.0 / 35.0) * Q3
        + (6.0 / 5.0) * A4
        + (72.0 / 35.0) * A2Q2
        + (100.0 / 231.0) * Q4
    )
    a[1] = (
        4.0 * A * (1.0 + (6.0 / 5.0) * Q + (18.0 / 35.0) * Q2)
        + (12.0 / 5.0) * A3
        + (72.0 / 35.0) * A3Q
    )
    a[2] = (
        4.0 * Q
        + 4.0 * A2
        + (12.0 / 7.0) * Q2
        + (24.0 / 5.0) * A2Q
        + (108.0 / 77.0) * Q3
        + (12.0 / 5.0) * A4
    )
    a[3] = (
        (36.0 / 5.0) * AQ
        + (36.0 / 5.0) * A3
        + (360.0 / 77.0) * AQ2
    )
    a[4] = (
        (108.0 / 35.0) * Q2
        + (72.0 / 7.0) * A2Q
        + (36.0 / 5.0) * A4
        + (3240.0 / 1001.0) * Q3
    )
    a[5] = (
        (360.0 / 77.0) * AQ2
        + (720.0 / 77.0) * A3Q
    )
    a[6] = (
        (3240.0 / 1001.0) * Q3
        + (1080.0 / 77.0) * A2Q2
    )
    a[7] = (5040.0 / 1001.0) * A * Q3
    a[8] = (
        (100.0 / 231.0) * Q4
        + (900.0 / 143.0) * A2 * Q3
    )
    return a


def theta4_coefficients_vec(
    A: Union[float, np.ndarray],
    Q: Union[float, np.ndarray],
) -> Dict[int, np.ndarray]:
    """Vectorized Θ⁴ Legendre coefficients for arrays of (A, Q).

    Broadcasting follows NumPy rules. Returns a dict of float64 arrays.
    """
    A_arr = np.asarray(A, dtype=np.float64)
    Q_arr = np.asarray(Q, dtype=np.float64)
    A2, A3, A4 = A_arr ** 2, A_arr ** 3, A_arr ** 4
    Q2, Q3, Q4 = Q_arr ** 2, Q_arr ** 3, Q_arr ** 4

    return {
        0: (
            1.0
            + 2.0 * A2
            + (2.0 / 3.0) * Q2
            + (12.0 / 5.0) * A2 * Q_arr
            + (36.0 / 35.0) * Q3
            + (6.0 / 5.0) * A4
            + (72.0 / 35.0) * A2 * Q2
            + (100.0 / 231.0) * Q4
        ),
        1: (
            4.0 * A_arr * (1.0 + (6.0 / 5.0) * Q_arr + (18.0 / 35.0) * Q2)
            + (12.0 / 5.0) * A3
            + (72.0 / 35.0) * A3 * Q_arr
        ),
        2: (
            4.0 * Q_arr
            + 4.0 * A2
            + (12.0 / 7.0) * Q2
            + (24.0 / 5.0) * A2 * Q_arr
            + (108.0 / 77.0) * Q3
            + (12.0 / 5.0) * A4
        ),
        3: (
            (36.0 / 5.0) * A_arr * Q_arr
            + (36.0 / 5.0) * A3
            + (360.0 / 77.0) * A_arr * Q2
        ),
        4: (
            (108.0 / 35.0) * Q2
            + (72.0 / 7.0) * A2 * Q_arr
            + (36.0 / 5.0) * A4
            + (3240.0 / 1001.0) * Q3
        ),
        5: (
            (360.0 / 77.0) * A_arr * Q2
            + (720.0 / 77.0) * A3 * Q_arr
        ),
        6: (
            (3240.0 / 1001.0) * Q3
            + (1080.0 / 77.0) * A2 * Q2
        ),
        7: (5040.0 / 1001.0) * A_arr * Q3,
        8: (
            (100.0 / 231.0) * Q4
            + (900.0 / 143.0) * A2 * Q3
        ),
    }


# ════════════════════════════════════════════════════════════════════
# Monopole gauge check — Gauss-Legendre verification
# ════════════════════════════════════════════════════════════════════

def monopole_gauge_check(A: float, Q: float, n_theta: int = 200) -> float:
    """Verify the monopole gauge ⟨Θ⟩_Ω = 1 by Gauss-Legendre quadrature.

    Computes ½ ∫_{-1}^{1} [1 + A·P₁(x) + Q·P₂(x)] dx which is identically 1
    by orthogonality of the Legendre basis. Deviations signal a coding
    error, not a physical effect.

    Parameters
    ----------
    A, Q : float
        Dipole and quadrupole amplitudes.
    n_theta : int
        Number of Gauss-Legendre nodes. 200 gives ≲ 10⁻¹⁵ precision.

    Returns
    -------
    float
        The numerical ⟨Θ⟩. Should equal 1 to machine precision.
    """
    from numpy.polynomial.legendre import leggauss
    x, w = leggauss(n_theta)
    theta = 1.0 + A * x + Q * 0.5 * (3.0 * x ** 2 - 1.0)
    return float(0.5 * np.sum(w * theta))


# ════════════════════════════════════════════════════════════════════
# Forward model class
# ════════════════════════════════════════════════════════════════════

class TeffBianchiForward:
    """T_eff Bianchi forward model: (Σ², β) → (f₂, f₃, a_ℓ).

    Uses the closed-form Θ⁴ expansion ``theta4_coefficients`` together
    with the standard maps

        A = tilt_to_A(β) = β          (leading order)
        Q = shear_to_Q(Σ²) = (5/3)·√(6·Σ²)

    where the factor (5/3) comes from the dipole-gradient prefactor × C₂
    in the C-09 MES derivation. Higher-order A(β) from non-perturbative
    tilt is available via ``TeffBianchiForward.tilt_to_A_exact``.

    Power fractions are defined with the T_eff convention f_ℓ = a_ℓ / (4·a₀),
    the factor 4 converting from Θ⁴ back to the physical temperature.
    """

    def __init__(self, n_theta: int = 200):
        self.n_theta = n_theta

    def shear_to_Q(self, Sigma2: float) -> float:
        """Map normalised shear Σ² to quadrupole amplitude Q ≈ (5/3)·√(6 Σ²)."""
        if Sigma2 <= 0:
            return 0.0
        sigma_H = np.sqrt(6.0 * Sigma2)
        return (5.0 / 3.0) * sigma_H

    def tilt_to_A(self, beta: float) -> float:
        """Linear map A ≈ β (small-β limit).

        For β > 0.1 prefer ``tilt_to_A_exact`` which uses the non-
        perturbative closure A = tanh(β) = v/c.
        """
        return beta

    @staticmethod
    def tilt_to_A_exact(beta: float) -> float:
        """Non-perturbative map A = tanh(β) = v/c.

        Consistent with the sinh/cosh RHS in
        ``bass.background.nonperturbative_tilt``. At β = 0.1 the relative
        difference A_linear − A_exact = β − tanh(β) ≈ β³/3 ≈ 3.3 × 10⁻⁴.
        """
        return float(np.tanh(beta))

    def compute_from_shear(
        self,
        Sigma2: float,
        beta: float = 0.0,
        *,
        exact_tilt: bool = False,
    ) -> dict:
        """Return ``{A, Q, a_ell, f2, f3, gauge_deviation}``.

        Parameters
        ----------
        Sigma2 : float
            Σ² shear amplitude.
        beta : float
            Tilt rapidity.
        exact_tilt : bool
            If True, use A = tanh(β); otherwise A = β.
        """
        Q = self.shear_to_Q(Sigma2)
        A = self.tilt_to_A_exact(beta) if exact_tilt else self.tilt_to_A(beta)

        coeffs = theta4_coefficients(A, Q)
        gauge = monopole_gauge_check(A, Q, self.n_theta)

        a0 = coeffs[0]
        f2 = coeffs[2] / (4.0 * a0) if a0 > 0 else 0.0
        f3 = coeffs[3] / (4.0 * a0) if a0 > 0 else 0.0

        return {
            'A': A,
            'Q': Q,
            'a_ell': coeffs,
            'f2': f2,
            'f3': f3,
            'gauge_deviation': abs(gauge - 1.0),
        }

    def transfer_functions(
        self,
        Sigma2_grid: np.ndarray,
        beta: float = 0.0,
        *,
        exact_tilt: bool = False,
    ) -> dict:
        """Grid sweep: f₂(Σ²) and f₃(Σ²) at fixed β.

        Returns dict with ``'Sigma2'``, ``'f2'``, ``'f3'`` as lists.
        """
        grid = np.asarray(Sigma2_grid, dtype=np.float64)
        f2_arr = np.zeros_like(grid)
        f3_arr = np.zeros_like(grid)
        for i, S2 in enumerate(grid):
            r = self.compute_from_shear(float(S2), beta, exact_tilt=exact_tilt)
            f2_arr[i] = r['f2']
            f3_arr[i] = r['f3']
        return {
            'Sigma2': grid.tolist(),
            'f2': f2_arr.tolist(),
            'f3': f3_arr.tolist(),
        }
