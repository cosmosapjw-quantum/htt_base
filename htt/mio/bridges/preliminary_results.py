"""MIO loaders for VER2 preliminary-result packs."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from common.contracts import TscAdequacyOverlay
from workspace.contracts.mio_certificate import MioCertificate
from workspace.contracts.preliminary_results import (
    PreliminaryResultPack,
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
    claim_tier: str
    production_status: str
    caveats: tuple[str, ...]
    artifact_ids: tuple[str, ...]


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
    certificate = load_exported_mio_certificate(generated_root=generated_root)
    overlay = load_exported_tsc_overlay(generated_root=generated_root)
    _validate_preliminary_mio_handoff(
        pack_d,
        certificate=certificate,
        overlay=overlay,
    )
    return PreliminaryMioHandoff(
        certificate=certificate,
        overlay=overlay,
        pack_id=pack_d.pack_id,
        claim_tier=pack_d.claim_tier,
        production_status=pack_d.production_status,
        caveats=pack_d.caveats,
        artifact_ids=pack_d.artifact_ids(),
    )


__all__ = ["PreliminaryMioHandoff", "build_preliminary_mio_handoff"]
