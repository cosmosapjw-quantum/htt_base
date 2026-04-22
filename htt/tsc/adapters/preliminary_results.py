"""TSC-facing loaders for VER2 preliminary-result packs."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from common.contracts import TscAdequacyOverlay
from tsc.adapters.bass_runtime import SourceAdequacySuggestion, overlay_to_bass_suggestion
from tsc.adapters.htt_inference import HttTscCaveatBundle, overlay_to_htt_caveats
from workspace.contracts.preliminary_results import (
    PreliminaryResultPack,
    TSC_ACTIVE_SERVICE_BUNDLE_ARTIFACT_ID,
    load_exported_tsc_overlay,
    TSC_POLICY_LEDGER_ARTIFACT_ID,
    TSC_OVERLAY_ARTIFACT_ID,
    ExportedTscActiveServiceBundle,
    ExportedTscPolicyLedger,
    load_exported_tsc_active_service_bundle,
    load_exported_tsc_policy_ledger,
    load_preliminary_result_pack,
)


@dataclass(frozen=True)
class PreliminaryTscHandoff:
    """TSC overlay plus downstream advisory views from generated exports."""

    overlay: TscAdequacyOverlay
    active_service_bundle: ExportedTscActiveServiceBundle
    policy_ledger: ExportedTscPolicyLedger
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


def _require_pack_artifact(
    pack: PreliminaryResultPack,
    *,
    artifact_id: str,
    owner: str,
) -> None:
    for artifact in pack.artifacts:
        if artifact.artifact_id != artifact_id:
            continue
        if artifact.owner != owner:
            raise ValueError(
                f"pack {pack.pack_id} artifact {artifact_id!r} must be owned by "
                f"{owner!r} (got {artifact.owner!r})"
            )
        return
    raise ValueError(
        f"pack {pack.pack_id} does not contain required artifact {artifact_id!r}"
    )


def _validate_preliminary_tsc_handoff(
    pack_d: PreliminaryResultPack,
    *,
    overlay: TscAdequacyOverlay,
    active_service_bundle: ExportedTscActiveServiceBundle,
    policy_ledger: ExportedTscPolicyLedger,
) -> None:
    overlay_id = overlay.manifest.artifact_id
    _require_pack_artifact(pack_d, artifact_id=TSC_OVERLAY_ARTIFACT_ID, owner="TSC")
    _require_pack_artifact(
        pack_d,
        artifact_id=TSC_ACTIVE_SERVICE_BUNDLE_ARTIFACT_ID,
        owner="TSC",
    )
    _require_pack_artifact(
        pack_d,
        artifact_id=TSC_POLICY_LEDGER_ARTIFACT_ID,
        owner="TSC",
    )
    if active_service_bundle.overlay_ref != overlay_id:
        raise ValueError(
            "exported TSC active-service bundle overlay ref does not match "
            f"the exported overlay ({active_service_bundle.overlay_ref!r} != {overlay_id!r})"
        )
    if policy_ledger.overlay_ref != overlay_id:
        raise ValueError(
            "exported TSC policy ledger overlay ref does not match "
            f"the exported overlay ({policy_ledger.overlay_ref!r} != {overlay_id!r})"
        )
    if active_service_bundle.overlay_artifact_id != overlay_id:
        raise ValueError(
            "exported TSC active-service bundle payload does not point at the exported overlay "
            f"({active_service_bundle.overlay_artifact_id!r} != {overlay_id!r})"
        )
    if policy_ledger.overlay_artifact_id != overlay_id:
        raise ValueError(
            "exported TSC policy ledger payload does not point at the exported overlay "
            f"({policy_ledger.overlay_artifact_id!r} != {overlay_id!r})"
        )
    if active_service_bundle.required_channels != policy_ledger.required_channels:
        raise ValueError(
            "exported TSC active-service bundle and policy ledger disagree on required channels "
            f"({active_service_bundle.required_channels!r} != {policy_ledger.required_channels!r})"
        )
    if active_service_bundle.publication_blockers != policy_ledger.publication_blockers:
        raise ValueError(
            "exported TSC active-service bundle and policy ledger disagree on publication blockers "
            f"({active_service_bundle.publication_blockers!r} != {policy_ledger.publication_blockers!r})"
        )
    if (
        active_service_bundle.overlay_policy_ledger_publication_blockers
        != policy_ledger.publication_blockers
    ):
        raise ValueError(
            "active-service embedded policy ledger does not match exported TSC policy ledger "
            f"({active_service_bundle.overlay_policy_ledger_publication_blockers!r} != {policy_ledger.publication_blockers!r})"
        )


def build_preliminary_tsc_handoff(
    *,
    generated_root: str | Path | None = None,
    required_channels: tuple[str, ...] = ("TT", "TE", "EE"),
    uses_scalar_only_geometry: bool = False,
) -> PreliminaryTscHandoff:
    pack_c = load_preliminary_result_pack("C", generated_root=generated_root)
    pack_d = load_preliminary_result_pack("D", generated_root=generated_root)
    overlay = load_exported_tsc_overlay(generated_root=generated_root)
    active_service_bundle = load_exported_tsc_active_service_bundle(
        generated_root=generated_root
    )
    policy_ledger = load_exported_tsc_policy_ledger(generated_root=generated_root)
    _validate_preliminary_tsc_handoff(
        pack_d,
        overlay=overlay,
        active_service_bundle=active_service_bundle,
        policy_ledger=policy_ledger,
    )
    overlay_ref = overlay.manifest.artifact_id
    return PreliminaryTscHandoff(
        overlay=overlay,
        active_service_bundle=active_service_bundle,
        policy_ledger=policy_ledger,
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
