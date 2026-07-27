#!/usr/bin/env python3
"""
bounds.py — MES algebraic bounds and defect-variable computations.
==================================================================
All functions use VA-02 conventions (Σ²_std = σ_{ab}σ^{ab}/(6H²)).
Frame corrections from VT-07. Filling fraction from VT-09c.
Nonlinear corrections from VN-04.
"""
import numpy as np
from htt.core.ssot import C

# PR-124: active MES consumers traverse the typed successor registry.  The
# omega/accel coefficient triples below are the LEGACY-REPRODUCTION values
# (non-geodesic, print-only MESb; in-house reconstruction refuted rev-r190),
# fetched through the labeled legacy channel so historical outputs stay
# byte-stable.  They are explicitly NON-AUTHORITATIVE: the live authority is
# the typed successor (common.mes_theorem_authority); flowing the authorized
# geodesic values into result-producing consumers is a result-regeneration
# event owned by later PRs.
from common.mes_successor_registry import (
    current_mes_successor_registry,
    legacy_reproduction_coefficients,
)

_MES_SUCCESSOR = current_mes_successor_registry().successor
_MES_SUCCESSOR_ID = _MES_SUCCESSOR.successor_id
_LEGACY_COEFFS = legacy_reproduction_coefficients()
_SIGMA_C1, _SIGMA_C2, _SIGMA_C3 = (float(c) for c in _LEGACY_COEFFS["sigma"])
_OMEGA_C1, _OMEGA_C2, _OMEGA_C3 = (float(c) for c in _LEGACY_COEFFS["omega"])
_ACCEL_C1, _ACCEL_C2, _ACCEL_C3 = (float(c) for c in _LEGACY_COEFFS["accel"])

__all__ = [
    'B_sigma', 'B_omega', 'B_accel',
    'B_sigma_corrected', 'Sig2_max_MES', 'W2_max_MES', 'A2_max_MES',
    'eps1_from_beta', 'beta_safe',
    'x_defect', 'filling_fraction',
    'Sig2_BV', 'frame_bias',
    'nonlinear_R_sigma', 'nonlinear_R_omega',
]

# ═══════════════════════════════════════════════════════════
#  MES ALGEBRAIC BOUNDS (Maartens-Ellis-Stoeger 1995)
# ═══════════════════════════════════════════════════════════

def B_sigma(e1, e2=C.eps2, e3=C.eps3):
    """MES shear bound combination B_σ = (5/3)ε₁ + 3ε₂ + (3/7)ε₃.

    The MES shear bound (Maartens, Ellis & Stoeger 1995) constrains
    the shear-to-expansion ratio σ/Θ < B_σ from the observed CMB
    multipoles ε₁, ε₂, ε₃. The coefficients arise from the
    Clebsch-Gordan coupling in the linearised Boltzmann hierarchy.

    Parameters
    ----------
    e1 : float
        CMB dipole amplitude ε₁ = √(3C₁/(4π))/T₀ (dimensionless).
    e2 : float
        Quadrupole amplitude ε₂. Default: Planck PR3 value.
    e3 : float
        Octupole amplitude ε₃. Default: Planck PR3 value.

    Returns
    -------
    float
        B_σ (dimensionless). At S3: B_σ ≈ 2.48×10⁻³.
        Dipole channel contributes 99.4% of the total.

    References
    ----------
    Theorem 3.1, Eq. (3.7); StoegerME1995 Eq. (3.3).
    """
    return _SIGMA_C1*e1 + _SIGMA_C2*e2 + _SIGMA_C3*e3

def B_omega(e1, e2=C.eps2, e3=C.eps3):
    """MES vorticity bound combination B_ω = (3/4)ε₁ + 2ε₂ + (2/7)ε₃.

    Constrains ω̄ = √(ω_{ab}ω^{ab})/Θ < B_ω. Derived from the
    odd-parity sector of the Boltzmann hierarchy (ΔΘ = ±1 coupling).

    Parameters
    ----------
    e1, e2, e3 : float
        CMB multipole amplitudes (same as B_sigma).

    Returns
    -------
    float
        B_ω (dimensionless). Always B_ω < B_σ (Theorem 3.4).

    References
    ----------
    Theorem 3.2, Eq. (3.12).
    """
    return _OMEGA_C1*e1 + _OMEGA_C2*e2 + _OMEGA_C3*e3

