#!/usr/bin/env python3
"""R54-L04: CF4 survey-resolved zero points. Is the common hemisphere step a survey calibration term?

Steps follow LOCAL_AGENT_CONTRACT.json:nodes[R54-L04]; deviations are in DEVIATIONS.json (DV-L04-*):
 1. scripts/r54/run_r54_cf4_exact.py is re-run separately and must reproduce its committed JSON (binding test)
 2. survey label per group from the raw CF4 tables and the owned SDSS FP catalogue, joined on identifiers
 3. survey table; small surveys pooled into '<family>_REST'
 4-5. survey operators added to run_r54_cf4_exact.build_operators (survey_step, log_survey, survey_offsets, log_mono_*)
 6. pair sum of the new operators (own cache RESULTS/R54_L04_COSMIC_COV.npz); offsets, steps, consistency; leave-6dFGS-proxy-out fit
 7. headline, window subsets, locking null (4000 draws, streams [20261116, 11..14]) and class for the four new nuisance variants
 8. stability: e_dmzp terciles and the two halves of 0.01 <= z < 0.055
 9. RESULTS/R54_L04_RESULT.json and the decision checks (the cloud decision is not edited; the L04 decision is appended)
Claim tier C0.
"""
from __future__ import annotations

import hashlib
import json
import math
import platform
import sys
import time
from pathlib import Path

import numpy as np
import scipy
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT / "htt", ROOT / "htt/src", ROOT, ROOT / "scripts/r54"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from htt.htt.infer import r54_distance_estimators as de  # noqa: E402
from htt.htt.infer import r54_survey as sv  # noqa: E402
from htt.htt.infer import r54_tensor_five_view as fv  # noqa: E402
import run_r54_cf4_exact as cf  # noqa: E402
import run_r54_lowz_frames as lz  # noqa: E402

RAW = Path("/mnt/extdrive/workdir/raw")
TABLE2, TABLE3, TABLE4 = (RAW / "cf4_full" / f"table{i}.dat" for i in (2, 3, 4))
SDSS_PV = RAW / "sdss_pv_zenodo_6824749/SDSS_PV_public.dat"
LOOP6 = ROOT / "docs/research_program/cf4_schur_loop8_20261015/inputs/loop6_result.json"
OUT = cf.OUT_DIR / "R54_L04_RESULT.json"
LABELS_OUT = cf.OUT_DIR / "R54_L04_SURVEY_LABELS.npz"
COV4 = cf.OUT_DIR / "R54_L04_COSMIC_COV.npz"
MIN_POOL, MIN_SIDE, N_LOCK = 200, 100, 4000
VARIANTS = ("log_survey", "log_mono_radial", "log_mono_galactic", "log_mono_error")     # fixed before any of them was run
STREAMS = {name: 11 + i for i, name in enumerate(VARIANTS)}
SPLITS = ("e_tercile_1", "e_tercile_2", "e_tercile_3", "z_low_half", "z_high_half")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def step_summary(theta: np.ndarray, white: np.ndarray, body: np.ndarray, names: list[str]) -> dict:
    """Per-survey hemisphere steps, their GLS common step and the consistency chi2, with white and white + exact-body errors."""
    out = {"surveys": names, "convention": "s > 0: higher apparent Hubble rate in the north; Delta mu (N - S) = -(5/ln10) 2 s"}
    for tag, cov in (("white", white), ("white_plus_exact_body", white + body)):
        sd = np.sqrt(np.diag(cov))
        per = {s: {"step": float(theta[i]), "sd": float(sd[i]), "z_score": float(theta[i] / sd[i]),
                   "delta_mu_north_minus_south_mag": float(-2.0 * theta[i] / de.LN10_OVER_5)} for i, s in enumerate(names)}
        fit = fv.gls_fit(theta, cov, np.ones((len(names), 1)))
        c, csd = float(fit["theta"][0]), math.sqrt(float(fit["cov"][0, 0]))
        out[tag] = {"per_survey": per, "common_step": c, "common_step_sd": csd, "common_z": c / csd,
                    "common_wald_p_value": float(stats.chi2.sf(fit["wald"], 1)),
                    "common_delta_mu_north_minus_south_mag": -2.0 * c / de.LN10_OVER_5,
                    "consistency_chi2": fit["chi2"], "consistency_dof": fit["dof"],
                    "consistency_p_value": fit["p_value"] if fit["dof"] > 0 else None,
                    "correlation": cov / np.outer(sd, sd)}
    return out


