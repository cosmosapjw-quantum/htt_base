"""mio.decomposition.evidence_anatomy — HJ-04 channel decomposition."""
from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping, Optional, Sequence

from mio.interface.manifest import MioPrerequisites, assess_mio_readiness
from mio.interface.mio_certificate import build_mio_certificate, certificate_to_payload
from workspace.contracts.mio_certificate import MioCertificate


DEFAULT_DOMAIN_CAVEAT = (
    "Evidence anatomy consumes HTT-produced evidence deltas and must not "
    "be reinterpreted as an MIO truth score."
)


@dataclass(frozen=True)
class EvidenceAnatomyContribution:
    """One channel's contribution to the total ``Δln B``."""

    name: str
    delta_lnB: float
    share_of_total: float
    sign_matches_total: bool


@dataclass(frozen=True)
class EvidenceAnatomyReport:
    """Channel-by-channel evidence decomposition summary."""

    model_label: str
    contributions: tuple[EvidenceAnatomyContribution, ...]
    total_delta_lnB: float
    reconstructed_delta_lnB: float
    residual_delta_lnB: float
    relative_residual: float
    consistency_tolerance: float
    consistent_with_total: bool


def summarize_evidence_anatomy(
    channel_contributions: Mapping[str, float],
    *,
    model_label: str = "FLRW_vs_BianchiI",
    total_delta_lnB: Optional[float] = None,
    consistency_tolerance: float = 0.10,
    residual_floor: float = 1e-3,
) -> EvidenceAnatomyReport:
    """Summarize a channel-by-channel ``Δln B`` decomposition."""
    if not channel_contributions:
        raise ValueError("channel_contributions must contain at least one channel")
    if consistency_tolerance < 0.0:
        raise ValueError("consistency_tolerance must be >= 0")
    if residual_floor <= 0.0:
        raise ValueError("residual_floor must be > 0")

    reconstructed = float(sum(float(v) for v in channel_contributions.values()))
    total = reconstructed if total_delta_lnB is None else float(total_delta_lnB)
    residual = float(total - reconstructed)
    denom = max(abs(total), residual_floor)
    relative = abs(residual) / denom

    contribs = []
    for name in sorted(channel_contributions):
        value = float(channel_contributions[name])
        share = value / total if abs(total) >= residual_floor else 0.0
        sign_matches = math.copysign(1.0, value or 0.0) == math.copysign(1.0, total or 0.0)
        contribs.append(
            EvidenceAnatomyContribution(
                name=name,
                delta_lnB=value,
                share_of_total=float(share),
                sign_matches_total=bool(sign_matches),
            )
        )

    return EvidenceAnatomyReport(
        model_label=model_label,
        contributions=tuple(contribs),
        total_delta_lnB=total,
        reconstructed_delta_lnB=reconstructed,
        residual_delta_lnB=residual,
        relative_residual=float(relative),
        consistency_tolerance=float(consistency_tolerance),
        consistent_with_total=bool(relative <= consistency_tolerance),
    )


def to_mio_certificate(
    report: EvidenceAnatomyReport,
    *,
    channel: str = "channel_decomposition",
    domain_caveats: Optional[Sequence[str]] = None,
    generated_by: str = "mio.decomposition.evidence_anatomy v0.1",
    input_data_hashes: Optional[Sequence[str]] = None,
    config_hash: Optional[str] = None,
    artifact_path: str = "artifacts/mio/mio_evidence_anatomy_v1.json",
) -> MioCertificate:
    """Pack a decomposition report into a ``MioCertificate``."""
    strongest = max(report.contributions, key=lambda item: abs(item.delta_lnB))
    departure = {
        "total_delta_lnB": float(report.total_delta_lnB),
        "reconstructed_delta_lnB": float(report.reconstructed_delta_lnB),
        "strongest_channel_delta_lnB": float(strongest.delta_lnB),
        "n_channels": float(len(report.contributions)),
    }
    adequacy = {
        "sum_rule_within_tolerance": bool(report.consistent_with_total),
        "residual_lt_10pct": bool(report.relative_residual <= 0.10),
    }
    consistency = {
        "residual_delta_lnB": float(report.residual_delta_lnB),
        "relative_residual": float(report.relative_residual),
        "consistency_tolerance": float(report.consistency_tolerance),
    }
    for item in report.contributions:
        key = item.name.lower()
        consistency[f"{key}_delta_lnB"] = float(item.delta_lnB)
        consistency[f"{key}_share"] = float(item.share_of_total)

    caveats = list(domain_caveats) if domain_caveats is not None else []
    if DEFAULT_DOMAIN_CAVEAT not in caveats:
        caveats.append(DEFAULT_DOMAIN_CAVEAT)
    readiness = assess_mio_readiness(MioPrerequisites(eligible_for_production=False))

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
            "compare_to": "htt.core.analysis_extended.evidence_matrix_report_artifact",
            "expected_relation": "channel contributions should reconstruct the HTT total evidence within tolerance",
        },
        readiness=readiness,
        artifact_id="mio.evidence_anatomy.certificate",
        artifact_path=artifact_path,
        statistics_definitions={
            "report_type": "evidence_anatomy",
            "channel": channel,
        },
    )


ARTEFACT_FILENAME = "mio_evidence_anatomy_v1.json"


def emit_evidence_anatomy_artefact(
    out_path: Path,
    channel_contributions: Mapping[str, float],
    *,
    model_label: str = "FLRW_vs_BianchiI",
    total_delta_lnB: Optional[float] = None,
    consistency_tolerance: float = 0.10,
    residual_floor: float = 1e-3,
    domain_caveats: Optional[Sequence[str]] = None,
    input_data_hashes: Optional[Sequence[str]] = None,
) -> dict:
    """Persist a JSON artifact for channel-by-channel evidence anatomy."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if not out_path.name.startswith("mio_"):
        raise ValueError(
            f"artefact filename must start with 'mio_' (REG-02): got {out_path.name}"
        )

    report = summarize_evidence_anatomy(
        channel_contributions,
        model_label=model_label,
        total_delta_lnB=total_delta_lnB,
        consistency_tolerance=consistency_tolerance,
        residual_floor=residual_floor,
    )
    cert = to_mio_certificate(
        report,
        domain_caveats=domain_caveats,
        input_data_hashes=input_data_hashes,
        artifact_path=str(out_path),
    )

    payload = {
        "schema_version": "v1",
        "report": {
            "model_label": report.model_label,
            "contributions": [asdict(item) for item in report.contributions],
            "total_delta_lnB": report.total_delta_lnB,
            "reconstructed_delta_lnB": report.reconstructed_delta_lnB,
            "residual_delta_lnB": report.residual_delta_lnB,
            "relative_residual": report.relative_residual,
            "consistency_tolerance": report.consistency_tolerance,
            "consistent_with_total": report.consistent_with_total,
        },
        "certificate": certificate_to_payload(cert),
    }
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


__all__ = [
    "ARTEFACT_FILENAME",
    "DEFAULT_DOMAIN_CAVEAT",
    "EvidenceAnatomyContribution",
    "EvidenceAnatomyReport",
    "emit_evidence_anatomy_artefact",
    "summarize_evidence_anatomy",
    "to_mio_certificate",
]
