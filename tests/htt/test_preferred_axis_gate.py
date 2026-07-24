from __future__ import annotations

import numpy as np
import pytest

from common.contracts import PreferredAxis, SkySupport
from common.posterior_summary import axis_from_posterior
from htt.PR13AJ_full_a2m_restoration import restore_full_a2m
from htt.direction.preferred_axis import build_preferred_axis
from htt.nulls.axis_nulls import build_axis_mock_calibration_report
from htt.zoa.axis_promotion import (
    AxisPromotionRecord,
    evaluate_axis_promotion,
    require_axis_for_harmonic_synthesis,
)
from htt.zoa.selection_ladder import build_zoa_selection_ladder


def _rich_sky_support(**overrides: object) -> SkySupport:
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


def _posterior_axis() -> PreferredAxis:
    samples = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.9, 0.1, 0.0],
            [1.1, -0.1, 0.1],
        ],
        dtype=float,
    )
    return axis_from_posterior(
        samples,
        weight_mode="native",
        selection_mode="mock_calibrated",
        config={"pr": "PR-042"},
    )


def _promotion_record(
    axis: PreferredAxis,
    sky_support: SkySupport,
    report=None,
    **overrides: object,
) -> AxisPromotionRecord:
    if report is None:
        report = _axis_mock_report(sky_support)
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
    )
    base.update(overrides)
    return AxisPromotionRecord(**base)  # type: ignore[arg-type]


def _axis_mock_report(sky_support: SkySupport, **overrides: object):
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
        generating_command="tests.htt.test_preferred_axis_gate",
        git_commit="test-commit",
        worktree_state="test-clean",
        sky_support_status="pr040_sky_support_attached",
        sky_support_metadata=sky_support.to_metadata(),
        coverage_68_count=156,
        false_positive_count=2,
        bias_direction_p95_deg=3.0,
    )
    base.update(overrides)
    return build_axis_mock_calibration_report(**base)


def test_preferred_axis_default_is_diagnostic_only() -> None:
    axis = build_preferred_axis(
        l_deg=12.0,
        b_deg=-4.0,
        label="raw-axis",
        source="raw_diagnostic",
        weight_mode="native",
        selection_mode="none",
    )
    assert isinstance(axis, PreferredAxis)
    assert axis.production_allowed is False


def test_zoa_diagnostic_axis_cannot_rotate_alm_or_a2m() -> None:
    l_deg = np.array([0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0])
    b_deg = np.array([-60.0, -25.0, -5.0, 12.0, 28.0, 45.0, 63.0, 78.0])
    ladder = build_zoa_selection_ladder(
        l_deg,
        b_deg,
        bcut_deg=15.0,
        nside=8,
        mock_calibration_weights=np.ones_like(l_deg),
        mock_coverage_status="adequate",
    )
    axis = ladder.mock_calibrated.to_diagnostic_axis(label="mock-support")

    decision = evaluate_axis_promotion(
        axis,
        sky_support=ladder.mock_calibrated.sky_support,
        target="a_lm",
    )
    assert decision.allowed is False
    assert "axis_not_production_promoted" in decision.blocked_reasons
    assert "production_axis_wrong_provenance" in decision.blocked_reasons
    assert "diagnostic_axis_cannot_rotate_a_lm" in decision.blocked_reasons

    with pytest.raises(RuntimeError, match="diagnostic_axis_cannot_rotate_a_2m"):
        require_axis_for_harmonic_synthesis(
            axis,
            sky_support=ladder.mock_calibrated.sky_support,
            target="a_2m",
        )
    with pytest.raises(RuntimeError, match="diagnostic_axis_cannot_rotate_a_2m"):
        restore_full_a2m(
            axis,
            a20_seed=complex(1.0, 0.0),
            sky_support=ladder.mock_calibrated.sky_support,
        )


def test_promotion_requires_rich_sky_support_and_record() -> None:
    axis = _posterior_axis()
    weak_sky = SkySupport(
        selection_mode="mock_calibrated",
        sky_support_hash="sky123",
        mask_hash="mask123",
        mock_coverage_status="adequate",
        scan_volume_hash="scan123",
    )
    record = _promotion_record(axis, _rich_sky_support())

    decision = evaluate_axis_promotion(
        axis,
        sky_support=weak_sky,
        promotion_record=record,
        target="a_lm",
    )
    assert decision.allowed is False
    assert "sky_support_hash_not_sha256" in decision.blocked_reasons
    assert "mask_hash_not_sha256" in decision.blocked_reasons
    assert "scan_volume_hash_not_sha256" in decision.blocked_reasons
    assert "sky_fraction_missing" in decision.blocked_reasons
    assert "coordinate_frame_legacy_unspecified" in decision.blocked_reasons
    assert "promotion_record_sky_support_hash_mismatch" in decision.blocked_reasons


