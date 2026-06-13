"""MIO G_F depth-gap contract with explicit depth-bin provenance."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import hashlib
import json
import math
import re
from typing import Any

from .budget_spec import BudgetUse
from .filling_fraction import CertifiedFillingFraction


DEFAULT_DEPTH_BIN_CAVEAT = (
    "Depth-bin metadata supports MIO diagnostic G_F bookkeeping only; it does "
    "not calibrate a tail probability or identify a model."
)
DEFAULT_G_CAVEAT = (
    "G_F is a MIO diagnostic depth-gap over certified F summaries under an "
    "explicit floor and bin metadata policy; it is not HTT inference, model "
    "selection, solver validation, or classification."
)

_FORBIDDEN_G_METADATA_TERMS = (
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
    "global " + "tilt",
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
    "morphology compatibility",
)
_ALLOWED_COVARIANCE_STATUSES = frozenset(
    {
        "mock_covariance",
        "matched_calibrated_covariance",
        "diagnostic_unmatched_covariance",
    }
)
_ALLOWED_NULL_MOCK_STATUSES = frozenset(
    {
        "mock_calibrated",
        "matched_calibrated_null",
        "diagnostic_unmatched_null",
    }
)
_ALLOWED_STATISTICAL_CALIBRATION_STATUSES = frozenset(
    {
        "matched_calibrated",
        "diagnostic_unmatched",
    }
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


def _finite_float(value: object, name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be finite") from exc
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite")
    return number


def _positive_float(value: object, name: str) -> float:
    number = _finite_float(value, name)
    if number <= 0.0:
        raise ValueError(f"{name} must be positive finite")
    return number


def _positive_int(value: object, name: str) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a positive integer") from exc
    if number <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return number


def _plain_metadata(value: object) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain_metadata(item) for key, item in value.items()}
    if isinstance(value, (str, bytes)):
        return str(value)
    if isinstance(value, Sequence):
        return [_plain_metadata(item) for item in value]
    if isinstance(value, float):
        if not math.isfinite(value):
            raise TypeError("metadata floats must be finite")
        return value
    if isinstance(value, (int, bool)) or value is None:
        return value
    raise TypeError(f"metadata value {value!r} is not JSON-compatible")


def _normalise_metadata(
    metadata: Mapping[str, object] | None,
    name: str,
    *,
    require_non_empty: bool = True,
) -> dict[str, Any]:
    if metadata is None:
        if require_non_empty:
            raise ValueError(f"{name} is required")
        return {}
    if not isinstance(metadata, Mapping):
        raise ValueError(f"{name} must be a mapping")
    try:
        result = _plain_metadata(dict(metadata))
    except TypeError as exc:
        raise ValueError(f"{name} must be JSON-compatible") from exc
    if not isinstance(result, dict):
        raise ValueError(f"{name} must be a mapping")
    if require_non_empty and not result:
        raise ValueError(f"{name} must be non-empty")
    _scan_reserved_language(result, name)
    _ensure_json_metadata(result, name)
    return result


def _ensure_json_metadata(value: object, name: str) -> None:
    try:
        json.dumps(value, sort_keys=True, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be JSON-compatible") from exc


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _metadata_hash(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _normalise_claim_text(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()


def _scan_reserved_language(value: object, name: str) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            _scan_reserved_language(key, name)
            _scan_reserved_language(item, name)
        return
    if isinstance(value, (str, bytes)):
        text = _normalise_claim_text(value)
        for term in _FORBIDDEN_G_METADATA_TERMS:
            if _normalise_claim_text(term) in text:
                raise ValueError(
                    f"{name} must not use reserved G_F metadata language: {term}"
                )
        return
    if isinstance(value, Sequence):
        for item in value:
            _scan_reserved_language(item, name)


def _require_metadata_key(metadata: Mapping[str, object], key: str, name: str) -> None:
    _non_empty(metadata.get(key), f"{name}.{key}")


def _require_status_value(
    value: object,
    name: str,
    allowed: frozenset[str],
) -> str:
    status = _non_empty(value, name)
    if status not in allowed:
        allowed_text = ", ".join(sorted(allowed))
        raise ValueError(f"{name} must be one of: {allowed_text}")
    return status


def _uniform_or_mixed(values: Sequence[str]) -> str:
    if not values:
        return "not_applicable"
    unique = set(values)
    if len(unique) == 1:
        return next(iter(unique))
    return "mixed"


def _mean(values: Sequence[float]) -> float:
    if not values:
        raise ValueError("cannot average an empty sequence")
    return math.fsum(values) / len(values)


def _merged_input_hashes(records: Sequence["DepthBinFRecord"]) -> tuple[str, ...]:
    values: list[str] = []
    for record in records:
        values.extend(record.input_hashes)
        values.extend(
            (
                record.depth_bin.selection_hash,
                record.depth_bin.bin_assignment_hash,
            )
        )
        covariance_hash = record.depth_bin.covariance_metadata.get("covariance_hash")
        null_hash = record.depth_bin.null_metadata.get("mock_bank_hash")
        if covariance_hash is not None:
            values.append(str(covariance_hash))
        if null_hash is not None:
            values.append(str(null_hash))
    return tuple(dict.fromkeys(values))


def _derive_config_hash(
    *,
    records: Sequence["DepthBinFRecord"],
    reference_bin_id: str,
    comparison_bin_id: str,
    floor_value: float,
    floor_label: str,
) -> str:
    payload = {
        "comparison_bin_id": comparison_bin_id,
        "floor_label": floor_label,
        "floor_value": floor_value,
        "record_config_hashes": [record.config_hash for record in records],
        "reference_bin_id": reference_bin_id,
        "score_label": "G_F",
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class DepthBinMetadata:
    """Required depth-bin metadata for exporting a MIO ``G_F`` diagnostic."""

    bin_id: str
    depth_min: float
    depth_max: float
    depth_unit: str
    depth_convention: str
    selection_rule: str
    selection_hash: str
    bin_assignment_hash: str
    sky_support_status: str
    mask_status: str
    covariance_status: str
    covariance_metadata: Mapping[str, object]
    null_mock_status: str
    null_metadata: Mapping[str, object]
    denominator_evolution_status: str
    sample_count: int
    caveats: tuple[str, ...] = field(
        default_factory=lambda: (DEFAULT_DEPTH_BIN_CAVEAT,)
    )

    def __post_init__(self) -> None:
        bin_id = _non_empty(self.bin_id, "bin_id")
        depth_min = _finite_float(self.depth_min, "depth_min")
        depth_max = _finite_float(self.depth_max, "depth_max")
        if depth_max <= depth_min:
            raise ValueError("depth metadata requires depth_max > depth_min")
        depth_unit = _non_empty(self.depth_unit, "depth_unit")
        depth_convention = _non_empty(self.depth_convention, "depth_convention")
        selection_rule = _non_empty(self.selection_rule, "selection_rule")
        selection_hash = _non_empty(self.selection_hash, "selection_hash")
        bin_assignment_hash = _non_empty(
            self.bin_assignment_hash,
            "bin_assignment_hash",
        )
        sky_support_status = _non_empty(
            self.sky_support_status,
            "sky_support_status",
        )
        if sky_support_status == "not_directional":
            raise ValueError("sky_support_status must describe depth-bin support")
        mask_status = _non_empty(self.mask_status, "mask_status")
        covariance_status = _non_empty(self.covariance_status, "covariance_status")
        if covariance_status == "not_statistical":
            raise ValueError("covariance_status must be explicit for G_F")
        _require_status_value(
            covariance_status,
            "covariance_status",
            _ALLOWED_COVARIANCE_STATUSES,
        )
        covariance_metadata = _normalise_metadata(
            self.covariance_metadata,
            "covariance_metadata",
        )
        _require_metadata_key(
            covariance_metadata,
            "covariance_hash",
            "covariance_metadata",
        )
        _require_metadata_key(covariance_metadata, "estimator", "covariance_metadata")
        if "shape" not in covariance_metadata:
            raise ValueError("covariance_metadata.shape is required")
        _require_status_value(
            covariance_metadata.get("calibration_status"),
            "covariance_metadata.calibration_status",
            _ALLOWED_STATISTICAL_CALIBRATION_STATUSES,
        )
        null_mock_status = _non_empty(self.null_mock_status, "null_mock_status")
        if null_mock_status == "not_statistical":
            raise ValueError("null_mock_status must be explicit for G_F")
        _require_status_value(
            null_mock_status,
            "null_mock_status",
            _ALLOWED_NULL_MOCK_STATUSES,
        )
        null_metadata = _normalise_metadata(self.null_metadata, "null_metadata")
        _require_metadata_key(null_metadata, "mock_bank_hash", "null_metadata")
        _require_status_value(
            null_metadata.get("calibration_status"),
            "null_metadata.calibration_status",
            _ALLOWED_STATISTICAL_CALIBRATION_STATUSES,
        )
        denominator_status = _non_empty(
            self.denominator_evolution_status,
            "denominator_evolution_status",
        )
        sample_count = _positive_int(self.sample_count, "sample_count")
        caveats = tuple(dict.fromkeys(_tuple_of_str(self.caveats, "caveats")))
        if DEFAULT_DEPTH_BIN_CAVEAT not in caveats:
            caveats = (DEFAULT_DEPTH_BIN_CAVEAT, *caveats)
        _scan_reserved_language(
            (
                bin_id,
                depth_unit,
                depth_convention,
                selection_rule,
                selection_hash,
                bin_assignment_hash,
                sky_support_status,
                mask_status,
                covariance_status,
                null_mock_status,
                denominator_status,
                caveats,
            ),
            "depth_bin_metadata",
        )

        object.__setattr__(self, "bin_id", bin_id)
        object.__setattr__(self, "depth_min", depth_min)
        object.__setattr__(self, "depth_max", depth_max)
        object.__setattr__(self, "depth_unit", depth_unit)
        object.__setattr__(self, "depth_convention", depth_convention)
        object.__setattr__(self, "selection_rule", selection_rule)
        object.__setattr__(self, "selection_hash", selection_hash)
        object.__setattr__(self, "bin_assignment_hash", bin_assignment_hash)
        object.__setattr__(self, "sky_support_status", sky_support_status)
        object.__setattr__(self, "mask_status", mask_status)
        object.__setattr__(self, "covariance_status", covariance_status)
        object.__setattr__(self, "covariance_metadata", covariance_metadata)
        object.__setattr__(self, "null_mock_status", null_mock_status)
        object.__setattr__(self, "null_metadata", null_metadata)
        object.__setattr__(self, "denominator_evolution_status", denominator_status)
        object.__setattr__(self, "sample_count", sample_count)
        object.__setattr__(self, "caveats", caveats)

    def as_payload(self) -> dict[str, object]:
        return {
            "bin_id": self.bin_id,
            "depth_min": self.depth_min,
            "depth_max": self.depth_max,
            "depth_unit": self.depth_unit,
            "depth_convention": self.depth_convention,
            "selection_rule": self.selection_rule,
            "selection_hash": self.selection_hash,
            "bin_assignment_hash": self.bin_assignment_hash,
            "sky_support_status": self.sky_support_status,
            "mask_status": self.mask_status,
            "covariance_status": self.covariance_status,
            "covariance_metadata": dict(self.covariance_metadata),
            "null_mock_status": self.null_mock_status,
            "null_metadata": dict(self.null_metadata),
            "denominator_evolution_status": self.denominator_evolution_status,
            "sample_count": self.sample_count,
            "caveats": list(self.caveats),
        }


@dataclass(frozen=True)
class DepthBinFRecord:
    """One certified-F summary bound to required depth-bin metadata."""

    filling_fraction: CertifiedFillingFraction
    depth_bin: DepthBinMetadata
    source_metadata: Mapping[str, object] | None = None
    caveats: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not isinstance(self.filling_fraction, CertifiedFillingFraction):
            raise TypeError("DepthBinFRecord requires a CertifiedFillingFraction")
        if not isinstance(self.depth_bin, DepthBinMetadata):
            raise TypeError("DepthBinFRecord requires DepthBinMetadata")
        for budget in self.filling_fraction.budget_specs:
            if BudgetUse.DEPTH_GAP_REFERENCE not in budget.admissible_uses:
                raise ValueError(
                    "G_F requires budgets admitting BudgetUse.DEPTH_GAP_REFERENCE"
                )
        metadata = _normalise_metadata(
            self.source_metadata,
            "source_metadata",
            require_non_empty=False,
        )
        caveats = tuple(dict.fromkeys(_tuple_of_str(self.caveats, "caveats")))
        _scan_reserved_language(caveats, "caveats")
        object.__setattr__(self, "source_metadata", metadata)
        object.__setattr__(self, "caveats", caveats)

    @property
    def bin_id(self) -> str:
        return self.depth_bin.bin_id

    @property
    def f_value(self) -> float:
        return self.filling_fraction.F_Bayes

    @property
    def x_C_mean(self) -> float:
        return _mean(self.filling_fraction.x_C_samples)

    @property
    def denominator_value_mean(self) -> float:
        return _mean(self.filling_fraction.U_samples)

    @property
    def denominator_policy(self) -> str:
        return self.filling_fraction.denominator_policy

    @property
    def transfer_source(self) -> str:
        return self.filling_fraction.transfer_source

    @property
    def transfer_spec_ids(self) -> tuple[str, ...]:
        ids = [
            spec_id
            for spec_id in (
                *self.filling_fraction.as_payload()["departure_transfer_spec_ids"],
                *self.filling_fraction.as_payload()["budget_transfer_spec_ids"],
            )
            if spec_id is not None
        ]
        return tuple(dict.fromkeys(str(spec_id) for spec_id in ids))

    @property
    def transfer_metadata(self) -> dict[str, Any] | None:
        metadata_values: list[dict[str, Any]] = []
        payload = self.filling_fraction.as_payload()
        raw_metadata_values = (
            *payload["departure_transfer_metadata"],
            *payload["budget_transfer_metadata"],
        )
        for metadata in raw_metadata_values:
            if metadata is None:
                continue
            plain_metadata = _plain_metadata(metadata)
            if not isinstance(plain_metadata, dict):
                raise ValueError("transfer metadata must be a mapping")
            metadata_values.append(plain_metadata)
        if not metadata_values:
            return None
        metadata_hashes = {_metadata_hash(metadata) for metadata in metadata_values}
        if len(metadata_hashes) != 1:
            raise ValueError("transfer_metadata must match within a depth-bin record")
        metadata = metadata_values[0]
        spec_ids = self.transfer_spec_ids
        if spec_ids:
            transfer_id = _non_empty(
                metadata.get("transfer_id"),
                "transfer_metadata.transfer_id",
            )
            if transfer_id not in spec_ids:
                raise ValueError(
                    "transfer_metadata.transfer_id must match transfer_spec_id"
                )
        return metadata

    @property
    def transfer_metadata_hash(self) -> str | None:
        metadata = self.transfer_metadata
        if metadata is None:
            return None
        return _metadata_hash(metadata)

    @property
    def config_hash(self) -> str:
        return self.filling_fraction.config_hash

    @property
    def input_hashes(self) -> tuple[str, ...]:
        return self.filling_fraction.input_hashes

    def as_payload(self) -> dict[str, object]:
        return {
            "bin_id": self.bin_id,
            "F_Bayes": self.f_value,
            "f_samples": list(self.filling_fraction.f_samples),
            "x_C_samples": list(self.filling_fraction.x_C_samples),
            "x_C_mean": self.x_C_mean,
            "denominator_values": list(self.filling_fraction.U_samples),
            "denominator_value_mean": self.denominator_value_mean,
            "denominator_policy": self.denominator_policy,
            "depth_bin": self.depth_bin.as_payload(),
            "source_metadata": dict(self.source_metadata),
            "transfer_source": self.transfer_source,
            "transfer_spec_ids": list(self.transfer_spec_ids),
            "transfer_metadata": self.transfer_metadata,
            "transfer_metadata_hash": self.transfer_metadata_hash,
            "config_hash": self.config_hash,
            "input_hashes": list(self.input_hashes),
            "caveats": list(self.caveats),
        }


@dataclass(frozen=True)
class IsotropyGap:
    """MIO diagnostic ``G_F`` as a floor-stabilized depth-bin contrast."""

    depth_bin_records: tuple[DepthBinFRecord, ...]
    reference_bin_id: str
    comparison_bin_id: str
    floor_value: float
    floor_label: str
    floor_reason: str
    generating_command: str = ""
    git_commit: str | None = None
    worktree_state: str | None = None
    config_hash: str | None = None
    input_hashes: tuple[str, ...] | None = None
    artifact_metadata: Mapping[str, object] | None = None
    caveats: tuple[str, ...] = field(default_factory=lambda: (DEFAULT_G_CAVEAT,))
    score_label: str = "G_F"
    claim_tier: str = "diagnostic_only"
    owner: str = "MIO"
    implementation_scope: str = "mio"

    def __post_init__(self) -> None:
        records = tuple(self.depth_bin_records)
        if len(records) < 2:
            raise ValueError("G_F requires at least two depth-bin records")
        if any(not isinstance(record, DepthBinFRecord) for record in records):
            raise TypeError("depth_bin_records must contain DepthBinFRecord entries")
        bin_ids = [record.bin_id for record in records]
        if len(set(bin_ids)) != len(bin_ids):
            raise ValueError("depth-bin identifiers must be unique")
        ordered_records = tuple(
            sorted(records, key=lambda record: record.depth_bin.depth_min)
        )
        for previous, current in zip(ordered_records, ordered_records[1:]):
            if previous.depth_bin.depth_max > current.depth_bin.depth_min:
                raise ValueError("depth-bin intervals must not overlap")
        reference_bin_id = _non_empty(self.reference_bin_id, "reference_bin_id")
        comparison_bin_id = _non_empty(self.comparison_bin_id, "comparison_bin_id")
        if reference_bin_id == comparison_bin_id:
            raise ValueError("reference and comparison bins must be distinct")
        by_id = {record.bin_id: record for record in ordered_records}
        if reference_bin_id not in by_id:
            raise ValueError("reference_bin_id must identify a depth bin")
        if comparison_bin_id not in by_id:
            raise ValueError("comparison_bin_id must identify a depth bin")
        floor_value = _positive_float(self.floor_value, "floor_value")
        if floor_value > 1.0:
            raise ValueError("floor_value must be in the F interval (0, 1]")
        floor_label = _non_empty(self.floor_label, "floor_label")
        floor_reason = _non_empty(self.floor_reason, "floor_reason")
        generating_command = _non_empty(
            self.generating_command,
            "generating_command",
        )
        git_commit = _optional_non_empty(self.git_commit, "git_commit")
        worktree_state = _optional_non_empty(self.worktree_state, "worktree_state")
        if git_commit is None and worktree_state is None:
            raise ValueError("G_F payload requires git_commit or worktree_state")
        if self.score_label != "G_F":
            raise ValueError("score_label must be 'G_F'")
        if self.owner != "MIO":
            raise ValueError("IsotropyGap owner must be 'MIO'")
        if self.claim_tier != "diagnostic_only":
            raise ValueError("IsotropyGap claim_tier must be 'diagnostic_only'")
        if self.implementation_scope != "mio":
            raise ValueError("IsotropyGap implementation_scope must be 'mio'")
        artifact_metadata = _normalise_metadata(
            self.artifact_metadata,
            "artifact_metadata",
            require_non_empty=False,
        )
        caveats = tuple(dict.fromkeys(_tuple_of_str(self.caveats, "caveats")))
        if DEFAULT_G_CAVEAT not in caveats:
            caveats = (DEFAULT_G_CAVEAT, *caveats)
        _scan_reserved_language(
            (
                reference_bin_id,
                comparison_bin_id,
                floor_label,
                floor_reason,
            ),
            "G_F metadata",
        )
        _scan_reserved_language(caveats, "caveats")

        sources = {record.transfer_source for record in ordered_records}
        if len(sources) != 1:
            raise ValueError("G_F requires matching transfer_source across bins")
        spec_ids = {
            spec_id
            for record in ordered_records
            for spec_id in record.transfer_spec_ids
            if spec_id is not None
        }
        if len(spec_ids) > 1:
            raise ValueError("G_F requires matching transfer_spec_id across bins")
        transfer_metadata_by_bin = {
            record.bin_id: record.transfer_metadata for record in ordered_records
        }
        transfer_metadata_hashes = {
            record.transfer_metadata_hash
            for record in ordered_records
            if record.transfer_metadata_hash is not None
        }
        source = next(iter(sources))
        if source == "none":
            if any(metadata is not None for metadata in transfer_metadata_by_bin.values()):
                raise ValueError("transfer_source='none' cannot carry transfer_metadata")
        else:
            if not spec_ids:
                raise ValueError(
                    "G_F requires transfer_spec_id for transfer-derived bins"
                )
            if any(metadata is None for metadata in transfer_metadata_by_bin.values()):
                raise ValueError(
                    "G_F requires transfer_metadata for transfer-derived bins"
                )
            if len(transfer_metadata_hashes) != 1:
                raise ValueError("G_F requires matching transfer_metadata across bins")

        config_hash = (
            _non_empty(self.config_hash, "config_hash")
            if self.config_hash is not None
            else _derive_config_hash(
                records=ordered_records,
                reference_bin_id=reference_bin_id,
                comparison_bin_id=comparison_bin_id,
                floor_value=floor_value,
                floor_label=floor_label,
            )
        )
        input_hashes = (
            _tuple_of_str(self.input_hashes, "input_hashes", require_non_empty=True)
            if self.input_hashes is not None
            else _merged_input_hashes(ordered_records)
        )
        if not input_hashes:
            raise ValueError("input_hashes must contain at least one hash")

        object.__setattr__(self, "depth_bin_records", ordered_records)
        object.__setattr__(self, "reference_bin_id", reference_bin_id)
        object.__setattr__(self, "comparison_bin_id", comparison_bin_id)
        object.__setattr__(self, "floor_value", floor_value)
        object.__setattr__(self, "floor_label", floor_label)
        object.__setattr__(self, "floor_reason", floor_reason)
        object.__setattr__(self, "generating_command", generating_command)
        object.__setattr__(self, "git_commit", git_commit)
        object.__setattr__(self, "worktree_state", worktree_state)
        object.__setattr__(self, "config_hash", config_hash)
        object.__setattr__(self, "input_hashes", input_hashes)
        object.__setattr__(self, "artifact_metadata", artifact_metadata)
        object.__setattr__(self, "caveats", caveats)

    @property
    def _records_by_id(self) -> dict[str, DepthBinFRecord]:
        return {record.bin_id: record for record in self.depth_bin_records}

    @property
    def reference_record(self) -> DepthBinFRecord:
        return self._records_by_id[self.reference_bin_id]

    @property
    def comparison_record(self) -> DepthBinFRecord:
        return self._records_by_id[self.comparison_bin_id]

    @property
    def raw_F_by_bin(self) -> dict[str, float]:
        return {record.bin_id: record.f_value for record in self.depth_bin_records}

    @property
    def effective_F_by_bin(self) -> dict[str, float]:
        return {
            record.bin_id: max(record.f_value, self.floor_value)
            for record in self.depth_bin_records
        }

    @property
    def floor_applied_by_bin(self) -> dict[str, bool]:
        return {
            record.bin_id: record.f_value < self.floor_value
            for record in self.depth_bin_records
        }

    @property
    def log_g_F(self) -> float:
        effective = self.effective_F_by_bin
        value = math.log(effective[self.comparison_bin_id]) - math.log(
            effective[self.reference_bin_id]
        )
        if not math.isfinite(value):
            raise ValueError("log_g_F must be finite")
        return value

    @property
    def G_F(self) -> float:
        value = math.exp(self.log_g_F)
        if not math.isfinite(value):
            raise ValueError("G_F must be finite")
        return value

    @property
    def transfer_source(self) -> str:
        return self.depth_bin_records[0].transfer_source

    @property
    def transfer_spec_ids(self) -> tuple[str, ...]:
        values = [
            spec_id
            for record in self.depth_bin_records
            for spec_id in record.transfer_spec_ids
        ]
        return tuple(dict.fromkeys(values))

    def _denominator_split_payload(self) -> dict[str, object]:
        reference = self.reference_record
        comparison = self.comparison_record
        return {
            "reference_bin_id": self.reference_bin_id,
            "comparison_bin_id": self.comparison_bin_id,
            "split_kind": "samplewise_values_plus_mean_summary",
            "mean_summary_is_decompositional": False,
            "mean_summary_note": (
                "Mean x_C and denominator deltas summarize per-bin centers only; "
                "F_Bayes is the mean of sample-wise ratios, so sample-wise arrays "
                "are the provenance for denominator-evolution effects."
            ),
            "x_C_by_bin": {
                record.bin_id: record.x_C_mean for record in self.depth_bin_records
            },
            "denominator_value_by_bin": {
                record.bin_id: record.denominator_value_mean
                for record in self.depth_bin_records
            },
            "denominator_policy_by_bin": {
                record.bin_id: record.denominator_policy
                for record in self.depth_bin_records
            },
            "F_by_bin": self.raw_F_by_bin,
            "samplewise_x_C_by_bin": {
                record.bin_id: list(record.filling_fraction.x_C_samples)
                for record in self.depth_bin_records
            },
            "samplewise_denominator_value_by_bin": {
                record.bin_id: list(record.filling_fraction.U_samples)
                for record in self.depth_bin_records
            },
            "samplewise_F_by_bin": {
                record.bin_id: list(record.filling_fraction.f_samples)
                for record in self.depth_bin_records
            },
            "sample_count_by_bin": {
                record.bin_id: len(record.filling_fraction.f_samples)
                for record in self.depth_bin_records
            },
            "x_C_depth_delta": comparison.x_C_mean - reference.x_C_mean,
            "denominator_depth_delta": (
                comparison.denominator_value_mean
                - reference.denominator_value_mean
            ),
            "F_depth_delta": comparison.f_value - reference.f_value,
            "denominator_evolution_status_by_bin": {
                record.bin_id: record.depth_bin.denominator_evolution_status
                for record in self.depth_bin_records
            },
        }

    def as_payload(self) -> dict[str, object]:
        covariance_statuses = [
            record.depth_bin.covariance_status for record in self.depth_bin_records
        ]
        null_statuses = [
            record.depth_bin.null_mock_status for record in self.depth_bin_records
        ]
        sky_statuses = [
            record.depth_bin.sky_support_status for record in self.depth_bin_records
        ]
        mask_statuses = [
            record.depth_bin.mask_status for record in self.depth_bin_records
        ]
        transfer_metadata_by_bin = {
            record.bin_id: record.transfer_metadata for record in self.depth_bin_records
        }
        transfer_metadata_hash_by_bin = {
            record.bin_id: record.transfer_metadata_hash
            for record in self.depth_bin_records
        }
        return {
            "owner": self.owner,
            "implementation_scope": self.implementation_scope,
            "claim_tier": self.claim_tier,
            "score_label": self.score_label,
            "score_kind": "isotropy_depth_gap",
            "gap_formula": (
                "log_g_F=log(max(F_comparison,floor))-"
                "log(max(F_reference,floor)); G_F=exp(log_g_F)"
            ),
            "G_F": self.G_F,
            "log_g_F": self.log_g_F,
            "reference_bin_id": self.reference_bin_id,
            "comparison_bin_id": self.comparison_bin_id,
            "floor_value": self.floor_value,
            "floor_label": self.floor_label,
            "floor_reason": self.floor_reason,
            "floor_applied_by_bin": self.floor_applied_by_bin,
            "raw_F_by_bin": self.raw_F_by_bin,
            "effective_F_by_bin": self.effective_F_by_bin,
            "depth_bin_count": len(self.depth_bin_records),
            "depth_bins": [
                record.depth_bin.as_payload() for record in self.depth_bin_records
            ],
            "depth_bin_records": [
                record.as_payload() for record in self.depth_bin_records
            ],
            "denominator_evolution_split": self._denominator_split_payload(),
            "generating_command": self.generating_command,
            "git_commit": self.git_commit,
            "worktree_state": self.worktree_state,
            "transfer_source": self.transfer_source,
            "transfer_spec_ids": list(self.transfer_spec_ids),
            "transfer_metadata_by_bin": transfer_metadata_by_bin,
            "transfer_metadata_hash_by_bin": transfer_metadata_hash_by_bin,
            "sky_support_status": _uniform_or_mixed(sky_statuses),
            "sky_support_statuses": sky_statuses,
            "mask_status": _uniform_or_mixed(mask_statuses),
            "mask_statuses": mask_statuses,
            "covariance_status": _uniform_or_mixed(covariance_statuses),
            "covariance_statuses": covariance_statuses,
            "null_mock_status": _uniform_or_mixed(null_statuses),
            "null_mock_statuses": null_statuses,
            "config_hash": self.config_hash,
            "source_config_hashes": [
                record.config_hash for record in self.depth_bin_records
            ],
            "input_hashes": list(self.input_hashes),
            "artifact_metadata": dict(self.artifact_metadata),
            "caveats": list(self.caveats),
        }


def build_depth_bin_f_record(
    filling_fraction: CertifiedFillingFraction,
    *,
    depth_bin: DepthBinMetadata,
    source_metadata: Mapping[str, object] | None = None,
    caveats: Sequence[object] = (),
) -> DepthBinFRecord:
    """Bind one certified ``F`` summary to validated depth-bin metadata."""

    return DepthBinFRecord(
        filling_fraction=filling_fraction,
        depth_bin=depth_bin,
        source_metadata=source_metadata,
        caveats=tuple(caveats),
    )


def build_isotropy_gap(
    depth_bin_records: Sequence[DepthBinFRecord],
    *,
    reference_bin_id: str,
    comparison_bin_id: str,
    floor_value: float,
    floor_label: str,
    floor_reason: str,
    generating_command: str,
    git_commit: str | None = None,
    worktree_state: str | None = None,
    config_hash: str | None = None,
    input_hashes: Sequence[object] | None = None,
    artifact_metadata: Mapping[str, object] | None = None,
    caveats: Sequence[object] | None = None,
) -> IsotropyGap:
    """Build a validated MIO ``G_F`` depth-gap diagnostic."""

    return IsotropyGap(
        depth_bin_records=tuple(depth_bin_records),
        reference_bin_id=reference_bin_id,
        comparison_bin_id=comparison_bin_id,
        floor_value=floor_value,
        floor_label=floor_label,
        floor_reason=floor_reason,
        generating_command=generating_command,
        git_commit=git_commit,
        worktree_state=worktree_state,
        config_hash=config_hash,
        input_hashes=(
            None
            if input_hashes is None
            else _tuple_of_str(input_hashes, "input_hashes", require_non_empty=True)
        ),
        artifact_metadata=artifact_metadata,
        caveats=(DEFAULT_G_CAVEAT,) if caveats is None else tuple(caveats),
    )


__all__ = [
    "DEFAULT_DEPTH_BIN_CAVEAT",
    "DEFAULT_G_CAVEAT",
    "DepthBinFRecord",
    "DepthBinMetadata",
    "IsotropyGap",
    "build_depth_bin_f_record",
    "build_isotropy_gap",
]
