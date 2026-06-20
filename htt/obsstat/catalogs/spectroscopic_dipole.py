"""Spectroscopic data-random dipole feature contracts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import re
from typing import Any

import numpy as np

from .redshift_selection import (
    RedshiftSelectionCorrectionSpec,
    apply_redshift_selection_correction,
)

__all__ = [
    "SpectroscopicCatalog",
    "SpectroscopicCatalogMetadata",
    "SpectroscopicDipoleFeature",
    "build_spectroscopic_catalog_from_mapping",
    "estimate_data_random_dipole",
    "first_moment",
]


_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_REQUIRED_FIELDS = ("object_id", "ra_deg", "dec_deg", "redshift", "weight")
_CATALOG_ROLES = {"data", "random"}
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
    if not _SHA256_RE.fullmatch(text):
        raise ValueError(f"{field} must be a sha256 hash")
    return text


def _sha256_sequence(value: Sequence[str], field: str) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not value:
        raise ValueError(f"{field} must be a non-empty sequence of sha256 hashes")
    return tuple(_sha256_text(item, field) for item in value)


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
    if array.ndim != 1 or not np.all(np.isfinite(array)):
        raise ValueError(f"{field} must be a finite one-dimensional array")
    return array


def _require_same_row_count(arrays: Mapping[str, object]) -> int:
    lengths = {field: len(value) for field, value in arrays.items()}  # type: ignore[arg-type]
    unique = set(lengths.values())
    if len(unique) != 1:
        raise ValueError("spectroscopic catalog arrays must have the same row count")
    return unique.pop()


@dataclass(frozen=True)
class SpectroscopicCatalogMetadata:
    """Release metadata for one spectroscopic data or random catalog."""

    release: str
    tracer: str
    region: str
    z_bin_id: str
    catalog_role: str
    source_path: str
    checksum: str
    redshift_frame: str
    redshift_selection_status: str
    weight_definition: str = "precomputed_object_weight"
    claim_tier: str = "diagnostic_only"
    allowed_use: str = "schema_check_and_diagnostic_feature"

    def __post_init__(self) -> None:
        for field in ("release", "tracer", "region", "z_bin_id", "source_path", "redshift_frame"):
            object.__setattr__(self, field, _text(getattr(self, field), field))
        role = _text(self.catalog_role, "catalog_role").lower()
        if role not in _CATALOG_ROLES:
            raise ValueError("catalog_role must be data or random")
        object.__setattr__(self, "catalog_role", role)
        object.__setattr__(self, "checksum", _sha256_text(self.checksum, "checksum"))
        object.__setattr__(
            self,
            "redshift_selection_status",
            _text(self.redshift_selection_status, "redshift_selection_status"),
        )
        object.__setattr__(self, "weight_definition", _text(self.weight_definition, "weight_definition"))
        if self.claim_tier != "diagnostic_only":
            raise ValueError("Spectroscopic catalog claim_tier must be diagnostic_only")
        allowed_use = _text(self.allowed_use, "allowed_use")
        if any(token in allowed_use.lower() for token in _FORBIDDEN_ALLOWED_USE_TOKENS):
            raise ValueError("allowed_use must not imply inference or claim promotion")
        object.__setattr__(self, "allowed_use", allowed_use)

    def parity_key(self) -> tuple[str, str, str, str]:
        return (self.release, self.tracer, self.region, self.z_bin_id)

    def to_metadata(self) -> dict[str, Any]:
        return {
            "release": self.release,
            "tracer": self.tracer,
            "region": self.region,
            "z_bin_id": self.z_bin_id,
            "catalog_role": self.catalog_role,
            "source_path": self.source_path,
            "checksum": self.checksum,
            "redshift_frame": self.redshift_frame,
            "redshift_selection_status": self.redshift_selection_status,
            "weight_definition": self.weight_definition,
            "claim_tier": self.claim_tier,
            "allowed_use": self.allowed_use,
        }


@dataclass(frozen=True)
class SpectroscopicCatalog:
    """Validated minimal spectroscopic catalog arrays."""

    metadata: SpectroscopicCatalogMetadata
    object_id: tuple[str, ...]
    ra_deg: np.ndarray
    dec_deg: np.ndarray
    redshift: np.ndarray
    weight: np.ndarray

    def __post_init__(self) -> None:
        arrays: dict[str, object] = {
            "object_id": self.object_id,
            "ra_deg": self.ra_deg,
            "dec_deg": self.dec_deg,
            "redshift": self.redshift,
            "weight": self.weight,
        }
        row_count = _require_same_row_count(arrays)
        if row_count <= 0:
            raise ValueError("spectroscopic catalog must contain at least one row")
        if np.any((self.ra_deg < 0.0) | (self.ra_deg >= 360.0)):
            raise ValueError("ra_deg must be in [0, 360)")
        if np.any((self.dec_deg < -90.0) | (self.dec_deg > 90.0)):
            raise ValueError("dec_deg must be in [-90, 90]")
        if np.any(self.redshift <= 0.0):
            raise ValueError("redshift must be positive finite")
        if np.any(self.weight < 0.0) or float(np.sum(self.weight)) <= 0.0:
            raise ValueError("weight must be non-negative with positive total weight")

    @property
    def row_count(self) -> int:
        return len(self.object_id)

    @property
    def line_of_sight_unit(self) -> np.ndarray:
        ra = np.deg2rad(self.ra_deg)
        dec = np.deg2rad(self.dec_deg)
        cos_dec = np.cos(dec)
        return np.column_stack((cos_dec * np.cos(ra), cos_dec * np.sin(ra), np.sin(dec)))

    def to_metadata(self) -> dict[str, Any]:
        return {
            "owner": "OBSSTAT",
            "implementation_scope": "obsstat",
            "claim_tier": "diagnostic_only",
            "artifact_role": "spectroscopic_catalog_schema",
            "row_count": self.row_count,
            "metadata": self.metadata.to_metadata(),
        }


@dataclass(frozen=True)
class SpectroscopicDipoleFeature:
    """Diagnostic-only data-random dipole feature."""

    dipole_vector: np.ndarray
    raw_data_random_dipole: np.ndarray
    data_first_moment: np.ndarray
    random_first_moment: np.ndarray
    alpha: float
    data_catalog: SpectroscopicCatalog
    random_catalog: SpectroscopicCatalog
    redshift_selection: RedshiftSelectionCorrectionSpec
    config_hash: str
    input_hashes: tuple[str, ...]
    generating_command: str
    worktree_state: str
    alpha_definition: str
    blockers: tuple[str, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            "owner": "OBSSTAT",
            "implementation_scope": "obsstat",
            "claim_tier": "diagnostic_only",
            "artifact_role": "spectroscopic_data_random_dipole_feature",
            "production_status": "diagnostic_only",
            "statistic_role": "feature_only",
            "model_role": "not_model_input",
            "publication_ready": False,
            "transfer_source": "none",
            "random_catalog_status": "bound_for_diagnostic_feature",
            "redshift_selection_status": self.redshift_selection.correction_status,
            "mask_status": "random_catalog_bound_mask_not_certified",
            "dipole_vector": self.dipole_vector.tolist(),
            "raw_data_random_dipole": self.raw_data_random_dipole.tolist(),
            "data_first_moment": self.data_first_moment.tolist(),
            "random_first_moment": self.random_first_moment.tolist(),
            "alpha": self.alpha,
            "alpha_definition": self.alpha_definition,
            "blockers": list(self.blockers),
            "data_catalog": self.data_catalog.to_metadata(),
            "random_catalog": self.random_catalog.to_metadata(),
            "redshift_selection": self.redshift_selection.to_metadata(),
            "sky_support_status": "data_random_sky_coordinates_bound",
            "null_mock_status": "not_bound",
            "covariance_status": "not_bound",
            "config_hash": self.config_hash,
            "input_hashes": list(self.input_hashes),
            "generating_command": self.generating_command,
            "git_commit_or_worktree_state": self.worktree_state,
            "caveats": [
                "diagnostic data-random first moment only",
                "requires survey randoms, selection model, nulls, and covariance before public result use",
                "no local/global interpretation is attached",
            ],
        }


def build_spectroscopic_catalog_from_mapping(
    payload: Mapping[str, object],
    *,
    metadata: SpectroscopicCatalogMetadata,
) -> SpectroscopicCatalog:
    missing = [field for field in _REQUIRED_FIELDS if field not in payload]
    if missing:
        raise ValueError("spectroscopic catalog missing required fields: " + ", ".join(missing))
    return SpectroscopicCatalog(
        metadata=metadata,
        object_id=_string_vector(payload["object_id"], "object_id"),
        ra_deg=_float_vector(payload["ra_deg"], "ra_deg"),
        dec_deg=_float_vector(payload["dec_deg"], "dec_deg"),
        redshift=_float_vector(payload["redshift"], "redshift"),
        weight=_float_vector(payload["weight"], "weight"),
    )


def first_moment(catalog: SpectroscopicCatalog) -> np.ndarray:
    """Return the weighted first angular moment of one catalog."""

    return np.average(catalog.line_of_sight_unit, axis=0, weights=catalog.weight)


def estimate_data_random_dipole(
    *,
    data_catalog: SpectroscopicCatalog,
    random_catalog: SpectroscopicCatalog | None,
    alpha: float,
    redshift_selection: RedshiftSelectionCorrectionSpec,
    config_hash: str,
    input_hashes: Sequence[str],
    generating_command: str,
    worktree_state: str,
    alpha_definition: str = "user_supplied_random_first_moment_scale",
) -> SpectroscopicDipoleFeature:
    """Compute a diagnostic data-random dipole feature."""

    if random_catalog is None:
        raise ValueError("random_catalog is required for data-random dipole estimation")
    if data_catalog.metadata.catalog_role != "data":
        raise ValueError("data_catalog metadata catalog_role must be data")
    if random_catalog.metadata.catalog_role != "random":
        raise ValueError("random_catalog metadata catalog_role must be random")
    if data_catalog.metadata.parity_key() != random_catalog.metadata.parity_key():
        raise ValueError("data and random catalogs must share release/tracer/region/bin")
    if redshift_selection.z_bin_id != data_catalog.metadata.z_bin_id:
        raise ValueError("redshift_selection z_bin_id must match catalog bin")
    alpha_value = float(alpha)
    if not np.isfinite(alpha_value) or alpha_value < 0.0:
        raise ValueError("alpha must be finite and non-negative")
    config = _sha256_text(config_hash, "config_hash")
    inputs = _sha256_sequence(tuple(input_hashes), "input_hashes")
    command = _text(generating_command, "generating_command")
    state = _text(worktree_state, "worktree_state")
    normalized_alpha_definition = _text(alpha_definition, "alpha_definition")

    data_moment = first_moment(data_catalog)
    random_moment = first_moment(random_catalog)
    raw = data_moment - alpha_value * random_moment
    corrected = apply_redshift_selection_correction(raw, redshift_selection)
    blockers = [
        "certified_selection_weights_not_bound",
        "random_mask_certification_not_bound",
        "matched_nulls_not_bound",
        "covariance_not_bound",
        "survey_systematics_not_bound",
        "ppc_loocv_not_bound",
        "response_rank_not_bound",
        "local_global_interpretation_not_bound",
        "native_morphology_atlas_not_bound",
    ]
    blockers.extend(redshift_selection.blockers)
    return SpectroscopicDipoleFeature(
        dipole_vector=corrected,
        raw_data_random_dipole=raw,
        data_first_moment=data_moment,
        random_first_moment=random_moment,
        alpha=alpha_value,
        data_catalog=data_catalog,
        random_catalog=random_catalog,
        redshift_selection=redshift_selection,
        config_hash=config,
        input_hashes=inputs,
        generating_command=command,
        worktree_state=state,
        alpha_definition=normalized_alpha_definition,
        blockers=tuple(dict.fromkeys(blockers)),
    )
