"""MIO loaders for VER2 preliminary-result packs."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from common.contracts import TscAdequacyOverlay
from workspace.contracts.mio_certificate import MioCertificate
from workspace.contracts.preliminary_results import (
    MIO_CERTIFICATE_ARTIFACT_ID,
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
    pack_id: str
    topic: str
    claim_tier: str
    production_status: str
    caveats: tuple[str, ...]
    summary_lines: tuple[str, ...]
    artifact_ids: tuple[str, ...]


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
) -> None:
    if certificate.manifest is None:
        raise ValueError("preliminary MIO handoff requires a manifest-backed certificate")
    certificate_id = certificate.manifest.artifact_id
    overlay_id = overlay.manifest.artifact_id
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
    _validate_preliminary_mio_handoff(
        pack_d,
        certificate=certificate,
        overlay=overlay,
    )
    return PreliminaryMioHandoff(
        certificate=certificate,
        overlay=overlay,
        pack_id=pack_d.pack_id,
        topic=pack_d.topic,
        claim_tier=pack_d.claim_tier,
        production_status=pack_d.production_status,
        caveats=pack_d.caveats,
        summary_lines=pack_d.summary_lines,
        artifact_ids=pack_d.artifact_ids(),
    )


__all__ = ["PreliminaryMioHandoff", "build_preliminary_mio_handoff"]
