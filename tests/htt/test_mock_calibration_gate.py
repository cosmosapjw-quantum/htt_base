from __future__ import annotations

import json

import pytest

from common.contracts import ClaimTier, PreferredAxis, SkySupport
from htt.nulls.axis_nulls import (
    AxisMockCalibrationThresholds,
    build_axis_mock_calibration_report,
    evaluate_axis_mock_gate,
)
from htt.zoa.axis_promotion import (
    AxisPromotionRecord,
    evaluate_axis_promotion,
    require_axis_for_harmonic_synthesis,
)


def _sky_support(**overrides: object) -> SkySupport:
    base = dict(
        selection_mode="mock_calibrated",
        sky_support_hash="sha256:" + "1" * 64,
        mask_hash="sha256:" + "2" * 64,
        mock_coverage_status="adequate",
        scan_volume_hash="sha256:" + "3" * 64,
        coordinate_frame="galactic",
        sky_fraction=0.75,
        completeness_status="mock_calibrated",
        pixelization="healpix",
        nside=8,
    )
    base.update(overrides)
    return SkySupport(**base)  # type: ignore[arg-type]


def _axis(**overrides: object) -> PreferredAxis:
    base = dict(
        l_deg=264.0,
        b_deg=48.0,
        label="fiducial-axis",
        source="fiducial_posterior",
        weight_mode="native",
        selection_mode="mock_calibrated",
        production_allowed=True,
        provenance_hash="1234567890abcdef",
    )
    base.update(overrides)
    return PreferredAxis(**base)  # type: ignore[arg-type]


def _thresholds(**overrides: object) -> AxisMockCalibrationThresholds:
    base = dict(
        min_retention_fraction=0.90,
        max_bias_direction_deg=5.0,
        coverage_68_window=(0.60, 0.76),
        max_false_positive_rate=0.05,
        min_n_mock=100,
        min_response_rank=3,
        min_effective_rank=2.0,
        max_condition_number=100.0,
        max_null_space_dimension=0,
    )
    base.update(overrides)
    return AxisMockCalibrationThresholds(**base)  # type: ignore[arg-type]


def _report(sky_support: SkySupport | None = None, **overrides: object):
    sky_support = _sky_support() if sky_support is None else sky_support
    base = dict(
        claim_target="production_axis_candidate",
        n_mock_requested=240,
        n_mock_succeeded=230,
        bias_direction_deg=2.0,
        coverage_68=0.68,
        false_positive_rate=0.01,
        null_ensemble="axis_direction_isotropic",
        detection_rule="max_cone_scan_threshold",
        look_elsewhere_trials=2,
        scan_trial_count=2,
        scan_trial_hash="sha256:" + "b" * 64,
        response_rank=3,
        effective_rank=2.8,
        null_space_dimension=0,
        condition_number=12.0,
        sky_support_hash=sky_support.sky_support_hash,
        mask_hash=sky_support.mask_hash,
        scan_volume_hash=sky_support.scan_volume_hash,
        config_hash="sha256:" + "8" * 64,
        input_hashes=("sha256:" + "9" * 64,),
        covariance_status="directional_mock_covariance_available",
        generating_command="tests.htt.test_mock_calibration_gate",
        git_commit="test-commit",
        worktree_state="test-clean",
        sky_support_status="pr040_sky_support_attached",
        sky_support_metadata=sky_support.to_metadata(),
        coverage_68_count=156,
        false_positive_count=2,
        bias_direction_p95_deg=3.0,
        thresholds=_thresholds(),
    )
    base.update(overrides)
    return build_axis_mock_calibration_report(**base)  # type: ignore[arg-type]


def _promotion_record(
    axis: PreferredAxis,
    sky_support: SkySupport,
    report,
    **overrides: object,
) -> AxisPromotionRecord:
    base = dict(
        axis_provenance_hash=axis.provenance_hash,
        sky_support_hash=sky_support.sky_support_hash,
        mask_hash=sky_support.mask_hash,
        mock_coverage_status=sky_support.mock_coverage_status,
        mock_calibration_hash=report.calibration_hash,
        posterior_bundle_hash="sha256:" + "5" * 64,
        config_hash="sha256:" + "6" * 64,
        input_hashes=("sha256:" + "7" * 64,),
        null_mock_status=report.null_mock_status,
        caveats=tuple(report.caveats),
    )
    base.update(overrides)
    return AxisPromotionRecord(**base)  # type: ignore[arg-type]


