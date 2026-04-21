"""Package-neutral VER2 validation and hostile-audit registry contracts."""
from __future__ import annotations

import ast
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal


ValidationStatus = Literal["pass", "warn", "fail"]
ValidationCategory = Literal[
    "baseline_reproduction",
    "adversarial_edge",
    "physics_sanity",
    "numerical_stability",
    "regression",
]

REQUIRED_VALIDATION_CATEGORIES: tuple[ValidationCategory, ...] = (
    "baseline_reproduction",
    "adversarial_edge",
    "physics_sanity",
    "numerical_stability",
    "regression",
)

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
_ALLOWED_CATEGORIES = set(REQUIRED_VALIDATION_CATEGORIES)


@dataclass(frozen=True)
class ValidationTestLink:
    """One theorem-linked or campaign-linked test witness."""

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
    check_links: tuple[ValidationTestLink, ...]
    artifact_refs: tuple[str, ...]
    manuscript_blocking: bool
    no_claim_conditions: tuple[str, ...]
    null_manifest_refs: tuple[str, ...] = ()
    injection_manifest_refs: tuple[str, ...] = ()
    runbook_refs: tuple[str, ...] = ()
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
        if not self.check_links:
            raise ValueError("ValidationCampaign.check_links must be non-empty")
        if not self.artifact_refs:
            raise ValueError("ValidationCampaign.artifact_refs must be non-empty")
        if not self.no_claim_conditions:
            raise ValueError(
                "ValidationCampaign.no_claim_conditions must be non-empty"
            )
        invalid = sorted(set(self.categories) - _ALLOWED_CATEGORIES)
        if invalid:
            raise ValueError(f"Unknown validation categories {invalid}")
        link_categories = {link.category for link in self.check_links}
        if set(self.categories) != link_categories:
            raise ValueError(
                "ValidationCampaign.categories must match ValidationCampaign.check_links"
            )

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
    theorem_refs: tuple[str, ...] = ()
    campaign_refs: tuple[str, ...] = ()

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
    theorem_refs: tuple[str, ...] = ()
    campaign_refs: tuple[str, ...] = ()
    required_null_refs: tuple[str, ...] = ()

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
    campaign_refs: tuple[str, ...]
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
        if not self.campaign_refs:
            raise ValueError("HostileAuditRunbook.campaign_refs must be non-empty")
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


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


@lru_cache(maxsize=None)
def _module_ast(path_str: str) -> ast.AST:
    path = Path(path_str)
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _path_targets_exist(path: str) -> bool:
    file_part, *qualifiers = path.split("::")
    file_path = _repo_root() / file_part
    if not file_path.exists():
        return False
    if not qualifiers:
        return True
    node: ast.AST = _module_ast(str(file_path))
    body = getattr(node, "body", ())
    for qualifier in qualifiers:
        match = next(
            (
                child
                for child in body
                if isinstance(
                    child,
                    (ast.AsyncFunctionDef, ast.ClassDef, ast.FunctionDef),
                )
                and child.name == qualifier
            ),
            None,
        )
        if match is None:
            return False
        body = getattr(match, "body", ())
    return True


