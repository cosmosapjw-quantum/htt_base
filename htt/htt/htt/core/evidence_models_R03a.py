#!/usr/bin/env python3
"""
evidence_models_R03a.py — 8-channel Bianchi evidence framework
================================================================
VE-R03a: Extensions over R03:
  Channel (g): MES exponential-tail penalty — a historical smooth comparator
  Channel (h): D₃ octupole χ²(7) — includes shear contribution via f₃(x)
  New: f₃(x) interpolation from AniCLASS dataset for VII_h octupole power fraction

Channels:
  (a) F&Q intrinsic dipole upper limit        [half-Gaussian on ε₁]
  (b) CatWISE + Radio dipole 2×2 covariance   [bivariate Gaussian on ε₁]
  (c) quarantined observational input              [blocked while findings are OPEN]
  (d) Saadeh vorticity upper limit             [half-Gaussian on ω/H]
  (e) D₂ quadrupole χ²(5)                     [scaled χ² with D₂^shear(Σ², f₂(x))]
  (f) typed geodesic MES hard ceiling          [hard support: reject if Σ² > Σ²_max]
  (g) MES exponential-tail penalty             [INERT by default; redundant with (f)]
  (h) D₃ octupole χ²(7)             *** NEW *** [scaled χ² with D₃^shear(Σ², f₃(x))]

There is no implicit active default while PR-120 is in force: the historical
default included channel (c). Independent method checks must explicitly pass
``channels=ACTIVE_DEFAULT_CHANNELS`` (``abdefh``). Channel (g) remains excluded
because (f) makes it redundant for nested sampling. Any implicit or explicit
request for channel (c) fails closed.

Data values (Planck PR3 Commander):
  D₂^obs  = 225.9 μK²   (COM_PowerSpect_CMB-TT-full_R3.01.txt, ℓ=2)
  D₃^obs  = 936.9 μK²   (same file, ℓ=3)
  D₂^ΛCDM = 1150.0 μK²  (Planck 2018 best-fit, VR-15 calibration)
  D₃^ΛCDM = 1000.0 μK²  (approximate, Sachs-Wolfe plateau)
"""
import hashlib
import json
import platform
import warnings
from typing import Any, Mapping

import numpy as np
from scipy.interpolate import interp1d
from scipy.special import erfinv, gammaln

from htt.core.cf4_observational_input import (
    ACTIVE_DEFAULT_CHANNELS,
    normalize_active_channels,
    require_cf4_observational_input,
)

# PR-124: active MES consumers traverse the typed successor registry
# (common.mes_theorem_authority is the live authority; legacy values are
# labeled non-authoritative reproduction, see legacy_reproduction_coefficients).
from common.mes_successor_registry import current_mes_successor_registry
from common.statistical_foundations import (
    AnchorConditioning,
    AnchorStatus,
    registered_geodesic_mes_anchors,
)

_MES_SUCCESSOR = current_mes_successor_registry().successor
_MES_SUCCESSOR_ID = _MES_SUCCESSOR.successor_id

# =====================================================================
#  SSOT: Physical and Observational Constants
# =====================================================================
T0        = 2.72548       # K, CMB monopole temperature
T0_UK     = T0 * 1e6      # μK
EPS2      = 3.559629e-6   # ε₂ quadrupole (ΔT/T)
EPS3      = 6.065291e-6   # ε₃ octupole (ΔT/T)
ETA_UDOT  = 1.0 / 12.0    # w/(3(1+w)) for w=1/3; exact (was 0.083)
OMEGA_M   = 0.3153        # Planck 2018 FLRW fit
# NOTE: In a Bianchi cosmology, the effective matter density at redshift z
# differs from this FLRW-fitted value by O(Σ²) due to the modified
# Friedmann constraint: Ω_m^eff = Ω_m × E²_FLRW / E²_Bianchi.
# At Σ² ~ 10⁻⁶ this shifts Ω_m by < 10⁻⁶, well within the prior width
# (σ_Ω ~ 0.006). The self-consistent correction is:
#   OMEGA_M_EFF = OMEGA_M / (1 - Sigma2 + W2)
# which is used in the background solver but not in the evidence models
# where the O(Σ²) shift is negligible compared to the prior.
OMEGA_L   = 0.6847
OK_PLANCK = 0.0007        # Planck 2018 Ω_K mean
OK_SIGMA  = 0.0019        # Planck 2018 Ω_K 1σ
R_WS_VIIH = 1.06          # W/Σ ratio for VII_h (Wainwright & Ellis)

# Data (Planck PR3 Commander)
D2_OBS    = 225.9          # μK²
D3_OBS    = 936.9          # μK²
D2_LCDM   = 1150.0         # μK² (Planck 2018 best-fit)
D3_LCDM   = 1000.0         # μK²

# Transfer function totals (Saadeh calibration)
T2_TOTAL_DECAY = 2.75e4    # (ΔT/T) per unit (σ/H), ℓ=all, decay mode
T2_TOTAL_GROW  = 5.5       # same, growing tensor mode

# MES exponential-tail penalty steepness
K_MES_STEEP = 10.0


# =====================================================================
#  f₂(x) and f₃(x) Interpolation — AniCLASS calibrated (VR-16c)
# =====================================================================
# x = √h / √Ω_K  (Collins-Hawking spiral parameter)
# f₂ = quadrupole (ℓ=2) power fraction
# f₃ = octupole  (ℓ=3) power fraction

# ── f₂: Vector mode (iso IC) — VR-17 Planck 2018, Ω_K=0.001 ──
_X_F2_VEC = [0.001, 0.01, 0.015, 0.02, 0.03, 0.05, 0.07, 0.1, 0.13, 0.16,
             0.2, 0.25, 0.3, 0.35, 0.4, 0.5, 0.62, 0.75, 0.9, 1.0,
             1.2, 1.5, 2.0, 3.0, 5.0, 7.0, 10.0, 20.0, 50.0, 100.0, 1e3]
_F2_VEC   = [0.0, 0.001, 0.001, 0.0004, 0.0, 0.0002, 0.0005, 0.004, 0.013, 0.043,
             0.291, 0.543, 0.688, 0.774, 0.829, 0.891, 0.929, 0.951, 0.966, 0.972,
             0.980, 0.986, 0.991, 0.995, 0.997, 0.997, 0.997, 0.998, 0.998, 0.998, 0.998]

# ── f₂: Tensor mode (regular/growing) — VR-17 Planck 2018, Ω_K=0.001 ──
_X_F2_TEN = [0.001, 0.01, 0.015, 0.02, 0.03, 0.05, 0.07, 0.1, 0.13, 0.16,
             0.2, 0.25, 0.3, 0.35, 0.4, 0.5, 0.62, 0.75, 0.9, 1.0,
             1.2, 1.5, 2.0, 3.0, 5.0, 7.0, 10.0, 20.0, 50.0, 100.0, 1e3]
