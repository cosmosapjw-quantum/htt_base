"""Strict PR-288 Bayesian evidence, PPC, and LOOCV semantics.

The PR-065 summary builders remain reproducibility-only APIs.  This module owns
new computations from frozen likelihood/prior inputs; it never accepts a
caller-authored evidence verdict, posterior-predictive p-value, or fold score.
"""

from __future__ import annotations

from copy import copy
from dataclasses import InitVar, dataclass
from enum import Enum
import hashlib
import importlib
import json
import math
from pathlib import Path
import re
from types import MappingProxyType
from typing import Mapping, Sequence

import numpy as np
from scipy import __version__ as scipy_version
from scipy.special import logsumexp
from scipy.stats import norm, qmc
import yaml


class BayesianSemanticsError(ValueError):
    """Raised when a frozen PR-288 computation contract is violated."""


class EngineRunStatus(str, Enum):
    PASS = "PASS"
    BLOCKED_REQUIRED_ENGINE_UNAVAILABLE = "BLOCKED_REQUIRED_ENGINE_UNAVAILABLE"


_FIXTURE_TOKEN = object()
_ENGINE_TOKEN = object()
_DRAWS_TOKEN = object()
_PPC_TOKEN = object()
_LOOCV_TOKEN = object()
_MUTATION_TOKEN = object()
_RECEIPT_TOKEN = object()
_SHA256_PREFIX = "sha256:"
_FROZEN_CLAIM_BOUNDARY = {
    "owner": "HTT",
    "scope": "preregistered synthetic and analytic Bayesian-method diagnostics",
    "claim_tier": "diagnostic_only",
    "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C2"},
    "scientific_artifact_mode": "synthetic_diagnostic",
    "transfer_source": "none",
    "observed_data_executed": False,
    "public_use": False,
    "family_identification_gate": "BLOCKED_PRE_NATIVE_ATLAS",
    "scientific_status_effect": "OPEN_UNCHANGED",
}
_FROZEN_RECEIPT_METADATA = (
    "owner",
    "scope",
    "claim_tier",
    "transfer_source",
    "fixture_and_config_identities",
    "posterior_draw_and_fold_identities",
    "covariance_and_null_status",
    "assumptions",
    "caveats",
    "generating_procedure",
    "git_commit_or_worktree_state",
    "claim_level",
    "scientific_artifact_mode",
    "observed_data_executed",
    "public_use",
    "family_identification_gate",
    "scientific_status_effect",
    "allowed_uses",
    "forbidden_uses",
    "legacy_disposition",
    "engine_versions_and_seed_inventories",
    "analytic_accuracy_and_null_status",
    "negative_control_status",
)


def _json_ready(value: object) -> object:
    if isinstance(value, np.ndarray):
        return [_json_ready(item) for item in value.tolist()]
    if isinstance(value, np.generic):
        return _json_ready(value.item())
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        raise BayesianSemanticsError("non-finite JSON value")
    return value


