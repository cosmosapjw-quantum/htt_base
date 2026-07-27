"""Canonical model ordering used by active null-library consumers.

The same ordering remains embedded in ``htt.core.analysis_extended`` for
historical byte/value reproduction.  Active code imports this dependency-light
copy so it does not activate the legacy filling/ceiling implementation.
"""
from __future__ import annotations

EVIDENCE_MODEL_TAGS = (
    "FLRW",
    "FLRW_tilt",
    "BI_orth",
    "BVII0_orth",
    "BII_orth",
    "BVI0_orth",
    "BVIII_orth",
    "BIX_orth",
    "BVIIh_orth",
    "BVIIh_orth_grow",
    "BI_tilt",
    "BV_tilt",
    "BIII_tilt",
    "BIX_tilt",
    "BVIIh_tilt",
    "BVIIh_tilt_grow",
)

__all__ = ["EVIDENCE_MODEL_TAGS"]
