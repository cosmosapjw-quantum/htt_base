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
_ALLOWED_OBSERVABLE_MODES = {
    "isotropic_compressed",
    "deterministic_template",
    "anisotropic_covariance",
    "mixed_template_covariance",
}
_ALLOWED_TSC_CHARTS = {
    "one_field",
    "two_field",
    "higher_field",
    "full_resolved_trace",
}
_ALLOWED_TSC_CHART_STATUSES = {
    "valid_one_field",
    "valid_two_field",
    "two_field_recommended",
    "higher_field_recommended",
    "full_resolved_trace_required",
    "invalid_domain",
}
_ALLOWED_SOURCE_STATUSES = {"adequate", "inadequate", "pending"}
_ALLOWED_PROPAGATION_STATUSES = {"pending", "validated", "blocked"}
_ALLOWED_CHANNELS = {"TT", "TE", "EE", "BB", "TB", "EB", "BiPoSH", "template", "scalar_summary"}

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
ObservableMode = Literal[
    "isotropic_compressed",
    "deterministic_template",
    "anisotropic_covariance",
    "mixed_template_covariance",
]
TscChart = Literal["one_field", "two_field", "higher_field", "full_resolved_trace"]
TscChartStatus = Literal[
    "valid_one_field",
    "valid_two_field",
    "two_field_recommended",
    "higher_field_recommended",
    "full_resolved_trace_required",
    "invalid_domain",
]
SourceStatus = Literal["adequate", "inadequate", "pending"]
PropagationStatus = Literal["pending", "validated", "blocked"]
Channel = Literal["TT", "TE", "EE", "BB", "TB", "EB", "BiPoSH", "template", "scalar_summary"]


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
class ClaimLedgerEntry:
    """Machine-readable claim-ledger row.

    This is the shared contract counterpart of ``docs/claim_ledger.md``. It is
    intentionally lightweight so later lanes can emit generated claim-tier
    records without redefining schema or promotion semantics.
    """

    artifact_id: str
    owner: Owner
    claim_tier: ClaimTier
    allowed_claims: tuple[str, ...]
    forbidden_claims: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    source_commit: str
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.artifact_id:
            raise ValueError("ClaimLedgerEntry.artifact_id must be non-empty")
        if self.owner not in _ALLOWED_OWNERS:
            raise ValueError(f"Unknown owner {self.owner!r}")
        if self.claim_tier not in _ALLOWED_CLAIM_TIERS:
            raise ValueError(f"Unknown claim_tier {self.claim_tier!r}")
        if not self.source_commit:
            raise ValueError("ClaimLedgerEntry.source_commit must be non-empty")
        if not self.allowed_claims and not self.forbidden_claims:
            raise ValueError(
                "ClaimLedgerEntry requires at least one allowed or forbidden claim"
            )


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
class AtlasEntryLite:
    """Theory-side low-footprint atlas contract."""

    atlas_id: str
    theory_family: str
    geometry_params: dict[str, float]
    kinematic_params: dict[str, float]
    tilt_params: dict[str, float]
    solver_output_ref: str
    observable_vector_ref: str
    response_blocks: dict[str, object]
    validity_domain: dict[str, object]
    interpolation_status: str
    manifest: ArtifactManifest

    def __post_init__(self) -> None:
        if not self.atlas_id:
            raise ValueError("AtlasEntryLite.atlas_id must be non-empty")
        if not self.theory_family:
            raise ValueError("AtlasEntryLite.theory_family must be non-empty")
        if self.manifest.owner != "BASS":
            raise ValueError(
                "AtlasEntryLite.manifest.owner must be 'BASS' "
                f"(got {self.manifest.owner!r})"
            )