def test_axis_mock_report_records_directional_calibration_metadata() -> None:
    sky_support = _sky_support()
    report = _report(sky_support)

    assert report.retention_fraction == pytest.approx(230.0 / 240.0)
    assert report.allowed_claim_tier is ClaimTier.CONDITIONAL
    assert report.null_mock_status == "directional_null_mock_passed"
    assert report.calibration_hash.startswith("sha256:")

    metadata = report.to_metadata()
    assert metadata["owner"] == "HTT"
    assert metadata["implementation_scope"] == "htt"
    assert metadata["claim_tier"] == "diagnostic_only"
    assert metadata["transfer_source"] == "none"
    assert metadata["sky_support_hash"] == sky_support.sky_support_hash
    assert metadata["mask_hash"] == sky_support.mask_hash
    assert metadata["mock_calibration_hash"] == report.calibration_hash
    assert metadata["retention"]["retention_fraction"] == pytest.approx(230 / 240)
    assert metadata["bias"]["bias_direction_deg"] == pytest.approx(2.0)
    assert metadata["coverage"]["coverage_68"] == pytest.approx(0.68)
    assert metadata["coverage"]["coverage_68_count"] == 156
    assert metadata["false_positive_rate"]["look_elsewhere_trials"] == 2
    assert metadata["false_positive_rate"]["scan_trial_count"] == 2
    assert metadata["false_positive_rate"]["false_positive_count"] == 2
    assert metadata["false_positive_rate"]["adjusted"] == pytest.approx(0.02)
    assert metadata["sky_support_status"] == "pr040_sky_support_attached"
    assert metadata["sky_support"]["coordinate_frame"] == "galactic"
    assert metadata["covariance_status"] == "directional_mock_covariance_available"

    payload_text = json.dumps(metadata, sort_keys=True).lower()
    for forbidden in ("family ident", "geometry detect", "native solver", "posterior odds", "mio evidence"):
        assert forbidden not in payload_text


def test_missing_mock_calibration_blocks_claims_above_diagnostic() -> None:
    diagnostic = evaluate_axis_mock_gate(None, requested_claim_tier=ClaimTier.DIAGNOSTIC_ONLY)
    assert diagnostic.allowed is True
    assert diagnostic.allowed_claim_tier is ClaimTier.DIAGNOSTIC_ONLY

    conditional = evaluate_axis_mock_gate(None, requested_claim_tier=ClaimTier.CONDITIONAL)
    assert conditional.allowed is False
    assert "axis_mock_calibration_report_missing" in conditional.blocked_reasons
    assert "requested_claim_tier_exceeds_mock_calibration_ceiling" in conditional.blocked_reasons


def test_inadequate_retention_bias_coverage_and_fpr_fail_closed() -> None:
    report = _report(
        n_mock_requested=240,
        n_mock_succeeded=120,
        bias_direction_deg=8.0,
        bias_direction_p95_deg=9.0,
        coverage_68=0.52,
        coverage_68_count=62,
        false_positive_rate=0.08,
        false_positive_count=10,
        look_elsewhere_trials=2,
        scan_trial_count=2,
        response_rank=1,
        effective_rank=1.5,
        null_space_dimension=3,
        condition_number=250.0,
    )

    assert report.allowed_claim_tier is ClaimTier.DIAGNOSTIC_ONLY
    for expected in (
        "retention_fraction_below_threshold",
        "direction_bias_exceeds_threshold",
        "coverage_68_outside_window",
        "false_positive_rate_exceeds_threshold",
        "response_rank_below_threshold",
        "effective_rank_below_threshold",
        "null_space_dimension_nonzero",
        "null_space_dimension_exceeds_threshold",
        "condition_number_exceeds_threshold",
    ):
        assert expected in report.blocked_reasons

    decision = evaluate_axis_mock_gate(report, requested_claim_tier=ClaimTier.CONDITIONAL)
    assert decision.allowed is False
    assert "requested_claim_tier_exceeds_mock_calibration_ceiling" in decision.blocked_reasons