_F2_TEN   = [0.0, 0.008, 0.0003, 0.001, 0.0001, 0.0, 0.0, 0.005, 0.003, 0.154,
             0.449, 0.669, 0.782, 0.845, 0.884, 0.928, 0.954, 0.969, 0.978, 0.982,
             0.988, 0.992, 0.995, 0.997, 0.999, 0.999, 0.999, 0.999, 0.999, 0.999, 0.999]

# ── f₃: Vector mode (iso IC) — VR-17 Planck 2018, Ω_K=0.001 ──
#    Peaks at x ~ 0.2 (f₃ ≈ 0.39) then decays; power migrates from ℓ=2 to ℓ=3
_X_F3_VEC = [0.001, 0.01, 0.015, 0.02, 0.03, 0.05, 0.07, 0.1, 0.13, 0.16,
             0.2, 0.25, 0.3, 0.35, 0.4, 0.5, 0.62, 0.75, 0.9, 1.0,
             1.2, 1.5, 2.0, 3.0, 5.0, 7.0, 10.0, 20.0, 50.0, 100.0, 1e3]
_F3_VEC   = [0.0, 0.002, 0.001, 0.003, 0.003, 0.002, 0.005, 0.034, 0.022, 0.261,
             0.392, 0.333, 0.255, 0.196, 0.154, 0.102, 0.068, 0.047, 0.034, 0.028,
             0.020, 0.014, 0.009, 0.005, 0.003, 0.003, 0.003, 0.002, 0.002, 0.002, 0.002]

# ── f₃: Tensor mode (regular) — VR-17 Planck 2018, Ω_K=0.001 ──
#    Peaks at x ~ 0.16–0.20 (f₃ ≈ 0.35) then decays
_X_F3_TEN = [0.001, 0.01, 0.015, 0.02, 0.03, 0.05, 0.07, 0.1, 0.13, 0.16,
             0.2, 0.25, 0.3, 0.35, 0.4, 0.5, 0.62, 0.75, 0.9, 1.0,
             1.2, 1.5, 2.0, 3.0, 5.0, 7.0, 10.0, 20.0, 50.0, 100.0, 1e3]
_F3_TEN   = [0.0, 0.0, 0.0004, 0.0001, 0.0002, 0.0001, 0.001, 0.004, 0.124, 0.341,
             0.352, 0.258, 0.186, 0.138, 0.106, 0.068, 0.045, 0.031, 0.022, 0.018,
             0.012, 0.008, 0.005, 0.003, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001]

# Build interpolators (linear in log₁₀(x))
_f2_vec_interp = interp1d(np.log10(_X_F2_VEC), _F2_VEC, kind='linear',
                           bounds_error=False, fill_value=(0.0, _F2_VEC[-1]))
_f2_ten_interp = interp1d(np.log10(_X_F2_TEN), _F2_TEN, kind='linear',
                           bounds_error=False, fill_value=(0.0, _F2_TEN[-1]))
_f3_vec_interp = interp1d(np.log10(_X_F3_VEC), _F3_VEC, kind='linear',
                           bounds_error=False, fill_value=(0.0, _F3_VEC[-1]))
_f3_ten_interp = interp1d(np.log10(_X_F3_TEN), _F3_TEN, kind='linear',
                           bounds_error=False, fill_value=(0.0, _F3_TEN[-1]))


def _warn_clip(name, raw, x):
    """Emit a warning if interpolation needed clipping."""
    if raw < 0 or raw > 1:
        warnings.warn(
            f"{name}(x={x:.4e}): raw interpolation={raw:.6f} clipped to [0,1]. "
            f"This x is outside the AniCLASS calibration range.",
            stacklevel=3)

def f2_vector(x):
    """ℓ=2 power fraction for vector (decay) mode."""
    if x is None or x <= 0: return 1.0
    raw = float(_f2_vec_interp(np.log10(x)))
    _warn_clip('f2_vector', raw, x)
    return float(np.clip(raw, 0.0, 1.0))

def f2_tensor(x):
    """ℓ=2 power fraction for tensor (regular/growing) mode."""
    if x is None or x <= 0: return 1.0
    raw = float(_f2_ten_interp(np.log10(x)))
    _warn_clip('f2_tensor', raw, x)
    return float(np.clip(raw, 0.0, 1.0))

def f3_vector(x):
    """ℓ=3 power fraction for vector (decay) mode."""
    if x is None or x <= 0: return 0.0
    raw = float(_f3_vec_interp(np.log10(x)))
    _warn_clip('f3_vector', raw, x)
    return float(np.clip(raw, 0.0, 1.0))

def f3_tensor(x):
    """ℓ=3 power fraction for tensor (regular/growing) mode."""
    if x is None or x <= 0: return 0.0
    raw = float(_f3_ten_interp(np.log10(x)))
    _warn_clip('f3_tensor', raw, x)
    return float(np.clip(raw, 0.0, 1.0))


# =====================================================================
#  Physics: MES bounds, shear-to-Dℓ, tilt
# =====================================================================
def B_sigma(e1, e2=EPS2, e3=EPS3):
    return (5./3)*e1 + 3.*e2 + (3./7)*e3

def B_sigma_corrected(e1, e2=EPS2, e3=EPS3):
    R = 1. + 2.69 * e1
    return R * B_sigma(e1, e2, e3)

def eps1_from_beta(beta):
    return beta * (1. + ETA_UDOT)

def boost_to_eps2(beta):
    return 0.5 * beta**2

def _sigma_H(Sigma2):
    """σ̄/Θ where σ̄ = √(σ_{ab}σ^{ab}) and Θ = 3H.

    From Σ² = σ_{ab}σ^{ab}/(6H²):
      σ_{ab}σ^{ab} = 6H² Σ² = (2/3)Θ² Σ²
      σ̄²/Θ² = (2/3)Σ²
      σ̄/Θ = √(2Σ²/3)

    NOTE: This is NOT σ/H. It is σ̄/Θ where σ̄ includes the full
    contraction (not the half-contraction σ² = ½σ_{ab}σ^{ab}).
    The MES bound chain uses this convention consistently.
    """
    return np.sqrt(2. * Sigma2 / 3.)

def shear_to_D2(Sigma2, mode='decay', x_h=None):
    """Σ² → D₂^shear [μK²] with AniCLASS-calibrated T₂(ℓ=2, x)."""
    sH = _sigma_H(Sigma2)
    if mode == 'grow':
        T2 = np.sqrt(f2_tensor(x_h)) * T2_TOTAL_GROW
    else:
        T2 = np.sqrt(f2_vector(x_h)) * T2_TOTAL_DECAY
    eps2_shear = T2 * sH
    return (6./(2.*np.pi)) * (eps2_shear * T0_UK)**2

