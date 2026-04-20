"""Blockwise residual-origin classification for TSC reports."""
from __future__ import annotations

from typing import Mapping

from common.contracts import ArtifactManifest, TscResidualReport, TscChart


def classify_residual_origin(
    trace_q: float,
    spin2_q: float,
    high_q: float,
    thresholds: Mapping[str, float] | None = None,
) -> str:
    thresholds = dict(thresholds or {})
    trace_thr = float(thresholds.get("trace", 0.0))
    spin2_thr = float(thresholds.get("spin2", 0.0))
    high_thr = float(thresholds.get("high", 0.0))

    trace_on = trace_q > trace_thr
    spin2_on = spin2_q > spin2_thr
    high_on = high_q > high_thr

    if trace_on and not spin2_on and not high_on:
        return "trace"
    if spin2_on and not trace_on and not high_on:
        return "spin2"
    if high_on and not trace_on and not spin2_on:
        return "high"
    if not trace_on and not spin2_on and not high_on:
        return "unknown"
    return "mixed"


def ambient_vs_projected_defect_report(
    *,
    chart: TscChart,
    laguerre_n_ge_2_norm: float,
    ambient_defect_rate: float | None,
    projected_defect_estimate: float | None,
    onefield_residual: float | None,
    twofield_residual: float | None,
    eta_tangent_fraction: float | None,
    trace_residual_q_tr: float | None,
    spin2_residual: float | None,
    high_residual: float | None,
    labels: tuple[str, ...],
    manifest: ArtifactManifest,
    thresholds: Mapping[str, float] | None = None,
) -> TscResidualReport:
    origin = classify_residual_origin(
        trace_q=float(trace_residual_q_tr or 0.0),
        spin2_q=float(spin2_residual or 0.0),
        high_q=float(high_residual or 0.0),
        thresholds=thresholds,
    )
    return TscResidualReport(
        chart=chart,
        laguerre_n_ge_2_norm=laguerre_n_ge_2_norm,
        ambient_defect_rate=ambient_defect_rate,
        projected_defect_estimate=projected_defect_estimate,
        onefield_residual=onefield_residual,
        twofield_residual=twofield_residual,
        eta_tangent_fraction=eta_tangent_fraction,
        trace_residual_q_tr=trace_residual_q_tr,
        spin2_residual=spin2_residual,
        high_residual=high_residual,
        residual_origin=origin,  # type: ignore[arg-type]
        labels=labels,
        manifest=manifest,
    )


__all__ = [
    "ambient_vs_projected_defect_report",
    "classify_residual_origin",
]
