"""bass/hierarchy/hierarchy_rhs.py (LB-2b + FB-2.4) — PSTF multipole RHS driver.

Sums ``T1 + T2 + T3 + T4 + T5 + T6 + T7 + T8 + T9 − K`` at every ℓ of
a PSTF multipole tower and returns ``dy/dη`` in the packed state
layout consumed by ``scipy.integrate.solve_ivp``. Two entry points are
provided:

- ``hierarchy_rhs_photon`` — photon brightness tower. A pluggable
  ``CollisionOperator`` (``ThomsonCollisionOperator`` at LB-4; the
  LB-2b default is ``ZeroCollisionOperator``) supplies ``K_{A_ℓ}``.
- ``hierarchy_rhs_neutrino`` — convenience wrapper that hard-wires
  ``ZeroCollisionOperator`` for collisionless neutrinos.

FB-2.4 — driver-level ``aniso_ricci_tensor`` routing
----------------------------------------------------
The driver now interpolates ``tetrad_state.aniso_3_curvature`` (a
``(N, 3, 3)`` anisotropic 3-Ricci history supplied by
``build_tetrad_state``; see ``bass/background/tetrad_state.py``
``FB-1.4``) to the evaluation epoch and forwards the ``(3, 3)`` slice
to ``T1_expansion`` / ``T2_gradient`` as the optional
``aniso_ricci_tensor`` kwarg introduced by FB-2.2. The default path
(``tetrad_state is None`` **or** ``aniso_3_curvature is None``) passes
``None``, preserving the LB-6 / FB-2.3 bit-identical regression for
FLRW and Class-A-unimodular configurations whose curvature status is
``type_i_flat`` / ``type_v_isotropic`` (anisotropic part exactly zero)
or explicitly unavailable. For the eight anisotropic Bianchi types
where ``³R_ab^{aniso} ≠ 0`` (II, VI_0, VIII, III, IV, VI_h, VII_h, and
the non-symmetric VII_0 branch) the T1 rank-ℓ curved-space correction
``(ℓ/(2ℓ+3)) ³R^b_{⟨a_ℓ} Π_{A_{ℓ−1}⟩ b}`` auto-activates; T2's
``∇̃ ³R_ab`` structural hook stays identically zero at the background
(left-invariant tetrad frame) awaiting the FB-5.1 harmonic-mode
wire-up.

Ellis-Maartens-MacCallum 2012 §16 distinguishes the nine-term
kinematic hierarchy from the curved-space corrections; FB-2.4 closes
the driver contract by making the curved-space correction a
*property of the tetrad state* rather than a caller responsibility.

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

from dataclasses import dataclass
from typing import Callable, Optional

import numpy as np

from bass.hierarchy.closure_interface import ClosureStrategy
from bass.hierarchy.collision_interface import (
    CollisionOperator,
    ZeroCollisionOperator,
)
from bass.hierarchy.contractions import pstf_pack, sym_trace_free
from bass.hierarchy.packed_operators import (
    apply_T1_expansion_packed,
    apply_T4_accel_divergence_packed,
    apply_T5_accel_gradient_packed,
    apply_T6_vorticity_packed,
    apply_T7_shear_up_packed,
    apply_T8_shear_same_packed,
    apply_T9_shear_down_packed,
)
from bass.hierarchy.pstf_tensor import (
    PSTFHierarchyState,
    pstf_to_tensor,
    unpack_hierarchy,
)
from bass.hierarchy.terms import (
    T2_gradient,
    T3_divergence,
    zero_nabla_operator,
)
from bass.species.base import SpeciesBackground
from bass.species.massive_neutrino import MassiveNeutrinoBackground


__all__ = [
    "hierarchy_rhs_photon",
    "hierarchy_rhs_neutrino",
    "proper_shear_at_eta",
    "aniso_ricci_at_eta",
]


@dataclass(frozen=True)
class HierarchyBackgroundSample:
    eta: float
    a_val: float
    Theta: float
    sigma: np.ndarray
    aniso_ricci: np.ndarray | None
    has_sigma: bool
    has_ricci: bool
    sigma_coeffs: np.ndarray | None
    ricci_coeffs: np.ndarray | None


_ZERO_VECTOR3 = np.zeros(3, dtype=np.float64)


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

    **Cubic-spline interpolation in η** (component-wise) — LB-2b F2
    post-audit repair. Prior behaviour used nearest-grid-point lookup
    with ~2 % quantisation error at mid-grid evaluations. A per-
    component scipy ``CubicSpline`` is lazily attached to the tetrad
    state on first call; subsequent calls within the same integrator
    run reuse the cached splines so the cost is O(log N) per query
    rather than O(N). Queries outside ``[eta[0], eta[-1]]`` fall back
    to endpoint clamping (matches the prior nearest-neighbour extremal
    behaviour).

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
    AUDIT_PHASE_LB2a_2026-04-19.md F1;
    AUDIT_PHASE_LB2b_2026-04-19.md F2 (spline upgrade).
    """
    if tetrad_state is None:
        return np.zeros((3, 3), dtype=np.float64)
    if a_at_eta <= 0.0:
        raise ValueError(f"a(η) must be positive, got {a_at_eta}")
    eta_grid = tetrad_state.eta
    # Endpoint clamping: outside the grid, spline extrapolation is
    # unreliable for a driver that should not be asked to evaluate there.
    # Clamp to grid endpoints (matches prior nearest-neighbour behaviour).
    eta_query = float(np.clip(eta, float(eta_grid[0]), float(eta_grid[-1])))
    sigma_spline = _get_or_build_sigma_spline(tetrad_state)
    sigma_conformal = sigma_spline(eta_query)
    return np.asarray(sigma_conformal, dtype=np.float64) / a_at_eta


