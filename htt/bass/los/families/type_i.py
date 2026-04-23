"""Type I (Kasner-like, abelian) transport kernel.

Type I is the only family that lands with real numerics in S3. It
delegates to ``build_lowell_line_of_sight_propagator`` — the legacy
Lowell LoS builder — through ``LegacyDelegationKernel``. This gives the
facade a Protocol-conforming reference implementation that still
produces the D_2 regression-anchor numerics bit-identically.
"""
from __future__ import annotations

from bass.los.families.base import LegacyDelegationKernel


class TypeIKernel(LegacyDelegationKernel):
    family = "I"
    branch = "cartesian_regular"
    chart = "cartesian_regular_chart"


KERNEL = TypeIKernel()
