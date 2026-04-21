"""mio.diagnostics — HJ-05 masked-sky caveats plus IM-07M residual atlas.

HJ-05a-lite (Week 6 Day 7) lands `masked_sky_caveats.py` with
SkyCoverageReport + build_report + as_caveats_list. Full HJ-05
(selection-response coupling + bulk-flow tie-in) is Week 8+. SK-07M
adds `predictive_residuals.py` as a manifest-backed residual-atlas
surface; IM-07M extends it so it can build live slices from the shared
VER2 prediction/data schema as well as caller-supplied summaries.
"""
from __future__ import annotations

from .masked_sky_caveats import (  # noqa: F401
    BIAS_AMP_CAVEAT,
    SkyCoverageReport,
    apply_bias_amp_caveat,
    as_caveats_list,
    build_report,
)
from .predictive_residuals import (  # noqa: F401
    ARTEFACT_FILENAME,
    DEFAULT_DOMAIN_CAVEAT,
    PredictiveResidualAtlas,
    ResidualChannelSlice,
    build_predictive_residual_atlas,
    build_predictive_residual_atlas_from_shared_schema,
    build_residual_slices_from_shared_schema,
    emit_predictive_residuals_artefact,
    emit_predictive_residuals_shared_schema_artefact,
    SHARED_SCHEMA_DOMAIN_CAVEAT,
    SUPPORTED_SPECTRUM_CHANNELS,
    to_mio_certificate as to_predictive_residual_mio_certificate,
)

__all__ = [
    "ARTEFACT_FILENAME",
    "BIAS_AMP_CAVEAT",
    "DEFAULT_DOMAIN_CAVEAT",
    "PredictiveResidualAtlas",
    "ResidualChannelSlice",
    "SHARED_SCHEMA_DOMAIN_CAVEAT",
    "SkyCoverageReport",
    "SUPPORTED_SPECTRUM_CHANNELS",
    "apply_bias_amp_caveat",
    "as_caveats_list",
    "build_predictive_residual_atlas",
    "build_predictive_residual_atlas_from_shared_schema",
    "build_residual_slices_from_shared_schema",
    "build_report",
    "emit_predictive_residuals_artefact",
    "emit_predictive_residuals_shared_schema_artefact",
    "to_predictive_residual_mio_certificate",
]
