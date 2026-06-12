"""Observer-side statistics and feature-extraction contracts."""

from __future__ import annotations

from .observable_vector import (
    ObservableVector,
    build_observable_vector,
    obsstat_manifest,
)

__all__ = [
    "ObservableVector",
    "build_observable_vector",
    "obsstat_manifest",
]
