"""bass/hierarchy/hierarchy_rhs.py (LB-2b) — PSTF multipole RHS driver.

Sums ``T1 + T2 + T3 + T4 + T5 + T6 + T7 + T8 + T9 − K`` at every ℓ of
a PSTF multipole tower and returns ``dy/dη`` in the packed state
layout consumed by ``scipy.integrate.solve_ivp``. Two entry points are
provided:

- ``hierarchy_rhs_photon`` — photon brightness tower. A pluggable
  ``CollisionOperator`` (``ThomsonCollisionOperator`` at LB-4; the
  LB-2b default is ``ZeroCollisionOperator``) supplies ``K_{A_ℓ}``.
- ``hierarchy_rhs_neutrino`` — convenience wrapper that hard-wires
  ``ZeroCollisionOperator`` for collisionless neutrinos.

Unit convention — F1 of the LB-2a audit (see
``docs/audits/AUDIT_PHASE_LB2a_2026-04-19.md``):

    Θ        : proper-time expansion Θ = 3 H [1/Mpc]
               (read directly from ``FLRWBackgroundTable.Theta``)
    σ_ab     : proper-time shear [1/Mpc]
               (converted from ``TetradBackgroundState.sigma_tensor``,
                which stores the **conformal** Σ_ab = e^α σ_ab = a σ_ab,
                by dividing by ``a(η)``)
    A_a, ω_a : zero for orthogonal Bianchi I / V / VII₀ (caller may
               override with explicit kwargs for future tilted /
               vorticity-bearing extensions)
    Π̇ → Π'(η): covariant overdot ``Π̇ = u^a ∇_a Π`` in conformal-η
               parameterisation becomes ``Π'(η) = a × Π̇``
               (Ellis §4.2; 02_multipole_hierarchy_spec.md §4.1).

References
----------
- lowell §6 (nine-term source equation; canonical form).
- lowell §9.2 (driver signature).
- Ellis, Maartens, MacCallum §4.6 (derivation of the hierarchy).
- Kolb-Turner §6.4 (simple Boltzmann moments, FLRW limit).
- ``docs/lowell_bianchi/02_multipole_hierarchy_spec.md §4, §8, §9``.
"""
from __future__ import annotations

from typing import Callable, Optional

import numpy as np

from bass.hierarchy.closure_interface import ClosureStrategy
from bass.hierarchy.collision_interface import (
    CollisionOperator,
    ZeroCollisionOperator,
)
from bass.hierarchy.contractions import pstf_pack, sym_trace_free
from bass.hierarchy.pstf_tensor import (
    PSTFHierarchyState,
    pstf_to_tensor,
    unpack_hierarchy,
)
from bass.hierarchy.terms import (
    T1_expansion,
    T2_gradient,
    T3_divergence,
    T4_accel_divergence,
    T5_accel_gradient,
    T6_vorticity,
    T7_shear_up,
    T8_shear_same,
    T9_shear_down,
    zero_nabla_operator,
)


__all__ = [
    "hierarchy_rhs_photon",
    "hierarchy_rhs_neutrino",
    "proper_shear_at_eta",
]


# ════════════════════════════════════════════════════════════════════
#   σ_ab : conformal → proper-time conversion
# ════════════════════════════════════════════════════════════════════

def proper_shear_at_eta(
    eta: float,
    tetrad_state: Optional["object"],
    a_at_eta: float,
) -> np.ndarray:
    """Return the **proper-time** shear ``σ_ab(η)`` as a ``(3, 3)`` tensor.

    ``TetradBackgroundState.sigma_tensor`` stores the **conformal** shear
    ``Σ_ab = e^α σ_ab = a σ_ab`` (Y-Block convention, §2 of
    ``tetrad_state`` module docstring). The LB-2 term functions
    (T7/T8/T9) require the proper-time ``σ_ab`` (audit F1); the driver
    applies the ``1 / a`` conversion here and nowhere else.

    If ``tetrad_state`` is ``None`` (FLRW diagnostic path), ``σ_ab ≡ 0``.

    Nearest-grid-point lookup is used (no spline) — consistent with
    ``TetradBackgroundState.shear_at``; LB-5 will upgrade to cubic
    splines at integrator setup time (spec §8).

    Parameters
    ----------
    eta : float
        Conformal time [Mpc].
    tetrad_state : TetradBackgroundState or None
        Y-Block tetrad background table. ``None`` → FLRW.
    a_at_eta : float
        Scale factor at ``eta`` — used for the conformal→proper
        conversion (``σ = Σ / a``).

    Reference: 02_multipole_hierarchy_spec.md §8;
    AUDIT_PHASE_LB2a_2026-04-19.md F1.
    """
    if tetrad_state is None:
        return np.zeros((3, 3), dtype=np.float64)
    idx = int(np.argmin(np.abs(tetrad_state.eta - eta)))
    sigma_conformal = tetrad_state.sigma_tensor[idx]
    if a_at_eta <= 0.0:
        raise ValueError(f"a(η) must be positive, got {a_at_eta}")
    return np.asarray(sigma_conformal, dtype=np.float64) / a_at_eta


