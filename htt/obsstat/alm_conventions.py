"""Harmonic coefficient convention metadata for OBSSTAT features.

OBSSTAT packages observer-side features.  This module records the basis and
storage conventions needed to interpret alms; it does not compute likelihoods,
posterior evidence, MIO certificates, or Bianchi family labels.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import hashlib
import json
import math
from typing import Any

import numpy as np

REQUIRED_CONVENTION_FIELDS = (
    "metadata_schema",
    "basis",
    "normalization",
    "phase_convention",
    "theta_phi_convention",
    "harmonic_evaluator",
    "evaluator_provenance",
    "coordinate_frame",
    "alm_storage",
    "reality_condition",
    "spin_weight",
    "spin_transform",
    "polarization_basis",
    "paired_map_order",
    "spin_output_convention",
    "eb_sign_convention",
    "lmax",
    "mmax",
    "claim_scope",
)

_ALLOWED_BASIS = {
    "complex_spherical_harmonic",
    "spin_weighted_spherical_harmonic",
}
_ALLOWED_NORMALIZATION = {"orthonormal_4pi"}
_ALLOWED_PHASE = {
    "condon_shortley_included",
    "condon_shortley_excluded",
}
_ALLOWED_THETA_PHI = {
    "theta_colatitude_phi_longitude",
    "theta_longitude_phi_colatitude",
}
_ALLOWED_HARMONIC_EVALUATOR = {
    "scipy.special.sph_harm_y",
    "not_applicable",
}
_ALLOWED_EVALUATOR_PROVENANCE = {
    "scipy_sph_harm_y_docs_current_theta_colatitude_phi_longitude",
    "healpy_map2alm_spin_docs_current_paired_maps",
}
_ALLOWED_COORDINATE_FRAME = {
    "galactic",
    "icrs",
    "ecliptic",
    "cmb",
}
_ALLOWED_ALM_STORAGE = {
    "healpy_m_major_l_minor",
    "dense_l_major_m_minor",
    "indexed_l_m_pairs",
}
_ALLOWED_REALITY = {
    "real_scalar_map",
    "complex_scalar_map",
    "spin_pair_q_u",
    "not_applicable",
}
_ALLOWED_SPIN_TRANSFORM = {
    "not_applicable",
    "healpy_map2alm_spin",
    "external_spin_transform",
}
_ALLOWED_POLARIZATION_BASIS = {
    "not_applicable",
    "IAU_Q_U",
    "COSMO_Q_U",
}
_ALLOWED_PAIRED_MAP_ORDER = {
    "not_applicable",
    "Q_then_U",
}
_ALLOWED_SPIN_OUTPUT_CONVENTION = {
    "not_applicable",
    "healpy_return_pair_unlabeled_spin_alms",
}
_ALLOWED_EB_SIGN_CONVENTION = {
    "not_applicable",
    "not_declared_no_eb_export",
}
_SCHEMA_VERSION = "obsstat.alm_convention.v1"
_CLAIM_SCOPE = "observable_feature_convention"
_DIAGNOSTIC_CAVEAT = (
    "harmonic convention metadata only; no inference or family identification"
)
_ALM_PAYLOAD_KEYS = {
    "alm",
    "alms",
    "a_lm",
    "coefficients",
    "coefficient_hash",
    "lmax",
    "mmax",
    "spin_weight",
    "convention",
}


@dataclass(frozen=True)
class AlmConvention:
    """Machine-checkable convention metadata for an alm feature block."""

    basis: str
    normalization: str
    phase_convention: str
    theta_phi_convention: str
    harmonic_evaluator: str
    evaluator_provenance: str
    coordinate_frame: str
    alm_storage: str
    reality_condition: str
    spin_weight: int
    spin_transform: str
    polarization_basis: str
    paired_map_order: str
    spin_output_convention: str
    eb_sign_convention: str
    lmax: int
    mmax: int | None = None
    metadata_schema: str = _SCHEMA_VERSION
    claim_scope: str = _CLAIM_SCOPE
    caveats: tuple[str, ...] = (_DIAGNOSTIC_CAVEAT,)

    def __post_init__(self) -> None:
        validate_alm_convention_metadata(self.to_metadata())

    def to_metadata(self) -> dict[str, Any]:
        """Return JSON-like metadata suitable for manifests and feature blocks."""

        return {
            "metadata_schema": self.metadata_schema,
            "basis": self.basis,
            "normalization": self.normalization,
            "phase_convention": self.phase_convention,
            "theta_phi_convention": self.theta_phi_convention,
            "harmonic_evaluator": self.harmonic_evaluator,
            "evaluator_provenance": self.evaluator_provenance,
            "coordinate_frame": self.coordinate_frame,
            "alm_storage": self.alm_storage,
            "reality_condition": self.reality_condition,
            "spin_weight": int(self.spin_weight),
            "spin_transform": self.spin_transform,
            "polarization_basis": self.polarization_basis,
            "paired_map_order": self.paired_map_order,
            "spin_output_convention": self.spin_output_convention,
            "eb_sign_convention": self.eb_sign_convention,
            "lmax": int(self.lmax),
            "mmax": None if self.mmax is None else int(self.mmax),
            "claim_scope": self.claim_scope,
            "caveats": list(self.caveats),
        }


def canonical_temperature_alm_convention(
    *,
    lmax: int,
    mmax: int | None = None,
    coordinate_frame: str = "galactic",
) -> AlmConvention:
    """Return the repo's default scalar-temperature harmonic metadata.

    The defaults match the documented SciPy/healpy convention used by current
    test and packaging paths: orthonormal complex spherical harmonics with
    Condon-Shortley phase, theta as colatitude, phi as longitude, and healpy's
    m-major alm storage.
    """

    return AlmConvention(
        basis="complex_spherical_harmonic",
        normalization="orthonormal_4pi",
        phase_convention="condon_shortley_included",
        theta_phi_convention="theta_colatitude_phi_longitude",
        harmonic_evaluator="scipy.special.sph_harm_y",
        evaluator_provenance=(
            "scipy_sph_harm_y_docs_current_theta_colatitude_phi_longitude"
        ),
        coordinate_frame=coordinate_frame,
        alm_storage="healpy_m_major_l_minor",
        reality_condition="real_scalar_map",
        spin_weight=0,
        spin_transform="not_applicable",
        polarization_basis="not_applicable",
        paired_map_order="not_applicable",
        spin_output_convention="not_applicable",
        eb_sign_convention="not_applicable",
        lmax=lmax,
        mmax=mmax,
    )


def canonical_spin2_alm_convention(
    *,
    lmax: int,
    mmax: int | None = None,
    coordinate_frame: str = "galactic",
    polarization_basis: str = "IAU_Q_U",
) -> AlmConvention:
    """Return metadata for paired spin-2 Q/U harmonic packaging."""

    return AlmConvention(
        basis="spin_weighted_spherical_harmonic",
        normalization="orthonormal_4pi",
        phase_convention="condon_shortley_included",
        theta_phi_convention="theta_colatitude_phi_longitude",
        harmonic_evaluator="scipy.special.sph_harm_y",
        evaluator_provenance="healpy_map2alm_spin_docs_current_paired_maps",
        coordinate_frame=coordinate_frame,
        alm_storage="healpy_m_major_l_minor",
        reality_condition="spin_pair_q_u",
        spin_weight=2,
        spin_transform="healpy_map2alm_spin",
        polarization_basis=polarization_basis,
        paired_map_order="Q_then_U",
        spin_output_convention="healpy_return_pair_unlabeled_spin_alms",
        eb_sign_convention="not_declared_no_eb_export",
        lmax=lmax,
        mmax=mmax,
    )


def validate_alm_convention_metadata(metadata: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and return normalized convention metadata."""

    if not isinstance(metadata, Mapping):
        raise ValueError("convention_metadata must be a mapping")
    allowed_fields = set(REQUIRED_CONVENTION_FIELDS) | {"caveats"}
    unknown = sorted(str(field) for field in metadata if field not in allowed_fields)
    if unknown:
        raise ValueError(
            "convention_metadata unknown field(s): " + ", ".join(unknown)
        )
    missing = [field for field in REQUIRED_CONVENTION_FIELDS if field not in metadata]
    if missing:
        raise ValueError(
            "convention_metadata missing required field(s): " + ", ".join(missing)
        )
    normalized = dict(metadata)
    _require_value(
        normalized,
        "metadata_schema",
        {_SCHEMA_VERSION},
        "metadata_schema",
    )
    _require_value(normalized, "basis", _ALLOWED_BASIS, "basis")
    _require_value(
        normalized,
        "normalization",
        _ALLOWED_NORMALIZATION,
        "normalization",
    )
    _require_value(
        normalized,
        "phase_convention",
        _ALLOWED_PHASE,
        "phase_convention",
    )
    _require_value(
        normalized,
        "theta_phi_convention",
        _ALLOWED_THETA_PHI,
        "theta_phi_convention",
    )
    _require_value(
        normalized,
        "harmonic_evaluator",
        _ALLOWED_HARMONIC_EVALUATOR,
        "harmonic_evaluator",
    )
    _require_value(
        normalized,
        "evaluator_provenance",
        _ALLOWED_EVALUATOR_PROVENANCE,
        "evaluator_provenance",
    )
    _require_value(
        normalized,
        "coordinate_frame",
        _ALLOWED_COORDINATE_FRAME,
        "coordinate_frame",
    )
    _require_value(normalized, "alm_storage", _ALLOWED_ALM_STORAGE, "alm_storage")
    _require_value(
        normalized,
        "reality_condition",
        _ALLOWED_REALITY,
        "reality_condition",
    )
    _require_value(
        normalized,
        "spin_transform",
        _ALLOWED_SPIN_TRANSFORM,
        "spin_transform",
    )
    _require_value(
        normalized,
        "polarization_basis",
        _ALLOWED_POLARIZATION_BASIS,
        "polarization_basis",
    )
    _require_value(
        normalized,
        "paired_map_order",
        _ALLOWED_PAIRED_MAP_ORDER,
        "paired_map_order",
    )
    _require_value(
        normalized,
        "spin_output_convention",
        _ALLOWED_SPIN_OUTPUT_CONVENTION,
        "spin_output_convention",
    )
    _require_value(
        normalized,
        "eb_sign_convention",
        _ALLOWED_EB_SIGN_CONVENTION,
        "eb_sign_convention",
    )
    _require_value(normalized, "claim_scope", {_CLAIM_SCOPE}, "claim_scope")
    spin_weight = _require_int(normalized["spin_weight"], "spin_weight")
    lmax = _require_int(normalized["lmax"], "lmax")
    if lmax < 0:
        raise ValueError("lmax must be non-negative")
    if normalized["mmax"] is not None:
        mmax = _require_int(normalized["mmax"], "mmax")
        if mmax < 0 or mmax > lmax:
            raise ValueError("mmax must be between 0 and lmax")
    if spin_weight == 0:
        _validate_scalar_convention(normalized)
    else:
        _validate_spin_convention(normalized, spin_weight)
    caveats = normalized.get("caveats", ())
    if isinstance(caveats, str) or not isinstance(caveats, Sequence):
        raise ValueError("convention_metadata caveats must be a sequence")
    return normalized


