from __future__ import annotations

import pytest

from htt.infer.joint_survey_hierarchy import build_joint_hierarchy_contract


def test_joint_hierarchy_blocks_without_cross_probe_covariance():
    contract = build_joint_hierarchy_contract(
        probes=("CatWISE", "radio", "CF4"),
        covariance_status="not_bound",
        nuisance_status="survey_nuisance_not_bound",
        heldout_status="not_run",
        config_hash="sha256:" + "a" * 64,
        input_hashes=("sha256:" + "b" * 64,),
        generating_command="pytest",
        worktree_state="test",
    )
    payload = contract.as_payload()
    assert payload["claim_tier"] == "blocked"
    assert payload["conditional_independence_product_allowed"] is False
    assert "cross_probe_covariance_not_bound" in payload["blocked_reasons"]


def test_joint_hierarchy_unblocks_only_when_all_fields_bound():
    contract = build_joint_hierarchy_contract(
        probes=("CatWISE", "radio", "CF4"),
        covariance_status="bound",
        nuisance_status="bound",
        heldout_status="passed",
        mask_selection_status="bound",
        shared_lss_covariance_status="bound",
        config_hash="sha256:" + "a" * 64,
        input_hashes=("sha256:" + "b" * 64,),
        generating_command="pytest",
        worktree_state="test",
    )
    payload = contract.as_payload()
    assert payload["claim_tier"] == "conditional"
    assert payload["conditional_independence_product_allowed"] is True
    assert payload["blocked_reasons"] == []


def test_joint_hierarchy_requires_probes():
    with pytest.raises(ValueError):
        build_joint_hierarchy_contract(
            probes=(),
            covariance_status="bound",
            nuisance_status="bound",
            heldout_status="passed",
            config_hash="sha256:" + "a" * 64,
            input_hashes=("sha256:" + "b" * 64,),
            generating_command="pytest",
            worktree_state="test",
        )
