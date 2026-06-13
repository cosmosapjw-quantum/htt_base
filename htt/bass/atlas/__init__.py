"""BASS atlas metadata schemas for pre-solver transfer comparisons."""

from __future__ import annotations

from .atlas_entry import (
    AtlasEntryLite,
    AtlasTransferComparison,
    build_default_transfer_side_by_side_comparison,
    entries_from_transfer_registry,
    validate_atlas_entry_lite_metadata,
)
from .budget_ceiling_optimizer import (
    AdmissibleSetMetadata,
    BudgetCeilingCandidate,
    BudgetCeilingPolicyResult,
    CeilingPrior,
    optimize_budget_ceiling,
)

__all__ = [
    "AdmissibleSetMetadata",
    "AtlasEntryLite",
    "AtlasTransferComparison",
    "BudgetCeilingCandidate",
    "BudgetCeilingPolicyResult",
    "CeilingPrior",
    "build_default_transfer_side_by_side_comparison",
    "entries_from_transfer_registry",
    "optimize_budget_ceiling",
    "validate_atlas_entry_lite_metadata",
]
