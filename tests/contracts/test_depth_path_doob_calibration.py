"""PR-284 premise-bound reverse-martingale and Doob calibration contracts."""

from __future__ import annotations

from fractions import Fraction
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest
import yaml

from common.depth_path import (
    DepthPathError,
    build_depth_path,
    build_mask_stratum,
    build_transport_kernel,
)
from common.depth_path_calibration import (
    DepthPathCalibrationStatus,
    ReverseMartingalePremiseStatus,
    build_depth_path_finite_target_law,
    build_depth_path_selection_contract,
    build_depth_path_threshold_contract,
    revalidate_depth_path_doob_calibration,
    revalidate_depth_path_finite_target_law,
    revalidate_depth_path_reverse_martingale_report,
    revalidate_depth_path_selection_contract,
    revalidate_depth_path_threshold_contract,
)
from common.sky_support import build_sky_support_from_mask
from htt.infer.depth_path_calibration import (
    build_depth_path_doob_calibration,
    build_depth_path_matched_mock_plan,
    build_depth_path_reverse_martingale_report,
    build_unproved_depth_path_reverse_martingale_report,
)


ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = ROOT / "docs/research_program/post_pr275/pr284_spec.yaml"
BACKLOG_PATH = ROOT / "docs/codex_handoff/pr_backlog.yaml"


def _stratum(suffix: str, *, depth: float, kept: tuple[int, ...]):
    mask = np.zeros(4, dtype=bool)
    mask[list(kept)] = True
    support = build_sky_support_from_mask(
        mask,
        coordinate_frame="GALACTIC",
        completeness_status="synthetic_fixture_complete",
        selection_mode=f"pr284-selection-{suffix}",
        mock_coverage_status="synthetic_fixture_only",
        pixelization="PR284_UNIT_PIXELS",
    )
    return build_mask_stratum(
        stratum_id=f"PR284-{suffix}",
        depth_coordinate=depth,
        depth_unit="synthetic_depth",
        support_unit_ids=tuple(f"pixel-{index}" for index in kept),
        support_universe_size=4,
        sky_support=support,
        selection_id=f"sha256:selection-{suffix}",
        covariance_id=f"sha256:covariance-{suffix}",
        source_artifact_id=f"sha256:source-{suffix}",
        feature_names=("centered_scalar",),
        feature_unit="dimensionless_diagnostic",
        assumptions=("synthetic nested-mask fixture",),
    )


def _path():
    strata = (
        _stratum("D1", depth=0.1, kept=(0, 1, 2, 3)),
        _stratum("D2", depth=0.2, kept=(0, 1, 2)),
        _stratum("D3", depth=0.3, kept=(0, 1)),
    )
    kernels = tuple(
        build_transport_kernel(
            transport_id=f"PR284-K{index}{index + 1}",
            source=source,
            target=target,
            matrix=((1.0,),),
            mask_transport_id=f"sha256:mask-k{index}{index + 1}",
            selection_transport_id=f"sha256:selection-k{index}{index + 1}",
            covariance_transport_id=f"sha256:covariance-k{index}{index + 1}",
            method_id="PR284-IDENTITY-TRANSPORT-V1",
            assumptions=("synthetic scalar identity transport",),
        )
        for index, (source, target) in enumerate(
            zip(strata[:-1], strata[1:], strict=True),
            start=1,
        )
    )
    return build_depth_path(
        path_id="PR284-NESTED-PATH-V1",
        strata=strata,
        kernels=kernels,
    )


