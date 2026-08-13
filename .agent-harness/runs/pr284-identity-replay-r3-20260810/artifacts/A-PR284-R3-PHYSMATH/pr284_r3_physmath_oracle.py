#!/usr/bin/env python3
"""Independent exact-arithmetic and hostile-identity oracle for PR-284."""
from __future__ import annotations

from fractions import Fraction
import json
from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "htt" / "src"))
sys.path.insert(0, str(ROOT / "htt"))

from common import depth_path_calibration as contracts  # noqa: E402
from common.depth_path import (  # noqa: E402
    DepthPathError,
    build_depth_path,
    build_mask_stratum,
    build_transport_kernel,
)
from common.depth_path_calibration import (  # noqa: E402
    DepthPathCalibrationStatus,
    ReverseMartingalePremiseStatus,
    build_depth_path_finite_target_law,
    build_depth_path_selection_contract,
    build_depth_path_threshold_contract,
)
from common.sky_support import build_sky_support_from_mask  # noqa: E402
from htt.infer.depth_path_calibration import (  # noqa: E402
    build_depth_path_doob_calibration,
    build_depth_path_matched_mock_plan,
    build_depth_path_reverse_martingale_report,
    build_unproved_depth_path_reverse_martingale_report,
)


WEIGHTS = (Fraction(1, 4),) * 4
TARGET = (Fraction(-3), Fraction(-1), Fraction(1), Fraction(3))
PARTITIONS = (
    ("a", "b", "c", "d"),
    ("left", "left", "right", "right"),
    ("all", "all", "all", "all"),
)


def conditional_values(labels: tuple[str, ...], target=TARGET) -> tuple[Fraction, ...]:
    mass: dict[str, Fraction] = {}
    weighted: dict[str, Fraction] = {}
    for probability, value, label in zip(WEIGHTS, target, labels, strict=True):
        mass[label] = mass.get(label, Fraction()) + probability
        weighted[label] = weighted.get(label, Fraction()) + probability * value
    return tuple(weighted[label] / mass[label] for label in labels)


def exact_event_probability(
    partitions: tuple[tuple[str, ...], ...],
    *,
    target=TARGET,
    threshold_squared: Fraction,
) -> Fraction:
    rows = tuple(conditional_values(row, target=target) for row in partitions)
    return sum(
        (
            probability
            for atom, probability in enumerate(WEIGHTS)
            if max(abs(row[atom]) for row in rows) ** 2 >= threshold_squared
        ),
        Fraction(),
    )


def assert_decreasing_tower() -> None:
    rows = tuple(conditional_values(row) for row in PARTITIONS)
    for fine_labels, coarse_labels, fine_values, coarse_values in zip(
        PARTITIONS[:-1],
        PARTITIONS[1:],
        rows[:-1],
        rows[1:],
        strict=True,
    ):
        fine_to_coarse: dict[str, str] = {}
        for fine, coarse in zip(fine_labels, coarse_labels, strict=True):
            prior = fine_to_coarse.setdefault(fine, coarse)
            assert prior == coarse
        mass: dict[str, Fraction] = {}
        weighted: dict[str, Fraction] = {}
        for probability, value, coarse in zip(
            WEIGHTS, fine_values, coarse_labels, strict=True
        ):
            mass[coarse] = mass.get(coarse, Fraction()) + probability
            weighted[coarse] = weighted.get(coarse, Fraction()) + probability * value
        iterated = tuple(weighted[label] / mass[label] for label in coarse_labels)
        assert iterated == coarse_values


