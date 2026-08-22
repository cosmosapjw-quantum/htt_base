"""Typed, fail-closed production Bayesian readiness contracts.

PR-288 validates Bayesian semantics only on analytic/synthetic Gaussian
fixtures.  This module deliberately does not run a sampler or open an
observational payload.  It records the contract that a later, authorized lane
must bind before nested-sampling output may feed PPC or blockwise LOO.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, replace
from enum import Enum
import hashlib
from importlib import metadata
import json
import marshal
from pathlib import Path
import platform
import sys
from types import MappingProxyType
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


def _strict_json_bytes(raw: bytes, *, field: str) -> Mapping[str, object]:
    def no_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ProductionBayesianError(f"{field} contains duplicate keys")
            result[key] = value
        return result

    try:
        payload = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=no_duplicates,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ProductionBayesianError(f"{field} contains {token}")
            ),
        )
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ProductionBayesianError(f"{field} is not strict UTF-8 JSON") from exc
    if not isinstance(payload, Mapping):
        raise ProductionBayesianError(f"{field} must contain a mapping")
    try:
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ProductionBayesianError(f"{field} is not canonical finite JSON") from exc
    return payload


def _exact_mapping(
    value: object, *, fields: frozenset[str], field: str
) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or set(value) != fields:
        raise ProductionBayesianError(f"{field} fields drifted")
    return value


def _relative_path(value: object, field: str) -> str:
    text = _nonempty(value, field)
    path = Path(text)
    if (
        path.is_absolute()
        or path.as_posix() != text
        or text.startswith(".")
        or ".." in path.parts
        or any(character in text for character in ("\x00", "\n", "\r", ":"))
    ):
        raise ProductionBayesianError(f"{field} must be candidate-relative")
    return text


@dataclass(frozen=True)
class RuntimeEnvironmentReceiptV1:
    python_executable: str
    python_implementation: str
    python_version: str
    platform_system: str
    platform_machine: str
    package_versions: Mapping[str, str]
    native_extension_sha256: Mapping[str, str]
    receipt_id: str

    def unsigned_payload(self) -> dict[str, object]:
        return {
            "schema": "htt.runtime_environment_receipt.v1",
            "python_executable": self.python_executable,
            "python_implementation": self.python_implementation,
            "python_version": self.python_version,
            "platform_system": self.platform_system,
            "platform_machine": self.platform_machine,
            "package_versions": dict(sorted(self.package_versions.items())),
            "native_extension_sha256": dict(
                sorted(self.native_extension_sha256.items())
            ),
        }

    def as_payload(self) -> dict[str, object]:
        return {**self.unsigned_payload(), "receipt_id": self.receipt_id}


def capture_runtime_environment_receipt(
    required_packages: Sequence[object],
) -> RuntimeEnvironmentReceiptV1:
    packages = _names(required_packages, "required runtime package")
    versions: dict[str, str] = {}
    for package in packages:
        try:
            versions[package] = metadata.version(package)
        except metadata.PackageNotFoundError as exc:
            raise ProductionBayesianError(
                f"required runtime package is not installed: {package}"
            ) from exc
    native: dict[str, str] = {}
    for name, module in (
        ("numpy._core._multiarray_umath", np._core._multiarray_umath),
    ):
        raw_path = getattr(module, "__file__", None)
        if not isinstance(raw_path, str):
            raise ProductionBayesianError("live native extension identity is unavailable")
        path = Path(raw_path).resolve(strict=True)
        with path.open("rb") as handle:
            native[name] = "sha256:" + hashlib.file_digest(handle, "sha256").hexdigest()
    provisional = RuntimeEnvironmentReceiptV1(
        python_executable=str(Path(sys.executable).resolve(strict=True)),
        python_implementation=platform.python_implementation(),
        python_version=platform.python_version(),
        platform_system=platform.system(),
        platform_machine=platform.machine(),
        package_versions=versions,
        native_extension_sha256=native,
        receipt_id="",
    )
    return replace(
        provisional,
        receipt_id=canonical_content_id(provisional.unsigned_payload()),
    )


@dataclass(frozen=True)
class ProviderManifestV1:
    manifest_binding: Mapping[str, str]
    provider_path: str
    dependency_paths: tuple[str, ...]
    configuration_path: str
    environment_contract_path: str
    response_matrix_path: str
    normalization_evidence_path: str
    execution_plan_path: str
    log_likelihood_symbol: str
    prior_transform_symbol: str
    replicate_generator_symbol: str
    discrepancy_symbols: Mapping[str, str]
    manifest_content_id: str

    def unsigned_payload(self) -> dict[str, object]:
        return {
            "schema": "htt.provider_manifest.v1",
            "manifest_binding": dict(self.manifest_binding),
            "provider_path": self.provider_path,
            "dependency_paths": list(self.dependency_paths),
            "configuration_path": self.configuration_path,
            "environment_contract_path": self.environment_contract_path,
            "response_matrix_path": self.response_matrix_path,
            "normalization_evidence_path": self.normalization_evidence_path,
            "execution_plan_path": self.execution_plan_path,
            "exports": {
                "log_likelihood": self.log_likelihood_symbol,
                "prior_transform": self.prior_transform_symbol,
                "replicate_generator": self.replicate_generator_symbol,
                "discrepancies": dict(sorted(self.discrepancy_symbols.items())),
            },
        }


_PROVIDER_FACTORY_TOKEN = object()


@dataclass(frozen=True)
class LoadedCandidateProviderV1:
    manifest: ProviderManifestV1
    source_bindings: Mapping[str, Mapping[str, str]]
    code_fingerprints: Mapping[str, str]
    log_likelihood: Callable[[np.ndarray], float]
    prior_transform: Callable[[np.ndarray], np.ndarray]
    replicate_generator: Callable[[np.ndarray, np.random.Generator], np.ndarray]
    discrepancies: Mapping[str, Callable[[np.ndarray, np.ndarray], float]]
    provider_content_id: str
    _construction_token: object

    def __post_init__(self) -> None:
        if self._construction_token is not _PROVIDER_FACTORY_TOKEN:
            raise ProductionBayesianError(
                "provider must be factory-loaded from candidate Git blobs"
            )

    def unsigned_payload(self) -> dict[str, object]:
        return {
            "schema": "htt.loaded_candidate_provider.v1",
            "manifest_content_id": self.manifest.manifest_content_id,
            "source_bindings": {
                key: dict(value) for key, value in sorted(self.source_bindings.items())
            },
            "code_fingerprints": dict(sorted(self.code_fingerprints.items())),
        }


def _candidate_blob_api():
    try:
        from common.human_execution_authorization import (
            CandidateIdentityV1,
            candidate_blob_binding,
            read_candidate_blob,
            revalidate_clean_candidate_identity,
        )
    except ImportError as exc:
        raise ProductionBayesianError("PR-304 Git-blob API is unavailable") from exc
    return (
        CandidateIdentityV1,
        candidate_blob_binding,
        read_candidate_blob,
        revalidate_clean_candidate_identity,
    )


def load_candidate_provider(
    *, candidate_identity: object, manifest_path: Path
) -> LoadedCandidateProviderV1:
    CandidateIdentityV1, binding_for, read_blob, revalidate = _candidate_blob_api()
    if type(candidate_identity) is not CandidateIdentityV1:
        raise ProductionBayesianError(
            "provider loading requires a factory-derived candidate identity"
        )
    if not isinstance(manifest_path, Path):
        raise ProductionBayesianError("provider manifest path must be a Path")
    try:
        candidate = revalidate(candidate_identity)
        relative_manifest = _relative_path(manifest_path.as_posix(), "provider manifest")
        manifest_binding = binding_for(candidate, relative_manifest)
        payload = _exact_mapping(
            _strict_json_bytes(read_blob(candidate, relative_manifest), field="provider manifest"),
            field="provider manifest",
            fields=frozenset(
                {
                    "schema",
                    "provider_path",
                    "dependency_paths",
                    "configuration_path",
                    "environment_contract_path",
                    "response_matrix_path",
                    "normalization_evidence_path",
                    "execution_plan_path",
                    "exports",
                }
            ),
        )
    except ValueError as exc:
        raise ProductionBayesianError("provider manifest Git blob is unavailable") from exc
    if payload["schema"] != "htt.provider_manifest.v1":
        raise ProductionBayesianError("provider manifest schema drifted")
    raw_dependencies = payload["dependency_paths"]
    if isinstance(raw_dependencies, (str, bytes)) or not isinstance(
        raw_dependencies, Sequence
    ):
        raise ProductionBayesianError("provider dependencies must be a sequence")
    dependencies = tuple(
        _relative_path(item, "provider dependency") for item in raw_dependencies
    )
    if len(dependencies) != len(set(dependencies)):
        raise ProductionBayesianError("provider dependencies must be unique")
    exports = _exact_mapping(
        payload["exports"],
        field="provider exports",
        fields=frozenset(
            {
                "log_likelihood",
                "prior_transform",
                "replicate_generator",
                "discrepancies",
            }
        ),
    )
    raw_discrepancies = exports["discrepancies"]
    if not isinstance(raw_discrepancies, Mapping) or not raw_discrepancies:
        raise ProductionBayesianError("provider discrepancies are missing")
    discrepancy_symbols = {
        _nonempty(name, "discrepancy id"): _nonempty(symbol, "discrepancy symbol")
        for name, symbol in raw_discrepancies.items()
    }
    provider_path = _relative_path(payload["provider_path"], "provider path")
    manifest = ProviderManifestV1(
        manifest_binding=manifest_binding,
        provider_path=provider_path,
        dependency_paths=dependencies,
        configuration_path=_relative_path(
            payload["configuration_path"], "provider configuration path"
        ),
        environment_contract_path=_relative_path(
            payload["environment_contract_path"], "environment contract path"
        ),
        response_matrix_path=_relative_path(
            payload["response_matrix_path"], "response matrix path"
        ),
        normalization_evidence_path=_relative_path(
            payload["normalization_evidence_path"], "normalization evidence path"
        ),
        execution_plan_path=_relative_path(
            payload["execution_plan_path"], "execution plan path"
        ),
        log_likelihood_symbol=_nonempty(
            exports["log_likelihood"], "log_likelihood symbol"
        ),
        prior_transform_symbol=_nonempty(
            exports["prior_transform"], "prior_transform symbol"
        ),
        replicate_generator_symbol=_nonempty(
            exports["replicate_generator"], "replicate_generator symbol"
        ),
        discrepancy_symbols=discrepancy_symbols,
        manifest_content_id="",
    )
    manifest = replace(
        manifest,
        manifest_content_id=canonical_content_id(manifest.unsigned_payload()),
    )
    source = read_blob(candidate, provider_path)
    try:
        parsed = ast.parse(source, filename=f"git:{candidate.commit}:{provider_path}")
    except (SyntaxError, ValueError) as exc:
        raise ProductionBayesianError("provider Git blob is not valid Python") from exc
    if any(isinstance(node, (ast.Import, ast.ImportFrom, ast.Global, ast.Nonlocal)) for node in ast.walk(parsed)):
        raise ProductionBayesianError("provider imports and global mutation are forbidden")
    dependency_blobs = {
        path: read_blob(candidate, path) for path in dependencies
    }
    safe_builtins = {
        "abs": abs,
        "float": float,
        "int": int,
        "len": len,
        "max": max,
        "min": min,
        "range": range,
        "sum": sum,
        "tuple": tuple,
        "ValueError": ValueError,
    }
    namespace: dict[str, object] = {
        "__builtins__": MappingProxyType(safe_builtins),
        "__file__": f"git:{candidate.commit}:{provider_path}",
        "__name__": "__htt_candidate_provider__",
        "np": np,
        "DEPENDENCY_BLOBS": MappingProxyType(dependency_blobs),
    }
    try:
        exec(compile(parsed, namespace["__file__"], "exec"), namespace)
    except Exception as exc:
        raise ProductionBayesianError("candidate provider initialization failed") from exc
    roles = {
        "log_likelihood": manifest.log_likelihood_symbol,
        "prior_transform": manifest.prior_transform_symbol,
        "replicate_generator": manifest.replicate_generator_symbol,
        **{
            f"discrepancy:{name}": symbol
            for name, symbol in sorted(manifest.discrepancy_symbols.items())
        },
    }
    functions: dict[str, Callable[..., object]] = {}
    fingerprints: dict[str, str] = {}
    for role, symbol in roles.items():
        function = namespace.get(symbol)
        if not callable(function) or getattr(function, "__globals__", None) is not namespace:
            raise ProductionBayesianError(f"provider export is not factory-loaded: {role}")
        if (
            getattr(function, "__closure__", None) is not None
            or getattr(function, "__defaults__", None) is not None
            or getattr(function, "__kwdefaults__", None) is not None
        ):
            raise ProductionBayesianError(
                f"provider export has unbound runtime state: {role}"
            )
        functions[role] = function
        fingerprints[role] = "sha256:" + hashlib.sha256(
            marshal.dumps(function.__code__)
        ).hexdigest()
    bindings: dict[str, Mapping[str, str]] = {
        "manifest": manifest_binding,
        "provider": binding_for(candidate, provider_path),
        **{
            f"dependency:{path}": binding_for(candidate, path)
            for path in dependencies
        },
    }
    provisional = LoadedCandidateProviderV1(
        manifest=manifest,
        source_bindings=bindings,
        code_fingerprints=fingerprints,
        log_likelihood=functions["log_likelihood"],
        prior_transform=functions["prior_transform"],
        replicate_generator=functions["replicate_generator"],
        discrepancies={
            name: functions[f"discrepancy:{name}"]
            for name in manifest.discrepancy_symbols
        },
        provider_content_id="",
        _construction_token=_PROVIDER_FACTORY_TOKEN,
    )
    return replace(
        provisional,
        provider_content_id=canonical_content_id(provisional.unsigned_payload()),
    )


@dataclass(frozen=True)
class ComputedResponseRankReceiptV1:
    response_matrix_binding: Mapping[str, str]
    feature_order: tuple[str, ...]
    parameter_order: tuple[str, ...]
    singular_value_threshold: float
    computed_rank: int
    covariance_identity: str
    lane_admission_bundle_id: str
    receipt_id: str

    def unsigned_payload(self) -> dict[str, object]:
        return {
            "schema": "htt.computed_response_rank_receipt.v1",
            "response_matrix_binding": dict(self.response_matrix_binding),
            "feature_order": list(self.feature_order),
            "parameter_order": list(self.parameter_order),
            "singular_value_threshold": self.singular_value_threshold,
            "computed_rank": self.computed_rank,
            "covariance_identity": self.covariance_identity,
            "lane_admission_bundle_id": self.lane_admission_bundle_id,
        }


@dataclass(frozen=True)
class NormalizationEvidenceV1:
    evidence_binding: Mapping[str, str]
    likelihood_identity: str
    likelihood_method_id: str
    prior_identity: str
    prior_method_id: str
    evidence_id: str

    def unsigned_payload(self) -> dict[str, object]:
        return {
            "schema": "htt.normalization_evidence.v1",
            "evidence_binding": dict(self.evidence_binding),
            "likelihood_identity": self.likelihood_identity,
            "likelihood_method_id": self.likelihood_method_id,
            "prior_identity": self.prior_identity,
            "prior_method_id": self.prior_method_id,
        }


@dataclass(frozen=True)
class ExecutionPlanBindingV1:
    plan_binding: Mapping[str, str]
    lane_id: str
    model_id: str
    entrypoint: str
    argv: tuple[str, ...]
    output_root: str
    run_mode: str
    provider_manifest_content_id: str
    runtime_environment_receipt_id: str
    plan_content_id: str

    def unsigned_payload(self) -> dict[str, object]:
        return {
            "schema": "htt.execution_plan_binding.v1",
            "plan_binding": dict(self.plan_binding),
            "lane_id": self.lane_id,
            "model_id": self.model_id,
            "entrypoint": self.entrypoint,
            "argv": list(self.argv),
            "output_root": self.output_root,
            "run_mode": self.run_mode,
            "provider_manifest_content_id": self.provider_manifest_content_id,
            "runtime_environment_receipt_id": self.runtime_environment_receipt_id,
        }


@dataclass(frozen=True)
class ProductionModelContract:
    """Non-executing specification for one exact candidate-blob provider."""

    lane_id: str
    model_id: str
    parameter_schema: Mapping[str, Mapping[str, object]]
    likelihood_identity: str
    prior_identity: str
    data_identity: str
    covariance_identity: str
    block_ids: tuple[str, ...]
    discrepancy_ids: tuple[str, ...]
    response_rank: int | None
    lane_admission_bundle_id: str | None
    ordered_admission_record_ids: tuple[str, ...]
    admitted_data_identity: str | None
    admitted_covariance_identity: str | None
    candidate_commit: str | None
    candidate_tree: str | None
    provider_manifest_binding: Mapping[str, str] | None
    provider_content_id: str | None
    provider_source_bindings: Mapping[str, Mapping[str, str]]
    provider_configuration_binding: Mapping[str, str] | None
    provider_environment_binding: Mapping[str, str] | None
    runtime_environment_receipt_id: str | None
    computed_response_rank_receipt_id: str | None
    normalization_evidence_id: str | None
    execution_plan_content_id: str | None
    contract_content_id: str

    def unsigned_payload(self) -> dict[str, object]:
        return {
            "schema": "htt.production_bayesian_contract.v3",
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
            "discrepancy_ids": list(self.discrepancy_ids),
            "lane_admission_bundle_id": self.lane_admission_bundle_id,
            "ordered_admission_record_ids": list(self.ordered_admission_record_ids),
            "admitted_data_identity": self.admitted_data_identity,
            "admitted_covariance_identity": self.admitted_covariance_identity,
            "candidate_commit": self.candidate_commit,
            "candidate_tree": self.candidate_tree,
            "provider_manifest_binding": (
                None if self.provider_manifest_binding is None else dict(self.provider_manifest_binding)
            ),
            "provider_content_id": self.provider_content_id,
            "provider_source_bindings": {
                name: dict(binding)
                for name, binding in sorted(self.provider_source_bindings.items())
            },
            "provider_configuration_binding": (
                None if self.provider_configuration_binding is None else dict(self.provider_configuration_binding)
            ),
            "provider_environment_binding": (
                None if self.provider_environment_binding is None else dict(self.provider_environment_binding)
            ),
            "runtime_environment_receipt_id": self.runtime_environment_receipt_id,
            "computed_response_rank_receipt_id": self.computed_response_rank_receipt_id,
            "normalization_evidence_id": self.normalization_evidence_id,
            "execution_plan_content_id": self.execution_plan_content_id,
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
    discrepancy_ids: Sequence[object] | None = None,
    response_rank: object | None = None,
    likelihood_normalized: object | None = None,
    prior_normalized: object | None = None,
    log_likelihood: object | None = None,
    prior_transform: object | None = None,
    replicate_generator: object | None = None,
    discrepancies: object | None = None,
) -> ProductionModelContract:
    if any(
        value is not None
        for value in (
            response_rank,
            likelihood_normalized,
            prior_normalized,
            log_likelihood,
            prior_transform,
            replicate_generator,
            discrepancies,
        )
    ):
        raise ProductionBayesianError(
            "raw callables, response rank, and normalization booleans are forbidden; "
            "use the candidate-Git-blob factory-loaded provider and computed evidence"
        )
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
    if discrepancy_ids is None:
        raise ProductionBayesianError("discrepancy_ids must be declared before binding")
    declared_discrepancies = tuple(sorted(_names(discrepancy_ids, "discrepancy_ids")))
    provisional = ProductionModelContract(
        lane_id=lane,
        model_id=_nonempty(model_id, "model_id"),
        parameter_schema=schema,
        likelihood_identity=_sha256_identity(likelihood_identity, "likelihood_identity"),
        prior_identity=_sha256_identity(prior_identity, "prior_identity"),
        data_identity=_sha256_identity(data_identity, "data_identity"),
        covariance_identity=_sha256_identity(covariance_identity, "covariance_identity"),
        block_ids=blocks,
        discrepancy_ids=declared_discrepancies,
        response_rank=None,
        lane_admission_bundle_id=None,
        ordered_admission_record_ids=(),
        admitted_data_identity=None,
        admitted_covariance_identity=None,
        candidate_commit=None,
        candidate_tree=None,
        provider_manifest_binding=None,
        provider_content_id=None,
        provider_source_bindings={},
        provider_configuration_binding=None,
        provider_environment_binding=None,
        runtime_environment_receipt_id=None,
        computed_response_rank_receipt_id=None,
        normalization_evidence_id=None,
        execution_plan_content_id=None,
        contract_content_id="",
    )
    return replace(
        provisional,
        contract_content_id=canonical_content_id(provisional.unsigned_payload()),
    )


def _unbound_contract(contract: ProductionModelContract) -> ProductionModelContract:
    provisional = replace(
        contract,
        response_rank=None,
        lane_admission_bundle_id=None,
        ordered_admission_record_ids=(),
        admitted_data_identity=None,
        admitted_covariance_identity=None,
        candidate_commit=None,
        candidate_tree=None,
        provider_manifest_binding=None,
        provider_content_id=None,
        provider_source_bindings={},
        provider_configuration_binding=None,
        provider_environment_binding=None,
        runtime_environment_receipt_id=None,
        computed_response_rank_receipt_id=None,
        normalization_evidence_id=None,
        execution_plan_content_id=None,
        contract_content_id="",
    )
    return replace(
        provisional,
        contract_content_id=canonical_content_id(provisional.unsigned_payload()),
    )


def _runtime_receipt_from_contract(
    *, candidate: object, provider: LoadedCandidateProviderV1
) -> tuple[RuntimeEnvironmentReceiptV1, Mapping[str, str]]:
    _, binding_for, read_blob, _ = _candidate_blob_api()
    path = provider.manifest.environment_contract_path
    payload = _exact_mapping(
        _strict_json_bytes(read_blob(candidate, path), field="runtime environment contract"),
        field="runtime environment contract",
        fields=frozenset({"schema", "required_packages", "expected_receipt"}),
    )
    if payload["schema"] != "htt.runtime_environment_contract.v1":
        raise ProductionBayesianError("runtime environment contract schema drifted")
    required = payload["required_packages"]
    if isinstance(required, (str, bytes)) or not isinstance(required, Sequence):
        raise ProductionBayesianError("runtime environment package inventory drifted")
    receipt = capture_runtime_environment_receipt(required)
    if payload["expected_receipt"] != receipt.as_payload():
        raise ProductionBayesianError(
            "live runtime differs from the candidate environment contract"
        )
    return receipt, binding_for(candidate, path)


def _computed_response_rank(
    *, candidate: object, provider: LoadedCandidateProviderV1,
    covariance_identity: str, lane_admission_bundle_id: str,
) -> ComputedResponseRankReceiptV1:
    _, binding_for, read_blob, _ = _candidate_blob_api()
    path = provider.manifest.response_matrix_path
    payload = _exact_mapping(
        _strict_json_bytes(read_blob(candidate, path), field="response matrix"),
        field="response matrix",
        fields=frozenset(
            {"schema", "feature_order", "parameter_order", "matrix", "singular_value_threshold"}
        ),
    )
    if payload["schema"] != "htt.response_matrix.v1":
        raise ProductionBayesianError("response matrix schema drifted")
    features = _names(payload["feature_order"], "response feature order")
    parameters = _names(payload["parameter_order"], "response parameter order")
    matrix = np.asarray(payload["matrix"], dtype=float)
    threshold = payload["singular_value_threshold"]
    if (
        matrix.shape != (len(features), len(parameters))
        or not np.all(np.isfinite(matrix))
        or not isinstance(threshold, (int, float))
        or isinstance(threshold, bool)
        or not np.isfinite(float(threshold))
        or float(threshold) <= 0
    ):
        raise ProductionBayesianError("response matrix or threshold is invalid")
    rank = int(np.linalg.matrix_rank(matrix, tol=float(threshold)))
    provisional = ComputedResponseRankReceiptV1(
        response_matrix_binding=binding_for(candidate, path),
        feature_order=features,
        parameter_order=parameters,
        singular_value_threshold=float(threshold),
        computed_rank=rank,
        covariance_identity=covariance_identity,
        lane_admission_bundle_id=lane_admission_bundle_id,
        receipt_id="",
    )
    return replace(
        provisional,
        receipt_id=canonical_content_id(provisional.unsigned_payload()),
    )


def _normalization_evidence(
    *, candidate: object, provider: LoadedCandidateProviderV1,
    likelihood_identity: str, prior_identity: str,
) -> NormalizationEvidenceV1:
    _, binding_for, read_blob, _ = _candidate_blob_api()
    path = provider.manifest.normalization_evidence_path
    payload = _exact_mapping(
        _strict_json_bytes(read_blob(candidate, path), field="normalization evidence"),
        field="normalization evidence",
        fields=frozenset({"schema", "likelihood", "prior"}),
    )
    if payload["schema"] != "htt.normalization_evidence.v1":
        raise ProductionBayesianError("normalization evidence schema drifted")
    likelihood = _exact_mapping(
        payload["likelihood"], field="likelihood normalization",
        fields=frozenset({"status", "identity", "method_id"}),
    )
    prior = _exact_mapping(
        payload["prior"], field="prior normalization",
        fields=frozenset({"status", "identity", "method_id"}),
    )
    if (
        likelihood["status"] != "ANALYTICALLY_NORMALIZED"
        or prior["status"] != "ANALYTICALLY_NORMALIZED"
        or likelihood["identity"] != likelihood_identity
        or prior["identity"] != prior_identity
    ):
        raise ProductionBayesianError("normalization evidence does not bind the model")
    provisional = NormalizationEvidenceV1(
        evidence_binding=binding_for(candidate, path),
        likelihood_identity=likelihood_identity,
        likelihood_method_id=_nonempty(likelihood["method_id"], "likelihood normalization method"),
        prior_identity=prior_identity,
        prior_method_id=_nonempty(prior["method_id"], "prior normalization method"),
        evidence_id="",
    )
    return replace(
        provisional,
        evidence_id=canonical_content_id(provisional.unsigned_payload()),
    )


def _execution_plan_binding(
    *, candidate: object, provider: LoadedCandidateProviderV1,
    contract: ProductionModelContract, runtime_receipt: RuntimeEnvironmentReceiptV1,
) -> ExecutionPlanBindingV1:
    _, binding_for, read_blob, _ = _candidate_blob_api()
    path = provider.manifest.execution_plan_path
    payload = _exact_mapping(
        _strict_json_bytes(read_blob(candidate, path), field="execution plan"),
        field="execution plan",
        fields=frozenset({"schema", "lane_id", "model_id", "entrypoint", "argv", "output_root", "run_mode"}),
    )
    if payload["schema"] != "htt.execution_plan.v1":
        raise ProductionBayesianError("execution plan schema drifted")
    argv = payload["argv"]
    if isinstance(argv, (str, bytes)) or not isinstance(argv, Sequence):
        raise ProductionBayesianError("execution plan argv must be a sequence")
    parsed_argv = tuple(_nonempty(item, "execution argv") for item in argv)
    output_root = _relative_path(payload["output_root"], "execution output root")
    if (
        payload["lane_id"] != contract.lane_id
        or payload["model_id"] != contract.model_id
        or payload["run_mode"] != "sampler"
        or not str(payload["entrypoint"]).startswith(provider.manifest.provider_path + ":")
        or not output_root.startswith("docs/generated/observed_runs/")
    ):
        raise ProductionBayesianError("execution plan does not bind the model/provider")
    provisional = ExecutionPlanBindingV1(
        plan_binding=binding_for(candidate, path),
        lane_id=contract.lane_id,
        model_id=contract.model_id,
        entrypoint=_nonempty(payload["entrypoint"], "execution entrypoint"),
        argv=parsed_argv,
        output_root=output_root,
        run_mode="sampler",
        provider_manifest_content_id=provider.manifest.manifest_content_id,
        runtime_environment_receipt_id=runtime_receipt.receipt_id,
        plan_content_id="",
    )
    return replace(
        provisional,
        plan_content_id=canonical_content_id(provisional.unsigned_payload()),
    )


def bind_production_model_contract(
    *,
    contract: ProductionModelContract,
    lane_spec: object,
    admission_decision: object,
    candidate_identity: object,
    provider_manifest_path: Path | None = None,
    provider_configuration_path: Path | None = None,
    provider_environment_path: Path | None = None,
) -> ProductionModelContract:
    if type(contract) is not ProductionModelContract:
        raise ProductionBayesianError("contract must be an exact ProductionModelContract")
    if provider_configuration_path is not None or provider_environment_path is not None:
        raise ProductionBayesianError(
            "provider resources must come from a factory-loaded candidate manifest"
        )
    if not isinstance(provider_manifest_path, Path):
        raise ProductionBayesianError("provider manifest path must be supplied")
    try:
        from common.human_execution_authorization import (
            CandidateIdentityV1,
            admitted_covariance_identity,
            admitted_data_identity,
            candidate_blob_binding,
            replay_complete_lane_admission,
            revalidate_clean_candidate_identity,
        )
    except ImportError as exc:
        raise ProductionBayesianError("PR-304 admission binding contract is unavailable") from exc
    if type(candidate_identity) is not CandidateIdentityV1:
        raise ProductionBayesianError("production binding requires a factory-derived candidate identity")
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
        raise ProductionBayesianError("production model cannot replay its exact admission binding") from exc
    if _LANE_ALIASES.get(contract.lane_id) != replayed.lane_id:
        raise ProductionBayesianError("production model lane does not match replayed admission")
    if contract.data_identity != data_identity:
        raise ProductionBayesianError("production model data identity does not equal admitted data identity")
    if contract.covariance_identity != covariance_identity:
        raise ProductionBayesianError("production model covariance identity does not equal admitted covariance identity")
    base = _unbound_contract(contract)
    provider = load_candidate_provider(
        candidate_identity=candidate, manifest_path=provider_manifest_path
    )
    if tuple(sorted(provider.discrepancies)) != base.discrepancy_ids:
        raise ProductionBayesianError("provider discrepancy exports drifted")
    runtime, environment_binding = _runtime_receipt_from_contract(
        candidate=candidate, provider=provider
    )
    rank = _computed_response_rank(
        candidate=candidate,
        provider=provider,
        covariance_identity=covariance_identity,
        lane_admission_bundle_id=str(replayed.lane_admission_bundle_id),
    )
    if rank.parameter_order != tuple(base.parameter_schema) or rank.computed_rank < len(base.parameter_schema):
        raise ProductionBayesianError("computed response rank is deficient for the parameter schema")
    normalization = _normalization_evidence(
        candidate=candidate,
        provider=provider,
        likelihood_identity=base.likelihood_identity,
        prior_identity=base.prior_identity,
    )
    execution = _execution_plan_binding(
        candidate=candidate,
        provider=provider,
        contract=base,
        runtime_receipt=runtime,
    )
    configuration_binding = candidate_blob_binding(
        candidate, provider.manifest.configuration_path
    )
    candidate_after = revalidate_clean_candidate_identity(candidate)
    if candidate_after.as_payload() != candidate.as_payload():
        raise ProductionBayesianError("production provider candidate changed during binding")
    provisional = replace(
        base,
        response_rank=rank.computed_rank,
        lane_admission_bundle_id=replayed.lane_admission_bundle_id,
        ordered_admission_record_ids=tuple(record.record_id for record in replayed.records),
        admitted_data_identity=data_identity,
        admitted_covariance_identity=covariance_identity,
        candidate_commit=candidate.commit,
        candidate_tree=candidate.tree,
        provider_manifest_binding=provider.manifest.manifest_binding,
        provider_content_id=provider.provider_content_id,
        provider_source_bindings=provider.source_bindings,
        provider_configuration_binding=configuration_binding,
        provider_environment_binding=environment_binding,
        runtime_environment_receipt_id=runtime.receipt_id,
        computed_response_rank_receipt_id=rank.receipt_id,
        normalization_evidence_id=normalization.evidence_id,
        execution_plan_content_id=execution.plan_content_id,
        contract_content_id="",
    )
    return replace(
        provisional,
        contract_content_id=canonical_content_id(provisional.unsigned_payload()),
    )


def revalidate_bound_production_model_contract(
    *, contract: ProductionModelContract, lane_spec: object,
    admission_decision: object, candidate_identity: object,
) -> ProductionModelContract:
    if type(contract) is not ProductionModelContract:
        raise ProductionBayesianError("contract must be an exact ProductionModelContract")
    if contract.provider_manifest_binding is None:
        raise ProductionBayesianError("production model contract is not admission/provider bound")
    manifest_path = Path(
        _nonempty(contract.provider_manifest_binding.get("path"), "provider manifest path")
    )
    rebuilt = bind_production_model_contract(
        contract=_unbound_contract(contract),
        lane_spec=lane_spec,
        admission_decision=admission_decision,
        candidate_identity=candidate_identity,
        provider_manifest_path=manifest_path,
    )
    if rebuilt.unsigned_payload() != contract.unsigned_payload() or rebuilt.contract_content_id != contract.contract_content_id:
        raise ProductionBayesianError("production model admission or provider binding is stale or forged")
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

    return contract.discrepancy_ids


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
        from common.data_identity import lane_registry_from_mapping
        from common.human_execution_authorization import (
            CandidateIdentityV1,
            ExternalTrustedLauncherRequired,
            ValidatedHumanExecutionAuthorization,
            read_candidate_blob,
            replay_complete_lane_admission,
            validate_authorization_execution_bindings,
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
        lane_spec = lane_registry_from_mapping(
            _strict_json_bytes(
                read_candidate_blob(
                    candidate,
                    "docs/research_program/post_pr275/data_registry_v2/LANE_REGISTRY_V2.json",
                ),
                field="PR-289 lane registry Git blob",
            )
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
    if posterior_lineage is not None or posterior_consumer_plan is not None:
        return LaneReadinessDecision(
            lane_id=descriptor.lane_id,
            status=LaneReadinessStatus.BLOCKED_SAMPLER_TERMINAL,
            observed_data_executed=False,
            artifact_mode="readiness_only",
            blocked_reasons=("pr305_observed_run_terminal_contract_unavailable",),
        )
    if validated_human_authorization is None:
        return LaneReadinessDecision(
            lane_id=descriptor.lane_id,
            status=LaneReadinessStatus.BLOCKED_HUMAN_AUTHORIZATION,
            observed_data_executed=False,
            artifact_mode="readiness_only",
            blocked_reasons=("external_trusted_launcher_required",),
        )
    if type(validated_human_authorization) is not ValidatedHumanExecutionAuthorization:
        raise ProductionBayesianError("human authorization must be a validator-built PR-304 capability")
    try:
        validate_authorization_execution_bindings(
            validated_human_authorization.receipt,
            model_contract_content_id=model_contract.contract_content_id,
            runtime_environment_receipt_id=model_contract.runtime_environment_receipt_id,
            computed_response_rank_receipt_id=model_contract.computed_response_rank_receipt_id,
            normalization_evidence_id=model_contract.normalization_evidence_id,
            execution_plan_content_id=model_contract.execution_plan_content_id,
        )
        revalidate_cached_human_execution_authorization(
            cached=validated_human_authorization,
            lane_spec=lane_spec,
            admission_decision=replayed_admission,
            candidate_identity=candidate_identity,
        )
    except ExternalTrustedLauncherRequired:
        pass
    except ValueError as exc:
        raise ProductionBayesianError(
            "authorization execution/model plan binding failed"
        ) from exc
    return LaneReadinessDecision(
        lane_id=descriptor.lane_id,
        status=LaneReadinessStatus.BLOCKED_HUMAN_AUTHORIZATION,
        observed_data_executed=False,
        artifact_mode="readiness_only",
        blocked_reasons=("external_trusted_launcher_required",),
    )


__all__ = [
    "ComputedResponseRankReceiptV1",
    "ExecutionPlanBindingV1",
    "LaneReadinessDecision",
    "LaneReadinessStatus",
    "LoadedCandidateProviderV1",
    "NormalizationEvidenceV1",
    "ObservationalLaneDescriptor",
    "PosteriorConsumerPlan",
    "ProductionBayesianError",
    "ProductionModelContract",
    "ProviderManifestV1",
    "RuntimeEnvironmentReceiptV1",
    "SamplerPosteriorLineage",
    "assess_lane_readiness",
    "bind_production_model_contract",
    "build_posterior_consumer_plan",
    "build_production_model_contract",
    "build_sampler_posterior_lineage",
    "capture_runtime_environment_receipt",
    "load_candidate_provider",
    "load_observational_lane_descriptors",
    "revalidate_bound_production_model_contract",
]
