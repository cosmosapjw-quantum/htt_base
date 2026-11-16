#!/usr/bin/env python3
"""R54-L01: calibrate the T+E type-I estimator on the 300 FFP10 realisations; masked E response.

Steps follow LOCAL_AGENT_CONTRACT.json:nodes[R54-L01] exactly:
 1. cache (300, 135) and covariance identity against observed_carrier.npz:S_ffp10_300_135x135_uK2
 2. masked E response J_E through the R51 masked debiased estimator (R51 maps, masks, NSIDE, beam)
 3. e_dev and the T/B rows of J_E
 4. leave-one-out calibration of carrier TE_l2
 5. B ell=2 null with the empirical LOO law
 6. optional legs: half-mission difference; Commander/NILC/SEVEM E2/B2 dispersion
 7. scripts/r54/run_r54_cmb_type1.py data block re-run with the calibrated law -> RESULTS/R54_L01_RESULT.json

Run: PYTHONPATH=htt/src:htt:. python scripts/r54/run_r54_cmb_type1.py --sims /mnt/extdrive/workdir/r49_chains/ffp10_300_debiased_135.npz
(or this script directly with --sims). Claim tier C0.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import platform
import sys
import time
from pathlib import Path

import numpy as np
import scipy

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT / "htt", ROOT / "htt/src", ROOT):
    sys.path.insert(0, str(_p))

from htt.htt.infer import r54_calibration as cal  # noqa: E402
from htt.htt.infer import r54_tensor_five_view as fv  # noqa: E402

PUB = ROOT / "docs/research_program/observational_publication_20261015"
NPZ = PUB / "R50_OBSERVED_CONVERGENCE_20261115/R51/observed_carrier.npz"
OUT = PUB / "R54_TENSOR_FRAME_TOMOGRAPHY_20261116/RESULTS/R54_L01_RESULT.json"
DEFAULT_SIMS = Path("/mnt/extdrive/workdir/r49_chains/ffp10_300_debiased_135.npz")
RAW = Path("/mnt/extdrive/workdir/raw")
HM = (RAW / "planck_pr3_smica_hm_20261015/COM_CMB_IQU-smica_2048_R3.00_hm1.fits",
      RAW / "planck_pr3_smica_hm_20261015/COM_CMB_IQU-smica_2048_R3.00_hm2.fits")
HM_MISSPIX = RAW / "planck_pr3_smica_hm_20261015/COM_Mask_CMB-HM-Misspix-Mask-Int_2048_R3.00.fits"
PIPELINES = {"NILC": RAW / "planck_pr3_component_maps_20261110/COM_CMB_IQU-nilc_2048_R3.00_full.fits",
             "SEVEM": RAW / "planck_pr3_component_maps_20261110/COM_CMB_IQU-sevem_2048_R3.00_full.fits"}
#: decision thresholds of the contract (never edited after a run)
E_DEV_KEEP, E_DEV_INVALID, B_NULL_ALPHA = 2e-3, 0.05, 0.01
BAND_95, BAND_68 = (0.912, 0.988), (0.60, 0.76)
PI_T_BAND = (0.8797209302325582, 0.8877209302325582)
#: interpretation fixed before the first run (DEVIATIONS.json): the coverage check holds when every one of the
#: ten TE_l2 parameters lies inside both bands; the pooled coverage is reported next to it
COVERAGE_RULE = "per_parameter_all_ten"


def load_script(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def masked_e_response(r51, lanes, op, beam_pixwin: np.ndarray, j_ideal: np.ndarray) -> np.ndarray:
    """Step 2: a^E_2m = ideal T pattern of STF basis k (R54-EQ-04 packing), a^T = a^B = 0, synthesised at NSIDE 2048 with
    the R51 beam x pixel window and passed through the identical masked debiased estimator."""
    import healpy as hp
    nside_t = 64
    nvec = np.array(hp.pix2vec(nside_t, np.arange(hp.nside2npix(nside_t)))).T
    j_e = np.zeros((135, 5))
    for k in range(5):
        tmap = -r51.T_CMB_UK * np.einsum("pi,ij,pj->p", nvec, r51.STF[k], nvec)
        alm = hp.map2alm(tmap, lmax=6, iter=10)
        packed = lanes._pack_hp_alm_n(alm, lanes._MODES_45)
        if np.max(np.abs(packed - j_ideal[:45, k])) > 1e-9 * np.max(np.abs(j_ideal[:45, k])):
            raise SystemExit("inverted real packing does not reproduce response_J_ideal_135x5_uK[:, k]")
        zero = np.zeros_like(alm)
        _, q, u = hp.alm2map([zero, hp.almxfl(alm, beam_pixwin), zero], 2048, lmax=6, pol=True)
        i = np.zeros_like(q)
        j_e[:, k] = lanes.extract_debiased_135_uK(i, q, u, op, in_place=True)
        del q, u, i
    return j_e


def extract(lanes, op, path: Path) -> np.ndarray:
    return lanes.extract_debiased_135_uK(*lanes.read_nested_iqu_ring_uK(path), op, in_place=True)


def run(sims_path: Path) -> dict:
    t0 = time.monotonic()
    cmb = load_script("r54_cmb", "scripts/r54/run_r54_cmb_type1.py")
    with np.load(NPZ, allow_pickle=False) as z:
        labels = [str(x) for x in z["mode_labels"]]
        s_ref, j_t, j_ideal = z["S_ffp10_300_135x135_uK2"], z["response_J_135x5_uK"], z["response_J_ideal_135x5_uK"]
        d_s, d_c = z["d_smica_135_uK"], z["d_commander_135_uK"]
        n_mc = int(z["n_mc"])
        loo_wald_r51 = z["null_loo_wald_300"]
    # ---- step 1 (loader of scripts/r53/run_r53_benchmark.py: key sim_tot)
    if not sims_path.is_file():
        return {"status": "BLOCKED_MISSING_INPUT", "reason": f"{sims_path} absent", "inputs_sha256": {}}
    with np.load(sims_path, allow_pickle=False) as z:
        sims, sims_noise = z["sim_tot"].copy(), z["sim_noise"].copy()
    if sims.shape != (300, 135) or n_mc != 300:
        return {"status": "BLOCKED_MISSING_INPUT", "reason": f"cache shape {sims.shape}, n_mc {n_mc}", "inputs_sha256": {}}
    ident = cal.covariance_identity_rel(sims, s_ref)
    if not ident <= 1e-10:
        return {"status": "BLOCKED_MISSING_INPUT", "reason": f"covariance identity {ident:.3e} > 1e-10", "inputs_sha256": {}}

    t2, e2, b2 = cmb.rows(labels, "T", (2,)), cmb.rows(labels, "E", (2,)), cmb.rows(labels, "B", (2,))
    if t2 != list(range(5)) or e2 != list(range(45, 50)) or b2 != list(range(90, 95)):
        raise SystemExit("row order of the 135-vector differs from conventions.cmb_vector")

    # ---- step 2: masked E response
    r51 = load_script("r51_lowell", "scripts/r51/run_r51_pr3_lowell.py")
    lanes = r51.lane_module()
    import healpy as hp
    from astropy.io import fits
    with fits.open(r51.SMICA, memmap=True) as h:
        int_beam = np.asarray(h[2].data["INT_BEAM"], float).reshape(-1)[:7]
        pol_beam = np.asarray(h[2].data["POL_BEAM"], float).reshape(-1)[:7]
    pixwin = hp.pixwin(2048)[:7]
    mask_i, mask_p = r51.read_mask(r51.MASK_I, "TMASK"), r51.read_mask(r51.MASK_P, "PMASK")
    op = lanes.build_lowell_mask_operators(mask_i, mask_p)
    j_e = masked_e_response(r51, lanes, op, int_beam * pixwin, j_ideal)
    print(f"[L01] masked E response done {time.monotonic() - t0:.0f}s", flush=True)
    # ---- step 3
    scale = float(np.max(np.abs(j_ideal[0:5])))
    e_dev = float(np.max(np.abs(j_e[45:50] - j_ideal[0:5])) / scale)
    use_masked = not e_dev < E_DEV_KEEP
    e_invalid = e_dev >= E_DEV_INVALID
    e_response = {"e_dev": e_dev, "rule": "e_dev < 2e-3 keeps the ideal response; else J_E; e_dev >= 0.05 invalidates the E lane",
                  "flag": "E_RESPONSE_MASKED_USED" if use_masked else "IDEAL_E_RESPONSE_KEPT", "e_lane_invalid": bool(e_invalid),
                  "J_E_135x5_uK": j_e, "norm_T_rows_rel": float(np.max(np.abs(j_e[0:45])) / scale),
                  "norm_B_rows_rel": float(np.max(np.abs(j_e[90:135])) / scale),
                  "norm_E_rows_ell_ge_3_rel": float(np.max(np.abs(j_e[50:90])) / scale),
                  "beam": "INT_BEAM x pixwin(2048) of the SMICA file, as in R51",
                  "pol_over_int_beam_ell2": float(pol_beam[2] / int_beam[2])}

    # ---- step 4: LOO calibration on TE_l2 (rows 0:5 and 45:50)
    idx = t2 + e2
    j_ide = np.zeros_like(j_t)
    j_ide[e2, :] = j_ideal[t2, :]
    j_te = np.hstack([j_t, j_e if use_masked else j_ide])[idx]
    blocks = {"T": range(0, 5), "E": range(5, 10)}
    rep = cal.loo_replicates(sims[:, idx], j_te, blocks)
    infl = fv.finite_mc_sd_inflation(299, 10, 10)
    cov68 = cal.coverage(rep["theta"], rep["sd_plugin"], infl, 0.68)
    cov95 = cal.coverage(rep["theta"], rep["sd_plugin"], infl, 0.95)
    calibrated = bool(np.all((cov95 >= BAND_95[0]) & (cov95 <= BAND_95[1])) and np.all((cov68 >= BAND_68[0]) & (cov68 <= BAND_68[1])))
    obs = cmb.fit(d_s[idx], s_ref[np.ix_(idx, idx)], j_te, n_mc)
    w_obs = {"W_all": float(obs["t"] @ obs["est"]), "W_T": cal.sub_wald(obs["est"], obs["cov_plugin"], blocks["T"]),
             "W_E": cal.sub_wald(obs["est"], obs["cov_plugin"], blocks["E"])}
    law = "FFP10 leave-one-out same-estimator null, TE_l2 (N=300)"
    tails = {"W_all": cal.EmpiricalNull(rep["wald"], law).upper_tail(w_obs["W_all"]),
             "W_T": cal.EmpiricalNull(rep["block_wald"]["T"], law).upper_tail(w_obs["W_T"]),
             "W_E": cal.EmpiricalNull(rep["block_wald"]["E"], law).upper_tail(w_obs["W_E"])}
    q95 = cal.empirical_quantile_inflation(rep["theta"], rep["sd_plugin"], 0.95)
    loo_cal = {"carrier": "TE_l2", "rows": idx, "n_replicates": rep["n"], "covariance_per_replicate": "the other 299 realisations",
               "sd_loo_over_mean_plugin_sd": rep["theta"].std(axis=0, ddof=1) / rep["sd_plugin"].mean(axis=0),
               "finite_mc_sd_inflation_299_10_10": infl, "coverage_68": cov68, "coverage_95": cov95,
               "coverage_68_pooled": float(cov68.mean()), "coverage_95_pooled": float(cov95.mean()),
               "band_68": BAND_68, "band_95": BAND_95, "coverage_rule": COVERAGE_RULE, "calibrated": calibrated,
               "empirical_quantile_inflation_95": q95, "observed": w_obs, "tails": tails,
               "wald_coverage_hotelling": {"law": "hotelling_T2(p=10,n=298) for W_i with S_i from 299 realisations",
                                           "coverage_68": cal.wald_coverage(rep, 0.68), "coverage_95": cal.wald_coverage(rep, 0.95)}}
    print(f"[L01] LOO TE_l2 done {time.monotonic() - t0:.0f}s", flush=True)

    # T-only reproduction of the R51 LOO Pi (acceptance t_only_pi_loo)
    t45 = cmb.rows(labels, "T", (2, 3, 4, 5, 6))
    ft = cmb.fit(d_s[t45], s_ref[np.ix_(t45, t45)], j_t[t45], n_mc)
    rep_t = cal.loo_replicates(sims[:, t45], j_t[t45])
    pi_t = cal.EmpiricalNull(rep_t["wald"], "FFP10 leave-one-out same-estimator null, T45 (N=300)").upper_tail(float(ft["t"] @ ft["est"]))
    t_only = {"Pi_loo": pi_t, "max_rel_diff_vs_R51_null_wald": float(np.max(np.abs(rep_t["wald"] - loo_wald_r51) / np.abs(loo_wald_r51)))}

    # ---- step 5: B ell=2 null with the empirical law
    qb = np.array([float(sims[i, b2] @ np.linalg.solve(np.cov(np.delete(sims, i, axis=0)[:, b2].T, ddof=1), sims[i, b2]))
                   for i in range(300)])
    qb_obs = float(d_s[b2] @ np.linalg.solve(s_ref[np.ix_(b2, b2)], d_s[b2]))
    qb_c = float(d_c[b2] @ np.linalg.solve(s_ref[np.ix_(b2, b2)], d_c[b2]))
    bnull = cal.EmpiricalNull(qb, "FFP10 leave-one-out B ell=2 Hotelling statistic (N=300)")
    b_obs = bnull.upper_tail(qb_obs)
    b_null = {"SMICA": b_obs, "Commander": bnull.upper_tail(qb_c), "rule": "empirical tail >= 0.01",
              "pass": bool(b_obs["p_value"] >= B_NULL_ALPHA), "hotelling_reference": fv.hotelling_null_tail(qb_obs, 5, 300)}

    # ---- step 6: optional legs
    optional = {}
    if all(p.is_file() for p in HM) and HM_MISSPIX.is_file():
        with fits.open(HM_MISSPIX, memmap=True) as h:
            col = h[1].columns.names[0]
        miss = r51.read_mask(HM_MISSPIX, col)
        bad_i, bad_p = int(np.sum(mask_i & ~miss)), int(np.sum(mask_p & ~miss))
        op_hm = op if bad_i + bad_p == 0 else lanes.build_lowell_mask_operators(mask_i & miss, mask_p & miss)
        hd = 0.5 * (extract(lanes, op_hm, HM[0]) - extract(lanes, op_hm, HM[1]))
        noise_var = np.var(sims_noise, axis=0, ddof=1)
        optional["half_mission"] = {"status": "DONE_SCOPED_C0", "vector": "(HM1 - HM2)/2 through the same estimator",
                                    "missing_pixel_mask_column": col, "missing_pixels_inside_R51_masks": [bad_i, bad_p],
                                    "mask": "R51 masks" if bad_i + bad_p == 0 else "R51 masks x HM missing-pixel mask",
                                    "E2_rms_uK": float(np.sqrt(np.mean(hd[e2] ** 2))), "B2_rms_uK": float(np.sqrt(np.mean(hd[b2] ** 2))),
                                    "E2_variance_uK2": float(np.mean(hd[e2] ** 2)), "B2_variance_uK2": float(np.mean(hd[b2] ** 2)),
                                    "ffp10_noise_E2_rms_uK": float(np.sqrt(np.mean(noise_var[e2]))),
                                    "ffp10_noise_B2_rms_uK": float(np.sqrt(np.mean(noise_var[b2]))),
                                    "vector_135_uK": hd, "note": "one realisation: difference tests only, never a null law"}
        print(f"[L01] half-mission done {time.monotonic() - t0:.0f}s", flush=True)
    else:
        optional["half_mission"] = {"status": "SKIPPED_OPTIONAL", "reason": "half-mission maps or missing-pixel mask absent"}
    vecs = {"SMICA": d_s, "Commander": d_c}
    for name, path in PIPELINES.items():
        if path.is_file():
            vecs[name] = extract(lanes, op, path)
    if len(vecs) >= 3:
        stack = np.array(list(vecs.values()))
        disp = stack.std(axis=0, ddof=1)
        optional["pipeline_dispersion"] = {"status": "DONE_SCOPED_C0", "pipelines": list(vecs),
                                           "E2_dispersion_variance_uK2": float(np.mean(disp[e2] ** 2)),
                                           "B2_dispersion_variance_uK2": float(np.mean(disp[b2] ** 2)),
                                           "ffp10_E2_rms_uK": float(np.sqrt(np.mean(np.diag(s_ref)[e2]))),
                                           "ffp10_B2_rms_uK": float(np.sqrt(np.mean(np.diag(s_ref)[b2]))),
                                           "B2_rms_uK_by_pipeline": {k: float(np.sqrt(np.mean(v[b2] ** 2))) for k, v in vecs.items()},
                                           "E2_rms_uK_by_pipeline": {k: float(np.sqrt(np.mean(v[e2] ** 2))) for k, v in vecs.items()},
                                           "B2_tail_by_pipeline": {k: bnull.upper_tail(float(v[b2] @ np.linalg.solve(s_ref[np.ix_(b2, b2)], v[b2])))
                                                                   for k, v in vecs.items()},
                                           "vectors_135_uK": {k: v for k, v in vecs.items() if k not in ("SMICA", "Commander")}}
        print(f"[L01] pipelines done {time.monotonic() - t0:.0f}s", flush=True)
    else:
        optional["pipeline_dispersion"] = {"status": "SKIPPED_OPTIONAL", "reason": "NILC/SEVEM maps absent"}

    # ---- step 7: R54-L1 data block with the calibrated law
    hist = cmb.history_block()
    sd_scale = None if calibrated else {"TE_l2": q95}
    data = cmb.data_block(hist, e_response=j_e if use_masked else None, sd_scale=sd_scale)
    if data["primary_carrier"] != loo_cal["carrier"]:
        raise SystemExit(f"primary carrier {data['primary_carrier']} differs from the calibrated carrier {loo_cal['carrier']}")
    e_status = "INVALID" if e_invalid else ("CLAIMABLE_SUBJECT_TO_R54-L02" if b_null["pass"] else "DIAGNOSTIC")
    results_calibrated = {
        "R54_L1_intervals": "CALIBRATED" if calibrated else "SUPERSEDED",
        "law": "analytic finite-MC inflation confirmed by LOO" if calibrated else "empirical LOO 95% quantile inflation per parameter",
        "E_response": e_response["flag"], "E_lane_status": e_status,
        "primary_carrier": data["primary_carrier"], "primary": data["results"]["primary"],
        "B_null_floor": data["results"]["B_null_floor"], "physics_primary": data["physics_primary"],
        "late_time_shear_bounds": data["late_time_shear_bounds"]}
    return {"status": "DONE_SCOPED_C0", "covariance_identity_rel": ident, "e_response": e_response, "loo_calibration": loo_cal,
            "t_only": t_only, "b_null_empirical": b_null, "optional_legs": optional, "results_calibrated": results_calibrated,
            "decision": {"loo_coverage": "CALIBRATED" if calibrated else "SUPERSEDED",
                         "e_response": e_response["flag"] + ("; E lane INVALID" if e_invalid else ""),
                         "b_null": "E lane may become CLAIMABLE subject to R54-L02" if b_null["pass"] else "E lane stays DIAGNOSTIC"},
            "acceptance": {"covariance_identity_rel": {"value": ident, "op": "<=", "threshold": 1e-10, "pass": ident <= 1e-10},
                           "t_only_pi_loo": {"value": pi_t["p_value"], "op": "within", "threshold": list(PI_T_BAND),
                                             "pass": PI_T_BAND[0] <= pi_t["p_value"] <= PI_T_BAND[1]}},
            "runtime_s": time.monotonic() - t0,
            "inputs_sha256": {str(NPZ.relative_to(ROOT)): sha256(NPZ), str(sims_path): sha256(sims_path),
                              **{p.name: sha256(p) for p in (r51.SMICA, r51.COMMANDER, r51.MASK_I, r51.MASK_P)},
                              **{p.name: sha256(p) for p in (*HM, HM_MISSPIX, *PIPELINES.values()) if p.is_file()}}}


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sims", type=Path, default=DEFAULT_SIMS)
    args = ap.parse_args(argv)
    cmb = load_script("r54_cmb", "scripts/r54/run_r54_cmb_type1.py")
    res = run(args.sims)
    prov = {"script": "scripts/r54/run_r54_l01_te_calibration.py", "script_sha256": sha256(Path(__file__)),
            "inputs_sha256": res.pop("inputs_sha256"), "python": platform.python_version(),
            "numpy": np.__version__, "scipy": scipy.__version__}
    out = {"schema": "htt.r54.l01_te_calibration/1", "node": "R54-L01", "claim_tier": "C0", **res, "provenance": prov,
           "limitations": ["E response from an ell <= 6 E-only template; leakage of ell > 6 power is in the FFP10 covariance, not in J_E.",
                           "LOO replicates share 298 of 299 covariance realisations; their coverage calibrates the plug-in law, they are not 300 independent experiments.",
                           "Optional legs are single realisations and enter difference tests only."]}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(cmb.clean(out), indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(cmb.clean({k: out.get(k) for k in ("status", "covariance_identity_rel", "acceptance", "decision")}), indent=1))
    if out["status"] != "DONE_SCOPED_C0":
        raise SystemExit(out["status"])


if __name__ == "__main__":
    main()