def shear_to_D3(Sigma2, mode='decay', x_h=None):
    """Σ² → D₃^shear [μK²] with AniCLASS-calibrated T₃(ℓ=3, x).

    T₃(ℓ=3) = √f₃ × T_total, analogous to T₂ but for octupole.
    For Types I/V/IX: f₃ = 0 → D₃^shear = 0.
    For VII_h: f₃ peaks at x ~ 0.3-0.5 (spiral pumps octupole).
    """
    sH = _sigma_H(Sigma2)
    if mode == 'grow':
        T3 = np.sqrt(f3_tensor(x_h)) * T2_TOTAL_GROW
    else:
        T3 = np.sqrt(f3_vector(x_h)) * T2_TOTAL_DECAY
    eps3_shear = T3 * sH
    # D₃ = ℓ(ℓ+1)/(2π) × (ε₃ × T₀)² = 12/(2π) × (...)²
    return (12./(2.*np.pi)) * (eps3_shear * T0_UK)**2


# ── BASS-calibrated D₂ (A3) ──────────────────────────────────
#
# The AniCLASS transfer function (shear_to_D2 above) is calibrated
# for the Saadeh linear regime at σ/H ~ 10⁻¹¹ (Σ² ~ 10⁻²²).
# At larger Σ², the linear extrapolation vastly overestimates D₂
# because it does not account for multipole redistribution and
# nonlinear damping in the full Boltzmann cascade.
#
# BASS computes D₂ from first principles: a reduced ℓ≤3 Boltzmann
# hierarchy with the (8/15)Σ_std shear source, Thomson damping,
# and free-streaming.  The resulting D₂(Σ²) follows a power law:
#
#   D₂^BASS = A × Σ²^α    [μK²]
#
# with A = 9.872e6, α = 0.955 (fit over 10⁻⁹ < Σ² < 10⁻⁴).
#
# VALIDITY RANGES:
#   AniCLASS shear_to_D2:  Σ² < 10⁻²⁰ (Saadeh linear regime)
#   BASS bass_shear_to_D2: 10⁻¹¹ < Σ² < 10⁻³ (reduced solver)
#   Overlap: none.  The two calibrations are complementary.
#
# The evidence_models likelihood uses AniCLASS shear_to_D2, which
# is CORRECT as a penalty function: larger Σ² → larger D₂_predicted
# → worse χ² fit → Σ² bounded from above.  The absolute D₂ value
# at the bound does not matter for the evidence computation because
# the bound is set by the quadrupole observation (D₂_obs ≈ 1150 μK²),
# not by the predicted D₂.

_BASS_D2_AMPLITUDE = 9.872e6   # μK², from BASS v8.2 power-law fit
_BASS_D2_SLOPE = 0.955         # D₂ ∝ Σ²^α
_BASS_D2_VALID_RANGE = (1e-11, 1e-3)  # Σ² validity


def bass_shear_to_D2(Sigma2):
    """BASS-calibrated D₂(Σ²) [μK²] from reduced Boltzmann solver.

    Uses the power-law fit D₂ = 9.872e6 × Σ²^0.955 computed from
    30-point BASS integration over 10⁻¹¹ < Σ² < 10⁻³.

    This function is for CROSS-VALIDATION and SCALING VERIFICATION,
    not for the evidence likelihood (which uses shear_to_D2 above).

    Parameters
    ----------
    Sigma2 : float or array
        Standardised shear Σ² = σ_{ab}σ^{ab}/(6H²).

    Returns
    -------
    float or array
        D₂ in μK².
    """
    S2 = np.asarray(Sigma2, dtype=float)
    return _BASS_D2_AMPLITUDE * S2**_BASS_D2_SLOPE


def bass_vs_aniclass_comparison(Sigma2):
    """Compare BASS and AniCLASS D₂ predictions at given Σ².

    Returns a dict with both predictions and their ratio.
    Useful for documenting the expected amplitude offset.
    """
    D2_bass = float(bass_shear_to_D2(Sigma2))
    D2_ani = float(shear_to_D2(Sigma2))
    return {
        'Sigma2': float(Sigma2),
        'D2_bass_uK2': D2_bass,
        'D2_aniclass_uK2': D2_ani,
        'ratio_ani_over_bass': D2_ani / D2_bass if D2_bass > 0 else float('inf'),
        'log10_ratio': np.log10(D2_ani / D2_bass) if D2_bass > 0 else float('inf'),
        'bass_valid': _BASS_D2_VALID_RANGE[0] <= Sigma2 <= _BASS_D2_VALID_RANGE[1],
        'note': ('AniCLASS calibrated for σ/H~10⁻¹¹; BASS for 10⁻¹¹<Σ²<10⁻³. '
                 'Amplitude mismatch is expected — scaling match is the validation.'),
    }


def boost_to_D2(beta):
    eps2_b = boost_to_eps2(beta)
    return (6./(2.*np.pi)) * (eps2_b * T0_UK)**2

def Sig2_BV(beta, Ok, w=0.):
    if Ok <= 0: return np.inf
    return ((1.+w)*OMEGA_M)**2 * beta**2 / (4.*Ok)

def omH_from_W2(W2):
    return np.sqrt(2.*W2/3.)


# =====================================================================
#  Prior primitives
# =====================================================================
def _logu(u, lo, hi):
    return lo * (hi/lo)**u

def _gauss(u, mu, sig):
    return mu + sig * np.sqrt(2.) * erfinv(2.*u - 1.)

def _halfgauss(u, sig):
    return sig * np.sqrt(2.) * erfinv(u)

def _unif(u, lo, hi):
    return lo + (hi - lo)*u


# =====================================================================
#  Observational Data Container
# =====================================================================
class ObsData:
    __slots__ = (
        'eps2','eps2_s','eps3','eps3_s',
        'D2_obs','D3_obs',
        'e1_FQ_UL','e1_FQ_s',
        'e1_CW','e1_CW_s','e1_CW_sys',
        'e1_rad','e1_rad_s','e1_rad_sys',
        'omH_UL','omH_s','rho45',
    )
    def __init__(self):
        self.eps2      = EPS2;           self.eps2_s    = 1.5e-6
        self.eps3      = EPS3;           self.eps3_s    = 2.0e-6
        self.D2_obs    = D2_OBS
        self.D3_obs    = D3_OBS
        self.e1_FQ_UL  = 1.358e-3;      self.e1_FQ_s   = 0.693e-3
        self.e1_CW     = 1.476e-3;      self.e1_CW_s   = 0.30e-3; self.e1_CW_sys = 0.0
        self.e1_rad    = 3.296e-3;      self.e1_rad_s  = 0.60e-3; self.e1_rad_sys= 0.0
        # Saadeh et al. (2016): (ω/H)₀ < 5.2e-11 where ω = √(ω_aω^a)
        # Code convention: omH = √(ω_{ab}ω^{ab})/Θ = (√2/3)(ω/H)
        # Conversion factor: √2/3 ≈ 0.4714
        self.omH_UL    = 2.45e-11;       self.omH_s     = 1.25e-11
        self.rho45     = 0.1

    @property
    def b_CF4(self):
        require_cf4_observational_input(consumer="ObsData.b_CF4")

    @b_CF4.setter
    def b_CF4(self, value):
        require_cf4_observational_input(consumer="ObsData.b_CF4 assignment")

    @property
    def b_CF4_s(self):
        require_cf4_observational_input(consumer="ObsData.b_CF4_s")

    @b_CF4_s.setter
    def b_CF4_s(self, value):
        require_cf4_observational_input(consumer="ObsData.b_CF4_s assignment")


