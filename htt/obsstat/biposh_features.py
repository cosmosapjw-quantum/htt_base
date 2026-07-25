"""BiPoSH and sparse covariance feature payloads for OBSSTAT.

OBSSTAT packages caller-supplied observable covariance descriptors.  This
module computes convention-tagged sparse coefficient summaries; it does not
compute transfer functions, native solver outputs, HTT evidence, MIO
certificates, or family labels.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import hashlib
import json
import math
from typing import Any

import numpy as np

from common.transfer_registry import (
    TransferSource,
    validate_transfer_dependent_result,
)

from .alm_conventions import (
    AlmConvention,
    validate_alm_convention_metadata,
)

__all__ = [
    "BiPoSHConventionMetadata",
    "BiPoSHFeatureSummary",
    "SparseBiPoSHCoefficient",
    "build_biposh_feature_payload",
]


_SCHEMA_VERSION = "obsstat.biposh_features.v1"
_CONVENTION_SCHEMA_VERSION = "obsstat.biposh_features.convention.v1"
_FEATURE_CAVEAT = (
    "BiPoSH/sparse covariance feature extraction only; not HTT model output, "
    "not MIO output, and not a family label"
)
_SYSTEMATIC_CAVEAT = (
    "mask/beam/systematic hooks are descriptive caveats unless matched null "
    "and covariance calibration are supplied elsewhere"
)
_REQUIRED_ROTATION_FIELDS = {
    "rotation_group",
    "component_index",
    "norm_invariant_under",
}
_ALLOWED_ROTATION_GROUPS = {"SO3"}
_ALLOWED_NORM_INVARIANTS = {"unitary_M_basis_rotation"}
_TRANSFER_TOP_LEVEL_FIELDS = {
    "transfer_id",
    "transfer_source",
    "family",
    "valid_range",
    "observable_kind",
    "normalization",
    "calibration_status",
    "source_ref",
    "version",
    "passed_validation_gates",
    "passed_gates",
    "returns_values",
    "consumable_as_result",
    "schema_status",
}
_PROTECTED_PAYLOAD_FIELDS = {
    "owner",
    "implementation_scope",
    "claim_tier",
    "production_status",
    "statistic_role",
    "model_role",
    "representation",
    "transfer_derived",
    "convention_metadata",
    "entries",
    "entry_hash",
    "sparse_index_policy",
    "threshold_policy",
    "norm_summary",
    "ell_range",
    "channel_pairs",
    "sky_support_status",
    "mask_status",
    "beam_status",
    "systematic_status",
    "covariance_status",
    "null_mock_status",
    "caveat_hooks",
    "config_hash",
    "input_hashes",
    "generating_command",
    "source_metadata",
    "claim_status",
    "definitions",
    "git_commit",
    "worktree_state",
}
_FORBIDDEN_TEXT_PARTS = (
    "posterior",
    "likelihood",
    "evidence",
    "bayes",
    "certificate",
    "truth",
    "detects geometry",
    "detected geometry",
    "geometry detected",
    "identified family",
    "family identified",
    "family identification",
    "family ranking",
    "family_rank",
    "identified_family",
    "geometry_detected",
    "native solver result",
    "native bass",
    "morphology compatibility",
)


@dataclass(frozen=True)
class BiPoSHConventionMetadata:
    """Convention tags needed to interpret a sparse BiPoSH feature."""

    alm_convention: AlmConvention | Mapping[str, Any]
    rotation_metadata: Mapping[str, Any]
    metadata_schema: str = _CONVENTION_SCHEMA_VERSION
    coefficient_basis: str = "bipolar_spherical_harmonic"
    coefficient_normalization: str = "sum_abs_squared_over_M"
    caveats: tuple[str, ...] = (
        "rotation-aware norms summarize M-components and do not identify a family",
    )

    def __post_init__(self) -> None:
        if self.metadata_schema != _CONVENTION_SCHEMA_VERSION:
            raise ValueError("BiPoSHConventionMetadata.metadata_schema is not allowed")
        metadata = _metadata_from_alm_convention(self.alm_convention)
        object.__setattr__(self, "alm_convention", metadata)
        rotation = _json_mapping(self.rotation_metadata)
        if not rotation:
            raise ValueError("BiPoSHConventionMetadata.rotation_metadata is required")
        missing = sorted(_REQUIRED_ROTATION_FIELDS - set(rotation))
        if missing:
            raise ValueError(
                "BiPoSHConventionMetadata.rotation_metadata missing required "
                "field(s): " + ", ".join(missing)
            )
        for field_name in _REQUIRED_ROTATION_FIELDS:
            if not str(rotation[field_name]).strip():
                raise ValueError(
                    "BiPoSHConventionMetadata.rotation_metadata "
                    f"{field_name} is required"
                )
        if str(rotation["rotation_group"]).strip() not in _ALLOWED_ROTATION_GROUPS:
            raise ValueError(
                "BiPoSHConventionMetadata.rotation_metadata rotation_group "
                "is not allowed"
            )
        if str(rotation["component_index"]) != "M":
            raise ValueError("BiPoSHConventionMetadata rotation component_index must be M")
        if (
            str(rotation["norm_invariant_under"]).strip()
            not in _ALLOWED_NORM_INVARIANTS
        ):
            raise ValueError(
                "BiPoSHConventionMetadata.rotation_metadata "
                "norm_invariant_under is not allowed"
            )
        if not str(self.coefficient_basis).strip():
            raise ValueError("BiPoSHConventionMetadata.coefficient_basis is required")
        if not str(self.coefficient_normalization).strip():
            raise ValueError(
                "BiPoSHConventionMetadata.coefficient_normalization is required"
            )
        object.__setattr__(self, "rotation_metadata", rotation)
        object.__setattr__(self, "caveats", tuple(str(item) for item in self.caveats))
        _reject_overclaim_text(
            {
                "rotation_metadata": rotation,
                "coefficient_basis": self.coefficient_basis,
                "coefficient_normalization": self.coefficient_normalization,
                "caveats": self.caveats,
            }
        )

    def to_metadata(self) -> dict[str, Any]:
        """Return JSON-compatible convention metadata."""

        return {
            "metadata_schema": self.metadata_schema,
            "coefficient_basis": self.coefficient_basis,
            "coefficient_normalization": self.coefficient_normalization,
            "alm_convention": dict(self.alm_convention),
            "rotation_metadata": dict(self.rotation_metadata),
            "rotation_aware_norm_definition": "sqrt(sum_M |A_l1_l2^LM|^2)",
            "claim_scope": "observable_feature_convention",
            "caveats": list(self.caveats),
        }


@dataclass(frozen=True)
class SparseBiPoSHCoefficient:
    """One sparse BiPoSH coefficient supplied by a caller."""

    channel_pair: tuple[str, str]
    ell1: int
    ell2: int
    L: int
    M: int
    value: complex | float | int

    def __post_init__(self) -> None:
        if (
            not isinstance(self.channel_pair, tuple)
            or len(self.channel_pair) != 2
            or any(not isinstance(item, str) or not item.strip() for item in self.channel_pair)
        ):
            raise ValueError("SparseBiPoSHCoefficient.channel_pair must be two strings")
        object.__setattr__(
            self,
            "channel_pair",
            tuple(str(item).strip() for item in self.channel_pair),
        )
        for field_name in ("ell1", "ell2", "L", "M"):
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError(f"SparseBiPoSHCoefficient.{field_name} must be an integer")
        if self.ell1 < 0 or self.ell2 < 0 or self.L < 0:
            raise ValueError("SparseBiPoSHCoefficient indices must be non-negative")
        if not (abs(self.ell1 - self.ell2) <= self.L <= self.ell1 + self.ell2):
            raise ValueError(
                "SparseBiPoSHCoefficient indices must satisfy the triangle condition"
            )
        if abs(self.M) > self.L:
            raise ValueError("SparseBiPoSHCoefficient requires abs(M) <= L")
        numeric = complex(self.value)
        if not (math.isfinite(numeric.real) and math.isfinite(numeric.imag)):
            raise ValueError("SparseBiPoSHCoefficient.value must be finite")
        object.__setattr__(self, "value", numeric)

    @property
    def key(self) -> tuple[str, str, int, int, int, int]:
        return (
            self.channel_pair[0],
            self.channel_pair[1],
            int(self.ell1),
            int(self.ell2),
            int(self.L),
            int(self.M),
        )

    def to_payload(self) -> dict[str, Any]:
        value = complex(self.value)
        return {
            "channel_pair": list(self.channel_pair),
            "ell1": int(self.ell1),
            "ell2": int(self.ell2),
            "L": int(self.L),
            "M": int(self.M),
            "real": float(value.real),
            "imag": float(value.imag),
            "abs_value": float(abs(value)),
            "power": float(abs(value) ** 2),
        }


@dataclass(frozen=True)
class BiPoSHFeatureSummary:
    """Diagnostic-only sparse BiPoSH feature summary."""

    entries: Sequence[SparseBiPoSHCoefficient]
    convention: BiPoSHConventionMetadata | Mapping[str, Any]
    sky_support_status: str
    mask_status: str
    beam_status: str
    systematic_status: str
    covariance_status: str
    null_mock_status: str
    threshold: float = 0.0
    config_hash: str = "sha256:config-not-supplied"
    input_hashes: Sequence[str] = field(default_factory=tuple)
    generating_command: str = ""
    git_commit: str | None = None
    worktree_state: str | None = None
    transfer_metadata: Mapping[str, Any] | None = None
    source_metadata: Mapping[str, Any] = field(default_factory=dict)
    representation: str = "biposh_sparse_coefficients"
    statistic_role: str = "feature_only"
    model_role: str = "not_model_input"
    claim_tier: str = "diagnostic_only"
    production_status: str = "diagnostic_only"
    metadata_schema: str = _SCHEMA_VERSION
    caveats: tuple[str, ...] = (_FEATURE_CAVEAT, _SYSTEMATIC_CAVEAT)

    def __post_init__(self) -> None:
        if self.metadata_schema != _SCHEMA_VERSION:
            raise ValueError("BiPoSHFeatureSummary.metadata_schema is not allowed")
        if self.statistic_role != "feature_only":
            raise ValueError("BiPoSHFeatureSummary.statistic_role must be feature_only")
        if self.model_role != "not_model_input":
            raise ValueError("BiPoSHFeatureSummary.model_role must be not_model_input")
        if self.claim_tier != "diagnostic_only":
            raise ValueError("BiPoSHFeatureSummary.claim_tier must be diagnostic_only")
        if self.production_status != "diagnostic_only":
            raise ValueError(
                "BiPoSHFeatureSummary.production_status must be diagnostic_only"
            )
        if self.representation not in {
            "biposh_sparse_coefficients",
            "sparse_harmonic_covariance",
            "basis_reduced_sparse_covariance",
            "sparse_mode_block_proxy",
        }:
            raise ValueError("BiPoSHFeatureSummary.representation is not allowed")
        entries = tuple(self.entries)
        if not entries:
            raise ValueError("BiPoSHFeatureSummary.entries must be non-empty")
        if any(not isinstance(item, SparseBiPoSHCoefficient) for item in entries):
            raise TypeError(
                "BiPoSHFeatureSummary.entries must contain SparseBiPoSHCoefficient"
            )
        object.__setattr__(self, "entries", entries)
        if isinstance(self.convention, BiPoSHConventionMetadata):
            convention = self.convention
        else:
            convention = _convention_from_metadata(self.convention)
        object.__setattr__(self, "convention", convention)
        convention_lmax = int(convention.alm_convention["lmax"])
        if any(
            max(entry.ell1, entry.ell2) > convention_lmax
            for entry in entries
        ):
            raise ValueError(
                "BiPoSHFeatureSummary entries must remain within "
                "alm_convention lmax"
            )
        for field_name in (
            "sky_support_status",
            "mask_status",
            "beam_status",
            "systematic_status",
            "covariance_status",
            "null_mock_status",
        ):
            value = str(getattr(self, field_name)).strip()
            if not value:
                raise ValueError(f"BiPoSHFeatureSummary.{field_name} is required")
            object.__setattr__(self, field_name, value)
        threshold = float(self.threshold)
        if not math.isfinite(threshold) or threshold < 0.0:
            raise ValueError("BiPoSHFeatureSummary.threshold must be finite and >= 0")
        object.__setattr__(self, "threshold", threshold)
        object.__setattr__(self, "config_hash", _require_hash(self.config_hash, "config_hash"))
        object.__setattr__(
            self,
            "input_hashes",
            _require_input_hashes(self.input_hashes, label="input_hashes"),
        )
        if not str(self.generating_command).strip():
            raise ValueError("BiPoSHFeatureSummary.generating_command is required")
        if not (self.git_commit or self.worktree_state):
            raise ValueError("BiPoSHFeatureSummary requires git_commit or worktree_state")
        object.__setattr__(
            self,
            "source_metadata",
            _json_mapping(self.source_metadata),
        )
        object.__setattr__(self, "caveats", tuple(str(item) for item in self.caveats))
        transfer_metadata = self._normalized_transfer_metadata()
        object.__setattr__(self, "transfer_metadata", transfer_metadata)
        _reject_overclaim_text(
            {
                "sky_support_status": self.sky_support_status,
                "mask_status": self.mask_status,
                "beam_status": self.beam_status,
                "systematic_status": self.systematic_status,
                "covariance_status": self.covariance_status,
                "null_mock_status": self.null_mock_status,
                "source_metadata": self.source_metadata,
                "generating_command": self.generating_command,
                "git_commit": self.git_commit or "",
                "worktree_state": self.worktree_state or "",
                "caveats": self.caveats,
            }
        )

    def to_feature_payload(self) -> dict[str, Any]:
        """Return an ObservableVector-compatible BiPoSH feature block."""

        retained, discarded = self._thresholded_entries()
        payload_entries = [entry.to_payload() for entry in retained]
        discarded_entries = [entry.to_payload() for entry in discarded]
        norm_summary = _norm_summary(retained)
        entry_hash = _sha256_payload(
            {
                "entries": payload_entries,
                "convention": self.convention.to_metadata(),
                "threshold": self.threshold,
            }
        )
        payload: dict[str, Any] = {
            "metadata_schema": self.metadata_schema,
            "owner": "OBSSTAT",
            "implementation_scope": "obsstat",
            "claim_tier": self.claim_tier,
            "production_status": self.production_status,
            "statistic_role": self.statistic_role,
            "model_role": self.model_role,
            "transfer_source": self._transfer_source_value(),
            "transfer_derived": self.transfer_metadata is not None,
            "representation": self.representation,
            "convention_metadata": self.convention.to_metadata(),
            "entries": payload_entries,
            "entry_hash": entry_hash,
            "sparse_index_policy": {
                "duplicate_policy": "reject",
                "ordering": "canonical_sorted",
                "threshold_policy": "drop_abs_value_below_threshold",
            },
            "threshold_policy": {
                "absolute_value_threshold": self.threshold,
                "retained_count": len(retained),
                "discarded_count": len(discarded),
                "input_count": len(self.entries),
                "discarded_power": float(
                    sum(float(item["power"]) for item in discarded_entries)
                ),
                "max_discarded_abs_value": (
                    None
                    if not discarded_entries
                    else float(max(float(item["abs_value"]) for item in discarded_entries))
                ),
                "discarded_entry_hash": _sha256_payload(
                    {"discarded_entries": discarded_entries}
                ),
                "discarded_entries": discarded_entries,
            },
            "norm_summary": norm_summary,
            "ell_range": _ell_range(retained),
            "channel_pairs": _channel_pairs(retained),
            "sky_support_status": self.sky_support_status,
            "mask_status": self.mask_status,
            "beam_status": self.beam_status,
            "systematic_status": self.systematic_status,
            "covariance_status": self.covariance_status,
            "null_mock_status": self.null_mock_status,
            "caveat_hooks": {
                "sky_support_status": self.sky_support_status,
                "mask_status": self.mask_status,
                "beam_status": self.beam_status,
                "systematic_status": self.systematic_status,
                "covariance_status": self.covariance_status,
                "null_mock_status": self.null_mock_status,
            },
            "config_hash": self.config_hash,
            "input_hashes": list(self.input_hashes),
            "generating_command": self.generating_command,
            "source_metadata": dict(self.source_metadata),
            "claim_status": {
                "geometry_status": "blocked_pre_native_atlas",
                "family_status": "blocked_pre_native_atlas",
                "inference_status": "not_model_input",
                "mio_status": "not_mio_output",
                "native_solver_status": "not_native_solver_output",
            },
            "definitions": {
                "total_power": "sum over retained sparse entries of |A_l1_l2^LM|^2",
                "total_norm": "sqrt(total_power)",
                "rotation_aware_norm": (
                    "per-(L,l1,l2) sqrt(sum_M |A_l1_l2^LM|^2) under the "
                    "declared rotation metadata"
                ),
            },
            "caveats": list(self.caveats),
        }
        if self.transfer_metadata is not None:
            transfer_metadata = dict(self.transfer_metadata)
            payload["transfer_metadata"] = transfer_metadata
            for key, value in transfer_metadata.items():
                if key == "caveats":
                    payload["transfer_caveats"] = list(value)
                elif key in _TRANSFER_TOP_LEVEL_FIELDS:
                    payload[key] = value
            if "caveats" in transfer_metadata:
                payload["caveats"] = list(self.caveats) + [
                    str(item) for item in transfer_metadata["caveats"]
                ]
        if self.git_commit is not None:
            payload["git_commit"] = self.git_commit
        if self.worktree_state is not None:
            payload["worktree_state"] = self.worktree_state
        return _json_payload_mapping(payload)

    def _thresholded_entries(
        self,
    ) -> tuple[tuple[SparseBiPoSHCoefficient, ...], tuple[SparseBiPoSHCoefficient, ...]]:
        canonical = _canonical_entries(self.entries)
        retained = tuple(entry for entry in canonical if abs(complex(entry.value)) >= self.threshold)
        discarded = tuple(entry for entry in canonical if abs(complex(entry.value)) < self.threshold)
        return retained, discarded

    def _normalized_transfer_metadata(self) -> dict[str, Any] | None:
        if self.transfer_metadata is None:
            return None
        metadata = _json_mapping(self.transfer_metadata)
        protected = sorted(set(metadata).intersection(_PROTECTED_PAYLOAD_FIELDS))
        if protected:
            raise ValueError(
                "BiPoSHFeatureSummary transfer metadata cannot set protected "
                "payload field(s): " + ", ".join(protected)
            )
        _reject_transfer_metadata_overclaim(metadata)
        source_value = str(metadata.get("transfer_source", ""))
        try:
            source = TransferSource(source_value)
        except ValueError as exc:
            raise ValueError("BiPoSHFeatureSummary transfer metadata is invalid") from exc
        if source is TransferSource.NONE:
            raise ValueError(
                "BiPoSHFeatureSummary transfer metadata must use a non-none "
                "transfer source"
            )
        validate_transfer_dependent_result(metadata)
        return metadata

    def _transfer_source_value(self) -> str:
        if self.transfer_metadata is None:
            return "none"
        return str(self.transfer_metadata["transfer_source"])


def build_biposh_feature_payload(
    *,
    entries: Sequence[SparseBiPoSHCoefficient],
    convention: BiPoSHConventionMetadata | Mapping[str, Any],
    sky_support_status: str,
    mask_status: str,
    beam_status: str,
    systematic_status: str,
    covariance_status: str,
    null_mock_status: str,
    threshold: float = 0.0,
    config_hash: str = "sha256:config-not-supplied",
    input_hashes: Sequence[str] = (),
    generating_command: str = "",
    git_commit: str | None = None,
    worktree_state: str | None = None,
    transfer_metadata: Mapping[str, Any] | None = None,
    source_metadata: Mapping[str, Any] | None = None,
    representation: str = "biposh_sparse_coefficients",
) -> dict[str, Any]:
    """Build an OBSSTAT diagnostic-only sparse BiPoSH feature payload."""

    return BiPoSHFeatureSummary(
        entries=entries,
        convention=convention,
        sky_support_status=sky_support_status,
        mask_status=mask_status,
        beam_status=beam_status,
        systematic_status=systematic_status,
        covariance_status=covariance_status,
        null_mock_status=null_mock_status,
        threshold=threshold,
        config_hash=config_hash,
        input_hashes=tuple(input_hashes),
        generating_command=generating_command,
        git_commit=git_commit,
        worktree_state=worktree_state,
        transfer_metadata=transfer_metadata,
        source_metadata=dict(source_metadata or {}),
        representation=representation,
    ).to_feature_payload()


def _metadata_from_alm_convention(
    convention: AlmConvention | Mapping[str, Any],
) -> dict[str, Any]:
    if isinstance(convention, AlmConvention):
        return convention.to_metadata()
    return validate_alm_convention_metadata(convention)


def _convention_from_metadata(metadata: Mapping[str, Any]) -> BiPoSHConventionMetadata:
    if not isinstance(metadata, Mapping):
        raise ValueError("BiPoSH convention metadata must be a mapping")
    alm = metadata.get("alm_convention")
    rotation = metadata.get("rotation_metadata")
    if not isinstance(alm, Mapping) or not isinstance(rotation, Mapping):
        raise ValueError(
            "BiPoSH convention metadata requires alm_convention and rotation_metadata"
        )
    return BiPoSHConventionMetadata(
        alm_convention=alm,
        rotation_metadata=rotation,
        metadata_schema=str(metadata.get("metadata_schema", _CONVENTION_SCHEMA_VERSION)),
        coefficient_basis=str(metadata.get("coefficient_basis", "bipolar_spherical_harmonic")),
        coefficient_normalization=str(
            metadata.get("coefficient_normalization", "sum_abs_squared_over_M")
        ),
        caveats=tuple(str(item) for item in metadata.get("caveats", ())),
    )


def _canonical_entries(
    entries: Sequence[SparseBiPoSHCoefficient],
) -> tuple[SparseBiPoSHCoefficient, ...]:
    seen: set[tuple[str, str, int, int, int, int]] = set()
    for entry in entries:
        if entry.key in seen:
            raise ValueError(f"duplicate sparse BiPoSH index: {entry.key!r}")
        seen.add(entry.key)
    return tuple(sorted(entries, key=lambda entry: entry.key))


def _norm_summary(entries: Sequence[SparseBiPoSHCoefficient]) -> dict[str, Any]:
    by_l: dict[str, float] = {}
    by_l_l1_l2: dict[str, float] = {}
    by_channel_l_l1_l2: dict[str, float] = {}
    total_power = 0.0
    for entry in entries:
        power = float(abs(complex(entry.value)) ** 2)
        total_power += power
        l_key = str(entry.L)
        by_l[l_key] = by_l.get(l_key, 0.0) + power
        grouped_key = f"{entry.L}:{entry.ell1}:{entry.ell2}"
        by_l_l1_l2[grouped_key] = by_l_l1_l2.get(grouped_key, 0.0) + power
        channel_grouped_key = (
            f"{entry.channel_pair[0]}:{entry.channel_pair[1]}:"
            f"{entry.L}:{entry.ell1}:{entry.ell2}"
        )
        by_channel_l_l1_l2[channel_grouped_key] = (
            by_channel_l_l1_l2.get(channel_grouped_key, 0.0) + power
        )
    return {
        "rotation_aware_norm_definition": "sqrt(sum_M |A_l1_l2^LM|^2)",
        "total_power": total_power,
        "total_norm": math.sqrt(total_power),
        "by_L": {
            key: {"power": power, "norm": math.sqrt(power)}
            for key, power in sorted(by_l.items(), key=lambda item: int(item[0]))
        },
        "by_L_l1_l2": {
            key: {"power": power, "norm": math.sqrt(power)}
            for key, power in sorted(by_l_l1_l2.items())
        },
        "by_channel_L_l1_l2": {
            key: {"power": power, "norm": math.sqrt(power)}
            for key, power in sorted(by_channel_l_l1_l2.items())
        },
    }


def _ell_range(entries: Sequence[SparseBiPoSHCoefficient]) -> dict[str, Any]:
    if not entries:
        return {"ell_min": None, "ell_max": None, "L_min": None, "L_max": None}
    ell_values = [entry.ell1 for entry in entries] + [entry.ell2 for entry in entries]
    l_values = [entry.L for entry in entries]
    return {
        "ell_min": int(min(ell_values)),
        "ell_max": int(max(ell_values)),
        "L_min": int(min(l_values)),
        "L_max": int(max(l_values)),
    }


def _channel_pairs(entries: Sequence[SparseBiPoSHCoefficient]) -> list[list[str]]:
    return [
        list(pair)
        for pair in sorted({tuple(entry.channel_pair) for entry in entries})
    ]


def _require_hash(value: str, label: str) -> str:
    token = str(value).strip()
    if _is_placeholder_hash(token):
        raise ValueError(f"{label} must be explicit")
    return token


def _require_input_hashes(values: Sequence[str], *, label: str) -> tuple[str, ...]:
    out = tuple(str(value).strip() for value in values)
    if not out or any(_is_placeholder_hash(value) for value in out):
        raise ValueError(f"{label} must be explicit")
    return out


def _is_placeholder_hash(value: str) -> bool:
    token = str(value).strip().lower()
    if not token:
        return True
    return any(
        marker in token
        for marker in ("not-supplied", "placeholder", "pending", "unknown")
    )


def _sha256_payload(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        _json_payload_mapping(payload),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _json_mapping(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {str(key): _json_ready(value) for key, value in payload.items()}


def _json_payload_mapping(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {str(key): _json_ready(value) for key, value in payload.items()}


def _json_ready(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return _json_ready(value.tolist())
    if isinstance(value, np.generic):
        return _json_ready(value.item())
    if isinstance(value, Mapping):
        return _json_payload_mapping(value)
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, complex):
        if not (math.isfinite(value.real) and math.isfinite(value.imag)):
            raise ValueError("BiPoSH payload complex values must be finite")
        return {"real": float(value.real), "imag": float(value.imag)}
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("BiPoSH payload floats must be finite")
        return value
    return value


def _reject_overclaim_text(payload: Mapping[str, Any]) -> None:
    for path in _walk_keys(payload):
        lower = path.lower()
        if any(part in lower for part in _FORBIDDEN_TEXT_PARTS):
            raise ValueError(f"forbidden claim language in BiPoSH metadata at {path}")
    for path, text in _walk_string_values(payload):
        lower = text.lower()
        if any(part in lower for part in _FORBIDDEN_TEXT_PARTS):
            raise ValueError(f"forbidden claim language in BiPoSH metadata at {path}")


def _reject_transfer_metadata_overclaim(metadata: Mapping[str, Any]) -> None:
    for path in _walk_keys(metadata):
        lower = path.lower()
        if lower == "family":
            continue
        if any(part in lower for part in _FORBIDDEN_TEXT_PARTS):
            raise ValueError(f"forbidden claim language in BiPoSH metadata at {path}")
    for path, text in _walk_string_values(metadata):
        lower = text.lower()
        if any(part in lower for part in _FORBIDDEN_TEXT_PARTS):
            raise ValueError(f"forbidden claim language in BiPoSH metadata at {path}")


def _walk_keys(payload: Mapping[str, Any], prefix: str = "") -> tuple[str, ...]:
    keys: list[str] = []
    for key, value in payload.items():
        path = f"{prefix}.{key}" if prefix else str(key)
        keys.append(path)
        if isinstance(value, Mapping):
            keys.extend(_walk_keys(value, path))
        elif isinstance(value, (tuple, list)):
            for idx, item in enumerate(value):
                if isinstance(item, Mapping):
                    keys.extend(_walk_keys(item, f"{path}.{idx}"))
    return tuple(keys)


def _walk_string_values(
    payload: Mapping[str, Any],
    prefix: str = "",
) -> tuple[tuple[str, str], ...]:
    values: list[tuple[str, str]] = []
    for key, value in payload.items():
        path = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(value, Mapping):
            values.extend(_walk_string_values(value, path))
        elif isinstance(value, (tuple, list)):
            for idx, item in enumerate(value):
                if isinstance(item, Mapping):
                    values.extend(_walk_string_values(item, f"{path}.{idx}"))
                elif isinstance(item, str):
                    values.append((f"{path}.{idx}", item))
        elif isinstance(value, str):
            values.append((path, value))
    return tuple(values)
