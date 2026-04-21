"""JSON/markdown export and artifact-attachment helpers for TSC overlays."""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, replace
import json

from common.contracts import FullCovMESReport, TscAdequacyOverlay
from common.departure_contracts import DepartureReport
from workspace.contracts.mio_certificate import MioCertificate


_DEFAULT_EXPORT_CHANNELS = ("TT", "TE", "EE")


def _required_budgets(
    overlay: TscAdequacyOverlay,
    *,
    required_channels: Sequence[str],
) -> tuple:
    required = set(required_channels)
    return tuple(
        budget for budget in overlay.channel_budgets if budget.channel in required
    )


def overlay_publication_blockers(
    overlay: TscAdequacyOverlay,
    *,
    required_channels: Sequence[str] = _DEFAULT_EXPORT_CHANNELS,
) -> tuple[str, ...]:
    blockers = list(overlay.quarantine_reasons)
    if overlay.domain_report.status == "invalid_domain":
        blockers.append("invalid_domain")

    source_report = overlay.source_bridge_report
    if source_report is None:
        blockers.append("source_bridge_missing")
    elif source_report.source_status != "adequate":
        blockers.append(f"source_status:{source_report.source_status}")

    required_budgets = _required_budgets(
        overlay,
        required_channels=required_channels,
    )
    if required_budgets:
        pending_channels = sorted(
            budget.channel for budget in required_budgets if budget.propagation_status != "validated"
        )
        if pending_channels:
            blockers.append("propagation_pending:" + ",".join(pending_channels))
        claim_limited = sorted(
            f"{budget.channel}={budget.claim_ceiling}"
            for budget in required_budgets
            if budget.claim_ceiling not in {"conditional", "validated"}
        )
        if claim_limited:
            blockers.append("claim_ceiling_insufficient:" + ",".join(claim_limited))

    return tuple(dict.fromkeys(blockers))


def overlay_is_publication_ready(
    overlay: TscAdequacyOverlay,
    *,
    required_channels: Sequence[str] = _DEFAULT_EXPORT_CHANNELS,
) -> bool:
    return not overlay_publication_blockers(
        overlay,
        required_channels=required_channels,
    )


def overlay_to_json_dict(
    overlay: TscAdequacyOverlay,
    *,
    required_channels: Sequence[str] = _DEFAULT_EXPORT_CHANNELS,
) -> dict[str, object]:
    blockers = overlay_publication_blockers(
        overlay,
        required_channels=required_channels,
    )
    payload = asdict(overlay)
    payload["publication_ready"] = not blockers
    payload["publication_blockers"] = blockers
    payload["required_channels"] = tuple(required_channels)
    payload["channel_claim_ceiling"] = {
        budget.channel: budget.claim_ceiling for budget in overlay.channel_budgets
    }
    return payload


def overlay_to_json(
    overlay: TscAdequacyOverlay,
    *,
    required_channels: Sequence[str] = _DEFAULT_EXPORT_CHANNELS,
) -> str:
    return json.dumps(
        overlay_to_json_dict(overlay, required_channels=required_channels),
        indent=2,
        sort_keys=True,
        default=str,
    )


def overlay_to_markdown(
    overlay: TscAdequacyOverlay,
    *,
    required_channels: Sequence[str] = _DEFAULT_EXPORT_CHANNELS,
) -> str:
    blockers = overlay_publication_blockers(
        overlay,
        required_channels=required_channels,
    )
    budgets = ", ".join(
        f"{budget.channel}:{budget.source_status}/{budget.propagation_status}/{budget.claim_ceiling}"
        for budget in overlay.channel_budgets
    ) or "none"
    blocker_text = ", ".join(blockers) if blockers else "none"
    required_text = ", ".join(required_channels) if required_channels else "none"
    return "\n".join(
        (
            "# TSC Adequacy Overlay",
            "",
            f"- artifact: `{overlay.manifest.artifact_id}`",
            f"- public snippet: {overlay.public_caveat_snippet}",
            f"- required channels: `{required_text}`",
            f"- budgets: `{budgets}`",
            f"- publication blockers: `{blocker_text}`",
        )
    )


def _overlay_ref(overlay: TscAdequacyOverlay) -> str:
    return overlay.manifest.artifact_id


def attach_overlay_to_departure_report(
    report: DepartureReport,
    overlay: TscAdequacyOverlay,
) -> DepartureReport:
    caveats = list(report.caveats)
    if overlay.public_caveat_snippet not in caveats:
        caveats.append(overlay.public_caveat_snippet)
    return replace(
        report,
        caveats=caveats,
        tsc_overlay_ref=_overlay_ref(overlay),
    )


def attach_overlay_to_mes_report(
    report: FullCovMESReport,
    overlay: TscAdequacyOverlay,
) -> FullCovMESReport:
    return replace(report, tsc_overlay_ref=_overlay_ref(overlay))


def attach_overlay_to_mio_certificate(
    certificate: MioCertificate,
    overlay: TscAdequacyOverlay,
) -> MioCertificate:
    domain_caveats = list(certificate.domain_caveats)
    if overlay.public_caveat_snippet not in domain_caveats:
        domain_caveats.append(overlay.public_caveat_snippet)
    return replace(
        certificate,
        domain_caveats=domain_caveats,
        tsc_overlay_ref=_overlay_ref(overlay),
    )


__all__ = [
    "attach_overlay_to_departure_report",
    "attach_overlay_to_mes_report",
    "attach_overlay_to_mio_certificate",
    "overlay_is_publication_ready",
    "overlay_publication_blockers",
    "overlay_to_json",
    "overlay_to_json_dict",
    "overlay_to_markdown",
]