# ════════════════════════════════════════════════════════════════════
#   Photon hierarchy RHS
# ════════════════════════════════════════════════════════════════════

def hierarchy_rhs_photon(
    eta: float,
    y_flat: np.ndarray,
    *,
    L_max: int,
    bg_table: "object",
    tetrad_state: Optional["object"],
    closure: ClosureStrategy,
    collision: CollisionOperator,
    collision_aux: Optional[object] = None,
    nabla_operator: Optional[Callable[..., np.ndarray]] = None,
    accel_vector: Optional[np.ndarray] = None,
    vorticity_vector: Optional[np.ndarray] = None,
) -> np.ndarray:
    """``dy/dη`` for the photon PSTF multipole tower at one η.

    Evaluates the nine-term hierarchy RHS at every ℓ ∈ ``0..L_max`` and
    returns the flat derivative vector in the same packing order as
    ``y_flat`` (see ``PSTFHierarchyState.as_flat``).

    Parameters
    ----------
    eta : float
        Conformal time [Mpc].
    y_flat : ndarray
        Packed state of length ``(L_max + 1)²``; concatenation of
        ``Π_ℓ`` packed components for ℓ = 0..L_max.
    L_max : int
        Highest multipole retained.
    bg_table : FLRWBackgroundTable
        Shared FLRW background table (supplies Θ(η), a(η)).
    tetrad_state : TetradBackgroundState or None
        Tetrad background supplying σ_ab(η). ``None`` ⇒ FLRW (σ = 0).
    closure : ClosureStrategy
        Strategy for ``Π_{L_max + 1}`` / ``Π_{L_max + 2}`` (enters T3
        and T7 at the top of the tower).
    collision : CollisionOperator
        Supplies ``K_{A_ℓ}`` for ℓ = 0..L_max. LB-2b default:
        ``ZeroCollisionOperator`` (Γ_T = 0). ``ThomsonCollisionOperator``
        arrives at LB-4.
    collision_aux : any, optional
        Forwarded to ``collision.evaluate`` (e.g. baryon velocity,
        E-mode polarisation, ``τ̇``).
    nabla_operator : callable, optional
        Spatial covariant-derivative hook for T2 and T3. Default:
        ``zero_nabla_operator`` (homogeneous background).
    accel_vector : (3,) ndarray, optional
        4-acceleration ``A_a`` for T4, T5. Default: zero (orthogonal).
    vorticity_vector : (3,) ndarray, optional
        Vorticity ``ω^a`` for T6. Default: zero (orthogonal).

    Returns
    -------
    dy : ndarray of the same shape as ``y_flat``
        ``dy/dη``. In conformal-η parameterisation
        ``Π'(η) = a(η) × (K_{A_ℓ} − Σ_n T_n)``.

    Reference: 02_multipole_hierarchy_spec.md §4, §9.2.
    """
    state = unpack_hierarchy(y_flat, L_max)
    a_val = float(bg_table.interp_a(eta))
    Theta = float(bg_table.interp_Theta(eta))

    sigma = proper_shear_at_eta(eta, tetrad_state, a_val)

    if accel_vector is None:
        accel_vector = np.zeros(3, dtype=np.float64)
    else:
        accel_vector = np.asarray(accel_vector, dtype=np.float64)
    if vorticity_vector is None:
        vorticity_vector = np.zeros(3, dtype=np.float64)
    else:
        vorticity_vector = np.asarray(vorticity_vector, dtype=np.float64)
    if nabla_operator is None:
        nabla_operator = zero_nabla_operator

    # Materialise the full-tensor form of every Π_ℓ in the tower.
    Pi_full = [pstf_to_tensor(t) for t in state.tensors]

    dy = np.empty_like(y_flat)
    offset = 0
    for ell in range(L_max + 1):
        size = 2 * ell + 1

        # Neighbours through the closure when the tower runs out.
        if ell - 1 >= 0:
            Pi_prev_full = Pi_full[ell - 1]
        else:
            Pi_prev_full = None
        if ell + 1 <= L_max:
            Pi_next_full = Pi_full[ell + 1]
        else:
            Pi_next_full = pstf_to_tensor(
                closure.get_closure(state, ell + 1)
            )
        if ell + 2 <= L_max:
            Pi_next_next_full = Pi_full[ell + 2]
        else:
            Pi_next_next_full = pstf_to_tensor(
                closure.get_closure(state, ell + 2)
            )
        if ell - 2 >= 0:
            Pi_prev_prev_full = Pi_full[ell - 2]
        else:
            Pi_prev_prev_full = None

        # Expansion (always active).
        T1 = T1_expansion(ell, Pi_full[ell], Theta)

        # Gradient-type couplings (zero at background unless nabla_operator
        # is supplied by the perturbation layer).
        if ell > 0:
            T2 = T2_gradient(ell, Pi_prev_full, nabla_operator)
        else:
            T2 = np.zeros((), dtype=np.float64)
        T3 = T3_divergence(ell, Pi_next_full, nabla_operator)

        # Acceleration / vorticity (orthogonal Bianchi: vectors are 0).
        T4 = T4_accel_divergence(ell, Pi_next_full, accel_vector)
        if ell > 0:
            T5 = T5_accel_gradient(ell, Pi_prev_full, accel_vector)
        else:
            T5 = np.zeros((), dtype=np.float64)
        if ell > 0:
            T6 = T6_vorticity(ell, Pi_full[ell], vorticity_vector)
        else:
            T6 = np.zeros((), dtype=np.float64)

        # Shear couplings (T7/T8/T9).
        T7 = T7_shear_up(ell, Pi_next_next_full, sigma)
        T8 = T8_shear_same(ell, Pi_full[ell], sigma)
        if ell >= 2:
            T9 = T9_shear_down(ell, Pi_prev_prev_full, sigma)
        elif ell == 1:
            T9 = np.zeros(3, dtype=np.float64)
        else:
            T9 = np.zeros((), dtype=np.float64)

        # Collision source K_{A_ℓ} (PSTF-packed → full).
        K_packed = collision.evaluate(ell, state, collision_aux)
        if K_packed.ell != ell:
            raise ValueError(
                f"CollisionOperator returned ell={K_packed.ell}, expected {ell}"
            )
        K_full = pstf_to_tensor(K_packed)

        # Π̇_{⟨A_ℓ⟩} = K − Σ_n T_n.
        sum_T = T1 + T2 + T3 + T4 + T5 + T6 + T7 + T8 + T9
        Pi_dot_full = K_full - sum_T

        # Overdot → η-prime: Π'(η) = a(η) × Π̇.
        dPi_deta_full = a_val * np.asarray(Pi_dot_full, dtype=np.float64)

        # Pack (PSTF-project along the way for numerical hygiene; the
        # sum is already PSTF by construction up to ε_mach, so pack
        # returns identical output as pack(sym_trace_free(...)).)
        components = pstf_pack(dPi_deta_full)
        dy[offset:offset + size] = components
        offset += size

    return dy


