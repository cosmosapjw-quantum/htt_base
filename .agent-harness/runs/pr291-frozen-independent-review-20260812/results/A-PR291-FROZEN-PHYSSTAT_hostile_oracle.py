#!/usr/bin/env python3
"""Independent hostile numerical checks for frozen PR-291 candidate 67076abb."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[5]
sys.path[:0] = [str(ROOT), str(ROOT / "htt/src"), str(ROOT / "htt")]

from htt.obsstat.cf4_post275_lane import (  # noqa: E402
    CF4_FEATURE_ORDER_ID,
    CF4_OPERATOR_IDENTITY_FIELDS,
    Cf4Post275Error,
    analyze_synthetic_response_nullspace,
    analyze_synthetic_shear,
    build_cf4_moment_design,
    build_synthetic_depth_zoa_path,
    fit_synthetic_cf4_moments,
)


def sha(label: str) -> str:
    return "sha256:" + hashlib.sha256(label.encode("ascii")).hexdigest()


def identity() -> dict[str, str]:
    result = {name: f"oracle:{name}:synthetic-v1" for name in CF4_OPERATOR_IDENTITY_FIELDS}
    result.update(
        {
            "covariance_id": sha("oracle-covariance"),
            "response_id": sha("oracle-response"),
            "estimand_id": sha("oracle-estimand"),
            "feature_order_id": CF4_FEATURE_ORDER_ID,
        }
    )
    return result


def directions_distances() -> tuple[np.ndarray, np.ndarray]:
    raw = np.asarray(
        [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1),
         (1,1,0),(1,-1,0),(1,0,1),(1,0,-1),(0,1,1),(0,1,-1),
         (1,1,1),(-1,1,1)], dtype=float
    )
    return raw / np.linalg.norm(raw, axis=1)[:, None], np.linspace(20.0, 150.0, len(raw))


def expect_error(fn, fragment: str) -> None:
    try:
        fn()
    except Cf4Post275Error as exc:
        if fragment not in str(exc):
            raise AssertionError(f"expected {fragment!r}, received {exc!r}") from exc
    else:
        raise AssertionError(f"expected Cf4Post275Error containing {fragment!r}")


def main() -> None:
    checks: dict[str, str] = {}
    ident = identity()
    dirs, distances = directions_distances()
    design = build_cf4_moment_design(dirs, distances, ident)
    truth = np.asarray([9.0, -4.0, 2.0, 1.0, 0.25, -0.15, 0.05, 0.10, -0.08])
    velocities = np.asarray(design.matrix) @ truth
    n = len(velocities)
    covariance = 2.5 * np.eye(n) + 0.03 * (np.ones((n, n)) - np.eye(n))
    report = fit_synthetic_cf4_moments(velocities, design=design, covariance=covariance)
    assert np.allclose(report.coefficients, truth, rtol=0.0, atol=2e-10)
    assert report.effective_rank == 9 and report.residual_chi_square <= 1e-18
    assert report.units[:4] == ("km_per_s",) * 4
    assert report.units[4:] == ("km_per_s_per_Mpc",) * 5
    checks["full_cholesky_gls_and_units"] = "pass"

    ill = np.eye(n)
    ill[0, 0] = 1e-13
    ill[0, 1] = ill[1, 0] = 1e-8
    expect_error(lambda: fit_synthetic_cf4_moments(velocities, design=design, covariance=ill), "ill-conditioned")
    expect_error(lambda: fit_synthetic_cf4_moments(velocities, design=design, covariance=np.eye(n)), "diagonal")
    checks["covariance_refusal"] = "pass"

    response = np.asarray([[1.0, 0.0, 1.0], [0.0, 1.0, 1.0]])
    response_cov = np.asarray([[1.0, 0.35], [0.35, 2.0]])
    base = analyze_synthetic_response_nullspace(response, response_cov, covariance_id=ident["covariance_id"], response_id=ident["response_id"], parameter_labels=("local", "global", "nuisance"), parameter_roles=("LOCAL", "GLOBAL", "NUISANCE"))
    rescaled = analyze_synthetic_response_nullspace(response * np.asarray([1e-180, 1e180, 1.0]), response_cov, covariance_id=ident["covariance_id"], response_id=ident["response_id"], parameter_labels=("local", "global", "nuisance"), parameter_roles=("LOCAL", "GLOBAL", "NUISANCE"))
    assert (base.response_rank, base.nullity) == (2, 1) == (rescaled.response_rank, rescaled.nullity)
    assert np.linalg.norm(response @ np.asarray(base.right_null_basis).T, ord=2) < 1e-12
    assert base.parameter_roles == ("LOCAL", "GLOBAL", "NUISANCE")
    checks["whitened_unit_covariant_rank_and_nullspace"] = "pass"

    near = np.asarray([[1.0, 1.0], [0.0, 1e-14]])
    near_report = analyze_synthetic_response_nullspace(near, response_cov, covariance_id=ident["covariance_id"], response_id=ident["response_id"], parameter_labels=("local", "global"), parameter_roles=("LOCAL", "GLOBAL"))
    assert near_report.response_rank == 1 and near_report.nullity == 1
    checks["relative_rank_floor"] = "pass"

    for scale in (1e-100, 1e100):
        shear = analyze_synthetic_shear(scale * np.diag([1.0, 1.0 + 1e-11, -2.0 - 1e-11]), covariance_id=ident["covariance_id"], response_id=ident["response_id"])
        assert shear.identification_status == "WEAKLY_IDENTIFIED"
        assert shear.required_action == "RESPONSE_EQUIVALENCE_ABSTENTION"
    checks["relative_eigengap_and_abstention"] = "pass"

    rows = (
        {"depth_mpc": 50.0, "support_unit_ids": ("g1", "g2", "g3")},
        {"depth_mpc": 100.0, "support_unit_ids": ("g1", "g2")},
        {"depth_mpc": 150.0, "support_unit_ids": ("g1",)},
    )
    path = build_synthetic_depth_zoa_path(rows, operator_identity=ident)
    assert path.path.nesting_rule == "TARGET_SUPPORT_SUBSET_OF_SOURCE"
    assert len(path.transport_identity_ids) == 2
    expect_error(lambda: build_synthetic_depth_zoa_path((rows[1], rows[0]), operator_identity=ident), "nested")
    changed = dict(ident); changed["zone_of_avoidance_mask_id"] = sha("changed-zoa")
    assert build_synthetic_depth_zoa_path(rows, operator_identity=changed).path.content_id != path.path.content_id
    checks["depth_nesting_transport_and_zoa_binding"] = "pass"

    receipt = json.loads((ROOT / "docs/research_program/post_pr275/data_runs/cf4/PR291_NONEXECUTION_RECEIPT.json").read_text())
    assert receipt["terminal"] == "BLOCKED_PREDECESSOR_FINAL_SUCCESS"
    assert receipt["observed_data_executed"] is False and receipt["public_use"] is False
    assert receipt["numeric_outputs_written"] == []
    assert receipt["claim_tier"] == "diagnostic_only"
    assert receipt["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS"
    checks["blocked_nonexecution_claim_ceiling"] = "pass"
    print(json.dumps({"oracle": "A-PR291-FROZEN-PHYSSTAT", "candidate_sha": "67076abbfce5e6bf549f1282c95729bfe89b4be8", "checks": checks, "status": "pass"}, sort_keys=True))


if __name__ == "__main__":
    main()
