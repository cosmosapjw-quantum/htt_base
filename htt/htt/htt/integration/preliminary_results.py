"""HTT loaders for manifest-backed VER2 preliminary-result packs."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from common.contracts import DiscriminationMatrix
from htt.integration.from_bass import ingest_ver2_directional_inputs
from htt.infer.likelihood_scope_guard import DirectionalLikelihoodInput
from workspace.contracts.preliminary_results import (
    PreliminaryResultPack,
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
    packs: tuple[PreliminaryResultPack, ...] = ()

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

    @property
    def pair_degeneracy_flags(self) -> dict[str, bool]:
        stats = self.discrimination_matrix.manifest.statistics_definitions
        mapping = stats.get("pair_degeneracy_flags", {})
        if isinstance(mapping, dict) and mapping:
            return {str(key): bool(value) for key, value in mapping.items()}
        if self.discrimination_matrix.degeneracy_flags:
            return {
                str(key): bool(value)
                for key, value in self.discrimination_matrix.degeneracy_flags.items()
            }
        overlap = np.asarray(self.discrimination_matrix.overlap_matrix, dtype=float)
        index_by_hypothesis = {
            name: idx for idx, name in enumerate(self.discrimination_matrix.hypotheses)
        }
        derived: dict[str, bool] = {}
        for pair, tier in sorted(self.pair_claim_tier.items()):
            left, right = pair.split("|", 1)
            left_index = index_by_hypothesis.get(left)
            right_index = index_by_hypothesis.get(right)
            if left_index is None or right_index is None:
                derived[pair] = tier != "conditional"
                continue
            rho = float(overlap[left_index, right_index])
            derived[pair] = (not np.isfinite(rho)) or abs(rho) >= 0.9
        return derived

    @property
    def pair_recommended_next_observable(self) -> dict[str, str]:
        stats = self.discrimination_matrix.manifest.statistics_definitions
        mapping = stats.get("pair_recommended_next_observable", {})
        if isinstance(mapping, dict) and mapping:
            return {str(key): str(value) for key, value in mapping.items()}
        return {
            str(key): str(value)
            for key, value in self.discrimination_matrix.recommended_next_observable.items()
        }

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
        packs=(pack_a, pack_b, pack_d),
    )


__all__ = ["PreliminaryDirectionalHandoff", "build_preliminary_directional_handoff"]
