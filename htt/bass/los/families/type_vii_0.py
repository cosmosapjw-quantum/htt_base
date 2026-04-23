"""Type VII_0 (helical Euclidean) transport kernel — skeleton.

Numerics deferred to S5 (Wave B). Basis: ``scipy.special.spherical_jn``
with helical chart transform.

Forbidden shortcuts (from ``_MUST_NOT_DO['VII_0']``):

* ``no_hidden_branch_choice``
* ``no_local_boost_folded_into_backend``
"""
from __future__ import annotations

from bass.los.families.base import NotImplementedKernel


class TypeVII0Kernel(NotImplementedKernel):
    family = "VII_0"
    branch = "helical_euclidean"
    deferred_to = "S5 (Wave B)"


KERNEL = TypeVII0Kernel()
