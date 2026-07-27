#!/usr/bin/env python3
"""
ssot.py — Single Source of Truth for the Bianchi defect framework.
=================================================================
VA-02 conventions enforced throughout. Loads obs_defaults.json.

Definitions (VA-04 verified):
  Σ²_std = σ_{ab}σ^{ab} / (6H²)  where H = Θ/3
  W²_std = ω_{ab}ω^{ab} / (6H²)
  A²_std = u̇_a u̇^a / (6H²)

Conversions:
  σ/Θ = √(2Σ²/3)        [shear scalar / expansion scalar]
  ω̄ = √(2W²/3)          [code vorticity variable]
  (ω/H) = √(3W²)        [Saadeh convention]
"""
import json, numpy as np
from importlib import resources
from pathlib import Path

__all__ = ['load_obs', 'C', 'eps_ell', 'D_ell_from_eps',
           'eps_ell_legacy_dl_as_cl', 'D_ell_from_eps_legacy',
           'sigma_H_from_Sig2', 'ombar_from_W2', 'omH_from_W2',
           'omega_tilt']

# ─── Load defaults ───────────────────────────────────────────
def _find_obs_defaults():
    """Find obs_defaults.json, including the installed package resource."""
    import os
    env = os.environ.get('HTT_OBS_DEFAULTS')
    if env:
        override = Path(env)
        if override.is_file():
            return override

    legacy = Path(__file__).resolve().parent / 'obs_defaults.json'
    if legacy.is_file():
        return legacy

    try:
        packaged = resources.files('workspace').joinpath('data').joinpath('obs_defaults.json')
    except (ModuleNotFoundError, TypeError):
        packaged = None
    if packaged is not None and packaged.is_file():
        return packaged

    workspace = (
        Path(__file__).resolve().parent.parent.parent.parent
        / 'workspace' / 'data' / 'obs_defaults.json'
    )
    if workspace.is_file():
        return workspace
    return legacy  # fail at load time with the historically expected path

_DEFAULT_PATH = _find_obs_defaults()

def load_obs(path=None):
    """Load the observational defaults JSON and return as dict."""
    p = Path(path) if path else _DEFAULT_PATH
    return json.loads(p.read_text(encoding='utf-8'))

# ─── Constants (loaded once at import) ───────────────────────
_OBS = load_obs() if _DEFAULT_PATH.is_file() else {}

class C:
    """Namespace for physical constants (VA-02 standard)."""
    T0_K  = 2.72548
    T0_uK = T0_K * 1e6

    # Planck 2018
    Omega_m     = 0.3153
    Omega_r     = 9.15e-5       # Planck 2018 (photons + 3 massless ν)
    Omega_Lambda = 0.6847
    h           = 0.6736

    # CMB multipole amplitudes (ε_ℓ = √((2ℓ+1)C_ℓ/(4π))/T₀)
    eps1_kin = 1.2336e-3
    # eps2/eps3 are the dimensionless amplitudes obtained from the registered
    # D2/D3 values with C_l = 2π D_l/[l(l+1)].  They are rounded historical
    # constants; value-anchored tests guard the conversion independently.
    eps2     = 3.559629e-6
    eps3     = 6.065291e-6

    # Frame correction (VT-07): η_{u̇} = w/[3(1+w)] = 1/12 for radiation
    eta_udot = 1.0 / 12.0  # exact; previously 0.083 (0.4% truncation)

    # Quadrupole / octupole power spectrum
    D2_obs  = 225.9    # μK²
    D3_obs  = 936.9
    D2_LCDM = 1150.0
    D3_LCDM = 1000.0

    # Transfer functions
    T2_decay = 2.75e4
    T2_grow  = 5.5

    # Model parameters
    R_WS_VIIh = 1.06
    # K_MES: steepness parameter for the logistic soft prior in
    # evidence channel (g).  This is NOT 12π/5 from MES algebra;
    # it controls the sigmoid rolloff width.  Channel (g) is INERT
    # by default (redundant with the hard ceiling in channel f).
    K_MES      = 10.0

# ─── Conversion functions ────────────────────────────────────

def eps_ell(D_ell, ell):
    """Convert power ``D_l`` to the dimensionless multipole amplitude.

    ``D_l = l(l+1) C_l/(2π)`` is converted to ``C_l`` before applying
    ``eps_l = sqrt((2l+1) C_l/(4π))/T0``.
    """
    if isinstance(ell, (bool, np.bool_)) or not isinstance(ell, (int, np.integer)):
        raise TypeError("ell must be an integer")
    if ell < 1:
        raise ValueError("ell must be >= 1")
    values = np.asarray(D_ell, dtype=float)
    if np.any(~np.isfinite(values)) or np.any(values < 0.0):
        raise ValueError("D_ell must be finite and non-negative")
    return np.sqrt((2*ell + 1) * values / (2 * ell * (ell + 1))) / C.T0_uK