@dataclass(frozen=True)
class FullCovMESReport:
    """Full-covariance morphology-aware bound report."""

    parameter_block: str
    diagonal_bound: float
    covariance_bound: float | None
    dynamical_bound: float | None
    final_bound: float
    information_gain: float
    response_rank: int
    singular_values: list[float]
    nuisance_projection_status: str
    observable_set: list[str]
    covariance_assumption: str
    validity_radius: float | None
    manifest: ArtifactManifest
    tsc_overlay_ref: str | None = None

    def __post_init__(self) -> None:
        if not self.parameter_block:
            raise ValueError("FullCovMESReport.parameter_block must be non-empty")
        if self.response_rank < 0:
            raise ValueError("FullCovMESReport.response_rank must be >= 0")


@dataclass(frozen=True)
class DiscriminationMatrix:
    """Response-overlap and degeneracy matrix."""

    hypotheses: tuple[str, ...]
    overlap_matrix: object
    response_norms: dict[str, float]
    degeneracy_flags: dict[str, bool]
    recommended_next_observable: dict[str, str]
    claim_tier_by_pair: dict[str, str]
    manifest: ArtifactManifest

    def __post_init__(self) -> None:
        if len(self.hypotheses) < 2:
            raise ValueError("DiscriminationMatrix requires at least two hypotheses")
        invalid = sorted(
            set(self.claim_tier_by_pair.values()) - _ALLOWED_CLAIM_TIERS
        )
        if invalid:
            raise ValueError(f"Unknown claim tiers in DiscriminationMatrix: {invalid}")


@dataclass(frozen=True)
class TscDomainReport:
    """TSC chart-domain and admissibility report."""

    chart: TscChart
    theta_min: float
    eta_max: float | None
    be_eta_nonpositive: bool | None
    weight_simplex_ok: bool
    jacobian_sigma_min: float | None
    domain_margin: float
    status: TscChartStatus
    blocking_reasons: tuple[str, ...]
    manifest: ArtifactManifest

    def __post_init__(self) -> None:
        if self.chart not in _ALLOWED_TSC_CHARTS:
            raise ValueError(f"Unknown TSC chart {self.chart!r}")
        if self.status not in _ALLOWED_TSC_CHART_STATUSES:
            raise ValueError(f"Unknown TSC chart status {self.status!r}")
        if self.manifest.owner != "TSC":
            raise ValueError(
                "TscDomainReport.manifest.owner must be 'TSC' "
                f"(got {self.manifest.owner!r})"
            )


@dataclass(frozen=True)
class TscResidualReport:
    """TSC residual and defect summary."""

    chart: TscChart
    laguerre_n_ge_2_norm: float
    ambient_defect_rate: float | None
    projected_defect_estimate: float | None
    onefield_residual: float | None
    twofield_residual: float | None
    eta_tangent_fraction: float | None
    trace_residual_q_tr: float | None
    spin2_residual: float | None
    high_residual: float | None
    residual_origin: Literal["trace", "eta_tangent", "spin2", "high", "mixed", "unknown"]
    labels: tuple[str, ...]
    manifest: ArtifactManifest

    def __post_init__(self) -> None:
        if self.chart not in _ALLOWED_TSC_CHARTS:
            raise ValueError(f"Unknown TSC chart {self.chart!r}")
        if self.manifest.owner != "TSC":
            raise ValueError(
                "TscResidualReport.manifest.owner must be 'TSC' "
                f"(got {self.manifest.owner!r})"
            )


@dataclass(frozen=True)
class TscSourceBridgeReport:
    """TSC trace-source bridge report."""

    source_name: Literal["thomson_trace_quadrupole", "other"]
    chart: TscChart
    q2_norm: float
    source_error_bound: float | None
    nonlinear_dipole_quartic_correction: float | None
    eta_correction_indicator: float | None
    on_manifold_exact: bool
    source_status: SourceStatus
    required_bass_primitives: tuple[str, ...]
    labels: tuple[str, ...]
    manifest: ArtifactManifest

    def __post_init__(self) -> None:
        if self.chart not in _ALLOWED_TSC_CHARTS:
            raise ValueError(f"Unknown TSC chart {self.chart!r}")
        if self.source_status not in _ALLOWED_SOURCE_STATUSES:
            raise ValueError(f"Unknown source_status {self.source_status!r}")
        if self.manifest.owner != "TSC":
            raise ValueError(
                "TscSourceBridgeReport.manifest.owner must be 'TSC' "
                f"(got {self.manifest.owner!r})"
            )


