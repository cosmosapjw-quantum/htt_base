"""Assemble R106 records: executed commands (with rc/wall/RSS) and node links with input SHA-256."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
R106 = ROOT / "docs/research_program/observational_publication_20261015/R106_RESEARCH_20261124"
R105 = R106.parent / "R105_RESEARCH_20261124"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def timings(log_dir):
    rows = []
    for f in sorted(Path(log_dir).glob("*.time")):
        text = f.read_text().strip().splitlines()
        line = next((t for t in reversed(text) if "|rc=" in t), None)
        if line is None:
            continue
        cmd, rc, wall, rss = line.rsplit("|", 3)
        rows.append({"label": f.stem, "command": cmd, "return_code": int(rc.split("=")[1]),
                     "wall_s": float(wall.split("=")[1]), "maxrss_kB": int(rss.split("=")[1])})
    return rows


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--log-dir", type=Path, required=True)
    p.add_argument("--start-commit", required=True)
    a = p.parse_args()
    nodes = {n["id"] for n in json.loads((R105 / "NODE60_EXECUTION.json").read_text())["nodes"]}
    j = lambda rel: json.loads((R106 / rel).read_text())
    stab, rei = j("CORAS/CORAS_STABILITY.json"), j("REI/REI_RESTART_REPLAY.json")
    merged = j("COMMANDER/COMMANDER_MERGED_00000_00006.json")
    pairs = {i: j(f"COMMANDER/COMMANDER_PAIR_0000{i}.json") for i in (3, 4, 5, 6)}
    solver = j("SOLVER/SOLVER_STAGE_RATE_FINAL.json")
    links = {
        "H02": {"class": "conditional prediction (CORAS realization scatter given 2MRS); numerical convergence (mesh axes)",
                "evidence": ["CORAS/CORAS_STABILITY.json", "CORAS/CORAS_H02_EXTENDED.json", "CORAS/CORAS_H02_EXTENDED_AXES.json"],
                "inputs": {"coras_donor_commit": "45ab25635aa32869ce207511d556ea257ab8a591",
                           "coras_pilot_binary_sha256": "a5450321da56b0ad46326ac74350bf9ddf641aed14458903b48228efb8c3da79",
                           "run_files": stab.get("inputs") or stab.get("run_files")},
                "status": "pending", "remaining_input": "independent posterior field ensemble (Manticore field.h5 or equivalent) and CF3-independent growth/bulk calibration"},
        "SQ-CF4": {"class": "conditional prediction (held-out scores conditional on CF3 overlap and CF3-calibrated fsigma8/bulk)",
                   "evidence": ["CORAS/CF4_MARKS128.json", "CORAS/CF4_MARKS8_MAIN.json", "CORAS/CF4_MARKS128_INFLUENCE.json", "CF3/CF3_OVERLAP.json.gz"],
                   "status": "ready_scoped", "remaining_input": "VizieR J/AJ/152/50 table3.dat for CF3-internal method attribution; K-band photometry for non-2MRS 6dFGSv rows"},
        "SQ-CMB-NULL": {"class": "numerical reproduction of 7 matched PR3 Commander pairs; no calibrated null",
                        "evidence": ["COMMANDER/COMMANDER_MERGED_00000_00006.json"] + [f"COMMANDER/COMMANDER_PAIR_0000{i}.json" for i in (3, 4, 5, 6)],
                        "inputs": {f"pair_{i}": pairs[i]["input_sha256_and_bytes"] for i in pairs},
                        "rank": merged["rank"], "status": "blocked_source", "pairs_reduced": 7, "pairs_required": 300},
        "L03": {"class": "blocked", "status": "pending", "remaining_input": "293 further pairs (356,352,825,600 B at the R105 inventory), HM/OE split products for null tests"},
        "SQ-NATIVE": {"class": "numerical convergence (solver fix and A/B); no physical attribution",
                      "evidence": ["SOLVER/SOLVER_STAGE_RATE_FINAL.json", "SOLVER/SOLVER_SCHEME_SELECT.json", "SOLVER_DIAGNOSIS/HYPOTHESES_AND_SYNTHESIS.json",
                                   "SOLVER_DIAGNOSIS/COLLISION_DEPTH_H1.json", "SOLVER_DIAGNOSIS/LATE_FLOOR.json", "SOLVER_DIAGNOSIS/PICARD_DECAY.json",
                                   "REI/REI_RESTART_REPLAY.json"],
                      "inputs": {"solver_sha256": solver["solver_sha256"], "rei_commit": "56dc609ea9b801c88d3364aed3eee140b3a20d46",
                                 "rei_checkpoints": {k: v for k, v in (rei.get("input_sha256") or {}).items() if "checkpoint" in k}},
                      "status": "blocked_external"},
        "B02": {"class": "numerical convergence", "evidence": ["SOLVER/SOLVER_STAGE_RATE_FINAL.json"], "status": "pending"},
        "SQ-PHOTON-FLUX": {"class": "numerical convergence: sky-dipole vs fluid photon q/E now converges with cells at fixed cap",
                           "evidence": ["SOLVER/SOLVER_STAGE_RATE_FINAL.json", "SOLVER_DIAGNOSIS/RENORM_AB.json"], "status": "blocked_source",
                           "remaining_input": "independent photon and matter moment source"},
        "SQ-GAIA": {"class": "conditional diagnostic (within-stratum permutation p for one Quaia realization); no physical attribution",
                    "evidence": ["GAIA/GAIA_NULL_REFIT.json", "GAIA/GAIA_OBSERVED.json"], "status": "ready_scoped",
                    "remaining_input": "independent AGN-centroid control and scan-law mocks"},
        "SQ-RADIO": {"class": "conditional prediction (p depends on unanchored C_1 of the differential field)",
                     "evidence": ["NVSS/NVSS_REVIEW_CORRECTIONS.json", "NVSS/C1ZERO.json", "NVSS/AMPLITUDE_NUISANCE.json", "NVSS/C1_VALIDATION.json",
                                  "NVSS/NVSS_NULL_MOCKS_PRE_REVIEW.json"],
                     "inputs": {"nvss_provider": "52eb576c1e3e71837f2fca26121789ccc0b316152cca3f25ea2f37ea8ef5a38e",
                                "r65_carriers": "a51da9a98c3d0563446eb61f21aceff69fbfeed5446ec74471177170b8664e89"},
                     "status": "ready_scoped", "remaining_input": "independent data anchoring the l=1 differential selection power"},
        "B03": {"class": "blocked", "status": "pending", "reason": "no calibrated joint null with common beam/mask/frame"},
        "B04": {"class": "blocked", "status": "pending", "reason": "requires B03"},
        "H05": {"class": "not executed in R106", "status": "pending"},
    }
    missing = sorted(set(links) - nodes)
    if missing:
        raise KeyError(f"unknown NODE60 ids {missing}")
    files = sorted(p for p in R106.rglob("*") if p.is_file() and p.name not in ("R106_RESULTS.json", "EXECUTED_COMMANDS.json"))
    (R106 / "EXECUTED_COMMANDS.json").write_text(json.dumps({
        "schema": "htt.r106.executed/1", "lead_commands": timings(a.log_dir),
        "agent_command_records": ["REVIEW/DATA_SUBTASKS_FIRST_PASS.json", "REVIEW/ADVERSARIAL_REVIEW.json", "REVIEW/REMEDIATION.json",
                                  "SOLVER_DIAGNOSIS/HYPOTHESES_AND_SYNTHESIS.json", "GAIA/GAIA_NULL_REFIT.json (provenance)",
                                  "NVSS/RUN_RECORD.json", "REI/COMMANDS.jsonl", "CF3/CF3_OVERLAP.json.gz (code)"],
        "failed_attempts": [
            {"command": "python -B -m scripts.r106.coras_marks_influence (lead rerun 1)", "return_code": 1,
             "first_failing_input": "SyntaxError at coras_marks_influence.py:191 introduced by the lead's wording fix",
             "resolution": "corrected expression; rerun rc=0 (logs infl3.time)"},
            {"command": "python -B -m scripts.r106.solver_stage_rate (first scheme)", "return_code": 0,
             "note": "pure stage-time rate without depth rescaling; superseded after review F1 (inexact applied depth): "
                     "SOLVER/SOLVER_STAGE_RATE_STAGEONLY_SUPERSEDED.json"}]},
        indent=1) + "\n")
    out = {"schema": "htt.r106.results/1", "start_commit": a.start_commit,
           "artifacts_sha256": {str(p.relative_to(R106)): sha(p) for p in files}, "node_links": links,
           "classification_rules": {"physical attribution": "none in R106",
                                    "conditional prediction": "results whose value depends on an unanchored assumption or overlapping calibration sample",
                                    "numerical convergence": "solver and replay results"},
           "physical_Pi": None, "physical_GF": None, "Bianchi_family_attribution": None, "calibrated_p": None}
    (R106 / "R106_RESULTS.json").write_text(json.dumps(out, indent=1, allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