def validation_test_path_exists(path: str) -> bool:
    """Return True when a repo-relative test target resolves to a live symbol."""

    return _path_targets_exist(path)


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
                ValidationTestLink(
                    test_id="type_i_observable_marks_isotropic_null_proxy",
                    category="regression",
                    path="htt/bass/observational/test_ver2_observable_atlas.py::test_live_tier_b_type_i_observable_marks_isotropic_null_proxy",
                    purpose="the live Tier-B observable export preserves the isotropic-null proxy label",
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
                    test_id="rotating_types_activate_offdiag_blocks",
                    category="adversarial_edge",
                    path="htt/bass/spectrum/test_fb72_off_diagonal_covariance_skeleton.py::test_fb72_anisotropic_types_produce_nonzero_off_diagonal_blocks",
                    purpose="anisotropic structures remain distinguishable from the isotropic null",
                    artifact_refs=("bass.observable_vector.proxy",),
                ),
                ValidationTestLink(
                    test_id="proxy_mode_records_no_claim",
                    category="physics_sanity",
                    path="htt/bass/observational/test_ver2_observable_atlas.py::test_covariance_proxy_and_feature_summary_record_guards",
                    purpose="proxy morphology exports explicit caveats rather than invariant claims",
                    artifact_refs=("bass.observable_vector.proxy",),
                ),
            ),
            artifact_refs=("bass.observable_vector.proxy",),
            no_claim_conditions=(
                "sparse_mode_block_proxy",
                "basis_reduced_not_full_biposh",
                "missing_biposh_basis",
            ),
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
                    test_id="injected_dipole_projection_recovered",
                    category="adversarial_edge",
                    path="htt/src/common/test_mock_calibration.py::TestMockGeneration::test_injected_dipole_reproduces_projection",
                    purpose="synthetic injections remain explicitly identified rather than folded into null logic",
                    artifact_refs=("validation.injection.template_amplitude",),
                ),
                ValidationTestLink(
                    test_id="synthetic_injection_coverage_reaches_nominal_band",
                    category="numerical_stability",
                    path="htt/bass/inference/test_fb115_synthetic_injection_skeleton.py::test_fb115_synthetic_injection_coverage_reaches_nominal_band",
                    purpose="the synthetic injection bank reports bounded coverage rather than raw best fits",
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
                ValidationTestLink(
                    test_id="full_cov_contract_rejects_negative_rank",
                    category="regression",
                    path="htt/src/common/test_ver2_contract_layer.py::test_full_cov_mes_report_rejects_negative_rank",
                    purpose="the shared schema blocks negative-rank regressions at construction time",
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
                    purpose="Q/F semantics stay separated when claim gates are not passed",
                    artifact_refs=("common.departure_report",),
                ),
                ValidationTestLink(
                    test_id="mock_coverage_within_published_window",
                    category="numerical_stability",
                    path="htt/src/common/test_mock_calibration.py::TestMockCoverageWithinBounds::test_zoa_null_coverage_within_published_window",
                    purpose="published calibration windows remain explicit before any filling language upgrade",
                    artifact_refs=("validation.null.flrw_isotropic_gaussian_lowell",),
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
                    test_id="local_boost_and_global_tilt_are_not_merged",
                    category="physics_sanity",
                    path="htt/htt/tests/test_ver2_local_global_discrimination.py::test_local_boost_and_global_tilt_are_not_merged",
                    purpose="the discrimination library keeps observer-side and source-side hypotheses separate",
                    artifact_refs=("htt.discrimination_matrix",),
                ),
                ValidationTestLink(
                    test_id="directional_promotion_gate_closed",
                    category="adversarial_edge",
                    path="htt/htt/tests/test_ver2_directional_shell.py::test_directional_bridge_promotion_gate_is_closed_fail",
                    purpose="directional bridge outputs stay blocked until promotion gates are satisfied",
                    artifact_refs=("htt.directional_shell",),
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
                    test_id="tsc_quarantine_flags_emitted",
                    category="regression",
                    path="htt/tsc/audit/test_no_overclaim.py::test_metadata_lint_and_quarantine_reasons",
                    purpose="overclaim metadata is converted into quarantine reasons rather than promotions",
                    artifact_refs=("tsc.adequacy_overlay",),
                ),
                ValidationTestLink(
                    test_id="tsc_theorem_map_covers_export_claims",
                    category="regression",
                    path="htt/tsc/validation/test_theorem_map.py::test_theorem_map_covers_source_budget_and_export_claims",
                    purpose="TSC theorem coverage stays anchored to source-budget and export claim ceilings",
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
            campaign_id="validation.observable_null_proxy",
            title="FLRW null recovery and observable proxy quarantine",
            owner="COMMON",
            implementation_scope="common",
            status="warn",
            theorem_refs=(
                "V8_isotropic_limit_recovery",
                "V8_biposh_Lgt0_null_or_proxy_block",
            ),
            categories=REQUIRED_VALIDATION_CATEGORIES,
            check_links=(
                ValidationTestLink(
                    test_id="flrw_limit_zero_offdiag",
                    category="baseline_reproduction",
                    path="htt/bass/spectrum/test_fb72_off_diagonal_covariance_skeleton.py::test_fb72_type_i_off_diagonal_vanishes_identically",
                    purpose="pin the isotropic null before any morphology promotion",
                    artifact_refs=("bass.observable_vector.proxy",),
                ),
                ValidationTestLink(
                    test_id="rotating_types_activate_offdiag_blocks",
                    category="adversarial_edge",
                    path="htt/bass/spectrum/test_fb72_off_diagonal_covariance_skeleton.py::test_fb72_anisotropic_types_produce_nonzero_off_diagonal_blocks",
                    purpose="ensure anisotropic structures do not collapse into the null proxy",
                    artifact_refs=("bass.observable_vector.proxy",),
                ),
                ValidationTestLink(
                    test_id="proxy_mode_records_no_claim",
                    category="physics_sanity",
                    path="htt/bass/observational/test_ver2_observable_atlas.py::test_covariance_proxy_and_feature_summary_record_guards",
                    purpose="keep sparse-mode caveats explicit on observable outputs",
                    artifact_refs=("bass.observable_vector.proxy",),
                ),
                ValidationTestLink(
                    test_id="anisotropic_te_is_finite",
                    category="numerical_stability",
                    path="htt/bass/spectrum/test_fb72_off_diagonal_covariance_skeleton.py::test_fb72_te_is_finite_for_anisotropic_type",
                    purpose="guard the observable proxy against non-finite anisotropic transport outputs",
                    artifact_refs=("bass.observable_vector.proxy",),
                ),
                ValidationTestLink(
                    test_id="type_i_observable_marks_isotropic_null_proxy",
                    category="regression",
                    path="htt/bass/observational/test_ver2_observable_atlas.py::test_live_tier_b_type_i_observable_marks_isotropic_null_proxy",
                    purpose="keep the live Type-I export on the conservative isotropic-null branch",
                    artifact_refs=("bass.observable_vector.proxy",),
                ),
            ),
            artifact_refs=("bass.observable_vector.proxy", "bass.full_cov_mes_report"),
            manuscript_blocking=True,
            no_claim_conditions=("sparse_proxy_only", "missing_biposh_basis"),
            null_manifest_refs=("null.flrw_isotropic_gaussian_lowell",),
            injection_manifest_refs=("validation.injection.anisotropic_covariance",),
            runbook_refs=("runbook.observable_promotion",),
            notes=(
                "Executable minimal campaign; remains warn until a dense BiPoSH basis and larger null bank land.",
            ),
        ),
        ValidationCampaign(
            campaign_id="validation.synthetic_injection",
            title="Null ensembles, synthetic injections, and live hook replay",
            owner="COMMON",
            implementation_scope="common",
            status="warn",
            theorem_refs=(
                "V8_template_injection_recovery",
                "V8_local_vs_global_discrimination",
            ),
            categories=REQUIRED_VALIDATION_CATEGORIES,
            check_links=(
                ValidationTestLink(
                    test_id="null_mock_zero_mean",
                    category="baseline_reproduction",
                    path="htt/src/common/test_mock_calibration.py::TestMockGeneration::test_isotropic_mock_has_zero_mean_over_many_realisations",
                    purpose="replay the isotropic null before evaluating any injected anisotropy",
                    artifact_refs=("validation.null.flrw_isotropic_gaussian_lowell",),
                ),
                ValidationTestLink(
                    test_id="injected_dipole_projection_recovered",
                    category="adversarial_edge",
                    path="htt/src/common/test_mock_calibration.py::TestMockGeneration::test_injected_dipole_reproduces_projection",
                    purpose="ensure the injection bank exposes controlled signals rather than hidden promotions",
                    artifact_refs=("validation.injection.template_amplitude",),
                ),
                ValidationTestLink(
                    test_id="local_boost_and_global_tilt_are_not_merged",
                    category="physics_sanity",
                    path="htt/htt/tests/test_ver2_local_global_discrimination.py::test_local_boost_and_global_tilt_are_not_merged",
                    purpose="keep injected observer-side structure distinct from background-side hypotheses",
                    artifact_refs=("htt.discrimination_matrix",),
                ),
                ValidationTestLink(
                    test_id="synthetic_injection_coverage_reaches_nominal_band",
                    category="numerical_stability",
                    path="htt/bass/inference/test_fb115_synthetic_injection_skeleton.py::test_fb115_synthetic_injection_coverage_reaches_nominal_band",
                    purpose="bind synthetic injections to explicit coverage criteria rather than point estimates",
                    artifact_refs=("validation.injection.template_amplitude",),
                ),
                ValidationTestLink(
                    test_id="tier_b_runtime_consumes_live_hooks",
                    category="regression",
                    path="htt/bass/runtime/test_ver2_tier_b_execution.py::test_execute_tier_b_solver_consumes_live_s1_s2_s3_hooks",
                    purpose="keep the live S1/S2/S3 hook chain attached to the validation harness",
                    artifact_refs=("bass.runtime.trace",),
                ),
            ),
            artifact_refs=(
                "validation.null.flrw_isotropic_gaussian_lowell",
                "validation.injection.template_amplitude",
                "htt.discrimination_matrix",
            ),
            manuscript_blocking=True,
            no_claim_conditions=(
                "missing_injection_campaign",
                "missing_null_ensemble",
                "missing_scan_volume",
            ),
            null_manifest_refs=(
                "null.flrw_isotropic_gaussian_lowell",
                "null.local_boost_only",
            ),
            injection_manifest_refs=("validation.injection.template_amplitude",),
            runbook_refs=("runbook.semantic_firewall",),
            notes=(
                "Executable minimal campaign; remains warn until the injection grid expands beyond the current smoke bank.",
            ),
        ),
        ValidationCampaign(
            campaign_id="validation.mes_claim_gates",
            title="Full-covariance MES claim gates and calibration windows",
            owner="COMMON",
            implementation_scope="common",
            status="warn",
            theorem_refs=(
                "V8_mes_rank_no_claim",
                "V8_filling_requires_certification",
            ),
            categories=REQUIRED_VALIDATION_CATEGORIES,
            check_links=(
                ValidationTestLink(
                    test_id="mes_covariance_bound_live",
                    category="baseline_reproduction",
                    path="htt/bass/observational/test_ver2_mes_departure.py::test_full_cov_mes_uses_covariance_bound_when_rank_is_available",
                    purpose="exercise the positive branch before any rank-failure downgrade",
                    artifact_refs=("bass.full_cov_mes_report",),
                ),
                ValidationTestLink(
                    test_id="mes_rank_failure_returns_no_claim",
                    category="adversarial_edge",
                    path="htt/bass/observational/test_ver2_mes_departure.py::test_full_cov_mes_rank_failure_returns_no_claim",
                    purpose="prove that rank failure downgrades instead of promoting weak evidence",
                    artifact_refs=("bass.full_cov_mes_report",),
                ),
                ValidationTestLink(
                    test_id="uncertified_f_downgrades_to_proxy",
                    category="physics_sanity",
                    path="htt/bass/observational/test_ver2_mes_departure.py::test_departure_report_stays_descriptive_without_claim_gate",
                    purpose="hold Q/F semantics apart until certification gates pass",
                    artifact_refs=("common.departure_report",),
                ),
                ValidationTestLink(
                    test_id="mock_coverage_within_published_window",
                    category="numerical_stability",
                    path="htt/src/common/test_mock_calibration.py::TestMockCoverageWithinBounds::test_zoa_null_coverage_within_published_window",
                    purpose="attach explicit calibration windows to the descriptive departure language",
                    artifact_refs=("validation.null.flrw_isotropic_gaussian_lowell",),
                ),
                ValidationTestLink(
                    test_id="full_cov_contract_rejects_negative_rank",
                    category="regression",
                    path="htt/src/common/test_ver2_contract_layer.py::test_full_cov_mes_report_rejects_negative_rank",
                    purpose="pin the shared contract against negative-rank regressions",
                    artifact_refs=("bass.full_cov_mes_report",),
                ),
            ),
            artifact_refs=(
                "bass.full_cov_mes_report",
                "common.departure_report",
                "validation.null.flrw_isotropic_gaussian_lowell",
            ),
            manuscript_blocking=True,
            no_claim_conditions=(
                "response_rank_deficient",
                "claim_gate_not_passed",
                "occupancy_not_certified",
            ),
            null_manifest_refs=("null.flrw_isotropic_gaussian_lowell",),
            runbook_refs=("runbook.observable_promotion",),
            notes=(
                "Executable minimal campaign; remains warn until covariance nuisance models move beyond the current conservative window.",
            ),
        ),
        ValidationCampaign(
            campaign_id="validation.semantic_firewall",
            title="Directional and TSC semantic firewall campaign",
            owner="COMMON",
            implementation_scope="common",
            status="warn",
            theorem_refs=(
                "V8_local_vs_global_discrimination",
                "V8_tsc_no_overclaim",
            ),
            categories=REQUIRED_VALIDATION_CATEGORIES,
            check_links=(
                ValidationTestLink(
                    test_id="directional_manifest_not_posterior",
                    category="baseline_reproduction",
                    path="htt/htt/tests/test_ver2_local_global_discrimination.py::test_discrimination_matrix_stub_is_manifest_backed_and_not_posterior",
                    purpose="keep the directional manifest explicitly diagnostic before stronger claims are considered",
                    artifact_refs=("htt.discrimination_matrix",),
                ),
                ValidationTestLink(
                    test_id="policy_rejects_tsc_posterior_correction",
                    category="adversarial_edge",
                    path="htt/htt/tests/test_ver2_directional_shell.py::test_policy_rejects_mio_merge_and_tsc_posterior_correction",
                    purpose="forbid TSC/MIO posterior correction paths at policy level",
                    artifact_refs=("htt.directional_shell", "tsc.adequacy_overlay"),
                ),
                ValidationTestLink(
                    test_id="response_library_keeps_local_and_global_distinct",
                    category="physics_sanity",
                    path="htt/htt/tests/test_ver2_directional_shell.py::test_response_library_keeps_local_boost_and_global_tilt_distinct",
                    purpose="preserve observer-side versus source-side semantics in the response library",
                    artifact_refs=("htt.discrimination_matrix",),
                ),
                ValidationTestLink(
                    test_id="axis_gate_requires_adequate_mock_coverage",
                    category="numerical_stability",
                    path="htt/htt/tests/test_ver2_directional_shell.py::test_axis_gate_requires_adequate_mock_coverage",
                    purpose="block directional promotion when mock calibration coverage is still pending",
                    artifact_refs=("htt.directional_shell",),
                ),
                ValidationTestLink(
                    test_id="tsc_quarantine_flags_emitted",
                    category="regression",
                    path="htt/tsc/audit/test_no_overclaim.py::test_metadata_lint_and_quarantine_reasons",
                    purpose="translate overclaim metadata into quarantine reasons instead of truth labels",
                    artifact_refs=("tsc.adequacy_overlay",),
                ),
            ),
            artifact_refs=("htt.discrimination_matrix", "tsc.adequacy_overlay"),
            manuscript_blocking=True,
            no_claim_conditions=(
                "posterior_correction_attempted",
                "missing_tsc_overlay",
                "missing_response_library",
            ),
            null_manifest_refs=("null.local_boost_only",),
            injection_manifest_refs=("validation.injection.anisotropic_covariance",),
            runbook_refs=("runbook.semantic_firewall",),
            notes=(
                "Executable minimal campaign; remains warn until IM-09D wires the same semantics into export-time figure gating.",
            ),
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
            theorem_refs=(
                "V8_isotropic_limit_recovery",
                "V8_template_injection_recovery",
                "V8_filling_requires_certification",
            ),
            campaign_refs=(
                "validation.observable_null_proxy",
                "validation.synthetic_injection",
                "validation.mes_claim_gates",
            ),
        ),
        NullEnsembleManifest(
            ensemble_id="null.local_boost_only",
            null_family="observer_local_boost_only",
            observable_basis="directional_power_and_coherence",
            scan_volume_hash="scan.local_boost.v1",
            status="warn",
            artifact_refs=("validation.null.local_boost_only",),
            no_claim_conditions=("missing_null_identity", "missing_false_promotion_check"),
            theorem_refs=("V8_local_vs_global_discrimination",),
            campaign_refs=(
                "validation.synthetic_injection",
                "validation.semantic_firewall",
            ),
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
            theorem_refs=("V8_template_injection_recovery",),
            campaign_refs=("validation.synthetic_injection",),
            required_null_refs=("null.flrw_isotropic_gaussian_lowell",),
        ),
        InjectionCampaignManifest(
            injection_id="validation.injection.anisotropic_covariance",
            hypothesis_family="anisotropic_covariance",
            target_statistic="covariance_feature_recovery",
            scan_volume_hash="scan.covariance.injection.v1",
            status="warn",
            artifact_refs=("validation.injection.anisotropic_covariance",),
            downgrade_conditions=("covariance_sampler_unavailable", "proxy_mode_only"),
            theorem_refs=(
                "V8_biposh_Lgt0_null_or_proxy_block",
                "V8_tsc_no_overclaim",
            ),
            campaign_refs=(
                "validation.observable_null_proxy",
                "validation.semantic_firewall",
            ),
            required_null_refs=(
                "null.flrw_isotropic_gaussian_lowell",
                "null.local_boost_only",
            ),
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
                "V8_filling_requires_certification",
            ),
            campaign_refs=(
                "validation.observable_null_proxy",
                "validation.mes_claim_gates",
            ),
            baseline_checks=("flrw_limit_zero_offdiag", "mes_covariance_bound_live"),
            adversarial_checks=(
                "rotating_types_activate_offdiag_blocks",
                "mes_rank_failure_returns_no_claim",
            ),
            physics_checks=(
                "proxy_mode_records_no_claim",
                "uncertified_f_downgrades_to_proxy",
            ),
            numerical_checks=(
                "anisotropic_te_is_finite",
                "mock_coverage_within_published_window",
            ),
            regression_checks=(
                "type_i_observable_marks_isotropic_null_proxy",
                "full_cov_contract_rejects_negative_rank",
            ),
            quarantine_conditions=(
                "sparse_proxy_only",
                "missing_biposh_basis",
                "response_rank_deficient",
                "claim_gate_not_passed",
            ),
            artifact_refs=("bass.observable_vector.proxy", "bass.full_cov_mes_report"),
        ),
        HostileAuditRunbook(
            runbook_id="runbook.semantic_firewall",
            title="Semantic firewall hostile audit",
            owner="COMMON",
            implementation_scope="common",
            theorem_refs=(
                "V8_template_injection_recovery",
                "V8_local_vs_global_discrimination",
                "V8_tsc_no_overclaim",
            ),
            campaign_refs=(
                "validation.synthetic_injection",
                "validation.semantic_firewall",
            ),
            baseline_checks=("null_mock_zero_mean", "directional_manifest_not_posterior"),
            adversarial_checks=(
                "injected_dipole_projection_recovered",
                "policy_rejects_tsc_posterior_correction",
            ),
            physics_checks=(
                "local_boost_and_global_tilt_are_not_merged",
                "response_library_keeps_local_and_global_distinct",
            ),
            numerical_checks=(
                "synthetic_injection_coverage_reaches_nominal_band",
                "axis_gate_requires_adequate_mock_coverage",
            ),
            regression_checks=(
                "tier_b_runtime_consumes_live_hooks",
                "tsc_quarantine_flags_emitted",
            ),
            quarantine_conditions=(
                "missing_injection_campaign",
                "missing_null_ensemble",
                "posterior_correction_attempted",
                "missing_tsc_overlay",
            ),
            artifact_refs=("htt.discrimination_matrix", "tsc.adequacy_overlay"),
        ),
    )


