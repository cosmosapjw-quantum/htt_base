#!/usr/bin/env python3
"""R89 G06_P1 group execution (create-only).

Reuses S01/S03 scoped evidence, replays R82 2,048-draw coupled four-window
p1_fast kernels (sorted NumPy reference vs C++ tail kernel & Fortran floor grid),
binds R23-DISTANCE HI-CF4 (628 targets / 274 observed / 354 missing) + S02
calibration obstruction diagnostics, and keeps SQ-P1-ANCHOR / S02 BLOCKED_INPUT
and S03-S06 BLOCKED_DEPENDENCY as governed by R78/R86/R89.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import platform
import resource
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[6]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from htt.obsstat import p1_fast

OUT_DIR = Path(__file__).resolve().parent
OUT_JSON = OUT_DIR / "RESULT.json"

PROG = ROOT / "docs/research_program/observational_publication_20261015"
PAIRED_NPZ = PROG / "CONTINUATION_20261018/P1/results/paired_functional_arrays.npz"
P1_SNAP = PROG / "CONTINUATION_20261018/P1/results/FUNCTIONAL_SENSITIVITY_RESULT.json"
S02_OBST = PROG / "CONTINUATION_20261018/S02_EXECUTION_20261018/results/S02_CALIBRATION_OBSTRUCTION.json"
R23_DIST = PROG / "CONTINUOUS_RESEARCH_20261023/execution/R23-DISTANCE/conditional_fit/RESULT.json"
R23_CONG = PROG / "CONTINUOUS_RESEARCH_20261023/execution/R23-CONGRUENCE/RESULT.json"
R69_P1_LOOP2 = PROG / "R69_P1_FIVEVIEW_PHYSICS_LOOP2_20261119/RESULT.json"
HI_CF4_CSV = Path("/mnt/extdrive/workdir/htt_open_data/cf4/D02_HI_CF4_20261018/TARGET_JOIN_AND_OOF.csv")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    if OUT_JSON.exists():
        raise FileExistsError(f"Create-only refusal to overwrite {OUT_JSON}")
    t0 = time.perf_counter()

    # 1. Reuse historical 21-30 anchor contract
    hist = p1_fast.historical_evidence_21_30()
    assert hist["original_R78_science_status_changed"] is False
    assert hist["physical_claim_upgrade"] is False

    # 2. Load 2,048 coupled 4-window P1 arrays & verify R82 fast kernels
    with np.load(PAIRED_NPZ, allow_pickle=False) as z:
        q_app = np.asarray(z["q_app"], dtype=np.float64)
        weights = np.asarray(z["weights"], dtype=np.float64)
        sample_id = z["sample_id"].copy()
        anchors = np.asarray(z["anchors"], dtype=np.float64)
        floors = np.asarray(z["floors"], dtype=np.float64)
        phys_Q_reason = z["physical_Q_reason"].tolist()
        phys_FG_reason = z["physical_F_G_reason"].tolist()

    snap = json.loads(P1_SNAP.read_text(encoding="utf-8"))
    ts = np.array([row["threshold"] for row in snap["strict_exceedance"]], dtype=np.float64)

    tail_np = p1_fast.joint_tail_bounds(q_app, weights, ts, sample_ids=sample_id, native_lib=None)
    tail_np_rec = p1_fast.last_p1_receipt()
    tail_auto = p1_fast.joint_tail_bounds(q_app, weights, ts, sample_ids=sample_id, native_lib="auto")
    tail_auto_rec = p1_fast.last_p1_receipt()
    tail_maxdiff = float(
        max(
            np.max(np.abs(tail_auto["lower"] - tail_np["lower"])),
            np.max(np.abs(tail_auto["upper"] - tail_np["upper"])),
        )
    )
    assert tail_auto["physical_Pi"] is None

    # Replay saved anchor x floor depth sensitivity grid (Fortran/OpenMP vs NumPy)
    floor_np = p1_fast.floor_depth_grid(q_app, weights, anchors, floors, native_lib=None)
    floor_np_rec = p1_fast.last_p1_receipt()
    # Force auto path over sufficient operations to check Fortran parity when enabled
    grid_anchors = np.linspace(float(anchors.min()), float(anchors.max()), 32)
    grid_floors = np.linspace(float(floors.min()), float(floors.max()), 32)
    floor_dense_np = p1_fast.floor_depth_grid(q_app, weights, grid_anchors, grid_floors, native_lib=None)
    floor_dense_auto = p1_fast.floor_depth_grid(q_app, weights, grid_anchors, grid_floors, native_lib="auto", threads=8)
    floor_dense_rec = p1_fast.last_p1_receipt()
    floor_dense_maxdiff = float(
        max(
            np.max(np.abs(floor_dense_auto["strict_above_one"] - floor_dense_np["strict_above_one"])),
            np.max(np.abs(floor_dense_auto["mean_ratio"] - floor_dense_np["mean_ratio"])),
        )
    )
    assert floor_dense_auto["physical_GF"] is None

    # Physical departure gate checks fail-closed under missing physical map/null
    gate_blocked = p1_fast.physical_departure_gate(
        physical_map_qualified=False,
        physical_null_qualified=False,
        x_bounds=(-0.05, 0.07),
    ) if hasattr(p1_fast, "physical_departure_gate") else {"physical_Pi": None, "status": "BLOCKED_MISSING_PHYSICAL_MAP_OR_NULL"}

    # 3. Inspect S02 calibration obstruction & HI-CF4 628-row workdir anchor census
    s02 = json.loads(S02_OBST.read_text(encoding="utf-8"))
    r23d = json.loads(R23_DIST.read_text(encoding="utf-8"))
    r23c = json.loads(R23_CONG.read_text(encoding="utf-8"))
    r69 = json.loads(R69_P1_LOOP2.read_text(encoding="utf-8"))

    with HI_CF4_CSV.open("r", encoding="utf-8") as f:
        hi_rows = list(csv.DictReader(f))
    outcome_counts = Counter(r["outcome"] for r in hi_rows)
    cf4_status_counts = Counter(r["CF4_status"] for r in hi_rows)
    n_obs_dm = sum(1 for r in hi_rows if r["CF4_selected_group"] == "True")

    elapsed = time.perf_counter() - t0
    input_paths = (PAIRED_NPZ, P1_SNAP, S02_OBST, R23_DIST, R23_CONG, R69_P1_LOOP2, HI_CF4_CSV)
    out = {
        "schema": "htt.r89.g06_p1_result/1",
        "group_id": "G06_P1",
        "node_ids": ["S01", "SQ-P1-ANCHOR", "S02", "S03", "S04", "S05", "S06"],
        "source_sha256": {str(p.relative_to(ROOT) if p.is_relative_to(ROOT) else p): _sha256(p) for p in input_paths},
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "elapsed_seconds": float(elapsed),
            "maxrss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
        },
        "reused_historical_21_30": {
            "original_42_nodes_sha256": hist["original_42_nodes_sha256"],
            "science_nodes_21_30": hist["science_nodes"],
            "r69_loop2_K0_chi": r69["K0_chi"],
        },
        "r82_coupled_2048_p1_replay": {
            "sample_count": int(len(q_app)),
            "window_centers": snap["q_app_definition"] if isinstance(snap["q_app_definition"], str) else "centers",
            "thresholds": ts.tolist(),
            "lower_per_window_any_all": tail_auto["lower"].tolist(),
            "upper_per_window_any_all": tail_auto["upper"].tolist(),
            "tail_numpy_receipt": tail_np_rec,
            "tail_auto_receipt": tail_auto_rec,
            "tail_auto_vs_numpy_maxabs": tail_maxdiff,
            "floor_grid_7x6_mean_ratio_shape": list(floor_np["mean_ratio"].shape),
            "floor_grid_7x6_numpy_receipt": floor_np_rec,
            "floor_grid_32x32_auto_receipt": floor_dense_rec,
            "floor_grid_32x32_auto_vs_numpy_maxabs": floor_dense_maxdiff,
            "physical_Pi": tail_auto["physical_Pi"],
            "physical_GF": floor_dense_auto["physical_GF"],
            "physical_Q_unique_reasons": sorted(set(str(x) for x in phys_Q_reason)),
            "physical_FG_unique_reasons": sorted(set(str(x) for x in phys_FG_reason)),
            "physical_departure_gate": gate_blocked,
        },
        "s02_and_workdir_hi_cf4_anchor_obstruction": {
            "s02_single_window_erasure_radius_mag_median": s02["single_window_erasure_radius_mag"]["quantiles"][1],
            "hi_cf4_target_count": len(hi_rows),
            "hi_cf4_selected_group_count": n_obs_dm,
            "hi_cf4_outcome_counts": dict(outcome_counts),
            "hi_cf4_cf4_status_counts": dict(cf4_status_counts),
            "r23_distance_undefined_count": r23d["undefined_distance_count"],
            "r23_distance_undefined_fraction": r23d["undefined_distance_fraction"],
            "r23_distance_conditional_T_actual": r23d["diagnostic"]["T_actual"],
            "r23_distance_conditional_p_plus_one": r23d["diagnostic"]["p_plus_one"],
            "r23_congruence_status": r23c.get("status"),
        },
        "node_verdicts": {
            "S01": "REUSED_SCOPED",
            "SQ-P1-ANCHOR": "BLOCKED_INPUT",
            "S02": "BLOCKED_INPUT",
            "S03": "BLOCKED_DEPENDENCY",
            "S04": "BLOCKED_DEPENDENCY",
            "S05": "BLOCKED_DEPENDENCY",
            "S06": "BLOCKED_DEPENDENCY",
        },
        "missing_physics_and_next_action": {
            "missing": [
                "Physical normal-frame calibration anchor (not apparent q_app or synthetic floor)",
                "Non-selected HI-CF4 target distances (354/628 missing, Manski uncertainty ~56.4% unidentifiable)",
                "Matched physical cosmological null and spacetime transport law for (Q, Pi, F, G_F)",
            ],
            "next_action": "Obtain unpooled calibration posterior & physical normal-frame anchor before promoting SQ-P1-ANCHOR / S02-S06.",
        },
    }
    OUT_JSON.write_text(json.dumps(out, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "group_id": "G06_P1",
        "elapsed_s": round(elapsed, 3),
        "tail_auto_backend": tail_auto_rec["used"],
        "tail_maxdiff": tail_maxdiff,
        "floor_32x32_backend": floor_dense_rec["used"],
        "floor_maxdiff": floor_dense_maxdiff,
        "hi_cf4_rows": len(hi_rows),
        "hi_cf4_undefined_frac": r23d["undefined_distance_fraction"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
