"""Selection-aware Zone-of-Avoidance ladder for HTT directional summaries.

The ladder is an HTT-facing composition layer over COMMON sky geometry and
selection primitives. It separates raw, hard-ZoA, angular-completeness, and
mock-calibrated support summaries while preserving the existing production-axis
firewall: these summaries remain diagnostic support records and are not
posterior axes by construction.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
from common.contracts import (
    DirectionalSummary,
    PreferredAxis,
    SkySelectionConfig,
    SkySupport,
)
from common.enum_compat import StrEnum
from common.healpix_selection import (
    build_angular_completeness,
    build_zoa_mask,
    compute_selection_weights,
    nside_to_npix,
    source_mask_from_pixel_mask,
)
from common.sky_geometry import normalize_weights, spherical_mean
from common.sky_support import build_sky_support_from_mask

__all__ = [
    "SelectionSupportMode",
    "ZoASelectionModeSummary",
    "ZoASelectionLadder",
    "build_zoa_selection_ladder",
]


class SelectionSupportMode(StrEnum):
    """Explicit support modes for ZoA selection summaries."""

    RAW = "raw"
    ZOA_MASKED = "zoa_masked"
    SELECTION_AWARE = "selection_aware"
    MOCK_CALIBRATED = "mock_calibrated"


_MODE_TO_SELECTION = {
    SelectionSupportMode.RAW: "none",
    SelectionSupportMode.ZOA_MASKED: "zoa_hard_cut",
    SelectionSupportMode.SELECTION_AWARE: "angular_completeness",
    SelectionSupportMode.MOCK_CALIBRATED: "mock_calibrated",
}

_MODE_TO_SOURCE = {
    SelectionSupportMode.RAW: "raw_diagnostic",
    SelectionSupportMode.ZOA_MASKED: "zoa_masked",
    SelectionSupportMode.SELECTION_AWARE: "selection_aware",
    # This is a calibrated support summary, not a posterior-derived axis.
    SelectionSupportMode.MOCK_CALIBRATED: "selection_aware",
}

_ALLOWED_MOCK_COVERAGE = {"adequate", "inadequate", "pending"}
_PIXELIZATION = "equal_area_iso_latitude_ring"
_DEFAULT_COMMAND = "htt.zoa.selection_ladder.build_zoa_selection_ladder"


@dataclass(frozen=True)
class ZoASelectionModeSummary:
    """One support-mode summary in the ZoA ladder."""

    mode: SelectionSupportMode
    selection_mode: str
    source: str
    weight_mode: str
    production_allowed: bool
    n_sources: int
    n_active: int
    retention_fraction: float
    fallback_status: str
    active_mask: tuple[bool, ...]
    weights: tuple[float, ...]
    axis_l_deg: float
    axis_b_deg: float
    resultant_R: float
    sky_support: SkySupport
    metadata: Mapping[str, Any]
    caveats: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.selection_mode != _MODE_TO_SELECTION[self.mode]:
            raise ValueError(
                f"{self.mode.value} must use selection_mode="
                f"{_MODE_TO_SELECTION[self.mode]!r}"
            )
        if self.source != _MODE_TO_SOURCE[self.mode]:
            raise ValueError(
                f"{self.mode.value} must use source={_MODE_TO_SOURCE[self.mode]!r}"
            )
        if self.production_allowed:
            raise ValueError(
                "ZoA selection-ladder summaries are support diagnostics, not "
                "posterior-derived production axes"
            )
        if self.n_sources <= 0:
            raise ValueError("n_sources must be positive")
        if not (0 <= self.n_active <= self.n_sources):
            raise ValueError("n_active must be in [0, n_sources]")
        if len(self.active_mask) != self.n_sources:
            raise ValueError("active_mask length must equal n_sources")
        if len(self.weights) != self.n_sources:
            raise ValueError("weights length must equal n_sources")
        retention = float(self.retention_fraction)
        if not np.isfinite(retention) or not (0.0 <= retention <= 1.0):
            raise ValueError("retention_fraction must be finite and in [0, 1]")
        object.__setattr__(self, "retention_fraction", retention)
        weights = np.asarray(self.weights, dtype=float)
        if not np.all(np.isfinite(weights)):
            raise ValueError("weights must be finite")
        if np.any(weights < 0.0):
            raise ValueError("weights must be non-negative")
        if not np.isclose(float(weights.sum()), 1.0):
            raise ValueError("weights must be normalized to sum 1")

    def to_mapping(self) -> dict[str, Any]:
        """Return a JSON-compatible payload for status/result cards."""

        return {
            "mode": self.mode.value,
            "selection_mode": self.selection_mode,
            "source": self.source,
            "weight_mode": self.weight_mode,
            "production_allowed": self.production_allowed,
            "n_sources": self.n_sources,
            "n_active": self.n_active,
            "retention_fraction": self.retention_fraction,
            "fallback_status": self.fallback_status,
            "active_mask": list(self.active_mask),
            "weights": list(self.weights),
            "axis": {
                "l_deg": self.axis_l_deg,
                "b_deg": self.axis_b_deg,
                "resultant_R": self.resultant_R,
                "mean_method": "unit_vector_resultant",
            },
            "sky_support": self.sky_support.to_metadata(),
            "metadata": dict(self.metadata),
            "caveats": list(self.caveats),
        }

    def to_diagnostic_axis(self, *, label: str | None = None) -> PreferredAxis:
        """Return a fail-closed diagnostic axis for gate-audit tests."""

        if not np.isfinite(self.axis_l_deg) or not np.isfinite(self.axis_b_deg):
            raise ValueError("Cannot build axis from degenerate directional mean")
        return PreferredAxis(
            l_deg=self.axis_l_deg,
            b_deg=self.axis_b_deg,
            label=label or f"{self.mode.value}_support_diagnostic",
            source=self.source,
            weight_mode=self.weight_mode,
            selection_mode=self.selection_mode,
            production_allowed=False,
            provenance_hash=str(self.metadata.get("summary_hash", "")),
        )


@dataclass(frozen=True)
class ZoASelectionLadder:
    """Four-mode HTT support ladder for a single ZoA configuration."""

    raw: ZoASelectionModeSummary
    zoa_masked: ZoASelectionModeSummary
    selection_aware: ZoASelectionModeSummary
    mock_calibrated: ZoASelectionModeSummary

    def to_directional_summary(self) -> DirectionalSummary:
        """Convert to the canonical COMMON four-channel transport wrapper."""

        return DirectionalSummary(
            raw=self.raw.to_mapping(),
            zoa_masked=self.zoa_masked.to_mapping(),
            selection_aware=self.selection_aware.to_mapping(),
            mock_calibrated=self.mock_calibrated.to_mapping(),
        )


def build_zoa_selection_ladder(
    l_deg: Sequence[float] | np.ndarray,
    b_deg: Sequence[float] | np.ndarray,
    *,
    bcut_deg: float,
    nside: int,
    smooth_sigma_pix: float = 1.0,
    production_mode: bool = False,
    allow_uniform_fallback: bool = False,
    mock_calibration_weights: Sequence[float] | np.ndarray | None = None,
    mock_coverage_status: str = "pending",
    config_hash: str | None = None,
    input_hashes: Sequence[str] | None = None,
    generating_command: str = _DEFAULT_COMMAND,
    git_commit: str | None = None,
) -> ZoASelectionLadder:
    """Build raw, ZoA-masked, selection-aware, and mock-calibrated summaries.

    ``production_mode=True`` activates strict gate behavior: uniform fallback is
    rejected by :class:`common.contracts.SkySelectionConfig`, and explicit
    adequate mock calibration weights are required. Even then the returned
    ladder remains a support diagnostic, not a production posterior axis.
    """

    cfg = SkySelectionConfig(
        zoa_half_angle_deg=float(bcut_deg),
        allow_uniform_fallback=bool(allow_uniform_fallback),
        production_mode=bool(production_mode),
        nside=int(nside),
        smooth_sigma_pix=float(smooth_sigma_pix),
        require_mock_calibration=True,
    )
    l, b = _check_coordinates(l_deg, b_deg)
    if l.size == 0:
        raise ValueError("ZoA selection ladder requires at least one source")
    mock_status = str(mock_coverage_status)
    if mock_status not in _ALLOWED_MOCK_COVERAGE:
        raise ValueError(
            f"mock_coverage_status must be one of {sorted(_ALLOWED_MOCK_COVERAGE)}"
        )
    mock_weights = _prepare_mock_weights(
        mock_calibration_weights,
        n_sources=l.size,
        production_mode=bool(production_mode),
        mock_coverage_status=mock_status,
    )
    common_metadata = _common_metadata(
        l,
        b,
        cfg=cfg,
        config_hash=config_hash,
        input_hashes=input_hashes,
        generating_command=generating_command,
        git_commit=git_commit,
    )
    full_mask = np.ones(nside_to_npix(cfg.nside), dtype=bool)
    zoa_mask = build_zoa_mask(l, b, cfg.zoa_half_angle_deg, cfg.nside)
    completeness = build_angular_completeness(
        l,
        b,
        cfg.nside,
        smooth_sigma_pix=cfg.smooth_sigma_pix,
    )
    raw_active = source_mask_from_pixel_mask(l, b, full_mask)
    zoa_active = source_mask_from_pixel_mask(l, b, zoa_mask)
    zoa_retention = float(zoa_active.mean())
    if production_mode and zoa_retention < cfg.min_retention_fraction:
        raise ValueError(
            "production_mode requires ZoA retention_fraction "
            f">= {cfg.min_retention_fraction}; got {zoa_retention}"
        )
    raw_summary = _build_mode_summary(
        SelectionSupportMode.RAW,
        l,
        b,
        pixel_mask=full_mask,
        active_mask=raw_active,
        raw_weights=np.ones_like(l, dtype=float),
        allow_uniform_fallback=False,
        metadata=common_metadata,
        completeness_status="not_applied",
        mock_coverage_status="not_applicable",
        caveats=("raw support mode ignores ZoA and completeness corrections",),
    )
    zoa_summary = _build_mode_summary(
        SelectionSupportMode.ZOA_MASKED,
        l,
        b,
        pixel_mask=zoa_mask,
        active_mask=zoa_active,
        raw_weights=zoa_active.astype(float),
        allow_uniform_fallback=bool(allow_uniform_fallback),
        metadata=common_metadata,
        completeness_status="hard_cut_only",
        mock_coverage_status="not_applicable",
        caveats=("ZoA hard-cut mode is diagnostic support only",),
    )
    selection_weights = compute_selection_weights(l, b, zoa_mask, completeness)
    selection_summary = _build_mode_summary(
        SelectionSupportMode.SELECTION_AWARE,
        l,
        b,
        pixel_mask=zoa_mask,
        active_mask=selection_weights > 0.0,
        raw_weights=selection_weights,
        allow_uniform_fallback=bool(allow_uniform_fallback),
        metadata=common_metadata,
        completeness_status="angular_completeness_estimated",
        mock_coverage_status="pending",
        caveats=("Angular-completeness mode is not mock calibrated",),
    )
    mock_raw_weights = (
        selection_weights if mock_weights is None else selection_weights * mock_weights
    )
    mock_caveats = [
        "Mock-calibrated support mode is not a posterior-derived production axis",
    ]
    if mock_weights is None:
        mock_caveats.append(
            "mock calibration weights not supplied; support summary remains pending"
        )
    else:
        mock_caveats.append(
            "caller-supplied mock calibration weights are support provenance only"
        )
    mock_summary = _build_mode_summary(
        SelectionSupportMode.MOCK_CALIBRATED,
        l,
        b,
        pixel_mask=zoa_mask,
        active_mask=mock_raw_weights > 0.0,
        raw_weights=mock_raw_weights,
        allow_uniform_fallback=bool(allow_uniform_fallback),
        metadata=common_metadata,
        completeness_status=(
            "mock_calibrated" if mock_weights is not None else "mock_pending"
        ),
        mock_coverage_status=mock_status,
        caveats=tuple(mock_caveats),
    )
    return ZoASelectionLadder(
        raw=raw_summary,
        zoa_masked=zoa_summary,
        selection_aware=selection_summary,
        mock_calibrated=mock_summary,
    )


def _check_coordinates(
    l_deg: Sequence[float] | np.ndarray,
    b_deg: Sequence[float] | np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    l = np.asarray(l_deg, dtype=float)
    b = np.asarray(b_deg, dtype=float)
    if l.shape != b.shape:
        raise ValueError(f"l_deg shape {l.shape} != b_deg shape {b.shape}")
    if l.ndim != 1:
        raise ValueError("l_deg/b_deg must be 1-D")
    if not np.all(np.isfinite(l)) or not np.all(np.isfinite(b)):
        raise ValueError("l_deg/b_deg must be finite")
    if np.any((b < -90.0) | (b > 90.0)):
        raise ValueError("b_deg values must be in [-90, 90]")
    return np.mod(l, 360.0), b


def _prepare_mock_weights(
    mock_calibration_weights: Sequence[float] | np.ndarray | None,
    *,
    n_sources: int,
    production_mode: bool,
    mock_coverage_status: str,
) -> np.ndarray | None:
    if mock_calibration_weights is None:
        if production_mode:
            raise ValueError(
                "production_mode requires explicit mock_calibration_weights"
            )
        return None
    weights = np.asarray(mock_calibration_weights, dtype=float)
    if weights.shape != (n_sources,):
        raise ValueError(
            f"mock_calibration_weights shape {weights.shape} != ({n_sources},)"
        )
    if not np.all(np.isfinite(weights)) or np.any(weights < 0.0):
        raise ValueError("mock_calibration_weights must be finite and non-negative")
    if production_mode and mock_coverage_status != "adequate":
        raise ValueError("production_mode requires adequate mock coverage")
    return weights


def _build_mode_summary(
    mode: SelectionSupportMode,
    l_deg: np.ndarray,
    b_deg: np.ndarray,
    *,
    pixel_mask: np.ndarray,
    active_mask: np.ndarray,
    raw_weights: np.ndarray,
    allow_uniform_fallback: bool,
    metadata: Mapping[str, Any],
    completeness_status: str,
    mock_coverage_status: str,
    caveats: tuple[str, ...],
) -> ZoASelectionModeSummary:
    normalized, fallback_status = normalize_weights(
        raw_weights,
        allow_uniform_fallback=allow_uniform_fallback,
    )
    mean = spherical_mean(l_deg, b_deg, normalized)
    sky_support = build_sky_support_from_mask(
        pixel_mask,
        coordinate_frame="galactic",
        completeness_status=completeness_status,
        selection_mode=_MODE_TO_SELECTION[mode],
        mock_coverage_status=mock_coverage_status,
        pixelization=_PIXELIZATION,
        nside=int(metadata["nside"]),
        scan_volume_hash=str(metadata["config_hash"]),
    )
    payload_without_hash = {
        **dict(metadata),
        "mode": mode.value,
        "selection_mode": _MODE_TO_SELECTION[mode],
        "fallback_status": fallback_status,
        "retention_fraction": float(np.asarray(active_mask, dtype=bool).mean()),
        "sky_support_hash": sky_support.sky_support_hash,
    }
    summary_metadata = {
        **dict(metadata),
        "summary_hash": _json_hash(payload_without_hash),
    }
    return ZoASelectionModeSummary(
        mode=mode,
        selection_mode=_MODE_TO_SELECTION[mode],
        source=_MODE_TO_SOURCE[mode],
        weight_mode=(
            "uniform_fallback" if fallback_status == "uniform_fallback_diagnostic_only"
            else "native"
        ),
        production_allowed=False,
        n_sources=int(l_deg.size),
        n_active=int(np.asarray(active_mask, dtype=bool).sum()),
        retention_fraction=float(np.asarray(active_mask, dtype=bool).mean()),
        fallback_status=fallback_status,
        active_mask=tuple(bool(v) for v in np.asarray(active_mask, dtype=bool)),
        weights=tuple(float(v) for v in normalized),
        axis_l_deg=float(mean["l_deg"]),
        axis_b_deg=float(mean["b_deg"]),
        resultant_R=float(mean["resultant_R"]),
        sky_support=sky_support,
        metadata=summary_metadata,
        caveats=tuple(caveats),
    )


def _common_metadata(
    l_deg: np.ndarray,
    b_deg: np.ndarray,
    *,
    cfg: SkySelectionConfig,
    config_hash: str | None,
    input_hashes: Sequence[str] | None,
    generating_command: str,
    git_commit: str | None,
) -> dict[str, Any]:
    if not generating_command.strip():
        raise ValueError("generating_command must be non-empty")
    resolved_inputs = (
        tuple(str(item).strip() for item in input_hashes)
        if input_hashes is not None
        else (_array_hash("l_deg", l_deg), _array_hash("b_deg", b_deg))
    )
    if not resolved_inputs or any(not item for item in resolved_inputs):
        raise ValueError("input_hashes must be non-empty strings")
    config_payload = {
        "bcut_deg": cfg.zoa_half_angle_deg,
        "nside": cfg.nside,
        "smooth_sigma_pix": cfg.smooth_sigma_pix,
        "production_mode": cfg.production_mode,
        "allow_uniform_fallback": cfg.allow_uniform_fallback,
        "input_hashes": resolved_inputs,
    }
    resolved_config_hash = config_hash or _json_hash(config_payload)
    if not str(resolved_config_hash).startswith("sha256:"):
        raise ValueError("config_hash must be a sha256:... value")
    return {
        "owner": "HTT",
        "implementation_scope": "htt",
        "claim_tier": "diagnostic_only",
        "transfer_source": "none",
        "config_hash": str(resolved_config_hash),
        "input_hashes": list(resolved_inputs),
        "sky_support_status": "directional",
        "null_mock_status": "not_statistical",
        "covariance_status": "not_statistical",
        "generating_command": generating_command,
        "git_commit": git_commit or "worktree",
        "bcut_deg": cfg.zoa_half_angle_deg,
        "nside": cfg.nside,
        "smooth_sigma_pix": cfg.smooth_sigma_pix,
        "production_mode": cfg.production_mode,
        "allow_uniform_fallback": cfg.allow_uniform_fallback,
    }


def _array_hash(name: str, values: np.ndarray) -> str:
    arr = np.ascontiguousarray(values, dtype=float)
    digest = hashlib.sha256()
    digest.update(name.encode("utf-8"))
    digest.update(str(arr.shape).encode("ascii"))
    digest.update(arr.dtype.str.encode("ascii"))
    digest.update(arr.tobytes())
    return f"sha256:{digest.hexdigest()}"


def _json_hash(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"
