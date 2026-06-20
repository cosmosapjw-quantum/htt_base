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
from enum import StrEnum
from typing import Any, Mapping, Optional, Literal

import numpy as np


class Owner(StrEnum):
    """Canonical owner vocabulary for new COMMON/HTT/MIO/BASS contracts."""

    COMMON = "COMMON"
    HTT = "HTT"
    MIO = "MIO"
    BASS = "BASS"
    OBSSTAT = "OBSSTAT"
    TSC_LEGACY = "TSC_LEGACY"


class ClaimTier(StrEnum):
    """Machine-checkable claim tier vocabulary.

    The lower-case values preserve compatibility with existing VER2 artifacts.
    """

    EXPLORATORY = "exploratory"
    CONDITIONAL = "conditional"
    DIAGNOSTIC_ONLY = "diagnostic_only"
    VALIDATED = "validated"
    BLOCKED = "blocked"


class ImplementationScope(StrEnum):
    """Machine-checkable implementation-scope vocabulary."""

    BASS_PY = "bass_py"
    BASS_RS = "bass_rs"
    BASS_NATIVE = "canonical_BASS"
    HTT = "htt"
    MIO = "mio"
    OBSSTAT = "obsstat"
    COMMON = "common"
    TSC_LEGACY = "tsc_legacy"


class ArtifactMode(StrEnum):
    """Artifact intent vocabulary independent of publication claim strength."""

    GOVERNANCE_DIAGNOSTIC = "governance_diagnostic"
    INTERNAL_EXPLORATORY = "internal_exploratory"
    EXTERNAL_AUDIT_CONDITIONED = "external_audit_conditioned"
    FORECAST_ONLY = "forecast_only"
    DISPLAY_ONLY_PRIOR_SENSITIVITY_SCHEMATIC = "display_only_prior_sensitivity_schematic"
    DISPLAY_ONLY_ERROR_BUDGET_SCHEMATIC = "display_only_error_budget_schematic"
    METHODS_NEGATIVE_RESULT = "methods_negative_result"
    PAPER_APPENDIX_CONDITIONED = "paper_appendix_conditioned"
    PAPER_MAIN_CANDIDATE = "paper_main_candidate"
    PAPER_MAIN_VALIDATED = "paper_main_validated"


class AllowedUse(StrEnum):
    """Allowed-use vocabulary for generated artifacts and plots."""

    INTERNAL_ONLY = "internal_only"
    EXTERNAL_AUDIT = "external_audit"
    PAPER_APPENDIX = "paper_appendix"
    PAPER_APPENDIX_BLOCKED_DEGENERACY = "paper_appendix_blocked_degeneracy"
    PAPER_MAIN = "paper_main"


class BundleKind(StrEnum):
    """Role-sensitive bundle classes for owner/firewall checks."""

    POSTERIOR = "posterior"
    DIAGNOSTIC_CERTIFICATE = "diagnostic_certificate"
    TRANSFER_ATLAS = "transfer_atlas"
    OBSERVABLE_FEATURES = "observable_features"
    COMMON_CONTRACT = "common_contract"
    LEGACY_REPRODUCTION = "legacy_reproduction"


def _enum_value(value: str | StrEnum) -> str:
    return value.value if isinstance(value, StrEnum) else str(value)


def normalize_owner(owner: str | Owner) -> Owner:
    """Return the canonical owner enum, mapping legacy TSC strings explicitly."""

    if owner == "TSC":
        return Owner.TSC_LEGACY
    return Owner(_enum_value(owner))


def normalize_claim_tier(claim_tier: str | ClaimTier) -> ClaimTier:
    return ClaimTier(_enum_value(claim_tier))


def normalize_implementation_scope(
    implementation_scope: str | ImplementationScope,
) -> ImplementationScope:
    value = _enum_value(implementation_scope)
    if value == "tsc":
        return ImplementationScope.TSC_LEGACY
    return ImplementationScope(value)


def normalize_bundle_kind(bundle_kind: str | BundleKind) -> BundleKind:
    return BundleKind(_enum_value(bundle_kind))


