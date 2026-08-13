#!/usr/bin/env python3
"""Independent PR-284 identity replay and construction-seam oracle."""

from __future__ import annotations

from fractions import Fraction
import json
from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "htt/src"))
sys.path.insert(0, str(ROOT / "htt/htt"))
sys.path.insert(0, str(ROOT / "htt"))

from common.depth_path import (
    DepthPathError,
    build_depth_path,
    build_transport_kernel,
    revalidate_depth_path,
)
from common import depth_path_calibration as contracts
from common.depth_path_calibration import (
    DepthPathCalibrationStatus,
    revalidate_depth_path_reverse_martingale_report,
)
from htt.infer.depth_path_calibration import (
    build_depth_path_doob_calibration,
    build_depth_path_reverse_martingale_report,
    build_unproved_depth_path_reverse_martingale_report,
)


FIXTURES = runpy.run_path(
    str(ROOT / "tests/contracts/test_depth_path_doob_calibration.py")
)


def rejected(call, expected: str) -> str:
    try:
        call()
    except (DepthPathError, TypeError) as exc:
        message = str(exc)
        if expected not in message:
            raise AssertionError(
                f"expected rejection containing {expected!r}, got {message!r}"
            ) from exc
        return message
    raise AssertionError(f"construction unexpectedly survived: {expected}")


def report_kwargs(report) -> dict[str, object]:
    return {
        "report_id": "PR284-R3-INVENTED-IDENTITY",
        "path_content_id": "sha256:no-registered-depth-path",
        "stratum_content_ids": (
            "sha256:no-registered-stratum-1",
            "sha256:no-registered-stratum-2",
            "sha256:no-registered-stratum-3",
        ),
        "threshold_contract": report.threshold_contract,
        "filtration_id": report.filtration_id,
        "filtration_direction": report.filtration_direction,
        "preprocessing_id": report.preprocessing_id,
        "estimator_id": report.estimator_id,
        "premise_evidence_id": "sha256:invented-premise-evidence",
        "premise_status": report.premise_status,
        "finite_target_law": report.finite_target_law,
        "selection_contract": report.selection_contract,
        "path_partitions": report.path_partitions,
        "sigma_field_ids": report.sigma_field_ids,
        "path_values": report.path_values,
        "path_maximum_abs": report.path_maximum_abs,
        "path_maximum_content_id": report.path_maximum_content_id,
        "target_second_moment": report.target_second_moment,
        "exact_tower_equalities": report.exact_tower_equalities,
        "exact_tower_report_content_id": report.exact_tower_report_content_id,
        "unresolved_reasons": (),
        "matched_mock_plan": None,
    }


def equal_support_path():
    stratum = FIXTURES["_stratum"]
    strata = (
        stratum("E1", depth=0.1, kept=(0, 1, 2, 3)),
        stratum("E2", depth=0.2, kept=(0, 1, 2, 3)),
        stratum("E3", depth=0.3, kept=(0, 1)),
    )
    kernels = tuple(
        build_transport_kernel(
            transport_id=f"PR284-EQUAL-K{index}{index + 1}",
            source=source,
            target=target,
            matrix=((1.0,),),
            mask_transport_id=f"sha256:equal-mask-{index}",
            selection_transport_id=f"sha256:equal-selection-{index}",
            covariance_transport_id=f"sha256:equal-covariance-{index}",
            method_id="PR284-EQUAL-SUPPORT-IDENTITY",
            assumptions=("adversarial equal-adjacent-support fixture",),
        )
        for index, (source, target) in enumerate(
            zip(strata[:-1], strata[1:], strict=True), start=1
        )
    )
    return build_depth_path(
        path_id="PR284-EQUAL-ADJACENT-SUPPORT-PATH",
        strata=strata,
        kernels=kernels,
    )


