"""Skeleton theorem-to-test map for TSC validation campaigns."""
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
        tests=("B2", "C1", "C2"),
        metrics=("trace_residual", "source_error", "spectrum_error"),
        required_artifacts=("metrics", "passfail", "summary"),
    ),
    TheoremTestLink(
        theorem="T27_realizability",
        tests=("domain_theta_positive", "domain_be_eta_nonpositive"),
        metrics=("theta_min", "eta_max", "jacobian_sigma_min"),
        required_artifacts=("metrics", "passfail"),
    ),
)


__all__ = ["CORE_THEOREM_MAP", "TheoremTestLink"]
