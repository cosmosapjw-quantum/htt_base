"""VER2 observational substrate exports."""

from bass.observational.atlas_entry_lite_builder import build_atlas_entry_lite
from bass.observational.covariance_sparse import (
    build_covariance_feature_summary,
    build_sparse_covariance_proxy,
)
from bass.observational.departure_report_plumbing import (
    DepartureBuildResult,
    build_descriptive_departure_report,
)
from bass.observational.full_cov_mes import (
    MesBoundBuildResult,
    build_full_cov_mes_report,
    evaluate_mes_claim_gate,
)
from bass.observational.observable_vector_builder import (
    build_observable_vector_from_solver_output,
)

__all__ = [
    "DepartureBuildResult",
    "MesBoundBuildResult",
    "build_atlas_entry_lite",
    "build_covariance_feature_summary",
    "build_descriptive_departure_report",
    "build_full_cov_mes_report",
    "build_observable_vector_from_solver_output",
    "build_sparse_covariance_proxy",
    "evaluate_mes_claim_gate",
]
