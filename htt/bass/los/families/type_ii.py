"""Type II (nil-Heisenberg) transport kernel — skeleton.

Numerics deferred to S4 (Wave A). Basis: ``scipy.special.jn`` with
twisted argument, collocation on a finite domain with edges logged.
Forbidden shortcuts (from ``_MUST_NOT_DO['II']``):

* ``no_flrw_seed_reuse``
* ``no_implicit_periodic_boundary``
* ``no_unlabeled_branch_choice``
"""
from __future__ import annotations

from bass.los.families.base import NotImplementedKernel


class TypeIIKernel(NotImplementedKernel):
    family = "II"
    branch = "nil_intrinsic"
    deferred_to = "S4 (Wave A)"


KERNEL = TypeIIKernel()
