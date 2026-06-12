"""Observer-side statistics and feature-extraction contracts."""

from __future__ import annotations

from .alm_conventions import (
    AlmConvention,
    build_alm_feature,
    canonical_spin2_alm_convention,
    canonical_temperature_alm_convention,
    validate_alm_convention_metadata,
    validate_alm_feature_conventions,
)
from .observable_vector import (
    ObservableVector,
    build_observable_vector,
    obsstat_manifest,
)

__all__ = [
    "AlmConvention",
    "ObservableVector",
    "build_alm_feature",
    "build_observable_vector",
    "canonical_spin2_alm_convention",
    "canonical_temperature_alm_convention",
    "obsstat_manifest",
    "validate_alm_convention_metadata",
    "validate_alm_feature_conventions",
]
