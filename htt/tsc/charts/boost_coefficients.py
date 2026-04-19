"""
tsc/charts/boost_coefficients.py  (Week 4 Day 5, Part 3 — P2-W4-01 refactor)
================================================================================

Paper I Proposition 5 boost mixing coefficients and transforms.

Originally defined in `bass/validation/channel_routing.py` under the pre-v4.1
flat layout. These coefficients physically belong to the TSC chart layer
(they transform Teff multipoles under a perturbative boost), so W4+ moves
them here. The v4.1 ownership rules permit bass/validation to import from
tsc/; the converse is what gets enforced. With this move, the lone
whitelist entry in `test_ownership_freeze.py::test_tsc_source_never_imports_bass_runtime_family`
is retired.

Physical content
----------------
Paper I Eqs. 29-32 give the axisymmetric boost law for Teff multipoles:

    T̃_0 = T_0 − (1/6) v²
    T̃_a = T_a + v_a − (4/5) T_ab v^b
    T̃_ab = T_ab + 2 v_⟨a T_b⟩ + v_⟨a v_b⟩
    T̃_abc = T_abc + 3 T_⟨ab v_c⟩   (octupole is purely induced from quadrupole)

Axisymmetric scalar-amplitude form: the mixing matrix B[ℓ, ℓ'] collects
the multipole-multipole couplings, while an additive vector a[ℓ] holds
the pure-velocity terms (independent of initial multipole state).

No gating
---------
Pure arithmetic on the TSC chart. No CanonicalDecision is consulted.
"""
from __future__ import annotations

import numpy as np


# ============================================================================
# Section 1 - Paper I Prop 5 mixing coefficients
# ============================================================================

# Canonical coefficients from Paper I Eqs. 29-32 (axisymmetric case)
PROP5_COEFF_DIPOLE_FROM_QUADRUPOLE: float = -4.0 / 5.0
"""T̃_a gets −(4/5) T_ab v^b coupling from the quadrupole."""

PROP5_COEFF_QUADRUPOLE_FROM_DIPOLE: float = +2.0
"""T̃_ab gets +2 v_⟨a T_b⟩ coupling from the dipole."""

PROP5_COEFF_OCTUPOLE_FROM_QUADRUPOLE: float = +3.0
"""T̃_abc = 3 T_⟨ab v_c⟩ — octupole is purely induced from quadrupole."""


# ============================================================================
# Section 2 - Boost mixing matrix
# ============================================================================

def boost_mixing_matrix(
    v: float, ell_max: int = 3,
) -> np.ndarray:
    """Linearized boost mixing matrix B with entries from Paper I Prop 5.

    For an axisymmetric boost of magnitude |v| along ê, the linear
    response of the Teff multipoles at O(v) is:

        T̃_ℓ = sum_{ℓ'} B[ℓ, ℓ'] T_{ℓ'} + (additive velocity terms)

    The mixing matrix entries from Prop 5:

        B[1, 2] = −4/5     (quadrupole → dipole)
        B[2, 1] = +2       (dipole → quadrupole)
        B[3, 2] = +3       (quadrupole → octupole; purely induced)

    Diagonal B[ℓ, ℓ] = 1 (identity part).

    Parameters
    ----------
    v : float
        Boost magnitude |v|. Must be small (|v| ≪ 1) for linearization.
    ell_max : int, optional
        Highest multipole index retained. Default 3 (enough for Prop 5).

    Returns
    -------
    B : ndarray shape (ell_max+1, ell_max+1)
        Linearized mixing matrix. B[ℓ, ℓ'] is the coupling of T_{ℓ'} into T̃_ℓ.
    """
    if ell_max < 1:
        raise ValueError(f"ell_max must be ≥ 1, got {ell_max}")
    if abs(v) >= 1.0:
        raise ValueError(
            f"Linear boost mixing requires |v| < 1, got |v| = {abs(v)}"
        )

    B = np.eye(ell_max + 1)
    if ell_max >= 2:
        B[1, 2] = PROP5_COEFF_DIPOLE_FROM_QUADRUPOLE * v
        B[2, 1] = PROP5_COEFF_QUADRUPOLE_FROM_DIPOLE * v
    if ell_max >= 3:
        B[3, 2] = PROP5_COEFF_OCTUPOLE_FROM_QUADRUPOLE * v
    return B


def boost_additive_velocity_terms(
    v: float, ell_max: int = 3,
) -> np.ndarray:
    """Additive (non-multiplicative) contributions from the boost velocity itself.

    Paper I Eqs. 29-31 show that the boost law includes terms that do NOT
    multiply the existing Teff multipoles:

        T̃_0 += −(1/6) v_a v^a                    (ℓ=0 from v²)
        T̃_a += v_a                               (ℓ=1 from v)
        T̃_ab += v_⟨a v_b⟩                         (ℓ=2 from v²)

    These are the "induced" multipole contributions carried by the boost
    itself, independent of the initial state.

    Parameters
    ----------
    v : float
        Boost magnitude.
    ell_max : int, optional
        Highest multipole index.

    Returns
    -------
    a : ndarray shape (ell_max+1,)
        Additive velocity contributions by multipole rank.
    """
    a = np.zeros(ell_max + 1)
    if ell_max >= 0:
        a[0] = -(1.0 / 6.0) * v**2
    if ell_max >= 1:
        a[1] = v
    if ell_max >= 2:
        a[2] = v**2
    # T̃_abc has no pure-velocity term at this order
    return a


# ============================================================================
# Section 3 - Combined boost transform
# ============================================================================

def apply_boost_to_teff(
    T_multipoles: np.ndarray, v: float,
) -> np.ndarray:
    """Apply the perturbative boost law to an axisymmetric Teff multipole state.

    Implements Paper I Prop 5 at O(v) linear + O(v²) pure-velocity additions.

        T̃ = B(v) T + a(v)

    Parameters
    ----------
    T_multipoles : ndarray shape (L+1,)
        Initial Teff multipoles [T_0, T_1, T_2, ..., T_L].
    v : float
        Boost magnitude (axisymmetric).

    Returns
    -------
    T_tilde : ndarray same shape
        Boosted multipoles.
    """
    ell_max = len(T_multipoles) - 1
    B = boost_mixing_matrix(v, ell_max)
    a = boost_additive_velocity_terms(v, ell_max)
    return B @ T_multipoles + a
