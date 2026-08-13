#!/usr/bin/env python3
"""Independent hostile physics/statistics oracle for A-PR291-R4-PHYSSTAT."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from common.source_separation import (
    SourceSeparationDecisionStatus,
    build_weak_identification_threshold_contract,
    evaluate_source_separation,
)
from htt.obsstat.cf4_post275_lane import (
    Cf4Post275Error,
    analyze_synthetic_eigenspace_drift,
    analyze_synthetic_response_nullspace,
    analyze_synthetic_shear,
    build_structural_identified_set,
)


def _sha(label: str) -> str:
    return "sha256:" + hashlib.sha256(label.encode("ascii")).hexdigest()


def _decision(response, *, source_joint_rank: int = 2):
    return evaluate_source_separation(
        source_geometry_report_id=_sha("oracle-geometry"),
        covariance_id=_sha("oracle-covariance"),
        nuisance_tangent_id=_sha("oracle-nuisance"),
        normalizer_id=response.normalizer_id,
        normalizer_source_identity="PR291-R4-INDEPENDENT-ORACLE",
        normalizer_coordinate_map_id=_sha("oracle-normalizer-map"),
        parameter_coordinate_units="dimensionless_beta_c_equals_1",
        provider_available=True,
        covariance_supported=True,
        local_parameter_count=1,
        global_parameter_count=1,
        local_rank=1,
        global_rank=1,
        joint_rank=source_joint_rank,
        principal_angles_radians=(0.1,),
        joint_singular_values=(1.0, 0.05),
        threshold_contract=build_weak_identification_threshold_contract(
            minimum_principal_angle_radians=0.2,
            minimum_normalizer_bound_relative_joint_singular_value=0.01,
        ),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    checks: list[dict[str, object]] = []

    covariance = np.asarray([[1.0, 0.2], [0.2, 1.0]])
    baseline_matrix = np.asarray([[1.0, 0.0, 1.0], [0.0, 1.0, 1.0]])
    baseline = analyze_synthetic_response_nullspace(
        baseline_matrix,
        covariance,
        covariance_id=_sha("oracle-covariance"),
        response_id=_sha("oracle-response"),
        parameter_labels=("local", "global", "nuisance"),
        parameter_roles=("LOCAL", "GLOBAL", "NUISANCE"),
    )
    scaled = analyze_synthetic_response_nullspace(
        baseline_matrix * np.asarray([1.0e-200, 1.0e200, 1.0]),
        covariance,
        covariance_id=_sha("oracle-covariance"),
        response_id=_sha("oracle-response"),
        parameter_labels=("local", "global", "nuisance"),
        parameter_roles=("LOCAL", "GLOBAL", "NUISANCE"),
    )
    scale_ok = (baseline.response_rank, baseline.nullity) == (
        scaled.response_rank,
        scaled.nullity,
    ) == (2, 1)
    checks.append(
        {
            "check": "whitened_column_normalized_rank_scale_invariance",
            "passed": scale_ok,
            "baseline_rank_nullity": [baseline.response_rank, baseline.nullity],
            "scaled_rank_nullity": [scaled.response_rank, scaled.nullity],
        }
    )

    null_replay_ok = (
        baseline.null_residual_norm <= baseline.null_residual_bound
        and baseline.null_residual_bound
        < baseline.relative_singular_floor
        * max(1.0, np.linalg.norm(np.asarray(baseline.covariance_whitened_response), 2))
    )
    checks.append(
        {
            "check": "null_replay_bound_independent_of_rank_floor",
            "passed": bool(null_replay_ok),
            "null_residual_norm": baseline.null_residual_norm,
            "null_residual_bound": baseline.null_residual_bound,
            "relative_singular_floor": baseline.relative_singular_floor,
        }
    )

    content_ok = baseline.content_id != scaled.content_id
    checks.append(
        {
            "check": "response_content_binding_changes_under_column_units",
            "passed": content_ok,
            "baseline_content_id": baseline.content_id,
            "scaled_content_id": scaled.content_id,
        }
    )

    shear_statuses = []
    drift_statuses = []
    for scale in (1.0e-100, 1.0, 1.0e100):
        tensor = scale * np.diag([1.0, 1.0 + 1.0e-11, -2.0 - 1.0e-11])
        shear_statuses.append(
            analyze_synthetic_shear(
                tensor,
                covariance_id=_sha("oracle-covariance"),
                response_id=_sha("oracle-response"),
            ).identification_status
        )
        drift_statuses.append(
            analyze_synthetic_eigenspace_drift(
                tensor,
                tensor,
                reference_depth_id="near",
                candidate_depth_id="far",
                depth_path_content_id=_sha("oracle-depth"),
                covariance_id=_sha("oracle-covariance"),
                response_id=_sha("oracle-response"),
            ).identification_status
        )
    eigengap_ok = set(shear_statuses) == {"WEAKLY_IDENTIFIED"} and set(
        drift_statuses
    ) == {"WEAKLY_IDENTIFIED"}
    checks.append(
        {
            "check": "fixed_relative_eigengap_scale_invariance",
            "passed": eigengap_ok,
            "shear_statuses": shear_statuses,
            "drift_statuses": drift_statuses,
        }
    )

    singleton_rejected = False
    try:
        build_structural_identified_set(
            lower=1.0,
            upper=1.0,
            nuisance_box_id="nuisance:oracle",
            response=baseline,
            source_separation=_decision(baseline),
        )
    except Cf4Post275Error:
        singleton_rejected = True
    checks.append(
        {
            "check": "strict_non_singleton_structural_set",
            "passed": singleton_rejected,
        }
    )

    adversarial_matrix = np.asarray([[1.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
    adversarial = analyze_synthetic_response_nullspace(
        adversarial_matrix,
        covariance,
        covariance_id=_sha("oracle-covariance"),
        response_id=_sha("oracle-response"),
        parameter_labels=("local", "global", "nuisance"),
        parameter_roles=("LOCAL", "GLOBAL", "NUISANCE"),
    )
    declared = _decision(adversarial, source_joint_rank=2)
    actual_local_global_rank = int(np.linalg.matrix_rank(adversarial_matrix[:, :2]))
    accepted_set = build_structural_identified_set(
        lower=-1.0,
        upper=1.0,
        nuisance_box_id="nuisance:oracle",
        response=adversarial,
        source_separation=declared,
    )
    rank_provenance_rejected = False
    checks.append(
        {
            "check": "typed_source_rank_recomputed_from_response_role_columns",
            "passed": rank_provenance_rejected,
            "actual_local_global_rank": actual_local_global_rank,
            "declared_local_global_joint_rank": declared.joint_rank,
            "total_response_rank": adversarial.response_rank,
            "decision_status": declared.status.value,
            "accepted_structural_set_status": accepted_set["status"],
            "explanation": (
                "LOCAL and GLOBAL columns are identical, so their actual joint "
                "rank is one. The independent NUISANCE column raises total response "
                "rank to two. The binding compares declared source joint rank only "
                "to total response rank and accepts the forged source geometry."
            ),
        }
    )

    payload = {
        "schema_version": 1,
        "oracle_id": "pr291-r4-physstat-hostile-oracle",
        "numpy_version": np.__version__,
        "checks": checks,
        "summary": {
            "passed": sum(bool(row["passed"]) for row in checks),
            "failed": sum(not bool(row["passed"]) for row in checks),
            "overall": "FAIL" if any(not bool(row["passed"]) for row in checks) else "PASS",
        },
    }
    output = Path(args.output)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload["summary"], sort_keys=True))
    # Executable oracle health passes: it must reproduce the expected hostile finding.
    expected = len(checks) == 6 and checks[-1]["passed"] is False
    return 0 if expected else 2


if __name__ == "__main__":
    raise SystemExit(main())
