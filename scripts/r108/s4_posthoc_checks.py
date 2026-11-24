"""R108 lane s4: post-hoc checks of the recorded S4 fits on the saved maps (review findings S4-3, S4-7b, S4-5a).

Purpose
-------
The S4 production and Richardson runs (``scripts.r108.s4_bjs_comparator``) were made before the review.
Rather than rerun them (about an hour, and the working-tree line-of-sight code has changed since), this
script re-reads the maps the fits were made to and, for every recorded fit:

1. reproduces the recorded full-map spline correlation at the recorded template axis (``score_axis``):
   this ties the saved map file to the fit (review S4-5a: the production main-map files were rewritten
   by the later Richardson runs under the same tag);
2. runs ``global_check`` (finer axis grid nside 32 on the nside-32 map with Nelder-Mead refinement on the
   full map, plus seeded random restarts) and records max(corr_check) - corr_best (review S4-3);
3. validates the spline template evaluator against ``bjs_temperature_sky`` on the full sky, both
   handedness values (review S4-7b; the run files validated on the first 4096 ring pixels only).

Inputs: --runs (S4 run JSON files), map npz files named in them (``map_files``) or, for runs written before
``map_files`` existed, the legacy names (``map_paths(..., richardson=False)``; the Richardson linearised maps
under ``_richardson.npz``).  Output: --output JSON.  Units: dimensionless correlations; degrees where named.
Randomness: the random restarts use numpy default_rng(--seed), recorded.  Claim ceiling: numerical checks of a
fit's optimisation; no family attribution, likelihood or calibrated p.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

from scripts.r108.s4_bjs_comparator import (
    GLOBAL_CHECK_TOL,
    HANDEDNESS,
    VARIANTS,
    TemplateSky,
    _centre,
    global_check,
    healpix_directions,
    map_paths,
    rot_y,
    rot_z,
    score_axis,
)

SCHEMA = "htt.r108.s4_posthoc_checks/1"


def case_maps(run: dict, c: dict) -> tuple[dict, dict]:
    """(maps by fit label, file records) of one case of one run."""
    rich = bool(run["argv"].get("richardson", False))
    if "map_files" in c:
        files = {k: Path(v["path"]) for k, v in c["map_files"].items()}
        naming = "map_files recorded in the run"
    else:
        bg = c["background"]
        p = map_paths(c["omega0"], c["x"], c["sigma0"], c["nside"], c["max_step"], c["M"], bg["rtol"], bg["atol"],
                      richardson=False)
        files = {"main": p["main"]}
        if rich:
            files["richardson"] = p["main"].with_name(p["main"].stem + "_richardson.npz")
        naming = "legacy tag (written before the richardson flag was part of the main-map tag)"
    main = np.load(files["main"])
    if rich:
        lin = np.load(files["richardson"])
        maps = {"protocol_richardson": lin["protocol"], "doppler_richardson": lin["doppler"]}
    else:
        maps = {"protocol": main["dTT"], "doppler_diagnostic": main["dTT_doppler"]}
    from scripts.r108.common import sha256_file

    recs = {k: {"path": str(p), "sha256": sha256_file(p), "bytes": p.stat().st_size,
                "mtime_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(p.stat().st_mtime))}
            for k, p in files.items()}
    # content check against the summary statistics the run recorded for its own in-memory maps
    y, yd = main["dTT"], main["dTT_doppler"]
    los = c["los"]
    recs["main_content_check_vs_run_json"] = {
        "rms_dTT_rel_diff": float(np.std(y) / los["rms_dTT"] - 1.0),
        "max_abs_dTT_rel_diff": float(np.max(np.abs(y)) / los["max_abs_dTT"] - 1.0),
        "doppler_map_rms_rel_diff": float(np.std(yd) / los["doppler_map_rms"] - 1.0)}
    recs["naming"] = naming
    return maps, recs


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--runs", nargs="+", required=True)
    ap.add_argument("--check-nside", type=int, default=32)
    ap.add_argument("--n-refine", type=int, default=8)
    ap.add_argument("--n-random", type=int, default=8)
    ap.add_argument("--seed", type=int, default=20261124)
    ap.add_argument("--output", required=True)
    a = ap.parse_args(argv)
    import healpy as hp

    from scripts.r108.common import git_state, sha256_file, write_json

    repo = Path(__file__).resolve().parents[2]
    srcs = ["scripts/r108/s4_posthoc_checks.py", "scripts/r108/s4_bjs_comparator.py",
            "htt/bass/transport/bjs_bianchi_vii_h.py"]
    payload = {"schema": SCHEMA, "argv": vars(a), "command": [sys.executable, *sys.argv], "git": git_state(),
               "sources_sha256": {s: sha256_file(repo / s) for s in srcs}, "global_check_tol": GLOBAL_CHECK_TOL,
               "claim_ceiling": "numerical checks of the fit optimisation only", "runs": []}
    for rp in a.runs:
        run = json.loads(Path(rp).read_text())
        rrow = {"file": rp, "sha256": sha256_file(rp), "richardson": bool(run["argv"].get("richardson", False)),
                "run_sources_sha256": run.get("sources_sha256"), "cases": []}
        payload["runs"].append(rrow)
        for c in run["cases"]:
            t_case = time.perf_counter()
            maps, recs = case_maps(run, c)
            dirs = healpix_directions(c["nside"])
            coarse_nside = max(c["nside"] // 2, 8)
            dirs_c = healpix_directions(coarse_nside)
            crow = {"omega0": c["omega0"], "x": c["x"], "map_files": recs, "spline_validation_full_sky": {},
                    "fits": {}}
            rrow["cases"].append(crow)
            for variant in VARIANTS:
                tmpl = TemplateSky(c["omega0"], c["x"], variant)
                crow["spline_validation_full_sky"][variant] = {
                    f"{k:+d}": tmpl.validate(dirs @ rot_y(0.37) @ rot_z(1.1), k) for k in HANDEDNESS}
                for label, ymap in maps.items():
                    yc = hp.ud_grade(ymap, coarse_nside, order_in="RING", order_out="RING")
                    y_c = _centre(np.asarray(ymap, dtype=np.float64))
                    for kappa in HANDEDNESS:
                        key = f"{label}|{variant}|{kappa:+d}"
                        f = c["fits"][key]
                        t0 = time.perf_counter()
                        axis = np.asarray(f["axis"], dtype=np.float64)
                        corr_rep, amp_rep, roll_rep = score_axis(tmpl, kappa, axis, dirs, y_c)
                        rep = {"corr_spline_recorded": f["corr_spline"], "corr_spline_recomputed": corr_rep,
                               "corr_abs_diff": abs(corr_rep - f["corr_spline"]),
                               "amp_spline_rel_diff": amp_rep / f["amp_spline"] - 1.0}
                        gc = global_check(tmpl, kappa, dirs, ymap, f["corr_spline"], axis,
                                          check_nside=a.check_nside, dirs_coarse=dirs_c, y_coarse=yc,
                                          n_refine=a.n_refine, n_random=a.n_random, seed=a.seed)
                        crow["fits"][key] = {"reproduction": rep, "global_check": gc,
                                             "seconds": time.perf_counter() - t0}
                        print(json.dumps({"run": Path(rp).name, "omega0": c["omega0"], "x": c["x"], "fit": key,
                                          "corr_rep_diff": rep["corr_abs_diff"],
                                          "excess": gc["corr_check_max_minus_corr_best"],
                                          "in_basin": gc["n_checks_in_fit_basin"]}), flush=True)
            crow["seconds"] = time.perf_counter() - t_case
            write_json(a.output, payload)
    allfits = [f for r in payload["runs"] for c in r["cases"] for f in c["fits"].values()]
    payload["summary"] = {
        "n_fits": len(allfits),
        "max_corr_check_minus_corr_best": max(f["global_check"]["corr_check_max_minus_corr_best"] for f in allfits),
        "all_pass": all(f["global_check"]["passes"] for f in allfits),
        "max_reproduction_corr_abs_diff": max(f["reproduction"]["corr_abs_diff"] for f in allfits)}
    write_json(a.output, payload)
    print(json.dumps(payload["summary"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
