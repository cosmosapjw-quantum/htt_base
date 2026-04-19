"""FB-7.2 skeleton — diagonal-plus-off-diagonal spectrum contract.

This module deliberately ships no spectrum extraction physics during the
FB-META-7 rotation. The public surface below is a contract placeholder
only and must raise ``NotImplementedError`` until the FB-7 spectrum
stack can assemble diagonal ``C_ell`` and off-diagonal
``C_{ell m, ell' m'}`` outputs from the LOS transfer bundle.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Literal

import numpy as np


def assemble_bianchi_spectrum_covariance(
    *,
    transfer_bundle: Mapping[str, np.ndarray],
    k_grid_mpc: np.ndarray,
    ell_max: int,
    off_diagonal_strategy: Literal[
        "m_decoupled_blocks",
        "dense_matrix",
        "wigner_d_sparse",
    ] = "m_decoupled_blocks",
) -> dict[str, object]:
    """Future FB-7.2 diagonal and off-diagonal spectrum assembler.

    Contract only: this surface is reserved for the future spectrum
    builder that emits diagonal ``C_ell^{TT,EE,TE,BB}`` together with
    off-diagonal anisotropic covariance blocks ``C_{ell m, ell' m'}``
    from the LOS transfer bundle.

    References
    ----------
    - ``docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 Phase FB-7``.
    - ``bass/spectrum/cl_assembly.py`` (existing diagonal-only spectrum
      consumer and explicit off-diagonal placeholder).
    - ``bass/spectrum/lowell_los.py`` (future FB-7.1 LOS transfer input).
    - Lewis & Challinor 2006, arXiv:astro-ph/0601594 (review-level
      polarized-spectrum / covariance context).
    - Pontzen & Challinor 2007, arXiv:0706.2075 (corrected Bianchi
      polarization / anisotropic-mixing anchor; the prompt-supplied
      ``astro-ph/0607373`` is a different paper and is rejected in the
      FB-META-7 audit).
    """
    raise NotImplementedError(
        "FB-7.2 skeleton only: diagonal plus off-diagonal Bianchi "
        "spectrum covariance is not implemented."
    )