# =====================================================================
#  Core Likelihood: 6 active defaults (a, b, d, e, f, h); channel g inert
# =====================================================================
def _chi2_logL(D_obs, D_true, nu):
    """Scaled χ²(ν) log-likelihood."""
    if D_true <= 0: return -np.inf
    x = nu * D_obs / D_true
    return (nu/2. - 1.)*np.log(x) - x/2. - (nu/2.)*np.log(2.) - gammaln(nu/2.) + np.log(nu/D_true)


class BianchiModel:
    """Base class for all Bianchi models.

    Class-level metadata for identifiability audit (CA-07, CA-08):
      _active_params:     parameters that enter predicted_observables
      _inactive_params:   parameters sampled but NOT entering likelihood
      _equivalence_class: tag grouping observationally identical models
      _duplicate_of:      if set, this model is a code duplicate of another
    """
    name        = "base"
    param_names = []
    ndim        = 0
    _shear_mode = 'decay'
    _bianchi_type = 'I'
    _active_params   = []
    _inactive_params = []
    _equivalence_class = None
    _duplicate_of      = None

    # The implicit default is quarantined because it historically included
    # channel (c). Explicit c-free method checks may use ACTIVE_DEFAULT_CHANNELS.
    # Channel (g) is intentionally excluded from the default because it is
    # redundant with channel (f): the hard MES ceiling in (f) rejects any
    # sample with Σ² > Σ²_max BEFORE the exponential-tail penalty in (g) can
    # activate.  Channel (g) code is retained below for use with samplers
    # that do not support hard prior boundaries (e.g. MCMC).  To include
    # it, pass channels='abdefgh' (still excluding quarantined channel c).
    def __init__(self, obs=None, channels=None):
        self.obs = obs or ObsData()
        self.channels = normalize_active_channels(
            channels,
            consumer=f"{type(self).__name__} likelihood",
        )

    def prior_transform(self, u):
        raise NotImplementedError
    def predicted_observables(self, theta):
        raise NotImplementedError

    def log_likelihood(self, theta):
        p = self.predicted_observables(theta)
        return self._core_logL(p) if p is not None else -np.inf

    def _get_x_h(self, p):
        if self._bianchi_type == 'VIIh': return p.get('x_h', 1.0)
        return None

    def _core_logL(self, p):
        o = self.obs; ch = self.channels
        ll = 0.0
        e1   = p.get("eps1", 0.)
        beta = p.get("beta", 0.)
        omH  = p.get("omega_H", 0.)
        Sig2 = p.get("Sigma2", 0.)
        x_h  = p.get("x_h", None)

        # (a) F&Q intrinsic dipole UL
        if 'a' in ch:
            ll -= 0.5 * (e1 / o.e1_FQ_s)**2

        # (b) CatWISE + Radio 2×2
        if 'b' in ch:
            s4 = np.hypot(o.e1_CW_s, o.e1_CW_sys)
            s5 = np.hypot(o.e1_rad_s, o.e1_rad_sys)
            r = o.rho45
            det = s4**2 * s5**2 * (1. - r**2)
            if det <= 0: return -np.inf
            d4 = e1 - o.e1_CW; d5 = e1 - o.e1_rad
            ll -= 0.5*(s5**2*d4**2 - 2*r*s4*s5*d4*d5 + s4**2*d5**2)/det
            ll -= 0.5*np.log(det) + np.log(2.*np.pi)

        # (c) quarantined observational input. The constructor rejects this
        # channel before likelihood evaluation; this branch is a second guard
        # against state mutation or deserialised legacy objects.
        if 'c' in ch:
            require_cf4_observational_input(
                consumer=f"{type(self).__name__}._core_logL",
            )

        # (d) Saadeh vorticity
        if 'd' in ch:
            if omH > o.omH_UL:
                ll -= 0.5*((omH - o.omH_UL)/o.omH_s)**2

        # (e) D₂ quadrupole χ²(5)
        if 'e' in ch:
            D2_shear = p.get("D2_shear", 0.)
            D2_boost = p.get("D2_boost", 0.)
            D2_true = D2_LCDM + D2_shear + D2_boost
            ll += _chi2_logL(o.D2_obs, D2_true, 5.0)

        # (f) MES hard ceiling
        if 'f' in ch:
            if not self._mes_ok(Sig2, e1):
                return -np.inf

        # (g) MES exponential-tail penalty — INERT when (f) is active (see
        #     __init__ docstring). Retained for historical MCMC comparison.
        if 'g' in ch:
            Sig2_max = _active_sig2_mes_ceiling(1.233e-3 + e1)
            if Sig2_max > 0:
                ratio = Sig2 / Sig2_max
                if ratio > 1.0:
                    ll -= K_MES_STEEP * (ratio - 1.0)

        # (h) D₃ octupole χ²(7)  *** NEW ***
        if 'h' in ch:
            D3_shear = p.get("D3_shear", 0.)
            D3_true = D3_LCDM + D3_shear
            ll += _chi2_logL(o.D3_obs, D3_true, 7.0)

        return ll

    @staticmethod
    def _mes_ok(Sig2, eps1_intrinsic=0.):
        if (
            isinstance(Sig2, (bool, np.bool_))
            or not isinstance(Sig2, (int, float, np.integer, np.floating))
            or not np.isfinite(Sig2)
            or Sig2 < 0.0
        ):
            return False
        EPS1_KIN = 1.233e-3
        eps1_total = EPS1_KIN + eps1_intrinsic
        ceil = _active_sig2_mes_ceiling(eps1_total)
        return Sig2 <= ceil


def _active_sig2_mes_ceiling(e1_total):
    """Return the verified uncorrected geodesic shear anchor for this input."""
    anchor = registered_geodesic_mes_anchors(
        eps1=e1_total,
        eps2=EPS2,
        eps3=EPS3,
        attribution=(
            "evidence_models_R03a total observed-plus-model-intrinsic dipole"
        ),
        conditioning=AnchorConditioning.REALIZATION_CONDITIONAL,
    )["sigma"]
    if anchor.status is not AnchorStatus.VERIFIED or not anchor.normalization_allowed:
        raise RuntimeError("active shear likelihood requires a verified MES anchor")
    return float(anchor.value)


