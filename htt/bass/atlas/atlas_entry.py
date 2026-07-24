"""Metadata-only AtlasEntryLite records for transfer side-by-side comparison.

The objects in this module are BASS-side atlas membership descriptors.  They
preserve transfer provenance for external/proxy and future native-schema
entries, but they do not carry measured sky data, solver values, likelihoods,
or model-dependent inference products.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from common.enum_compat import StrEnum
from common.transfer_registry import (
    TransferFunctionSpec,
    TransferRegistry,
    TransferSource,
)

from ..transfer.native_schema import NativeLowEllSchema, default_native_lowell_schema
from ..transfer.registry import default_external_transfer_registry

_SCHEMA_VERSION = "bass.atlas_entry_lite.v1"
_COMPARISON_SCHEMA_VERSION = "bass.atlas_transfer_comparison.v1"
_DEFAULT_COMMAND = "bass.atlas.build_default_transfer_side_by_side_comparison"
_EXTERNAL_SOURCES = {
    TransferSource.ANICLASS_EXTERNAL.value,
    TransferSource.EXTERNAL_TRANSFER.value,
    TransferSource.EMPIRICAL_PROXY.value,
}
_NATIVE_SCHEMA_SOURCE = TransferSource.BASS_NATIVE_PROVISIONAL.value
_ALLOWED_TRANSFER_SOURCES = _EXTERNAL_SOURCES | {_NATIVE_SCHEMA_SOURCE}
_FORBIDDEN_ACTIVE_ROLE_TERMS = (
    "observed_data",
    "certificate",
    "certification",
    "posterior",
    "likelihood",
    "bayes",
    "truth",
    "evidence",
)
_FORBIDDEN_CLAIM_PHRASES = (
    "family identification",
    "family identified",
    "identified family",
    "geometry detected",
    "detected geometry",
    "morphology compatibility",
    "family ranking",
    "family rank",
    "native validated",
    "native validation",
)
_PROVENANCE_TEXT_KEYS = {
    "source_ref",
    "callable_path",
    "transfer_id",
    "family",
    "normalization",
    "observable_kind",
    "version",
}
_FORBIDDEN_VALUE_KEYS = {
    "value",
    "values",
    "solver_output",
    "solver_values",
    "native_output",
    "native_values",
    "output_values",
    "alm_t",
    "alm_e",
    "alm_b",
    "cl",
    "cls",
    "biposh",
    "template_values",
    "map_t",
    "map_q",
    "map_u",
}


def _is_empty_role_marker(value: object) -> bool:
    return value is False or value is None or (
        isinstance(value, str) and value in {"not_applicable", "none"}
    )


def _jsonable(value: Any) -> Any:
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    raise TypeError(f"metadata value {value!r} is not JSON-compatible")


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(
        _jsonable(payload),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


def _hash_payload(payload: Mapping[str, Any]) -> str:
    encoded = _canonical_json(payload).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _require_non_empty_text(value: object, field_name: str) -> str:
    text = str(value).strip()
    if not text:
        raise ValueError(f"{field_name} must be non-empty")
    return text


def _normalise_hash_list(input_hashes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(input_hashes, (str, bytes)):
        raise ValueError("input_hashes must be a non-string sequence")
    hashes = tuple(str(item).strip() for item in input_hashes)
    if not hashes or any(not item for item in hashes):
        raise ValueError("input_hashes must be non-empty")
    return hashes


def _normalise_caveats(caveats: Sequence[str]) -> tuple[str, ...]:
    if isinstance(caveats, (str, bytes)):
        raise ValueError("caveats must be a non-string sequence")
    normalised = tuple(str(item).strip() for item in caveats)
    if any(not item for item in normalised):
        raise ValueError("caveats must not contain blank items")
    for item in normalised:
        _reject_forbidden_claim_phrase(item)
    return normalised


def _reject_active_role_keys(metadata: Mapping[str, object]) -> None:
    for key, value in metadata.items():
        key_text = str(key).lower()
        if any(term in key_text for term in _FORBIDDEN_ACTIVE_ROLE_TERMS):
            if not _is_empty_role_marker(value):
                raise ValueError(
                    "AtlasEntryLite metadata cannot carry active observed-data "
                    "or inference roles"
                )
        if isinstance(value, Mapping):
            _reject_active_role_keys(value)
        elif isinstance(value, (list, tuple)):
            for item in value:
                if isinstance(item, Mapping):
                    _reject_active_role_keys(item)
                elif isinstance(item, str) and key_text not in _PROVENANCE_TEXT_KEYS:
                    _reject_active_role_value(item)
        elif isinstance(value, str) and key_text not in _PROVENANCE_TEXT_KEYS:
            _reject_active_role_value(value)


def _reject_active_role_value(value: str) -> None:
    text = value.lower()
    if not any(term in text for term in _FORBIDDEN_ACTIVE_ROLE_TERMS):
        return
    if (
        text.startswith(("not_", "not-", "non_", "non-"))
        or "not " in text
        or "_not_" in text
        or "-not-" in text
        or "without" in text
    ):
        return
    raise ValueError(
        "AtlasEntryLite metadata cannot carry active observed-data "
        "or inference roles"
    )


def _reject_forbidden_claim_phrase(value: str) -> None:
    text = value.lower().replace("_", " ").replace("-", " ")
    if not any(phrase in text for phrase in _FORBIDDEN_CLAIM_PHRASES):
        return
    if any(
        marker in text
        for marker in (
            "not ",
            "no ",
            "blocked",
            "pending",
            "without",
            "cannot",
            "must not",
        )
    ):
        return
    raise ValueError(
        "AtlasEntryLite metadata cannot carry family-identification or "
        "morphology-compatibility claim language"
    )


def _reject_claim_phrases_in_fields(metadata: Mapping[str, object]) -> None:
    for value in metadata.values():
        if isinstance(value, str):
            _reject_forbidden_claim_phrase(value)
        elif isinstance(value, Mapping):
            _reject_claim_phrases_in_fields(value)
        elif isinstance(value, (list, tuple)):
            for item in value:
                if isinstance(item, str):
                    _reject_forbidden_claim_phrase(item)
                elif isinstance(item, Mapping):
                    _reject_claim_phrases_in_fields(item)


def _reject_value_bearing_fields(metadata: Mapping[str, object], *, path: str) -> None:
    for key, value in metadata.items():
        key_text = str(key).lower()
        if key_text in _FORBIDDEN_VALUE_KEYS or key_text.endswith("_values"):
            if not _is_empty_role_marker(value):
                raise ValueError(
                    f"{path}.{key} cannot carry solver or observable values"
                )
        if isinstance(value, Mapping):
            _reject_value_bearing_fields(value, path=f"{path}.{key}")
        elif isinstance(value, (list, tuple)):
            for idx, item in enumerate(value):
                if isinstance(item, Mapping):
                    _reject_value_bearing_fields(item, path=f"{path}.{key}[{idx}]")


def _source(metadata: Mapping[str, object]) -> str:
    try:
        return str(metadata["transfer_source"])
    except KeyError as exc:
        raise ValueError("transfer_metadata missing transfer_source") from exc


def _validate_transfer_metadata(metadata: Mapping[str, object]) -> dict[str, object]:
    normalised = _jsonable(metadata)
    if not isinstance(normalised, dict):
        raise TypeError("transfer_metadata must normalize to a mapping")
    source = _source(normalised)
    if source not in _ALLOWED_TRANSFER_SOURCES:
        raise ValueError(
            "AtlasEntryLite supports external/proxy transfer metadata and "
            "schema-only future native metadata only"
        )
    required = {
        "transfer_id",
        "family",
        "valid_range",
        "observable_kind",
        "normalization",
        "calibration_status",
        "caveats",
    }
    missing = sorted(field for field in required if field not in normalised)
    if missing:
        raise ValueError(f"transfer_metadata missing fields: {missing}")
    if not isinstance(normalised["valid_range"], Mapping):
        raise ValueError("transfer_metadata.valid_range must be a mapping")
    if source in _EXTERNAL_SOURCES:
        if normalised.get("native_solver_result") is True:
            raise ValueError("external transfer metadata cannot be native output")
        normalised.setdefault("claim_tier", "conditional")
        normalised.setdefault("production_status", "diagnostic_only")
        normalised.setdefault("transfer_conditional", True)
        normalised.setdefault("native_solver_result", False)
        if normalised.get("claim_tier") != "conditional":
            raise ValueError("external transfer metadata must remain conditional")
        if normalised.get("production_status") != "diagnostic_only":
            raise ValueError("external transfer metadata must remain diagnostic_only")
        if normalised.get("transfer_conditional") is not True:
            raise ValueError("external transfer metadata must be transfer-conditional")
        if normalised.get("native_solver_result") is not False:
            raise ValueError("external transfer metadata cannot be native output")
        gates = tuple(str(item) for item in normalised.get("passed_validation_gates", ()))
        if any("native" in gate.lower() for gate in gates):
            raise ValueError("external transfer metadata cannot claim native gates")
    if source == _NATIVE_SCHEMA_SOURCE:
        if normalised.get("schema_status") != "schema_only_no_solver_output":
            raise ValueError("future native AtlasEntryLite requires schema-only metadata")
        if normalised.get("calibration_status") != "native_provisional":
            raise ValueError("future native AtlasEntryLite must remain provisional")
        gates = tuple(str(item) for item in normalised.get("passed_validation_gates", ()))
        if gates:
            raise ValueError("future native AtlasEntryLite schema cannot carry gates")
        for key in (
            "native_solver_result",
            "returns_values",
            "outputs_available",
            "consumable_as_result",
        ):
            if normalised.get(key) is not False:
                raise ValueError(
                    "future native AtlasEntryLite metadata must remain non-consumable"
                )
        _reject_value_bearing_fields(normalised, path="transfer_metadata")
    _reject_active_role_keys(normalised)
    _reject_claim_phrases_in_fields(normalised)
    return normalised


def _default_entry_caveats(transfer_metadata: Mapping[str, object]) -> tuple[str, ...]:
    source = _source(transfer_metadata)
    caveats = [
        "atlas membership is transfer-provenance metadata only",
        "not an empirical measurement",
        "not model-dependent inference",
        "not morphology compatibility or family identification",
    ]
    if source in _EXTERNAL_SOURCES:
        caveats.append("external-transfer path remains transfer-conditional")
    if source == _NATIVE_SCHEMA_SOURCE:
        caveats.append("future native entry is schema-only with no solver output")
    return tuple(caveats)


@dataclass(frozen=True)
class AtlasEntryLite:
    """Metadata-only BASS atlas row for comparing transfer provenance paths."""

    entry_id: str
    comparison_group: str
    transfer_metadata: Mapping[str, object]
    config_hash: str
    input_hashes: Sequence[str]
    generating_command: str
    git_commit_or_worktree_state: str
    caveats: Sequence[str] = field(default_factory=tuple)
    owner: str = "BASS"
    implementation_scope: str = "bass_py"
    claim_tier: str = "diagnostic_only"
    production_status: str = "diagnostic_only"
    schema_version: str = _SCHEMA_VERSION
    atlas_membership_role: str = "metadata_only_side_by_side_transfer_reference"
    entry_hash: str = field(init=False)

    def __post_init__(self) -> None:
        entry_id = _require_non_empty_text(self.entry_id, "entry_id")
        comparison_group = _require_non_empty_text(
            self.comparison_group,
            "comparison_group",
        )
        transfer_metadata = _validate_transfer_metadata(self.transfer_metadata)
        config_hash = _require_non_empty_text(self.config_hash, "config_hash")
        input_hashes = _normalise_hash_list(self.input_hashes)
        generating_command = _require_non_empty_text(
            self.generating_command,
            "generating_command",
        )
        git_state = _require_non_empty_text(
            self.git_commit_or_worktree_state,
            "git_commit_or_worktree_state",
        )
        caveats = _normalise_caveats(self.caveats)
        if not caveats:
            caveats = _default_entry_caveats(transfer_metadata)
        if self.owner != "BASS":
            raise ValueError("AtlasEntryLite.owner must be BASS")
        if self.implementation_scope != "bass_py":
            raise ValueError("AtlasEntryLite.implementation_scope must be bass_py")
        if self.claim_tier != "diagnostic_only":
            raise ValueError("AtlasEntryLite.claim_tier must be diagnostic_only")
        if self.production_status != "diagnostic_only":
            raise ValueError(
                "AtlasEntryLite.production_status must be diagnostic_only"
            )
        if self.atlas_membership_role != "metadata_only_side_by_side_transfer_reference":
            raise ValueError("AtlasEntryLite atlas membership must remain metadata-only")
        object.__setattr__(self, "entry_id", entry_id)
        object.__setattr__(self, "comparison_group", comparison_group)
        object.__setattr__(self, "transfer_metadata", transfer_metadata)
        object.__setattr__(self, "config_hash", config_hash)
        object.__setattr__(self, "input_hashes", input_hashes)
        object.__setattr__(self, "generating_command", generating_command)
        object.__setattr__(self, "git_commit_or_worktree_state", git_state)
        object.__setattr__(self, "caveats", caveats)
        object.__setattr__(self, "entry_hash", _hash_payload(self._hash_material()))

    @classmethod
    def from_transfer_spec(
        cls,
        spec: TransferFunctionSpec,
        *,
        comparison_group: str,
        config_hash: str,
        input_hashes: Sequence[str],
        generating_command: str,
        git_commit_or_worktree_state: str,
        entry_id: str | None = None,
        caveats: Sequence[str] = (),
    ) -> "AtlasEntryLite":
        if not isinstance(spec, TransferFunctionSpec):
            raise TypeError("from_transfer_spec requires TransferFunctionSpec")
        metadata = spec.to_metadata()
        return cls(
            entry_id=entry_id or f"atlas_lite.{spec.transfer_id}",
            comparison_group=comparison_group,
            transfer_metadata=metadata,
            config_hash=config_hash,
            input_hashes=input_hashes,
            generating_command=generating_command,
            git_commit_or_worktree_state=git_commit_or_worktree_state,
            caveats=caveats,
        )

    def _hash_material(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "entry_id": self.entry_id,
            "comparison_group": self.comparison_group,
            "transfer_metadata": self.transfer_metadata,
            "config_hash": self.config_hash,
            "input_hashes": list(self.input_hashes),
            "generating_command": self.generating_command,
            "git_commit_or_worktree_state": self.git_commit_or_worktree_state,
        }

    @property
    def transfer_id(self) -> str:
        return str(self.transfer_metadata["transfer_id"])

    @property
    def transfer_source(self) -> str:
        return _source(self.transfer_metadata)

    @property
    def is_future_native_schema(self) -> bool:
        return self.transfer_source == _NATIVE_SCHEMA_SOURCE

    @property
    def is_external_or_proxy(self) -> bool:
        return self.transfer_source in _EXTERNAL_SOURCES

    def to_metadata(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "entry_id": self.entry_id,
            "entry_hash": self.entry_hash,
            "owner": self.owner,
            "implementation_scope": self.implementation_scope,
            "claim_tier": self.claim_tier,
            "production_status": self.production_status,
            "atlas_membership_role": self.atlas_membership_role,
            "comparison_group": self.comparison_group,
            "transfer_id": self.transfer_id,
            "transfer_source": self.transfer_source,
            "transfer_family": self.transfer_metadata["family"],
            "family_label_role": "transfer_provenance_only_not_identification",
            "family_identification_status": "blocked_pre_native_morphology_atlas",
            "observable_kind": self.transfer_metadata["observable_kind"],
            "normalization": self.transfer_metadata["normalization"],
            "valid_range": dict(self.transfer_metadata["valid_range"]),
            "transfer_metadata": dict(self.transfer_metadata),
            "atlas_entry_returns_values": False,
            "native_solver_result": False,
            "consumable_as_result": False,
            "consumable_as_observed_data": False,
            "consumable_as_posterior": False,
            "data_role": "metadata_only_not_measurement",
            "inference_role": "not_model_dependent_inference_input",
            "mio_role": "not_mio_certificate",
            "htt_role": "not_htt_evidence",
            "sky_support_status": "not_directional",
            "null_mock_status": "not_statistical",
            "covariance_status": "not_statistical",
            "config_hash": self.config_hash,
            "input_hashes": list(self.input_hashes),
            "generating_command": self.generating_command,
            "git_commit_or_worktree_state": self.git_commit_or_worktree_state,
            "caveats": list(self.caveats),
        }

    def to_observed_data(self) -> None:
        raise RuntimeError("AtlasEntryLite is metadata-only and not observed data")

    def to_posterior_input(self) -> None:
        raise RuntimeError(
            "AtlasEntryLite is metadata-only and not model-dependent inference input"
        )

    def to_evidence_input(self) -> None:
        raise RuntimeError("AtlasEntryLite is metadata-only and not HTT evidence")


@dataclass(frozen=True)
class AtlasTransferComparison:
    """Side-by-side collection of external/proxy and future native atlas entries."""

    comparison_group: str
    entries: Sequence[AtlasEntryLite]
    schema_version: str = _COMPARISON_SCHEMA_VERSION
    owner: str = "BASS"
    implementation_scope: str = "bass_py"
    claim_tier: str = "diagnostic_only"
    production_status: str = "diagnostic_only"
    comparison_role: str = "transfer_provenance_side_by_side_only"

    def __post_init__(self) -> None:
        comparison_group = _require_non_empty_text(
            self.comparison_group,
            "comparison_group",
        )
        entries = tuple(self.entries)
        if not entries:
            raise ValueError("AtlasTransferComparison.entries must be non-empty")
        if any(not isinstance(entry, AtlasEntryLite) for entry in entries):
            raise TypeError("entries must be AtlasEntryLite objects")
        if any(entry.comparison_group != comparison_group for entry in entries):
            raise ValueError("all AtlasEntryLite entries must share comparison_group")
        transfer_ids = [entry.transfer_id for entry in entries]
        if len(set(transfer_ids)) != len(transfer_ids):
            raise ValueError("AtlasTransferComparison transfer_ids must be unique")
        if not any(entry.is_external_or_proxy for entry in entries):
            raise ValueError("comparison requires at least one external/proxy entry")
        if not any(entry.is_future_native_schema for entry in entries):
            raise ValueError("comparison requires at least one future native schema entry")
        if self.owner != "BASS":
            raise ValueError("AtlasTransferComparison.owner must be BASS")
        if self.implementation_scope != "bass_py":
            raise ValueError(
                "AtlasTransferComparison.implementation_scope must be bass_py"
            )
        if self.claim_tier != "diagnostic_only":
            raise ValueError(
                "AtlasTransferComparison.claim_tier must be diagnostic_only"
            )
        if self.production_status != "diagnostic_only":
            raise ValueError(
                "AtlasTransferComparison.production_status must be diagnostic_only"
            )
        object.__setattr__(self, "comparison_group", comparison_group)
        object.__setattr__(self, "entries", entries)

    def to_metadata(self) -> dict[str, object]:
        entry_metadata = [entry.to_metadata() for entry in self.entries]
        return {
            "schema_version": self.schema_version,
            "comparison_group": self.comparison_group,
            "owner": self.owner,
            "implementation_scope": self.implementation_scope,
            "claim_tier": self.claim_tier,
            "production_status": self.production_status,
            "comparison_role": self.comparison_role,
            "entry_count": len(self.entries),
            "transfer_ids": [entry.transfer_id for entry in self.entries],
            "transfer_sources": sorted({entry.transfer_source for entry in self.entries}),
            "external_entry_count": sum(
                1 for entry in self.entries if entry.is_external_or_proxy
            ),
            "future_native_schema_entry_count": sum(
                1 for entry in self.entries if entry.is_future_native_schema
            ),
            "family_identification_status": "blocked_pre_native_morphology_atlas",
            "atlas_membership_role": "metadata_only_side_by_side_transfer_reference",
            "consumable_as_observed_data": False,
            "consumable_as_posterior": False,
            "consumable_as_result": False,
            "entries": entry_metadata,
            "comparison_hash": _hash_payload(
                {
                    "schema_version": self.schema_version,
                    "comparison_group": self.comparison_group,
                    "entries": entry_metadata,
                }
            ),
        }


def entries_from_transfer_registry(
    registry: TransferRegistry,
    *,
    comparison_group: str,
    config_hash: str,
    input_hashes: Sequence[str],
    generating_command: str,
    git_commit_or_worktree_state: str,
) -> tuple[AtlasEntryLite, ...]:
    if not isinstance(registry, TransferRegistry):
        raise TypeError("registry must be TransferRegistry")
    return tuple(
        AtlasEntryLite.from_transfer_spec(
            spec,
            comparison_group=comparison_group,
            config_hash=config_hash,
            input_hashes=input_hashes,
            generating_command=generating_command,
            git_commit_or_worktree_state=git_commit_or_worktree_state,
        )
        for spec in sorted(registry.all(), key=lambda item: item.transfer_id)
    )


def build_default_transfer_side_by_side_comparison(
    *,
    external_registry: TransferRegistry | None = None,
    native_schema: NativeLowEllSchema | None = None,
    comparison_group: str | None = None,
    config_hash: str | None = None,
    input_hashes: Sequence[str] | None = None,
    generating_command: str = _DEFAULT_COMMAND,
    git_commit_or_worktree_state: str | None = None,
) -> AtlasTransferComparison:
    """Return default external/proxy vs future-native transfer metadata entries."""

    if git_commit_or_worktree_state is None:
        raise ValueError(
            "git_commit_or_worktree_state is required for AtlasEntryLite metadata"
        )
    external_registry = external_registry or default_external_transfer_registry()
    native_schema = native_schema or default_native_lowell_schema()
    external_transfer_ids = [spec.transfer_id for spec in external_registry.all()]
    native_transfer_ids = [
        spec.transfer_id for spec in native_schema.to_transfer_registry().all()
    ]
    seed = {
        "external_transfer_ids": sorted(external_transfer_ids),
        "native_transfer_ids": sorted(native_transfer_ids),
        "native_schema": native_schema.to_metadata(),
    }
    resolved_config_hash = config_hash or _hash_payload(seed)
    resolved_input_hashes = input_hashes or (
        _hash_payload({"source": "PR-080", "transfer_ids": sorted(external_transfer_ids)}),
        _hash_payload({"source": "PR-081", "transfer_ids": sorted(native_transfer_ids)}),
    )
    resolved_group = comparison_group or (
        "transfer_side_by_side." + _hash_payload(seed).split(":", 1)[1][:12]
    )
    entries = (
        entries_from_transfer_registry(
            external_registry,
            comparison_group=resolved_group,
            config_hash=resolved_config_hash,
            input_hashes=resolved_input_hashes,
            generating_command=generating_command,
            git_commit_or_worktree_state=git_commit_or_worktree_state,
        )
        + entries_from_transfer_registry(
            native_schema.to_transfer_registry(),
            comparison_group=resolved_group,
            config_hash=resolved_config_hash,
            input_hashes=resolved_input_hashes,
            generating_command=generating_command,
            git_commit_or_worktree_state=git_commit_or_worktree_state,
        )
    )
    return AtlasTransferComparison(
        comparison_group=resolved_group,
        entries=entries,
    )


def validate_atlas_entry_lite_metadata(metadata: Mapping[str, object]) -> None:
    """Fail closed if AtlasEntryLite metadata is treated as data or inference."""

    required = {
        "schema_version",
        "entry_id",
        "entry_hash",
        "owner",
        "implementation_scope",
        "claim_tier",
        "production_status",
        "atlas_membership_role",
        "comparison_group",
        "transfer_id",
        "transfer_source",
        "transfer_family",
        "observable_kind",
        "normalization",
        "valid_range",
        "transfer_metadata",
        "native_solver_result",
        "data_role",
        "inference_role",
        "mio_role",
        "htt_role",
        "family_label_role",
        "family_identification_status",
        "config_hash",
        "input_hashes",
        "sky_support_status",
        "null_mock_status",
        "covariance_status",
        "generating_command",
        "git_commit_or_worktree_state",
        "caveats",
    }
    missing = sorted(field for field in required if field not in metadata)
    if missing:
        raise ValueError(f"AtlasEntryLite metadata missing fields: {missing}")
    if metadata["schema_version"] != _SCHEMA_VERSION:
        raise ValueError("AtlasEntryLite metadata schema_version mismatch")
    if metadata["owner"] != "BASS":
        raise ValueError("AtlasEntryLite metadata owner must be BASS")
    if metadata["implementation_scope"] != "bass_py":
        raise ValueError("AtlasEntryLite metadata implementation_scope must be bass_py")
    if metadata["claim_tier"] != "diagnostic_only":
        raise ValueError("AtlasEntryLite metadata claim_tier must be diagnostic_only")
    if metadata["production_status"] != "diagnostic_only":
        raise ValueError(
            "AtlasEntryLite metadata production_status must be diagnostic_only"
        )
    if metadata.get("atlas_membership_role") != (
        "metadata_only_side_by_side_transfer_reference"
    ):
        raise ValueError("AtlasEntryLite metadata membership role must be metadata-only")
    if metadata.get("atlas_entry_returns_values") is not False:
        raise ValueError("AtlasEntryLite metadata must not return values")
    if metadata.get("native_solver_result") is not False:
        raise ValueError("AtlasEntryLite metadata must not be native solver output")
    expected_roles = {
        "data_role": "metadata_only_not_measurement",
        "inference_role": "not_model_dependent_inference_input",
        "mio_role": "not_mio_certificate",
        "htt_role": "not_htt_evidence",
        "family_label_role": "transfer_provenance_only_not_identification",
        "family_identification_status": "blocked_pre_native_morphology_atlas",
    }
    for key, expected in expected_roles.items():
        if metadata.get(key) != expected:
            raise ValueError(f"AtlasEntryLite metadata {key} must be {expected}")
    for key in (
        "consumable_as_observed_data",
        "consumable_as_posterior",
        "consumable_as_result",
    ):
        if metadata.get(key) is not False:
            raise ValueError("AtlasEntryLite metadata must remain non-consumable")
    _reject_active_role_keys(metadata)
    if not isinstance(metadata["transfer_metadata"], Mapping):
        raise ValueError("AtlasEntryLite transfer_metadata must be a mapping")
    transfer_metadata = _validate_transfer_metadata(metadata["transfer_metadata"])
    projected_transfer_fields = {
        "transfer_id": transfer_metadata["transfer_id"],
        "transfer_source": transfer_metadata["transfer_source"],
        "transfer_family": transfer_metadata["family"],
        "observable_kind": transfer_metadata["observable_kind"],
        "normalization": transfer_metadata["normalization"],
        "valid_range": transfer_metadata["valid_range"],
    }
    for field_name, expected in projected_transfer_fields.items():
        if _jsonable(metadata[field_name]) != expected:
            raise ValueError(
                f"AtlasEntryLite metadata {field_name} must match transfer_metadata"
            )


__all__ = [
    "AtlasEntryLite",
    "AtlasTransferComparison",
    "build_default_transfer_side_by_side_comparison",
    "entries_from_transfer_registry",
    "validate_atlas_entry_lite_metadata",
]
