#!/usr/bin/env python3
"""Bounded independent physics/statistics oracle for A-PR291-R3-PHYSSTAT.

The oracle exercises only synthetic arrays.  It does not read a CF4 catalogue,
inspect another reviewer result, or mutate candidate/shared files.
"""

from __future__ import annotations

import hashlib
import json

import numpy as np

from htt.obsstat.cf4_post275_lane import (
    CF4_FEATURE_ORDER_ID,
    CF4_OPERATOR_IDENTITY_FIELDS,
    RELATIVE_EIGENGAP_FLOOR,
    RELATIVE_SINGULAR_FLOOR,
    Cf4Post275Error,
    analyze_synthetic_eigenspace_drift,
    analyze_synthetic_response_nullspace,
    analyze_synthetic_shear,
    build_cf4_gate_snapshot,
    build_cf4_moment_design,
    build_structural_identified_set,
    build_synthetic_depth_zoa_path,
)
from common.source_separation import (
    build_weak_identification_threshold_contract,
    evaluate_source_separation,
)


def _sha(label: str) -> str:
    return "sha256:" + hashlib.sha256(label.encode("ascii")).hexdigest()


def main() -> int:
    covariance = np.asarray([[1.0, 0.2], [0.2, 1.0]])
    full_rank_response = np.eye(2)

    default_full_rank_rejected = False
    try:
        analyze_synthetic_response_nullspace(
            full_rank_response,
            covariance,
            covariance_id="covariance:oracle:v1",
            response_id="response:oracle:v1",
            parameter_labels=("local", "global"),
            parameter_roles=("LOCAL", "GLOBAL"),
        )
    except Cf4Post275Error as exc:
        default_full_rank_rejected = "retain an unidentified direction" in str(exc)

    overridden = analyze_synthetic_response_nullspace(
        full_rank_response,
        covariance,
        covariance_id="covariance:oracle:v1",
        response_id="response:oracle:v1",
        parameter_labels=("local", "global"),
        parameter_roles=("LOCAL", "GLOBAL"),
        rank_tolerance=2.0,
    )
    overridden_basis = np.asarray(overridden.right_null_basis)
    null_replay_residual = float(
        np.linalg.norm(full_rank_response @ overridden_basis.T, ord=2)
    )

    shear = np.diag([-2.0, 0.5, 1.5])
    registered_shear = analyze_synthetic_shear(
        shear,
        covariance_id="covariance:oracle:v1",
        response_id="response:oracle:v1",
    )
    overridden_shear = analyze_synthetic_shear(
        shear,
        covariance_id="covariance:oracle:v1",
        response_id="response:oracle:v1",
        eigengap_floor=2.0,
    )

    singleton = build_structural_identified_set(
        lower=3.0,
        upper=3.0,
        identification_status="WEAKLY_IDENTIFIED",
        nuisance_box_id="nuisance:oracle:v1",
        response_id="response:oracle:v1",
    )

    identity = {
        name: f"oracle:{name}:v1" for name in CF4_OPERATOR_IDENTITY_FIELDS
    }
    identity.update(
        covariance_id=_sha("oracle-covariance"),
        response_id=_sha("oracle-response"),
        estimand_id=_sha("oracle-estimand"),
        feature_order_id=CF4_FEATURE_ORDER_ID,
    )
    raw_directions = np.asarray(
        [
            (1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0),
            (0, 0, 1), (0, 0, -1), (1, 1, 0), (1, -1, 0),
            (1, 0, 1), (1, 0, -1), (0, 1, 1), (0, 1, -1),
            (1, 1, 1), (-1, 1, 1),
        ],
        dtype=float,
    )
    directions = raw_directions / np.linalg.norm(raw_directions, axis=1)[:, None]
    design = build_cf4_moment_design(
        directions, np.linspace(20.0, 150.0, len(directions)), identity
    )
    depth = build_synthetic_depth_zoa_path(
        (
            {"depth_mpc": 50.0, "support_unit_ids": ("a", "b", "c")},
            {"depth_mpc": 100.0, "support_unit_ids": ("a", "b")},
        ),
        operator_identity=identity,
    )
    gate_response = analyze_synthetic_response_nullspace(
        full_rank_response,
        covariance,
        covariance_id=identity["covariance_id"],
        response_id=identity["response_id"],
        parameter_labels=("local", "global"),
        parameter_roles=("LOCAL", "GLOBAL"),
        rank_tolerance=2.0,
    )
    gate_shear = analyze_synthetic_shear(
        shear,
        covariance_id=identity["covariance_id"],
        response_id=identity["response_id"],
        eigengap_floor=2.0,
    )
    gate_eigenspace = analyze_synthetic_eigenspace_drift(
        shear,
        shear,
        reference_depth_id=depth.path.strata[0].stratum_id,
        candidate_depth_id=depth.path.strata[1].stratum_id,
        depth_path_content_id=depth.path.content_id,
        covariance_id=identity["covariance_id"],
        response_id=identity["response_id"],
        eigengap_floor=2.0,
    )
    source_decision = evaluate_source_separation(
        source_geometry_report_id=identity["estimand_id"],
        covariance_id=identity["covariance_id"],
        nuisance_tangent_id=_sha("oracle-nuisance"),
        normalizer_id=gate_response.normalizer_id,
        normalizer_source_identity="PR291-ORACLE-DIMENSIONLESS-NORMALIZER",
        normalizer_coordinate_map_id=_sha("oracle-normalizer-map"),
        parameter_coordinate_units="dimensionless_beta_c_equals_1",
        provider_available=True,
        covariance_supported=True,
        local_parameter_count=1,
        global_parameter_count=1,
        local_rank=1,
        global_rank=1,
        joint_rank=2,
        principal_angles_radians=(0.1,),
        joint_singular_values=(1.0, 0.05),
        threshold_contract=build_weak_identification_threshold_contract(
            minimum_principal_angle_radians=0.2,
            minimum_normalizer_bound_relative_joint_singular_value=0.01,
        ),
    )
    gates = build_cf4_gate_snapshot(
        design=design,
        depth=depth,
        shear=gate_shear,
        eigenspace_drift=gate_eigenspace,
        response=gate_response,
        source_separation=source_decision,
    )

    result = {
        "schema": "htt.pr291.physstat_oracle.v1",
        "assignment_id": "A-PR291-R3-PHYSSTAT",
        "synthetic_only": True,
        "registered_constants": {
            "relative_singular_floor": RELATIVE_SINGULAR_FLOOR,
            "relative_eigengap_floor": RELATIVE_EIGENGAP_FLOOR,
        },
        "finite_null_rank": {
            "independent_matrix_rank": int(np.linalg.matrix_rank(full_rank_response)),
            "default_full_rank_rejected": default_full_rank_rejected,
            "override_tolerance": overridden.relative_singular_floor,
            "override_reported_rank": overridden.response_rank,
            "override_reported_nullity": overridden.nullity,
            "override_status": overridden.status,
            "purported_null_basis_replay_residual_2norm": null_replay_residual,
            "false_null_reproduced": (
                overridden.response_rank == 0
                and overridden.nullity == 2
                and null_replay_residual > 0.5
            ),
            "gate_source_decision_joint_rank": source_decision.joint_rank,
            "gate_g4_status": gates["G4"]["status"],
            "gate_g7_status": gates["G7"]["status"],
            "false_null_passes_gate_snapshot": (
                gates["G4"]["status"]
                == "PASS_SYNTHETIC_WEAK_IDENTIFICATION_ABSTENTION"
                and gates["G7"]["status"]
                == "PASS_SYNTHETIC_UNIDENTIFIED_DIRECTIONS_PRESERVED"
                and gate_response.response_rank == 0
                and source_decision.joint_rank == 2
            ),
        },
        "eigengap_registration": {
            "eigenvalues": list(registered_shear.eigenvalues),
            "eigengaps": list(registered_shear.eigengaps),
            "registered_status": registered_shear.identification_status,
            "override_floor": 2.0,
            "override_status": overridden_shear.identification_status,
            "classification_flip_reproduced": (
                registered_shear.identification_status
                == "SYNTHETIC_ORBIT_COMPATIBILITY_ONLY"
                and overridden_shear.identification_status == "WEAKLY_IDENTIFIED"
            ),
        },
        "identified_set": {
            "bounds": singleton["bounds"],
            "status": singleton["status"],
            "reported_point": singleton["reported_point"],
            "singleton_mislabeled_nonpoint": (
                singleton["bounds"][0] == singleton["bounds"][1]
                and singleton["status"] == "BOUNDED_BUT_NOT_POINT_IDENTIFIED"
            ),
        },
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    assert result["finite_null_rank"]["false_null_reproduced"]
    assert result["finite_null_rank"]["false_null_passes_gate_snapshot"]
    assert result["eigengap_registration"]["classification_flip_reproduced"]
    assert result["identified_set"]["singleton_mislabeled_nonpoint"]
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
