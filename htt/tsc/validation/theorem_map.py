"""Theorem-to-test map for TSC validation campaigns."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


ValidationCategory = Literal[
    "baseline_reproduction",
    "adversarial_edge",
    "physics_sanity",
    "numerical_stability",
    "regression",
]

_ALLOWED_CATEGORIES = {
    "baseline_reproduction",
    "adversarial_edge",
    "physics_sanity",
    "numerical_stability",
    "regression",
}


@dataclass(frozen=True)
class TheoremTestLink:
    theorem: str
    tests: tuple[str, ...]
    metrics: tuple[str, ...]
    required_artifacts: tuple[str, ...]


@dataclass(frozen=True)
class TscValidationWitness:
    theorem: str
    test_id: str
    category: ValidationCategory
    path: str
    purpose: str
    artifact_refs: tuple[str, ...] = ("tsc.adequacy_overlay",)

    def __post_init__(self) -> None:
        if not self.theorem:
            raise ValueError("TscValidationWitness.theorem must be non-empty")
        if not self.test_id:
            raise ValueError("TscValidationWitness.test_id must be non-empty")
        if self.category not in _ALLOWED_CATEGORIES:
            raise ValueError(f"Unknown validation category {self.category!r}")
        if not self.path:
            raise ValueError("TscValidationWitness.path must be non-empty")
        if not self.purpose:
            raise ValueError("TscValidationWitness.purpose must be non-empty")


CORE_THEOREM_MAP: tuple[TheoremTestLink, ...] = (
    TheoremTestLink(
        theorem="T20_trace_source_adequacy",
        tests=("B2", "B4"),
        metrics=("trace_residual", "source_error", "q2_exact"),
        required_artifacts=("metrics", "passfail", "summary"),
    ),
    TheoremTestLink(
        theorem="T21_q_normalization_table_convention",
        tests=("B4",),
        metrics=("I2_exact", "I2_linear", "percent_underestimate"),
        required_artifacts=("metrics", "summary"),
    ),
    TheoremTestLink(
        theorem="T22_source_bridge_convention_provenance",
        tests=("B4",),
        metrics=(
            "quadrupole_convention",
            "quadrupole_parameter_name",
            "conversion_to_legendre_q",
            "spin2_propagation_required",
        ),
        required_artifacts=("metrics", "summary"),
    ),
    TheoremTestLink(
        theorem="T27_realizability",
        tests=("domain_theta_positive", "domain_be_eta_nonpositive"),
        metrics=("theta_min", "eta_max", "jacobian_sigma_min"),
        required_artifacts=("metrics", "passfail"),
    ),
    TheoremTestLink(
        theorem="T29_observable_bridge_requires_state_residual",
        tests=("C1", "C2"),
        metrics=(
            "collision_residual",
            "state_residual",
            "observable_bound",
            "jacobian_sigma_min",
        ),
        required_artifacts=("metrics", "passfail", "summary"),
    ),
    TheoremTestLink(
        theorem="T30_tt_channel_conditional_adequacy",
        tests=("C1",),
        metrics=(
            "trace_budget",
            "source_to_field_bound",
            "propagation_status",
            "claim_ceiling",
        ),
        required_artifacts=("metrics", "passfail", "summary"),
    ),
    TheoremTestLink(
        theorem="T31_spin2_channels_require_external_validation",
        tests=("B3", "C2"),
        metrics=("spin2_residual", "high_residual", "claim_ceiling"),
        required_artifacts=("metrics", "passfail", "summary"),
    ),
    TheoremTestLink(
        theorem="T90_overlay_export_no_overclaim",
        tests=("audit_no_overclaim", "overlay_quarantine"),
        metrics=("quarantine_count", "claim_ceiling", "publication_blockers"),
        required_artifacts=("summary", "passfail"),
    ),
)


TSC_VALIDATION_WITNESSES: tuple[TscValidationWitness, ...] = (
    TscValidationWitness(
        theorem="T20_trace_source_adequacy",
        test_id="tsc_source_exact_trace_bridge",
        category="physics_sanity",
        path=(
            "htt/tsc/source/test_thomson_bridge.py::"
            "test_build_source_bridge_report_from_samples_infers_exact_trace_labels_and_primitives"
        ),
        purpose="on-manifold source bridge preserves exact adequacy labels and required primitives",
        artifact_refs=("tsc.source_bridge_report",),
    ),
    TscValidationWitness(
        theorem="T21_q_normalization_table_convention",
        test_id="quadrupole_convention_roundtrip",
        category="baseline_reproduction",
        path=(
            "htt/tsc/source/test_quadrupole_conventions.py::"
            "test_q_mu_to_legendre_q_conversion_and_inverse_roundtrip"
        ),
        purpose="registered Q_mu and q conventions roundtrip without drift",
        artifact_refs=("tsc.source_bridge_report",),
    ),
    TscValidationWitness(
        theorem="T22_source_bridge_convention_provenance",
        test_id="source_bridge_provenance_records_quadrupole_policy",
        category="regression",
        path=(
            "htt/tsc/source/test_thomson_bridge.py::"
            "test_build_source_bridge_report_from_samples_infers_exact_trace_labels_and_primitives"
        ),
        purpose="source bridge report carries quadrupole policy tags and spin-2 propagation requirement",
        artifact_refs=("tsc.source_bridge_report",),
    ),
    TscValidationWitness(
        theorem="T27_realizability",
        test_id="domain_invalid_collects_reasons",
        category="adversarial_edge",
        path=(
            "htt/tsc/admissibility/test_domain.py::"
            "test_build_domain_report_invalid_domain_collects_reasons"
        ),
        purpose="invalid domains stay explicit and collect blocking reasons instead of degrading silently",
        artifact_refs=("tsc.domain_report",),
    ),
    TscValidationWitness(
        theorem="T27_realizability",
        test_id="jacobian_sigma_min_guard",
        category="numerical_stability",
        path=(
            "htt/tsc/admissibility/test_domain.py::"
            "test_jacobian_sigma_min_guard"
        ),
        purpose="near-singular Jacobians stay on the no-claim side of the domain gate",
        artifact_refs=("tsc.domain_report",),
    ),
    TscValidationWitness(
        theorem="T29_observable_bridge_requires_state_residual",
        test_id="collision_only_bridge_is_blocked",
        category="adversarial_edge",
        path=(
            "htt/tsc/residuals/test_observable_bridge.py::"
            "test_collision_residual_alone_cannot_claim_observable_bound"
        ),
        purpose="collision residual alone may not be promoted into an observable adequacy claim",
        artifact_refs=("tsc.residual_bridge_report",),
    ),
    TscValidationWitness(
        theorem="T29_observable_bridge_requires_state_residual",
        test_id="state_residual_yields_conditional_observable_bound",
        category="physics_sanity",
        path=(
            "htt/tsc/residuals/test_observable_bridge.py::"
            "test_state_residual_and_sigma_min_yield_conditional_observable_bound"
        ),
        purpose="state residual plus Jacobian control yields only a conditional observable bound",
        artifact_refs=("tsc.residual_bridge_report",),
    ),
    TscValidationWitness(
        theorem="T29_observable_bridge_requires_state_residual",
        test_id="small_sigma_min_blocks_observable_bound",
        category="numerical_stability",
        path=(
            "htt/tsc/residuals/test_observable_bridge.py::"
            "test_small_sigma_min_blocks_observable_claim_even_with_state_residual"
        ),
        purpose="poor conditioning blocks observable claims even when state residuals are available",
        artifact_refs=("tsc.residual_bridge_report",),
    ),
    TscValidationWitness(
        theorem="T30_tt_channel_conditional_adequacy",
        test_id="tt_claim_ceiling_requires_state_bridge",
        category="adversarial_edge",
        path=(
            "htt/tsc/budget/test_source_to_channel.py::"
            "test_tt_claim_ceiling_requires_state_residual_bridge"
        ),
        purpose="TT remains exploratory when the residual bridge lacks state-side control",
        artifact_refs=("tsc.channel_budget",),
    ),
    TscValidationWitness(
        theorem="T30_tt_channel_conditional_adequacy",
        test_id="tt_claim_ceiling_conditional_with_state_bridge",
        category="regression",
        path=(
            "htt/tsc/budget/test_source_to_channel.py::"
            "test_tt_claim_ceiling_becomes_conditional_with_state_residual_bridge"
        ),
        purpose="TT becomes conditional only when the residual bridge and source split stay coherent",
        artifact_refs=("tsc.channel_budget",),
    ),
    TscValidationWitness(
        theorem="T31_spin2_channels_require_external_validation",
        test_id="bb_claim_remains_blocked_after_trace_validation",
        category="regression",
        path=(
            "htt/tsc/budget/test_source_to_channel.py::"
            "test_validated_budgets_emit_field_bounds_but_keep_bb_claim_blocked"
        ),
        purpose="trace-side validation never upgrades BB into an allowed claim",
        artifact_refs=("tsc.channel_budget",),
    ),
    TscValidationWitness(
        theorem="T90_overlay_export_no_overclaim",
        test_id="tsc_quarantine_flags_emitted",
        category="regression",
        path=(
            "htt/tsc/audit/test_no_overclaim.py::"
            "test_metadata_lint_and_quarantine_reasons"
        ),
        purpose="overclaim metadata is converted into quarantine reasons rather than promotions",
    ),
    TscValidationWitness(
        theorem="T90_overlay_export_no_overclaim",
        test_id="export_blocks_exploratory_claim_ceiling",
        category="regression",
        path=(
            "htt/tsc/reports/test_json_export.py::"
            "test_overlay_export_blocks_exploratory_claim_ceiling_even_when_propagation_validated"
        ),
        purpose="publication/export gates remain blocked when claim ceilings stay exploratory",
    ),
    TscValidationWitness(
        theorem="T90_overlay_export_no_overclaim",
        test_id="tsc_theorem_map_covers_export_claims",
        category="regression",
        path=(
            "htt/tsc/validation/test_theorem_map.py::"
            "test_theorem_map_covers_source_budget_and_export_claims"
        ),
        purpose="local theorem coverage stays synchronized with export and claim-ceiling semantics",
    ),
)


def build_tsc_validation_witnesses() -> tuple[TscValidationWitness, ...]:
    return TSC_VALIDATION_WITNESSES


__all__ = [
    "CORE_THEOREM_MAP",
    "TSC_VALIDATION_WITNESSES",
    "TheoremTestLink",
    "TscValidationWitness",
    "build_tsc_validation_witnesses",
]
