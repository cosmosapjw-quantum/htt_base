"""R54 perturbed-FLRW (linear LCDM) cosmic-variance body for window velocity multipoles.

Purpose: supply the declared physical body K0 that the five-view gauge Q,
support utilization F, exceedance Pi and depth transport G_F need for the
low-redshift apparent-Hubble multipoles (monopole, dipole, STF quadrupole per
depth window). R52 had none ("Q/F/Pi: UNAVAILABLE"; "no calibrated depth law").

Model (linear theory, z = 0, full-sky isotropic sampling inside each window):

R54-EQ-10  u(r n) = n.v,   u_lm(r) = 4 pi f H0 i^l int d^3k/(2pi)^3 (delta_k/k) j_l'(kr) Y*_lm(k)
R54-EQ-11  C_l^{w w'} = (2/pi) (f H0)^2 int dk P(k) I_l^w(k) I_l^{w'}(k),
           I_l^w(k) = int dr Wcal_w(r) j_l'(kr)
           Wcal_w(r) [1/Mpc]: radial weight of the apparent-H estimator,
           theta_w = sum_i Wcal-weighted u_i / d_i-type average, so C_l is in (km/s/Mpc)^2.
R54-EQ-12  Cartesian blocks: Var(H_w)   = C_0 / (4 pi)
                             Cov(D_i)   = delta_ij (3 / (4 pi)) C_1
                             Cov(q_a)   = delta_ab (15 / (8 pi)) C_2   (orthonormal STF5)

Limits used as tests: k r -> 0 gives <B_i^2> = (f H0)^2/(6 pi^2) int dk P (the 1-D
velocity dispersion) for a point window; a uniform flow V gives D = V int Wcal dr.

The harmonic body above is IDEAL-SKY. The exact body for a catalogue is O C_uu O^T
with the catalogue operator O; mask and anisotropic sampling couple l = 0, 1, 2 there:

R54-EQ-30  Psi_perp(r) = (f H0)^2/(2 pi^2) int dk P(k) j_1(kr)/(kr)
           Psi_par(r)  = (f H0)^2/(2 pi^2) int dk P(k) [j_0(kr) - 2 j_1(kr)/(kr)] = d(r Psi_perp)/dr
R54-EQ-31  C_uu(i,j) = Psi_perp(r_ij) (n_i.n_j) + [Psi_par(r_ij) - Psi_perp(r_ij)] (n_i.rhat_ij)(n_j.rhat_ij),
           r_ij = |r_i n_i - r_j n_j|, rhat_ij = (r_i n_i - r_j n_j)/r_ij,  C_uu(i,i) = Psi(0) = sigma_v,1D^2
R54-EQ-33  flat LCDM: chi_hat(z) = int_0^z dz'/E(z'),  y(z) = c (1+z) chi_hat = H0 d_L(z)  [km/s, H0-free],
           g(z) = [(1+z)/(E(z) chi_hat(z)) - 1]/c : response of ln[y(z_obs)/d_L,obs] to a source radial
           velocity u (Doppler shift of z_obs minus the (1+u/c)^2 factor of the observed d_L).
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Sequence

import numpy as np
from scipy.special import spherical_jn

CARTESIAN_FACTOR = {0: 1.0 / (4.0 * math.pi), 1: 3.0 / (4.0 * math.pi), 2: 15.0 / (8.0 * math.pi)}
BLOCK_DIM = {0: 1, 1: 3, 2: 5}


@dataclass(frozen=True)
class RadialWindow:
    """Radial weight Wcal(r) on a grid; ``norm`` = int Wcal dr (response to a uniform flow)."""

    r_mpc: np.ndarray
    weight_per_mpc: np.ndarray

    def __post_init__(self) -> None:
        r, w = np.asarray(self.r_mpc, float), np.asarray(self.weight_per_mpc, float)
        if r.ndim != 1 or r.shape != w.shape or r.size < 8 or (np.diff(r) <= 0).any() or r[0] <= 0:
            raise ValueError("window grid must be 1-D, increasing, positive")
        if not np.isfinite(w).all() or (w < 0).any() or w.sum() <= 0:
            raise ValueError("window weights must be finite, non-negative and non-zero")

    @property
    def norm(self) -> float:
        return float(np.trapezoid(self.weight_per_mpc, self.r_mpc))


def gaussian_window(r_center_mpc: float, sigma_r_mpc: float, norm_per_mpc: float, n: int = 400) -> RadialWindow:
    """Gaussian radial weight truncated to r > 0 and rescaled so that int Wcal dr = norm."""
    if min(r_center_mpc, sigma_r_mpc, norm_per_mpc) <= 0:
        raise ValueError("window parameters must be positive")
    lo = max(r_center_mpc - 5.0 * sigma_r_mpc, 1e-3 * sigma_r_mpc)
    r = np.linspace(lo, r_center_mpc + 5.0 * sigma_r_mpc, n)
    w = np.exp(-0.5 * ((r - r_center_mpc) / sigma_r_mpc) ** 2)
    w *= norm_per_mpc / np.trapezoid(w, r)
    return RadialWindow(r, w)


def window_integral(ell: int, k_per_mpc: np.ndarray, window: RadialWindow) -> np.ndarray:
    """I_l^w(k) = int dr Wcal(r) j_l'(k r) (R54-EQ-11), dimension 1/Mpc."""
    if ell not in BLOCK_DIM:
        raise ValueError("ell must be 0, 1 or 2")
    k = np.asarray(k_per_mpc, float)
    x = np.outer(k, window.r_mpc)
    return np.trapezoid(spherical_jn(ell, x, derivative=True) * window.weight_per_mpc[None, :], window.r_mpc, axis=1)


