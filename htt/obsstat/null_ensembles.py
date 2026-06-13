"""Null ensemble provenance and look-elsewhere metadata for OBSSTAT features.

This module records feature-null calibration metadata.  It does not generate
sky mocks, evaluate HTT likelihoods, create MIO certificates, validate transfer
functions, validate native solver output, or assign geometry/family labels.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import hashlib
import json
import math
import re
from typing import Any

__all__ = [
    "LookElsewhereBookkeeping",
    "NullCalibratedFeature",
    "NullEnsembleSpec",
    "build_null_ensemble_feature_payload",
    "validate_null_feature_payload",
]


_SCHEMA_VERSION = "obsstat.null_ensembles.v1"
_LOOK_ELSEWHERE_SCHEMA_VERSION = "obsstat.look_elsewhere.v1"
_FEATURE_CAVEAT = (
    "null-calibrated OBSSTAT feature metadata only; diagnostic descriptor "
    "with no model-input role"
)
_LOCAL_CAVEAT = (
    "local or tracked-only tail metadata is not a global significance claim"
)
_ALLOWED_NULL_FAMILIES = frozenset(
    {
        "flrw_mask_noise",
        "local_systematic",
        "injected_template",
    }
)
_ALLOWED_LOOK_ELSEWHERE_STATUSES = frozenset(
    {
        "global_corrected",
        "tracked_not_corrected",
        "local_unadjusted_with_trials",
    }
)
_ALLOWED_TAILS = frozenset(
    {
        "upper_tail",
        "lower_tail",
        "two_sided",
        "absolute_tail",
        "max_scan_tail",
    }
)
_FORBIDDEN_TEXT_PARTS = (
    "posterior",
    "likelihood",
    "evidence",
    "bayes",
    "certificate",
    "truth",
    "native solver result",
    "native validation",
    "transfer validated",
    "morphology compatibility",
    "geometry detected",
    "detected geometry",
    "family identified",
    "family identification",
    "family ranking",
)
_DOES_NOT_ESTABLISH = (
    "htt_evidence",
    "mio_certificate",
    "transfer_validation",
    "native_solver_validation",
    "morphology_compatibility",
    "geometry_detection",
    "family_identification",
)


def _non_empty(value: object, name: str) -> str:
    if value is None:
        raise ValueError(f"{name} is required")
    text = str(value).strip()
    if not text:
        raise ValueError(f"{name} is required")
    return text


def _tuple_of_str(values: Sequence[object], name: str) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{name} must be a sequence")
    result = tuple(str(value).strip() for value in values)
    if not result or any(not value for value in result):
        raise ValueError(f"{name} must contain non-empty strings")
    if len(set(result)) != len(result):
        raise ValueError(f"{name} must not contain duplicates")
    return result


def _positive_int(value: object, name: str) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a positive integer") from exc
    if number <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return number


def _json_value(value: object) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (str, bytes)):
        return str(value)
    if isinstance(value, Sequence):
        return [_json_value(item) for item in value]
    if isinstance(value, float):
        if not math.isfinite(value):
            raise TypeError("metadata floats must be finite")
        return value
    if isinstance(value, (int, bool)) or value is None:
        return value
    raise TypeError(f"metadata value {value!r} is not JSON-compatible")


def _json_mapping(value: Mapping[str, object] | None, name: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be a mapping")
    try:
        result = _json_value(value)
    except TypeError as exc:
        raise ValueError(f"{name} must be JSON-compatible") from exc
    if not isinstance(result, dict):
        raise ValueError(f"{name} must be a mapping")
    _reject_overclaim_text(result, name)
    _canonical_json(result)
    return result


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _sha256_payload(value: object) -> str:
    encoded = _canonical_json(value).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _require_hash(value: object, name: str) -> str:
    text = _non_empty(value, name)
    if not text.startswith("sha256:"):
        raise ValueError(f"{name} must start with sha256:")
    return text


def _require_input_hashes(values: Sequence[object], name: str) -> tuple[str, ...]:
    hashes = _tuple_of_str(values, name)
    for value in hashes:
        if not value.startswith("sha256:"):
            raise ValueError(f"{name} entries must start with sha256:")
    return hashes


def _normalise_text(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()


def _reject_overclaim_text(value: object, name: str = "metadata") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            _reject_overclaim_text(key, name)
            if str(key) == "does_not_establish":
                continue
            _reject_overclaim_text(item, name)
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for item in value:
            _reject_overclaim_text(item, name)
        return
    if not isinstance(value, (str, bytes)):
        return
    text = _normalise_text(value)
    for part in _FORBIDDEN_TEXT_PARTS:
        if _normalise_text(part) in text:
            raise ValueError(f"{name} contains forbidden claim language: {part}")


@dataclass(frozen=True)
class NullEnsembleSpec:
    """Declared OBSSTAT null ensemble provenance; no mock generation occurs."""

    null_ensemble_ref: str
    null_family: str
    mock_count: int
    feature_targets: Sequence[str]
    statistic_keys: Sequence[str]
    sky_support_status: str
    mask_status: str
    noise_model_status: str
    covariance_status: str
    null_mock_status: str
    random_seed_policy: str
    config_hash: str
    input_hashes: Sequence[str]
    generating_command: str
    git_commit: str | None = None
    worktree_state: str | None = None
    source_metadata: Mapping[str, object] = field(default_factory=dict)
    transfer_source: str = "none"
    metadata_schema: str = _SCHEMA_VERSION
    caveats: tuple[str, ...] = (_FEATURE_CAVEAT,)

    def __post_init__(self) -> None:
        if self.metadata_schema != _SCHEMA_VERSION:
            raise ValueError("NullEnsembleSpec.metadata_schema is not allowed")
        null_ensemble_ref = _non_empty(
            self.null_ensemble_ref,
            "null_ensemble_ref",
        )
        null_family = _non_empty(self.null_family, "null_family")
        if null_family not in _ALLOWED_NULL_FAMILIES:
            raise ValueError("null_family is not allowed")
        transfer_source = _non_empty(self.transfer_source, "transfer_source")
        if transfer_source != "none":
            raise ValueError("NullEnsembleSpec transfer_source must be none")
        mock_count = _positive_int(self.mock_count, "mock_count")
        feature_targets = _tuple_of_str(self.feature_targets, "feature_targets")
        statistic_keys = _tuple_of_str(self.statistic_keys, "statistic_keys")
        source_metadata = _json_mapping(self.source_metadata, "source_metadata")
        caveats = tuple(str(item) for item in self.caveats)
        if not caveats:
            caveats = (_FEATURE_CAVEAT,)
        _reject_overclaim_text(caveats, "caveats")

        git_commit = None if self.git_commit is None else _non_empty(self.git_commit, "git_commit")
        worktree_state = (
            None
            if self.worktree_state is None
            else _non_empty(self.worktree_state, "worktree_state")
        )
        if git_commit is None and worktree_state is None:
            raise ValueError("NullEnsembleSpec requires git_commit or worktree_state")

        object.__setattr__(self, "null_ensemble_ref", null_ensemble_ref)
        object.__setattr__(self, "null_family", null_family)
        object.__setattr__(self, "mock_count", mock_count)
        object.__setattr__(self, "feature_targets", feature_targets)
        object.__setattr__(self, "statistic_keys", statistic_keys)
        object.__setattr__(
            self,
            "sky_support_status",
            _non_empty(self.sky_support_status, "sky_support_status"),
        )
        object.__setattr__(
            self,
            "mask_status",
            _non_empty(self.mask_status, "mask_status"),
        )
        object.__setattr__(
            self,
            "noise_model_status",
            _non_empty(self.noise_model_status, "noise_model_status"),
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
        object.__setattr__(
            self,
            "random_seed_policy",
            _non_empty(self.random_seed_policy, "random_seed_policy"),
        )
        object.__setattr__(self, "config_hash", _require_hash(self.config_hash, "config_hash"))
        object.__setattr__(self, "input_hashes", _require_input_hashes(self.input_hashes, "input_hashes"))
        object.__setattr__(
            self,
            "generating_command",
            _non_empty(self.generating_command, "generating_command"),
        )
        object.__setattr__(self, "git_commit", git_commit)
        object.__setattr__(self, "worktree_state", worktree_state)
        object.__setattr__(self, "source_metadata", source_metadata)
        object.__setattr__(self, "transfer_source", transfer_source)
        object.__setattr__(self, "caveats", caveats)

    def to_metadata(self) -> dict[str, Any]:
        return {
            "metadata_schema": self.metadata_schema,
            "null_ensemble_ref": self.null_ensemble_ref,
            "null_family": self.null_family,
            "mock_count": self.mock_count,
            "feature_targets": list(self.feature_targets),
            "statistic_keys": list(self.statistic_keys),
            "sky_support_status": self.sky_support_status,
            "mask_status": self.mask_status,
            "noise_model_status": self.noise_model_status,
            "covariance_status": self.covariance_status,
            "null_mock_status": self.null_mock_status,
            "random_seed_policy": self.random_seed_policy,
            "transfer_source": self.transfer_source,
            "config_hash": self.config_hash,
            "input_hashes": list(self.input_hashes),
            "generating_command": self.generating_command,
            "git_commit": self.git_commit,
            "worktree_state": self.worktree_state,
            "source_metadata": dict(self.source_metadata),
            "caveats": list(self.caveats),
        }


@dataclass(frozen=True)
class LookElsewhereBookkeeping:
    """Scan-volume and tail bookkeeping for OBSSTAT null-calibrated features."""

    look_elsewhere_status: str
    trial_count: int
    scan_volume: Mapping[str, object]
    correction_method: str
    pre_registration_status: str
    tail_definitions: Mapping[str, str] = field(default_factory=dict)
    scan_volume_hash: str | None = None
    metadata_schema: str = _LOOK_ELSEWHERE_SCHEMA_VERSION
    caveats: tuple[str, ...] = (_FEATURE_CAVEAT,)

    def __post_init__(self) -> None:
        if self.metadata_schema != _LOOK_ELSEWHERE_SCHEMA_VERSION:
            raise ValueError("LookElsewhereBookkeeping.metadata_schema is not allowed")
        status = _non_empty(self.look_elsewhere_status, "look_elsewhere_status")
        if status not in _ALLOWED_LOOK_ELSEWHERE_STATUSES:
            raise ValueError("look_elsewhere_status is not allowed")
        trial_count = _positive_int(self.trial_count, "trial_count")
        scan_volume = _json_mapping(self.scan_volume, "scan_volume")
        missing = {
            "feature_targets",
            "statistic_keys",
            "trial_count",
            "global_local_status",
        } - set(scan_volume)
        if missing:
            raise ValueError(
                "scan_volume missing required field(s): "
                + ", ".join(sorted(missing))
            )
        if int(scan_volume["trial_count"]) != trial_count:
            raise ValueError("scan_volume trial_count mismatch")
        if str(scan_volume["global_local_status"]) != status:
            raise ValueError("scan_volume global_local_status mismatch")
        statistic_keys = _tuple_of_str(scan_volume["statistic_keys"], "scan_volume.statistic_keys")
        tail_definitions = {
            str(key): str(value).strip()
            for key, value in self.tail_definitions.items()
        }
        if tail_definitions:
            if set(tail_definitions) != set(statistic_keys):
                raise ValueError(
                    "tail_definitions statistic_keys must match scan_volume statistic_keys"
                )
            invalid_tails = sorted(
                value
                for value in tail_definitions.values()
                if value not in _ALLOWED_TAILS
            )
            if invalid_tails:
                raise ValueError(f"tail_definitions contain invalid tails: {invalid_tails}")
        derived_hash = _sha256_payload(scan_volume)
        if self.scan_volume_hash is not None and self.scan_volume_hash != derived_hash:
            raise ValueError("scan_volume_hash must match scan_volume")
        caveats = tuple(str(item) for item in self.caveats)
        _reject_overclaim_text(
            {
                "look_elsewhere_status": status,
                "scan_volume": scan_volume,
                "correction_method": self.correction_method,
                "pre_registration_status": self.pre_registration_status,
                "tail_definitions": tail_definitions,
                "caveats": caveats,
            },
            "look_elsewhere",
        )

        object.__setattr__(self, "look_elsewhere_status", status)
        object.__setattr__(self, "trial_count", trial_count)
        object.__setattr__(self, "scan_volume", scan_volume)
        object.__setattr__(
            self,
            "correction_method",
            _non_empty(self.correction_method, "correction_method"),
        )
        object.__setattr__(
            self,
            "pre_registration_status",
            _non_empty(self.pre_registration_status, "pre_registration_status"),
        )
        object.__setattr__(self, "tail_definitions", tail_definitions)
        object.__setattr__(self, "scan_volume_hash", derived_hash)
        object.__setattr__(self, "caveats", caveats or (_FEATURE_CAVEAT,))

    @property
    def statistic_keys(self) -> tuple[str, ...]:
        return _tuple_of_str(self.scan_volume["statistic_keys"], "scan_volume.statistic_keys")

    @property
    def feature_targets(self) -> tuple[str, ...]:
        return _tuple_of_str(self.scan_volume["feature_targets"], "scan_volume.feature_targets")

    def to_metadata(self) -> dict[str, Any]:
        return {
            "metadata_schema": self.metadata_schema,
            "look_elsewhere_status": self.look_elsewhere_status,
            "trial_count": self.trial_count,
            "scan_volume": dict(self.scan_volume),
            "scan_volume_hash": self.scan_volume_hash,
            "correction_method": self.correction_method,
            "pre_registration_status": self.pre_registration_status,
            "tail_definitions": dict(self.tail_definitions),
            "caveats": list(self.caveats),
        }


@dataclass(frozen=True)
class NullCalibratedFeature:
    """A feature p-value payload tied to a declared OBSSTAT null ensemble."""

    null_ensemble: NullEnsembleSpec
    look_elsewhere: LookElsewhereBookkeeping
    p_values: Mapping[str, float]
    observed_feature_ref: str | None = None
    caveats: tuple[str, ...] = (_FEATURE_CAVEAT,)

    def __post_init__(self) -> None:
        if not isinstance(self.null_ensemble, NullEnsembleSpec):
            raise TypeError("NullCalibratedFeature requires NullEnsembleSpec")
        if not isinstance(self.look_elsewhere, LookElsewhereBookkeeping):
            raise TypeError(
                "NullCalibratedFeature requires LookElsewhereBookkeeping"
            )
        p_values = {str(key): float(value) for key, value in self.p_values.items()}
        if not p_values:
            raise ValueError("p_values must be non-empty")
        for key, value in p_values.items():
            if not math.isfinite(value) or not (0.0 <= value <= 1.0):
                raise ValueError(f"p_values[{key!r}] must be in [0, 1]")
        available = set(self.null_ensemble.statistic_keys)
        missing = sorted(set(p_values) - available)
        if missing:
            raise ValueError(f"p_values are not available in statistic_keys: {missing}")
        look_missing = sorted(set(p_values) - set(self.look_elsewhere.statistic_keys))
        if look_missing:
            raise ValueError(
                f"p_values are not available in look_elsewhere statistic_keys: {look_missing}"
            )
        tail_missing = sorted(
            key for key in p_values if not self.look_elsewhere.tail_definitions.get(key)
        )
        if tail_missing:
            raise ValueError(
                "tail_definitions must cover every p-value key: "
                + ", ".join(tail_missing)
            )
        target_missing = sorted(
            set(self.null_ensemble.feature_targets) - set(self.look_elsewhere.feature_targets)
        )
        if target_missing:
            raise ValueError(f"feature_targets missing from scan_volume: {target_missing}")
        caveats = tuple(str(item) for item in self.caveats)
        if self.look_elsewhere.look_elsewhere_status != "global_corrected":
            caveats = tuple(dict.fromkeys((*caveats, _LOCAL_CAVEAT)))
        _reject_overclaim_text(
            {
                "p_values": p_values,
                "observed_feature_ref": self.observed_feature_ref,
                "caveats": caveats,
            },
            "null_calibrated_feature",
        )
        object.__setattr__(self, "p_values", p_values)
        object.__setattr__(self, "caveats", caveats or (_FEATURE_CAVEAT,))

    def to_payload(self) -> dict[str, Any]:
        null_metadata = self.null_ensemble.to_metadata()
        look_metadata = self.look_elsewhere.to_metadata()
        payload: dict[str, Any] = {
            "metadata_schema": _SCHEMA_VERSION,
            "owner": "OBSSTAT",
            "implementation_scope": "obsstat",
            "claim_tier": "diagnostic_only",
            "production_status": "diagnostic_only",
            "statistic_role": "null_calibrated_feature",
            "model_role": "not_model_input",
            "transfer_source": self.null_ensemble.transfer_source,
            "null_ensemble_ref": self.null_ensemble.null_ensemble_ref,
            "null_family": self.null_ensemble.null_family,
            "mock_count": self.null_ensemble.mock_count,
            "feature_targets": list(self.null_ensemble.feature_targets),
            "statistic_keys": list(self.null_ensemble.statistic_keys),
            "p_values": dict(self.p_values),
            "tail_definitions": dict(self.look_elsewhere.tail_definitions),
            "look_elsewhere_status": self.look_elsewhere.look_elsewhere_status,
            "look_elsewhere_trials": self.look_elsewhere.trial_count,
            "scan_volume": dict(self.look_elsewhere.scan_volume),
            "scan_volume_hash": self.look_elsewhere.scan_volume_hash,
            "global_local_status": self.look_elsewhere.look_elsewhere_status,
            "covariance_status": self.null_ensemble.covariance_status,
            "sky_support_status": self.null_ensemble.sky_support_status,
            "mask_status": self.null_ensemble.mask_status,
            "noise_model_status": self.null_ensemble.noise_model_status,
            "null_mock_status": self.null_ensemble.null_mock_status,
            "random_seed_policy": self.null_ensemble.random_seed_policy,
            "config_hash": self.null_ensemble.config_hash,
            "input_hashes": list(self.null_ensemble.input_hashes),
            "generating_command": self.null_ensemble.generating_command,
            "git_commit": self.null_ensemble.git_commit,
            "worktree_state": self.null_ensemble.worktree_state,
            "observed_feature_ref": self.observed_feature_ref,
            "null_ensemble": null_metadata,
            "look_elsewhere": look_metadata,
            "does_not_establish": list(_DOES_NOT_ESTABLISH),
            "caveats": list(self.caveats),
        }
        _reject_overclaim_text(payload, "null_feature_payload")
        return payload


def build_null_ensemble_feature_payload(
    *,
    null_ensemble: NullEnsembleSpec,
    look_elsewhere: LookElsewhereBookkeeping,
    p_values: Mapping[str, float],
    observed_feature_ref: str | None = None,
    caveats: Sequence[str] = (_FEATURE_CAVEAT,),
) -> dict[str, Any]:
    """Build an OBSSTAT null-calibrated feature payload."""

    return NullCalibratedFeature(
        null_ensemble=null_ensemble,
        look_elsewhere=look_elsewhere,
        p_values=p_values,
        observed_feature_ref=observed_feature_ref,
        caveats=tuple(caveats),
    ).to_payload()


def validate_null_feature_payload(payload: Mapping[str, object]) -> None:
    """Validate a serialized PR-076 null feature payload."""

    if not isinstance(payload, Mapping):
        raise ValueError("null_features must be a mapping")
    if payload.get("metadata_schema") != _SCHEMA_VERSION:
        raise ValueError("null_features.metadata_schema must be obsstat.null_ensembles.v1")
    expected = {
        "owner": "OBSSTAT",
        "implementation_scope": "obsstat",
        "claim_tier": "diagnostic_only",
        "production_status": "diagnostic_only",
        "statistic_role": "null_calibrated_feature",
        "model_role": "not_model_input",
        "transfer_source": "none",
    }
    for key, value in expected.items():
        if payload.get(key) != value:
            raise ValueError(f"null_features.{key} must be {value!r}")
    required = (
        "null_ensemble_ref",
        "null_family",
        "mock_count",
        "feature_targets",
        "statistic_keys",
        "p_values",
        "tail_definitions",
        "look_elsewhere_status",
        "look_elsewhere_trials",
        "scan_volume",
        "scan_volume_hash",
        "global_local_status",
        "covariance_status",
        "sky_support_status",
        "mask_status",
        "noise_model_status",
        "null_mock_status",
        "random_seed_policy",
        "config_hash",
        "input_hashes",
        "generating_command",
        "null_ensemble",
        "look_elsewhere",
        "does_not_establish",
    )
    missing = [key for key in required if key not in payload]
    if missing:
        raise ValueError(f"null_features missing required field(s): {missing}")
    if payload["null_family"] not in _ALLOWED_NULL_FAMILIES:
        raise ValueError("null_features.null_family is not allowed")
    if payload["look_elsewhere_status"] not in _ALLOWED_LOOK_ELSEWHERE_STATUSES:
        raise ValueError("null_features.look_elsewhere_status is not allowed")
    mock_count = _positive_int(payload["mock_count"], "null_features.mock_count")
    look_elsewhere_trials = _positive_int(
        payload["look_elsewhere_trials"],
        "null_features.look_elsewhere_trials",
    )
    feature_targets = _tuple_of_str(payload["feature_targets"], "null_features.feature_targets")
    statistic_key_values = _tuple_of_str(
        payload["statistic_keys"],
        "null_features.statistic_keys",
    )
    statistic_keys = set(statistic_key_values)
    scan_volume = _json_mapping(payload["scan_volume"], "null_features.scan_volume")
    missing_scan_fields = {
        "feature_targets",
        "statistic_keys",
        "trial_count",
        "global_local_status",
    } - set(scan_volume)
    if missing_scan_fields:
        raise ValueError(
            "null_features.scan_volume missing required field(s): "
            + ", ".join(sorted(missing_scan_fields))
        )
    scan_feature_targets = set(
        _tuple_of_str(
            scan_volume["feature_targets"],
            "null_features.scan_volume.feature_targets",
        )
    )
    missing_targets = sorted(set(feature_targets) - scan_feature_targets)
    if missing_targets:
        raise ValueError(
            "null_features.feature_targets must be covered by scan_volume: "
            + ", ".join(missing_targets)
        )
    scan_statistic_keys = set(
        _tuple_of_str(
            scan_volume["statistic_keys"],
            "null_features.scan_volume.statistic_keys",
        )
    )
    if not statistic_keys.issubset(scan_statistic_keys):
        raise ValueError(
            "null_features.statistic_keys must be covered by scan_volume"
        )
    scan_trials = _positive_int(
        scan_volume["trial_count"],
        "null_features.scan_volume.trial_count",
    )
    if scan_trials != look_elsewhere_trials:
        raise ValueError("null_features.scan_volume trial_count mismatch")
    if str(scan_volume["global_local_status"]) != payload["look_elsewhere_status"]:
        raise ValueError("null_features.scan_volume global_local_status mismatch")
    if payload["global_local_status"] != payload["look_elsewhere_status"]:
        raise ValueError("null_features.global_local_status mismatch")
    scan_volume_hash = _require_hash(
        payload["scan_volume_hash"],
        "null_features.scan_volume_hash",
    )
    if scan_volume_hash != _sha256_payload(scan_volume):
        raise ValueError("null_features.scan_volume_hash must match scan_volume")
    p_values = payload["p_values"]
    if not isinstance(p_values, Mapping) or not p_values:
        raise ValueError("null_features.p_values must be non-empty")
    for key, value in p_values.items():
        numeric = float(value)
        if not math.isfinite(numeric) or not (0.0 <= numeric <= 1.0):
            raise ValueError(f"null_features.p_values[{key!r}] must be in [0, 1]")
    if not set(str(key) for key in p_values).issubset(statistic_keys):
        raise ValueError("null_features.p_values must be covered by statistic_keys")
    tail_definitions = payload["tail_definitions"]
    if not isinstance(tail_definitions, Mapping):
        raise ValueError("null_features.tail_definitions must be a mapping")
    tail_definitions = {str(key): str(value).strip() for key, value in tail_definitions.items()}
    if set(tail_definitions) != scan_statistic_keys:
        raise ValueError(
            "null_features.tail_definitions statistic_keys must match scan_volume"
        )
    invalid_tails = sorted(
        value for value in tail_definitions.values() if value not in _ALLOWED_TAILS
    )
    if invalid_tails:
        raise ValueError(
            f"null_features.tail_definitions contain invalid tails: {invalid_tails}"
        )
    if not set(str(key) for key in p_values).issubset(set(tail_definitions)):
        raise ValueError("null_features.tail_definitions must cover p_values")
    for status_key in (
        "null_ensemble_ref",
        "covariance_status",
        "sky_support_status",
        "mask_status",
        "noise_model_status",
        "null_mock_status",
        "random_seed_policy",
    ):
        _non_empty(payload[status_key], f"null_features.{status_key}")
    _require_hash(payload["config_hash"], "null_features.config_hash")
    input_hashes = _require_input_hashes(
        payload["input_hashes"],
        "null_features.input_hashes",
    )
    _non_empty(payload["generating_command"], "null_features.generating_command")
    if not (payload.get("git_commit") or payload.get("worktree_state")):
        raise ValueError("null_features requires git_commit or worktree_state")
    nested_null = payload["null_ensemble"]
    if not isinstance(nested_null, Mapping):
        raise ValueError("null_features.null_ensemble must be a mapping")
    if nested_null.get("metadata_schema") != _SCHEMA_VERSION:
        raise ValueError("null_features.null_ensemble.metadata_schema has drifted")
    nested_look = payload["look_elsewhere"]
    if not isinstance(nested_look, Mapping):
        raise ValueError("null_features.look_elsewhere must be a mapping")
    if nested_look.get("metadata_schema") != _LOOK_ELSEWHERE_SCHEMA_VERSION:
        raise ValueError("null_features.look_elsewhere.metadata_schema has drifted")
    _require_nested_match(
        nested_null,
        "null_features.null_ensemble",
        {
            "null_ensemble_ref": payload["null_ensemble_ref"],
            "null_family": payload["null_family"],
            "mock_count": mock_count,
            "feature_targets": list(feature_targets),
            "statistic_keys": list(statistic_key_values),
            "sky_support_status": payload["sky_support_status"],
            "mask_status": payload["mask_status"],
            "noise_model_status": payload["noise_model_status"],
            "covariance_status": payload["covariance_status"],
            "null_mock_status": payload["null_mock_status"],
            "random_seed_policy": payload["random_seed_policy"],
            "transfer_source": payload["transfer_source"],
            "config_hash": payload["config_hash"],
            "input_hashes": list(input_hashes),
            "generating_command": payload["generating_command"],
            "git_commit": payload.get("git_commit"),
            "worktree_state": payload.get("worktree_state"),
        },
    )
    _require_nested_match(
        nested_look,
        "null_features.look_elsewhere",
        {
            "look_elsewhere_status": payload["look_elsewhere_status"],
            "trial_count": look_elsewhere_trials,
            "scan_volume": scan_volume,
            "scan_volume_hash": scan_volume_hash,
            "tail_definitions": tail_definitions,
        },
    )
    if tuple(payload.get("does_not_establish", ())) != _DOES_NOT_ESTABLISH:
        raise ValueError("null_features.does_not_establish has drifted")
    _reject_overclaim_text(payload, "null_features")


def _require_nested_match(
    nested: Mapping[str, object],
    name: str,
    expected: Mapping[str, object],
) -> None:
    for key, value in expected.items():
        nested_value = nested.get(key)
        if isinstance(value, Mapping):
            if _json_mapping(nested_value, f"{name}.{key}") != dict(value):
                raise ValueError(f"{name}.{key} does not match top-level payload")
        elif isinstance(value, list):
            if list(nested_value or ()) != value:
                raise ValueError(f"{name}.{key} does not match top-level payload")
        elif nested_value != value:
            raise ValueError(f"{name}.{key} does not match top-level payload")
