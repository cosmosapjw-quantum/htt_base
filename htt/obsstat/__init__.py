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
from .biposh_features import (
    BiPoSHConventionMetadata,
    BiPoSHFeatureSummary,
    SparseBiPoSHCoefficient,
    build_biposh_feature_payload,
)
from .morphology import (
    DiagnosticMorphologyAxis,
    MorphologyAxisSummary,
    MorphologyNullCalibration,
    summarize_morphology_axes,
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
from .template_fit import (
    CovarianceAssumption,
    OrientationScanMetadata,
    TemplateFitDiagnostic,
    fit_template_diagnostic,
)

for _submodule in (
    "alm_conventions",
    "biposh_features",
    "morphology",
    "observable_vector",
    "scalar_lowell",
    "template_fit",
):
    _loaded = _sys.modules.get(f"{__name__}.{_submodule}")
    if _loaded is not None:
        for _alias in _PACKAGE_ALIASES:
            _sys.modules.setdefault(f"{_alias}.{_submodule}", _loaded)

__all__ = [
    "AlmConvention",
    "BiPoSHConventionMetadata",
    "BiPoSHFeatureSummary",
    "CovarianceAssumption",
    "DiagnosticMorphologyAxis",
    "LowEllNullCalibration",
    "LowEllScalarSummary",
    "MorphologyAxisSummary",
    "MorphologyNullCalibration",
    "ObservableVector",
    "OrientationScanMetadata",
    "SparseBiPoSHCoefficient",
    "TemplateFitDiagnostic",
    "build_alm_feature",
    "build_biposh_feature_payload",
    "build_observable_vector",
    "compute_cl_from_alm",
    "canonical_spin2_alm_convention",
    "canonical_temperature_alm_convention",
    "fit_template_diagnostic",
    "obsstat_manifest",
    "summarize_morphology_axes",
    "summarize_lowell_scalars",
    "validate_alm_convention_metadata",
    "validate_alm_feature_conventions",
]
