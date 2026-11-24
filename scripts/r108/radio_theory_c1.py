"""R108 radio lane (SQ-RADIO, R107 THEORY_FOUNDATIONS TF7): LSS angular power C_1 of radio source counts without Limber.

Purpose
    C_l = (2/pi) int dk k^2 [W_l(k)]^2 with W_l(k) = int dchi n_chi(chi) b(z) T(k,z) j_l(k chi), T(k,z) = sqrt(P(k,z))
    (equivalently D(z) sqrt(P(k,0)) in linear theory; both are computed), evaluated at l = 1 with exact spherical
    Bessel functions for literature brackets of the radio n(z) and b(z), Planck 2018 cosmology, CAMB P(k,z) and chi(z).
    Optional terms, reported separately so that they can be bounded:
      * redshift-space (Kaiser) term  W^RSD_l = - int dchi n_chi f(z) T_lin(k,z) j_l''(k chi)   (delta_s = (b + f mu^2) delta);
      * magnification term  2(x-1) W^kappa_l  with N(>S) ~ S^-x and
        W^kappa_l(k) = l(l+1) (3/2) Om (H0/c)^2 int dchi (1+z) T_lin(k,z) j_l(k chi) g(chi)/(k^2 chi),
        g(chi) = int_chi^inf dchi_s n_chi(chi_s) (chi_s - chi)/chi_s   (Born, flat; kappa_lm = l(l+1)/2 psi_lm).
    The observer-velocity (kinematic) dipole is not part of C_1 (R106 injects it as the common dipole D0).
Validation (written into the output JSON, all before l = 1 is used)
    V1 exact real-space identity for P = A k^-2:  C_l = A/(2l+1) int int n(chi) n(chi') chi_<^l / chi_>^(l+1)
       (from int_0^inf j_l(k a) j_l(k b) dk = pi/(2(2l+1)) a_<^l/a_>^(l+1)), at l = 1, 2, 5 for three n(chi);
    V2 Limber at l = 100, 300 (C_l^Limber = int dchi n_chi^2 b^2 P((l+1/2)/chi, z)/chi^2);
    V3 CAMB 2.0.5 non-Limber number counts (SplinedSourceWindow, density only, then density+redshift, then
       density+lensing) at l = 2..10 with massless neutrinos, i.e. an independent line-of-sight code;
    V4 numerical convergence of C_1 (chi sampling, k grid, k_max).
    V3 systematic: the integrator lies below CAMB counts_density at low l (unexplained: V3_DIAGNOSTIC.json rules out the
       P(k) sampling and matter variable and records a CAMB accuracy variation). The per-window power law of |rel(l)| over
       l = 2..10 is extrapolated to l = 1; s = max over windows; the envelope and C1_forms_for_R106 carry the upward factor
       1/(1 - s) (V3_low_l_systematic, envelope.<pv>.with_V3_low_l_systematic, *_x_V3_factor_up). It is a systematic,
       not a correction.
Brackets (exact locators)
    n(z): DZ10  de Zotti et al. 2010, A&ARv 18, 1 (arXiv:0908.1896) Sect. 9.1 Eq. (26):
                N(z) = 1.29 + 32.37 z - 32.89 z^2 + 11.13 z^3 - 1.25 z^4  (CENSORS fit; truncated at its first root z > 0)
          TN16  Tiwari & Nusser 2016, JCAP 03 (2016) 062 (arXiv:1509.02532) Eq. (3.11): N ~ z^a1 exp[-(z/a2)^a3],
                a1 = 0.74, a2 = 0.71, a3 = 1.06 (Nusser & Tiwari 2015 fit)
          H08   Ho et al. 2008, PRD 78, 043519 (arXiv:0801.0642) Sect. V.D.1 Eq. (33): b dN/dz ~ z^alpha exp(-alpha z/z*),
                alpha = 1.18, z* = 0.79, b_eff = 1.98
    b(z): NT15      b = 0.33 z^2 + 0.85 z + 1.6 (Nusser & Tiwari 2015, ApJ 812, 85, arXiv:1505.06817; TN16 Eq. (3.12))
          NT15cap   the same with b(z > 1.5) = b(1.5) (TN16 Sect. 4)
          const2, const3   b = 2, 3 (TN16 Sect. 3.3 and Table 2)
          H08beff   b = 1.98 (Ho et al. 2008, text after Eq. (33))
    Cosmology: Planck 2018 VI (arXiv:1807.06209) Table 2, column TT,TE,EE+lowE+lensing+BAO: H0 = 67.66, Omega_b h^2 =
    0.02242, Omega_c h^2 = 0.11933, tau = 0.0561, ln(10^10 A_s) = 3.047, n_s = 0.9665, one massive neutrino 0.06 eV.
Units: k in 1/Mpc, chi in Mpc, P in Mpc^3, C_l dimensionless (fractional count contrast; equals the log-density C_l to
first order, the quantity whose l = 1 value R106 calls C_1: per-component dipole RMS sqrt(3 C_1/4 pi), TN16 Eq. (3.9)
C_1 = (4 pi/9) D^2).
Shot noise: 1/Nbar (sources per steradian; TN16 Eq. (3.4)) from the R65 NVSS carrier (input SHA-256 recorded).
Inputs: docs/.../R65_DIPOLE_ANOMALY_20261117/RESULTS/PROVIDER_NVSS_CARRIERS.npz (SHA-256
    a51da9a98c3d0563446eb61f21aceff69fbfeed5446ec74471177170b8664e89, verified at run time).
Usage (repo root, SYSTEM python with camb):
    python3 -m scripts.r108.radio_theory_c1 --out docs/research_program/observational_publication_20261015/R108_LOS_ATLAS_DATA_20261124/RADIO/THEORY_C1.json
Deterministic (no random numbers).
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import itertools
import json
import math
import platform
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from scipy import special
from scipy.integrate import cumulative_trapezoid, simpson
from scipy.interpolate import CubicSpline

C_KM_S = 299792.458
PLANCK18 = dict(H0=67.66, ombh2=0.02242, omch2=0.11933, tau=0.0561, ln10As=3.047, ns=0.9665, mnu=0.06)
PLANCK18_LOCATOR = "Planck 2018 VI (arXiv:1807.06209) Table 2, column TT,TE,EE+lowE+lensing+BAO"
CARRIER = Path("docs/research_program/observational_publication_20261015/R65_DIPOLE_ANOMALY_20261117/RESULTS/PROVIDER_NVSS_CARRIERS.npz")
CARRIER_SHA = "a51da9a98c3d0563446eb61f21aceff69fbfeed5446ec74471177170b8664e89"
NSIDE_R65 = 64
ZMAX = 7.0

# ---------------------------------------------------------------------------------------------- literature brackets

DZ10_COEF = (1.29, 32.37, -32.89, 11.13, -1.25)


def dz10_root():
    """First positive root of the de Zotti et al. 2010 Eq. (26) polynomial (where it turns negative)."""
    r = np.roots(DZ10_COEF[::-1])
    r = np.sort(r[(abs(r.imag) < 1e-12) & (r.real > 0)].real)
    return float(r[0])


def nz_shape(name, z):
    """Un-normalised n(z) of a bracket (dN/dz up to a constant)."""
    z = np.asarray(z, dtype=float)
    if name == "DZ10":
        zr = dz10_root()
        v = sum(c * z ** i for i, c in enumerate(DZ10_COEF))
        return np.where((z >= 0) & (z <= zr), np.maximum(v, 0.0), 0.0)
    if name == "TN16":
        return np.where(z > 0, z ** 0.74 * np.exp(-(np.maximum(z, 0) / 0.71) ** 1.06), 0.0)
    if name == "H08":
        return np.where(z > 0, z ** 1.18 * np.exp(-1.18 * z / 0.79), 0.0)
    raise ValueError(name)


NZ_LOCATORS = {
    "DZ10": "de Zotti et al. 2010, A&ARv 18, 1 (arXiv:0908.1896), Sect. 9.1 Eq. (26): N(z)=1.29+32.37z-32.89z^2+11.13z^3-1.25z^4 (CENSORS); truncated at its first positive root",
    "TN16": "Tiwari & Nusser 2016, JCAP 03 (2016) 062 (arXiv:1509.02532), Eq. (3.11): N ~ z^0.74 exp[-(z/0.71)^1.06] (NT15 best fit)",
    "H08": "Ho et al. 2008, PRD 78, 043519 (arXiv:0801.0642), Sect. V.D.1 Eq. (33): z^1.18 exp(-1.18 z/0.79), b_eff = 1.98",
}


def bias(name, z):
    z = np.asarray(z, dtype=float)
    if name == "NT15":
        return 0.33 * z ** 2 + 0.85 * z + 1.6
    if name == "NT15cap":
        zc = np.minimum(z, 1.5)
        return 0.33 * zc ** 2 + 0.85 * zc + 1.6
    if name == "const2":
        return np.full_like(z, 2.0)
    if name == "const3":
        return np.full_like(z, 3.0)
    if name == "H08beff":
        return np.full_like(z, 1.98)
    if name == "unit":
        return np.ones_like(z)
    raise ValueError(name)


BIAS_LOCATORS = {
    "NT15": "Nusser & Tiwari 2015, ApJ 812, 85 (arXiv:1505.06817); Tiwari & Nusser 2016 Eq. (3.12): b = 0.33 z^2 + 0.85 z + 1.6",
    "NT15cap": "NT15 with b(z>1.5) = b(1.5), Tiwari & Nusser 2016 Sect. 4",
    "const2": "b = 2, Tiwari & Nusser 2016 Sect. 3.3 / Table 2",
    "const3": "b = 3, Tiwari & Nusser 2016 Sect. 3.3 / Table 2",
    "H08beff": "b_eff = 1.98, Ho et al. 2008 text after Eq. (33)",
}
# literature pairings (the n(z) and b(z) used together in the cited work); the full cross product is the extended set
PRIMARY = [("TN16", "NT15cap"), ("TN16", "NT15"), ("TN16", "const2"), ("TN16", "const3"),
           ("DZ10", "NT15"), ("H08", "H08beff")]


# ---------------------------------------------------------------------------------------------- spherical Bessel

def sph_jn(ell, x):
    return special.spherical_jn(ell, x)


def sph_jn_dd(ell, x):
    """Second derivative j_l''(x) from the spherical Bessel ODE j'' = -(2/x) j' - (1 - l(l+1)/x^2) j.

    For l = 0, 1 the ODE form cancels 1/x terms, so the Taylor series is used below x = 1e-3; for l >= 2 the ODE form
    has no growing cancellation and is used for all x > 0 (x = 0: 2/15 for l = 2, 0 for l >= 3)."""
    x = np.asarray(x, dtype=float)
    pos = x > 0
    xs = np.where(pos, x, 1.0)
    j = special.spherical_jn(ell, xs)
    jp = special.spherical_jn(ell, xs, derivative=True)
    big = -(2.0 / xs) * jp - (1.0 - ell * (ell + 1) / xs ** 2) * j
    if ell == 0:
        return np.where(x < 1e-3, -1.0 / 3.0 + x ** 2 / 10.0, big)
    if ell == 1:
        return np.where(x < 1e-3, -x / 5.0 + x ** 3 / 42.0, big)
    return np.where(pos, big, 2.0 / 15.0 if ell == 2 else 0.0)


# ---------------------------------------------------------------------------------------------- core integrator

class Background:
    """chi(z), H(z)/c, D(z), f(z) tables (Mpc, 1/Mpc)."""

    def __init__(self, z, chi, hc, growth=None, omega_m=None, h0c=None):
        self.z, self.chi, self.hc = (np.asarray(v, dtype=float) for v in (z, chi, hc))
        self._z_of_chi = CubicSpline(self.chi, self.z)
        self._chi_of_z = CubicSpline(self.z, self.chi)
        self._hc = CubicSpline(self.z, self.hc)
        self.growth = None if growth is None else CubicSpline(self.z, growth)
        self.omega_m, self.h0c = omega_m, h0c

    def z_of_chi(self, chi):
        return self._z_of_chi(chi)

    def chi_of_z(self, z):
        return self._chi_of_z(z)

    def hubble_over_c(self, z):
        return self._hc(z)

    def f_growth(self, z):
        d = self.growth(z)
        dd = self.growth(z, 1)
        return -(1.0 + z) * dd / d


def chi_grid(chi_lo, chi_hi, k, base_step, per_period):
    """Uniform chi grid (odd number of points for Simpson) resolving j_l(k chi) with per_period points per 2 pi/k."""
    step = min(base_step, 2.0 * math.pi / (k * per_period))
    n = int(math.ceil((chi_hi - chi_lo) / step))
    n += (n % 2 == 1)
    return np.linspace(chi_lo, chi_hi, n + 1)


class Kernel:
    """Radial kernels on chi for a bracket: n_chi(chi) b(z) and, for the optional terms, f(z) and the lensing g(chi)."""

    def __init__(self, bg, nz_fn, bias_fn, z_lo=0.0, z_hi=ZMAX, n_norm=40001):
        self.bg = bg
        self.chi_lo, self.chi_hi = float(bg.chi_of_z(z_lo)), float(bg.chi_of_z(z_hi))
        zz = np.linspace(z_lo, z_hi, n_norm)
        nz = nz_fn(zz)
        norm = simpson(nz, x=zz)
        if not norm > 0:
            raise ValueError("n(z) has no support")
        self.nz_fn, self.bias_fn, self.norm = nz_fn, bias_fn, norm
        # lensing g(chi) on a fine chi table
        cc = np.linspace(0.0, self.chi_hi, 20001)  # lenses extend from the observer to the furthest source
        nchi = self.n_chi(cc)
        a = cumulative_trapezoid(nchi[::-1], cc[::-1], initial=0.0)[::-1] * -1.0  # int_chi^hi n
        b = cumulative_trapezoid((nchi / np.maximum(cc, 1e-30))[::-1], cc[::-1], initial=0.0)[::-1] * -1.0
        self._g = CubicSpline(cc, a - cc * b)

    def n_chi(self, chi):
        z = self.bg.z_of_chi(chi)
        return self.nz_fn(z) * self.bg.hubble_over_c(z) / self.norm

    def g_lens(self, chi):
        return np.maximum(self._g(chi), 0.0)


def window(kern, k, t_of_kz, ell, term="density", base_step=4.0, per_period=32, t_lin_of_kz=None):
    """W_l(k) for one k (units Mpc^{3/2}); t_of_kz(k, z) returns sqrt(P(k,z)) on an array z."""
    chi = chi_grid(0.0 if term == "kappa" else kern.chi_lo, kern.chi_hi, k, base_step, per_period)
    z = kern.bg.z_of_chi(chi)
    x = k * chi
    if term == "density":
        f = kern.n_chi(chi) * kern.bias_fn(z) * t_of_kz(k, z) * sph_jn(ell, x)
    elif term == "rsd":
        tl = (t_lin_of_kz or t_of_kz)(k, z)
        f = -kern.n_chi(chi) * kern.bg.f_growth(z) * tl * sph_jn_dd(ell, x)
    elif term == "kappa":
        tl = (t_lin_of_kz or t_of_kz)(k, z)
        bg = kern.bg
        pref = ell * (ell + 1) * 1.5 * bg.omega_m * bg.h0c ** 2 / k ** 2
        with np.errstate(divide="ignore", invalid="ignore"):
            f = pref * (1.0 + z) * tl * sph_jn(ell, x) * kern.g_lens(chi) / chi
        f[chi <= 0] = 0.0  # j_l(k chi)/chi -> 0 for l >= 2 and -> k/3 for l = 1 times g, finite; set by continuity below
        if ell == 1 and chi[0] <= 0:
            f[0] = pref * (1.0 + z[0]) * tl[0] * (k / 3.0) * kern.g_lens(chi[:1])[0]
    else:
        raise ValueError(term)
    return float(simpson(f, x=chi))


def cl_from_windows(kgrid, wa, wb=None):
    """C = (2/pi) int dk k^2 W_a W_b with Simpson in ln k."""
    wb = wa if wb is None else wb
    return float(2.0 / math.pi * simpson(kgrid ** 3 * wa * wb, x=np.log(kgrid)))


def kgrid_log(kmin, kmax, n):
    n += (n % 2 == 0)
    return np.logspace(math.log10(kmin), math.log10(kmax), n)


def windows_for(kern, kgrid, t_of_kz, ell, terms=("density",), **kw):
    return {t: np.array([window(kern, k, t_of_kz, ell, term=t, **kw) for k in kgrid]) for t in terms}


# ---------------------------------------------------------------------------------------------- analytic references

def realspace_powerlaw_m2(chi, nchi, ell, amp=1.0):
    """Exact C_l for P = amp k^-2 (b = D = 1): amp/(2l+1) int int n n' chi_<^l/chi_>^(l+1) (trapezoid on a fine grid)."""
    chi, nchi = np.asarray(chi, float), np.asarray(nchi, float)
    inner = cumulative_trapezoid(nchi * chi ** ell, chi, initial=0.0)
    with np.errstate(divide="ignore", invalid="ignore"):
        integrand = np.where(chi > 0, nchi * inner / chi ** (ell + 1), 0.0)
    return float(2.0 * amp / (2 * ell + 1) * np.trapezoid(integrand, chi))