def offset_summary(theta: np.ndarray, white: np.ndarray, body: np.ndarray, names: list[str]) -> dict:
    out = {"offsets": names, "units": "Delta mu in mag of the survey relative to the reference survey of its family (R54-EQ-36)"}
    for tag, cov in (("white", white), ("white_plus_exact_body", white + body)):
        sd = np.sqrt(np.diag(cov))
        out[tag] = {s: {"delta_eta": float(theta[i]), "delta_mu_mag": float(-theta[i] / de.LN10_OVER_5),
                        "delta_mu_sd_mag": float(sd[i] / de.LN10_OVER_5), "z_score": float(theta[i] / sd[i])} for i, s in enumerate(names)}
    return out


def survey_table(lab: np.ndarray, cat: dict, dec: np.ndarray, in_range: np.ndarray) -> dict:
    out = {}
    for s in np.unique(lab):
        sel = lab == s
        out[str(s)] = {"n": int(sel.sum()), "n_in_common_range": int(np.sum(sel & in_range)), "fraction_north": float(np.mean(dec[sel] >= 0.0)),
                       "n_north_in_common_range": int(np.sum(sel & in_range & (dec >= 0.0))),
                       "n_south_in_common_range": int(np.sum(sel & in_range & (dec < 0.0))),
                       "median_z": float(np.median(cat["z_CMB"][sel])), "median_e_dmzp": float(np.median(cat["e_dmzp"][sel]))}
    return out


def decide(st: dict, hls: dict, classes: dict) -> dict:
    """Decision checks of R54-L04 with the contract thresholds, evaluated once."""
    sb = st["white_plus_exact_body"]
    d1 = abs(sb["common_z"]) < 2.0
    single = {s: sb["per_survey"].get(s) for s in ("TF_ALL", "SN_ALL")}
    d2 = all(v is not None and abs(v["z_score"]) >= 2.0 for v in single.values()) and \
        len({math.copysign(1.0, v["step"]) for v in single.values() if v is not None}) == 1
    d3 = hls["quadrupole_constant_wald_p"] >= 0.01
    d4 = hls["joint_null_p"] >= 0.01
    d5 = len(set(classes.values())) == 1
    step_class = "SURVEY_ZERO_POINT" if d1 else ("COMMON_MODE_NOT_SURVEY_SPECIFIC" if d2 else "UNRESOLVED")
    return {
        "checks": [
            {"check": "common step after survey monopoles has |z| < 2 (white + exact body)", "value": sb["common_z"], "result": d1,
             "branch": "class SURVEY_ZERO_POINT; H-L5g REJECTED as a common-mode statement" if d1 else "go to the next check"},
            {"check": "single-survey all-sky samples (TF_ALL, SN_ALL) each keep a step with |z| >= 2 and agree in sign",
             "value": {k: (None if v is None else v["z_score"]) for k, v in single.items()}, "result": None if d1 else bool(d2),
             "branch": "not evaluated (first check true)" if d1 else ("class COMMON_MODE_NOT_SURVEY_SPECIFIC" if d2 else "class UNRESOLVED")},
            {"check": "constant quadrupole of log_survey has Wald p >= 0.01", "value": hls["quadrupole_constant_wald_p"], "result": d3,
             "branch": "H-L5h REJECTED (survey monopoles remove it)" if d3 else "H-L5h stays HOLD"},
            {"check": "joint null of log_survey has p >= 0.01", "value": hls["joint_null_p"], "result": d4,
             "branch": "H-L5a REJECTED as an excess over the body" if d4 else "H-L5a stays HOLD; conditional statement with the nuisance table"},
            {"check": "class identical for pooled, log_mono, log_survey, log_mono_radial, log_mono_galactic, log_mono_error",
             "value": classes, "result": d5,
             "branch": "robust class quoted" if d5 else "robust class stays DEPENDS_ON_ZERO_POINT_NUISANCE_MODEL; the table is quoted; H-L5c stays HOLD"}],
        "step_class": step_class,
        "hypotheses": {"H-L5g": "REJECT" if d1 else "HOLD", "H-L5h": "REJECT" if d3 else "HOLD", "H-L5a": "REJECT" if d4 else "HOLD",
                       "H-L5c": "HOLD"},
        "robust_class": next(iter(classes.values())) if d5 else "DEPENDS_ON_ZERO_POINT_NUISANCE_MODEL",
        "note": "decision checks evaluated once with the contract thresholds; the R54-L05 decision block is not edited"}


