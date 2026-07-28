"""Active MIO formalism surface.

Only typed state, identified-set, channel-stress, legacy-projection-report and
orbit/nonlinearity contracts are exported here.  Historical scalar Q/F/Pi/G_F
builders remain reproducible under :mod:`mio.legacy_projection`; they are not
active estimands, occupancies, probabilities, evidence, or family classifiers.
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
    "DepartureComponent",
    "DepartureState",
    "DiagnosticScalarReport",
    "DynamicBudgetBarrierResult",
    "FiniteCoverUnionBoundResult",
    "IdentifiedDepartureSet",
    "LegacyProjectionReport",
    "MESAnchorSpec",
    "NormalizerBenchmarkReport",
    "NormalizerPurpose",
    "NormalizerSpec",
    "NativeMorphologyAtlasStatus",
    "NonlinearityReport",
    "ScalarRange",
    "SectorStress",
    "SummaryDepartureState",
    "bound_to_pi_domination",
    "build_budget_spec",
    "compare_denominator_policies",
    "dynamic_comparison_budget_barrier",
    "finite_cover_union_bound",
    "signed_component_projection",
]
