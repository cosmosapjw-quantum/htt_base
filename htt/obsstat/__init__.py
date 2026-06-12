"""Observer-side statistics and feature-extraction contracts."""

from __future__ import annotations

import sys as _sys

_PACKAGE_ALIASES = ("obsstat", "htt.obsstat")
_THIS_PACKAGE = _sys.modules[__name__]
if __name__ in _PACKAGE_ALIASES:
    for _alias in _PACKAGE_ALIASES:
        _sys.modules.setdefault(_alias, _THIS_PACKAGE)

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
from .scalar_lowell import (
    LowEllNullCalibration,
    LowEllScalarSummary,
    compute_cl_from_alm,
    summarize_lowell_scalars,
)

for _submodule in ("alm_conventions", "observable_vector", "scalar_lowell"):
    _loaded = _sys.modules.get(f"{__name__}.{_submodule}")
    if _loaded is not None:
        for _alias in _PACKAGE_ALIASES:
            _sys.modules.setdefault(f"{_alias}.{_submodule}", _loaded)

__all__ = [
    "AlmConvention",
    "LowEllNullCalibration",
    "LowEllScalarSummary",
    "ObservableVector",
    "build_alm_feature",
    "build_observable_vector",
    "compute_cl_from_alm",
    "canonical_spin2_alm_convention",
    "canonical_temperature_alm_convention",
    "obsstat_manifest",
    "summarize_lowell_scalars",
    "validate_alm_convention_metadata",
    "validate_alm_feature_conventions",
]
