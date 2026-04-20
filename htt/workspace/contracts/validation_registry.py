"""Package-neutral VER2 validation and hostile-audit registry contracts."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal


ValidationStatus = Literal["pass", "warn", "fail"]
ValidationCategory = Literal[
    "baseline_reproduction",
    "adversarial_edge",
    "physics_sanity",
    "numerical_stability",
    "regression",
]

_ALLOWED_OWNERS = {"BASS", "HTT", "MIO", "TSC", "COMMON"}
_ALLOWED_SCOPES = {
    "bass_py",
    "bass_rs",
    "canonical_BASS",
    "htt",
    "mio",
    "tsc",
    "common",
}
_ALLOWED_STATUSES = {"pass", "warn", "fail"}
_ALLOWED_CATEGORIES = {
    "baseline_reproduction",
    "adversarial_edge",
    "physics_sanity",
    "numerical_stability",
    "regression",
}


@dataclass(frozen=True)
class ValidationTestLink:
    """One theorem-linked test or verification witness."""

    test_id: str
    category: ValidationCategory
    path: str
    purpose: str
    artifact_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.test_id:
            raise ValueError("ValidationTestLink.test_id must be non-empty")
        if self.category not in _ALLOWED_CATEGORIES:
            raise ValueError(f"Unknown validation category {self.category!r}")
        if not self.path:
            raise ValueError("ValidationTestLink.path must be non-empty")
        if not self.purpose:
            raise ValueError("ValidationTestLink.purpose must be non-empty")


@dataclass(frozen=True)
class TheoremToTestEntry:
    """Machine-readable theorem/proof-obligation to test mapping."""

    theorem_id: str
    theorem_label: str
    owner: str
    implementation_scope: str
    claim_guard: str
    source_docs: tuple[str, ...]
    test_links: tuple[ValidationTestLink, ...]
    artifact_refs: tuple[str, ...]
    no_claim_conditions: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.theorem_id:
            raise ValueError("TheoremToTestEntry.theorem_id must be non-empty")
        if not self.theorem_label:
            raise ValueError("TheoremToTestEntry.theorem_label must be non-empty")
        if self.owner not in _ALLOWED_OWNERS:
            raise ValueError(f"Unknown owner {self.owner!r}")
        if self.implementation_scope not in _ALLOWED_SCOPES:
            raise ValueError(
                f"Unknown implementation_scope {self.implementation_scope!r}"
            )
        if not self.claim_guard:
            raise ValueError("TheoremToTestEntry.claim_guard must be non-empty")
        if not self.source_docs:
            raise ValueError("TheoremToTestEntry.source_docs must be non-empty")
        if not self.test_links:
            raise ValueError("TheoremToTestEntry.test_links must be non-empty")
        if not self.artifact_refs:
            raise ValueError("TheoremToTestEntry.artifact_refs must be non-empty")
        if not self.no_claim_conditions:
            raise ValueError(
                "TheoremToTestEntry.no_claim_conditions must be non-empty"
            )


@dataclass(frozen=True)
class ValidationCampaign:
    """Package-neutral validation campaign registry row."""

    campaign_id: str
    title: str
    owner: str
    implementation_scope: str
    status: ValidationStatus
    theorem_refs: tuple[str, ...]
    categories: tuple[ValidationCategory, ...]
    artifact_refs: tuple[str, ...]
    manuscript_blocking: bool
    no_claim_conditions: tuple[str, ...]
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.campaign_id:
            raise ValueError("ValidationCampaign.campaign_id must be non-empty")
        if not self.title:
            raise ValueError("ValidationCampaign.title must be non-empty")
        if self.owner not in _ALLOWED_OWNERS:
            raise ValueError(f"Unknown owner {self.owner!r}")
        if self.implementation_scope not in _ALLOWED_SCOPES:
            raise ValueError(
                f"Unknown implementation_scope {self.implementation_scope!r}"
            )
        if self.status not in _ALLOWED_STATUSES:
            raise ValueError(f"Unknown validation status {self.status!r}")
        if not self.theorem_refs:
            raise ValueError("ValidationCampaign.theorem_refs must be non-empty")
        if not self.categories:
            raise ValueError("ValidationCampaign.categories must be non-empty")
        if not self.artifact_refs:
            raise ValueError("ValidationCampaign.artifact_refs must be non-empty")
        if not self.no_claim_conditions:
            raise ValueError(
                "ValidationCampaign.no_claim_conditions must be non-empty"
            )
        invalid = sorted(set(self.categories) - _ALLOWED_CATEGORIES)
        if invalid:
            raise ValueError(f"Unknown validation categories {invalid}")

    @property
    def promotes_to_validated(self) -> bool:
        return self.status == "pass"


@dataclass(frozen=True)
class NullEnsembleManifest:
    """Declared null ensemble for calibration and false-promotion checks."""

    ensemble_id: str
    null_family: str
    observable_basis: str
    scan_volume_hash: str
    status: ValidationStatus
    artifact_refs: tuple[str, ...]
    no_claim_conditions: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.ensemble_id:
            raise ValueError("NullEnsembleManifest.ensemble_id must be non-empty")
        if not self.null_family:
            raise ValueError("NullEnsembleManifest.null_family must be non-empty")
        if not self.observable_basis:
            raise ValueError(
                "NullEnsembleManifest.observable_basis must be non-empty"
            )
        if not self.scan_volume_hash:
            raise ValueError(
                "NullEnsembleManifest.scan_volume_hash must be non-empty"
            )
        if self.status not in _ALLOWED_STATUSES:
            raise ValueError(f"Unknown validation status {self.status!r}")
        if not self.artifact_refs:
            raise ValueError("NullEnsembleManifest.artifact_refs must be non-empty")
        if not self.no_claim_conditions:
            raise ValueError(
                "NullEnsembleManifest.no_claim_conditions must be non-empty"
            )


@dataclass(frozen=True)
class InjectionCampaignManifest:
    """Declared injection-recovery campaign for calibration-only use."""

    injection_id: str
    hypothesis_family: str
    target_statistic: str
    scan_volume_hash: str
    status: ValidationStatus
    artifact_refs: tuple[str, ...]
    downgrade_conditions: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.injection_id:
            raise ValueError(
                "InjectionCampaignManifest.injection_id must be non-empty"
            )
        if not self.hypothesis_family:
            raise ValueError(
                "InjectionCampaignManifest.hypothesis_family must be non-empty"
            )
        if not self.target_statistic:
            raise ValueError(
                "InjectionCampaignManifest.target_statistic must be non-empty"
            )
        if not self.scan_volume_hash:
            raise ValueError(
                "InjectionCampaignManifest.scan_volume_hash must be non-empty"
            )
        if self.status not in _ALLOWED_STATUSES:
            raise ValueError(f"Unknown validation status {self.status!r}")
        if not self.artifact_refs:
            raise ValueError(
                "InjectionCampaignManifest.artifact_refs must be non-empty"
            )
        if not self.downgrade_conditions:
            raise ValueError(
                "InjectionCampaignManifest.downgrade_conditions must be non-empty"
            )


@dataclass(frozen=True)
class HostileAuditRunbook:
    """Runbook grouping checks by validation category."""

    runbook_id: str
    title: str
    owner: str
    implementation_scope: str
    theorem_refs: tuple[str, ...]
    baseline_checks: tuple[str, ...]
    adversarial_checks: tuple[str, ...]
    physics_checks: tuple[str, ...]
    numerical_checks: tuple[str, ...]
    regression_checks: tuple[str, ...]
    quarantine_conditions: tuple[str, ...]
    artifact_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.runbook_id:
            raise ValueError("HostileAuditRunbook.runbook_id must be non-empty")
        if not self.title:
            raise ValueError("HostileAuditRunbook.title must be non-empty")
        if self.owner not in _ALLOWED_OWNERS:
            raise ValueError(f"Unknown owner {self.owner!r}")
        if self.implementation_scope not in _ALLOWED_SCOPES:
            raise ValueError(
                f"Unknown implementation_scope {self.implementation_scope!r}"
            )
        if not self.theorem_refs:
            raise ValueError("HostileAuditRunbook.theorem_refs must be non-empty")
        if not self.baseline_checks:
            raise ValueError("HostileAuditRunbook.baseline_checks must be non-empty")
        if not self.adversarial_checks:
            raise ValueError(
                "HostileAuditRunbook.adversarial_checks must be non-empty"
            )
        if not self.physics_checks:
            raise ValueError("HostileAuditRunbook.physics_checks must be non-empty")
        if not self.numerical_checks:
            raise ValueError(
                "HostileAuditRunbook.numerical_checks must be non-empty"
            )
        if not self.regression_checks:
            raise ValueError(
                "HostileAuditRunbook.regression_checks must be non-empty"
            )
        if not self.quarantine_conditions:
            raise ValueError(
                "HostileAuditRunbook.quarantine_conditions must be non-empty"
            )
        if not self.artifact_refs:
            raise ValueError("HostileAuditRunbook.artifact_refs must be non-empty")


def manuscript_export_blocked(campaigns: tuple[ValidationCampaign, ...]) -> bool:
    """A fail in any manuscript-blocking campaign blocks export."""
    return any(
        campaign.manuscript_blocking and campaign.status == "fail"
        for campaign in campaigns
    )


def build_default_theorem_to_test_map() -> tuple[TheoremToTestEntry, ...]:
    return (
        TheoremToTestEntry(
            theorem_id="V8_isotropic_limit_recovery",
            theorem_label="FLRW isotropic limit recovers zero anisotropic morphology",
            owner="BASS",
            implementation_scope="canonical_BASS",
            claim_guard="anisotropic outputs must recover the isotropic null before any promotion",
            source_docs=(
                "docs/ver2_upgrade/BASS_HTT_MIO_TSC_observable_atlas_SDD_WBS_PR_plan.md",
                "docs/ver2_upgrade/VER2_PHASE_PROMPTS_01_SKELETON_PREIMPLANT.md",
            ),
            test_links=(
                ValidationTestLink(
                    test_id="flrw_limit_zero_offdiag",
                    category="baseline_reproduction",
                    path="htt/bass/spectrum/test_fb72_off_diagonal_covariance_skeleton.py::test_fb72_type_i_off_diagonal_vanishes_identically",
                    purpose="off-diagonal blocks vanish in the isotropic/type-I limit",
                    artifact_refs=("bass.observable_vector.proxy",),
                ),
            ),
            artifact_refs=("bass.observable_vector.proxy", "bass.full_cov_mes_report"),
            no_claim_conditions=("missing_observable_vector", "sparse_proxy_only"),
        ),
        TheoremToTestEntry(
            theorem_id="V8_biposh_Lgt0_null_or_proxy_block",
            theorem_label="BiPoSH/off-diagonal morphology must vanish in the isotropic null or stay blocked as proxy-only",
            owner="BASS",
            implementation_scope="bass_py",
            claim_guard="proxy sparse morphology may not be promoted as invariant BiPoSH evidence",
            source_docs=(
                "docs/ver2_upgrade/mes_full_covariance_extension_self_contained.md",
                "docs/ver2_upgrade/BASS_HTT_MIO_TSC_observable_atlas_SDD_WBS_PR_plan.md",
            ),
            test_links=(
                ValidationTestLink(
                    test_id="proxy_mode_records_no_claim",
                    category="physics_sanity",
                    path="htt/bass/observational/test_ver2_observable_atlas.py::test_covariance_proxy_and_feature_summary_record_guards",
                    purpose="proxy morphology exports explicit caveats rather than invariant claims",
                    artifact_refs=("bass.observable_vector.proxy",),
                ),
            ),
            artifact_refs=("bass.observable_vector.proxy",),
            no_claim_conditions=("sparse_mode_block_proxy", "missing_biposh_basis"),
        ),
        TheoremToTestEntry(
            theorem_id="V8_template_injection_recovery",
            theorem_label="deterministic template injections must be tracked with explicit scan-volume metadata",
            owner="HTT",
            implementation_scope="htt",
            claim_guard="injection recovery claims require declared null/injection manifests",
            source_docs=(
                "docs/ver2_upgrade/BASS_HTT_MIO_TSC_observable_atlas_SDD_WBS_PR_plan.md",
            ),
            test_links=(
                ValidationTestLink(
                    test_id="template_injection_manifest_declared",
                    category="adversarial_edge",
                    path="tests/validation/test_template_injection_recovery.py",
                    purpose="planned injection-recovery gate referenced by the campaign registry",
                    artifact_refs=("validation.injection.template_amplitude",),
                ),
            ),
            artifact_refs=("validation.injection.template_amplitude",),
            no_claim_conditions=("missing_injection_campaign", "missing_scan_volume"),
        ),
        TheoremToTestEntry(
            theorem_id="V8_mes_rank_no_claim",
            theorem_label="MES covariance rank failure is an explicit no-claim condition",
            owner="BASS",
            implementation_scope="bass_py",
            claim_guard="rank-deficient covariance upgrades may not be interpreted as weak evidence",
            source_docs=(
                "docs/ver2_upgrade/mes_full_covariance_extension_self_contained.md",
                "docs/ver2_upgrade/audits/AUDIT_SK-04O_2026-04-21.md",
            ),
            test_links=(
                ValidationTestLink(
                    test_id="mes_rank_failure_returns_no_claim",
                    category="adversarial_edge",
                    path="htt/bass/observational/test_ver2_mes_departure.py::test_full_cov_mes_rank_failure_returns_no_claim",
                    purpose="rank deficiency blocks covariance claims",
                    artifact_refs=("bass.full_cov_mes_report",),
                ),
            ),
            artifact_refs=("bass.full_cov_mes_report",),
            no_claim_conditions=("response_rank_deficient", "missing_covariance_features"),
        ),
        TheoremToTestEntry(
            theorem_id="V8_filling_requires_certification",
            theorem_label="Filling fraction language requires certification and admissible ceilings",
            owner="COMMON",
            implementation_scope="common",
            claim_guard="uncertified normalized scores remain Q/proxy surfaces, not F",
            source_docs=(
                "docs/ver2_upgrade/x_Q_Pi_F_G_model_independent_framework_upgrade.md",
                "docs/ver2_upgrade/audits/AUDIT_SK-04O_2026-04-21.md",
            ),
            test_links=(
                ValidationTestLink(
                    test_id="uncertified_f_downgrades_to_proxy",
                    category="physics_sanity",
                    path="htt/bass/observational/test_ver2_mes_departure.py::test_departure_report_stays_descriptive_without_claim_gate",
                    purpose="Q/F semantics stay separated when gates are not passed",
                    artifact_refs=("common.departure_report",),
                ),
            ),
            artifact_refs=("common.departure_report",),
            no_claim_conditions=("claim_gate_not_passed", "occupancy_not_certified"),
        ),
        TheoremToTestEntry(
            theorem_id="V8_local_vs_global_discrimination",
            theorem_label="local boost and global tilt remain distinct discrimination hypotheses",
            owner="HTT",
            implementation_scope="htt",
            claim_guard="observer-side local boost may not be promoted to a source/background tilt claim",
            source_docs=(
                "docs/ver2_upgrade/BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN_critical_upgraded.md",
                "docs/ver2_upgrade/audits/AUDIT_SK-06H_2026-04-21.md",
            ),
            test_links=(
                ValidationTestLink(
                    test_id="local_boost_not_promoted_to_global",
                    category="adversarial_edge",
                    path="tests/validation/test_local_boost_not_promoted_to_global.py",
                    purpose="planned false-promotion gate for observer-vs-source discrimination",
                    artifact_refs=("htt.discrimination_matrix",),
                ),
            ),
            artifact_refs=("htt.discrimination_matrix",),
            no_claim_conditions=("missing_response_library", "missing_null_ensemble"),
        ),
        TheoremToTestEntry(
            theorem_id="V8_tsc_no_overclaim",
            theorem_label="TSC caveat overlays do not promote posterior or runtime ownership",
            owner="TSC",
            implementation_scope="tsc",
            claim_guard="TSC remains advisory and quarantines overclaim rather than emitting truth labels",
            source_docs=(
                "docs/ver2_upgrade/TSC_active_service_SDD_WBS_PR_plan.md",
            ),
            test_links=(
                ValidationTestLink(
                    test_id="tsc_overlay_remains_advisory",
                    category="regression",
                    path="htt/tsc/test_theorem_map_contains_core_tests.py",
                    purpose="planned theorem-map coverage for TSC no-overclaim gates",
                    artifact_refs=("tsc.adequacy_overlay",),
                ),
            ),
            artifact_refs=("tsc.adequacy_overlay",),
            no_claim_conditions=("missing_tsc_overlay", "posterior_correction_attempted"),
        ),
    )


def build_default_validation_campaigns() -> tuple[ValidationCampaign, ...]:
    return (
        ValidationCampaign(
            campaign_id="validation.flrw_baseline",
            title="FLRW baseline recovery and proxy quarantine",
            owner="COMMON",
            implementation_scope="common",
            status="warn",
            theorem_refs=(
                "V8_isotropic_limit_recovery",
                "V8_biposh_Lgt0_null_or_proxy_block",
            ),
            categories=("baseline_reproduction", "regression"),
            artifact_refs=("bass.observable_vector.proxy", "bass.full_cov_mes_report"),
            manuscript_blocking=True,
            no_claim_conditions=("sparse_proxy_only", "missing_biposh_basis"),
            notes=("warn until executable BiPoSH/covariance campaign exists",),
        ),
        ValidationCampaign(
            campaign_id="validation.false_promotion",
            title="false-promotion and discrimination quarantine",
            owner="COMMON",
            implementation_scope="common",
            status="warn",
            theorem_refs=(
                "V8_local_vs_global_discrimination",
                "V8_tsc_no_overclaim",
            ),
            categories=("adversarial_edge", "regression"),
            artifact_refs=("htt.discrimination_matrix", "tsc.adequacy_overlay"),
            manuscript_blocking=True,
            no_claim_conditions=("missing_null_ensemble", "posterior_correction_attempted"),
            notes=("warn until local/global mock calibration is executable",),
        ),
        ValidationCampaign(
            campaign_id="validation.mes_no_claim",
            title="full-covariance MES no-claim and ceiling audit",
            owner="BASS",
            implementation_scope="bass_py",
            status="warn",
            theorem_refs=(
                "V8_mes_rank_no_claim",
                "V8_filling_requires_certification",
            ),
            categories=("physics_sanity", "numerical_stability"),
            artifact_refs=("bass.full_cov_mes_report", "common.departure_report"),
            manuscript_blocking=True,
            no_claim_conditions=("response_rank_deficient", "claim_gate_not_passed"),
            notes=("warn until executable nuisance/noise model replaces skeleton bound",),
        ),
    )


def build_default_null_manifests() -> tuple[NullEnsembleManifest, ...]:
    return (
        NullEnsembleManifest(
            ensemble_id="null.flrw_isotropic_gaussian_lowell",
            null_family="flrw_isotropic_gaussian",
            observable_basis="lowell_alm_features",
            scan_volume_hash="scan.flrw.lowell.v1",
            status="warn",
            artifact_refs=("validation.null.flrw_isotropic_gaussian_lowell",),
            no_claim_conditions=("missing_scan_volume", "missing_tail_calibration"),
        ),
        NullEnsembleManifest(
            ensemble_id="null.local_boost_only",
            null_family="observer_local_boost_only",
            observable_basis="directional_power_and_coherence",
            scan_volume_hash="scan.local_boost.v1",
            status="warn",
            artifact_refs=("validation.null.local_boost_only",),
            no_claim_conditions=("missing_null_identity", "missing_false_promotion_check"),
        ),
    )


def build_default_injection_manifests() -> tuple[InjectionCampaignManifest, ...]:
    return (
        InjectionCampaignManifest(
            injection_id="validation.injection.template_amplitude",
            hypothesis_family="deterministic_template",
            target_statistic="template_amplitude_recovery",
            scan_volume_hash="scan.template.injection.v1",
            status="warn",
            artifact_refs=("validation.injection.template_amplitude",),
            downgrade_conditions=("missing_injection_grid", "missing_recovery_tolerance"),
        ),
        InjectionCampaignManifest(
            injection_id="validation.injection.anisotropic_covariance",
            hypothesis_family="anisotropic_covariance",
            target_statistic="covariance_feature_recovery",
            scan_volume_hash="scan.covariance.injection.v1",
            status="warn",
            artifact_refs=("validation.injection.anisotropic_covariance",),
            downgrade_conditions=("covariance_sampler_unavailable", "proxy_mode_only"),
        ),
    )


def build_default_hostile_audit_runbooks() -> tuple[HostileAuditRunbook, ...]:
    return (
        HostileAuditRunbook(
            runbook_id="runbook.observable_promotion",
            title="Observable promotion hostile audit",
            owner="COMMON",
            implementation_scope="common",
            theorem_refs=(
                "V8_isotropic_limit_recovery",
                "V8_biposh_Lgt0_null_or_proxy_block",
                "V8_mes_rank_no_claim",
            ),
            baseline_checks=("recover_flrw_limit",),
            adversarial_checks=("proxy_not_promoted_as_biposh", "rank_failure_not_spun_as_signal"),
            physics_checks=("diagonal_only_not_sufficient", "no_claim_conditions_explicit"),
            numerical_checks=("psd_guard_present", "scan_volume_hash_recorded"),
            regression_checks=("observable_manifest_owner_scope",),
            quarantine_conditions=("sparse_proxy_only", "response_rank_deficient"),
            artifact_refs=("bass.observable_vector.proxy", "bass.full_cov_mes_report"),
        ),
        HostileAuditRunbook(
            runbook_id="runbook.semantic_firewall",
            title="Semantic firewall hostile audit",
            owner="COMMON",
            implementation_scope="common",
            theorem_refs=(
                "V8_filling_requires_certification",
                "V8_local_vs_global_discrimination",
                "V8_tsc_no_overclaim",
            ),
            baseline_checks=("q_f_separation_preserved",),
            adversarial_checks=("local_boost_not_global_tilt", "tsc_not_posterior"),
            physics_checks=("certified_f_requires_admissible_ceiling",),
            numerical_checks=("manuscript_blocking_fail_semantics",),
            regression_checks=("workspace_schema_barrier",),
            quarantine_conditions=(
                "claim_gate_not_passed",
                "posterior_correction_attempted",
            ),
            artifact_refs=("common.departure_report", "htt.discrimination_matrix", "tsc.adequacy_overlay"),
        ),
    )


def validation_registry_payload() -> dict[str, object]:
    theorem_map = build_default_theorem_to_test_map()
    campaigns = build_default_validation_campaigns()
    nulls = build_default_null_manifests()
    injections = build_default_injection_manifests()
    runbooks = build_default_hostile_audit_runbooks()
    return {
        "theorem_map": [asdict(entry) for entry in theorem_map],
        "campaigns": [asdict(entry) for entry in campaigns],
        "null_manifests": [asdict(entry) for entry in nulls],
        "injection_manifests": [asdict(entry) for entry in injections],
        "hostile_audit_runbooks": [asdict(entry) for entry in runbooks],
        "manuscript_export_blocked": manuscript_export_blocked(campaigns),
    }


__all__ = [
    "HostileAuditRunbook",
    "InjectionCampaignManifest",
    "NullEnsembleManifest",
    "TheoremToTestEntry",
    "ValidationCampaign",
    "ValidationCategory",
    "ValidationStatus",
    "ValidationTestLink",
    "build_default_hostile_audit_runbooks",
    "build_default_injection_manifests",
    "build_default_null_manifests",
    "build_default_theorem_to_test_map",
    "build_default_validation_campaigns",
    "manuscript_export_blocked",
    "validation_registry_payload",
]
