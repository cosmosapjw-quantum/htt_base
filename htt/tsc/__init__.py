"""tsc: Teff-chart service layer and diagnostics.

VER2 extends TSC from a passive chart/admissibility toolbox into an active
service layer that can emit domain, residual, source-bridge, channel-budget,
and no-overclaim artifacts without taking runtime or inference ownership.
"""

from .contracts import (
    ALLOWED_COMBINED_LABELS,
    FORBIDDEN_COMBINED_LABELS,
    FORBIDDEN_TSC_FIELDS,
    TSC_NOT_APPLICABLE,
)

__all__ = [
    "ALLOWED_COMBINED_LABELS",
    "FORBIDDEN_COMBINED_LABELS",
    "FORBIDDEN_TSC_FIELDS",
    "TSC_NOT_APPLICABLE",
]
