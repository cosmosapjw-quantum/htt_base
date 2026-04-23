"""Type IX (compact SU(2)) transport kernel — skeleton.

Numerics deferred to S4 (Wave A). Basis: Wigner-D matrices via
``scipy.special.sph_harm_y``; passive Euler rotation. Easiest of
Wave A because compactness eliminates cutoff choice.

Forbidden shortcuts (from ``_MUST_NOT_DO['IX']``):

* ``no_untracked_compact_basis_reordering``
"""
from __future__ import annotations

from bass.los.families.base import NotImplementedKernel


class TypeIXKernel(NotImplementedKernel):
    family = "IX"
    branch = "wigner_d_compact"
    deferred_to = "S4 (Wave A)"


KERNEL = TypeIXKernel()
