from __future__ import annotations

import numpy as np
import pytest

from common.contracts import DirectionalSummary
from common.healpix_selection import build_zoa_mask, source_mask_from_pixel_mask
from htt.infer.axis_gate import evaluate_axis_gate
from htt.zoa.selection_ladder import (
    SelectionSupportMode,
    build_zoa_selection_ladder,
)


def _mixed_catalogue() -> tuple[np.ndarray, np.ndarray]:
    l_deg = np.array([0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0])
    b_deg = np.array([-60.0, -25.0, -5.0, 12.0, 28.0, 45.0, 63.0, 78.0])
    return l_deg, b_deg


def _equatorial_catalogue() -> tuple[np.ndarray, np.ndarray]:
    l_deg = np.linspace(0.0, 350.0, 24)
    b_deg = np.linspace(-5.0, 5.0, 24)
    return l_deg, b_deg


def test_source_mask_from_pixel_mask_maps_support_to_sources() -> None:
    l_deg, b_deg = _mixed_catalogue()
    mask = build_zoa_mask(l_deg, b_deg, bcut_deg=20.0, nside=8)
    source_mask = source_mask_from_pixel_mask(l_deg, b_deg, mask)
    assert source_mask.shape == l_deg.shape
    assert source_mask.dtype == np.dtype(bool)
    assert not source_mask[2]
    assert source_mask[-1]


def test_ladder_separates_four_support_modes_with_metadata() -> None:
    l_deg, b_deg = _mixed_catalogue()
    ladder = build_zoa_selection_ladder(
        l_deg,
        b_deg,
        bcut_deg=20.0,
        nside=8,
        smooth_sigma_pix=0.0,
        input_hashes=("sha256:catalogue",),
    )

    assert ladder.raw.mode is SelectionSupportMode.RAW
    assert ladder.zoa_masked.mode is SelectionSupportMode.ZOA_MASKED
    assert ladder.selection_aware.mode is SelectionSupportMode.SELECTION_AWARE
    assert ladder.mock_calibrated.mode is SelectionSupportMode.MOCK_CALIBRATED

    assert ladder.raw.selection_mode == "none"
    assert ladder.zoa_masked.selection_mode == "zoa_hard_cut"
    assert ladder.selection_aware.selection_mode == "angular_completeness"
    assert ladder.mock_calibrated.selection_mode == "mock_calibrated"

    assert ladder.raw.retention_fraction == 1.0
    assert 0.0 < ladder.zoa_masked.retention_fraction < 1.0
    assert ladder.selection_aware.n_active == ladder.zoa_masked.n_active
    assert ladder.mock_calibrated.sky_support.mock_coverage_status == "pending"
    assert ladder.mock_calibrated.metadata["owner"] == "HTT"
    assert ladder.mock_calibrated.metadata["claim_tier"] == "diagnostic_only"
    assert ladder.mock_calibrated.metadata["transfer_source"] == "none"
    assert ladder.mock_calibrated.metadata["config_hash"].startswith("sha256:")

    directional = ladder.to_directional_summary()
    assert isinstance(directional, DirectionalSummary)
    assert directional.raw["mode"] == "raw"
    assert directional.mock_calibrated["sky_support"]["selection_mode"] == "mock_calibrated"


def test_diagnostic_ladder_modes_cannot_pass_production_axis_gate() -> None:
    l_deg, b_deg = _mixed_catalogue()
    ladder = build_zoa_selection_ladder(
        l_deg,
        b_deg,
        bcut_deg=15.0,
        nside=8,
        mock_calibration_weights=np.ones_like(l_deg),
        mock_coverage_status="adequate",
    )
    summaries = (
        ladder.raw,
        ladder.zoa_masked,
        ladder.selection_aware,
        ladder.mock_calibrated,
    )
    assert all(summary.production_allowed is False for summary in summaries)

    decision = evaluate_axis_gate(
        ladder.mock_calibrated.to_diagnostic_axis(label="mock-support"),
        sky_support=ladder.mock_calibrated.sky_support,
    )
    assert not decision.allowed
    assert "axis_not_production_promoted" in decision.blocked_reasons
    assert "production_axis_wrong_provenance" in decision.blocked_reasons


def test_uniform_fallback_is_forbidden_in_production_mode() -> None:
    l_deg, b_deg = _equatorial_catalogue()
    with pytest.raises(ValueError, match="mutually exclusive"):
        build_zoa_selection_ladder(
            l_deg,
            b_deg,
            bcut_deg=60.0,
            nside=8,
            production_mode=True,
            allow_uniform_fallback=True,
            mock_calibration_weights=np.ones_like(l_deg),
            mock_coverage_status="adequate",
        )


def test_aggressive_cut_raises_unless_fallback_is_explicitly_diagnostic() -> None:
    l_deg, b_deg = _equatorial_catalogue()
    with pytest.raises(ValueError, match="forbidden"):
        build_zoa_selection_ladder(
            l_deg,
            b_deg,
            bcut_deg=60.0,
            nside=8,
            allow_uniform_fallback=False,
        )

    ladder = build_zoa_selection_ladder(
        l_deg,
        b_deg,
        bcut_deg=60.0,
        nside=8,
        allow_uniform_fallback=True,
    )
    assert ladder.zoa_masked.fallback_status == "uniform_fallback_diagnostic_only"
    assert ladder.zoa_masked.production_allowed is False
    np.testing.assert_allclose(ladder.zoa_masked.weights, 1.0 / l_deg.size)


def test_production_mode_requires_adequate_mock_calibration_inputs() -> None:
    l_deg, b_deg = _mixed_catalogue()
    with pytest.raises(ValueError, match="mock_calibration_weights"):
        build_zoa_selection_ladder(
            l_deg,
            b_deg,
            bcut_deg=20.0,
            nside=8,
            production_mode=True,
            mock_coverage_status="adequate",
        )
    with pytest.raises(ValueError, match="adequate mock coverage"):
        build_zoa_selection_ladder(
            l_deg,
            b_deg,
            bcut_deg=20.0,
            nside=8,
            production_mode=True,
            mock_calibration_weights=np.ones_like(l_deg),
            mock_coverage_status="pending",
        )

    ladder = build_zoa_selection_ladder(
        l_deg,
        b_deg,
        bcut_deg=20.0,
        nside=8,
        production_mode=True,
        mock_calibration_weights=np.ones_like(l_deg),
        mock_coverage_status="adequate",
    )
    assert ladder.mock_calibrated.sky_support.mock_coverage_status == "adequate"
    assert ladder.mock_calibrated.production_allowed is False
