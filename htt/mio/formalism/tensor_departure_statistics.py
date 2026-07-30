"""MIO-owned diagnostic bridge for vector/tensor departure statistics.

The implementation and semantic authority live in
``common.tensor_departure_statistics``.  This bridge exposes only diagnostic
builders; it contains no likelihood, posterior, or evidence operation.
"""

from common.tensor_departure_statistics import (
    CertifiedFunctionalPushforward,
    DirectionalRatioStatus,
    FunctionalCellStatus,
    LegacyCompatibilityStatus,
    LegacyXQPiFGView,
    OCCUPANCY_MEASURE_KIND,
    OccupancyMeasure,
    OccupancyMeasureStatus,
    PushforwardSummaryStatus,
    SUPPORT_CATALOGUE_STATUS,
    ScalarizationPolicy,
    SupportUtilizationProfile,
    SupportUtilizationStatus,
    TENSOR_DEPARTURE_ALLOWED_USE,
    TENSOR_DEPARTURE_CLAIM_CEILING,
    TENSOR_DEPARTURE_FORBIDDEN_USE,
    TensorDepartureStatisticsError,
    build_certified_functional_pushforward,
    build_legacy_xqpi_fg_view,
    build_occupancy_measure,
    build_support_utilization_profile,
)

__all__ = [
    "CertifiedFunctionalPushforward",
    "DirectionalRatioStatus",
    "FunctionalCellStatus",
    "LegacyCompatibilityStatus",
    "LegacyXQPiFGView",
    "OCCUPANCY_MEASURE_KIND",
    "OccupancyMeasure",
    "OccupancyMeasureStatus",
    "PushforwardSummaryStatus",
    "SUPPORT_CATALOGUE_STATUS",
    "ScalarizationPolicy",
    "SupportUtilizationProfile",
    "SupportUtilizationStatus",
    "TENSOR_DEPARTURE_ALLOWED_USE",
    "TENSOR_DEPARTURE_CLAIM_CEILING",
    "TENSOR_DEPARTURE_FORBIDDEN_USE",
    "TensorDepartureStatisticsError",
    "build_certified_functional_pushforward",
    "build_legacy_xqpi_fg_view",
    "build_occupancy_measure",
    "build_support_utilization_profile",
]
