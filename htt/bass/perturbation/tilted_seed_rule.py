"""FB-5.6 skeleton — tilted-boost seed-rule contract.

This module deliberately ships no physics during the FB-META-5
rotation. The public surface below is a contract placeholder only and
must raise ``NotImplementedError`` until the tilted initial-value boost
and PSTF re-regularisation rule are implemented.
"""
from __future__ import annotations

import numpy as np


def apply_tilted_boost_seed_rule(
    seed_state: np.ndarray,
    *,
    beta: float,
    v_hat_e: tuple[float, float, float],
) -> np.ndarray:
    """Future FB-5.6 tilted-boost regularisation of perturbation seeds.

    Contract only: this surface is reserved for the future rule that
    takes an orthogonal perturbation seed, applies the appropriate tilt
    boost on the initial-value surface, and re-regularises the result in
    PSTF form before the perturbative hierarchy evolves.

    References
    ----------
    - ``docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 Phase FB-5``.
    - ``bass/hierarchy/boost_kernel.py`` (current boost-side PSTF SSOT
      and the off-axis defer carried into FB-5).
    - ``bass/perturbation/regular_adiabatic_ic.py`` (orthogonal seed
      placeholder landed at FB-5.3).
    - Challinor 2000, arXiv:astro-ph/9911481 (PSTF multipoles and
      observer dependence; broad boost formalism anchor).
    - ``# TODO: citation needed`` exact Lowell `§13.5` tilted-seed rule
      text; the on-disk solver-reference path is absent in this worktree.
    """
    raise NotImplementedError(
        "FB-5.6 skeleton only: tilted boost seed rule is not "
        "implemented."
    )
