"""R52: joint identification of shear / acceleration / tilt / boost from owned carriers.

Run: PYTHONPATH=htt/src:htt:. python scripts/r52/run_r52_joint.py [--no-cobaya]

Probes (all compact carriers already owned; raw catalogues only read for the Quaia z law):
  CMB_Sigma   R51 SMICA PR3 T45 integrated shear (LOO-calibrated covariance), Galactic
  Gaia_E2     R50 Quaia-G20.0 PM carrier (spin+glide profiled), ICRS, uas/yr
  Quaia/NVSS/RACS count dipoles (R49 carriers), ICRS
  CMB_dipole  Planck 2018 I solar dipole (published measurement), Galactic
  CF4_H03     R36 36-coordinate four-window apparent-H operator, ICRS, km/s/Mpc
Pantheon+ is not used (shares hosts/velocity field with CF4 and its z_HD carries
2M++ PV corrections that remove the bulk flow targeted here).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from astropy.io import fits
from scipy.stats import chi2

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "htt"), str(ROOT / "htt/src")]

from htt.htt.infer.r49_general_bianchi_likelihood import ICRS_TO_GALACTIC_MATRIX  # noqa: E402
from htt.htt.infer.r51_source_bound_response import (  # noqa: E402
    bianchi_i_shear_history_integral, radiation_density_parameter,
)
from htt.htt.infer.r52_joint_identification import (  # noqa: E402
    C_KM_S, SL, THETA_NAMES, LinearProbe, block_ranks, cf4_h03_design, chi2_at, cmb_dipole_design,
    count_dipole_design, effective_dof, endpoint_history_factor, gaussian_posterior, h0_uas_per_year,
    identification, joint, stf5_rotation,
)

P = ROOT / "docs/research_program/observational_publication_20261015"
R50 = P / "R50_OBSERVED_CONVERGENCE_20261115"
OUT = R50 / "R52"
CHAINS = Path("/mnt/extdrive/workdir/r52_chains")
R49_NPZ = Path("/mnt/extdrive/workdir/r49_chains/r49_real_multiprobe_dataset.npz")
CF4_NPZ = Path("/mnt/extdrive/workdir/htt_open_data/r36_cf4_exact_operator_actual/A_RAW_36x35970.npz")
CF4_COV = Path("/mnt/extdrive/workdir/htt_open_data/r36_cf4_correlated_actual/RESULT_MATRICES.npz")
QUAIA20 = Path("/mnt/extdrive/workdir/raw/observational_bundles/Quaia_zenodo_10403370_v1.0.0/quaia_G20.0.fits")
PLANCK18 = {"H0": 67.36, "Omega_m": 0.3153}
SOLAR_DIPOLE = {"amp_uK": 3362.08, "amp_err_uK": 0.99, "l_deg": 264.021, "b_deg": 48.253}  # Planck 2018 I
T_CMB_UK = 2.72548e6
# Ellis-Baldwin factors: Quaia x measured (R40 loop02, G<20.5), alpha=0.5 assumed; radio literature-approximate.
C_EB = {"Quaia": 3.7386422874798133, "NVSS": 3.5, "RACS": 3.6}
# Declared reference scales == proper prior SDs, fixed BEFORE posterior evaluation (rank recorded first).
SCALE = np.array([1e-2] * 5 + [1.0] * 3 + [1.0] * 3 + [1e-2] * 3 + [1e-2] * 3)
R_G2I = ICRS_TO_GALACTIC_MATRIX.T
M5_G2I = stf5_rotation(R_G2I)


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def zero_J(n: int) -> np.ndarray:
    return np.zeros((n, 17))


_QUAIA_CACHE: dict = {}


def quaia_z_weights():
    if not _QUAIA_CACHE:
        with fits.open(QUAIA20, memmap=True) as h:
            d = h[1].data
            _QUAIA_CACHE["z"] = np.asarray(d["redshift_quaia"], float)
            _QUAIA_CACHE["w"] = 1.0 / np.asarray(d["pmra_error"], float) ** 2 + 1.0 / np.asarray(d["pmdec_error"], float) ** 2
    return _QUAIA_CACHE["z"], _QUAIA_CACHE["w"]


def build_probes(om_r: float, variant: dict) -> tuple[list[LinearProbe], dict]:
    meta: dict = {}
    om, ol = PLANCK18["Omega_m"], 1 - PLANCK18["Omega_m"] - om_r
    # --- CMB integrated shear (R51)
    with np.load(R50 / "R51/observed_carrier.npz", allow_pickle=False) as z:
        F51, t51, loo = z["F_T45"], z["t_T45"], z["null_loo_shat_300x5"]
    sig_hat = np.linalg.solve(F51, t51)
    C_emp = np.cov(loo.T, ddof=1)
    I_hist = bianchi_i_shear_history_integral(om, om_r, ol, 1089.94)
    J = zero_J(5); J[:, SL["sigma"]] = I_hist * np.eye(5)
    probes = [LinearProbe("CMB_Sigma", sig_hat, 0.5 * (C_emp + C_emp.T), J, block_id="R51:observed_carrier.npz", frame="Galactic")]
    meta["I_hist"] = I_hist
    # --- Gaia E2 (R50 carrier, Quaia G<20.0)
    g = json.loads((R50 / "OBSERVED_GAIA_BENCHMARK.json").read_text())["nuisance_models"]["primary_spin_glide6"]
    zq, w = quaia_z_weights()
    zg = np.linspace(0.0, max(5.0, float(zq.max())), 801)
    Kg = np.array([1.0] + [endpoint_history_factor(z_, om, om_r, ol) for z_ in zg[1:]])
    Ki = np.interp(np.clip(zq, 0, None), zg, Kg)
    K_eff = float(np.sum(w * Ki) / np.sum(w))
    meta["gaia"] = {"K_eff_information_weighted": K_eff, "K_percentiles_16_50_84": np.percentile(Ki, [16, 50, 84]).tolist(),
                    "n_sources": int(zq.size), "z_median": float(np.median(zq)),
                    "approximation": "information-weighted mean K replaces per-source design weighting"}
    K_use = K_eff * variant.get("gaia_K_scale", 1.0)
    h0u = h0_uas_per_year(PLANCK18["H0"])
    J = zero_J(5); J[:, SL["sigma"]] = h0u * K_use * M5_G2I
    C_g = np.asarray(g["covariance_stf5_uasyr2"], float)
    probes.append(LinearProbe("Gaia_E2", np.asarray(g["mean_stf5_uasyr"], float), 0.5 * (C_g + C_g.T), J,
                              block_id="R36-03:full_stats.npz", frame="ICRS"))
    meta["H0_uas_per_yr"] = h0u
    # --- count dipoles (Ellis-Baldwin, beta_MO), optional cross-correlation
    with np.load(R49_NPZ, allow_pickle=False) as z:
        dips = {"Quaia": (z["quaia_d_icrs"].copy(), z["quaia_cov_icrs"].copy()),
                "NVSS": (z["nvss_d_icrs"].copy(), z["nvss_cov_icrs"].copy()),
                "RACS": (z["racs_d_icrs"].copy(), z["racs_cov_sys_icrs"].copy())}
    ceb_scale = variant.get("c_eb_scale", 1.0)
    rho = variant.get("dipole_rho", 0.0)
    if rho == 0.0:
        for k, (dv, Cv) in dips.items():
            J = count_dipole_design(C_EB[k] * ceb_scale, R_G2I)
            probes.append(LinearProbe(f"{k}_dipole", dv, 0.5 * (Cv + Cv.T), J, block_id=f"R49:{k}", frame="ICRS"))
    else:
        keys = list(dips)
        y = np.concatenate([dips[k][0] for k in keys])
        C = np.zeros((9, 9)); J = zero_J(9)
        sq = {k: np.linalg.cholesky(0.5 * (dips[k][1] + dips[k][1].T)) for k in keys}
        for i, ki in enumerate(keys):
            J[3 * i:3 * i + 3] = count_dipole_design(C_EB[ki] * ceb_scale, R_G2I)
            for j, kj in enumerate(keys):
                C[3 * i:3 * i + 3, 3 * j:3 * j + 3] = dips[ki][1] if i == j else rho * sq[ki] @ sq[kj].T
        probes.append(LinearProbe("count_dipoles_correlated", y, 0.5 * (C + C.T), J, block_id="R49:counts", frame="ICRS"))
    # --- CMB dipole (Planck 2018): observer rel. radiation = beta_MO - beta_RM(0) at first order
    l, b = math.radians(SOLAR_DIPOLE["l_deg"]), math.radians(SOLAR_DIPOLE["b_deg"])
    beta = SOLAR_DIPOLE["amp_uK"] / T_CMB_UK
    y = beta * np.array([math.cos(b) * math.cos(l), math.cos(b) * math.sin(l), math.sin(b)])
    J = cmb_dipole_design()
    probes.append(LinearProbe("CMB_dipole", y, (SOLAR_DIPOLE["amp_err_uK"] / T_CMB_UK) ** 2 * np.eye(3), J,
                              block_id="Planck2018I:solar_dipole", frame="Galactic"))
    # --- CF4 four-window apparent-H operator
    with np.load(CF4_NPZ, allow_pickle=False) as z:
        th36, AN = z["theta36"].copy(), z["AN"].copy()
    with np.load(CF4_COV, allow_pickle=False) as z:
        C36 = z["conditional_R5"].copy()
    windows = variant.get("cf4_windows", [0, 1, 2, 3])
    rows = np.concatenate([np.arange(9 * w_, 9 * w_ + 9) for w_ in windows])
    J = cf4_h03_design(AN, PLANCK18["H0"], R_G2I)
    N = np.zeros((36, 4))
    for w_ in range(4):
        N[9 * w_, w_] = 1.0
    if variant.get("cf4_calibration_dipole"):
        # fractional distance-calibration dipole common to all windows: delta H_w = h_w (n.c)
        Ncal = np.zeros((36, 3))
        for w_ in range(4):
            Ncal[9 * w_ + 1:9 * w_ + 4, :] = th36[9 * w_] * np.eye(3)
        N = np.hstack([N, Ncal])
    Cc = 0.5 * (C36 + C36.T) * variant.get("cf4_cov_scale", 1.0)
    sb = variant.get("cf4_bulk_sd_kms", 0.0)
    if sb:
        Cc = Cc + sb**2 * AN @ AN.T
    keep_n = [w_ for w_ in range(4) if w_ in windows] + list(range(4, N.shape[1]))
    probes.append(LinearProbe("CF4_H03", th36[rows], Cc[np.ix_(rows, rows)], J[rows], N[np.ix_(rows, keep_n)],
                              block_id="R36-01:A_RAW_36x35970", frame="ICRS"))
    drop = set(variant.get("drop", []))
    return [p for p in probes if p.name not in drop], meta


def summarize(probes, label):
    jt = joint(probes)
    ident = identification(jt["F"], rel_tol=1e-10)
    mean, cov = gaussian_posterior(jt["F"], jt["t"], SCALE)
    out = {"label": label, "probes": [p.name for p in probes],
           "likelihood_rank": ident["rank"], "block_ranks": block_ranks(jt["F"], jt["F_unprofiled"]),
           "normalized_fisher_eigenvalues": ident["eigenvalues"].tolist(),
           "posterior_mean": mean.tolist(), "posterior_sd": np.sqrt(np.diag(cov)).tolist(),
           "prior_dominated": (np.sqrt(np.diag(cov)) / SCALE > 0.5).tolist()}
    ppc = {}
    for p in probes:
        c2, dof = chi2_at(p, mean)
        edf = effective_dof(p, cov)
        ppc[p.name] = {"chi2": c2, "n_minus_nuisance": dof, "effective_dof": edf,
                       "working_tail": float(chi2.sf(c2, edf)) if edf >= 0.5 else None,
                       "status": "tested" if edf >= 0.5 else "SATURATED_NO_TEST"}
    out["ppc_at_posterior_mean"] = ppc
    return out, jt, ident, mean, cov


def main(run_cobaya: bool = True) -> dict:
    t0 = time.monotonic()
    OUT.mkdir(parents=True, exist_ok=True)
    git_sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    om_r = radiation_density_parameter(PLANCK18["H0"] / 100)
    probes, meta = build_probes(om_r, {})
    base, jt, ident, mean, cov = summarize(probes, "baseline")
    per_probe = {}
    for p in probes:
        sub = joint([p])
        per_probe[p.name] = {"block_ranks": block_ranks(sub["F"], sub["F_unprofiled"]),
                             "rank": identification(sub["F"], 1e-10)["rank"]}
    per_depth = {}
    for w_ in range(4):
        pw, _ = build_probes(om_r, {"cf4_windows": [w_]})
        cf = [p for p in pw if p.name == "CF4_H03"][0]
        jw = joint([cf])
        ab = np.r_[np.arange(8, 11), np.arange(11, 14)]
        per_depth[f"window_{w_}"] = {"block_ranks": block_ranks(jw["F"], jw["F_unprofiled"]),
                                     "A_and_bRM_joint_rank": identification(jw["F"][np.ix_(ab, ab)], 1e-8)["rank"],
                                     "A_bRM_normalized_eigenvalues": identification(jw["F"][np.ix_(ab, ab)], 1e-8)["eigenvalues"].tolist()}
    V = ident["eigenvectors"]
    named = []
    for k in range(V.shape[1]):
        v = V[:, k]
        top = np.argsort(-np.abs(v))[:4]
        named.append({"eigenvalue_normalized": float(ident["eigenvalues"][k]), "identified": bool(k < ident["rank"]),
                      "leading": [[THETA_NAMES[i], float(v[i])] for i in top]})
    bMO, bRM = mean[SL["bMO"]], mean[SL["bRM"]]
    sdv = np.sqrt(np.diag(cov))
    Cb = cov[SL["bRM"], SL["bRM"]]
    phys = {
        "beta_MO_kms": (C_KM_S * bMO).tolist(), "beta_MO_sd_kms": (C_KM_S * sdv[SL["bMO"]]).tolist(),
        "beta_MO_norm_kms": float(C_KM_S * np.linalg.norm(bMO)),
        "beta_RM0_kms": (C_KM_S * bRM).tolist(), "beta_RM0_sd_kms": (C_KM_S * sdv[SL["bRM"]]).tolist(),
        "beta_RM0_norm_kms": float(C_KM_S * np.linalg.norm(bRM)),
        "beta_RM0_zero_wald": float(bRM @ np.linalg.solve(Cb, bRM)),
        "beta_RM0_zero_working_tail": float(chi2.sf(bRM @ np.linalg.solve(Cb, bRM), 3)),
        "A_over_cH0": mean[SL["A"]].tolist(), "A_over_cH0_sd": sdv[SL["A"]].tolist(),
        "sigma_over_H0": mean[SL["sigma"]].tolist(), "sigma_over_H0_sd": sdv[SL["sigma"]].tolist(),
        "omega": "prior-only (no source-bound response; Gaia B1 is degenerate with frame spin)",
        "interpretation": {
            "beta_RM0": "frame-offset parameter: one velocity forced to represent both the z~1-2 count-source frame and the z<0.1 CF4 bulk; NOT a homogeneous global tilt measurement; Wald uses measurement covariance only (no LCDM bulk-flow cosmic variance unless the cf4_bulk_* cases)",
            "A": "NOT physically identified: column-identical to a CF4 directional distance-calibration dipole (rank 0 with that nuisance) and absorbs depth-varying bulk flow",
            "sigma": "CMB-dominated, conditional on the Bianchi-I history operator",
        },
    }
    sens = {}
    gk = meta["gaia"]
    cases = {"c_eb_minus10": {"c_eb_scale": 0.9}, "c_eb_plus10": {"c_eb_scale": 1.1}, "dipole_rho_0p5": {"dipole_rho": 0.5},
             "cf4_bulk_150kms": {"cf4_bulk_sd_kms": 150.0}, "cf4_bulk_250kms": {"cf4_bulk_sd_kms": 250.0}, "cf4_calibration_dipole": {"cf4_calibration_dipole": True},
             "drop_all_counts": {"drop": ["Quaia_dipole", "NVSS_dipole", "RACS_dipole"]},
             "cf4_cov_scaled_by_ppc": {"cf4_cov_scale": float(base["ppc_at_posterior_mean"]["CF4_H03"]["chi2"] / base["ppc_at_posterior_mean"]["CF4_H03"]["effective_dof"])},
             "gaia_K_p16": {"gaia_K_scale": gk["K_percentiles_16_50_84"][0] / gk["K_eff_information_weighted"]},
             "gaia_K_p84": {"gaia_K_scale": gk["K_percentiles_16_50_84"][2] / gk["K_eff_information_weighted"]}}
    for nm in [p.name for p in probes]:
        cases[f"leave_out_{nm}"] = {"drop": [nm]}
    for nm, var in cases.items():
        pr, _ = build_probes(om_r, var)
        s, _, _, m, c = summarize(pr, nm)
        sens[nm] = {"posterior_mean": s["posterior_mean"], "posterior_sd": s["posterior_sd"],
                    "shift_in_baseline_sd": ((m - mean) / sdv).tolist(), "block_ranks": s["block_ranks"],
                    "ppc": {k: v["chi2"] for k, v in s["ppc_at_posterior_mean"].items()},
                    "beta_RM0_norm_kms": float(C_KM_S * np.linalg.norm(m[SL["bRM"]])),
                    "beta_MO_norm_kms": float(C_KM_S * np.linalg.norm(m[SL["bMO"]])),
                    "beta_RM0_zero_wald": float(m[SL["bRM"]] @ np.linalg.solve(c[SL["bRM"], SL["bRM"]], m[SL["bRM"]]))}
    # counts-vs-CF4 consistency on beta_RM(0): disjoint data (CMB dipole shared, ~exact)
    def sub_post(drop):
        pr, _ = build_probes(om_r, {"drop": drop})
        jj = joint(pr)
        return gaussian_posterior(jj["F"], jj["t"], SCALE)
    mA, cA = sub_post(["CF4_H03"])
    mB, cB = sub_post(["Quaia_dipole", "NVSS_dipole", "RACS_dipole"])
    dlt = mA[SL["bRM"]] - mB[SL["bRM"]]
    Cd = cA[SL["bRM"], SL["bRM"]] + cB[SL["bRM"], SL["bRM"]]
    tension = {"beta_RM0_counts_plus_cmbdipole_kms": (C_KM_S * mA[SL["bRM"]]).tolist(),
               "beta_RM0_cf4_plus_cmbdipole_kms": (C_KM_S * mB[SL["bRM"]]).tolist(),
               "chi2_3": float(dlt @ np.linalg.solve(Cd, dlt)), "working_tail": float(chi2.sf(dlt @ np.linalg.solve(Cd, dlt), 3)),
               "law": "Gaussian working law; count clustering and CF4 conditional covariances as supplied"}
    cf = [p for p in probes if p.name == "CF4_H03"][0]
    resid = cf.y - cf.J @ mean
    gdepth = [{"window": w_, "dipole_resid_kms_Mpc": resid[9 * w_ + 1:9 * w_ + 4].tolist()} for w_ in range(4)]
    # independent algebraic route: stack all raw rows, nuisances as explicit parameters with wide priors
    rows_J, rows_y, Cs, Ns = [], [], [], []
    for p in probes:
        rows_J.append(p.J); rows_y.append(p.y); Cs.append(p.C); Ns.append(p.N)
    import scipy.linalg as sla
    Jall = np.vstack(rows_J); yall = np.concatenate(rows_y); Call = sla.block_diag(*Cs)
    Nall = sla.block_diag(*[n if n.shape[1] else np.zeros((n.shape[0], 0)) for n in Ns])
    X = np.hstack([Jall, Nall])
    psd_all = np.concatenate([SCALE, np.full(Nall.shape[1], 1e8)])
    W = np.linalg.solve(Call, X)
    Pfull = X.T @ W + np.diag(1 / psd_all**2)
    dsc = np.sqrt(np.diag(Pfull))
    Cfull = np.linalg.inv(Pfull / dsc[:, None] / dsc[None, :]) / dsc[:, None] / dsc[None, :]
    mfull = Cfull @ (X.T @ np.linalg.solve(Call, yall))
    stacked_check = {"max_abs_mean_diff_in_sd": float(np.max(np.abs(mfull[:17] - mean) / sdv)),
                     "max_rel_sd_diff": float(np.max(np.abs(np.sqrt(np.diag(Cfull))[:17] / sdv - 1))),
                     "method": "stacked raw rows, nuisances as parameters with prior SD 1e8 (approximates flat)"}
    cob = {"status": "not_run"}
    if run_cobaya:
        from cobaya.run import run as cobaya_run
        from htt.htt.infer.r52_cobaya_provider import cobaya_info
        CHAINS.mkdir(parents=True, exist_ok=True)
        Lref = np.linalg.cholesky(cov)
        info = cobaya_info(jt["F"], jt["t"], mean, Lref, SCALE, str(CHAINS / "r52_joint"))
        _, sampler = cobaya_run(info)
        prod = sampler.products()["sample"]
        v = np.array([prod[f"v_{n}"].to_numpy() for n in THETA_NAMES]).T
        wts = prod["weight"].to_numpy()
        burn = int(0.3 * len(wts))
        v, wts = v[burn:], wts[burn:]
        th = mean + v @ Lref.T
        cm = np.average(th, axis=0, weights=wts)
        cs = np.sqrt(np.average((th - cm) ** 2, axis=0, weights=wts))
        cob = {"status": "run", "n_samples_weighted": float(wts.sum()), "n_rows": int(len(wts)),
               "mean_minus_analytic_in_sd": ((cm - mean) / sdv).tolist(), "sd_ratio_to_analytic": (cs / sdv).tolist(),
               "burn_in_fraction_discarded": 0.3,
               "chain_dir": str(CHAINS), "sampler": "cobaya stock mcmc (unchanged kernel), external Likelihood, affine whitened coordinates",
               "note": "affine map uses the analytic posterior covariance, so this checks the sampled density and sampler, not an independent posterior; the independent algebraic check is stacked_gls_check"}
        with open(OUT / "cobaya_config.yaml", "w") as f:
            f.write("# R52 Cobaya run; external Likelihood htt.htt.infer.r52_cobaya_provider.R52JointLikelihood\n")
            f.write("# F,t = joint profiled carrier (R52/identified_combinations.npz); theta = m0 + L v, v ~ U(-50,50), Gaussian theta prior inside logp\n")
            f.write(f"output: {CHAINS / 'r52_joint'}\nsampler:\n  mcmc:\n")
            for k, v in info["sampler"]["mcmc"].items():
                if k not in ("covmat", "covmat_params"):
                    f.write(f"    {k}: {v}\n")
            f.write("params:\n")
            for n in THETA_NAMES:
                f.write(f"  v_{n}: {{prior: {{min: -50, max: 50}}, ref: {{dist: norm, loc: 0, scale: 0.5}}, proposal: 0.5}}\n")
        files = sorted(p for p in CHAINS.glob("r52_joint*") if p.is_file())
        (OUT / "chain_manifest.json").write_text(json.dumps({"chain_dir": str(CHAINS), "location": "local only (not committed)",
            "files": [{"name": f.name, "bytes": f.stat().st_size, "sha256": sha(f)} for f in files]}, indent=1) + "\n")
    np.savez(OUT / "identified_combinations.npz", allow_pickle=False, theta_names=np.array(THETA_NAMES),
             F_joint=jt["F"], t_joint=jt["t"], scale=SCALE, scaled_eigenvalues=ident["eigenvalues"],
             scaled_eigenvectors=ident["eigenvectors"], posterior_mean=mean, posterior_cov=cov)
    result = {
        "node_id": "R52", "source_git_sha": git_sha, "claim_tier": "C0", "owner": "htt",
        "theta": THETA_NAMES, "units_frames_epochs": "htt/htt/htt/infer/r52_joint_identification.py docstring",
        "prior_policy": "likelihood rank recorded first; then independent Gaussian priors with SD = scale (sigma, beta 1e-2; omega, A 1)",
        "scale": SCALE.tolist(), "c_eb": C_EB, "meta": meta, "baseline": base, "per_probe_identification": per_probe,
        "per_depth_cf4_identification": per_depth, "eigen_combinations": named, "physical": phys,
        "sensitivity": sens, "counts_vs_cf4_tension": tension, "stacked_gls_check": stacked_check, "cf4_cross_depth_residuals": gdepth, "cobaya": cob,
        "five_views": {"x": "signed 17D joint posterior (this result + local chain)",
                       "Q": "UNAVAILABLE: no declared K0 gauge for this joint carrier",
                       "F": "UNAVAILABLE: no anchor/support measure declared",
                       "Pi": "UNAVAILABLE: no same-estimator joint null replicates (no BETA_MO_MATCHED_NULL)",
                       "G_F": "cf4_cross_depth_residuals (descriptive contrast; no calibrated depth law)"},
        "input_sha256": {"r49_dataset": sha(R49_NPZ), "cf4_operator": sha(CF4_NPZ), "cf4_cov": sha(CF4_COV), "quaia_G20.0": sha(QUAIA20)},
        "excluded": {"PantheonPlus": "shares hosts and velocity field with CF4; z_HD includes 2M++ PV corrections that remove the targeted bulk flow"},
        "elapsed_s": time.monotonic() - t0,
    }
    (OUT / "R52_JOINT_RESULT.json").write_text(json.dumps(result, indent=1, allow_nan=False) + "\n")
    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-cobaya", action="store_true")
    a = ap.parse_args()
    r = main(run_cobaya=not a.no_cobaya)
    for k in ("meta", "physical", "cobaya"):
        print(k, json.dumps(r[k], indent=1))
    print("baseline", json.dumps({k: r["baseline"][k] for k in ("likelihood_rank", "block_ranks", "ppc_at_posterior_mean")}, indent=1))
    print("tension", json.dumps(r["counts_vs_cf4_tension"], indent=1))
    print("per_probe", json.dumps(r["per_probe_identification"], indent=1))
    print("sensitivity", json.dumps({k: {kk: v[kk] for kk in ("beta_RM0_norm_kms", "beta_MO_norm_kms")} for k, v in r["sensitivity"].items()}, indent=1))
