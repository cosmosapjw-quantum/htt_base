"""Type VII_h (helical open, h>0) transport kernel — skeleton.

Numerics deferred to S5 (Wave B). Basis: ``spherical_jn`` + Legendre
hybrid with h-dependent radial cutoff.

Forbidden shortcuts (from ``_MUST_NOT_DO['VII_h']``):

* ``no_hidden_h_branch_choice``
* ``no_local_boost_folded_into_backend``
"""
from __future__ import annotations

from bass.los.families.base import NotImplementedKernel


class TypeVIIhKernel(NotImplementedKernel):
    family = "VII_h"
    branch = "helical_open_h"
    deferred_to = "S5 (Wave B)"


KERNEL = TypeVIIhKernel()