def growth_rate(omega_m: float, gamma: float = 0.55) -> float:
    """f = Omega_m^gamma at z = 0."""
    if not 0 < omega_m <= 1:
        raise ValueError("omega_m in (0, 1] required")
    return omega_m**gamma


def harmonic_cosmic_cov(ell: int, k_per_mpc: np.ndarray, pk_mpc3: np.ndarray, windows: Sequence[RadialWindow],
                        f_growth: float, h0_km_s_mpc: float) -> np.ndarray:
    """C_l^{w w'} of R54-EQ-11 in (km/s/Mpc)^2 for a list of windows (log-k trapezoid)."""
    k, p = np.asarray(k_per_mpc, float), np.asarray(pk_mpc3, float)
    if k.ndim != 1 or k.shape != p.shape or (np.diff(k) <= 0).any() or k[0] <= 0 or (p < 0).any():
        raise ValueError("k must be increasing positive and P non-negative")
    ints = np.array([window_integral(ell, k, w) for w in windows])
    lnk = np.log(k)
    pref = (2.0 / math.pi) * (f_growth * h0_km_s_mpc) ** 2
    out = np.empty((len(windows), len(windows)))
    for a in range(len(windows)):
        for b in range(a, len(windows)):
            out[a, b] = out[b, a] = pref * np.trapezoid(k * p * ints[a] * ints[b], lnk)
    return out


def cartesian_cosmic_cov(ell: int, c_ell: np.ndarray) -> np.ndarray:
    """Kronecker lift of C_l^{w w'} to the (window x Cartesian component) covariance (R54-EQ-12)."""
    c = np.asarray(c_ell, float)
    return np.kron(CARTESIAN_FACTOR[ell] * c, np.eye(BLOCK_DIM[ell]))


