"""FB-5.3 skeleton — CAMB regular adiabatic seed initial conditions.

This module deliberately ships no physics during the FB-META-5
rotation. The public surface below is a contract placeholder only and
must raise ``NotImplementedError`` until the perturbation-sector CAMB
regular adiabatic seed is derived and packed onto the BASS state vector.
"""
from __future__ import annotations

import numpy as np


def make_camb_regular_adiabatic_seed(
    *,
    k_comoving: float,
    eta_initial: float,
    a_initial: float,
    L_max: int,
) -> np.ndarray:
    """Future FB-5.3 CAMB-style regular adiabatic perturbation seed.

    Contract only: this surface is reserved for the future replacement
    of the current zero-by-default perturbation seed with a packed
    regular-adiabatic state carrying the leading-order radiation-era
    photon, baryon, CDM, and neutrino amplitudes for one comoving mode.

    References
    ----------
    - ``docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 Phase FB-5``.
    - ``bass/hierarchy/ic.py`` (current zero-IC anchor and the explicit
      forward note that CAMB-regular seeding belongs in FB-5.3).
    - Ma & Bertschinger 1995, arXiv:astro-ph/9506072 (super-horizon
      isentropic / adiabatic initial conditions).
    - ``# TODO: citation needed`` exact CAMB seed locator; the prompt-
      supplied Lewis-Challinor anchor `astro-ph/9911177` is a closed-FRW
      line-of-sight paper, not an initial-condition derivation.
    - ``# TODO: citation needed`` historical Lowell solver reference
      ``§13.2`` path is not present on disk in this worktree.
    """
    raise NotImplementedError(
        "FB-5.3 skeleton only: CAMB regular adiabatic seed initial "
        "conditions are not implemented."
    )