# Historical corrected ceiling: retained for explicit reproduction only.
def Sig2_max_MES(e1_total):
    """Legacy frame-corrected ceiling; active channels do not call this."""
    return 1.5 * B_sigma_corrected(e1_total)**2


# =====================================================================
#  FLRW (0D reference)
# =====================================================================
class FLRW(BianchiModel):
    name = "FLRW"; param_names = []; ndim = 0
    def prior_transform(self, u): return np.array([])
    def predicted_observables(self, theta=None):
        return {"eps1":0., "beta":0., "omega_H":0.,
                "Sigma2":0., "D2_shear":0., "D2_boost":0., "D3_shear":0.}
    def log_likelihood(self, theta=None):
        return self._core_logL(self.predicted_observables())
    def log_evidence(self):
        return self.log_likelihood()


# =====================================================================
#  FLRW_tilt (1D: pure tilt, no shear — fills the model hierarchy gap)
# =====================================================================
class FLRW_tilt(BianchiModel):
    """Tilted FLRW: isotropic geometry (Σ² = 0) with tilt (β ≠ 0).

    This model fills the structural gap in the evidence hierarchy:
        β=0      β≠0
    Σ²=0  FLRW    FLRW_tilt  ← THIS MODEL
    Σ²≠0  BI_orth BI_tilt

    The evidence decomposition:
      ln B(BI_tilt) ≈ ln B(BI_orth) + ln B(FLRW_tilt) + interaction

    Parameters: β (tilt rapidity), log-uniform on [10⁻⁸, 10⁻¹].
    Observables: ε₁ from β, D₂^boost from β, all shear terms = 0.
    """
    name = "FLRW_tilt"; param_names = ["beta"]; ndim = 1
    _bianchi_type = 'FLRW'

    def prior_transform(self, u):
        b = _logu(u[0], 1e-8, 1e-1)
        return np.array([b])

    def predicted_observables(self, theta):
        beta = theta[0]
        e1 = eps1_from_beta(beta)
        return {
            "eps1": e1, "beta": beta,
            "omega_H": 0., "Sigma2": 0.,
            "D2_shear": 0.,
            "D2_boost": boost_to_D2(beta),
            "D3_shear": 0.,
        }

    def log_evidence_quadrature(self, n_points=10000):
        """Compute ln Z by 1D numerical quadrature over log β.

        For this single-parameter model, direct quadrature is more
        accurate than nested sampling.  Uses the trapezoidal rule
        on a uniform grid in log₁₀(β).
        """
        log10_lo, log10_hi = -8.0, -1.0
        log10_beta = np.linspace(log10_lo, log10_hi, n_points)
        betas = 10.0**log10_beta

        # Prior is uniform in log₁₀(β) ⇒ dβ/β = ln(10) d(log₁₀β)
        # ⇒ prior density p(β) = 1/(β × (log₁₀_hi − log₁₀_lo) × ln10)
        log_prior_norm = -np.log((log10_hi - log10_lo) * np.log(10))

        log_likes = np.array([
            self.log_likelihood(np.array([b])) for b in betas
        ])

        # log integrand = log L(β) + log p(β) = log L + log_prior_norm - log(β)
        log_integrand = log_likes + log_prior_norm - np.log(betas)

        # Trapezoidal integration in β-space:
        # ∫ L(β) p(β) dβ ≈ Σ L_i p_i Δβ_i
        # Since grid is uniform in log₁₀β, Δβ_i = β_i × ln(10) × Δ(log₁₀β)
        d_log10 = log10_beta[1] - log10_beta[0]
        log_dβ = np.log(betas) + np.log(np.log(10)) + np.log(d_log10)

        log_terms = log_likes + log_prior_norm + log_dβ - np.log(betas)
        # Simplifies to: log_likes + log_prior_norm + log(ln10 × d_log10)
        log_terms_simple = log_likes + log_prior_norm + np.log(np.log(10) * d_log10)

        # log-sum-exp for numerical stability
        max_lt = np.max(log_terms_simple)
        ln_Z = max_lt + np.log(np.sum(np.exp(log_terms_simple - max_lt)))

        # Also extract posterior statistics
        log_post = log_terms_simple - ln_Z
        post = np.exp(log_post)
        beta_mean = np.sum(post * betas)
        beta_median = betas[np.searchsorted(np.cumsum(post), 0.5)]
        beta_mode = betas[np.argmax(log_likes)]
        # 68% CI
        cumpost = np.cumsum(post)
        i16 = np.searchsorted(cumpost, 0.16)
        i84 = np.searchsorted(cumpost, 0.84)
        beta_lo = betas[i16]
        beta_hi = betas[min(i84, len(betas)-1)]

        return {
            'lnZ': float(ln_Z),
            'beta_mean': float(beta_mean),
            'beta_median': float(beta_median),
            'beta_mode': float(beta_mode),
            'beta_68CI': (float(beta_lo), float(beta_hi)),
            'n_points': n_points,
            'log_likes': log_likes,
            'betas': betas,
            'posterior': post,
        }

# =====================================================================
#  Orthogonal Models (ℓ=2 only, no tilt)
# =====================================================================
class _OrthBase(BianchiModel):
    _shear_mode = 'decay'

    def _pred_orth(self, Sig2, x_h=None):
        if not self._mes_ok(Sig2): return None
        return {"eps1":0., "beta":0., "omega_H":0.,
                "Sigma2": Sig2,
                "D2_shear": shear_to_D2(Sig2, self._shear_mode, x_h),
                "D2_boost": 0.,
                "D3_shear": shear_to_D3(Sig2, self._shear_mode, x_h),
                "x_h": x_h}


class BianchiI_orth(_OrthBase):
    name="BI_orth"; param_names=["Sigma2"]; ndim=1; _bianchi_type='I'
    def prior_transform(self, u): return np.array([_logu(u[0], 1e-30, 1e-4)])
    def predicted_observables(self, theta): return self._pred_orth(theta[0])

class BianchiVII0_orth(_OrthBase):
    name="BVII0_orth"; param_names=["Sigma2"]; ndim=1; _bianchi_type='I'
    def prior_transform(self, u): return np.array([_logu(u[0], 1e-30, 1e-4)])
    def predicted_observables(self, theta): return self._pred_orth(theta[0])

class BianchiII_orth(_OrthBase):
    name="BII_orth"; param_names=["Sigma2","n1"]; ndim=2; _bianchi_type='I'
    def prior_transform(self, u):
        return np.array([_logu(u[0], 1e-30, 1e-4), _logu(u[1], 1e-6, 1.)])
    def predicted_observables(self, theta): return self._pred_orth(theta[0])

