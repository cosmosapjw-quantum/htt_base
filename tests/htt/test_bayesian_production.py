from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from htt.infer.bayesian_production import (
    LaneReadinessStatus,
    ProductionBayesianError,
    assess_lane_readiness,
    build_production_model_contract,
    build_posterior_consumer_plan,
    build_sampler_posterior_lineage,
    load_observational_lane_descriptors,
)


ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "docs/research_program/post_pr275/pr299_spec.yaml"
_HASH = "sha256:" + "a" * 64


def _contract(**overrides):
    values = {
        "lane_id": "H-DESI",
        "model_id": "desi-selection-competitor",
        "parameter_schema": {
            "amplitude": {"support": "real", "role": "signal"},
            "selection": {"support": "real", "role": "nuisance"},
        },
        "likelihood_identity": _HASH,
        "prior_identity": "sha256:" + "b" * 64,
        "data_identity": "sha256:" + "c" * 64,
        "covariance_identity": "sha256:" + "d" * 64,
        "block_ids": ("NGC-z1", "SGC-z1"),
        "discrepancy_ids": ("amplitude",),
    }
    values.update(overrides)
    return build_production_model_contract(**values)


def test_contract_rejects_caller_asserted_normalization_rank_and_callables() -> None:
    with pytest.raises(ProductionBayesianError, match="computed evidence"):
        _contract(likelihood_normalized=True)
    with pytest.raises(ProductionBayesianError, match="computed evidence"):
        _contract(response_rank=2)
    with pytest.raises(ProductionBayesianError, match="factory-loaded"):
        _contract(log_likelihood=lambda theta: -float(np.dot(theta, theta)))
    with pytest.raises(ProductionBayesianError, match="blockwise"):
        _contract(block_ids=("only",))
    with pytest.raises(ProductionBayesianError, match="support"):
        _contract(parameter_schema={"amplitude": {"role": "signal"}})


def test_weighted_posterior_lineage_binds_exact_samples_weights_and_settings() -> None:
    contract = _contract()
    lineage = build_sampler_posterior_lineage(
        contract=contract,
        samples=np.array([[0.0, 1.0], [1.0, 2.0], [2.0, 3.0]]),
        normalized_weights=np.array([0.2, 0.3, 0.5]),
        sampler_settings={"nlive": 200, "dlogz": 0.1, "bound": "multi", "sample": "rwalk", "seed": 7},
        resampling_rule="systematic",
    )
    assert lineage.model_contract_content_id == contract.contract_content_id
    assert lineage.weighted_ess == pytest.approx(1.0 / 0.38)
    plan = build_posterior_consumer_plan(
        contract=contract,
        lineage=lineage,
        ppc_discrepancy_ids=("amplitude",),
        loo_block_ids=("NGC-z1", "SGC-z1"),
    )
    assert plan.posterior_lineage_content_id == lineage.lineage_content_id
    with pytest.raises(ProductionBayesianError, match="normalized"):
        build_sampler_posterior_lineage(
            contract=contract,
            samples=np.zeros((3, 2)),
            normalized_weights=np.array([0.2, 0.3, 0.6]),
            sampler_settings={"nlive": 200, "dlogz": 0.1, "bound": "multi", "sample": "rwalk", "seed": 7},
            resampling_rule="systematic",
        )


def test_ppc_consumer_plan_requires_unique_canonical_discrepancy_order() -> None:
    contract = _contract(
        discrepancy_ids=("zeta", "amplitude")
    )
    lineage = build_sampler_posterior_lineage(
        contract=contract,
        samples=np.array([[0.0, 1.0], [1.0, 2.0], [2.0, 3.0]]),
        normalized_weights=np.array([0.2, 0.3, 0.5]),
        sampler_settings={"nlive": 200, "dlogz": 0.1, "bound": "multi", "sample": "rwalk", "seed": 7},
        resampling_rule="systematic",
    )
    with pytest.raises(ProductionBayesianError, match="registered discrepancy"):
        build_posterior_consumer_plan(
            contract=contract,
            lineage=lineage,
            ppc_discrepancy_ids=("zeta", "amplitude"),
            loo_block_ids=("NGC-z1", "SGC-z1"),
        )
    plan = build_posterior_consumer_plan(
        contract=contract,
        lineage=lineage,
        ppc_discrepancy_ids=("amplitude", "zeta"),
        loo_block_ids=("NGC-z1", "SGC-z1"),
    )
    assert plan.ppc_discrepancy_ids == ("amplitude", "zeta")


def test_all_registered_lanes_are_readiness_only_until_bound_and_authorized() -> None:
    descriptors = load_observational_lane_descriptors(SPEC)
    assert tuple(item.lane_id for item in descriptors) == ("H-PLANCK", "H-DESI", "H-CF4", "H-JWST", "H-ACT")
    assert all((ROOT / path).is_file() for item in descriptors for path in item.runner_patterns)
    assert {assess_lane_readiness(item).status for item in descriptors} == {
        LaneReadinessStatus.BLOCKED_PRODUCTION_MODEL_CONTRACT_UNBOUND
    }
    desi = next(item for item in descriptors if item.lane_id == "H-DESI")
    decision = assess_lane_readiness(desi, model_contract=_contract())
    assert decision.status is LaneReadinessStatus.BLOCKED_PRODUCTION_MODEL_CONTRACT_UNBOUND
    assert decision.blocked_reasons == ("complete_pr289_lane_admission_unbound",)


def test_pr289_receipts_cannot_substitute_for_pr304_human_capabilities() -> None:
    desi = next(item for item in load_observational_lane_descriptors(SPEC) if item.lane_id == "H-DESI")
    contract = _contract()
    with pytest.raises(ProductionBayesianError, match="cannot substitute"):
        assess_lane_readiness(desi, model_contract=contract, authorization_receipt=object())
