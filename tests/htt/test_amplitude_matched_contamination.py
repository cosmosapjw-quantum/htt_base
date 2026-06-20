from __future__ import annotations

import pytest

from htt.infer.amplitude_matched_contamination import contamination_fpr_report


def test_high_contamination_fpr_blocks_source_identification():
    report = contamination_fpr_report(
        n_trials=100,
        n_false_positive=95,
        trigger="lnB_gt_5",
        config_hash="sha256:" + "a" * 64,
        input_hashes=("sha256:" + "b" * 64,),
        generating_command="pytest",
        worktree_state="test",
    )
    payload = report.as_payload()
    assert payload["claim_tier"] == "blocked"
    assert payload["source_identification_status"] == "failed"
    assert payload["false_positive_rate"]["raw"] == 0.95
    assert payload["false_positive_rate"]["wilson_95"][0] > 0.85
    assert payload["headline_bayes_factor_allowed"] is False


def test_low_contamination_fpr_does_not_block():
    report = contamination_fpr_report(
        n_trials=100,
        n_false_positive=1,
        trigger="lnB_gt_5",
        config_hash="sha256:" + "a" * 64,
        input_hashes=("sha256:" + "b" * 64,),
        generating_command="pytest",
        worktree_state="test",
    )
    payload = report.as_payload()
    assert payload["claim_tier"] == "conditional"
    assert payload["source_identification_status"] == "not_blocked_by_contamination"
    assert payload["headline_bayes_factor_allowed"] is True


def test_invalid_counts_rejected():
    with pytest.raises(ValueError):
        contamination_fpr_report(
            n_trials=10,
            n_false_positive=20,
            trigger="lnB_gt_5",
            config_hash="sha256:" + "a" * 64,
            input_hashes=("sha256:" + "b" * 64,),
            generating_command="pytest",
            worktree_state="test",
        )