# ════════════════════════════════════════════════════════════════════
#   Neutrino hierarchy RHS (collisionless)
# ════════════════════════════════════════════════════════════════════

_ZERO_COLLISION = ZeroCollisionOperator()


def hierarchy_rhs_neutrino(
    eta: float,
    y_flat: np.ndarray,
    *,
    L_max: int,
    bg_table: "object",
    tetrad_state: Optional["object"],
    closure: ClosureStrategy,
    nabla_operator: Optional[Callable[..., np.ndarray]] = None,
    accel_vector: Optional[np.ndarray] = None,
    vorticity_vector: Optional[np.ndarray] = None,
) -> np.ndarray:
    """``dy/dη`` for the neutrino PSTF tower — collisionless transport.

    Thin convenience wrapper that fixes
    ``collision = ZeroCollisionOperator()`` and forwards to
    ``hierarchy_rhs_photon``. See that function for the full parameter
    list and unit conventions.

    Reference: 02_multipole_hierarchy_spec.md §1.2 (K_{A_ℓ} = 0 for
    collisionless neutrinos); Ma-Bertschinger 1995 §4.
    """
    return hierarchy_rhs_photon(
        eta,
        y_flat,
        L_max=L_max,
        bg_table=bg_table,
        tetrad_state=tetrad_state,
        closure=closure,
        collision=_ZERO_COLLISION,
        collision_aux=None,
        nabla_operator=nabla_operator,
        accel_vector=accel_vector,
        vorticity_vector=vorticity_vector,
    )


# Silence unused-import warning on ``sym_trace_free`` — re-exported as
# part of the RHS toolkit for callers building mock nabla operators.
_ = sym_trace_free
_ = PSTFHierarchyState