def compute() -> dict:
    t0 = time.monotonic()
    loop6 = json.loads(LOOP6.read_text())
    if not all(p.is_file() for p in (TABLE2, TABLE3, TABLE4, SDSS_PV)):
        return {"status": "BLOCKED_MISSING_INPUT", "reason": "raw CF4 tables or the SDSS FP catalogue are absent"}
    ident = {"table3": sha256(TABLE3) == loop6["source_table3_sha256"], "table4": sha256(TABLE4) == loop6["source_table4_sha256"]}
    if not any(ident.values()):
        return {"status": "BLOCKED_MISSING_INPUT", "reason": "no raw group table matches the loop6 hashes"}
    data = cf.load()
    cat = data["cat"]
    z, n, emu = cat["z_CMB"], cat["n_J2000"], cat["e_dmzp"]
    # ---- step 2: labels joined on identifiers
    with open(TABLE2) as f:
        gal = sv.galaxy_table(f)
    with open(TABLE3) as f:
        t3 = np.array([int(x) for x in sv.read_fixed_width(f, sv.TABLE3_COLUMNS)["1PGC"]], np.int64)
    sdss = np.loadtxt(SDSS_PV, usecols=0, dtype=np.int64)
    raw = sv.survey_labels(cat["group_id"], cat["method_family"], gal, sdss)
    coverage = sv.join_coverage(cat["group_id"], t3)
    dec = np.degrees(np.arcsin(np.clip(n[:, 2], -1.0, 1.0)))
    in_range = (z >= cf.Z_COMMON[0]) & (z < cf.Z_COMMON[1])
    lab = sv.pool_small(raw, cat["method_family"], in_range, MIN_POOL)
    np.savez_compressed(LABELS_OUT, group_id=cat["group_id"], survey=lab, survey_unpooled=raw)
    # ---- steps 4-5: operators (existing ones unchanged)
    lr = de.log_distance_ratio(cat["dmzp"], z, cf.OMEGA_M)
    eta, g = lr["eta"], lr["g_per_km_s"]
    tau2 = de.log_noise_variance(emu, g, cf.SIGMA_STAR)
    survey = {"labels": lab, "raw_labels": raw, "min_side": MIN_SIDE}
    ops_all, _ = cf.build_operators(cat, data["a_raw"], tau2, survey=survey)
    base = cf.build_operators(cat, data["a_raw"], tau2)[0]
    for k, v in base.items():
        if not np.array_equal(ops_all[k], v):
            raise SystemExit(f"existing operator {k} changed")
    names = [k for k in ops_all if k not in base]
    ops = {k: ops_all[k] for k in names}
    offsets, labels, start = {}, [], 0
    for k in names:
        offsets[k] = slice(start, start + ops[k].shape[0])
        labels += [f"{k}:{i}" for i in range(ops[k].shape[0])]
        start += ops[k].shape[0]
    vel = np.concatenate([ops[k] * g[None, :] for k in names], axis=0)
    r = de.C_KM_S / cf.H_FID * lr["chi_hat"]
    print(f"[L04] operators {vel.shape} {time.monotonic() - t0:.0f}s", flush=True)
    # ---- step 6: exact body of the new operators
    cosmic = cf.cosmic_covariances(vel, labels, n, r, path=COV4, damped=False)
    body = cosmic["linear"]
    print(f"[L04] pair sum cached={cosmic['cached']} {cosmic['seconds']:.0f}s", flush=True)
    theta = {k: ops[k] @ eta for k in names}
    white = {k: de.white_covariance(ops[k], tau2) for k in names}
    bk = {k: cf.block(body, offsets[k]) for k in names}
    an = {k: vel[offsets[k]] @ n for k in names}
    layout = survey["layout"]

    def steps_of(name: str) -> dict:
        if name not in ops:
            return {"surveys": [], "note": f"no survey with {MIN_SIDE} groups in each hemisphere"}
        return step_summary(theta[name], white[name], bk[name], layout[name])

    def offsets_of(name: str) -> dict:
        if name not in ops:
            return {"offsets": [], "note": "no family with two surveys"}
        return offset_summary(theta[name], white[name], bk[name], layout[name])

    l05 = json.loads(cf.OUT.read_text())
    law = "white (distance-modulus error + 250 km/s) + exact catalogue linear LCDM body"
    k6 = "log_mono_no_6dfgs_proxy"
    c6 = white[k6] + bk[k6]
    no6 = cf.as_fraction(lz.analyse_window_multipoles(theta[k6], c6, an[k6], 1.0, law + "; method monopoles; FP_NOT_SDSS and FP_MIXED removed",
                                                       estimator="log"))
    # ---- step 7: the four nuisance variants
    removed = bool(l05["decision"]["flags"]["removed_by_method_hemisphere_split"])
    variants = {}
    for name in VARIANTS:
        cov = white[name] + bk[name]
        res = cf.as_fraction(lz.analyse_window_multipoles(theta[name], cov, an[name], 1.0, law + f"; nuisance {name}", estimator="log"))
        hl = cf.headline_of(res, True)
        lock = cf.locking_null(theta[name], cov, np.random.default_rng([cf.SEED, STREAMS[name]]), N_LOCK)
        tail = lock["tails"]["sky_fraction_at_most_observed"]
        variants[name] = {"headline": hl, "window_subsets": cf.window_subset_nulls(theta[name], cov), "axis_locking_null": lock,
                          "class": cf.classify(hl["joint_null_p"], removed, tail), "locking_tail": tail, "stream": [cf.SEED, STREAMS[name]]}
        print(f"[L04] variant {name} {time.monotonic() - t0:.0f}s", flush=True)
    dv = l05["decision"]
    cloud = {key: {"class": dv["class_by_nuisance_variant"][src], "joint_null_p": dv["joint_null_p_by_nuisance_variant"][src],
                   "locking_tail": dv["locking_tail_by_nuisance_variant"][src]}
             for key, src in (("pooled", "pooled"), ("log_mono", "method_monopoles_marginalised"), ("log_split", "method_x_hemisphere_steps_marginalised"))}
    classes = {"pooled": cloud["pooled"]["class"], "log_mono": cloud["log_mono"]["class"], **{k: variants[k]["class"] for k in VARIANTS}}
    st = steps_of("survey_step")
    if "white_plus_exact_body" not in st:
        raise SystemExit("no survey step is identified: decision check 1 cannot be evaluated")
    decision = decide(st, variants["log_survey"]["headline"], classes)
    decision["cloud_robust_class_unchanged"] = dv["robust_class"]
    # ---- step 8: stability
    stability = {}
    for tag in SPLITS:
        stp = steps_of(f"survey_step_{tag}")
        wb = stp.get("white_plus_exact_body", {})
        stability[tag] = {"n_groups": survey["splits"][tag], "steps": stp, "offsets": offsets_of(f"survey_offsets_{tag}"),
                          "common_step": wb.get("common_step"), "common_step_sd": wb.get("common_step_sd"), "common_z": wb.get("common_z")}
    return {
        "status": "DONE_SCOPED_C0",
        "label_join": {"group_table_identity": ident, "label_join_coverage": coverage,
                       "coverage_table2_group_ids": sv.join_coverage(cat["group_id"], gal["group"]), "sdss_fp_galaxies": int(sdss.size),
                       "rule": "FP_SDSS / FP_NOT_SDSS / FP_MIXED by galaxy PGC in the SDSS FP catalogue; TF_ALL, SN_ALL, OTHER_ALL"},
        "survey_table": {"unpooled": survey_table(raw, cat, dec, in_range), "pooled": survey_table(lab, cat, dec, in_range),
                         "pool_rule": f"surveys with fewer than {MIN_POOL} groups in {list(cf.Z_COMMON)} pooled into '<family>_REST'"},
        "operators": {k: [offsets[k].start, offsets[k].stop] for k in names}, "operator_layout": layout,
        "survey_offsets": offsets_of("survey_offsets"), "survey_steps": st,
        "log_survey_headline": variants["log_survey"]["headline"],
        "leave_6dfgs_proxy_out": {"selection": "log_mono window fit without FP_NOT_SDSS and FP_MIXED (6dFGSv is not separable from them)",
                                  "headline": cf.headline_of(no6, True), "window_subsets": cf.window_subset_nulls(theta[k6], c6),
                                  "n_groups_with_weight": int(np.sum(np.abs(ops[k6]).sum(axis=0) > 0))},
        "nuisance_variants": {"cloud": cloud, "local": variants, "classes": classes},
        "stability": {"splits": stability, "e_dmzp_terciles": survey["e_terciles"],
                      "z_halves": [cf.Z_COMMON[0], 0.5 * (cf.Z_COMMON[0] + cf.Z_COMMON[1]), cf.Z_COMMON[1]]},
        "decision": decision,
        "pair_sum": {"file": str(COV4.relative_to(ROOT)), "cached": cosmic["cached"], "seconds": cosmic["seconds"], "rows": int(vel.shape[0])},
        "acceptance": {"label_join_coverage": {"value": coverage, "op": ">=", "threshold": 0.99, "pass": coverage >= 0.99}},
        "runtime_s": time.monotonic() - t0,
    }


