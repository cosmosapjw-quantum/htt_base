from __future__ import annotations

import pytest

from common.contracts import (
    ArtifactManifest,
    BundleKind,
    ClaimLedgerEntry,
    ClaimTier,
    ImplementationScope,
    Owner,
    StatusSnapshotEntry,
    assert_owner_can_emit_bundle,
    normalize_owner,
    owner_can_emit_bundle,
)
from workspace.contracts.validation_registry import (
    build_default_theorem_to_test_map,
    build_default_validation_campaigns,
)
from workspace.contracts.ownership import (
    BundleKind as WorkspaceBundleKind,
    Owner as WorkspaceOwner,
    assert_owner_can_emit_bundle as workspace_assert_owner_can_emit_bundle,
)


def test_owner_enum_covers_canonical_science_owners_without_active_tsc() -> None:
    assert {owner.value for owner in Owner} == {
        "COMMON",
        "HTT",
        "MIO",
        "BASS",
        "OBSSTAT",
        "TSC_LEGACY",
    }
    assert "TSC" not in {owner.value for owner in Owner}


def test_claim_tier_and_scope_are_string_compatible_enums() -> None:
    assert ClaimTier.CONDITIONAL == "conditional"
    assert ClaimTier.DIAGNOSTIC_ONLY == "diagnostic_only"
    assert ImplementationScope.HTT == "htt"
    assert ImplementationScope.TSC_LEGACY == "tsc_legacy"


def test_legacy_tsc_owner_normalizes_to_tsc_legacy_without_becoming_canonical() -> None:
    assert normalize_owner("TSC") is Owner.TSC_LEGACY
    assert normalize_owner("TSC_LEGACY") is Owner.TSC_LEGACY


def test_artifact_manifest_accepts_enum_values_and_legacy_strings() -> None:
    manifest = ArtifactManifest(
        artifact_id="common.contract",
        artifact_path="artifacts/common/contract.json",
        owner=Owner.COMMON,
        implementation_scope=ImplementationScope.COMMON,
        claim_tier=ClaimTier.CONDITIONAL,
        production_status="diagnostic_only",
        created_by="test-suite",
        git_commit="abc123",
        config_hash="cfg",
        input_hashes=["input"],
        code_version="0.0-test",
        schema_version="pr010",
    )

    assert manifest.owner is Owner.COMMON
    assert manifest.implementation_scope is ImplementationScope.COMMON
    assert manifest.claim_tier is ClaimTier.CONDITIONAL


def test_canonical_contract_rows_normalize_legacy_tsc_strings() -> None:
    manifest = ArtifactManifest(
        artifact_id="tsc.legacy.overlay",
        artifact_path="artifacts/tsc/overlay.json",
        owner="TSC",
        implementation_scope="tsc",
        claim_tier="conditional",
        production_status="diagnostic_only",
        created_by="test-suite",
        git_commit="abc123",
        config_hash="cfg",
        input_hashes=["input"],
        code_version="0.0-test",
        schema_version="pr010",
    )
    snapshot = StatusSnapshotEntry(
        artifact_id="tsc.legacy.snapshot",
        owner="TSC",
        implementation_scope="tsc",
        claim_tier="conditional",
        implemented=True,
        smoke_tested=True,
        production_validated=False,
        manuscript_used=False,
        source_commit="abc123",
    )
    ledger = ClaimLedgerEntry(
        artifact_id="tsc.legacy.claims",
        owner="TSC",
        claim_tier="conditional",
        allowed_claims=("legacy reproducibility only",),
        forbidden_claims=("active science ownership",),
        evidence_refs=("tsc.legacy.overlay",),
        source_commit="abc123",
    )

    assert manifest.owner is Owner.TSC_LEGACY
    assert manifest.implementation_scope is ImplementationScope.TSC_LEGACY
    assert manifest.claim_tier is ClaimTier.CONDITIONAL
    assert snapshot.owner is Owner.TSC_LEGACY
    assert snapshot.implementation_scope is ImplementationScope.TSC_LEGACY
    assert snapshot.claim_tier is ClaimTier.CONDITIONAL
    assert ledger.owner is Owner.TSC_LEGACY
    assert ledger.claim_tier is ClaimTier.CONDITIONAL


def test_validation_registry_uses_canonical_owner_and_scope_vocabulary() -> None:
    theorem_rows = build_default_theorem_to_test_map()
    campaigns = build_default_validation_campaigns()

    assert "TSC" not in {row.owner for row in theorem_rows}
    assert "tsc" not in {row.implementation_scope for row in theorem_rows}
    assert "TSC" not in {campaign.owner for campaign in campaigns}
    assert "tsc" not in {campaign.implementation_scope for campaign in campaigns}
    assert Owner.TSC_LEGACY.value in {row.owner for row in theorem_rows}
    assert ImplementationScope.TSC_LEGACY.value in {
        row.implementation_scope for row in theorem_rows
    }


def test_mio_cannot_own_posterior_and_htt_cannot_own_certificate() -> None:
    assert owner_can_emit_bundle(Owner.HTT, BundleKind.POSTERIOR)
    assert owner_can_emit_bundle(Owner.MIO, BundleKind.DIAGNOSTIC_CERTIFICATE)
    assert not owner_can_emit_bundle(Owner.MIO, BundleKind.POSTERIOR)
    assert not owner_can_emit_bundle(Owner.HTT, BundleKind.DIAGNOSTIC_CERTIFICATE)

    with pytest.raises(ValueError, match="MIO.*posterior"):
        assert_owner_can_emit_bundle(Owner.MIO, BundleKind.POSTERIOR)
    with pytest.raises(ValueError, match="HTT.*diagnostic_certificate"):
        assert_owner_can_emit_bundle(Owner.HTT, BundleKind.DIAGNOSTIC_CERTIFICATE)


def test_owner_firewall_assigns_non_inference_roles() -> None:
    assert owner_can_emit_bundle(Owner.BASS, BundleKind.TRANSFER_ATLAS)
    assert owner_can_emit_bundle(Owner.OBSSTAT, BundleKind.OBSERVABLE_FEATURES)
    assert owner_can_emit_bundle(Owner.COMMON, BundleKind.COMMON_CONTRACT)
    assert owner_can_emit_bundle(Owner.TSC_LEGACY, BundleKind.LEGACY_REPRODUCTION)
    assert not owner_can_emit_bundle(Owner.TSC_LEGACY, BundleKind.POSTERIOR)


def test_workspace_ownership_facade_reexports_canonical_contracts() -> None:
    assert WorkspaceOwner.MIO is Owner.MIO
    assert WorkspaceBundleKind.POSTERIOR is BundleKind.POSTERIOR
    with pytest.raises(ValueError, match="MIO.*posterior"):
        workspace_assert_owner_can_emit_bundle(WorkspaceOwner.MIO, WorkspaceBundleKind.POSTERIOR)
