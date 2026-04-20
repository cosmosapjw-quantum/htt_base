"""mio.decomposition.redshift_tomography — HJ-04 coarse redshift slicing."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional, Sequence

from mio.interface.mio_certificate import build_mio_certificate
from workspace.contracts.mio_certificate import MioCertificate


DEFAULT_DOMAIN_CAVEAT = (
    "Redshift evidence tomography is a decomposition of HTT evidence, "
    "not an independent likelihood."
)


@dataclass(frozen=True)
class RedshiftEvidenceSlice:
    """One coarse redshift-era contribution."""

    label: str
    z_min: float
    z_max: float
    delta_lnB: float


@dataclass(frozen=True)
class RedshiftTomographyReport:
    """Coarse redshift decomposition summary."""

    model_label: str
    slices: tuple[RedshiftEvidenceSlice, ...]
    total_delta_lnB: float
    reconstructed_delta_lnB: float
    residual_delta_lnB: float
    consistent_with_total: bool
    consistency_tolerance: float


def summarize_redshift_tomography(
    slices: Sequence[RedshiftEvidenceSlice],
    *,
    model_label: str = "FLRW_vs_BianchiI",
    total_delta_lnB: Optional[float] = None,
    consistency_tolerance: float = 0.10,
) -> RedshiftTomographyReport:
    """Summarize a coarse redshift-era decomposition."""
    if not slices:
        raise ValueError("slices must contain at least one entry")
    reconstructed = float(sum(float(item.delta_lnB) for item in slices))
    total = reconstructed if total_delta_lnB is None else float(total_delta_lnB)
    residual = float(total - reconstructed)
    denom = max(abs(total), 1e-3)
    consistent = abs(residual) / denom <= consistency_tolerance
    return RedshiftTomographyReport(
        model_label=model_label,
        slices=tuple(slices),
        total_delta_lnB=total,
        reconstructed_delta_lnB=reconstructed,
        residual_delta_lnB=residual,
        consistent_with_total=bool(consistent),
        consistency_tolerance=float(consistency_tolerance),
    )


def to_mio_certificate(
    report: RedshiftTomographyReport,
    *,
    channel: str = "redshift_tomography",
    domain_caveats: Optional[Sequence[str]] = None,
    generated_by: str = "mio.decomposition.redshift_tomography v0.1",
    input_data_hashes: Optional[Sequence[str]] = None,
    config_hash: Optional[str] = None,
) -> MioCertificate:
    """Pack a redshift decomposition report into a ``MioCertificate``."""
    strongest = max(report.slices, key=lambda item: abs(item.delta_lnB))
    departure = {
        "total_delta_lnB": float(report.total_delta_lnB),
        "reconstructed_delta_lnB": float(report.reconstructed_delta_lnB),
        "strongest_slice_delta_lnB": float(strongest.delta_lnB),
        "n_slices": float(len(report.slices)),
    }
    adequacy = {
        "sum_rule_within_tolerance": bool(report.consistent_with_total),
    }
    consistency = {
        "residual_delta_lnB": float(report.residual_delta_lnB),
        "consistency_tolerance": float(report.consistency_tolerance),
    }
    for item in report.slices:
        key = item.label.lower().replace("-", "_")
        consistency[f"{key}_delta_lnB"] = float(item.delta_lnB)
        consistency[f"{key}_z_min"] = float(item.z_min)
        consistency[f"{key}_z_max"] = float(item.z_max)

    caveats = list(domain_caveats) if domain_caveats is not None else []
    if DEFAULT_DOMAIN_CAVEAT not in caveats:
        caveats.append(DEFAULT_DOMAIN_CAVEAT)

    return build_mio_certificate(
        report_type="evidence_anatomy",
        probe_name=report.model_label,
        channel=channel,
        departure_variables=departure,
        adequacy_indicators=adequacy,
        consistency_metrics=consistency,
        domain_caveats=caveats,
        reduction_status="diagnostic-only",
        generated_by=generated_by,
        input_data_hashes=list(input_data_hashes) if input_data_hashes else [],
        config_hash=config_hash,
        htt_cross_check_suggested={
            "compare_to": "htt.core.advanced_diagnostics.redshift_tomography_report_artifact",
            "expected_relation": "HTT and MIO redshift slicing should agree on the dominant era",
        },
    )


REDSHIFT_ARTEFACT_FILENAME = "mio_redshift_evidence_tomo_v1.json"


def emit_redshift_tomography_artefact(
    out_path: Path,
    slices: Sequence[RedshiftEvidenceSlice],
    *,
    model_label: str = "FLRW_vs_BianchiI",
    total_delta_lnB: Optional[float] = None,
    consistency_tolerance: float = 0.10,
    domain_caveats: Optional[Sequence[str]] = None,
    input_data_hashes: Optional[Sequence[str]] = None,
) -> dict:
    """Persist a JSON artifact for coarse redshift evidence slices."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if not out_path.name.startswith("mio_"):
        raise ValueError(
            f"artefact filename must start with 'mio_' (REG-02): got {out_path.name}"
        )

    report = summarize_redshift_tomography(
        slices,
        model_label=model_label,
        total_delta_lnB=total_delta_lnB,
        consistency_tolerance=consistency_tolerance,
    )
    cert = to_mio_certificate(
        report,
        domain_caveats=domain_caveats,
        input_data_hashes=input_data_hashes,
    )

    payload = {
        "schema_version": "v1",
        "report": {
            "model_label": report.model_label,
            "slices": [asdict(item) for item in report.slices],
            "total_delta_lnB": report.total_delta_lnB,
            "reconstructed_delta_lnB": report.reconstructed_delta_lnB,
            "residual_delta_lnB": report.residual_delta_lnB,
            "consistent_with_total": report.consistent_with_total,
            "consistency_tolerance": report.consistency_tolerance,
        },
        "certificate": {
            "report_type": cert.report_type,
            "probe_name": cert.probe_name,
            "channel": cert.channel,
            "departure_variables": cert.departure_variables,
            "adequacy_indicators": cert.adequacy_indicators,
            "consistency_metrics": cert.consistency_metrics,
            "domain_caveats": cert.domain_caveats,
            "reduction_status": cert.reduction_status,
            "generated_by": cert.generated_by,
            "git_commit": cert.git_commit,
            "config_hash": cert.config_hash,
        },
    }
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


__all__ = [
    "DEFAULT_DOMAIN_CAVEAT",
    "REDSHIFT_ARTEFACT_FILENAME",
    "RedshiftEvidenceSlice",
    "RedshiftTomographyReport",
    "emit_redshift_tomography_artefact",
    "summarize_redshift_tomography",
    "to_mio_certificate",
]
