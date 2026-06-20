from __future__ import annotations

import pytest

from htt.infer.prior_error_sensitivity import summarize_prior_error_grid


def test_sign_flip_blocks_single_evidence_label():
    report = summarize_prior_error_grid(
        rows=[
            {"prior_floor": 1e-12, "ceiling": 1.0, "sigma_beta": 2.7e-4, "lnB": 26.0},
            {"prior_floor": 1e-6, "ceiling": 1.0, "sigma_beta": 2.7e-4, "lnB": -39.1},
        ],
        config_hash="sha256:" + "a" * 64,
        input_hashes=("sha256:" + "b" * 64,),
        generating_command="pytest",
        worktree_state="test",
    )
    payload = report.as_payload()
    assert payload["single_jeffreys_label_allowed"] is False
    assert payload["sign_flip_detected"] is True
    assert payload["claim_tier"] == "blocked"


def test_proxy_rows_block_label_even_without_sign_flip():
    report = summarize_prior_error_grid(
        rows=[
            {"prior_floor": 1e-12, "ceiling": 1.0, "sigma_beta": 2.7e-4, "lnB": 26.0},
            {"prior_floor": 1e-6, "ceiling": 1.0, "sigma_beta": 2.7e-4, "lnB": 12.0},
        ],
        config_hash="sha256:" + "a" * 64,
        input_hashes=("sha256:" + "b" * 64,),
        generating_command="pytest",
        worktree_state="test",
    )
    payload = report.as_payload()
    assert payload["sign_flip_detected"] is False
    assert payload["single_jeffreys_label_allowed"] is False
    assert payload["claim_tier"] == "blocked"
    assert payload["boundary_mass_status"] == "not_computed_placeholder"


def test_robust_marginal_rows_allow_conditional_label():
    report = summarize_prior_error_grid(
        rows=[
            {"prior_floor": 1e-12, "ceiling": 1.0, "sigma_beta": 2.7e-4, "lnB": 26.0},
            {"prior_floor": 1e-6, "ceiling": 1.0, "sigma_beta": 2.7e-4, "lnB": 18.0},
        ],
        config_hash="sha256:" + "a" * 64,
        input_hashes=("sha256:" + "b" * 64,),
        generating_command="pytest",
        worktree_state="test",
        rows_are_marginal_likelihoods=True,
    )
    payload = report.as_payload()
    assert payload["single_jeffreys_label_allowed"] is True
    assert payload["claim_tier"] == "conditional"


def test_empty_grid_rejected():
    with pytest.raises(ValueError):
        summarize_prior_error_grid(
            rows=[],
            config_hash="sha256:" + "a" * 64,
            input_hashes=("sha256:" + "b" * 64,),
            generating_command="pytest",
            worktree_state="test",
        )