_ALLOWED_OWNERS = {owner.value for owner in Owner}
_ALLOWED_CLAIM_TIERS = {claim_tier.value for claim_tier in ClaimTier}
_ALLOWED_IMPLEMENTATION_SCOPES = {scope.value for scope in ImplementationScope}
_ALLOWED_BUNDLES_BY_OWNER = {
    Owner.COMMON: {BundleKind.COMMON_CONTRACT},
    Owner.HTT: {BundleKind.POSTERIOR},
    Owner.MIO: {BundleKind.DIAGNOSTIC_CERTIFICATE},
    Owner.BASS: {BundleKind.TRANSFER_ATLAS},
    Owner.OBSSTAT: {BundleKind.OBSERVABLE_FEATURES},
    Owner.TSC_LEGACY: {BundleKind.LEGACY_REPRODUCTION},
}
_ALLOWED_PRODUCTION_STATUSES = {
    "diagnostic_only",
    "production_candidate",
    "production_validated",
    "blocked_missing_covariance",
    "blocked_missing_null_mocks",
    "blocked_missing_atlas",
    "blocked_provenance_mismatch",
    "blocked_rank_deficient",
    "blocked_owner_violation",
}
_ALLOWED_ARTIFACT_READINESS = {
    "missing",
    "generated",
    "smoke_tested",
    "validation_candidate",
    "production_validated",
    "blocked",
}
_ALLOWED_ARTIFACT_MODES = {mode.value for mode in ArtifactMode}
_ALLOWED_ALLOWED_USES = {use.value for use in AllowedUse}
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
_ALLOWED_QUADRUPOLE_CONVENTIONS = {"mu2_minus_one_third", "legendre_P2"}
_ALLOWED_QUADRUPOLE_PARAMETER_NAMES = {"Q_mu", "q"}

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


