"""Directional likelihood-input skeleton and scope guards for VER2 HTT."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from common.contracts import (
    AtlasEntryLite,
    ObservableVector,
    PreferredAxis,
    TscAdequacyOverlay,
)
from htt.infer.matched_complexity import (
    MatchedComplexityHook,
    build_matched_complexity_hook,
)
from htt.infer.null_competition import (
    NullCompetitionHook,
    build_null_competition_hook,
)
from tsc.adapters.htt_inference import HttTscCaveatBundle, overlay_to_htt_caveats
from workspace.contracts.mio_certificate import MioCertificate

__all__ = [
    "DirectionalLikelihoodInput",
    "LikelihoodScopeDecision",
    "build_directional_likelihood_input",
    "evaluate_likelihood_scope",
    "guard_tsc_posterior_correction",
    "reject_mio_certificate_merge",
]


_MORPHOLOGY_CHANNELS = {"BB", "BiPoSH", "template"}
_SPIN2_CHANNELS = {"EE", "TE"}
_CLAIM_CAVEAT_PREFIXES = ("observable_bridge_", "scalar_summary_")


@dataclass(frozen=True)
class DirectionalLikelihoodInput:
    """Pre-inference HTT likelihood input bundle."""

    observable_vector: ObservableVector
    atlas_entry: AtlasEntryLite | None
    preferred_axis: PreferredAxis | None
    tsc_caveats: HttTscCaveatBundle | None
    required_channels: tuple[str, ...]
    scalar_only_geometry: bool
    matched_complexity_hook: MatchedComplexityHook
    null_competition_hook: NullCompetitionHook
    solver_coupled_ready: bool = False
    caveats: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.observable_vector.manifest.owner != "BASS":
            raise ValueError(
                "DirectionalLikelihoodInput.observable_vector must carry a BASS-owned manifest"
            )
        missing = sorted(set(self.required_channels) - set(self.observable_vector.channels))
        if missing:
            raise ValueError(
                f"DirectionalLikelihoodInput requires unavailable channels: {missing}"
            )
        if self.atlas_entry is not None and self.atlas_entry.manifest.owner != "BASS":
            raise ValueError(
                "DirectionalLikelihoodInput.atlas_entry must carry a BASS-owned manifest"
            )


@dataclass(frozen=True)
class LikelihoodScopeDecision:
    """Closed-fail decision for whether the current HTT shell may proceed."""

    allowed: bool
    blocking_reasons: tuple[str, ...]
    caveats: tuple[str, ...]
    input_bundle: DirectionalLikelihoodInput


def reject_mio_certificate_merge(*artifacts: object) -> None:
    """Reject any attempt to fold MIO certificates into HTT posterior inputs."""

    if any(isinstance(artifact, MioCertificate) for artifact in artifacts):
        raise TypeError(
            "HTT likelihood inputs may not ingest MioCertificate artifacts; "
            "MIO certificates are diagnostic-only and must not merge into HTT posterior/evidence."
        )


def guard_tsc_posterior_correction(*, enabled: bool) -> None:
    """TSC may contribute caveats only, never posterior arithmetic."""

    if enabled:
        raise RuntimeError(
            "TSC posterior correction is disabled by default in HTT; "
            "only caveat/guard consumption is permitted in the H-lane skeleton."
        )


def build_directional_likelihood_input(
    *,
    observable_vector: ObservableVector,
    atlas_entry: AtlasEntryLite | None = None,
    preferred_axis: PreferredAxis | None = None,
    tsc_overlay: TscAdequacyOverlay | None = None,
    required_channels: Iterable[str] = ("TT",),
    scalar_only_geometry: bool = False,
    matched_complexity_hook: MatchedComplexityHook | None = None,
    null_competition_hook: NullCompetitionHook | None = None,
    solver_coupled_ready: bool = False,
    external_artifacts: Iterable[object] = (),
) -> DirectionalLikelihoodInput:
    """Build an HTT-owned, solver-independent directional-input shell."""

    reject_mio_certificate_merge(*tuple(external_artifacts))
    guard_tsc_posterior_correction(enabled=False)
    channels = tuple(required_channels)
    resolved_matched = matched_complexity_hook or build_matched_complexity_hook()
    resolved_null = null_competition_hook or build_null_competition_hook()
    tsc_caveats = (
        overlay_to_htt_caveats(
            tsc_overlay,
            required_channels=channels,
            uses_scalar_only_geometry=scalar_only_geometry,
            overlay_ref=tsc_overlay.manifest.artifact_id,
        )
        if tsc_overlay is not None
        else None
    )
    caveats: list[str] = []
    if scalar_only_geometry:
        caveats.append("scalar_only_discrimination_insufficient")
    if tsc_caveats is not None:
        caveats.extend(tsc_caveats.caveats)
    return DirectionalLikelihoodInput(
        observable_vector=observable_vector,
        atlas_entry=atlas_entry,
        preferred_axis=preferred_axis,
        tsc_caveats=tsc_caveats,
        required_channels=channels,
        scalar_only_geometry=scalar_only_geometry,
        matched_complexity_hook=resolved_matched,
        null_competition_hook=resolved_null,
        solver_coupled_ready=solver_coupled_ready,
        caveats=tuple(dict.fromkeys(caveats)),
    )


def evaluate_likelihood_scope(bundle: DirectionalLikelihoodInput) -> LikelihoodScopeDecision:
    """Evaluate whether the current shell can support the requested HTT scope."""

    blocking: list[str] = []
    caveats = list(bundle.caveats)

    if bundle.preferred_axis is not None:
        if not bundle.preferred_axis.production_allowed:
            blocking.append("axis_not_production_promoted")
        if bundle.preferred_axis.source != "fiducial_posterior":
            blocking.append("axis_wrong_provenance")

    required = set(bundle.required_channels)
    if required & _MORPHOLOGY_CHANNELS and bundle.atlas_entry is None:
        blocking.append("atlas_entry_required_for_morphology")

    if bundle.tsc_caveats is not None:
        validity = bundle.tsc_caveats.channel_validity
        claim_ceiling = bundle.tsc_caveats.channel_claim_ceiling
        channel_labels = bundle.tsc_caveats.channel_labels
        if required & _SPIN2_CHANNELS:
            missing_spin2 = sorted(
                channel
                for channel in required & _SPIN2_CHANNELS
                if validity.get(channel) != "validated"
            )
            if missing_spin2:
                blocking.append(
                    "missing_spin2_validation:" + ",".join(missing_spin2)
                )
        insufficient_claims = sorted(
            channel
            for channel in required - _MORPHOLOGY_CHANNELS
            if claim_ceiling.get(channel) in {"exploratory", "blocked"}
        )
        for channel in insufficient_claims:
            blocking.append(
                f"tsc_claim_ceiling_insufficient:{channel}={claim_ceiling[channel]}"
            )
            caveats.extend(
                label
                for label in channel_labels.get(channel, ())
                if label.startswith(_CLAIM_CAVEAT_PREFIXES)
            )
        if required & _MORPHOLOGY_CHANNELS:
            blocking.append("morphology_requires_external_validation")
            caveats.append("tsc_caveat_only_for_morphology")
    elif required & (_SPIN2_CHANNELS | _MORPHOLOGY_CHANNELS):
        blocking.append("tsc_overlay_missing_for_requested_channels")

    if not bundle.matched_complexity_hook.overall_pass:
        blocking.append("matched_complexity_failed")
    if not bundle.matched_complexity_hook.controls_required:
        caveats.append("matched_complexity_hook_pending")
    if bundle.matched_complexity_hook.scope != "pre_inference_only":
        caveats.append("matched_complexity_scope_unexpected")
    if not bundle.null_competition_hook.ready_for_inference:
        caveats.append("null_competition_hook_pending")
    if bundle.null_competition_hook.scope != "pre_posterior":
        caveats.append("null_competition_scope_unexpected")
    if not bundle.solver_coupled_ready:
        caveats.append("solver_coupled_wiring_pending")

    return LikelihoodScopeDecision(
        allowed=not blocking,
        blocking_reasons=tuple(blocking),
        caveats=tuple(dict.fromkeys(caveats)),
        input_bundle=bundle,
    )