def B_accel(e1, e2=C.eps2, e3=C.eps3):
    """MES acceleration bound combination B_u̇ = (3/4)ε₁ + ε₂ + (3/14)ε₃.

    Constrains |u̇|/(3H) < B_u̇. Derived from the even-parity
    acceleration sector (same Δℓ = ±1 as vorticity but opposite parity).

    Parameters
    ----------
    e1, e2, e3 : float
        CMB multipole amplitudes.

    Returns
    -------
    float
        B_u̇ (dimensionless). Always B_u̇ < B_ω < B_σ (Theorem 3.4).

    References
    ----------
    Theorem 3.3, Eq. (3.15).
    """
    return _ACCEL_C1*e1 + _ACCEL_C2*e2 + _ACCEL_C3*e3

# ─── Frame-corrected bounds (VT-07) ─────────────────────────

def B_sigma_corrected(e1, e2=C.eps2, e3=C.eps3):
    """Frame-corrected shear bound: R(ε₁) × B_σ, R = 1 + 2.69ε₁."""
    R = 1.0 + 2.69 * e1
    return R * B_sigma(e1, e2, e3)

def Sig2_max_MES(e1_total):
    """MES ceiling on Σ²_std: (3/2) × [B_σ^corr]²  (Corollary 3.1)."""
    return 1.5 * B_sigma_corrected(e1_total)**2

def W2_max_MES(e1_total):
    """MES ceiling on W²_std: (3/2) × B_ω²."""
    return 1.5 * B_omega(e1_total)**2

def A2_max_MES(e1_total):
    """MES ceiling on A²_std: (3/2) × B_u̇²."""
    return 1.5 * B_accel(e1_total)**2

# ═══════════════════════════════════════════════════════════
#  TILT AND FRAME CORRECTION (VT-07)
# ═══════════════════════════════════════════════════════════

def eps1_from_beta(beta, eta=C.eta_udot):
    """Boost dipole: ε₁ = β(1 + η_u̇).  VT-07 safe-route."""
    return beta * (1.0 + eta)

def beta_safe(e1, eta=C.eta_udot):
    """Safe-route tilt bound: β ≤ ε₁/(1 + η_u̇)."""
    return e1 / (1.0 + eta)

def frame_bias(e1, eta=C.eta_udot):
    """Frame-attribution bias 𝒷_σ = B_σ^obs - B_σ^geom.
    Fractional: 𝒷_σ/B_σ ≈ 2.69ε₁ ≈ η_u̇ β / B_σ."""
    Bs_obs = B_sigma_corrected(e1)
    Bs_geom = B_sigma(e1)
    return Bs_obs - Bs_geom

# ═══════════════════════════════════════════════════════════
#  DEFECT VARIABLES AND TYPE-DEPENDENT BOUNDS
# ═══════════════════════════════════════════════════════════

def x_defect(Sig2, Omega_tilt=0.0, Omega_k_aniso=0.0, W2=0.0):
    """Master defect variable: x = Σ²_std - W²_std + Ω_tilt + Ω_{k,aniso}.

    Implements the exact algebraic identity of Theorem 2.1.
    The −W² term arises from the generalised Hamiltonian constraint
    (Eq. 2.8); it is non-zero only for Bianchi types admitting
    vorticity (VII_h in the present classification).

    Parameters
    ----------
    Sig2 : float
        Standardised shear Σ²_std = σ_{ab}σ^{ab}/(6H²). Non-negative.
    Omega_tilt : float
        Tilt density parameter (1+w)Ω_m sinh²β. Non-negative.
    Omega_k_aniso : float
        Anisotropic curvature Ω_k − Ω_{k,ref}. Can be positive or negative.
    W2 : float
        Standardised vorticity W²_std = ω_{ab}ω^{ab}/(6H²). Non-negative.
        Default 0.0 (irrotational models). Placed last for backward
        compatibility with existing callers.

    Returns
    -------
    float
        Signed Gauss/Friedmann budget projection.  It may be negative because
        the vorticity term enters with a minus sign and the anisotropic
        curvature coordinate is signed; it is not a distance or occupancy.

    References
    ----------
    Theorem 2.1, Eq. (2.10).
    """
    return Sig2 - W2 + Omega_tilt + Omega_k_aniso

