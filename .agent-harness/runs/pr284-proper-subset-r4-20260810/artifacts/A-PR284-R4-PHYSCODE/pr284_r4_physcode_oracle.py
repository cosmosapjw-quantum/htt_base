#!/usr/bin/env python3
"""Independent PR-284 proper-subset, exact-math, and seam oracle."""
from __future__ import annotations

from fractions import Fraction
import json
from pathlib import Path
import sys
from unittest.mock import patch

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
    revalidate_depth_path_reverse_martingale_report,
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


def conditional_values(
    labels: tuple[str, ...], *, target=TARGET
) -> tuple[Fraction, ...]:
    mass: dict[str, Fraction] = {}
    weighted: dict[str, Fraction] = {}
    for probability, value, label in zip(WEIGHTS, target, labels, strict=True):
        mass[label] = mass.get(label, Fraction()) + probability
        weighted[label] = weighted.get(label, Fraction()) + probability * value
    return tuple(weighted[label] / mass[label] for label in labels)


def assert_exact_decreasing_tower() -> tuple[tuple[Fraction, ...], ...]:
    rows = tuple(conditional_values(partition) for partition in PARTITIONS)
    for fine_labels, coarse_labels, fine_values, coarse_values in zip(
        PARTITIONS[:-1],
        PARTITIONS[1:],
        rows[:-1],
        rows[1:],
        strict=True,
    ):
        fine_to_coarse: dict[str, str] = {}
        for fine_label, coarse_label in zip(
            fine_labels, coarse_labels, strict=True
        ):
            assert fine_to_coarse.setdefault(fine_label, coarse_label) == coarse_label
        mass: dict[str, Fraction] = {}
        weighted: dict[str, Fraction] = {}
        for probability, fine_value, coarse_label in zip(
            WEIGHTS, fine_values, coarse_labels, strict=True
        ):
            mass[coarse_label] = mass.get(coarse_label, Fraction()) + probability
            weighted[coarse_label] = (
                weighted.get(coarse_label, Fraction()) + probability * fine_value
            )
        iterated = tuple(
            weighted[label] / mass[label] for label in coarse_labels
        )
        assert iterated == coarse_values
    return rows


def exact_event_probability(threshold_squared: Fraction) -> Fraction:
    rows = tuple(conditional_values(partition) for partition in PARTITIONS)
    return sum(
        (
            probability
            for index, probability in enumerate(WEIGHTS)
            if max(abs(row[index]) for row in rows) ** 2 >= threshold_squared
        ),
        Fraction(),
    )


def stratum(suffix: str, *, depth: float, kept: tuple[int, ...]):
    mask = np.zeros(4, dtype=bool)
    mask[list(kept)] = True
    support = build_sky_support_from_mask(
        mask,
        coordinate_frame="GALACTIC",
        completeness_status="synthetic_fixture_complete",
        selection_mode=f"pr284-r4-oracle-selection-{suffix}",
        mock_coverage_status="synthetic_fixture_only",
        pixelization="PR284_UNIT_PIXELS",
    )
    return build_mask_stratum(
        stratum_id=f"PR284-R4-ORACLE-{suffix}",
        depth_coordinate=depth,
        depth_unit="synthetic_depth",
        support_unit_ids=tuple(f"pixel-{index}" for index in kept),
        support_universe_size=4,
        sky_support=support,
        selection_id=f"sha256:r4-oracle-selection-{suffix}",
        covariance_id=f"sha256:r4-oracle-covariance-{suffix}",
        source_artifact_id=f"sha256:r4-oracle-source-{suffix}",
        feature_names=("centered_scalar",),
        feature_unit="dimensionless_diagnostic",
        assumptions=("assignment-local exact oracle",),
    )


