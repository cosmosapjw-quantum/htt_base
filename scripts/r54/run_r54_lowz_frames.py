#!/usr/bin/env python3
"""R54 loops L2/L3/L5/L6: low-redshift frame and expansion-rate tensors from committed products.

Executable without the local data drive. Inputs (all committed):
  R36-01 CF4 apparent-Hubble window multipoles theta4x9 with their working covariance
  the L2 count-dipole receipt (Quaia, NVSS)
  tests/fixtures/r54/planck18_linear_pk_z0.csv (theory fixture)

What it does
  1. builds the ideal-sky linear-LCDM cosmic-variance body for the four windows (R54-EQ-11/12);
  2. tests the dipole (vector irrep) and quadrupole (STF2 irrep) against that body (Q, Pi);
  3. compares depth-transport laws for the dipole (G_F):
        V : D_w = AN_w V      constant velocity (bulk flow or observer boost; decays as 1/d)
        A : D_w = A           constant fractional-H dipole (distance zero-point or acceleration type)
  4. scans the axis of a two-parameter template (constant dH dipole + axisymmetric quadrupole)
     and measures its locking to the equatorial pole (survey-geometry frame) with controls;
  5. evaluates the count-dipole excess vectors against the kinematic expectation (L2).

Claim ceiling C0, DIAGNOSTIC. The body is ideal-sky; the exact catalogue body A C_uu A^T,
the method/hemisphere zero-point split and the selection model are local obligations (R54-L05).
Published comparison values are anchors for the adversarial benchmark, not owned data.
"""
from __future__ import annotations

import hashlib
import json
import math
import platform
import sys
from pathlib import Path

import numpy as np
import scipy
from scipy import optimize, stats

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT / "htt", ROOT / "htt/src", ROOT):
    sys.path.insert(0, str(_p))

from htt.htt.infer import r54_lcdm_body as lb  # noqa: E402
from htt.htt.infer import r54_tensor_five_view as fv  # noqa: E402

PUB = ROOT / "docs/research_program/observational_publication_20261015"
CF4 = PUB / "OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-01-CF4-OPERATOR/RESULT.json"
COUNTS = PUB / "HTT_SIX_LOOP_INTEGRATED_20261109/COUNT_DIPOLES_REAL_RECEIPT.json"
PK = ROOT / "tests/fixtures/r54/planck18_linear_pk_z0.csv"
OUT = PUB / "R54_TENSOR_FRAME_TOMOGRAPHY_20261116/RESULTS/R54_L5_LOWZ_FRAMES.json"

C_KM_S = 299792.458
H0_THEORY, OMEGA_M = 67.36, 0.3153            # linear-theory body (Planck 2018), declared
SIGMA_Z_WINDOW = 0.012                         # R36 Gaussian window width in z_CMB
V_SUN_CMB, L_CMB, B_CMB = 369.82, 264.021, 48.253   # Planck 2018 solar dipole
C_EB = {"Quaia_G20": 3.7386422874798133, "NVSS": 3.5}   # scripts/r52/run_r52_joint.py
#: rows = Galactic unit vectors expressed in ICRS: x_gal = R_I2G @ x_icrs
R_I2G = np.array([[-0.0548755604162154, -0.8734370902348850, -0.4838350155487132],
                  [0.4941094278755837, -0.4448296299600112, 0.7469822444972189],
                  [-0.8676661490190047, -0.1980763734312015, 0.4559837761750669]])
