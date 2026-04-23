"""Type VI_0 (class-A solvable, directional) transport kernel — skeleton.

Numerics deferred to S4 (Wave A). Basis: product of cos/sin per-axis
with directional tag; mixed-sign directional 2-sector refinement
required.

Forbidden shortcuts (from ``_MUST_NOT_DO['VI_0']``):

* ``no_borrowing_type_i_or_vii_seeds``
* ``no_isotropic_direction_compression``
"""
from __future__ import annotations

from bass.los.families.base import NotImplementedKernel


class TypeVI0Kernel(NotImplementedKernel):
    family = "VI_0"
    branch = "class_a_solvable"
    deferred_to = "S4 (Wave A)"


KERNEL = TypeVI0Kernel()