def limber(kern, ell, pk_of_kz, n=4001):
    chi = np.linspace(max(kern.chi_lo, 1.0), kern.chi_hi, n)
    z = kern.bg.z_of_chi(chi)
    k = (ell + 0.5) / chi
    nb = kern.n_chi(chi) * kern.bias_fn(z)
    return float(simpson(nb ** 2 * pk_of_kz(k, z) / chi ** 2, x=chi))


# ---------------------------------------------------------------------------------------------- CAMB layer

def camb_params(nonlinear=False, massless_nu=False, kmax=20.0, zmax=ZMAX + 0.5, redshifts=None):
    import camb
    from camb import model
    p = PLANCK18
    pars = camb.CAMBparams()
    pars.set_cosmology(H0=p["H0"], ombh2=p["ombh2"], omch2=p["omch2"], tau=p["tau"],
                       mnu=0.0 if massless_nu else p["mnu"], num_massive_neutrinos=0 if massless_nu else 1)
    pars.InitPower.set_params(As=math.exp(p["ln10As"]) * 1e-10, ns=p["ns"])
    pars.set_matter_power(redshifts=redshifts or [0.0], kmax=kmax)
    if nonlinear:
        pars.NonLinear = model.NonLinear_pk
        pars.NonLinearModel.set_params(halofit_version="mead2020")
    else:
        pars.NonLinear = model.NonLinear_none
    return pars


