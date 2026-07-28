"""Active BASS atlas metadata schemas for pre-solver transfer comparisons."""
from __future__ import annotations

from importlib import import_module
import warnings

from .atlas_entry import (
    AtlasEntryLite,
    AtlasTransferComparison,
    build_default_transfer_side_by_side_comparison,
    entries_from_transfer_registry,
    validate_atlas_entry_lite_metadata,
)

_LEGACY_BUDGET_EXPORTS = {
    "AdmissibleSetMetadata",
    "BudgetCeilingCandidate",
    "BudgetCeilingPolicyResult",
    "CeilingPrior",
    "optimize_budget_ceiling",
}


def __getattr__(name: str):
    if name not in _LEGACY_BUDGET_EXPORTS:
        raise AttributeError(name)
    warnings.warn(
        f"bass.atlas.{name} is a legacy scalar-budget export",
        DeprecationWarning,
        stacklevel=2,
    )
    module = import_module("bass.atlas.budget_ceiling_optimizer")
    return getattr(module, name)


__all__ = [
    "AtlasEntryLite",
    "AtlasTransferComparison",
    "build_default_transfer_side_by_side_comparison",
    "entries_from_transfer_registry",
    "validate_atlas_entry_lite_metadata",
]
