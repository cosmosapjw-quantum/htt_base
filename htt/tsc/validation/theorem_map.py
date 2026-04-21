"""Theorem-to-test map for TSC validation campaigns."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TheoremTestLink:
    theorem: str
    tests: tuple[str, ...]
    metrics: tuple[str, ...]
    required_artifacts: tuple[str, ...]


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
        theorem="T27_realizability",
        tests=("domain_theta_positive", "domain_be_eta_nonpositive"),
        metrics=("theta_min", "eta_max", "jacobian_sigma_min"),
        required_artifacts=("metrics", "passfail"),
    ),
    TheoremTestLink(
        theorem="T30_tt_channel_conditional_adequacy",
        tests=("C1",),
        metrics=("trace_budget", "source_to_field_bound", "propagation_status"),
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
        metrics=("quarantine_count", "publication_blockers"),
        required_artifacts=("summary", "passfail"),
    ),
)


__all__ = ["CORE_THEOREM_MAP", "TheoremTestLink"]