def stratum(suffix: str, *, depth: float, kept: tuple[int, ...]):
    mask = np.zeros(4, dtype=bool)
    mask[list(kept)] = True
    support = build_sky_support_from_mask(
        mask,
        coordinate_frame="GALACTIC",
        completeness_status="synthetic_fixture_complete",
        selection_mode=f"pr284-oracle-selection-{suffix}",
        mock_coverage_status="synthetic_fixture_only",
        pixelization="PR284_UNIT_PIXELS",
    )
    return build_mask_stratum(
        stratum_id=f"PR284-ORACLE-{suffix}",
        depth_coordinate=depth,
        depth_unit="synthetic_depth",
        support_unit_ids=tuple(f"pixel-{index}" for index in kept),
        support_universe_size=4,
        sky_support=support,
        selection_id=f"sha256:oracle-selection-{suffix}",
        covariance_id=f"sha256:oracle-covariance-{suffix}",
        source_artifact_id=f"sha256:oracle-source-{suffix}",
        feature_names=("centered_scalar",),
        feature_unit="dimensionless_diagnostic",
        assumptions=("assignment-local exact oracle",),
    )


def path(*, supports=((0, 1, 2, 3), (0, 1, 2), (0, 1))):
    strata = tuple(
        stratum(f"D{index}", depth=index / 10, kept=tuple(kept))
        for index, kept in enumerate(supports, start=1)
    )
    kernels = tuple(
        build_transport_kernel(
            transport_id=f"PR284-ORACLE-K{index}{index + 1}",
            source=source,
            target=target,
            matrix=((1.0,),),
            mask_transport_id=f"sha256:oracle-mask-k{index}{index + 1}",
            selection_transport_id=f"sha256:oracle-selection-k{index}{index + 1}",
            covariance_transport_id=f"sha256:oracle-covariance-k{index}{index + 1}",
            method_id="PR284-ORACLE-IDENTITY-TRANSPORT-V1",
            assumptions=("assignment-local identity transport",),
        )
        for index, (source, target) in enumerate(
            zip(strata[:-1], strata[1:], strict=True), start=1
        )
    )
    return build_depth_path(
        path_id="PR284-ORACLE-PATH-V1",
        strata=strata,
        kernels=kernels,
    )


def law(*, target=TARGET):
    return build_depth_path_finite_target_law(
        law_id="PR284-ORACLE-LAW-V1",
        common_target_id="PR284-ORACLE-CENTERED-TARGET-V1",
        atom_ids=("atom-a", "atom-b", "atom-c", "atom-d"),
        weights=WEIGHTS,
        common_target=target,
        registration_id="sha256:oracle-law-preregistered-v1",
    )


def selection(finite_law, atom_index=0):
    return build_depth_path_selection_contract(
        selection_id="PR284-ORACLE-SELECTION-V1",
        finite_target_law=finite_law,
        selected_atom_id=finite_law.atom_ids[atom_index],
        selected_atom_index=atom_index,
        selection_rule_id="sha256:oracle-fixed-atom-rule-v1",
        registration_id="sha256:oracle-selection-preregistered-v1",
    )


def threshold(multiplier=Fraction(6, 5)):
    return build_depth_path_threshold_contract(
        contract_id="PR284-ORACLE-THRESHOLD-V1",
        multiplier=multiplier,
        registration_id="sha256:oracle-threshold-preregistered-v1",
    )


def proved_report(*, resolved_path=None, finite_law=None, threshold_contract=None):
    p = path() if resolved_path is None else resolved_path
    q = law() if finite_law is None else finite_law
    t = threshold() if threshold_contract is None else threshold_contract
    return build_depth_path_reverse_martingale_report(
        report_id="PR284-ORACLE-PROVED-REPORT-V1",
        path=p,
        threshold_contract=t,
        finite_target_law=q,
        selection_contract=selection(q),
        path_partitions=PARTITIONS,
        sigma_field_ids=("sha256:oracle-F1", "sha256:oracle-F2", "sha256:oracle-F3"),
        filtration_id="sha256:oracle-decreasing-filtration-v1",
        preprocessing_id="sha256:oracle-common-preprocessing-v1",
        estimator_id="sha256:oracle-conditional-estimator-v1",
        premise_evidence_id="sha256:oracle-independent-exact-replay-v1",
    )


