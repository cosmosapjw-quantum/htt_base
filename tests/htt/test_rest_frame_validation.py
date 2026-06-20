from __future__ import annotations

import pytest


def _sha(char: str = "a") -> str:
    return "sha256:" + char * 64


def test_validation_summary_blocks_evidence_grade_until_all_statuses_pass() -> None:
    from htt.rest_frame.validation import RestFrameValidationSummary

    summary = RestFrameValidationSummary(
        prior_support_status="passed",
        matched_null_status="not_bound",
        ppc_status="passed",
        leave_one_out_status="passed",
        covariance_sensitivity_status="passed",
        config_hash=_sha("1"),
        input_hashes=(_sha("2"),),
        generating_command="pytest rest-frame validation",
        worktree_state="test",
    )
    payload = summary.to_payload()

    assert payload["owner"] == "HTT"
    assert payload["claim_tier"] == "diagnostic_only"
    assert payload["evidence_grade_allowed"] is False
    assert payload["claim_status"] == "blocked_validation_incomplete"
    assert "matched_null_status_not_passed" in payload["blockers"]
    assert payload["native_solver_result"] is False


def test_validation_summary_records_passed_candidate_without_evidence_claim() -> None:
    from htt.rest_frame.validation import RestFrameValidationSummary

    summary = RestFrameValidationSummary(
        prior_support_status="passed",
        matched_null_status="passed",
        ppc_status="passed",
        leave_one_out_status="passed",
        covariance_sensitivity_status="passed",
        config_hash=_sha("3"),
        input_hashes=(_sha("4"),),
        generating_command="pytest rest-frame validation",
        worktree_state="test",
    )
    payload = summary.to_payload()

    assert payload["validation_preconditions_passed"] is True
    assert payload["evidence_grade_allowed"] is False
    assert payload["claim_status"] == "validation_preconditions_passed"
    assert payload["claim_tier"] == "diagnostic_only"
    assert payload["blockers"] == []


def test_validation_summary_rejects_bad_statuses_and_hashes() -> None:
    from htt.rest_frame.validation import RestFrameValidationSummary

    with pytest.raises(ValueError, match="prior_support_status"):
        RestFrameValidationSummary(
            prior_support_status="maybe",
            matched_null_status="passed",
            ppc_status="passed",
            leave_one_out_status="passed",
            covariance_sensitivity_status="passed",
            config_hash=_sha("5"),
            input_hashes=(_sha("6"),),
            generating_command="pytest rest-frame validation",
            worktree_state="test",
        )
    with pytest.raises(ValueError, match="input_hashes"):
        RestFrameValidationSummary(
            prior_support_status="passed",
            matched_null_status="passed",
            ppc_status="passed",
            leave_one_out_status="passed",
            covariance_sensitivity_status="passed",
            config_hash=_sha("7"),
            input_hashes=("",),
            generating_command="pytest rest-frame validation",
            worktree_state="test",
        )
