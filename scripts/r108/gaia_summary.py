"""R108 gaia lane: collect receipts and result files into one node-status JSON (no new computation).

Purpose
  Reads the acquisition receipts (RECEIPTS.jsonl), the lane result JSONs in
  R108_LOS_ATLAS_DATA_20261124/GAIA/ and the command log, checks their SHA-256 against the receipts
  that reference them, and writes GAIA_R108_SUMMARY.json with: products (rows, bytes, SHA-256, job ids),
  the headline numbers of each control copied from the result files (with the file and key path),
  and the result label of each sub-task (CONDITIONAL / NUMERICAL / BLOCKED) with its stated reason.
Inputs: --receipts RECEIPTS.jsonl, --results-dir, --commands gaia_COMMANDS.jsonl (SHA-256 recorded).
Usage: python -m scripts.r108.gaia_summary --receipts R --results-dir D --commands C --out J
Deterministic.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.r108.common import git_state, sha256_file, write_json

FILES = ("SCANLAW_PIXEL_STATISTICS.json", "SCANLAW_VALIDATION.json", "SCAN_NULL_CALIBRATION.json", "SCAN_NULL.json",
         "FRAME_LEAKAGE.json", "AGN_SPLIT.json")


def get(d, path):
    for k in path.split("/"):
        d = d[int(k)] if isinstance(d, list) else d[k]
    return d


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--receipts", type=Path, required=True)
    ap.add_argument("--results-dir", type=Path, required=True)
    ap.add_argument("--commands", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    rec = [json.loads(x) for x in a.receipts.expanduser().read_text().splitlines() if x.strip()]
    products = {}
    for r in rec:
        products.setdefault(r["id"], []).append({k: r.get(k) for k in (
            "name", "status", "rows", "expected_rows", "archive_count", "unique_source_id", "bytes", "sha256", "md5",
            "url", "final_url", "job_id", "query", "fetched_at_utc", "n_jobs_completed", "n_jobs_aborted_and_bisected")
            if k in r})
    out_dl = a.receipts.expanduser().parent
    logdir = a.commands.expanduser().parent
    blocked = {}
    for name, sub, log in (("D10_attempt1", "D10_agn_cross_id_gaia_source", None),
                           ("D10_attempt2", "D10_agn_cross_id_gaia_source_attempt2", "gaia_acq_D10_attempt2.log"),
                           ("D10S_attempt1_joined_supplement", "D10S_gaia_crf3_xm_flags", "gaia_acq_D10S.log")):
        d = out_dl / sub
        ent = {"directory": str(d)}
        if (d / "JOB.json").exists():
            ent["job"] = json.loads((d / "JOB.json").read_text())
        if (d / "JOBS.jsonl").exists():
            jobs = [json.loads(x) for x in (d / "JOBS.jsonl").read_text().splitlines() if x.strip()]
            ent["jobs"] = len(jobs)
            ent["completed"] = sum(j["phase"] == "COMPLETED" for j in jobs)
            ent["aborted"] = sum(j["phase"] == "ABORTED" for j in jobs)
            ent["rows_in_completed_jobs"] = sum(j.get("rows") or 0 for j in jobs)
            ent["jobs_jsonl_sha256"] = sha256_file(d / "JOBS.jsonl")
            errs = sorted({(j.get("error") or "")[:60] for j in jobs if j["phase"] != "COMPLETED"})
            ent["abort_messages_prefix"] = errs
            ent["last_job"] = {k: jobs[-1].get(k) for k in ("lo", "hi", "phase", "job_id")}
            ent["last_job_error_tail"] = (jobs[-1].get("error") or "")[-120:]
        if log and (logdir / log).exists():
            for line in (logdir / log).read_text().splitlines():
                if line.startswith("{") and "archive_count" in line:
                    ent["archive_count_logged_by_script"] = json.loads(line)["archive_count"]
                    break
        blocked[name] = ent
    res_files, data = {}, {}
    for f in FILES:
        p = a.results_dir / f
        if p.exists():
            res_files[f] = sha256_file(p)
            data[f] = json.loads(p.read_text())
        else:
            res_files[f] = None
    out = {"schema": "htt.r108.gaia_summary/1", "products": products, "result_files_sha256": res_files,
           "commands_jsonl_sha256": sha256_file(a.commands.expanduser()), "git": git_state(),
           "claim_ceiling": "no physical Pi/G_F, no Bianchi family attribution, no calibrated p", "headline": {},
           "tap_attempts": blocked}
    picks = {
        "SCANLAW_PIXEL_STATISTICS.json": ["rows/rows", "samples_outside_edr3_interval",
                                          "scan_angle_convention_check/fov1/frac_abs_diff_lt_1deg_standard",
                                          "per_pixel/nside64/passes_per_pixel_q01_q50_q99",
                                          "per_pixel/nside64/scan_anisotropy_abs_mean_exp2ipsi_q05_q50_q95"],
        "SCANLAW_VALIDATION.json": ["pearson_pred_vs_catalogue_pm_corr", "mirrored_convention_control",
                                    "pearson_pred_vs_catalogue_log_sigma_ratio"],
    }
    for f, paths in picks.items():
        if f in data:
            out["headline"][f] = {p: get(data[f], p) for p in paths}
    if "SCAN_NULL.json" in data:
        sn = data["SCAN_NULL.json"]
        out["headline"]["SCAN_NULL.json"] = {
            k: ({t: v["tables"][t] for t in ("all48__spin6", "excl__spin6")} | (
                {"systematic_only_all48": v["systematic_only_all48"]} if "systematic_only_all48" in v else {}))
            if "tables" in v else v for k, v in sn["kinds"].items()}
        if "script_versions" in sn:
            out["headline"]["SCAN_NULL.json__script_versions"] = sn["script_versions"]
    if "FRAME_LEAKAGE.json" in data:
        fl = data["FRAME_LEAKAGE.json"]
        h = {"claim_class": fl.get("claim_class"), "constraint_summary": fl.get("constraint_summary")}
        A = fl.get("A_icrf3_minus_gaia", {})
        h["A_census"] = A.get("census")
        h["A_global_clip5"] = {k: A.get("global", {}).get("clip_X_gt_5", {}).get(k) for k in (
            "n_used", "glide_vector", "spin_vector", "spin_chi2_vs_zero", "glide_chi2_vs_zero")}
        h["A_shells"] = A.get("shells")
        h["A_shell_curvature"] = A.get("shell_curvature")
        h["A_constraint"] = A.get("constraint")
        B = fl.get("B_crf3_agn_pm_frames", {})
        h["B_global_complement"] = {k: B.get("global_frame_crf3_complement", {}).get(k) for k in (
            "n_used", "glide_vector", "spin_vector", "spin_chi2_vs_zero")}
        h["B_leak_point"] = B.get("leak_complement_cell_frames_point")
        h["B_bound"] = B.get("bound_draws")
        h["B_insample_diagnostic"] = B.get("leak_quaia_in_sample_cell_frames_diagnostic")
        h["C"] = fl.get("C_constant_frame_annihilation")
        h["d10_consistency"] = {k: v for k, v in fl.get("d10_vs_pinned_crf3_fits", {}).items()
                                if k != "agn_cross_id_catalogue_name_counts"}
        out["headline"]["FRAME_LEAKAGE.json"] = h
    if "AGN_SPLIT.json" in data:
        ag = data["AGN_SPLIT.json"]
        out["headline"]["AGN_SPLIT.json"] = {"membership": ag["membership"], "agn_vs_non_agn": ag["agn_vs_non_agn"],
                                             "splits": {k: {"status": v["status"], "definition": v.get("definition"),
                                                            "n_A": v["n_A"], "n_B": v["n_B"],
                                                            "A_null": v.get("A", {}).get("patch_permutation_null_jk1", {}).get("all48", {}).get("spin6"),
                                                            "B_null": v.get("B", {}).get("patch_permutation_null_jk1", {}).get("all48", {}).get("spin6"),
                                                            "difference_spin6": v.get("difference_test", {}).get("all48", {}).get("spin6")}
                                                        for k, v in ag["splits"].items()}}
    write_json(a.out, out)
    print(json.dumps({"out": str(a.out), "result_files": res_files}))


if __name__ == "__main__":
    main()
