"""MIO loaders for VER2 preliminary-result packs."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from common.contracts import TscAdequacyOverlay
from workspace.contracts.mio_certificate import MioCertificate
from workspace.contracts.preliminary_results import (
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


def build_preliminary_mio_handoff(
    *,
    generated_root: str | Path | None = None,
) -> PreliminaryMioHandoff:
    pack_d = load_preliminary_result_pack("D", generated_root=generated_root)
    certificate = load_exported_mio_certificate(generated_root=generated_root)
    overlay = load_exported_tsc_overlay(generated_root=generated_root)
    return PreliminaryMioHandoff(
        certificate=certificate,
        overlay=overlay,
        pack_id=pack_d.pack_id,
    )


__all__ = ["PreliminaryMioHandoff", "build_preliminary_mio_handoff"]
