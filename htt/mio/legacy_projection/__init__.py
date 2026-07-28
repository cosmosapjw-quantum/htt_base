"""Explicit compatibility namespace for historical MIO scalar reports."""
from __future__ import annotations

import warnings

warnings.warn(
    "mio.legacy_projection preserves historical Q/F/Pi/G_F calculations; "
    "new analysis must use typed mio.formalism contracts",
    DeprecationWarning,
    stacklevel=2,
)

from mio.formalism.exceedance import (
    ExceedanceCurve,
    MeasureKind,
    ThresholdPolicy,
    build_exceedance_curve,
    build_exceedance_curve_from_filling_fraction,
    build_exceedance_curve_from_normalized_scores,
)
from mio.formalism.filling_fraction import (
    CertifiedFillingFraction,
    build_certified_filling_fraction,
)
from mio.formalism.isotropy_gap import (
    DepthBinFRecord,
    DepthBinMetadata,
    IsotropyGap,
    build_depth_bin_f_record,
    build_isotropy_gap,
)
from mio.formalism.normalized_score import (
    ComparatorMultiverseSummary,
    NormalizedScore,
    NumeratorPolicy,
    build_comparator_multiverse_summary,
    build_normalized_score,
)
from mio.reports.departure_report import (
    DepartureReport,
    DepartureReportSection,
    build_departure_report,
)

LEGACY_REPRODUCTION_ONLY = True

__all__ = [
    "ComparatorMultiverseSummary",
    "CertifiedFillingFraction",
    "DepthBinFRecord",
    "DepthBinMetadata",
    "DepartureReport",
    "DepartureReportSection",
    "ExceedanceCurve",
    "IsotropyGap",
    "MeasureKind",
    "NormalizedScore",
    "NumeratorPolicy",
    "ThresholdPolicy",
    "build_certified_filling_fraction",
    "build_comparator_multiverse_summary",
    "build_depth_bin_f_record",
    "build_departure_report",
    "build_exceedance_curve",
    "build_exceedance_curve_from_filling_fraction",
    "build_exceedance_curve_from_normalized_scores",
    "build_isotropy_gap",
    "build_normalized_score",
]
