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
from pathlib import Path

__all__ = ['load_obs', 'C', 'eps_ell', 'D_ell_from_eps',
           'sigma_H_from_Sig2', 'ombar_from_W2', 'omH_from_W2']

# ─── Load defaults ───────────────────────────────────────────
_DEFAULT_PATH = Path(__file__).parent / 'obs_defaults.json'

def load_obs(path=None):
    """Load the observational defaults JSON and return as dict."""
    p = Path(path) if path else _DEFAULT_PATH
    with open(p) as f:
        return json.load(f)

# ─── Constants (loaded once at import) ───────────────────────
_OBS = load_obs() if _DEFAULT_PATH.exists() else {}

class C:
    """Namespace for physical constants (VA-02 standard)."""
    T0_K  = 2.72548
    T0_uK = 2.7255e6

    # Planck 2018
    Omega_m     = 0.3153
    Omega_Lambda = 0.6847
    h           = 0.6736

    # CMB multipole amplitudes (ε_ℓ = √((2ℓ+1)C_ℓ/(4π))/T₀)
    eps1_kin = 1.2336e-3
    # eps2/eps3: Planck PR3 Commander component-separation pipeline
    # (distinct from D₂/D₃ which are from the TT full-mission spectrum).
    # The Commander values are used in B_σ; the D_ℓ values enter the
    # χ² likelihood channels (e, h) directly.  Impact of the difference
    # on B_σ: < 0.04% (dipole contributes 99.4%).
    eps2     = 3.559629e-6    # Commander ℓ=2
    eps3     = 6.065291e-6    # Commander ℓ=3

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
    """ε_ℓ from D_ℓ: ε_ℓ = √((2ℓ+1)D_ℓ/(4π)) / T₀  (dimensionless ΔT/T)."""
    return np.sqrt((2*ell + 1) * D_ell / (4 * np.pi)) / C.T0_uK

def D_ell_from_eps(eps, ell):
    """D_ℓ from ε_ℓ: D_ℓ = 4π ε_ℓ² T₀² / (2ℓ+1)."""
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
