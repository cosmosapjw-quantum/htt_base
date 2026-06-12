"""OBSSTAT ObservableVector facade.

This module intentionally reuses the canonical ``common.contracts`` data
classes.  OBSSTAT owns feature extraction and descriptive feature packaging;
it does not own likelihoods, posterior evidence, MIO certificates, or family
identification.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from common.contracts import (
    ArtifactManifest,
    ClaimTier,
    ImplementationScope,
    ObservableVector,
    Owner,
    SkySupport,
    normalize_owner,
)
from common.transfer_registry import TransferSource, validate_transfer_dependent_result

from .alm_conventions import validate_alm_feature_conventions

_FORBIDDEN_FEATURE_KEY_PARTS = (
    "posterior",
    "likelihood",
    "evidence",
    "bayes",
    "ln_b",
    "miocertificate",
    "mio_certificate",
    "mio_cert",
    "certificate",
    "truth",
)
_FAMILY_ID_KEY_PARTS = (
    "family_identification",
    "family_identified",
    "geometry_detected",
    "geometry_detection",
    "family_ranking",
    "identified_family",
    "identified_geometry",
    "detected_geometry",
    "family_rank",
    "geometry_rank",
    "ranked_geometry",
    "bianchi_geometry",
)
_FAMILY_ID_CONTEXT_PARTS = ("identification", "identified", "detect", "rank")
_CLAIM_GEOMETRY_KEY_PARTS = ("geometry", "bianchi")
_NULL_PVALUE_KEY_PARTS = ("p_value", "pvalue")
_NULL_METADATA_FIELDS = ("null_ensemble_ref", "look_elsewhere_status")
_LOOK_ELSEWHERE_ALLOWED_STATUSES = {
    "tracked",
    "look_elsewhere_tracked",
    "corrected",
    "look_elsewhere_corrected",
    "global_corrected",
    "documented",
}
_TRANSFER_METADATA_FIELDS = (
    "transfer_source",
    "family",
    "valid_range",
    "observable_kind",
    "normalization",
    "calibration_status",
    "caveats",
    "source_ref",
    "version",
    "passed_validation_gates",
    "passed_gates",
)
_NATIVE_VALIDATION_GATES = {"native_transfer_validated", "native_solver_validation"}
_FORBIDDEN_VALUE_PHRASES = (
    "bianchi family identified",
    "family identified",
    "identified family",
    "identified as",
    "geometry detected",
    "detected geometry",
    "family ranking",
    "family rank",
)


def obsstat_manifest(
    *,
    artifact_id: str,
    artifact_path: str,
    config_hash: str,
    input_hashes: list[str],
    git_commit: str | None = None,
    caveats: list[str] | None = None,
    statistics_definitions: Mapping[str, Any] | None = None,
) -> ArtifactManifest:
    """Build an OBSSTAT-owned diagnostic-only manifest."""

    return ArtifactManifest(
        artifact_id=artifact_id,
        artifact_path=artifact_path,
        owner=Owner.OBSSTAT,
        implementation_scope=ImplementationScope.OBSSTAT,
        claim_tier=ClaimTier.DIAGNOSTIC_ONLY,
        production_status="diagnostic_only",
        created_by="htt.obsstat.observable_vector",
        git_commit=git_commit,
        config_hash=config_hash,
        input_hashes=list(input_hashes),
        code_version="pr-070",
        schema_version="obsstat.observable_vector.v1",
        caveats=list(caveats or ["diagnostic feature extraction only"]),
        statistics_definitions=dict(statistics_definitions or {}),
    )


def build_observable_vector(
    *,
    ell_max: int,
    channels: tuple[str, ...],
    cl: Mapping[str, Any] | None = None,
    alm_features: Mapping[str, Any] | None = None,
    template_features: Mapping[str, Any] | None = None,
    covariance_features: Mapping[str, Any] | None = None,
    scalar_features: Mapping[str, Any] | None = None,
    morphology_features: Mapping[str, Any] | None = None,
    null_features: Mapping[str, Any] | None = None,
    biposh_features: Mapping[str, Any] | None = None,
    scan_volume: Mapping[str, Any] | None = None,
    sky_support: SkySupport,
    manifest: ArtifactManifest,
) -> ObservableVector:
    """Build the canonical ObservableVector from OBSSTAT feature blocks."""

    _require_obsstat_manifest(manifest)
    blocks = {
        "alm": dict(alm_features or {}),
        "scalar_features": dict(scalar_features or {}),
        "morphology_features": dict(morphology_features or {}),
        "null_features": dict(null_features or {}),
    }
    alm_convention_metadata = validate_alm_feature_conventions(blocks["alm"])
    _require_alm_coordinate_frame_match(alm_convention_metadata, sky_support)
    _reject_forbidden_feature_keys(blocks)
    template_payload = dict(template_features or {})
    covariance_payload = dict(covariance_features or {})
    biposh_payload = dict(biposh_features or {})
    all_features = {
        **blocks,
        "template_features": template_payload,
        "covariance_features": covariance_payload,
        "biposh_features": biposh_payload,
    }
    _require_null_provenance(all_features)
    _reject_forbidden_feature_keys(
        {
            "template_features": template_payload,
            "covariance_features": covariance_payload,
            "biposh_features": biposh_payload,
        }
    )
    _require_transfer_metadata(all_features)
    _require_channel_names(channels)
    return ObservableVector(
        ell_max=int(ell_max),
        channels=tuple(channels),
        cl=dict(cl or {}),
        alm_features=blocks,
        biposh=biposh_payload or None,
        template_fit=template_payload or None,
        covariance_features=covariance_payload or None,
        scan_volume=dict(scan_volume or {}),
        sky_support=sky_support,
        manifest=manifest,
    )


def _require_obsstat_manifest(manifest: ArtifactManifest) -> None:
    if normalize_owner(manifest.owner) is not Owner.OBSSTAT:
        raise ValueError("ObservableVector requires an OBSSTAT-owned manifest")
    if manifest.implementation_scope is not ImplementationScope.OBSSTAT:
        raise ValueError(
            "ObservableVector requires implementation_scope='obsstat'"
        )
    if manifest.claim_tier is not ClaimTier.DIAGNOSTIC_ONLY:
        raise ValueError("ObservableVector requires diagnostic_only claim tier")


def _reject_forbidden_feature_keys(payload: Mapping[str, Any]) -> None:
    for path in _walk_keys(payload):
        lower = path.lower()
        if _is_family_identification_key(lower):
            raise ValueError(
                "ObservableVector morphology features cannot make a family "
                "identification claim"
            )
        if _is_forbidden_inference_key(lower):
            raise ValueError(f"forbidden inference key in ObservableVector: {path}")
    for path, value in _walk_string_values(payload):
        lower_value = value.lower()
        if any(phrase in lower_value for phrase in _FORBIDDEN_VALUE_PHRASES):
            raise ValueError(
                "ObservableVector feature values cannot make a family "
                f"identification claim: {path}"
            )


def _is_family_identification_key(lower_path: str) -> bool:
    if any(part in lower_path for part in _FAMILY_ID_KEY_PARTS):
        return True
    has_family_context = "family" in lower_path and any(
        part in lower_path for part in _FAMILY_ID_CONTEXT_PARTS
    )
    has_geometry_context = any(
        part in lower_path for part in _CLAIM_GEOMETRY_KEY_PARTS
    ) and any(
        part in lower_path for part in _FAMILY_ID_CONTEXT_PARTS
    )
    return has_family_context or has_geometry_context


def _is_forbidden_inference_key(lower_path: str) -> bool:
    if any(part in lower_path for part in _FORBIDDEN_FEATURE_KEY_PARTS):
        return True
    components = lower_path.replace("_", ".").split(".")
    return "mio" in components and any(
        component in {"cert", "certificate"} for component in components
    )


def _require_null_provenance(payload: Mapping[str, Any]) -> None:
    pvalue_paths = tuple(
        path
        for path in _walk_keys(payload)
        if any(part in path.lower() for part in _NULL_PVALUE_KEY_PARTS)
    )
    if not pvalue_paths:
        return
    null_ref = _payload_value_for_key(payload, "null_ensemble_ref")
    if not null_ref:
        raise ValueError("null p-value features require null_ensemble_ref")
    if not isinstance(null_ref, str) or not null_ref.strip():
        raise ValueError("null_ensemble_ref must be a non-empty string")
    look_elsewhere_status = _payload_value_for_key(payload, "look_elsewhere_status")
    if look_elsewhere_status is None:
        raise ValueError("null p-value features require look_elsewhere_status")
    if not isinstance(look_elsewhere_status, str):
        raise ValueError("look_elsewhere_status must be a string")
    if look_elsewhere_status.strip().lower() not in _LOOK_ELSEWHERE_ALLOWED_STATUSES:
        raise ValueError(
            "look_elsewhere_status must document tracked or corrected null "
            "look-elsewhere provenance"
        )


def _require_transfer_metadata(features: Mapping[str, Any]) -> None:
    _require_transfer_metadata_recursive(features, inherited={}, path="features")


def _require_transfer_metadata_recursive(
    features: Mapping[str, Any],
    *,
    inherited: Mapping[str, Any],
    path: str,
) -> None:
    metadata = _merge_transfer_metadata(inherited, features)
    if features.get("transfer_derived"):
        if "transfer_source" not in metadata:
            raise ValueError(
                "transfer-derived OBSSTAT features require transfer_source"
            )
        _validate_transfer_metadata(metadata, path)
    for key, value in features.items():
        if isinstance(value, Mapping):
            child_path = f"{path}.{key}"
            _require_transfer_metadata_recursive(
                value,
                inherited=metadata,
                path=child_path,
            )


def _merge_transfer_metadata(
    inherited: Mapping[str, Any],
    features: Mapping[str, Any],
) -> dict[str, Any]:
    metadata = dict(inherited)
    for key in _TRANSFER_METADATA_FIELDS:
        if key in features:
            metadata[key] = features[key]
    return metadata


def _validate_transfer_metadata(metadata: Mapping[str, Any], path: str) -> None:
    source_value = str(metadata.get("transfer_source", ""))
    if source_value == "native_solver":
        _raise_native_transfer_without_gate(path)
    try:
        source = TransferSource(source_value)
    except ValueError as exc:
        raise ValueError(
            f"unknown transfer_source for OBSSTAT features at {path}: {source_value!r}"
        ) from exc
    if source is TransferSource.NONE:
        raise ValueError(
            f"transfer-derived OBSSTAT features at {path} require a non-none "
            "transfer_source"
        )
    gates = _transfer_validation_gates(metadata)
    if source in {
        TransferSource.BASS_NATIVE_PROVISIONAL,
        TransferSource.BASS_NATIVE_VALIDATED,
    } and not _NATIVE_VALIDATION_GATES.intersection(gates):
        _raise_native_transfer_without_gate(path)
    registry_metadata = dict(metadata)
    if "passed_gates" in registry_metadata:
        registry_metadata.setdefault(
            "passed_validation_gates",
            registry_metadata["passed_gates"],
        )
    validate_transfer_dependent_result(registry_metadata)


def _transfer_validation_gates(metadata: Mapping[str, Any]) -> set[str]:
    raw_gates = metadata.get(
        "passed_validation_gates",
        metadata.get("passed_gates", ()),
    )
    if isinstance(raw_gates, (str, bytes)):
        return {str(raw_gates)}
    try:
        return {str(gate) for gate in raw_gates}
    except TypeError:
        return set()


def _raise_native_transfer_without_gate(path: str) -> None:
    raise ValueError(
        "native transfer source for OBSSTAT features at "
        f"{path} requires native_transfer_validated or native_solver_validation gate"
    )


def _require_channel_names(channels: tuple[str, ...]) -> None:
    if any(not isinstance(channel, str) or not channel for channel in channels):
        raise ValueError("ObservableVector channels must be non-empty strings")


def _require_alm_coordinate_frame_match(
    convention_metadata: tuple[dict[str, Any], ...],
    sky_support: SkySupport,
) -> None:
    sky_frame = str(sky_support.coordinate_frame).strip().lower()
    for metadata in convention_metadata:
        alm_frame = str(metadata["coordinate_frame"]).strip().lower()
        if alm_frame != sky_frame:
            raise ValueError(
                "alm convention coordinate_frame must match SkySupport.coordinate_frame "
                f"({alm_frame!r} != {sky_frame!r})"
            )


def _walk_keys(payload: Mapping[str, Any], prefix: str = "") -> tuple[str, ...]:
    keys: list[str] = []
    for key, value in payload.items():
        path = f"{prefix}.{key}" if prefix else str(key)
        keys.append(path)
        if isinstance(value, Mapping):
            keys.extend(_walk_keys(value, path))
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
        elif isinstance(value, str):
            values.append((path, value))
    return tuple(values)


def _payload_value_for_key(payload: Mapping[str, Any], wanted: str) -> Any | None:
    wanted_lower = wanted.lower()
    for key, value in payload.items():
        if str(key).lower() == wanted_lower:
            return value
        if isinstance(value, Mapping):
            nested = _payload_value_for_key(value, wanted)
            if nested is not None:
                return nested
    return None


__all__ = [
    "ObservableVector",
    "build_observable_vector",
    "obsstat_manifest",
]
