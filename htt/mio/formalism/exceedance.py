"""MIO Pi exceedance-curve contract with explicit threshold policy."""
from __future__ import annotations

import hashlib
import json
import math
from bisect import bisect_right
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from common.enum_compat import StrEnum
from common.transfer_registry import validate_transfer_dependent_result

from .budget_spec import BudgetUse
from .filling_fraction import CertifiedFillingFraction
from .normalized_score import NormalizedScore

DEFAULT_PI_CAVEAT = (
    "Pi is a MIO diagnostic exceedance curve over recorded diagnostic samples "
    "and explicit threshold policy metadata; it is not HTT inference, model "
    "selection, solver validation, or classification."
)
RAW_PI_CALIBRATION_STATUS = "raw_exceedance_only_uncalibrated_no_p_value"


class ThresholdPolicy(StrEnum):
    """Threshold-selection policy for Pi exceedance diagnostics."""

    CURVE_ONLY = "curve_only"
    PRE_REGISTERED = "pre_registered"


class MeasureKind(StrEnum):
    """Explicit empirical measure behind a Pi exceedance curve."""

    SAMPLE_DISTRIBUTION = "sample_distribution"
    BOOTSTRAP_MOCK_DISTRIBUTION = "bootstrap_mock_distribution"
    NULL_ENSEMBLE = "null_ensemble"
    CROSS_CHECK_PUSHFORWARD = "cross_check_pushforward"


_ALLOWED_SOURCE_LABELS = {"Q", "F"}
_FORBIDDEN_PI_METADATA_TERMS = (
    "p-value",
    "p value",
    "pvalue",
    "significance",
    "probability",
    "probability_anisotropy_true",
    "anisotropy is true",
    "truth probability",
    "posterior",
    "posterior odds",
    "evidence",
    "likelihood",
    "bayes factor",
    "model weight",
    "htt evidence",
    "mio posterior",
    "truth certificate",
    "certifies truth",
    "model-independent proof",
    "family_id",
    "family identification",
    "family identified",
    "family classification",
    "geometry",
    "class label",
    "class-label",
    "solver result",
    "native solver result",
    "external transfer " + "validated as " + "native",
    "validated as native",
    "native_validated",
    "combined mio" + "+htt score",
)
PI_DISPLAY_BLOCKED_USE_CODES = (
    "p_value_claim",
    "truth_probability",
    "htt_inference_consumption",
    "model_selection",
    "solver_validation",
    "scalar_classification",
)
_CURVE_ONLY_SELECTED_KEYS = {
    "pi_value",
    "selected_exceedance_fraction",
    "selected_threshold",
    "threshold_value",
    "truth_probability",
}
_POST_HOC_THRESHOLD_TERMS = (
    "post hoc",
    "post-hoc",
    "after diagnostic",
    "after looking",
    "after scan",
    "choose after",
    "chosen after",
    "data dependent",
    "data-dependent",
)
_EXTERNAL_TRANSFER_SOURCE_VALUES = {
    "AniCLASS_external",
    "external_transfer",
    "empirical_proxy",
}
_FORBIDDEN_SOURCE_KIND_TERMS = (
    "htt_posterior_pushforward",
    "htt posterior pushforward",
    "posterior_pushforward_distribution",
    "posterior pushforward distribution",
)


def _non_empty(value: object, name: str) -> str:
    if value is None:
        raise ValueError(f"{name} must be non-empty")
    text = str(value).strip()
    if not text:
        raise ValueError(f"{name} must be non-empty")
    return text


def _optional_non_empty(value: object | None, name: str) -> str | None:
    if value is None:
        return None
    return _non_empty(value, name)


