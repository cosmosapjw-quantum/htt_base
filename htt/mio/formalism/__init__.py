"""Active MIO formalism surface.

Only typed state, identified-set, channel-stress, legacy-projection-report and
orbit/nonlinearity contracts are exported here.  The active object named
``OccupancyMeasure`` is an empirical diagnostic level-set mass, never physical
occupancy. Historical scalar Q/F/Pi/G_F builders remain reproducible under
:mod:`mio.legacy_projection`; they are not active estimands, probabilities,
evidence, or family classifiers.
"""
from __future__ import annotations

from common.orbit_nonlinearity import NonlinearityReport
from common.mes_successor_registry import current_mes_successor_registry
from common.anchor_geometry import (
    AnchorBodySpec,
    AnchorFamily,
    AnchorGaugeInterval,
    AnchorMarginReport,
    NormalizerBenchmarkReport,
    NormalizerPurpose,
    NormalizerSpec,
)
from common.statistical_foundations import (
    AnchorStressReport,
    BudgetRadiusResult,
    DepartureState,
    DiagnosticScalarReport,
    IdentifiedDepartureSet,
    LegacyProjectionReport,
    MESAnchorSpec,
    ScalarRange,
    SectorStress,
    SummaryDepartureState,
)
from common.tensor_functionals import (
    FunctionalAdmissibilityReport,
    FunctionalAnchorReport,
    FunctionalCodomainReport,
    FunctionalDomainReport,
    FunctionalStressReport,
    TensorFunctionalOperator,
    TensorFunctionalResult,
    TensorFunctionalSpec,
    build_tensor_functional_spec,
    evaluate_tensor_functional,
    revalidate_tensor_functional_result,
)
from common.tensor_departure_statistics import (
    CertifiedFunctionalPushforward,
    DirectionalRatioStatus,
    FunctionalCellStatus,
    LegacyCompatibilityStatus,
    LegacyXQPiFGView,
    OccupancyMeasure,
    OccupancyMeasureStatus,
    PushforwardSummaryStatus,
    ScalarizationPolicy,
    SupportUtilizationProfile,
    SupportUtilizationStatus,
    TensorDepartureStatisticsError,
    build_certified_functional_pushforward,
    build_legacy_xqpi_fg_view,
    build_occupancy_measure,
    build_support_utilization_profile,
)

from .bound_pushforward import (
    BoundToPiDominationResult,
    FiniteCoverUnionBoundResult,
    bound_to_pi_domination,
    finite_cover_union_bound,
)
from .budget_spec import (
    BudgetPolicy,
    BudgetSensitivityPoint,
    BudgetSpec,
    BudgetUse,
    NativeMorphologyAtlasStatus,
    build_budget_spec,
    compare_denominator_policies,
)
from .component_breakdown import (
    CANONICAL_COMPONENT_ORDER,
    CANONICAL_COMPONENT_SIGNS,
    ComponentBreakdown,
    DepartureComponent,
    signed_component_projection,
)
from .dynamic_budget import (
    DynamicBudgetBarrierResult,
    dynamic_comparison_budget_barrier,
)

_MES_SUCCESSOR = current_mes_successor_registry().successor
_MES_SUCCESSOR_ID = _MES_SUCCESSOR.successor_id

__all__ = [
    "AnchorStressReport",
    "AnchorBodySpec",
    "AnchorFamily",
    "AnchorGaugeInterval",
    "AnchorMarginReport",
    "BoundToPiDominationResult",
    "BudgetPolicy",
    "BudgetRadiusResult",
    "BudgetSensitivityPoint",
    "BudgetSpec",
    "BudgetUse",
    "CANONICAL_COMPONENT_ORDER",
    "CANONICAL_COMPONENT_SIGNS",
    "ComponentBreakdown",
    "CertifiedFunctionalPushforward",
    "DepartureComponent",
    "DepartureState",
    "DiagnosticScalarReport",
    "DynamicBudgetBarrierResult",
    "FiniteCoverUnionBoundResult",
    "FunctionalAdmissibilityReport",
    "FunctionalAnchorReport",
    "FunctionalCodomainReport",
    "FunctionalDomainReport",
    "FunctionalStressReport",
    "FunctionalCellStatus",
    "IdentifiedDepartureSet",
    "LegacyProjectionReport",
    "LegacyCompatibilityStatus",
    "LegacyXQPiFGView",
    "MESAnchorSpec",
    "NormalizerBenchmarkReport",
    "NormalizerPurpose",
    "NormalizerSpec",
    "NativeMorphologyAtlasStatus",
    "NonlinearityReport",
    "OccupancyMeasure",
    "OccupancyMeasureStatus",
    "ScalarRange",
    "ScalarizationPolicy",
    "SectorStress",
    "SummaryDepartureState",
    "SupportUtilizationProfile",
    "SupportUtilizationStatus",
    "TensorFunctionalOperator",
    "TensorFunctionalResult",
    "TensorFunctionalSpec",
    "TensorDepartureStatisticsError",
    "DirectionalRatioStatus",
    "PushforwardSummaryStatus",
    "bound_to_pi_domination",
    "build_tensor_functional_spec",
    "build_certified_functional_pushforward",
    "build_budget_spec",
    "compare_denominator_policies",
    "build_legacy_xqpi_fg_view",
    "build_occupancy_measure",
    "build_support_utilization_profile",
    "dynamic_comparison_budget_barrier",
    "evaluate_tensor_functional",
    "revalidate_tensor_functional_result",
    "finite_cover_union_bound",
    "signed_component_projection",
]