def camb_background_and_pk(nonlinear=False, massless_nu=False, kmax=20.0, var="delta_nonu"):
    import camb
    pars = camb_params(nonlinear=nonlinear, massless_nu=massless_nu, kmax=kmax)
    res = camb.get_background(pars)
    zt = np.concatenate([np.linspace(0, 0.2, 401)[:-1], np.linspace(0.2, ZMAX + 0.5, 1201)])
    chi = res.comoving_radial_distance(zt)
    hc = res.hubble_parameter(zt) / C_KM_S
    pk = camb.get_matter_power_interpolator(pars, zmin=0.0, zmax=ZMAX + 0.5, nz_step=150, kmax=kmax, nonlinear=nonlinear,
                                            var1=var, var2=var, hubble_units=False, k_hunit=False,
                                            extrap_kmax=max(1e3, kmax))
    pk_lin = pk if not nonlinear else camb.get_matter_power_interpolator(
        camb_params(nonlinear=False, massless_nu=massless_nu, kmax=kmax), zmin=0.0, zmax=ZMAX + 0.5, nz_step=150,
        kmax=kmax, nonlinear=False, var1=var, var2=var, hubble_units=False, k_hunit=False, extrap_kmax=max(1e3, kmax))
    kref = 1e-3
    growth = np.sqrt(np.array([pk_lin.P(z, kref) for z in zt]) / pk_lin.P(0.0, kref))
    om = (pars.ombh2 + pars.omch2 + pars.omnuh2) / (pars.H0 / 100.0) ** 2
    bg = Background(zt, chi, hc, growth=growth, omega_m=om, h0c=pars.H0 / C_KM_S)
    results = camb.get_results(pars)
    sig8 = float(results.get_sigma8_0())
    return pars, bg, pk, pk_lin, sig8, om