def authentic_builder_kwargs(report) -> dict[str, object]:
    return {
        "report_id": "PR284-ORACLE-HOSTILE-REPORT",
        "path_content_id": report.path_content_id,
        "stratum_content_ids": report.stratum_content_ids,
        "threshold_contract": report.threshold_contract,
        "filtration_id": report.filtration_id,
        "filtration_direction": report.filtration_direction,
        "preprocessing_id": report.preprocessing_id,
        "estimator_id": report.estimator_id,
        "premise_evidence_id": "sha256:oracle-hostile-evidence",
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


def expect_rejection(action, contains: str) -> str:
    try:
        action()
    except DepthPathError as exc:
        assert contains in str(exc), (contains, str(exc))
        return str(exc)
    raise AssertionError(f"hostile construction unexpectedly passed: {contains}")


def main() -> None:
    assert sum(p * x for p, x in zip(WEIGHTS, TARGET, strict=True)) == 0
    second_moment = sum(p * x * x for p, x in zip(WEIGHTS, TARGET, strict=True))
    assert second_moment == 5
    assert_decreasing_tower()
    independent_rows = tuple(conditional_values(row) for row in PARTITIONS)
    assert tuple(row[0] for row in independent_rows) == (-3, -2, 0)

    authentic = proved_report()
    calibration = build_depth_path_doob_calibration(
        calibration_id="PR284-ORACLE-CALIBRATION-V1",
        report=authentic,
        threshold_contract=threshold(),
    )
    assert authentic.path_values == (-3, -2, 0)
    assert authentic.path_maximum_abs == 3
    assert authentic.target_second_moment == 5
    assert calibration.threshold_squared == Fraction(36, 5)
    assert calibration.path_maximum_squared == 9
    assert calibration.path_exceeds_threshold is True
    assert calibration.probability_upper_bound == Fraction(25, 36)
    event_probability = exact_event_probability(
        PARTITIONS, threshold_squared=Fraction(36, 5)
    )
    assert event_probability == Fraction(1, 2)
    assert event_probability <= calibration.probability_upper_bound

    equality_target = (
        Fraction(-1), Fraction(-1), Fraction(1), Fraction(1)
    )
    equality_law = law(target=equality_target)
    equality_threshold = threshold(Fraction(1))
    equality_report = proved_report(
        finite_law=equality_law,
        threshold_contract=equality_threshold,
    )
    equality_calibration = build_depth_path_doob_calibration(
        calibration_id="PR284-ORACLE-EQUALITY-CALIBRATION",
        report=equality_report,
        threshold_contract=equality_threshold,
    )
    assert equality_calibration.path_maximum_squared == 1
    assert equality_calibration.threshold_squared == 1
    assert equality_calibration.path_exceeds_threshold is True

    hostile = authentic_builder_kwargs(authentic)
    missing_path = expect_rejection(
        lambda: contracts._build_depth_path_reverse_martingale_report_contract(
            **hostile
        ),
        "exact DepthPath",
    )
    invented_path_kwargs = dict(hostile)
    invented_path_kwargs["path_content_id"] = "sha256:invented-path"
    invented_path = expect_rejection(
        lambda: contracts._build_depth_path_reverse_martingale_report_contract(
            path=authentic.path, **invented_path_kwargs
        ),
        "path content identity",
    )
    invented_strata_kwargs = dict(hostile)
    invented_strata_kwargs["stratum_content_ids"] = (
        "sha256:invented-stratum-1",
        "sha256:invented-stratum-2",
        "sha256:invented-stratum-3",
    )
    invented_strata = expect_rejection(
        lambda: contracts._build_depth_path_reverse_martingale_report_contract(
            path=authentic.path, **invented_strata_kwargs
        ),
        "stratum identities",
    )

    drifted = proved_report()
    object.__setattr__(
        drifted.path.strata[1],
        "support_unit_ids",
        ("pixel-0", "pixel-1", "pixel-3"),
    )
    support_drift = expect_rejection(
        lambda: build_depth_path_doob_calibration(
            calibration_id="PR284-ORACLE-SUPPORT-DRIFT",
            report=drifted,
            threshold_contract=threshold(),
        ),
        "identity drifted",
    )

    nonnested_rejected = expect_rejection(
        lambda: path(supports=((0, 1), (1, 2), (1,))),
        "non-nested sky supports",
    )

    fallback_path = path()
    fallback_threshold = threshold()
    plan = build_depth_path_matched_mock_plan(
        plan_id="PR284-ORACLE-MOCK-PLAN-V1",
        path=fallback_path,
        threshold_contract=fallback_threshold,
        preprocessing_id="sha256:oracle-common-preprocessing-v1",
        estimator_id="sha256:oracle-conditional-estimator-v1",
        registration_id="sha256:oracle-mock-plan-preregistered-v1",
        null_law_id="sha256:oracle-null-law-v1",
        mock_generator_id="sha256:oracle-mock-generator-v1",
        ensemble_policy_id="sha256:oracle-ensemble-policy-v1",
        seed_policy_id="sha256:oracle-seed-policy-v1",
        matching_variable_ids=("mask", "selection", "noise", "depth"),
        acceptance_rule_id="sha256:oracle-acceptance-rule-v1",
        multiplicity_rule_id="sha256:oracle-multiplicity-rule-v1",
    )
    fallback_report = build_unproved_depth_path_reverse_martingale_report(
        report_id="PR284-ORACLE-UNPROVED-REPORT-V1",
        path=fallback_path,
        threshold_contract=fallback_threshold,
        filtration_id="sha256:oracle-unproved-filtration-v1",
        preprocessing_id="sha256:oracle-common-preprocessing-v1",
        estimator_id="sha256:oracle-conditional-estimator-v1",
        premise_evidence_id="sha256:oracle-support-nesting-only-v1",
        unresolved_reasons=("explicit tower premise is unproved",),
        matched_mock_plan=plan,
    )
    fallback = build_depth_path_doob_calibration(
        calibration_id="PR284-ORACLE-MOCK-FALLBACK-V1",
        report=fallback_report,
        threshold_contract=fallback_threshold,
    )
    assert fallback.status is DepthPathCalibrationStatus.MATCHED_MOCKS_REQUIRED
    assert fallback_report.premise_status is ReverseMartingalePremiseStatus.UNPROVED_REQUIRES_MATCHED_MOCKS
    assert fallback.probability_upper_bound is None
    assert fallback.threshold_squared is None
    assert fallback.path_maximum_squared is None
    assert fallback.path_exceeds_threshold is None
    assert fallback.report.matched_mock_plan.null_mock_status == "required_not_executed"

    # The PR-284 spec requires *strictly* nested supports.  The historical
    # DepthPath contract uses ordinary subset and therefore admits equality.
    equal_support_path = path(
        supports=((0, 1, 2, 3), (0, 1, 2, 3), (0, 1, 2, 3))
    )
    equal_support_report = proved_report(resolved_path=equal_support_path)
    equal_support_calibration = build_depth_path_doob_calibration(
        calibration_id="PR284-ORACLE-EQUAL-SUPPORT-CALIBRATION",
        report=equal_support_report,
        threshold_contract=threshold(),
    )
    strict_nesting_gap = (
        equal_support_calibration.probability_upper_bound == Fraction(25, 36)
    )
    assert strict_nesting_gap

    print(
        json.dumps(
            {
                "oracle": "PR284_R3_PHYSMATH_V1",
                "exact_mean": "0/1",
                "exact_second_moment": "5/1",
                "selected_atom_path": ["-3/1", "-2/1", "0/1"],
                "selected_atom_path_maximum": "3/1",
                "threshold_squared": "36/5",
                "inclusive_event_probability": "1/2",
                "doob_upper_bound": "25/36",
                "named_identity_bypass_closed": True,
                "hostile_rejections": {
                    "missing_path": missing_path,
                    "invented_path_content_id": invented_path,
                    "invented_stratum_content_ids": invented_strata,
                    "post_construction_support_drift": support_drift,
                    "nonnested_support": nonnested_rejected,
                },
                "matched_mock_abstention": True,
                "strict_nesting_spec_gap_bound_emitted": strict_nesting_gap,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
