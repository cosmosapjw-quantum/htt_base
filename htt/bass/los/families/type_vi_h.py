"""Type VI_h (class-B negative-h twist) transport kernel — skeleton.

Numerics deferred to S5 (Wave B). Basis: reuses Type VI_0 directional
machinery with h-dependent twist. The h parameter from
``family_spec.algebra.h_parameter`` must appear in the kernel name
(enforced by ``_FAMILY_RESIDUALS['VI_h']`` which lists
``h_consistency``).

Forbidden shortcuts (from ``_MUST_NOT_DO['VI_h']``):

* ``no_using_vi0_seed_at_nonzero_h``
* ``no_hiding_h_inside_generic_branch_label``
"""
from __future__ import annotations

from bass.los.families.base import NotImplementedKernel


class TypeVIhKernel(NotImplementedKernel):
    family = "VI_h"
    branch = "class_b_negative_h"
    deferred_to = "S5 (Wave B)"


KERNEL = TypeVIhKernel()
