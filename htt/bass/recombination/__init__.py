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
    build_tilted_visibility_source_stub,
    build_visibility_history_contract,
)

__all__ = [
    "ScalarHistoryMetadata",
    "VisibilityEventMarkers",
    "VisibilityHistoryContract",
    "TiltedVisibilitySource",
    "build_visibility_history_contract",
    "build_tilted_visibility_source",
    "build_tilted_visibility_source_stub",
]
