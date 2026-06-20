from __future__ import annotations

import pytest

from htt.infer.predictive_adequacy import adequacy_gate


def test_ppc_failure_blocks_channel_evidence():
    gate = adequacy_gate(
        ppc_p_value=0.012,
        ppc_threshold=0.05,
        loocv_status="not_run",
        config_hash="sha256:" + "a" * 64,
        input_hashes=("sha256:" + "b" * 64,),
        generating_command="pytest",
        worktree_state="test",
    )
    payload = gate.as_payload()
    assert payload["adequacy_status"] == "failed"
    assert payload["evidence_claim_allowed"] is False
    assert "ppc_failure" in payload["blocked_reasons"]
    assert "loocv_not_run" in payload["blocked_reasons"]


def test_passing_ppc_and_loocv_allows_evidence():
    gate = adequacy_gate(
        ppc_p_value=0.42,
        ppc_threshold=0.05,
        loocv_status="passed",
        config_hash="sha256:" + "a" * 64,
        input_hashes=("sha256:" + "b" * 64,),
        generating_command="pytest",
        worktree_state="test",
    )
    payload = gate.as_payload()
    assert payload["adequacy_status"] == "passed"
    assert payload["evidence_claim_allowed"] is True
    assert payload["blocked_reasons"] == []


def test_required_next_models_listed():
    gate = adequacy_gate(
        ppc_p_value=0.012,
        ppc_threshold=0.05,
        loocv_status="not_run",
        config_hash="sha256:" + "a" * 64,
        input_hashes=("sha256:" + "b" * 64,),
        generating_command="pytest",
        worktree_state="test",
    )
    payload = gate.as_payload()
    assert set(payload["required_next_models"]) == {
        "single_beta",
        "survey_specific_amplitudes",
        "mixture_outlier",
        "systematic_response",
    }


def test_invalid_p_value_rejected():
    with pytest.raises(ValueError):
        adequacy_gate(
            ppc_p_value=1.5,
            ppc_threshold=0.05,
            loocv_status="not_run",
            config_hash="sha256:" + "a" * 64,
            input_hashes=("sha256:" + "b" * 64,),
            generating_command="pytest",
            worktree_state="test",
        )