def path(supports: tuple[tuple[int, ...], ...], *, path_id: str):
    strata = tuple(
        stratum(f"D{index}", depth=index / 10, kept=kept)
        for index, kept in enumerate(supports, start=1)
    )
    kernels = tuple(
        build_transport_kernel(
            transport_id=f"PR284-R4-ORACLE-K{index}{index + 1}",
            source=source,
            target=target,
            matrix=((1.0,),),
            mask_transport_id=f"sha256:r4-oracle-mask-k{index}{index + 1}",
            selection_transport_id=(
                f"sha256:r4-oracle-selection-k{index}{index + 1}"
            ),
            covariance_transport_id=(
                f"sha256:r4-oracle-covariance-k{index}{index + 1}"
            ),
            method_id="PR284-R4-ORACLE-IDENTITY-TRANSPORT-V1",
            assumptions=("assignment-local identity transport",),
        )
        for index, (source, target) in enumerate(
            zip(strata[:-1], strata[1:], strict=True), start=1
        )
    )
    return build_depth_path(path_id=path_id, strata=strata, kernels=kernels)


def proper_path():
    return path(
        ((0, 1, 2, 3), (0, 1, 2), (0, 1)),
        path_id="PR284-R4-ORACLE-PROPER-PATH",
    )


def equal_adjacent_path():
    return path(
        ((0, 1, 2, 3), (0, 1, 2, 3), (0, 1)),
        path_id="PR284-R4-ORACLE-EQUAL-PATH",
    )


def law(*, target=TARGET):
    return build_depth_path_finite_target_law(
        law_id="PR284-R4-ORACLE-LAW",
        common_target_id="PR284-R4-ORACLE-TARGET",
        atom_ids=("atom-a", "atom-b", "atom-c", "atom-d"),
        weights=WEIGHTS,
        common_target=target,
        registration_id="sha256:r4-oracle-law-preregistered",
    )


def selection(finite_law, index=0):
    return build_depth_path_selection_contract(
        selection_id="PR284-R4-ORACLE-SELECTION",
        finite_target_law=finite_law,
        selected_atom_id=finite_law.atom_ids[index],
        selected_atom_index=index,
        selection_rule_id="sha256:r4-oracle-fixed-selection",
        registration_id="sha256:r4-oracle-selection-preregistered",
    )


def threshold(multiplier=Fraction(6, 5)):
    return build_depth_path_threshold_contract(
        contract_id="PR284-R4-ORACLE-THRESHOLD",
        multiplier=multiplier,
        registration_id="sha256:r4-oracle-threshold-preregistered",
    )


def build_proved(resolved_path, *, finite_law=None, threshold_contract=None):
    q = law() if finite_law is None else finite_law
    t = threshold() if threshold_contract is None else threshold_contract
    return build_depth_path_reverse_martingale_report(
        report_id="PR284-R4-ORACLE-PROVED",
        path=resolved_path,
        threshold_contract=t,
        finite_target_law=q,
        selection_contract=selection(q),
        path_partitions=PARTITIONS,
        sigma_field_ids=("sha256:r4-F1", "sha256:r4-F2", "sha256:r4-F3"),
        filtration_id="sha256:r4-oracle-decreasing-filtration",
        preprocessing_id="sha256:r4-oracle-preprocessing",
        estimator_id="sha256:r4-oracle-estimator",
        premise_evidence_id="sha256:r4-oracle-exact-replay",
    )


def builder_kwargs(authentic, resolved_path) -> dict[str, object]:
    return {
        "report_id": "PR284-R4-ORACLE-SEAM",
        "path_content_id": resolved_path.content_id,
        "stratum_content_ids": tuple(
            value.content_id for value in resolved_path.strata
        ),
        "threshold_contract": authentic.threshold_contract,
        "filtration_id": authentic.filtration_id,
        "filtration_direction": authentic.filtration_direction,
        "preprocessing_id": authentic.preprocessing_id,
        "estimator_id": authentic.estimator_id,
        "premise_evidence_id": "sha256:r4-oracle-private-seam",
        "premise_status": ReverseMartingalePremiseStatus.PROVED_FINITE_REGISTERED_PATH,
        "finite_target_law": authentic.finite_target_law,
        "selection_contract": authentic.selection_contract,
        "path_partitions": authentic.path_partitions,
        "sigma_field_ids": authentic.sigma_field_ids,
        "path_values": authentic.path_values,
        "path_maximum_abs": authentic.path_maximum_abs,
        "path_maximum_content_id": authentic.path_maximum_content_id,
        "target_second_moment": authentic.target_second_moment,
        "exact_tower_equalities": authentic.exact_tower_equalities,
        "exact_tower_report_content_id": authentic.exact_tower_report_content_id,
        "unresolved_reasons": (),
        "matched_mock_plan": None,
    }