def main() -> int:
    path = FIXTURES["_path"]()
    threshold = FIXTURES["_threshold"]()
    authentic = FIXTURES["_proved_report"]()
    kwargs = report_kwargs(authentic)

    outcomes: dict[str, object] = {}
    outcomes["missing_exact_path_rejected"] = rejected(
        lambda: contracts._build_depth_path_reverse_martingale_report_contract(
            **kwargs
        ),
        "exact DepthPath",
    )
    outcomes["invented_identity_rejected"] = rejected(
        lambda: contracts._build_depth_path_reverse_martingale_report_contract(
            path=path,
            **kwargs,
        ),
        "path content identity",
    )

    object.__setattr__(authentic, "path_content_id", "sha256:post-build-drift")
    outcomes["later_path_drift_rejected"] = rejected(
        lambda: revalidate_depth_path_reverse_martingale_report(authentic),
        "path content identity",
    )

    clean_report = FIXTURES["_proved_report"]()
    proved_calibration = build_depth_path_doob_calibration(
        calibration_id="PR284-R3-PROVED-PUBLIC-FACTORY",
        report=clean_report,
        threshold_contract=threshold,
    )
    assert (
        proved_calibration.status
        is DepthPathCalibrationStatus.BOUND_AVAILABLE_CONDITIONAL_PROVED_PREMISE
    )
    assert proved_calibration.probability_upper_bound == Fraction(1, 4)
    outcomes["proved_public_factory"] = "BOUND_1/4"

    mock_plan = FIXTURES["_mock_plan"](path=path, threshold=threshold)
    unproved = build_unproved_depth_path_reverse_martingale_report(
        report_id="PR284-R3-UNPROVED-PUBLIC-FACTORY",
        path=path,
        threshold_contract=threshold,
        filtration_id="sha256:r3-unproved-filtration",
        preprocessing_id="sha256:common-preprocessing-v1",
        estimator_id="sha256:conditional-estimator-v1",
        premise_evidence_id="sha256:r3-unproved-evidence",
        unresolved_reasons=("tower premise unproved",),
        matched_mock_plan=mock_plan,
    )
    fallback = build_depth_path_doob_calibration(
        calibration_id="PR284-R3-UNPROVED-CALIBRATION",
        report=unproved,
        threshold_contract=threshold,
    )
    assert fallback.status is DepthPathCalibrationStatus.MATCHED_MOCKS_REQUIRED
    assert fallback.probability_upper_bound is None
    outcomes["unproved_public_factory"] = "MATCHED_MOCKS_REQUIRED_NO_BOUND"

    equal_path = revalidate_depth_path(equal_support_path())
    assert (
        equal_path.strata[0].support_unit_ids
        == equal_path.strata[1].support_unit_ids
    )
    law = FIXTURES["_finite_law"]()
    equal_report = build_depth_path_reverse_martingale_report(
        report_id="PR284-R3-EQUAL-SUPPORT-PROVED",
        path=equal_path,
        threshold_contract=threshold,
        finite_target_law=law,
        selection_contract=FIXTURES["_selection"](law),
        path_partitions=(
            ("a", "b", "c", "d"),
            ("left", "left", "right", "right"),
            ("all", "all", "all", "all"),
        ),
        sigma_field_ids=("sha256:E1", "sha256:E2", "sha256:E3"),
        filtration_id="sha256:equal-support-filtration",
        preprocessing_id="sha256:common-preprocessing-v1",
        estimator_id="sha256:conditional-estimator-v1",
        premise_evidence_id="sha256:equal-support-premise",
    )
    equal_calibration = build_depth_path_doob_calibration(
        calibration_id="PR284-R3-EQUAL-SUPPORT-BOUND",
        report=equal_report,
        threshold_contract=threshold,
    )
    assert (
        equal_calibration.status
        is DepthPathCalibrationStatus.BOUND_AVAILABLE_CONDITIONAL_PROVED_PREMISE
    )
    assert equal_calibration.probability_upper_bound == Fraction(1, 4)
    outcomes["strict_support_bypass_survived"] = {
        "adjacent_supports_equal": True,
        "premise_status": equal_report.premise_status.value,
        "probability_upper_bound": "1/4",
    }

    print(json.dumps(outcomes, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