def _check_bucket(
    issues: list[str],
    *,
    runbook_id: str,
    category: ValidationCategory,
    check_ids: tuple[str, ...],
    available_by_category: dict[ValidationCategory, set[str]],
) -> None:
    missing = sorted(set(check_ids) - available_by_category[category])
    if missing:
        issues.append(
            f"runbook {runbook_id} has unknown {category} checks: {missing}"
        )


def hostile_audit_issues(
    *,
    theorem_map: tuple[TheoremToTestEntry, ...] | None = None,
    campaigns: tuple[ValidationCampaign, ...] | None = None,
    nulls: tuple[NullEnsembleManifest, ...] | None = None,
    injections: tuple[InjectionCampaignManifest, ...] | None = None,
    runbooks: tuple[HostileAuditRunbook, ...] | None = None,
) -> tuple[str, ...]:
    """Return runbook-specific registry issues."""

    theorem_map = theorem_map or build_default_theorem_to_test_map()
    campaigns = campaigns or build_default_validation_campaigns()
    nulls = nulls or build_default_null_manifests()
    injections = injections or build_default_injection_manifests()
    runbooks = runbooks or build_default_hostile_audit_runbooks()

    theorem_ids = {entry.theorem_id for entry in theorem_map}
    campaign_by_id = {campaign.campaign_id: campaign for campaign in campaigns}
    null_by_id = {manifest.ensemble_id: manifest for manifest in nulls}
    injection_by_id = {manifest.injection_id: manifest for manifest in injections}
    issues: list[str] = []

    for runbook in runbooks:
        unknown_theorems = sorted(
            ref for ref in runbook.theorem_refs if ref not in theorem_ids
        )
        if unknown_theorems:
            issues.append(
                f"runbook {runbook.runbook_id} references unknown theorems {unknown_theorems}"
            )
        unknown_campaigns = sorted(
            ref for ref in runbook.campaign_refs if ref not in campaign_by_id
        )
        if unknown_campaigns:
            issues.append(
                f"runbook {runbook.runbook_id} references unknown campaigns {unknown_campaigns}"
            )
        available_by_category: dict[ValidationCategory, set[str]] = {
            category: set() for category in REQUIRED_VALIDATION_CATEGORIES
        }
        quarantine_pool: set[str] = set()
        for campaign_id in runbook.campaign_refs:
            campaign = campaign_by_id.get(campaign_id)
            if campaign is None:
                continue
            for link in campaign.check_links:
                available_by_category[link.category].add(link.test_id)
            quarantine_pool.update(campaign.no_claim_conditions)
            for null_ref in campaign.null_manifest_refs:
                manifest = null_by_id.get(null_ref)
                if manifest is not None:
                    quarantine_pool.update(manifest.no_claim_conditions)
            for injection_ref in campaign.injection_manifest_refs:
                manifest = injection_by_id.get(injection_ref)
                if manifest is not None:
                    quarantine_pool.update(manifest.downgrade_conditions)
        _check_bucket(
            issues,
            runbook_id=runbook.runbook_id,
            category="baseline_reproduction",
            check_ids=runbook.baseline_checks,
            available_by_category=available_by_category,
        )
        _check_bucket(
            issues,
            runbook_id=runbook.runbook_id,
            category="adversarial_edge",
            check_ids=runbook.adversarial_checks,
            available_by_category=available_by_category,
        )
        _check_bucket(
            issues,
            runbook_id=runbook.runbook_id,
            category="physics_sanity",
            check_ids=runbook.physics_checks,
            available_by_category=available_by_category,
        )
        _check_bucket(
            issues,
            runbook_id=runbook.runbook_id,
            category="numerical_stability",
            check_ids=runbook.numerical_checks,
            available_by_category=available_by_category,
        )
        _check_bucket(
            issues,
            runbook_id=runbook.runbook_id,
            category="regression",
            check_ids=runbook.regression_checks,
            available_by_category=available_by_category,
        )
        unknown_quarantine = sorted(
            set(runbook.quarantine_conditions) - quarantine_pool
        )
        if unknown_quarantine:
            issues.append(
                f"runbook {runbook.runbook_id} has quarantine conditions without campaign or manifest support: {unknown_quarantine}"
            )
    return tuple(issues)


