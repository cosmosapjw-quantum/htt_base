"""bass/collision/thomson_pstf.py (LB-4) — PSTF Thomson collision operator.

Implements the orthogonal (``v_e = 0``) Thomson collision source for
the photon brightness multipole tower and its companion E-mode tower.
The formulas are the canonical Ma-Bertschinger 1995 / Zaldarriaga-
Seljak 1997 collision coefficients in PSTF packing, with the tensor
generalisation applied slot-by-slot in the real-spherical-harmonic
basis (exact at rank 0/1, slot-diagonal at rank ≥ 2 since Thomson
scattering is isotropic in azimuth in the electron rest frame).

Two concrete ``CollisionOperator`` implementations are exposed:

- ``ThomsonPSTFCollisionOperator`` — per-ℓ ``K^T_ell`` for the
  temperature tower, consumed by ``hierarchy_rhs_photon``.
- ``EModeThomsonCollisionOperator`` — per-ℓ ``K^E_ell`` for the
  E-mode tower, pluggable into a parallel ``hierarchy_rhs_photon``
  call driving the E-mode state.

Both operators are pure: ``evaluate(ell, state, aux)`` never mutates
``state`` and returns a fresh ``PSTFTensor`` of the requested rank.

Scope restrictions (LB-4a, orthogonal Bianchi only)
---------------------------------------------------
- ``v_e`` (electron bulk velocity) is assumed zero at background.
  The full PSTF-moment-level Lorentz boost of ``K_{A_ℓ}`` into the
  ``n^a`` frame lives at LB-4b.
- Baryon velocity ``v_b`` is passed in as a rank-1 real-SH packed
  (3,) array supplied by the caller; LB-4 uses only its ``v_b − Π_1``
  difference at the dipole level and makes no assumption about how
  the caller tracks ``v_b`` over η.
- B-mode is tracked separately (LB-4c).

References
----------
- Ma-Bertschinger 1995 (astro-ph/9506072) eq (63–65).
- Zaldarriaga & Seljak 1997 (astro-ph/9609170) eq (7), (17).
- Portsmouth & Bertschinger 2004 (astro-ph/0412094) §3.
- Chandrasekhar 1960 *Radiative Transfer* Ch IX.
- Ellis, Maartens, MacCallum §5.5 — 1+3 decomposition of Thomson.
- Kolb-Turner §6.4 — Boltzmann moments with Thomson source.
- lowell §4, §9.2, §11.
- ``docs/lowell_bianchi/04_thomson_collision_spec.md``.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from bass.collision.polarization import (
    E_mode_collision_source,
    PolarizationHierarchyState,
)
from bass.hierarchy.pstf_tensor import (
    PSTFHierarchyState,
    PSTFTensor,
    zero_hierarchy,
    zero_pstf,
)


__all__ = [
    "ThomsonAux",
    "EModeThomsonAux",
    "ThomsonPSTFCollisionOperator",
    "EModeThomsonCollisionOperator",
    "THOMSON_ELL2_SELF_COEFF",
    "THOMSON_ELL2_POLARIZATION_COEFF",
]


GAMMA_T_NUMERICAL_FLOOR: float = 1.0e-7
"""Small negative τ̇ interpolation noise tolerated as zero.