def t_from_interp(pk):
    def t(k, z):
        z = np.atleast_1d(z)
        return np.sqrt(np.maximum(pk.P(z, k, grid=False), 0.0))
    return t


def p_from_interp(pk):
    def p(k, z):
        return np.maximum(pk.P(np.atleast_1d(z), np.atleast_1d(k), grid=False), 0.0)
    return p


GAUSS_V3 = {"gauss_z0p5_s0p15": (0.5, 0.15), "gauss_z1p0_s0p30": (1.0, 0.30)}


def gauss_nz(name, z):
    """Smooth test window for the CAMB cross-check (support kept away from z = 0)."""
    z0, s = GAUSS_V3[name]
    z = np.asarray(z, dtype=float)
    return np.where(np.abs(z - z0) <= 6 * s, np.exp(-0.5 * ((z - z0) / s) ** 2), 0.0)


def camb_counts_cls(nz_name, b_const, lmax, terms, massless_nu=True, x_slope=None, accuracy=1.0):
    """CAMB non-Limber number-count C_l (l = 2..lmax) for a smooth Gaussian test window with constant bias.

    (Radio n(z) reaching z -> 0 made each CAMB run exceed 10 min in R108; the radio n(z) are validated by V1 instead.)"""
    import camb
    pars = camb_params(nonlinear=False, massless_nu=massless_nu, kmax=10.0)
    pars.set_for_lmax(lmax + 50, lens_potential_accuracy=0)
    pars.Want_CMB = False
    pars.set_accuracy(AccuracyBoost=accuracy, lSampleBoost=50, lAccuracyBoost=accuracy)
    st = pars.SourceTerms
    for name in ("counts_density", "counts_redshift", "counts_lensing", "counts_velocity", "counts_radial",
                 "counts_timedelay", "counts_ISW", "counts_potential", "counts_evolve"):
        setattr(st, name, name in terms)
    st.limber_windows = False
    st.limber_phi_lmin = 10000
    z0, sg = GAUSS_V3[nz_name]
    zz = np.linspace(max(z0 - 6 * sg, 1e-3), z0 + 6 * sg, 600)
    w = gauss_nz(nz_name, zz)
    kw = dict(z=zz, W=w, bias=b_const)
    if x_slope is not None:
        kw["dlog10Ndm"] = 0.4 * x_slope
    from camb import sources
    pars.SourceWindows = [sources.SplinedSourceWindow(**kw)]
    res = camb.get_results(pars)
    cls = res.get_source_cls_dict(raw_cl=True, lmax=lmax)
    return np.asarray(cls["W1xW1"][: lmax + 1], dtype=float)


V3_SYSTEMATIC_CAP = 0.5  # an extrapolated |rel| at l = 1 at or above this is not usable as a multiplicative systematic