def _equal_support_path():
    strata = (
        _stratum("E1", depth=0.1, kept=(0, 1, 2, 3)),
        _stratum("E2", depth=0.2, kept=(0, 1, 2, 3)),
        _stratum("E3", depth=0.3, kept=(0, 1)),
    )
    kernels = tuple(
        build_transport_kernel(
            transport_id=f"PR284-EK{index}{index + 1}",
            source=source,
            target=target,
            matrix=((1.0,),),
            mask_transport_id=f"sha256:equal-mask-k{index}{index + 1}",
            selection_transport_id=(
                f"sha256:equal-selection-k{index}{index + 1}"
            ),
            covariance_transport_id=(
                f"sha256:equal-covariance-k{index}{index + 1}"
            ),
            method_id="PR284-EQUAL-SUPPORT-TRANSPORT-V1",
            assumptions=("synthetic scalar identity transport",),
        )
        for index, (source, target) in enumerate(
            zip(strata[:-1], strata[1:], strict=True),
            start=1,
        )
    )
    return build_depth_path(
        path_id="PR284-EQUAL-SUPPORT-PATH-V1",
        strata=strata,
        kernels=kernels,
    )


def _threshold(multiplier: Fraction = Fraction(2, 1)):
    return build_depth_path_threshold_contract(
        contract_id="PR284-DOOB-THRESHOLD-V1",
        multiplier=multiplier,
        registration_id="sha256:preregistered-before-path-inspection",
    )


def _finite_law(*, target: tuple[int, ...] = (-3, -1, 1, 3)):
    return build_depth_path_finite_target_law(
        law_id="PR284-FINITE-LAW-V1",
        common_target_id="PR284-CENTERED-TARGET-V1",
        atom_ids=("atom-a", "atom-b", "atom-c", "atom-d"),
        weights=(Fraction(1, 4),) * 4,
        common_target=target,
        registration_id="sha256:finite-law-preregistered-v1",
    )


def _selection(law, *, selected_atom_index: int = 0):
    return build_depth_path_selection_contract(
        selection_id="PR284-SELECTED-ATOM-V1",
        finite_target_law=law,
        selected_atom_id=law.atom_ids[selected_atom_index],
        selected_atom_index=selected_atom_index,
        selection_rule_id="sha256:fixed-first-atom-rule-v1",
        registration_id="sha256:selection-preregistered-v1",
    )


def _mock_plan(*, path=None, threshold=None):
    resolved_path = _path() if path is None else path
    resolved_threshold = _threshold() if threshold is None else threshold
    return build_depth_path_matched_mock_plan(
        plan_id="PR284-MATCHED-MOCK-PLAN-V1",
        path=resolved_path,
        threshold_contract=resolved_threshold,
        preprocessing_id="sha256:common-preprocessing-v1",
        estimator_id="sha256:conditional-estimator-v1",
        registration_id="sha256:mock-plan-preregistered-v1",
        null_law_id="sha256:matched-null-law-v1",
        mock_generator_id="sha256:matched-mock-generator-v1",
        ensemble_policy_id="sha256:ensemble-policy-v1",
        seed_policy_id="sha256:seed-policy-v1",
        matching_variable_ids=("mask", "selection", "noise", "depth"),
        acceptance_rule_id="sha256:mock-acceptance-rule-v1",
        multiplicity_rule_id="sha256:path-maximum-multiplicity-v1",
    )


def _proved_report(*, selected_atom_index: int = 0):
    law = _finite_law()
    return build_depth_path_reverse_martingale_report(
        report_id="PR284-PROVED-REPORT-V1",
        path=_path(),
        threshold_contract=_threshold(),
        finite_target_law=law,
        selection_contract=_selection(
            law,
            selected_atom_index=selected_atom_index,
        ),
        path_partitions=(
            ("a", "b", "c", "d"),
            ("left", "left", "right", "right"),
            ("all", "all", "all", "all"),
        ),
        sigma_field_ids=("sha256:F1", "sha256:F2", "sha256:F3"),
        filtration_id="sha256:decreasing-filtration-v1",
        preprocessing_id="sha256:common-preprocessing-v1",
        estimator_id="sha256:conditional-estimator-v1",
        premise_evidence_id="sha256:pr271-finite-tower-v1",
    )