class BianchiVI0_orth(_OrthBase):
    name="BVI0_orth"; param_names=["Sigma2","a1"]; ndim=2; _bianchi_type='I'
    def prior_transform(self, u):
        return np.array([_logu(u[0], 1e-30, 1e-4), _logu(u[1], 1e-6, 1.)])
    def predicted_observables(self, theta): return self._pred_orth(theta[0])

class BianchiVIII_orth(_OrthBase):
    name="BVIII_orth"; param_names=["Sigma2","Omega_k"]; ndim=2; _bianchi_type='I'
    def prior_transform(self, u):
        return np.array([_logu(u[0], 1e-30, 1e-4), _gauss(u[1], 0., 0.005)])
    def predicted_observables(self, theta): return self._pred_orth(theta[0])

class BianchiIX_orth(_OrthBase):
    name="BIX_orth"; param_names=["Sigma2","Omega_k"]; ndim=2; _bianchi_type='IX'
    def prior_transform(self, u):
        S = _logu(u[0], 1e-30, 1e-4)
        Ok = -abs(_gauss(u[1], OK_PLANCK, OK_SIGMA))
        if Ok >= 0: Ok = -1e-6
        return np.array([S, Ok])
    def predicted_observables(self, theta):
        Sig2, Ok = theta
        return self._pred_orth(Sig2)

class BianchiVIIh_orth(_OrthBase):
    name="BVIIh_orth"; param_names=["Sigma2","x_h"]; ndim=2; _bianchi_type='VIIh'
    def prior_transform(self, u):
        return np.array([_logu(u[0], 1e-30, 1e-4), _logu(u[1], 1e-3, 1e3)])
    def predicted_observables(self, theta):
        Sig2, xh = theta
        if not self._mes_ok(Sig2): return None
        W2 = R_WS_VIIH**2 * Sig2
        omH = omH_from_W2(W2)
        return {"eps1":0., "beta":0., "omega_H":omH,
                "Sigma2":Sig2, "W2":W2, "x_h":xh,
                "D2_shear": shear_to_D2(Sig2, 'decay', xh),
                "D2_boost": 0.,
                "D3_shear": shear_to_D3(Sig2, 'decay', xh)}

class BianchiVIIh_orth_grow(_OrthBase):
    name="BVIIh_orth_grow"; param_names=["Sigma2","x_h"]; ndim=2
    _bianchi_type='VIIh'; _shear_mode='grow'
    def prior_transform(self, u):
        return np.array([_logu(u[0], 1e-20, 1e-4), _logu(u[1], 1e-3, 1e3)])
    def predicted_observables(self, theta):
        Sig2, xh = theta
        if not self._mes_ok(Sig2): return None
        W2 = R_WS_VIIH**2 * Sig2
        omH = omH_from_W2(W2)
        return {"eps1":0., "beta":0., "omega_H":omH,
                "Sigma2":Sig2, "W2":W2, "x_h":xh,
                "D2_shear": shear_to_D2(Sig2, 'grow', xh),
                "D2_boost": 0.,
                "D3_shear": shear_to_D3(Sig2, 'grow', xh)}


# =====================================================================
#  Tilted Models
# =====================================================================
class BianchiI_tilt(BianchiModel):
    name="BI_tilt"; param_names=["Sigma2","beta"]; ndim=2; _bianchi_type='I'
    def prior_transform(self, u):
        return np.array([_logu(u[0], 1e-30, 1e-4), _logu(u[1], 1e-8, 1e-1)])
    def predicted_observables(self, theta):
        Sig2, beta = theta
        e1 = eps1_from_beta(beta)
        if not self._mes_ok(Sig2, e1): return None
        return {"eps1":e1, "beta":beta, "omega_H":0., "Sigma2":Sig2,
                "D2_shear": shear_to_D2(Sig2, "decay", None),
                "D2_boost": boost_to_D2(beta),
                "D3_shear": shear_to_D3(Sig2, "decay", None)}

class BianchiV_tilt(BianchiModel):
    name="BV_tilt"; param_names=["beta","Omega_k"]; ndim=2; _bianchi_type='V'
    def prior_transform(self, u):
        b = _logu(u[0], 1e-8, 1e-1)
        Ok = _gauss(u[1], OK_PLANCK, OK_SIGMA); Ok = max(Ok, 1e-6)
        return np.array([b, Ok])
    def predicted_observables(self, theta):
        beta, Ok = theta
        if Ok <= 0: return None
        Sig2 = Sig2_BV(beta, Ok)
        e1 = eps1_from_beta(beta)
        if not self._mes_ok(Sig2, e1): return None
        return {"eps1":e1, "beta":beta, "omega_H":0., "Sigma2":Sig2,
                "Omega_k":Ok,
                "D2_shear": shear_to_D2(Sig2, "decay", None),
                "D2_boost": boost_to_D2(beta),
                "D3_shear": shear_to_D3(Sig2, "decay", None)}

class BianchiIII_tilt(BianchiModel):
    name="BIII_tilt"; param_names=["Sigma2","beta","Omega_k"]; ndim=3; _bianchi_type='I'
    def prior_transform(self, u):
        S = _logu(u[0], 1e-30, 1e-4); b = _logu(u[1], 1e-8, 1e-1)
        Ok = _gauss(u[2], OK_PLANCK, OK_SIGMA); Ok = max(Ok, 1e-6)
        return np.array([S, b, Ok])
    def predicted_observables(self, theta):
        Sig2, beta, Ok = theta
        e1 = eps1_from_beta(beta)
        if not self._mes_ok(Sig2, e1): return None
        return {"eps1":e1, "beta":beta, "omega_H":0., "Sigma2":Sig2,
                "Omega_k":Ok,
                "D2_shear": shear_to_D2(Sig2, "decay", None),
                "D2_boost": boost_to_D2(beta),
                "D3_shear": shear_to_D3(Sig2, "decay", None)}

class BianchiIX_tilt(BianchiModel):
    name="BIX_tilt"; param_names=["Sigma2","beta","Omega_k"]; ndim=3; _bianchi_type='IX'
    def prior_transform(self, u):
        S = _logu(u[0], 1e-30, 1e-4); b = _logu(u[1], 1e-8, 1e-1)
        Ok = -abs(_gauss(u[2], OK_PLANCK, OK_SIGMA))
        if Ok >= 0: Ok = -1e-6
        return np.array([S, b, Ok])
    def predicted_observables(self, theta):
        Sig2, beta, Ok = theta
        e1 = eps1_from_beta(beta)
        if not self._mes_ok(Sig2, e1): return None
        return {"eps1":e1, "beta":beta, "omega_H":0., "Sigma2":Sig2,
                "Omega_k":Ok,
                "D2_shear": shear_to_D2(Sig2, "decay", None),
                "D2_boost": boost_to_D2(beta),
                "D3_shear": shear_to_D3(Sig2, "decay", None)}

