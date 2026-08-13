#!/usr/bin/env python3
"""Independent frozen physics/statistics oracle for assignment A-PR286-FROZEN-PHYSSTAT."""

from __future__ import annotations

from collections import Counter
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np
import yaml


ROOT = Path(__file__).resolve().parents[4]
RECEIPT_PATH = ROOT / (
    "docs/research_program/post_pr275/pillar_s_adjudication/"
    "PILLAR_S_COMPLETE_ADJUDICATION_V1.json"
)
SIGNATURES_PATH = ROOT / "docs/research_program/vector_tensor/THEOREM_SIGNATURES_V3.yaml"
PROGRAM_PATH = ROOT / "docs/research_program/vector_tensor/VECTOR_TENSOR_PROOF_PROGRAM_V1.yaml"
PR272_SPEC_PATH = ROOT / "docs/research_program/vector_tensor/pr272_spec.yaml"
PR273_PACK_PATH = ROOT / "docs/research_program/vector_tensor/integration/PR273_DIAGNOSTIC_PACK.json"

SOURCE_PASS = {"I-2.1", "I-2.2", "I-2.3", "I-2.9", "I-5.1", "I-5.2", "I-5.3", "I-5.4"}
VT_EXACT = {"VT-S1", "VT-S2", "VT-S4", "VT-S7", "VT-S8"}
VT_SYNTHETIC_PASS = {"VT-S3", "VT-S5", "VT-S6", "VT-S9", "VT-S10", "VT-S11", "VT-S12", "VT-S13"}


def canonical_sha(value: object, *, omit: set[str] | None = None) -> str:
    if omit and isinstance(value, dict):
        value = {key: item for key, item in value.items() if key not in omit}
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def source_replay_sha(row: dict[str, object]) -> str:
    return canonical_sha(
        {
            "row_id": row["row_id"],
            "source_group": row["source_group"],
            "source_partition": row.get("source_partition"),
            "proof_class": row.get("proof_class"),
            "source_status": row.get("source_status"),
            "source_statement": row.get("source_statement"),
        }
    )


