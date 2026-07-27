"""Explicit historical comparator-ratio reproduction helpers.

This module preserves the old ``x_C / x_max`` arithmetic for frozen fixtures.
The denominator is not a typed MES anchor and the returned value has no
distance, filling, occupancy, probability, evidence, or family semantics.
New code must use ``bass.validation.comparator_policy`` together with the
typed COMMON anchor-stress contracts.
"""
from __future__ import annotations

import math
import warnings
from typing import Optional, Protocol, Tuple

from common.statistical_foundations import (
    BC1_LEGACY_PROJECTION,
    BC2_NO_REPRESENTATION_PROMOTION,
)

LEGACY_REPRODUCTION_ONLY = True

warnings.warn(
    "bass.validation.legacy_comparator_policy is for historical reproduction "
    "only; use typed sector stress for active analysis",
    DeprecationWarning,
    stacklevel=2,
)


class _LegacyComponents(Protocol):
    @property
    def x_C(self) -> Optional[float]: ...


def legacy_projection_ratio(
    comp: _LegacyComponents,
    denominator: float,
) -> Tuple[Optional[float], str]:
    """Reproduce the historical signed ratio without physical semantics."""

    if isinstance(denominator, bool) or not isinstance(denominator, (int, float)):
        return None, "invalid_legacy_denominator"
    denominator = float(denominator)
    if not math.isfinite(denominator) or denominator <= 0.0:
        return None, "invalid_legacy_denominator"
    value = comp.x_C
    if value is None:
        return None, "null_comparator"
    status = (
        "legacy_nonnegative_projection"
        if value >= 0.0
        else "legacy_signed_projection"
    )
    return float(value) / denominator, status


def filling_fraction(
    comp: _LegacyComponents,
    x_max: float,
) -> Tuple[Optional[float], str]:
    """Deprecated spelling retained only in the explicit legacy namespace."""

    warnings.warn(
        "filling_fraction is a legacy name for a denominator-conditioned "
        f"ratio ({BC1_LEGACY_PROJECTION}; "
        f"{BC2_NO_REPRESENTATION_PROMOTION})",
        DeprecationWarning,
        stacklevel=2,
    )
    value, status = legacy_projection_ratio(comp, x_max)
    compatibility_status = {
        "legacy_nonnegative_projection": "unsigned",
        "legacy_signed_projection": "signed",
        "invalid_legacy_denominator": "invalid_x_max",
    }.get(status, status)
    return value, compatibility_status


__all__ = [
    "LEGACY_REPRODUCTION_ONLY",
    "filling_fraction",
    "legacy_projection_ratio",
]