@dataclass(frozen=True)
class TscChannelAdequacyBudget:
    """TSC source-to-channel budget record."""

    channel: Channel
    trace_budget: float | None
    spin2_budget: float | None
    high_budget: float | None
    source_to_field_bound: float | None
    spectrum_bound_linear: float | None
    spectrum_bound_quadratic: float | None
    source_status: SourceStatus
    propagation_status: PropagationStatus
    claim_ceiling: ClaimTier
    labels: tuple[str, ...]
    manifest: ArtifactManifest

    def __post_init__(self) -> None:
        if self.channel not in _ALLOWED_CHANNELS:
            raise ValueError(f"Unknown channel {self.channel!r}")
        if self.source_status not in _ALLOWED_SOURCE_STATUSES:
            raise ValueError(f"Unknown source_status {self.source_status!r}")
        if self.propagation_status not in _ALLOWED_PROPAGATION_STATUSES:
            raise ValueError(
                f"Unknown propagation_status {self.propagation_status!r}"
            )
        if self.claim_ceiling not in _ALLOWED_CLAIM_TIERS:
            raise ValueError(f"Unknown claim_ceiling {self.claim_ceiling!r}")
        if self.manifest.owner != "TSC":
            raise ValueError(
                "TscChannelAdequacyBudget.manifest.owner must be 'TSC' "
                f"(got {self.manifest.owner!r})"
            )


@dataclass(frozen=True)
class TscUpgradeRecommendation:
    """TSC chart-upgrade or block recommendation."""

    current_chart: TscChart
    recommended_chart: TscChart
    reason: Literal[
        "eta_tangent_false_trigger",
        "spectral_distortion_residual",
        "invalid_domain",
        "jacobian_near_singular",
        "source_error_bound_exceeded",
        "spin2_required",
        "high_residual_required",
        "stable_no_upgrade",
    ]
    severity: Literal["info", "warn", "block"]
    dwell_time_required: float | None
    hysteresis_state: str | None
    labels: tuple[str, ...]
    manifest: ArtifactManifest

    def __post_init__(self) -> None:
        if self.current_chart not in _ALLOWED_TSC_CHARTS:
            raise ValueError(f"Unknown current_chart {self.current_chart!r}")
        if self.recommended_chart not in _ALLOWED_TSC_CHARTS:
            raise ValueError(
                f"Unknown recommended_chart {self.recommended_chart!r}"
            )
        if self.severity not in {"info", "warn", "block"}:
            raise ValueError(f"Unknown severity {self.severity!r}")
        if self.manifest.owner != "TSC":
            raise ValueError(
                "TscUpgradeRecommendation.manifest.owner must be 'TSC' "
                f"(got {self.manifest.owner!r})"
            )


@dataclass(frozen=True)
class TscAdequacyOverlay:
    """Top-level TSC adequacy overlay object."""

    domain_report: TscDomainReport
    residual_report: TscResidualReport
    source_bridge_report: TscSourceBridgeReport | None
    channel_budgets: tuple[TscChannelAdequacyBudget, ...]
    upgrade_recommendation: TscUpgradeRecommendation
    no_overclaim_flags: dict[str, bool]
    quarantine_reasons: tuple[str, ...]
    public_caveat_snippet: str
    manifest: ArtifactManifest

    def __post_init__(self) -> None:
        if self.manifest.owner != "TSC":
            raise ValueError(
                "TscAdequacyOverlay.manifest.owner must be 'TSC' "
                f"(got {self.manifest.owner!r})"
            )
        if not self.public_caveat_snippet:
            raise ValueError(
                "TscAdequacyOverlay.public_caveat_snippet must be non-empty"
            )


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
