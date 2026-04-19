"""FB-7.1 skeleton — line-of-sight matrix propagator contract.

This module deliberately ships no LOS physics during the FB-META-7
rotation. The public surface below is a contract placeholder only and
must raise ``NotImplementedError`` until the all-type line-of-sight
matrix propagator is wired to the existing Bianchi LOS and spectrum
scaffolding.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Literal

import numpy as np

from bass.background.bianchi_types import StructureConstants


def build_lowell_line_of_sight_propagator(
    structure: StructureConstants,
    *,
    eta_grid_mpc: np.ndarray,
    k_grid_mpc: np.ndarray,
    ell_max: int,
    visibility_fn: Callable[[float], float],
    source_builder: Callable[[float, float], Mapping[str, np.ndarray]],
    limber_eta_sp_sign: Literal["integrator", "legacy_negative"] = "integrator",
) -> dict[str, object]:
    """Future FB-7.1 line-of-sight matrix propagator across all 11 types.

    Contract only: this surface is reserved for the future LOS builder
    that composes visibility, anisotropic sources, and the per-type
    transfer geometry into the matrix propagator used by the FB-7
    spectrum stack.

    References
    ----------
    - ``docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 Phase FB-7``.
    - ``docs/lowell_bianchi/extended_coverage/PROJECT_MEMORY_EXPLICIT.md``
      §10 (phase-0 carry: Limber ``η_sp`` sign closes here).
    - ``bass/los/bianchi_propagator.py`` (existing Bianchi-I LOS
      scaffolding and FLRW / B-mode known limits).
    - ``bass/spectrum/cl_assembly.py`` (existing diagonal spectrum
      consumer of LOS transfer outputs).
    - Seljak & Zaldarriaga 1996, arXiv:astro-ph/9603033 (line-of-sight
      source-times-geometry split).
    - ``# TODO: citation needed`` exact on-disk Lowell ``§7`` locator;
      the prompt-supplied historical path is absent in this worktree and
      is recorded explicitly in the FB-META-7 audit.
    """
    raise NotImplementedError(
        "FB-7.1 skeleton only: all-type line-of-sight matrix propagator "
        "is not implemented."
    )
