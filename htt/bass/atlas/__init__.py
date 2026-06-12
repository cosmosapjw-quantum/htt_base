"""BASS atlas metadata schemas for pre-solver transfer comparisons."""

from __future__ import annotations

from .atlas_entry import (
    AtlasEntryLite,
    AtlasTransferComparison,
    build_default_transfer_side_by_side_comparison,
    entries_from_transfer_registry,
    validate_atlas_entry_lite_metadata,
)

__all__ = [
    "AtlasEntryLite",
    "AtlasTransferComparison",
    "build_default_transfer_side_by_side_comparison",
    "entries_from_transfer_registry",
    "validate_atlas_entry_lite_metadata",
]