def test_promotion_rejects_invalid_healpix_nside() -> None:
    axis = _posterior_axis()
    sky_support = _rich_sky_support(nside=3)
    report = _axis_mock_report(sky_support)

    decision = evaluate_axis_promotion(
        axis,
        sky_support=sky_support,
        promotion_record=_promotion_record(axis, sky_support, report),
        mock_calibration_report=report,
        target="a_lm",
    )

    assert decision.allowed is False
    assert "nside_not_power_of_two" in decision.blocked_reasons


def test_promotion_rejects_malformed_sha256_prefixes() -> None:
    axis = _posterior_axis()
    sky_support = _rich_sky_support(sky_support_hash="sha256:not-a-digest")
    record = _promotion_record(
        axis,
        _rich_sky_support(),
        sky_support_hash="sha256:" + "1" * 64,
    )

    decision = evaluate_axis_promotion(
        axis,
        sky_support=sky_support,
        promotion_record=record,
        target="a_lm",
    )
    assert decision.allowed is False
    assert "sky_support_hash_not_sha256" in decision.blocked_reasons

    with pytest.raises(ValueError, match="64 hex chars"):
        _promotion_record(
            axis,
            _rich_sky_support(),
            mock_calibration_hash="sha256:not-a-digest",
        )


def test_promotion_rejects_forged_axis_provenance_even_with_matching_record() -> None:
    axis = PreferredAxis(
        l_deg=264.0,
        b_deg=48.0,
        label="manual",
        source="fiducial_posterior",
        weight_mode="native",
        selection_mode="mock_calibrated",
        production_allowed=True,
        provenance_hash="not-a-real-hash",
    )
    sky_support = _rich_sky_support()

    decision = evaluate_axis_promotion(
        axis,
        sky_support=sky_support,
        target="a_lm",
    )
    assert decision.allowed is False
    assert "axis_provenance_hash_placeholder" in decision.blocked_reasons

    with pytest.raises(ValueError, match="axis_provenance_hash"):
        _promotion_record(axis, sky_support)


def test_promotion_record_lineage_is_self_attested_pre_solver() -> None:
    axis = _posterior_axis()
    sky_support = _rich_sky_support()
    record = _promotion_record(axis, sky_support)

    assert record.lineage_status == "self_attested_pre_solver"
    assert record.to_metadata()["lineage_status"] == "self_attested_pre_solver"
    with pytest.raises(ValueError, match="self_attested_pre_solver"):
        _promotion_record(axis, sky_support, lineage_status="native_validated")


def test_manual_production_flag_without_record_still_fails_closed() -> None:
    axis = PreferredAxis(
        l_deg=264.0,
        b_deg=48.0,
        label="manual",
        source="fiducial_posterior",
        weight_mode="native",
        selection_mode="mock_calibrated",
        production_allowed=True,
        provenance_hash="1234567890abcdef",
    )
    sky_support = _rich_sky_support()

    missing = evaluate_axis_promotion(axis, sky_support=sky_support, target="a_lm")
    assert missing.allowed is False
    assert "axis_promotion_record_missing" in missing.blocked_reasons

    mismatch = evaluate_axis_promotion(
        axis,
        sky_support=sky_support,
        promotion_record=_promotion_record(
            axis,
            sky_support,
            axis_provenance_hash="fedcba0987654321",
        ),
        target="a_lm",
    )
    assert mismatch.allowed is False
    assert "promotion_record_axis_hash_mismatch" in mismatch.blocked_reasons


def test_posterior_axis_with_rich_support_and_record_passes_lock() -> None:
    axis = _posterior_axis()
    sky_support = _rich_sky_support()
    report = _axis_mock_report(sky_support)
    record = _promotion_record(axis, sky_support, report)

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

    with pytest.raises(NotImplementedError, match="Rotation body pending"):
        restore_full_a2m(
            axis,
            a20_seed=complex(1.0, 0.0),
            sky_support=sky_support,
            promotion_record=record,
            mock_calibration_report=report,
        )


def test_restore_full_a2m_requires_synthesis_lock_before_stub() -> None:
    axis = _posterior_axis()
    with pytest.raises(RuntimeError, match="sky_support_missing"):
        restore_full_a2m(axis, a20_seed=complex(1.0, 0.0))
