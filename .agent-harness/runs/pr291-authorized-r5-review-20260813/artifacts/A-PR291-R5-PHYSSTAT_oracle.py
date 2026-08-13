#!/usr/bin/env python3
"""Independent numerical/property oracle for A-PR291-R5-PHYSSTAT."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(ROOT), str(ROOT / "htt" / "src"), str(ROOT / "htt")]

from common.source_separation import (
    SourceSeparationDecisionStatus,
    build_weak_identification_threshold_contract,
    evaluate_source_separation,
)
from htt.obsstat import cf4_post275_lane as lane


def sha_id(label: str) -> str:
    return "sha256:" + hashlib.sha256(label.encode("ascii")).hexdigest()


def independent_geometry(report: lane.Cf4ResponseNullReport) -> dict[str, object]:
    whitened = np.asarray(report.covariance_whitened_response, dtype=float)
    normalized = whitened / np.asarray(report.column_scales, dtype=float)
    local_idx = [i for i, role in enumerate(report.parameter_roles) if role == "LOCAL"]
    global_idx = [i for i, role in enumerate(report.parameter_roles) if role == "GLOBAL"]
    local = normalized[:, local_idx]
    global_ = normalized[:, global_idx]
    joint = normalized[:, local_idx + global_idx]

    def rank(matrix: np.ndarray) -> tuple[np.ndarray, int]:
        singular = np.linalg.svd(matrix, compute_uv=False)
        observed = int(np.count_nonzero(singular > 1.0e-12 * singular[0]))
        return singular, observed

    _, local_rank = rank(local)
    _, global_rank = rank(global_)
    joint_singular, joint_rank = rank(joint)
    angles: tuple[float, ...] = ()
    if local_rank == local.shape[1] and global_rank == global_.shape[1]:
        left = np.linalg.svd(local, full_matrices=False)[0][:, :local_rank]
        right = np.linalg.svd(global_, full_matrices=False)[0][:, :global_rank]
        cosine = np.linalg.svd(left.T @ right, compute_uv=False)
        angles = tuple(float(v) for v in np.arccos(np.clip(cosine, 0.0, 1.0)))
    return {
        "local_rank": local_rank,
        "global_rank": global_rank,
        "joint_rank": joint_rank,
        "angles": angles,
        "joint_singular": tuple(float(v) for v in joint_singular),
    }


def source_decision(
    report: lane.Cf4ResponseNullReport,
    *,
    source_id: str,
    weak: bool = True,
):
    geometry = independent_geometry(report)
    angles = geometry["angles"]
    assert isinstance(angles, tuple)
    threshold = min(angles) if weak and angles else 0.0
    return evaluate_source_separation(
        source_geometry_report_id=source_id,
        covariance_id=report.covariance_id,
        nuisance_tangent_id=sha_id("oracle-nuisance"),
        normalizer_id=report.normalizer_id,
        normalizer_source_identity="ORACLE-DIMENSIONLESS-NORMALIZER",
        normalizer_coordinate_map_id=sha_id("oracle-normalizer-map"),
        parameter_coordinate_units="dimensionless_beta_c_equals_1",
        provider_available=True,
        covariance_supported=True,
        local_parameter_count=report.parameter_roles.count("LOCAL"),
        global_parameter_count=report.parameter_roles.count("GLOBAL"),
        local_rank=geometry["local_rank"],
        global_rank=geometry["global_rank"],
        joint_rank=geometry["joint_rank"],
        principal_angles_radians=angles,
        joint_singular_values=geometry["joint_singular"],
        threshold_contract=build_weak_identification_threshold_contract(
            minimum_principal_angle_radians=threshold,
            minimum_normalizer_bound_relative_joint_singular_value=0.0,
        ),
    )


def expect_error(callable_, text: str) -> str:
    try:
        callable_()
    except (lane.Cf4Post275Error, TypeError) as exc:
        assert text in str(exc), (text, str(exc))
        return type(exc).__name__
    raise AssertionError(f"expected failure containing {text!r}")


def identity() -> dict[str, str]:
    out = {
        key: f"oracle:{key}:synthetic-v1"
        for key in lane.CF4_OPERATOR_IDENTITY_FIELDS
    }
    out.update(
        covariance_id=sha_id("oracle-covariance"),
        response_id=sha_id("oracle-response"),
        estimand_id=sha_id("oracle-estimand"),
        feature_order_id=lane.CF4_FEATURE_ORDER_ID,
        coordinate_frame_id="Galactic_cartesian_right_handed",
        sign_orientation_convention_id="positive_receding",
        units_id="Mpc_and_km_per_s_and_km_per_s_per_Mpc",
    )
    return out


def main() -> int:
    checks: dict[str, object] = {}
    ids = identity()
    covariance = np.asarray(
        [[2.0, 0.2, 0.1], [0.2, 1.3, 0.15], [0.1, 0.15, 0.9]],
        dtype=float,
    )
    matrix = np.asarray(
        [[1.0, 0.2, 1.0, 0.0], [0.0, 1.0, 1.0, 1.0], [0.5, -0.4, 0.1, 0.5]],
        dtype=float,
    )
    roles = ("LOCAL", "GLOBAL", "NUISANCE", "NUISANCE")
    labels = ("local", "global", "nuisance_a", "nuisance_b")
    baseline = lane.analyze_synthetic_response_nullspace(
        matrix,
        covariance,
        covariance_id=ids["covariance_id"],
        response_id=ids["response_id"],
        parameter_labels=labels,
        parameter_roles=roles,
    )
    geometry = independent_geometry(baseline)
    assert baseline.response_rank == 3 and baseline.nullity == 1
    assert geometry["local_rank"] == 1 and geometry["global_rank"] == 1
    assert geometry["joint_rank"] == 2
    checks["covariance_whitened_rank"] = [baseline.response_rank, baseline.nullity]

    scaled = lane.analyze_synthetic_response_nullspace(
        matrix * np.asarray([1.0e-120, 1.0e120, -3.0, 7.0]),
        covariance,
        covariance_id=ids["covariance_id"],
        response_id=ids["response_id"],
        parameter_labels=labels,
        parameter_roles=roles,
    )
    assert (scaled.response_rank, scaled.nullity) == (3, 1)
    assert independent_geometry(scaled)["joint_rank"] == 2
    checks["column_scale_invariance"] = True

    permutation = [2, 1, 3, 0]
    permuted = lane.analyze_synthetic_response_nullspace(
        matrix[:, permutation],
        covariance,
        covariance_id=ids["covariance_id"],
        response_id=ids["response_id"],
        parameter_labels=tuple(labels[i] for i in permutation),
        parameter_roles=tuple(roles[i] for i in permutation),
    )
    permuted_geometry = independent_geometry(permuted)
    assert (permuted.response_rank, permuted.nullity) == (3, 1)
    assert permuted_geometry["joint_rank"] == 2
    assert np.allclose(
        geometry["joint_singular"], permuted_geometry["joint_singular"],
        rtol=128.0 * np.finfo(float).eps,
        atol=128.0 * np.finfo(float).eps,
    )
    checks["role_preserving_permutation"] = True

    nuisance_lift = lane.analyze_synthetic_response_nullspace(
        [[1.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
        [[1.0, 0.2], [0.2, 1.0]],
        covariance_id=ids["covariance_id"],
        response_id=ids["response_id"],
        parameter_labels=("local", "global", "nuisance"),
        parameter_roles=("LOCAL", "GLOBAL", "NUISANCE"),
    )
    nuisance_geometry = independent_geometry(nuisance_lift)
    assert nuisance_lift.response_rank == 2
    assert nuisance_geometry["joint_rank"] == 1
    nuisance_decision = source_decision(
        nuisance_lift, source_id=ids["estimand_id"], weak=True
    )
    assert nuisance_decision.status is SourceSeparationDecisionStatus.SUM_ONLY
    checks["nuisance_excluded_from_source_rank"] = True

    decision = source_decision(baseline, source_id=ids["estimand_id"], weak=True)
    assert decision.status is SourceSeparationDecisionStatus.WEAKLY_IDENTIFIED
    structural = lane.build_structural_identified_set(
        lower=-2.0,
        upper=4.0,
        nuisance_box_id="oracle:nuisance-box:v1",
        response=baseline,
        source_separation=decision,
    )
    assert structural["reported_point"] is None
    assert structural["confidence_level"] is None
    assert structural["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS"
    checks["strict_structural_set"] = structural["status"]
    checks["singleton_rejected"] = expect_error(
        lambda: lane.build_structural_identified_set(
            lower=1.0,
            upper=1.0,
            nuisance_box_id="oracle:nuisance-box:v1",
            response=baseline,
            source_separation=decision,
        ),
        "strictly ordered",
    )
    checks["sum_only_rejected"] = expect_error(
        lambda: lane.build_structural_identified_set(
            lower=-1.0,
            upper=1.0,
            nuisance_box_id="oracle:nuisance-box:v1",
            response=nuisance_lift,
            source_separation=nuisance_decision,
        ),
        "requires weak identification",
    )

    drifted_singular = list(geometry["joint_singular"])
    drifted_singular[0] += 1.0e-15
    forged = evaluate_source_separation(
        source_geometry_report_id=ids["estimand_id"],
        covariance_id=baseline.covariance_id,
        nuisance_tangent_id=sha_id("oracle-nuisance"),
        normalizer_id=baseline.normalizer_id,
        normalizer_source_identity="ORACLE-DIMENSIONLESS-NORMALIZER",
        normalizer_coordinate_map_id=sha_id("oracle-normalizer-map"),
        parameter_coordinate_units="dimensionless_beta_c_equals_1",
        provider_available=True,
        covariance_supported=True,
        local_parameter_count=1,
        global_parameter_count=1,
        local_rank=1,
        global_rank=1,
        joint_rank=2,
        principal_angles_radians=geometry["angles"],
        joint_singular_values=drifted_singular,
        threshold_contract=decision.threshold_contract,
    )
    checks["sub_tolerance_content_drift_rejected"] = expect_error(
        lambda: lane.build_structural_identified_set(
            lower=-1.0,
            upper=1.0,
            nuisance_box_id="oracle:nuisance-box:v1",
            response=baseline,
            source_separation=forged,
        ),
        "source geometry drifted",
    )

    nearly_singular = np.asarray(
        [
            [1.0, 1.0, 0.0, 1.0],
            [0.0, 0.0, 1.0, 1.0],
            [0.0, 5.0e-13, 0.0, 0.0],
        ],
        dtype=float,
    )
    checks["scientific_rank_not_null_replay_tolerance"] = expect_error(
        lambda: lane.analyze_synthetic_response_nullspace(
            nearly_singular,
            covariance,
            covariance_id=ids["covariance_id"],
            response_id=ids["response_id"],
            parameter_labels=labels,
            parameter_roles=roles,
        ),
        "right-null basis failed numerical replay",
    )
    checks["diagonal_covariance_rejected"] = expect_error(
        lambda: lane.analyze_synthetic_response_nullspace(
            matrix,
            np.eye(3),
            covariance_id=ids["covariance_id"],
            response_id=ids["response_id"],
            parameter_labels=labels,
            parameter_roles=roles,
        ),
        "diagonal covariance shortcut",
    )

    directions = np.asarray(
        [(1.0, 0.0, 0.0), (-1.0, 0.0, 0.0), (0.0, 1.0, 0.0),
         (0.0, -1.0, 0.0), (0.0, 0.0, 1.0), (0.0, 0.0, -1.0),
         (1.0, 1.0, 0.0), (1.0, 0.0, 1.0), (0.0, 1.0, 1.0),
         (1.0, -1.0, 0.0), (1.0, 0.0, -1.0), (0.0, 1.0, -1.0),
         (1.0, 1.0, 1.0), (-1.0, 1.0, 1.0)], dtype=float
    )
    directions /= np.linalg.norm(directions, axis=1)[:, None]
    distances = np.linspace(20.0, 150.0, len(directions))
    design = lane.build_cf4_moment_design(directions, distances, ids)
    design_matrix = np.asarray(design.matrix)
    assert design.units == lane.FEATURE_UNITS
    assert design_matrix[0, 1] == 1.0 and design_matrix[1, 1] == -1.0
    assert design_matrix[0, 4] == distances[0]
    assert ids["coordinate_frame_id"] == "Galactic_cartesian_right_handed"
    assert ids["sign_orientation_convention_id"] == "positive_receding"
    checks["units_and_positive_receding_sign"] = True

    checks["fixed_rank_threshold"] = expect_error(
        lambda: lane.analyze_synthetic_response_nullspace(
            matrix,
            covariance,
            covariance_id=ids["covariance_id"],
            response_id=ids["response_id"],
            parameter_labels=labels,
            parameter_roles=roles,
            rank_tolerance=1.0,
        ),
        "rank_tolerance",
    )
    checks["fixed_eigengap_threshold"] = expect_error(
        lambda: lane.analyze_synthetic_shear(
            np.diag([-2.0, 0.5, 1.5]),
            covariance_id=ids["covariance_id"],
            response_id=ids["response_id"],
            eigengap_floor=1.0,
        ),
        "eigengap_floor",
    )
    shear = lane.analyze_synthetic_shear(
        1.0e100 * np.diag([1.0, 1.0 + 1.0e-11, -2.0 - 1.0e-11]),
        covariance_id=ids["covariance_id"],
        response_id=ids["response_id"],
    )
    assert shear.identification_status == "WEAKLY_IDENTIFIED"
    checks["relative_eigengap_scale_invariance"] = True

    forbidden_api_tokens = ("likelihood", "posterior", "evidence", "bayes")
    public_names = {name.lower() for name in lane.__all__}
    assert not any(any(token in name for token in forbidden_api_tokens) for name in public_names)
    assert not any(name in public_names for name in ("q", "pi", "f", "g_f"))
    checks["likelihood_prior_qfg_absent"] = True
    checks["family_gate"] = lane.FAMILY_GATE

    print(json.dumps({"status": "PASS", "checks": checks}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