def _tuple_of_str(
    values: Sequence[object],
    name: str,
    *,
    require_non_empty: bool = False,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{name} must be a sequence of strings")
    result = tuple(str(value).strip() for value in values)
    if require_non_empty and not result:
        raise ValueError(f"{name} must contain at least one entry")
    if any(not value for value in result):
        raise ValueError(f"{name} must contain only non-empty strings")
    return result


def _finite_nonnegative(value: object, name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be finite nonnegative") from exc
    if not math.isfinite(number) or number < 0.0:
        raise ValueError(f"{name} must be finite nonnegative")
    return number


def _positive_int(value: object, name: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a positive integer")
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a positive integer") from exc
    if number < 1 or number != value:
        raise ValueError(f"{name} must be a positive integer")
    return number


def _canonical_policy(policy: object) -> ThresholdPolicy:
    try:
        return ThresholdPolicy(str(policy))
    except ValueError as exc:
        allowed = ", ".join(item.value for item in ThresholdPolicy)
        raise ValueError(f"threshold_policy must be one of: {allowed}") from exc


def _canonical_measure_kind(kind: object) -> MeasureKind:
    if kind is None:
        raise ValueError("measure_kind must be explicit")
    try:
        return MeasureKind(str(kind))
    except ValueError as exc:
        allowed = ", ".join(item.value for item in MeasureKind)
        raise ValueError(f"measure_kind must be one of: {allowed}") from exc


def _canonical_samples(values: Sequence[object]) -> tuple[float, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("sample_values must be a non-string sequence")
    result = tuple(
        _finite_nonnegative(value, "sample_values") for value in values
    )
    if not result:
        raise ValueError("sample_values must contain at least one value")
    return result


def _canonical_thresholds(
    thresholds: Sequence[object] | None,
    sample_values: tuple[float, ...],
) -> tuple[float, ...]:
    if thresholds is None:
        raw_values: Sequence[object] = sample_values
    else:
        if isinstance(thresholds, (str, bytes)):
            raise ValueError("thresholds must be a non-string sequence")
        raw_values = thresholds
    values = tuple(_finite_nonnegative(value, "thresholds") for value in raw_values)
    if not values:
        raise ValueError("thresholds must contain at least one value")
    return tuple(sorted(set(values)))


def _plain_metadata(value: object) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain_metadata(item) for key, item in value.items()}
    if isinstance(value, (str, bytes)):
        return str(value)
    if isinstance(value, Sequence):
        return [_plain_metadata(item) for item in value]
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    raise TypeError(f"metadata value {value!r} is not JSON-compatible")


def _ensure_json_metadata(value: object, name: str) -> None:
    try:
        json.dumps(value, sort_keys=True, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be JSON-compatible") from exc


def _normalise_optional_metadata(
    metadata: Mapping[str, object] | None,
    name: str,
) -> dict[str, Any] | None:
    if metadata is None:
        return None
    if not isinstance(metadata, Mapping):
        raise ValueError(f"{name} entries must be mappings or None")
    try:
        normalised = _plain_metadata(dict(metadata))
    except TypeError as exc:
        raise ValueError(f"{name} must be JSON-compatible") from exc
    if not isinstance(normalised, dict):
        raise ValueError(f"{name} entries must be mappings or None")
    _ensure_json_metadata(normalised, name)
    _scan_reserved_language(normalised, name)
    return normalised


def _validate_measure_statuses(
    *,
    measure_kind: MeasureKind,
    covariance_statuses: tuple[str, ...],
    null_mock_statuses: tuple[str, ...],
) -> None:
    if measure_kind in {
        MeasureKind.BOOTSTRAP_MOCK_DISTRIBUTION,
        MeasureKind.NULL_ENSEMBLE,
    }:
        if all(status == "not_statistical" for status in covariance_statuses):
            raise ValueError(
                f"{measure_kind.value} requires explicit covariance_statuses"
            )
        if all(status == "not_statistical" for status in null_mock_statuses):
            raise ValueError(
                f"{measure_kind.value} requires explicit null_mock_statuses"
            )


def _validate_transfer_provenance(
    *,
    sources: tuple[str, ...],
    spec_ids: tuple[str | None, ...],
    metadata: tuple[dict[str, Any] | None, ...],
) -> None:
    for index, source in enumerate(sources):
        if source == "none":
            if spec_ids[index] is not None or metadata[index] is not None:
                raise ValueError(
                    "transfer_source='none' cannot carry transfer spec or metadata"
                )
            continue
        if source not in _EXTERNAL_TRANSFER_SOURCE_VALUES:
            raise ValueError("Pi cannot claim native transfer provenance")
        if spec_ids[index] is None:
            raise ValueError("external-transfer Pi source requires transfer_spec_id")
        if metadata[index] is None:
            raise ValueError("external-transfer Pi source requires transfer_metadata")
        validate_transfer_dependent_result(metadata[index])
        metadata_source = str(metadata[index].get("transfer_source", ""))
        if metadata_source and metadata_source != source:
            raise ValueError("source_transfer_sources must match transfer metadata")


def _canonical_transfer_provenance(
    sources: Sequence[object],
    spec_ids: Sequence[str | None],
    metadata: Sequence[Mapping[str, object] | None],
) -> tuple[tuple[str, ...], tuple[str | None, ...], tuple[dict[str, Any] | None, ...]]:
    source_values = tuple(str(source) for source in sources)
    if not source_values:
        source_values = ("none",)
    spec_values = tuple(spec_ids)
    if not spec_values:
        spec_values = (None,) * len(source_values)
    metadata_values = tuple(
        _normalise_optional_metadata(item, "source_transfer_metadata")
        for item in metadata
    )
    if not metadata_values:
        metadata_values = (None,) * len(source_values)
    if len(spec_values) != len(source_values):
        raise ValueError("source_transfer_spec_ids length must match sources")
    if len(metadata_values) != len(source_values):
        raise ValueError("source_transfer_metadata length must match sources")
    _validate_transfer_provenance(
        sources=source_values,
        spec_ids=spec_values,
        metadata=metadata_values,
    )
    return source_values, spec_values, metadata_values


def _scan_reserved_language(value: object, name: str) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            _scan_reserved_language(key, name)
            _scan_reserved_language(item, name)
        return
    if isinstance(value, (str, bytes)):
        text = str(value).lower().replace("_", " ")
        for term in _FORBIDDEN_PI_METADATA_TERMS:
            if term.replace("_", " ") in text:
                raise ValueError(
                    f"{name} must not use reserved Pi metadata language: {term}"
                )
        return
    if isinstance(value, Sequence):
        for item in value:
            _scan_reserved_language(item, name)


def _reject_htt_posterior_source_kind(value: str) -> None:
    text = value.lower().replace("_", " ")
    for term in _FORBIDDEN_SOURCE_KIND_TERMS:
        if term.replace("_", " ") in text:
            raise ValueError(
                "MIO Pi source_kind cannot use HTT posterior pushforward "
                "distribution semantics"
            )


def _scan_curve_only_metadata(value: object, name: str) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key).lower()
            if key_text in _CURVE_ONLY_SELECTED_KEYS:
                raise ValueError(
                    f"{name} cannot smuggle selected threshold key {key!r}"
                )
            _scan_curve_only_metadata(item, name)
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for item in value:
            _scan_curve_only_metadata(item, name)


def _canonical_threshold_metadata(
    metadata: Mapping[str, object] | None,
    policy: ThresholdPolicy,
) -> dict[str, Any]:
    if policy is ThresholdPolicy.CURVE_ONLY:
        if metadata is not None:
            raise ValueError("threshold_metadata is only allowed for pre_registered")
        return {}
    if metadata is None:
        raise ValueError("threshold_metadata is required for pre_registered threshold")
    result = _plain_metadata(dict(metadata))
    if not isinstance(result, dict) or not result:
        raise ValueError("threshold_metadata must be a non-empty mapping")
    _scan_reserved_language(result, "threshold_metadata")
    _scan_curve_only_metadata(result, "threshold_metadata")
    _ensure_json_metadata(result, "threshold_metadata")
    registration_status = str(result.get("registration_status", "")).strip()
    if registration_status != "pre_registered":
        raise ValueError(
            "threshold_metadata registration_status must be pre_registered"
        )
    _non_empty(result.get("selection_rule"), "threshold_metadata.selection_rule")
    _non_empty(result.get("registration_hash"), "threshold_metadata.registration_hash")
    selection_rule = str(result["selection_rule"]).lower()
    for term in _POST_HOC_THRESHOLD_TERMS:
        if term in selection_rule:
            raise ValueError("threshold_metadata cannot describe post-hoc selection")
    return result


def _derive_config_hash(
    *,
    sample_values: tuple[float, ...],
    thresholds: tuple[float, ...],
    source_score_label: str,
    source_kind: str,
    measure_kind: MeasureKind,
    threshold_policy: ThresholdPolicy,
    selected_threshold: float | None,
    look_elsewhere_trials: int,
    source_config_hashes: tuple[str, ...],
) -> str:
    payload = {
        "sample_values": sample_values,
        "selected_threshold": selected_threshold,
        "source_config_hashes": source_config_hashes,
        "source_kind": source_kind,
        "source_score_label": source_score_label,
        "measure_kind": measure_kind.value,
        "threshold_policy": threshold_policy.value,
        "thresholds": thresholds,
        "look_elsewhere_trials": look_elsewhere_trials,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return hashlib.sha256(encoded).hexdigest()


def _exceedance_counts(
    sample_values: tuple[float, ...],
    thresholds: tuple[float, ...],
) -> tuple[int, ...]:
    sorted_samples = sorted(sample_values)
    sample_count = len(sorted_samples)
    return tuple(sample_count - bisect_right(sorted_samples, threshold) for threshold in thresholds)


def _uniform_or_mixed(values: Sequence[str]) -> str:
    if not values:
        return "not_applicable"
    unique = set(values)
    if len(unique) == 1:
        return next(iter(unique))
    return "mixed"


def _combined_transfer_source(values: Sequence[str]) -> str:
    sources = [value for value in values if value != "none"]
    if not sources:
        return "none"
    if len(set(sources)) != 1:
        raise ValueError("transfer_source mismatch across Pi samples")
    return sources[0]


def _require_exceedance_budget_use(budget: object, name: str) -> None:
    admissible_uses = getattr(budget, "admissible_uses", ())
    if BudgetUse.EXCEEDANCE_THRESHOLD not in admissible_uses:
        raise ValueError(f"{name} requires BudgetUse.EXCEEDANCE_THRESHOLD")


@dataclass(frozen=True)
class ExceedanceCurve:
    """MIO diagnostic ``Pi`` as an empirical exceedance-fraction curve."""

    sample_values: tuple[float, ...]
    source_score_label: str
    input_hashes: tuple[str, ...]
    generating_command: str = ""
    thresholds: tuple[float, ...] | None = None
    threshold_policy: ThresholdPolicy | str = ThresholdPolicy.CURVE_ONLY
    threshold_metadata: Mapping[str, object] | None = None
    selected_threshold: float | None = None
    look_elsewhere_trials: int = 1
    source_kind: str = "diagnostic_samples"
    measure_kind: MeasureKind | str | None = None
    source_config_hashes: tuple[str, ...] = ()
    source_metadata: tuple[Mapping[str, object], ...] = ()
    source_transfer_sources: tuple[str, ...] = ()
    source_transfer_spec_ids: tuple[str | None, ...] = ()
    source_transfer_metadata: tuple[Mapping[str, object] | None, ...] = ()
    sky_support_statuses: tuple[str, ...] = ("not_directional",)
    covariance_statuses: tuple[str, ...] = ("not_statistical",)
    null_mock_statuses: tuple[str, ...] = ("not_statistical",)
    git_commit: str | None = None
    worktree_state: str | None = None
    config_hash: str | None = None
    artifact_metadata: Mapping[str, object] | None = None
    caveats: tuple[str, ...] = field(default_factory=lambda: (DEFAULT_PI_CAVEAT,))
    score_label: str = "Pi"
    claim_tier: str = "diagnostic_only"
    owner: str = "MIO"
    implementation_scope: str = "mio"

    def __post_init__(self) -> None:
        source_score_label = _non_empty(
            self.source_score_label,
            "source_score_label",
        )
        if source_score_label not in _ALLOWED_SOURCE_LABELS:
            allowed = ", ".join(sorted(_ALLOWED_SOURCE_LABELS))
            raise ValueError(f"source_score_label must be one of: {allowed}")
        source_kind = _non_empty(self.source_kind, "source_kind")
        _reject_htt_posterior_source_kind(source_kind)
        _scan_reserved_language(source_kind, "source_kind")
        measure_kind = _canonical_measure_kind(self.measure_kind)
        score_label = _non_empty(self.score_label, "score_label")
        if score_label != "Pi":
            raise ValueError("score_label must be 'Pi'")
        sample_values = _canonical_samples(self.sample_values)
        thresholds = _canonical_thresholds(self.thresholds, sample_values)
        threshold_policy = _canonical_policy(self.threshold_policy)
        selected_threshold = (
            None
            if self.selected_threshold is None
            else _finite_nonnegative(self.selected_threshold, "selected_threshold")
        )
        look_elsewhere_trials = _positive_int(
            self.look_elsewhere_trials,
            "look_elsewhere_trials",
        )
        if threshold_policy is ThresholdPolicy.CURVE_ONLY:
            if selected_threshold is not None:
                raise ValueError(
                    "selected_threshold requires pre_registered threshold policy"
                )
        else:
            if selected_threshold is None:
                raise ValueError(
                    "selected_threshold is required for pre_registered threshold"
                )
            if selected_threshold not in thresholds:
                raise ValueError("selected_threshold must appear in thresholds")
        threshold_metadata = _canonical_threshold_metadata(
            self.threshold_metadata,
            threshold_policy,
        )

        generating_command = _non_empty(
            self.generating_command,
            "generating_command",
        )
        git_commit = _optional_non_empty(self.git_commit, "git_commit")
        worktree_state = _optional_non_empty(self.worktree_state, "worktree_state")
        if git_commit is None and worktree_state is None:
            raise ValueError("Pi payload requires git_commit or worktree_state")
        input_hashes = _tuple_of_str(
            self.input_hashes,
            "input_hashes",
            require_non_empty=True,
        )
        source_config_hashes = _tuple_of_str(
            self.source_config_hashes,
            "source_config_hashes",
        )
        source_metadata = tuple(
            _normalise_optional_metadata(metadata, "source_metadata")
            for metadata in self.source_metadata
        )
        if any(metadata is None for metadata in source_metadata):
            raise ValueError("source_metadata entries must be mappings")
        source_metadata = tuple(
            metadata for metadata in source_metadata if metadata is not None
        )
        if threshold_policy is ThresholdPolicy.CURVE_ONLY:
            _scan_curve_only_metadata(source_metadata, "source_metadata")
        (
            source_transfer_sources,
            source_transfer_spec_ids,
            source_transfer_metadata,
        ) = _canonical_transfer_provenance(
            self.source_transfer_sources,
            self.source_transfer_spec_ids,
            self.source_transfer_metadata,
        )
        sky_support_statuses = _tuple_of_str(
            self.sky_support_statuses,
            "sky_support_statuses",
            require_non_empty=True,
        )
        covariance_statuses = _tuple_of_str(
            self.covariance_statuses,
            "covariance_statuses",
            require_non_empty=True,
        )
        null_mock_statuses = _tuple_of_str(
            self.null_mock_statuses,
            "null_mock_statuses",
            require_non_empty=True,
        )
        _validate_measure_statuses(
            measure_kind=measure_kind,
            covariance_statuses=covariance_statuses,
            null_mock_statuses=null_mock_statuses,
        )

        artifact_metadata = (
            {}
            if self.artifact_metadata is None
            else _plain_metadata(dict(self.artifact_metadata))
        )
        if not isinstance(artifact_metadata, dict):
            raise ValueError("artifact_metadata must be a mapping")
        _scan_reserved_language(artifact_metadata, "artifact_metadata")
        if threshold_policy is ThresholdPolicy.CURVE_ONLY:
            _scan_curve_only_metadata(artifact_metadata, "artifact_metadata")
            _scan_curve_only_metadata(
                source_transfer_metadata,
                "source_transfer_metadata",
            )
        _ensure_json_metadata(artifact_metadata, "artifact_metadata")
        caveats = tuple(dict.fromkeys(_tuple_of_str(self.caveats, "caveats")))
        if DEFAULT_PI_CAVEAT not in caveats:
            caveats = (DEFAULT_PI_CAVEAT, *caveats)
        _scan_reserved_language(caveats, "caveats")
        if self.owner != "MIO":
            raise ValueError("ExceedanceCurve owner must be 'MIO'")
        if self.claim_tier != "diagnostic_only":
            raise ValueError("ExceedanceCurve claim_tier must be 'diagnostic_only'")
        if self.implementation_scope != "mio":
            raise ValueError("ExceedanceCurve implementation_scope must be 'mio'")

        config_hash = (
            _non_empty(self.config_hash, "config_hash")
            if self.config_hash is not None
            else _derive_config_hash(
                sample_values=sample_values,
                thresholds=thresholds,
                source_score_label=source_score_label,
                source_kind=source_kind,
                measure_kind=measure_kind,
                threshold_policy=threshold_policy,
                selected_threshold=selected_threshold,
                look_elsewhere_trials=look_elsewhere_trials,
                source_config_hashes=source_config_hashes,
            )
        )
        _combined_transfer_source(source_transfer_sources)

        object.__setattr__(self, "sample_values", sample_values)
        object.__setattr__(self, "thresholds", thresholds)
        object.__setattr__(self, "threshold_policy", threshold_policy)
        object.__setattr__(self, "threshold_metadata", threshold_metadata)
        object.__setattr__(self, "selected_threshold", selected_threshold)
        object.__setattr__(self, "look_elsewhere_trials", look_elsewhere_trials)
        object.__setattr__(self, "source_score_label", source_score_label)
        object.__setattr__(self, "source_kind", source_kind)
        object.__setattr__(self, "measure_kind", measure_kind)
        object.__setattr__(self, "input_hashes", input_hashes)
        object.__setattr__(self, "generating_command", generating_command)
        object.__setattr__(self, "git_commit", git_commit)
        object.__setattr__(self, "worktree_state", worktree_state)
        object.__setattr__(self, "source_config_hashes", source_config_hashes)
        object.__setattr__(self, "source_metadata", source_metadata)
        object.__setattr__(self, "source_transfer_sources", source_transfer_sources)
        object.__setattr__(self, "source_transfer_spec_ids", source_transfer_spec_ids)
        object.__setattr__(self, "source_transfer_metadata", source_transfer_metadata)
        object.__setattr__(self, "sky_support_statuses", sky_support_statuses)
        object.__setattr__(self, "covariance_statuses", covariance_statuses)
        object.__setattr__(self, "null_mock_statuses", null_mock_statuses)
        object.__setattr__(self, "artifact_metadata", artifact_metadata)
        object.__setattr__(self, "caveats", caveats)
        object.__setattr__(self, "config_hash", config_hash)
        object.__setattr__(self, "score_label", score_label)

    @property
    def sample_count(self) -> int:
        return len(self.sample_values)

    @property
    def exceedance_counts(self) -> tuple[int, ...]:
        return _exceedance_counts(self.sample_values, self.thresholds)

    @property
    def exceedance_fractions(self) -> tuple[float, ...]:
        return tuple(count / self.sample_count for count in self.exceedance_counts)

    @property
    def selected_exceedance_fraction(self) -> float | None:
        if self.selected_threshold is None:
            return None
        index = self.thresholds.index(self.selected_threshold)
        return self.exceedance_fractions[index]

    @property
    def transfer_source(self) -> str:
        return _combined_transfer_source(self.source_transfer_sources)

    @property
    def sky_support_status(self) -> str:
        return _uniform_or_mixed(self.sky_support_statuses)

    @property
    def covariance_status(self) -> str:
        return _uniform_or_mixed(self.covariance_statuses)

    @property
    def null_mock_status(self) -> str:
        return _uniform_or_mixed(self.null_mock_statuses)

    @property
    def threshold_registration_status(self) -> str:
        return (
            "curve_only_no_selected_threshold"
            if self.threshold_policy is ThresholdPolicy.CURVE_ONLY
            else "pre_registered"
        )

    @property
    def display_metadata(self) -> dict[str, object]:
        registration_hash = None
        if self.threshold_policy is ThresholdPolicy.PRE_REGISTERED:
            registration_hash = self.threshold_metadata.get("registration_hash")
        return {
            "requires_measure_kind": True,
            "source_score_label": self.source_score_label,
            "source_kind": self.source_kind,
            "measure_kind": self.measure_kind.value,
            "threshold_policy": self.threshold_policy.value,
            "threshold_registration_status": self.threshold_registration_status,
            "registration_hash": registration_hash,
            "threshold_grid": list(self.thresholds),
            "selected_threshold": self.selected_threshold,
            "look_elsewhere_trials": self.look_elsewhere_trials,
            "exceedance_rule": "sample_value > threshold",
            "calibration_status": RAW_PI_CALIBRATION_STATUS,
            "covariance_status": self.covariance_status,
            "null_mock_status": self.null_mock_status,
            "sky_support_status": self.sky_support_status,
            "p_value_interpretation_status": "blocked_exceedance_not_p_value",
            "blocked_use_codes": list(PI_DISPLAY_BLOCKED_USE_CODES),
        }

    def as_payload(self) -> dict[str, object]:
        payload = {
            "owner": self.owner,
            "implementation_scope": self.implementation_scope,
            "claim_tier": self.claim_tier,
            "score_label": self.score_label,
            "score_kind": "exceedance_curve",
            "target": self.source_score_label,
            "source_score_label": self.source_score_label,
            "source_kind": self.source_kind,
            "measure_kind": self.measure_kind.value,
            "sample_values": list(self.sample_values),
            "sample_count": self.sample_count,
            "valid_sample_count": self.sample_count,
            "invalid_sample_count": 0,
            "invalid_sample_reasons": [],
            "threshold_policy": self.threshold_policy.value,
            "threshold_values": list(self.thresholds),
            "threshold_grid": list(self.thresholds),
            "threshold_metadata": dict(self.threshold_metadata),
            "threshold_registration_status": self.threshold_registration_status,
            "threshold_labels": [f"threshold:{index}" for index, _ in enumerate(self.thresholds)],
            "selected_threshold": self.selected_threshold,
            "selected_exceedance_fraction": self.selected_exceedance_fraction,
            "look_elsewhere_trials": self.look_elsewhere_trials,
            "exceedance_rule": "sample_value > threshold",
            "calibration_status": RAW_PI_CALIBRATION_STATUS,
            "exceedance_counts": list(self.exceedance_counts),
            "exceedance_fractions": list(self.exceedance_fractions),
            "pi_grid": list(self.exceedance_fractions),
            "generating_command": self.generating_command,
            "git_commit": self.git_commit,
            "worktree_state": self.worktree_state,
            "transfer_source": self.transfer_source,
            "source_transfer_sources": list(self.source_transfer_sources),
            "source_transfer_spec_ids": list(self.source_transfer_spec_ids),
            "source_transfer_metadata": list(self.source_transfer_metadata),
            "sky_support_status": self.sky_support_status,
            "sky_support_statuses": list(self.sky_support_statuses),
            "covariance_status": self.covariance_status,
            "covariance_statuses": list(self.covariance_statuses),
            "null_mock_status": self.null_mock_status,
            "null_mock_statuses": list(self.null_mock_statuses),
            "config_hash": self.config_hash,
            "source_config_hashes": list(self.source_config_hashes),
            "source_metadata": [dict(metadata) for metadata in self.source_metadata],
            "input_hashes": list(self.input_hashes),
            "display_metadata": self.display_metadata,
            "artifact_metadata": dict(self.artifact_metadata),
            "caveats": list(self.caveats),
        }
        return payload


def build_exceedance_curve(
    sample_values: Sequence[object],
    *,
    source_score_label: str,
    input_hashes: Sequence[object],
    generating_command: str,
    thresholds: Sequence[object] | None = None,
    threshold_policy: ThresholdPolicy | str = ThresholdPolicy.CURVE_ONLY,
    threshold_metadata: Mapping[str, object] | None = None,
    selected_threshold: float | None = None,
    look_elsewhere_trials: int = 1,
    measure_kind: MeasureKind | str,
    source_kind: str = "diagnostic_samples",
    source_config_hashes: Sequence[object] = (),
    source_metadata: Sequence[Mapping[str, object]] = (),
    source_transfer_sources: Sequence[object] = (),
    source_transfer_spec_ids: Sequence[str | None] = (),
    source_transfer_metadata: Sequence[Mapping[str, object] | None] = (),
    sky_support_statuses: Sequence[object] = ("not_directional",),
    covariance_statuses: Sequence[object] = ("not_statistical",),
    null_mock_statuses: Sequence[object] = ("not_statistical",),
    git_commit: str | None = None,
    worktree_state: str | None = None,
    config_hash: str | None = None,
    artifact_metadata: Mapping[str, object] | None = None,
    caveats: Sequence[object] | None = None,
) -> ExceedanceCurve:
    """Build a validated MIO diagnostic Pi exceedance curve."""

    return ExceedanceCurve(
        sample_values=tuple(float(value) for value in sample_values),
        source_score_label=source_score_label,
        input_hashes=_tuple_of_str(input_hashes, "input_hashes", require_non_empty=True),
        generating_command=generating_command,
        thresholds=None if thresholds is None else tuple(float(value) for value in thresholds),
        threshold_policy=threshold_policy,
        threshold_metadata=threshold_metadata,
        selected_threshold=selected_threshold,
        look_elsewhere_trials=look_elsewhere_trials,
        source_kind=source_kind,
        measure_kind=measure_kind,
        source_config_hashes=_tuple_of_str(
            source_config_hashes,
            "source_config_hashes",
        ),
        source_metadata=tuple(source_metadata),
        source_transfer_sources=tuple(str(value) for value in source_transfer_sources),
        source_transfer_spec_ids=tuple(source_transfer_spec_ids),
        source_transfer_metadata=tuple(source_transfer_metadata),
        sky_support_statuses=_tuple_of_str(
            sky_support_statuses,
            "sky_support_statuses",
            require_non_empty=True,
        ),
        covariance_statuses=_tuple_of_str(
            covariance_statuses,
            "covariance_statuses",
            require_non_empty=True,
        ),
        null_mock_statuses=_tuple_of_str(
            null_mock_statuses,
            "null_mock_statuses",
            require_non_empty=True,
        ),
        git_commit=git_commit,
        worktree_state=worktree_state,
        config_hash=config_hash,
        artifact_metadata=artifact_metadata,
        caveats=(DEFAULT_PI_CAVEAT,) if caveats is None else tuple(caveats),
    )


def build_exceedance_curve_from_normalized_scores(
    scores: Sequence[NormalizedScore],
    *,
    thresholds: Sequence[object] | None = None,
    threshold_policy: ThresholdPolicy | str = ThresholdPolicy.CURVE_ONLY,
    threshold_metadata: Mapping[str, object] | None = None,
    selected_threshold: float | None = None,
    look_elsewhere_trials: int = 1,
    measure_kind: MeasureKind | str,
    generating_command: str,
    git_commit: str | None = None,
    worktree_state: str | None = None,
    artifact_metadata: Mapping[str, object] | None = None,
    caveats: Sequence[object] | None = None,
) -> ExceedanceCurve:
    """Build Pi over Q samples while preserving Q and denominator provenance."""

    if isinstance(scores, (str, bytes)):
        raise ValueError("scores must be a sequence of NormalizedScore samples")
    score_tuple = tuple(scores)
    if not score_tuple:
        raise ValueError("scores must contain at least one NormalizedScore sample")
    if any(not isinstance(score, NormalizedScore) for score in score_tuple):
        raise TypeError("scores must contain NormalizedScore samples")
    for index, score in enumerate(score_tuple):
        _require_exceedance_budget_use(score.budget_spec, f"Q sample {index}")
        if score.numerator_policy.value == "signed":
            raise ValueError("Pi over Q requires non-signed Q numerator policy")
    input_hashes: list[str] = []
    for score in score_tuple:
        input_hashes.extend(score.input_hashes)
    return build_exceedance_curve(
        [score.q_value for score in score_tuple],
        source_score_label="Q",
        source_kind="normalized_score.q_value",
        input_hashes=tuple(dict.fromkeys(input_hashes)),
        thresholds=thresholds,
        threshold_policy=threshold_policy,
        threshold_metadata=threshold_metadata,
        selected_threshold=selected_threshold,
        look_elsewhere_trials=look_elsewhere_trials,
        measure_kind=measure_kind,
        generating_command=generating_command,
        git_commit=git_commit,
        worktree_state=worktree_state,
        source_config_hashes=[score.config_hash for score in score_tuple],
        source_metadata=[
            {
                "numerator_policy": score.numerator_policy.value,
                "denominator_policy": score.denominator_policy,
                "denominator_use": BudgetUse.EXCEEDANCE_THRESHOLD.value,
                "comparator": score.departure_bundle.comparator,
                "frame": score.departure_bundle.frame,
                "units": score.departure_bundle.units,
            }
            for score in score_tuple
        ],
        source_transfer_sources=[score.transfer_source for score in score_tuple],
        source_transfer_spec_ids=[
            score.departure_bundle.transfer_spec_id
            or score.budget_spec.transfer_spec_id
            for score in score_tuple
        ],
        source_transfer_metadata=[
            score.departure_bundle.transfer_metadata
            or score.budget_spec.transfer_metadata
            for score in score_tuple
        ],
        sky_support_statuses=[
            score.budget_spec.sky_support_status for score in score_tuple
        ],
        covariance_statuses=[
            score.budget_spec.covariance_status for score in score_tuple
        ],
        null_mock_statuses=[
            score.budget_spec.null_mock_status for score in score_tuple
        ],
        artifact_metadata=artifact_metadata,
        caveats=caveats,
    )


def build_exceedance_curve_from_filling_fraction(
    filling_fraction: CertifiedFillingFraction,
    *,
    thresholds: Sequence[object] | None = None,
    threshold_policy: ThresholdPolicy | str = ThresholdPolicy.CURVE_ONLY,
    threshold_metadata: Mapping[str, object] | None = None,
    selected_threshold: float | None = None,
    look_elsewhere_trials: int = 1,
    measure_kind: MeasureKind | str,
    generating_command: str,
    git_commit: str | None = None,
    worktree_state: str | None = None,
    artifact_metadata: Mapping[str, object] | None = None,
    caveats: Sequence[object] | None = None,
) -> ExceedanceCurve:
    """Build Pi over certified F samples without using the F_Bayes summary."""

    if not isinstance(filling_fraction, CertifiedFillingFraction):
        raise TypeError("filling_fraction must be a CertifiedFillingFraction")
    for index, budget in enumerate(filling_fraction.budget_specs):
        _require_exceedance_budget_use(budget, f"F sample {index}")
    filling_payload = filling_fraction.as_payload()
    transfer_pairs: list[tuple[str | None, Mapping[str, object] | None]] = []
    for spec_id, metadata in (
        *zip(
            filling_payload["departure_transfer_spec_ids"],
            filling_payload["departure_transfer_metadata"],
            strict=True,
        ),
        *zip(
            filling_payload["budget_transfer_spec_ids"],
            filling_payload["budget_transfer_metadata"],
            strict=True,
        ),
    ):
        if spec_id is not None or metadata is not None:
            pair = (spec_id, metadata)
            if pair not in transfer_pairs:
                transfer_pairs.append(pair)
    return build_exceedance_curve(
        filling_fraction.f_samples,
        source_score_label="F",
        source_kind="certified_filling_fraction.f_samples",
        input_hashes=filling_fraction.input_hashes,
        thresholds=thresholds,
        threshold_policy=threshold_policy,
        threshold_metadata=threshold_metadata,
        selected_threshold=selected_threshold,
        look_elsewhere_trials=look_elsewhere_trials,
        measure_kind=measure_kind,
        generating_command=generating_command,
        git_commit=git_commit,
        worktree_state=worktree_state,
        source_config_hashes=(filling_fraction.config_hash,),
        source_metadata=(
            {
                "sample_pushforward": "sample_wise",
                "sign_clean_sector": True,
                "denominator_policy": filling_fraction.denominator_policy,
                "denominator_use": BudgetUse.EXCEEDANCE_THRESHOLD.value,
                "comparator": filling_fraction.departure_bundles[0].comparator,
                "frame": filling_fraction.departure_bundles[0].frame,
                "units": filling_fraction.departure_bundles[0].units,
            },
        ),
        source_transfer_sources=(
            () if not transfer_pairs else (filling_fraction.transfer_source,) * len(transfer_pairs)
        ),
        source_transfer_spec_ids=tuple(spec_id for spec_id, _ in transfer_pairs),
        source_transfer_metadata=tuple(metadata for _, metadata in transfer_pairs),
        sky_support_statuses=filling_payload["sky_support_statuses"],
        covariance_statuses=filling_payload["covariance_statuses"],
        null_mock_statuses=filling_payload["null_mock_statuses"],
        artifact_metadata=artifact_metadata,
        caveats=caveats,
    )


__all__ = [
    "DEFAULT_PI_CAVEAT",
    "ExceedanceCurve",
    "MeasureKind",
    "ThresholdPolicy",
    "build_exceedance_curve",
    "build_exceedance_curve_from_filling_fraction",
    "build_exceedance_curve_from_normalized_scores",
]
