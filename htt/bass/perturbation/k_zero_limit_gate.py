"""FB-5.4 skeleton — explicit ``k = 0`` perturbation-limit gate.

This module deliberately ships no physics during the FB-META-5
rotation. The public surface below is a contract placeholder only and
must raise ``NotImplementedError`` until the perturbation-sector
``k = 0`` limit is checked against the shipped LB-6 background anchor.
"""
from __future__ import annotations

import numpy as np


def assert_k_zero_limit_matches_background(
    *,
    k_comoving: float,
    background_state: np.ndarray,
    perturbation_state: np.ndarray,
    atol: float,
    rtol: float,
) -> None:
    """Future FB-5.4 validator for the ``k = 0`` perturbation limit.

    Contract only: this surface is reserved for the future assertion
    that the perturbative ``k -> 0`` evolution reduces to the shipped
    LB-6 background-only path, with any large-scale Sachs-Wolfe gate
    applied explicitly rather than hidden inside the integrator.

    References
    ----------
    - ``docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 Phase FB-5``.
    - ``bass/integration/test_lowell_bianchi.py`` (LB-6 background and
      geometry regression anchor).
    - ``docs/PROGRESS_SCOREBOARD.md`` (existing k=0 physics-gate note).
    - ``# TODO: citation needed`` Sachs & Wolfe 1967 original paper
      (not arXiv-era; unverified in the arXiv-only channel).
    - ``# TODO: citation needed`` Kolb & Turner 1990 §9.6 locator
      (book citation, not verifiable on arXiv).
    """
    raise NotImplementedError(
        "FB-5.4 skeleton only: k=0 perturbation-limit gate is not "
        "implemented."
    )
