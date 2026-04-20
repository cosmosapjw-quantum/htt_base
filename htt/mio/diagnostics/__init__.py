"""mio.diagnostics — HJ-05 masked-sky caveats plus SK-07M residual shells.

HJ-05a-lite (Week 6 Day 7) lands `masked_sky_caveats.py` with
SkyCoverageReport + build_report + as_caveats_list. Full HJ-05
(selection-response coupling + bulk-flow tie-in) is Week 8+. SK-07M
adds `predictive_residuals.py` as a manifest-backed residual-atlas
shell; it packages caller-supplied residual summaries but does not
implement final scoring logic yet.
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
    emit_predictive_residuals_artefact,
    to_mio_certificate as to_predictive_residual_mio_certificate,
)

__all__ = [
    "ARTEFACT_FILENAME",
    "BIAS_AMP_CAVEAT",
    "DEFAULT_DOMAIN_CAVEAT",
    "PredictiveResidualAtlas",
    "ResidualChannelSlice",
    "SkyCoverageReport",
    "apply_bias_amp_caveat",
    "as_caveats_list",
    "build_predictive_residual_atlas",
    "build_report",
    "emit_predictive_residuals_artefact",
    "to_predictive_residual_mio_certificate",
]
