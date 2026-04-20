from __future__ import annotations

import pytest

from common.contracts import PreferredAxis, SkySupport
from htt.infer.axis_gate import build_diagnostic_axis, evaluate_axis_gate, require_production_axis


def _sky_support(*, mock_coverage_status: str = "adequate") -> SkySupport:
    return SkySupport(
        selection_mode="mock_calibrated",
        sky_support_hash="sky123",
        mask_hash="mask123",
        mock_coverage_status=mock_coverage_status,
        scan_volume_hash="scan123",
    )


def test_diagnostic_axis_stays_diagnostic():
    axis = build_diagnostic_axis(l_deg=10.0, b_deg=20.0, label="diag")
    assert axis.production_allowed is False
    decision = evaluate_axis_gate(axis, sky_support=_sky_support())
    assert not decision.allowed
    assert "axis_not_production_promoted" in decision.blocked_reasons


def test_production_axis_requires_mock_and_sky_support():
    axis = PreferredAxis(
        l_deg=264.0,
        b_deg=48.0,
        label="fiducial",
        source="fiducial_posterior",
        weight_mode="native",
        selection_mode="mock_calibrated",
        production_allowed=True,
        provenance_hash="abc123",
    )
    with pytest.raises(RuntimeError, match="mock_coverage_missing"):
        require_production_axis(axis, sky_support=_sky_support(mock_coverage_status="pending"))
    with pytest.raises(RuntimeError, match="sky_support_missing"):
        require_production_axis(axis, sky_support=None)


def test_production_axis_gate_allows_posterior_axis():
    axis = PreferredAxis(
        l_deg=264.0,
        b_deg=48.0,
        label="fiducial",
        source="fiducial_posterior",
        weight_mode="native",
        selection_mode="mock_calibrated",
        production_allowed=True,
        provenance_hash="abc123",
    )
    out = require_production_axis(axis, sky_support=_sky_support())
    assert out is axis