def expect_rejection(action, fragment: str) -> str:
    try:
        action()
    except DepthPathError as exc:
        assert fragment in str(exc), (fragment, str(exc))
        return str(exc)
    raise AssertionError(f"expected rejection containing {fragment!r}")


def main() -> None:
    assert sum(p * x for p, x in zip(WEIGHTS, TARGET, strict=True)) == 0
    second = sum(p * x * x for p, x in zip(WEIGHTS, TARGET, strict=True))
    assert second == 5
    rows = assert_exact_decreasing_tower()
    assert tuple(row[0] for row in rows) == (-3, -2, 0)

    proper = proper_path()
    authentic = build_proved(proper)
    calibration = build_depth_path_doob_calibration(
        calibration_id="PR284-R4-ORACLE-CALIBRATION",
        report=authentic,
        threshold_contract=threshold(),
    )
    assert authentic.target_second_moment == 5
    assert authentic.path_values == (-3, -2, 0)
    assert authentic.path_maximum_abs == 3
    assert calibration.threshold_squared == Fraction(36, 5)
    assert calibration.path_maximum_squared == 9
    assert calibration.path_exceeds_threshold is True
    assert exact_event_probability(calibration.threshold_squared) == Fraction(1, 2)
    assert calibration.probability_upper_bound == Fraction(25, 36)

    equal_path = equal_adjacent_path()
    assert equal_path.strata[0].support_unit_ids == equal_path.strata[1].support_unit_ids
    public_rejection = expect_rejection(
        lambda: build_proved(equal_path), "strictly nested sky supports"
    )

    equal_kwargs = builder_kwargs(authentic, equal_path)
    private_rejection = expect_rejection(
        lambda: contracts._build_depth_path_reverse_martingale_report_contract(
            path=equal_path, **equal_kwargs
        ),
        "strictly nested sky supports",
    )

    # Simulate a sealed legacy report created before the proper-subset guard.
    # Once the current method is restored, ordinary revalidation must kill it.
    with patch.object(
        contracts.DepthPathReverseMartingaleReport,
        "_assert_proved_premise_replay",
        lambda self: None,
    ):
        legacy_equal = contracts._build_depth_path_reverse_martingale_report_contract(
            path=equal_path, **equal_kwargs
        )
    revalidation_rejection = expect_rejection(
        lambda: revalidate_depth_path_reverse_martingale_report(legacy_equal),
        "strictly nested sky supports",
    )
    calibration_rejection = expect_rejection(
        lambda: build_depth_path_doob_calibration(
            calibration_id="PR284-R4-ORACLE-LEGACY-CALIBRATION",
            report=legacy_equal,
            threshold_contract=threshold(),
        ),
        "strictly nested sky supports",
    )

    missing_path_kwargs = builder_kwargs(authentic, proper)
    missing_path = expect_rejection(
        lambda: contracts._build_depth_path_reverse_martingale_report_contract(
            **missing_path_kwargs
        ),
        "exact DepthPath",
    )
    invented_path_kwargs = dict(missing_path_kwargs)
    invented_path_kwargs["path_content_id"] = "sha256:invented-path"
    invented_path = expect_rejection(
        lambda: contracts._build_depth_path_reverse_martingale_report_contract(
            path=proper, **invented_path_kwargs
        ),
        "path content identity",
    )
    invented_strata_kwargs = dict(missing_path_kwargs)
    invented_strata_kwargs["stratum_content_ids"] = (
        "sha256:invented-stratum-1",
        "sha256:invented-stratum-2",
        "sha256:invented-stratum-3",
    )
    invented_strata = expect_rejection(
        lambda: contracts._build_depth_path_reverse_martingale_report_contract(
            path=proper, **invented_strata_kwargs
        ),
        "stratum identities",
    )

    t = threshold()
    plan = build_depth_path_matched_mock_plan(
        plan_id="PR284-R4-ORACLE-MOCK-PLAN",
        path=equal_path,
        threshold_contract=t,
        preprocessing_id="sha256:r4-oracle-preprocessing",
        estimator_id="sha256:r4-oracle-estimator",
        registration_id="sha256:r4-oracle-mock-plan-preregistered",
        null_law_id="sha256:r4-oracle-null-law",
        mock_generator_id="sha256:r4-oracle-mock-generator",
        ensemble_policy_id="sha256:r4-oracle-ensemble-policy",
        seed_policy_id="sha256:r4-oracle-seed-policy",
        matching_variable_ids=("mask", "selection", "noise", "depth"),
        acceptance_rule_id="sha256:r4-oracle-acceptance-rule",
        multiplicity_rule_id="sha256:r4-oracle-multiplicity-rule",
    )
    fallback_report = build_unproved_depth_path_reverse_martingale_report(
        report_id="PR284-R4-ORACLE-UNPROVED",
        path=equal_path,
        threshold_contract=t,
        filtration_id="sha256:r4-oracle-unproved-filtration",
        preprocessing_id="sha256:r4-oracle-preprocessing",
        estimator_id="sha256:r4-oracle-estimator",
        premise_evidence_id="sha256:r4-oracle-unproved-evidence",
        unresolved_reasons=("proper support reduction is unproved",),
        matched_mock_plan=plan,
    )
    fallback = build_depth_path_doob_calibration(
        calibration_id="PR284-R4-ORACLE-FALLBACK",
        report=fallback_report,
        threshold_contract=t,
    )
    assert fallback.status is DepthPathCalibrationStatus.MATCHED_MOCKS_REQUIRED
    assert fallback_report.premise_status is ReverseMartingalePremiseStatus.UNPROVED_REQUIRES_MATCHED_MOCKS
    assert fallback.probability_upper_bound is None
    assert fallback.target_second_moment is None
    assert fallback.threshold_squared is None
    assert fallback.path_maximum_squared is None
    assert fallback.path_exceeds_threshold is None
    assert fallback.report.matched_mock_plan.null_mock_status == "required_not_executed"

    equality_target = (
        Fraction(-1), Fraction(-1), Fraction(1), Fraction(1)
    )
    equality_law = law(target=equality_target)
    equality_threshold = threshold(Fraction(1))
    equality_report = build_proved(
        proper,
        finite_law=equality_law,
        threshold_contract=equality_threshold,
    )
    equality = build_depth_path_doob_calibration(
        calibration_id="PR284-R4-ORACLE-EQUALITY",
        report=equality_report,
        threshold_contract=equality_threshold,
    )
    assert equality.threshold_squared == 1
    assert equality.path_maximum_squared == 1
    assert equality.path_exceeds_threshold is True

    print(
        json.dumps(
            {
                "oracle": "PR284_R4_PHYSCODE_V1",
                "generic_equal_support_depth_path_constructed": True,
                "proper_subset_public_construction_rejected": public_rejection,
                "proper_subset_private_construction_rejected": private_rejection,
                "proper_subset_later_revalidation_rejected": revalidation_rejection,
                "proper_subset_calibration_revalidation_rejected": calibration_rejection,
                "identity_seam_rejections": {
                    "missing_path": missing_path,
                    "invented_path_content_id": invented_path,
                    "invented_stratum_content_ids": invented_strata,
                },
                "matched_mock_equal_support_abstention": True,
                "exact_mean": "0/1",
                "exact_second_moment": "5/1",
                "selected_path": ["-3/1", "-2/1", "0/1"],
                "selected_path_maximum": "3/1",
                "threshold_squared": "36/5",
                "inclusive_event_probability": "1/2",
                "doob_upper_bound": "25/36",
                "inclusive_equality_case": True,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
