"""Type IV (solvable group, most anisotropic) transport kernel — skeleton.

Numerics deferred to S5 (Wave B). Basis: exponential decay × Bessel
tensor product; closure via anisotropic edge metadata. The
``no_chart_swap_without_translator_update`` forbidden shortcut must be
enforced at kernel construction time.

Forbidden shortcuts (from ``_MUST_NOT_DO['IV']``):

* ``no_isotropic_radial_reduction``
* ``no_chart_swap_without_translator_update``
"""
from __future__ import annotations

from bass.los.families.base import NotImplementedKernel


class TypeIVKernel(NotImplementedKernel):
    family = "IV"
    branch = "solvable_group_base"
    deferred_to = "S5 (Wave B)"


KERNEL = TypeIVKernel()