def validation_registry_issues(
    *,
    theorem_map: tuple[TheoremToTestEntry, ...] | None = None,
    campaigns: tuple[ValidationCampaign, ...] | None = None,
    nulls: tuple[NullEnsembleManifest, ...] | None = None,
    injections: tuple[InjectionCampaignManifest, ...] | None = None,
    runbooks: tuple[HostileAuditRunbook, ...] | None = None,
) -> tuple[str, ...]:
    """Return registry issues for theorem maps, campaigns, manifests, and runbooks."""

    theorem_map = theorem_map or build_default_theorem_to_test_map()
    campaigns = campaigns or build_default_validation_campaigns()
    nulls = nulls or build_default_null_manifests()
    injections = injections or build_default_injection_manifests()
    runbooks = runbooks or build_default_hostile_audit_runbooks()

    theorem_ids = {entry.theorem_id for entry in theorem_map}
    campaign_by_id = {campaign.campaign_id: campaign for campaign in campaigns}
    runbook_by_id = {runbook.runbook_id: runbook for runbook in runbooks}
    null_by_id = {manifest.ensemble_id: manifest for manifest in nulls}
    injection_by_id = {manifest.injection_id: manifest for manifest in injections}
    issues: list[str] = []

    for entry in theorem_map:
        for link in entry.test_links:
            if not validation_test_path_exists(link.path):
                issues.append(
                    f"theorem {entry.theorem_id} references missing test target {link.path}"
                )

    covered_theorems: set[str] = set()
    seen_campaign_check_ids: dict[str, str] = {}
    for campaign in campaigns:
        unknown_theorems = sorted(
            ref for ref in campaign.theorem_refs if ref not in theorem_ids
        )
        if unknown_theorems:
            issues.append(
                f"campaign {campaign.campaign_id} references unknown theorems {unknown_theorems}"
            )
        covered_theorems.update(campaign.theorem_refs)
        if set(campaign.categories) != set(REQUIRED_VALIDATION_CATEGORIES):
            issues.append(
                f"campaign {campaign.campaign_id} must cover {list(REQUIRED_VALIDATION_CATEGORIES)}"
            )
        for link in campaign.check_links:
            if not validation_test_path_exists(link.path):
                issues.append(
                    f"campaign {campaign.campaign_id} references missing test target {link.path}"
                )
            owner = seen_campaign_check_ids.setdefault(link.test_id, campaign.campaign_id)
            if owner != campaign.campaign_id:
                issues.append(
                    f"campaign check id {link.test_id} is duplicated in {owner} and {campaign.campaign_id}"
                )
        unknown_nulls = sorted(
            ref for ref in campaign.null_manifest_refs if ref not in null_by_id
        )
        if unknown_nulls:
            issues.append(
                f"campaign {campaign.campaign_id} references unknown null manifests {unknown_nulls}"
            )
        unknown_injections = sorted(
            ref
            for ref in campaign.injection_manifest_refs
            if ref not in injection_by_id
        )
        if unknown_injections:
            issues.append(
                f"campaign {campaign.campaign_id} references unknown injection manifests {unknown_injections}"
            )
        unknown_runbooks = sorted(
            ref for ref in campaign.runbook_refs if ref not in runbook_by_id
        )
        if unknown_runbooks:
            issues.append(
                f"campaign {campaign.campaign_id} references unknown runbooks {unknown_runbooks}"
            )

    orphan_theorems = sorted(theorem_ids - covered_theorems)
    if orphan_theorems:
        issues.append(f"theorem map contains unassigned theorems {orphan_theorems}")

    for manifest in nulls:
        if not manifest.theorem_refs:
            issues.append(f"null manifest {manifest.ensemble_id} is missing theorem_refs")
        if not manifest.campaign_refs:
            issues.append(f"null manifest {manifest.ensemble_id} is missing campaign_refs")
        unknown_theorems = sorted(
            ref for ref in manifest.theorem_refs if ref not in theorem_ids
        )
        if unknown_theorems:
            issues.append(
                f"null manifest {manifest.ensemble_id} references unknown theorems {unknown_theorems}"
            )
        unknown_campaigns = sorted(
            ref for ref in manifest.campaign_refs if ref not in campaign_by_id
        )
        if unknown_campaigns:
            issues.append(
                f"null manifest {manifest.ensemble_id} references unknown campaigns {unknown_campaigns}"
            )
        for campaign_id in manifest.campaign_refs:
            campaign = campaign_by_id.get(campaign_id)
            if campaign is not None and manifest.ensemble_id not in campaign.null_manifest_refs:
                issues.append(
                    f"null manifest {manifest.ensemble_id} is not mirrored by campaign {campaign_id}"
                )

    for manifest in injections:
        if not manifest.theorem_refs:
            issues.append(
                f"injection manifest {manifest.injection_id} is missing theorem_refs"
            )
        if not manifest.campaign_refs:
            issues.append(
                f"injection manifest {manifest.injection_id} is missing campaign_refs"
            )
        if not manifest.required_null_refs:
            issues.append(
                f"injection manifest {manifest.injection_id} is missing required_null_refs"
            )
        unknown_theorems = sorted(
            ref for ref in manifest.theorem_refs if ref not in theorem_ids
        )
        if unknown_theorems:
            issues.append(
                f"injection manifest {manifest.injection_id} references unknown theorems {unknown_theorems}"
            )
        unknown_campaigns = sorted(
            ref for ref in manifest.campaign_refs if ref not in campaign_by_id
        )
        if unknown_campaigns:
            issues.append(
                f"injection manifest {manifest.injection_id} references unknown campaigns {unknown_campaigns}"
            )
        unknown_nulls = sorted(
            ref for ref in manifest.required_null_refs if ref not in null_by_id
        )
        if unknown_nulls:
            issues.append(
                f"injection manifest {manifest.injection_id} references unknown null manifests {unknown_nulls}"
            )
        for campaign_id in manifest.campaign_refs:
            campaign = campaign_by_id.get(campaign_id)
            if (
                campaign is not None
                and manifest.injection_id not in campaign.injection_manifest_refs
            ):
                issues.append(
                    f"injection manifest {manifest.injection_id} is not mirrored by campaign {campaign_id}"
                )

    for campaign in campaigns:
        for runbook_ref in campaign.runbook_refs:
            runbook = runbook_by_id.get(runbook_ref)
            if runbook is not None and campaign.campaign_id not in runbook.campaign_refs:
                issues.append(
                    f"campaign {campaign.campaign_id} is not mirrored by runbook {runbook_ref}"
                )

    issues.extend(
        hostile_audit_issues(
            theorem_map=theorem_map,
            campaigns=campaigns,
            nulls=nulls,
            injections=injections,
            runbooks=runbooks,
        )
    )
    return tuple(issues)


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
        "registry_issues": list(
            validation_registry_issues(
                theorem_map=theorem_map,
                campaigns=campaigns,
                nulls=nulls,
                injections=injections,
                runbooks=runbooks,
            )
        ),
    }


__all__ = [
    "HostileAuditRunbook",
    "InjectionCampaignManifest",
    "NullEnsembleManifest",
    "REQUIRED_VALIDATION_CATEGORIES",
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
    "hostile_audit_issues",
    "manuscript_export_blocked",
    "validation_registry_issues",
    "validation_registry_payload",
    "validation_test_path_exists",
]
