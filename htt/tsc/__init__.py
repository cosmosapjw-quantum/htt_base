"""tsc: legacy Teff-chart service layer and diagnostics.

TSC remains import-compatible for old chart/admissibility overlays and
reproducibility checks. New framework ownership is ``TSC_LEGACY`` and bounded
to legacy reproduction; TSC is not an active science owner, runtime gate,
posterior/evidence owner, MIO certificate owner, native solver, or
family-identification path.
"""

from .contracts import (
    ALLOWED_COMBINED_LABELS,
    FORBIDDEN_COMBINED_LABELS,
    FORBIDDEN_TSC_FIELDS,
    TSC_NOT_APPLICABLE,
)
from tsc_legacy import (
    TSC_ACTIVE_SCIENCE_OWNER,
    TSC_ALLOWED_BUNDLE_KIND,
    TSC_DEPRECATION_CAVEAT,
    TSC_DEPRECATION_STATUS,
    TSC_IMPLEMENTATION_SCOPE,
    TSC_LEGACY_IMPORT_COMPATIBLE,
    TSC_OWNER,
    assert_legacy_reproduction_manifest,
)

__all__ = [
    "ALLOWED_COMBINED_LABELS",
    "FORBIDDEN_COMBINED_LABELS",
    "FORBIDDEN_TSC_FIELDS",
    "TSC_ACTIVE_SCIENCE_OWNER",
    "TSC_ALLOWED_BUNDLE_KIND",
    "TSC_DEPRECATION_CAVEAT",
    "TSC_DEPRECATION_STATUS",
    "TSC_IMPLEMENTATION_SCOPE",
    "TSC_LEGACY_IMPORT_COMPATIBLE",
    "TSC_NOT_APPLICABLE",
    "TSC_OWNER",
    "assert_legacy_reproduction_manifest",
]