def _get_or_build_sigma_spline(tetrad_state):
    """Return a component-wise cubic spline ``η → σ_ab^{conformal}``
    attached to ``tetrad_state``. Cached in ``_sigma_spline_cache``
    attribute (bypasses the frozen dataclass via ``object.__setattr__``).

    Rebuilds on first call; reused on subsequent calls for the same
    ``tetrad_state`` instance (O(log N) per query after build). Uses
    ``scipy.interpolate.CubicSpline`` with ``natural`` BC — consistent
    with the bg_table spline convention at the species layer.
    """
    cached = getattr(tetrad_state, "_sigma_spline_cache", None)
    if cached is not None:
        return cached
    from scipy.interpolate import CubicSpline
    eta_grid = np.asarray(tetrad_state.eta, dtype=np.float64)
    sigma_grid = np.asarray(tetrad_state.sigma_tensor, dtype=np.float64)
    # sigma_grid has shape (N, 3, 3); CubicSpline treats axis=0 as the
    # independent variable and vectorises over the remaining axes.
    spline = CubicSpline(eta_grid, sigma_grid, axis=0, bc_type="natural")
    try:
        object.__setattr__(tetrad_state, "_sigma_spline_cache", spline)
    except Exception:
        # tetrad_state is not a frozen dataclass — fall back to plain
        # attribute assignment. Either path exposes the cache.
        tetrad_state._sigma_spline_cache = spline  # type: ignore[attr-defined]
    return spline


# ════════════════════════════════════════════════════════════════════
#   FB-2.4: aniso_3_curvature (η) → (3, 3) interpolator
# ════════════════════════════════════════════════════════════════════