def Omega_tilt(beta, w=0.0, Omega_m=C.Omega_m):
    """Tilt density parameter: Ω_tilt = (1+w)Ω_m sinh²β."""
    return (1.0 + w) * Omega_m * np.sinh(beta)**2

def filling_fraction(x_obs, x_max):
    """Filling fraction: ℱ = x_obs / x_max.  Invariant under frame corrections."""
    if x_max <= 0:
        return np.inf
    return x_obs / x_max

# ─── Type-dependent bounds ───────────────────────────────────

_TYPE_INFO = {
    # (has_vorticity, has_curvature, has_spiral, class)
    'I':     (False, False, False, 'A'),
    'II':    (False, True,  False, 'A'),
    'V':     (False, True,  False, 'B'),
    'VI0':   (False, False, False, 'B'),
    'VII0':  (False, False, False, 'A'),
    'VIII':  (False, True,  False, 'A'),
    'IX':    (False, True,  False, 'A'),
    'VIIh':  (True,  True,  True,  'A'),
    'III':   (False, True,  False, 'B'),
}

def x_max_type(type_name, e1, tilted=False, beta=0.0, w=0.0):
    """Maximum defect x for a given Bianchi type and tilt state.
    
    Returns (x_max, components_dict).
    """
    info = _TYPE_INFO.get(type_name)
    if info is None:
        raise ValueError(f"Unknown Bianchi type: {type_name}")
    
    has_vort, has_curv, has_spiral, bclass = info
    
    Sig2_max = Sig2_max_MES(e1)
    
    components = {'Sigma2_max': Sig2_max, 'W2_max': 0.0, 'A2_max': 0.0,
                  'Omega_tilt': 0.0, 'Omega_k_aniso': 0.0}
    
    x = Sig2_max
    
    if tilted and beta > 0:
        Ot = Omega_tilt(beta, w)
        components['Omega_tilt'] = Ot
        x += Ot
    
    return x, components

# ═══════════════════════════════════════════════════════════
#  BV MOMENTUM CONSTRAINT
# ═══════════════════════════════════════════════════════════

def Sig2_BV(beta, Omega_K, w=0.0, Omega_m=C.Omega_m):
    """Bianchi V momentum constraint: Σ²_std = [(1+w)Ω_m]²β²/(4|Ω_K|).

    For tilted Bianchi V, the Einstein G_{0z} equation algebraically
    determines the shear from the tilt and curvature. This constraint
    has no free parameter: the shear is FIXED by β and Ω_K.

    At the CF4 tilt β = 1.334×10⁻³ and Planck Ω_K = 0.001, the
    forced shear produces D₂ ~ 10¹⁷ μK², a 10¹⁵-fold overproduction
    relative to D₂^obs = 225.9 μK². This excludes BV at ln B = −24.5.

    Parameters
    ----------
    beta : float
        Tilt rapidity (dimensionless hyperbolic angle).
    Omega_K : float
        Curvature density parameter. Must be > 0 for BV.
    w : float
        Equation of state. Default 0 (dust).
    Omega_m : float
        Matter density parameter. Default Planck 2018.

    Returns
    -------
    float
        Σ²_std. Returns np.inf if Ω_K ≤ 0.

    References
    ----------
    Eq. (3.30), Appendix A §A.2.
    """
    if Omega_K <= 0:
        return np.inf
    return ((1.0 + w) * Omega_m)**2 * beta**2 / (4.0 * Omega_K)

# ═══════════════════════════════════════════════════════════
#  NONLINEAR CORRECTIONS (VN-04)
# ═══════════════════════════════════════════════════════════

def nonlinear_R_sigma(sigma_H, ell_max=3):
    """Nonlinear correction to shear: R_σ = Σ²_nl / Σ²_lin.
    
    At σ/Θ ~ 10⁻³: R_σ ≈ 1 + 6(σ/Θ)² ≈ 1 + 6×10⁻⁶ ≈ 1.000006.
    """
    return 1.0 + 6.0 * sigma_H**2

def nonlinear_R_omega(omega_H, sigma_H):
    """Nonlinear correction to vorticity: R_ω = W²_nl / W²_lin.
    
    Shear-vorticity coupling: dominant at O(σ²ω²).
    """
    return 1.0 + 4.0 * sigma_H**2
