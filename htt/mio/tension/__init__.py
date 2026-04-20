"""mio.tension — HJ-03 FLRW-null tension diagnostics.

The research plan splits HJ-03 into two public surfaces:

* ``flrw_tension`` — posterior-predictive p-values against FLRW mocks
* ``xc_estimator`` — direct ``x_C`` estimate from data-side ingredients

This package intentionally does **not** generate FLRW mocks or HTT
posteriors itself. Instead, callers pass observed statistics, mock
ensembles, or transfer-calibrated components into the pure-python
helpers here. That keeps G19 separation intact while still exposing a
real artifact-producing API for non-BASS development.
"""
from __future__ import annotations

from .flrw_tension import (  # noqa: F401
    ARTEFACT_FILENAME,
    FlrwPppReport,
    FlrwPppStatistic,
    emit_flrw_tension_artefact,
    evaluate_flrw_tension,
    posterior_predictive_pvalue,
    to_mio_certificate,
)
from .xc_estimator import (  # noqa: F401
    XC_ARTEFACT_FILENAME,
    XCInputs,
    XCReport,
    departure_parameter_estimate,
    emit_xc_direct_estimate_artefact,
    estimate_xc_report,
    to_mio_certificate as to_xc_mio_certificate,
)

__all__ = [
    "ARTEFACT_FILENAME",
    "XC_ARTEFACT_FILENAME",
    "FlrwPppReport",
    "FlrwPppStatistic",
    "XCInputs",
    "XCReport",
    "departure_parameter_estimate",
    "emit_flrw_tension_artefact",
    "emit_xc_direct_estimate_artefact",
    "estimate_xc_report",
    "evaluate_flrw_tension",
    "posterior_predictive_pvalue",
    "to_mio_certificate",
    "to_xc_mio_certificate",
]