def aniso_ricci_at_eta(
    eta: float,
    tetrad_state: Optional["object"],
) -> Optional[np.ndarray]:
    """Return the anisotropic 3-Ricci ``³R_ab^{aniso}(η)`` as ``(3, 3)``
    or ``None`` when no curved-space correction applies.

    FB-2.4 driver contract: forwards ``tetrad_state.aniso_3_curvature``
    (shape ``(N, 3, 3)`` built by ``build_tetrad_state``; see
    ``FB-1.4`` in ``bass/background/tetrad_state.py``) to
    ``T1_expansion`` / ``T2_gradient`` via their ``aniso_ricci_tensor``
    kwarg (FB-2.2). Returns ``None`` whenever either
    (i) ``tetrad_state is None`` (FLRW diagnostic path), or
    (ii) ``tetrad_state.aniso_3_curvature is None`` (unsupported label),
    so that the LB-6 / FB-2.3 bit-identical regression is preserved
    automatically for every configuration that does not carry a
    non-trivial anisotropic spatial curvature.

    At the background level the spatial 3-Ricci is *time-independent*
    in the left-invariant orthonormal tetrad (Ellis-MacCallum 1969 §4),
    so interpolation is a formality. Building a cubic spline at every
    driver call would cost O(N) per integrator step and dominate the
    RHS time for a homogeneous quantity; we therefore cache one spline
    on the tetrad state (mirroring ``_get_or_build_sigma_spline``) and
    reuse it for every subsequent query within the same integrator run.

    Parameters
    ----------
    eta : float
        Conformal time [Mpc].
    tetrad_state : TetradBackgroundState or None
        FB-1.4 tetrad history. ``None`` → ``None`` (FLRW path). When
        non-None but ``aniso_3_curvature is None`` (unavailable label),
        also returns ``None``.

    Returns
    -------
    R_aniso : ndarray of shape (3, 3) or None
        Anisotropic spatial Ricci at ``η`` in the orthonormal tetrad
        basis, units ``[length]⁻²``. Symmetric trace-free.

    Reference: Ellis-MacCallum 1969 §4 (Bianchi ³R_ab); Ellis-Maartens-
    MacCallum 2012 §14.3 (³R coupling into the hierarchy); FB-1.4
    (non-None for all 11 Bianchi types + FLRW).
    """
    if tetrad_state is None:
        return None
    ricci_grid = getattr(tetrad_state, "aniso_3_curvature", None)
    if ricci_grid is None:
        return None
    ricci_arr = np.asarray(ricci_grid, dtype=np.float64)
    if ricci_arr.shape == (3, 3):
        return ricci_arr
    eta_grid = tetrad_state.eta
    eta_query = float(np.clip(eta, float(eta_grid[0]), float(eta_grid[-1])))
    spline = _get_or_build_aniso_ricci_spline(tetrad_state)
    return np.asarray(spline(eta_query), dtype=np.float64)


def _get_or_build_aniso_ricci_spline(tetrad_state):
    """Return a component-wise cubic spline ``η → ³R_ab^{aniso}``
    attached to ``tetrad_state`` (cached on first call).

    Mirrors ``_get_or_build_sigma_spline``. Uses ``bc_type='natural'``
    for consistency with the shear spline. O(log N) per query after
    the first O(N) build.
    """
    cached = getattr(tetrad_state, "_aniso_ricci_spline_cache", None)
    if cached is not None:
        return cached
    from scipy.interpolate import CubicSpline
    eta_grid = np.asarray(tetrad_state.eta, dtype=np.float64)
    ricci_grid = np.asarray(
        tetrad_state.aniso_3_curvature, dtype=np.float64
    )
    spline = CubicSpline(eta_grid, ricci_grid, axis=0, bc_type="natural")
    try:
        object.__setattr__(
            tetrad_state, "_aniso_ricci_spline_cache", spline
        )
    except Exception:
        tetrad_state._aniso_ricci_spline_cache = spline  # type: ignore[attr-defined]
    return spline


