"""Typed, fail-closed production Bayesian readiness contracts.

PR-288 validates Bayesian semantics only on analytic/synthetic Gaussian
fixtures.  This module deliberately does not run a sampler or open an
observational payload.  It records the contract that a later, authorized lane
must bind before nested-sampling output may feed PPC or blockwise LOO.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Mapping, Sequence

import numpy as np
import yaml

from htt.infer.bayesian_semantics import BayesianSemanticsError, canonical_content_id


class ProductionBayesianError(BayesianSemanticsError):
    """Raised when a production Bayesian contract is incomplete or mismatched."""


class LaneReadinessStatus(str, Enum):
    BLOCKED_PRODUCTION_MODEL_CONTRACT_UNBOUND = "BLOCKED_PRODUCTION_MODEL_CONTRACT_UNBOUND"
    BLOCKED_OBSERVED_EXECUTION_NOT_AUTHORIZED = "BLOCKED_OBSERVED_EXECUTION_NOT_AUTHORIZED"
    READY_FOR_AUTHORIZED_EXECUTION = "READY_FOR_AUTHORIZED_EXECUTION"


_REQUIRED_SAMPLER_SETTINGS = frozenset({"nlive", "dlogz", "bound", "sample", "seed"})
_EXPECTED_LANES = ("H-PLANCK", "H-DESI", "H-CF4", "H-JWST", "H-ACT")


def _nonempty(value: object, field: str) -> str:
    text = str(value).strip()
    if not text:
        raise ProductionBayesianError(f"{field} must be non-empty")
    return text


def _sha256_identity(value: object, field: str) -> str:
    text = _nonempty(value, field)
    if not text.startswith("sha256:") or len(text) != 71:
        raise ProductionBayesianError(f"{field} must be a sha256 content identity")
    try:
        int(text[7:], 16)
    except ValueError as exc:
        raise ProductionBayesianError(f"{field} must be a sha256 content identity") from exc
    return text


def _names(values: Sequence[object], field: str) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not values:
        raise ProductionBayesianError(f"{field} must be a non-empty sequence")
    parsed = tuple(_nonempty(value, field) for value in values)
    if len(parsed) != len(set(parsed)):
        raise ProductionBayesianError(f"{field} must be unique")
    return parsed


@dataclass(frozen=True)
class ProductionModelContract:
    """Non-executing specification for one observable-lane likelihood."""

    lane_id: str
    model_id: str
    parameter_schema: Mapping[str, Mapping[str, object]]
    likelihood_identity: str
    prior_identity: str
    data_identity: str
    covariance_identity: str
    block_ids: tuple[str, ...]
    response_rank: int
    log_likelihood: Callable[[np.ndarray], float]
    prior_transform: Callable[[np.ndarray], np.ndarray]
    replicate_generator: Callable[[np.ndarray, np.random.Generator], np.ndarray]
    discrepancies: Mapping[str, Callable[[np.ndarray, np.ndarray], float]]
    contract_content_id: str

    def unsigned_payload(self) -> dict[str, object]:
        return {
            "schema": "htt.production_bayesian_contract.v1",
            "lane_id": self.lane_id,
            "model_id": self.model_id,
            "parameter_schema": {
                name: dict(specification)
                for name, specification in self.parameter_schema.items()
            },
            "likelihood_identity": self.likelihood_identity,
            "prior_identity": self.prior_identity,
            "data_identity": self.data_identity,
            "covariance_identity": self.covariance_identity,
            "block_ids": list(self.block_ids),
            "response_rank": self.response_rank,
            "discrepancy_ids": sorted(self.discrepancies),
        }


def build_production_model_contract(
    *,
    lane_id: object,
    model_id: object,
    parameter_schema: Mapping[str, Mapping[str, object]],
    likelihood_identity: object,
    prior_identity: object,
    data_identity: object,
    covariance_identity: object,
    block_ids: Sequence[object],
    response_rank: object,
    likelihood_normalized: object,
    prior_normalized: object,
    log_likelihood: Callable[[np.ndarray], float],
    prior_transform: Callable[[np.ndarray], np.ndarray],
    replicate_generator: Callable[[np.ndarray, np.random.Generator], np.ndarray],
    discrepancies: Mapping[str, Callable[[np.ndarray, np.ndarray], float]],
) -> ProductionModelContract:
    lane = _nonempty(lane_id, "lane_id")
    if lane not in _EXPECTED_LANES:
        raise ProductionBayesianError("lane_id is not a registered observational lane")
    if not isinstance(parameter_schema, Mapping) or not parameter_schema:
        raise ProductionBayesianError("parameter_schema must be a non-empty mapping")
    schema: dict[str, Mapping[str, object]] = {}
    for raw_name, raw_specification in parameter_schema.items():
        name = _nonempty(raw_name, "parameter_schema name")
        if name in schema:
            raise ProductionBayesianError("parameter_schema names must be unique")
        if not isinstance(raw_specification, Mapping) or not raw_specification:
            raise ProductionBayesianError("each parameter schema entry must be a non-empty mapping")
        if "support" not in raw_specification:
            raise ProductionBayesianError("each parameter schema entry must declare support")
        schema[name] = dict(raw_specification)
    blocks = _names(block_ids, "block_ids")
    if len(blocks) < 2:
        raise ProductionBayesianError("blockwise LOO requires at least two registered blocks")
    if type(response_rank) is not int or response_rank < len(schema):
        raise ProductionBayesianError("response rank is deficient for the parameter schema")
    if likelihood_normalized is not True or prior_normalized is not True:
        raise ProductionBayesianError("likelihood and prior normalizations must be explicit")
    if not all(callable(item) for item in (log_likelihood, prior_transform, replicate_generator)):
        raise ProductionBayesianError("likelihood, prior transform, and replicate generator must be callable")
    if not isinstance(discrepancies, Mapping) or not discrepancies:
        raise ProductionBayesianError("discrepancy registry must be non-empty")
    discrepancy_map = {str(name): function for name, function in discrepancies.items()}
    if any(not name or not callable(function) for name, function in discrepancy_map.items()):
        raise ProductionBayesianError("discrepancy registry must contain named callables")
    provisional = ProductionModelContract(
        lane_id=lane,
        model_id=_nonempty(model_id, "model_id"),
        parameter_schema=schema,
        likelihood_identity=_sha256_identity(likelihood_identity, "likelihood_identity"),
        prior_identity=_sha256_identity(prior_identity, "prior_identity"),
        data_identity=_sha256_identity(data_identity, "data_identity"),
        covariance_identity=_sha256_identity(covariance_identity, "covariance_identity"),
        block_ids=blocks,
        response_rank=response_rank,
        log_likelihood=log_likelihood,
        prior_transform=prior_transform,
        replicate_generator=replicate_generator,
        discrepancies=discrepancy_map,
        contract_content_id="",
    )
    return ProductionModelContract(
        **{**provisional.__dict__, "contract_content_id": canonical_content_id(provisional.unsigned_payload())}
    )


@dataclass(frozen=True)
class SamplerPosteriorLineage:
    model_contract_content_id: str
    posterior_sample_content_sha256: str
    normalized_weight_content_sha256: str
    draw_count: int
    weighted_ess: float
    sampler_settings: Mapping[str, object]
    resampling_rule: str
    lineage_content_id: str


@dataclass(frozen=True)
class PosteriorConsumerPlan:
    """Exact non-executing handoff from sampler output to PPC and blockwise LOO."""

    model_contract_content_id: str
    posterior_lineage_content_id: str
    ppc_discrepancy_ids: tuple[str, ...]
    loo_block_ids: tuple[str, ...]
    plan_content_id: str


def build_sampler_posterior_lineage(
    *,
    contract: ProductionModelContract,
    samples: object,
    normalized_weights: object,
    sampler_settings: Mapping[str, object],
    resampling_rule: object,
) -> SamplerPosteriorLineage:
    if type(contract) is not ProductionModelContract:
        raise ProductionBayesianError("contract must be an exact ProductionModelContract")
    sample_array = np.asarray(samples, dtype=float)
    weight_array = np.asarray(normalized_weights, dtype=float)
    if sample_array.ndim != 2 or sample_array.shape[1] != len(contract.parameter_schema) or not np.all(np.isfinite(sample_array)):
        raise ProductionBayesianError("posterior samples do not match the parameter schema")
    if weight_array.shape != (len(sample_array),) or not np.all(np.isfinite(weight_array)) or np.any(weight_array < 0):
        raise ProductionBayesianError("posterior weights are invalid")
    if not np.isclose(float(weight_array.sum()), 1.0, rtol=0.0, atol=1e-12):
        raise ProductionBayesianError("posterior weights must be normalized")
    if not isinstance(sampler_settings, Mapping) or _REQUIRED_SAMPLER_SETTINGS - set(sampler_settings):
        raise ProductionBayesianError("sampler settings omit required nested-sampling controls")
    ess = float(1.0 / np.sum(np.square(weight_array)))
    if not np.isfinite(ess) or ess <= 0:
        raise ProductionBayesianError("weighted ESS is invalid")
    sample_id = canonical_content_id(sample_array)
    weight_id = canonical_content_id(weight_array)
    unsigned = {
        "schema": "htt.production_bayesian_posterior_lineage.v1",
        "model_contract_content_id": contract.contract_content_id,
        "posterior_sample_content_sha256": sample_id,
        "normalized_weight_content_sha256": weight_id,
        "draw_count": len(sample_array),
        "weighted_ess": ess,
        "sampler_settings": dict(sampler_settings),
        "resampling_rule": _nonempty(resampling_rule, "resampling_rule"),
    }
    return SamplerPosteriorLineage(
        model_contract_content_id=contract.contract_content_id,
        posterior_sample_content_sha256=sample_id,
        normalized_weight_content_sha256=weight_id,
        draw_count=len(sample_array),
        weighted_ess=ess,
        sampler_settings=dict(sampler_settings),
        resampling_rule=str(unsigned["resampling_rule"]),
        lineage_content_id=canonical_content_id(unsigned),
    )


def build_posterior_consumer_plan(
    *,
    contract: ProductionModelContract,
    lineage: SamplerPosteriorLineage,
    ppc_discrepancy_ids: Sequence[object],
    loo_block_ids: Sequence[object],
) -> PosteriorConsumerPlan:
    """Bind one weighted sampler lineage to the declared PPC/LOO consumers.

    This is deliberately a planning artifact: no likelihood, data payload, or
    replicate is evaluated here.  An authorized lane must consume this exact
    plan when it calculates posterior predictive checks and conditional LOO.
    """

    if type(contract) is not ProductionModelContract or type(lineage) is not SamplerPosteriorLineage:
        raise ProductionBayesianError("contract and lineage must be exact production types")
    if lineage.model_contract_content_id != contract.contract_content_id:
        raise ProductionBayesianError("posterior lineage does not bind this model contract")
    discrepancies = _names(ppc_discrepancy_ids, "ppc_discrepancy_ids")
    if set(discrepancies) != set(contract.discrepancies):
        raise ProductionBayesianError("PPC consumer must use the registered discrepancy family")
    blocks = _names(loo_block_ids, "loo_block_ids")
    if blocks != contract.block_ids:
        raise ProductionBayesianError("blockwise LOO consumer must preserve the registered partition")
    unsigned = {
        "schema": "htt.production_bayesian_posterior_consumer_plan.v1",
        "model_contract_content_id": contract.contract_content_id,
        "posterior_lineage_content_id": lineage.lineage_content_id,
        "ppc_discrepancy_ids": list(discrepancies),
        "loo_block_ids": list(blocks),
    }
    return PosteriorConsumerPlan(
        model_contract_content_id=contract.contract_content_id,
        posterior_lineage_content_id=lineage.lineage_content_id,
        ppc_discrepancy_ids=discrepancies,
        loo_block_ids=blocks,
        plan_content_id=canonical_content_id(unsigned),
    )


@dataclass(frozen=True)
class ObservationalLaneDescriptor:
    lane_id: str
    runner_patterns: tuple[str, ...]


@dataclass(frozen=True)
class LaneReadinessDecision:
    lane_id: str
    status: LaneReadinessStatus
    observed_data_executed: bool
    artifact_mode: str
    blocked_reasons: tuple[str, ...]


def load_observational_lane_descriptors(spec_path: Path) -> tuple[ObservationalLaneDescriptor, ...]:
    if spec_path.is_symlink() or not spec_path.is_file():
        raise ProductionBayesianError("PR-299 spec must be a regular file")
    try:
        payload = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ProductionBayesianError("PR-299 spec cannot be parsed") from exc
    if not isinstance(payload, dict) or payload.get("pr_id") != "PR-299":
        raise ProductionBayesianError("not the registered PR-299 spec")
    if payload.get("scope", {}).get("observed_data_execution") is not False:
        raise ProductionBayesianError("PR-299 must not execute observed data")
    rows = payload.get("readiness_lanes")
    if not isinstance(rows, list):
        raise ProductionBayesianError("readiness lane inventory is missing")
    descriptors = tuple(
        ObservationalLaneDescriptor(
            lane_id=_nonempty(row.get("lane_id"), "lane_id"),
            runner_patterns=_names(row.get("runner_patterns"), "runner_patterns"),
        )
        for row in rows
        if isinstance(row, dict)
    )
    if tuple(item.lane_id for item in descriptors) != _EXPECTED_LANES:
        raise ProductionBayesianError("readiness lane inventory drifted")
    if len(descriptors) != len(rows):
        raise ProductionBayesianError("readiness lane row is malformed")
    return descriptors


def assess_lane_readiness(
    descriptor: ObservationalLaneDescriptor,
    *,
    model_contract: ProductionModelContract | None = None,
    authorization_receipt: object | None = None,
) -> LaneReadinessDecision:
    if type(descriptor) is not ObservationalLaneDescriptor:
        raise ProductionBayesianError("descriptor must be an exact ObservationalLaneDescriptor")
    if model_contract is None:
        return LaneReadinessDecision(
            lane_id=descriptor.lane_id,
            status=LaneReadinessStatus.BLOCKED_PRODUCTION_MODEL_CONTRACT_UNBOUND,
            observed_data_executed=False,
            artifact_mode="readiness_only",
            blocked_reasons=("production_model_contract_unbound",),
        )
    if type(model_contract) is not ProductionModelContract or model_contract.lane_id != descriptor.lane_id:
        raise ProductionBayesianError("production contract does not match the lane descriptor")
    if authorization_receipt is None:
        return LaneReadinessDecision(
            lane_id=descriptor.lane_id,
            status=LaneReadinessStatus.BLOCKED_OBSERVED_EXECUTION_NOT_AUTHORIZED,
            observed_data_executed=False,
            artifact_mode="readiness_only",
            blocked_reasons=("missing_external_human_authorization_receipt",),
        )
    try:
        from common.data_identity import AuthorizationStatus, ExecutionAuthorizationReceipt
    except ImportError as exc:
        raise ProductionBayesianError(
            "PR-289 execution-authorization contract is unavailable"
        ) from exc
    lane_aliases = {
        "H-PLANCK": "PLANCK",
        "H-DESI": "DESI",
        "H-CF4": "CF4",
        "H-JWST": "JWST_SN",
        "H-ACT": "ACT",
    }
    if type(authorization_receipt) is not ExecutionAuthorizationReceipt:
        raise ProductionBayesianError("authorization receipt must use the PR-289 exact type")
    if authorization_receipt.lane_id != lane_aliases[descriptor.lane_id]:
        raise ProductionBayesianError("authorization receipt lane does not match the descriptor")
    if authorization_receipt.status is not AuthorizationStatus.AUTHORIZED:
        return LaneReadinessDecision(
            lane_id=descriptor.lane_id,
            status=LaneReadinessStatus.BLOCKED_OBSERVED_EXECUTION_NOT_AUTHORIZED,
            observed_data_executed=False,
            artifact_mode="readiness_only",
            blocked_reasons=("authorization_receipt_not_authorized",),
        )
    return LaneReadinessDecision(
        lane_id=descriptor.lane_id,
        status=LaneReadinessStatus.READY_FOR_AUTHORIZED_EXECUTION,
        observed_data_executed=False,
        artifact_mode="readiness_only",
        blocked_reasons=(),
    )


__all__ = [
    "LaneReadinessDecision",
    "LaneReadinessStatus",
    "ObservationalLaneDescriptor",
    "PosteriorConsumerPlan",
    "ProductionBayesianError",
    "ProductionModelContract",
    "SamplerPosteriorLineage",
    "assess_lane_readiness",
    "build_production_model_contract",
    "build_posterior_consumer_plan",
    "build_sampler_posterior_lineage",
    "load_observational_lane_descriptors",
]
