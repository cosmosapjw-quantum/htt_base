"""Type III (class-B hyperbolic, h=-1) transport kernel — skeleton.

Numerics deferred to S4 (Wave A). Basis: ``scipy.special.lpmv`` with
imaginary order for the hyperbolic continuation; closure via
``truncated_hyperbolic_branch``. Special branch flag
``VI_-1_special`` must be recorded in kernel metadata (from
``_DEFAULT_BRANCH_FLAGS['III']``).

Forbidden shortcuts (from ``_MUST_NOT_DO['III']``):

* ``no_open_flrw_seed_import_without_branch_justification``
* ``no_dropping_special_branch_flag``
"""
from __future__ import annotations

from bass.los.families.base import NotImplementedKernel


class TypeIIIKernel(NotImplementedKernel):
    family = "III"
    branch = "class_b_special"
    deferred_to = "S4 (Wave A)"


KERNEL = TypeIIIKernel()
