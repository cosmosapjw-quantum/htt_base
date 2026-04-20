from __future__ import annotations

from workspace.contracts.validation_registry import (
    HostileAuditRunbook,
    NullEnsembleManifest,
    TheoremToTestEntry,
    ValidationCampaign,
    ValidationTestLink,
    build_default_hostile_audit_runbooks,
    build_default_theorem_to_test_map,
    build_default_validation_campaigns,
    manuscript_export_blocked,
)


def test_campaign_requires_owner_and_scope():
    try:
        ValidationCampaign(
            campaign_id="bad",
            title="bad",
            owner="BAD",
            implementation_scope="htt",
            status="warn",
            theorem_refs=("x",),
            categories=("baseline_reproduction",),
            artifact_refs=("a",),
            manuscript_blocking=True,
            no_claim_conditions=("n",),
        )
    except ValueError as exc:
        assert "Unknown owner" in str(exc)
    else:
        raise AssertionError("invalid owner should fail")


def test_theorem_to_test_entry_has_artifact_refs():
    entries = build_default_theorem_to_test_map()
    assert all(entry.artifact_refs for entry in entries)
    assert any(
        any(link.category == "adversarial_edge" for link in entry.test_links)
        for entry in entries
    )


def test_warn_does_not_promote_to_validated():
    campaign = build_default_validation_campaigns()[0]
    assert campaign.status == "warn"
    assert campaign.promotes_to_validated is False


def test_fail_blocks_manuscript_export():
    campaign = ValidationCampaign(
        campaign_id="blocking.fail",
        title="blocking fail",
        owner="COMMON",
        implementation_scope="common",
        status="fail",
        theorem_refs=("t",),
        categories=("regression",),
        artifact_refs=("a",),
        manuscript_blocking=True,
        no_claim_conditions=("n",),
    )
    assert manuscript_export_blocked((campaign,)) is True


def test_null_manifest_requires_scan_volume_and_no_claim_conditions():
    try:
        NullEnsembleManifest(
            ensemble_id="null.bad",
            null_family="flrw",
            observable_basis="lowell",
            scan_volume_hash="",
            status="warn",
            artifact_refs=("a",),
            no_claim_conditions=("missing_scan_volume",),
        )
    except ValueError as exc:
        assert "scan_volume_hash" in str(exc)
    else:
        raise AssertionError("missing scan_volume_hash should fail")


def test_hostile_audit_runbook_has_all_check_buckets():
    runbook = build_default_hostile_audit_runbooks()[0]
    assert runbook.baseline_checks
    assert runbook.adversarial_checks
    assert runbook.physics_checks
    assert runbook.numerical_checks
    assert runbook.regression_checks

