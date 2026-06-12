"""Directional mock-calibration gates for HTT axis claims.

The module is an HTT-facing adapter over ``common.mock_calibration``.  It
does not turn null mocks into posterior evidence and it does not identify a
Bianchi morphology family.  Its only job is to decide whether directional
mock calibration is sufficient for an HTT production-axis candidate.
"""
from __future__ import annotations

from common.contracts import ClaimTier, SkySupport
from common.mock_calibration import (
    AxisMockCalibrationGateDecision,
    AxisMockCalibrationReport,
    AxisMockCalibrationThresholds,
    build_axis_mock_calibration_report,
    evaluate_directional_claim_mock_gate,
)

__all__ = [
    "AxisMockCalibrationGateDecision",
    "AxisMockCalibrationReport",
    "AxisMockCalibrationThresholds",
    "build_axis_mock_calibration_report",
    "evaluate_axis_mock_gate",
]


def evaluate_axis_mock_gate(
    report: AxisMockCalibrationReport | None,
    *,
    requested_claim_tier: ClaimTier | str = ClaimTier.CONDITIONAL,
    sky_support: SkySupport | None = None,
    calibration_hash: str | None = None,
) -> AxisMockCalibrationGateDecision:
    """Evaluate the mock-calibration ceiling for a directional axis claim."""

    return evaluate_directional_claim_mock_gate(
        report,
        requested_claim_tier=requested_claim_tier,
        sky_support_hash=(
            sky_support.sky_support_hash if sky_support is not None else None
        ),
        mask_hash=sky_support.mask_hash if sky_support is not None else None,
        scan_volume_hash=(
            sky_support.scan_volume_hash if sky_support is not None else None
        ),
        calibration_hash=calibration_hash,
    )
