"""FB-5.2 skeleton — full off-axis ``nabla_tilde`` mode dispatch.

This module deliberately ships no physics during the FB-META-5
rotation. The public surface below is a contract placeholder only and
must raise ``NotImplementedError`` until the off-axis Wigner-d mode
rotation and full ``k != 0`` spatial-derivative dispatch are implemented.
"""
from __future__ import annotations

from typing import Callable

from bass.background.bianchi_types import StructureConstants
from bass.hierarchy.nabla_dispatch import HarmonicMode


def make_full_mode_nabla_tilde_operator(
    structure: StructureConstants,
    mode: HarmonicMode,
    *,
    euler_angles: tuple[float, float, float],
) -> Callable[..., object]:
    """Future FB-5.2 off-axis ``nabla_tilde`` operator for perturbations.

    Contract only: this surface is reserved for the future off-axis
    Wigner-d rotation that lifts the axis-aligned FB-2 dispatch into the
    full mode-resolved ``k != 0`` perturbation operator without silently
    falling back to the abelian-subalgebra subsets already shipped.

    References
    ----------
    - ``docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 Phase FB-5``.
    - ``bass/hierarchy/nabla_dispatch.py`` (explicit FB-5.2 defer on all
      non-axis-aligned / non-abelian subsets).
    - ``bass/hierarchy/boost_kernel.py`` (off-axis Wigner-d defer in the
      sibling tilted-boost seed surface).
    - Pontzen & Challinor 2007, arXiv:0706.2075 (verified Bianchi
      hierarchy context only).
    - ``# TODO: citation needed`` exact off-axis Wigner-d literature pin;
      the prompt-supplied Lowell solver reference ``§13`` path is not
      present on disk in this worktree.
    """
    raise NotImplementedError(
        "FB-5.2 skeleton only: off-axis nabla_tilde mode dispatch is not "
        "implemented."
    )
