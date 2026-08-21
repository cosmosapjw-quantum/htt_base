from __future__ import annotations

from pathlib import Path
from enum import Enum
from types import ModuleType
import sys

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
        "response_rank": 2,
        "likelihood_normalized": True,
        "prior_normalized": True,
        "log_likelihood": lambda theta: -float(np.dot(theta, theta)),
        "prior_transform": lambda unit: np.asarray(unit),
        "replicate_generator": lambda theta, rng: np.asarray(theta) + rng.normal(size=len(theta)),
        "discrepancies": {"amplitude": lambda observed, replicated: float(np.sum(observed - replicated))},
    }
    values.update(overrides)
    return build_production_model_contract(**values)


def test_contract_rejects_unnormalized_and_rank_deficient_inputs() -> None:
    with pytest.raises(ProductionBayesianError, match="normalizations"):
        _contract(likelihood_normalized=False)
    with pytest.raises(ProductionBayesianError, match="rank"):
        _contract(response_rank=1)
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


def test_all_registered_lanes_are_readiness_only_until_bound_and_authorized() -> None:
    descriptors = load_observational_lane_descriptors(SPEC)
    assert tuple(item.lane_id for item in descriptors) == ("H-PLANCK", "H-DESI", "H-CF4", "H-JWST", "H-ACT")
    assert all((ROOT / path).is_file() for item in descriptors for path in item.runner_patterns)
    assert {assess_lane_readiness(item).status for item in descriptors} == {
        LaneReadinessStatus.BLOCKED_PRODUCTION_MODEL_CONTRACT_UNBOUND
    }
    desi = next(item for item in descriptors if item.lane_id == "H-DESI")
    assert assess_lane_readiness(desi, model_contract=_contract()).status is LaneReadinessStatus.BLOCKED_OBSERVED_EXECUTION_NOT_AUTHORIZED


def test_authorization_requires_the_exact_pr289_runtime_type(monkeypatch: pytest.MonkeyPatch) -> None:
    class AuthorizationStatus(str, Enum):
        NOT_AUTHORIZED = "NOT_AUTHORIZED"
        AUTHORIZED = "AUTHORIZED"

    class ExecutionAuthorizationReceipt:
        def __init__(self, lane_id: str, status: AuthorizationStatus) -> None:
            self.lane_id = lane_id
            self.status = status

    module = ModuleType("common.data_identity")
    module.AuthorizationStatus = AuthorizationStatus
    module.ExecutionAuthorizationReceipt = ExecutionAuthorizationReceipt
    monkeypatch.setitem(sys.modules, "common.data_identity", module)
    desi = next(item for item in load_observational_lane_descriptors(SPEC) if item.lane_id == "H-DESI")
    with pytest.raises(ProductionBayesianError, match="exact type"):
        assess_lane_readiness(desi, model_contract=_contract(), authorization_receipt=object())
    blocked = assess_lane_readiness(
        desi,
        model_contract=_contract(),
        authorization_receipt=ExecutionAuthorizationReceipt("DESI", AuthorizationStatus.NOT_AUTHORIZED),
    )
    assert blocked.status is LaneReadinessStatus.BLOCKED_OBSERVED_EXECUTION_NOT_AUTHORIZED
    ready = assess_lane_readiness(
        desi,
        model_contract=_contract(),
        authorization_receipt=ExecutionAuthorizationReceipt("DESI", AuthorizationStatus.AUTHORIZED),
    )
    assert ready.status is LaneReadinessStatus.READY_FOR_AUTHORIZED_EXECUTION
