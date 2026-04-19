#!/usr/bin/env python3
"""
tilted_flrw.py — Tilted-FLRW observables in defect variables.
==============================================================
Implements all boxed equations from TF-T01 through TF-T03,
connecting the homogeneous Bianchi defect framework to the
perturbative Tsagas tilted-FLRW programme.

All functions use VA-02 conventions (Σ²_std = σ_{ab}σ^{ab}/(6H²)).
Requires ssot.py for constants.

Reference equations (TF-series LaTeX labels):
  H-ratio-defect    → tilted_H_ratio()
  tilted-H-tsagas   → tilted_H_perturbative()
  What-defect        → matter_vorticity()
  A2-hat-defect      → matter_acceleration()
  lambda-J-defect    → peculiar_jeans()
  Dq-defect          → Delta_q()
  q-decomposition    → Delta_q_three_term()
  beta-from-colin    → beta_from_colin()
"""
import numpy as np
from htt.core.ssot import C

__all__ = [
    'tilted_H_ratio', 'tilted_H_perturbative',
    'Delta_q', 'Delta_q_three_term',
    'peculiar_jeans', 'q_matter',
    'velocity_growth',
    'matter_vorticity', 'matter_acceleration',
    'beta_from_colin',
    'Omega_tilt', 'tilted_densities',
]

# ─── Physical constants ──────────────────────────────────────
_c_km_s = 299792.458            # km/s
# H₀ here is the GEOMETRY-FRAME value H_θ = Θ/3 (not the tilted-observer Ĥ).
# The tilted observer measures Ĥ = H_θ·cosh(β) ≈ H_θ(1 + β²/2).
# This module CORRECTLY uses H_θ as the base and computes the tilt
# correction on top of it, avoiding the double-counting principle
# (using tilt-contaminated H₀ as background AND adding ΔH from tilt).
_H0 = C.h * 100.0               # km/s/Mpc  (67.36, geometry-frame Planck 2018)
_lambda_H = _c_km_s / _H0       # Mpc  (Hubble radius ≈ 4452)
_eta_udot = C.eta_udot           # 1/12 (exact, radiation)


# ═══════════════════════════════════════════════════════════════
#  TILTED FRIEDMANN
# ═══════════════════════════════════════════════════════════════

def tilted_H_ratio(beta):
    """Exact ratio Ĥ²/H² = cosh²β.

    From TF-T01 Eq. H-ratio-defect (neglecting ξ ~ 8e-9).
    The fractional correction is ΔH/H = cosh β − 1 ≈ β²/2.

    Parameters
    ----------
    beta : float or array
        Tilt rapidity (dimensionless).

    Returns
    -------
    float or array
        Ĥ²/H².
    """
    return np.cosh(beta)**2


def tilted_H_perturbative(beta, d_Mpc, H0=None):
    """Perturbative tilted Hubble rate Ĥ = H[1 + β λ_H/(3d)].

    From TF-T01 Eq. tilted-H-tsagas.  Valid for d ≪ λ_H only.
    At d ~ λ_H the formula exits its validity range; use
    tilted_H_ratio() instead.

    Parameters
    ----------
    beta : float
        Tilt rapidity.
    d_Mpc : float
        Comoving survey depth in Mpc.  Must be > 0.
    H0 : float, optional
        Hubble constant in km/s/Mpc.  Default: SSOT value.

    Returns
    -------
    H_tilt : float
        Tilted Hubble rate in km/s/Mpc.
    DH_over_H : float
        Fractional correction ΔH/H = β λ_H/(3d).
    """
    if H0 is None:
        H0 = _H0
    lH = _c_km_s / H0
    DH_over_H = beta * lH / (3.0 * d_Mpc)
    H_tilt = H0 * (1.0 + DH_over_H)
    return H_tilt, DH_over_H


# ═══════════════════════════════════════════════════════════════
#  TILTED DECELERATION
# ═══════════════════════════════════════════════════════════════

def Delta_q(beta, d_Mpc, H0=None):
    """Apparent deceleration correction Δq = (β/9)(λ_H/d)³.

    From TF-T03 Eq. Dq-defect.  Uses the self-consistent
    closure |ϑ̃|/H = β λ_H/d.

    Parameters
    ----------
    beta : float
        Tilt rapidity.
    d_Mpc : float
        Comoving survey depth in Mpc.
    H0 : float, optional
        Hubble constant.

    Returns
    -------
    float
        Δq (dimensionless).
    """
    if H0 is None:
        H0 = _H0
    lH = _c_km_s / H0
    return (beta / 9.0) * (lH / d_Mpc)**3


