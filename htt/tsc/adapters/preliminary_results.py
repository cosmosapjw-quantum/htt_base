"""TSC-facing loaders for VER2 preliminary-result packs."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from common.contracts import TscAdequacyOverlay
from tsc.adapters.bass_runtime import SourceAdequacySuggestion, overlay_to_bass_suggestion
from tsc.adapters.htt_inference import HttTscCaveatBundle, overlay_to_htt_caveats
from workspace.contracts.preliminary_results import (
    load_exported_tsc_overlay,
    load_preliminary_result_pack,
)


@dataclass(frozen=True)
class PreliminaryTscHandoff:
    """TSC overlay plus downstream advisory views from generated exports."""

    overlay: TscAdequacyOverlay
    bass_suggestion: SourceAdequacySuggestion
    htt_caveats: HttTscCaveatBundle
    pack_ids: tuple[str, ...]


def build_preliminary_tsc_handoff(
    *,
    generated_root: str | Path | None = None,
    required_channels: tuple[str, ...] = ("TT", "TE", "EE"),
    uses_scalar_only_geometry: bool = False,
) -> PreliminaryTscHandoff:
    pack_c = load_preliminary_result_pack("C", generated_root=generated_root)
    pack_d = load_preliminary_result_pack("D", generated_root=generated_root)
    overlay = load_exported_tsc_overlay(generated_root=generated_root)
    overlay_ref = overlay.manifest.artifact_id
    return PreliminaryTscHandoff(
        overlay=overlay,
        bass_suggestion=overlay_to_bass_suggestion(
            overlay,
            required_channels=required_channels,
            overlay_ref=overlay_ref,
        ),
        htt_caveats=overlay_to_htt_caveats(
            overlay,
            required_channels=required_channels,
            uses_scalar_only_geometry=uses_scalar_only_geometry,
            overlay_ref=overlay_ref,
        ),
        pack_ids=(pack_c.pack_id, pack_d.pack_id),
    )


__all__ = ["PreliminaryTscHandoff", "build_preliminary_tsc_handoff"]
