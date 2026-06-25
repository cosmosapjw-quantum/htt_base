#!/usr/bin/env python3
"""Evidence-only CoVe verifier (concise chain-of-checks) for the PR07/PR08
synthetic + theorem gates.

Reads the docs/generated/pr07_*.json products written by
run_pr07_experiments.py and emits docs/generated/pr07_cove_report.json with
schema htt.pr07.cove.v1. Failure is a nonzero exit. This records verifiable
checks only; it does not store any private reasoning transcript.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import numpy as np

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "docs/generated"


def load(name: str) -> dict:
    return json.loads((GEN / name).read_text())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=GEN / "pr07_cove_report.json")
    args = parser.parse_args()

    a = load("pr07_paper_a.json")
    b = load("pr07_paper_b.json")
    k1 = load("pr07_k1_global_synthetic.json")
    k5 = load("pr07_k5_hierarchical_synthetic.json")
    k6 = load("pr07_k6_affine_ensemble_synthetic.json")
    checks: list[dict] = []

    def check(cid: str, condition: bool, evidence: object, requirement: str) -> None:
        checks.append({"id": cid, "pass": bool(condition), "evidence": evidence, "requirement": requirement})

    check("A_duplicate_rank",
          a["duplicate"]["rank_A"] == a["duplicate"]["rank_AA"] and a["duplicate"]["nullspace_equals_x_minus_x"],
          a["duplicate"], "duplicate adds no rank; equality claim requires full-column-rank fixture")
    check("A_radial_vorticity", a["radial_vorticity_max_abs"] < 5e-12, a["radial_vorticity_max_abs"],
          "antisymmetric radial contraction is zero")
    check("A_shell_degeneracy", a["single_shell_rank"] == 3 and a["broad_depth_rank"] == 6,
          {"single": a["single_shell_rank"], "broad": a["broad_depth_rank"]}, "one shell rank 3, broad depth rank 6")
    check("A_temporal_tensor_rank", a["temporal_tensor_rank"] == 15, a["temporal_tensor_rank"],
          "three independent temporal rows times five STF modes")
    check("A_boost", a["boost"]["lorentz_error"] < 5e-13 and a["boost"]["nonadditivity_norm"] > 1e-6,
          a["boost"], "Lorentz and non-Euclidean composition (NOT a Wigner-angle claim)")
    check("A_first_jet", a["first_jet"]["same_pointwise_velocity"] and a["first_jet"]["different_first_jet"],
          a["first_jet"], "point value does not determine first jet")

    rc = b["random_conservation"]
    check("B_random_conservation",
          rc["samples"] >= 1000 and rc["max_energy_residual"] < 1e-11 and rc["max_momentum_residual"] < 1e-11 and rc["minimum_1_minus_wv2"] > 1e-4,
          rc, "1000 admissible states; independent residuals <1e-11")
    ct = b["constraint_transport"]
    check("B_constraint_transport",
          abs(ct["gauss_transport_residual"]) < 1e-11 and ct["codazzi_transport_residual_norm"] < 1e-11,
          ct, "Gauss and Codazzi transport identities")
    integ = b["integrator_crosscheck"]
    maxerr = max(v for method in integ.values() for v in method.values())
    check("B_integrators", maxerr < 1e-9, integ, "DOP853/Radau exact-dust error <1e-9")

    min_local = float(min(k1["local_p"]))
    check("K1_max_scan",
          k1["global_p"] >= min_local and 0.0 < k1["global_p"] <= 1.0 and k1["simulation_count"] >= 1000,
          {"min_local": min_local, "global": k1["global_p"], "n": k1["simulation_count"]},
          "synthetic max-scan global p is finite and no smaller than the most extreme local rank p")

    h68 = float(np.mean(k5["hierarchical_component_coverage_68"]))
    h95 = float(np.mean(k5["hierarchical_component_coverage_95"]))
    n68 = float(np.mean(k5["naive_component_coverage_68"]))
    hbias = float(np.linalg.norm(k5["hierarchical_mean_bias_km_s"]))
    nbias = float(np.linalg.norm(k5["naive_mean_bias_km_s"]))
    check("K5_hierarchical_coverage",
          k5["simulations"] >= 400 and abs(h68 - 0.68) < 0.05 and abs(h95 - 0.95) < 0.04,
          {"h68": h68, "h95": h95, "n68": n68, "simulations": k5["simulations"]},
          "mechanics-only hierarchical coverage near nominal")
    check("K5_bias_reduction", hbias < nbias,
          {"hierarchical_bias_norm": hbias, "naive_bias_norm": nbias},
          "registered random-effect model reduces deliberate selection-offset bias")

    full_omega = np.linalg.norm(k6["full_reconstruction_vorticity_mean"])
    check("K6_curl_suppression",
          k6["potential_projected_vorticity_max_norm"] < 1e-10 and full_omega > 1e-4,
          {"full_mean_norm": float(full_omega), "potential_max_norm": k6["potential_projected_vorticity_max_norm"]},
          "potential projection erases curl present before projection")

    passed = all(c["pass"] for c in checks)
    payload = {
        "schema": "htt.pr07.cove.v1",
        "status": "PASS_WITH_REGISTERED_DELEGATIONS" if passed else "FAIL",
        "checks": checks,
        "delegations": [
            "BLOCKED_MISSING_PR4_E2E_ACCESS",
            "BLOCKED_MISSING_RELEASE_MOCK_OWNERSHIP",
            "BLOCKED_MISSING_FIELD_REALIZATIONS",
            "AWAITING_NATIVE_LOWELL_SOLVER",
            "LOCAL_WOLFRAM_XACT_GATE_REQUIRED",
        ],
        "claim_boundary": "synthetic/theorem mechanics only; no observational estimate, family identification, global tilt, or physical vorticity detection",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps({"status": payload["status"], "checks_passed": sum(c["pass"] for c in checks), "n_checks": len(checks)}, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