ProductionStatus = Literal[
    "diagnostic_only",
    "production_candidate",
    "production_validated",
    "blocked_missing_covariance",
    "blocked_missing_null_mocks",
    "blocked_missing_atlas",
    "blocked_provenance_mismatch",
    "blocked_rank_deficient",
    "blocked_owner_violation",
]
ArtifactReadiness = Literal[
    "missing",
    "generated",
    "smoke_tested",
    "validation_candidate",
    "production_validated",
    "blocked",
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
QuadrupoleConvention = Literal["mu2_minus_one_third", "legendre_P2"]
QuadrupoleParameterName = Literal["Q_mu", "q"]


def owner_can_emit_bundle(
    owner: str | Owner,
    bundle_kind: str | BundleKind,
) -> bool:
    canonical_owner = normalize_owner(owner)
    canonical_kind = normalize_bundle_kind(bundle_kind)
    return canonical_kind in _ALLOWED_BUNDLES_BY_OWNER[canonical_owner]


def assert_owner_can_emit_bundle(
    owner: str | Owner,
    bundle_kind: str | BundleKind,
) -> None:
    canonical_owner = normalize_owner(owner)
    canonical_kind = normalize_bundle_kind(bundle_kind)
    if not owner_can_emit_bundle(canonical_owner, canonical_kind):
        raise ValueError(
            f"{canonical_owner.value} cannot own {canonical_kind.value} bundle"
        )


def _set_canonical_owner(instance: object, field_name: str = "owner") -> Owner:
    raw_owner = getattr(instance, field_name)
    try:
        owner = normalize_owner(raw_owner)
    except ValueError as exc:
        raise ValueError(f"Unknown {field_name} {raw_owner!r}") from exc
    object.__setattr__(instance, field_name, owner)
    return owner


def _set_canonical_claim_tier(
    instance: object,
    field_name: str = "claim_tier",
) -> ClaimTier:
    raw_claim_tier = getattr(instance, field_name)
    try:
        claim_tier = normalize_claim_tier(raw_claim_tier)
    except ValueError as exc:
        raise ValueError(f"Unknown {field_name} {raw_claim_tier!r}") from exc
    object.__setattr__(instance, field_name, claim_tier)
    return claim_tier


def _set_canonical_implementation_scope(
    instance: object,
    field_name: str = "implementation_scope",
) -> ImplementationScope:
    raw_scope = getattr(instance, field_name)
    try:
        scope = normalize_implementation_scope(raw_scope)
    except ValueError as exc:
        raise ValueError(f"Unknown {field_name} {raw_scope!r}") from exc
    object.__setattr__(instance, field_name, scope)
    return scope


def _require_manifest_owner(
    manifest: "ArtifactManifest",
    owner: Owner,
    context: str,
) -> None:
    if normalize_owner(manifest.owner) is not owner:
        raise ValueError(
            f"{context}.manifest.owner must be {owner.value!r} "
            f"(got {manifest.owner!r})"
        )


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
    artifact_mode: ArtifactMode = ArtifactMode.GOVERNANCE_DIAGNOSTIC
    allowed_use: AllowedUse = AllowedUse.INTERNAL_ONLY
    caption_policy: list[str] = field(default_factory=list)
    numeric_payload_path: str = ""
    promotion_blockers: list[str] = field(default_factory=list)
    report_generation_gates: dict[str, str] = field(default_factory=dict)
    science_promotion_gates: dict[str, str] = field(default_factory=dict)
    publication_gates: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.artifact_id:
            raise ValueError("ArtifactManifest.artifact_id must be non-empty")
        if not self.artifact_path:
            raise ValueError("ArtifactManifest.artifact_path must be non-empty")
        _set_canonical_owner(self)
        _set_canonical_implementation_scope(self)
        _set_canonical_claim_tier(self)
        if not isinstance(self.artifact_mode, ArtifactMode):
            object.__setattr__(self, "artifact_mode", ArtifactMode(str(self.artifact_mode)))
        if not isinstance(self.allowed_use, AllowedUse):
            object.__setattr__(self, "allowed_use", AllowedUse(str(self.allowed_use)))
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
    """Canonical sky-support metadata shared by sky-facing surfaces."""

    selection_mode: str
    sky_support_hash: str
    mask_hash: str
    mock_coverage_status: str
    scan_volume_hash: str = ""
    coordinate_frame: str = "legacy_unspecified"
    sky_fraction: float | None = None
    completeness_status: str = "legacy_unspecified"
    pixelization: str = "legacy_unspecified"
    nside: int | None = None

    def __post_init__(self) -> None:
        if not self.selection_mode:
            raise ValueError("SkySupport.selection_mode must be non-empty")
        if not self.sky_support_hash:
            raise ValueError("SkySupport.sky_support_hash must be non-empty")
        if not self.mask_hash:
            raise ValueError("SkySupport.mask_hash must be non-empty")
        if not self.mock_coverage_status:
            raise ValueError("SkySupport.mock_coverage_status must be non-empty")
        if not self.coordinate_frame:
            raise ValueError("SkySupport.coordinate_frame must be non-empty")
        if self.sky_fraction is not None:
            sky_fraction = float(self.sky_fraction)
            if not np.isfinite(sky_fraction) or not (0.0 <= sky_fraction <= 1.0):
                raise ValueError(
                    "SkySupport.sky_fraction must be finite and in [0, 1]"
                )
            object.__setattr__(self, "sky_fraction", sky_fraction)
        if not self.completeness_status:
            raise ValueError("SkySupport.completeness_status must be non-empty")
        if not self.pixelization:
            raise ValueError("SkySupport.pixelization must be non-empty")
        if self.nside is not None and int(self.nside) <= 0:
            raise ValueError("SkySupport.nside must be positive when provided")
        if self.nside is not None:
            object.__setattr__(self, "nside", int(self.nside))

    def to_metadata(self) -> dict[str, object]:
        """Return a JSON-compatible sky-support metadata payload."""

        return {
            "selection_mode": self.selection_mode,
            "sky_support_hash": self.sky_support_hash,
            "mask_hash": self.mask_hash,
            "mock_coverage_status": self.mock_coverage_status,
            "scan_volume_hash": self.scan_volume_hash,
            "coordinate_frame": self.coordinate_frame,
            "sky_fraction": self.sky_fraction,
            "completeness_status": self.completeness_status,
            "pixelization": self.pixelization,
            "nside": self.nside,
        }


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
    artifact_readiness: ArtifactReadiness = "missing"
    artifact_mode: ArtifactMode = ArtifactMode.GOVERNANCE_DIAGNOSTIC
    allowed_use: AllowedUse = AllowedUse.INTERNAL_ONLY
    caption_policy: tuple[str, ...] = ()
    promotion_blockers: tuple[str, ...] = ()
    report_generation_gates: dict[str, str] = field(default_factory=dict)
    science_promotion_gates: dict[str, str] = field(default_factory=dict)
    publication_gates: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _set_canonical_owner(self)
        _set_canonical_implementation_scope(self)
        _set_canonical_claim_tier(self)
        if self.artifact_readiness not in _ALLOWED_ARTIFACT_READINESS:
            raise ValueError(
                f"Unknown artifact_readiness {self.artifact_readiness!r}"
            )
        if not isinstance(self.artifact_mode, ArtifactMode):
            object.__setattr__(self, "artifact_mode", ArtifactMode(str(self.artifact_mode)))
        if not isinstance(self.allowed_use, AllowedUse):
            object.__setattr__(self, "allowed_use", AllowedUse(str(self.allowed_use)))
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
        _set_canonical_owner(self)
        _set_canonical_claim_tier(self)
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
        owner = _set_canonical_owner(self)
        if owner is not Owner.BASS:
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
        _set_canonical_claim_tier(self)
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
        # Honest map-output contract (audit P-08, 2026-04-26): the
        # ``map_T/Q/U`` fields are typed pass-throughs that no production
        # path currently populates. Require an explicit
        # ``map_output_support`` flag so that callers cannot silently
        # carry ``None`` while claiming map-level outputs.
        map_status = self.metadata.get("map_output_support")
        if map_status is None:
            raise ValueError(
                "SolverCoreOutput.metadata must declare 'map_output_support' "
                "explicitly; allowed values are 'not_implemented' (maps must "
                "be None) or 'producer_attached' (maps must be non-None)"
            )
        if map_status not in {"not_implemented", "producer_attached"}:
            raise ValueError(
                f"unknown map_output_support {map_status!r}; "
                "expected 'not_implemented' or 'producer_attached'"
            )
        maps = (self.map_T, self.map_Q, self.map_U)
        if map_status == "not_implemented" and any(m is not None for m in maps):
            raise ValueError(
                "map_output_support='not_implemented' but map_T/Q/U is non-None; "
                "either populate the producer and switch the flag to "
                "'producer_attached' or drop the maps to None"
            )
        if map_status == "producer_attached" and any(m is None for m in maps):
            raise ValueError(
                "map_output_support='producer_attached' but at least one of "
                "map_T/Q/U is None; populate all three or downgrade the flag"
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
        _require_manifest_owner(self.manifest, Owner.BASS, "AtlasEntryLite")


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
            {_enum_value(value) for value in self.claim_tier_by_pair.values()}
            - _ALLOWED_CLAIM_TIERS
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
        _require_manifest_owner(self.manifest, Owner.TSC_LEGACY, "TscDomainReport")


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
        _require_manifest_owner(self.manifest, Owner.TSC_LEGACY, "TscResidualReport")


@dataclass(frozen=True)
class TscSourceBridgeReport:
    """TSC trace-source bridge report."""

    source_name: Literal["thomson_trace_quadrupole", "other"]
    chart: TscChart
    quadrupole_convention: QuadrupoleConvention
    quadrupole_parameter_name: QuadrupoleParameterName
    conversion_to_legendre_q: float
    q2_norm: float
    source_error_bound: float | None
    nonlinear_dipole_quartic_correction: float | None
    eta_correction_indicator: float | None
    on_manifold_exact: bool
    spin2_propagation_required: bool
    source_status: SourceStatus
    required_bass_primitives: tuple[str, ...]
    labels: tuple[str, ...]
    manifest: ArtifactManifest

    def __post_init__(self) -> None:
        if self.chart not in _ALLOWED_TSC_CHARTS:
            raise ValueError(f"Unknown TSC chart {self.chart!r}")
        if self.quadrupole_convention not in _ALLOWED_QUADRUPOLE_CONVENTIONS:
            raise ValueError(
                f"Unknown quadrupole_convention {self.quadrupole_convention!r}"
            )
        if self.quadrupole_parameter_name not in _ALLOWED_QUADRUPOLE_PARAMETER_NAMES:
            raise ValueError(
                "Unknown quadrupole_parameter_name "
                f"{self.quadrupole_parameter_name!r}"
            )
        if self.source_status not in _ALLOWED_SOURCE_STATUSES:
            raise ValueError(f"Unknown source_status {self.source_status!r}")
        _require_manifest_owner(self.manifest, Owner.TSC_LEGACY, "TscSourceBridgeReport")


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
        if _enum_value(self.claim_ceiling) not in _ALLOWED_CLAIM_TIERS:
            raise ValueError(f"Unknown claim_ceiling {self.claim_ceiling!r}")
        _require_manifest_owner(self.manifest, Owner.TSC_LEGACY, "TscChannelAdequacyBudget")


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
        _require_manifest_owner(self.manifest, Owner.TSC_LEGACY, "TscUpgradeRecommendation")


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
        _require_manifest_owner(self.manifest, Owner.TSC_LEGACY, "TscAdequacyOverlay")
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
