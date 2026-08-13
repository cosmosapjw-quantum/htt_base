#!/usr/bin/env python3
"""Independent hostile oracle for the PR-286 VT-S14 public API."""

from __future__ import annotations

import json
import math
import warnings

import numpy as np

from common.vector_tensor_statistical_inference import (
    ModelCandidate,
    ValidationStatus,
    evaluate_depth_local_global,
)


def evaluate(local: np.ndarray, global_: np.ndarray, covariance: np.ndarray):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        report = evaluate_depth_local_global(
            local,
            covariance=covariance,
            covariance_id="hostile-covariance",
            local_design=local,
            global_design=global_,
            mask_path_id="hostile-mask",
            transfer_source="none",
            principal_angle_floor_radians=1.0e-12,
        )
    return report, tuple(str(item.message) for item in caught)


def main() -> None:
    local = np.asarray((1.0e200, 1.0e200))
    global_ = np.asarray((1.0e200, 1.0e200 + 2.0e185))
    delta = (global_[1] / global_[0]) - 1.0
    stable_angle = math.atan2(abs(delta), 2.0 + delta)
    report, runtime_warnings = evaluate(local, global_, np.eye(2))
    nonfinite_fields = [
        name
        for name in (
            "local_chi_square",
            "global_chi_square",
            "chi_square_difference_global_minus_local",
            "local_amplitude",
            "global_amplitude",
        )
        if not math.isfinite(float(getattr(report, name)))
    ]
    positive_result_minted = (
        stable_angle <= 1.0e-12
        and report.status is ValidationStatus.VALIDATED_REGISTERED_SYNTHETIC
        and report.selected_candidate is ModelCandidate.INDETERMINATE
        and bool(nonfinite_fields)
    )
    assert positive_result_minted

    covariance = np.diag((1.0, 1.0e-32))
    local_rank = np.asarray((1.0, 0.0))
    global_rank = np.asarray((1.0, 1.0e-16))
    design = np.column_stack((local_rank, global_rank))
    whitened = np.linalg.solve(np.linalg.cholesky(covariance), design)
    rank_report, _ = evaluate(local_rank, global_rank, covariance)
    rank_seam = {
        "unwhitened_rank": int(np.linalg.matrix_rank(design)),
        "whitened_rank": int(np.linalg.matrix_rank(whitened)),
        "status": rank_report.status.value,
    }
    assert rank_seam == {
        "unwhitened_rank": 1,
        "whitened_rank": 2,
        "status": "ABSTAIN_NON_IDENTIFIED",
    }

    zero_design_exception = None
    try:
        evaluate(np.zeros(2), np.asarray((1.0, 0.0)), np.eye(2))
    except Exception as exc:  # the concrete leaked type is the evidence
        zero_design_exception = type(exc).__name__
    assert zero_design_exception == "ZeroDivisionError"

    proportional, _ = evaluate(
        np.asarray((1.0, 2.0)), np.asarray((2.0, 4.0)), np.eye(2)
    )
    assert proportional.status is ValidationStatus.ABSTAIN_NON_IDENTIFIED

    print(
        json.dumps(
            {
                "oracle": "PR286-VTS14-HOSTILE-NUMERICS",
                "status": "PASS_BUG_REPRODUCED",
                "large_scale_near_proportional": {
                    "stable_angle_radians": stable_angle,
                    "registered_status": report.status.value,
                    "selected_candidate": report.selected_candidate.value,
                    "nonfinite_fields": nonfinite_fields,
                    "runtime_warnings": list(runtime_warnings),
                    "positive_result_minted": positive_result_minted,
                },
                "nonidentity_rank_seam": rank_seam,
                "zero_design_exception": zero_design_exception,
                "proportional_control": proportional.status.value,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
