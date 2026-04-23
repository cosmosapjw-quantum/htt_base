"""Type VIII (SL(2,ℝ) noncompact) transport kernel — skeleton.

Numerics deferred to S5 (Wave B). Discrete series via
``scipy.special.lpmv``; continuous series deferred per plan
Open-Question 1 (``mpmath.hyper`` with imaginary ₂F₁ parameters).

Forbidden shortcuts (from ``_MUST_NOT_DO['VIII']``):

* ``no_compact_su2_reuse``
* ``no_wigner_d_assumption_without_explicit_approximation_tag``
"""
from __future__ import annotations

from bass.los.families.base import NotImplementedKernel


class TypeVIIIKernel(NotImplementedKernel):
    family = "VIII"
    branch = "sl2r_discrete"
    deferred_to = "S5 (Wave B, discrete series only — continuous deferred)"


KERNEL = TypeVIIIKernel()
