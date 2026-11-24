"""R108 A8 (H05 first step) and A7 CF4 frame: joint coherent bulk flow + expansion dipole on the R98 CF4 windows.

Purpose
    The H05 rejection condition (R105 CF4_LITERATURE_H05.md) asks for a joint fit of the signed
    Cartesian components of an intrinsic linear expansion dipole and a radial flow on the same
    objects, windows, zero point and covariance, with a pre-fixed holdout. This script does the
    first executable step with data already in the repository:
      * replays the R98 four-window CF4 log-distance fit (35,970 groups, 0.01<z<0.1, windows
        z=0.025/0.040/0.060/0.080, sigma_z=0.012) and checks it against R98 CF4_P1_RESULTS.json;
      * builds the exact linear responses of the 36 fitted coefficients to (i) a coherent bulk
        velocity B (km/s, CMB frame of the release) and (ii) an expansion dipole h
        (H(n) = Hbar (1 + h.n)), both through the same fixed-weight window operator;
      * fits nested models (free window monopoles and quadrupoles in all models):
        M0 none, MB bulk, MH expansion dipole, MBH both, MD free dipole per window;
      * distance holdout fixed before the fit: inner windows (0.025, 0.040) -> outer windows
        (0.060, 0.080) dipole prediction with the Schur conditional (R98 construction);
      * covariance variants: 'working' (R98 law: independent modulus error + 250 km/s
        nonlinear velocity), 'working+calibration' (R98 7-channel method calibration block:
        SNIa-gauge rank-5 overlap covariance, common 0.087 mag, DirectCal 0.5 mag);
      * projects h on the two literature W1 zero-point axes (R105 CF4_H05_AXES.json).
    The coherent large-scale peculiar-velocity covariance is not included (R98 saved only its
    diagnostics), so every number here is CONDITIONAL on the working covariance.

Inputs (SHA-256 checked or recorded)
    docs/research_program/cf4_schur_loop8_20261015/inputs/selected_source_observables.npz (86dfd896...)
    /mnt/extdrive/workdir/raw/cf4_full/table3.dat, table4.dat, ReadMe (via scripts.r98.cf4_p1.catalog)
    docs/research_program/observational_publication_20261015/R98_FOURTH_RESEARCH_CYCLE_20261123/CF4_P1_RESULTS.json
    docs/research_program/observational_publication_20261015/R105_RESEARCH_20261124/CF4_H05_AXES.json
    docs/.../R108_LOS_ATLAS_DATA_20261124/FRAME/CATALOGUE_FRAME_REGISTRY.json (frame_registry_build.py output;
        used for the frame-convention systematic: release linear Vh->V3k sum versus the exact transform,
        release (Fixsen-like) beta versus Planck 2018 beta, registry keys only)

Units
    B km/s (Galactic and ICRS Cartesian); h dimensionless (ln H dipole); coefficients natural log.

Usage
    PYTHONPATH=.:htt:htt/src .venv/bin/python -m scripts.r108.frame_cf4_joint \
        --output docs/research_program/observational_publication_20261015/R108_LOS_ATLAS_DATA_20261124/FRAME/CF4_BULK_HDIPOLE_JOINT.json
    Deterministic; no random numbers.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
from scipy.linalg import cho_factor, cho_solve

from obsstat.catalogue_frame_registry import FrameRegistry
from scripts.r108.common import OUT_DIR, REPO, git_state, sha256_file, write_json

R98_JSON = REPO / "docs/research_program/observational_publication_20261015/R98_FOURTH_RESEARCH_CYCLE_20261123/CF4_P1_RESULTS.json"
H05_AXES = REPO / "docs/research_program/observational_publication_20261015/R105_RESEARCH_20261124/CF4_H05_AXES.json"
OUTFILE = OUT_DIR / "FRAME/CF4_BULK_HDIPOLE_JOINT.json"
REGISTRY_JSON = OUT_DIR / "FRAME/CATALOGUE_FRAME_REGISTRY.json"
CF4_RELEASE_ID = "CF4_groups_J_ApJ_944_94_table4"  # registry release whose Vh/V3k are transformed
C_KMS = 299792.458
MAG = math.log(10.0) / 5.0
# ReadMe J/ApJ/944/94 Note (6): f = 1 + (1-q0) z/2 - (1 - q0 - 3 q0^2 + j0) z^2/6, Omega_m=0.27, Omega_L=0.73
OMEGA_M_CF4, OMEGA_L_CF4 = 0.27, 0.73
Q0 = OMEGA_M_CF4 / 2.0 - OMEGA_L_CF4
J0 = 1.0
NUIS_SLOTS = [0, 4, 5, 6, 7, 8]  # monopole + 5 STF per window
DIP_SLOTS = [1, 2, 3]


def f_curv(z):
    z = np.asarray(z, float)
    return 1.0 + 0.5 * (1.0 - Q0) * z - (1.0 - Q0 - 3.0 * Q0 ** 2 + J0) * z ** 2 / 6.0


def dlnf_dz(z):
    z = np.asarray(z, float)
    return (0.5 * (1.0 - Q0) - (1.0 - Q0 - 3.0 * Q0 ** 2 + J0) * z / 3.0) / f_curv(z)


def bulk_rows(z, n):
    """d y_i / d B (per km/s): y = ln(fV3k) - ..., 1+z_obs = (1+z_cos)(1+B.n/c)."""
    z = np.asarray(z, float)
    return ((1.0 + z) * (1.0 / z + dlnf_dz(z)) / C_KMS)[:, None] * n


def hdipole_rows(z, n):
    """d y_i / d h for H(n) = Hbar (1 + h.n) at fixed distance: dz = z h.n."""
    z = np.asarray(z, float)
    return (1.0 + z * dlnf_dz(z))[:, None] * n


def nuisance_design(n_windows: int = 4) -> np.ndarray:
    P = np.zeros((9 * n_windows, len(NUIS_SLOTS) * n_windows))
    for w in range(n_windows):
        for j, s in enumerate(NUIS_SLOTS):
            P[9 * w + s, len(NUIS_SLOTS) * w + j] = 1.0
    return P


def free_dipole_design(n_windows: int = 4) -> np.ndarray:
    P = np.zeros((9 * n_windows, 3 * n_windows))
    for w in range(n_windows):
        for j, s in enumerate(DIP_SLOTS):
            P[9 * w + s, 3 * w + j] = 1.0
    return P


def gls(y, D, C):
    cf = cho_factor(C, lower=True)
    CiD = cho_solve(cf, D)
    F = D.T @ CiD
    cov = np.linalg.inv(F)
    beta = cov @ (CiD.T @ y)
    r = y - D @ beta
    chi2 = float(r @ cho_solve(cf, r))
    return beta, 0.5 * (cov + cov.T), chi2


def schur_predict(y, D, C, train, test):
    """GLS on the train rows, conditional Gaussian prediction of the test rows (R98 form)."""
    Ctt, Cst, Css = C[np.ix_(train, train)], C[np.ix_(test, train)], C[np.ix_(test, test)]
    Dt, Ds = D[train], D[test]
    cf = cho_factor(Ctt, lower=True)
    CiD = cho_solve(cf, Dt)
    keep = np.linalg.norm(Dt, axis=0) > 0  # parameters identified by the training rows
    Dt_k, Ds_k, CiD_k = Dt[:, keep], Ds[:, keep], CiD[:, keep]
    covb = np.linalg.inv(Dt_k.T @ CiD_k)
    b = covb @ (CiD_k.T @ y[train])
    resid = y[train] - Dt_k @ b
    pred = Ds_k @ b + Cst @ cho_solve(cf, resid)
    Hs = Ds_k - Cst @ CiD_k
    Cp = Css - Cst @ cho_solve(cf, Cst.T) + Hs @ covb @ Hs.T
    Cp = 0.5 * (Cp + Cp.T)
    if np.any(np.linalg.norm(Ds[:, ~keep], axis=0) > 0):
        raise ValueError("test rows depend on parameters the training rows do not identify")
    L = np.linalg.cholesky(Cp)
    e = np.linalg.solve(L, y[test] - pred)
    chi2 = float(e @ e)
    logdet = float(2 * np.sum(np.log(np.diag(L))))
    return {"chi2": chi2, "dof": int(len(test)), "log_predictive_density": float(-0.5 * (chi2 + logdet + len(test) * math.log(2 * math.pi))),
            "prediction": pred.tolist(), "observed": y[test].tolist(), "pred_sd": np.sqrt(np.diag(Cp)).tolist()}


def icrs_to_gal_matrix():
    from astropy.coordinates import SkyCoord
    cols = [SkyCoord(x=e[0], y=e[1], z=e[2], representation_type="cartesian", frame="icrs").galactic.cartesian.xyz.value
            for e in np.eye(3)]
    return np.array(cols).T  # v_gal = M @ v_icrs


def lb(v):
    v = np.asarray(v, float)
    r = float(np.linalg.norm(v))
    return {"amplitude": r, "l_deg": math.degrees(math.atan2(v[1], v[0])) % 360.0,
            "b_deg": math.degrees(math.asin(v[2] / r)) if r > 0 else float("nan")}


def vector_summary(est, cov, Mg, scale=1.0):
    est = np.asarray(est) * scale
    cov = np.asarray(cov) * scale ** 2
    g = Mg @ est
    gc = Mg @ cov @ Mg.T
    s = lb(g)
    u = g / s["amplitude"]
    s.update({"icrs": est.tolist(), "icrs_cov": cov.tolist(), "galactic": g.tolist(), "galactic_cov": gc.tolist(),
              "amplitude_sd_linear": float(math.sqrt(u @ gc @ u)),
              "wald_zero": float(g @ np.linalg.solve(gc, g))})
    return s


def run(output: Path) -> dict:
    t0 = time.perf_counter()
    from scripts.r95 import sq_cf4_synthesis as r95
    from scripts.r97 import cf4_genealogy_and_partial_id as r97
    from scripts.r98 import cf4_p1 as r98

    H = r95._load_h03()
    inp = H.source(r95.SELECT)
    ids, mu, emu, cz, v, ds, wf, ramp, n, vls = r98.catalog()
    z = cz / C_KMS
    selected = (z >= .01) & (z <= .10)
    sel = np.flatnonzero(selected)[np.argsort(ids[selected])]
    if not np.array_equal(ids[sel], inp.ids):
        raise ValueError("R98 selected identity drift")
    # fV3k = f(z) V3k replay (ReadMe Note 6); integer rounding of both columns
    fv_resid = v[sel] - f_curv(z[sel]) * cz[sel]
    X, y, sig, A, cov_work, b = r98.tomography(H, n[sel], cz[sel], v[sel], mu[sel], emu[sel])
    theta = b.ravel()
    r98j = json.loads(R98_JSON.read_text())
    replay_b = float(np.max(abs(theta - np.ravel(r98j["fit"]["selected_log_coefficients_4x9"]))))
    replay_c = float(np.max(abs(cov_work - np.asarray(r98j["fit"]["selected_log_covariance_36x36"]))))
    if replay_b > 1e-10 or replay_c > 1e-12:
        raise ArithmeticError(f"R98 replay failed: coef {replay_b}, cov {replay_c}")

    # calibration block (R98 construction)
    t3 = r97._parse_complete_table3_for_selected(ids)
    W = r98.magnitude_weights(t3)[sel]
    f = r97.cf4_p0b.profile_method_offsets(t3["dm_vals_6"][sel], t3["e_vals_6"][sel])
    cov5 = f["cov_working_mag2"][1:, 1:]
    Sigma_cal = np.zeros((7, 7))
    Sigma_cal[1:6, 1:6] = cov5
    Sigma_cal += 0.087 ** 2 * np.ones((7, 7))
    Sigma_cal[6, 6] += 0.5 ** 2
    T = -MAG * (A @ W)
    C_cal = T @ Sigma_cal @ T.T
    covs = {"working": cov_work, "working_plus_calibration": 0.5 * (cov_work + C_cal + (cov_work + C_cal).T)}

    nsel, zsel = n[sel], z[sel]
    J_B = A @ bulk_rows(zsel, nsel)     # 36 x 3 per km/s (ICRS components)
    J_H = A @ hdipole_rows(zsel, nsel)  # 36 x 3 (ICRS components)
    P = nuisance_design()
    Dfree = free_dipole_design()
    designs = {"M0_none": P, "MB_bulk": np.hstack([P, J_B]), "MH_expansion_dipole": np.hstack([P, J_H]),
               "MBH_bulk_plus_expansion_dipole": np.hstack([P, J_B, J_H]), "MD_free_dipole_per_window": np.hstack([P, Dfree])}
    # effective 1/z of each window dipole response (diagnostic of separability)
    resp = {"bulk_dipole_response_diag_per_kms": [float(np.mean(np.diag(J_B[9 * w + 1:9 * w + 4]))) for w in range(4)],
            "hdipole_response_diag": [float(np.mean(np.diag(J_H[9 * w + 1:9 * w + 4]))) for w in range(4)]}
    resp["implied_z_eff"] = [float(resp["hdipole_response_diag"][w] / (resp["bulk_dipole_response_diag_per_kms"][w] * C_KMS))
                             for w in range(4)]
    Mg = icrs_to_gal_matrix()
    axes = json.loads(H05_AXES.read_text())["axes"]
    npar = P.shape[1]
    results = {}
    for cname, C in covs.items():
        res = {}
        for mname, D in designs.items():
            beta, cb, chi2 = gls(theta, D, C)
            entry = {"chi2": chi2, "dof": int(36 - D.shape[1]), "n_params": int(D.shape[1])}
            if mname in ("MB_bulk", "MBH_bulk_plus_expansion_dipole"):
                entry["bulk_kms"] = vector_summary(beta[npar:npar + 3], cb[npar:npar + 3, npar:npar + 3], Mg)
            if mname in ("MH_expansion_dipole", "MBH_bulk_plus_expansion_dipole"):
                k = npar + (3 if mname.startswith("MBH") else 0)
                hs = vector_summary(beta[k:k + 3], cb[k:k + 3, k:k + 3], Mg)
                proj = {}
                for ax, a in axes.items():
                    u = np.asarray(a["unit_icrs"])
                    val = float(u @ beta[k:k + 3]); sd = float(math.sqrt(u @ cb[k:k + 3, k:k + 3] @ u))
                    proj[ax] = {"h_dot_axis": val, "sd": sd, "as_mag_zero_point": val / MAG, "as_mag_sd": sd / MAG,
                                "literature_axis_galactic_lb_deg": a["galactic_lb_deg"]}
                hs["projection_on_literature_axes"] = proj
                entry["expansion_dipole_h"] = hs
                if mname.startswith("MBH"):
                    cbh = cb[npar:npar + 3, k:k + 3]
                    entry["corr_bulk_h_icrs"] = (cbh / np.sqrt(np.outer(np.diag(cb[npar:npar + 3, npar:npar + 3]), np.diag(cb[k:k + 3, k:k + 3])))).tolist()
            res[mname] = entry
        for a_, b_ in (("M0_none", "MB_bulk"), ("M0_none", "MH_expansion_dipole"), ("MB_bulk", "MBH_bulk_plus_expansion_dipole"),
                       ("MH_expansion_dipole", "MBH_bulk_plus_expansion_dipole"), ("MBH_bulk_plus_expansion_dipole", "MD_free_dipole_per_window")):
            res[f"delta_chi2_{a_}_to_{b_}"] = {"delta_chi2": res[a_]["chi2"] - res[b_]["chi2"],
                                               "delta_params": res[b_]["n_params"] - res[a_]["n_params"]}
        # distance holdout: train = all 18 inner coefficients, test = 6 outer dipole coefficients
        train = list(range(18))
        test = [9 * w + s for w in (2, 3) for s in DIP_SLOTS]
        hold = {}
        for mname, D in designs.items():
            if mname == "MD_free_dipole_per_window":
                continue
            Dh = D.copy()
            Dh[test] = D[test]
            try:
                hold[mname] = schur_predict(theta, Dh, C, train, test)
            except ValueError as exc:
                hold[mname] = {"error": str(exc)}
        res["distance_holdout_inner_to_outer_dipoles"] = hold
        # leave-one-window-out stability of MBH
        lowo = {}
        for w in range(4):
            keep = [i for i in range(36) if i // 9 != w]
            D = designs["MBH_bulk_plus_expansion_dipole"][keep]
            D = D[:, np.linalg.norm(D, axis=0) > 0]
            beta, cb, chi2 = gls(theta[keep], D, C[np.ix_(keep, keep)])
            k = D.shape[1] - 6
            lowo[f"drop_window_{w}"] = {"bulk_kms": vector_summary(beta[k:k + 3], cb[k:k + 3, k:k + 3], Mg),
                                        "expansion_dipole_h": vector_summary(beta[k + 3:k + 6], cb[k + 3:k + 6, k + 3:k + 6], Mg),
                                        "chi2": chi2, "dof": int(len(keep) - D.shape[1])}
        res["leave_one_window_out_MBH"] = lowo
        results[cname] = res

    # ---- frame-convention systematic (registry keys only; SQ-FRAME -> H05) ----
    reg = FrameRegistry.from_json(REGISTRY_JSON)
    rows4 = [ln for ln in (r97.RAW_CF4 / "table4.dat").read_text(encoding="ascii").splitlines() if ln.strip()]
    ids4 = np.array([int(ln[0:7]) for ln in rows4])
    vh = np.array([float(ln[27:32]) for ln in rows4])
    if not np.array_equal(ids4, ids):
        raise ValueError("table4 row order differs from scripts.r98.cf4_p1.catalog()")
    n_gal = nsel @ Mg.T
    zh = vh[sel] / C_KMS
    # every transform names the data's release (CF4 groups, heliocentric Vh); the Planck 2018 dipole is the
    # registered reference of the Planck PR3 release and acts on CF4 data in the barycentre frame it states
    rid = CF4_RELEASE_ID
    z_rel, _ = reg.photon_to_rest("cf4_t4_helio_to_cmb", zh, n_gal, release_id=rid)  # release convention (linear sum)
    z_ex, _ = reg.photon_to_rest("cf4_t4_helio_to_cmb", zh, n_gal, formula="exact_relativistic", release_id=rid)
    z_pl, _ = reg.photon_to_rest("planck2018_solar_dipole", zh, n_gal, formula="exact_relativistic", release_id=rid)
    z_pl_lin, _ = reg.photon_to_rest("planck2018_solar_dipole", zh, n_gal, formula="linear_cz_sum", release_id=rid)
    lnfz = lambda zz: np.log(f_curv(zz) * zz)
    rel_check = C_KMS * z_rel - cz[sel]
    variants = {"release_linear_fixsen_beta": np.zeros(36),
                "exact_relativistic_release_beta": A @ (lnfz(z_ex) - lnfz(z_rel)),
                "exact_relativistic_planck2018_beta": A @ (lnfz(z_pl) - lnfz(z_rel)),
                "linear_planck2018_beta": A @ (lnfz(z_pl_lin) - lnfz(z_rel))}
    frame_sys = {"registry_json_sha256": sha256_file(REGISTRY_JSON),
                 "keys": ["cf4_t4_helio_to_cmb", "planck2018_solar_dipole"], "release_id": rid,
                 "release_reconstruction_V3k_minus_registry_kms": {"max_abs": float(np.max(abs(rel_check))),
                                                                   "rms": float(np.sqrt(np.mean(rel_check ** 2)))},
                 "variants": {}}
    for vname, dth in variants.items():
        out = {"delta_dipole_icrs_per_window": [dth[9 * w + 1:9 * w + 4].tolist() for w in range(4)],
               "delta_monopole_per_window": [float(dth[9 * w]) for w in range(4)]}
        for mname in ("MB_bulk", "MH_expansion_dipole", "MBH_bulk_plus_expansion_dipole"):
            beta, cb, chi2 = gls(theta + dth, designs[mname], covs["working"])
            e = {"chi2": chi2}
            k = npar
            if "bulk" in mname:
                e["bulk_kms"] = {kk: vv for kk, vv in vector_summary(beta[k:k + 3], cb[k:k + 3, k:k + 3], Mg).items()
                                 if kk in ("amplitude", "l_deg", "b_deg", "galactic", "amplitude_sd_linear")}
                k += 3
            if "expansion" in mname:
                e["expansion_dipole_h"] = {kk: vv for kk, vv in vector_summary(beta[k:k + 3], cb[k:k + 3, k:k + 3], Mg).items()
                                           if kk in ("amplitude", "l_deg", "b_deg", "galactic", "amplitude_sd_linear")}
            out[mname] = e
        frame_sys["variants"][vname] = out
    base = frame_sys["variants"]["release_linear_fixsen_beta"]
    for vname, out in frame_sys["variants"].items():
        out["shift_vs_release_working"] = {
            m: {q: (np.asarray(out[m][q]["galactic"]) - np.asarray(base[m][q]["galactic"])).tolist()
                for q in ("bulk_kms", "expansion_dipole_h") if q in out[m]}
            for m in ("MB_bulk", "MH_expansion_dipole", "MBH_bulk_plus_expansion_dipole")}

    payload = {
        "schema": "htt.r108.frame.cf4_bulk_hdipole_joint/1",
        "nodes": ["H05 (first executable step)", "SQ-LIE-FLUX CF4 frame input"],
        "label": "CONDITIONAL: working covariance without coherent large-scale peculiar-velocity covariance; "
                 "CF4 all-method groups, not the W1 Tully-Fisher subset of the literature (not the same estimand)",
        "git": git_state(), "command": " ".join(sys.argv),
        "code_sha256": {c: sha256_file(REPO / c) for c in (
            "scripts/r108/frame_cf4_joint.py", "scripts/r108/frame_registry_build.py", "scripts/r108/common.py",
            "htt/obsstat/catalogue_frame_registry.py", "htt/obsstat/publication_frame_kinematics.py",
            "scripts/r98/cf4_p1.py", "scripts/r97/cf4_genealogy_and_partial_id.py", "htt/obsstat/cf4_p0b.py")},
        "inputs": {"selected": {"path": str(r95.SELECT), "sha256": sha256_file(r95.SELECT)},
                   "cf4_table3": {"path": str(r97.RAW_CF4 / 'table3.dat'), "sha256": sha256_file(r97.RAW_CF4 / 'table3.dat')},
                   "cf4_table4": {"path": str(r97.RAW_CF4 / 'table4.dat'), "sha256": sha256_file(r97.RAW_CF4 / 'table4.dat')},
                   "cf4_ReadMe": {"path": str(r97.RAW_CF4 / 'ReadMe'), "sha256": sha256_file(r97.RAW_CF4 / 'ReadMe')},
                   "r98_results": {"path": str(R98_JSON.relative_to(REPO)), "sha256": sha256_file(R98_JSON)},
                   "r105_h05_axes": {"path": str(H05_AXES.relative_to(REPO)), "sha256": sha256_file(H05_AXES)},
                   "h03_module": {"path": str(r95.H03_PY.relative_to(REPO)), "sha256": sha256_file(r95.H03_PY)},
                   "frame_registry": {"path": str(REGISTRY_JSON.relative_to(REPO)), "sha256": sha256_file(REGISTRY_JSON)}},
        "definitions": {
            "coefficients": "R98 36-vector: 4 windows x [monopole, nx, ny, nz (ICRS), 5 STF] of y = ln(fV3k/74.6) - (ln10/5)(DMzp-25)",
            "bulk_response": "1+z_obs=(1+z)(1+B.n/c); dy/dB = (1+z)(1/z + dlnf/dz) n / c, f from ReadMe Note 6 (Omega_m 0.27, Omega_L 0.73)",
            "expansion_dipole_response": "H(n)=Hbar(1+h.n) at fixed distance; dy/dh = (1 + z dlnf/dz) n",
            "nuisance": "free monopole and 5 STF coefficients in every window (a common zero point moves monopoles only)",
            "window_weights_held_fixed": "weights use the observed z; second-order change of weights under B or h is neglected",
            "holdout": "pre-fixed: train on all 18 inner-window coefficients (z=0.025, 0.040), predict the 6 outer-window dipole coefficients (z=0.060, 0.080)",
            "literature_axes": "R105 CF4_H05_AXES.json unit_icrs (Boubel 2025 fig4 (142,52); Stiskalek 2026 sec4.1 (127,10)); as_mag = (h.axis)/(ln10/5)",
            "frame": "CF4 release CMB frame (V3k); conversion to the Planck 2018 frame is applied in frame_lie_flux.py with registry keys"},
        "replay": {"coefficients_max_abs_vs_R98": replay_b, "covariance_max_abs_vs_R98": replay_c,
                   "fV3k_minus_f_V3k_kms": {"max_abs": float(np.max(abs(fv_resid))), "rms": float(np.sqrt(np.mean(fv_resid ** 2)))},
                   "n_groups": int(len(sel))},
        "calibration_block": {"Sigma_cal_7x7": Sigma_cal.tolist(), "trace_C_cal": float(np.trace(C_cal)),
                              "method_order": r98.METHODS,
                              "construction": "R98 cf4_p1: T=-(ln10/5) A W; Sigma = SNIa-gauge rank-5 overlap cov5 + 0.087^2 common + 0.5^2 DirectCal"},
        "responses": resp,
        "results": results,
        "frame_convention_systematic": frame_sys,
        "not_included": ["coherent large-scale peculiar-velocity covariance of the 36-vector (R98 computed it in-run; matrices not saved)",
                         "selection (Malmquist/boundary) covariance block of R98",
                         "W1 Tully-Fisher object list, photometry and line widths of Boubel 2025 / Stiskalek 2026 (same-estimand comparison)",
                         "cross-covariance of shared W1 objects between the two papers"],
        "runtime_s": time.perf_counter() - t0,
    }
    write_json(output, payload)
    return payload


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--output", type=Path, default=OUTFILE)
    a = ap.parse_args(argv)
    p = run(a.output)
    out = {"replay": p["replay"], "responses": p["responses"]}
    for c, r in p["results"].items():
        out[c] = {m: {k: (v if k in ("chi2", "dof") else None) for k, v in e.items() if k in ("chi2", "dof")}
                  for m, e in r.items() if isinstance(e, dict) and "chi2" in e}
        mbh = r["MBH_bulk_plus_expansion_dipole"]
        out[c]["MBH_bulk"] = {k: mbh["bulk_kms"][k] for k in ("amplitude", "l_deg", "b_deg", "amplitude_sd_linear", "wald_zero")}
        out[c]["MBH_h"] = {k: mbh["expansion_dipole_h"][k] for k in ("amplitude", "l_deg", "b_deg", "amplitude_sd_linear", "wald_zero")}
        out[c]["holdout"] = {m: {k: h.get(k) for k in ("chi2", "dof", "log_predictive_density")} for m, h in r["distance_holdout_inner_to_outer_dipoles"].items()}
    out["frame_convention_systematic"] = {
        v: {"MBH_shift_bulk_kms_gal": o["shift_vs_release_working"]["MBH_bulk_plus_expansion_dipole"]["bulk_kms"],
            "MBH_shift_h_gal": o["shift_vs_release_working"]["MBH_bulk_plus_expansion_dipole"]["expansion_dipole_h"],
            "MH_shift_h_gal": o["shift_vs_release_working"]["MH_expansion_dipole"]["expansion_dipole_h"],
            "MB_shift_bulk_kms_gal": o["shift_vs_release_working"]["MB_bulk"]["bulk_kms"]}
        for v, o in p["frame_convention_systematic"]["variants"].items()}
    out["release_reconstruction"] = p["frame_convention_systematic"]["release_reconstruction_V3k_minus_registry_kms"]
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
