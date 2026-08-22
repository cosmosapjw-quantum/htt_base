"""Typed, fail-closed production Bayesian readiness contracts.

PR-288 validates Bayesian semantics only on analytic/synthetic Gaussian
fixtures.  This module deliberately does not run a sampler or open an
observational payload.  It records the contract that a later, authorized lane
must bind before nested-sampling output may feed PPC or blockwise LOO.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
import hashlib
from pathlib import Path
import subprocess
from typing import Callable, Mapping, Sequence

import numpy as np
import yaml

from htt.infer.bayesian_semantics import BayesianSemanticsError, canonical_content_id


class ProductionBayesianError(BayesianSemanticsError):
    """Raised when a production Bayesian contract is incomplete or mismatched."""


class LaneReadinessStatus(str, Enum):
    BLOCKED_PRODUCTION_MODEL_CONTRACT_UNBOUND = "BLOCKED_PRODUCTION_MODEL_CONTRACT_UNBOUND"
    BLOCKED_HUMAN_AUTHORIZATION = "BLOCKED_HUMAN_AUTHORIZATION"
    READY_TO_START_SAMPLER = "READY_TO_START_SAMPLER"
    BLOCKED_SAMPLER_TERMINAL = "BLOCKED_SAMPLER_TERMINAL"
    READY_FOR_POSTERIOR_CONSUMERS = "READY_FOR_POSTERIOR_CONSUMERS"


_REQUIRED_SAMPLER_SETTINGS = frozenset({"nlive", "dlogz", "bound", "sample", "seed"})
_EXPECTED_LANES = ("H-PLANCK", "H-DESI", "H-CF4", "H-JWST", "H-ACT")
_LANE_ALIASES = {
    "H-PLANCK": "PLANCK",
    "H-DESI": "DESI",
    "H-CF4": "CF4",
    "H-JWST": "JWST_SN",
    "H-ACT": "ACT",
}


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
    lane_admission_bundle_id: str | None
    ordered_admission_record_ids: tuple[str, ...]
    admitted_data_identity: str | None
    admitted_covariance_identity: str | None
    candidate_commit: str | None
    candidate_tree: str | None
    provider_source_bindings: Mapping[str, Mapping[str, str]]
    provider_configuration_binding: Mapping[str, str] | None
    provider_environment_binding: Mapping[str, str] | None
    contract_content_id: str

    def unsigned_payload(self) -> dict[str, object]:
        return {
            "schema": "htt.production_bayesian_contract.v2",
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
            "lane_admission_bundle_id": self.lane_admission_bundle_id,
            "ordered_admission_record_ids": list(self.ordered_admission_record_ids),
            "admitted_data_identity": self.admitted_data_identity,
            "admitted_covariance_identity": self.admitted_covariance_identity,
            "candidate_commit": self.candidate_commit,
            "candidate_tree": self.candidate_tree,
            "provider_source_bindings": {
                name: dict(binding)
                for name, binding in sorted(self.provider_source_bindings.items())
            },
            "provider_configuration_binding": (
                None
                if self.provider_configuration_binding is None
                else dict(self.provider_configuration_binding)
            ),
            "provider_environment_binding": (
                None
                if self.provider_environment_binding is None
                else dict(self.provider_environment_binding)
            ),
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
        lane_admission_bundle_id=None,
        ordered_admission_record_ids=(),
        admitted_data_identity=None,
        admitted_covariance_identity=None,
        candidate_commit=None,
        candidate_tree=None,
        provider_source_bindings={},
        provider_configuration_binding=None,
        provider_environment_binding=None,
        contract_content_id="",
    )
    return ProductionModelContract(
        **{**provisional.__dict__, "contract_content_id": canonical_content_id(provisional.unsigned_payload())}
    )


def _git(repo_root: Path, *args: str) -> str:
    try:
        completed = subprocess.run(
            ["git", "-C", str(repo_root), *args],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ProductionBayesianError(
            "production provider Git identity cannot be inspected"
        ) from exc
    if completed.returncode != 0:
        raise ProductionBayesianError(
            "production provider path is not tracked by the candidate"
        )
    return completed.stdout.rstrip("\n")


def _tracked_file_binding(repo_root: Path, raw_path: Path) -> dict[str, str]:
    if not isinstance(raw_path, Path):
        raise ProductionBayesianError("production provider path must be a Path")
    path = raw_path if raw_path.is_absolute() else repo_root / raw_path
    try:
        resolved = path.resolve(strict=True)
        relative = resolved.relative_to(repo_root).as_posix()
    except (OSError, ValueError) as exc:
        raise ProductionBayesianError(
            "production provider path must resolve inside the candidate"
        ) from exc
    if path.is_symlink() or not resolved.is_file():
        raise ProductionBayesianError(
            "production provider path must be a regular non-symlink file"
        )
    _git(repo_root, "ls-files", "--error-unmatch", "--", relative)
    return {
        "path": relative,
        "sha256": "sha256:" + hashlib.sha256(resolved.read_bytes()).hexdigest(),
    }


def _callable_source_path(function: Callable[..., object], *, field: str) -> Path:
    code = getattr(function, "__code__", None)
    filename = getattr(code, "co_filename", None)
    if not isinstance(filename, str) or not filename:
        raise ProductionBayesianError(
            f"{field} must be a Python callable with a bindable source file"
        )
    return Path(filename)


def _provider_source_bindings(
    contract: ProductionModelContract, *, repo_root: Path
) -> dict[str, Mapping[str, str]]:
    functions: dict[str, Callable[..., object]] = {
        "log_likelihood": contract.log_likelihood,
        "prior_transform": contract.prior_transform,
        "replicate_generator": contract.replicate_generator,
        **{
            f"discrepancy:{name}": function
            for name, function in sorted(contract.discrepancies.items())
        },
    }
    return {
        role: _tracked_file_binding(
            repo_root, _callable_source_path(function, field=role)
        )
        for role, function in functions.items()
    }


def _unbound_contract(contract: ProductionModelContract) -> ProductionModelContract:
    provisional = replace(
        contract,
        lane_admission_bundle_id=None,
        ordered_admission_record_ids=(),
        admitted_data_identity=None,
        admitted_covariance_identity=None,
        candidate_commit=None,
        candidate_tree=None,
        provider_source_bindings={},
        provider_configuration_binding=None,
        provider_environment_binding=None,
        contract_content_id="",
    )
    return replace(
        provisional,
        contract_content_id=canonical_content_id(provisional.unsigned_payload()),
    )


def bind_production_model_contract(
    *,
    contract: ProductionModelContract,
    lane_spec: object,
    admission_decision: object,
    candidate_identity: object,
    provider_configuration_path: Path,
    provider_environment_path: Path,
) -> ProductionModelContract:
    """Bind a semantic model to exact admitted bytes and clean provider code."""

    if type(contract) is not ProductionModelContract:
        raise ProductionBayesianError(
            "contract must be an exact ProductionModelContract"
        )
    try:
        from common.human_execution_authorization import (
            CandidateIdentityV1,
            admitted_covariance_identity,
            admitted_data_identity,
            replay_complete_lane_admission,
            revalidate_clean_candidate_identity,
        )
    except ImportError as exc:
        raise ProductionBayesianError(
            "PR-304 admission binding contract is unavailable"
        ) from exc
    if type(candidate_identity) is not CandidateIdentityV1:
        raise ProductionBayesianError(
            "production binding requires a factory-derived candidate identity"
        )
    try:
        candidate = revalidate_clean_candidate_identity(candidate_identity)
        replayed = replay_complete_lane_admission(
            lane_spec=lane_spec,
            admission_decision=admission_decision,
            candidate_identity=candidate,
        )
        data_identity = admitted_data_identity(replayed)
        covariance_identity = admitted_covariance_identity(replayed)
    except ValueError as exc:
        raise ProductionBayesianError(
            "production model cannot replay its exact admission binding"
        ) from exc
    if _LANE_ALIASES.get(contract.lane_id) != replayed.lane_id:
        raise ProductionBayesianError(
            "production model lane does not match replayed admission"
        )
    if contract.data_identity != data_identity:
        raise ProductionBayesianError(
            "production model data identity does not equal admitted data identity"
        )
    if contract.covariance_identity != covariance_identity:
        raise ProductionBayesianError(
            "production model covariance identity does not equal admitted covariance identity"
        )
    base = _unbound_contract(contract)
    source_bindings = _provider_source_bindings(base, repo_root=candidate.repo_root)
    configuration_binding = _tracked_file_binding(
        candidate.repo_root, provider_configuration_path
    )
    environment_binding = _tracked_file_binding(
        candidate.repo_root, provider_environment_path
    )
    try:
        candidate_after_read = revalidate_clean_candidate_identity(candidate)
    except ValueError as exc:
        raise ProductionBayesianError(
            "production provider candidate changed during binding"
        ) from exc
    if candidate_after_read.as_payload() != candidate.as_payload():
        raise ProductionBayesianError(
            "production provider candidate changed during binding"
        )
    provisional = replace(
        base,
        lane_admission_bundle_id=replayed.lane_admission_bundle_id,
        ordered_admission_record_ids=tuple(
            record.record_id for record in replayed.records
        ),
        admitted_data_identity=data_identity,
        admitted_covariance_identity=covariance_identity,
        candidate_commit=candidate.commit,
        candidate_tree=candidate.tree,
        provider_source_bindings=source_bindings,
        provider_configuration_binding=configuration_binding,
        provider_environment_binding=environment_binding,
        contract_content_id="",
    )
    return replace(
        provisional,
        contract_content_id=canonical_content_id(provisional.unsigned_payload()),
    )


def revalidate_bound_production_model_contract(
    *,
    contract: ProductionModelContract,
    lane_spec: object,
    admission_decision: object,
    candidate_identity: object,
) -> ProductionModelContract:
    """Rebuild every binding from live clean state before an authority use."""

    if type(contract) is not ProductionModelContract:
        raise ProductionBayesianError(
            "contract must be an exact ProductionModelContract"
        )
    if (
        contract.provider_configuration_binding is None
        or contract.provider_environment_binding is None
    ):
        raise ProductionBayesianError(
            "production model contract is not admission/provider bound"
        )
    configuration_path = Path(
        _nonempty(
            contract.provider_configuration_binding.get("path"),
            "provider configuration path",
        )
    )
    environment_path = Path(
        _nonempty(
            contract.provider_environment_binding.get("path"),
            "provider environment path",
        )
    )
    rebuilt = bind_production_model_contract(
        contract=_unbound_contract(contract),
        lane_spec=lane_spec,
        admission_decision=admission_decision,
        candidate_identity=candidate_identity,
        provider_configuration_path=configuration_path,
        provider_environment_path=environment_path,
    )
    if (
        rebuilt.unsigned_payload() != contract.unsigned_payload()
        or rebuilt.contract_content_id != contract.contract_content_id
    ):
        raise ProductionBayesianError(
            "production model admission or provider binding is stale or forged"
        )
    return rebuilt


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


def _consumer_plan_unsigned_payload(
    *,
    model_contract_content_id: str,
    posterior_lineage_content_id: str,
    ppc_discrepancy_ids: Sequence[object],
    loo_block_ids: Sequence[object],
) -> dict[str, object]:
    """Canonical payload for a plan that may authorize posterior consumers."""

    return {
        "schema": "htt.production_bayesian_posterior_consumer_plan.v1",
        "model_contract_content_id": model_contract_content_id,
        "posterior_lineage_content_id": posterior_lineage_content_id,
        "ppc_discrepancy_ids": list(ppc_discrepancy_ids),
        "loo_block_ids": list(loo_block_ids),
    }


def _canonical_ppc_discrepancy_ids(contract: ProductionModelContract) -> tuple[str, ...]:
    """Return the sole stable order accepted by a posterior-consumer plan."""

    return tuple(sorted(contract.discrepancies))


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
    if discrepancies != _canonical_ppc_discrepancy_ids(contract):
        raise ProductionBayesianError("PPC consumer must use the registered discrepancy family")
    blocks = _names(loo_block_ids, "loo_block_ids")
    if blocks != contract.block_ids:
        raise ProductionBayesianError("blockwise LOO consumer must preserve the registered partition")
    unsigned = _consumer_plan_unsigned_payload(
        model_contract_content_id=contract.contract_content_id,
        posterior_lineage_content_id=lineage.lineage_content_id,
        ppc_discrepancy_ids=discrepancies,
        loo_block_ids=blocks,
    )
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
    admission_decision: object | None = None,
    validated_human_authorization: object | None = None,
    candidate_identity: object | None = None,
    authorization_receipt: object | None = None,
    posterior_lineage: SamplerPosteriorLineage | None = None,
    posterior_consumer_plan: PosteriorConsumerPlan | None = None,
) -> LaneReadinessDecision:
    if type(descriptor) is not ObservationalLaneDescriptor:
        raise ProductionBayesianError("descriptor must be an exact ObservationalLaneDescriptor")
    if authorization_receipt is not None:
        raise ProductionBayesianError(
            "PR-289 NOT_AUTHORIZED receipts cannot substitute for human authorization"
        )
    if model_contract is None or admission_decision is None:
        reasons = []
        if model_contract is None:
            reasons.append("production_model_contract_unbound")
        if admission_decision is None:
            reasons.append("complete_pr289_lane_admission_unbound")
        return LaneReadinessDecision(
            lane_id=descriptor.lane_id,
            status=LaneReadinessStatus.BLOCKED_PRODUCTION_MODEL_CONTRACT_UNBOUND,
            observed_data_executed=False,
            artifact_mode="readiness_only",
            blocked_reasons=tuple(reasons),
        )
    if type(model_contract) is not ProductionModelContract or model_contract.lane_id != descriptor.lane_id:
        raise ProductionBayesianError("production contract does not match the lane descriptor")
    try:
        from common.data_identity import load_lane_registry
        from common.human_execution_authorization import (
            CandidateIdentityV1,
            ValidatedHumanExecutionAuthorization,
            replay_complete_lane_admission,
            revalidate_cached_human_execution_authorization,
            revalidate_clean_candidate_identity,
        )
    except ImportError as exc:
        raise ProductionBayesianError(
            "PR-304 admission-bound human authorization contract is unavailable"
        ) from exc
    if candidate_identity is None:
        return LaneReadinessDecision(
            lane_id=descriptor.lane_id,
            status=LaneReadinessStatus.BLOCKED_PRODUCTION_MODEL_CONTRACT_UNBOUND,
            observed_data_executed=False,
            artifact_mode="readiness_only",
            blocked_reasons=("clean_candidate_identity_unbound",),
        )
    if type(candidate_identity) is not CandidateIdentityV1:
        raise ProductionBayesianError(
            "candidate identity must be factory-derived for readiness"
        )
    try:
        candidate = revalidate_clean_candidate_identity(candidate_identity)
        lane_spec = load_lane_registry(
            candidate.repo_root
            / "docs/research_program/post_pr275/data_registry_v2/LANE_REGISTRY_V2.json"
        ).lane(_LANE_ALIASES[descriptor.lane_id])
        replayed_admission = replay_complete_lane_admission(
            lane_spec=lane_spec,
            admission_decision=admission_decision,
            candidate_identity=candidate,
        )
    except (KeyError, ValueError) as exc:
        raise ProductionBayesianError("PR-289 complete lane admission does not bind this descriptor") from exc
    try:
        revalidate_bound_production_model_contract(
            contract=model_contract,
            lane_spec=lane_spec,
            admission_decision=replayed_admission,
            candidate_identity=candidate_identity,
        )
    except (ProductionBayesianError, ValueError) as exc:
        raise ProductionBayesianError(
            "production model admission/provider binding failed readiness replay"
        ) from exc
    if validated_human_authorization is None:
        return LaneReadinessDecision(
            lane_id=descriptor.lane_id,
            status=LaneReadinessStatus.BLOCKED_HUMAN_AUTHORIZATION,
            observed_data_executed=False,
            artifact_mode="readiness_only",
            blocked_reasons=("missing_external_human_authorization_receipt",),
        )
    if type(validated_human_authorization) is not ValidatedHumanExecutionAuthorization:
        raise ProductionBayesianError("human authorization must be a validator-built PR-304 capability")
    try:
        revalidate_cached_human_execution_authorization(
            cached=validated_human_authorization,
            lane_spec=lane_spec,
            admission_decision=replayed_admission,
            candidate_identity=candidate_identity,
        )
    except ValueError as exc:
        raise ProductionBayesianError(
            "signed human authorization failed just-in-time revalidation"
        ) from exc
    if posterior_lineage is None and posterior_consumer_plan is None:
        return LaneReadinessDecision(
            lane_id=descriptor.lane_id,
            status=LaneReadinessStatus.READY_TO_START_SAMPLER,
            observed_data_executed=False,
            artifact_mode="readiness_only",
            blocked_reasons=(),
        )
    if posterior_lineage is None or posterior_consumer_plan is None:
        return LaneReadinessDecision(
            lane_id=descriptor.lane_id,
            status=LaneReadinessStatus.BLOCKED_SAMPLER_TERMINAL,
            observed_data_executed=False,
            artifact_mode="readiness_only",
            blocked_reasons=("sampler_lineage_or_ppc_loo_consumer_unbound",),
        )
    if (
        type(posterior_lineage) is not SamplerPosteriorLineage
        or type(posterior_consumer_plan) is not PosteriorConsumerPlan
        or posterior_lineage.model_contract_content_id != model_contract.contract_content_id
        or posterior_consumer_plan.model_contract_content_id != model_contract.contract_content_id
        or posterior_consumer_plan.posterior_lineage_content_id
        != posterior_lineage.lineage_content_id
    ):
        raise ProductionBayesianError(
            "posterior lineage and PPC/LOO consumer plan do not bind this model contract"
        )
    if (
        _names(posterior_consumer_plan.ppc_discrepancy_ids, "ppc_discrepancy_ids")
        != _canonical_ppc_discrepancy_ids(model_contract)
    ):
        raise ProductionBayesianError(
            "PPC consumer plan does not use the exact registered discrepancy tuple"
        )
    if posterior_consumer_plan.loo_block_ids != model_contract.block_ids:
        raise ProductionBayesianError(
            "LOO consumer plan does not preserve the registered block partition"
        )
    expected_plan_content_id = canonical_content_id(
        _consumer_plan_unsigned_payload(
            model_contract_content_id=model_contract.contract_content_id,
            posterior_lineage_content_id=posterior_lineage.lineage_content_id,
            ppc_discrepancy_ids=posterior_consumer_plan.ppc_discrepancy_ids,
            loo_block_ids=posterior_consumer_plan.loo_block_ids,
        )
    )
    if posterior_consumer_plan.plan_content_id != expected_plan_content_id:
        raise ProductionBayesianError("PPC/LOO consumer plan content identity is forged or stale")
    return LaneReadinessDecision(
        lane_id=descriptor.lane_id,
        status=LaneReadinessStatus.READY_FOR_POSTERIOR_CONSUMERS,
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
    "bind_production_model_contract",
    "build_production_model_contract",
    "build_posterior_consumer_plan",
    "build_sampler_posterior_lineage",
    "load_observational_lane_descriptors",
    "revalidate_bound_production_model_contract",
]
