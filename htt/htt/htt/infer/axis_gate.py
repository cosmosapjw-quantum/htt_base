"""Production-axis gating for VER2 HTT directional inference."""
from __future__ import annotations

from dataclasses import dataclass

from common.contracts import PreferredAxis, SkySupport

__all__ = [
    "AxisGateDecision",
    "build_diagnostic_axis",
    "evaluate_axis_gate",
    "require_production_axis",
]


@dataclass(frozen=True)
class AxisGateDecision:
    """Decision record for production use of a directional axis."""

    allowed: bool
    required_conditions: tuple[str, ...]
    blocked_reasons: tuple[str, ...]
    axis: PreferredAxis
    sky_support: SkySupport | None
    carry_forward: tuple[str, ...] = ()

    @property
    def reasons(self) -> tuple[str, ...]:
        """Compatibility alias for older call sites."""
        return self.blocked_reasons


def build_diagnostic_axis(
    *,
    l_deg: float,
    b_deg: float,
    label: str,
    source: str = "raw_diagnostic",
    weight_mode: str = "native",
    selection_mode: str = "none",
) -> PreferredAxis:
    """Construct a diagnostic-only axis."""
    return PreferredAxis(
        l_deg=l_deg,
        b_deg=b_deg,
        label=label,
        source=source,  # type: ignore[arg-type]
        weight_mode=weight_mode,  # type: ignore[arg-type]
        selection_mode=selection_mode,  # type: ignore[arg-type]
        production_allowed=False,
    )


def evaluate_axis_gate(
    axis: PreferredAxis,
    *,
    sky_support: SkySupport | None,
) -> AxisGateDecision:
    """Closed-fail gate for promoting an HTT axis into production use."""

    required = (
        "PreferredAxis.production_allowed=True",
        "PreferredAxis.source='fiducial_posterior'",
        "PreferredAxis.selection_mode='mock_calibrated'",
        "SkySupport.selection_mode='mock_calibrated'",
        "SkySupport.mock_coverage_status='adequate'",
    )
    blocked: list[str] = []
    if not axis.production_allowed:
        blocked.append("axis_not_production_promoted")
    if axis.source != "fiducial_posterior":
        blocked.append("production_axis_wrong_provenance")
    if axis.selection_mode != "mock_calibrated":
        blocked.append("production_axis_requires_mock_calibrated_selection")
    if sky_support is None:
        blocked.append("sky_support_missing")
    else:
        if sky_support.selection_mode != "mock_calibrated":
            blocked.append("sky_support_not_mock_calibrated")
        if axis.selection_mode != sky_support.selection_mode:
            blocked.append("axis_sky_selection_mismatch")
        if sky_support.mock_coverage_status != "adequate":
            blocked.append("mock_coverage_missing")

    carry_forward: list[str] = []
    if not axis.provenance_hash:
        carry_forward.append("axis_provenance_hash_placeholder")
    if sky_support is not None and not sky_support.scan_volume_hash:
        carry_forward.append("sky_support_scan_volume_placeholder")

    return AxisGateDecision(
        allowed=not blocked,
        required_conditions=required,
        blocked_reasons=tuple(blocked),
        axis=axis,
        sky_support=sky_support,
        carry_forward=tuple(carry_forward),
    )


def require_production_axis(
    axis: PreferredAxis,
    *,
    sky_support: SkySupport | None,
) -> PreferredAxis:
    """Raise if a directional axis does not pass the production gate."""

    decision = evaluate_axis_gate(axis, sky_support=sky_support)
    if not decision.allowed:
        raise RuntimeError(
            "HTT production axis gate failed: " + ", ".join(decision.blocked_reasons)
        )
    return axis