def v3_low_l_systematic(v3_results, cap=V3_SYSTEMATIC_CAP):
    """Low-l offset of the integrator to CAMB counts_density (V3) carried to l = 1 as a systematic factor on C_1.

    Per V3 test window: least-squares power law log|rel| = log A + p log l over the tested l (l = 2..10), extrapolated to
    l = 1 (an extrapolation: l = 1 is not tested against CAMB). s = max over windows. The offset is unexplained (V3_DIAGNOSTIC
    rules out the integrator P(k) sampling and matter variable and records a CAMB accuracy variation), so it is carried as
    a systematic: if the integrator lies below CAMB at every tested l (rel < 0), a CAMB-like l = 1 value is C_1/(1 - s),
    i.e. factor_up = 1/(1 - s) (>= 1 + s) and factor_down = 1; all rel > 0 gives factor_down = 1/(1 + s), factor_up = 1;
    mixed signs give both. Units: dimensionless."""
    per = {}
    signs = set()
    for win in sorted({r["nz"] for r in v3_results}):
        rows = sorted((r for r in v3_results if r["nz"] == win), key=lambda r: r["ell"])
        ls = [math.log(r["ell"]) for r in rows]
        ys = [math.log(abs(r["density"]["rel"])) for r in rows]
        n = len(ls)
        mx, my = sum(ls) / n, sum(ys) / n
        slope = sum((a - mx) * (b - my) for a, b in zip(ls, ys)) / sum((a - mx) ** 2 for a in ls)
        signs |= {math.copysign(1.0, r["density"]["rel"]) for r in rows}
        per[win] = dict(ells=[r["ell"] for r in rows], power_law_exponent=slope, rel_l2=rows[0]["density"]["rel"],
                        rel_lmax=rows[-1]["density"]["rel"], extrapolated_abs_rel_l1=math.exp(my + slope * (0.0 - mx)),
                        all_negative=all(r["density"]["rel"] < 0 for r in rows))
    worst = max(per, key=lambda k: per[k]["extrapolated_abs_rel_l1"])
    s = per[worst]["extrapolated_abs_rel_l1"]
    if not s < cap:
        raise ValueError(f"V3 extrapolated |rel| at l = 1 is {s} >= {cap}: not usable as a multiplicative systematic")
    up = 1.0 / (1.0 - s) if -1.0 in signs else 1.0
    down = 1.0 / (1.0 + s) if 1.0 in signs else 1.0
    return dict(per_window=per, worst_window=worst, s_abs_rel_l1=s, factor_up=up, factor_down=down,
                integrator_below_camb_at_every_tested_l=signs == {-1.0},
                method=("power-law fit of |C_l^integrator/C_l^CAMB - 1| over the tested l per V3 window, extrapolated to l = 1; "
                        "s = max over windows; integrator below CAMB at all tested l => one-sided upward factor 1/(1 - s) "
                        "(the CAMB-like value if the deficit is a fractional deficit of the integrator)"),
                transfer_caveat=("taken from the worst smooth Gaussian test window (b = 2); the radio n(z) brackets were not run "
                                 "through CAMB (runtime), so the factor is transferred, not measured, for them"),
                status=("unexplained low-l offset to CAMB counts_density: not the integrator P(k) sampling or matter variable, "
                        "CAMB accuracy variation recorded (V3_DIAGNOSTIC.json); carried as a systematic, not a correction"))


def apply_v3_systematic(env_pv, syst):
    """Envelope values of one P(k) variant with the V3 low-l systematic applied (upper values x factor_up, lower x factor_down)."""
    up, down = syst["factor_up"], syst["factor_down"]
    return dict(factor_up=up, factor_down=down,
                primary_min=env_pv["primary_min"] * down, extended_min=env_pv["extended_min"] * down,
                primary_max=env_pv["primary_max"] * up, extended_max=env_pv["extended_max"] * up,
                differential_pair_max=env_pv["differential_pair_max"]["C1"] * up,
                differential_triangle_bound_4max=env_pv["differential_triangle_bound_4max"] * up,
                note="upper envelope values x factor_up, lower x factor_down; see V3_low_l_systematic for the method")


# ---------------------------------------------------------------------------------------------- driver helpers

def sha256(path):
    with open(path, "rb") as fh:
        return hashlib.file_digest(fh, "sha256").hexdigest()


def git_head():
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return None