def sample_hierarchy_background(
    eta: float,
    *,
    bg_table: "object",
    tetrad_state: Optional["object"],
) -> HierarchyBackgroundSample:
    """Sample all background quantities needed by the hierarchy at one ``η``.

    This keeps the interpolation boundary explicit, matching VER3's
    proper-time background / conformal-time hierarchy split, while
    allowing callers that already share an ``η`` to reuse one sampled
    snapshot across multiple T/E/ν RHS evaluations.
    """
    a_val = float(bg_table.interp_a(eta))
    Theta = float(bg_table.interp_Theta(eta))
    sigma = proper_shear_at_eta(eta, tetrad_state, a_val)
    aniso_ricci = aniso_ricci_at_eta(eta, tetrad_state)
    has_sigma = bool(np.any(sigma))
    has_ricci = aniso_ricci is not None and bool(np.any(aniso_ricci))
    sigma_coeffs = (
        np.asarray(pstf_pack(np.asarray(sigma, dtype=np.float64)), dtype=np.float64)
        if has_sigma
        else None
    )
    ricci_coeffs = (
        np.asarray(pstf_pack(np.asarray(aniso_ricci, dtype=np.float64)), dtype=np.float64)
        if has_ricci
        else None
    )
    return HierarchyBackgroundSample(
        eta=float(eta),
        a_val=a_val,
        Theta=Theta,
        sigma=np.asarray(sigma, dtype=np.float64),
        aniso_ricci=None if aniso_ricci is None else np.asarray(aniso_ricci, dtype=np.float64),
        has_sigma=has_sigma,
        has_ricci=has_ricci,
        sigma_coeffs=sigma_coeffs,
        ricci_coeffs=ricci_coeffs,
    )


# ════════════════════════════════════════════════════════════════════
#   Photon hierarchy RHS
# ════════════════════════════════════════════════════════════════════

