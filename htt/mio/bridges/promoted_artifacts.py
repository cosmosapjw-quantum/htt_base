"""mio.bridges.promoted_artifacts — HTT promoted bundle ingestion surface.

This module provides the narrow HTT→MIO handoff for promoted HTT
artifacts. MIO must never ingest raw posterior samples; it may only
consume already-promoted summaries whose contracts explicitly advertise
``production_allowed=True``.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any, Mapping

from mio.interface.manifest import MioPrerequisites, assess_mio_readiness
from mio.interface.mio_certificate import build_mio_certificate, certificate_to_payload
from workspace.contracts.mio_certificate import MioCertificate
from workspace.contracts.tsc_overlay import TscAdequacyOverlay

ARTEFACT_FILENAME = "mio_promoted_axis_ingest_v1.json"


@dataclass(frozen=True)
class PromotedAxisSummary:
    """MIO-safe summary extracted from an HTT promoted posterior bundle."""

    artifact_name: str
    config_hash: str
    axis_l_deg: float
    axis_b_deg: float
    axis_label: str
    axis_source: str
    axis_weight_mode: str
    axis_selection_mode: str
    axis_provenance_hash: str
    credible_radius_deg: float
    coverage_68: float
    logz: float
    ncall: int
    posterior_samples_ref: str | None
    mock_calibration_ref: str | None


def _load_payload(bundle_or_path: Mapping[str, Any] | str | Path) -> Mapping[str, Any]:
    """Return a mapping from an in-memory dict or on-disk JSON path."""
    if isinstance(bundle_or_path, Mapping):
        return bundle_or_path
    path = Path(bundle_or_path)
    return json.loads(path.read_text(encoding="utf-8"))


def ingest_fiducial_posterior_bundle(
    bundle_or_path: Mapping[str, Any] | str | Path,
) -> PromotedAxisSummary:
    """Validate and ingest ``fiducial_posterior_bundle_v1.json`` for MIO."""
    payload = _load_payload(bundle_or_path)
    if payload.get("artifact_name") != "fiducial_posterior_bundle_v1.json":
        raise ValueError(
            "Expected fiducial_posterior_bundle_v1.json; got "
            f"{payload.get('artifact_name')!r}"
        )
    if payload.get("production_allowed") is not True:
        raise ValueError("HTT bundle must be production_allowed=True for MIO ingestion")
    if "posterior_samples" in payload:
        raise ValueError("MIO bridge refuses raw posterior_samples payloads")

    axis = payload.get("axis", {})
    if axis.get("production_allowed") is not True:
        raise ValueError("HTT axis must be production_allowed=True for MIO ingestion")
    if not axis.get("provenance_hash"):
        raise ValueError("HTT axis provenance_hash must be non-empty")

    posterior_summary = payload.get("posterior_summary", {})
    credible_cone = posterior_summary.get("credible_cone_68", {})
    mock = payload.get("mock_calibration", {})
    if mock.get("passed_window") is not True:
        raise ValueError("mock_calibration.passed_window must be True")

    return PromotedAxisSummary(
        artifact_name=str(payload["artifact_name"]),
        config_hash=str(payload.get("config_hash", "")),
        axis_l_deg=float(axis["l_deg"]),
        axis_b_deg=float(axis["b_deg"]),
        axis_label=str(axis.get("label", "")),
        axis_source=str(axis.get("source", "")),
        axis_weight_mode=str(axis.get("weight_mode", "")),
        axis_selection_mode=str(axis.get("selection_mode", "")),
        axis_provenance_hash=str(axis["provenance_hash"]),
        credible_radius_deg=float(credible_cone.get("radius_deg", mock.get("credible_radius_deg", 0.0))),
        coverage_68=float(mock["coverage_68"]),
        logz=float(payload.get("logz", 0.0)),
        ncall=int(payload.get("ncall", 0)),
        posterior_samples_ref=payload.get("posterior_samples_ref"),
        mock_calibration_ref=payload.get("mock_calibration_ref"),
    )


def to_mio_certificate(
    summary: PromotedAxisSummary,
    *,
    tsc_overlay: TscAdequacyOverlay | None = None,
    tsc_overlay_ref: str | None = None,
) -> MioCertificate:
    """Convert an ingested HTT promoted axis summary into a MioCertificate."""
    readiness = assess_mio_readiness(MioPrerequisites(eligible_for_production=False))
    return build_mio_certificate(
        report_type="promoted_axis_ingest",
        probe_name="HTT",
        channel="direction_axis",
        departure_variables={
            "axis_l_deg": float(summary.axis_l_deg),
            "axis_b_deg": float(summary.axis_b_deg),
            "credible_radius_deg": float(summary.credible_radius_deg),
            "coverage_68": float(summary.coverage_68),
        },
        adequacy_indicators={
            "coverage_window_passed": True,
            "axis_promoted": True,
            "bundle_promoted": True,
        },
        consistency_metrics={
            "logz": float(summary.logz),
            "ncall": float(summary.ncall),
        },
        domain_caveats=[
            "derived_from_htt_promoted_bundle",
            "mio_ingests_promoted_summary_only_not_posterior",
        ],
        channel_caveats=[],
        reduction_status="diagnostic-only",
        generated_by="mio.bridges.promoted_artifacts v0.1",
        input_data_hashes=[summary.config_hash],
        htt_cross_check_suggested={
            "module": "common.posterior_summary",
            "artifact_name": summary.artifact_name,
        },
        tsc_overlay=tsc_overlay,
        tsc_overlay_ref=tsc_overlay_ref,
        readiness=readiness,
        artifact_id="mio.promoted_axis_ingest.certificate",
        artifact_path=f"artifacts/mio/{ARTEFACT_FILENAME}",
        statistics_definitions={
            "report_type": "promoted_axis_ingest",
            "channel": "direction_axis",
        },
    )


def emit_promoted_axis_ingestion_artefact(
    out_path: str | Path,
    bundle_or_path: Mapping[str, Any] | str | Path,
    *,
    tsc_overlay: TscAdequacyOverlay | None = None,
    tsc_overlay_ref: str | None = None,
) -> dict[str, Any]:
    """Write ``mio_promoted_axis_ingest_v1.json`` from an HTT promoted bundle."""
    out = Path(out_path)
    if not out.name.startswith("mio_"):
        raise ValueError("MIO artefact filename must start with 'mio_'")

    summary = ingest_fiducial_posterior_bundle(bundle_or_path)
    cert = to_mio_certificate(
        summary,
        tsc_overlay=tsc_overlay,
        tsc_overlay_ref=tsc_overlay_ref,
    )
    payload = {
        "artifact_name": ARTEFACT_FILENAME,
        "summary": asdict(summary),
        "certificate": certificate_to_payload(cert),
    }
    out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


__all__ = [
    "ARTEFACT_FILENAME",
    "PromotedAxisSummary",
    "emit_promoted_axis_ingestion_artefact",
    "ingest_fiducial_posterior_bundle",
    "to_mio_certificate",
]