def shot_noise_from_carrier(path=CARRIER):
    """Sources per steradian and 1/Nbar for the R65 NVSS selections (peak, integrated, off-diagonal, diagonal)."""
    if sha256(path) != CARRIER_SHA:
        raise ValueError("R65 carrier SHA-256 mismatch")
    with np.load(path, allow_pickle=False) as z:
        j = z["joint_bin_pixel_counts"].sum(axis=2).astype(float)
        npix = z["pixel_indices"].size
    omega = npix * 4.0 * math.pi / (12 * NSIDE_R65 ** 2)
    off = ~np.eye(4, dtype=bool)
    n = dict(peak_ge20=j[1:, :].sum(), integrated_ge20=j[:, 1:].sum(), offdiag_resolved_migrating=j[off].sum(),
             diag_selected=sum(j[i, i] for i in range(1, 4)))
    out = dict(mask_pixels=int(npix), mask_solid_angle_sr=omega, joint_class_counts=j.tolist(), selections={})
    for k, v in n.items():
        out["selections"][k] = dict(N=int(v), Nbar_per_sr=v / omega, shot_noise_1_over_Nbar=omega / v)
    out["g_diff_shot_noise"] = omega / n["offdiag_resolved_migrating"] + omega / n["diag_selected"]
    # integral count slope from the 20/40 mJy edges: N(>20)/N(>40) = 2^x
    for sel, (a, b) in dict(peak=(j[1:, :].sum(), j[2:, :].sum()), integrated=(j[:, 1:].sum(), j[:, 2:].sum())).items():
        out[f"integral_count_slope_x_20_40mJy_{sel}"] = math.log2(a / b)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--nk", type=int, default=601)
    ap.add_argument("--kmin", type=float, default=1e-5)
    ap.add_argument("--kmax", type=float, default=2.0)
    ap.add_argument("--per-period", type=int, default=32)
    ap.add_argument("--quick", action="store_true", help="primary pairings only, smaller grids (smoke)")
    a = ap.parse_args(argv)
    t0 = time.time()
    out = dict(schema="htt.r108.radio.theory_c1/1", node="SQ-RADIO", theory="R107 THEORY_FOUNDATIONS.md TF7",
               command=" ".join([sys.executable, "-m", "scripts.r108.radio_theory_c1", *(argv or sys.argv[1:])]),
               git_head=git_head(), python=platform.python_version(), started_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
               script_sha256=sha256(Path(__file__)), cosmology=dict(PLANCK18, locator=PLANCK18_LOCATOR),
               nz_locators=NZ_LOCATORS, bias_locators=BIAS_LOCATORS, primary_pairings=PRIMARY,
               conventions=dict(C1="(2/pi) int dk k^2 W_1(k)^2, fractional count contrast; per-component dipole RMS sqrt(3 C1/4pi); TN16 Eq. (3.9) C1=(4pi/9) D^2",
                                matter_variable="CAMB delta_nonu (CDM+baryons) for P(k,z); growth D from linear P at k=1e-3/Mpc",
                                magnification="coefficient alpha_mu = 2(x-1) for N(>S) ~ S^-x; C1(alpha_mu) = C_dd + 2 alpha_mu C_dk + alpha_mu^2 C_kk",
                                rsd="W_rsd = -int n_chi f T_lin j_1''; C1(rsd) = C_dd + 2 C_dr + C_rr"))
    import camb
    out["camb_version"] = camb.__version__
    out["numpy"] = np.__version__

    # ---------------- V1 analytic power-law identity (background from CAMB only for the chi grid of the radio n(z))
    pars, bg, pk_lin, _, sig8, om = camb_background_and_pk(nonlinear=False)
    out["camb_sigma8_0"] = sig8
    out["camb_omega_m"] = om
    out["sigma8_reference"] = dict(value=0.8102, locator=PLANCK18_LOCATOR)
    kg = kgrid_log(1e-6, 5.0, 801)
    v1 = []
    tpl = lambda k, z: np.full(np.shape(np.atleast_1d(z)), 1.0 / k)  # sqrt(A k^-2), A = 1
    cases = {"gauss_chi2000_sig500": lambda z: np.exp(-0.5 * ((bg.chi_of_z(z) - 2000.0) / 500.0) ** 2) / bg.hubble_over_c(z),
             "TN16": lambda z: nz_shape("TN16", z), "DZ10": lambda z: nz_shape("DZ10", z)}
    for name, fn in cases.items():
        zhi = dz10_root() if name == "DZ10" else ZMAX
        kern = Kernel(bg, fn, lambda z: bias("unit", z), z_hi=zhi)
        chi_f = np.linspace(kern.chi_lo, kern.chi_hi, 400001)
        for ell in (1, 2, 5):
            w = windows_for(kern, kg, tpl, ell, per_period=a.per_period)["density"]
            num = cl_from_windows(kg, w)
            ref = realspace_powerlaw_m2(chi_f, kern.n_chi(chi_f), ell)
            v1.append(dict(case=name, ell=ell, kspace=num, realspace_exact=ref, rel_err=num / ref - 1.0))
    out["V1_powerlaw_identity"] = dict(description="P = k^-2: k-space integrator vs exact real-space double integral",
                                       k_range=[1e-6, 5.0], nk=801, results=v1)
    print("V1", [(r["case"], r["ell"], round(r["rel_err"], 6)) for r in v1], flush=True)

    # ---------------- V2 Limber at high l
    t_lin = t_from_interp(pk_lin)
    p_lin = p_from_interp(pk_lin)
    v2 = []
    for nzn, bn in (("TN16", "NT15cap"), ("H08", "H08beff")):
        kern = Kernel(bg, lambda z, n=nzn: nz_shape(n, z), lambda z, b=bn: bias(b, z))
        for ell in (100, 300):
            kk = kgrid_log((ell + 0.5) / kern.chi_hi * 0.3, min(5.0, (ell + 0.5) / 20.0), 601)
            w = windows_for(kern, kk, t_lin, ell, per_period=a.per_period)["density"]
            ex = cl_from_windows(kk, w)
            li = limber(kern, ell, p_lin)
            v2.append(dict(nz=nzn, bias=bn, ell=ell, exact=ex, limber=li, rel_diff=ex / li - 1.0))
    out["V2_limber_high_ell"] = v2
    print("V2", [(r["nz"], r["ell"], round(r["rel_diff"], 5)) for r in v2], flush=True)

    # ---------------- V3 CAMB number counts (massless neutrinos so delta_tot = delta_nonu), l = 2..10, constant b = 2
    lmax3 = 10
    _, bg0, pk0, _, _, _ = camb_background_and_pk(nonlinear=False, massless_nu=True)
    t0l = t_from_interp(pk0)
    v3 = []
    for nzn, (zc, sg) in GAUSS_V3.items():
        kern = Kernel(bg0, lambda z, n=nzn: gauss_nz(n, z), lambda z: bias("const2", z), z_lo=max(zc - 6 * sg, 1e-3), z_hi=zc + 6 * sg)
        cam_d = camb_counts_cls(nzn, 2.0, lmax3, ("counts_density",))
        cam_dr = camb_counts_cls(nzn, 2.0, lmax3, ("counts_density", "counts_redshift"))
        xs = 0.5
        cam_dl = camb_counts_cls(nzn, 2.0, lmax3, ("counts_density", "counts_lensing"), x_slope=xs)
        cam_all = camb_counts_cls(nzn, 2.0, lmax3, ("counts_density", "counts_redshift", "counts_lensing", "counts_velocity",
                                                     "counts_radial", "counts_timedelay", "counts_ISW", "counts_potential"), x_slope=1.0)
        cam_drl = camb_counts_cls(nzn, 2.0, lmax3, ("counts_density", "counts_redshift", "counts_lensing"), x_slope=1.0)
        for ell in range(2, lmax3 + 1):
            kk = kgrid_log(1e-5, 2.0, 401)
            w = windows_for(kern, kk, t0l, ell, terms=("density", "rsd", "kappa"), per_period=a.per_period)
            dd = cl_from_windows(kk, w["density"])
            dr = cl_from_windows(kk, w["density"] + w["rsd"])
            amu = 2.0 * (xs - 1.0)
            dl = cl_from_windows(kk, w["density"] + amu * w["kappa"])
            v3.append(dict(nz=nzn, ell=ell, density=dict(mine=dd, camb=cam_d[ell], rel=dd / cam_d[ell] - 1.0),
                           density_rsd=dict(mine=dr, camb=cam_dr[ell], rel=dr / cam_dr[ell] - 1.0),
                           density_magnification_x0p5=dict(mine=dl, camb=cam_dl[ell], rel=dl / cam_dl[ell] - 1.0),
                           camb_all_terms_over_density_rsd_lensing_x1=cam_all[ell] / cam_drl[ell] - 1.0))
        print("V3", nzn, [(r["ell"], round(r["density"]["rel"], 5), round(r["density_rsd"]["rel"], 5),
                           round(r["density_magnification_x0p5"]["rel"], 5)) for r in v3 if r["nz"] == nzn], flush=True)
    out["V3_camb_number_counts"] = dict(description="CAMB 2.0.5 SplinedSourceWindow non-Limber C_l (raw), massless neutrinos, b=2, "
                                        "smooth Gaussian test windows in z (z0, sigma) = (0.5, 0.15), (1.0, 0.30); "
                                        "magnification test with x=0.5 (dlog10Ndm=0.2, coefficient 5s-2=-1); "
                                        "last column: CAMB all GR source terms vs density+RSD+lensing at x=1 (size of omitted velocity/potential terms)",
                                        results=v3)
    v3sys = v3_low_l_systematic(v3)
    out["V3_low_l_systematic"] = v3sys
    print("V3 systematic", v3sys["worst_window"], round(v3sys["s_abs_rel_l1"], 5), "factor_up", round(v3sys["factor_up"], 5), flush=True)

    # ---------------- production l = 1
    nzs = ("TN16", "DZ10", "H08")
    biases = ("NT15", "NT15cap", "const2", "const3", "H08beff")
    combos = PRIMARY if a.quick else list(itertools.product(nzs, biases))
    kg1 = kgrid_log(a.kmin, a.kmax, a.nk)
    pk_variants = {"linear": (t_lin, t_lin)}
    _, _, pk_nl, _, _, _ = camb_background_and_pk(nonlinear=True)
    pk_variants["hmcode2020"] = (t_from_interp(pk_nl), t_lin)
    # literal TF7 form: D(z) sqrt(P_lin(k,0))
    t_growth = lambda k, z: bg.growth(np.atleast_1d(z)) * math.sqrt(max(pk_lin.P(0.0, k), 0.0))
    prod, windows = {}, {}
    for nzn, bn in combos:
        zhi = dz10_root() if nzn == "DZ10" else ZMAX
        kern = Kernel(bg, lambda z, n=nzn: nz_shape(n, z), lambda z, b=bn: bias(b, z), z_hi=zhi)
        key = f"{nzn}|{bn}"
        row = dict(nz=nzn, bias=bn, primary=(nzn, bn) in PRIMARY, z_support=[0.0, zhi])
        for pv, (tt, tl) in pk_variants.items():
            w = windows_for(kern, kg1, tt, 1, terms=("density", "rsd", "kappa"), per_period=a.per_period, t_lin_of_kz=tl)
            windows[(key, pv)] = w["density"]
            cdd = cl_from_windows(kg1, w["density"])
            cdr = cl_from_windows(kg1, w["density"], w["rsd"])
            crr = cl_from_windows(kg1, w["rsd"])
            cdk = cl_from_windows(kg1, w["density"], w["kappa"])
            ckk = cl_from_windows(kg1, w["kappa"])
            mag = {f"{am:+.1f}": cdd + 2 * am * cdk + am * am * ckk for am in (-0.6, -0.3, 0.3, 0.6)}
            row[pv] = dict(C1_density=cdd, C1_density_plus_rsd=cdd + 2 * cdr + crr, C_dr=cdr, C_rr=crr, C_dk=cdk, C_kk=ckk,
                           C1_density_magnification_by_alpha_mu=mag,
                           max_rel_change_rsd=(2 * cdr + crr) / cdd,
                           max_rel_change_magnification_abs_alpha_le_0p6=max(abs(v / cdd - 1.0) for v in mag.values()),
                           rms_dipole_per_component=math.sqrt(3 * cdd / (4 * math.pi)),
                           expected_dipole_amplitude_rms=math.sqrt(9 * cdd / (4 * math.pi)),
                           frac_kgt0p1=cl_from_windows(kg1[kg1 >= 0.1], w["density"][kg1 >= 0.1]) / cdd if (kg1 >= 0.1).sum() > 2 else 0.0)
        # literal TF7 growth form (linear) and low-z split
        wg = windows_for(kern, kg1, t_growth, 1, per_period=a.per_period)["density"]
        row["linear_TF7_growth_form_C1"] = cl_from_windows(kg1, wg)
        for zlo, zhi2, tag in ((0.0, 0.1, "z_lt_0p1_only"), (0.1, zhi, "z_ge_0p1_only")):
            kz = Kernel(bg, lambda z, n=nzn, lo=zlo, hi=zhi2: np.where((z >= lo) & (z < hi), nz_shape(n, z), 0.0),
                        lambda z, b=bn: bias(b, z), z_lo=0.0, z_hi=zhi)
            kz.norm = kern.norm  # same normalisation as the full sample: these are the parts of the full kernel
            wz = windows_for(kz, kg1, t_lin, 1, per_period=a.per_period)["density"]
            row[f"linear_C1_{tag}"] = cl_from_windows(kg1, wz)
        prod[key] = row
        print("C1", key, "lin=%.4e nl=%.4e tf7=%.4e" % (row["linear"]["C1_density"], row["hmcode2020"]["C1_density"],
                                                          row["linear_TF7_growth_form_C1"]), flush=True)
    out["C1_l1"] = prod
    out["k_grid"] = dict(kmin=a.kmin, kmax=a.kmax, nk=len(kg1), per_period=a.per_period)

    # ---------------- V4 convergence on one bracket (DZ10 has n(0) > 0: the UV-sensitive case) and TN16
    v4 = []
    for nzn, bn in (("TN16", "NT15cap"), ("DZ10", "NT15")):
        zhi = dz10_root() if nzn == "DZ10" else ZMAX
        kern = Kernel(bg, lambda z, n=nzn: nz_shape(n, z), lambda z, b=bn: bias(b, z), z_hi=zhi)
        base = prod[f"{nzn}|{bn}"]["linear"]["C1_density"]
        for kmax, nk, pp in ((a.kmax, 2 * a.nk - 1, a.per_period), (a.kmax, a.nk, 2 * a.per_period), (10.0, a.nk + 200, a.per_period),
                             (0.5, a.nk, a.per_period)):
            kk = kgrid_log(a.kmin, kmax, nk)
            w = windows_for(kern, kk, t_lin, 1, per_period=pp)["density"]
            c = cl_from_windows(kk, w)
            v4.append(dict(nz=nzn, bias=bn, kmax=kmax, nk=len(kk), per_period=pp, C1=c, rel_to_production=c / base - 1.0))
    out["V4_convergence"] = v4
    print("V4", [(r["nz"], r["kmax"], r["nk"], r["per_period"], round(r["rel_to_production"], 6)) for r in v4], flush=True)

    # ---------------- bracket envelope and differential (resolved minus compact) bound, linear and nonlinear
    env = {}
    for pv in pk_variants:
        keys = list(prod)
        vals = {k: prod[k][pv]["C1_density"] for k in keys}
        prim = {k: v for k, v in vals.items() if prod[k]["primary"]}
        diffs = []
        for k1, k2 in itertools.combinations(keys, 2):
            d = cl_from_windows(kg1, windows[(k1, pv)] - windows[(k2, pv)])
            diffs.append((d, k1, k2))
        diffs.sort()
        env[pv] = dict(primary_min=min(prim.values()), primary_max=max(prim.values()),
                       primary_argmin=min(prim, key=prim.get), primary_argmax=max(prim, key=prim.get),
                       extended_min=min(vals.values()), extended_max=max(vals.values()),
                       extended_argmax=max(vals, key=vals.get),
                       differential_pair_max=dict(C1=diffs[-1][0], pair=[diffs[-1][1], diffs[-1][2]]),
                       differential_pair_min=dict(C1=diffs[0][0], pair=[diffs[0][1], diffs[0][2]]),
                       differential_triangle_bound_4max=4.0 * max(vals.values()),
                       note=("differential = C1 of [W_i - W_j] for two bracket members, i.e. the l=1 power of "
                             "delta_resolved - delta_compact if each class follows one bracket member; "
                             "4 max C1 is the Minkowski bound (sqrt(C_i)+sqrt(C_j))^2 over the extended set; "
                             "V4 is the numerical convergence of the integrator only; the unexplained V3 low-l offset to CAMB "
                             "is carried separately in with_V3_low_l_systematic"))
        env[pv]["with_V3_low_l_systematic"] = apply_v3_systematic(env[pv], v3sys)
    out["envelope"] = env
    sn = shot_noise_from_carrier()
    out["shot_noise_R65_NVSS"] = dict(sn, input=str(CARRIER), input_sha256=CARRIER_SHA,
                                      note=("R106's closed form Cov = Cov_{C1=0} + df^2 (3 C1/4pi) I_2 uses the clustering-only C1 "
                                            "of g_diff; Poisson noise is generated by the multinomial placement inside Cov_{C1=0}. "
                                            "The with-shot-noise numbers are C1 + 1/Nbar for the count fields (TN16 Eq. 3.4) and "
                                            "C1_diff + 1/Nbar_off + 1/Nbar_diag for g_diff; feeding them into p(C1) double counts Poisson noise."))
    wsn = {}
    for pv in pk_variants:
        e = env[pv]
        wsn[pv] = dict(
            count_field_integrated_ge20=dict(shot_noise_free=[e["extended_min"], e["extended_max"]],
                                             with_shot_noise=[e["extended_min"] + sn["selections"]["integrated_ge20"]["shot_noise_1_over_Nbar"],
                                                              e["extended_max"] + sn["selections"]["integrated_ge20"]["shot_noise_1_over_Nbar"]]),
            g_diff=dict(shot_noise_free=[0.0, e["differential_pair_max"]["C1"], e["differential_triangle_bound_4max"]],
                        with_shot_noise=[sn["g_diff_shot_noise"], e["differential_pair_max"]["C1"] + sn["g_diff_shot_noise"],
                                         e["differential_triangle_bound_4max"] + sn["g_diff_shot_noise"]],
                        labels=["identical classes (C1_diff = 0)", "max over bracket pairs", "Minkowski bound 4 max C1"]))
        fu = v3sys["factor_up"]
        for blk, noise in ((wsn[pv]["count_field_integrated_ge20"], sn["selections"]["integrated_ge20"]["shot_noise_1_over_Nbar"]),
                           (wsn[pv]["g_diff"], sn["g_diff_shot_noise"])):
            blk["shot_noise_free_x_V3_factor_up"] = [f * fu for f in blk["shot_noise_free"]]
            blk["with_shot_noise_and_V3_factor_up"] = [f * fu + noise for f in blk["shot_noise_free"]]
        wsn[pv]["V3_low_l_systematic_factor_up"] = fu
    out["C1_forms_for_R106"] = wsn
    out["elapsed_s"] = time.time() - t0
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, indent=1, default=float) + "\n")
    print("wrote", a.out, "elapsed", round(out["elapsed_s"], 1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
