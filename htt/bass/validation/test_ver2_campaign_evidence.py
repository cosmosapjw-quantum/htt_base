from __future__ import annotations

import pytest

from bass.validation import (
    build_representative_family_sweep_evidence,
    build_type_i_reionization_probe_evidence,
    build_type_i_runtime_validation_evidence,
    representative_family_sweep_payload,
    type_i_reionization_probe_payload,
    type_i_runtime_validation_payload,
)


def test_type_i_runtime_validation_evidence_passes_with_shipped_thresholds() -> None:
    evidence = build_type_i_runtime_validation_evidence()
    assert evidence.status == "pass"
    assert evidence.bianchi_type == "I"
    assert evidence.cutoffs == (4, 6)
    assert "late_time_reionization_window_missing" in evidence.no_claim_conditions
    assert evidence.tier_a_tier_b_max_relative_l2 <= 5.0e-2
    assert evidence.cutoff_max_relative_delta <= 7.5e-1
    assert all(check.passed for check in evidence.checks)


def test_type_i_runtime_validation_payload_is_json_ready() -> None:
    payload = type_i_runtime_validation_payload()
    assert payload["campaign_id"] == "validation.bass_native_runtime_bridge"
    assert payload["status"] == "pass"
    assert payload["cutoffs"] == (4, 6)
    check_ids = {row["check_id"] for row in payload["checks"]}
    assert {
        "type_i_observable_null_recovery",
        "native_seed_projection_survives_without_startup",
        "tier_a_tier_b_type_i_bridge_matches",
        "tier_b_cutoff_campaign_stays_bounded",
        "tier_b_runtime_consumes_live_hooks_and_exact_type_i_propagator",
        "tier_b_runtime_explicitly_flags_missing_late_time_reionization_window",
    } <= check_ids


def test_type_i_runtime_validation_rejects_strict_cutoff_threshold() -> None:
    with pytest.raises(ValueError, match="cutoff_delta_tolerance"):
        build_type_i_runtime_validation_evidence(cutoff_delta_tolerance=0.0)


def test_type_i_runtime_validation_evidence_records_missing_late_time_reionization_window() -> None:
    evidence = build_type_i_runtime_validation_evidence()
    check = next(
        row
        for row in evidence.checks
        if row.check_id == "tier_b_runtime_explicitly_flags_missing_late_time_reionization_window"
    )
    assert check.passed is True
    assert "late-time low-z source window" in check.summary


def test_representative_family_sweep_evidence_passes_with_bounded_orthogonal_subset() -> None:
    evidence = build_representative_family_sweep_evidence()
    assert evidence.status == "pass"
    assert evidence.campaign_id == "validation.bass_representative_family_sweep"
    assert evidence.bianchi_type == "I,V,VII_0,VIII"
    assert "representative_tilted_runtime_partial_only" in evidence.no_claim_conditions
    checks = {row.check_id: row for row in evidence.checks}
    assert checks["representative_orthogonal_families_run_end_to_end"].passed is True
    assert checks["representative_tilted_runnable_subset_runs_end_to_end"].passed is True
    assert checks["representative_remaining_tilted_branches_fail_controlledly"].passed is True
    assert checks["representative_family_realizations_are_algebra_aware"].passed is True
    assert checks["representative_family_b_mode_payloads_remain_family_conditional"].passed is True


def test_representative_family_sweep_payload_is_json_ready() -> None:
    payload = representative_family_sweep_payload()
    assert payload["campaign_id"] == "validation.bass_representative_family_sweep"
    assert payload["status"] == "pass"
    check_ids = {row["check_id"] for row in payload["checks"]}
    assert {
        "representative_orthogonal_families_run_end_to_end",
        "representative_tilted_runnable_subset_runs_end_to_end",
        "representative_remaining_tilted_branches_fail_controlledly",
        "representative_family_realizations_are_algebra_aware",
        "representative_family_outputs_stay_finite_on_bounded_low_ell_grid",
        "representative_family_b_mode_payloads_remain_family_conditional",
        "representative_family_sweep_preserves_tilt_boost_contracts",
    } <= check_ids


def test_type_i_reionization_probe_evidence_passes_for_extended_low_z_runtime() -> None:
    evidence = build_type_i_reionization_probe_evidence()
    assert evidence.status == "pass"
    assert evidence.campaign_id == "validation.bass_type_i_extended_reionization_probe"
    assert evidence.cutoffs == (4,)
    assert "direction_resolved_reionization_microphysics_missing" in evidence.no_claim_conditions
    checks = {row.check_id: row for row in evidence.checks}
    assert checks["extended_runtime_reaches_low_z_probe"].passed is True
    assert checks["reionization_mode_toggle_changes_claim_surface"].passed is True
    assert checks["reionization_increases_low_z_visibility_source"].passed is True


def test_type_i_reionization_probe_payload_is_json_ready() -> None:
    payload = type_i_reionization_probe_payload()
    assert payload["campaign_id"] == "validation.bass_type_i_extended_reionization_probe"
    assert payload["status"] == "pass"
    check_ids = {row["check_id"] for row in payload["checks"]}
    assert {
        "extended_runtime_reaches_low_z_probe",
        "reionization_mode_toggle_changes_claim_surface",
        "reionization_increases_low_z_visibility_source",
        "extended_runtime_hits_declared_low_z_endpoint",
        "extended_runtime_preserves_exact_type_i_propagator",
    } <= check_ids
