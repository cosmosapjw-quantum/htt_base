"""R54-L03 count dipoles: clustering body (R54-EQ-32), Poisson dipole likelihood and mask identity.

  growth_factor          linear growth D(z) of flat LCDM normalised to D(0) = 1
  ho_nz                  gamma-shaped N(z) of the Ho et al. 2008 form, dN/dz ~ z^alpha exp(-alpha z / z_*)
  dipole_clustering_cl1  C_1 = (2/pi) int dk k^2 P(k) [int dchi W(chi) b(z) D(z) j_1(k chi)]^2   (R54-EQ-32, no Limber)
  dipole_axis_variance   Var(d_i) = (3/(4 pi)) C_1 for delta(n) = d.n
  poisson_dipole_fit     maximum-likelihood dipole of pixel counts N_p ~ Poisson(M s_p (1 + d.n_p)) with its Hessian covariance
  mask_hash              sha256 of the set of pixels an estimator uses (data and mocks must share it; gate MG-L04)
"""
from __future__ import annotations

import hashlib
import math
from typing import Callable

import numpy as np
from scipy import integrate, optimize, special

C_KM_S = 299792.458


def growth_factor(z: np.ndarray, omega_m: float) -> np.ndarray:
    """D(z)/D(0) for flat LCDM: D(a) ~ H(a) int_0^a da' / (a' H(a'))^3."""
    z = np.atleast_1d(np.asarray(z, float))
    if np.any(z < 0) or not 0.0 < omega_m < 1.0:
        raise ValueError("z >= 0 and 0 < Omega_m < 1 required")

    def e(a: float) -> float:
        return math.sqrt(omega_m / a**3 + 1.0 - omega_m)

    def d(a: float) -> float:
        return e(a) * integrate.quad(lambda x: 1.0 / (x * e(x)) ** 3, 0.0, a, limit=200)[0]

    d0 = d(1.0)
    return np.array([d(1.0 / (1.0 + zz)) / d0 for zz in z])


def ho_nz(z: np.ndarray, z_star: float, alpha: float) -> np.ndarray:
    """Normalised dN/dz = z^alpha exp(-alpha z / z_*) (alpha / z_*)^(alpha + 1) / Gamma(alpha + 1)."""
    z = np.asarray(z, float)
    if z_star <= 0 or alpha <= -1:
        raise ValueError("z_* > 0 and alpha > -1 required")
    lam = alpha / z_star
    return np.where(z > 0, np.clip(z, 0.0, None) ** alpha * np.exp(-lam * z) * lam ** (alpha + 1.0) / special.gamma(alpha + 1.0), 0.0)


def comoving_distance(z: np.ndarray, omega_m: float, h0: float) -> np.ndarray:
    zg = np.linspace(0.0, float(np.max(z)) * 1.0001 + 1e-9, 20001)
    inv_e = 1.0 / np.sqrt(omega_m * (1.0 + zg) ** 3 + 1.0 - omega_m)
    chi = np.concatenate([[0.0], np.cumsum(0.5 * (inv_e[1:] + inv_e[:-1]) * np.diff(zg))]) * C_KM_S / h0
    return np.interp(z, zg, chi)


def dipole_clustering_cl1(k: np.ndarray, pk: np.ndarray, z: np.ndarray, dndz: np.ndarray, bias: Callable[[np.ndarray], np.ndarray],
                          omega_m: float, h0: float, z_min: float = 0.0) -> float:
    """C_1 of the projected galaxy overdensity for the redshift distribution dndz on the grid z (R54-EQ-32, exact j_1)."""
    z, dndz = np.asarray(z, float), np.asarray(dndz, float)
    sel = z >= z_min
    if sel.sum() < 10 or np.any(dndz < 0):
        raise ValueError("redshift grid too short or negative dN/dz")
    zz, w = z[sel], dndz[sel]
    w = w / np.trapezoid(w, zz)                       # normalised over the selected range: W(chi) dchi = n(z) dz
    chi = comoving_distance(zz, omega_m, h0)
    kern = w * np.asarray(bias(zz), float) * growth_factor(zz, omega_m)
    k, pk = np.asarray(k, float), np.asarray(pk, float)
    integ = np.array([np.trapezoid(kern * special.spherical_jn(1, kk * chi), zz) for kk in k])
    return float(2.0 / math.pi * np.trapezoid(k**2 * pk * integ**2, k))


def dipole_axis_variance(cl1: float) -> float:
    """Var(d_i) = (3/(4 pi)) C_1 for delta(n) = d.n (R54-EQ-32)."""
    if cl1 < 0:
        raise ValueError("C_1 must be non-negative")
    return 3.0 * cl1 / (4.0 * math.pi)


def poisson_dipole_fit(counts: np.ndarray, expect: np.ndarray, nvec: np.ndarray) -> dict:
    """ML of N_p ~ Poisson(M e_p (1 + d.n_p)) over pixels with e_p > 0; covariance from the expected information."""
    counts, expect, nvec = np.asarray(counts, float), np.asarray(expect, float), np.asarray(nvec, float)
    use = expect > 0
    n, e, v = counts[use], expect[use], nvec[use]

    def nll(x: np.ndarray) -> float:
        lam = x[0] * e * (1.0 + v @ x[1:])
        if np.any(lam <= 0):
            return 1e300
        return float(np.sum(lam - n * np.log(lam)))

    x0 = np.array([n.sum() / e.sum(), 0.0, 0.0, 0.0])
    res = optimize.minimize(nll, x0, method="Nelder-Mead", options={"xatol": 1e-12, "fatol": 1e-10, "maxiter": 40000})
    res = optimize.minimize(nll, res.x, method="BFGS", options={"gtol": 1e-9})
    m, d = res.x[0], res.x[1:]
    lam = m * e * (1.0 + v @ d)
    jac = np.column_stack([lam / m, m * e[:, None] * v])            # d lambda / d(M, d)
    info = (jac / lam[:, None]).T @ jac
    cov = np.linalg.inv(info)
    return {"D_icrs": d, "amplitude": float(np.linalg.norm(d)), "monopole": float(m), "cov_D": cov[1:, 1:], "n_pixels": int(use.sum()),
            "n_sources": float(n.sum()), "converged": bool(res.success)}


def mask_hash(used: np.ndarray) -> str:
    """sha256 of the boolean pixel set an estimator uses."""
    return hashlib.sha256(np.packbits(np.asarray(used, bool)).tobytes()).hexdigest()