def Delta_q_three_term(beta, d_Mpc, age_slope, Delta_age_Gyr,
                       q_true, H0=None):
    """Three-term deceleration decomposition.

    q_obs = q_true + Δq_tilt(β, d) + Δq_age(s, Δage)

    From TF-T03 Eq. q-decomposition.

    Parameters
    ----------
    beta : float
        Tilt rapidity.
    d_Mpc : float
        Survey depth in Mpc.
    age_slope : float
        Son+2025 age-luminosity slope s [mag/Gyr].
    Delta_age_Gyr : float
        Mean progenitor age difference Δ<t> at the survey redshift [Gyr].
    q_true : float
        True (background) deceleration parameter.
    H0 : float, optional
        Hubble constant.

    Returns
    -------
    q_obs : float
        Observed (apparent) deceleration parameter.
    Dq_tilt : float
        Tilt contribution Δq^(tilt).
    Dq_age : float
        Age-bias contribution Δq^(age).
    """
    Dq_tilt = Delta_q(beta, d_Mpc, H0)
    # Δμ → Δq conversion: Δq ≈ (2 ln10 / 5z_eff) × Δμ
    # where z_eff ≈ 0.42 (upper range of Son+2025 sample).
    # The factor 2.17 = 2 ln10/(5 × 0.424) is an approximate
    # z-averaged conversion; for precision work, use the explicit
    # z-dependent formula Δq = (2 ln10 / 5z) × s × Δ<t>.
    _DQ_AGE_FACTOR = 2.0 * np.log(10) / (5.0 * 0.424)  # ≈ 2.17
    Dq_age = -_DQ_AGE_FACTOR * age_slope * Delta_age_Gyr
    q_obs = q_true + Dq_tilt + Dq_age
    return q_obs, Dq_tilt, Dq_age


# ═══════════════════════════════════════════════════════════════
#  PECULIAR JEANS LENGTH
# ═══════════════════════════════════════════════════════════════

def peculiar_jeans(beta, q, H0=None):
    """Peculiar Jeans length λ_J^pec = λ_H × (β/(9q))^{1/3}.

    From TF-T02 Eq. lambda-J-defect.  The peculiar Jeans length
    separates the regime where tilt-induced peculiar velocities grow
    under gravitational instability (d < λ_J) from the regime where
    Hubble drag suppresses growth (d > λ_J).

    Parameters
    ----------
    beta : float
        Tilt rapidity.
    q : float
        Background deceleration parameter.  When q ≤ 0 (accelerating
        expansion), gravitational instability is suppressed at all
        scales and λ_J → ∞.  For the matter-gravitational contribution
        independent of Λ, pass q = ½Ω_m ≈ 0.158 via q_matter().
    H0 : float, optional
        Hubble constant [km/s/Mpc].  Default: SSOT value.

    Returns
    -------
    lambda_J_Mpc : float
        Peculiar Jeans length in Mpc.  Returns inf when q ≤ 0.
    lambda_J_over_lH : float
        Dimensionless ratio λ_J/λ_H.  Returns inf when q ≤ 0.
    """
    if H0 is None:
        H0 = _H0
    lH = _c_km_s / H0

    if q <= 0:
        # In an accelerating universe, dark energy overcomes matter
        # self-gravity at all scales.  The gravitational Jeans
        # instability that defines λ_J^pec does not operate, so
        # the Jeans scale is formally infinite.
        return float('inf'), float('inf')

    ratio = (beta / (9.0 * q))**(1.0 / 3.0)
    return ratio * lH, ratio


def q_matter(Om=None):
    """Matter-only deceleration: q_m = ½Ω_m.

    This is the gravitational deceleration due to matter alone,
    ignoring the accelerating effect of Λ.  Use this as the q
    argument to peculiar_jeans() when computing the matter-gravitational
    Jeans scale in a Λ-dominated universe.

    Returns
    -------
    float
        ½Ω_m.  Always positive.
    """
    if Om is None:
        Om = C.Omega_m
    return 0.5 * Om


# ═══════════════════════════════════════════════════════════════
#  VELOCITY GROWTH
# ═══════════════════════════════════════════════════════════════

# Growth indices from TF-R03
_GROWTH_MODELS = {
    'Newtonian': 0.69,   # n = 3p/2, p = 0.4574 from p² + p − 2/3 = 0; exact n = 0.686
    'GR_min':    1.5,    # p² − (1/3)p − 2/3 = 0 → p = 1
    'GR_full':   2.0,    # long-wavelength
    'constant':  0.0,    # β(z) = β₀ (frozen)
}