def fit_gls(data: np.ndarray, design: np.ndarray, covariance: np.ndarray) -> tuple[float, float]:
    inv = np.linalg.inv(covariance)
    amplitude = float(design @ inv @ data) / float(design @ inv @ design)
    residual = data - amplitude * design
    return amplitude, float(residual @ inv @ residual)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    sys.path[:0] = [str(ROOT / "htt/src"), str(ROOT / "htt"), str(ROOT)]
    from common.vector_tensor_statistical_inference import (
        ModelCandidate,
        ValidationStatus,
        evaluate_depth_local_global,
    )

    receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
    signatures = yaml.safe_load(SIGNATURES_PATH.read_text(encoding="utf-8"))
    program = yaml.safe_load(PROGRAM_PATH.read_text(encoding="utf-8"))
    pr272 = yaml.safe_load(PR272_SPEC_PATH.read_text(encoding="utf-8"))
    pr273 = json.loads(PR273_PACK_PATH.read_text(encoding="utf-8"))

    checks: dict[str, bool] = {}
    source_registry = signatures["source_groups"]["proposal_registry_rows"]["entries"]
    program_rows = program["theorems"]["pillar_S"]
    rows = receipt["rows"]
    source = [row for row in rows if row["source_group"] == "proposal_registry_rows"]
    vector = [row for row in rows if row["source_group"] == "vector_tensor_successor"]
    row_map = {row["row_id"]: row for row in rows}

    checks["source_inventory_58"] = (
        len(source_registry) == len(source) == 58
        and [row["entry_id"] for row in source_registry] == [row["row_id"] for row in source]
        and Counter(row["source_partition"] for row in source_registry) == {"I": 30, "II": 24, "BRIDGE": 4}
        and Counter(row["proof_class"] for row in source_registry) == {"TC": 30, "ST": 24, "U": 4}
    )
    checks["vt_inventory_14"] = (
        len(program_rows) == len(vector) == 14
        and [row["id"] for row in program_rows] == [f"VT-S{i}" for i in range(1, 15)]
        and [row["row_id"] for row in vector] == [f"VT-S{i}" for i in range(1, 15)]
    )
    checks["statement_replay"] = all(
        row["source_replay_identity_sha256"] == source_replay_sha(row) for row in rows
    )
    checks["source_dispositions"] = (
        {row["row_id"] for row in source if row["verdict"] == "PASS"} == SOURCE_PASS
        and all(row["evidence_class"] == "EXACT_PROOF" for row in source if row["row_id"] in SOURCE_PASS)
        and all(row["verdict"] == "INCONCLUSIVE_WITH_RECEIPT" for row in source if row["row_id"] not in SOURCE_PASS)
    )
    checks["vt_evidence_ceiling"] = (
        all(row_map[key]["evidence_class"] == "EXACT_TYPED_PROOF" and row_map[key]["verdict"] == "PASS" for key in VT_EXACT)
        and all(row_map[key]["evidence_class"] == "PREREGISTERED_SYNTHETIC_VALIDATION_ONLY" and row_map[key]["verdict"] == "PASS" for key in VT_SYNTHETIC_PASS)
        and row_map["VT-S14"]["evidence_class"] == "PREREGISTERED_SYNTHETIC_VALIDATION_ONLY"
        and row_map["VT-S14"]["verdict"] == "BLOCKED_WITH_RECEIPT"
        and row_map["VT-S14"]["source_status_effect"] == "RETAIN_PROGRAM_OBLIGATION"
        and all(row["claim_ceiling"] == "diagnostic_only" for row in rows)
    )
    statistical_rows = [row_map[f"VT-S{i}"] for i in (3, 5, 6, 9, 10, 11, 12, 13, 14)]
    checks["estimand_law_covariance_preregistered"] = all(
        row["estimand"] not in {"", "UNAVAILABLE"}
        and row["sampling_law"] not in {"", "UNAVAILABLE"}
        and row["finite_or_asymptotic_status"] == "FINITE_PREREGISTERED_SYNTHETIC"
        and isinstance(row["preregistration_evidence"], dict)
        and isinstance(row["coverage_evidence"], dict)
        for row in statistical_rows
    )
    checks["units_sign_prior_rank_typed"] = all(
        row["units_normalization_and_frame"]
        and row["sign_orientation_convention"]
        and row["prior_applicability_and_identity"] == "NOT_APPLICABLE_NO_PRIOR_IN_REGISTERED_ROW"
        and row["rank_and_identification_scope"]
        for row in vector
    )
    checks["coverage_and_controls_visible"] = all(
        row["positive_cell_terminal"] == "PASS_REGISTERED_POSITIVE_CELL"
        and row["negative_control_terminal"] == "EXPECTED_NEGATIVE_CONTROL_KILLED"
        and row["negative_controls"]
        for row in statistical_rows
    )
    checks["claim_and_ownership_firewall"] = (
        receipt["metadata"]["claim_tier"] == "diagnostic_only"
        and receipt["metadata"]["observed_data_executed"] is False
        and receipt["metadata"]["public_use"] is False
        and receipt["metadata"]["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS"
        and receipt["mio_forbidden_outputs"] == ["likelihood", "posterior", "Bayes_factor", "evidence"]
        and receipt["ownership"]["HTT"].startswith("model-dependent")
        and receipt["ownership"]["MIO"].endswith("only")
    )
    checks["q_f_g_pi_diagnostic_only"] = (
        pr273["observed_data"] is False
        and pr273["claim_ceiling"] == "diagnostic_only"
        and pr273["transfer_source"] == "none"
        and "G_F is represented by the typed depth-path successor, not a scalar" in pr273["caveats"]
        and "Bianchi family identification or ranking" in pr273["forbidden_use"]
        and set(pr273["scalar_successor_mapping"]) == {"x", "Q", "F", "G_F", "Pi"}
    )
    checks["receipt_content_address"] = (
        receipt["receipt_content_sha256"] == canonical_sha(receipt, omit={"receipt_content_sha256"})
    )

    cfg = pr272["preregistration"]["depth_local_global"]
    covariance = np.asarray(cfg["covariance"], dtype=float)
    local = np.asarray(cfg["local_design"], dtype=float)
    global_ = np.asarray(cfg["global_design"], dtype=float)
    inv = np.linalg.inv(covariance)
    registered_angle = math.acos(
        abs(float(local @ inv @ global_))
        / math.sqrt(float(local @ inv @ local) * float(global_ @ inv @ global_))
    )
    rank_receipt = row_map["VT-S14"]["rank_and_identification_scope"]
    checks["registered_whitened_rank_angle"] = (
        np.linalg.matrix_rank(np.column_stack((local, global_))) == 2
        and math.isclose(registered_angle, rank_receipt["whitened_principal_angle_radians"], rel_tol=0.0, abs_tol=2e-15)
        and registered_angle > rank_receipt["principal_angle_floor_radians"]
    )

    data = 3.2 * local + np.asarray((0.05, -0.02, 0.03, -0.01))
    report = evaluate_depth_local_global(
        data,
        covariance=covariance,
        covariance_id="oracle-nonidentity",
        local_design=local,
        global_design=global_,
        mask_path_id="oracle-mask",
        transfer_source="none",
    )
    local_amp, local_chi2 = fit_gls(data, local, covariance)
    global_amp, global_chi2 = fit_gls(data, global_, covariance)
    checks["nonidentity_gls_differential"] = (
        report.status is ValidationStatus.VALIDATED_REGISTERED_SYNTHETIC
        and report.selected_candidate is ModelCandidate.LOCAL
        and math.isclose(report.local_amplitude, local_amp, rel_tol=1e-13, abs_tol=1e-13)
        and math.isclose(report.global_amplitude, global_amp, rel_tol=1e-13, abs_tol=1e-13)
        and math.isclose(report.local_chi_square, local_chi2, rel_tol=1e-13, abs_tol=1e-13)
        and math.isclose(report.global_chi_square, global_chi2, rel_tol=1e-13, abs_tol=1e-13)
    )
    proportional = evaluate_depth_local_global(
        local,
        covariance=covariance,
        covariance_id="oracle-nonidentity",
        local_design=local,
        global_design=2.0 * local,
        mask_path_id="oracle-mask",
        transfer_source="none",
    )
    checks["nonidentity_proportional_abstention"] = (
        proportional.status is ValidationStatus.ABSTAIN_NON_IDENTIFIED
        and proportional.selected_candidate is ModelCandidate.INDETERMINATE
    )

    # Accepted finite SPD input at extreme scale reveals a bounded API hardening gap.
    # This is outside the byte-frozen registered covariance cell, so it is recorded
    # as a residual risk and does not replace the in-scope fixed-design verdict.
    extreme = np.diag([1.0e-320, 1.0, 2.0, 3.0])
    with np.errstate(all="ignore"):
        extreme_report = evaluate_depth_local_global(
            local,
            covariance=extreme,
            covariance_id="oracle-extreme-conditioning",
            local_design=local,
            global_design=global_,
            mask_path_id="oracle-mask",
            transfer_source="none",
        )
    extreme_fields = [
        extreme_report.local_chi_square,
        extreme_report.global_chi_square,
        extreme_report.chi_square_difference_global_minus_local,
        extreme_report.local_amplitude,
        extreme_report.global_amplitude,
    ]
    residual_risk = {
        "id": "R-PR286-EXTREME-COVARIANCE-NONFINITE",
        "outside_registered_covariance_cell": True,
        "reproduced": (
            extreme_report.status is ValidationStatus.VALIDATED_REGISTERED_SYNTHETIC
            and not all(math.isfinite(value) for value in extreme_fields)
        ),
        "status": extreme_report.status.value,
        "selected_candidate": extreme_report.selected_candidate.value,
        "all_numeric_fields_finite": all(math.isfinite(value) for value in extreme_fields),
        "target": "htt/src/common/vector_tensor_statistical_inference.py:evaluate_depth_local_global",
    }

    passed = all(checks.values()) and residual_risk["reproduced"]
    output = {
        "schema": "htt.pr286.frozen_physstat_oracle.v1",
        "candidate_sha": "f2fb069d4ac5bdcd18564839ffa236bd242ca115",
        "registered_claim_pass": all(checks.values()),
        "oracle_pass": passed,
        "checks": checks,
        "registered_covariance_condition_number": float(np.linalg.cond(covariance)),
        "registered_whitened_principal_angle_radians": registered_angle,
        "nonidentity_gls": {
            "selected_candidate": report.selected_candidate.value,
            "local_chi_square": report.local_chi_square,
            "global_chi_square": report.global_chi_square,
        },
        "residual_risk": residual_risk,
    }
    output_path = ROOT / args.output
    output_path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"oracle_pass": passed, "output": args.output}, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
