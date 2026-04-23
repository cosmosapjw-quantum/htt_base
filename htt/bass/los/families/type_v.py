"""Type V (open hyperbolic) transport kernel — skeleton.

Numerics deferred to S5 (Wave B). Basis: hyperbolic Legendre (reuses
Type III); closure via ``open_hyperbolic_radial_cutoff``.

Forbidden shortcuts (from ``_MUST_NOT_DO['V']``):

* ``no_hidden_flrw_import_without_open_chart_metadata``
"""
from __future__ import annotations

from bass.los.families.base import NotImplementedKernel


class TypeVKernel(NotImplementedKernel):
    family = "V"
    branch = "open_hyperbolic"
    deferred_to = "S5 (Wave B)"


KERNEL = TypeVKernel()