PUBLISHED = {   # anchors for the adversarial benchmark; identifiers re-verified by web search on 2026-11-16
    "stiskalek_2025_cf4_tfr_zero_point_dipole": {"arxiv": "2509.14997", "percent_of_H": 4.1, "sd": 0.9, "mag": 0.087, "mag_sd": 0.019},
    "watkins_2023_cf4_bulk_flow_200": {"arxiv": "2302.02028", "km_s": 419.0, "sd": 36.0, "l_deg": 298.0, "b_deg": -8.0, "depth_h_inv_Mpc": 200.0},
    "kalbouneh_2026_cf4_axis": {"arxiv": "2510.02510", "l_deg": 295.0, "b_deg": 5.0},
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clean(obj):
    if isinstance(obj, dict):
        return {str(k): clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [clean(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return clean(obj.tolist())
    if isinstance(obj, (np.floating, float)):
        f = float(obj)
        return f if math.isfinite(f) else (None if math.isnan(f) else ("inf" if f > 0 else "-inf"))
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    return obj


def gal_unit(l_deg: float, b_deg: float) -> np.ndarray:
    l, b = math.radians(l_deg), math.radians(b_deg)
    return np.array([math.cos(b) * math.cos(l), math.cos(b) * math.sin(l), math.sin(b)])


def icrs_to_lb(v: np.ndarray) -> list[float]:
    g = R_I2G @ (np.asarray(v, float) / np.linalg.norm(v))
    return [float(math.degrees(math.atan2(g[1], g[0])) % 360.0), float(math.degrees(math.asin(np.clip(g[2], -1, 1))))]


def angle_deg(u: np.ndarray, v: np.ndarray, axis: bool = False) -> float:
    c = float(np.dot(u, v) / np.linalg.norm(u) / np.linalg.norm(v))
    if axis:
        c = abs(c)
    return float(math.degrees(math.acos(np.clip(c, -1.0, 1.0))))


AXES_ICRS = {
    "equatorial_pole": np.array([0.0, 0.0, 1.0]),
    "galactic_pole": R_I2G.T @ np.array([0.0, 0.0, 1.0]),
    "supergalactic_pole": R_I2G.T @ gal_unit(47.37, 6.32),
    "ecliptic_pole": np.array([0.0, -math.sin(math.radians(23.4392911)), math.cos(math.radians(23.4392911))]),
    "cmb_dipole_axis": R_I2G.T @ gal_unit(L_CMB, B_CMB),
}


def block_rows(kind: str) -> np.ndarray:
    cols = {"dipole": (1, 2, 3), "quadrupole": (4, 5, 6, 7, 8)}[kind]
    return np.array([9 * w + k for w in range(4) for k in cols])


def axis_template(n: np.ndarray) -> np.ndarray:
    """32 x 2 design on [dipole(3), quadrupole(5)] x 4 windows: constant dH dipole along n and
    constant axisymmetric quadrupole sqrt(3/2)(nn - I/3) about n."""
    n = np.asarray(n, float) / np.linalg.norm(n)
    j = np.zeros((32, 2))
    q5 = fv.axisymmetric_stf5(n)
    for w in range(4):
        j[8 * w:8 * w + 3, 0] = n
        j[8 * w + 3:8 * w + 8, 1] = q5
    return j


def analyse_window_multipoles(theta: np.ndarray, cov: np.ndarray, an: np.ndarray, h_fit: float, law: str, estimator: str = "linear") -> dict:
    """Null, depth-law and axis-locking analysis of 4 windows x [H, D(3), STF5] multipoles.

    ``theta`` and ``cov`` are in the units of the estimator (km/s/Mpc for the R36 linear estimator with
    ``h_fit`` = fitted H; dimensionless fractions for the log-distance estimator with ``h_fit`` = 1).
    ``an`` (36 x 3) is the response of theta to a uniform velocity (units of theta per km/s).
    ``estimator`` fixes the magnitude map of a dipole amplitude A: "linear" (theta in km/s/Mpc) uses
    5 log10(1 + A/h_fit); "log" (theta = shift of eta = ln H, h_fit = 1) uses (5/ln10) A of R54-EQ-36.
    """
    if estimator not in ("linear", "log") or (estimator == "log" and h_fit != 1.0):
        raise ValueError("estimator must be 'linear', or 'log' with h_fit = 1")

    def to_mag(a: float) -> float:
        return 5.0 * math.log10(1.0 + abs(a) / h_fit) if estimator == "linear" else abs(a) * 5.0 / math.log(10.0)

    dip, quad = block_rows("dipole"), block_rows("quadrupole")
    dq = np.sort(np.concatenate([dip, quad]))
    an_d = an[dip]
    a_const = np.tile(np.eye(3), (4, 1))
    pole = AXES_ICRS["equatorial_pole"]
    cmb = AXES_ICRS["cmb_dipole_axis"]
    cd, cq, cdq = cov[np.ix_(dip, dip)], cov[np.ix_(quad, quad)], cov[np.ix_(dq, dq)]
    yd, yq, ydq = theta[dip], theta[quad], theta[dq]
    models = fv.compare_transport_models(yd, cd, {"V_constant_velocity": an_d, "A_constant_dH": a_const,
                                                  "V_plus_A": np.hstack([an_d, a_const])})
    fit_v, fit_a, fit_va = (fv.gls_fit(yd, cd, an_d), fv.gls_fit(yd, cd, a_const), fv.gls_fit(yd, cd, np.hstack([an_d, a_const])))
    v_va, a_va = fit_va["theta"][:3], fit_va["theta"][3:]
    cva = fit_va["cov"]
    dipole = {
        "null": fv.chi2_null_tail(models["null"]["chi2"], 12, law),
        "Q_center": math.sqrt(models["null"]["chi2"] / stats.chi2.ppf(0.95, 12)),
        "models": models,
        "V_only": {"km_s_icrs": fit_v["theta"], "amplitude_km_s": float(np.linalg.norm(fit_v["theta"])),
                   "direction_l_b_deg": icrs_to_lb(fit_v["theta"]), "wald": fit_v["wald"],
                   "angle_to_watkins_2023_deg": angle_deg(R_I2G @ fit_v["theta"], gal_unit(298.0, -8.0))},
        "A_only": {"km_s_Mpc_icrs": fit_a["theta"], "sd": np.sqrt(np.diag(fit_a["cov"])),
                   "amplitude_km_s_Mpc": float(np.linalg.norm(fit_a["theta"])),
                   "percent_of_H": 100.0 * float(np.linalg.norm(fit_a["theta"])) / h_fit,
                   "equivalent_mag": to_mag(float(np.linalg.norm(fit_a["theta"]))),
                   "direction_l_b_deg": icrs_to_lb(fit_a["theta"]), "wald": fit_a["wald"],
                   "wald_p_value": float(stats.chi2.sf(fit_a["wald"], 3)),
                   "angle_to_equatorial_pole_axis_deg": angle_deg(fit_a["theta"], pole, axis=True),
                   "perpendicular_to_pole_chi2_2dof": float(fit_a["theta"][:2] @ np.linalg.solve(fit_a["cov"][:2, :2], fit_a["theta"][:2]))},
        "V_plus_A": {"V_km_s_icrs": v_va, "V_amplitude_km_s": float(np.linalg.norm(v_va)), "V_direction_l_b_deg": icrs_to_lb(v_va),
                     "V_wald_3dof": float(v_va @ np.linalg.solve(cva[:3, :3], v_va)),
                     "A_km_s_Mpc_icrs": a_va, "A_percent_of_H": 100.0 * float(np.linalg.norm(a_va)) / h_fit,
                     "A_direction_l_b_deg": icrs_to_lb(a_va), "A_wald_3dof": float(a_va @ np.linalg.solve(cva[3:, 3:], a_va)),
                     "angle_V_to_cmb_apex_deg": angle_deg(v_va, cmb), "angle_A_to_equatorial_pole_axis_deg": angle_deg(a_va, pole, axis=True)},
        "delta_chi2_A_minus_V_same_parameter_count": models["V_constant_velocity"]["chi2"] - models["A_constant_dH"]["chi2"],
    }
    qfit = fv.gls_fit(yq, cq, fv.transport_design([1.0, 1.0, 1.0, 1.0], 5))
    inv = fv.stf2_invariants(qfit["theta"])
    axi = fv.axisymmetry_statistic(qfit["theta"], np.linalg.inv(qfit["cov"]))
    qnull = float(yq @ np.linalg.solve(cq, yq))
    quadrupole = {
        "null": fv.chi2_null_tail(qnull, 20, law), "Q_center": math.sqrt(qnull / stats.chi2.ppf(0.95, 20)),
        "constant_tensor": {"q_km_s_Mpc": qfit["theta"], "sd": np.sqrt(np.diag(qfit["cov"])), "chi2": qfit["chi2"], "dof": qfit["dof"],
                            "p_value": qfit["p_value"], "wald_5dof": qfit["wald"], "invariants": inv,
                            "principal_axis_l_b_deg": icrs_to_lb(np.asarray(inv["principal_axis"])),
                            "principal_axis_angle_to_equatorial_pole_deg": angle_deg(np.asarray(inv["principal_axis"]), pole, axis=True),
                            "percent_of_H": 100.0 * abs(inv["principal_eigenvalue"]) / h_fit,
                            "axisymmetry": {"statistic_3dof_nominal": axi["statistic"], "axis_l_b_deg": icrs_to_lb(np.asarray(axi["axis"])),
                                            "axis_angle_to_equatorial_pole_deg": angle_deg(np.asarray(axi["axis"]), pole, axis=True)}},
    }
    # ---- axis locking of the joint two-parameter template
    ci = np.linalg.inv(cdq)
    c0 = float(ydq @ ci @ ydq)

    def gain(n: np.ndarray) -> float:
        j = axis_template(n)
        f = j.T @ ci @ j
        t = j.T @ ci @ ydq
        return float(t @ np.linalg.solve(f, t))

    grid = fv.fibonacci_sphere(4000)
    gains = np.array([gain(n) for n in grid])
    n0 = grid[int(np.argmax(gains))]
    sol = optimize.minimize(lambda x: -gain(np.array([math.sin(x[0]) * math.cos(x[1]), math.sin(x[0]) * math.sin(x[1]), math.cos(x[0])])),
                            [math.acos(float(np.clip(n0[2], -1, 1))), math.atan2(n0[1], n0[0])], method="Nelder-Mead",
                            options={"xatol": 1e-8, "fatol": 1e-10, "maxiter": 4000})
    nb = np.array([math.sin(sol.x[0]) * math.cos(sol.x[1]), math.sin(sol.x[0]) * math.sin(sol.x[1]), math.cos(sol.x[0])])
    gpole = gain(pole)
    fp = fv.gls_fit(ydq, cdq, axis_template(pole))
    locking = {
        "template": "constant dH dipole along n + constant axisymmetric quadrupole about n (2 parameters, 32 data)",
        "null_chi2": c0, "null_p_value": float(stats.chi2.sf(c0, 32)),
        "delta_chi2_at_reference_axes": {name: gain(ax) for name, ax in AXES_ICRS.items()},
        "best_axis": {"delta_chi2": float(-sol.fun), "icrs_ra_dec_deg": [float(math.degrees(math.atan2(nb[1], nb[0])) % 360.0),
                                                                         float(math.degrees(math.asin(np.clip(nb[2], -1, 1))))],
                      "l_b_deg": icrs_to_lb(nb), "angle_to_equatorial_pole_axis_deg": angle_deg(nb, pole, axis=True)},
        "sky_fraction_of_axes_with_gain_at_least_equatorial_pole": float(np.mean(gains >= gpole)),
        "n_grid_axes": int(grid.shape[0]),
        "equatorial_pole_fit": {"dH_dipole_km_s_Mpc": float(fp["theta"][0]), "dH_dipole_sd": float(math.sqrt(fp["cov"][0, 0])),
                                "dH_dipole_percent_of_H": 100.0 * float(fp["theta"][0]) / h_fit,
                                "dipole_equivalent_mag": to_mag(float(fp["theta"][0])),
                                "axisymmetric_quadrupole_km_s_Mpc": float(fp["theta"][1]), "quadrupole_sd": float(math.sqrt(fp["cov"][1, 1])),
                                "residual_chi2": fp["chi2"], "residual_dof": fp["dof"], "residual_p_value": fp["p_value"]},
    }
    return {"law": law, "dipole": dipole, "quadrupole": quadrupole, "axis_locking": locking}


def cf4_block(k: np.ndarray, pk: np.ndarray) -> dict:
    src = json.loads(CF4.read_text())
    theta = np.asarray(src["theta4x9"], float).ravel()
    c_meas = np.asarray(src["covariance36x36"], float)
    an = np.asarray(src["AN_36x3_inverse_Mpc"], float)
    zc = [float(x) for x in src["window_centers"]]
    a_w = np.array([np.mean(np.diag(an[9 * w + 1:9 * w + 4])) for w in range(4)])
    h_fit = float(np.mean(theta[0::9]))
    sigma_r = C_KM_S * SIGMA_Z_WINDOW / h_fit
    f_growth = lb.growth_rate(OMEGA_M)

    def body(sig: float, amp: float = 1.0) -> np.ndarray:
        wins = [lb.gaussian_window(1.0 / a_w[w], sig, a_w[w]) for w in range(4)]
        return amp * lb.stacked_window_body(k, pk, wins, f_growth, H0_THEORY)

    b0 = body(sigma_r)
    covs = {"MEAS": c_meas, "MEAS_PLUS_LCDM": c_meas + b0}
    dip, quad = block_rows("dipole"), block_rows("quadrupole")
    dq = np.sort(np.concatenate([dip, quad]))
    out: dict = {
        "source": {"schema": src["schema"], "task_id": src["task_id"], "claim_tier": src["claim_tier"],
                   "frame": src["frames"], "window_centers_z": zc, "working_model": src["working_model"]},
        "windows": {"uniform_flow_response_per_Mpc": a_w, "r_eff_Mpc": 1.0 / a_w, "sigma_r_Mpc": sigma_r, "H_fit_km_s_Mpc": h_fit},
        "lcdm_body": {"kind": "IDEAL_SKY_LINEAR_THEORY (R54-EQ-11/12)", "H0": H0_THEORY, "omega_m": OMEGA_M, "f": f_growth,
                      "cosmic_sd_dipole_km_s_Mpc": np.sqrt(np.diag(b0))[1::9], "cosmic_sd_quadrupole_km_s_Mpc": np.sqrt(np.diag(b0))[4::9],
                      "cosmic_sd_monopole_km_s_Mpc": np.sqrt(np.diag(b0))[0::9],
                      "bulk_velocity_sd_per_axis_km_s": np.sqrt(np.diag(b0))[1::9] / a_w,
                      "dipole_cross_window_correlation": (b0[np.ix_([1, 10, 19, 28], [1, 10, 19, 28])]
                                                          / np.outer(np.sqrt(np.diag(b0))[1::9], np.sqrt(np.diag(b0))[1::9]))},
        "observed": {"dipole_km_s_Mpc": theta[dip].reshape(4, 3), "quadrupole_km_s_Mpc": theta[quad].reshape(4, 5),
                     "dipole_meas_sd": np.sqrt(np.diag(c_meas))[dip].reshape(4, 3)},
    }
    an_d = an[dip]
    a_const = np.tile(np.eye(3), (4, 1))
    pole = AXES_ICRS["equatorial_pole"]
    cmb = AXES_ICRS["cmb_dipole_axis"]
    per_cov = {}
    for tag, cov in covs.items():
        law = "R36 working measurement covariance" + (" + ideal-sky linear LCDM body" if tag != "MEAS" else "")
        per_cov[tag] = analyse_window_multipoles(theta, cov, an, h_fit, law)
    out["analysis"] = per_cov
    # ---- sensitivity of the headline numbers to the body
    sens = []
    for sig in (0.75 * sigma_r, sigma_r, 1.25 * sigma_r):
        for amp in (0.5, 1.0, 2.0):
            cov = c_meas + body(sig, amp)
            cd, cdq = cov[np.ix_(dip, dip)], cov[np.ix_(dq, dq)]
            m = fv.compare_transport_models(theta[dip], cd, {"V": an_d, "A": a_const})
            fa = fv.gls_fit(theta[dip], cd, a_const)
            fp = fv.gls_fit(theta[dq], cdq, axis_template(pole))
            c0 = float(theta[dq] @ np.linalg.solve(cdq, theta[dq]))
            sens.append({"sigma_r_Mpc": sig, "body_amplitude_scale": amp, "dipole_null_p": m["null"]["p_value"],
                         "chi2_V": m["V"]["chi2"], "chi2_A": m["A"]["chi2"], "A_percent_of_H": 100.0 * float(np.linalg.norm(fa["theta"])) / h_fit,
                         "A_angle_to_pole_deg": angle_deg(fa["theta"], pole, axis=True), "pole_template_delta_chi2": c0 - fp["chi2"],
                         "pole_template_residual_p": fp["p_value"]})
    out["body_sensitivity"] = sens
    return out


def counts_block() -> dict:
    src = json.loads(COUNTS.read_text())
    beta = V_SUN_CMB / C_KM_S
    n_cmb = AXES_ICRS["cmb_dipole_axis"]
    out, ys, covs, taus = {}, [], [], []
    for name, c_eb in C_EB.items():
        r = src["results"][name]
        d, sd = np.asarray(r["D_icrs"], float), np.asarray(r["sd_axes"], float)
        excess = d - c_eb * beta * n_cmb
        chi2 = float(np.sum((excess / sd) ** 2))
        out[name] = {"D_icrs": d, "sd_axes_including_declared_systematics": sd, "c_EB": c_eb, "kinematic_expectation_amplitude": c_eb * beta,
                     "observed_amplitude": float(np.linalg.norm(d)), "excess_icrs": excess,
                     "excess_test": fv.chi2_null_tail(chi2, 3, "receipt per-axis sd incl. mask/declination systematics; no clustering-dipole term"),
                     "Q_center": math.sqrt(chi2 / stats.chi2.ppf(0.95, 3)),
                     "implied_velocity_km_s_if_kinematic": float(np.linalg.norm(d)) / c_eb * C_KM_S}
        ys.append(excess)
        covs.append(np.diag(sd**2))
        taus.append(c_eb)
    cov = np.zeros((6, 6))
    cov[:3, :3], cov[3:, 3:] = covs
    common = fv.gls_fit(np.concatenate(ys), cov, fv.transport_design(taus, 3))
    out["common_excess_velocity"] = {
        "transport": "excess_k = c_EB,k * beta_excess (one frame offset shared by both catalogues)",
        "beta_excess_km_s_icrs": common["theta"] * C_KM_S, "sd_km_s": np.sqrt(np.diag(common["cov"])) * C_KM_S,
        "wald_3dof": common["wald"], "wald_p_value": float(stats.chi2.sf(common["wald"], 3)),
        "consistency_chi2": common["chi2"], "consistency_dof": common["dof"], "consistency_p_value": common["p_value"]}
    # power of this estimator against a published-size excess: an observed dipole twice the kinematic one along the CMB apex
    doubled = beta * n_cmb
    lam = float(doubled @ np.linalg.solve(common["cov"], doubled))
    out["power_against_doubled_dipole"] = {
        "assumed_excess_km_s": V_SUN_CMB, "direction": "CMB dipole apex", "noncentrality": lam,
        "power_at_alpha_0p05": float(stats.ncx2.sf(stats.chi2.ppf(0.95, 3), 3, lam)),
        "power_at_alpha_0p01": float(stats.ncx2.sf(stats.chi2.ppf(0.99, 3), 3, lam)),
        "note": "a non-detection with this power does not test the published count-dipole excess"}
    out["receipt_status"] = src["status"]
    out["note"] = ("RACS is excluded as in the receipt. The per-axis sd already carries the latitude-cut sweep and the declination "
                   "degeneracy; a clustering-dipole body and a same-estimator velocity null are local obligations (R54-L03).")
    return out


def main() -> None:
    tab = np.loadtxt(PK, delimiter=",", skiprows=1)
    cf4 = cf4_block(tab[:, 0], tab[:, 1])
    counts = counts_block()
    lc = cf4["analysis"]["MEAS_PLUS_LCDM"]
    stis = PUBLISHED["stiskalek_2025_cf4_tfr_zero_point_dipole"]
    bench = {
        "published_anchors": PUBLISHED,
        "zero_point_dipole_percent": {"r54_A_only_with_lcdm_body": lc["dipole"]["A_only"]["percent_of_H"],
                                      "r54_sd_percent": 100.0 * float(np.linalg.norm(lc["dipole"]["A_only"]["sd"])) / cf4["windows"]["H_fit_km_s_Mpc"] / math.sqrt(3),
                                      "stiskalek_2025": stis["percent_of_H"], "stiskalek_sd": stis["sd"],
                                      "note": "different CF4 subsample (all groups vs TF W1) and estimator; agreement is a consistency check, not a replication"},
        "bulk_only_direction": {"r54_V_only_meas_cov_l_b_deg": cf4["analysis"]["MEAS"]["dipole"]["V_only"]["direction_l_b_deg"],
                                "r54_V_only_meas_cov_km_s": cf4["analysis"]["MEAS"]["dipole"]["V_only"]["amplitude_km_s"],
                                "angle_to_watkins_2023_deg": cf4["analysis"]["MEAS"]["dipole"]["V_only"]["angle_to_watkins_2023_deg"]},
        "axis": {"r54_best_template_axis_l_b_deg": lc["axis_locking"]["best_axis"]["l_b_deg"],
                 "angle_to_kalbouneh_2026_axis_deg": angle_deg(gal_unit(*lc["axis_locking"]["best_axis"]["l_b_deg"]), gal_unit(295.0, 5.0), axis=True),
                 "equatorial_pole_l_b_deg": icrs_to_lb(AXES_ICRS["equatorial_pole"])},
    }
    views = fv.five_view_record({
        "x": {"status": fv.AVAILABLE, "coordinates": "4 windows x [D(3), STF5]; km/s/Mpc; ICRS; z_CMB frame", "source": "R36-01 theta4x9"},
        "Q": {"status": fv.AVAILABLE, "body": "ideal-sky linear LCDM cosmic-variance body + R36 measurement covariance (95% ellipsoid)",
              "dipole_Q_center": lc["dipole"]["Q_center"], "quadrupole_Q_center": lc["quadrupole"]["Q_center"]},
        "F": {"status": fv.UNAVAILABLE,
              "reason": "support utilization needs a declared convex body in parameter space; the axis scan is a template statistic and is reported under Pi"},
        "Pi": {"status": fv.AVAILABLE, "law": lc["law"], "dipole_null": lc["dipole"]["null"], "quadrupole_null": lc["quadrupole"]["null"],
               "axis_scan_uncalibrated": lc["axis_locking"]},
        "G_F": {"status": fv.AVAILABLE, "transport_laws": ["V: 1/d", "A: constant"], "dipole_models": lc["dipole"]["models"],
                "delta_chi2_A_minus_V": lc["dipole"]["delta_chi2_A_minus_V_same_parameter_count"]},
    })
    out = {
        "schema": "htt.r54.lowz_frames/1", "node": "R54-L5", "claim_tier": "C0_DIAGNOSTIC_IDEAL_SKY_BODY",
        "provenance": {"script": "scripts/r54/run_r54_lowz_frames.py", "script_sha256": sha256(Path(__file__)),
                       "inputs_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in (CF4, COUNTS, PK)},
                       "python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__},
        "cf4": cf4, "count_dipoles": counts, "benchmark": bench, "five_views": views,
        "limitations": [
            "The LCDM body is ideal-sky and linear; mask coupling, selection and the exact catalogue geometry are not modelled (R54-L05).",
            "The R36 measurement covariance excludes method calibration covariance; chi-square values under MEAS alone are not calibrated.",
            "Axis locking to the equatorial pole indicates a survey-geometry origin but does not identify the responsible sub-sample; the method/hemisphere zero-point split is local (R54-L05).",
            "A constant dH dipole is not separable from a distance zero-point dipole within one distance-indicator sample.",
            "Count dipoles use the receipt estimator with its declared systematic budget; no clustering-dipole body yet (R54-L03).",
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(clean(out), indent=1, sort_keys=True) + "\n")
    print(json.dumps(clean({
        "dip_null_lcdm": lc["dipole"]["null"], "chi2_V": lc["dipole"]["models"]["V_constant_velocity"]["chi2"],
        "chi2_A": lc["dipole"]["models"]["A_constant_dH"]["chi2"], "A_percent": lc["dipole"]["A_only"]["percent_of_H"],
        "A_angle_pole": lc["dipole"]["A_only"]["angle_to_equatorial_pole_axis_deg"], "quad_null": lc["quadrupole"]["null"],
        "quad_axis_angle_pole": lc["quadrupole"]["constant_tensor"]["principal_axis_angle_to_equatorial_pole_deg"],
        "locking": {k: lc["axis_locking"][k] for k in ("delta_chi2_at_reference_axes", "best_axis", "sky_fraction_of_axes_with_gain_at_least_equatorial_pole", "equatorial_pole_fit")},
        "counts": {k: v["excess_test"] for k, v in counts.items() if isinstance(v, dict) and "excess_test" in v},
        "common": counts["common_excess_velocity"]}), indent=1))


if __name__ == "__main__":
    main()
