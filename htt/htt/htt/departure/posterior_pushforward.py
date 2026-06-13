"""HTT posterior pushforward diagnostics for PR-066.

The pushforward maps HTT posterior samples onto diagnostic scalar functionals
with explicit transfer provenance. It records Q, F, Pi, and G_F summaries but
does not consume MIO certificates or MIO report cards.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from enum import StrEnum
import hashlib
import json
import math
from typing import Any

from common.contracts import ArtifactManifest, ClaimTier, ImplementationScope, Owner
from common.transfer_registry import (
    TransferSource,
    validate_transfer_dependent_result,
)
from workspace.contracts.htt_posterior import reject_mio_likelihood_inputs


SCHEMA_VERSION = "htt.departure.posterior_pushforward.v1"
_CREATED_BY = "htt.departure.posterior_pushforward.build_posterior_pushforward_report"
_DEFAULT_ARTIFACT_PATH = "memory://htt/departure/posterior_pushforward.json"
_DEFAULT_CAVEATS = (
    "htt_owned_posterior_pushforward_diagnostic",
    "transfer_conditional_pre_solver_result",
    "mio_certificate_and_report_outputs_not_consumed",
    "scalar_functionals_do_not_identify_geometry_or_family",
)
_EXPECTED_STATUSES = {
    "local_global_status": "ready_diagnostic_likelihood",
    "inference_adequacy_status": "inference_adequacy_ready",
    "matched_null_status": "matched_null_ready",
    "prior_sweep_status": "prior_sweep_ready",
    "posterior_predictive_status": "posterior_predictive_ready",
    "loocv_status": "loocv_ready",
}
_FORBIDDEN_MIO_TOKENS = (
    "pvalue",
    "p_value",
    "evidence",
    "likelihood",
    "posterior",
    "truth",
    "score",
    "model_weight",
    "bayes_factor",
    "ln_b",
    "lnb",
)


class PiSource(StrEnum):
    """Source functional for the PR-066 exceedance curve."""

    Q = "Q"
    F = "F"
    G_F = "G_F"


def _non_empty(value: object, field_name: str) -> str:
    text = str(value).strip()
    if not text:
        raise ValueError(f"{field_name} must be non-empty")
    return text


def _optional_non_empty(value: object | None, field_name: str) -> str | None:
    if value is None:
        return None
    return _non_empty(value, field_name)


def _finite_float(value: object, field_name: str) -> float:
    out = float(value)
    if not math.isfinite(out):
        raise ValueError(f"{field_name} must be finite")
    return out


def _positive_float(value: object, field_name: str) -> float:
    out = _finite_float(value, field_name)
    if out <= 0.0:
        raise ValueError(f"{field_name} must be positive")
    return out


def _unit_interval(value: object, field_name: str) -> float:
    out = _finite_float(value, field_name)
    if not 0.0 <= out <= 1.0:
        raise ValueError(f"{field_name} must be in [0, 1]")
    return out


def _tuple_of_str(
    values: Sequence[object],
    field_name: str,
    *,
    require_non_empty: bool = False,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be a sequence")
    out = tuple(_non_empty(value, field_name) for value in values)
    if require_non_empty and not out:
        raise ValueError(f"{field_name} must contain at least one entry")
    return out


def _plain_json(value: object) -> Any:
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): _plain_json(item) for key, item in value.items()}
    if isinstance(value, (str, bytes)):
        return str(value)
    if isinstance(value, Sequence):
        return [_plain_json(item) for item in value]
    if isinstance(value, float):
        if not math.isfinite(value):
            raise TypeError("payload floats must be finite")
        return value
    if isinstance(value, (int, bool)) or value is None:
        return value
    raise TypeError(f"value {value!r} is not JSON-compatible")


def _stable_hash(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(
        _plain_json(payload),
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _manifest_payload(manifest: ArtifactManifest) -> dict[str, Any]:
    payload = _plain_json(asdict(manifest))
    if not isinstance(payload, dict):
        raise TypeError("manifest payload must be a mapping")
    return payload


def _normalise_key(value: object) -> str:
    return str(value).strip().lower().replace("-", "_").replace(" ", "_")


def _looks_like_mio_diagnostic_payload(value: Mapping[object, object]) -> bool:
    keys = {_normalise_key(key) for key in value}
    owner = _normalise_key(value.get("owner", value.get("source_owner", "")))
    scope = _normalise_key(value.get("implementation_scope", ""))
    mio_markers = {
        "sections",
        "score_order",
        "report_type",
        "departure_variables",
        "adequacy_indicators",
        "consistency_metrics",
        "reduction_status",
    }
    return owner == "mio" or scope == "mio" or bool(keys & mio_markers)


def _scan_mio_leakage(value: object, path: str) -> None:
    if isinstance(value, Mapping):
        if _looks_like_mio_diagnostic_payload(value):
            raise TypeError(
                "MIO diagnostic payload cannot be a posterior pushforward input"
            )
        for key, item in value.items():
            canonical = _normalise_key(key)
            if canonical.startswith("mio_") and any(
                token in canonical for token in _FORBIDDEN_MIO_TOKENS
            ):
                raise TypeError(f"{path}.{canonical} cannot be a pushforward input")
            _scan_mio_leakage(item, f"{path}.{canonical}")
        return
    if isinstance(value, (list, tuple, set, frozenset)):
        for index, item in enumerate(value):
            _scan_mio_leakage(item, f"{path}[{index}]")


def reject_mio_pushforward_inputs(*values: object) -> None:
    """Reject MIO certificate/report-card objects or MIO-shaped mappings."""

    try:
        reject_mio_likelihood_inputs(*values)
    except (TypeError, ValueError) as exc:
        raise TypeError(
            "MIO diagnostic payload cannot be a posterior pushforward input"
        ) from exc
    for value in values:
        _scan_mio_leakage(value, "pushforward_input")


def _canonical_transfer_source(value: object) -> TransferSource:
    try:
        return TransferSource(str(value))
    except ValueError as exc:
        raise ValueError(f"unknown transfer_source {value!r}") from exc


def _validate_sample_transfer(
    *,
    transfer_source: TransferSource,
    transfer_spec_id: str | None,
    transfer_metadata: Mapping[str, object] | None,
) -> None:
    if transfer_source in {
        TransferSource.BASS_NATIVE_PROVISIONAL,
        TransferSource.BASS_NATIVE_VALIDATED,
    }:
        raise ValueError("PR-066 does not consume native transfer provenance")
    if transfer_source is TransferSource.NONE:
        if transfer_spec_id is not None or transfer_metadata is not None:
            raise ValueError("transfer_source='none' cannot carry transfer provenance")
        return
    if transfer_spec_id is None:
        raise ValueError("transfer-dependent samples require transfer_spec_id")
    if transfer_metadata is None:
        raise ValueError("transfer-dependent samples require transfer_metadata")
    validate_transfer_dependent_result(transfer_metadata)
    metadata_source = str(transfer_metadata["transfer_source"])
    if metadata_source != transfer_source.value:
        raise ValueError("sample transfer_source must match transfer_metadata")
    metadata_id = transfer_metadata.get("transfer_id")
    if metadata_id is not None and str(metadata_id) != transfer_spec_id:
        raise ValueError("sample transfer_spec_id must match transfer_metadata")


def _dedupe(values: Sequence[str]) -> tuple[str, ...]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value not in seen:
            seen.add(value)
            out.append(value)
    return tuple(out)


def _require_samples(
    samples: Sequence["PosteriorPushforwardSample"],
) -> tuple["PosteriorPushforwardSample", ...]:
    if isinstance(samples, (str, bytes)):
        raise ValueError("samples must be a non-string sequence")
    out = tuple(samples)
    if not out:
        raise ValueError("samples must contain at least one posterior sample")
    if any(not isinstance(sample, PosteriorPushforwardSample) for sample in out):
        raise TypeError("samples must contain PosteriorPushforwardSample entries")
    sample_ids = [sample.sample_id for sample in out]
    if len(set(sample_ids)) != len(sample_ids):
        raise ValueError("posterior sample ids must be unique")
    return out


def _normalised_weights(
    samples: Sequence["PosteriorPushforwardSample"],
) -> tuple[float, ...]:
    total = math.fsum(sample.posterior_weight for sample in samples)
    if total <= 0.0:
        raise ValueError("posterior weights must have positive total")
    return tuple(sample.posterior_weight / total for sample in samples)


def _weighted_mean(values: Sequence[float], weights: Sequence[float]) -> float:
    return math.fsum(
        value * weight for value, weight in zip(values, weights, strict=True)
    )


def _weighted_quantile(
    values: Sequence[float],
    weights: Sequence[float],
    quantile: float,
) -> float:
    if not 0.0 <= quantile <= 1.0:
        raise ValueError("quantile must be in [0, 1]")
    ordered = sorted(zip(values, weights, strict=True), key=lambda item: item[0])
    cumulative = 0.0
    for value, weight in ordered:
        cumulative += weight
        if cumulative >= quantile:
            return float(value)
    return float(ordered[-1][0])


def _weighted_summary(
    values: Sequence[float],
    weights: Sequence[float],
) -> dict[str, object]:
    weighted_mean = _weighted_mean(values, weights)
    variance = _weighted_mean(
        tuple((value - weighted_mean) ** 2 for value in values),
        weights,
    )
    return {
        "weighted_mean": weighted_mean,
        "weighted_std": math.sqrt(max(variance, 0.0)),
        "min": min(values),
        "max": max(values),
        "weighted_quantiles": {
            "q05": _weighted_quantile(values, weights, 0.05),
            "q16": _weighted_quantile(values, weights, 0.16),
            "q50": _weighted_quantile(values, weights, 0.50),
            "q84": _weighted_quantile(values, weights, 0.84),
            "q95": _weighted_quantile(values, weights, 0.95),
        },
    }


def _thresholds(values: Sequence[object]) -> tuple[float, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("pi_thresholds must be a non-string sequence")
    out = tuple(_finite_float(value, "pi_thresholds") for value in values)
    if not out:
        raise ValueError("pi_thresholds must contain at least one threshold")
    return tuple(sorted(dict.fromkeys(out)))


@dataclass(frozen=True)
class PosteriorPushforwardSample:
    """One HTT posterior sample already mapped to diagnostic scalar values."""

    sample_id: str
    posterior_weight: float
    q_value: float
    f_value: float
    g_f_value: float
    x_c_value: float
    transfer_source: str = "none"
    transfer_spec_id: str | None = None
    transfer_metadata: Mapping[str, object] | None = None
    input_hashes: tuple[str, ...] = ()
    depth_bin_id: str | None = None
    sky_support_status: str = "not_directional"
    covariance_status: str = "not_statistical"
    null_mock_status: str = "not_statistical"

    def __post_init__(self) -> None:
        sample_id = _non_empty(self.sample_id, "sample_id")
        weight = _finite_float(self.posterior_weight, "posterior_weight")
        if weight < 0.0:
            raise ValueError("posterior_weight must be nonnegative")
        q_value = _finite_float(self.q_value, "q_value")
        f_value = _unit_interval(self.f_value, "f_value")
        g_f_value = _positive_float(self.g_f_value, "g_f_value")
        x_c_value = _finite_float(self.x_c_value, "x_c_value")
        transfer_source = _canonical_transfer_source(self.transfer_source)
        transfer_spec_id = _optional_non_empty(
            self.transfer_spec_id,
            "transfer_spec_id",
        )
        transfer_metadata = (
            None if self.transfer_metadata is None else dict(self.transfer_metadata)
        )
        _validate_sample_transfer(
            transfer_source=transfer_source,
            transfer_spec_id=transfer_spec_id,
            transfer_metadata=transfer_metadata,
        )
        input_hashes = _tuple_of_str(
            self.input_hashes,
            "input_hashes",
            require_non_empty=True,
        )
        object.__setattr__(self, "sample_id", sample_id)
        object.__setattr__(self, "posterior_weight", weight)
        object.__setattr__(self, "q_value", q_value)
        object.__setattr__(self, "f_value", f_value)
        object.__setattr__(self, "g_f_value", g_f_value)
        object.__setattr__(self, "x_c_value", x_c_value)
        object.__setattr__(self, "transfer_source", transfer_source.value)
        object.__setattr__(self, "transfer_spec_id", transfer_spec_id)
        object.__setattr__(self, "transfer_metadata", transfer_metadata)
        object.__setattr__(self, "input_hashes", input_hashes)
        object.__setattr__(
            self,
            "depth_bin_id",
            _optional_non_empty(self.depth_bin_id, "depth_bin_id"),
        )
        object.__setattr__(
            self,
            "sky_support_status",
            _non_empty(self.sky_support_status, "sky_support_status"),
        )
        object.__setattr__(
            self,
            "covariance_status",
            _non_empty(self.covariance_status, "covariance_status"),
        )
        object.__setattr__(
            self,
            "null_mock_status",
            _non_empty(self.null_mock_status, "null_mock_status"),
        )

    def as_payload(self) -> dict[str, object]:
        return {
            "sample_id": self.sample_id,
            "posterior_weight": self.posterior_weight,
            "x_C": self.x_c_value,
            "Q": self.q_value,
            "F": self.f_value,
            "G_F": self.g_f_value,
            "transfer_source": self.transfer_source,
            "transfer_spec_id": self.transfer_spec_id,
            "transfer_metadata": self.transfer_metadata,
            "input_hashes": list(self.input_hashes),
            "depth_bin_id": self.depth_bin_id,
            "sky_support_status": self.sky_support_status,
            "covariance_status": self.covariance_status,
            "null_mock_status": self.null_mock_status,
        }


@dataclass(frozen=True)
class PosteriorPushforwardPrerequisites:
    """HTT prerequisite statuses required before claim-bearing pushforward."""

    local_global_status: str
    local_global_report_hash: str
    inference_adequacy_status: str
    inference_adequacy_report_hash: str
    matched_null_status: str
    prior_sweep_status: str
    posterior_predictive_status: str
    loocv_status: str

    def __post_init__(self) -> None:
        for field_name in _EXPECTED_STATUSES:
            object.__setattr__(
                self,
                field_name,
                _non_empty(getattr(self, field_name), field_name),
            )
        object.__setattr__(
            self,
            "local_global_report_hash",
            _non_empty(self.local_global_report_hash, "local_global_report_hash"),
        )
        object.__setattr__(
            self,
            "inference_adequacy_report_hash",
            _non_empty(
                self.inference_adequacy_report_hash,
                "inference_adequacy_report_hash",
            ),
        )

    @property
    def blocked_reasons(self) -> tuple[str, ...]:
        reasons: list[str] = []
        for field_name, expected in _EXPECTED_STATUSES.items():
            actual = getattr(self, field_name)
            if actual != expected:
                reasons.append(field_name.replace("_status", "_not_ready"))
        return tuple(reasons)

    @property
    def ready_for_pushforward_claims(self) -> bool:
        return not self.blocked_reasons

    def as_payload(self) -> dict[str, object]:
        return {
            "local_global_status": self.local_global_status,
            "local_global_report_hash": self.local_global_report_hash,
            "inference_adequacy_status": self.inference_adequacy_status,
            "inference_adequacy_report_hash": self.inference_adequacy_report_hash,
            "matched_null_status": self.matched_null_status,
            "prior_sweep_status": self.prior_sweep_status,
            "posterior_predictive_status": self.posterior_predictive_status,
            "loocv_status": self.loocv_status,
            "ready_for_pushforward_claims": self.ready_for_pushforward_claims,
            "blocked_reasons": list(self.blocked_reasons),
        }


@dataclass(frozen=True)
class PosteriorPushforwardReport:
    """Manifest-backed HTT posterior pushforward report."""

    manifest: ArtifactManifest
    samples: tuple[PosteriorPushforwardSample, ...]
    prerequisites: PosteriorPushforwardPrerequisites
    pi_source: PiSource
    pi_thresholds: tuple[float, ...]
    summaries: Mapping[str, object]
    pi_payload: Mapping[str, object]
    pushforward_status: str
    blocked_reasons: tuple[str, ...]
    report_hash: str
    generating_command: str
    worktree_state: str | None
    git_commit: str | None
    transfer_source: str
    transfer_spec_id: str | None
    transfer_metadata: Mapping[str, object] | None
    caveats: tuple[str, ...]

    @property
    def ready_for_claims(self) -> bool:
        return self.pushforward_status == "posterior_pushforward_ready"

    def as_payload(self) -> dict[str, Any]:
        return _plain_json(
            {
                "owner": Owner.HTT.value,
                "implementation_scope": ImplementationScope.HTT.value,
                "claim_tier": self.manifest.claim_tier.value,
                "production_status": self.manifest.production_status,
                "schema_version": SCHEMA_VERSION,
                "manifest": _manifest_payload(self.manifest),
                "transfer_source": self.transfer_source,
                "transfer_spec_id": self.transfer_spec_id,
                "transfer_metadata": self.transfer_metadata,
                "config_hash": self.manifest.config_hash,
                "input_hashes": list(self.manifest.input_hashes),
                "sky_support_status": self.manifest.statistics_definitions[
                    "sky_support_status"
                ],
                "null_mock_status": self.manifest.statistics_definitions[
                    "null_mock_status"
                ],
                "generating_command": self.generating_command,
                "git_commit_or_worktree_state": (
                    self.git_commit or self.worktree_state or "unknown"
                ),
                "git_commit": self.git_commit,
                "worktree_state": self.worktree_state,
                "report_hash": self.report_hash,
                "pushforward_status": self.pushforward_status,
                "ready_for_claims": self.ready_for_claims,
                "posterior_sample_count": len(self.samples),
                "effective_sample_size": self.summaries["effective_sample_size"],
                "posterior_weight_sum": self.summaries["posterior_weight_sum"],
                "posterior_source_owner": "HTT",
                "mio_input_status": "not_consumed",
                "mio_certificate_input": False,
                "mio_certificate_input_status": "rejected_by_contract",
                "scalar_functionals": ["Q", "F", "Pi", "G_F"],
                "scalar_semantics": "posterior_pushforward_diagnostic_functionals",
                "native_solver_validation": "not_claimed",
                "morphology_compatibility": "not_claimed",
                "family_identification": "blocked_pre_native_morphology_atlas",
                "summaries": {
                    key: value
                    for key, value in self.summaries.items()
                    if key not in {"effective_sample_size", "posterior_weight_sum"}
                },
                "Pi": dict(self.pi_payload),
                "prerequisites": self.prerequisites.as_payload(),
                "samples": [sample.as_payload() for sample in self.samples],
                "blocked_reasons": list(self.blocked_reasons),
                "caveats": list(self.caveats),
                "claim_status": {
                    "owner": "HTT",
                    "surface": "posterior_pushforward",
                    "mio_status": "mio_certificate_and_report_outputs_not_consumed",
                    "native_solver_status": "not_native_solver_output",
                    "family_status": "blocked_pre_native_atlas",
                },
            }
        )


def _combined_transfer(
    samples: Sequence[PosteriorPushforwardSample],
) -> tuple[str, str | None, Mapping[str, object] | None]:
    sources = {sample.transfer_source for sample in samples}
    if len(sources) != 1:
        raise ValueError("posterior pushforward samples must share transfer_source")
    source = next(iter(sources))
    spec_ids = {sample.transfer_spec_id for sample in samples}
    if len(spec_ids) != 1:
        raise ValueError("posterior pushforward samples must share transfer_spec_id")
    metadata_hashes = {
        _stable_hash(sample.transfer_metadata)
        for sample in samples
        if sample.transfer_metadata is not None
    }
    if len(metadata_hashes) > 1:
        raise ValueError("posterior pushforward samples must share transfer_metadata")
    metadata = next(
        (
            sample.transfer_metadata
            for sample in samples
            if sample.transfer_metadata is not None
        ),
        None,
    )
    return source, next(iter(spec_ids)), metadata


def _passed_prerequisite_gates(
    prerequisites: PosteriorPushforwardPrerequisites,
) -> list[str]:
    passed: list[str] = []
    if prerequisites.local_global_status == _EXPECTED_STATUSES["local_global_status"]:
        passed.append("local_global_mixture_ready")
    if (
        prerequisites.inference_adequacy_status
        == _EXPECTED_STATUSES["inference_adequacy_status"]
    ):
        passed.append("inference_adequacy_ready")
    if prerequisites.matched_null_status == _EXPECTED_STATUSES["matched_null_status"]:
        passed.append("matched_null_ready")
    if (
        prerequisites.prior_sweep_status == _EXPECTED_STATUSES["prior_sweep_status"]
        and prerequisites.posterior_predictive_status
        == _EXPECTED_STATUSES["posterior_predictive_status"]
        and prerequisites.loocv_status == _EXPECTED_STATUSES["loocv_status"]
    ):
        passed.append("prior_ppc_loocv_ready")
    return passed


def _uniform_or_mixed(values: Sequence[str]) -> str:
    unique = set(values)
    if len(unique) == 1:
        return next(iter(unique))
    return "mixed"


def build_posterior_pushforward_report(
    *,
    samples: Sequence[PosteriorPushforwardSample],
    prerequisites: PosteriorPushforwardPrerequisites,
    pi_source: PiSource | str,
    pi_thresholds: Sequence[object],
    artifact_id: object,
    config_hash: object,
    input_hashes: Sequence[object],
    generating_command: object,
    artifact_path: object = _DEFAULT_ARTIFACT_PATH,
    worktree_state: object | None = None,
    git_commit: object | None = None,
    caveats: Sequence[object] = _DEFAULT_CAVEATS,
) -> PosteriorPushforwardReport:
    """Build an HTT-owned posterior pushforward diagnostic report."""

    reject_mio_pushforward_inputs(samples, prerequisites)
    resolved_samples = _require_samples(samples)
    if not isinstance(prerequisites, PosteriorPushforwardPrerequisites):
        raise TypeError("prerequisites must be PosteriorPushforwardPrerequisites")
    source = PiSource(str(pi_source))
    thresholds = _thresholds(pi_thresholds)
    artifact_id_text = _non_empty(artifact_id, "artifact_id")
    artifact_path_text = _non_empty(artifact_path, "artifact_path")
    config_hash_text = _non_empty(config_hash, "config_hash")
    input_hash_values = _tuple_of_str(
        input_hashes,
        "input_hashes",
        require_non_empty=True,
    )
    generating_command_text = _non_empty(generating_command, "generating_command")
    git_text = _optional_non_empty(git_commit, "git_commit")
    worktree_text = _optional_non_empty(worktree_state, "worktree_state")
    if git_text is None and worktree_text is None:
        raise ValueError("git_commit or worktree_state is required")
    caveat_values = _tuple_of_str(caveats, "caveats", require_non_empty=True)
    if not set(_DEFAULT_CAVEATS) <= set(caveat_values):
        caveat_values = _dedupe((*_DEFAULT_CAVEATS, *caveat_values))
    weights = _normalised_weights(resolved_samples)
    q_values = tuple(sample.q_value for sample in resolved_samples)
    f_values = tuple(sample.f_value for sample in resolved_samples)
    g_values = tuple(sample.g_f_value for sample in resolved_samples)
    x_values = tuple(sample.x_c_value for sample in resolved_samples)
    source_values = {
        PiSource.Q: q_values,
        PiSource.F: f_values,
        PiSource.G_F: g_values,
    }[source]
    pi_fractions = tuple(
        math.fsum(
            weight
            for value, weight in zip(source_values, weights, strict=True)
            if value > threshold
        )
        for threshold in thresholds
    )
    transfer_source, transfer_spec_id, transfer_metadata = _combined_transfer(
        resolved_samples
    )
    blocker_reasons = list(prerequisites.blocked_reasons)
    ready = not blocker_reasons
    status = "posterior_pushforward_ready" if ready else "blocked_prerequisite_status"
    effective_sample_size = 1.0 / math.fsum(weight * weight for weight in weights)
    summary_payload: dict[str, object] = {
        "effective_sample_size": effective_sample_size,
        "posterior_weight_sum": math.fsum(
            sample.posterior_weight for sample in resolved_samples
        ),
        "x_C": _weighted_summary(x_values, weights),
        "Q": _weighted_summary(q_values, weights),
        "F": _weighted_summary(f_values, weights),
        "G_F": _weighted_summary(g_values, weights),
    }
    pi_payload = {
        "score_kind": "exceedance_curve",
        "source": source.value,
        "threshold_policy": "predeclared_curve",
        "thresholds": list(thresholds),
        "exceedance_rule": "sample_value > threshold",
        "exceedance_fractions": list(pi_fractions),
        "measure_kind": "htt_posterior_pushforward_distribution",
        "truth_probability": "not_claimed",
    }
    report_hash = _stable_hash(
        {
            "schema_version": SCHEMA_VERSION,
            "samples": [sample.as_payload() for sample in resolved_samples],
            "prerequisites": prerequisites.as_payload(),
            "pi_source": source.value,
            "pi_thresholds": thresholds,
            "config_hash": config_hash_text,
            "input_hashes": input_hash_values,
        }
    )
    input_refs = _dedupe(
        (
            *input_hash_values,
            *[
                hash_value
                for sample in resolved_samples
                for hash_value in sample.input_hashes
            ],
            prerequisites.local_global_report_hash,
            prerequisites.inference_adequacy_report_hash,
            report_hash,
        )
    )
    manifest = ArtifactManifest(
        artifact_id=artifact_id_text,
        artifact_path=artifact_path_text,
        owner=Owner.HTT,
        implementation_scope=ImplementationScope.HTT,
        claim_tier=ClaimTier.CONDITIONAL if ready else ClaimTier.BLOCKED,
        production_status=(
            "diagnostic_only" if ready else "blocked_provenance_mismatch"
        ),
        created_by=_CREATED_BY,
        git_commit=git_text,
        config_hash=_stable_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "config_hash": config_hash_text,
                "pi_source": source.value,
                "pi_thresholds": thresholds,
                "transfer_source": transfer_source,
            }
        ),
        input_hashes=list(input_refs),
        code_version=str(git_text or worktree_text),
        schema_version=SCHEMA_VERSION,
        caveats=list(caveat_values),
        required_gates=[
            "htt_posterior_samples",
            "local_global_mixture_ready",
            "inference_adequacy_ready",
            "matched_null_ready",
            "prior_ppc_loocv_ready",
            "transfer_provenance_attached",
            "mio_inputs_rejected",
        ],
        passed_gates=[
            "htt_posterior_samples",
            "transfer_provenance_attached",
            "mio_inputs_rejected",
            *_passed_prerequisite_gates(prerequisites),
        ],
        failed_gates=list(blocker_reasons),
        statistics_definitions={
            "surface": "posterior_pushforward",
            "pushforward_status": status,
            "posterior_sample_count": len(resolved_samples),
            "effective_sample_size": effective_sample_size,
            "pi_source": source.value,
            "transfer_source": transfer_source,
            "transfer_spec_id": transfer_spec_id,
            "sky_support_status": _uniform_or_mixed(
                [sample.sky_support_status for sample in resolved_samples]
            ),
            "null_mock_status": _uniform_or_mixed(
                [sample.null_mock_status for sample in resolved_samples]
            ),
            "covariance_status": _uniform_or_mixed(
                [sample.covariance_status for sample in resolved_samples]
            ),
        },
    )
    return PosteriorPushforwardReport(
        manifest=manifest,
        samples=resolved_samples,
        prerequisites=prerequisites,
        pi_source=source,
        pi_thresholds=thresholds,
        summaries=summary_payload,
        pi_payload=pi_payload,
        pushforward_status=status,
        blocked_reasons=_dedupe(blocker_reasons),
        report_hash=report_hash,
        generating_command=generating_command_text,
        worktree_state=worktree_text,
        git_commit=git_text,
        transfer_source=transfer_source,
        transfer_spec_id=transfer_spec_id,
        transfer_metadata=transfer_metadata,
        caveats=caveat_values,
    )


__all__ = [
    "PiSource",
    "PosteriorPushforwardPrerequisites",
    "PosteriorPushforwardReport",
    "PosteriorPushforwardSample",
    "build_posterior_pushforward_report",
    "reject_mio_pushforward_inputs",
]