def cloud_json_reproduced() -> dict:
    """Step 1: run_r54_cf4_exact.compute() with read-only caches must reproduce the committed R54_L05_CF4_EXACT.json (provenance excluded)."""
    committed = json.loads(cf.OUT.read_text())
    cf.CACHE_WRITE = False
    fresh = json.loads(json.dumps(lz.clean(cf.compute()), sort_keys=True))
    keep = {k: v for k, v in committed.items() if k != "provenance"}
    same = json.dumps(keep, sort_keys=True) == json.dumps({k: v for k, v in fresh.items() if k != "provenance"}, sort_keys=True)
    return {"value": bool(same), "op": "==", "threshold": True, "pass": bool(same),
            "note": "compute() re-executed with read-only pair-sum caches; every key except provenance compared exactly"}


def main() -> None:
    reproduced = cloud_json_reproduced()
    print(f"[L04] cloud JSON reproduced: {reproduced['pass']}", flush=True)
    res = compute()
    if "acceptance" in res:
        res["acceptance"]["cloud_json_reproduced"] = reproduced
    prov = {"script": "scripts/r54/run_r54_l04_cf4_survey.py", "script_sha256": sha256(Path(__file__)),
            "inputs_sha256": {**{str(p): sha256(p) for p in (TABLE2, TABLE3, TABLE4, SDSS_PV) if p.is_file()},
                              **{str(p.relative_to(ROOT)): sha256(p) for p in (cf.SRC, cf.OPF, LOOP6, cf.OUT, cf.PK)}},
            "seed": cf.SEED, "python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__}
    out = {"schema": "htt.r54.l04_cf4_survey_split/1", "node": "R54-L04", "claim_tier": "C0", **res, "provenance": prov,
           "limitations": ["Survey labels resolve only SDSS vs non-SDSS FP; 6dFGSv, TF samples or bands and SN compilations are not separable with owned files (DV-L04-1, DV-L04-2).",
                           "Same body assumptions as R54-L05 (linear theory, redshift-space positions, no selection or calibration covariance between objects).",
                           "SDSS FP is a northern sample and non-SDSS FP is mostly southern, so an FP survey offset and an FP hemisphere step are close to degenerate."]}
    OUT.write_text(json.dumps(lz.clean(out), indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(lz.clean({"status": out["status"], "acceptance": out.get("acceptance"), "decision": out.get("decision", {}).get("checks")}), indent=1))
    if out["status"] != "DONE_SCOPED_C0":
        raise SystemExit(out["status"])


if __name__ == "__main__":
    main()