def build_alm_feature(
    *,
    channel: str,
    coefficients: Sequence[Any],
    convention: AlmConvention | Mapping[str, Any],
    provenance: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Package alm coefficients with validated convention metadata."""

    if not isinstance(channel, str) or not channel:
        raise ValueError("alm feature channel must be a non-empty string")
    metadata = _metadata_from_convention(convention)
    coefficient_payload = _json_ready(coefficients)
    _validate_coefficient_payload_shape(coefficient_payload, metadata)
    return {
        "channel": channel,
        "coefficients": coefficient_payload,
        "coefficient_hash": _sha256_payload(
            {
                "channel": channel,
                "coefficients": coefficient_payload,
                "convention_metadata": metadata,
            }
        ),
        "convention_metadata": metadata,
        "claim_tier": "diagnostic_only",
        "provenance": dict(provenance or {}),
    }


def validate_alm_feature_conventions(
    alm_features: Mapping[str, Any] | None,
) -> tuple[dict[str, Any], ...]:
    """Require convention metadata on alm-like feature nodes."""

    if not alm_features:
        return tuple()
    if not isinstance(alm_features, Mapping):
        raise ValueError("alm_features must be a mapping")
    collected: list[dict[str, Any]] = []
    _validate_alm_feature_node(alm_features, path="alm_features", collected=collected)
    return tuple(collected)


def _validate_alm_feature_node(
    node: Mapping[str, Any],
    *,
    path: str,
    collected: list[dict[str, Any]],
) -> None:
    metadata_present = "convention_metadata" in node
    if metadata_present:
        collected.append(validate_alm_convention_metadata(node["convention_metadata"]))
    node_has_metadata = metadata_present
    if _looks_like_alm_payload(node) and not node_has_metadata:
        raise ValueError(
            f"{path} carries harmonic coefficients or limits and requires "
            "convention_metadata"
        )
    for key, value in node.items():
        if key == "convention_metadata":
            continue
        if isinstance(value, Mapping):
            _validate_alm_feature_node(
                value,
                path=f"{path}.{key}",
                collected=collected,
            )


def _looks_like_alm_payload(node: Mapping[str, Any]) -> bool:
    keys = {str(key).lower() for key in node}
    return bool(keys.intersection(_ALM_PAYLOAD_KEYS))


def _metadata_from_convention(
    convention: AlmConvention | Mapping[str, Any],
) -> dict[str, Any]:
    if isinstance(convention, AlmConvention):
        return convention.to_metadata()
    return validate_alm_convention_metadata(convention)


def _validate_scalar_convention(metadata: Mapping[str, Any]) -> None:
    if metadata["basis"] != "complex_spherical_harmonic":
        raise ValueError("spin_weight=0 requires complex_spherical_harmonic basis")
    if metadata["spin_transform"] != "not_applicable":
        raise ValueError("spin_weight=0 requires spin_transform='not_applicable'")
    if metadata["polarization_basis"] != "not_applicable":
        raise ValueError("spin_weight=0 requires polarization_basis='not_applicable'")
    if metadata["paired_map_order"] != "not_applicable":
        raise ValueError("spin_weight=0 requires paired_map_order='not_applicable'")
    if metadata["spin_output_convention"] != "not_applicable":
        raise ValueError(
            "spin_weight=0 requires spin_output_convention='not_applicable'"
        )
    if metadata["eb_sign_convention"] != "not_applicable":
        raise ValueError(
            "spin_weight=0 requires eb_sign_convention='not_applicable'"
        )
    if metadata["reality_condition"] not in {"real_scalar_map", "complex_scalar_map"}:
        raise ValueError(
            "spin_weight=0 requires scalar-map reality_condition metadata"
        )


def _validate_spin_convention(
    metadata: Mapping[str, Any],
    spin_weight: int,
) -> None:
    if metadata["basis"] != "spin_weighted_spherical_harmonic":
        raise ValueError(
            "non-zero spin_weight requires spin_weighted_spherical_harmonic basis"
        )
    if metadata["spin_transform"] == "not_applicable":
        raise ValueError("non-zero spin_weight requires spin_transform metadata")
    if metadata["polarization_basis"] == "not_applicable":
        raise ValueError("non-zero spin_weight requires polarization_basis metadata")
    if metadata["paired_map_order"] == "not_applicable":
        raise ValueError("non-zero spin_weight requires paired_map_order metadata")
    if metadata["spin_output_convention"] == "not_applicable":
        raise ValueError(
            "non-zero spin_weight requires spin_output_convention metadata"
        )
    if metadata["eb_sign_convention"] == "not_applicable":
        raise ValueError("non-zero spin_weight requires eb_sign_convention metadata")
    if metadata["reality_condition"] not in {"spin_pair_q_u", "not_applicable"}:
        raise ValueError(
            "non-zero spin_weight requires spin-pair reality_condition metadata"
        )
    if abs(spin_weight) > metadata["lmax"]:
        raise ValueError("|spin_weight| cannot exceed lmax")


def _require_value(
    metadata: Mapping[str, Any],
    field: str,
    allowed: set[str],
    label: str,
) -> None:
    value = metadata[field]
    if not isinstance(value, str) or value not in allowed:
        raise ValueError(
            f"{label} must be one of {sorted(allowed)}; got {value!r}"
        )


def _require_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field} must be an integer")
    return value


def _sha256_payload(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _validate_coefficient_payload_shape(
    coefficients: Any,
    metadata: Mapping[str, Any],
) -> None:
    storage = metadata["alm_storage"]
    if storage != "healpy_m_major_l_minor":
        return
    expected = _healpy_alm_size(int(metadata["lmax"]), metadata["mmax"])
    spin_weight = int(metadata["spin_weight"])
    if spin_weight == 0:
        if not _is_sequence_like(coefficients) or len(coefficients) != expected:
            raise ValueError(
                "scalar alm coefficients for healpy_m_major_l_minor storage "
                f"must contain {expected} entries"
            )
        return
    if (
        not _is_sequence_like(coefficients)
        or len(coefficients) != 2
        or any(
            not _is_sequence_like(component) or len(component) != expected
            for component in coefficients
        )
    ):
        raise ValueError(
            "spin alm coefficients for healpy_m_major_l_minor storage must be "
            f"a pair of arrays with {expected} entries each"
        )


def _healpy_alm_size(lmax: int, mmax: Any) -> int:
    effective_mmax = lmax if mmax is None else int(mmax)
    return (effective_mmax + 1) * (lmax + 1) - (
        effective_mmax * (effective_mmax + 1)
    ) // 2


def _is_sequence_like(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes))


def _json_ready(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return _json_ready(value.tolist())
    if isinstance(value, np.generic):
        return _json_ready(value.item())
    if isinstance(value, Mapping):
        return {str(key): _json_ready(child) for key, child in value.items()}
    if isinstance(value, complex):
        if not math.isfinite(value.real) or not math.isfinite(value.imag):
            raise ValueError("complex alm coefficients must be finite")
        return {"real": value.real, "imag": value.imag}
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("alm coefficients must be finite")
        return value
    if isinstance(value, tuple):
        return [_json_ready(child) for child in value]
    if isinstance(value, list):
        return [_json_ready(child) for child in value]
    return value


__all__ = [
    "AlmConvention",
    "REQUIRED_CONVENTION_FIELDS",
    "build_alm_feature",
    "canonical_spin2_alm_convention",
    "canonical_temperature_alm_convention",
    "validate_alm_convention_metadata",
    "validate_alm_feature_conventions",
]