def test_report_cannot_weaken_production_mock_thresholds() -> None:
    weak_thresholds = AxisMockCalibrationThresholds(
        min_retention_fraction=0.01,
        max_bias_direction_deg=180.0,
        coverage_68_window=(0.0, 1.0),
        max_false_positive_rate=1.0,
        min_n_mock=1,
        min_response_rank=1,
        min_effective_rank=0.0,
        max_condition_number=1.0e30,
        max_null_space_dimension=99,
    )
    report = _report(
        n_mock_requested=100,
        n_mock_succeeded=1,
        bias_direction_deg=170.0,
        bias_direction_p95_deg=175.0,
        coverage_68=0.0,
        coverage_68_count=0,
        false_positive_rate=1.0,
        false_positive_count=1,
        look_elsewhere_trials=1,
        scan_trial_count=1,
        response_rank=1,
        effective_rank=0.0,
        null_space_dimension=0,
        condition_number=1.0e20,
        thresholds=weak_thresholds,
    )

    assert report.allowed_claim_tier is ClaimTier.DIAGNOSTIC_ONLY
    assert (
        "mock_calibration_thresholds_weaker_than_policy"
        in report.blocked_reasons
    )
    decision = evaluate_axis_mock_gate(
        report,
        requested_claim_tier=ClaimTier.CONDITIONAL,
    )
    assert decision.allowed is False


def test_zero_success_mock_bank_serializes_as_blocked_report() -> None:
    report = _report(
        n_mock_requested=120,
        n_mock_succeeded=0,
        coverage_68=0.0,
        coverage_68_count=0,
        false_positive_rate=0.0,
        false_positive_count=0,
    )

    assert report.allowed_claim_tier is ClaimTier.DIAGNOSTIC_ONLY
    assert "n_mock_below_threshold" in report.blocked_reasons
    assert "retention_fraction_below_threshold" in report.blocked_reasons
    metadata = report.to_metadata()
    assert metadata["coverage"]["coverage_68_interval"] == [0.0, 1.0]
    assert metadata["false_positive_rate"]["adjusted_interval"] == [0.0, 1.0]


def test_axis_mock_report_rejects_reserved_claim_language() -> None:
    with pytest.raises(ValueError, match="reserved claim language"):
        _report(caveats=("family identified by calibration",))

    with pytest.raises(ValueError, match="reserved claim language"):
        _report(detection_rule="posterior odds threshold")


def test_axis_mock_report_rejects_unattached_sky_and_covariance_status() -> None:
    report = _report(
        sky_support_status="hashes_only",
        sky_support_metadata=None,
        covariance_status="not_available",
    )

    assert report.allowed_claim_tier is ClaimTier.DIAGNOSTIC_ONLY
    assert "sky_support_status_not_attached" in report.blocked_reasons
    assert "sky_support_metadata_missing" in report.blocked_reasons
    assert "covariance_status_not_calibrated" in report.blocked_reasons


def test_axis_mock_report_requires_exact_event_counts_and_bias_tail() -> None:
    with pytest.raises(ValueError, match="coverage_68_count is required"):
        _report(coverage_68_count=None)

    with pytest.raises(ValueError, match="false_positive_count is required"):
        _report(false_positive_count=None)

    with pytest.raises(ValueError, match="bias_direction_p95_deg is required"):
        _report(bias_direction_p95_deg=None)


def test_axis_mock_report_rejects_transfer_source_and_record_transfer_source() -> None:
    with pytest.raises(ValueError, match="transfer_source"):
        _report(transfer_source="BASS_native_validated")

    sky_support = _sky_support()
    axis = _axis()
    report = _report(sky_support)
    with pytest.raises(ValueError, match="transfer_source"):
        _promotion_record(axis, sky_support, report, transfer_source="native_solver")