def hierarchy_rhs_photon_from_state(
    state: PSTFHierarchyState,
    *,
    background: HierarchyBackgroundSample,
    closure: ClosureStrategy,
    collision: CollisionOperator,
    collision_aux: Optional[object] = None,
    nabla_operator: Optional[Callable[..., np.ndarray]] = None,
    accel_vector: Optional[np.ndarray] = None,
    vorticity_vector: Optional[np.ndarray] = None,
) -> np.ndarray:
    """Internal array-first photon RHS helper.

    This preserves the public packed storage contract while allowing
    callers that already hold an unpacked ``PSTFHierarchyState`` to
    avoid a second pack/unpack cycle on the hot path.
    """
    L_max = state.L
    target_dtype = np.result_type(
        np.float64,
        *[np.asarray(t.components).dtype for t in state.tensors],
    )
    if accel_vector is None:
        accel_vector = _ZERO_VECTOR3
        has_accel = False
    else:
        accel_vector = np.asarray(accel_vector, dtype=np.float64)
        has_accel = bool(np.any(accel_vector))
    if vorticity_vector is None:
        vorticity_vector = _ZERO_VECTOR3
        has_vorticity = False
    else:
        vorticity_vector = np.asarray(vorticity_vector, dtype=np.float64)
        has_vorticity = bool(np.any(vorticity_vector))
    if nabla_operator is None:
        nabla_operator = zero_nabla_operator

    needs_full_gradient_terms = nabla_operator is not zero_nabla_operator
    state_full_cache: list[np.ndarray | None] | None = [None] * (L_max + 1) if needs_full_gradient_terms else None
    closure_packed_cache: dict[int, np.ndarray] = {}
    closure_full_cache: dict[int, np.ndarray] | None = {} if needs_full_gradient_terms else None

    def _state_full(ell: int) -> np.ndarray:
        assert state_full_cache is not None
        cached = state_full_cache[ell]
        if cached is None:
            cached = pstf_to_tensor(state.tensors[ell])
            state_full_cache[ell] = cached
        return cached

    def _closure_packed(ell: int) -> np.ndarray:
        cached = closure_packed_cache.get(ell)
        if cached is None:
            cached = np.asarray(
                closure.get_closure(state, ell).components,
                dtype=target_dtype,
            )
            closure_packed_cache[ell] = cached
        return cached

    def _closure_full(ell: int) -> np.ndarray:
        assert closure_full_cache is not None
        cached = closure_full_cache.get(ell)
        if cached is None:
            cached = pstf_to_tensor(closure.get_closure(state, ell))
            closure_full_cache[ell] = cached
        return cached

    has_sigma = background.has_sigma
    zero_collision = isinstance(collision, ZeroCollisionOperator)
    sigma_coeffs = background.sigma_coeffs
    ricci_coeffs = background.ricci_coeffs
    a_val = float(background.a_val)
    theta = float(background.Theta)
    component_blocks = [
        np.asarray(t.components, dtype=target_dtype)
        for t in state.tensors
    ]

    packed_blocks: list[np.ndarray] = []
    for ell in range(L_max + 1):
        size = 2 * ell + 1
        Pi_components = component_blocks[ell]

        if ell - 1 >= 0:
            Pi_prev_components = component_blocks[ell - 1]
        else:
            Pi_prev_components = None
        if ell + 1 <= L_max:
            Pi_next_components = component_blocks[ell + 1]
        else:
            Pi_next_components = _closure_packed(ell + 1)
        if ell + 2 <= L_max:
            Pi_next_next_components = component_blocks[ell + 2]
        else:
            Pi_next_next_components = _closure_packed(ell + 2)
        if ell - 2 >= 0:
            Pi_prev_prev_components = component_blocks[ell - 2]
        else:
            Pi_prev_prev_components = None

        sum_T = apply_T1_expansion_packed(
            ell,
            Pi_components,
            theta,
            aniso_ricci_tensor=ricci_coeffs,
        )

        if needs_full_gradient_terms:
            if ell > 0:
                sum_T += np.asarray(
                    pstf_pack(
                        T2_gradient(
                            ell,
                            _state_full(ell - 1),
                            nabla_operator,
                            aniso_ricci_tensor=background.aniso_ricci,
                        )
                    ),
                    dtype=target_dtype,
                )
            sum_T += np.asarray(
                pstf_pack(
                    T3_divergence(
                        ell,
                        _state_full(ell + 1) if ell + 1 <= L_max else _closure_full(ell + 1),
                        nabla_operator,
                    )
                ),
                dtype=target_dtype,
            )

        if has_accel:
            sum_T += apply_T4_accel_divergence_packed(ell, Pi_next_components, accel_vector)
            if ell > 0:
                sum_T += apply_T5_accel_gradient_packed(ell, Pi_prev_components, accel_vector)
        if ell > 0 and has_vorticity:
            sum_T += apply_T6_vorticity_packed(ell, Pi_components, vorticity_vector)

        if has_sigma:
            sum_T += apply_T7_shear_up_packed(ell, Pi_next_next_components, sigma_coeffs)
            sum_T += apply_T8_shear_same_packed(ell, Pi_components, sigma_coeffs)
            if ell >= 2:
                sum_T += apply_T9_shear_down_packed(ell, Pi_prev_prev_components, sigma_coeffs)
        if zero_collision:
            components = np.asarray(
                -a_val * sum_T,
                dtype=target_dtype,
            )
        else:
            K_packed = collision.evaluate(ell, state, collision_aux)
            if K_packed.ell != ell:
                raise ValueError(
                    f"CollisionOperator returned ell={K_packed.ell}, expected {ell}"
                )
            components = np.asarray(
                a_val * (np.asarray(K_packed.components) - sum_T),
                dtype=np.result_type(target_dtype, K_packed.components.dtype, sum_T.dtype),
            )
        if components.shape != (size,):
            raise RuntimeError(
                f"packed derivative returned shape {components.shape} for ell={ell}, "
                f"expected {(size,)}"
            )
        packed_blocks.append(components)

    return np.concatenate(packed_blocks) if packed_blocks else np.zeros(
        0, dtype=target_dtype
    )


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
    background = sample_hierarchy_background(
        eta,
        bg_table=bg_table,
        tetrad_state=tetrad_state,
    )
    return hierarchy_rhs_photon_from_state(
        state,
        background=background,
        closure=closure,
        collision=collision,
        collision_aux=collision_aux,
        nabla_operator=nabla_operator,
        accel_vector=accel_vector,
        vorticity_vector=vorticity_vector,
    )


