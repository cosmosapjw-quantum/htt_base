"""Sky-support provenance helpers for directional artifacts.

This module builds on :class:`common.contracts.SkySupport` without redefining
the schema. It provides deterministic mask/support hashes and validation for
sky-facing metadata surfaces that need coordinate-frame, sky-fraction, and
completeness provenance before downstream HTT/MIO/BASS consumers can promote
them.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np

from common.contracts import SkySupport

__all__ = [
    "mask_hash_from_array",
    "sky_fraction_from_mask",
    "build_sky_support_from_mask",
    "validate_sky_facing_artifact_metadata",
]


_SKY_SUPPORT_REQUIRED_FIELDS = (
    "coordinate_frame",
    "mask_hash",
    "sky_support_hash",
    "sky_fraction",
    "completeness_status",
)
_ALLOWED_SKY_FACING_STATUSES = {
    "directional",
    "full_sky",
    "partial_sky",
    "masked_sky",
    "coordinate_frame_annotated",
    "sky_support_recorded",
}


def _require_nonempty_string(value: object, field_name: str) -> str:
    text = str(value).strip() if value is not None else ""
    if not text:
        raise ValueError(f"{field_name} must be non-empty")
    return text


def _mask_bool_1d(mask: object) -> np.ndarray:
    arr = np.asarray(mask, dtype=bool)
    if arr.ndim != 1:
        raise ValueError("sky-support mask must be 1-D")
    if arr.size == 0:
        raise ValueError("sky-support mask must be non-empty")
    return arr


def _json_hash(payload: Mapping[str, Any], *, prefix: str = "sha256") -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return f"{prefix}:{hashlib.sha256(encoded).hexdigest()}"


def mask_hash_from_array(
    mask: object,
    *,
    coordinate_frame: str,
    pixelization: str,
    nside: int | None = None,
) -> str:
    """Return a deterministic SHA-256 hash for a 1-D mask and frame metadata."""

    arr = _mask_bool_1d(mask)
    frame = _require_nonempty_string(coordinate_frame, "coordinate_frame")
    pixelization_text = _require_nonempty_string(pixelization, "pixelization")
    if nside is not None and int(nside) <= 0:
        raise ValueError("nside must be positive when provided")
    payload = {
        "coordinate_frame": frame,
        "pixelization": pixelization_text,
        "nside": int(nside) if nside is not None else None,
        "mask_length": int(arr.size),
        "mask_bits": arr.astype(np.uint8).tolist(),
    }
    return _json_hash(payload)


def sky_fraction_from_mask(mask: object) -> float:
    """Return the equal-area sky fraction kept by a boolean mask."""

    arr = _mask_bool_1d(mask)
    return float(arr.mean())


def build_sky_support_from_mask(
    mask: object,
    *,
    coordinate_frame: str,
    completeness_status: str,
    selection_mode: str,
    mock_coverage_status: str,
    pixelization: str,
    nside: int | None = None,
    scan_volume_hash: str = "",
) -> SkySupport:
    """Construct canonical sky-support metadata from an equal-area mask."""

    frame = _require_nonempty_string(coordinate_frame, "coordinate_frame")
    completeness = _require_nonempty_string(
        completeness_status,
        "completeness_status",
    )
    selection = _require_nonempty_string(selection_mode, "selection_mode")
    mock_status = _require_nonempty_string(
        mock_coverage_status,
        "mock_coverage_status",
    )
    pixelization_text = _require_nonempty_string(pixelization, "pixelization")
    fraction = sky_fraction_from_mask(mask)
    mask_hash = mask_hash_from_array(
        mask,
        coordinate_frame=frame,
        pixelization=pixelization_text,
        nside=nside,
    )
    support_payload = {
        "coordinate_frame": frame,
        "sky_fraction": fraction,
        "completeness_status": completeness,
        "selection_mode": selection,
        "mock_coverage_status": mock_status,
        "pixelization": pixelization_text,
        "nside": int(nside) if nside is not None else None,
        "mask_hash": mask_hash,
        "scan_volume_hash": scan_volume_hash,
    }
    return SkySupport(
        selection_mode=selection,
        sky_support_hash=_json_hash(support_payload),
        mask_hash=mask_hash,
        mock_coverage_status=mock_status,
        scan_volume_hash=scan_volume_hash,
        coordinate_frame=frame,
        sky_fraction=fraction,
        completeness_status=completeness,
        pixelization=pixelization_text,
        nside=nside,
    )


def _sky_support_payload(value: object) -> dict[str, object]:
    if isinstance(value, SkySupport):
        return value.to_metadata()
    if isinstance(value, Mapping):
        return dict(value)
    raise ValueError("sky_support must be a mapping or SkySupport instance")


def _require_sequence_caveats(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, (str, bytes)):
        raise ValueError("sky_support caveats must be a sequence of strings")
    if not isinstance(value, Sequence):
        return ()
    return tuple(str(item) for item in value)


def validate_sky_facing_artifact_metadata(metadata: Mapping[str, Any]) -> None:
    """Validate PR-040 sky-support metadata for a sky-facing artifact.

    The caller uses this only for sky-facing outputs; therefore
    ``sky_support_status='not_directional'`` is rejected.
    """

    status = _require_nonempty_string(
        metadata.get("sky_support_status"),
        "sky_support_status",
    )
    if status == "not_directional":
        raise ValueError(
            "sky-facing artifacts cannot declare sky_support_status='not_directional'"
        )
    if status not in _ALLOWED_SKY_FACING_STATUSES:
        raise ValueError(
            "sky_support_status for sky-facing artifacts must be one of "
            f"{sorted(_ALLOWED_SKY_FACING_STATUSES)}; got {status!r}"
        )
    support = _sky_support_payload(metadata.get("sky_support"))
    for field in _SKY_SUPPORT_REQUIRED_FIELDS:
        if field not in support:
            raise ValueError(f"sky_support.{field} is required")
        if support[field] is None or (
            isinstance(support[field], str) and not support[field]
        ):
            raise ValueError(f"sky_support.{field} must be non-empty")
    fraction = float(support["sky_fraction"])
    if not np.isfinite(fraction) or not (0.0 < fraction <= 1.0):
        raise ValueError("sky_support.sky_fraction must be in (0, 1]")
    if not str(support["mask_hash"]).startswith("sha256:"):
        raise ValueError("sky_support.mask_hash must be a sha256 hash")
    if not str(support["sky_support_hash"]).startswith("sha256:"):
        raise ValueError("sky_support.sky_support_hash must be a sha256 hash")
    SkySupport(
        selection_mode=str(support.get("selection_mode", "unknown")),
        sky_support_hash=str(support["sky_support_hash"]),
        mask_hash=str(support["mask_hash"]),
        mock_coverage_status=str(support.get("mock_coverage_status", "unknown")),
        scan_volume_hash=str(support.get("scan_volume_hash", "")),
        coordinate_frame=str(support["coordinate_frame"]),
        sky_fraction=fraction,
        completeness_status=str(support["completeness_status"]),
        pixelization=str(support.get("pixelization", "unknown")),
        nside=support.get("nside"),  # type: ignore[arg-type]
    )
    _require_sequence_caveats(metadata.get("caveats"))