class BianchiVIIh_tilt(BianchiModel):
    name="BVIIh_tilt"; param_names=["Sigma2","W2","beta","x_h"]; ndim=4
    _bianchi_type='VIIh'
    def prior_transform(self, u):
        S = _logu(u[0], 1e-30, 1e-4); W = _logu(u[1], 1e-24, 1e-10)
        b = _logu(u[2], 1e-8, 1e-1); xh = _logu(u[3], 1e-3, 1e3)
        return np.array([S, W, b, xh])
    def predicted_observables(self, theta):
        Sig2, W2, beta, xh = theta
        e1 = eps1_from_beta(beta)
        if not self._mes_ok(Sig2, e1): return None
        omH = omH_from_W2(W2)
        return {"eps1":e1, "beta":beta, "omega_H":omH,
                "Sigma2":Sig2, "W2":W2, "x_h":xh,
                "D2_shear": shear_to_D2(Sig2, "decay", xh),
                "D2_boost": boost_to_D2(beta),
                "D3_shear": shear_to_D3(Sig2, "decay", xh)}

class BianchiVIIh_tilt_grow(BianchiModel):
    name="BVIIh_tilt_grow"; param_names=["Sigma2","W2","beta","x_h"]; ndim=4
    _bianchi_type='VIIh'; _shear_mode='grow'
    def prior_transform(self, u):
        S = _logu(u[0], 1e-20, 1e-4); W = _logu(u[1], 1e-24, 1e-10)
        b = _logu(u[2], 1e-8, 1e-1); xh = _logu(u[3], 1e-3, 1e3)
        return np.array([S, W, b, xh])
    def predicted_observables(self, theta):
        Sig2, W2, beta, xh = theta
        e1 = eps1_from_beta(beta)
        if not self._mes_ok(Sig2, e1): return None
        omH = omH_from_W2(W2)
        return {"eps1":e1, "beta":beta, "omega_H":omH,
                "Sigma2":Sig2, "W2":W2, "x_h":xh,
                "D2_shear": shear_to_D2(Sig2, "grow", xh),
                "D2_boost": boost_to_D2(beta),
                "D3_shear": shear_to_D3(Sig2, "grow", xh)}


# =====================================================================
#  CONSISTENCY DIAGNOSTIC: Dipolar Deceleration (TF-N02)
# =====================================================================
# This function does NOT participate in the evidence computation.
# It provides a non-CF4 consistency check: β_SNe(z_ref) vs model β.
# See TF-T03 §channel-i for the decision not to add channel (i).
#
# No channel-c Fisher comparison is active while the PR-120 findings are OPEN.

_C_KMS = 299792.458
_COLIN_QD = -8.03
_COLIN_S  = 0.0262

def consistency_Dq(
    beta,
    z_ref=0.05,
    q_d=_COLIN_QD,
    S=_COLIN_S,
    beta_CF4=None,
    sigma_CF4=None,
):
    """Dipolar deceleration consistency diagnostic.

    Translates the Colin et al. (2019) dipolar q into β_SNe at
    z_ref using the Tsagas formula, and computes χ² against the
    caller-supplied model beta. This function is INERT in the evidence
    computation and excludes channel c.

    Parameters
    ----------
    beta : float
        Model-predicted tilt rapidity (from nested sampling posterior).
    z_ref : float
        Reference redshift for the Colin → β translation.
    q_d : float
        Colin dipole amplitude (default: −8.03).
    S : float
        Colin decay scale (default: 0.0262).
    Returns
    -------
    dict with keys:
        'beta_SNe'    : float — β translated from Colin at z_ref
        'chi2_vs_model': float — (β_SNe − beta)² / σ²_β,i
        'sigma_beta_i' : float — uncertainty on β_SNe
    """
    if beta_CF4 is not None or sigma_CF4 is not None:
        require_cf4_observational_input(consumer="consistency_Dq CF4 arguments")

    # β_SNe = 9|q_d| z³ exp(−z/S)
    beta_SNe = 9.0 * abs(q_d) * z_ref**3 * np.exp(-z_ref / S)

    # σ(β_SNe) = |dβ/dq_d| × σ(q_d) = 9 z³ exp(−z/S) × |q_d|/3.9
    sigma_qd = abs(q_d) / 3.9
    sigma_beta_i = 9.0 * z_ref**3 * np.exp(-z_ref / S) * sigma_qd

    # χ² against model-predicted β
    chi2_model = ((beta_SNe - beta) / sigma_beta_i)**2

    return {
        'beta_SNe':      beta_SNe,
        'chi2_vs_model': chi2_model,
        'sigma_beta_i':  sigma_beta_i,
        'excluded_channels': ['c'],
        'cf4_channel_status': 'QUARANTINED_OPEN_FINDINGS',
    }


def consistency_Dq_scan(beta, z_refs=None, **kwargs):
    """Run consistency_Dq at multiple z_ref values.

    Returns a list of dicts, one per z_ref.
    """
    if z_refs is None:
        z_refs = [0.03, 0.04, 0.05, 0.06, 0.08, 0.10]
    return [{'z_ref': z, **consistency_Dq(beta, z_ref=z, **kwargs)}
            for z in z_refs]


# =====================================================================
#  Registry
# =====================================================================
ALL_MODELS = {
    "FLRW": FLRW, "FLRW_tilt": FLRW_tilt,
    "BI_orth": BianchiI_orth, "BVII0_orth": BianchiVII0_orth,
    "BII_orth": BianchiII_orth, "BVI0_orth": BianchiVI0_orth,
    "BVIII_orth": BianchiVIII_orth, "BIX_orth": BianchiIX_orth,
    "BVIIh_orth": BianchiVIIh_orth, "BVIIh_orth_grow": BianchiVIIh_orth_grow,
    "BI_tilt": BianchiI_tilt, "BV_tilt": BianchiV_tilt,
    "BIII_tilt": BianchiIII_tilt, "BIX_tilt": BianchiIX_tilt,
    "BVIIh_tilt": BianchiVIIh_tilt, "BVIIh_tilt_grow": BianchiVIIh_tilt_grow,
}

def create_model(name, obs=None, channels=None):
    if name not in ALL_MODELS:
        raise ValueError(f"Unknown model '{name}'")
    return ALL_MODELS[name](obs=obs, channels=channels)


