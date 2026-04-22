"""HTT loaders for manifest-backed VER2 preliminary-result packs."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from common.contracts import DiscriminationMatrix
from htt.integration.from_bass import ingest_ver2_directional_inputs
from htt.infer.likelihood_scope_guard import DirectionalLikelihoodInput
from workspace.contracts.preliminary_results import (
    load_exported_atlas_entry_lite,
    load_exported_discrimination_matrix,
    load_exported_observable_vector,
    load_exported_tsc_overlay,
    load_preliminary_result_pack,
)


@dataclass(frozen=True)
class PreliminaryDirectionalHandoff:
    """Preliminary-results HTT bundle loaded from generated VER2 exports."""

    likelihood_input: DirectionalLikelihoodInput
    discrimination_matrix: DiscriminationMatrix
    pack_ids: tuple[str, ...]

    @property
    def support_profile(self) -> dict[str, float]:
        stats = self.discrimination_matrix.manifest.statistics_definitions
        profile = stats.get("support_profile", {})
        if not isinstance(profile, dict):
            return {}
        return {str(key): float(value) for key, value in profile.items()}

    @property
    def pair_claim_tier(self) -> dict[str, str]:
        stats = self.discrimination_matrix.manifest.statistics_definitions
        mapping = stats.get("pair_claim_tier", {})
        if isinstance(mapping, dict) and mapping:
            return {str(key): str(value) for key, value in mapping.items()}
        return {
            str(key): str(value)
            for key, value in self.discrimination_matrix.claim_tier_by_pair.items()
        }

    @property
    def conditional_pairs(self) -> tuple[str, ...]:
        stats = self.discrimination_matrix.manifest.statistics_definitions
        pairs = stats.get("conditional_pairs", ())
        if isinstance(pairs, (list, tuple)) and pairs:
            return tuple(str(pair) for pair in pairs)
        return tuple(
            pair for pair, tier in sorted(self.pair_claim_tier.items()) if tier == "conditional"
        )

    @property
    def blocked_pairs(self) -> tuple[str, ...]:
        stats = self.discrimination_matrix.manifest.statistics_definitions
        pairs = stats.get("blocked_pairs", ())
        if isinstance(pairs, (list, tuple)) and pairs:
            return tuple(str(pair) for pair in pairs)
        return tuple(
            pair for pair, tier in sorted(self.pair_claim_tier.items()) if tier == "blocked"
        )


def build_preliminary_directional_handoff(
    *,
    generated_root: str | Path | None = None,
    required_channels: tuple[str, ...] = ("TT",),
    scalar_only_geometry: bool = False,
    matched_complexity_ready: bool = False,
    null_competition_ready: bool = False,
) -> PreliminaryDirectionalHandoff:
    pack_a = load_preliminary_result_pack("A", generated_root=generated_root)
    pack_b = load_preliminary_result_pack("B", generated_root=generated_root)
    pack_d = load_preliminary_result_pack("D", generated_root=generated_root)

    observable_vector = load_exported_observable_vector(generated_root=generated_root)
    atlas_entry = load_exported_atlas_entry_lite(generated_root=generated_root)
    overlay = load_exported_tsc_overlay(generated_root=generated_root)
    discrimination_matrix = load_exported_discrimination_matrix(
        generated_root=generated_root
    )

    likelihood_input = ingest_ver2_directional_inputs(
        observable_vector=observable_vector,
        atlas_entry=atlas_entry,
        tsc_overlay=overlay,
        required_channels=required_channels,
        scalar_only_geometry=scalar_only_geometry,
        matched_complexity_ready=matched_complexity_ready,
        null_competition_ready=null_competition_ready,
    )
    return PreliminaryDirectionalHandoff(
        likelihood_input=likelihood_input,
        discrimination_matrix=discrimination_matrix,
        pack_ids=(pack_a.pack_id, pack_b.pack_id, pack_d.pack_id),
    )


__all__ = ["PreliminaryDirectionalHandoff", "build_preliminary_directional_handoff"]
