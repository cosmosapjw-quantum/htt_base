"""Independent numerical hostile oracle for PR-291 synthetic operators."""

from __future__ import annotations

import json
import math
import sys

import numpy as np

sys.path.insert(0, "htt/src")
sys.path.insert(0, "htt")

from obsstat.cf4_post275_lane import (  # noqa: E402
    Cf4Post275Error,
    analyze_synthetic_response_nullspace,
    analyze_synthetic_shear,
    build_cf4_moment_design,
    fit_synthetic_cf4_moments,
)


def identity() -> dict[str, str]:
    fields = (
        "pipeline_id", "catalogue_product_id", "grouping_id", "row_identity_id",
        "selection_id", "coordinate_frame_id", "sign_orientation_convention_id",
        "distance_scale_id", "velocity_estimator_id", "estimand_id", "depth_path_id",
        "zone_of_avoidance_mask_id", "covariance_id", "nuisance_box_id", "response_id",
        "units_id", "feature_order_id", "null_or_matched_mock_id",
    )
    return {field: "oracle:" + field for field in fields}


def expect_error(callable_, fragment: str) -> None:
    try:
        callable_()
    except Cf4Post275Error as exc:
        if fragment not in str(exc):
            raise AssertionError(f"expected {fragment!r}, got {exc!s}") from exc
    else:
        raise AssertionError(f"expected Cf4Post275Error containing {fragment!r}")


def main() -> None:
    # An overdetermined 9-column full-rank design; explicit GLS oracle uses C^-1.
    raw = np.array([
        [1.0, 0.0, 0.0], [-1.0, 0.0, 0.0], [0.0, 1.0, 0.0],
        [0.0, -1.0, 0.0], [0.0, 0.0, 1.0], [0.0, 0.0, -1.0],
        [1.0, 1.0, 1.0], [-1.0, 1.0, 1.0], [1.0, -1.0, 1.0],
        [1.0, 1.0, -1.0], [-1.0, -1.0, 1.0], [-1.0, 1.0, -1.0],
    ])
    directions = raw / np.linalg.norm(raw, axis=1)[:, None]
    distances = np.linspace(10.0, 120.0, len(directions))
    design = build_cf4_moment_design(directions, distances, identity())
    a = np.asarray(design.matrix)
    coeff = np.array([120.0, -35.0, 12.0, 7.0, 0.31, -0.21, 0.11, 0.07, -0.05])
    velocity = a @ coeff
    rng = np.random.default_rng(291)
    m = rng.normal(size=(len(velocity), len(velocity)))
    covariance = m @ m.T + 0.3 * np.eye(len(velocity))
    report = fit_synthetic_cf4_moments(velocity, design=design, covariance=covariance)
    cinv = np.linalg.inv(covariance)
    explicit = np.linalg.solve(a.T @ cinv @ a, a.T @ cinv @ velocity)
    if not np.allclose(report.coefficients, explicit, rtol=1e-10, atol=1e-10):
        raise AssertionError("Cholesky-whitened estimate differs from explicit GLS")
    if not np.allclose(report.coefficients, coeff, rtol=1e-10, atol=1e-10):
        raise AssertionError("noise-free GLS does not recover injected coefficients")
    # Strict inequality at condition 1e12 is admissible; > 1e12 must refuse.
    ill = covariance.copy()
    vals, vecs = np.linalg.eigh(ill)
    ill = vecs @ np.diag(np.linspace(1.0e-13, 1.0, len(vals))) @ vecs.T
    expect_error(lambda: fit_synthetic_cf4_moments(velocity, design=design, covariance=ill), "ill-conditioned")
    response = np.array([[1.0, 0.0, 1.0], [0.0, 1.0, 1.0]])
    c2 = np.array([[2.0, 0.4], [0.4, 1.0]])
    base = analyze_synthetic_response_nullspace(response, c2, covariance_id="oracle:cov", response_id="oracle:response", parameter_labels=("local", "global", "nuisance"), parameter_roles=("LOCAL", "GLOBAL", "NUISANCE"))
    scaled = analyze_synthetic_response_nullspace(response * np.array([1e-180, 1e180, 1.0]), c2, covariance_id="oracle:cov", response_id="oracle:response", parameter_labels=("local", "global", "nuisance"), parameter_roles=("LOCAL", "GLOBAL", "NUISANCE"))
    if (base.response_rank, base.nullity) != (2, 1) or (scaled.response_rank, scaled.nullity) != (2, 1):
        raise AssertionError("whitened column-normalized response rank is not scale invariant")
    if np.linalg.norm(response @ np.asarray(base.right_null_basis).T, ord=2) > 1e-11:
        raise AssertionError("reported response null basis is not a null basis")
    weak = analyze_synthetic_shear(np.diag([1.0, 1.0 + 1e-11, -2.0 - 1e-11]), covariance_id="oracle:cov", response_id="oracle:response")
    if weak.identification_status != "WEAKLY_IDENTIFIED" or weak.required_action != "RESPONSE_EQUIVALENCE_ABSTENTION":
        raise AssertionError("relative eigengap does not produce abstention")
    print(json.dumps({"status": "PASS", "gls_max_abs_error": float(np.max(np.abs(np.asarray(report.coefficients) - explicit))), "response_rank": base.response_rank, "response_nullity": base.nullity, "weak_status": weak.identification_status}, sort_keys=True))


if __name__ == "__main__":
    main()