# ── SSOT cross-validation (T3-10 upgrade: 15 checks, strict) ─
def _validate_ssot():
    """Cross-validate all evidence_models constants against ssot.py.

    Raises AssertionError on any mismatch; silently passes if ssot.py
    is unavailable (standalone mode).  Called at import time and by
    the test suite (test_pipeline.py::test_ssot_triple_consistency).
    """
    try:
        from ssot import C
    except ImportError:
        return  # standalone mode; no cross-check possible
    _checks = [
        ('T0',          T0,              C.T0_K),
        ('T0_UK',       T0_UK,           C.T0_uK),
        ('EPS2',        EPS2,            C.eps2),
        ('EPS3',        EPS3,            C.eps3),
        ('ETA_UDOT',    ETA_UDOT,        C.eta_udot),
        ('OMEGA_M',     OMEGA_M,         C.Omega_m),
        ('OMEGA_L',     OMEGA_L,         C.Omega_Lambda),
        ('R_WS_VIIH',   R_WS_VIIH,      C.R_WS_VIIh),
        ('D2_OBS',      D2_OBS,          C.D2_obs),
        ('D3_OBS',      D3_OBS,          C.D3_obs),
        ('D2_LCDM',     D2_LCDM,        C.D2_LCDM),
        ('D3_LCDM',     D3_LCDM,        C.D3_LCDM),
        ('T2_DECAY',    T2_TOTAL_DECAY,  C.T2_decay),
        ('T2_GROW',     T2_TOTAL_GROW,   C.T2_grow),
        ('K_MES',       K_MES_STEEP,     C.K_MES),
    ]
    for name, local, ssot_val in _checks:
        assert local == ssot_val, (
            f"SSOT mismatch: {name}: evidence_models={local}, "
            f"ssot.C={ssot_val}"
        )
    return True

_validate_ssot()

# =====================================================================
#  MODEL IDENTIFIABILITY AUDIT (CA-07, CA-08)
# =====================================================================
MODEL_AUDIT = {
    'FLRW':            {'active': [],                       'inactive': [],            'equivalence': 'FLRW',       'duplicate_of': None},
    'FLRW_tilt':       {'active': ['beta'],                 'inactive': [],            'equivalence': 'tilt_only',  'duplicate_of': None},
    'BI_orth':         {'active': ['Sigma2'],               'inactive': [],            'equivalence': 'orth_1D',    'duplicate_of': None},
    'BVII0_orth':      {'active': ['Sigma2'],               'inactive': [],            'equivalence': 'orth_1D',    'duplicate_of': 'BI_orth'},
    'BII_orth':        {'active': ['Sigma2'],               'inactive': ['n1'],        'equivalence': 'orth_1D',    'duplicate_of': 'BI_orth'},
    'BVI0_orth':       {'active': ['Sigma2'],               'inactive': ['a1'],        'equivalence': 'orth_1D',    'duplicate_of': 'BI_orth'},
    'BVIII_orth':      {'active': ['Sigma2'],               'inactive': ['Omega_k'],   'equivalence': 'orth_1D',    'duplicate_of': 'BI_orth'},
    'BIX_orth':        {'active': ['Sigma2'],               'inactive': ['Omega_k'],   'equivalence': 'orth_1D',    'duplicate_of': 'BI_orth'},
    'BVIIh_orth':      {'active': ['Sigma2', 'x_h'],       'inactive': [],            'equivalence': 'orth_VIIh',  'duplicate_of': None},
    'BVIIh_orth_grow': {'active': ['Sigma2', 'x_h'],       'inactive': [],            'equivalence': 'orth_VIIh_g','duplicate_of': None},
    'BI_tilt':         {'active': ['Sigma2', 'beta'],       'inactive': [],            'equivalence': 'tilt_flat',  'duplicate_of': None},
    'BV_tilt':         {'active': ['beta', 'Omega_k'],      'inactive': [],            'equivalence': 'BV_unique',  'duplicate_of': None},
    'BIII_tilt':       {'active': ['Sigma2', 'beta'],       'inactive': ['Omega_k'],   'equivalence': 'tilt_flat',  'duplicate_of': 'BI_tilt'},
    'BIX_tilt':        {'active': ['Sigma2', 'beta'],       'inactive': ['Omega_k'],   'equivalence': 'tilt_flat',  'duplicate_of': 'BI_tilt'},
    'BVIIh_tilt':      {'active': ['Sigma2','W2','beta','x_h'], 'inactive': [],        'equivalence': 'tilt_VIIh',  'duplicate_of': None},
    'BVIIh_tilt_grow': {'active': ['Sigma2','W2','beta','x_h'], 'inactive': [],        'equivalence': 'tilt_VIIh_g','duplicate_of': None},
}


def _jsonify(obj: Any) -> Any:
    """Recursively convert numpy-heavy structures to JSON-native values."""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, np.generic):
        return obj.item()
    if isinstance(obj, Mapping):
        return {str(k): _jsonify(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonify(v) for v in obj]
    return obj


def _config_hash(payload: Mapping[str, Any]) -> str:
    """Stable SHA256 hash for report configuration payloads."""
    blob = json.dumps(_jsonify(payload), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def audit_inactive_parameters():
    """Return summary of inactive parameters and duplicate models (CA-08)."""
    from collections import defaultdict
    report = {'inactive_parameters': {}, 'duplicate_models': {}, 'equivalence_classes': {}}
    for tag, info in MODEL_AUDIT.items():
        if info['inactive']:
            report['inactive_parameters'][tag] = info['inactive']
        if info['duplicate_of']:
            report['duplicate_models'][tag] = info['duplicate_of']
    eq = defaultdict(list)
    for tag, info in MODEL_AUDIT.items():
        eq[info['equivalence']].append(tag)
    report['equivalence_classes'] = {k: v for k, v in eq.items() if len(v) > 1}
    return report


def model_identifiability_audit_artifact(
    *,
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build ``model_identifiability_audit_v1.json`` from ``MODEL_AUDIT``."""
    report = audit_inactive_parameters()
    equivalence_classes = {
        key: value
        for key, value in report['equivalence_classes'].items()
        if len(value) > 1
    }
    extra = dict(metadata or {})
    config_payload = {
        'metadata': extra,
        'n_models': len(MODEL_AUDIT),
    }
    return _jsonify({
        'artifact_name': 'model_identifiability_audit_v1.json',
        'generated_by': extra.get(
            'generated_by',
            'htt.core.evidence_models_R03a.model_identifiability_audit_artifact',
        ),
        'git_commit': extra.get('git_commit', ''),
        'config_hash': _config_hash(config_payload),
        'input_data_hashes': list(extra.get('input_data_hashes', [])),
        'random_seed': extra.get('random_seed'),
        'wall_time_sec': extra.get('wall_time_sec'),
        'python_version': extra.get('python_version', platform.python_version()),
        'numpy_version': extra.get('numpy_version', np.__version__),
        'claim_tier': extra.get('claim_tier', 'REPORT'),
        'scope_label': extra.get('scope_label', 'report'),
        'production_allowed': False,
        'n_models': len(MODEL_AUDIT),
        'n_models_with_inactive_params': len(report['inactive_parameters']),
        'n_duplicate_models': len(report['duplicate_models']),
        'n_equivalence_classes_gt1': len(equivalence_classes),
        'inactive_parameters': report['inactive_parameters'],
        'duplicate_models': report['duplicate_models'],
        'equivalence_classes': equivalence_classes,
        'model_audit': MODEL_AUDIT,
    })
