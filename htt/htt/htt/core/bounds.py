"""Typed MES-anchor and stress facade for active HTT consumers.

The historical float-returning bounds implementation now lives at
``tsc_legacy.htt_core_bounds``.  This active namespace exposes only typed,
channel-matched statistical-foundation contracts.  In particular it does not
export a four-acceleration MES coefficient, the withheld ``2.69 epsilon_1``
shear correction, a scalar cross-sector ceiling, or a filling/occupancy helper.
"""
from __future__ import annotations

from common.mes_successor_registry import current_mes_successor_registry
from common.statistical_foundations import (
    AnchorAuthorityKind,
    AnchorConditioning,
    AnchorStatus,
    AnchorStressReport,
    MESAnchorSpec,
    ScalarRange,
    SectorStress,
    StressStatus,
    evaluate_sector_stress,
    quarantined_shear_anchors,
    registered_geodesic_mes_anchors,
)

_MES_SUCCESSOR = current_mes_successor_registry().successor
_MES_SUCCESSOR_ID = _MES_SUCCESSOR.successor_id

__all__ = [
    "AnchorAuthorityKind",
    "AnchorConditioning",
    "AnchorStatus",
    "AnchorStressReport",
    "MESAnchorSpec",
    "ScalarRange",
    "SectorStress",
    "StressStatus",
    "evaluate_sector_stress",
    "quarantined_shear_anchors",
    "registered_geodesic_mes_anchors",
]
