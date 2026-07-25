from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import yaml

from common.k6_continuum_oracle import (
    curl_divergence,
    run_k6_continuum_suite,
    run_second_order_only_mutant,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC = REPO_ROOT / "docs/research_program/long_horizon_rescue/pr123_spec.yaml"
CARD = REPO_ROOT / "docs/generated/pr123_k6_continuum_card.json"


def test_solid_body_anchor_is_exact_for_both_registered_stencils() -> None:
    axis = np.linspace(-1.0, 1.0, 17)
    x, y, z = np.meshgrid(axis, axis, axis, indexing="ij")
    velocity = np.array((-0.7 * y, 0.7 * x, np.zeros_like(z)))
    expected = np.array((np.zeros_like(x), np.zeros_like(x), np.full_like(x, 1.4)))
    for order in (2, 4):
        curl, divergence = curl_divergence(
            velocity, float(axis[1] - axis[0]), order, periodic=False
        )
        assert np.allclose(curl, expected, atol=1e-11)
        assert np.allclose(divergence, 0.0, atol=1e-11)


def test_full_k6_suite_passes_preregistered_orders_and_domain_lock() -> None:
    spec = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    report, outcome = run_k6_continuum_suite(
        spec["k6_continuum_contract"],
        consumer_inventory=[
            "scripts/codex_harness/run_pr123_oracle_lab.py",
            "tests/contracts/test_pr123_k6_continuum_oracle.py",
        ],
        unexpected_consumers=[],
    )
    assert outcome.status == "PASS_MECHANICS_C2"
    assert outcome.mutant_killed is True
    assert report["periodic"]["2"]["mixed_observed_order"] >= 1.8
    assert report["periodic"]["4"]["mixed_observed_order"] >= 3.5
    assert report["boundary"]["2"]["manufactured_observed_order"] >= 1.8
    assert report["boundary"]["4"]["manufactured_observed_order"] >= 3.5
    assert report["boundary"]["2"]["interior_observed_order"] >= 1.8
    assert report["boundary"]["2"]["boundary_collar_observed_order"] >= 1.8
    assert report["boundary"]["4"]["interior_observed_order"] >= 3.5
    assert report["boundary"]["4"]["boundary_collar_observed_order"] >= 3.5
    assert report["interpolation"]["observed_order"] >= 1.8
    for observed in report["sqrt2_residual_lock"]["observed"].values():
        assert np.isclose(observed["ratio"], np.sqrt(2.0), atol=1e-11)
        assert observed["signed_atom_count"] == 18
        assert observed["gradient_mean_norm"] < 1e-14
        assert observed["gradient_covariance_isotropy_max_error"] < 1e-14
        assert not np.isclose(observed["correlated_challenge_ratio"], np.sqrt(2.0), atol=0.1)
    assert report["sqrt2_residual_lock"]["correlated_challenge_suspends_lock"] is True
    assert report["empirical_inputs"] == []
    assert report["empirical_consumers"] == []
    assert report["scientific_status"] == "OPEN"


def test_low_order_only_mutant_executes_and_fails_fourth_order_contract() -> None:
    mutant = run_second_order_only_mutant([16, 24, 32, 48])
    assert mutant["executed_grid_count"] == 4
    assert mutant["field_interpretation"] == "finite_grid_field_content"
    assert mutant["claimed_order_four_observed_order"] < 3.5
    assert len(mutant["claimed_order_four_errors"]) == 4


def test_unexpected_consumer_blocks_k6_lane() -> None:
    spec = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    _, outcome = run_k6_continuum_suite(
        spec["k6_continuum_contract"],
        consumer_inventory=["scripts/empirical_consumer.py"],
        unexpected_consumers=["scripts/empirical_consumer.py"],
    )
    assert outcome.clean_passed is False
    assert outcome.status == "BLOCKED_PROPERTY_FAILURE"
    no_consumer = next(
        item for item in outcome.properties if item.property_id == "no_empirical_consumer"
    )
    assert no_consumer.passed is False


def test_consumer_inventory_cannot_be_laundered_by_empty_unexpected_list() -> None:
    spec = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    report, outcome = run_k6_continuum_suite(
        spec["k6_continuum_contract"],
        consumer_inventory=["scripts/empirical_consumer.py"],
        unexpected_consumers=[],
    )
    no_consumer = next(
        item for item in outcome.properties if item.property_id == "no_empirical_consumer"
    )
    assert no_consumer.passed is False
    assert outcome.status == "BLOCKED_PROPERTY_FAILURE"
    assert report["unexpected_consumers"] == ["scripts/empirical_consumer.py"]
    assert report["empirical_consumer_count"] == 1


def test_checked_in_k6_card_has_no_empirical_consumer_or_observed_claim() -> None:
    payload = json.loads(CARD.read_text(encoding="utf-8"))
    assert payload["mutation_status"] == "PASS_MECHANICS_C2"
    assert payload["mutation_killed"] is True
    assert payload["empirical_consumer_count"] == 0
    assert payload["empirical_inputs"] == []
    assert payload["empirical_consumers"] == []
    assert payload["unexpected_consumers"] == []
    assert payload["consumer_inventory"] == [
        "scripts/codex_harness/run_pr123_oracle_lab.py",
        "tests/contracts/test_pr123_k6_continuum_oracle.py",
    ]
    assert payload["allowed_statement"].startswith("catalog-independent")
    assert payload["scientific_status"] == "OPEN"
