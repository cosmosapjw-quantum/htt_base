"""Assemble R104_RESULTS.json: node IDs, raw-data SHA-256, commands, return codes, residuals, units."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

R104 = Path("docs/research_program/observational_publication_20261015/R104_DATA_SOLVER_CONTINUATION_20261124")
R103 = R104.parent / "R103_SOLVER_SOURCE_CONTINUATION_20261123"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--runs", type=Path, required=True, help="JSON list of executed commands with rc/wall/rss")
    p.add_argument("--start-commit", required=True)
    a = p.parse_args()
    nodes = {n["id"]: n for n in json.loads((R103 / "NODE60_EXECUTION.json").read_text())["nodes"]}
    art = {f.name: sha(f) for f in sorted(R104.glob("*.json")) if f.name != "R104_RESULTS.json"}
    cf4 = json.loads((R104 / "CF4_2MRS_FIELD.json").read_text())
    gaia = json.loads((R104 / "GAIA_PATCH_INFLUENCE.json").read_text())
    jk4 = json.loads((R104 / "RADIO_BLOCK_JACKKNIFE_NSIDE4.json").read_text())
    jk8 = json.loads((R104 / "RADIO_BLOCK_JACKKNIFE_NSIDE8.json").read_text())
    c0 = json.loads((R104 / "COMMANDER_PR3_00000.json").read_text())
    c1 = json.loads((R104 / "COMMANDER_PR3_00001.json").read_text())
    links = {
        "SQ-CF4": {"evidence": ["CF4_2MRS_FIELD.json", "MANTICORE_FETCH_FAILURE.json"],
                   "raw_sha256": {"cf4_table2": "8e908928e68352b59292cf67020a4d70aaa6d30f278dfa6aa3e41a9df808332f",
                                  "sixdf_pv_table1": "08f3d4b264e28efcb574bea4efa370d66e4f299f8254e21bd04979fb8301a14d",
                                  "2mrs_neuralnet_zip": cf4["field_zip_sha256"], **{f"2mrs_v{k}": v for k, v in cf4["field_sha256"].items()},
                                  "courtois_cf4_velocity_fits": cf4["courtois_cf4_internal"].get("sha256")},
                   "status": "analysis_extended_scoped", "manticore_real_realizations": 0},
        "H02": {"evidence": ["CF4_2MRS_FIELD.json"], "status": "blocked_source",
                "remaining_input": "posterior field ensemble (Manticore field.h5 or equivalent) for inter-group covariance"},
        "SQ-CMB-NULL": {"evidence": ["COMMANDER_PR3_00000.json", "COMMANDER_PR3_00001.json", "COMMANDER_PAIR0_REPLAY.json", "COMMANDER_PLAN.json"],
                        "raw_sha256": {"pair0": c0["raw_sha256"], "pair1": c1["raw_sha256"], "masks": c0["config"]["mask_sha256"]},
                        "status": "blocked_source", "pairs_reduced": 2, "pairs_required": 300},
        "L03": {"evidence": ["COMMANDER_PR3_00001.json"], "status": "pending",
                "remaining_input": "release effective beam/pixel window/foreground transfer and 298 further matched pairs"},
        "SQ-GAIA": {"evidence": ["GAIA_PATCH_INFLUENCE.json"], "raw_sha256": {"receipt": gaia["receipt_sha256"], "patch_cache": gaia["patch_cache_sha256"]},
                    "status": "ready_scoped"},
        "SQ-RADIO": {"evidence": ["RADIO_BLOCK_JACKKNIFE_NSIDE4.json", "RADIO_BLOCK_JACKKNIFE_NSIDE8.json"],
                     "raw_sha256": {"nvss_provider": jk4["catalogue_sha256"]}, "status": "ready_scoped",
                     "jk_over_poisson_trace_ratio_xy": [jk4["jk_over_poisson_trace_ratio_xy"], jk8["jk_over_poisson_trace_ratio_xy"]]},
        "SQ-NATIVE": {"evidence": ["SOLVER_AXIS_SWEEP.json", "SOLVER_CELLS_PICARD6.json", "FIRST_DIVERGENCE.json"], "status": "blocked_external"},
        "B02": {"evidence": ["SOLVER_AXIS_SWEEP.json", "SOLVER_CELLS_PICARD6.json"], "status": "pending"},
        "SQ-PHOTON-FLUX": {"evidence": ["FIRST_DIVERGENCE.json", "SOLVER_CELLS_PICARD6.json"], "status": "blocked_source",
                           "note": "sky-dipole vs fluid photon q/E now converges at second order; physical source still external"},
        "B03": {"status": "pending", "reason": "no release-matched beam/transfer and qualified null; no family attribution computed"},
        "B04": {"status": "pending", "reason": "requires B03"},
    }
    for k in links:
        if k not in nodes:
            raise KeyError(f"unknown NODE60 id {k}")
    out = {"schema": "htt.r104.results/1", "start_commit": a.start_commit, "artifacts_sha256": art,
           "executed": json.loads(a.runs.read_text()), "node_links": links,
           "units": {"cf4_window_coefficients": "natural-log distance ratio (R98 basis)", "velocity": "km/s (CMB frame)",
                     "holdout_scores": "nats, held-out log predictive density minus no-flow model",
                     "commander_pseudo_cl": "uK^2 (raw masked pseudo-C_ell, ell>=2)",
                     "gaia_curvature": "microarcsec/yr per unit z^2", "radio_dipole": "dimensionless",
                     "solver_q_over_E": "dimensionless T^{0i}/T^{00}", "solver_cl": "dimensionless bolometric (Delta T/T)^2"},
           "physical_Pi": None, "physical_GF": None, "Bianchi_family_attribution": None, "calibrated_p": None}
    (R104 / "R104_RESULTS.json").write_text(json.dumps(out, indent=1, allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
