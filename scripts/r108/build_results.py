"""Build R108_RESULTS.json (node -> result files with SHA-256, raw-input receipts, gap-register delta)
and EXECUTED_COMMANDS.json (every timed command line and every lane command log).

Usage: PYTHONPATH=.:htt:htt/src python -m scripts.r108.build_results --start-commit b79b9526b
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from scripts.r108.common import OUT_DIR, REPO, git_state, sha256_file, write_json

DL = Path.home() / "Downloads/htt_r108"
R107 = REPO / "docs/research_program/observational_publication_20261015/R107_CLOUD_SOLVER_DATA_THEORY_20261124"

NODES = {
    "F0-F3 (cloud integration)": ["REVIEW/CLOUD_DIFF_REVIEW.json", "REVIEW/R107_CLAIM_CHECK.json", "F2_COUPLED_LOS.json"],
    "SQ-NATIVE / B02": ["SOLVER/S1_ATLAS.json", "SOLVER/S2_TRUNCATION.json", "SOLVER/S3_CONVERGENCE.json",
                        "SOLVER/S4_BJS_COMPARATOR.json", "SOLVER/S7_LOS_PERFORMANCE.json"],
    "SQ-PHOTON-FLUX": ["SOLVER/S5_PHOTON_MOMENTS.json"],
    "B03 (preparation only)": ["SOLVER/S6_B03_TEMPLATES.json"],
    "REC/REI": ["REI/S8_REPLAY_COMPARISON.json", "REI/S8_LOWZ_TAU.json", "REI/S8_LOWZ_FEASIBILITY.json",
                "REI/S8_UVB_VO_PROBE.json"],
    "SQ-CF4": ["CF4/ACQUISITION.json", "CF4/CF3_TABLE3_OVERLAP.json", "CF4/KBAND_CONTRAST.json",
               "CF4/KBAND_CONTRAST_CORAS128.json"],
    "H02": ["CF4/TWOMPP_FIELD.json"],
    "SQ-CMB-NULL / L03": ["COMMANDER/MERGED.json", "COMMANDER/SPLIT_DIFFERENCE.json", "COMMANDER/ACQUISITION_STATUS.json"],
    "SQ-GAIA / K03": ["GAIA/GAIA_R108_SUMMARY.json", "GAIA/SCANLAW_PIXEL_STATISTICS.json", "GAIA/SCANLAW_VALIDATION.json",
                      "GAIA/SCAN_NULL.json", "GAIA/SCAN_NULL_CALIBRATION.json", "GAIA/FRAME_LEAKAGE.json",
                      "GAIA/AGN_SPLIT.json"],
    "SQ-RADIO": ["RADIO/SUMMARY.json", "RADIO/THEORY_C1.json", "RADIO/P_OF_C1_THEORY.json", "RADIO/RACS_DIPOLE.json",
                 "RADIO/RACS_CASDA_TABLE_VERSIONS.json", "RADIO/V3_DIAGNOSTIC.json"],
    "SQ-FRAME": ["FRAME/CATALOGUE_FRAME_REGISTRY.json"],
    "SQ-LIE-FLUX": ["FRAME/LIE_FLUX_FRAMES.json"],
    "H05": ["FRAME/CF4_BULK_HDIPOLE_JOINT.json", "FRAME/W1TF_BULK_HDIPOLE_JOINT.json", "FRAME/W1TF_CATALOGUE_PROBE.json"],
}

GAP_DELTA = {
    "SQ-NATIVE": "CODE gap closed for the coupled-solver line of sight (review findings R1, R9 and S-4 fixed; optical-substep "
                 "source nodes; S4 exact geodesics against the published BJS template pass the pre-registered 0.99 sky "
                 "correlation). COMPUTE: eight-family atlas at epsilon 2e-4 with S2/S3 tables (S3 rows list every axis above "
                 "1e-3). Canonical state unchanged; no DAG acceptance claimed.",
    "B02": "LoS all-m T/E/B to lmax 256 per family exists (S1); DEPENDENCY on SQ-NATIVE acceptance and qualified nulls remains.",
    "SQ-PHOTON-FLUX": "LoS photon moments exist at the 48 common times (S5); the LoS-minus-hierarchy q/E difference exceeds "
                      "the hierarchy-minus-fluid difference at every cell count (S5 summary), so the line of sight is not yet "
                      "an independent check at that level.",
    "B03": "templates projected through the R105 Commander estimator for the S6 orientation basis; no scoring.",
    "SQ-CF4": "DATA gap closed (D01/D02/D03 with receipts; CF3 table3 membership by agreeing routes, remainder by position "
              "only, CF3_TABLE3_OVERLAP.json); COMPUTE open: the source-level C = N + S_PV + Jcal Sigma_cal Jcal^T + C_sel "
              "was not formed.",
    "H02": "unchanged: D04 (2M++ portal) and D05 (Manticore) unreachable (TCP connect timeouts; receipts in cf4/RECEIPTS.jsonl).",
    "SQ-CMB-NULL": "pairs reduced so far and split-product status in COMMANDER/ACQUISITION_STATUS.json; fewer than 300 pairs.",
    "L03": "unchanged (depends on SQ-CMB-NULL).",
    "SQ-GAIA": "D08/D09 acquired; scan-law and frame-leakage controls built; D10 blocked (archive async limit); "
               "revolution-coherent chromatic systematic unqualified.",
    "K03": "unchanged (after SQ-GAIA).",
    "SQ-RADIO": "theory C1 bracket and RACS-low empirical C1 exist; every p is CONDITIONAL (RADIO/P_OF_C1_THEORY.json); DAG "
                "acceptance (physical k, kappa; overdispersion-reproducing mocks) open.",
    "SQ-FRAME": "registry built with boost/inverse tests; 2MRS entry and 6dFGSv conversion velocity missing.",
    "SQ-LIE-FLUX": "frame velocities and Codazzi ranks/blind direction computed in the production sign convention "
                   "(convention_bridge: D_j sigma^j_i + kappa q_i = 0). The frozen R108 audit recorded a polarity mismatch "
                   "in the legacy IC helper, subsequently repaired in R109. Acceptance blocked (no "
                   "independent sigma_ab, no group-frame orientation).",
    "H05": "first joint bulk + H-dipole step done on R98 windows (CONDITIONAL); W1 TF step blocked (CDS unavailable).",
}

OPTIONAL = {"COMMANDER/SPLIT_DIFFERENCE.json": "split downloads may not have finished in this round"}


def _timed_lines(text: str):
    for line in text.splitlines():
        m = re.match(r"^(?P<cmd>.+)\|rc=(?P<rc>-?\d+)\|wall=(?P<wall>[\d.]+)\|maxrss_kB=(?P<rss>\d+)$", line.strip())
        if m:
            yield {"cmd": m["cmd"], "rc": int(m["rc"]), "wall_s": float(m["wall"]), "maxrss_kB": int(m["rss"])}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start-commit", required=True)
    args = ap.parse_args()
    nodes = {}
    for node, files in NODES.items():
        entries = []
        for rel in files:
            p = OUT_DIR / rel
            if not p.is_file() and rel not in OPTIONAL:
                raise SystemExit(f"result file missing: {rel}")
            entries.append({"file": rel, "present": p.is_file(), **({"sha256": sha256_file(p), "bytes": p.stat().st_size}
                                                                      if p.is_file() else {"reason": OPTIONAL[rel]})})
        nodes[node] = entries
    receipts = []
    for path in sorted(DL.rglob("RECEIPTS.jsonl")):
        for line in path.read_text().splitlines():
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            receipts.append({"receipt_file": str(path.relative_to(DL)),
                             **{k: r.get(k) for k in ("id", "name", "url", "final_url", "bytes", "sha256", "md5", "status",
                                                      "fetched_at_utc", "route", "query", "job_id", "rows")
                                if r.get(k) is not None}})
    gap = json.loads((R107 / "GAP_REGISTER.json").read_text())
    delta = [{"id": row["id"], "canonical_state_R107": row.get("canonical_state"), "R108": GAP_DELTA[row["id"]]}
             for row in gap["rows"] if row["id"] in GAP_DELTA]
    write_json(OUT_DIR / "R108_RESULTS.json", {
        "schema": "htt.r108.results.1", "start_commit": args.start_commit, "git": git_state(),
        "solver_identity_atlas": json.loads((DL / "atlas" / "IDENTITY.json").read_text()),
        "nodes": nodes, "raw_input_receipts": receipts, "gap_register_delta": delta,
        "claim_ceiling": "no physical Pi/G_F, no family attribution, no calibrated p; CONDITIONAL / NUMERICAL / BLOCKED labels per node"})
    commands = []
    for log in sorted((DL / "logs").glob("*.log")):
        for rec in _timed_lines(log.read_text(errors="replace")):
            commands.append({"log": log.name, **rec})
    lane_logs = {}
    for jl in sorted((DL / "logs").glob("*_COMMANDS.jsonl")):
        rows = []
        for line in jl.read_text().splitlines():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        lane_logs[jl.name] = rows
    write_json(OUT_DIR / "EXECUTED_COMMANDS.json", {"schema": "htt.r108.executed_commands.1",
                                                    "timed_commands": commands, "lane_command_logs": lane_logs})


if __name__ == "__main__":
    main()
