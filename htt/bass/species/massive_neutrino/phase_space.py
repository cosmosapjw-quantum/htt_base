"""FB-9.1 skeleton — massive-neutrino phase-space grid contract.

The only load-bearing invariant at this stage is
``Sigma_mnu = 0 -> byte-identical to the LB-1 massless
NeutrinoBackground``: this module exists to reserve the future massive-ν
quadrature surface, not to replace the LB-1 massless runtime.
"""
from __future__ import annotations

from typing import Tuple

import numpy as np


def phase_space_grid(
    mass_eV: float,
    N_q: int = 15,
) -> Tuple[np.ndarray, np.ndarray]:
    """Return the future `(q_grid, weights)` quadrature pair.

    The invariant remains ``Sigma_mnu = 0 -> byte-identical to the
    LB-1 massless NeutrinoBackground`` because the massless production
    path must not route through this FB-9.1 placeholder.
    """
    raise NotImplementedError(
        "FB-9.1 skeleton only: phase_space_grid is reserved for the "
        "future massive-neutrino quadrature implementation."
    )
