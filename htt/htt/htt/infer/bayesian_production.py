"""Fail-closed contracts for an authorized observed Bayesian sampler run.

This module is deliberately not a sampler and never opens a survey payload.
It separates the start-of-sampler authorization decision from the post-run
posterior-consumer decision so a posterior cannot be used to authorize the
sampler that would create it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import hashlib
import importlib.metadata
import inspect
import json
import math
from typing import Callable, Mapping, Sequence

import numpy as np

from common.human_execution_authorization import ValidatedHumanExecutionAuthorization


class ProductionBayesianError(ValueError):
    """A required observed-run proof object is absent, stale, or malformed."""


class SamplerStartStatus(str, Enum):
    BLOCKED_PRODUCTION_MODEL_CONTRACT_UNBOUND = "BLOCKED_PRODUCTION_MODEL_CONTRACT_UNBOUND"
    BLOCKED_OBSERVED_EXECUTION_NOT_AUTHORIZED = "BLOCKED_OBSERVED_EXECUTION_NOT_AUTHORIZED"
    BLOCKED_ENGINE_ENVIRONMENT = "BLOCKED_ENGINE_ENVIRONMENT"
    READY_TO_START_SAMPLER = "READY_TO_START_SAMPLER"


class PosteriorConsumerStatus(str, Enum):
    BLOCKED_NO_OBSERVED_EXECUTION_BINDING = "BLOCKED_NO_OBSERVED_EXECUTION_BINDING"
    BLOCKED_CONVERGENCE_EVIDENCE = "BLOCKED_CONVERGENCE_EVIDENCE"
    READY_FOR_POSTERIOR_CONSUMERS = "READY_FOR_POSTERIOR_CONSUMERS"


_VALIDATED = object()
_ALLOWED_BOUND = frozenset({"multi", "single", "balls", "cubes", "none"})
_ALLOWED_SAMPLE = frozenset({"auto", "unif", "rwalk", "slice", "rslice", "hslice"})


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _content_id(value: object) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def _nonempty(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProductionBayesianError(f"{field_name} must be a non-empty string")
    return value


def _immutable_json(value: object, field_name: str) -> object:
    try:
        return json.loads(_canonical(value))
    except (TypeError, ValueError) as exc:
        raise ProductionBayesianError(f"{field_name} must be JSON-canonicalizable") from exc


def _callable_id(function: Callable[..., object], field_name: str) -> str:
    if not callable(function):
        raise ProductionBayesianError(f"{field_name} must be callable")
    try:
        source = inspect.getsource(function)
    except (OSError, TypeError) as exc:
        raise ProductionBayesianError(f"{field_name} source identity is unavailable") from exc
    return _content_id({"module": function.__module__, "qualname": function.__qualname__, "source": source})


def _array_id(array: object, field_name: str) -> tuple[np.ndarray, str]:
    value = np.asarray(array, dtype=float)
    if value.ndim != 2 or not value.size or not np.all(np.isfinite(value)):
        raise ProductionBayesianError(f"{field_name} must be a finite non-empty matrix")
    return value, "sha256:" + hashlib.sha256(value.tobytes(order="C")).hexdigest()


@dataclass(frozen=True)
class NormalizationEvidenceReceipt:
    provider_id: str
    provider_content_id: str
    support: object
    units: object
    constants: object
    receipt_content_id: str
    _token: object = field(repr=False, compare=False, default=None)

    def __post_init__(self) -> None:
        if self._token is not _VALIDATED:
            raise ProductionBayesianError("normalization evidence is factory-issued only")


def build_normalization_evidence_receipt(*, provider_id: object, provider: Callable[..., object], support: object, units: object, constants: object) -> NormalizationEvidenceReceipt:
    frozen_support = _immutable_json(support, "support")
    frozen_units = _immutable_json(units, "units")
    frozen_constants = _immutable_json(constants, "constants")
    provider_content_id = _callable_id(provider, "provider")
    payload = {
        "schema": "htt.normalization_evidence_receipt.v1", "provider_id": _nonempty(provider_id, "provider_id"),
        "provider_content_id": provider_content_id, "support": frozen_support,
        "units": frozen_units, "constants": frozen_constants,
    }
    return NormalizationEvidenceReceipt(
        provider_id=payload["provider_id"], provider_content_id=provider_content_id,
        support=frozen_support, units=frozen_units, constants=frozen_constants,
        receipt_content_id=_content_id(payload), _token=_VALIDATED,
    )


@dataclass(frozen=True)
class ProductionModelContract:
    lane_id: str
    model_id: str
    parameter_schema: object
    likelihood_receipt: NormalizationEvidenceReceipt
    prior_receipt: NormalizationEvidenceReceipt
    response_content_id: str
    covariance_content_id: str
    computed_response_rank: int
    block_ids: tuple[str, ...]
    callable_content_ids: tuple[str, ...]
    discrepancy_ids: tuple[str, ...]
    contract_content_id: str


def build_production_model_contract(*, lane_id: object, model_id: object, parameter_schema: Mapping[str, Mapping[str, object]], likelihood_receipt: NormalizationEvidenceReceipt, prior_receipt: NormalizationEvidenceReceipt, response_matrix: object, covariance_matrix: object, block_ids: Sequence[object], log_likelihood: Callable[..., object], prior_transform: Callable[..., object], replicate_generator: Callable[..., object], discrepancies: Mapping[object, Callable[..., object]]) -> ProductionModelContract:
    if type(likelihood_receipt) is not NormalizationEvidenceReceipt or type(prior_receipt) is not NormalizationEvidenceReceipt:
        raise ProductionBayesianError("likelihood and prior require exact normalization evidence receipts")
    if not isinstance(parameter_schema, Mapping) or not parameter_schema:
        raise ProductionBayesianError("parameter_schema must be non-empty")
    frozen_schema: dict[str, object] = {}
    for name, specification in parameter_schema.items():
        key = _nonempty(name, "parameter schema name")
        if not isinstance(specification, Mapping) or "support" not in specification:
            raise ProductionBayesianError("each parameter schema item requires support")
        frozen_schema[key] = _immutable_json(specification, "parameter schema")
    response, response_id = _array_id(response_matrix, "response_matrix")
    covariance, covariance_id = _array_id(covariance_matrix, "covariance_matrix")
    if covariance.shape[0] != covariance.shape[1] or covariance.shape[0] != response.shape[0]:
        raise ProductionBayesianError("response/covariance dimensions differ")
    if not np.allclose(covariance, covariance.T, rtol=0.0, atol=1e-12):
        raise ProductionBayesianError("covariance must be symmetric")
    rank = int(np.linalg.matrix_rank(response))
    if rank < len(frozen_schema):
        raise ProductionBayesianError("computed response rank is deficient")
    if isinstance(block_ids, (str, bytes)) or len(block_ids) < 2:
        raise ProductionBayesianError("blockwise LOO requires at least two blocks")
    blocks = tuple(_nonempty(item, "block_id") for item in block_ids)
    if len(blocks) != len(set(blocks)):
        raise ProductionBayesianError("block_ids must be unique")
    if not isinstance(discrepancies, Mapping) or not discrepancies:
        raise ProductionBayesianError("discrepancies must be non-empty")
    canonical_discrepancies: dict[str, Callable[..., object]] = {}
    for name, function in discrepancies.items():
        key = _nonempty(str(name), "discrepancy name")
        if key in canonical_discrepancies:
            raise ProductionBayesianError("discrepancy names collide after canonical conversion")
        canonical_discrepancies[key] = function
    callable_ids = tuple(_callable_id(item, field) for item, field in ((log_likelihood, "log_likelihood"), (prior_transform, "prior_transform"), (replicate_generator, "replicate_generator")))
    callable_ids += tuple(_callable_id(function, f"discrepancy:{name}") for name, function in sorted(canonical_discrepancies.items()))
    payload = {
        "schema": "htt.production_bayesian_contract.v2", "lane_id": _nonempty(lane_id, "lane_id"),
        "model_id": _nonempty(model_id, "model_id"), "parameter_schema": frozen_schema,
        "likelihood_receipt": likelihood_receipt.receipt_content_id, "prior_receipt": prior_receipt.receipt_content_id,
        "response_content_id": response_id, "covariance_content_id": covariance_id, "computed_response_rank": rank,
        "block_ids": list(blocks), "callable_content_ids": list(callable_ids), "discrepancy_ids": sorted(canonical_discrepancies),
    }
    return ProductionModelContract(
        lane_id=payload["lane_id"], model_id=payload["model_id"], parameter_schema=frozen_schema,
        likelihood_receipt=likelihood_receipt, prior_receipt=prior_receipt,
        response_content_id=response_id, covariance_content_id=covariance_id,
        computed_response_rank=rank, block_ids=blocks, callable_content_ids=callable_ids,
        discrepancy_ids=tuple(sorted(canonical_discrepancies)), contract_content_id=_content_id(payload),
    )


@dataclass(frozen=True)
class EngineEnvironmentReceipt:
    package: str
    version: str
    receipt_content_id: str
    _token: object = field(repr=False, compare=False, default=None)

    def __post_init__(self) -> None:
        if self._token is not _VALIDATED:
            raise ProductionBayesianError("engine environment is validator-issued only")


def validate_dynesty_environment(*, expected_version: str) -> EngineEnvironmentReceipt:
    try:
        installed = importlib.metadata.version("dynesty")
    except importlib.metadata.PackageNotFoundError as exc:
        raise ProductionBayesianError("dynesty is not installed") from exc
    if installed != _nonempty(expected_version, "expected dynesty version"):
        raise ProductionBayesianError("dynesty version differs from registered version")
    payload = {"schema": "htt.dynesty_environment.v1", "package": "dynesty", "version": installed}
    return EngineEnvironmentReceipt(package="dynesty", version=installed, receipt_content_id=_content_id(payload), _token=_VALIDATED)


@dataclass(frozen=True)
class ObservedExecutionBinding:
    run_id: str
    lane_id: str
    admission_record_ids: tuple[str, ...]
    admission_bundle_id: str
    authorization_id: str
    authorization_hash: str
    candidate_commit: str
    candidate_tree: str
    executable_content_id: str
    engine_receipt_content_id: str
    started_at_utc: str
    binding_content_id: str


def build_observed_execution_binding(*, run_id: object, lane_id: object, admission_record_ids: Sequence[object], admission_bundle_id: object, authorization: ValidatedHumanExecutionAuthorization, candidate_commit: object, candidate_tree: object, executable_content_id: object, engine_receipt: EngineEnvironmentReceipt, started_at_utc: object) -> ObservedExecutionBinding:
    if type(authorization) is not ValidatedHumanExecutionAuthorization or type(engine_receipt) is not EngineEnvironmentReceipt:
        raise ProductionBayesianError("binding requires exact validated authorization and engine receipt")
    if authorization.lane_id != lane_id:
        raise ProductionBayesianError("authorization lane differs from observed binding lane")
    records = tuple(_nonempty(item, "admission_record_id") for item in admission_record_ids)
    if not records or len(records) != len(set(records)):
        raise ProductionBayesianError("admission records must be ordered and unique")
    if not isinstance(started_at_utc, str):
        raise ProductionBayesianError("started_at_utc must be UTC text")
    try:
        start = datetime.fromisoformat(started_at_utc.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ProductionBayesianError("started_at_utc must be ISO-8601") from exc
    if start.tzinfo is None or start.utcoffset() != timezone.utc.utcoffset(start):
        raise ProductionBayesianError("started_at_utc must be UTC")
    payload = {
        "schema": "htt.observed_execution_binding.v1", "run_id": _nonempty(run_id, "run_id"),
        "lane_id": _nonempty(lane_id, "lane_id"), "admission_record_ids": list(records),
        "admission_bundle_id": _nonempty(admission_bundle_id, "admission_bundle_id"),
        "authorization_id": authorization.authorization_id, "authorization_hash": authorization.authorization_hash,
        "candidate_commit": _nonempty(candidate_commit, "candidate_commit"), "candidate_tree": _nonempty(candidate_tree, "candidate_tree"),
        "executable_content_id": _nonempty(executable_content_id, "executable_content_id"),
        "engine_receipt_content_id": engine_receipt.receipt_content_id, "started_at_utc": started_at_utc,
    }
    return ObservedExecutionBinding(
        run_id=payload["run_id"], lane_id=payload["lane_id"], admission_record_ids=records,
        admission_bundle_id=payload["admission_bundle_id"], authorization_id=authorization.authorization_id,
        authorization_hash=authorization.authorization_hash, candidate_commit=payload["candidate_commit"],
        candidate_tree=payload["candidate_tree"], executable_content_id=payload["executable_content_id"],
        engine_receipt_content_id=engine_receipt.receipt_content_id, started_at_utc=started_at_utc,
        binding_content_id=_content_id(payload),
    )


@dataclass(frozen=True)
class SamplerStartDecision:
    status: SamplerStartStatus
    reasons: tuple[str, ...]


def assess_sampler_start_readiness(*, contract: ProductionModelContract | None, authorization: ValidatedHumanExecutionAuthorization | None, engine_receipt: EngineEnvironmentReceipt | None) -> SamplerStartDecision:
    if contract is None:
        return SamplerStartDecision(SamplerStartStatus.BLOCKED_PRODUCTION_MODEL_CONTRACT_UNBOUND, ("missing_production_model_contract",))
    if type(contract) is not ProductionModelContract:
        raise ProductionBayesianError("contract must be exact ProductionModelContract")
    if authorization is None:
        return SamplerStartDecision(SamplerStartStatus.BLOCKED_OBSERVED_EXECUTION_NOT_AUTHORIZED, ("missing_validated_human_authorization",))
    if type(authorization) is not ValidatedHumanExecutionAuthorization or authorization.lane_id != contract.lane_id:
        raise ProductionBayesianError("authorization does not bind the production contract lane")
    if engine_receipt is None:
        return SamplerStartDecision(SamplerStartStatus.BLOCKED_ENGINE_ENVIRONMENT, ("missing_registered_dynesty_environment",))
    if type(engine_receipt) is not EngineEnvironmentReceipt:
        raise ProductionBayesianError("engine receipt must be validator-issued")
    return SamplerStartDecision(SamplerStartStatus.READY_TO_START_SAMPLER, ())


def _validate_sampler_settings(settings: Mapping[str, object]) -> dict[str, object]:
    if not isinstance(settings, Mapping):
        raise ProductionBayesianError("sampler settings must be a mapping")
    required = {"nlive", "dlogz", "bound", "sample", "seed"}
    if set(settings) != required:
        raise ProductionBayesianError("sampler settings must have exactly registered controls")
    nlive, dlogz, seed = settings["nlive"], settings["dlogz"], settings["seed"]
    if type(nlive) is not int or nlive <= 0:
        raise ProductionBayesianError("nlive must be positive integer")
    if type(dlogz) not in (int, float) or not math.isfinite(float(dlogz)) or float(dlogz) <= 0:
        raise ProductionBayesianError("dlogz must be finite and positive")
    if settings["bound"] not in _ALLOWED_BOUND or settings["sample"] not in _ALLOWED_SAMPLE:
        raise ProductionBayesianError("unknown dynesty bound/sample setting")
    if type(seed) is not int:
        raise ProductionBayesianError("seed must be an integral non-bool")
    return dict(settings)


@dataclass(frozen=True)
class SamplerPosteriorLineage:
    observed_binding_content_id: str
    model_contract_content_id: str
    sample_content_id: str
    weight_content_id: str
    weighted_ess: float
    logz: float
    logzerr: float
    terminal_receipt_content_id: str
    sampler_settings: object
    lineage_content_id: str


def build_sampler_posterior_lineage(*, contract: ProductionModelContract, binding: ObservedExecutionBinding, samples: object, normalized_weights: object, sampler_settings: Mapping[str, object], logz: object, logzerr: object, terminal_run_receipt: Mapping[str, object]) -> SamplerPosteriorLineage:
    if type(contract) is not ProductionModelContract or type(binding) is not ObservedExecutionBinding:
        raise ProductionBayesianError("observed posterior requires exact contract and observed execution binding")
    if binding.lane_id != contract.lane_id:
        raise ProductionBayesianError("observed binding lane differs from model contract")
    if not isinstance(terminal_run_receipt, Mapping) or terminal_run_receipt.get("observed_data_executed") is not True or terminal_run_receipt.get("binding_content_id") != binding.binding_content_id:
        raise ProductionBayesianError("posterior lineage requires a terminal observed run receipt bound to this run")
    sample = np.asarray(samples, dtype=float)
    weights = np.asarray(normalized_weights, dtype=float)
    if sample.ndim != 2 or sample.shape[1] != len(contract.parameter_schema) or not np.all(np.isfinite(sample)):
        raise ProductionBayesianError("posterior samples do not match parameter schema")
    if weights.shape != (len(sample),) or not np.all(np.isfinite(weights)) or np.any(weights < 0) or not np.isclose(float(weights.sum()), 1.0, atol=1e-12, rtol=0.0):
        raise ProductionBayesianError("posterior weights must be finite normalized non-negative")
    ess = float(1.0 / np.square(weights).sum())
    if not np.isfinite(ess) or ess <= 1.0:
        raise ProductionBayesianError("posterior weighted ESS is insufficient")
    if type(logz) not in (int, float) or type(logzerr) not in (int, float) or not math.isfinite(float(logz)) or not math.isfinite(float(logzerr)) or float(logzerr) <= 0:
        raise ProductionBayesianError("logZ and positive finite logZerr are required")
    frozen_settings = _validate_sampler_settings(sampler_settings)
    sample_id = "sha256:" + hashlib.sha256(sample.tobytes(order="C")).hexdigest()
    weight_id = "sha256:" + hashlib.sha256(weights.tobytes(order="C")).hexdigest()
    terminal_id = _content_id(_immutable_json(terminal_run_receipt, "terminal_run_receipt"))
    payload = {"schema": "htt.observed_sampler_posterior_lineage.v2", "observed_binding_content_id": binding.binding_content_id, "model_contract_content_id": contract.contract_content_id, "sample_content_id": sample_id, "weight_content_id": weight_id, "weighted_ess": ess, "logz": float(logz), "logzerr": float(logzerr), "terminal_receipt_content_id": terminal_id, "sampler_settings": frozen_settings}
    return SamplerPosteriorLineage(
        observed_binding_content_id=binding.binding_content_id, model_contract_content_id=contract.contract_content_id,
        sample_content_id=sample_id, weight_content_id=weight_id, weighted_ess=ess, logz=float(logz),
        logzerr=float(logzerr), terminal_receipt_content_id=terminal_id, sampler_settings=frozen_settings,
        lineage_content_id=_content_id(payload),
    )


@dataclass(frozen=True)
class PosteriorConsumerDecision:
    status: PosteriorConsumerStatus
    reasons: tuple[str, ...]


def assess_posterior_consumer_readiness(*, lineage: SamplerPosteriorLineage | None, convergence_receipts: Mapping[str, object] | None) -> PosteriorConsumerDecision:
    if lineage is None:
        return PosteriorConsumerDecision(PosteriorConsumerStatus.BLOCKED_NO_OBSERVED_EXECUTION_BINDING, ("missing_observed_posterior_lineage",))
    if type(lineage) is not SamplerPosteriorLineage:
        raise ProductionBayesianError("consumer must receive exact observed posterior lineage")
    required = {"ess", "repeated_run_stability", "prior_sensitivity", "independent_engine_or_injection"}
    if not isinstance(convergence_receipts, Mapping) or set(convergence_receipts) != required or not all(convergence_receipts.values()):
        return PosteriorConsumerDecision(PosteriorConsumerStatus.BLOCKED_CONVERGENCE_EVIDENCE, ("missing_lane_preregistered_convergence_receipts",))
    return PosteriorConsumerDecision(PosteriorConsumerStatus.READY_FOR_POSTERIOR_CONSUMERS, ())
