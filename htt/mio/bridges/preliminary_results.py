"""MIO loaders for VER2 preliminary-result packs."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from common.contracts import TscAdequacyOverlay
from tsc.adapters.mio_certificate import MioTscAdequacyFields, overlay_to_mio_fields
from workspace.contracts.mio_certificate import MioCertificate
from workspace.contracts.preliminary_results import (
    MIO_CERTIFICATE_ARTIFACT_ID,
    PreliminaryPackArtifactRef,
    PreliminaryResultPack,
    TSC_OVERLAY_ARTIFACT_ID,
    load_exported_mio_certificate,
    load_exported_tsc_overlay,
    load_preliminary_result_pack,
)


@dataclass(frozen=True)
class PreliminaryMioHandoff:
    """MIO-facing preliminary-results handoff bundle."""

    certificate: MioCertificate
    overlay: TscAdequacyOverlay
    pack: PreliminaryResultPack
    pack_id: str
    topic: str
    claim_tier: str
    production_status: str
    caveats: tuple[str, ...]
    summary_lines: tuple[str, ...]
    artifact_ids: tuple[str, ...]
    tsc_required_channels: tuple[str, ...]
    tsc_publication_blockers: tuple[str, ...]
    tsc_claim_ceiling: dict[str, str]
    tsc_trace_source_adequacy: str
    tsc_consistency_issues: tuple[str, ...]

    @property
    def artifact_index(self) -> dict[str, PreliminaryPackArtifactRef]:
        return {
            artifact.artifact_id: artifact
            for artifact in self.pack.artifacts
        }

    @property
    def artifact_claim_tiers(self) -> dict[str, str]:
        return {
            artifact_id: artifact.claim_tier
            for artifact_id, artifact in sorted(self.artifact_index.items())
        }

    @property
    def artifact_production_statuses(self) -> dict[str, str]:
        return {
            artifact_id: artifact.production_status
            for artifact_id, artifact in sorted(self.artifact_index.items())
        }

    @property
    def artifact_summaries(self) -> dict[str, str]:
        return {
            artifact_id: artifact.summary
            for artifact_id, artifact in sorted(self.artifact_index.items())
        }


def _certificate_tsc_publication_blockers(
    certificate: MioCertificate,
) -> tuple[str, ...]:
    prefix = "tsc_publication_blocker="
    return tuple(
        caveat[len(prefix) :]
        for caveat in certificate.domain_caveats
        if caveat.startswith(prefix)
    )


def _certificate_tsc_trace_source_adequacy(
    certificate: MioCertificate,
) -> str | None:
    prefix = "tsc_trace_source_adequacy="
    for caveat in certificate.domain_caveats:
        if caveat.startswith(prefix):
            return caveat[len(prefix) :]
    return None


def _certificate_tsc_claim_ceiling(
    certificate: MioCertificate,
) -> dict[str, str]:
    prefix = "tsc_claim_ceiling:"
    ceilings: dict[str, str] = {}
    for caveat in certificate.channel_caveats:
        if not caveat.startswith(prefix):
            continue
        payload = caveat[len(prefix) :]
        channel, sep, ceiling = payload.partition("=")
        if not sep or not channel or not ceiling:
            raise ValueError(f"invalid tsc claim ceiling caveat {caveat!r}")
        ceilings[channel] = ceiling
    return ceilings


def _tsc_certificate_consistency_issues(
    certificate: MioCertificate,
    fields: MioTscAdequacyFields,
) -> tuple[str, ...]:
    issues: list[str] = []
    if _certificate_tsc_publication_blockers(certificate) != fields.publication_blockers:
        issues.append("tsc_publication_blockers_mismatch")
    if _certificate_tsc_claim_ceiling(certificate) != fields.channel_claim_ceiling:
        issues.append("tsc_claim_ceiling_mismatch")
    if _certificate_tsc_trace_source_adequacy(certificate) != fields.trace_source_adequacy:
        issues.append("tsc_trace_source_adequacy_mismatch")
    if bool(certificate.adequacy_indicators.get("tsc_overlay_diagnostic_only")) != fields.diagnostic_only:
        issues.append("tsc_diagnostic_only_flag_mismatch")
    return tuple(issues)


def _require_pack_artifact(
    pack: PreliminaryResultPack,
    *,
    artifact_id: str,
    owner: str,
):
    for artifact in pack.artifacts:
        if artifact.artifact_id == artifact_id:
            if artifact.owner != owner:
                raise ValueError(
                    f"pack {pack.pack_id} artifact {artifact_id!r} must be owned by "
                    f"{owner!r} (got {artifact.owner!r})"
                )
            return artifact
    raise ValueError(
        f"pack {pack.pack_id} does not contain required artifact {artifact_id!r}"
    )


def _validate_preliminary_mio_handoff(
    pack_d: PreliminaryResultPack,
    *,
    certificate: MioCertificate,
    overlay: TscAdequacyOverlay,
) -> MioTscAdequacyFields:
    if certificate.manifest is None:
        raise ValueError("preliminary MIO handoff requires a manifest-backed certificate")
    certificate_id = certificate.manifest.artifact_id
    overlay_id = overlay.manifest.artifact_id
    fields = overlay_to_mio_fields(overlay)
    artifact_ids = pack_d.artifact_ids()
    if certificate_id not in artifact_ids:
        raise ValueError(
            "pack D does not reference the exported MIO certificate artifact "
            f"{certificate_id!r}"
        )
    if overlay_id not in artifact_ids:
        raise ValueError(
            "pack D does not reference the exported TSC overlay artifact "
            f"{overlay_id!r}"
        )
    if certificate.tsc_overlay_ref != overlay_id:
        raise ValueError(
            "exported MIO certificate overlay ref does not match the exported TSC overlay "
            f"({certificate.tsc_overlay_ref!r} != {overlay_id!r})"
        )
    return fields


def build_preliminary_mio_handoff(
    *,
    generated_root: str | Path | None = None,
) -> PreliminaryMioHandoff:
    pack_d = load_preliminary_result_pack("D", generated_root=generated_root)
    certificate_ref = _require_pack_artifact(
        pack_d,
        artifact_id=MIO_CERTIFICATE_ARTIFACT_ID,
        owner="MIO",
    )
    overlay_ref = _require_pack_artifact(
        pack_d,
        artifact_id=TSC_OVERLAY_ARTIFACT_ID,
        owner="TSC",
    )
    certificate = load_exported_mio_certificate(
        artifact_id_or_path=certificate_ref.artifact_id,
        generated_root=generated_root,
    )
    overlay = load_exported_tsc_overlay(
        artifact_id_or_path=overlay_ref.artifact_id,
        generated_root=generated_root,
    )
    fields = _validate_preliminary_mio_handoff(
        pack_d,
        certificate=certificate,
        overlay=overlay,
    )
    return PreliminaryMioHandoff(
        certificate=certificate,
        overlay=overlay,
        pack=pack_d,
        pack_id=pack_d.pack_id,
        topic=pack_d.topic,
        claim_tier=pack_d.claim_tier,
        production_status=pack_d.production_status,
        caveats=pack_d.caveats,
        summary_lines=pack_d.summary_lines,
        artifact_ids=pack_d.artifact_ids(),
        tsc_required_channels=fields.required_channels,
        tsc_publication_blockers=fields.publication_blockers,
        tsc_claim_ceiling=fields.channel_claim_ceiling,
        tsc_trace_source_adequacy=fields.trace_source_adequacy,
        tsc_consistency_issues=_tsc_certificate_consistency_issues(
            certificate,
            fields,
        ),
    )


__all__ = ["PreliminaryMioHandoff", "build_preliminary_mio_handoff"]