def stacked_window_body(k_per_mpc: np.ndarray, pk_mpc3: np.ndarray, windows: Sequence[RadialWindow],
                        f_growth: float, h0_km_s_mpc: float) -> np.ndarray:
    """(9W x 9W) ideal-sky cosmic covariance in the R36 ordering [H, D(3), STF5] per window.

    Different l are uncorrelated for an isotropic full-sky window; cross-window
    blocks of equal l are kept in full.
    """
    nw = len(windows)
    out = np.zeros((9 * nw, 9 * nw))
    sl = {0: [0], 1: [1, 2, 3], 2: [4, 5, 6, 7, 8]}
    for ell in (0, 1, 2):
        c = CARTESIAN_FACTOR[ell] * harmonic_cosmic_cov(ell, k_per_mpc, pk_mpc3, windows, f_growth, h0_km_s_mpc)
        for a in range(nw):
            for b in range(nw):
                for j in sl[ell]:
                    out[9 * a + j, 9 * b + j] = c[a, b]
    return out


def point_velocity_dispersion_1d(k_per_mpc: np.ndarray, pk_mpc3: np.ndarray, f_growth: float,
                                 h0_km_s_mpc: float, window_fn: Callable[[np.ndarray], np.ndarray] | None = None) -> float:
    """sigma_v,1D^2 = (f H0)^2/(6 pi^2) int dk P(k) W^2(k) in (km/s)^2 (reference limit)."""
    k, p = np.asarray(k_per_mpc, float), np.asarray(pk_mpc3, float)
    w2 = 1.0 if window_fn is None else np.asarray(window_fn(k), float) ** 2
    return float((f_growth * h0_km_s_mpc) ** 2 / (6.0 * math.pi**2) * np.trapezoid(k * p * w2, np.log(k)))


# ------------------------------------------------- exact catalogue body (R54-EQ-30/31/33)
def velocity_correlation(k_per_mpc: np.ndarray, pk_mpc3: np.ndarray, f_growth: float, h0_km_s_mpc: float,
                         r_mpc: np.ndarray, n_k: int = 120000, damping_mpc: float = 0.0) -> tuple[np.ndarray, np.ndarray]:
    """Linear-theory velocity correlation functions (Psi_perp, Psi_par) in (km/s)^2 on ``r_mpc`` (R54-EQ-30).

    P(k) is interpolated in log-log onto a fine logarithmic grid so that j_l(kr) stays resolved at the
    largest separation. ``damping_mpc`` = sigma_u multiplies P by sinc^2(k sigma_u) (non-linear damping variant).
    """
    k, p = np.asarray(k_per_mpc, float), np.asarray(pk_mpc3, float)
    r = np.atleast_1d(np.asarray(r_mpc, float))
    good = (k > 0) & (p > 0) & np.isfinite(p)
    if good.sum() < 16 or (r < 0).any() or f_growth <= 0 or h0_km_s_mpc <= 0 or damping_mpc < 0:
        raise ValueError("velocity_correlation needs a positive P(k) table, r >= 0 and positive f, H0")
    lk = np.linspace(math.log(k[good][0]), math.log(k[good][-1]), int(n_k))
    kf = np.exp(lk)
    pf = np.exp(np.interp(lk, np.log(k[good]), np.log(p[good])))
    if damping_mpc > 0:
        pf = pf * np.sinc(kf * damping_mpc / math.pi) ** 2
    if r.max() * kf[-1] * (lk[1] - lk[0]) > 0.5:
        raise ValueError("k grid too coarse for the largest separation; raise n_k")
    weight = pf * kf * (lk[1] - lk[0])                    # dk P(k) on the log grid
    weight[0] *= 0.5
    weight[-1] *= 0.5
    norm = (f_growth * h0_km_s_mpc) ** 2 / (2.0 * math.pi**2)
    perp, par = np.empty_like(r), np.empty_like(r)
    for a in range(0, r.size, 64):
        x = np.outer(r[a:a + 64], kf)
        small = x < 1.0e-3
        xs = np.where(small, 1.0, x)
        j0 = np.where(small, 1.0 - x * x / 6.0, np.sin(xs) / xs)
        j1x = np.where(small, 1.0 / 3.0 - x * x / 30.0, (np.sin(xs) - xs * np.cos(xs)) / xs**3)
        perp[a:a + 64] = norm * (j1x @ weight)
        par[a:a + 64] = norm * ((j0 - 2.0 * j1x) @ weight)
    return perp, par


