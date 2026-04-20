"""common.contracts — canonical shared schema layer.

This module now carries two contract generations:

1. Legacy COMMON-A directional and mock-calibration dataclasses used by the
   existing HTT/MIO stack.
2. VER2 barrier contracts frozen at the `docs/ver2_upgrade/*` authority layer.

The VER2 rule is:

* base enums, manifest primitives, ownership, claim tiers, and runtime
  decision primitives live here;
* cross-package wrappers under ``workspace/contracts`` may *reference* these
  objects but must not redefine them;
* all dataclasses remain frozen so downstream code cannot silently mutate
  ownership or claim-tier metadata.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional, Literal

import numpy as np


_ALLOWED_OWNERS = {"BASS", "HTT", "MIO", "TSC", "COMMON"}
_ALLOWED_CLAIM_TIERS = {"exploratory", "conditional", "validated", "blocked"}
_ALLOWED_IMPLEMENTATION_SCOPES = {
    "bass_py",
    "bass_rs",
    "canonical_BASS",
    "htt",
    "mio",
    "tsc",
    "common",
}
_ALLOWED_PRODUCTION_STATUSES = {
    "diagnostic_only",
    "production_candidate",
    "production_validated",
    "blocked_missing_covariance",
    "blocked_missing_null_mocks",
    "blocked_missing_atlas",
    "blocked_owner_violation",
}
_ALLOWED_SOURCE_STATUSES = {"adequate", "inadequate", "pending"}
_ALLOWED_PROPAGATION_STATUSES = {"pending", "validated", "blocked"}

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


Owner = Literal["BASS", "HTT", "MIO", "TSC", "COMMON"]
ClaimTier = Literal["exploratory", "conditional", "validated", "blocked"]
ImplementationScope = Literal[
    "bass_py",
    "bass_rs",
    "canonical_BASS",
    "htt",
    "mio",
    "tsc",
    "common",
]
ProductionStatus = Literal[
    "diagnostic_only",
    "production_candidate",
    "production_validated",
    "blocked_missing_covariance",
    "blocked_missing_null_mocks",
    "blocked_missing_atlas",
    "blocked_owner_violation",
]


@dataclass(frozen=True)
class ArtifactManifest:
    """Cross-package artifact provenance and promotion gate.

    This is the canonical manifest primitive for the VER2 upgrade. Any
    package-specific wrapper may embed this object but must not redefine it.
    """

    artifact_id: str
    artifact_path: str
    owner: Owner
    implementation_scope: ImplementationScope
    claim_tier: ClaimTier
    production_status: ProductionStatus
    created_by: str
    git_commit: str | None
    config_hash: str
    input_hashes: list[str]
    code_version: str
    schema_version: str
    caveats: list[str] = field(default_factory=list)
    required_gates: list[str] = field(default_factory=list)
    passed_gates: list[str] = field(default_factory=list)
    failed_gates: list[str] = field(default_factory=list)
    statistics_definitions: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.artifact_id:
            raise ValueError("ArtifactManifest.artifact_id must be non-empty")
        if not self.artifact_path:
            raise ValueError("ArtifactManifest.artifact_path must be non-empty")
        if self.owner not in _ALLOWED_OWNERS:
            raise ValueError(f"Unknown owner {self.owner!r}")
        if self.implementation_scope not in _ALLOWED_IMPLEMENTATION_SCOPES:
            raise ValueError(
                f"Unknown implementation_scope {self.implementation_scope!r}"
            )
        if self.claim_tier not in _ALLOWED_CLAIM_TIERS:
            raise ValueError(f"Unknown claim_tier {self.claim_tier!r}")
        if self.production_status not in _ALLOWED_PRODUCTION_STATUSES:
            raise ValueError(
                f"Unknown production_status {self.production_status!r}"
            )
        if not self.created_by:
            raise ValueError("ArtifactManifest.created_by must be non-empty")
        if not self.config_hash:
            raise ValueError("ArtifactManifest.config_hash must be non-empty")
        if not self.code_version:
            raise ValueError("ArtifactManifest.code_version must be non-empty")
        if not self.schema_version:
            raise ValueError("ArtifactManifest.schema_version must be non-empty")


@dataclass(frozen=True)
class SkySupport:
    """Minimal sky-support metadata for production directional surfaces."""

    selection_mode: str
    sky_support_hash: str
    mask_hash: str
    mock_coverage_status: str
    scan_volume_hash: str = ""

    def __post_init__(self) -> None:
        if not self.selection_mode:
            raise ValueError("SkySupport.selection_mode must be non-empty")
        if not self.sky_support_hash:
            raise ValueError("SkySupport.sky_support_hash must be non-empty")
        if not self.mask_hash:
            raise ValueError("SkySupport.mask_hash must be non-empty")
        if not self.mock_coverage_status:
            raise ValueError("SkySupport.mock_coverage_status must be non-empty")


@dataclass(frozen=True)
class StatusSnapshotEntry:
    """Machine-readable package/module status row."""

    artifact_id: str
    owner: Owner
    implementation_scope: ImplementationScope
    claim_tier: ClaimTier
    implemented: bool
    smoke_tested: bool
    production_validated: bool
    manuscript_used: bool
    source_commit: str

    def __post_init__(self) -> None:
        if self.owner not in _ALLOWED_OWNERS:
            raise ValueError(f"Unknown owner {self.owner!r}")
        if self.implementation_scope not in _ALLOWED_IMPLEMENTATION_SCOPES:
            raise ValueError(
                f"Unknown implementation_scope {self.implementation_scope!r}"
            )
        if self.claim_tier not in _ALLOWED_CLAIM_TIERS:
            raise ValueError(f"Unknown claim_tier {self.claim_tier!r}")
        if not self.artifact_id:
            raise ValueError("StatusSnapshotEntry.artifact_id must be non-empty")
        if not self.source_commit:
            raise ValueError("StatusSnapshotEntry.source_commit must be non-empty")


@dataclass(frozen=True)
class RuntimeReductionDecision:
    """BASS-owned allow/block decision primitive.

    VER2 P0 freezes the rule that only BASS may own reduction allow/block.
    """

    owner: Owner
    allow_reduction: bool
    source_status: Literal["adequate", "inadequate", "pending"]
    propagation_status: Literal["pending", "validated", "blocked"]
    reason: str
    claim_tier: ClaimTier = "conditional"

    def __post_init__(self) -> None:
        if self.owner != "BASS":
            raise ValueError(
                "RuntimeReductionDecision.owner must be 'BASS' "
                f"(got {self.owner!r})"
            )
        if self.source_status not in _ALLOWED_SOURCE_STATUSES:
            raise ValueError(f"Unknown source_status {self.source_status!r}")
        if self.propagation_status not in _ALLOWED_PROPAGATION_STATUSES:
            raise ValueError(
                f"Unknown propagation_status {self.propagation_status!r}"
            )
        if self.claim_tier not in _ALLOWED_CLAIM_TIERS:
            raise ValueError(f"Unknown claim_tier {self.claim_tier!r}")
        if not self.reason:
            raise ValueError("RuntimeReductionDecision.reason must be non-empty")


@dataclass(frozen=True)
class SolverCoreOutput:
    """Observer-neutral solver output contract."""

    alm_T: object | None
    alm_E: object | None
    alm_B: object | None
    map_T: object | None
    map_Q: object | None
    map_U: object | None
    deterministic_template: dict[str, Any] | None
    anisotropic_covariance: object | None
    metadata: Mapping[str, Any]
    manifest: ArtifactManifest

    def __post_init__(self) -> None:
        required = {
            "bianchi_type",
            "harmonic_basis",
            "eb_sign_convention",
            "multipole_cutoff",
            "tilt_enabled",
            "thomson_mode",
        }
        missing = sorted(k for k in required if k not in self.metadata)
        if missing:
            raise ValueError(
                f"SolverCoreOutput.metadata missing required keys: {missing}"
            )


@dataclass(frozen=True)
class ObservableVector:
    """Descriptive observable substrate shared across BASS/HTT/MIO/TSC."""

    ell_max: int
    channels: tuple[str, ...]
    cl: dict[str, object]
    alm_features: dict[str, object]
    biposh: dict[str, object] | None
    template_fit: dict[str, object] | None
    covariance_features: dict[str, object] | None
    scan_volume: dict[str, object]
    sky_support: SkySupport
    manifest: ArtifactManifest

    def __post_init__(self) -> None:
        if self.ell_max < 0:
            raise ValueError("ObservableVector.ell_max must be >= 0")
        if not self.channels:
            raise ValueError("ObservableVector.channels must be non-empty")


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
