"""R102 60-node conditional execution overlay preserving R78 canonical science authority.

Maintains immutable R78 SSOT SHA (`90aba8c1...`) and original-42 canonical SHA
(`e3264e10...`), `new_science_acceptances = 0`, and `next_id = "SQ-CF4"`. Maps R102
concrete native solver (`M08/M09/A03`), raw Planck Commander pair alignment (`D03`
1-pair pre-check), and SQ-CF4 group-holdout / SDSS randoms / 36D component tangent
capabilities onto the 60-node science graph while keeping calibrated observational
inference and Bianchi family attribution explicitly blocked/quarantined.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
R78_DAG_PATH = ROOT / "docs/research_program/observational_publication_20261015/R78_UNIFIED_SCIENCE_DAG_20261119/INTEGRATED_DAG.json"
PUB_DAG_PATH = ROOT / "docs/research_program/observational_publication_20261015/PUBLICATION_DAG.json"
R102_DIR = ROOT / "docs/research_program/observational_publication_20261015/R102_CF4_HOLDOUT_NATIVE_SOLVER_20261123"

EXPECTED_R78_SHA256 = "90aba8c1ca9c8e3a7744be0f071dcfe09b81e5353892aca13878191e20f58c11"
EXPECTED_PUB42_SHA256 = "e3264e105cabf78ddac37addc36cacc3cfa05ee942e33e54b431b22e3e87de0d"


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _verify_r78_authority() -> tuple[dict[str, object], str, str]:
    r78_sha = _sha256_file(R78_DAG_PATH)
    if r78_sha != EXPECTED_R78_SHA256:
        raise ValueError(f"R78 INTEGRATED_DAG SHA mismatch: {r78_sha} != {EXPECTED_R78_SHA256}")
    dag = json.loads(R78_DAG_PATH.read_text(encoding="utf-8"))

    if not PUB_DAG_PATH.is_file():
        raise FileNotFoundError(f"Missing PUBLICATION_DAG baseline: {PUB_DAG_PATH}")
    pub = json.loads(PUB_DAG_PATH.read_text(encoding="utf-8"))
    # Canonical sorted-json node SHA256 over the immutable 42 original nodes
    pub_sha = hashlib.sha256(
        json.dumps(pub["nodes"], sort_keys=True).encode("utf-8")
    ).hexdigest()
    if pub_sha != EXPECTED_PUB42_SHA256:
        raise ValueError(f"PUBLICATION_DAG 42-node SHA mismatch: {pub_sha} != {EXPECTED_PUB42_SHA256}")
    recorded_pub_sha = str(dag["original_42_payload_sha256"])
    if recorded_pub_sha != EXPECTED_PUB42_SHA256:
        raise ValueError(f"R78 original_42_payload_sha256 mismatch: {recorded_pub_sha} != {EXPECTED_PUB42_SHA256}")
    return dag, r78_sha, recorded_pub_sha


JOBS: dict[str, dict[str, object]] = {
    "ACQUISITION_BOUNDED_INTAKE": {
        "module": "scripts.r102.acquire_commander_pair",
        "result": "ACQUISITION_RECEIPT.json",
        "scope": "SDSS randoms v1.1.0 (MD5-verified 284,000,071 B) + Commander PR3 FFP10 noise 00000 (chunked FITS 603,987,840 B).",
    },
    "COMMANDER_PAIR_CHECK": {
        "module": "scripts.r102.commander_pair_check",
        "result": "COMMANDER_PAIR_00000_CHECK.json",
        "scope": "Single FFP10 s+n pair vs PR3 observed alignment, RING/NESTED & K_CMB checks; pseudo-C_l identity only (null UNQUALIFIED).",
    },
    "CF4_HOLDOUT_AND_SELECTION": {
        "module": "scripts.r102.cf4_selection_holdout",
        "result": "CF4_SELECTION_HOLDOUT_RESULTS.json",
        "scope": "6dFGSv 8,885-row 5-fold group CV & Fisher selection uncertainty, 4-row ambiguity policies, 4M SDSS_randoms geometry, 36D component Euler tangents.",
    },
    "NATIVE_SOLVER_CONVERGENCE": {
        "module": "scripts.r102.native_solver_convergence",
        "result": "NATIVE_SOLVER_CONVERGENCE.json",
        "scope": "Coupled Bianchi Einstein-Euler + GeneralLieStokes (T,E,B,V) + MovingFrameThomson + 4-channel TiltedHyrec convergence across 7 families.",
    },
    "R101_PREDICTIVE_AND_COLLISION_REPLAY": {
        "module": "scripts.r101.program",
        "result": "../R101_SIXTH_SOLVER_RESPONSE_20261123/NODE60_EXECUTION.json",
        "scope": "Inherited R101 rank-9 collision, SDIRK2, moving projection, clocked chemistry, and 8,885-row CF4 plug-in baseline.",
    },
}


def _map_r102_jobs(node: dict[str, object]) -> list[str]:
    nid = str(node["id"])
    paper = str(node.get("paper", ""))
    jobs: list[str] = []
    if nid in {"SQ-CF4", "S01", "S02", "S03", "S04", "S05", "S06", "H01", "H02", "H03", "H04", "H05", "H06", "K04", "SQ-P1-ANCHOR", "SQ-CROSS-COV", "PHY-01", "PHY-07"}:
        jobs.append("CF4_HOLDOUT_AND_SELECTION")
    if nid in {"SQ-CMB-NULL", "L03", "L04", "L05", "L06", "B03", "B04", "B05", "PHY-02", "PHY-06"}:
        jobs.append("COMMANDER_PAIR_CHECK")
    if (
        paper == "P5"
        or nid.startswith("B0")
        or nid in {"SQ-NATIVE", "SQ-LIE-FLUX", "SQ-PHOTON-FLUX", "L01", "L02", "L03", "L04", "PHY-02", "PHY-03", "PHY-05", "PHY-06"}
    ):
        jobs.append("NATIVE_SOLVER_CONVERGENCE")
    if not jobs:
        jobs.append("R101_PREDICTIVE_AND_COLLISION_REPLAY")
    return jobs


def build_overlay() -> tuple[dict[str, object], str]:
    dag, r78_sha, pub42_sha = _verify_r78_authority()
    r101_exec_path = ROOT / "docs/research_program/observational_publication_20261015/R101_SIXTH_SOLVER_RESPONSE_20261123/NODE60_EXECUTION.json"
    r101_exec = json.loads(r101_exec_path.read_text(encoding="utf-8")) if r101_exec_path.is_file() else None

    parent_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()

    node_rows = []
    for n in dag.get("nodes", []):
        nid = str(n["id"])
        status = str(n["state"])
        title = str(n.get("objective") or n.get("acceptance") or "")
        r102_jobs = _map_r102_jobs(n)
        native_code_status = (
            "COMPLETE_SCOPED_R102"
            if "NATIVE_SOLVER_CONVERGENCE" in r102_jobs
            else "INHERITED_SCOPED"
        )
        node_rows.append(
            {
                "id": nid,
                "paper": n.get("paper"),
                "title": title,
                "science_status": status,
                "new_scientific_acceptance": False,
                "r102_conditional_jobs": r102_jobs,
                "r102_capability_status": {
                    "native_implementation_and_numerical_validation": native_code_status,
                    "source_conditioned_analysis": "PARTIAL_SCOPED" if any(j in r102_jobs for j in ("CF4_HOLDOUT_AND_SELECTION", "COMMANDER_PAIR_CHECK")) else "INHERITED_ONLY",
                    "calibrated_observational_inference": "BLOCKED_MISSING_UPSTREAM_INPUTS",
                    "bianchi_family_attribution": "BLOCKED_ATLAS_UNQUALIFIED_AND_MISSING_NULL",
                },
            }
        )

    payload: dict[str, object] = {
        "schema": "htt.r102.conditional_execution/1",
        "parent_head": parent_head,
        "science_authority": "docs/research_program/observational_publication_20261015/R78_UNIFIED_SCIENCE_DAG_20261119/INTEGRATED_DAG.json",
        "science_authority_sha256": r78_sha,
        "original_42_sha256": pub42_sha,
        "r101_parent_overlay_schema": None if r101_exec is None else r101_exec.get("schema"),
        "next_id": str(dag["next_action_id"]),
        "counts": {
            "nodes": len(node_rows),
            "canonical_edges": len(dag.get("edges", [])),
            "new_science_acceptances": 0,
        },
        "native_solver_milestones_r102": {
            "M08_general_lie_moving_thomson_einstein_boltzmann": "CODE_AND_CONVERGENCE_COMPLETE_AT_R102_SCOPED",
            "M09_four_channel_tilted_hyrec_jacobians": "CODE_AND_PLANCK2018_VALIDATION_COMPLETE_AT_R102_SCOPED",
            "A03_family_convergence_and_geodesic_oracles": "SEVEN_FAMILY_NUMERICAL_SUITE_COMPLETE_ATLAS_UNQUALIFIED",
            "observational_family_id_and_planck_null_gate": "BLOCKED_D03_A02_M04",
        },
        "source_qualification_guarantees": {
            "source_qualification": "BLOCKED_INPUT",
            "physical_Pi": None,
            "physical_GF": None,
            "calibrated_p": None,
            "Bianchi_family_attribution": None,
            "commander_null_qualified": False,
            "atlas_qualified_for_planck_family_id": False,
        },
        "jobs": JOBS,
        "nodes": node_rows,
    }

    lines = [
        "# R102 60-Node Conditional Execution Map",
        "",
        f"- Authoritative Science DAG: `INTEGRATED_DAG.json` (SHA-256 `{r78_sha}`)",
        f"- Canonical 42 Baseline SHA-256: `{pub42_sha}`",
        f"- Authoritative `next_id`: `{payload['next_id']}` (`new_science_acceptances = 0`)",
        "- Claim quarantine: `NATIVE_CODE_COMPLETE_CONVERGED` (M08/M09/A03 numerical suite) is strictly separated from `SOURCE_CONDITIONED_PARTIAL` (CF4 holdout / 1-pair Commander alignment) and `BLOCKED` calibrated inference / Bianchi family attribution.",
        "",
        "| Node | Paper | R78 Science Status | R102 Conditional Jobs | Code / Source / Inference / Family ID |",
        "|---|---|---|---|---|",
    ]
    for r in node_rows:
        st = r["r102_capability_status"]
        cap = f"{st['native_implementation_and_numerical_validation']} / {st['source_conditioned_analysis']} / {st['calibrated_observational_inference']} / {st['bianchi_family_attribution']}"
        lines.append(f"| {r['id']} | {r['paper']} | {r['science_status']} | {', '.join(r['r102_conditional_jobs'])} | {cap} |")
    md_text = "\n".join(lines) + "\n"
    return payload, md_text


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("action", nargs="?", default="export", choices=("export", "check-node", "verify-sha"))
    ap.add_argument("--node", default="SQ-CF4")
    ap.add_argument("--phase", default="analysis", choices=("analysis", "science"))
    ap.add_argument("--out-dir", type=Path, default=R102_DIR)
    args = ap.parse_args(argv)

    payload, md_text = build_overlay()
    if args.action == "verify-sha":
        print(json.dumps({"r78_sha256": payload["science_authority_sha256"], "next_id": payload["next_id"]}))
        return 0
    if args.action == "check-node":
        match = [n for n in payload["nodes"] if n["id"] == args.node]
        if not match:
            print(json.dumps({"error": f"unknown node {args.node}"}))
            return 2
        node = match[0]
        print(json.dumps(node, indent=2))
        if node["science_status"] != "completed_scoped" and args.phase == "science":
            return 3
        if args.node == "SQ-CF4":
            return 3
        return 0

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "NODE60_EXECUTION.json").write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n")
    (out_dir / "NODE60_EXECUTION.md").write_text(md_text, encoding="utf-8")
    print(
        json.dumps(
            {
                "schema": payload["schema"],
                "science_authority_sha256": payload["science_authority_sha256"],
                "original_42_sha256": payload["original_42_sha256"],
                "next_id": payload["next_id"],
                "nodes": payload["counts"]["nodes"],
                "canonical_edges": payload["counts"]["canonical_edges"],
                "new_science_acceptances": payload["counts"]["new_science_acceptances"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