def velocity_growth(z, beta0, model='GR_min'):
    """Tilt rapidity at redshift z: β(z) = β₀ × (1+z)^{−n}.

    Parameters
    ----------
    z : float or array
        Redshift.
    beta0 : float
        Present-epoch tilt rapidity (z = 0).
    model : str
        Growth model: 'Newtonian', 'GR_min', 'GR_full', 'constant'.

    Returns
    -------
    float or array
        β(z).
    """
    if model not in _GROWTH_MODELS:
        raise ValueError(f"Unknown model '{model}'; choose from {list(_GROWTH_MODELS)}")
    n = _GROWTH_MODELS[model]
    return beta0 * (1.0 + z)**(-n)


# ═══════════════════════════════════════════════════════════════
#  MATTER-FRAME KINEMATIC QUANTITIES
# ═══════════════════════════════════════════════════════════════

def matter_vorticity(beta, Sig2):
    """Upper bound on matter-frame vorticity Ŵ² ≤ Σ² sinh⁴β/cosh²β.

    From TF-T01 Eq. What-defect.  Saturates for isotropic shear
    with tilt at 45° to all eigenvectors.

    Parameters
    ----------
    beta : float or array
        Tilt rapidity.
    Sig2 : float or array
        Standardised shear Σ²_std.

    Returns
    -------
    float or array
        Upper bound on Ŵ²_std.
    """
    return Sig2 * np.sinh(beta)**4 / np.cosh(beta)**2


def matter_acceleration(beta, eta=None):
    """Matter-frame acceleration Â²_std = η² sinh²β / 6.

    From TF-T01 Eq. A2-hat-defect.  For single barotropic fluid.

    Parameters
    ----------
    beta : float or array
        Tilt rapidity.
    eta : float, optional
        Acceleration efficiency η_{u̇}.  Default: 1/12.

    Returns
    -------
    float or array
        Â²_std.
    """
    if eta is None:
        eta = _eta_udot
    return eta**2 * np.sinh(beta)**2 / 6.0


# ═══════════════════════════════════════════════════════════════
#  TILT DEFECT AND TILTED DENSITY PARAMETERS
# ═══════════════════════════════════════════════════════════════

def Omega_tilt(beta, w=0.0, Omega_species=None):
    """Tilt defect: Ω_tilt = (1+w) Ω_species sinh²β.

    From TF-T04 Eq. Otilt-multi (single component).

    Parameters
    ----------
    beta : float
        Tilt rapidity.
    w : float
        Equation of state parameter.  Default: 0 (dust).
    Omega_species : float, optional
        Density parameter.  Default: SSOT Ω_m.

    Returns
    -------
    float
        Ω_tilt.
    """
    if Omega_species is None:
        Omega_species = C.Omega_m
    return (1.0 + w) * Omega_species * np.sinh(beta)**2


def tilted_densities(beta, Omega_m=None, Omega_Lambda=None,
                     Omega_k=None, w=0.0):
    """Tilted density parameters: Ω̂_m, Ω̂_Λ, Ω̂_k.

    From TF-T01 Eqs. Om-hat, OL-hat, Ok-hat.

    Returns
    -------
    dict with keys 'Om_hat', 'OL_hat', 'Ok_hat', 'Otilt'.
    """
    Om = Omega_m if Omega_m is not None else C.Omega_m
    OL = Omega_Lambda if Omega_Lambda is not None else C.Omega_Lambda
    Ok = Omega_k if Omega_k is not None else 0.0007
    Ot = Omega_tilt(beta, w, Om)
    sech2 = 1.0 / np.cosh(beta)**2
    return {
        'Om_hat': Om + Ot,
        'OL_hat': OL * sech2,
        'Ok_hat': Ok * sech2,
        'Otilt':  Ot,
    }


# ═══════════════════════════════════════════════════════════════
#  COLIN → β TRANSLATION
# ═══════════════════════════════════════════════════════════════

def beta_from_colin(z_ref, q_d=-8.03, S=0.0262):
    """Translate Colin et al. (2019) dipolar q to β.

    β_SNe = 9 |q_d| z³ exp(−z/S)

    From TF-T03 Eq. beta-from-colin.

    Parameters
    ----------
    z_ref : float or array
        Reference redshift.
    q_d : float
        Colin dipole amplitude (default: −8.03).
    S : float
        Colin decay scale (default: 0.0262).

    Returns
    -------
    float or array
        β_SNe.
    """
    z = np.asarray(z_ref, dtype=float)
    return 9.0 * abs(q_d) * z**3 * np.exp(-z / S)
