"""BASS recombination/history surfaces.

This package still exposes the earlier W8 history tables and now also carries
the VER2 S2 scalar-history / visibility skeleton contracts.
"""

from bass.recombination.history_visibility import (
    ScalarHistoryMetadata,
    TiltedVisibilitySource,
    VisibilityEventMarkers,
    VisibilityHistoryContract,
    build_tilted_visibility_source,
    build_visibility_history_contract,
    homogeneous_reionization_history,
    opacity_from_physical_inputs,
    optical_depth,
    visibility_history_gate_bundle,
    visibility_function,
)

__all__ = [
    "ScalarHistoryMetadata",
    "VisibilityEventMarkers",
    "VisibilityHistoryContract",
    "TiltedVisibilitySource",
    "opacity_from_physical_inputs",
    "optical_depth",
    "visibility_function",
    "homogeneous_reionization_history",
    "visibility_history_gate_bundle",
    "build_visibility_history_contract",
    "build_tilted_visibility_source",
]
