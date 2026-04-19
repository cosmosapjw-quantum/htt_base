"""FB-5.1 skeleton — harmonic-mode context for ``k != 0`` perturbations.

This module deliberately ships no physics during the FB-META-5
rotation. The public surface below is a contract placeholder only and
must raise ``NotImplementedError`` until the full per-type harmonic-mode
state machine and complex-dtype ``nabla_tilde`` wire-up are implemented.
"""
from __future__ import annotations

from bass.background.bianchi_types import StructureConstants
from bass.hierarchy.nabla_dispatch import HarmonicMode


def make_harmonic_mode_rhs_context(
    structure: StructureConstants,
    mode: HarmonicMode,
    *,
    L_max: int,
) -> dict[str, object]:
    """Future FB-5.1 harmonic-mode context for perturbative ``k != 0``.

    Contract only: this surface is reserved for the future wrapper that
    binds the FB-2 ``HarmonicMode`` descriptor and complex-valued
    ``make_nabla_tilde`` operator to the perturbation-sector RHS without
    mutating the shipped real-dtype hierarchy driver ahead of the full
    FB-5 implementation.

    References
    ----------
    - ``docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 Phase FB-5``.
    - ``bass/hierarchy/nabla_dispatch.py`` (FB-2 complex ``nabla_tilde``
      anchor and the explicit ``FB-5.2`` off-axis defer).
    - Pontzen & Challinor 2007, arXiv:0706.2075 (Bianchi hierarchy and
      VII_h spiral-mode context; corrected from the broken prompt-supplied
      arXiv ID ``astro-ph/0607373``).
    - ``# TODO: citation needed`` historical Lowell solver reference
      ``§13.1`` path is not present on disk in this worktree.
    """
    raise NotImplementedError(
        "FB-5.1 skeleton only: harmonic-mode context and complex-dtype "
        "nabla wire-up are not implemented."
    )
