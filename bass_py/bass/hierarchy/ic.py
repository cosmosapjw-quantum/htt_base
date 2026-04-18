"""bass/hierarchy/ic.py (LB-5) — initial condition constructors.

Build the packed ``Y(η_initial)`` state vector handed to ``solve_ivp``.
At LB-5 the baseline is **all-zero except ``a(η_initial)``**: the
perturbation sector is integrated-in-future; the only non-trivial
physics at the start is the background scale factor plus (optionally)
a seeded tetrad shear ``Σ_+(η_initial)`` that triggers the T9 shear-
injection term in the hierarchy RHS and thereby excites Π_2 through
the Thomson source (damped or TCA-balanced depending on Γ_T).

``CAMB-regular-adiabatic`` seeding for the full perturbation sector
(lowell §13.2) is deferred to LB-6/LB-7 per the spec §6 note.

References
----------
- ``docs/lowell_bianchi/05_integrator_spec.md §6`` (IC policy;
  zero-by-default; non-zero Σ_+ as a config option).
- Ma-Bertschinger 1995 §7 (regular-adiabatic seed IC for the FLRW
  Boltzmann system — cited for LB-6 forward compatibility).
- Ellis §18.3 (Bianchi I background IC).
"""
from __future__ import annotations

from typing import Optional

import numpy as np

from bass.collision.polarization import zero_polarization_hierarchy
from bass.hierarchy.pack_unpack import (
    NEUTRINO_REDUCED_SIZE,
    pack_combined_state,
)
from bass.hierarchy.pstf_tensor import zero_hierarchy


__all__ = [
    "zero_IC",
    "make_initial_state",
]


def _validate_scalar(name: str, value: float) -> float:
    if not np.isfinite(value):
        raise ValueError(f"{name} must be finite, got {value}")
    return float(value)


def zero_IC(
    *,
    L_max: int,
    a_initial: float,
    Sigma_plus_initial: float = 0.0,
    Sigma_minus_initial: float = 0.0,
) -> np.ndarray:
    """Baseline LB-5 initial condition: all zero except ``a`` and Σ.

    Parameters
    ----------
    L_max : int ≥ 0
        Top multipole retained (temperature + E-mode towers both).
    a_initial : float > 0
        Scale factor at the start of the integration (corresponds to
        ``η_initial``). Spec default: ``a ≈ 1e-4`` for ``η_initial ≈
        0.5 Mpc``.
    Sigma_plus_initial, Sigma_minus_initial : float
        Tetrad shear amplitudes at the start. ``0, 0`` → strict FLRW;
        non-zero values trigger the Bianchi I / V / VII₀ shear-injection
        term (T9 in the hierarchy).

    Returns
    -------
    y0 : (combined_total_size(L_max),) float64
        Packed initial state ready for ``solve_ivp``.

    Raises
    ------
    ValueError
        Invalid scalar (NaN / Inf / non-positive ``a_initial``) or
        ``L_max < 0``.

    Reference: spec §6.
    """
    if L_max < 0:
        raise ValueError(f"L_max must be non-negative, got {L_max}")
    a0 = _validate_scalar("a_initial", a_initial)
    if a0 <= 0.0:
        raise ValueError(f"a_initial must be positive, got {a0}")
    Sp = _validate_scalar("Sigma_plus_initial", Sigma_plus_initial)
    Sm = _validate_scalar("Sigma_minus_initial", Sigma_minus_initial)

    # Need L_max ≥ 2 for the E-mode tower (PolarizationHierarchyState
    # requires L ≥ 2). Use max(L_max, 2) for the E container; for
    # L_max < 2 the state ignores E content, but we still need valid
    # layout — spec §1 fixes L_max ≥ 2 at the integrator level, so we
    # assert here rather than silently promoting.
    if L_max < 2:
        raise ValueError(
            f"L_max must be ≥ 2 for the E-mode tower (spec §1.1); "
            f"got L_max={L_max}"
        )

    photon_T = zero_hierarchy(L=L_max)
    photon_E = zero_polarization_hierarchy(L=L_max)
    nu = np.zeros(NEUTRINO_REDUCED_SIZE, dtype=np.float64)

    return pack_combined_state(
        a=a0,
        Sigma_plus=Sp,
        Sigma_minus=Sm,
        photon_T=photon_T,
        photon_E=photon_E,
        neutrino_reduced=nu,
        L_max=L_max,
    )


def make_initial_state(
    *,
    L_max: int,
    a_initial: float,
    Sigma_plus_initial: float = 0.0,
    Sigma_minus_initial: float = 0.0,
    seed_Pi_2_m0: Optional[float] = None,
    seed_E_2_m0: Optional[float] = None,
) -> np.ndarray:
    """Extended IC constructor with optional axisymmetric quadrupole seeds.

    Deliberately narrow in scope — the only non-zero perturbations
    exposed at LB-5 are the axisymmetric ``m = 0`` slots of ``Π_2`` and
    ``E_2`` (the components that W6-04 TCA populates). Anything more
    general belongs in the CAMB-regular-adiabatic seeder shipped at
    LB-6.

    Reference: spec §6; spec §10.4 (I-13 shear-driven Π_2 source).
    """
    y0 = zero_IC(
        L_max=L_max,
        a_initial=a_initial,
        Sigma_plus_initial=Sigma_plus_initial,
        Sigma_minus_initial=Sigma_minus_initial,
    )
    if seed_Pi_2_m0 is None and seed_E_2_m0 is None:
        return y0

    # Import here to avoid a top-level cycle with pack_unpack (tests
    # for pack_unpack must not depend on the real-SH axisymmetric
    # convention).
    from bass.hierarchy.pack_unpack import (
        slice_photon_E, slice_photon_T, unpack_combined_state,
        pack_combined_state as _pack,
    )
    _ = slice_photon_T  # explicit re-export for readers
    _ = slice_photon_E

    state = unpack_combined_state(y0, L_max=L_max)
    if seed_Pi_2_m0 is not None:
        val = _validate_scalar("seed_Pi_2_m0", seed_Pi_2_m0)
        # m = 0 slot at ℓ=2 is index 2 in (-2,-1,0,+1,+2) packing.
        state.photon_T.tensors[2].components[2] = val
    if seed_E_2_m0 is not None:
        val = _validate_scalar("seed_E_2_m0", seed_E_2_m0)
        state.photon_E.E.tensors[2].components[2] = val

    return _pack(
        a=state.a,
        Sigma_plus=state.Sigma_plus,
        Sigma_minus=state.Sigma_minus,
        photon_T=state.photon_T,
        photon_E=state.photon_E,
        neutrino_reduced=state.neutrino_reduced,
        L_max=L_max,
    )
