"""CF4 object-catalog schema adapter.

The adapter validates object-level CF4-like rows for diagnostic forward-model
experiments. It does not promote compact velocity grids, transformed peculiar
velocities, or toy fixtures into production likelihood evidence.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Any

import numpy as np

__all__ = [
    "Cf4Catalog",
    "Cf4CatalogMetadata",
    "build_cf4_catalog_from_mapping",
    "load_cf4_catalog_npz",
]


_CHECKSUM_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_REQUIRED_FIELDS = (
    "object_id",
    "ra_deg",
    "dec_deg",
    "redshift",
    "distance_variable",
    "distance_uncertainty",
    "group_id",
    "is_grouped",
    "method_flag",
    "calibration_flag",
)
_DISTANCE_KINDS = {
    "logdistance",
    "distance_modulus",
    "metric_distance",
    "peculiar_velocity",
}
_GAUSSIAN_VELOCITY_STATUSES = {
    "gaussian_exact",
    "manifested_gaussian_exact",
}
_GAUSSIAN_NOISE_MODELS = {
    "gaussian_exact",
    "manifested_gaussian_exact",
    "independent_gaussian",
    "diagonal_gaussian",
}
_GAUSSIAN_MANIFEST_FIELDS = (
    "variable_definition",
    "redshift_frame",
    "noise_model",
    "covariance_status",
    "calibration_status",
    "config_hash",
    "input_hashes",
)
_FORBIDDEN_ALLOWED_USE_TOKENS = (
    "certificate",
    "evidence",
    "family",
    "inference",
    "native",
    "odds",
    "posterior",
    "production",
    "publication",
    "solver",
    "truth",
)


def _text(value: object, field: str) -> str:
    text = str(value).strip() if value is not None else ""
    if not text:
        raise ValueError(f"{field} is required")
    return text


def _sha256_text(value: object, field: str) -> str:
    text = _text(value, field)
    if not _CHECKSUM_RE.fullmatch(text):
        raise ValueError(f"{field} must be a sha256 hash")
    return text


def _sha256_sequence(value: object, field: str) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field} must be a non-empty sequence of sha256 hashes")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field} must be a non-empty sequence of sha256 hashes") from exc
    if not items:
        raise ValueError(f"{field} must be a non-empty sequence of sha256 hashes")
    return tuple(_sha256_text(item, field) for item in items)


def _string_vector(value: object, field: str) -> tuple[str, ...]:
    array = np.asarray(value)
    if array.ndim != 1:
        raise ValueError(f"{field} must be a one-dimensional array")
    result = tuple(str(item).strip() for item in array.tolist())
    if any(not item for item in result):
        raise ValueError(f"{field} must not contain blank values")
    return result


def _float_vector(value: object, field: str) -> np.ndarray:
    array = np.asarray(value, dtype=float)
    if array.ndim != 1:
        raise ValueError(f"{field} must be a one-dimensional array")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{field} must contain finite values")
    return array


def _bool_vector(value: object, field: str) -> np.ndarray:
    array = np.asarray(value, dtype=bool)
    if array.ndim != 1:
        raise ValueError(f"{field} must be a one-dimensional array")
    return array


def _require_same_row_count(arrays: Mapping[str, object]) -> int:
    lengths = {
        field: len(value)  # type: ignore[arg-type]
        for field, value in arrays.items()
    }
    unique = set(lengths.values())
    if len(unique) != 1:
        raise ValueError(f"CF4 catalog arrays must have the same row count: {lengths}")
    return unique.pop()


def _load_gaussian_velocity_manifest(
    manifest_ref: str,
    *,
    redshift_frame: str,
    calibration_status: str,
) -> str:
    path = Path(manifest_ref)
    if not path.is_file():
        raise ValueError("Gaussian velocity manifest is required and must be a readable JSON file")
    raw = path.read_bytes()
    try:
        payload = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("Gaussian velocity manifest must be valid JSON") from exc
    if not isinstance(payload, Mapping):
        raise ValueError("Gaussian velocity manifest must be a JSON object")
    missing = [field for field in _GAUSSIAN_MANIFEST_FIELDS if field not in payload]
    if missing:
        raise ValueError(
            "Gaussian velocity manifest missing required fields: " + ", ".join(missing)
        )
    manifest_frame = _text(payload["redshift_frame"], "Gaussian velocity manifest redshift_frame")
    if manifest_frame != redshift_frame:
        raise ValueError("Gaussian velocity manifest redshift_frame must match catalog metadata")
    manifest_calibration = _text(
        payload["calibration_status"],
        "Gaussian velocity manifest calibration_status",
    )
    if manifest_calibration != calibration_status:
        raise ValueError("Gaussian velocity manifest calibration_status must match catalog metadata")
    noise_model = _text(payload["noise_model"], "Gaussian velocity manifest noise_model").lower()
    if noise_model not in _GAUSSIAN_NOISE_MODELS:
        raise ValueError("Gaussian velocity manifest noise_model must declare Gaussian semantics")
    _text(payload["variable_definition"], "Gaussian velocity manifest variable_definition")
    _text(payload["covariance_status"], "Gaussian velocity manifest covariance_status")
    _sha256_text(payload["config_hash"], "Gaussian velocity manifest config_hash")
    _sha256_sequence(payload["input_hashes"], "Gaussian velocity manifest input_hashes")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class Cf4CatalogMetadata:
    """Release and calibration metadata for a CF4 object-level binding."""

    release: str
    source_path: str
    checksum: str
    redshift_frame: str
    distance_variable_kind: str
    calibration_status: str
    coordinate_frame: str = "icrs_ra_dec"
    velocity_distribution_status: str = "not_assumed_gaussian"
    gaussian_velocity_manifest_ref: str = ""
    gaussian_velocity_manifest_hash: str = ""
    claim_tier: str = "diagnostic_only"
    allowed_use: str = "schema_check_and_diagnostic_likelihood"

    def __post_init__(self) -> None:
        object.__setattr__(self, "release", _text(self.release, "release"))
        object.__setattr__(self, "source_path", _text(self.source_path, "source_path"))
        checksum = _text(self.checksum, "checksum")
        if not _CHECKSUM_RE.fullmatch(checksum):
            raise ValueError("checksum must be a sha256 hash")
        object.__setattr__(self, "checksum", checksum)
        object.__setattr__(self, "redshift_frame", _text(self.redshift_frame, "redshift_frame"))
        kind = _text(self.distance_variable_kind, "distance_variable_kind").lower()
        if kind not in _DISTANCE_KINDS:
            raise ValueError(
                "distance_variable_kind must be one of "
                + ", ".join(sorted(_DISTANCE_KINDS))
            )
        object.__setattr__(self, "distance_variable_kind", kind)
        object.__setattr__(
            self,
            "calibration_status",
            _text(self.calibration_status, "calibration_status"),
        )
        object.__setattr__(self, "coordinate_frame", _text(self.coordinate_frame, "coordinate_frame"))
        velocity_status = _text(
            self.velocity_distribution_status,
            "velocity_distribution_status",
        ).lower()
        object.__setattr__(self, "velocity_distribution_status", velocity_status)
        gaussian_ref = str(self.gaussian_velocity_manifest_ref or "").strip()
        manifest_hash = str(self.gaussian_velocity_manifest_hash or "").strip()
        if velocity_status in _GAUSSIAN_VELOCITY_STATUSES:
            if not gaussian_ref:
                raise ValueError("Gaussian velocity manifest is required")
            computed_hash = _load_gaussian_velocity_manifest(
                gaussian_ref,
                redshift_frame=self.redshift_frame,
                calibration_status=self.calibration_status,
            )
            if manifest_hash and manifest_hash != computed_hash:
                raise ValueError("Gaussian velocity manifest hash does not match manifest bytes")
            manifest_hash = computed_hash
        elif manifest_hash:
            manifest_hash = _sha256_text(manifest_hash, "gaussian_velocity_manifest_hash")
        if velocity_status in _GAUSSIAN_VELOCITY_STATUSES and not manifest_hash:
            raise ValueError("Gaussian velocity manifest is required")
        object.__setattr__(self, "gaussian_velocity_manifest_ref", gaussian_ref)
        object.__setattr__(self, "gaussian_velocity_manifest_hash", manifest_hash)
        if self.claim_tier != "diagnostic_only":
            raise ValueError("CF4 catalog metadata claim_tier must be diagnostic_only")
        allowed_use = _text(self.allowed_use, "allowed_use")
        lowered_allowed_use = allowed_use.lower()
        if any(token in lowered_allowed_use for token in _FORBIDDEN_ALLOWED_USE_TOKENS):
            raise ValueError("CF4 catalog allowed_use must not imply inference or claim promotion")
        object.__setattr__(self, "allowed_use", allowed_use)

    @property
    def allows_exact_gaussian_velocity(self) -> bool:
        return (
            self.distance_variable_kind != "peculiar_velocity"
            or (
                self.velocity_distribution_status in _GAUSSIAN_VELOCITY_STATUSES
                and bool(self.gaussian_velocity_manifest_ref)
                and bool(self.gaussian_velocity_manifest_hash)
            )
        )

    def to_metadata(self) -> dict[str, Any]:
        return {
            "release": self.release,
            "source_path": self.source_path,
            "checksum": self.checksum,
            "redshift_frame": self.redshift_frame,
            "distance_variable_kind": self.distance_variable_kind,
            "calibration_status": self.calibration_status,
            "coordinate_frame": self.coordinate_frame,
            "velocity_distribution_status": self.velocity_distribution_status,
            "gaussian_velocity_manifest_ref": self.gaussian_velocity_manifest_ref,
            "gaussian_velocity_manifest_hash": self.gaussian_velocity_manifest_hash,
            "claim_tier": self.claim_tier,
            "allowed_use": self.allowed_use,
        }


@dataclass(frozen=True)
class Cf4Catalog:
    """Validated object-level CF4-like catalog arrays."""

    metadata: Cf4CatalogMetadata
    object_id: tuple[str, ...]
    ra_deg: np.ndarray
    dec_deg: np.ndarray
    redshift: np.ndarray
    distance_variable: np.ndarray
    distance_uncertainty: np.ndarray
    group_id: tuple[str, ...]
    is_grouped: np.ndarray
    method_flag: tuple[str, ...]
    calibration_flag: tuple[str, ...]

    def __post_init__(self) -> None:
        arrays: dict[str, object] = {
            "object_id": self.object_id,
            "ra_deg": self.ra_deg,
            "dec_deg": self.dec_deg,
            "redshift": self.redshift,
            "distance_variable": self.distance_variable,
            "distance_uncertainty": self.distance_uncertainty,
            "group_id": self.group_id,
            "is_grouped": self.is_grouped,
            "method_flag": self.method_flag,
            "calibration_flag": self.calibration_flag,
        }
        row_count = _require_same_row_count(arrays)
        if row_count <= 0:
            raise ValueError("CF4 catalog must contain at least one row")
        if np.any((self.ra_deg < 0.0) | (self.ra_deg >= 360.0)):
            raise ValueError("ra_deg must be in [0, 360)")
        if np.any((self.dec_deg < -90.0) | (self.dec_deg > 90.0)):
            raise ValueError("dec_deg must be in [-90, 90]")
        if np.any(self.redshift <= 0.0):
            raise ValueError("redshift must be positive finite")
        if np.any(self.distance_uncertainty <= 0.0):
            raise ValueError("distance_uncertainty must be positive finite")

    @property
    def row_count(self) -> int:
        return len(self.object_id)

    @property
    def line_of_sight_unit(self) -> np.ndarray:
        ra = np.deg2rad(self.ra_deg)
        dec = np.deg2rad(self.dec_deg)
        cos_dec = np.cos(dec)
        return np.column_stack(
            (
                cos_dec * np.cos(ra),
                cos_dec * np.sin(ra),
                np.sin(dec),
            )
        )

    def to_metadata(self) -> dict[str, Any]:
        return {
            "owner": "OBSSTAT",
            "implementation_scope": "obsstat",
            "claim_tier": "diagnostic_only",
            "artifact_role": "cf4_object_catalog_schema",
            "row_count": self.row_count,
            "redshift_frame": self.metadata.redshift_frame,
            "distance_variable_kind": self.metadata.distance_variable_kind,
            "coordinate_frame": self.metadata.coordinate_frame,
            "release": self.metadata.release,
            "checksum": self.metadata.checksum,
            "schema_fields": {field: "required" for field in _REQUIRED_FIELDS},
            "velocity_distribution_status": self.metadata.velocity_distribution_status,
            "gaussian_velocity_manifest_ref": self.metadata.gaussian_velocity_manifest_ref,
            "gaussian_velocity_manifest_hash": self.metadata.gaussian_velocity_manifest_hash,
            "caveats": [
                "object-level CF4 schema validation only",
                "not HTT evidence and not publication-grade inference",
                "compact velocity grids are not object catalogs",
            ],
        }


def build_cf4_catalog_from_mapping(
    payload: Mapping[str, object],
    *,
    metadata: Cf4CatalogMetadata,
) -> Cf4Catalog:
    """Build a validated CF4 object-level catalog from array-like fields."""

    missing = [field for field in _REQUIRED_FIELDS if field not in payload]
    if missing:
        raise ValueError("CF4 object catalog missing required fields: " + ", ".join(missing))
    return Cf4Catalog(
        metadata=metadata,
        object_id=_string_vector(payload["object_id"], "object_id"),
        ra_deg=_float_vector(payload["ra_deg"], "ra_deg"),
        dec_deg=_float_vector(payload["dec_deg"], "dec_deg"),
        redshift=_float_vector(payload["redshift"], "redshift"),
        distance_variable=_float_vector(payload["distance_variable"], "distance_variable"),
        distance_uncertainty=_float_vector(
            payload["distance_uncertainty"],
            "distance_uncertainty",
        ),
        group_id=_string_vector(payload["group_id"], "group_id"),
        is_grouped=_bool_vector(payload["is_grouped"], "is_grouped"),
        method_flag=_string_vector(payload["method_flag"], "method_flag"),
        calibration_flag=_string_vector(payload["calibration_flag"], "calibration_flag"),
    )


def load_cf4_catalog_npz(
    path: str | Path,
    *,
    metadata: Cf4CatalogMetadata,
) -> Cf4Catalog:
    """Load a CF4 object-level catalog from `.npz` without pickle support."""

    with np.load(Path(path), allow_pickle=False) as data:
        payload = {key: data[key] for key in data.files}
    actual_checksum = "sha256:" + hashlib.sha256(Path(path).read_bytes()).hexdigest()
    if metadata.checksum != actual_checksum:
        raise ValueError("CF4 catalog checksum does not match file bytes")
    return build_cf4_catalog_from_mapping(payload, metadata=metadata)
