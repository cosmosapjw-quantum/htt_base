"""Shared linear peculiar-velocity power spectrum utilities (REV-R196).

A self-contained fiducial LambdaCDM linear power spectrum P(k) (Eisenstein-Hu
1998 no-wiggle transfer, sigma_8-normalised, no download) plus the (H0 f)^2
prefactor and the closed-form 1-D velocity dispersion, factored out so the new
peculiar-velocity lanes (the minimum-variance ideal-window estimator and the
velocity-correlation function) share ONE power spectrum.

Convention (matches scripts/cf4_bulkflow_lcdm_variance.py, rev-r195, which keeps
its own frozen copy of these functions -- this module is a shared successor, not
an edit of the frozen script): work in Mpc/h and h/Mpc; the velocity prefactor
(a H f)^2 in these units is (100 f)^2 (the h cancels), f = Omega_m^0.55. The
linear 1-D velocity dispersion is sigma_v_1d^2 = (100 f)^2/(6 pi^2) * int P dk.

Diagnostic-only kinematic descriptor; no Bianchi family, geometry, or
observer-frame claim.
"""
from __future__ import annotations

import json
from importlib import resources

import numpy as np

OBS_DEFAULTS = resources.files("workspace").joinpath("data").joinpath("obs_defaults.json")

# fiducial LambdaCDM extras not carried in obs_defaults (Planck 2018 base)
OMEGA_B = 0.0493
N_S = 0.9649
SIGMA_8 = 0.8111
T_CMB = 2.7255

# k-range for the sigma_8 normalisation + the 1-D dispersion integral
KMIN_S, KMAX_S = 1.0e-4, 50.0


def _trapz(y, x):
    return np.trapz(y, x) if hasattr(np, "trapz") else np.trapezoid(y, x)


def transfer_eh98_nw(k_hmpc, om, ob, h):
    """Eisenstein-Hu 1998 no-wiggle transfer, k in h/Mpc."""
    k_hmpc = np.asarray(k_hmpc, dtype=float)
    omhh = om * h * h
    theta = T_CMB / 2.7
    s = 44.5 * np.log(9.83 / omhh) / np.sqrt(1.0 + 10.0 * (ob * h * h) ** 0.75)
    ob_om = ob / om
    ag = (1.0 - 0.328 * np.log(431.0 * omhh) * ob_om
          + 0.38 * np.log(22.3 * omhh) * ob_om ** 2)
    k_mpc = k_hmpc * h
    gamma = om * h * (ag + (1.0 - ag) / (1.0 + (0.43 * k_mpc * s) ** 4))
    q = k_hmpc * theta * theta / gamma
    c0 = 14.2 + 731.0 / (1.0 + 62.5 * q)
    l0 = np.log(2.0 * np.e + 1.8 * q)
    return l0 / (l0 + c0 * q * q)


def _sigma8_sq_unnorm(pk_unnorm, k):
    r = 8.0                                              # Mpc/h
    x = k * r
    w = 3.0 * (np.sin(x) - x * np.cos(x)) / x ** 3
    return _trapz(k * k * pk_unnorm(k) * w * w, k) / (2.0 * np.pi ** 2)


def make_pk(om, ob, h):
    """sigma_8-normalised linear P(k) = A k^n_s T(k)^2, k in h/Mpc, P in (Mpc/h)^3."""
    def pk_unnorm(k):
        return k ** N_S * transfer_eh98_nw(k, om, ob, h) ** 2
    k8 = np.geomspace(KMIN_S, KMAX_S, 4000)
    amp = SIGMA_8 ** 2 / _sigma8_sq_unnorm(pk_unnorm, k8)
    return lambda k: amp * pk_unnorm(k)


def velocity_correlation_functions(pk, hf2, a_grid, *, kmin=1.0e-4, kmax=10.0,
                                   nk=4000):
    """Linear radial/transverse peculiar-velocity correlation functions
    (Gorski 1988), km^2/s^2, on the separation grid a_grid (Mpc/h):

        Psi_par(A)  = hf2/(2 pi^2) int P(k) [j0(kA) - 2 j1(kA)/(kA)] dk
        Psi_perp(A) = hf2/(2 pi^2) int P(k)  j1(kA)/(kA)            dk

    with hf2 = (100 f)^2. At A -> 0 both reduce to sigma_v_1d^2 = hf2/(6 pi^2)
    int P dk (isotropic). These are the closed-form angular integrals of the
    velocity covariance tensor -- the well-converged replacement for a numerical
    solid-angle grid, shared by the MV pairwise covariance and the
    velocity-correlation-function statistic."""
    from scipy.special import spherical_jn
    a = np.asarray(a_grid, float)
    k = np.geomspace(kmin, kmax, nk)
    pkv = pk(k)
    pref = hf2 / (2.0 * np.pi ** 2)
    psi_par = np.empty_like(a)
    psi_perp = np.empty_like(a)
    for i, A in enumerate(a):
        x = k * A
        if A <= 0.0:
            psi_par[i] = pref * _trapz(pkv * (1.0 / 3.0), k)
            psi_perp[i] = psi_par[i]
            continue
        j0 = spherical_jn(0, x)
        j1 = spherical_jn(1, x)
        j1_over_x = j1 / x
        psi_par[i] = pref * _trapz(pkv * (j0 - 2.0 * j1_over_x), k)
        psi_perp[i] = pref * _trapz(pkv * j1_over_x, k)
    return psi_par, psi_perp


def fiducial():
    """Load the fiducial cosmology (Omega_m, h from obs_defaults; the rest above).

    Returns a dict: om, ob, h, f_growth, hf2 = (100 f)^2, pk callable, and the
    linear 1-D velocity dispersion sigma_v_1d (km/s)."""
    obs = json.loads(OBS_DEFAULTS.read_text(encoding="utf-8"))
    om, h = float(obs["Omega_m"]), float(obs["h"])
    f = om ** 0.55
    hf2 = (100.0 * f) ** 2
    pk = make_pk(om, OMEGA_B, h)
    ks = np.geomspace(KMIN_S, KMAX_S, 400)
    sigma_v_1d = float(np.sqrt(hf2 / (6.0 * np.pi ** 2) * _trapz(pk(ks), ks)))
    return {"om": om, "ob": OMEGA_B, "h": h, "n_s": N_S, "sigma_8": SIGMA_8,
            "f_growth": f, "hf2": hf2, "pk": pk, "sigma_v_1d": sigma_v_1d}