def canonical_content_id(value: object) -> str:
    try:
        encoded = json.dumps(
            _json_ready(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise BayesianSemanticsError("payload is not canonical JSON") from exc
    return _SHA256_PREFIX + hashlib.sha256(encoded).hexdigest()


def _array(value: object, *, ndim: int, field: str) -> np.ndarray:
    try:
        out = np.asarray(value, dtype=float)
    except (TypeError, ValueError) as exc:
        raise BayesianSemanticsError(f"{field} must be numeric") from exc
    if out.ndim != ndim or not np.all(np.isfinite(out)):
        raise BayesianSemanticsError(f"{field} has invalid shape or values")
    out = np.array(out, dtype=float, copy=True)
    out.setflags(write=False)
    return out


def _positive_definite(value: np.ndarray, field: str) -> None:
    if value.shape[0] != value.shape[1]:
        raise BayesianSemanticsError(f"{field} must be square")
    if not np.allclose(value, value.T, rtol=0.0, atol=1e-14):
        raise BayesianSemanticsError(f"{field} must be symmetric")
    try:
        np.linalg.cholesky(value)
    except np.linalg.LinAlgError as exc:
        raise BayesianSemanticsError(f"{field} must be positive definite") from exc


@dataclass(frozen=True, eq=False)
class EvidenceFixture:
    fixture_id: str
    dimension: int
    observations: np.ndarray
    design_matrix: np.ndarray
    covariance: np.ndarray
    prior_mean: np.ndarray
    prior_covariance: np.ndarray
    units: str
    base_measure: str
    negative_control_terminal: str | None
    fixture_content_id: str
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _FIXTURE_TOKEN:
            raise BayesianSemanticsError("EvidenceFixture must be factory-derived")

    def unsigned_payload(self) -> dict[str, object]:
        return {
            "schema": "HTT_PR288_EVIDENCE_FIXTURE_V1",
            "fixture_id": self.fixture_id,
            "dimension": self.dimension,
            "observations": self.observations,
            "design_matrix": self.design_matrix,
            "covariance": self.covariance,
            "prior_mean": self.prior_mean,
            "prior_covariance": self.prior_covariance,
            "units": self.units,
            "base_measure": self.base_measure,
            "negative_control_terminal": self.negative_control_terminal,
        }


def _build_fixture(
    *,
    fixture_id: str,
    dimension: int,
    observations: object,
    design_matrix: object,
    covariance: object,
    prior_mean: object,
    prior_covariance: object,
    units: str,
    base_measure: str,
    negative_control_terminal: str | None = None,
) -> EvidenceFixture:
    if not isinstance(fixture_id, str) or not fixture_id:
        raise BayesianSemanticsError("fixture_id must be nonempty")
    if isinstance(dimension, bool) or not isinstance(dimension, int) or dimension <= 0:
        raise BayesianSemanticsError("dimension must be a positive integer")
    y = _array(observations, ndim=1, field="observations")
    design = _array(design_matrix, ndim=2, field="design_matrix")
    cov = _array(covariance, ndim=2, field="covariance")
    mean = _array(prior_mean, ndim=1, field="prior_mean")
    prior_cov = _array(prior_covariance, ndim=2, field="prior_covariance")
    if design.shape != (len(y), dimension):
        raise BayesianSemanticsError("design matrix shape differs from fixture dimension")
    if cov.shape != (len(y), len(y)):
        raise BayesianSemanticsError("covariance shape differs from observations")
    if mean.shape != (dimension,) or prior_cov.shape != (dimension, dimension):
        raise BayesianSemanticsError("prior shape differs from fixture dimension")
    _positive_definite(cov, "covariance")
    _positive_definite(prior_cov, "prior_covariance")
    if np.linalg.matrix_rank(design) != dimension:
        raise BayesianSemanticsError("registered design is rank deficient")
    if not isinstance(units, str) or not units or not isinstance(base_measure, str) or not base_measure:
        raise BayesianSemanticsError("units and base measure must be explicit")
    unsigned = {
        "schema": "HTT_PR288_EVIDENCE_FIXTURE_V1",
        "fixture_id": fixture_id,
        "dimension": dimension,
        "observations": y,
        "design_matrix": design,
        "covariance": cov,
        "prior_mean": mean,
        "prior_covariance": prior_cov,
        "units": units,
        "base_measure": base_measure,
        "negative_control_terminal": negative_control_terminal,
    }
    return EvidenceFixture(
        fixture_id=fixture_id,
        dimension=dimension,
        observations=y,
        design_matrix=design,
        covariance=cov,
        prior_mean=mean,
        prior_covariance=prior_cov,
        units=units,
        base_measure=base_measure,
        negative_control_terminal=negative_control_terminal,
        fixture_content_id=canonical_content_id(unsigned),
        _construction_token=_FIXTURE_TOKEN,
    )


def _load_spec(spec_path: Path) -> dict[str, object]:
    if spec_path.is_symlink() or not spec_path.is_file():
        raise BayesianSemanticsError("PR-288 spec must be a regular file")
    try:
        value = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise BayesianSemanticsError("PR-288 spec cannot be parsed") from exc
    if not isinstance(value, dict) or value.get("pr_id") != "PR-288":
        raise BayesianSemanticsError("not the registered PR-288 spec")
    if any(
        value.get(key) != expected
        for key, expected in _FROZEN_CLAIM_BOUNDARY.items()
    ):
        raise BayesianSemanticsError("PR-288 frozen claim boundary drifted")
    if value.get("dependencies") != ["PR-280"]:
        raise BayesianSemanticsError("PR-288 dependency boundary drifted")
    dependency = value.get("dependency_contract")
    if not isinstance(dependency, dict) or any(
        dependency.get(key) != expected
        for key, expected in {
            "upstream_id": "PR-280",
            "mode": "requires_terminal_receipt",
            "accepted_terminal": "COMPLETED_FAILED_WITH_RECEIPT",
            "success_dependency_required": False,
        }.items()
    ):
        raise BayesianSemanticsError("PR-288 dependency boundary drifted")
    receipt_contract = value.get("receipt_contract")
    if not isinstance(receipt_contract, dict) or tuple(
        receipt_contract.get("required_metadata", ())
    ) != _FROZEN_RECEIPT_METADATA:
        raise BayesianSemanticsError("PR-288 frozen receipt metadata drifted")
    if (
        receipt_contract.get("output_path")
        != "docs/generated/pr288_bayesian_semantics_receipt.json"
        or receipt_contract.get("pass_token")
        != "PASS_BAYESIAN_SEMANTICS_REPAIR"
        or tuple(receipt_contract.get("terminal_precedence", ()))
        != (
            "BLOCKED_DEPENDENCY_OR_ENGINE",
            "BLOCKED_EVIDENCE_CROSSCHECK",
            "BLOCKED_PPC_OR_LOOCV_CONTRACT",
            "BLOCKED_REGISTERED_MUTATION",
            "PASS_BAYESIAN_SEMANTICS_REPAIR",
        )
    ):
        raise BayesianSemanticsError("PR-288 frozen receipt contract drifted")
    return value


def load_registered_fixtures(spec_path: Path) -> Mapping[str, EvidenceFixture]:
    spec = _load_spec(spec_path)
    rows = spec.get("evidence_fixtures")
    if not isinstance(rows, list) or len(rows) != 4:
        raise BayesianSemanticsError("exact four-fixture inventory is required")
    by_id = {row.get("fixture_id"): row for row in rows if isinstance(row, dict)}
    if len(by_id) != 4:
        raise BayesianSemanticsError("fixture IDs must be unique")

    normal_row = by_id.get("PR288-NORMAL-MEAN-ANALYTIC")
    null_row = by_id.get("PR288-NULL-EQUAL-MODELS")
    correlated_row = by_id.get("PR288-REGISTERED-CORRELATED-NUISANCE")
    negative_row = by_id.get("PR288-MISSPECIFIED-NEGATIVE-CONTROL")
    if not all(isinstance(row, dict) for row in (normal_row, null_row, correlated_row, negative_row)):
        raise BayesianSemanticsError("registered fixture row is missing")

    assert isinstance(normal_row, dict)
    normal_like = normal_row.get("likelihood")
    normal_prior = normal_row.get("prior")
    if not isinstance(normal_like, dict) or not isinstance(normal_prior, dict):
        raise BayesianSemanticsError("normal fixture likelihood/prior is incomplete")
    if normal_like.get("normalized_density") is not True or normal_prior.get("normalized_density") is not True:
        raise BayesianSemanticsError("normal fixture densities must be normalized")
    normal_obs = normal_row.get("observations")
    sigma = float(normal_like.get("known_sigma"))
    tau = float(normal_prior.get("sigma"))
    fixtures: dict[str, EvidenceFixture] = {}
    fixtures["PR288-NORMAL-MEAN-ANALYTIC"] = _build_fixture(
        fixture_id="PR288-NORMAL-MEAN-ANALYTIC",
        dimension=1,
        observations=normal_obs,
        design_matrix=np.ones((len(normal_obs), 1)),
        covariance=np.eye(len(normal_obs)) * sigma**2,
        prior_mean=[float(normal_prior.get("mean"))],
        prior_covariance=[[tau**2]],
        units=str(normal_row.get("units")),
        base_measure=str(normal_row.get("base_measure")),
    )

    assert isinstance(null_row, dict)
    null_like = null_row.get("likelihood")
    null_prior = null_row.get("prior")
    copy_ids = null_row.get("model_copy_ids")
    if (
        not isinstance(null_like, dict)
        or not isinstance(null_prior, dict)
        or copy_ids != ["PR288-NULL-EQUAL-MODELS-A", "PR288-NULL-EQUAL-MODELS-B"]
        or null_like.get("normalized_density") is not True
        or null_prior.get("normalized_density") is not True
    ):
        raise BayesianSemanticsError("equal-model null fixture is incomplete")
    null_obs = null_row.get("observations")
    null_sigmas = np.asarray(null_like.get("known_sigma_by_coordinate"), dtype=float)
    for copy_id in copy_ids:
        fixtures[copy_id] = _build_fixture(
            fixture_id=copy_id,
            dimension=2,
            observations=null_obs,
            design_matrix=np.eye(2),
            covariance=np.diag(null_sigmas**2),
            prior_mean=np.zeros(2),
            prior_covariance=np.eye(2),
            units=str(null_row.get("units")),
            base_measure=str(null_row.get("base_measure")),
        )

    assert isinstance(correlated_row, dict)
    if correlated_row.get("normalized_likelihood_and_prior") is not True:
        raise BayesianSemanticsError("correlated fixture densities must be normalized")
    correlated = _build_fixture(
        fixture_id="PR288-REGISTERED-CORRELATED-NUISANCE",
        dimension=3,
        observations=correlated_row.get("observations"),
        design_matrix=correlated_row.get("design_matrix"),
        covariance=correlated_row.get("covariance"),
        prior_mean=correlated_row.get("prior_mean"),
        prior_covariance=correlated_row.get("prior_covariance"),
        units=str(correlated_row.get("units")),
        base_measure=str(correlated_row.get("base_measure")),
    )
    if (
        np.linalg.matrix_rank(correlated.covariance)
        != correlated_row.get("covariance_required_rank")
        or np.linalg.matrix_rank(correlated.design_matrix)
        != correlated_row.get("design_required_rank")
    ):
        raise BayesianSemanticsError("correlated fixture rank contract drifted")
    fixtures[correlated.fixture_id] = correlated

    assert isinstance(negative_row, dict)
    if negative_row.get("generator_fixture") != correlated.fixture_id:
        raise BayesianSemanticsError("negative control generator identity drifted")
    negative = _build_fixture(
        fixture_id="PR288-MISSPECIFIED-NEGATIVE-CONTROL",
        dimension=correlated.dimension,
        observations=correlated.observations,
        design_matrix=correlated.design_matrix,
        covariance=np.diag(np.diag(correlated.covariance)),
        prior_mean=correlated.prior_mean,
        prior_covariance=correlated.prior_covariance,
        units=correlated.units,
        base_measure=correlated.base_measure,
        negative_control_terminal=str(negative_row.get("expected_terminal")),
    )
    if negative.fixture_content_id == correlated.fixture_content_id:
        raise BayesianSemanticsError("negative-control covariance identity was hidden")
    fixtures[negative.fixture_id] = negative
    return MappingProxyType(fixtures)


def analytic_log_evidence(fixture: EvidenceFixture) -> float:
    if type(fixture) is not EvidenceFixture:
        raise TypeError("fixture must be an exact EvidenceFixture")
    marginal_mean = fixture.design_matrix @ fixture.prior_mean
    marginal_cov = (
        fixture.covariance
        + fixture.design_matrix @ fixture.prior_covariance @ fixture.design_matrix.T
    )
    residual = fixture.observations - marginal_mean
    sign, logdet = np.linalg.slogdet(marginal_cov)
    if sign <= 0:
        raise BayesianSemanticsError("marginal covariance is not positive definite")
    quadratic = float(residual @ np.linalg.solve(marginal_cov, residual))
    return float(-0.5 * (len(residual) * math.log(2 * math.pi) + logdet + quadratic))


def _log_likelihood_many(theta: np.ndarray, fixture: EvidenceFixture) -> np.ndarray:
    residual = fixture.observations[None, :] - theta @ fixture.design_matrix.T
    inverse = np.linalg.inv(fixture.covariance)
    quadratic = np.einsum("ni,ij,nj->n", residual, inverse, residual)
    sign, logdet = np.linalg.slogdet(fixture.covariance)
    if sign <= 0:
        raise BayesianSemanticsError("likelihood covariance is not positive definite")
    normalizer = len(fixture.observations) * math.log(2 * math.pi) + logdet
    return -0.5 * (normalizer + quadratic)


def _prior_transform_many(unit: np.ndarray, fixture: EvidenceFixture) -> np.ndarray:
    eps = np.finfo(float).eps
    z = norm.ppf(np.clip(unit, eps, 1.0 - eps))
    chol = np.linalg.cholesky(fixture.prior_covariance)
    return fixture.prior_mean[None, :] + z @ chol.T


@dataclass(frozen=True)
class EngineEvidenceResult:
    engine_id: str
    fixture_id: str
    status: EngineRunStatus
    log_evidence: float | None
    declared_standard_uncertainty: float | None
    effective_or_live_sample_count: int
    termination_status: str
    engine_version: str | None
    scramble_or_seed_inventory: tuple[int, ...]
    likelihood_call_count: int
    likelihood_and_prior_contract_content_id: str
    sample_or_node_inventory_content_id: str | None
    independent_estimate_content_id: str | None
    independent_linear_evidence_estimates: tuple[float, ...]
    result_content_id: str
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _ENGINE_TOKEN:
            raise BayesianSemanticsError("EngineEvidenceResult must be factory-derived")

    def unsigned_payload(self) -> dict[str, object]:
        return {
            "schema": "HTT_PR288_ENGINE_EVIDENCE_RESULT_V1",
            "engine_id": self.engine_id,
            "fixture_id": self.fixture_id,
            "status": self.status.value,
            "log_evidence": self.log_evidence,
            "declared_standard_uncertainty": self.declared_standard_uncertainty,
            "effective_or_live_sample_count": self.effective_or_live_sample_count,
            "termination_status": self.termination_status,
            "engine_version": self.engine_version,
            "scramble_or_seed_inventory": list(self.scramble_or_seed_inventory),
            "likelihood_call_count": self.likelihood_call_count,
            "likelihood_and_prior_contract_content_id": self.likelihood_and_prior_contract_content_id,
            "sample_or_node_inventory_content_id": self.sample_or_node_inventory_content_id,
            "independent_estimate_content_id": self.independent_estimate_content_id,
            "independent_linear_evidence_estimates": list(
                self.independent_linear_evidence_estimates
            ),
        }


def _engine_result(**values: object) -> EngineEvidenceResult:
    unsigned = {"schema": "HTT_PR288_ENGINE_EVIDENCE_RESULT_V1", **values}
    return EngineEvidenceResult(
        **values,
        result_content_id=canonical_content_id(unsigned),
        _construction_token=_ENGINE_TOKEN,
    )


def validate_engine_evidence_result(result: EngineEvidenceResult) -> EngineEvidenceResult:
    if type(result) is not EngineEvidenceResult:
        raise BayesianSemanticsError("result must be an exact EngineEvidenceResult")
    if result.status is EngineRunStatus.PASS:
        if (
            result.log_evidence is None
            or not math.isfinite(result.log_evidence)
            or result.declared_standard_uncertainty is None
            or not math.isfinite(result.declared_standard_uncertainty)
            or result.declared_standard_uncertainty < 0
            or result.effective_or_live_sample_count <= 0
            or result.likelihood_call_count <= 0
            or result.sample_or_node_inventory_content_id is None
            or result.independent_estimate_content_id is None
        ):
            raise BayesianSemanticsError("passing engine result is incomplete")
    else:
        if (
            result.log_evidence is not None
            or result.declared_standard_uncertainty is not None
            or result.effective_or_live_sample_count != 0
            or result.likelihood_call_count != 0
            or result.termination_status != "BLOCKED_REQUIRED_ENGINE_UNAVAILABLE"
            or result.scramble_or_seed_inventory
            or result.sample_or_node_inventory_content_id is not None
            or result.independent_estimate_content_id is not None
            or result.independent_linear_evidence_estimates
        ):
            raise BayesianSemanticsError("blocked engine result carries invented evidence")
    if result.result_content_id != canonical_content_id(result.unsigned_payload()):
        raise BayesianSemanticsError("engine result content identity drifted")
    return result


def _engine_config(spec_path: Path, engine_id: str) -> dict[str, object]:
    spec = _load_spec(spec_path)
    contract = spec.get("engine_contract")
    if not isinstance(contract, dict):
        raise BayesianSemanticsError("engine contract is missing")
    engines = contract.get("required_engines")
    if not isinstance(engines, list):
        raise BayesianSemanticsError("required engine inventory is missing")
    matches = [row for row in engines if isinstance(row, dict) and row.get("engine_id") == engine_id]
    if len(matches) != 1:
        raise BayesianSemanticsError("engine configuration is missing or duplicated")
    return matches[0]


def _release_tuple(value: object) -> tuple[int, int, int]:
    if not isinstance(value, str):
        raise BayesianSemanticsError("engine version is unavailable")
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)", value)
    if match is None:
        raise BayesianSemanticsError("engine version is not a semantic release")
    return tuple(int(component) for component in match.groups())


def run_scrambled_sobol_evidence(
    fixture: EvidenceFixture, *, spec_path: Path
) -> EngineEvidenceResult:
    config = _engine_config(spec_path, "SCIPY_SOBOL_QMC")
    seed_map = config.get("scramble_seeds_by_fixture")
    seeds = seed_map.get(fixture.fixture_id) if isinstance(seed_map, Mapping) else None
    count = config.get("scramble_count")
    power_m = config.get("power_m")
    if (
        config.get("scramble") is not True
        or not isinstance(seeds, list)
        or any(isinstance(seed, bool) or not isinstance(seed, int) for seed in seeds)
        or len(set(seeds)) != len(seeds)
        or count != len(seeds)
        or power_m != 14
        or config.get("aggregation_space") != "linear_evidence"
    ):
        raise BayesianSemanticsError("Sobol frozen randomization contract drifted")
    estimates: list[float] = []
    inventory = hashlib.sha256()
    calls = 0
    for seed in seeds:
        sampler = qmc.Sobol(d=fixture.dimension, scramble=True, seed=int(seed))
        nodes = sampler.random_base2(m=int(power_m))
        inventory.update(np.ascontiguousarray(nodes).tobytes())
        theta = _prior_transform_many(nodes, fixture)
        log_like = _log_likelihood_many(theta, fixture)
        log_z = float(logsumexp(log_like) - math.log(len(log_like)))
        estimates.append(math.exp(log_z))
        calls += len(log_like)
    linear_mean = float(np.mean(estimates))
    linear_se = float(np.std(estimates, ddof=1) / math.sqrt(len(estimates)))
    if not math.isfinite(linear_mean) or linear_mean <= 0 or linear_se < 0:
        raise BayesianSemanticsError("Sobol linear-evidence ensemble is invalid")
    node_id = _SHA256_PREFIX + inventory.hexdigest()
    estimate_id = canonical_content_id(
        {
            "engine_id": "SCIPY_SOBOL_QMC",
            "fixture_content_id": fixture.fixture_content_id,
            "linear_estimates": estimates,
            "node_inventory_content_id": node_id,
        }
    )
    result = _engine_result(
        engine_id="SCIPY_SOBOL_QMC",
        fixture_id=fixture.fixture_id,
        status=EngineRunStatus.PASS,
        log_evidence=math.log(linear_mean),
        declared_standard_uncertainty=linear_se / linear_mean,
        effective_or_live_sample_count=calls,
        termination_status="COMPLETED_POWER_OF_TWO_SCRAMBLES",
        engine_version=f"scipy-{scipy_version}",
        scramble_or_seed_inventory=tuple(int(seed) for seed in seeds),
        likelihood_call_count=calls,
        likelihood_and_prior_contract_content_id=fixture.fixture_content_id,
        sample_or_node_inventory_content_id=node_id,
        independent_estimate_content_id=estimate_id,
        independent_linear_evidence_estimates=tuple(estimates),
    )
    return validate_engine_evidence_result(result)


def run_dynesty_evidence(
    fixture: EvidenceFixture, *, spec_path: Path
) -> EngineEvidenceResult:
    config = _engine_config(spec_path, "DYNESTY_NESTED")
    try:
        dynesty = importlib.import_module("dynesty")
    except ModuleNotFoundError as exc:
        if exc.name != "dynesty":
            raise
        result = _engine_result(
            engine_id="DYNESTY_NESTED",
            fixture_id=fixture.fixture_id,
            status=EngineRunStatus.BLOCKED_REQUIRED_ENGINE_UNAVAILABLE,
            log_evidence=None,
            declared_standard_uncertainty=None,
            effective_or_live_sample_count=0,
            termination_status="BLOCKED_REQUIRED_ENGINE_UNAVAILABLE",
            engine_version=None,
            scramble_or_seed_inventory=(),
            likelihood_call_count=0,
            likelihood_and_prior_contract_content_id=fixture.fixture_content_id,
            sample_or_node_inventory_content_id=None,
            independent_estimate_content_id=None,
            independent_linear_evidence_estimates=(),
        )
        return validate_engine_evidence_result(result)
    dynesty_version = str(getattr(dynesty, "__version__", "unknown"))
    try:
        version_ready = _release_tuple(dynesty_version) >= _release_tuple(
            str(config.get("version_floor"))
        )
    except BayesianSemanticsError:
        version_ready = False
    if not version_ready:
        result = _engine_result(
            engine_id="DYNESTY_NESTED",
            fixture_id=fixture.fixture_id,
            status=EngineRunStatus.BLOCKED_REQUIRED_ENGINE_UNAVAILABLE,
            log_evidence=None,
            declared_standard_uncertainty=None,
            effective_or_live_sample_count=0,
            termination_status="BLOCKED_REQUIRED_ENGINE_UNAVAILABLE",
            engine_version=f"dynesty-{dynesty_version}",
            scramble_or_seed_inventory=(),
            likelihood_call_count=0,
            likelihood_and_prior_contract_content_id=fixture.fixture_content_id,
            sample_or_node_inventory_content_id=None,
            independent_estimate_content_id=None,
            independent_linear_evidence_estimates=(),
        )
        return validate_engine_evidence_result(result)
    seeds = config.get("fixture_seeds")
    if not isinstance(seeds, Mapping) or fixture.fixture_id not in seeds:
        raise BayesianSemanticsError("Dynesty fixture seed is missing")
    seed = int(seeds[fixture.fixture_id])
    nlive = int(config.get("nlive"))
    dlogz = float(config.get("dlogz"))
    rng = np.random.default_rng(seed)

    def loglike(theta: np.ndarray) -> float:
        return float(_log_likelihood_many(np.asarray(theta)[None, :], fixture)[0])

    def transform(unit: np.ndarray) -> np.ndarray:
        return _prior_transform_many(np.asarray(unit)[None, :], fixture)[0]

    sampler = dynesty.NestedSampler(
        loglike,
        transform,
        fixture.dimension,
        nlive=nlive,
        bound=str(config.get("bound")),
        sample=str(config.get("sample")),
        rstate=rng,
    )
    sampler.run_nested(dlogz=dlogz, print_progress=False)
    values = sampler.results
    samples = np.asarray(values.samples, dtype=float)
    logwt = np.asarray(values.logwt, dtype=float)
    inventory = hashlib.sha256()
    inventory.update(np.ascontiguousarray(samples).tobytes())
    inventory.update(np.ascontiguousarray(logwt).tobytes())
    node_id = _SHA256_PREFIX + inventory.hexdigest()
    estimate_id = canonical_content_id(
        {
            "engine_id": "DYNESTY_NESTED",
            "fixture_content_id": fixture.fixture_content_id,
            "log_evidence": float(values.logz[-1]),
            "uncertainty": float(values.logzerr[-1]),
            "sample_inventory_content_id": node_id,
        }
    )
    calls = int(np.sum(np.asarray(values.ncall, dtype=int)))
    result = _engine_result(
        engine_id="DYNESTY_NESTED",
        fixture_id=fixture.fixture_id,
        status=EngineRunStatus.PASS,
        log_evidence=float(values.logz[-1]),
        declared_standard_uncertainty=float(values.logzerr[-1]),
        effective_or_live_sample_count=len(samples),
        termination_status="COMPLETED_DLOGZ_THRESHOLD",
        engine_version=f"dynesty-{dynesty_version}",
        scramble_or_seed_inventory=(seed,),
        likelihood_call_count=calls,
        likelihood_and_prior_contract_content_id=fixture.fixture_content_id,
        sample_or_node_inventory_content_id=node_id,
        independent_estimate_content_id=estimate_id,
        independent_linear_evidence_estimates=(),
    )
    return validate_engine_evidence_result(result)


@dataclass(frozen=True, eq=False)
class WeightedPosteriorDraws:
    model_and_likelihood_identity: str
    parameter_names: tuple[str, ...]
    samples: np.ndarray
    normalized_weights: np.ndarray
    posterior_sample_content_sha256: str
    normalized_weight_content_sha256: str
    draw_content_id: str
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _DRAWS_TOKEN:
            raise BayesianSemanticsError("WeightedPosteriorDraws must be factory-derived")

    def unsigned_payload(self) -> dict[str, object]:
        return {
            "schema": "HTT_PR288_WEIGHTED_POSTERIOR_DRAWS_V1",
            "model_and_likelihood_identity": self.model_and_likelihood_identity,
            "parameter_names": list(self.parameter_names),
            "posterior_sample_content_sha256": self.posterior_sample_content_sha256,
            "normalized_weight_content_sha256": self.normalized_weight_content_sha256,
            "draw_count": len(self.samples),
            "parameter_count": self.samples.shape[1],
        }


def build_weighted_posterior_draws(
    *,
    model_and_likelihood_identity: str,
    parameter_names: Sequence[str],
    samples: object,
    weights: object,
) -> WeightedPosteriorDraws:
    if not isinstance(model_and_likelihood_identity, str) or not model_and_likelihood_identity.startswith(
        _SHA256_PREFIX
    ):
        raise BayesianSemanticsError("model and likelihood identity must be content addressed")
    names = tuple(parameter_names)
    if (
        not names
        or any(not isinstance(name, str) or not name for name in names)
        or len(set(names)) != len(names)
    ):
        raise BayesianSemanticsError("parameter names must be unique nonempty strings")
    sample_array = _array(samples, ndim=2, field="posterior samples")
    weight_array = _array(weights, ndim=1, field="posterior weights")
    if sample_array.shape[0] < 256:
        raise BayesianSemanticsError("posterior draws must contain at least 256 rows")
    if sample_array.shape[1] != len(names) or len(weight_array) != len(sample_array):
        raise BayesianSemanticsError("posterior sample, weight, and parameter shapes differ")
    if np.any(weight_array < 0) or not float(np.sum(weight_array)) > 0:
        raise BayesianSemanticsError("posterior weights must be nonnegative with positive sum")
    normalized = np.array(weight_array / np.sum(weight_array), dtype=float, copy=True)
    normalized.setflags(write=False)
    sample_id = canonical_content_id(sample_array)
    weight_id = canonical_content_id(normalized)
    unsigned = {
        "schema": "HTT_PR288_WEIGHTED_POSTERIOR_DRAWS_V1",
        "model_and_likelihood_identity": model_and_likelihood_identity,
        "parameter_names": list(names),
        "posterior_sample_content_sha256": sample_id,
        "normalized_weight_content_sha256": weight_id,
        "draw_count": len(sample_array),
        "parameter_count": sample_array.shape[1],
    }
    return WeightedPosteriorDraws(
        model_and_likelihood_identity=model_and_likelihood_identity,
        parameter_names=names,
        samples=sample_array,
        normalized_weights=normalized,
        posterior_sample_content_sha256=sample_id,
        normalized_weight_content_sha256=weight_id,
        draw_content_id=canonical_content_id(unsigned),
        _construction_token=_DRAWS_TOKEN,
    )


def _validate_weighted_posterior_draws(
    draws: WeightedPosteriorDraws,
) -> WeightedPosteriorDraws:
    if type(draws) is not WeightedPosteriorDraws:
        raise BayesianSemanticsError("draws must be exact WeightedPosteriorDraws")
    if (
        canonical_content_id(draws.samples) != draws.posterior_sample_content_sha256
        or canonical_content_id(draws.normalized_weights)
        != draws.normalized_weight_content_sha256
        or not np.isclose(np.sum(draws.normalized_weights), 1.0, rtol=0.0, atol=1e-14)
        or draws.draw_content_id != canonical_content_id(draws.unsigned_payload())
    ):
        raise BayesianSemanticsError("posterior draw identity drifted")
    return draws


def draw_conjugate_gaussian_posterior(
    fixture: EvidenceFixture, *, draw_count: int, seed: int
) -> WeightedPosteriorDraws:
    if isinstance(draw_count, bool) or draw_count < 256:
        raise BayesianSemanticsError("posterior draw_count must be at least 256")
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise BayesianSemanticsError("posterior draw seed must be a nonnegative integer")
    prior_precision = np.linalg.inv(fixture.prior_covariance)
    noise_precision = np.linalg.inv(fixture.covariance)
    posterior_precision = (
        prior_precision
        + fixture.design_matrix.T @ noise_precision @ fixture.design_matrix
    )
    posterior_covariance = np.linalg.inv(posterior_precision)
    posterior_mean = posterior_covariance @ (
        prior_precision @ fixture.prior_mean
        + fixture.design_matrix.T @ noise_precision @ fixture.observations
    )
    rng = np.random.default_rng(seed)
    samples = rng.multivariate_normal(
        posterior_mean, posterior_covariance, size=int(draw_count)
    )
    return build_weighted_posterior_draws(
        model_and_likelihood_identity=fixture.fixture_content_id,
        parameter_names=tuple(f"theta_{index}" for index in range(fixture.dimension)),
        samples=samples,
        weights=np.ones(draw_count, dtype=float),
    )


@dataclass(frozen=True)
class PosteriorPredictiveReceipt:
    posterior_draw_content_id: str
    posterior_sample_content_sha256: str
    normalized_weight_content_sha256: str
    replicate_seed_commitment: str
    model_and_likelihood_identity: str
    discrepancy_statistic_identity: str
    observed_discrepancies: tuple[float, ...]
    replicated_discrepancies: tuple[float, ...]
    comparison_indicators: tuple[int, ...]
    posterior_predictive_pvalue: float
    predictive_summaries: Mapping[str, object]
    equality_rule: str
    status: str
    receipt_content_id: str
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _PPC_TOKEN:
            raise BayesianSemanticsError(
                "PosteriorPredictiveReceipt must be factory-derived"
            )

    def unsigned_payload(self) -> dict[str, object]:
        return {
            "schema": "HTT_PR288_POSTERIOR_PREDICTIVE_RECEIPT_V1",
            "posterior_draw_content_id": self.posterior_draw_content_id,
            "posterior_sample_content_sha256": self.posterior_sample_content_sha256,
            "normalized_weight_content_sha256": self.normalized_weight_content_sha256,
            "replicate_seed_commitment": self.replicate_seed_commitment,
            "model_and_likelihood_identity": self.model_and_likelihood_identity,
            "discrepancy_statistic_identity": self.discrepancy_statistic_identity,
            "observed_discrepancies": list(self.observed_discrepancies),
            "replicated_discrepancies": list(self.replicated_discrepancies),
            "comparison_indicators": list(self.comparison_indicators),
            "posterior_predictive_pvalue": self.posterior_predictive_pvalue,
            "predictive_summaries": dict(self.predictive_summaries),
            "equality_rule": self.equality_rule,
            "status": self.status,
        }


def run_posterior_draw_ppc(
    *,
    draws: WeightedPosteriorDraws,
    observed_data: object,
    replicate_seed: int,
    replicate_generator,
    discrepancy,
    discrepancy_statistic_identity: str,
) -> PosteriorPredictiveReceipt:
    _validate_weighted_posterior_draws(draws)
    observed = _array(observed_data, ndim=1, field="observed_data")
    if isinstance(replicate_seed, bool) or not isinstance(replicate_seed, int) or replicate_seed < 0:
        raise BayesianSemanticsError("replicate_seed must be a nonnegative integer")
    if not callable(replicate_generator) or not callable(discrepancy):
        raise BayesianSemanticsError("replicate generator and discrepancy must be callable")
    if not isinstance(discrepancy_statistic_identity, str) or not discrepancy_statistic_identity:
        raise BayesianSemanticsError("discrepancy statistic identity is required")
    root_seed = np.random.SeedSequence(replicate_seed)
    child_seeds = root_seed.spawn(len(draws.samples))
    replicated: list[np.ndarray] = []
    observed_discrepancies: list[float] = []
    replicated_discrepancies: list[float] = []
    indicators: list[int] = []
    shape: tuple[int, ...] | None = None
    for theta, child in zip(draws.samples, child_seeds, strict=True):
        rng = np.random.default_rng(child)
        observed_statistic = float(
            discrepancy(np.array(observed, copy=True), np.array(theta, copy=True))
        )
        if not math.isfinite(observed_statistic):
            raise BayesianSemanticsError("observed discrepancy is not finite")
        value = _array(
            replicate_generator(np.array(theta, copy=True), rng),
            ndim=1,
            field="replicated dataset",
        )
        if shape is None:
            shape = value.shape
        elif value.shape != shape:
            raise BayesianSemanticsError("replicated dataset shape drifted")
        statistic = float(
            discrepancy(np.array(value, copy=True), np.array(theta, copy=True))
        )
        if not math.isfinite(statistic):
            raise BayesianSemanticsError("replicated discrepancy is not finite")
        replicated.append(value)
        observed_discrepancies.append(observed_statistic)
        replicated_discrepancies.append(statistic)
        indicators.append(int(statistic >= observed_statistic))
    replicated_array = np.stack(replicated)
    weights = draws.normalized_weights
    predictive_mean = np.average(replicated_array, axis=0, weights=weights)
    centered = replicated_array - predictive_mean
    predictive_sd = np.sqrt(np.average(centered**2, axis=0, weights=weights))
    pvalue = float(np.dot(weights, np.asarray(indicators, dtype=float)))
    summaries = MappingProxyType(
        {
            "weighted_mean": predictive_mean.tolist(),
            "weighted_standard_deviation": predictive_sd.tolist(),
            "replicate_inventory_content_id": canonical_content_id(replicated_array),
        }
    )
    seed_commitment = canonical_content_id(
        {"domain": "PR288_PPC_REPLICATE_SEED_V1", "seed": replicate_seed}
    )
    unsigned = {
        "schema": "HTT_PR288_POSTERIOR_PREDICTIVE_RECEIPT_V1",
        "posterior_draw_content_id": draws.draw_content_id,
        "posterior_sample_content_sha256": draws.posterior_sample_content_sha256,
        "normalized_weight_content_sha256": draws.normalized_weight_content_sha256,
        "replicate_seed_commitment": seed_commitment,
        "model_and_likelihood_identity": draws.model_and_likelihood_identity,
        "discrepancy_statistic_identity": discrepancy_statistic_identity,
        "observed_discrepancies": observed_discrepancies,
        "replicated_discrepancies": replicated_discrepancies,
        "comparison_indicators": indicators,
        "posterior_predictive_pvalue": pvalue,
        "predictive_summaries": dict(summaries),
        "equality_rule": "replicated_discrepancy_greater_or_equal_observed_counts_in_tail",
        "status": "PASS_REGISTERED_POSTERIOR_DRAW_PPC",
    }
    return PosteriorPredictiveReceipt(
        **{
            key: value
            for key, value in unsigned.items()
            if key
            not in {
                "schema",
                "observed_discrepancies",
                "replicated_discrepancies",
                "comparison_indicators",
                "predictive_summaries",
            }
        },
        observed_discrepancies=tuple(observed_discrepancies),
        replicated_discrepancies=tuple(replicated_discrepancies),
        comparison_indicators=tuple(indicators),
        predictive_summaries=summaries,
        receipt_content_id=canonical_content_id(unsigned),
        _construction_token=_PPC_TOKEN,
    )


def validate_posterior_predictive_receipt(
    receipt: PosteriorPredictiveReceipt, *, draws: WeightedPosteriorDraws
) -> PosteriorPredictiveReceipt:
    if type(receipt) is not PosteriorPredictiveReceipt:
        raise BayesianSemanticsError(
            "receipt must be an exact PosteriorPredictiveReceipt"
        )
    _validate_weighted_posterior_draws(draws)
    if (
        receipt.posterior_draw_content_id != draws.draw_content_id
        or receipt.posterior_sample_content_sha256
        != draws.posterior_sample_content_sha256
        or receipt.normalized_weight_content_sha256
        != draws.normalized_weight_content_sha256
        or receipt.model_and_likelihood_identity
        != draws.model_and_likelihood_identity
    ):
        raise BayesianSemanticsError("PPC posterior draw identity drifted")
    if (
        len(receipt.observed_discrepancies) != len(draws.samples)
        or len(receipt.replicated_discrepancies) != len(draws.samples)
        or len(receipt.comparison_indicators) != len(draws.samples)
    ):
        raise BayesianSemanticsError("PPC comparison inventory drifted")
    expected_indicators = tuple(
        int(replicated >= observed)
        for observed, replicated in zip(
            receipt.observed_discrepancies,
            receipt.replicated_discrepancies,
            strict=True,
        )
    )
    expected_pvalue = float(
        np.dot(draws.normalized_weights, np.asarray(expected_indicators, dtype=float))
    )
    if (
        receipt.comparison_indicators != expected_indicators
        or not math.isclose(
            receipt.posterior_predictive_pvalue,
            expected_pvalue,
            rel_tol=0.0,
            abs_tol=1e-15,
        )
        or receipt.equality_rule
        != "replicated_discrepancy_greater_or_equal_observed_counts_in_tail"
        or receipt.status != "PASS_REGISTERED_POSTERIOR_DRAW_PPC"
        or receipt.receipt_content_id
        != canonical_content_id(receipt.unsigned_payload())
    ):
        raise BayesianSemanticsError("PPC receipt content identity drifted")
    return receipt


def run_registered_posterior_predictive(
    fixture: EvidenceFixture, *, spec_path: Path
) -> tuple[WeightedPosteriorDraws, PosteriorPredictiveReceipt]:
    fixtures = load_registered_fixtures(spec_path)
    registered = fixtures.get(fixture.fixture_id)
    if registered is None or registered.fixture_content_id != fixture.fixture_content_id:
        raise BayesianSemanticsError("PPC fixture identity is unregistered")
    contract = _load_spec(spec_path)["posterior_predictive_contract"]
    if fixture.fixture_id != contract["fixture_id"]:
        raise BayesianSemanticsError("fixture is not the registered PPC fixture")
    if (
        contract["replicate_generator"]
        != "normalized_multivariate_gaussian_from_registered_design_and_covariance"
        or contract["discrepancy_statistic"]
        != "registered_whitened_quadratic_residual"
    ):
        raise BayesianSemanticsError("registered PPC computation identity drifted")
    draw_count = int(contract["registered_draw_count"])
    draws = draw_conjugate_gaussian_posterior(
        fixture,
        draw_count=draw_count,
        seed=int(contract["posterior_draw_seed"]),
    )
    covariance_inverse = np.linalg.inv(fixture.covariance)

    def replicate_generator(theta: np.ndarray, rng) -> np.ndarray:
        return rng.multivariate_normal(
            fixture.design_matrix @ theta,
            fixture.covariance,
        )

    def discrepancy(values: np.ndarray, theta: np.ndarray) -> float:
        residual = values - fixture.design_matrix @ theta
        return float(residual @ covariance_inverse @ residual)

    discrepancy_identity = canonical_content_id(
        {
            "domain": "PR288_REGISTERED_WHITENED_QUADRATIC_RESIDUAL_V1",
            "fixture_content_id": fixture.fixture_content_id,
            "covariance_content_id": canonical_content_id(fixture.covariance),
            "design_content_id": canonical_content_id(fixture.design_matrix),
            "drawwise_parameter_residual": True,
        }
    )
    receipt = run_posterior_draw_ppc(
        draws=draws,
        observed_data=fixture.observations,
        replicate_seed=int(contract["replicate_seed"]),
        replicate_generator=replicate_generator,
        discrepancy=discrepancy,
        discrepancy_statistic_identity=discrepancy_identity,
    )
    return draws, receipt


@dataclass(frozen=True)
class FoldPredictiveResult:
    held_out_id: str
    training_input_identity: str
    held_out_input_identity: str
    nuisance_refit_identity: str
    posterior_draw_identity: str
    integrated_held_out_log_predictive_density: float
    fit_status: str
    posterior_draw_count: int
    fold_seed: int
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _LOOCV_TOKEN:
            raise BayesianSemanticsError(
                "FoldPredictiveResult must be factory-derived"
            )

    def payload(self) -> dict[str, object]:
        return {
            "held_out_id": self.held_out_id,
            "training_input_identity": self.training_input_identity,
            "held_out_input_identity": self.held_out_input_identity,
            "nuisance_refit_identity": self.nuisance_refit_identity,
            "posterior_draw_identity": self.posterior_draw_identity,
            "integrated_held_out_log_predictive_density": (
                self.integrated_held_out_log_predictive_density
            ),
            "fit_status": self.fit_status,
            "posterior_draw_count": self.posterior_draw_count,
            "fold_seed": self.fold_seed,
        }


@dataclass(frozen=True)
class LOOCVReceipt:
    fixture_id: str
    fixture_content_id: str
    registered_fold_order: tuple[str, ...]
    fold_results: tuple[FoldPredictiveResult, ...]
    aggregate_log_predictive_density: float
    status: str
    receipt_content_id: str
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _LOOCV_TOKEN:
            raise BayesianSemanticsError("LOOCVReceipt must be factory-derived")

    def unsigned_payload(self) -> dict[str, object]:
        return {
            "schema": "HTT_PR288_FOLDWISE_LOOCV_RECEIPT_V1",
            "fixture_id": self.fixture_id,
            "fixture_content_id": self.fixture_content_id,
            "registered_fold_order": list(self.registered_fold_order),
            "fold_results": [row.payload() for row in self.fold_results],
            "aggregate_log_predictive_density": (
                self.aggregate_log_predictive_density
            ),
            "status": self.status,
        }


def _compute_foldwise_loocv(
    fixture: EvidenceFixture, *, spec_path: Path
) -> LOOCVReceipt:
    fixtures = load_registered_fixtures(spec_path)
    registered = fixtures.get(fixture.fixture_id)
    if registered is None or registered.fixture_content_id != fixture.fixture_content_id:
        raise BayesianSemanticsError("LOOCV fixture identity is unregistered")
    spec = _load_spec(spec_path)
    contract = spec["loocv_contract"]
    if fixture.fixture_id != contract["fixture_id"]:
        raise BayesianSemanticsError("fixture is not the registered LOOCV fixture")
    fold_order = tuple(contract["registered_fold_order"])
    seeds = tuple(contract["fold_draw_seeds"])
    draw_count = int(contract["posterior_draws_per_fold"])
    if (
        len(fold_order) < int(contract["minimum_folds"])
        or len(fold_order) != len(fixture.observations)
        or len(fold_order) != len(seeds)
        or len(set(fold_order)) != len(fold_order)
        or len(set(seeds)) != len(seeds)
    ):
        raise BayesianSemanticsError("registered LOOCV fold inventory is invalid")

    rows: list[FoldPredictiveResult] = []
    all_indices = np.arange(len(fixture.observations), dtype=int)
    for held_out_index, (held_out_id, seed) in enumerate(
        zip(fold_order, seeds, strict=True)
    ):
        training_indices = all_indices[all_indices != held_out_index]
        training_fixture = _build_fixture(
            fixture_id=f"{fixture.fixture_id}#TRAIN-WITHOUT-{held_out_id}",
            dimension=fixture.dimension,
            observations=fixture.observations[training_indices],
            design_matrix=fixture.design_matrix[training_indices, :],
            covariance=fixture.covariance[np.ix_(training_indices, training_indices)],
            prior_mean=fixture.prior_mean,
            prior_covariance=fixture.prior_covariance,
            units=fixture.units,
            base_measure=fixture.base_measure,
        )
        draws = draw_conjugate_gaussian_posterior(
            training_fixture, draw_count=draw_count, seed=int(seed)
        )

        training_covariance = fixture.covariance[
            np.ix_(training_indices, training_indices)
        ]
        held_to_training = fixture.covariance[
            held_out_index, training_indices
        ]
        conditional_gain = held_to_training @ np.linalg.inv(training_covariance)
        conditional_variance = float(
            fixture.covariance[held_out_index, held_out_index]
            - conditional_gain
            @ fixture.covariance[training_indices, held_out_index]
        )
        if not math.isfinite(conditional_variance) or conditional_variance <= 0:
            raise BayesianSemanticsError(
                "held-out conditional variance must be positive"
            )
        training_residuals = (
            fixture.observations[training_indices, None]
            - fixture.design_matrix[training_indices, :] @ draws.samples.T
        )
        held_out_means = (
            fixture.design_matrix[held_out_index, :] @ draws.samples.T
            + conditional_gain @ training_residuals
        )
        held_out_value = float(fixture.observations[held_out_index])
        log_densities = -0.5 * (
            math.log(2.0 * math.pi * conditional_variance)
            + (held_out_value - held_out_means) ** 2 / conditional_variance
        )
        integrated_log_density = float(
            logsumexp(np.log(draws.normalized_weights) + log_densities)
        )
        training_identity = canonical_content_id(
            {
                "fold_id": held_out_id,
                "training_indices": training_indices.tolist(),
                "training_fixture_content_id": training_fixture.fixture_content_id,
            }
        )
        held_out_identity = canonical_content_id(
            {
                "fold_id": held_out_id,
                "held_out_index": held_out_index,
                "held_out_observation": held_out_value,
                "held_out_design_row": fixture.design_matrix[
                    held_out_index, :
                ],
                "held_out_covariance_row": fixture.covariance[
                    held_out_index, :
                ],
            }
        )
        nuisance_refit_identity = canonical_content_id(
            {
                "method": contract["fold_refit_method"],
                "training_input_identity": training_identity,
                "posterior_draw_identity": draws.draw_content_id,
                "nuisance_parameter_indices": contract[
                    "nuisance_parameter_indices"
                ],
                "conditional_covariance_used": True,
                "correlated_holdout_rule": contract[
                    "correlated_holdout_rule"
                ],
            }
        )
        rows.append(
            FoldPredictiveResult(
                held_out_id=held_out_id,
                training_input_identity=training_identity,
                held_out_input_identity=held_out_identity,
                nuisance_refit_identity=nuisance_refit_identity,
                posterior_draw_identity=draws.draw_content_id,
                integrated_held_out_log_predictive_density=integrated_log_density,
                fit_status="PASS_FOLDWISE_NUISANCE_REFIT",
                posterior_draw_count=draw_count,
                fold_seed=int(seed),
                _construction_token=_LOOCV_TOKEN,
            )
        )
    aggregate = float(
        sum(row.integrated_held_out_log_predictive_density for row in rows)
    )
    unsigned = {
        "schema": "HTT_PR288_FOLDWISE_LOOCV_RECEIPT_V1",
        "fixture_id": fixture.fixture_id,
        "fixture_content_id": fixture.fixture_content_id,
        "registered_fold_order": list(fold_order),
        "fold_results": [row.payload() for row in rows],
        "aggregate_log_predictive_density": aggregate,
        "status": "PASS_FOLDWISE_REFIT_LOOCV",
    }
    return LOOCVReceipt(
        fixture_id=fixture.fixture_id,
        fixture_content_id=fixture.fixture_content_id,
        registered_fold_order=fold_order,
        fold_results=tuple(rows),
        aggregate_log_predictive_density=aggregate,
        status="PASS_FOLDWISE_REFIT_LOOCV",
        receipt_content_id=canonical_content_id(unsigned),
        _construction_token=_LOOCV_TOKEN,
    )


def run_foldwise_loocv(
    fixture: EvidenceFixture, *, spec_path: Path
) -> LOOCVReceipt:
    receipt = _compute_foldwise_loocv(fixture, spec_path=spec_path)
    return validate_loocv_receipt(receipt, fixture=fixture, spec_path=spec_path)


def validate_loocv_receipt(
    receipt: LOOCVReceipt, *, fixture: EvidenceFixture, spec_path: Path
) -> LOOCVReceipt:
    if type(receipt) is not LOOCVReceipt:
        raise BayesianSemanticsError("receipt must be an exact LOOCVReceipt")
    spec = _load_spec(spec_path)
    contract = spec["loocv_contract"]
    expected_order = tuple(contract["registered_fold_order"])
    observed_order = tuple(row.held_out_id for row in receipt.fold_results)
    if (
        receipt.registered_fold_order != expected_order
        or observed_order != expected_order
        or len(receipt.fold_results) != len(expected_order)
    ):
        raise BayesianSemanticsError("LOOCV fold inventory drifted")
    posterior_ids = tuple(row.posterior_draw_identity for row in receipt.fold_results)
    if len(set(posterior_ids)) != len(posterior_ids):
        raise BayesianSemanticsError("LOOCV posterior draw identity was reused")
    if any(
        row.posterior_draw_count != int(contract["posterior_draws_per_fold"])
        or row.fold_seed != int(seed)
        or row.fit_status != "PASS_FOLDWISE_NUISANCE_REFIT"
        for row, seed in zip(
            receipt.fold_results, contract["fold_draw_seeds"], strict=True
        )
    ):
        raise BayesianSemanticsError("LOOCV fold refit metadata drifted")
    if not math.isclose(
        receipt.aggregate_log_predictive_density,
        sum(
            row.integrated_held_out_log_predictive_density
            for row in receipt.fold_results
        ),
        rel_tol=0.0,
        abs_tol=1e-14,
    ):
        raise BayesianSemanticsError("LOOCV aggregate drifted")
    expected = _compute_foldwise_loocv(fixture, spec_path=spec_path)
    if (
        receipt.fixture_id != fixture.fixture_id
        or receipt.fixture_content_id != fixture.fixture_content_id
        or receipt.status != "PASS_FOLDWISE_REFIT_LOOCV"
        or receipt.unsigned_payload() != expected.unsigned_payload()
        or receipt.receipt_content_id
        != canonical_content_id(receipt.unsigned_payload())
    ):
        raise BayesianSemanticsError(
            "LOOCV receipt differs from registered foldwise recomputation"
        )
    return receipt


@dataclass(frozen=True)
class EvidenceCrosscheck:
    fixture_id: str
    status: str
    absolute_log_evidence_difference: float | None
    threshold: float | None
    analytic_log_evidence: float
    dynesty_content_id: str
    sobol_content_id: str

    def payload(self) -> dict[str, object]:
        return {
            "fixture_id": self.fixture_id,
            "status": self.status,
            "absolute_log_evidence_difference": self.absolute_log_evidence_difference,
            "threshold": self.threshold,
            "analytic_log_evidence": self.analytic_log_evidence,
            "dynesty_content_id": self.dynesty_content_id,
            "sobol_content_id": self.sobol_content_id,
        }


def compare_independent_evidence(
    first: EngineEvidenceResult,
    second: EngineEvidenceResult,
    *,
    spec_path: Path,
) -> EvidenceCrosscheck:
    if (
        first.independent_estimate_content_id is not None
        and first.independent_estimate_content_id
        == second.independent_estimate_content_id
    ):
        raise BayesianSemanticsError("engines reused an independent estimate")
    if (
        first.sample_or_node_inventory_content_id is not None
        and first.sample_or_node_inventory_content_id
        == second.sample_or_node_inventory_content_id
    ):
        raise BayesianSemanticsError("engines reused samples or quadrature nodes")
    validate_engine_evidence_result(first)
    validate_engine_evidence_result(second)
    if first.engine_id == second.engine_id:
        raise BayesianSemanticsError("crosscheck requires two distinct engines")
    if first.fixture_id != second.fixture_id:
        raise BayesianSemanticsError("engine fixture identities differ")
    fixtures = load_registered_fixtures(spec_path)
    fixture = fixtures.get(first.fixture_id)
    if fixture is None:
        raise BayesianSemanticsError("crosscheck fixture is unregistered")
    analytic = analytic_log_evidence(fixture)
    if (
        first.status is not EngineRunStatus.PASS
        or second.status is not EngineRunStatus.PASS
    ):
        return EvidenceCrosscheck(
            fixture_id=first.fixture_id,
            status="BLOCKED_DEPENDENCY_OR_ENGINE",
            absolute_log_evidence_difference=None,
            threshold=None,
            analytic_log_evidence=analytic,
            dynesty_content_id=(first if first.engine_id == "DYNESTY_NESTED" else second).result_content_id,
            sobol_content_id=(first if first.engine_id == "SCIPY_SOBOL_QMC" else second).result_content_id,
        )
    dynesty_result = first if first.engine_id == "DYNESTY_NESTED" else second
    sobol_result = first if first.engine_id == "SCIPY_SOBOL_QMC" else second
    if {first.engine_id, second.engine_id} != {"DYNESTY_NESTED", "SCIPY_SOBOL_QMC"}:
        raise BayesianSemanticsError("registered engine pair drifted")
    assert first.log_evidence is not None and second.log_evidence is not None
    assert first.declared_standard_uncertainty is not None
    assert second.declared_standard_uncertainty is not None
    difference = abs(first.log_evidence - second.log_evidence)
    spec = _load_spec(spec_path)
    rule = spec["engine_contract"]["combined_uncertainty_rule"]
    threshold = max(
        float(rule["deterministic_floor"]),
        float(rule["k_sigma"])
        * math.sqrt(
            first.declared_standard_uncertainty**2
            + second.declared_standard_uncertainty**2
        ),
    )
    analytic_ok = all(
        abs(result.log_evidence - analytic)
        <= max(0.05, 3 * result.declared_standard_uncertainty)
        for result in (first, second)
    )
    return EvidenceCrosscheck(
        fixture_id=first.fixture_id,
        status=(
            "PASS_INDEPENDENT_EVIDENCE_CROSSCHECK"
            if difference <= threshold and analytic_ok
            else "BLOCKED_EVIDENCE_CROSSCHECK"
        ),
        absolute_log_evidence_difference=difference,
        threshold=threshold,
        analytic_log_evidence=analytic,
        dynesty_content_id=dynesty_result.result_content_id,
        sobol_content_id=sobol_result.result_content_id,
    )


@dataclass(frozen=True)
class DegenerateNullControl:
    model_fixture_ids: tuple[str, str]
    log_bayes_factors: Mapping[str, float | None]
    compatibility_thresholds: Mapping[str, float | None]
    engine_result_content_ids: Mapping[str, tuple[str, str]]
    status: str
    control_content_id: str
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _RECEIPT_TOKEN:
            raise BayesianSemanticsError(
                "DegenerateNullControl must be factory-derived"
            )

    def unsigned_payload(self) -> dict[str, object]:
        return {
            "schema": "HTT_PR288_DEGENERATE_NULL_CONTROL_V1",
            "model_fixture_ids": list(self.model_fixture_ids),
            "log_bayes_factors": dict(self.log_bayes_factors),
            "compatibility_thresholds": dict(self.compatibility_thresholds),
            "engine_result_content_ids": {
                key: list(value)
                for key, value in self.engine_result_content_ids.items()
            },
            "status": self.status,
        }


@dataclass(frozen=True)
class NegativeControlResult:
    generator_fixture_content_id: str
    analysis_fixture_content_id: str
    analytic_log_evidence_shift: float
    required_minimum_shift: float
    status: str
    control_content_id: str
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _RECEIPT_TOKEN:
            raise BayesianSemanticsError(
                "NegativeControlResult must be factory-derived"
            )

    def unsigned_payload(self) -> dict[str, object]:
        return {
            "schema": "HTT_PR288_NEGATIVE_CONTROL_RESULT_V1",
            "generator_fixture_content_id": self.generator_fixture_content_id,
            "analysis_fixture_content_id": self.analysis_fixture_content_id,
            "analytic_log_evidence_shift": self.analytic_log_evidence_shift,
            "required_minimum_shift": self.required_minimum_shift,
            "status": self.status,
        }


@dataclass(frozen=True)
class RegisteredMutationResult:
    mutation_id: str
    executed: bool
    activated: bool
    killed: bool
    expected_marker: str
    observed_marker: str
    evidence_content_id: str
    result_content_id: str
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _MUTATION_TOKEN:
            raise BayesianSemanticsError(
                "RegisteredMutationResult must be factory-derived"
            )

    def unsigned_payload(self) -> dict[str, object]:
        return {
            "schema": "HTT_PR288_REGISTERED_MUTATION_RESULT_V1",
            "mutation_id": self.mutation_id,
            "executed": self.executed,
            "activated": self.activated,
            "killed": self.killed,
            "expected_marker": self.expected_marker,
            "observed_marker": self.observed_marker,
            "evidence_content_id": self.evidence_content_id,
        }


@dataclass(frozen=True)
class BayesianSemanticsReceipt:
    engine_results: tuple[EngineEvidenceResult, ...]
    evidence_crosschecks: tuple[EvidenceCrosscheck, ...]
    null_control: DegenerateNullControl
    negative_control: NegativeControlResult
    posterior_draws: WeightedPosteriorDraws
    posterior_predictive: PosteriorPredictiveReceipt
    loocv: LOOCVReceipt
    mutation_results: tuple[RegisteredMutationResult, ...]
    source_bindings: tuple[Mapping[str, str], ...]
    metadata: Mapping[str, object]
    generation_identity: str
    terminal: str
    reasons: tuple[str, ...]
    receipt_content_id: str
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _RECEIPT_TOKEN:
            raise BayesianSemanticsError(
                "BayesianSemanticsReceipt must be factory-derived"
            )

    def unsigned_payload(self) -> dict[str, object]:
        return {
            "schema": "HTT_PR288_BAYESIAN_SEMANTICS_RECEIPT_V1",
            "engine_results": [
                {**row.unsigned_payload(), "result_content_id": row.result_content_id}
                for row in self.engine_results
            ],
            "evidence_crosschecks": [
                row.payload() for row in self.evidence_crosschecks
            ],
            "degenerate_null_control": {
                **self.null_control.unsigned_payload(),
                "control_content_id": self.null_control.control_content_id,
            },
            "negative_control": {
                **self.negative_control.unsigned_payload(),
                "control_content_id": self.negative_control.control_content_id,
            },
            "posterior_draws": {
                **self.posterior_draws.unsigned_payload(),
                "draw_content_id": self.posterior_draws.draw_content_id,
            },
            "posterior_predictive": {
                **self.posterior_predictive.unsigned_payload(),
                "receipt_content_id": self.posterior_predictive.receipt_content_id,
            },
            "loocv": {
                **self.loocv.unsigned_payload(),
                "receipt_content_id": self.loocv.receipt_content_id,
            },
            "mutation_results": [
                {**row.unsigned_payload(), "result_content_id": row.result_content_id}
                for row in self.mutation_results
            ],
            "source_bindings": [dict(row) for row in self.source_bindings],
            "metadata": dict(self.metadata),
            "generation_identity": self.generation_identity,
            "terminal": self.terminal,
            "reasons": list(self.reasons),
        }

    def payload(self) -> dict[str, object]:
        return {
            **self.unsigned_payload(),
            "receipt_content_id": self.receipt_content_id,
        }


def _mutant(value: object, **changes: object) -> object:
    out = copy(value)
    for key, replacement in changes.items():
        object.__setattr__(out, key, replacement)
    return out


def _sha256_regular_file(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise BayesianSemanticsError(f"source binding is not regular: {path}")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _registered_source_bindings(
    *, spec_path: Path, repository_root: Path
) -> tuple[Mapping[str, str], ...]:
    spec = _load_spec(spec_path)
    contract = spec.get("receipt_contract")
    if not isinstance(contract, dict):
        raise BayesianSemanticsError("receipt contract is missing")
    expected = (
        "docs/research_program/post_pr275/pr288_spec.yaml",
        "htt/htt/htt/infer/bayesian_semantics.py",
        "scripts/codex_harness/run_pr288_bayesian_semantics.py",
        "tests/htt/test_bayesian_semantics_repair.py",
    )
    if tuple(contract.get("source_bindings_required", ())) != expected:
        raise BayesianSemanticsError("source binding inventory drifted")
    root = repository_root.resolve(strict=True)
    bindings: list[Mapping[str, str]] = []
    for relative in expected:
        candidate = root / relative
        try:
            candidate.relative_to(root)
        except ValueError as exc:
            raise BayesianSemanticsError("source binding escaped repository root") from exc
        bindings.append(
            MappingProxyType(
                {"path": relative, "sha256": _sha256_regular_file(candidate)}
            )
        )
    return tuple(bindings)


def _expected_sobol_seeds(
    fixture_id: str, *, spec_path: Path
) -> tuple[int, ...]:
    config = _engine_config(spec_path, "SCIPY_SOBOL_QMC")
    by_fixture = config.get("scramble_seeds_by_fixture")
    if not isinstance(by_fixture, Mapping):
        raise BayesianSemanticsError("Sobol fixture seed inventory is missing")
    seeds = by_fixture.get(fixture_id)
    if (
        not isinstance(seeds, list)
        or len(seeds) != int(config.get("scramble_count", -1))
        or len(set(seeds)) != len(seeds)
        or any(isinstance(seed, bool) or not isinstance(seed, int) for seed in seeds)
    ):
        raise BayesianSemanticsError("Sobol fixture seed inventory drifted")
    return tuple(seeds)


def _validate_registered_engine_inventory(
    results: Sequence[EngineEvidenceResult],
    *,
    fixtures: Mapping[str, EvidenceFixture],
    spec_path: Path,
) -> tuple[EngineEvidenceResult, ...]:
    expected_pairs = tuple(
        (fixture_id, engine_id)
        for fixture_id in fixtures
        for engine_id in ("DYNESTY_NESTED", "SCIPY_SOBOL_QMC")
    )
    observed_pairs = tuple((row.fixture_id, row.engine_id) for row in results)
    if observed_pairs != expected_pairs:
        raise BayesianSemanticsError("registered engine inventory drifted")
    dynesty_config = _engine_config(spec_path, "DYNESTY_NESTED")
    dynesty_seeds = dynesty_config.get("fixture_seeds")
    sobol_config = _engine_config(spec_path, "SCIPY_SOBOL_QMC")
    for result in results:
        validate_engine_evidence_result(result)
        if (
            result.likelihood_and_prior_contract_content_id
            != fixtures[result.fixture_id].fixture_content_id
        ):
            raise BayesianSemanticsError("engine fixture contract identity drifted")
        if result.engine_id == "DYNESTY_NESTED":
            expected_seed = (
                dynesty_seeds.get(result.fixture_id)
                if isinstance(dynesty_seeds, Mapping)
                else None
            )
            if result.status is EngineRunStatus.PASS and (
                result.scramble_or_seed_inventory != (expected_seed,)
                or result.termination_status != "COMPLETED_DLOGZ_THRESHOLD"
                or result.independent_linear_evidence_estimates
                or not isinstance(result.engine_version, str)
                or not result.engine_version.startswith("dynesty-")
                or _release_tuple(result.engine_version.removeprefix("dynesty-"))
                < _release_tuple(str(dynesty_config["version_floor"]))
            ):
                raise BayesianSemanticsError("Dynesty registered configuration drifted")
        else:
            expected_seeds = _expected_sobol_seeds(
                result.fixture_id, spec_path=spec_path
            )
            expected_calls = len(expected_seeds) * 2 ** int(sobol_config["power_m"])
            if (
                result.scramble_or_seed_inventory != expected_seeds
                or result.termination_status
                != "COMPLETED_POWER_OF_TWO_SCRAMBLES"
                or len(result.independent_linear_evidence_estimates)
                != len(expected_seeds)
                or result.effective_or_live_sample_count != expected_calls
                or result.likelihood_call_count != expected_calls
                or not isinstance(result.engine_version, str)
                or not result.engine_version.startswith("scipy-")
            ):
                raise BayesianSemanticsError("Sobol registered configuration drifted")
    return tuple(results)


def _build_crosschecks(
    results: Sequence[EngineEvidenceResult], *, spec_path: Path
) -> tuple[EvidenceCrosscheck, ...]:
    return tuple(
        compare_independent_evidence(
            results[index], results[index + 1], spec_path=spec_path
        )
        for index in range(0, len(results), 2)
    )


def _validate_crosschecks(
    crosschecks: Sequence[EvidenceCrosscheck],
    *,
    engine_results: Sequence[EngineEvidenceResult],
    spec_path: Path,
) -> tuple[EvidenceCrosscheck, ...]:
    expected = _build_crosschecks(engine_results, spec_path=spec_path)
    if tuple(crosschecks) != expected:
        raise BayesianSemanticsError("evidence crosscheck threshold or result drifted")
    return tuple(crosschecks)


def _build_null_control(
    results: Sequence[EngineEvidenceResult], *, spec_path: Path
) -> DegenerateNullControl:
    indexed = {(row.fixture_id, row.engine_id): row for row in results}
    model_ids = (
        "PR288-NULL-EQUAL-MODELS-A",
        "PR288-NULL-EQUAL-MODELS-B",
    )
    log_bayes_factors: dict[str, float | None] = {}
    thresholds: dict[str, float | None] = {}
    content_ids: dict[str, tuple[str, str]] = {}
    blocked = False
    failed = False
    for engine_id in ("DYNESTY_NESTED", "SCIPY_SOBOL_QMC"):
        first = indexed[(model_ids[0], engine_id)]
        second = indexed[(model_ids[1], engine_id)]
        content_ids[engine_id] = (first.result_content_id, second.result_content_id)
        if (
            first.status is not EngineRunStatus.PASS
            or second.status is not EngineRunStatus.PASS
        ):
            blocked = True
            log_bayes_factors[engine_id] = None
            thresholds[engine_id] = None
            continue
        assert first.log_evidence is not None and second.log_evidence is not None
        assert first.declared_standard_uncertainty is not None
        assert second.declared_standard_uncertainty is not None
        difference = first.log_evidence - second.log_evidence
        threshold = max(
            0.02,
            3
            * math.sqrt(
                first.declared_standard_uncertainty**2
                + second.declared_standard_uncertainty**2
            ),
        )
        log_bayes_factors[engine_id] = difference
        thresholds[engine_id] = threshold
        failed = failed or abs(difference) > threshold
    status = (
        "BLOCKED_DEPENDENCY_OR_ENGINE"
        if blocked
        else (
            "BLOCKED_DEGENERATE_NULL_FALSE_PREFERENCE"
            if failed
            else "PASS_DEGENERATE_NULL_COMPATIBLE_WITH_ZERO"
        )
    )
    unsigned = {
        "schema": "HTT_PR288_DEGENERATE_NULL_CONTROL_V1",
        "model_fixture_ids": list(model_ids),
        "log_bayes_factors": log_bayes_factors,
        "compatibility_thresholds": thresholds,
        "engine_result_content_ids": {
            key: list(value) for key, value in content_ids.items()
        },
        "status": status,
    }
    return DegenerateNullControl(
        model_fixture_ids=model_ids,
        log_bayes_factors=MappingProxyType(log_bayes_factors),
        compatibility_thresholds=MappingProxyType(thresholds),
        engine_result_content_ids=MappingProxyType(content_ids),
        status=status,
        control_content_id=canonical_content_id(unsigned),
        _construction_token=_RECEIPT_TOKEN,
    )


def _validate_null_control(
    control: DegenerateNullControl,
    *,
    engine_results: Sequence[EngineEvidenceResult],
    spec_path: Path,
) -> DegenerateNullControl:
    expected = _build_null_control(engine_results, spec_path=spec_path)
    if (
        type(control) is not DegenerateNullControl
        or control.unsigned_payload() != expected.unsigned_payload()
        or control.control_content_id
        != canonical_content_id(control.unsigned_payload())
    ):
        raise BayesianSemanticsError("degenerate null control drifted")
    return control


def _build_negative_control(
    fixtures: Mapping[str, EvidenceFixture], *, spec_path: Path
) -> NegativeControlResult:
    generator = fixtures["PR288-REGISTERED-CORRELATED-NUISANCE"]
    analysis = fixtures["PR288-MISSPECIFIED-NEGATIVE-CONTROL"]
    spec = _load_spec(spec_path)
    row = next(
        item
        for item in spec["evidence_fixtures"]
        if item["fixture_id"] == "PR288-MISSPECIFIED-NEGATIVE-CONTROL"
    )
    minimum = float(row["analytic_log_evidence_shift_minimum"])
    shift = abs(analytic_log_evidence(generator) - analytic_log_evidence(analysis))
    status = (
        "MISSPECIFIED_NEGATIVE_CONTROL_VISIBLE"
        if (
            generator.fixture_content_id != analysis.fixture_content_id
            and shift >= minimum
        )
        else "BLOCKED_NEGATIVE_CONTROL_HIDDEN"
    )
    unsigned = {
        "schema": "HTT_PR288_NEGATIVE_CONTROL_RESULT_V1",
        "generator_fixture_content_id": generator.fixture_content_id,
        "analysis_fixture_content_id": analysis.fixture_content_id,
        "analytic_log_evidence_shift": shift,
        "required_minimum_shift": minimum,
        "status": status,
    }
    return NegativeControlResult(
        generator_fixture_content_id=generator.fixture_content_id,
        analysis_fixture_content_id=analysis.fixture_content_id,
        analytic_log_evidence_shift=shift,
        required_minimum_shift=minimum,
        status=status,
        control_content_id=canonical_content_id(unsigned),
        _construction_token=_RECEIPT_TOKEN,
    )


def _validate_negative_control(
    control: NegativeControlResult,
    *,
    fixtures: Mapping[str, EvidenceFixture],
    spec_path: Path,
) -> NegativeControlResult:
    expected = _build_negative_control(fixtures, spec_path=spec_path)
    if (
        type(control) is not NegativeControlResult
        or control.unsigned_payload() != expected.unsigned_payload()
        or control.control_content_id
        != canonical_content_id(control.unsigned_payload())
    ):
        raise BayesianSemanticsError("negative control identity or visibility drifted")
    return control


def _expected_claim_metadata(
    *,
    spec: Mapping[str, object],
    spec_path: Path,
    fixtures: Mapping[str, EvidenceFixture],
    engine_results: Sequence[EngineEvidenceResult],
    draws: WeightedPosteriorDraws,
    ppc: PosteriorPredictiveReceipt,
    loocv: LOOCVReceipt,
    null_control: DegenerateNullControl,
    negative_control: NegativeControlResult,
    generation_identity: str,
) -> Mapping[str, object]:
    if generation_identity not in {
        "EXTERNAL_CANDIDATE_SEAL_OR_SOURCE_HASHES",
        "SYSTEM_REQUIRED_ENGINE_PROBE",
        "UNIT_TEST_DOUBLE_NOT_ACCEPTANCE_EVIDENCE",
    }:
        raise BayesianSemanticsError("generation identity is not registered")
    metadata = {
        "owner": spec["owner"],
        "scope": spec["scope"],
        "claim_tier": spec["claim_tier"],
        "claim_level": spec["claim_level"],
        "scientific_artifact_mode": spec["scientific_artifact_mode"],
        "transfer_source": spec["transfer_source"],
        "observed_data_executed": spec["observed_data_executed"],
        "public_use": spec["public_use"],
        "family_identification_gate": spec["family_identification_gate"],
        "scientific_status_effect": spec["scientific_status_effect"],
        "allowed_uses": list(spec["allowed_uses"]),
        "forbidden_uses": list(spec["forbidden_uses"]),
        "legacy_disposition": spec["legacy_disposition"],
        "fixture_and_config_identities": {
            key: value.fixture_content_id for key, value in fixtures.items()
        },
        "posterior_draw_and_fold_identities": {
            "posterior_draw_content_id": draws.draw_content_id,
            "posterior_predictive_receipt_content_id": ppc.receipt_content_id,
            "loocv_receipt_content_id": loocv.receipt_content_id,
            "fold_posterior_draw_content_ids": [
                row.posterior_draw_identity for row in loocv.fold_results
            ],
        },
        "covariance_and_null_status": {
            "sky_support_status": "synthetic_no_observed_sky",
            "covariance_status": (
                "registered_synthetic_full_and_misspecified_control"
            ),
            "null_status": null_control.status,
        },
        "assumptions": [
            "normalized registered Gaussian likelihoods and priors",
            "frozen analytic and synthetic fixtures only",
            "independent Dynesty and scrambled Sobol estimates",
            "foldwise nuisance refit with registered conditional covariance",
        ],
        "caveats": list(spec["caveats"]),
        "generating_procedure": (
            "scripts/codex_harness/run_pr288_bayesian_semantics.py engines"
        ),
        "git_commit_or_worktree_state": generation_identity,
        "engine_versions_and_seed_inventories": [
            {
                "engine_id": row.engine_id,
                "fixture_id": row.fixture_id,
                "engine_version": row.engine_version,
                "seed_inventory": list(row.scramble_or_seed_inventory),
            }
            for row in engine_results
        ],
        "analytic_accuracy_and_null_status": {
            "crosscheck_statuses": [
                row.status
                for row in _build_crosschecks(
                    engine_results, spec_path=spec_path
                )
            ],
            "null_control_status": null_control.status,
        },
        "negative_control_status": negative_control.status,
    }
    if set(metadata) != set(_FROZEN_RECEIPT_METADATA):
        raise BayesianSemanticsError(
            "generated receipt metadata inventory drifted"
        )
    return MappingProxyType(metadata)


def _validate_claim_metadata(
    metadata: Mapping[str, object], *, expected: Mapping[str, object]
) -> None:
    if not isinstance(metadata, Mapping) or dict(metadata) != dict(expected):
        raise BayesianSemanticsError("claim metadata drifted or was promoted")


def _registered_mutation_ids(spec_path: Path) -> tuple[str, ...]:
    rows = _load_spec(spec_path).get("mutation_registry")
    if not isinstance(rows, list):
        raise BayesianSemanticsError("mutation registry is missing")
    values = tuple(
        row.get("mutation_id") for row in rows if isinstance(row, dict)
    )
    expected = (
        "MU288-SINGLE-ENGINE",
        "MU288-SHARED-SAMPLES",
        "MU288-POSTHOC-TOLERANCE",
        "MU288-DEGENERATE-NULL-PREFERENCE",
        "MU288-SOBOL-UNCERTAINTY",
        "MU288-PPC-CALLER-PVALUE",
        "MU288-PPC-PLUGIN",
        "MU288-PPC-DRAW-IDENTITY",
        "MU288-LOOCV-FULL-POSTERIOR",
        "MU288-LOOCV-FIXED-NUISANCE",
        "MU288-LOOCV-FOLD-INVENTORY",
        "MU288-NEGATIVE-CONTROL-HIDDEN",
        "MU288-LEGACY-ANCHOR",
        "MU288-MUTATION-OMISSION",
        "MU288-CLAIM-PROMOTION",
    )
    if values != expected:
        raise BayesianSemanticsError("mutation registry drifted")
    return expected


def _mutation_result(
    mutation_id: str,
    expected_marker: str,
    probe,
) -> RegisteredMutationResult:
    observed_marker = "NO_REJECTION"
    killed = False
    try:
        probe()
    except (BayesianSemanticsError, TypeError) as exc:
        observed_marker = f"{type(exc).__name__}:{exc}"
        killed = expected_marker in str(exc)
    evidence_id = canonical_content_id(
        {
            "domain": "PR288_MUTATION_EXECUTION_EVIDENCE_V1",
            "mutation_id": mutation_id,
            "expected_marker": expected_marker,
            "observed_marker": observed_marker,
        }
    )
    unsigned = {
        "schema": "HTT_PR288_REGISTERED_MUTATION_RESULT_V1",
        "mutation_id": mutation_id,
        "executed": True,
        "activated": True,
        "killed": killed,
        "expected_marker": expected_marker,
        "observed_marker": observed_marker,
        "evidence_content_id": evidence_id,
    }
    return RegisteredMutationResult(
        mutation_id=mutation_id,
        executed=True,
        activated=True,
        killed=killed,
        expected_marker=expected_marker,
        observed_marker=observed_marker,
        evidence_content_id=evidence_id,
        result_content_id=canonical_content_id(unsigned),
        _construction_token=_MUTATION_TOKEN,
    )


def _validate_mutation_results(
    results: Sequence[RegisteredMutationResult], *, spec_path: Path
) -> tuple[RegisteredMutationResult, ...]:
    expected_ids = _registered_mutation_ids(spec_path)
    observed_ids = tuple(row.mutation_id for row in results)
    if observed_ids != expected_ids:
        raise BayesianSemanticsError("registered mutation inventory drifted")
    for row in results:
        if (
            type(row) is not RegisteredMutationResult
            or not row.executed
            or not row.activated
            or not row.killed
            or row.observed_marker == "NO_REJECTION"
            or row.result_content_id
            != canonical_content_id(row.unsigned_payload())
        ):
            raise BayesianSemanticsError("registered mutation result is incomplete")
    return tuple(results)


def _run_registered_mutations(
    *,
    fixtures: Mapping[str, EvidenceFixture],
    engine_results: tuple[EngineEvidenceResult, ...],
    crosschecks: tuple[EvidenceCrosscheck, ...],
    null_control: DegenerateNullControl,
    negative_control: NegativeControlResult,
    draws: WeightedPosteriorDraws,
    ppc: PosteriorPredictiveReceipt,
    loocv: LOOCVReceipt,
    metadata: Mapping[str, object],
    spec_path: Path,
) -> tuple[RegisteredMutationResult, ...]:
    normal_dynesty, normal_sobol = engine_results[:2]
    results: list[RegisteredMutationResult] = []

    results.append(
        _mutation_result(
            "MU288-SINGLE-ENGINE",
            "registered engine inventory",
            lambda: _validate_registered_engine_inventory(
                engine_results[1:], fixtures=fixtures, spec_path=spec_path
            ),
        )
    )

    shared = _mutant(
        normal_dynesty if normal_dynesty.status is EngineRunStatus.PASS else normal_sobol,
        engine_id="DYNESTY_NESTED",
        sample_or_node_inventory_content_id=normal_sobol.sample_or_node_inventory_content_id,
        independent_estimate_content_id=canonical_content_id(
            {"domain": "PR288_SHARED_SAMPLE_MUTATION"}
        ),
    )
    object.__setattr__(shared, "result_content_id", canonical_content_id(shared.unsigned_payload()))
    results.append(
        _mutation_result(
            "MU288-SHARED-SAMPLES",
            "reused samples",
            lambda: compare_independent_evidence(shared, normal_sobol, spec_path=spec_path),
        )
    )

    posthoc = _mutant(
        crosschecks[0], threshold=(crosschecks[0].threshold or 0.02) * 10.0
    )
    results.append(
        _mutation_result(
            "MU288-POSTHOC-TOLERANCE",
            "threshold or result drifted",
            lambda: _validate_crosschecks(
                (posthoc, *crosschecks[1:]),
                engine_results=engine_results,
                spec_path=spec_path,
            ),
        )
    )

    null_bf = dict(null_control.log_bayes_factors)
    null_bf["SCIPY_SOBOL_QMC"] = 1.0
    null_mutant = _mutant(null_control, log_bayes_factors=MappingProxyType(null_bf))
    results.append(
        _mutation_result(
            "MU288-DEGENERATE-NULL-PREFERENCE",
            "degenerate null control",
            lambda: _validate_null_control(
                null_mutant,
                engine_results=engine_results,
                spec_path=spec_path,
            ),
        )
    )

    one_scramble = _mutant(
        normal_sobol,
        independent_linear_evidence_estimates=(
            normal_sobol.independent_linear_evidence_estimates[0],
        ),
    )
    object.__setattr__(
        one_scramble,
        "result_content_id",
        canonical_content_id(one_scramble.unsigned_payload()),
    )
    results.append(
        _mutation_result(
            "MU288-SOBOL-UNCERTAINTY",
            "Sobol registered configuration",
            lambda: _validate_registered_engine_inventory(
                (normal_dynesty, one_scramble, *engine_results[2:]),
                fixtures=fixtures,
                spec_path=spec_path,
            ),
        )
    )

    results.append(
        _mutation_result(
            "MU288-PPC-CALLER-PVALUE",
            "unexpected keyword argument 'pvalue'",
            lambda: run_posterior_draw_ppc(
                draws=draws,
                observed_data=fixtures["PR288-REGISTERED-CORRELATED-NUISANCE"].observations,
                replicate_seed=288202,
                replicate_generator=lambda theta, rng: np.asarray(theta),
                discrepancy=lambda values, theta: float(np.sum(values - theta)),
                discrepancy_statistic_identity="MUTANT",
                pvalue=0.5,
            ),
        )
    )

    plugin = _mutant(ppc, discrepancy_statistic_identity="PLUGIN_POSTERIOR_MEAN")
    object.__setattr__(plugin, "receipt_content_id", canonical_content_id(plugin.unsigned_payload()))
    results.append(
        _mutation_result(
            "MU288-PPC-PLUGIN",
            "registered PPC",
            lambda: _validate_registered_ppc(
                plugin,
                draws=draws,
                fixture=fixtures["PR288-REGISTERED-CORRELATED-NUISANCE"],
                spec_path=spec_path,
            ),
        )
    )

    draw_drift = _mutant(ppc, posterior_draw_content_id="sha256:" + "0" * 64)
    results.append(
        _mutation_result(
            "MU288-PPC-DRAW-IDENTITY",
            "posterior draw identity",
            lambda: validate_posterior_predictive_receipt(draw_drift, draws=draws),
        )
    )

    reused_row = _mutant(
        loocv.fold_results[1],
        posterior_draw_identity=loocv.fold_results[0].posterior_draw_identity,
    )
    reused_loocv = _mutant(
        loocv,
        fold_results=(loocv.fold_results[0], reused_row, *loocv.fold_results[2:]),
    )
    results.append(
        _mutation_result(
            "MU288-LOOCV-FULL-POSTERIOR",
            "posterior draw identity",
            lambda: validate_loocv_receipt(
                reused_loocv,
                fixture=fixtures["PR288-REGISTERED-CORRELATED-NUISANCE"],
                spec_path=spec_path,
            ),
        )
    )

    fixed_row = _mutant(loocv.fold_results[0], nuisance_refit_identity="FIXED_FULL_DATA")
    fixed_loocv = _mutant(
        loocv, fold_results=(fixed_row, *loocv.fold_results[1:])
    )
    results.append(
        _mutation_result(
            "MU288-LOOCV-FIXED-NUISANCE",
            "registered foldwise recomputation",
            lambda: validate_loocv_receipt(
                fixed_loocv,
                fixture=fixtures["PR288-REGISTERED-CORRELATED-NUISANCE"],
                spec_path=spec_path,
            ),
        )
    )

    missing_fold = _mutant(loocv, fold_results=loocv.fold_results[:-1])
    results.append(
        _mutation_result(
            "MU288-LOOCV-FOLD-INVENTORY",
            "fold inventory",
            lambda: validate_loocv_receipt(
                missing_fold,
                fixture=fixtures["PR288-REGISTERED-CORRELATED-NUISANCE"],
                spec_path=spec_path,
            ),
        )
    )

    hidden_negative = _mutant(
        negative_control,
        analysis_fixture_content_id=negative_control.generator_fixture_content_id,
        analytic_log_evidence_shift=0.0,
    )
    results.append(
        _mutation_result(
            "MU288-NEGATIVE-CONTROL-HIDDEN",
            "negative control identity or visibility",
            lambda: _validate_negative_control(
                hidden_negative, fixtures=fixtures, spec_path=spec_path
            ),
        )
    )

    legacy_metadata = dict(metadata)
    legacy_metadata["legacy_disposition"] = {
        **dict(legacy_metadata["legacy_disposition"]),
        "status": "CURRENT_ENGINE_ANCHOR",
    }
    results.append(
        _mutation_result(
            "MU288-LEGACY-ANCHOR",
            "claim metadata",
            lambda: _validate_claim_metadata(legacy_metadata, expected=metadata),
        )
    )

    results.append(
        _mutation_result(
            "MU288-MUTATION-OMISSION",
            "mutation inventory",
            lambda: _validate_mutation_results(results, spec_path=spec_path),
        )
    )

    promoted_metadata = dict(metadata)
    promoted_metadata.update(
        {
            "observed_data_executed": True,
            "public_use": True,
            "family_identification_gate": "PASS",
        }
    )
    results.append(
        _mutation_result(
            "MU288-CLAIM-PROMOTION",
            "claim metadata",
            lambda: _validate_claim_metadata(promoted_metadata, expected=metadata),
        )
    )
    return _validate_mutation_results(results, spec_path=spec_path)


def _validate_registered_ppc(
    receipt: PosteriorPredictiveReceipt,
    *,
    draws: WeightedPosteriorDraws,
    fixture: EvidenceFixture,
    spec_path: Path,
) -> PosteriorPredictiveReceipt:
    validate_posterior_predictive_receipt(receipt, draws=draws)
    expected_draws, expected = run_registered_posterior_predictive(
        fixture, spec_path=spec_path
    )
    if (
        draws.unsigned_payload() != expected_draws.unsigned_payload()
        or receipt.unsigned_payload() != expected.unsigned_payload()
        or receipt.receipt_content_id != expected.receipt_content_id
    ):
        raise BayesianSemanticsError("registered PPC recomputation drifted")
    return receipt


def _derive_terminal(
    *,
    engine_results: Sequence[EngineEvidenceResult],
    crosschecks: Sequence[EvidenceCrosscheck],
    null_control: DegenerateNullControl,
    negative_control: NegativeControlResult,
    ppc: PosteriorPredictiveReceipt,
    loocv: LOOCVReceipt,
    mutation_results: Sequence[RegisteredMutationResult],
) -> tuple[str, tuple[str, ...]]:
    if any(row.status is not EngineRunStatus.PASS for row in engine_results):
        return "BLOCKED_DEPENDENCY_OR_ENGINE", (
            "required Dynesty engine unavailable or incomplete",
        )
    if (
        any(row.status != "PASS_INDEPENDENT_EVIDENCE_CROSSCHECK" for row in crosschecks)
        or null_control.status != "PASS_DEGENERATE_NULL_COMPATIBLE_WITH_ZERO"
        or negative_control.status != "MISSPECIFIED_NEGATIVE_CONTROL_VISIBLE"
    ):
        return "BLOCKED_EVIDENCE_CROSSCHECK", (
            "engine, analytic, null, or negative-control crosscheck failed",
        )
    if (
        ppc.status != "PASS_REGISTERED_POSTERIOR_DRAW_PPC"
        or loocv.status != "PASS_FOLDWISE_REFIT_LOOCV"
    ):
        return "BLOCKED_PPC_OR_LOOCV_CONTRACT", (
            "posterior predictive or foldwise-refit contract failed",
        )
    if any(
        not (row.executed and row.activated and row.killed)
        for row in mutation_results
    ):
        return "BLOCKED_REGISTERED_MUTATION", (
            "one or more registered mutations survived or were omitted",
        )
    return "PASS_BAYESIAN_SEMANTICS_REPAIR", ()


def build_bayesian_semantics_receipt(
    spec_path: Path,
    *,
    repository_root: Path,
    generation_identity: str = "EXTERNAL_CANDIDATE_SEAL_OR_SOURCE_HASHES",
) -> BayesianSemanticsReceipt:
    spec_path = spec_path.resolve(strict=True)
    root = repository_root.resolve(strict=True)
    spec = _load_spec(spec_path)
    fixtures = load_registered_fixtures(spec_path)
    engine_results_list: list[EngineEvidenceResult] = []
    for fixture in fixtures.values():
        engine_results_list.extend(
            (
                run_dynesty_evidence(fixture, spec_path=spec_path),
                run_scrambled_sobol_evidence(fixture, spec_path=spec_path),
            )
        )
    engine_results = _validate_registered_engine_inventory(
        engine_results_list, fixtures=fixtures, spec_path=spec_path
    )
    crosschecks = _build_crosschecks(engine_results, spec_path=spec_path)
    _validate_crosschecks(
        crosschecks, engine_results=engine_results, spec_path=spec_path
    )
    null_control = _build_null_control(engine_results, spec_path=spec_path)
    _validate_null_control(
        null_control, engine_results=engine_results, spec_path=spec_path
    )
    negative_control = _build_negative_control(fixtures, spec_path=spec_path)
    _validate_negative_control(
        negative_control, fixtures=fixtures, spec_path=spec_path
    )
    ppc_fixture = fixtures["PR288-REGISTERED-CORRELATED-NUISANCE"]
    draws, ppc = run_registered_posterior_predictive(
        ppc_fixture, spec_path=spec_path
    )
    _validate_registered_ppc(
        ppc, draws=draws, fixture=ppc_fixture, spec_path=spec_path
    )
    loocv = run_foldwise_loocv(ppc_fixture, spec_path=spec_path)
    metadata = _expected_claim_metadata(
        spec=spec,
        spec_path=spec_path,
        fixtures=fixtures,
        engine_results=engine_results,
        draws=draws,
        ppc=ppc,
        loocv=loocv,
        null_control=null_control,
        negative_control=negative_control,
        generation_identity=generation_identity,
    )
    _validate_claim_metadata(metadata, expected=metadata)
    mutations = _validate_mutation_results(
        _run_registered_mutations(
            fixtures=fixtures,
            engine_results=engine_results,
            crosschecks=crosschecks,
            null_control=null_control,
            negative_control=negative_control,
            draws=draws,
            ppc=ppc,
            loocv=loocv,
            metadata=metadata,
            spec_path=spec_path,
        ),
        spec_path=spec_path,
    )
    terminal, reasons = _derive_terminal(
        engine_results=engine_results,
        crosschecks=crosschecks,
        null_control=null_control,
        negative_control=negative_control,
        ppc=ppc,
        loocv=loocv,
        mutation_results=mutations,
    )
    source_bindings = _registered_source_bindings(
        spec_path=spec_path, repository_root=root
    )
    unsigned = {
        "schema": "HTT_PR288_BAYESIAN_SEMANTICS_RECEIPT_V1",
        "engine_results": [
            {**row.unsigned_payload(), "result_content_id": row.result_content_id}
            for row in engine_results
        ],
        "evidence_crosschecks": [row.payload() for row in crosschecks],
        "degenerate_null_control": {
            **null_control.unsigned_payload(),
            "control_content_id": null_control.control_content_id,
        },
        "negative_control": {
            **negative_control.unsigned_payload(),
            "control_content_id": negative_control.control_content_id,
        },
        "posterior_draws": {
            **draws.unsigned_payload(),
            "draw_content_id": draws.draw_content_id,
        },
        "posterior_predictive": {
            **ppc.unsigned_payload(),
            "receipt_content_id": ppc.receipt_content_id,
        },
        "loocv": {
            **loocv.unsigned_payload(),
            "receipt_content_id": loocv.receipt_content_id,
        },
        "mutation_results": [
            {**row.unsigned_payload(), "result_content_id": row.result_content_id}
            for row in mutations
        ],
        "source_bindings": [dict(row) for row in source_bindings],
        "metadata": dict(metadata),
        "generation_identity": generation_identity,
        "terminal": terminal,
        "reasons": list(reasons),
    }
    return BayesianSemanticsReceipt(
        engine_results=engine_results,
        evidence_crosschecks=crosschecks,
        null_control=null_control,
        negative_control=negative_control,
        posterior_draws=draws,
        posterior_predictive=ppc,
        loocv=loocv,
        mutation_results=mutations,
        source_bindings=source_bindings,
        metadata=metadata,
        generation_identity=generation_identity,
        terminal=terminal,
        reasons=reasons,
        receipt_content_id=canonical_content_id(unsigned),
        _construction_token=_RECEIPT_TOKEN,
    )


def validate_bayesian_semantics_receipt(
    receipt: BayesianSemanticsReceipt,
    *,
    spec_path: Path,
    repository_root: Path,
) -> BayesianSemanticsReceipt:
    if type(receipt) is not BayesianSemanticsReceipt:
        raise BayesianSemanticsError(
            "receipt must be an exact BayesianSemanticsReceipt"
        )
    spec_path = spec_path.resolve(strict=True)
    spec = _load_spec(spec_path)
    fixtures = load_registered_fixtures(spec_path)
    _validate_registered_engine_inventory(
        receipt.engine_results, fixtures=fixtures, spec_path=spec_path
    )
    _validate_crosschecks(
        receipt.evidence_crosschecks,
        engine_results=receipt.engine_results,
        spec_path=spec_path,
    )
    _validate_null_control(
        receipt.null_control,
        engine_results=receipt.engine_results,
        spec_path=spec_path,
    )
    _validate_negative_control(
        receipt.negative_control, fixtures=fixtures, spec_path=spec_path
    )
    ppc_fixture = fixtures["PR288-REGISTERED-CORRELATED-NUISANCE"]
    _validate_registered_ppc(
        receipt.posterior_predictive,
        draws=receipt.posterior_draws,
        fixture=ppc_fixture,
        spec_path=spec_path,
    )
    validate_loocv_receipt(
        receipt.loocv, fixture=ppc_fixture, spec_path=spec_path
    )
    _validate_mutation_results(receipt.mutation_results, spec_path=spec_path)
    expected_metadata = _expected_claim_metadata(
        spec=spec,
        spec_path=spec_path,
        fixtures=fixtures,
        engine_results=receipt.engine_results,
        draws=receipt.posterior_draws,
        ppc=receipt.posterior_predictive,
        loocv=receipt.loocv,
        null_control=receipt.null_control,
        negative_control=receipt.negative_control,
        generation_identity=receipt.generation_identity,
    )
    _validate_claim_metadata(receipt.metadata, expected=expected_metadata)
    expected_bindings = _registered_source_bindings(
        spec_path=spec_path, repository_root=repository_root
    )
    if tuple(dict(row) for row in receipt.source_bindings) != tuple(
        dict(row) for row in expected_bindings
    ):
        raise BayesianSemanticsError("source binding bytes drifted")
    terminal, reasons = _derive_terminal(
        engine_results=receipt.engine_results,
        crosschecks=receipt.evidence_crosschecks,
        null_control=receipt.null_control,
        negative_control=receipt.negative_control,
        ppc=receipt.posterior_predictive,
        loocv=receipt.loocv,
        mutation_results=receipt.mutation_results,
    )
    if receipt.terminal != terminal or receipt.reasons != reasons:
        raise BayesianSemanticsError("terminal precedence drifted")
    if receipt.receipt_content_id != canonical_content_id(receipt.unsigned_payload()):
        raise BayesianSemanticsError("receipt content identity drifted")
    return receipt


__all__ = [
    "BayesianSemanticsReceipt",
    "BayesianSemanticsError",
    "DegenerateNullControl",
    "EngineEvidenceResult",
    "EngineRunStatus",
    "EvidenceCrosscheck",
    "EvidenceFixture",
    "FoldPredictiveResult",
    "LOOCVReceipt",
    "NegativeControlResult",
    "PosteriorPredictiveReceipt",
    "RegisteredMutationResult",
    "WeightedPosteriorDraws",
    "analytic_log_evidence",
    "build_weighted_posterior_draws",
    "build_bayesian_semantics_receipt",
    "canonical_content_id",
    "compare_independent_evidence",
    "draw_conjugate_gaussian_posterior",
    "load_registered_fixtures",
    "run_dynesty_evidence",
    "run_foldwise_loocv",
    "run_posterior_draw_ppc",
    "run_registered_posterior_predictive",
    "run_scrambled_sobol_evidence",
    "validate_engine_evidence_result",
    "validate_bayesian_semantics_receipt",
    "validate_loocv_receipt",
    "validate_posterior_predictive_receipt",
]
