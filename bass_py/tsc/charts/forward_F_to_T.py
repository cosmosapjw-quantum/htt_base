"""
bass/teff/forward_F_to_T.py  (Week 2 Day 2)
============================================

Paper I forward map F : (ξ, Θ(ê), [η(ê)]) → (T_0, T_a, T_ab, T_abc, ...)

Role in Paper I
---------------
Given the species exponential-family distribution

    f_s(x, ê) = Φ_{ξ_s}( x / Θ_s(ê) − η_s(ê) )

where x = E/(k_B T_{0,s}) is the dimensionless energy, the macroscopic
multipole moments of the stress-energy tensor are obtained by energy
integration plus PSTF angular projection:

    T_ℓ(A_ℓ) = ⟨ Θ(ê)^{n+1} × I_n(ξ, η(ê)) × ê_⟨A_ℓ⟩ ⟩_{S²}

with n ∈ {2 (number), 3 (energy), 4 (stress)} depending on which multipole
hierarchy is tracked. For CMB-type analyses, n = 3 is canonical (energy
density + heat flux + anisotropic stress).

The PSTF bracket ê_⟨A_ℓ⟩ denotes the trace-free symmetric product of ℓ
direction unit vectors, reducing in axisymmetric form to Legendre
polynomials P_ℓ(μ) with μ = ê·n̂ the polar cosine along the symmetry axis.

Axisymmetric reduction
-----------------------
For axisymmetric Θ(μ), η(μ):

    T_ℓ = (2ℓ+1)/2 × ∫_{-1}^{1} dμ  Θ(μ)^{n+1} I_n(ξ, η(μ)) P_ℓ(μ)

which reduces S² surface integrals to 1D Gauss-Legendre quadrature.

General 3D
----------
For non-axisymmetric inputs, a Lebedev quadrature on S² is required. Day 2
provides the API scaffolding (`general_F_stub`); full 3D quadrature
implementation is deferred to Week 3 (`teff/spherical_quadrature.py`).

Paper I cross-references
------------------------
  - Eq. 5 (Φ_ξ occupation function)
  - §III (PSTF multipole reconstruction)
  - Thm 3 (exact boost at μ = 0)
  - Prop 5 (perturbative boost with mixing coefficients)
  - Appendix A (Laguerre spectral expansion)

Implementation conventions
--------------------------
- Input multipoles are axisymmetric Legendre coefficients Θ_ℓ (not fully
  tensorial). This matches Paper I §IV convention for 1D reduction.
- Default moment order n = 3 (energy multipoles). Caller can override via
  `moment_order` parameter for number (n=2) or stress (n=4) reconstructions.
- Admissibility checked at construction: Θ(μ) > 0 required; if ξ = +1
  (BE), also η(μ) ≤ 0 required.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import math

import numpy as np
from scipy.special import eval_legendre

from tsc.charts.laguerre_basis import xi_moment, build_stiffness_table


# ═══════════════════════════════════════════════════════════════
# §1 — Axisymmetric Legendre field representation
# ═══════════════════════════════════════════════════════════════

@dataclass
class AxisymmetricField:
    """Axisymmetric scalar field f(μ) = Σ_ℓ coeffs[ℓ] × P_ℓ(μ).

    Attributes
    ----------
    coeffs : ndarray shape (L+1,)
        Legendre coefficients [c_0, c_1, ..., c_L].
    name : str
        Human-readable label (e.g., 'Theta', 'eta').
    """
    coeffs: np.ndarray
    name: str = "field"

    def __post_init__(self):
        self.coeffs = np.asarray(self.coeffs, dtype=float)
        if self.coeffs.ndim != 1:
            raise ValueError(
                f"coeffs must be 1D, got shape {self.coeffs.shape}"
            )

    @property
    def L_max(self) -> int:
        """Highest retained multipole ℓ."""
        return len(self.coeffs) - 1

    def evaluate(self, mu) -> np.ndarray:
        """Evaluate f(μ) at given cos θ values.

        Parameters
        ----------
        mu : array-like or scalar
            Evaluation points in [-1, 1].

        Returns
        -------
        f : array
            Field values.
        """
        mu_arr = np.asarray(mu, dtype=float)
        result = np.zeros_like(mu_arr)
        for ell, coeff in enumerate(self.coeffs):
            if abs(coeff) > 0:
                result = result + coeff * eval_legendre(ell, mu_arr)
        return result


def isotropic_theta(value: float = 1.0) -> AxisymmetricField:
    """Θ(μ) ≡ `value` (isotropic temperature field)."""
    return AxisymmetricField(coeffs=np.array([value]), name="Theta_iso")


def quadrupole_theta(Theta_0: float, Theta_2: float) -> AxisymmetricField:
    """Θ(μ) = Θ_0 + Θ_2 × P_2(μ) (axisymmetric quadrupole perturbation)."""
    return AxisymmetricField(
        coeffs=np.array([Theta_0, 0.0, Theta_2]),
        name=f"Theta_Q({Theta_0}, {Theta_2})",
    )


def dipole_theta(Theta_0: float, Theta_1: float) -> AxisymmetricField:
    """Θ(μ) = Θ_0 + Θ_1 × P_1(μ) = Θ_0 + Θ_1 × μ (axisymmetric dipole)."""
    return AxisymmetricField(
        coeffs=np.array([Theta_0, Theta_1]),
        name=f"Theta_D({Theta_0}, {Theta_1})",
    )


# ═══════════════════════════════════════════════════════════════
# §2 — Admissibility checks
# ═══════════════════════════════════════════════════════════════

def check_theta_positive(
    Theta: AxisymmetricField, n_check: int = 200,
) -> bool:
    """Verify Θ(μ) > 0 on [-1, 1] via dense sampling."""
    mu = np.linspace(-1.0, 1.0, n_check)
    return bool(np.all(Theta.evaluate(mu) > 0))


def check_be_admissibility(
    eta: Optional[AxisymmetricField], n_check: int = 200,
) -> bool:
    """Verify η(μ) ≤ 0 on [-1, 1] (required for BE statistics).

    If eta is None (one-field), trivially admissible.
    """
    if eta is None:
        return True
    mu = np.linspace(-1.0, 1.0, n_check)
    return bool(np.all(eta.evaluate(mu) <= 1e-15))


# ═══════════════════════════════════════════════════════════════
# §3 — Axisymmetric forward map F
# ═══════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class ForwardResult:
    """Container for forward map output multipoles."""
    T_ell: np.ndarray              # axisymmetric multipoles [T_0, ..., T_{L_out}]
    xi: int
    moment_order: int              # n (= 2, 3, or 4)
    L_out: int
    n_quad: int                    # quadrature points used

    @property
    def T_0(self) -> float:
        """Monopole (energy density proxy)."""
        return float(self.T_ell[0])

    @property
    def T_1(self) -> float:
        """Dipole coefficient (heat flux proxy)."""
        if self.L_out >= 1:
            return float(self.T_ell[1])
        return 0.0

    @property
    def T_2(self) -> float:
        """Quadrupole coefficient (anisotropic stress proxy)."""
        if self.L_out >= 2:
            return float(self.T_ell[2])
        return 0.0

    @property
    def T_3(self) -> float:
        """Octupole coefficient."""
        if self.L_out >= 3:
            return float(self.T_ell[3])
        return 0.0


def axisymmetric_F(
    xi: int,
    Theta: AxisymmetricField,
    eta: Optional[AxisymmetricField] = None,
    L_out: int = 3,
    moment_order: int = 3,
    n_quad: Optional[int] = None,
    check_admissibility: bool = True,
) -> ForwardResult:
    """Paper I forward map F for axisymmetric Θ(μ), η(μ).

        T_ℓ = (2ℓ+1)/2 × ∫_{-1}^{1} dμ Θ(μ)^{n+1} I_n(ξ, η(μ)) P_ℓ(μ)

    Parameters
    ----------
    xi : int
        Statistics ∈ {-1 (FD), 0 (MB), +1 (BE)}.
    Theta : AxisymmetricField
        Direction-dependent temperature field Θ(μ) > 0.
    eta : AxisymmetricField, optional
        Direction-dependent fugacity η(μ). If None, η ≡ 0 (one-field).
    L_out : int, optional
        Highest multipole to return. Default 3 (up to octupole).
    moment_order : int, optional
        n in I_n: 2 (number), 3 (energy, default), 4 (stress).
    n_quad : int, optional
        Gauss-Legendre quadrature points. Defaults to 4 × L_out + 8 to
        handle the Θ^{n+1} nonlinearity with order (n+1) × L_out polynomial.
    check_admissibility : bool
        If True (default), verify Θ > 0 and (for BE) η ≤ 0 before computing.

    Returns
    -------
    ForwardResult
        Wrapped multipole output.

    Raises
    ------
    ValueError
        If ξ invalid, Θ not positive, or BE with η > 0.
    """
    if xi not in (-1, 0, +1):
        raise ValueError(f"ξ must be ∈ {{-1, 0, +1}}, got {xi}")
    if moment_order not in (2, 3, 4):
        raise ValueError(
            f"moment_order must be 2, 3, or 4, got {moment_order}"
        )

    if check_admissibility:
        if not check_theta_positive(Theta):
            raise ValueError(f"Θ(μ) must be positive on [-1, 1]")
        if xi == +1 and not check_be_admissibility(eta):
            raise ValueError("BE requires η(μ) ≤ 0 on [-1, 1]")

    # Quadrature order: Θ^{n+1} P_ℓ polynomial degree ≈ (n+1)×L_Theta + L_out
    # so we need at least this many points. Default generous.
    if n_quad is None:
        L_Theta = Theta.L_max
        L_eta = 0 if eta is None else eta.L_max
        min_order = (moment_order + 1) * L_Theta + L_out + 2 * L_eta
        n_quad = max(16, min_order + 8)

    # Gauss-Legendre on [-1, 1]
    mu, w = np.polynomial.legendre.leggauss(n_quad)

    # Evaluate Θ and η at quadrature points
    Theta_vals = Theta.evaluate(mu)
    eta_vals = np.zeros_like(mu) if eta is None else eta.evaluate(mu)

    # Compute I_n(ξ, η(μ)) point-wise
    I_vals = np.array([
        xi_moment(moment_order, xi, float(eta_val)) for eta_val in eta_vals
    ])

    # Integrand weight: Θ(μ)^{n+1} × I_n(ξ, η(μ))
    weight = (Theta_vals ** (moment_order + 1)) * I_vals

    # Project onto each Legendre mode
    T_ell = np.zeros(L_out + 1)
    for ell in range(L_out + 1):
        P_ell_vals = eval_legendre(ell, mu)
        integral = float(np.sum(w * weight * P_ell_vals))
        T_ell[ell] = (2 * ell + 1) / 2.0 * integral

    return ForwardResult(
        T_ell=T_ell, xi=xi,
        moment_order=moment_order, L_out=L_out, n_quad=n_quad,
    )


# ═══════════════════════════════════════════════════════════════
# §4 — Isotropic limit cross-check
# ═══════════════════════════════════════════════════════════════

def isotropic_limit_T0(
    xi: int, Theta_0: float = 1.0, eta_0: float = 0.0,
    moment_order: int = 3,
) -> float:
    """Analytical isotropic limit: T_0 = Θ_0^{n+1} × I_n(ξ, η_0).

    For Θ ≡ Θ_0, η ≡ η_0 (constants), all T_ℓ (ℓ ≥ 1) vanish and
        T_0 = (1/2) × ∫_{-1}^{1} dμ × Θ_0^{n+1} × I_n × P_0(μ)
            = Θ_0^{n+1} × I_n(ξ, η_0)

    Used for the sanity cross-check in the isotropic limit.
    """
    return (Theta_0 ** (moment_order + 1)) * xi_moment(moment_order, xi, eta_0)


# ═══════════════════════════════════════════════════════════════
# §5 — Linear-response (Paper I Prop 5 cross-check)
# ═══════════════════════════════════════════════════════════════

def linear_response_F(
    xi: int, Theta_0: float, Theta_ell_in: np.ndarray,
    moment_order: int = 3,
) -> np.ndarray:
    """Linear-response F: truncate to O(Θ_ℓ/Θ_0) terms.

    For small anisotropy Θ(μ) = Θ_0 × (1 + Σ_{ℓ≥1} (Θ_ℓ/Θ_0) P_ℓ(μ)),
    the forward map at linear order gives

        T_0^{lin} = Θ_0^{n+1} × I_n(ξ, 0)
        T_ℓ^{lin} = (n+1) × Θ_0^{n+1} × I_n(ξ, 0) × (Θ_ℓ / Θ_0)
                  = (n+1) × Θ_0^n × Θ_ℓ × I_n(ξ, 0)   for ℓ ≥ 1

    This linearization is the zeroth-order Paper I map and is used for
    sanity cross-checks against the full nonlinear `axisymmetric_F`.

    Parameters
    ----------
    xi : int
        Statistics.
    Theta_0 : float
        Background (monopole) temperature.
    Theta_ell_in : ndarray
        Higher-ℓ coefficients [Θ_1, Θ_2, ...] (starting at ℓ = 1).
    moment_order : int
        n in I_n (default 3).

    Returns
    -------
    T_ell : ndarray shape (L+1,)
        Linearized multipole output [T_0, T_1, ..., T_L].
    """
    I_n = xi_moment(moment_order, xi, 0.0)
    L = len(Theta_ell_in)
    T_ell = np.zeros(L + 1)
    T_ell[0] = (Theta_0 ** (moment_order + 1)) * I_n
    for ell_idx in range(L):
        ell = ell_idx + 1
        T_ell[ell] = (moment_order + 1) * (Theta_0 ** moment_order) \
                     * Theta_ell_in[ell_idx] * I_n
    return T_ell


# ═══════════════════════════════════════════════════════════════
# §6 — General 3D stub (Week 3 deferred)
# ═══════════════════════════════════════════════════════════════

def general_F_stub(*args, **kwargs):
    """General 3D forward map F (Week 3 implementation).

    Will use `teff/spherical_quadrature.py` (Lebedev quadrature on S²) to
    handle non-axisymmetric Θ_{a_1...a_ℓ}(ê) inputs and produce fully
    tensorial PSTF outputs.

    Status: NOT_IMPLEMENTED — use `axisymmetric_F` for Day 2 — Week 3 work.
    """
    raise NotImplementedError(
        "General 3D forward F deferred to Week 3 (requires Lebedev "
        "quadrature module). Use axisymmetric_F for 1D reduction."
    )
