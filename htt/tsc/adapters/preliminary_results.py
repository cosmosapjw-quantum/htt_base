"""TSC-facing loaders for VER2 preliminary-result packs."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from common.contracts import TscAdequacyOverlay
from tsc.adapters.bass_runtime import SourceAdequacySuggestion, overlay_to_bass_suggestion
from tsc.adapters.htt_inference import HttTscCaveatBundle, overlay_to_htt_caveats
from workspace.contracts.preliminary_results import (
    PreliminaryResultPack,
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
    packs: tuple[PreliminaryResultPack, ...] = ()

    @property
    def pack_index(self) -> dict[str, PreliminaryResultPack]:
        return {pack.pack_id: pack for pack in self.packs}

    @property
    def pack_claim_tiers(self) -> dict[str, str]:
        return {
            pack_id: pack.claim_tier
            for pack_id, pack in sorted(self.pack_index.items())
        }

    @property
    def pack_production_statuses(self) -> dict[str, str]:
        return {
            pack_id: pack.production_status
            for pack_id, pack in sorted(self.pack_index.items())
        }

    @property
    def pack_summary_lines(self) -> dict[str, tuple[str, ...]]:
        return {
            pack_id: tuple(pack.summary_lines)
            for pack_id, pack in sorted(self.pack_index.items())
        }

    @property
    def pack_artifact_ids(self) -> dict[str, tuple[str, ...]]:
        return {
            pack_id: pack.artifact_ids()
            for pack_id, pack in sorted(self.pack_index.items())
        }


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
        packs=(pack_c, pack_d),
    )


__all__ = ["PreliminaryTscHandoff", "build_preliminary_tsc_handoff"]