def test_spec_and_backlog_bind_g6_terminal_receipt_and_claim_ceiling() -> None:
    spec = yaml.safe_load(SPEC_PATH.read_text())
    backlog = yaml.safe_load(BACKLOG_PATH.read_text())
    card = next(row for row in backlog["prs"] if row["id"] == "PR-284")
    assert spec["gate"]["gate_id"] == "G6"
    assert spec["dependency_contract"] == {
        "upstream_id": "PR-280",
        "mode": "requires_terminal_receipt",
    }
    assert card["depends"] == ["PR-280"]
    assert card["dependency_contracts"][0]["mode"] == "requires_terminal_receipt"
    assert spec["claim_tier"] == "diagnostic_only"
    assert spec["observed_data_executed"] is False
    assert spec["public_use"] is False
    assert spec["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS"


def test_exact_finite_centered_tower_produces_premise_bound_doob_report() -> None:
    report = _proved_report()
    replay = revalidate_depth_path_reverse_martingale_report(report)
    assert replay.content_id == report.content_id
    assert report.premise_status is ReverseMartingalePremiseStatus.PROVED_FINITE_REGISTERED_PATH
    assert report.filtration_direction == "DECREASING"
    assert report.path.content_id == _path().content_id
    assert report.path_values == (Fraction(-3), Fraction(-2), Fraction(0))
    assert report.path_maximum_abs == Fraction(3)
    assert report.target_second_moment == Fraction(5)
    assert report.exact_tower_equalities == (True, True)
    assert report.matched_mock_plan_id is None

    calibration = build_depth_path_doob_calibration(
        calibration_id="PR284-DOOB-CALIBRATION-V1",
        report=report,
        threshold_contract=_threshold(),
    )
    replayed = revalidate_depth_path_doob_calibration(calibration)
    assert replayed.content_id == calibration.content_id
    assert calibration.status is DepthPathCalibrationStatus.BOUND_AVAILABLE_CONDITIONAL_PROVED_PREMISE
    assert calibration.probability_upper_bound == Fraction(1, 4)
    assert calibration.threshold_squared == Fraction(20)
    assert calibration.path_maximum_squared == Fraction(9)
    assert calibration.path_exceeds_threshold is False
    assert calibration.matched_mock_plan_id is None


def test_common_report_builder_cannot_mint_proved_status_without_replay() -> None:
    from common import depth_path_calibration as contracts

    path = _path()
    threshold = _threshold()
    law = _finite_law(target=(0, 1, 2, 3))
    selection = _selection(law)

    with pytest.raises(DepthPathError, match="centered|decreasing filtration"):
        contracts._build_depth_path_reverse_martingale_report_contract(
            path=path,
            report_id="PR284-FORGED-PROVED-REPORT",
            path_content_id=path.content_id,
            stratum_content_ids=tuple(
                stratum.content_id for stratum in path.strata
            ),
            threshold_contract=threshold,
            filtration_id="sha256:forged-filtration",
            filtration_direction="DECREASING",
            preprocessing_id="sha256:common-preprocessing-v1",
            estimator_id="sha256:conditional-estimator-v1",
            premise_evidence_id="sha256:caller-supplied-proof",
            premise_status=(
                ReverseMartingalePremiseStatus.PROVED_FINITE_REGISTERED_PATH
            ),
            finite_target_law=law,
            selection_contract=selection,
            path_partitions=(
                ("left", "left", "right", "right"),
                ("x", "y", "x", "y"),
                ("all", "all", "all", "all"),
            ),
            sigma_field_ids=("sigma-1", "sigma-2", "sigma-3"),
            path_values=(Fraction(0), Fraction(0), Fraction(0)),
            path_maximum_abs=Fraction(0),
            path_maximum_content_id="sha256:caller-supplied-maximum",
            target_second_moment=Fraction(1),
            exact_tower_equalities=(True, True),
            exact_tower_report_content_id="sha256:caller-supplied-tower",
            unresolved_reasons=(),
            matched_mock_plan=None,
        )


def test_common_report_builder_requires_exact_replayed_depth_path_identity() -> None:
    from common import depth_path_calibration as contracts

    path = _path()
    authentic = _proved_report()
    kwargs = {
        "report_id": "PR284-INVENTED-PATH-IDENTITY",
        "path_content_id": "sha256:no-registered-depth-path",
        "stratum_content_ids": (
            "sha256:no-registered-stratum-1",
            "sha256:no-registered-stratum-2",
            "sha256:no-registered-stratum-3",
        ),
        "threshold_contract": authentic.threshold_contract,
        "filtration_id": authentic.filtration_id,
        "filtration_direction": authentic.filtration_direction,
        "preprocessing_id": authentic.preprocessing_id,
        "estimator_id": authentic.estimator_id,
        "premise_evidence_id": "sha256:invented-premise-evidence",
        "premise_status": authentic.premise_status,
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

    with pytest.raises(DepthPathError, match="exact DepthPath"):
        contracts._build_depth_path_reverse_martingale_report_contract(**kwargs)

    with pytest.raises(DepthPathError, match="path content identity"):
        contracts._build_depth_path_reverse_martingale_report_contract(
            path=path,
            **kwargs,
        )


def test_selected_atom_path_is_recomputed_from_exact_conditionals() -> None:
    report = _proved_report(selected_atom_index=3)
    assert report.path_values == (Fraction(3), Fraction(2), Fraction(0))
    assert report.path_maximum_abs == Fraction(3)


def test_support_nesting_alone_routes_to_matched_mocks_without_bound() -> None:
    path = _path()
    threshold = _threshold()
    report = build_unproved_depth_path_reverse_martingale_report(
        report_id="PR284-UNPROVED-REPORT-V1",
        path=path,
        threshold_contract=threshold,
        filtration_id="sha256:unproved-filtration-v1",
        preprocessing_id="sha256:common-preprocessing-v1",
        estimator_id="sha256:conditional-estimator-v1",
        premise_evidence_id="sha256:support-nesting-only-v1",
        unresolved_reasons=(
            "explicit conditional-expectation partitions are not proved",
        ),
        matched_mock_plan=_mock_plan(path=path, threshold=threshold),
    )
    assert report.premise_status is ReverseMartingalePremiseStatus.UNPROVED_REQUIRES_MATCHED_MOCKS
    assert report.weights == ()
    assert report.path_partitions == ()
    assert report.path_values == ()
    assert report.path_maximum_abs is None
    assert report.target_second_moment is None

    calibration = build_depth_path_doob_calibration(
        calibration_id="PR284-MOCK-FALLBACK-V1",
        report=report,
        threshold_contract=_threshold(),
    )
    assert calibration.status is DepthPathCalibrationStatus.MATCHED_MOCKS_REQUIRED
    assert calibration.probability_upper_bound is None
    assert calibration.threshold_squared is None
    assert calibration.path_maximum_squared is None
    assert calibration.path_exceeds_threshold is None
    assert calibration.matched_mock_plan_id == "PR284-MATCHED-MOCK-PLAN-V1"
    assert calibration.matched_mock_plan_content_id == report.matched_mock_plan.content_id


def test_proved_report_requires_proper_support_reduction_but_unproved_abstains() -> None:
    path = _equal_support_path()
    threshold = _threshold()
    law = _finite_law()

    with pytest.raises(DepthPathError, match="strictly nested sky supports"):
        build_depth_path_reverse_martingale_report(
            report_id="PR284-EQUAL-SUPPORT-PROVED",
            path=path,
            threshold_contract=threshold,
            finite_target_law=law,
            selection_contract=_selection(law),
            path_partitions=(
                ("a", "b", "c", "d"),
                ("left", "left", "right", "right"),
                ("all", "all", "all", "all"),
            ),
            sigma_field_ids=("sha256:F1", "sha256:F2", "sha256:F3"),
            filtration_id="sha256:decreasing-filtration-v1",
            preprocessing_id="sha256:common-preprocessing-v1",
            estimator_id="sha256:conditional-estimator-v1",
            premise_evidence_id="sha256:pr271-finite-tower-v1",
        )

    report = build_unproved_depth_path_reverse_martingale_report(
        report_id="PR284-EQUAL-SUPPORT-UNPROVED",
        path=path,
        threshold_contract=threshold,
        filtration_id="sha256:unproved-filtration-v1",
        preprocessing_id="sha256:common-preprocessing-v1",
        estimator_id="sha256:conditional-estimator-v1",
        premise_evidence_id="sha256:support-nesting-only-v1",
        unresolved_reasons=("strict support reduction is not proved",),
        matched_mock_plan=_mock_plan(path=path, threshold=threshold),
    )
    calibration = build_depth_path_doob_calibration(
        calibration_id="PR284-EQUAL-SUPPORT-FALLBACK",
        report=report,
        threshold_contract=threshold,
    )
    assert calibration.status is DepthPathCalibrationStatus.MATCHED_MOCKS_REQUIRED
    assert calibration.probability_upper_bound is None


def test_proved_factory_rejects_noncentered_or_degenerate_target() -> None:
    kwargs = dict(
        report_id="PR284-BAD-TARGET",
        path=_path(),
        threshold_contract=_threshold(),
        path_partitions=(
            ("a", "b", "c", "d"),
            ("left", "left", "right", "right"),
            ("all", "all", "all", "all"),
        ),
        sigma_field_ids=("sha256:F1", "sha256:F2", "sha256:F3"),
        filtration_id="sha256:decreasing-filtration-v1",
        preprocessing_id="sha256:common-preprocessing-v1",
        estimator_id="sha256:conditional-estimator-v1",
        premise_evidence_id="sha256:pr271-finite-tower-v1",
    )
    noncentered = _finite_law(target=(0, 1, 2, 3))
    with pytest.raises(DepthPathError, match="centered"):
        build_depth_path_reverse_martingale_report(
            finite_target_law=noncentered,
            selection_contract=_selection(noncentered),
            **kwargs,
        )
    degenerate = _finite_law(target=(0, 0, 0, 0))
    with pytest.raises(DepthPathError, match="positive second moment"):
        build_depth_path_reverse_martingale_report(
            finite_target_law=degenerate,
            selection_contract=_selection(degenerate),
            **kwargs,
        )


def test_decreasing_filtration_is_distinct_from_nested_support() -> None:
    law = _finite_law()
    with pytest.raises(DepthPathError, match="decreasing filtration"):
        build_depth_path_reverse_martingale_report(
            report_id="PR284-BAD-FILTRATION",
            path=_path(),
            threshold_contract=_threshold(),
            finite_target_law=law,
            selection_contract=_selection(law),
            path_partitions=(
                ("left", "left", "right", "right"),
                ("x", "y", "x", "y"),
                ("all", "all", "all", "all"),
            ),
            sigma_field_ids=("sha256:F1", "sha256:F2", "sha256:F3"),
            filtration_id="sha256:invalid-filtration-v1",
            preprocessing_id="sha256:common-preprocessing-v1",
            estimator_id="sha256:conditional-estimator-v1",
            premise_evidence_id="sha256:pr271-finite-tower-v1",
        )


def test_threshold_requires_exact_positive_rational_and_sealed_registration() -> None:
    with pytest.raises(DepthPathError, match="exact rational"):
        build_depth_path_threshold_contract(
            contract_id="PR284-FLOAT-THRESHOLD",
            multiplier=2.0,
            registration_id="sha256:registration",
        )
    with pytest.raises(DepthPathError, match="positive"):
        build_depth_path_threshold_contract(
            contract_id="PR284-ZERO-THRESHOLD",
            multiplier=Fraction(0, 1),
            registration_id="sha256:registration",
        )
    threshold = _threshold()
    object.__setattr__(threshold, "multiplier", Fraction(3, 1))
    with pytest.raises(DepthPathError, match="identity drifted"):
        revalidate_depth_path_threshold_contract(threshold)


def test_report_and_calibration_reject_identity_or_path_maximum_drift() -> None:
    report = _proved_report()
    object.__setattr__(report, "path_maximum_abs", Fraction(99, 1))
    with pytest.raises(DepthPathError, match="identity drifted"):
        revalidate_depth_path_reverse_martingale_report(report)
    with pytest.raises(DepthPathError, match="identity drifted"):
        build_depth_path_doob_calibration(
            calibration_id="PR284-DRIFTED-REPORT",
            report=report,
            threshold_contract=_threshold(),
        )


def test_calibration_rejects_threshold_and_premise_status_forgery() -> None:
    report = _proved_report()
    with pytest.raises(DepthPathError, match="threshold contract"):
        build_depth_path_doob_calibration(
            calibration_id="PR284-THRESHOLD-DRIFT",
            report=report,
            threshold_contract=_threshold(Fraction(3, 1)),
        )

    path = _path()
    threshold = _threshold()
    fallback = build_unproved_depth_path_reverse_martingale_report(
        report_id="PR284-FORGED-FALLBACK",
        path=path,
        threshold_contract=threshold,
        filtration_id="sha256:unproved-filtration-v1",
        preprocessing_id="sha256:common-preprocessing-v1",
        estimator_id="sha256:conditional-estimator-v1",
        premise_evidence_id="sha256:support-nesting-only-v1",
        unresolved_reasons=("tower premise unproved",),
        matched_mock_plan=_mock_plan(path=path, threshold=threshold),
    )
    object.__setattr__(
        fallback,
        "premise_status",
        ReverseMartingalePremiseStatus.PROVED_FINITE_REGISTERED_PATH,
    )
    with pytest.raises(DepthPathError, match="identity drifted"):
        build_depth_path_doob_calibration(
            calibration_id="PR284-FREE-BOUND-FORGERY",
            report=fallback,
            threshold_contract=_threshold(),
        )


def test_unproved_report_requires_resolvable_mock_plan_and_reasons() -> None:
    path = _path()
    threshold = _threshold()
    kwargs = dict(
        report_id="PR284-INCOMPLETE-FALLBACK",
        path=path,
        threshold_contract=threshold,
        filtration_id="sha256:unproved-filtration-v1",
        preprocessing_id="sha256:common-preprocessing-v1",
        estimator_id="sha256:conditional-estimator-v1",
        premise_evidence_id="sha256:support-nesting-only-v1",
    )
    with pytest.raises(DepthPathError, match="unresolved_reasons"):
        build_unproved_depth_path_reverse_martingale_report(
            unresolved_reasons=(),
            matched_mock_plan=_mock_plan(path=path, threshold=threshold),
            **kwargs,
        )
    with pytest.raises(DepthPathError, match="matched_mock_plan"):
        build_unproved_depth_path_reverse_martingale_report(
            unresolved_reasons=("tower premise unproved",),
            matched_mock_plan=None,
            **kwargs,
        )


def test_exact_squared_threshold_includes_equality_without_float_sqrt() -> None:
    law = _finite_law(target=(-1, -1, 1, 1))
    report = build_depth_path_reverse_martingale_report(
        report_id="PR284-EQUALITY-REPORT",
        path=_path(),
        threshold_contract=_threshold(Fraction(1, 1)),
        finite_target_law=law,
        selection_contract=_selection(law),
        path_partitions=(
            ("a", "b", "c", "d"),
            ("left", "left", "right", "right"),
            ("all", "all", "all", "all"),
        ),
        sigma_field_ids=("sha256:F1", "sha256:F2", "sha256:F3"),
        filtration_id="sha256:equality-filtration-v1",
        preprocessing_id="sha256:common-preprocessing-v1",
        estimator_id="sha256:conditional-estimator-v1",
        premise_evidence_id="sha256:pr271-finite-tower-v1",
    )
    calibration = build_depth_path_doob_calibration(
        calibration_id="PR284-EQUALITY-CALIBRATION",
        report=report,
        threshold_contract=_threshold(Fraction(1, 1)),
    )
    assert calibration.threshold_squared == Fraction(1, 1)
    assert calibration.path_maximum_squared == Fraction(1, 1)
    assert calibration.path_exceeds_threshold is True
    assert calibration.event_comparison == "GREATER_THAN_OR_EQUAL_EXACT_SQUARES"


def test_finite_law_and_selection_identity_drift_fail_closed() -> None:
    law = _finite_law()
    object.__setattr__(
        law,
        "weights",
        (Fraction(1, 8), Fraction(3, 8), Fraction(1, 4), Fraction(1, 4)),
    )
    with pytest.raises(DepthPathError, match="identity drifted"):
        revalidate_depth_path_finite_target_law(law)

    clean_law = _finite_law()
    selection = _selection(clean_law)
    object.__setattr__(selection, "selected_atom_id", "atom-d")
    with pytest.raises(DepthPathError, match="identity drifted"):
        revalidate_depth_path_selection_contract(selection)


def test_estimator_identity_drift_blocks_calibration() -> None:
    with pytest.raises(DepthPathError, match="estimator identity"):
        build_depth_path_doob_calibration(
            calibration_id="PR284-ESTIMATOR-DRIFT",
            report=_proved_report(),
            threshold_contract=_threshold(),
            estimator_id="sha256:different-estimator",
        )


def test_matched_mock_plan_is_content_addressed_and_not_execution_evidence() -> None:
    path = _path()
    threshold = _threshold()
    plan = _mock_plan(path=path, threshold=threshold)
    payload = plan.as_payload()
    assert payload["null_mock_status"] == "required_not_executed"
    assert payload["path_content_id"] == path.content_id
    assert payload["threshold_contract_content_id"] == threshold.content_id
    assert payload["matching_variable_ids"] == ["mask", "selection", "noise", "depth"]
    object.__setattr__(plan, "mock_generator_id", "sha256:post-result-generator")
    with pytest.raises(DepthPathError, match="identity drifted"):
        build_unproved_depth_path_reverse_martingale_report(
            report_id="PR284-DRIFTED-MOCK-PLAN",
            path=path,
            threshold_contract=threshold,
            filtration_id="sha256:unproved-filtration-v1",
            preprocessing_id="sha256:common-preprocessing-v1",
            estimator_id="sha256:conditional-estimator-v1",
            premise_evidence_id="sha256:support-nesting-only-v1",
            unresolved_reasons=("tower premise unproved",),
            matched_mock_plan=plan,
        )


def test_payloads_preserve_diagnostic_only_nonobserved_boundary() -> None:
    report = _proved_report()
    calibration = build_depth_path_doob_calibration(
        calibration_id="PR284-BOUNDARY",
        report=report,
        threshold_contract=_threshold(),
    )
    for payload in (report.as_payload(), calibration.as_payload()):
        assert payload["owner"] == "HTT"
        assert payload["claim_tier"] == "diagnostic_only"
        assert payload["transfer_source"] == "none"
        assert payload["observed_data_executed"] is False
        assert payload["public_use"] is False
        assert payload["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS"
        assert "family identification" in " ".join(payload["forbidden_use"])


def test_receipt_replays_all_registered_mutations_and_content_address() -> None:
    from scripts.codex_harness import run_pr284_depth_path_doob as runner

    payload = json.loads(runner.OUTPUT.read_text())
    spec = yaml.safe_load(SPEC_PATH.read_text())
    assert [row["mutation_id"] for row in payload["mutations"]] == [
        row["mutation_id"] for row in spec["mutation_registry"]
    ]
    assert all(
        row["executed"] is True
        and row["activated"] is True
        and row["killed"] is True
        for row in payload["mutations"]
    )
    expected = dict(payload)
    digest = expected.pop("receipt_content_sha256")
    canonical = json.dumps(
        expected,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode()
    assert digest == hashlib.sha256(canonical).hexdigest()
    assert runner.main(["check"]) == 0


def test_receipt_binds_direct_modules_not_growing_package_export_surface() -> None:
    from htt import infer as public_api
    from htt.infer import depth_path_calibration as implementation
    from scripts.codex_harness import run_pr284_depth_path_doob as runner

    spec = yaml.safe_load(SPEC_PATH.read_text())
    assert tuple(spec["receipt_contract"]["required_bindings"]) == runner.BOUND_SOURCES
    assert "htt/htt/htt/infer/__init__.py" not in runner.BOUND_SOURCES
    assert (
        public_api.build_depth_path_doob_calibration
        is implementation.build_depth_path_doob_calibration
    )
    assert (
        public_api.build_depth_path_reverse_martingale_report
        is implementation.build_depth_path_reverse_martingale_report
    )


def test_runner_refuses_hardlinked_output_before_build(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from scripts.codex_harness import run_pr284_depth_path_doob as runner

    generated = tmp_path / "docs/generated"
    generated.mkdir(parents=True)
    outside = tmp_path / "outside.json"
    outside.write_text("preserve\n", encoding="utf-8")
    destination = generated / "receipt.json"
    destination.hardlink_to(outside)
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    monkeypatch.setattr(runner, "OUTPUT", destination)

    def must_not_build():
        raise AssertionError("builder ran before destination preflight")

    monkeypatch.setattr(runner, "_build_payload", must_not_build)
    assert runner.main(["build"]) == 1
    assert outside.read_text(encoding="utf-8") == "preserve\n"


def test_receipt_builder_fails_closed_on_incomplete_or_inconsistent_mutations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from scripts.codex_harness import run_pr284_depth_path_doob as runner

    baseline = runner._run_mutations()
    mutations = (
        baseline[:-1],
        [*baseline[:-1], baseline[0]],
        [baseline[1], baseline[0], *baseline[2:]],
        [{**baseline[0], "executed": False}, *baseline[1:]],
        [{**baseline[0], "activated": False}, *baseline[1:]],
        [{**baseline[0], "killed": False}, *baseline[1:]],
    )
    for rows in mutations:
        monkeypatch.setattr(runner, "_run_mutations", lambda rows=rows: rows)
        with pytest.raises(RuntimeError, match="mutation"):
            runner._build_payload()


def test_receipt_binds_selected_atom_threshold_maximum_and_mock_plan() -> None:
    from scripts.codex_harness import run_pr284_depth_path_doob as runner

    payload = json.loads(runner.OUTPUT.read_text())
    proved = payload["proved_fixture"]
    assert proved["finite_target_law"]["content_id"].startswith("sha256:")
    assert proved["selection_contract"]["content_id"].startswith("sha256:")
    assert proved["threshold_contract"]["content_id"].startswith("sha256:")
    assert proved["report"]["path_maximum_content_id"].startswith("sha256:")
    fallback = payload["unproved_fixture"]
    assert fallback["matched_mock_plan"]["null_mock_status"] == "required_not_executed"
    assert fallback["matched_mocks_executed"] is False
    assert fallback["probability_bound"] is None
    assert payload["future_consumer_contract"]["consumer"] == "PR-287"
    assert "known fast-oracle instability is hidden or promoted" in payload[
        "mathematical_boundary"
    ]["counterexample_boundaries"]
