#!/usr/bin/env python3
"""Independent hostile replay oracle for A-PR291-R5-CODE-REPLAY."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "htt"))
sys.path.insert(0, str(ROOT / "htt" / "src"))

from common.semantic_guards.no_overclaim import scan_text
from common.source_separation import (
    build_weak_identification_threshold_contract,
    evaluate_source_separation,
)
from htt.obsstat.cf4_post275_lane import (
    CF4_FEATURE_ORDER_ID,
    CF4_OPERATOR_IDENTITY_FIELDS,
    Cf4Post275Error,
    analyze_synthetic_eigenspace_drift,
    analyze_synthetic_response_nullspace,
    analyze_synthetic_shear,
    build_cf4_gate_snapshot,
    build_cf4_moment_design,
    build_structural_identified_set,
    build_synthetic_depth_zoa_path,
)


def sha_id(label: str) -> str:
    return "sha256:" + hashlib.sha256(label.encode("ascii")).hexdigest()


def identity() -> dict[str, str]:
    result = {
        name: f"oracle:{name}:synthetic-v1"
        for name in CF4_OPERATOR_IDENTITY_FIELDS
    }
    result.update(
        {
            "covariance_id": sha_id("oracle-covariance"),
            "response_id": sha_id("oracle-response"),
            "estimand_id": sha_id("oracle-source-geometry"),
            "feature_order_id": CF4_FEATURE_ORDER_ID,
        }
    )
    return result


def source_geometry(response) -> dict[str, object]:
    whitened = np.asarray(response.covariance_whitened_response, dtype=float)
    normalized = whitened / np.asarray(response.column_scales, dtype=float)
    local = normalized[:, [
        i for i, role in enumerate(response.parameter_roles) if role == "LOCAL"
    ]]
    global_ = normalized[:, [
        i for i, role in enumerate(response.parameter_roles) if role == "GLOBAL"
    ]]
    joint = np.column_stack((local, global_))

    def rank(matrix: np.ndarray) -> int:
        singular = np.linalg.svd(matrix, compute_uv=False)
        return int(np.count_nonzero(singular > 1.0e-12 * singular[0]))

    local_rank = rank(local)
    global_rank = rank(global_)
    joint_singular = np.linalg.svd(joint, compute_uv=False)
    joint_rank = int(
        np.count_nonzero(joint_singular > 1.0e-12 * joint_singular[0])
    )
    angles: tuple[float, ...] = ()
    if local_rank == local.shape[1] and global_rank == global_.shape[1]:
        local_u = np.linalg.svd(local, full_matrices=False)[0][:, :local_rank]
        global_u = np.linalg.svd(global_, full_matrices=False)[0][:, :global_rank]
        cosines = np.linalg.svd(local_u.T @ global_u, compute_uv=False)
        angles = tuple(float(x) for x in np.arccos(np.clip(cosines, 0.0, 1.0)))
    return {
        "local_rank": local_rank,
        "global_rank": global_rank,
        "joint_rank": joint_rank,
        "principal_angles_radians": angles,
        "joint_singular_values": tuple(float(x) for x in joint_singular),
    }


def decision_for(
    bound_identity: dict[str, str],
    response,
    geometry: dict[str, object],
):
    angles = geometry["principal_angles_radians"]
    assert isinstance(angles, tuple) and angles
    return evaluate_source_separation(
        source_geometry_report_id=bound_identity["estimand_id"],
        covariance_id=bound_identity["covariance_id"],
        nuisance_tangent_id=sha_id("oracle-nuisance"),
        normalizer_id=response.normalizer_id,
        normalizer_source_identity="PR291-ORACLE-DIMENSIONLESS-NORMALIZER",
        normalizer_coordinate_map_id=sha_id("oracle-normalizer-map"),
        parameter_coordinate_units="dimensionless_beta_c_equals_1",
        provider_available=True,
        covariance_supported=True,
        local_parameter_count=1,
        global_parameter_count=1,
        local_rank=geometry["local_rank"],
        global_rank=geometry["global_rank"],
        joint_rank=geometry["joint_rank"],
        principal_angles_radians=angles,
        joint_singular_values=geometry["joint_singular_values"],
        threshold_contract=build_weak_identification_threshold_contract(
            minimum_principal_angle_radians=min(angles),
            minimum_normalizer_bound_relative_joint_singular_value=0.0,
        ),
    )


def gate_fixture(bound_identity: dict[str, str], response, decision):
    raw = np.asarray(
        [
            (1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0),
            (0, 0, 1), (0, 0, -1), (1, 1, 0), (1, -1, 0),
            (1, 0, 1), (1, 0, -1), (0, 1, 1), (0, 1, -1),
            (1, 1, 1), (-1, 1, 1),
        ],
        dtype=float,
    )
    directions = raw / np.linalg.norm(raw, axis=1)[:, None]
    distances = np.linspace(20.0, 150.0, raw.shape[0])
    design = build_cf4_moment_design(directions, distances, bound_identity)
    depth = build_synthetic_depth_zoa_path(
        (
            {"depth_mpc": 50.0, "support_unit_ids": ("g1", "g2", "g3", "g4")},
            {"depth_mpc": 100.0, "support_unit_ids": ("g1", "g2", "g3")},
            {"depth_mpc": 150.0, "support_unit_ids": ("g1", "g2")},
        ),
        operator_identity=bound_identity,
    )
    shear = analyze_synthetic_shear(
        np.diag([2.0, -0.5, -1.5]),
        covariance_id=bound_identity["covariance_id"],
        response_id=bound_identity["response_id"],
    )
    eigenspace = analyze_synthetic_eigenspace_drift(
        np.diag([1.0, 1.0 + 1.0e-11, -2.0 - 1.0e-11]),
        np.diag([1.0 + 1.0e-11, 1.0, -2.0 - 1.0e-11]),
        reference_depth_id=depth.path.strata[0].stratum_id,
        candidate_depth_id=depth.path.strata[1].stratum_id,
        depth_path_content_id=depth.path.content_id,
        covariance_id=bound_identity["covariance_id"],
        response_id=bound_identity["response_id"],
    )
    return build_cf4_gate_snapshot(
        design=design,
        depth=depth,
        shear=shear,
        eigenspace_drift=eigenspace,
        response=response,
        source_separation=decision,
    )


def expect_rejected(label: str, thunk, checks: dict[str, str]) -> None:
    try:
        thunk()
    except Cf4Post275Error as exc:
        checks[label] = f"PASS:{type(exc).__name__}:{exc}"
    else:
        raise AssertionError(f"{label} unexpectedly accepted")


def main() -> int:
    checks: dict[str, str] = {}
    bound_identity = identity()
    covariance = [[1.0, 0.2], [0.2, 1.0]]

    baseline = analyze_synthetic_response_nullspace(
        [[1.0, 0.0, 1.0], [0.0, 1.0, 1.0]],
        covariance,
        covariance_id=bound_identity["covariance_id"],
        response_id=bound_identity["response_id"],
        parameter_labels=("local", "global", "nuisance"),
        parameter_roles=("LOCAL", "GLOBAL", "NUISANCE"),
    )
    baseline_geometry = source_geometry(baseline)
    baseline_decision = decision_for(bound_identity, baseline, baseline_geometry)
    structural = build_structural_identified_set(
        lower=-1.0,
        upper=1.0,
        nuisance_box_id="nuisance:oracle:v1",
        response=baseline,
        source_separation=baseline_decision,
    )
    gates = gate_fixture(bound_identity, baseline, baseline_decision)
    assert structural["response_rank"] == 2
    assert structural["response_nullity"] == 1
    assert gates["G7"]["response_rank"] == 2
    assert gates["G7"]["unidentified_direction_count"] == 1
    checks["baseline_structural_and_g4_g7_replay"] = "PASS"

    nuisance_response = analyze_synthetic_response_nullspace(
        [[1.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
        covariance,
        covariance_id=bound_identity["covariance_id"],
        response_id=bound_identity["response_id"],
        parameter_labels=("local", "global", "nuisance"),
        parameter_roles=("LOCAL", "GLOBAL", "NUISANCE"),
    )
    nuisance_geometry = source_geometry(nuisance_response)
    assert nuisance_response.response_rank == 2
    assert nuisance_geometry["joint_rank"] == 1
    forged_nuisance_geometry = dict(nuisance_geometry)
    forged_nuisance_geometry.update(
        {
            "joint_rank": 2,
            "principal_angles_radians": (0.1,),
            "joint_singular_values": (1.0, 0.05),
        }
    )
    forged_nuisance_decision = decision_for(
        bound_identity, nuisance_response, forged_nuisance_geometry
    )
    expect_rejected(
        "nuisance_excluded_structural",
        lambda: build_structural_identified_set(
            lower=-1.0,
            upper=1.0,
            nuisance_box_id="nuisance:oracle:v1",
            response=nuisance_response,
            source_separation=forged_nuisance_decision,
        ),
        checks,
    )
    expect_rejected(
        "nuisance_excluded_g4_g7",
        lambda: gate_fixture(
            bound_identity, nuisance_response, forged_nuisance_decision
        ),
        checks,
    )

    drift_geometry = dict(baseline_geometry)
    drifted_singular = list(drift_geometry["joint_singular_values"])
    drifted_singular[0] += 1.0e-15
    drift_geometry["joint_singular_values"] = tuple(drifted_singular)
    drifted_decision = decision_for(bound_identity, baseline, drift_geometry)
    expect_rejected(
        "sub_tolerance_content_drift_structural",
        lambda: build_structural_identified_set(
            lower=-1.0,
            upper=1.0,
            nuisance_box_id="nuisance:oracle:v1",
            response=baseline,
            source_separation=drifted_decision,
        ),
        checks,
    )
    expect_rejected(
        "sub_tolerance_content_drift_g4_g7",
        lambda: gate_fixture(bound_identity, baseline, drifted_decision),
        checks,
    )

    forged_rank = analyze_synthetic_response_nullspace(
        [[1.0, 0.0, 1.0], [0.0, 1.0, 1.0]],
        covariance,
        covariance_id=bound_identity["covariance_id"],
        response_id=bound_identity["response_id"],
        parameter_labels=("local", "global", "nuisance"),
        parameter_roles=("LOCAL", "GLOBAL", "NUISANCE"),
    )
    object.__setattr__(forged_rank, "response_rank", 1)
    object.__setattr__(forged_rank, "nullity", 2)
    expect_rejected(
        "rank_nullity_replay_structural",
        lambda: build_structural_identified_set(
            lower=-1.0,
            upper=1.0,
            nuisance_box_id="nuisance:oracle:v1",
            response=forged_rank,
            source_separation=baseline_decision,
        ),
        checks,
    )
    expect_rejected(
        "rank_nullity_replay_g4_g7",
        lambda: gate_fixture(bound_identity, forged_rank, baseline_decision),
        checks,
    )

    forbidden = {
        "reordered_plural": "The analysis identifies the families as Bianchi VII_h.",
        "plural_modifier": "Bianchi families are not public but are identified in the CF4 result.",
        "multiline_active": "The analysis identified several Bianchi\nfamilies from the CF4 statistic.",
        "reverse_scalar": "Bianchi family identification\nfollows from the scalar x/Q result.",
        "unrelated_negation": "The scalar result is not public but establishes Bianchi family identification.",
    }
    for label, text in forbidden.items():
        issues = scan_text(text, path=Path(f"oracle-{label}.md"))
        if not issues:
            raise AssertionError(f"scanner missed {label}")
        checks[f"scanner_{label}"] = "PASS:" + ",".join(
            issue.rule_id for issue in issues
        )

    safe = (
        "The analysis does not identify the families as Bianchi VII_h.\n"
        "Bianchi families are not identified in the CF4 result.\n"
        "Bianchi family identification does not follow from the scalar x/Q result.\n"
    )
    assert scan_text(safe, path=Path("oracle-predicate-downclaims.md")) == ()
    checks["scanner_predicate_scoped_downclaims"] = "PASS"

    print(
        json.dumps(
            {
                "schema": "A-PR291-R5-CODE-REPLAY-ORACLE-V1",
                "status": "PASS",
                "check_count": len(checks),
                "checks": checks,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
