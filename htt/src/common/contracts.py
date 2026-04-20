"""common.contracts — shared dataclasses (COMMON-A, INDEPENDENT_TRACKS_PLAN §2.6).

The five dataclasses here are the "public wire format" shared by bass, htt,
and tsc. They are all frozen so consumers cannot silently mutate them.

Scope
-----
* ``PreferredAxis`` — directional axis with provenance and production gate.
* ``SkySelectionConfig`` — the single ZoA/selection configuration object
  with production-mode invariants (§6.6 of the parent plan).
* ``DirectionalSummary`` — 4-channel summary aggregate (mirrors the AH-side
  channels; the htt AH module has per-channel ``ChannelSummary`` records).
* ``DynestyResult`` — Layer C posterior output container.
* ``MockCalibrationReport`` — Layer D mock calibration outcome.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional

import numpy as np


_ALLOWED_SOURCES = {
    "raw_diagnostic",
    "zoa_masked",
    "selection_aware",
    "fiducial_posterior",
}
_ALLOWED_WEIGHT_MODES = {"uniform_fallback", "native", "native_with_nuisance"}
_ALLOWED_SELECTION_MODES = {
    "none",
    "zoa_hard_cut",
    "angular_completeness",
    "mock_calibrated",
}


@dataclass(frozen=True)
class PreferredAxis:
    """Directional axis with full provenance (§6.2 of parent plan).

    ``production_allowed=True`` must come from a posterior-derived constructor
    (see forthcoming ``common.posterior_summary.axis_from_posterior``). Any
    axis flowing into a_{ℓm} restoration must satisfy this predicate.
    """

    l_deg: float
    b_deg: float
    label: str
    source: str
    weight_mode: str
    selection_mode: str
    production_allowed: bool = False
    provenance_hash: str = ""

    def __post_init__(self) -> None:
        if self.source not in _ALLOWED_SOURCES:
            raise ValueError(
                f"PreferredAxis.source={self.source!r} not in {_ALLOWED_SOURCES}"
            )
        if self.weight_mode not in _ALLOWED_WEIGHT_MODES:
            raise ValueError(
                f"PreferredAxis.weight_mode={self.weight_mode!r} "
                f"not in {_ALLOWED_WEIGHT_MODES}"
            )
        if self.selection_mode not in _ALLOWED_SELECTION_MODES:
            raise ValueError(
                f"PreferredAxis.selection_mode={self.selection_mode!r} "
                f"not in {_ALLOWED_SELECTION_MODES}"
            )


@dataclass(frozen=True)
class SkySelectionConfig:
    """Single configuration object for ZoA / selection handling (§6.6).

    Invariants (enforced in ``__post_init__``):

    * ``production_mode and allow_uniform_fallback`` → ValueError.
    * ``production_mode and not require_mock_calibration`` → ValueError.
    """

    zoa_half_angle_deg: float
    allow_uniform_fallback: bool = False
    min_retention_fraction: float = 0.3
    production_mode: bool = False
    nside: int = 64
    smooth_sigma_pix: float = 1.0
    n_mock: int = 1000
    require_mock_calibration: bool = True

    def __post_init__(self) -> None:
        if self.production_mode and self.allow_uniform_fallback:
            raise ValueError(
                "production_mode=True and allow_uniform_fallback=True "
                "are mutually exclusive"
            )
        if self.production_mode and not self.require_mock_calibration:
            raise ValueError(
                "production_mode requires mock calibration"
            )
        if not (0.0 <= self.min_retention_fraction <= 1.0):
            raise ValueError(
                f"min_retention_fraction must be in [0, 1]; "
                f"got {self.min_retention_fraction}"
            )
        if self.nside <= 0 or (self.nside & (self.nside - 1)) != 0:
            raise ValueError(
                f"nside must be a positive power of two; got {self.nside}"
            )


@dataclass(frozen=True)
class DirectionalSummary:
    """Four-channel directional summary aggregate (§6.3 AH structural slot).

    Each channel carries its own metadata — see the htt AH ChannelSummary
    record. This wrapper packages the four together for downstream transport.
    """

    raw: Mapping[str, Any]
    zoa_masked: Mapping[str, Any]
    selection_aware: Mapping[str, Any]
    mock_calibrated: Mapping[str, Any]


@dataclass(frozen=True)
class DynestyResult:
    """Dynesty Layer C posterior output container."""

    samples: np.ndarray          # (n_samples, n_params)
    logwt: np.ndarray            # (n_samples,) log-weights
    logz: float                  # log-evidence
    ncall: int                   # likelihood evaluations used
    config: Mapping[str, Any]    # dynesty config echo

    def __post_init__(self) -> None:
        if self.samples.ndim != 2:
            raise ValueError(
                f"DynestyResult.samples must be 2-D (got ndim={self.samples.ndim})"
            )
        if self.logwt.shape != (self.samples.shape[0],):
            raise ValueError(
                f"DynestyResult.logwt shape {self.logwt.shape} incompatible "
                f"with samples shape {self.samples.shape}"
            )
        if self.ncall < 0:
            raise ValueError(f"DynestyResult.ncall must be ≥ 0; got {self.ncall}")


@dataclass(frozen=True)
class MockCalibrationReport:
    """Mock-calibration Layer D outcome (§6.4)."""

    bias_amp: float
    bias_direction_deg: float
    coverage_68: float
    credible_radius_deg: float
    n_mock: int
    config: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not (0.0 <= self.coverage_68 <= 1.0):
            raise ValueError(
                f"coverage_68 must be in [0, 1]; got {self.coverage_68}"
            )
        if self.credible_radius_deg < 0:
            raise ValueError(
                f"credible_radius_deg must be ≥ 0; got {self.credible_radius_deg}"
            )
        if self.n_mock <= 0:
            raise ValueError(f"n_mock must be > 0; got {self.n_mock}")