def test_coverage_interval_and_scan_trial_provenance_fail_closed() -> None:
    coverage_edge = _report(
        n_mock_requested=120,
        n_mock_succeeded=100,
        coverage_68=0.60,
        coverage_68_count=60,
        false_positive_rate=0.01,
        false_positive_count=1,
    )
    assert "coverage_68_interval_outside_window" in coverage_edge.blocked_reasons

    look_elsewhere_gap = _report(
        look_elsewhere_trials=1,
        scan_trial_count=2,
    )
    assert (
        "look_elsewhere_trials_scan_count_mismatch"
        in look_elsewhere_gap.blocked_reasons
    )


def test_axis_promotion_requires_hash_matched_calibration_report() -> None:
    sky_support = _sky_support()
    axis = _axis()
    report = _report(sky_support)
    record = _promotion_record(axis, sky_support, report)

    missing = evaluate_axis_promotion(
        axis,
        sky_support=sky_support,
        promotion_record=record,
        target="a_lm",
    )
    assert missing.allowed is False
    assert "axis_mock_calibration_report_missing" in missing.blocked_reasons

    forged = evaluate_axis_promotion(
        axis,
        sky_support=sky_support,
        promotion_record=_promotion_record(
            axis,
            sky_support,
            report,
            mock_calibration_hash="sha256:" + "a" * 64,
        ),
        mock_calibration_report=report,
        target="a_lm",
    )
    assert forged.allowed is False
    assert "promotion_record_mock_calibration_hash_mismatch" in forged.blocked_reasons

    decision = evaluate_axis_promotion(
        axis,
        sky_support=sky_support,
        promotion_record=record,
        mock_calibration_report=report,
        target="a_lm",
    )
    assert decision.allowed is True
    assert require_axis_for_harmonic_synthesis(
        axis,
        sky_support=sky_support,
        promotion_record=record,
        mock_calibration_report=report,
        target="a_lm",
    ) is axis


def test_axis_promotion_rejects_bad_calibration_even_when_status_is_adequate() -> None:
    sky_support = _sky_support()
    axis = _axis()
    bad_report = _report(
        sky_support,
        false_positive_rate=0.08,
        false_positive_count=18,
    )
    record = _promotion_record(axis, sky_support, bad_report)

    decision = evaluate_axis_promotion(
        axis,
        sky_support=sky_support,
        promotion_record=record,
        mock_calibration_report=bad_report,
        target="a_lm",
    )
    assert decision.allowed is False
    assert "false_positive_rate_exceeds_threshold" in decision.blocked_reasons
    assert "requested_claim_tier_exceeds_mock_calibration_ceiling" in decision.blocked_reasons


def test_axis_promotion_rejects_sky_support_mismatch_in_report() -> None:
    sky_support = _sky_support()
    report = _report(_sky_support(sky_support_hash="sha256:" + "a" * 64))
    axis = _axis()
    record = _promotion_record(axis, sky_support, report)

    decision = evaluate_axis_promotion(
        axis,
        sky_support=sky_support,
        promotion_record=record,
        mock_calibration_report=report,
        target="a_lm",
    )
    assert decision.allowed is False
    assert "mock_calibration_sky_support_hash_mismatch" in decision.blocked_reasons


def test_axis_promotion_rejects_mask_and_scan_mismatch_in_report() -> None:
    sky_support = _sky_support()
    axis = _axis()

    mask_report = _report(_sky_support(mask_hash="sha256:" + "c" * 64))
    mask_record = _promotion_record(axis, sky_support, mask_report)
    mask_decision = evaluate_axis_promotion(
        axis,
        sky_support=sky_support,
        promotion_record=mask_record,
        mock_calibration_report=mask_report,
        target="a_lm",
    )
    assert mask_decision.allowed is False
    assert "mock_calibration_mask_hash_mismatch" in mask_decision.blocked_reasons

    scan_report = _report(_sky_support(scan_volume_hash="sha256:" + "d" * 64))
    scan_record = _promotion_record(axis, sky_support, scan_report)
    scan_decision = evaluate_axis_promotion(
        axis,
        sky_support=sky_support,
        promotion_record=scan_record,
        mock_calibration_report=scan_report,
        target="a_lm",
    )
    assert scan_decision.allowed is False
    assert "mock_calibration_scan_volume_hash_mismatch" in scan_decision.blocked_reasons
