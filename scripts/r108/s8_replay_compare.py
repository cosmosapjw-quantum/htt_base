"""R108 lane s8 step 1: compare a fresh rerun of the R106 REI restart replay with the committed R106 result.

Purpose
  The R106 replay (scripts/r106/rei_restart_replay.py, stages build,record,replay,analyze) restarts the
  frozen rei_bianchi AXBI driver from the z = 4 checkpoints of the five shear cases and replays the last
  two output intervals (accepted steps 312120 -> 312180 -> 312237, plus a restart 312180 -> 312237).
  This script reads the rerun written at the current tree and states, per case, whether
  (a) the rerun is bitwise identical to the ORIGINAL run (checkpoint text, every replayed output row,
      every compared state field), as the R106 script itself measures it;
  (b) every numeric leaf of the restart inventory (charge, temperature, proper time, photon inventory,
      expansion), of the replay diff reports and of the derived clock/foreground blocks equals the
      committed R106 JSON exactly;
  (c) the new native replay output files equal the R106 cached native replay output files byte for byte
      (replay.json compared after removing its wall-clock fields);
  (d) the build: compiled source identity, src tree hash and binary sha256 equal the R106 build.

Inputs (paths are arguments): the rerun directory (REI_RESTART_REPLAY.json, BUILD.json, replay/<case>/),
  the committed R106 REI_RESTART_REPLAY.json, and the R106 cached replay directory.
Output: one JSON file (default docs/.../R108_LOS_ATLAS_DATA_20261124/REI/S8_REPLAY_COMPARISON.json).
Units: as in the R106 schema (fractions per H or He, K, s, photons per H, eV per H).
Claim class: numerical reproducibility of a frozen solver over the replayed window; no physics claim.
No randomness.
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

HTT_BASE = Path(__file__).resolve().parents[2]
R106_JSON = HTT_BASE / "docs/research_program/observational_publication_20261015/R106_RESEARCH_20261124/REI/REI_RESTART_REPLAY.json"
R106_CACHE = Path.home() / "Downloads/htt_r106_analysis/rei"
DEFAULT_RERUN = Path.home() / "Downloads/htt_r108/s8/replay_rerun"
DEFAULT_OUT = HTT_BASE / "docs/research_program/observational_publication_20261015/R108_LOS_ATLAS_DATA_20261124/REI/S8_REPLAY_COMPARISON.json"
INVENTORY_BLOCKS = ("charge", "temperature", "proper_time", "photons", "expansion")
# Keys whose values are host clocks or file locations, not solver output.
VOLATILE_KEYS = {"wall_elapsed_s", "continuous_wall_s", "restart_wall_s", "replay_wall_s", "original_tail_of",
                 "restart_file", "segment"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 22), b""):
            h.update(block)
    return h.hexdigest()


def numeric_leaves(obj, prefix=""):
    """Yield (path, value) for every int/float/bool/None/str leaf, skipping VOLATILE_KEYS."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in VOLATILE_KEYS:
                continue
            yield from numeric_leaves(v, f"{prefix}.{k}" if prefix else str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from numeric_leaves(v, f"{prefix}[{i}]")
    else:
        yield prefix, obj


def exact_compare(new, old) -> dict:
    """Exact equality of all leaves (floats compared with ==, NaN-free by construction of the R106 JSON)."""
    a, b = dict(numeric_leaves(new)), dict(numeric_leaves(old))
    only_new, only_old = sorted(set(a) - set(b)), sorted(set(b) - set(a))
    unequal = []
    max_abs = 0.0
    for k in sorted(set(a) & set(b)):
        x, y = a[k], b[k]
        if x != y:
            entry = {"path": k, "new": x, "r106": y}
            if isinstance(x, (int, float)) and isinstance(y, (int, float)) and not isinstance(x, bool):
                d = abs(float(x) - float(y))
                entry["abs_diff"] = d
                max_abs = max(max_abs, d)
            unequal.append(entry)
    return {"n_leaves_compared": len(set(a) & set(b)), "n_unequal": len(unequal), "unequal": unequal[:50],
            "leaves_only_in_new": only_new[:50], "leaves_only_in_r106": only_old[:50],
            "max_abs_numeric_difference": max_abs, "identical": not unequal and not only_new and not only_old}


def strip_wall(obj):
    if isinstance(obj, dict):
        return {k: strip_wall(v) for k, v in obj.items() if k not in VOLATILE_KEYS}
    if isinstance(obj, list):
        return [strip_wall(v) for v in obj]
    return obj


def native_files_compare(new_dir: Path, old_dir: Path) -> dict:
    names = sorted({p.name for p in new_dir.iterdir()} | {p.name for p in old_dir.iterdir()})
    out, all_equal = {}, True
    for name in names:
        p, q = new_dir / name, old_dir / name
        if not (p.exists() and q.exists()):
            out[name] = {"present_new": p.exists(), "present_r106": q.exists()}
            all_equal = False
            continue
        if name == "replay.json":
            jn, jo = json.loads(p.read_text()), json.loads(q.read_text())
            cmp = exact_compare(strip_wall(jn), strip_wall(jo))
            out[name] = {"compared": "all fields except wall-clock fields", "identical": cmp["identical"],
                         "n_leaves_compared": cmp["n_leaves_compared"], "n_unequal": cmp["n_unequal"],
                         "unequal": cmp["unequal"][:10]}
            all_equal &= cmp["identical"]
        else:
            same = sha256(p) == sha256(q)
            out[name] = {"sha256_new": sha256(p), "bytewise_identical_to_r106": same}
            all_equal &= same
    return {"files": out, "all_identical": all_equal, "n_files": len(names)}


def rows_all_identical(rows: dict) -> bool:
    ok = True
    for prefix in ("continuous", "restart_from_00312180"):
        for name in ("history", "abundances", "ledgers", "feedback"):
            r = rows[prefix][name]
            ok &= r["rows"] == r["rows_bytewise_identical"] and r["rows"] > 0
        ok &= all(v["bytewise_identical"] is True for v in rows[prefix]["spectra"].values())
    ok &= all(rows["terminal_restart_reread"].values())
    return ok


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rerun", type=Path, default=DEFAULT_RERUN)
    ap.add_argument("--r106-json", type=Path, default=R106_JSON)
    ap.add_argument("--r106-cache", type=Path, default=R106_CACHE)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args(argv)
    t0 = time.time()
    new = json.loads((args.rerun / "REI_RESTART_REPLAY.json").read_text())
    old = json.loads(args.r106_json.read_text())
    head = subprocess.run(["git", "-C", str(HTT_BASE), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "-C", str(HTT_BASE), "status", "--porcelain", "--untracked-files=no"],
                           capture_output=True, text=True).stdout.splitlines()
    result = {
        "schema": "htt.r108.s8.rei_replay_comparison/1",
        "purpose": ("R108 S8 acceptance 'restart replay identical as in R106': fresh rebuild + native replay of the "
                    "five REI z=4 restart checkpoints at the current tree, compared with the original run and with the "
                    "committed R106 result"),
        "script": {"path": str(Path(__file__).resolve()), "sha256": sha256(Path(__file__).resolve())},
        "htt_base": {"head": head, "n_modified_tracked_paths": len(dirty)},
        "inputs": {"rerun_result": str(args.rerun / "REI_RESTART_REPLAY.json"),
                   "rerun_result_sha256": sha256(args.rerun / "REI_RESTART_REPLAY.json"),
                   "r106_result": str(args.r106_json), "r106_result_sha256": sha256(args.r106_json),
                   "r106_native_cache": str(args.r106_cache)},
        "rerun": {"native_outputs_mode": new["native_outputs"]["mode"],
                  "replay_script_sha256": new["script"]["sha256"], "r106_script_sha256": old["script"]["sha256"],
                  "replay_script_unchanged": new["script"]["sha256"] == old["script"]["sha256"],
                  "invocation": new.get("invocation"),
                  "native_command_records": {t: {k: r.get(k) for k in ("command", "return_code", "wall_s", "maxrss_kB")}
                                             for t, r in new["native_outputs"]["native_command_records"].items()},
                  "environment": {k: new["environment"][k] for k in ("htt_base", "rei_bianchi", "libraries",
                                                                     "toolchain_now")}},
        "build": {}, "cases": {}}
    for tag in ("d7676", "4de69"):
        bn, bo = new["build"][tag], old["build"][tag]
        result["build"][tag] = {
            "compiled_source_identity_sha256": bn["compiled_source_identity_sha256"],
            "identity_equal_r106": bn["compiled_source_identity_sha256"] == bo["compiled_source_identity_sha256"],
            "src_tree_sha256": bn["post_build_record"]["src_tree"]["sha256"],
            "src_tree_equal_r106": bn["post_build_record"]["src_tree"]["sha256"] == bo["post_build_record"]["src_tree"]["sha256"],
            "binary_sha256": bn["binary_sha256"], "binary_equal_r106": bn["binary_sha256"] == bo["binary_sha256"],
            "replay_example_equal_r106": bn["replay_example_sha256"] == bo["replay_example_sha256"],
            "build_return_code": bn["build"]["return_code"], "build_wall_s": bn["build"]["wall_s"]}
    verdicts = []
    for case, cn in new["cases"].items():
        co = old["cases"][case]
        rn, ro = cn["replay"], co["replay"]
        inv = {blk: exact_compare(cn["restart_inventory"][blk], co["restart_inventory"][blk]) for blk in INVENTORY_BLOCKS}
        intervals = {
            "continuous_312120_to_312180_vs_original": rn["continuous_vs_original"]["312180"],
            "continuous_312180_to_312237_vs_original": rn["continuous_vs_original"]["312237"],
            "restart_312180_to_312237_vs_original": rn["restart_from_original_312180_vs_original_312237"]}
        interval_zero = {}
        for label, rep in intervals.items():
            nonzero = []
            for key, d in rep.items():
                v = d.get("difference", d.get("max_abs", d.get("abs")))
                if v != 0:
                    nonzero.append(key)
            interval_zero[label] = {"n_fields": len(rep), "fields_with_nonzero_difference": nonzero,
                                    "all_zero": not nonzero}
        diff_reports_vs_r106 = exact_compare(
            {k: rn[k] for k in ("continuous_vs_original", "restart_from_original_312180_vs_original_312237", "window",
                                "headline_residual", "checkpoint_text_bytewise_identical_with_original_wall_field",
                                "output_rows", "caps_from_original_wrapper", "solver_log")},
            {k: ro[k] for k in ("continuous_vs_original", "restart_from_original_312180_vs_original_312237", "window",
                                "headline_residual", "checkpoint_text_bytewise_identical_with_original_wall_field",
                                "output_rows", "caps_from_original_wrapper", "solver_log")})
        derived = {blk: exact_compare(cn[blk], co[blk]) for blk in ("clock_H_consistency_and_quadrature",
                                                                     "foreground_sensitivity_z_0_to_4")}
        prov = exact_compare(cn["provenance"], co["provenance"])
        native = native_files_compare(args.rerun / "replay" / case, args.r106_cache / "replay" / case)
        ck = rn["checkpoint_text_bytewise_identical_with_original_wall_field"]
        identical_to_original = (rn["headline_residual"]["all_bitwise_equal"] and all(ck.values())
                                 and rows_all_identical(rn["output_rows"])
                                 and all(v["all_zero"] for v in interval_zero.values()))
        identical_to_r106 = (all(v["identical"] for v in inv.values()) and diff_reports_vs_r106["identical"]
                             and all(v["identical"] for v in derived.values()) and native["all_identical"])
        verdicts.append(identical_to_original and identical_to_r106)
        ri = cn["restart_inventory"]
        result["cases"][case] = {
            "q_ref": cn["q_ref"],
            "restart_checkpoint_sha256": ri["restart_sha256"],
            "restart_checkpoint_sha256_equal_r106": ri["restart_sha256"] == co["restart_inventory"]["restart_sha256"],
            "window": rn["headline_residual"]["window"],
            "replay_identical_to_original_run": identical_to_original,
            "checkpoint_text_bytewise_identical": ck,
            "last_two_output_intervals": interval_zero,
            "output_rows_all_bytewise_identical": rows_all_identical(rn["output_rows"]),
            "headline_residual": {k: rn["headline_residual"][k] for k in ("n_fields", "max_abs_difference_any_field",
                                                                          "all_bitwise_equal", "unequal_fields")},
            "restart_state_values": {
                "x_e_per_H_at_restart": ri["charge"]["xe_per_H"], "x_HII": ri["charge"]["x_HII"],
                "x_HeII": ri["charge"]["x_HeII"], "x_HeIII": ri["charge"]["x_HeIII"],
                "temperature_K_native_eos": ri["temperature"]["T_K_native_eos"],
                "time_s_since_mean_z20": ri["proper_time"]["time_s_restart"],
                "photon_n_per_H": ri["photons"]["photon_n_per_H"], "photon_u_eV_per_H": ri["photons"]["photon_u_eV_per_H"]},
            "restart_inventory_vs_r106_exact": inv,
            "replay_reports_vs_r106_exact": {k: diff_reports_vs_r106[k] for k in ("identical", "n_leaves_compared",
                                                                                  "n_unequal", "unequal")},
            "derived_blocks_vs_r106_exact": {k: {kk: v[kk] for kk in ("identical", "n_leaves_compared", "n_unequal",
                                                                      "unequal", "max_abs_numeric_difference")}
                                             for k, v in derived.items()},
            "provenance_vs_r106_exact": {kk: prov[kk] for kk in ("identical", "n_leaves_compared", "n_unequal",
                                                                 "unequal")},
            "native_replay_files_vs_r106_cache": native,
            "identical_to_r106": identical_to_r106,
            "replay_wall_s": rn["replay_wall_s"]}
    result["verdict"] = {
        "all_cases_identical_to_original_and_r106": all(verdicts),
        "statement": ("PASS: restart replay identical as in R106 for every case" if all(verdicts) else
                      "FAIL: see cases.*.identical_to_r106 / replay_identical_to_original_run"),
        "claim_class": "NUMERICAL_REPRODUCIBILITY of the frozen solver over the replayed window only"}
    result["wall_s"] = time.time() - t0
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps(result["verdict"]))
    return 0 if all(verdicts) else 1


if __name__ == "__main__":
    sys.exit(main())
