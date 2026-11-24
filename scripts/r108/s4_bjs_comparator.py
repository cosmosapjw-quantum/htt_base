"""R108 lane s4: independent BJS Bianchi VII_h comparator for the exact-characteristic line of sight.

Purpose
-------
Handoff S4 / THEORY_FOUNDATIONS TF4 (R107 cloud).  For open dust (Omega_Lambda = Omega_r = 0)
Bianchi VII_h states with Omega_0 in {0.3, 0.5, 0.7} and x in {0.62, 1.0}:

1. build an admissible tilted state today (N = 0, H = 1) whose Lie geometry is the isotropic-limit
   BJS dictionary (``bjs_lie_geometry_today``: a/H = sqrt(1 - Omega_0) e_z, n/H = diag(1/x, 1/x, 0)),
   with a small shear in the BJS mode (only sigma_13, sigma_23 nonzero for the VII_h axis e_z;
   Pontzen & Challinor 2007, MNRAS 380, 1387, sec. 5.1-5.3: "sigma_ij = 0 except for sigma_12,
   sigma_13" with their axis e_1) and the dust tilt that satisfies the momentum (Codazzi)
   constraint exactly (``exact_momentum_divergence`` + ``solve_compensating_tilt_velocity``);
2. evolve it backward with ``evolve_general_tilted_bianchi`` from N = 0 to below
   N_E = -ln(1 + 1100), recording (sigma/H, a/H, n/H)(N) on a dense grid, with constraint and
   open-dust background checks;
3. run ``los_sky`` with ONE optically thick shell at N_E and zero source increment on
   ``healpix_directions(64)``; dT/T = (1 + 4 T)^(1/4) - 1 with the monopole removed;
4. fit amplitude and a full SO(3) rotation of ``bjs_temperature_sky`` (both variants, both
   handedness values) by a global search over the template-axis direction (HEALPix grid) with the
   roll and amplitude solved in closed form (the template has m = +-1 only, McEwen et al. 2006,
   MNRAS 369, 1858, below eq. A22), followed by local optimisation from up to ``n_starts`` grid local
   maxima (fewer when the grid has fewer); an independent global check (``global_check``: a finer
   axis grid with its own local optimisation plus seeded random restarts) records
   max(corr_check) - corr_best;
5. linearity: the map for 2 (sigma/H)_0 against twice the map for (sigma/H)_0.

Pre-registered secondary diagnostic (not part of the acceptance): the BJS template contains the
Doppler terms of the tilted dust at the observer (C1 sin theta terms) and at last scattering
(C1 C2 terms) besides the integrated shear (C3 term); Pontzen & Challinor 2007 sec. 5.7 (eq. 67)
give the shear-to-Doppler ratio (~30 for a common tilt).  The protocol map is the redshift
between normal (hypersurface-orthogonal) observers.  The diagnostic map multiplies it by the exact
Doppler factors of the evolved dust velocity at N = 0 and N_E (ray direction at N_E from
``trace_rays``) and is fitted with the same fitter; it is reported separately.

Units: H-normalised rates per e-fold N = ln a; dT/T dimensionless; angles in radians (degrees
where the key says so).  Sigma convention: sigma^2 = (1/2) sigma_ab sigma^ab (repository,
``evaluate_tilted_constraints``); with only sigma_13 = sigma_31 and sigma_23 = sigma_32 nonzero,
sigma = sqrt(sigma_13^2 + sigma_23^2) =: sigma_perp.  The state is built with
sigma_13 = sigma_23 = sigma_perp / sqrt(2) (phase pi/4), i.e. the "sigma_12 = sigma_13" choice
that Pontzen & Challinor 2007 (sec. 5.3) make "for compatibility with previous studies".

No randomness.  Claim ceiling: numerical comparison only; no family attribution, likelihood or p.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from bass.background.bianchi_types import BianchiAlgebra, _branch_policy_for_type, build_structure_tensor
from bass.background.convention_bridge import exact_momentum_divergence, exact_spatial_ricci_from_compact
from bass.background.general_tilted_evolution import TiltedEvolutionConfig, evolve_general_tilted_bianchi
from bass.background.tilted_bianchi_state import (
    SpeciesFluidCongruence,
    construct_admissible_tilted_state,
    solve_compensating_tilt_velocity,
)
from bass.transport.bjs_bianchi_vii_h import (
    BJSParameters,
    bjs_coefficients,
    bjs_lie_geometry_today,
    bjs_temperature_sky,
    bjs_vorticity_over_hubble,
)
from bass.transport.general_lie_stokes import GeneralLieStokesOperator
from bass.transport.hybrid_los_transfer import (
    LosSourceHistory,
    healpix_directions,
    los_sky,
    pack_geometry14,
    trace_rays,
)

SCHEMA = "htt.r108.s4_bjs_comparator/1"
Z_EMISSION = 1100.0
OMEGAS = (0.3, 0.5, 0.7)
XS = (0.62, 1.0)
VARIANTS = ("mcewen2006", "kogut1997")
HANDEDNESS = (1, -1)
WORK = Path.home() / "Downloads/htt_r108/s4"


# ----------------------------------------------------------------------------- rotations
def rot_z(a: float) -> np.ndarray:
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


def rot_y(b: float) -> np.ndarray:
    c, s = math.cos(b), math.sin(b)
    return np.array([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]])


def euler_zyz(alpha: float, beta: float, gamma: float) -> np.ndarray:
    """Active zyz rotation R = Rz(alpha) Ry(beta) Rz(gamma); a function f is rotated to f(R^-1 n)."""
    return rot_z(alpha) @ rot_y(beta) @ rot_z(gamma)


def axis_rotation(d: np.ndarray) -> np.ndarray:
    """R(d) = Rz(phi_d) Ry(theta_d), which maps e_z onto the unit vector d."""
    d = np.asarray(d, dtype=np.float64) / np.linalg.norm(d)
    return rot_z(math.atan2(d[1], d[0])) @ rot_y(math.acos(max(-1.0, min(1.0, d[2]))))


def euler_from_matrix(R: np.ndarray) -> tuple[float, float, float]:
    """zyz Euler angles (alpha, beta, gamma) of a rotation matrix (beta in [0, pi])."""
    beta = math.acos(max(-1.0, min(1.0, R[2, 2])))
    if abs(math.sin(beta)) > 1e-12:
        alpha = math.atan2(R[1, 2], R[0, 2])
        gamma = math.atan2(R[2, 1], -R[2, 0])
    else:  # gimbal lock: only alpha + gamma (or alpha - gamma) is defined
        alpha = math.atan2(R[1, 0], R[0, 0])
        gamma = 0.0
    return alpha, beta, gamma


def euler_determined(R: np.ndarray, *, sin_tol: float = 1e-3) -> dict:
    """The zyz Euler combination that R determines when |sin(beta)| < sin_tol (review S4-7a).

    R = Rz(alpha) Ry(beta) Rz(gamma).  At beta = pi, Ry(pi) Rz(gamma) = Rz(-gamma) Ry(pi), so
    R = Rz(alpha - gamma) Ry(pi) and only alpha - gamma = atan2(-R01, R11) is determined; at beta = 0 only
    alpha + gamma = atan2(R10, R00).  The separately reported alpha and gamma are then ill-conditioned.
    """
    R = np.asarray(R, dtype=np.float64)
    alpha, beta, gamma = euler_from_matrix(R)
    sb = math.sin(beta)
    out = {"beta_rad": beta, "sin_beta": sb, "sin_tol": sin_tol,
           "alpha_gamma_individually_ill_conditioned": bool(abs(sb) < sin_tol)}
    if abs(sb) >= sin_tol:
        out.update({"combination": None, "value_rad": None})
    elif math.cos(beta) < 0.0:
        v = math.atan2(-R[0, 1], R[1, 1])
        out.update({"combination": "alpha - gamma", "value_rad": v,
                    "from_euler_angles_rad": math.remainder(alpha - gamma, 2.0 * math.pi)})
    else:
        v = math.atan2(R[1, 0], R[0, 0])
        out.update({"combination": "alpha + gamma", "value_rad": v,
                    "from_euler_angles_rad": math.remainder(alpha + gamma, 2.0 * math.pi)})
    return out


def angle_deg(u: np.ndarray, v: np.ndarray) -> float:
    u = np.asarray(u, dtype=np.float64) / np.linalg.norm(u)
    v = np.asarray(v, dtype=np.float64) / np.linalg.norm(v)
    return math.degrees(math.atan2(np.linalg.norm(np.cross(u, v)), float(u @ v)))


def rotation_angle_deg(R: np.ndarray) -> float:
    """Angle of the rotation R (geodesic distance on SO(3) from the identity)."""
    return math.degrees(math.acos(max(-1.0, min(1.0, 0.5 * (np.trace(R) - 1.0)))))


# ----------------------------------------------------------------------------- template on the sky
class TemplateSky:
    """Fast evaluator of ``bjs_temperature_sky`` (per unit (sigma/H)_0) for outward template-frame directions.

    The published template is T(theta0, phi0) = f1(theta0) sin(phi0) + kappa f2(theta0) cos(phi0) in
    incoming-photon angles (mcewen2006: f1 = A + B, f2 = B - A; kogut1997: f1 = A, f2 = B).  A and B are
    computed by ``bjs_coefficients`` on a dense theta grid and interpolated by cubic splines (both vanish
    on the axis); the accuracy against ``bjs_temperature_sky`` is measured by ``validate``.  Sky direction
    m corresponds to the photon direction -m (``bjs_temperature_sky``).
    """

    def __init__(self, omega0: float, x: float, variant: str, *, z_emission: float = Z_EMISSION,
                 n_theta: int = 8193, n_quadrature: int = 2048):
        from scipy.interpolate import CubicSpline

        self.omega0, self.x, self.variant, self.z_emission = float(omega0), float(x), variant, float(z_emission)
        self.n_quadrature = int(n_quadrature)
        p = self.params(1)
        th = np.linspace(0.0, math.pi, int(n_theta))
        A = np.zeros_like(th)
        B = np.zeros_like(th)
        A[1:-1], B[1:-1] = bjs_coefficients(th[1:-1], p)
        if variant == "mcewen2006":
            f1, f2 = A + B, B - A
        elif variant == "kogut1997":
            f1, f2 = A, B
        else:
            raise ValueError(variant)
        self._f1 = CubicSpline(th, f1)
        self._f2 = CubicSpline(th, f2)
        self.n_theta = int(n_theta)

    def params(self, kappa: int) -> BJSParameters:
        return BJSParameters(omega0=self.omega0, x=self.x, z_emission=self.z_emission, handedness=int(kappa),
                             sigma_over_h=1.0, variant=self.variant, n_quadrature=self.n_quadrature)

    def __call__(self, m: np.ndarray, kappa: int) -> np.ndarray:
        m = np.asarray(m, dtype=np.float64)
        theta0 = np.arccos(np.clip(-m[:, 2], -1.0, 1.0))
        phi0 = np.arctan2(-m[:, 1], -m[:, 0])
        return self._f1(theta0) * np.sin(phi0) + kappa * self._f2(theta0) * np.cos(phi0)

    def exact(self, m: np.ndarray, kappa: int) -> np.ndarray:
        return bjs_temperature_sky(np.asarray(m, dtype=np.float64), self.params(kappa))

    def validate(self, m: np.ndarray, kappa: int) -> dict:
        fast = self(m, kappa)
        ex = self.exact(m, kappa)
        return {"max_abs_diff": float(np.max(np.abs(fast - ex))), "max_abs_exact": float(np.max(np.abs(ex))),
                "relative": float(np.max(np.abs(fast - ex)) / np.max(np.abs(ex)))}


# ----------------------------------------------------------------------------- rotation fitter
def _centre(v: np.ndarray) -> np.ndarray:
    return v - v.mean()


def roll_basis(tmpl, m: np.ndarray, kappa: int) -> tuple[np.ndarray, np.ndarray]:
    """S0(m), S90(m) with S(Rz(-gamma) m) = cos(gamma) S0 + sin(gamma) S90 (exact for an m = +-1 template)."""
    return tmpl(m, kappa), tmpl(m @ rot_z(0.5 * math.pi), kappa)


def score_axis(tmpl, kappa: int, d: np.ndarray, dirs: np.ndarray, y_c: np.ndarray) -> tuple[float, float, float]:
    """Best correlation over roll and amplitude for template axis d; returns (corr, amplitude, roll gamma)."""
    m = dirs @ axis_rotation(d)
    s0, s90 = roll_basis(tmpl, m, kappa)
    X = np.stack([_centre(s0), _centre(s90)], axis=1)
    G = X.T @ X
    b = X.T @ y_c
    c = np.linalg.solve(G, b)
    fit = X @ c
    nf = float(np.linalg.norm(fit))
    corr = float(y_c @ fit) / (float(np.linalg.norm(y_c)) * nf) if nf > 0 else 0.0
    return corr, float(math.hypot(c[0], c[1])), float(math.atan2(c[1], c[0]))


def _tangent_frame(d0: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    t = np.array([1.0, 0.0, 0.0]) if abs(d0[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
    e1 = t - (t @ d0) * d0
    e1 /= np.linalg.norm(e1)
    return e1, np.cross(d0, e1)


def _grid_local_maxima(tmpl, kappa: int, nside: int, dc: np.ndarray, yc: np.ndarray):
    """Closed-form score on every HEALPix(nside) template axis; local maxima (8-neighbour) sorted by score."""
    import healpy as hp

    axes = healpix_directions(nside)
    grid = np.array([score_axis(tmpl, kappa, d, dc, yc)[0] for d in axes])
    neigh = hp.get_all_neighbours(nside, np.arange(axes.shape[0]))
    is_max = np.array([all(grid[i] >= grid[j] for j in neigh[:, i] if j >= 0) for i in range(axes.shape[0])])
    return axes, grid, is_max, [i for i in np.argsort(-grid) if is_max[i]]


def _refine_axis(tmpl, kappa: int, d0: np.ndarray, dirs: np.ndarray, y_c: np.ndarray):
    """Nelder-Mead over the template axis in the tangent plane at the unit vector d0 (closed-form roll/amp)."""
    from scipy.optimize import minimize

    e1, e2 = _tangent_frame(d0)

    def neg(u, d0=d0, e1=e1, e2=e2):
        d = d0 + u[0] * e1 + u[1] * e2
        return -score_axis(tmpl, kappa, d / np.linalg.norm(d), dirs, y_c)[0]

    res = minimize(neg, np.zeros(2), method="Nelder-Mead",
                   options={"xatol": 1e-9, "fatol": 1e-15, "maxiter": 4000,
                            "initial_simplex": np.array([[0.0, 0.0], [0.03, 0.0], [0.0, 0.03]])})
    d = d0 + res.x[0] * e1 + res.x[1] * e2
    d /= np.linalg.norm(d)
    corr, amp, gam = score_axis(tmpl, kappa, d, dirs, y_c)
    return d, corr, amp, gam, int(res.nfev)


GLOBAL_CHECK_TOL = 1e-9  # stated before the post-hoc check runs (Nelder-Mead fatol 1e-15 on 1 - corr)


def global_check(tmpl, kappa: int, dirs: np.ndarray, y: np.ndarray, corr_best: float, axis_best, *,
                 check_nside: int = 32, dirs_coarse: np.ndarray | None = None, y_coarse: np.ndarray | None = None,
                 n_refine: int = 8, n_random: int = 8, seed: int = 20261124, basin_sep_deg: float = 5.0,
                 tol: float = GLOBAL_CHECK_TOL) -> dict:
    """Independent check that corr_best (full-map spline correlation of a fit) is the global maximum.

    The check does not reuse the fit's starting points: (i) a finer HEALPix(check_nside) axis grid on
    (dirs_coarse, y_coarse) whose up-to-n_refine best local maxima are each refined by Nelder-Mead on the full
    map, and (ii) n_random seeded uniform random axes, each refined the same way.  Reported:
    corr_check_max - corr_best (<= tol when no better basin is found; a positive excess means the fit missed
    the global maximum) and how many checks converged to the fit's basin (angle <= basin_sep_deg).
    Review S4-3: this replaces the former refined-vs-grid flag, which was true by construction.
    """
    dirs = np.asarray(dirs, dtype=np.float64)
    y_c = _centre(np.asarray(y, dtype=np.float64))
    dc = dirs if dirs_coarse is None else np.asarray(dirs_coarse, dtype=np.float64)
    yc = y_c if y_coarse is None else _centre(np.asarray(y_coarse, dtype=np.float64))
    axes, grid, is_max, order = _grid_local_maxima(tmpl, kappa, check_nside, dc, yc)
    rng = np.random.default_rng(seed)
    rnd = rng.normal(size=(n_random, 3))
    rnd /= np.linalg.norm(rnd, axis=1)[:, None]
    starts = [("finer_grid_local_max", axes[i], float(grid[i])) for i in order[:n_refine]]
    starts += [("random_restart", r, None) for r in rnd]
    rows = []
    for origin, d0, g in starts:
        d, corr, _amp, _gam, nfev = _refine_axis(tmpl, kappa, d0, dirs, y_c)
        rows.append({"origin": origin, "start_axis": np.asarray(d0).tolist(), "start_grid_corr_coarse": g,
                     "axis": d.tolist(), "corr": float(corr), "nfev": nfev,
                     "angle_to_fit_axis_deg": angle_deg(d, axis_best)})
    k = int(np.argmax([r["corr"] for r in rows]))
    cmax = rows[k]["corr"]
    outside = [r["corr"] for r in rows if r["angle_to_fit_axis_deg"] > basin_sep_deg]
    return {
        "method": (f"finer axis grid HEALPix nside {check_nside} on the coarse map, up to {n_refine} of its local maxima "
                   f"refined by Nelder-Mead on the full map, plus {n_random} seeded random restarts (seed {seed}) "
                   "refined the same way; closed-form roll and amplitude"),
        "check_nside": int(check_nside), "n_check_axes": int(axes.shape[0]),
        "n_check_grid_local_maxima": int(is_max.sum()), "n_refined_from_finer_grid": int(min(n_refine, len(order))),
        "n_random_restarts": int(n_random), "seed": int(seed), "check_grid_max_corr_coarse": float(grid.max()),
        "corr_best": float(corr_best), "corr_check_max": float(cmax),
        "corr_check_max_minus_corr_best": float(cmax - corr_best), "tol": float(tol),
        "passes": bool(cmax - corr_best <= tol),
        "angle_check_max_to_fit_axis_deg": float(rows[k]["angle_to_fit_axis_deg"]),
        "n_checks_in_fit_basin": int(sum(r["angle_to_fit_axis_deg"] <= basin_sep_deg for r in rows)),
        "n_checks": len(rows), "basin_sep_deg": float(basin_sep_deg),
        "best_check_corr_outside_fit_basin": float(max(outside)) if outside else None,
        "checks": rows,
    }


def fit_rotation(tmpl, kappa: int, dirs: np.ndarray, y: np.ndarray, *, grid_nside: int = 16, n_starts: int = 8,
                 dirs_coarse: np.ndarray | None = None, y_coarse: np.ndarray | None = None,
                 exact_final: bool = True, basin_sep_deg: float = 5.0, check: bool = True,
                 check_kwargs: dict | None = None) -> dict:
    """Global SO(3) + amplitude fit of the template to the sky map y on dirs (outward unit vectors).

    Model: y(n) ~ amp * S(R^-1 n) + const, R = R(d) Rz(gamma) = Rz(alpha) Ry(beta) Rz(gamma) (active zyz).
    Global stage: every HEALPix(grid_nside) axis d on (dirs_coarse, y_coarse) (closed-form roll/amp).
    Local stage: Nelder-Mead over the axis (tangent plane) from up to n_starts best grid local maxima on the
    full map.  With ``check``: ``global_check`` (finer grid nside 2 grid_nside + random restarts).
    Final: exact ``bjs_temperature_sky`` at the optimum.
    """
    dirs = np.asarray(dirs, dtype=np.float64)
    y_c = _centre(np.asarray(y, dtype=np.float64))
    dc = dirs if dirs_coarse is None else np.asarray(dirs_coarse, dtype=np.float64)
    yc = y_c if y_coarse is None else _centre(np.asarray(y_coarse, dtype=np.float64))
    axes, grid, is_max, order = _grid_local_maxima(tmpl, kappa, grid_nside, dc, yc)
    order = order[:n_starts]
    grid_best_full = score_axis(tmpl, kappa, axes[int(np.argmax(grid))], dirs, y_c)[0]
    starts = []
    for i in order:
        d, corr, amp, gam, nfev = _refine_axis(tmpl, kappa, axes[i], dirs, y_c)
        starts.append({"grid_pixel": int(i), "grid_corr": float(grid[i]), "axis": d.tolist(), "corr": corr,
                       "amp": amp, "roll": gam, "nfev": nfev})
    best = max(starts, key=lambda s: s["corr"])
    d_best = np.asarray(best["axis"])
    others = [s["corr"] for s in starts if angle_deg(s["axis"], d_best) > basin_sep_deg]
    R = axis_rotation(d_best) @ rot_z(best["roll"])
    alpha, beta, gamma = euler_from_matrix(R)
    out = {
        "kappa": int(kappa),
        "corr_spline": float(best["corr"]),
        "amp_spline": float(best["amp"]),
        "axis": d_best.tolist(),
        "rotation_matrix": R.tolist(),
        "euler_zyz_active_rad": [alpha, beta, gamma],
        "euler_determined": euler_determined(R),
        "grid_nside": int(grid_nside),
        "grid_max_corr_coarse": float(grid.max()),
        "grid_argmax_corr_full": float(grid_best_full),
        "n_grid_local_maxima": int(is_max.sum()),
        "n_starts_used": len(order),
        "starts": starts,
        "best_other_basin_corr": float(max(others)) if others else None,
    }
    if check:
        out["global_check"] = global_check(tmpl, kappa, dirs, y_c, float(best["corr"]), d_best,
                                           **{"check_nside": 2 * grid_nside, "dirs_coarse": dc, "y_coarse": yc,
                                              "basin_sep_deg": basin_sep_deg, **(check_kwargs or {})})
    if exact_final:
        t = _centre(tmpl.exact(dirs @ R, kappa))
        amp = float(y_c @ t) / float(t @ t)
        resid = y_c - amp * t
        out.update({
            "corr": float(y_c @ t) / (float(np.linalg.norm(y_c)) * float(np.linalg.norm(t))),
            "amp": amp,
            "residual_rms": float(np.sqrt(np.mean(resid ** 2))),
            "map_rms": float(np.sqrt(np.mean(y_c ** 2))),
            "residual_rms_relative": float(np.sqrt(np.mean(resid ** 2)) / np.sqrt(np.mean(y_c ** 2))),
            "spline_vs_exact_max_abs": float(np.max(np.abs(_centre(tmpl(dirs @ R, kappa)) - t))),
        })
    return out


# ----------------------------------------------------------------------------- state and background
def stable_compensating_tilt_velocity(target_q_vec: np.ndarray, *, eps_hat: float, p_hat: float) -> np.ndarray:
    """Root of gamma^2 (eps_hat + p_hat) v = q, i.e. v^2 + r v - 1 = 0 with r = w/|q|, in the cancellation-free form.

    Same quadratic as ``solve_compensating_tilt_velocity``.  At the time of the R108 S4 production runs
    (htt/bass/background/tilted_bianchi_state.py sha256 e36dd616..., the git HEAD blob) that function evaluated
    the difference form v = (-r + sqrt(r^2 + 4))/2; for |q|/w ~ 1e-8 (the shear amplitudes of this lane) the
    difference of two numbers of size r cancels catastrophically (relative error ~ eps r^2: 0.7%-36% measured,
    ``repo_solve_compensating_tilt_velocity_rel_error`` in the run files), and the repository constraint
    certificate (tol 1e-11) then rejected the state.  The working tree now evaluates the same stable form
    (sha256 dd6bd75f...), so for runs made with it ``repo_solve_compensating_tilt_velocity_rel_error`` is of
    order 1e-16.  v = 2/(r + sqrt(r^2 + 4)) has no cancellation.
    """
    q = np.asarray(target_q_vec, dtype=np.float64)
    qn = float(np.linalg.norm(q))
    if qn == 0.0:
        return np.zeros(3)
    r = float(eps_hat + p_hat) / qn
    return (2.0 / (r + math.sqrt(r * r + 4.0)) / qn) * q


def build_bjs_state(omega0: float, x: float, sigma_perp: float, *, phase: float = 0.25 * math.pi):
    """Admissible open-dust VII_h state at N = 0 with H = 1 (see module docstring)."""
    p = BJSParameters(omega0=omega0, x=x)
    a, n = bjs_lie_geometry_today(p)
    alg = BianchiAlgebra(type_name="VII_h", a=a, n=n, C=build_structure_tensor(a, n),
                         h_parameter=float(a @ a / (n[0, 0] * n[1, 1])), class_label="B",
                         h_convention="h = a^2/(n_11 n_22), VII_h axis e_z (R107 TF4 BJS dictionary)",
                         axis_permutation=(0, 1, 2), branch_policy=_branch_policy_for_type("VII_h"))
    sig = np.zeros((3, 3))
    sig[0, 2] = sig[2, 0] = sigma_perp * math.cos(phase)
    sig[1, 2] = sig[2, 1] = sigma_perp * math.sin(phase)
    sigma_sq = 0.5 * float(np.sum(sig * sig))
    _, R_sc, _ = exact_spatial_ricci_from_compact(a, n, a_sign=1)
    rho_target = 3.0 - sigma_sq + 0.5 * R_sc  # 3 H^2 = rho + sigma^2 - R/2 with H = 1, kappa = 1, Lambda = 0
    q_target = -exact_momentum_divergence(sig, a, n, a_sign=1)  # D_j sigma^j_i + kappa q_i = 0
    eps = rho_target
    for _ in range(6):  # dust: rho_normal = gamma^2 eps_hat
        v = stable_compensating_tilt_velocity(q_target, eps_hat=eps, p_hat=0.0)
        eps = rho_target * (1.0 - float(v @ v))
    v_repo = solve_compensating_tilt_velocity(q_target, eps_hat=eps, p_hat=0.0)
    sp = SpeciesFluidCongruence(species="cdm", eps_hat=eps, p_hat=0.0, v_vec=v)
    st = construct_admissible_tilted_state(family="VII_h", algebra=alg, sigma_ab=sig, species=[sp],
                                           lambda_value=0.0, kappa=1.0, closure="solve_H", tol=1e-11)
    kin = st.kinematics_by_species["cdm"]
    h = p.h
    info = {
        "a_over_H": a.tolist(), "n_over_H": n.tolist(), "h": h, "h_from_algebra": alg.h_parameter,
        "sigma_ab": sig.tolist(), "sigma_perp": sigma_perp, "sigma_phase_rad": phase,
        "sigma_convention": "sigma^2 = (1/2) sigma_ab sigma^ab = sigma_13^2 + sigma_23^2; sigma_13 = sigma_23",
        "H": float(st.H), "H_minus_1": float(st.H - 1.0), "R_spatial": float(R_sc),
        "dust_v": v.tolist(), "dust_speed": float(np.linalg.norm(v)), "dust_eps_hat": eps,
        "repo_solve_compensating_tilt_velocity_rel_error": float(np.linalg.norm(v_repo - v) / np.linalg.norm(v)),
        "constraint_normalized_residuals": dict(st.constraints.normalized_residuals),
        "constraints_admissible": bool(st.constraints.is_admissible),
        "dust_vorticity_over_H": float(kin.vorticity_norm / st.H),
        "dust_vorticity_vector": np.asarray(kin.omega_vec_3d).tolist(),
        # closed forms used below: |v| = sqrt(n^2 + 9 a^2) sigma_perp / (3 Omega_0 H^2) (Codazzi), and
        # McEwen et al. 2006 eq. A2 omega/sigma ratio
        "speed_closed_form": float(math.sqrt(1.0 / x ** 2 + 9.0 * (1.0 - omega0)) * sigma_perp / (3.0 * omega0)),
        "A2_omega_over_sigma": bjs_vorticity_over_hubble(BJSParameters(omega0=omega0, x=x, sigma_over_h=1.0)),
        # template observer dipole (C1 sin theta terms of A and B): amplitude C1 sqrt((1+3 sqrt h)^2 + (3 sqrt h - 1)^2).
        # With h = (1 - Omega_0) x^2 this times sigma_perp/sqrt(2) equals speed_closed_form identically (review
        # S4-7d): the ratio dust_speed / (it x sigma_perp/sqrt(2)) is an identity check, not a measurement.
        "template_C1_dipole_amplitude_per_unit_sigma": float(
            math.sqrt((1 + 3 * math.sqrt(h)) ** 2 + (3 * math.sqrt(h) - 1) ** 2) / (3.0 * omega0 * x)),
    }
    return st, info


def evolve_background(st, omega0: float, x: float, N_E: float, *, M: int = 1400, extra: int = 2,
                      rtol: float = 1e-12, atol: float = 1e-16) -> tuple[dict, dict]:
    """Backward evolution 0 -> N_E (M intervals, N_E on the grid) plus ``extra`` intervals beyond N_E."""
    N_end = N_E * (M + extra) / M
    cfg = TiltedEvolutionConfig(N_start=0.0, N_end=N_end, n_eval=M + extra + 1, method="DOP853",
                                rtol=rtol, atol=atol, constraint_abort_tol=1e-6)
    t0 = time.perf_counter()
    res = evolve_general_tilted_bianchi(st, eos_by_species={"cdm": 0.0}, config=cfg)
    wall = time.perf_counter() - t0
    N = res.N_grid
    H = res.H_grid
    sig = res.sigma_ab_grid / H[:, None, None]
    a = res.a_grid / H[:, None]
    n = res.n_grid / H[:, None, None]
    v = res.species_v_grid["cdm"]
    eps = res.species_eps_hat_grid["cdm"]
    rho = eps / (1.0 - np.sum(v * v, axis=1))
    Omega = rho / (3.0 * H ** 2)
    E = np.sqrt(omega0 * np.exp(-3.0 * N) + (1.0 - omega0) * np.exp(-2.0 * N))  # open dust H/H0
    Omega_flrw = omega0 * np.exp(-3.0 * N) / E ** 2
    a_flrw = math.sqrt(1.0 - omega0) * np.exp(-N) / E
    n_flrw = np.exp(-N) / (x * E)
    Sigma2 = 0.5 * np.sum(sig * sig, axis=(1, 2)) / 3.0
    sig_perp = np.sqrt(sig[:, 0, 2] ** 2 + sig[:, 1, 2] ** 2)
    sig_other = np.sqrt(np.maximum(np.sum(sig ** 2, axis=(1, 2)) - 2.0 * sig_perp ** 2, 0.0))
    sig_perp_dim = sig_perp * H
    a_perp = np.sqrt(a[:, 0] ** 2 + a[:, 1] ** 2)
    n_off = np.sqrt(n[:, 0, 1] ** 2 + n[:, 0, 2] ** 2 + n[:, 1, 2] ** 2)
    hval = np.array([float(a[k] @ a[k]) / float(np.prod(np.sort(np.abs(np.linalg.eigvalsh(n[k])))[1:]))
                     for k in range(N.size)])
    iE = M
    checks = {
        "N_E": float(N_E), "N_grid_at_index_M": float(N[iE]), "N_end": float(N[-1]), "n_eval": int(N.size),
        "rtol": rtol, "atol": atol, "method": "DOP853", "wall_s": wall, "n_rhs_evals": int(res.n_rhs_evals),
        "max_jacobi_residual": float(res.max_jacobi_residual),
        "max_hamiltonian_residual_rel": float(res.max_hamiltonian_residual_rel),
        "max_codazzi_residual_rel": float(res.max_codazzi_residual_rel),
        "max_shear_trace_error": float(res.max_shear_trace_error),
        "max_abs_Omega_minus_open_dust": float(np.max(np.abs(Omega - Omega_flrw))),
        "max_Sigma2": float(np.max(Sigma2)),
        "max_abs_friedmann_closure": float(np.max(np.abs(Omega + np.sum(a * a, axis=1) + Sigma2 - 1.0))),
        "max_rel_a_axis_minus_open_dust": float(np.max(np.abs(a[:, 2] / a_flrw - 1.0))),
        "max_rel_n_transverse_minus_open_dust": float(max(np.max(np.abs(n[:, 0, 0] / n_flrw - 1.0)),
                                                          np.max(np.abs(n[:, 1, 1] / n_flrw - 1.0)))),
        "max_abs_n33_over_H": float(np.max(np.abs(n[:, 2, 2]))),
        "max_a_perp_over_sigma_perp": float(np.max(a_perp / sig_perp)),
        "max_n_offdiag_over_sigma_perp": float(np.max(n_off / sig_perp)),
        "max_rel_h_drift": float(np.max(np.abs(hval / hval[0] - 1.0))),
        "max_rel_sigma_perp_e3N_drift": float(np.max(np.abs(sig_perp_dim * np.exp(3.0 * N) / sig_perp_dim[0] - 1.0))),
        "max_sigma_other_over_sigma_perp": float(np.max(sig_other / sig_perp)),
        "max_rel_dust_speed_eN_drift": float(np.max(np.abs(np.linalg.norm(v, axis=1) * np.exp(N)
                                                           / np.linalg.norm(v[0]) - 1.0))),
        "sigma_over_H_at_N_E": float(sig_perp[iE]), "sigma_over_H_today": float(sig_perp[0]),
        "Omega_at_N_E": float(Omega[iE]), "a_over_H_at_N_E": float(a[iE, 2]), "n_over_H_at_N_E": float(n[iE, 0, 0]),
        "dust_v_today": v[0].tolist(), "dust_v_at_N_E": v[iE].tolist(),
    }
    order = np.argsort(N)
    g14 = np.stack([pack_geometry14(sig[k], a[k], n[k]) for k in order])
    geo = {"geometry_N": N[order], "geometry14": g14, "v_today": v[0], "v_E": v[iE]}
    return geo, checks


# ----------------------------------------------------------------------------- line of sight
def shell_history(geo: dict, N_E: float) -> LosSourceHistory:
    """One optically thick shell at N_E with zero source increment (cf. ``_shell_history`` in the LoS tests)."""
    op = GeneralLieStokesOperator(2)
    N = np.array([N_E - 1e-3, N_E, 0.0])
    return LosSourceHistory(N=N, delta_tau=np.array([1e6, 0.0]), emission=np.zeros((3, op.dim), dtype=complex),
                            initial_state=np.zeros(op.dim, dtype=complex), geometry_N=geo["geometry_N"],
                            geometry14=geo["geometry14"], ell_max_native=2,
                            provenance={"source": "r108_s4_bjs_comparator", "shell": "thick at N_E, zero increment"})


def los_maps(geo: dict, N_E: float, nside: int, max_step: float, *, doppler: bool = True) -> dict:
    """Protocol map (normal observers) and, optionally, the Doppler diagnostic map (dust observer/emitter)."""
    dirs = healpix_directions(nside)
    hist = shell_history(geo, N_E)
    t0 = time.perf_counter()
    sky = los_sky(hist, dirs, max_step=max_step)
    t_los = time.perf_counter() - t0
    dTT = np.expm1(0.25 * np.log1p(4.0 * sky.T))
    out = {"dirs": dirs, "T": sky.T, "dTT": dTT - dTT.mean(), "monopole": float(dTT.mean()), "los_seconds": t_los,
           "los_diagnostics": {k: v for k, v in sky.diagnostics.items() if k != "provenance"}}
    if doppler:
        t0 = time.perf_counter()
        nE = dE = None
        for k, n_k, delta_k, _chi in trace_rays(dirs, hist.N, hist.geometry_N, hist.geometry14, max_step=max_step):
            if k == 1:
                nE, dE = n_k, delta_k
        v0, vE = np.asarray(geo["v_today"]), np.asarray(geo["v_E"])
        g0, gE = 1.0 / math.sqrt(1.0 - v0 @ v0), 1.0 / math.sqrt(1.0 - vE @ vE)
        # observer moving with v0 sees E' = gamma E (1 + v0.n); emitter isotropic in its rest frame gives
        # T_normal(n_E) = T_rest / (gamma (1 + vE.n_E)) for sky direction n_E (photon along -n_E).
        fac = g0 * (1.0 + dirs @ v0) * np.exp(-dE) / (gE * (1.0 + nE @ vE))
        dm = fac - 1.0
        out.update({"dTT_doppler": dm - dm.mean(), "trace_seconds": time.perf_counter() - t0,
                    "los_vs_trace_max_abs": float(np.max(np.abs(sky.T - 0.25 * np.expm1(-4.0 * dE)))),
                    "observer_doppler_rms": float(np.std(dirs @ v0)),
                    "emitter_doppler_rms": float(np.std(nE @ vE))})
    return out


# ----------------------------------------------------------------------------- driver
def map_paths(omega0: float, x: float, sigma0: float, nside: int, max_step: float, M: int, rtol: float, atol: float,
              *, richardson: bool, work: Path = WORK) -> dict:
    """Map files of one case.  The main-map tag carries the richardson flag (review S4-5a: before this, a
    --richardson run wrote its main map under the production tag and overwrote the production file)."""
    tag = f"O{omega0:.1f}_x{x:.2f}_s{sigma0:.0e}_ns{nside}_st{max_step:g}_M{M}_rt{rtol:.0e}_at{atol:.0e}"
    run = "_richrun" if richardson else ""
    return {"main": work / f"S4_map_{tag}{run}.npz",
            "x2": None if richardson else work / f"S4_map_{tag}_x2.npz",
            "richardson": work / f"S4_map_{tag}_richardson.npz" if richardson else None}


def _file_record(p: Path) -> dict:
    from scripts.r108.common import sha256_file

    return {"path": str(p), "sha256": sha256_file(p), "bytes": p.stat().st_size}


def run_case(omega0: float, x: float, *, sigma0: float, nside: int, max_step: float, M: int, grid_nside: int,
             n_starts: int, linearity: bool, fits: bool, rtol: float = 1e-12, atol: float = 1e-16,
             richardson: bool = False) -> dict:
    """One (Omega_0, x) case.  With ``richardson`` the doubled-shear run also gets the Doppler map and the fits are
    made to the Richardson-linearised maps 2 M(sigma) - M(2 sigma)/2 (second order in sigma removed), a
    post-hoc diagnostic that separates the nonlinear residual from template differences; not the acceptance."""
    t_case = time.perf_counter()
    N_E = -math.log1p(Z_EMISSION)
    st, info = build_bjs_state(omega0, x, sigma0)
    geo, bg = evolve_background(st, omega0, x, N_E, M=M, rtol=rtol, atol=atol)
    maps = los_maps(geo, N_E, nside, max_step)
    y = maps["dTT"]
    case = {"omega0": omega0, "x": x, "z_emission": Z_EMISSION, "sigma0": sigma0, "nside": nside, "max_step": max_step,
            "M": M, "state": info, "background": bg,
            "los": {"monopole": maps["monopole"], "rms_dTT": float(np.std(y)), "max_abs_dTT": float(np.max(np.abs(y))),
                    "los_seconds": maps["los_seconds"], "diagnostics": maps["los_diagnostics"],
                    "los_vs_trace_max_abs": maps.get("los_vs_trace_max_abs"),
                    "doppler_map_rms": float(np.std(maps["dTT_doppler"])),
                    "observer_doppler_rms": maps.get("observer_doppler_rms"),
                    "emitter_doppler_rms": maps.get("emitter_doppler_rms")}}
    WORK.mkdir(parents=True, exist_ok=True)
    paths = map_paths(omega0, x, sigma0, nside, max_step, M, rtol, atol, richardson=richardson)
    np.savez_compressed(paths["main"], dTT=y, dTT_doppler=maps["dTT_doppler"], T=maps["T"])
    case["map_files"] = {"main": _file_record(paths["main"])}
    if linearity or richardson:
        st2, _ = build_bjs_state(omega0, x, 2.0 * sigma0)
        geo2, bg2 = evolve_background(st2, omega0, x, N_E, M=M, rtol=rtol, atol=atol)
        maps2 = los_maps(geo2, N_E, nside, max_step, doppler=richardson)
        y2 = maps2["dTT"]
        dev = y2 - 2.0 * y
        case["linearity"] = {
            "sigma0_doubled": 2.0 * sigma0,
            "rel_rms_deviation": float(np.sqrt(np.mean(dev ** 2)) / np.sqrt(np.mean((2.0 * y) ** 2))),
            "rel_max_deviation": float(np.max(np.abs(dev)) / np.max(np.abs(2.0 * y))),
            "max_abs_dTT_single": float(np.max(np.abs(y))),
            "rel_rms_deviation_over_max_abs_dTT": float(np.sqrt(np.mean(dev ** 2)) / np.sqrt(np.mean((2.0 * y) ** 2))
                                                         / np.max(np.abs(y))),
            "background_doubled": {k: bg2[k] for k in ("max_hamiltonian_residual_rel", "max_codazzi_residual_rel",
                                                       "max_jacobi_residual", "sigma_over_H_at_N_E")},
        }
        if richardson:
            fit_maps = (("protocol_richardson", 2.0 * y - 0.5 * y2),
                        ("doppler_richardson", 2.0 * maps["dTT_doppler"] - 0.5 * maps2["dTT_doppler"]))
            np.savez_compressed(paths["richardson"], protocol=fit_maps[0][1], doppler=fit_maps[1][1])
            case["map_files"]["richardson"] = _file_record(paths["richardson"])
            case["richardson"] = {"definition": "2 M(sigma0) - M(2 sigma0)/2", "rel_rms_protocol_minus_raw": float(
                np.std(fit_maps[0][1] - y) / np.std(y)), "rel_rms_doppler_minus_raw": float(
                np.std(fit_maps[1][1] - maps["dTT_doppler"]) / np.std(maps["dTT_doppler"]))}
        else:
            np.savez_compressed(paths["x2"], dTT=y2)
            case["map_files"]["x2"] = _file_record(paths["x2"])
    if not richardson:
        fit_maps = (("protocol", y), ("doppler_diagnostic", maps["dTT_doppler"]))
    if fits:
        import healpy as hp

        coarse_nside = max(nside // 2, 8)
        dirs_c = healpix_directions(coarse_nside)
        fit_rows = {}
        for variant in VARIANTS:
            t0 = time.perf_counter()
            tmpl = TemplateSky(omega0, x, variant)
            t_build = time.perf_counter() - t0
            # full sky (review S4-7b; before: the first 4096 ring pixels, a polar cap of the rotated frame)
            val = {k: dict(tmpl.validate(maps["dirs"] @ rot_y(0.37) @ rot_z(1.1), k), domain="full sky")
                   for k in HANDEDNESS}
            for label, ymap in fit_maps:
                yc = hp.ud_grade(ymap, coarse_nside, order_in="RING", order_out="RING")
                for kappa in HANDEDNESS:
                    t0 = time.perf_counter()
                    r = fit_rotation(tmpl, kappa, maps["dirs"], ymap, grid_nside=grid_nside, n_starts=n_starts,
                                     dirs_coarse=dirs_c, y_coarse=yc)
                    R = np.asarray(r["rotation_matrix"])
                    d = np.asarray(r["axis"])
                    r.update({
                        "variant": variant, "map": label, "fit_seconds": time.perf_counter() - t0,
                        "amp_over_sigma_perp": r["amp"] / sigma0,
                        "amp_over_sigma_perp_times_sqrt2": r["amp"] * math.sqrt(2.0) / sigma0,
                        "template_axis_angle_to_plus_z_deg": angle_deg(d, [0, 0, 1]),
                        "template_axis_angle_to_minus_z_deg": angle_deg(d, [0, 0, -1]),
                        "rotation_angle_from_identity_deg": rotation_angle_deg(R),
                        "spline_validation": val[kappa], "template_build_seconds": t_build,
                    })
                    fit_rows[f"{label}|{variant}|{kappa:+d}"] = r
        case["fits"] = fit_rows
    case["case_seconds"] = time.perf_counter() - t_case
    return case


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--omega0", type=float, nargs="+", default=list(OMEGAS))
    ap.add_argument("--x", type=float, nargs="+", default=list(XS))
    ap.add_argument("--sigma0", type=float, default=1e-8)
    ap.add_argument("--nside", type=int, default=64)
    ap.add_argument("--max-step", type=float, default=0.02)
    ap.add_argument("--M", type=int, default=1400)
    ap.add_argument("--grid-nside", type=int, default=16)
    ap.add_argument("--n-starts", type=int, default=8)
    ap.add_argument("--rtol", type=float, default=1e-12)
    ap.add_argument("--atol", type=float, default=1e-16)
    ap.add_argument("--no-linearity", action="store_true")
    ap.add_argument("--no-fits", action="store_true")
    ap.add_argument("--richardson", action="store_true",
                    help="fit the Richardson-linearised maps 2 M(sigma) - M(2 sigma)/2 instead (diagnostic)")
    ap.add_argument("--output", required=True)
    a = ap.parse_args(argv)
    from scripts.r108.common import git_state, sha256_file, write_json

    REPO = Path(__file__).resolve().parents[2]
    srcs = ["htt/bass/transport/hybrid_los_transfer.py", "htt/bass/transport/bjs_bianchi_vii_h.py",
            "htt/bass/background/general_tilted_evolution.py", "htt/bass/background/tilted_bianchi_state.py",
            "htt/bass/background/convention_bridge.py", "scripts/r108/s4_bjs_comparator.py"]
    payload = {"schema": SCHEMA, "argv": vars(a), "command": [sys.executable, *sys.argv], "git": git_state(),
               "sources_sha256": {s: sha256_file(REPO / s) for s in srcs}, "cases": []}
    for om in a.omega0:
        for xx in a.x:
            case = run_case(om, xx, sigma0=a.sigma0, nside=a.nside, max_step=a.max_step, M=a.M,
                            grid_nside=a.grid_nside, n_starts=a.n_starts, linearity=not a.no_linearity,
                            fits=not a.no_fits, rtol=a.rtol, atol=a.atol, richardson=a.richardson)
            payload["cases"].append(case)
            write_json(a.output, payload)
            print(json.dumps({"omega0": om, "x": xx, "seconds": case["case_seconds"],
                              "best": {k: round(v["corr"], 6) for k, v in case.get("fits", {}).items()}}), flush=True)
    write_json(a.output, payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
