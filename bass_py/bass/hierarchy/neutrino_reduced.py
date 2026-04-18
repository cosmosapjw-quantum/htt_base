"""bass/hierarchy/neutrino_reduced.py (LB-5) — 4-scalar reduced ν fluid.

At LB-5 scope the neutrino sector is modelled by the fluid-limit
retained set ``(Δ_ν, q_ν, π_ν, G_3)`` — see lowell §9.3 and
Ma-Bertschinger 1995 eq (49). A full PSTF multipole tower matching
the photon temperature state is deferred to LB-5b (spec §13).

Definitions (lowell §9.3; Ma-Bertschinger 1995 eq (49)):

    Δ_ν   : neutrino density contrast
    q_ν   : neutrino heat flux magnitude
    π_ν   : neutrino anisotropic stress magnitude
    G_3   : ℓ = 3 truncation moment

At the **k = 0 background only** LB-5 scope, the scalar gradient
terms ∇̃ vanish identically and the four scalars decouple from the
photon hierarchy. The only active term is the expansion damping

    Δ̇_ν = −Θ (1 + w_ν) Δ_ν  ≈  −(4/3) Θ Δ_ν          (radiation)
    q̇_ν = −Θ q_ν                                       (heat flux drag)
    π̇_ν = −Θ π_ν                                       (anisotropic drag)
    Ġ_3 = −Θ G_3

All four obey the same ``Π̇ = −Θ Π`` dissipation at k = 0 in conformal-
η parameterisation (``Π'(η) = a × Π̇``), so the four-scalar block is a
linear system with a diagonal ``−a Θ`` matrix at background.

At non-zero k (post-LB-5) the block picks up the full Ma-Bertschinger
eq (49) cross-couplings; the signature of ``neutrino_reduced_rhs``
already carries ``bg_table`` to accommodate that extension without a
rewrite.

References
----------
- Ma-Bertschinger 1995 (astro-ph/9506072) eq (49).
- lowell §9.3 (retained-set definition).
- ``docs/lowell_bianchi/05_integrator_spec.md §1, §3, §12``.
- Kolb §3.3 (radiation fluid continuity).
"""
from __future__ import annotations

import numpy as np

from bass.species.background_table import FLRWBackgroundTable


__all__ = [
    "NEUTRINO_REDUCED_LABELS",
    "neutrino_reduced_rhs",
]


NEUTRINO_REDUCED_LABELS: tuple = ("Delta_nu", "q_nu", "pi_nu", "G_3")
"""Canonical order of the 4-scalar reduced ν fluid moments.

Matches the tail-of-state packing layout in
``bass/hierarchy/pack_unpack.py`` (spec §2.1 last four indices).
"""

_W_RADIATION: float = 1.0 / 3.0
"""Equation of state ``w = p/ρ = 1/3`` for relativistic neutrinos
(Kolb §3.3; massless assumption at LB-5)."""


def neutrino_reduced_rhs(
    eta: float,
    nu_state: np.ndarray,
    *,
    bg_table: FLRWBackgroundTable,
) -> np.ndarray:
    """``dy/dη`` for the 4-scalar reduced neutrino fluid at one η.

    At the k = 0 LB-5 background scope the RHS is the diagonal
    expansion-damping block

        Δ_ν'   = −a Θ (1 + w_ν) Δ_ν
        q_ν'   = −a Θ q_ν
        π_ν'   = −a Θ π_ν
        G_3'   = −a Θ G_3

    with ``(1 + w_ν) = 4/3`` for the radiation-era fluid (``w = 1/3``).
    The common prefactor ``a Θ = 3 a H = 3 𝓗`` so the damping rate is
    proportional to conformal Hubble.

    Parameters
    ----------
    eta : float
        Conformal time [Mpc].
    nu_state : ndarray of shape (4,)
        ``(Δ_ν, q_ν, π_ν, G_3)`` at ``eta``.
    bg_table : FLRWBackgroundTable
        Shared FLRW background table; supplies ``a(η)`` and ``Θ(η)``.

    Returns
    -------
    ndarray of shape (4,)
        ``d(Δ_ν, q_ν, π_ν, G_3)/dη`` in the same layout.

    Raises
    ------
    ValueError
        ``nu_state`` not shape ``(4,)``.

    Reference: Ma-Bertschinger 1995 eq (49); spec §3, §12.
    """
    arr = np.asarray(nu_state, dtype=np.float64)
    if arr.shape != (4,):
        raise ValueError(
            f"nu_state must have shape (4,), got {arr.shape}"
        )

    a_val = float(bg_table.interp_a(eta))
    Theta = float(bg_table.interp_Theta(eta))
    # Common damping rate in η-prime units: Π'(η) = a × Π̇(τ)
    damping = -a_val * Theta
    one_plus_w = 1.0 + _W_RADIATION     # 4/3 at radiation

    d_Delta = damping * one_plus_w * arr[0]
    d_q     = damping * arr[1]
    d_pi    = damping * arr[2]
    d_G3    = damping * arr[3]
    return np.array([d_Delta, d_q, d_pi, d_G3], dtype=np.float64)