# ════════════════════════════════════════════════════════════════════
#   Neutrino hierarchy RHS (collisionless)
# ════════════════════════════════════════════════════════════════════

_ZERO_COLLISION = ZeroCollisionOperator()


def hierarchy_rhs_neutrino_from_state(
    state: PSTFHierarchyState,
    *,
    background: HierarchyBackgroundSample,
    closure: ClosureStrategy,
    neutrino_background: Optional[SpeciesBackground] = None,
    nabla_operator: Optional[Callable[..., np.ndarray]] = None,
    accel_vector: Optional[np.ndarray] = None,
    vorticity_vector: Optional[np.ndarray] = None,
) -> np.ndarray:
    effective_nabla = nabla_operator
    if (
        isinstance(neutrino_background, MassiveNeutrinoBackground)
        and neutrino_background.mass_eV > 0.0
    ):
        base_nabla = nabla_operator or zero_nabla_operator
        modifier = float(neutrino_background.free_streaming_modifier(background.eta))

        def scaled_nabla(
            tensor: np.ndarray, kind: str = "gradient",
        ) -> np.ndarray:
            return modifier * np.asarray(base_nabla(tensor, kind=kind))

        effective_nabla = scaled_nabla

    return hierarchy_rhs_photon_from_state(
        state,
        background=background,
        closure=closure,
        collision=_ZERO_COLLISION,
        collision_aux=None,
        nabla_operator=effective_nabla,
        accel_vector=accel_vector,
        vorticity_vector=vorticity_vector,
    )


def hierarchy_rhs_neutrino(
    eta: float,
    y_flat: np.ndarray,
    *,
    L_max: int,
    bg_table: "object",
    tetrad_state: Optional["object"],
    closure: ClosureStrategy,
    neutrino_background: Optional[SpeciesBackground] = None,
    nabla_operator: Optional[Callable[..., np.ndarray]] = None,
    accel_vector: Optional[np.ndarray] = None,
    vorticity_vector: Optional[np.ndarray] = None,
) -> np.ndarray:
    """``dy/dη`` for the neutrino PSTF tower — collisionless transport.

    Thin convenience wrapper that fixes
    ``collision = ZeroCollisionOperator()`` and forwards to
    ``hierarchy_rhs_photon``. See that function for the full parameter
    list and unit conventions.

    FB-9 extends the wrapper with an optional ``neutrino_background``
    hook. When that object is a ``MassiveNeutrinoBackground`` with
    positive mass, the free-streaming gradient/divergence operator is
    multiplied by the energy-weighted Ma-Bertschinger ``q / epsilon``
    factor exposed by
    ``MassiveNeutrinoBackground.free_streaming_modifier(eta)``. The
    byte-identical LB-1 / FB-2.4 path is preserved whenever
    ``neutrino_background is None`` or when the caller passes the
    original massless ``NeutrinoBackground`` from the default registry.

    Reference: 02_multipole_hierarchy_spec.md §1.2 (K_{A_ℓ} = 0 for
    collisionless neutrinos); Ma-Bertschinger 1995 §4.
    """
    state = unpack_hierarchy(y_flat, L_max)
    background = sample_hierarchy_background(
        eta,
        bg_table=bg_table,
        tetrad_state=tetrad_state,
    )
    return hierarchy_rhs_neutrino_from_state(
        state,
        background=background,
        closure=closure,
        neutrino_background=neutrino_background,
        nabla_operator=nabla_operator,
        accel_vector=accel_vector,
        vorticity_vector=vorticity_vector,
    )


# Silence unused-import warning on ``sym_trace_free`` — re-exported as
# part of the RHS toolkit for callers building mock nabla operators.
_ = sym_trace_free
_ = PSTFHierarchyState