def radial_velocity_covariance_product(op: np.ndarray, nhat: np.ndarray, r_mpc: np.ndarray, r_grid: np.ndarray,
                                       tables: Sequence[tuple[np.ndarray, np.ndarray]], chunk: int = 400) -> list[np.ndarray]:
    """O C_uu O^T for the radial velocities u_i = n_i.v(r_i n_i) of a catalogue, one matrix per table (R54-EQ-31).

    ``op`` (m x N) acts on the N radial velocities; ``tables`` holds (Psi_perp, Psi_par) sampled on ``r_grid``.
    The dense N x N matrix is never stored: rows are accumulated in chunks.
    """
    op, n, r = np.asarray(op, float), np.asarray(nhat, float), np.asarray(r_mpc, float)
    grid = np.asarray(r_grid, float)
    if op.ndim != 2 or n.shape != (op.shape[1], 3) or r.shape != (op.shape[1],) or (r <= 0).any():
        raise ValueError("operator, directions and distances are inconsistent")
    if np.abs(np.einsum("ij,ij->i", n, n) - 1.0).max() > 1e-9:
        raise ValueError("directions must be unit vectors")
    if grid[0] != 0.0 or (np.diff(grid) <= 0).any() or 2.0 * r.max() > grid[-1]:
        raise ValueError("r_grid must start at 0, increase and cover twice the largest distance")
    out = [np.zeros((op.shape[0], op.shape[0])) for _ in tables]
    opt = np.ascontiguousarray(op.T)
    for a in range(0, r.size, chunk):
        sl = slice(a, min(a + chunk, r.size))
        cos = n[sl] @ n.T
        ri, rj = r[sl, None], r[None, :]
        rij = np.sqrt(np.maximum(ri * ri + rj * rj - 2.0 * ri * rj * cos, 0.0))
        safe = np.where(rij > 0.0, rij, 1.0)
        mm = (ri - rj * cos) * (ri * cos - rj) / safe**2          # (n_i.rhat_ij)(n_j.rhat_ij)
        for acc, (perp, par) in zip(out, tables):
            pp = np.interp(rij, grid, perp)
            cuu = pp * cos + (np.interp(rij, grid, par) - pp) * mm
            acc += op[:, sl] @ (cuu @ opt)
    return [0.5 * (m + m.T) for m in out]


def flat_lcdm_distance_factors(z: np.ndarray, omega_m: float, n_grid: int = 6001) -> dict:
    """chi_hat = H0 d_C/c, y = H0 d_L in km/s, E(z) and the velocity response g(z) of ln[y(z_obs)/d_L,obs] (R54-EQ-33)."""
    z = np.asarray(z, float)
    if (z <= 0).any() or not 0.0 < omega_m < 1.0:
        raise ValueError("redshifts must be positive and 0 < omega_m < 1")
    zg = np.linspace(0.0, float(z.max()) * 1.001, int(n_grid))
    inv_e = 1.0 / np.sqrt(omega_m * (1.0 + zg) ** 3 + 1.0 - omega_m)
    steps = 0.5 * (inv_e[1:] + inv_e[:-1]) * np.diff(zg)
    chi_hat = np.interp(z, zg, np.concatenate([[0.0], np.cumsum(steps)]))
    e_z = np.sqrt(omega_m * (1.0 + z) ** 3 + 1.0 - omega_m)
    c = 299792.458
    return {"chi_hat": chi_hat, "y_km_s": c * (1.0 + z) * chi_hat, "E": e_z, "g_per_km_s": ((1.0 + z) / (e_z * chi_hat) - 1.0) / c}
