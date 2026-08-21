from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import hmac
from pathlib import Path

import numpy as np
import pytest

from common.human_execution_authorization import (
    AUTHORIZATION_DOMAIN,
    SCHEMA,
    HumanExecutionAuthorizationError,
    HumanExecutionAuthorizationReceiptV1,
    validate_and_consume,
)
from htt.infer.bayesian_production import (
    PosteriorConsumerStatus,
    ProductionBayesianError,
    SamplerStartStatus,
    assess_posterior_consumer_readiness,
    assess_sampler_start_readiness,
    build_normalization_evidence_receipt,
    build_observed_execution_binding,
    build_production_model_contract,
    build_sampler_posterior_lineage,
    validate_dynesty_environment,
)


NOW = datetime(2026, 8, 21, tzinfo=timezone.utc)
KEY = b"external-test-key"


def likelihood(theta: np.ndarray) -> float:
    return -float(np.dot(theta, theta))


def prior(unit: np.ndarray) -> np.ndarray:
    return np.asarray(unit)


def replicate(theta: np.ndarray) -> np.ndarray:
    return np.asarray(theta)


def discrepancy(observed: np.ndarray, replicated: np.ndarray) -> float:
    return float(np.sum(observed - replicated))


def provider() -> None:
    return None


def _receipt() -> HumanExecutionAuthorizationReceiptV1:
    raw: dict[str, object] = {
        "schema": SCHEMA, "lane_id": "H-DESI", "required_human_gate_id": "H-DESI",
        "analysis_plan_id": "desi-plan-v1", "exact_admission_record_ids": ["record-1", "record-2"],
        "lane_admission_bundle_id": "desi-bundle-v1", "authorized_scope": "one_lane",
        "authorization_domain": AUTHORIZATION_DOMAIN, "key_id": "operator", "key_sha256": hashlib.sha256(KEY).hexdigest(),
        "issued_at_utc": NOW.isoformat(), "expires_at_utc": (NOW + timedelta(minutes=10)).isoformat(), "nonce": "desi-nonce", "hmac_sha256": "pending",
    }
    unsigned = HumanExecutionAuthorizationReceiptV1.from_mapping(raw).unsigned_payload()
    raw["hmac_sha256"] = hmac.new(KEY, __import__("json").dumps(unsigned, sort_keys=True, separators=(",", ":")).encode(), hashlib.sha256).hexdigest()
    return HumanExecutionAuthorizationReceiptV1.from_mapping(raw)


def _authorization(tmp_path: Path):
    return validate_and_consume(
        _receipt(), expected_lane_id="H-DESI", expected_human_gate_id="H-DESI", expected_analysis_plan_id="desi-plan-v1",
        expected_record_ids=("record-1", "record-2"), expected_bundle_id="desi-bundle-v1", expected_scope="one_lane",
        key_resolver=lambda _: KEY, nonce_ledger=tmp_path / "nonces", now_utc=NOW,
    )


def _contract():
    normalization = build_normalization_evidence_receipt(
        provider_id="provider-v1", provider=provider, support={"theta": "real"}, units={"theta": "1"}, constants={"c": 1},
    )
    return build_production_model_contract(
        lane_id="H-DESI", model_id="desi-model", parameter_schema={"a": {"support": "real"}, "b": {"support": "real"}},
        likelihood_receipt=normalization, prior_receipt=normalization,
        response_matrix=np.eye(2), covariance_matrix=np.eye(2), block_ids=("north", "south"),
        log_likelihood=likelihood, prior_transform=prior, replicate_generator=replicate, discrepancies={"sum": discrepancy},
    )


def test_BAYES_001_start_readiness_has_no_posterior_cycle(tmp_path: Path) -> None:
    contract = _contract()
    authorization = _authorization(tmp_path)
    engine = validate_dynesty_environment(expected_version="3.0.0")
    decision = assess_sampler_start_readiness(contract=contract, authorization=authorization, engine_receipt=engine)
    assert decision.status is SamplerStartStatus.READY_TO_START_SAMPLER


