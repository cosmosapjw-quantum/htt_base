from __future__ import annotations

import pytest

from bass.validation import (
    build_type_i_runtime_validation_evidence,
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