def D_ell_from_eps(eps, ell):
    """Inverse of :func:`eps_ell` for ``D_l``."""
    if isinstance(ell, (bool, np.bool_)) or not isinstance(ell, (int, np.integer)):
        raise TypeError("ell must be an integer")
    if ell < 1:
        raise ValueError("ell must be >= 1")
    values = np.asarray(eps, dtype=float)
    if np.any(~np.isfinite(values)) or np.any(values < 0.0):
        raise ValueError("eps must be finite and non-negative")
    return (
        2 * ell * (ell + 1) * values**2 * C.T0_uK**2 / (2*ell + 1)
    )


def eps_ell_legacy_dl_as_cl(D_ell, ell):
    """Historical incorrect conversion, for explicit reproduction only."""
    return np.sqrt((2*ell + 1) * D_ell / (4 * np.pi)) / C.T0_uK


def D_ell_from_eps_legacy(eps, ell):
    """Inverse of :func:`eps_ell_legacy_dl_as_cl`."""
    return 4 * np.pi * eps**2 * C.T0_uK**2 / (2*ell + 1)

def sigma_H_from_Sig2(Sig2):
    """σ/Θ = √(2Σ²_std/3).  Used in D₂^shear formula."""
    return np.sqrt(2.0 * Sig2 / 3.0)

def ombar_from_W2(W2):
    """ω̄ = √(ω_{ab}ω^{ab})/Θ = √(2W²_std/3).  Code convention."""
    return np.sqrt(2.0 * W2 / 3.0)

def omH_from_W2(W2):
    """(ω/H) = √(3W²_std).  Saadeh convention."""
    return np.sqrt(3.0 * W2)

def Sig2_from_sigmaH(sigma_H):
    """Inverse: Σ²_std from σ/Θ."""
    return 1.5 * sigma_H**2

def W2_from_ombar(ombar):
    """Inverse: W²_std from ω̄."""
    return 1.5 * ombar**2

# ─── Scenario loader ─────────────────────────────────────────

def get_scenario(name='S3'):
    """Return (eps1, beta) for a named scenario."""
    obs = load_obs()
    sc = obs['scenarios'][name]
    return sc['eps1'], sc['beta']


# ─── Shared Ω_tilt computation (P3: frame-aware SSOT) ────────

def omega_tilt(Om, Or, beta, frame='matter'):
    """Tilt energy density Ω_tilt with explicit frame convention.

    The tilt energy contributes to the defect identity:
      x = Σ² − W² + Ω_tilt + Ω_{k,aniso}

    Two frame conventions exist for the density parameters:

    frame='matter' (default):
      Om, Or are matter-frame (Planck-fitted) density parameters.
      Ω_tilt = [(1+w_r)Ω_r + (1+w_m)Ω_m] × sinh²β
             = [(4/3)Ω_r + Ω_m] × sinh²β

    frame='geometry':
      Om, Or are geometry-frame density parameters (ODE state variables).
      The geometry-frame Ω already absorbs part of the tilt boost, so
      Ω_tilt must be extracted by un-boosting:
      Ω_tilt_r = Ω_r^geom × (1+w_r)sinh²β / (1 + (1+w_r)sinh²β)
      Ω_tilt_m = Ω_m^geom × (1+w_m)sinh²β / (1 + (1+w_m)sinh²β)

    Their historical observational comparison is unavailable to active code.
    They diverge for sufficiently large synthetic tilt parameters.

    Parameters
    ----------
    Om : float or array
        Matter density parameter.
    Or : float or array
        Radiation density parameter.
    beta : float or array
        Tilt rapidity.
    frame : str
        'matter' or 'geometry'.

    Returns
    -------
    float or array
        Tilt energy density Ω_tilt.
    """
    s2 = np.sinh(np.asarray(beta, dtype=float))**2
    w_r = 1.0 / 3.0
    w_m = 0.0

    if frame == 'matter':
        return (1 + w_r) * np.asarray(Or) * s2 + (1 + w_m) * np.asarray(Om) * s2
    elif frame == 'geometry':
        ot_r = np.asarray(Or) * (1 + w_r) * s2 / (1 + (1 + w_r) * s2)
        ot_m = np.asarray(Om) * (1 + w_m) * s2 / (1 + (1 + w_m) * s2)
        return ot_r + ot_m
    else:
        raise ValueError(f"frame must be 'matter' or 'geometry', got '{frame}'")
