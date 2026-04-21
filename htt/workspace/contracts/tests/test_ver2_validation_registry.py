from __future__ import annotations

from workspace.contracts.validation_registry import (
    NullEnsembleManifest,
    REQUIRED_VALIDATION_CATEGORIES,
    ValidationCampaign,
    ValidationTestLink,
    build_default_hostile_audit_runbooks,
    build_default_theorem_to_test_map,
    build_default_validation_campaigns,
    hostile_audit_issues,
    manuscript_export_blocked,
    validation_registry_issues,
    validation_test_path_exists,
)


def _link(
    *,
    test_id: str = "regression.anchor",
    category: str = "regression",
    path: str = "htt/workspace/contracts/tests/test_ver2_validation_registry.py::test_campaign_requires_owner_and_scope",
) -> ValidationTestLink:
    return ValidationTestLink(
        test_id=test_id,
        category=category,  # type: ignore[arg-type]
        path=path,
        purpose="test anchor",
        artifact_refs=("validation.anchor",),
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
            categories=("regression",),
            check_links=(_link(),),
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
    assert all(entry.no_claim_conditions for entry in entries)
    assert any(
        any(link.category == "adversarial_edge" for link in entry.test_links)
        for entry in entries
    )


def test_tsc_registry_entry_pulls_live_local_validation_witnesses():
    tsc_entry = next(
        entry
        for entry in build_default_theorem_to_test_map()
        if entry.theorem_id == "V8_tsc_no_overclaim"
    )
    test_ids = {link.test_id for link in tsc_entry.test_links}

    assert "quadrupole_convention_roundtrip" in test_ids
    assert "collision_only_bridge_is_blocked" in test_ids
    assert "export_blocks_exploratory_claim_ceiling" in test_ids


def test_warn_does_not_promote_to_validated():
    campaign = next(
        campaign
        for campaign in build_default_validation_campaigns()
        if campaign.status == "warn"
    )
    assert campaign.status == "warn"
    assert campaign.promotes_to_validated is False


def test_pass_campaign_promotes_to_validated():
    campaign = next(
        campaign
        for campaign in build_default_validation_campaigns()
        if campaign.status == "pass"
    )
    assert campaign.promotes_to_validated is True


def test_fail_blocks_manuscript_export():
    campaign = ValidationCampaign(
        campaign_id="blocking.fail",
        title="blocking fail",
        owner="COMMON",
        implementation_scope="common",
        status="fail",
        theorem_refs=("t",),
        categories=("regression",),
        check_links=(
            _link(
                test_id="blocking.fail.regression",
                path="htt/workspace/contracts/tests/test_ver2_validation_registry.py::test_fail_blocks_manuscript_export",
            ),
        ),
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
    assert runbook.campaign_refs
    assert runbook.baseline_checks
    assert runbook.adversarial_checks
    assert runbook.physics_checks
    assert runbook.numerical_checks
    assert runbook.regression_checks


def test_validation_test_path_exists_for_function_and_class_method():
    assert validation_test_path_exists(
        "htt/workspace/contracts/tests/test_ver2_validation_registry.py::test_campaign_requires_owner_and_scope"
    )
    assert validation_test_path_exists(
        "htt/src/common/test_mock_calibration.py::TestMockGeneration::test_isotropic_mock_has_zero_mean_over_many_realisations"
    )


def test_default_campaigns_cover_all_required_categories():
    required = set(REQUIRED_VALIDATION_CATEGORIES)
    campaigns = build_default_validation_campaigns()
    assert campaigns
    for campaign in campaigns:
        assert set(campaign.categories) == required
        assert {link.category for link in campaign.check_links} == required


def test_bass_native_runtime_bridge_records_missing_late_time_reionization_window() -> None:
    campaigns = build_default_validation_campaigns()
    campaign = next(
        row for row in campaigns if row.campaign_id == "validation.bass_native_runtime_bridge"
    )
    assert "late_time_reionization_window_missing" in campaign.no_claim_conditions
    theorem = next(
        row
        for row in build_default_theorem_to_test_map()
        if row.theorem_id == "V8_bass_native_runtime_bridge"
    )
    assert "late_time_reionization_window_missing" in theorem.no_claim_conditions
    assert any(
        link.test_id == "tier_b_runtime_explicitly_flags_missing_late_time_reionization_window"
        for link in campaign.check_links
    )


def test_bass_representative_family_sweep_records_tilted_runtime_blocker() -> None:
    campaigns = build_default_validation_campaigns()
    campaign = next(
        row for row in campaigns if row.campaign_id == "validation.bass_representative_family_sweep"
    )
    assert "representative_tilted_runtime_blocked" in campaign.no_claim_conditions
    theorem = next(
        row
        for row in build_default_theorem_to_test_map()
        if row.theorem_id == "V8_bass_representative_family_sweep"
    )
    assert "representative_tilted_runtime_blocked" in theorem.no_claim_conditions
    assert any(
        link.test_id == "representative_tilted_branches_fail_controlledly"
        for link in campaign.check_links
    )


def test_default_registry_has_no_link_or_coverage_issues():
    assert validation_registry_issues() == ()


def test_default_hostile_audit_has_no_bucket_or_quarantine_issues():
    assert hostile_audit_issues() == ()
