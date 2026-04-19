"""COMMON-A tests — contracts (INDEPENDENT_TRACKS_PLAN §2.6)."""
from __future__ import annotations

import numpy as np
import pytest

from common.contracts import (
    DirectionalSummary,
    DynestyResult,
    MockCalibrationReport,
    PreferredAxis,
    SkySelectionConfig,
)


def _axis(**overrides) -> PreferredAxis:
    base = dict(
        l_deg=264.0,
        b_deg=48.0,
        label="test",
        source="fiducial_posterior",
        weight_mode="native",
        selection_mode="mock_calibrated",
        production_allowed=True,
        provenance_hash="deadbeef",
    )
    base.update(overrides)
    return PreferredAxis(**base)


class TestPreferredAxisContract:
    def test_roundtrips_fiducial_fields(self):
        ax = _axis()
        assert ax.production_allowed is True
        assert ax.provenance_hash == "deadbeef"

    def test_rejects_bad_source(self):
        with pytest.raises(ValueError, match="source"):
            _axis(source="bogus")

    def test_rejects_bad_weight_mode(self):
        with pytest.raises(ValueError, match="weight_mode"):
            _axis(weight_mode="bogus")

    def test_rejects_bad_selection_mode(self):
        with pytest.raises(ValueError, match="selection_mode"):
            _axis(selection_mode="bogus")

    def test_is_frozen(self):
        ax = _axis()
        with pytest.raises(Exception):
            ax.production_allowed = False  # type: ignore[misc]


class TestSkySelectionConfigInvariants:
    def test_fiducial_config_ok(self):
        cfg = SkySelectionConfig(
            zoa_half_angle_deg=20.0,
            production_mode=True,
            allow_uniform_fallback=False,
            require_mock_calibration=True,
        )
        assert cfg.production_mode is True

    def test_production_blocks_uniform_fallback(self):
        with pytest.raises(ValueError, match="mutually exclusive"):
            SkySelectionConfig(
                zoa_half_angle_deg=20.0,
                production_mode=True,
                allow_uniform_fallback=True,
            )

    def test_production_requires_mock_calibration(self):
        with pytest.raises(ValueError, match="mock calibration"):
            SkySelectionConfig(
                zoa_half_angle_deg=20.0,
                production_mode=True,
                require_mock_calibration=False,
            )

    def test_rejects_out_of_range_retention(self):
        with pytest.raises(ValueError, match="min_retention_fraction"):
            SkySelectionConfig(zoa_half_angle_deg=20.0, min_retention_fraction=1.5)

    def test_rejects_non_power_of_two_nside(self):
        with pytest.raises(ValueError, match="power of two"):
            SkySelectionConfig(zoa_half_angle_deg=20.0, nside=96)


class TestDirectionalSummary:
    def test_stores_four_channels(self):
        s = DirectionalSummary(
            raw={"tag": "raw"},
            zoa_masked={"tag": "zoa"},
            selection_aware={"tag": "sel"},
            mock_calibrated={"tag": "mock"},
        )
        assert s.raw["tag"] == "raw"
        assert s.mock_calibrated["tag"] == "mock"


class TestDynestyResult:
    def test_shape_mismatch_rejected(self):
        samples = np.zeros((10, 3))
        with pytest.raises(ValueError, match="logwt"):
            DynestyResult(
                samples=samples, logwt=np.zeros(5), logz=0.0, ncall=100, config={},
            )

    def test_requires_2d_samples(self):
        with pytest.raises(ValueError, match="2-D"):
            DynestyResult(
                samples=np.zeros(10), logwt=np.zeros(10),
                logz=0.0, ncall=10, config={},
            )


class TestMockCalibrationReport:
    def test_coverage_out_of_range_rejected(self):
        with pytest.raises(ValueError, match="coverage_68"):
            MockCalibrationReport(
                bias_amp=0.0, bias_direction_deg=0.0, coverage_68=1.5,
                credible_radius_deg=10.0, n_mock=100,
            )

    def test_negative_credible_radius_rejected(self):
        with pytest.raises(ValueError, match="credible_radius_deg"):
            MockCalibrationReport(
                bias_amp=0.0, bias_direction_deg=0.0, coverage_68=0.68,
                credible_radius_deg=-1.0, n_mock=100,
            )

    def test_zero_n_mock_rejected(self):
        with pytest.raises(ValueError, match="n_mock"):
            MockCalibrationReport(
                bias_amp=0.0, bias_direction_deg=0.0, coverage_68=0.68,
                credible_radius_deg=10.0, n_mock=0,
            )