def test_BAYES_002_to_016_observed_lineage_contracts(tmp_path: Path) -> None:
    contract = _contract()
    authorization = _authorization(tmp_path)
    engine = validate_dynesty_environment(expected_version="3.0.0")
    binding = build_observed_execution_binding(
        run_id="run-1", lane_id="H-DESI", admission_record_ids=("record-1", "record-2"), admission_bundle_id="desi-bundle-v1",
        authorization=authorization, candidate_commit="a" * 40, candidate_tree="b" * 40,
        executable_content_id="sha256:" + "c" * 64, engine_receipt=engine, started_at_utc=NOW.isoformat(),
    )
    with pytest.raises(ProductionBayesianError, match="terminal observed"):
        build_sampler_posterior_lineage(
            contract=contract, binding=binding, samples=np.zeros((3, 2)), normalized_weights=np.array([.2, .3, .5]),
            sampler_settings={"nlive": 10, "dlogz": .1, "bound": "multi", "sample": "rwalk", "seed": 1}, logz=1.0, logzerr=.1, terminal_run_receipt={},
        )
    terminal = {"observed_data_executed": True, "binding_content_id": binding.binding_content_id}
    with pytest.raises(ProductionBayesianError, match="ESS"):
        build_sampler_posterior_lineage(
            contract=contract, binding=binding, samples=np.zeros((3, 2)), normalized_weights=np.array([1., 0., 0.]),
            sampler_settings={"nlive": 10, "dlogz": .1, "bound": "multi", "sample": "rwalk", "seed": 1}, logz=1.0, logzerr=.1, terminal_run_receipt=terminal,
        )
    with pytest.raises(ProductionBayesianError, match="nlive"):
        build_sampler_posterior_lineage(
            contract=contract, binding=binding, samples=np.zeros((3, 2)), normalized_weights=np.array([.2, .3, .5]),
            sampler_settings={"nlive": 0, "dlogz": .1, "bound": "multi", "sample": "rwalk", "seed": 1}, logz=1.0, logzerr=.1, terminal_run_receipt=terminal,
        )
    lineage = build_sampler_posterior_lineage(
        contract=contract, binding=binding, samples=np.zeros((3, 2)), normalized_weights=np.array([.2, .3, .5]),
        sampler_settings={"nlive": 10, "dlogz": .1, "bound": "multi", "sample": "rwalk", "seed": 1}, logz=1.0, logzerr=.1, terminal_run_receipt=terminal,
    )
    assert assess_posterior_consumer_readiness(lineage=lineage, convergence_receipts=None).status is PosteriorConsumerStatus.BLOCKED_CONVERGENCE_EVIDENCE
    assert assess_posterior_consumer_readiness(lineage=lineage, convergence_receipts={"ess": True, "repeated_run_stability": True, "prior_sensitivity": True, "independent_engine_or_injection": True}).status is PosteriorConsumerStatus.READY_FOR_POSTERIOR_CONSUMERS


def test_BAYES_settings_and_response_are_computed_not_caller_claims() -> None:
    receipt = build_normalization_evidence_receipt(provider_id="provider", provider=provider, support={"a": "real"}, units={}, constants={})
    with pytest.raises(ProductionBayesianError, match="computed response rank"):
        build_production_model_contract(
            lane_id="H-DESI", model_id="model", parameter_schema={"a": {"support": "real"}, "b": {"support": "real"}},
            likelihood_receipt=receipt, prior_receipt=receipt, response_matrix=np.array([[1., 0.], [0., 0.]]), covariance_matrix=np.eye(2), block_ids=("a", "b"),
            log_likelihood=likelihood, prior_transform=prior, replicate_generator=replicate, discrepancies={"x": discrepancy},
        )


def test_AUTH_001_and_AUTH_002_historical_or_fake_receipts_cannot_authorize(tmp_path: Path) -> None:
    with pytest.raises(HumanExecutionAuthorizationError, match="exact V1 type"):
        validate_and_consume(
            object(), expected_lane_id="H-DESI", expected_human_gate_id="H-DESI", expected_analysis_plan_id="desi-plan-v1",
            expected_record_ids=("record-1", "record-2"), expected_bundle_id="desi-bundle-v1", expected_scope="one_lane",
            key_resolver=lambda _: KEY, nonce_ledger=tmp_path / "nonces", now_utc=NOW,
        )
