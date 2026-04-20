"""Gauss-Laguerre phase-space grid for the FB-9 massive-neutrino sector.

The load-bearing invariant remains
``Sigma_mnu = 0 -> byte-identical to the LB-1 massless
NeutrinoBackground``: the zero-mass production path still stays on the
existing LB-1 class via the registry. This module only serves the
positive-mass branch.

The grid is expressed in the dimensionless comoving momentum

    q = p a / T_nu,0 ,

so the quadrature itself is independent of the neutrino mass in the
degenerate-thermal approximation. The ``mass_eV`` argument is still part
of the public contract because the FB-9 SDD pins the call signature and
because future non-thermal extensions may choose mass-dependent
optimisation.
"""
from __future__ import annotations

from typing import Tuple

import numpy as np
from numpy.polynomial.laguerre import laggauss


__all__ = [
    "MASSLESS_FD_ENERGY_INTEGRAL",
    "phase_space_grid",
]


# ∫ dq q^3 / (exp(q) + 1) = 7 π^4 / 120  (massless energy-density moment).
MASSLESS_FD_ENERGY_INTEGRAL: float = 7.0 * np.pi ** 4 / 120.0


def phase_space_grid(
    mass_eV: float,
    N_q: int = 15,
) -> Tuple[np.ndarray, np.ndarray]:
    """Return the deterministic `(q_grid, weights)` quadrature pair.

    ``q_grid`` contains the Gauss-Laguerre abscissae. ``weights``
    already include the Fermi-Dirac phase-space measure ``q² f_FD(q)``
    so that

        ∫ dq q² f_FD(q) g(q)  ~=  Σ_i weights[i] g(q_grid[i])

    for smooth ``g``. Background thermodynamics then reduce to simple
    weighted sums over ``epsilon(q, a)`` and ``q² / epsilon(q, a)``.

    Parameters
    ----------
    mass_eV : float
        Per-species neutrino mass in eV. The thermal-FD grid in
        ``q = p a / T_nu,0`` units is mass-independent, but the public
        signature keeps the mass argument pinned to the FB-9 SDD.
    N_q : int, default ``15``
        Number of Gauss-Laguerre nodes. FB-9 pins ``N_q = 15`` as the
        default delivery budget.
    """
    if mass_eV < 0.0:
        raise ValueError(f"mass_eV must be non-negative, got {mass_eV}")
    if N_q <= 0:
        raise ValueError(f"N_q must be positive, got {N_q}")

    q_grid, laguerre_weights = laggauss(int(N_q))
    q_grid = np.asarray(q_grid, dtype=np.float64)
    laguerre_weights = np.asarray(laguerre_weights, dtype=np.float64)

    # Gauss-Laguerre integrates ∫ exp(-q) h(q) dq. Rewriting the FD
    # measure as q² / (exp(q) + 1) = exp(-q) * q² / (1 + exp(-q))
    # yields a stable positive weight function.
    weights = laguerre_weights * q_grid ** 2 / (1.0 + np.exp(-q_grid))
    return q_grid, np.asarray(weights, dtype=np.float64)
