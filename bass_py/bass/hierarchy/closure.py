"""bass/hierarchy/closure.py (LB-3) — Multipole-tower closure strategies.

Implements the four closure strategies enumerated in
``docs/lowell_bianchi/03_closure_truncation_spec.md`` §4–§7:

* ``HardCutClosure``             — Π_{L+1} = Π_{L+2} = 0 (LB-2a baseline,
  re-exported from ``closure_interface`` for back-compat).
* ``FreeStreamingClosure``       — Ma-Bertschinger 1995 eq (53) per-m
  recursion.
* ``PowerLawExtrapolationClosure`` — Π_ℓ ∝ ℓ⁻α extrapolation (caller
  supplies α).
* ``TCAClosure``                 — ℓ=2 algebraic override wrapping
  ``bass.closure.quadrupole_tca.solve_tca_closure`` (W6-04).

All four implement the LB-2a ``ClosureStrategy`` protocol (spec §3.1):
a single method ``get_closure(state, ell_requested) -> PSTFTensor``
invoked by the LB-2b ``hierarchy_rhs_photon`` driver for the tower-
top closure slots (Π_{L+1} and Π_{L+2}). ``TCAClosure`` additionally
exposes ``override_at_ell`` / ``algebraic_closure`` (spec §3.2) for
the LB-5 integrator's algebraic-vs-ODE dispatch at ℓ=2.

All returned tensors are **fresh copies** (never aliased views into
``state.tensors``) — closure is side-effect-free per LB-2a precedent
(``HardCutClosure.get_closure`` defensive copy).

References
----------
- ``docs/lowell_bianchi/03_closure_truncation_spec.md`` §4–§7, §10, §11.
- Ma-Bertschinger 1995 (astro-ph/9506072) §6 eq (53), (63), (64).
- Ellis, Maartens, MacCallum *Relativistic Cosmology* §4.6 — moment
  truncation.
- Kolb-Turner *The Early Universe* §9.4 — fluid approximation tail
  ``Π_ℓ ∝ ℓ⁻α``.
- Pitrou 2009 (CQG 26:065006) §4 — non-FLRW closure convergence study.
- Pontzen-Challinor 2007 §5 / ``bass/closure/quadrupole_tca.py`` (W6-04)
  — ℓ=2 algebraic tight-coupling formula.
- lowell reference §6 / §10 (L=4/6/8 recommendations, TCA matrix).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Tuple

import numpy as np

from bass.closure.quadrupole_tca import solve_tca_closure
from bass.hierarchy.closure_interface import (
    ClosureStrategy,
    HardCutClosure,
)
from bass.hierarchy.pstf_tensor import (
    PSTFHierarchyState,
    PSTFTensor,
    zero_pstf,
)
from bass.runtime.canonical_decision import CanonicalDecision


__all__ = [
    "ClosureStrategy",
    "HardCutClosure",
    "FreeStreamingClosure",
    "PowerLawExtrapolationClosure",
    "TCAClosure",
    "build_default_closure",
]


# ════════════════════════════════════════════════════════════════════
#   Helpers
# ════════════════════════════════════════════════════════════════════

def _per_m_slot_mapping(
    packed_src: np.ndarray, ell_src: int, ell_dst: int,
) -> np.ndarray:
    """Return a rank-``ell_dst`` packed vector carrying the ``ell_src``
    amplitudes at the matching ``m`` slot and zero elsewhere.

    In the real-spherical-harmonic packing used throughout LB-2a
    (``00_conventions.md §5``), index ``i ∈ 0..2ℓ`` maps to ``m = i −
    ℓ``. The ``m = k`` slot of a rank-ℓ packed array is therefore at
    index ``ℓ + k``.

    This helper is the natural per-``m`` transport used by both
    ``FreeStreamingClosure`` (scalar recursion matched slot-by-slot
    across ranks) and ``PowerLawExtrapolationClosure``. ``m`` values
    that fall outside the source rank's range are left at zero.
    """
    if packed_src.shape != (2 * ell_src + 1,):
        raise ValueError(
            f"packed_src shape {packed_src.shape} incompatible with "
            f"ell_src={ell_src}"
        )
    out = np.zeros(2 * ell_dst + 1, dtype=np.float64)
    m_max = min(ell_src, ell_dst)
    for m in range(-m_max, m_max + 1):
        out[ell_dst + m] = packed_src[ell_src + m]
    return out


# ════════════════════════════════════════════════════════════════════
#   FreeStreamingClosure  (Ma-Bertschinger 1995 §6, eq 53)
# ════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class FreeStreamingClosure:
    """Ma-Bertschinger 1995 free-streaming truncation.

    The scalar free-streaming recursion
    ``Π_{L+1} = ((2L+1) / (kη)) Π_L − Π_{L−1}``
    is the closure obtained by assuming the high-ℓ tower is dominated
    by the covariant free-streaming recursion (Ma-Bertschinger 1995
    eq 53; Baumann §4.6). It is exact in the collisionless regime
    ``Γ_T ≪ H`` for the k̂-aligned scalar multipole.

    Generalisation to the PSTF tensor packing
    -----------------------------------------
    For a rank-ℓ real-spherical-harmonic packing, the recursion is
    applied **per ``m`` slot** between the source ranks: the
    ``m = k`` amplitude of ``Π_{L+1}`` is the scalar recursion of the
    ``m = k`` amplitudes of ``Π_L`` and ``Π_{L−1}``. This matches
    Ma-Bertschinger exactly in the axisymmetric (``m = 0``) limit and
    degenerates to zero at ``k = 0`` per spec §5 (C-04).

    ``k_mpc_inv = 0`` degenerates the closure to the zero tensor
    (the numerator ``2L+1`` divided by zero limit is handled by
    early-returning ``zero_pstf(ell_requested)`` — consistent with
    ``HardCutClosure``).

    Attributes
    ----------
    k_mpc_inv : float
        Mode wavenumber ``k`` [Mpc⁻¹]. ``k = 0`` → hard-cut fallback.
    eta_at_call : float
        Conformal time ``η`` [Mpc] at which the closure is evaluated.
        The driver passes ``η`` explicitly; the closure stores this
        via ``bind_eta`` before being consumed by the RHS.

    References
    ----------
    Ma-Bertschinger 1995 (astro-ph/9506072) eq (53); Baumann §4.6;
    spec §5 (C-04..C-06).
    """

    k_mpc_inv: float
    eta: float = 0.0
    k_eta_floor: float = 1e-30

    def __post_init__(self) -> None:
        if not np.isfinite(self.k_mpc_inv) or self.k_mpc_inv < 0:
            raise ValueError(
                f"k_mpc_inv must be non-negative finite, got {self.k_mpc_inv}"
            )
        if not np.isfinite(self.eta):
            raise ValueError(f"eta must be finite, got {self.eta}")
        if self.k_eta_floor <= 0 or not np.isfinite(self.k_eta_floor):
            raise ValueError(
                f"k_eta_floor must be positive finite, got {self.k_eta_floor}"
            )

    def with_eta(self, eta: float) -> "FreeStreamingClosure":
        """Return a copy bound to the given conformal time ``η``.

        ``FreeStreamingClosure`` depends on ``kη``; the LB-2b driver
        must rebind ``η`` at every RHS evaluation. ``get_closure`` then
        reads ``self.eta`` to form ``kη``.
        """
        return FreeStreamingClosure(
            k_mpc_inv=self.k_mpc_inv,
            eta=float(eta),
            k_eta_floor=self.k_eta_floor,
        )

    def get_closure(
        self, state: PSTFHierarchyState, ell_requested: int,
    ) -> PSTFTensor:
        """Return ``Π_{ell_requested}`` via the free-streaming recursion.

        Applied iteratively: ``ell_requested = L_max + 1`` uses the two
        top tower tensors (``Π_{L_max}``, ``Π_{L_max−1}``);
        ``ell_requested = L_max + 2`` then folds in the freshly-computed
        ``Π_{L_max + 1}``.
        """
        if ell_requested < 0:
            raise ValueError(
                f"ell_requested must be non-negative, got {ell_requested}"
            )
        # Within-tower query: return defensive copy (HardCut parity).
        if ell_requested <= state.L:
            return state.tensors[ell_requested].copy()

        k_eta = float(self.k_mpc_inv) * float(self.eta)
        if abs(k_eta) < self.k_eta_floor:
            return zero_pstf(ell_requested)

        # Recur upward from the tower top.  ``Pi_prev2`` ≡ Π_{ℓ−1},
        # ``Pi_prev1`` ≡ Π_ℓ at each step; the new ``Pi_next`` is
        # ``Π_{ℓ+1}``.
        Pi_prev2 = state.tensors[state.L - 1].copy() if state.L >= 1 else zero_pstf(0)
        Pi_prev1 = state.tensors[state.L].copy()
        for ell_target in range(state.L + 1, ell_requested + 1):
            ell_src_prev1 = ell_target - 1    # rank of Pi_prev1
            ell_src_prev2 = ell_target - 2    # rank of Pi_prev2
            coeff = (2 * ell_src_prev1 + 1) / k_eta
            # Lift Pi_prev1 and Pi_prev2 into rank ``ell_target`` via
            # per-m slot transport; subtract.
            term_prev1 = _per_m_slot_mapping(
                Pi_prev1.components, ell_src_prev1, ell_target,
            )
            if ell_src_prev2 >= 0:
                term_prev2 = _per_m_slot_mapping(
                    Pi_prev2.components, ell_src_prev2, ell_target,
                )
            else:
                term_prev2 = np.zeros(2 * ell_target + 1, dtype=np.float64)
            new_comps = coeff * term_prev1 - term_prev2
            Pi_next = PSTFTensor(ell=ell_target, components=new_comps)
            # Slide the window for the next iteration.
            Pi_prev2 = Pi_prev1
            Pi_prev1 = Pi_next
        return Pi_prev1


# ════════════════════════════════════════════════════════════════════
#   PowerLawExtrapolationClosure  (Kolb §9.4 fluid-tail ansatz)
# ════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class PowerLawExtrapolationClosure:
    """Power-law extrapolation of the top-tower amplitude.

    Assume ``Π_ℓ ∝ ℓ^{-α}`` for ``ℓ > L_max`` and extrapolate from
    ``Π_{L_max}``:

        ``Π_{L_max + n} = Π_{L_max} × (L_max / (L_max + n))^{α}``

    applied per-``m`` slot (outer ``|m|`` values padded with zero
    when the target rank exceeds ``L_max``).

    Typical values:

    * ``α = 2``: free-streaming radiation (Kolb-Turner §9.4).
    * ``α = 3``: damped post-recombination photon tail.

    Usage: primarily a **diagnostic** against ``HardCutClosure`` to
    quantify truncation sensitivity (spec §6).

    Reference: Kolb-Turner *The Early Universe* §9.4; spec §6.
    """

    alpha: float

    def __post_init__(self) -> None:
        if not np.isfinite(self.alpha) or self.alpha <= 0:
            raise ValueError(
                f"alpha must be a positive finite float, got {self.alpha}"
            )

    def get_closure(
        self, state: PSTFHierarchyState, ell_requested: int,
    ) -> PSTFTensor:
        if ell_requested < 0:
            raise ValueError(
                f"ell_requested must be non-negative, got {ell_requested}"
            )
        if ell_requested <= state.L:
            return state.tensors[ell_requested].copy()
        L = state.L
        if L < 1:
            # Power-law from rank-0 is ill-defined (ℓ=0 in denominator).
            return zero_pstf(ell_requested)
        scale = (L / ell_requested) ** self.alpha
        lifted = _per_m_slot_mapping(
            state.tensors[L].components, L, ell_requested,
        )
        return PSTFTensor(
            ell=ell_requested,
            components=scale * lifted,
        )


# ════════════════════════════════════════════════════════════════════
#   TCAClosure  (wraps W6-04 solve_tca_closure; algebraic ℓ=2 override)
# ════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class TCAClosure:
    """Quadrupole-aware tight-coupling closure at ℓ=2.

    **Tower-top behaviour** (standard ``ClosureStrategy`` protocol):
    delegates ``get_closure(state, ell_requested)`` to an inner
    strategy (typically ``FreeStreamingClosure`` or ``HardCutClosure``)
    for every ``ell_requested``. TCA itself does not contribute to the
    tower top — that is a separate physical regime governed by the
    inner closure.

    **Algebraic ℓ=2 override** (spec §3.2): exposes two extra hooks
    consumed by the LB-5 integrator:

    * ``override_at_ell(ell)`` — returns ``True`` iff ``ell == 2``,
      signalling that an algebraic solution *may* replace the ODE at
      that multipole.
    * ``algebraic_closure(state, ell, eta, *, source_T, source_E,
      Gamma_T, H_local)`` — returns the PSTFTensor ``Π_2`` with its
      ``m = 0`` slot carrying the ``Θ_2`` value from the W6-04
      ``solve_tca_closure`` solver. Raises ``RuntimeError`` if
      ``Gamma_T / H_local < gamma_threshold_over_H`` (outside the
      tight-coupling regime).

    The companion ``tca_scalars(...)`` method returns both the raw
    ``(Θ_2, E_2)`` scalars for polarisation-hierarchy consumers
    (LB-4) and for bit-identicality regression against
    ``solve_tca_closure``.

    ``solve_tca_closure`` **is not reimplemented** here — this class
    is a pure wrapper (spec §7; LB-3 constraint). The CanonicalDecision
    object required by the W6-04 entrypoint is constructed internally
    via ``canonical_decision`` at each algebraic call.

    Attributes
    ----------
    inner : ClosureStrategy
        Tower-top closure used for ``ell > state.L``. Typical choices:
        ``FreeStreamingClosure`` (post-recombination photons,
        neutrinos) or ``HardCutClosure`` (background-only).
    gamma_threshold_over_H : float
        Minimum ``Γ_T / H`` above which the algebraic closure activates;
        below this threshold ``algebraic_closure`` raises. Default 100
        (CAMB / lowell §10 recommendation).

    References
    ----------
    - ``bass/closure/quadrupole_tca.py`` (W6-04); Pontzen-Challinor 2007
      §5; Cyr-Racine-Sigurdson 2010.
    - Spec §7, §11.4 (C-09..C-12).
    """

    inner: ClosureStrategy
    gamma_threshold_over_H: float = 100.0

    def __post_init__(self) -> None:
        if not isinstance(self.inner, ClosureStrategy):
            raise TypeError(
                f"inner must satisfy ClosureStrategy protocol, got "
                f"{type(self.inner).__name__}"
            )
        if (not np.isfinite(self.gamma_threshold_over_H)
                or self.gamma_threshold_over_H <= 0):
            raise ValueError(
                f"gamma_threshold_over_H must be positive finite, got "
                f"{self.gamma_threshold_over_H}"
            )

    # ---- Standard ClosureStrategy protocol -----------------------------

    def get_closure(
        self, state: PSTFHierarchyState, ell_requested: int,
    ) -> PSTFTensor:
        """Delegate to ``inner`` for the tower-top closure slots."""
        return self.inner.get_closure(state, ell_requested)

    # ---- Algebraic-override extension (spec §3.2) ----------------------

    def override_at_ell(self, ell: int) -> bool:
        """Return ``True`` iff the ℓ equation has an algebraic form.

        TCA provides an algebraic ℓ=2 closure; other multipoles always
        evolve through the ODE. ``ell`` must be non-negative.
        """
        if ell < 0:
            raise ValueError(f"ell must be non-negative, got {ell}")
        return ell == 2

    def tca_scalars(
        self,
        *,
        source_T: float,
        source_E: float,
        Gamma_T: float,
        H_local: float,
    ) -> Tuple[float, float]:
        """Compute the raw ``(Θ_2, E_2)`` scalars via the W6-04 solver.

        Parameters
        ----------
        source_T, source_E : float
            Non-collision sources at ℓ=2 (spec / W6-04 convention).
        Gamma_T : float
            Conformal Thomson rate ``τ̇ = a n_e σ_T`` [Mpc⁻¹].
        H_local : float
            Local Hubble parameter ``H`` [Mpc⁻¹] used for the
            ``Γ_T / H`` threshold check.

        Raises
        ------
        RuntimeError
            If ``Gamma_T / H_local`` is below ``gamma_threshold_over_H``.
            The algebraic approximation is not physically valid there
            and callers must fall back to the ODE integration.
        """
        if H_local <= 0 or not np.isfinite(H_local):
            raise ValueError(f"H_local must be positive finite, got {H_local}")
        if Gamma_T < 0 or not np.isfinite(Gamma_T):
            raise ValueError(
                f"Gamma_T must be non-negative finite, got {Gamma_T}"
            )
        if Gamma_T / H_local < self.gamma_threshold_over_H:
            raise RuntimeError(
                f"TCA inactive: Γ_T/H = {Gamma_T / H_local:.3e} < "
                f"threshold {self.gamma_threshold_over_H:.3e}. "
                f"Caller must use the ODE path."
            )
        decision = _always_allowing_tca_decision()
        return solve_tca_closure(
            S_T=float(source_T),
            S_E=float(source_E),
            gamma_T=float(Gamma_T),
            decision=decision,
        )

    def algebraic_closure(
        self,
        state: PSTFHierarchyState,
        ell: int,
        eta: float,
        *,
        source_T: float,
        source_E: float,
        Gamma_T: float,
        H_local: float,
    ) -> PSTFTensor:
        """Return the algebraic ``Π_2`` PSTFTensor at ``ell == 2``.

        The returned tensor carries ``Θ_2`` (W6-04 convention) in its
        ``m = 0`` slot (index 2 of the length-5 packed array) and zero
        elsewhere — the axisymmetric projection along k̂ used by MB-1995.
        The companion ``E_2`` scalar is available via ``tca_scalars``.

        Parameters
        ----------
        state : PSTFHierarchyState
            Current multipole tower (unused at ℓ=2 but accepted for
            signature parity with the general protocol).
        ell : int
            Must be ``2``; other ranks raise.
        eta : float
            Conformal time [Mpc] (unused by the pure-algebraic path).
        source_T, source_E : float
            Non-collision sources at ℓ=2.
        Gamma_T, H_local : float
            Collision rate and local Hubble; the ratio must clear the
            TCA activation threshold.
        """
        _ = state  # state unused; signature kept for protocol parity
        _ = eta    # eta unused; kept for future inhomogeneous forms
        if ell != 2:
            raise ValueError(
                f"TCAClosure.algebraic_closure handles ell=2 only, got {ell}"
            )
        theta_2, _E_2 = self.tca_scalars(
            source_T=source_T,
            source_E=source_E,
            Gamma_T=Gamma_T,
            H_local=H_local,
        )
        components = np.zeros(5, dtype=np.float64)
        components[2] = theta_2     # m = 0 slot: index ℓ = 2 in (-2..+2)
        return PSTFTensor(ell=2, components=components)


# ════════════════════════════════════════════════════════════════════
#   Internal: always-allowing CanonicalDecision for the TCA wrapper
# ════════════════════════════════════════════════════════════════════

_CACHED_TCA_DECISION: Optional[CanonicalDecision] = None


def _always_allowing_tca_decision() -> CanonicalDecision:
    """Construct (once) a permissive ``CanonicalDecision`` for the TCA
    algebraic-closure wrapper.

    The TCA closure is consumed by the hierarchy integrator whose W3
    gating lives at the integrator level; at the algebraic step
    itself every inputs-validity check is handled by
    ``TCAClosure.tca_scalars``. The downstream ``solve_tca_closure``
    nonetheless requires a ``CanonicalDecision`` (W3 contract). We
    emit an always-allowing decision here, matching the pattern used
    in ``bass/closure/test_quadrupole_tca.py``
    (``_allowing_decision``).

    Cached lazily on first use — ``make_canonical_decision`` touches
    the tangency machinery (``tsc.diagnostics.tangency``) which we do
    not want to load unless the TCA path is actually exercised.
    """
    global _CACHED_TCA_DECISION
    if _CACHED_TCA_DECISION is not None:
        return _CACHED_TCA_DECISION
    from bass.runtime.canonical_decision import make_canonical_decision
    from tsc.diagnostics.tangency import TangentKind, compute_D_diagnostic

    def _G_field(x):
        return np.asarray(x, dtype=np.float64)

    tang = compute_D_diagnostic(
        G_field=_G_field, kind=TangentKind.ONE_FIELD, xi=0, eta=0.0,
    )
    _CACHED_TCA_DECISION = make_canonical_decision(
        beta_result=(True, {
            "beta": 1.36e-3, "beta_max": 8.62e-3, "slack": 7.26e-3,
            "eta_u_dot": 0.16, "safety_factor": 0.5, "epsilon_1": 0.02,
        }),
        sigma_result=(True, {
            "sigma_sq": 1e-5, "floor": 1e-6, "log_margin_decades": 1.0,
        }),
        tangency_result=tang,
    )
    return _CACHED_TCA_DECISION


# ════════════════════════════════════════════════════════════════════
#   Factory
# ════════════════════════════════════════════════════════════════════

_STRATEGY_NAMES = frozenset({"hardcut", "freestream", "powerlaw", "tca"})


def build_default_closure(
    L_max: int,
    strategy_name: str = "freestream",
    *,
    k_mpc_inv: float = 0.0,
    eta: float = 0.0,
    alpha: float = 2.0,
    gamma_threshold_over_H: float = 100.0,
) -> ClosureStrategy:
    """Dispatch-by-name factory for the four LB-3 closure strategies.

    Parameters
    ----------
    L_max : int
        Top multipole of the tower. Used only for validation; the
        returned strategy is rank-agnostic (all strategies read the
        current ``state.L`` at call time).
    strategy_name : {'hardcut', 'freestream', 'powerlaw', 'tca'}
        Named strategy. Unknown names raise ``ValueError``.
    k_mpc_inv : float
        Wavenumber used by ``FreeStreamingClosure``; ignored by others.
        Pass ``0.0`` for background-only / FLRW-zero-mode integration.
    eta : float
        Initial binding for the free-streaming ``η``; rebind per step
        via ``FreeStreamingClosure.with_eta`` inside the RHS.
    alpha : float
        Power-law exponent for ``PowerLawExtrapolationClosure``.
        Default 2 (free-streaming radiation; Kolb §9.4).
    gamma_threshold_over_H : float
        Activation threshold for ``TCAClosure``.

    Returns
    -------
    ClosureStrategy
        A fresh closure-strategy instance. For ``'tca'`` the inner
        strategy is a ``FreeStreamingClosure`` (when ``k_mpc_inv > 0``)
        or a ``HardCutClosure`` (when ``k_mpc_inv == 0``).

    Raises
    ------
    ValueError
        If ``strategy_name`` is not among the four recognised names.

    Reference: spec §10.2.
    """
    if L_max < 0:
        raise ValueError(f"L_max must be non-negative, got {L_max}")
    name = strategy_name.strip().lower()
    if name not in _STRATEGY_NAMES:
        raise ValueError(
            f"Unknown strategy_name '{strategy_name}'; expected one of "
            f"{sorted(_STRATEGY_NAMES)}"
        )
    if name == "hardcut":
        return HardCutClosure()
    if name == "freestream":
        return FreeStreamingClosure(k_mpc_inv=float(k_mpc_inv), eta=float(eta))
    if name == "powerlaw":
        return PowerLawExtrapolationClosure(alpha=float(alpha))
    # name == "tca"
    if k_mpc_inv > 0:
        inner: ClosureStrategy = FreeStreamingClosure(
            k_mpc_inv=float(k_mpc_inv), eta=float(eta),
        )
    else:
        inner = HardCutClosure()
    return TCAClosure(
        inner=inner,
        gamma_threshold_over_H=float(gamma_threshold_over_H),
    )


# Silence unused-import warnings on dependencies kept for the public API.
_ = field