The physical Thomson rate is non-negative. Some early-time interpolators can
undershoot by tiny amounts near the table edge; those values are numerical
noise rather than a sign change and are clipped to zero here.
"""


# ════════════════════════════════════════════════════════════════════
#   Thomson coefficients for the temperature collision source
# ════════════════════════════════════════════════════════════════════

THOMSON_ELL2_SELF_COEFF: float = -9.0 / 10.0
"""Self-damping coefficient of Π_2 in K^T_2: −(9/10)."""

THOMSON_ELL2_POLARIZATION_COEFF: float = -np.sqrt(6.0) / 10.0
"""Cross-coupling coefficient of E_2 in K^T_2: −√6/10."""


# ════════════════════════════════════════════════════════════════════
#   Auxiliary dataclasses (aux payload for the CollisionOperator protocol)
# ════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class ThomsonAux:
    """Payload for ``ThomsonPSTFCollisionOperator.evaluate``.

    Attributes
    ----------
    E_state : PolarizationHierarchyState
        Current E-mode tower. Required to evaluate the ℓ=2 cross-coupling
        term in ``K^T_2``.
    v_b_real_sph : (3,) ndarray
        Baryon 3-velocity in the real-spherical-harmonic packing
        (``Q_1 = I_3`` for rank 1, so this is just the ``(x, y, z)``
        vector). Supplied at every call; reduces the photon dipole
        toward ``v_b`` at rate ``Γ_T``.
    Gamma_T : float
        Conformal Thomson rate ``τ̇ = a n_e σ_T`` [Mpc⁻¹]. Must be
        non-negative finite. ``Gamma_T == 0`` returns zero everywhere.

    Reference: 04_thomson_collision_spec.md §9.2; Ma-Bertschinger 1995.
    """

    E_state: PolarizationHierarchyState
    v_b_real_sph: np.ndarray
    Gamma_T: float

    def __post_init__(self) -> None:
        if not isinstance(self.E_state, PolarizationHierarchyState):
            raise TypeError(
                f"E_state must be PolarizationHierarchyState, got "
                f"{type(self.E_state).__name__}"
            )
        v = np.asarray(self.v_b_real_sph, dtype=np.float64)
        if v.shape != (3,):
            raise ValueError(
                f"v_b_real_sph must have shape (3,), got {v.shape}"
            )
        object.__setattr__(self, "v_b_real_sph", v)
        gamma = float(self.Gamma_T)
        if gamma < 0.0 and gamma > -GAMMA_T_NUMERICAL_FLOOR:
            gamma = 0.0
        object.__setattr__(self, "Gamma_T", gamma)
        if not np.isfinite(self.Gamma_T) or self.Gamma_T < 0.0:
            raise ValueError(
                f"Gamma_T must be non-negative finite, got {self.Gamma_T}"
            )


@dataclass(frozen=True)
class EModeThomsonAux:
    """Payload for ``EModeThomsonCollisionOperator.evaluate``.

    Attributes
    ----------
    Pi_2_packed : (5,) ndarray
        Packed ``Π_2`` components of the temperature quadrupole
        supplying the ℓ=2 cross-coupling in ``K^E_2``.
    Gamma_T : float
        Conformal Thomson rate ``τ̇`` [Mpc⁻¹]; same value as in the
        temperature-side aux.

    Reference: 04_thomson_collision_spec.md §5.
    """

    Pi_2_packed: np.ndarray
    Gamma_T: float

    def __post_init__(self) -> None:
        pi2 = np.asarray(self.Pi_2_packed, dtype=np.float64)
        if pi2.shape != (5,):
            raise ValueError(
                f"Pi_2_packed must have shape (5,), got {pi2.shape}"
            )
        object.__setattr__(self, "Pi_2_packed", pi2)
        gamma = float(self.Gamma_T)
        if gamma < 0.0 and gamma > -GAMMA_T_NUMERICAL_FLOOR:
            gamma = 0.0
        object.__setattr__(self, "Gamma_T", gamma)
        if not np.isfinite(self.Gamma_T) or self.Gamma_T < 0.0:
            raise ValueError(
                f"Gamma_T must be non-negative finite, got {self.Gamma_T}"
            )


# ════════════════════════════════════════════════════════════════════
#   Temperature-side Thomson collision operator
# ════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class ThomsonPSTFCollisionOperator:
    """PSTF Thomson collision source for the temperature tower.

    Per-ℓ formulas (orthogonal, ``v_e = 0``):

    ======  ==============================================================
    ℓ       ``K^T_ℓ``
    ======  ==============================================================
    0       ``0``                                           (photon number
                                                             conserved)
    1       ``Γ_T (v_b − Π_1)``                             (Compton drag)
    2       ``−Γ_T (9/10) Π_2 − Γ_T (√6/10) E_2``           (polter
                                                             coupling)
    ≥3      ``−Γ_T Π_ℓ``                                    (Thomson
                                                             damping)
    ======  ==============================================================

    Implements the LB-2a ``CollisionOperator`` Protocol via
    ``evaluate(ell, state, aux)`` where ``aux`` is a ``ThomsonAux``.
    Also provides ``evaluate_tower`` for the full ``K^T`` tower in
    one call (direct-algebra tests / diagnostics).

    The operator is **stateless** (frozen dataclass with no fields)
    and therefore trivially thread-safe. All coefficients are the
    universal Ma-Bertschinger / Zaldarriaga-Seljak values (spec §2);
    the only runtime data is carried in the ``aux`` payload.

    References
    ----------
    - Ma-Bertschinger 1995 eq (63); Zaldarriaga-Seljak 1997 eq (7);
      Ellis §5.5; lowell §9.2.
    - Spec §2, §4, §10.
    """

    def evaluate(
        self,
        ell: int,
        state: PSTFHierarchyState,
        aux: Optional[object] = None,
    ) -> PSTFTensor:
        """Return ``K^T_ell`` as a fresh rank-``ell`` PSTFTensor.

        ``aux`` must be a ``ThomsonAux``; ``None`` is rejected because
        the operator has no way to supply ``Γ_T``, ``v_b``, or ``E_2``
        from the temperature state alone.

        Raises ``TypeError`` on an aux of the wrong type and
        ``ValueError`` on out-of-range ℓ or mismatched shapes.

        Reference: spec §4.
        """
        if ell < 0:
            raise ValueError(f"ell must be non-negative, got {ell}")
        if ell > state.L:
            raise ValueError(
                f"ell={ell} exceeds temperature tower L={state.L}"
            )
        if aux is None:
            raise TypeError(
                "ThomsonPSTFCollisionOperator.evaluate requires a "
                "ThomsonAux; None received."
            )
        if not isinstance(aux, ThomsonAux):
            raise TypeError(
                f"aux must be ThomsonAux, got {type(aux).__name__}"
            )

        return _compute_K_T_at_ell(
            ell=ell,
            Pi=state.tensors[ell],
            E_state=aux.E_state,
            v_b_real_sph=aux.v_b_real_sph,
            Gamma_T=aux.Gamma_T,
        )

    def evaluate_tower(
        self,
        state: PSTFHierarchyState,
        E_state: PolarizationHierarchyState,
        v_b_real_sph: np.ndarray,
        Gamma_T: float,
    ) -> PSTFHierarchyState:
        """Return the full ``K^T`` tower ``{K_0, K_1, …, K_{L_max}}``.

        Produced one call per ℓ through ``_compute_K_T_at_ell``; the
        tower layout matches ``state`` (same ``L``).

        Reference: spec §9.2.
        """
        aux = ThomsonAux(
            E_state=E_state,
            v_b_real_sph=np.asarray(v_b_real_sph, dtype=np.float64),
            Gamma_T=float(Gamma_T),
        )
        tensors = [
            _compute_K_T_at_ell(
                ell=ell,
                Pi=state.tensors[ell],
                E_state=aux.E_state,
                v_b_real_sph=aux.v_b_real_sph,
                Gamma_T=aux.Gamma_T,
            )
            for ell in range(state.L + 1)
        ]
        return PSTFHierarchyState(L=state.L, tensors=tensors)


# ════════════════════════════════════════════════════════════════════
#   E-mode Thomson collision operator
# ════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class EModeThomsonCollisionOperator:
    """PSTF Thomson collision source for the E-mode tower.

    Per-ℓ formulas:

    ======  ==============================================================
    ℓ       ``K^E_ℓ``
    ======  ==============================================================
    0       ``0``                                           (no E₀)
    1       ``0``                                           (no E₁)
    2       ``−Γ_T (2/5) E_2 − Γ_T (3/(5√6)) Π_2``          (polter)
    ≥3      ``−Γ_T E_ℓ``                                    (damping)
    ======  ==============================================================

    Implements the LB-2a ``CollisionOperator`` Protocol. The ``state``
    parameter passed to ``evaluate`` is the E-mode hierarchy state
    (the underlying ``PolarizationHierarchyState.E`` — see
    ``hierarchy_rhs_E_mode`` for the plumbing). ``aux`` is an
    ``EModeThomsonAux`` carrying the temperature quadrupole and
    ``Γ_T``.

    Reference: spec §5, §9.2.
    """

    def evaluate(
        self,
        ell: int,
        state: PSTFHierarchyState,
        aux: Optional[object] = None,
    ) -> PSTFTensor:
        """Return ``K^E_ell`` as a fresh rank-``ell`` PSTFTensor.

        ``state`` is the E-mode hierarchy state (caller packs /
        unpacks through ``PolarizationHierarchyState.E``).

        Reference: spec §5.
        """
        if ell < 0:
            raise ValueError(f"ell must be non-negative, got {ell}")
        if ell > state.L:
            raise ValueError(
                f"ell={ell} exceeds E-mode tower L={state.L}"
            )
        if aux is None:
            raise TypeError(
                "EModeThomsonCollisionOperator.evaluate requires an "
                "EModeThomsonAux; None received."
            )
        if not isinstance(aux, EModeThomsonAux):
            raise TypeError(
                f"aux must be EModeThomsonAux, got {type(aux).__name__}"
            )

        # Reuse the shared E-mode source routine; the PolarizationHierarchyState
        # wrapper is just a thin cover around ``state`` for type parity.
        wrapper = PolarizationHierarchyState(E=state)
        pi2 = aux.Pi_2_packed if ell == 2 else None
        return E_mode_collision_source(
            ell=ell,
            E_state=wrapper,
            Pi_2_packed=pi2,
            Gamma_T=aux.Gamma_T,
        )

    def evaluate_tower(
        self,
        E_state: PolarizationHierarchyState,
        Pi_2_packed: np.ndarray,
        Gamma_T: float,
    ) -> PolarizationHierarchyState:
        """Return the full ``K^E`` tower as a ``PolarizationHierarchyState``.

        Reference: spec §9.2.
        """
        tensors = [
            E_mode_collision_source(
                ell=ell,
                E_state=E_state,
                Pi_2_packed=(Pi_2_packed if ell == 2 else None),
                Gamma_T=float(Gamma_T),
            )
            for ell in range(E_state.L + 1)
        ]
        return PolarizationHierarchyState(
            E=PSTFHierarchyState(L=E_state.L, tensors=tensors),
        )


# ════════════════════════════════════════════════════════════════════
#   Internal: per-ℓ temperature Thomson source
# ════════════════════════════════════════════════════════════════════

def _compute_K_T_at_ell(
    *,
    ell: int,
    Pi: PSTFTensor,
    E_state: PolarizationHierarchyState,
    v_b_real_sph: np.ndarray,
    Gamma_T: float,
) -> PSTFTensor:
    """Compute ``K^T_ell`` from the decomposed inputs.

    Keeps the Thomson coefficients in one place so both the protocol
    ``evaluate`` and the full-tower ``evaluate_tower`` route through
    the same arithmetic (no drift between per-ℓ and full-tower
    semantics).

    Reference: spec §4.
    """
    if Pi.ell != ell:
        raise ValueError(
            f"Pi.ell={Pi.ell} != requested ell={ell}"
        )

    if ell == 0:
        # Monopole conserved: photon number is Thomson-invariant.
        return zero_pstf(0)

    if ell == 1:
        # Compton drag: K_1 = Γ_T (v_b − Π_1).
        components = Gamma_T * (v_b_real_sph - Pi.components)
        return PSTFTensor(ell=1, components=components)

    if ell == 2:
        # Polter coupling: K_2 = -(9/10) Γ_T Π_2 - (√6/10) Γ_T E_2.
        E_2_packed = E_state.tensors[2].components
        components = Gamma_T * (
            THOMSON_ELL2_SELF_COEFF * Pi.components
            + THOMSON_ELL2_POLARIZATION_COEFF * E_2_packed
        )
        return PSTFTensor(ell=2, components=components)

    # ell >= 3: Thomson damping.
    return PSTFTensor(
        ell=ell,
        components=-Gamma_T * Pi.components,
    )


# Silence unused-import warnings on symbols kept in the public API.
_ = zero_hierarchy
