"""
bass/tilt/channel_routing.py  (Week 1 Day 5)
=============================================

Channel routing for global cosmological tilt vs local observer patch.

Two fundamentally different tilts appear in the analysis
--------------------------------------------------------

GLOBAL β̄  (cosmological, pre-recombination):
  - Drives baryon velocity in the early universe through the tight-coupling
    structure enforced by `baryon_only_policy.py`.
  - Enters the Thomson collision operator — photon anisotropy is generated
    with the baryon-frame source function.
  - Signature: TT AND EE at ℓ ≥ 2 (nontrivial quadrupole from coupled shear).

LOCAL v_loc  (observer patch, post-recombination):
  - Observer's peculiar velocity in their own local rest frame.
  - Doppler-boosts the observed CMB spectrum (aberration + frequency shift).
  - Signature: TT ONLY (dipole at ℓ = 1, plus boost-induced ℓ-mixing).
  - No EE contribution because τ ≈ 0 post-recombination; there is no
    Thomson source regeneration from the observer's motion.
  - Supported on a C² window function W_R of patch radius R.

The routing policy is the TT-vs-EE separation identified in
ch09 §sec:disc-local-patch:

    "[...] local motion is encoded in the photon dipole Θ^(γ)_a and affects
     only the temperature power spectrum (TT) at ℓ = 1; it does not source
     E-mode polarisation. Cosmological tilt, by contrast, affects both TT
     and EE through the pre-recombination anisotropic stress."

Paper I Prop 5 coefficients
---------------------------
The perturbative boost law (Paper I Eqs. 29–32) for axisymmetric Θ multipoles:

    T̃_0/T_0  = 1 − (1/3) T_a v^a − (1/6) v_a v^a + O(v³)
    T̃_a     = T_a + v_a − (4/5) T_ab v^b + O(v²)
    T̃_ab    = T_ab + 2 v_⟨a T_b⟩ + v_⟨a v_b⟩ + O(v³)
    T̃_abc   = 3 T_⟨ab v_c⟩ + O(v²)

Coefficients: −4/5 (ℓ=2 → ℓ=1), +2 (ℓ=1 → ℓ=2), +3 (ℓ=2 → ℓ=3).
Axisymmetric (1D) case retains the same coefficients up to PSTF projection
factors, which in this notation absorb to ±1.

Window function W_R
-------------------
C² raised-cosine taper supported on patch of radius R:

    W_R(r) = 1                                     for r ≤ r_inner
           = 1 − q(t),  t = (r − r_inner)/(R − r_inner),   for r_inner < r < R
           = 0                                     for r ≥ R

where q(t) = 10 t³ − 15 t⁴ + 6 t⁵ (smoothstep_C2) provides C² continuity:
q(0) = 0, q(1) = 1, q'(0) = q'(1) = 0, q''(0) = q''(1) = 0.

The maximum |∂_r W_R| occurs at t = 1/2, where |∂_r W_R|_max = 15/(8(R − r_inner)).

References
----------
  ch09_discussion.tex §sec:disc-local-patch
  Paper I (Park-Cheoun-Park 2026) Prop. 5, Eqs. 29–32, Appendix B3
  R-TILT-02 §3.2 (local patch gradient contribution)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import math
import numpy as np


# ═══════════════════════════════════════════════════════════════
# §1 — Channel and effect type enums
# ═══════════════════════════════════════════════════════════════

class Channel(Enum):
    """Observational power-spectrum channels."""
    TT = "TT"
    TE = "TE"
    EE = "EE"
    BB = "BB"


class TiltEffect(Enum):
    """The two tilt effect types distinguished by the routing architecture."""
    GLOBAL = "global"   # cosmological β̄ (pre-recombination, TT+EE)
    LOCAL = "local"     # observer v_loc (post-recombination, TT only)


# ═══════════════════════════════════════════════════════════════
# §2 — W_R window function
# ═══════════════════════════════════════════════════════════════

def smoothstep_C2(t: np.ndarray) -> np.ndarray:
    """Quintic smoothstep function with C² continuity at endpoints.

        q(t) = 10 t³ − 15 t⁴ + 6 t⁵

    Properties:
        q(0) = 0, q(1) = 1
        q'(0) = q'(1) = 0
        q''(0) = q''(1) = 0
        max |q'| = 15/8 at t = 1/2

    Parameters
    ----------
    t : array-like
        Input in [0, 1] (values outside are clipped).

    Returns
    -------
    array-like
        q(t) with same shape as input.
    """
    t = np.clip(t, 0.0, 1.0)
    return t**3 * (10.0 - 15.0 * t + 6.0 * t**2)


def window_W_R(
    r: np.ndarray,
    R_patch: float,
    r_inner_fraction: float = 0.5,
) -> np.ndarray:
    """Radial patch window W_R(r), C²-continuous raised-cosine (smoothstep) taper.

    Parameters
    ----------
    r : array-like
        Radial distance in Mpc (comoving).
    R_patch : float
        Patch radius in Mpc. Window is zero for r ≥ R_patch.
    r_inner_fraction : float, optional
        Fraction of R_patch at which taper begins. Default 0.5 → inner 50%
        of patch is flat at 1.0, outer 50% tapers to 0.0.

    Returns
    -------
    W : array
        W_R(r) ∈ [0, 1] with same shape as r.
    """
    if R_patch <= 0:
        raise ValueError(f"R_patch must be > 0, got {R_patch}")
    if not 0.0 <= r_inner_fraction < 1.0:
        raise ValueError(
            f"r_inner_fraction must be in [0, 1), got {r_inner_fraction}"
        )

    r_arr = np.asarray(r, dtype=float)
    r_inner = r_inner_fraction * R_patch

    W = np.ones_like(r_arr)

    # Taper region: r_inner < r < R_patch
    taper_mask = (r_arr > r_inner) & (r_arr < R_patch)
    if np.any(taper_mask):
        t = (r_arr[taper_mask] - r_inner) / (R_patch - r_inner)
        W[taper_mask] = 1.0 - smoothstep_C2(t)

    # Zero beyond R_patch
    W[r_arr >= R_patch] = 0.0

    return W


def window_W_R_max_gradient(
    R_patch: float, r_inner_fraction: float = 0.5,
) -> float:
    """Maximum |∂_r W_R| (used for u̇ boundary estimate; R-TILT-02 §3.2).

    For quintic smoothstep: max |q'| = 15/8 at t=1/2.
    Therefore max |∂_r W| = (15/8) / (R_patch − r_inner) = (15/8) / (R_patch × (1 − r_inner_fraction))
    """
    taper_width = R_patch * (1.0 - r_inner_fraction)
    if taper_width <= 0:
        return np.inf
    return (15.0 / 8.0) / taper_width


# ═══════════════════════════════════════════════════════════════
# §3 — Paper I Prop 5 boost mixing coefficients
# ═══════════════════════════════════════════════════════════════
#
# P2-W4-01 (resolved W4D5): the coefficient definitions and transforms
# below originally lived in this module. They physically belong to the
# TSC chart layer and have been moved to tsc/charts/boost_coefficients.py.
# We re-export here for backward compatibility with callers that expect
# these symbols on bass.validation.channel_routing.
#
# The bass/validation → tsc direction is architecturally permitted; only
# the reverse (tsc → bass/runtime, tsc → bass/validation, etc.) is
# forbidden by the ownership freeze.

from tsc.charts.boost_coefficients import (  # noqa: F401  (re-export)
    PROP5_COEFF_DIPOLE_FROM_QUADRUPOLE,
    PROP5_COEFF_QUADRUPOLE_FROM_DIPOLE,
    PROP5_COEFF_OCTUPOLE_FROM_QUADRUPOLE,
    boost_mixing_matrix,
    boost_additive_velocity_terms,
    apply_boost_to_teff,
)


# ═══════════════════════════════════════════════════════════════
# §4 — TiltRouter: route global vs local effects
# ═══════════════════════════════════════════════════════════════

@dataclass
class TiltRouter:
    """Route tilt effects to observational channels, enforcing TT-vs-EE separation.

    Parameters
    ----------
    beta_bar : float
        Cosmological (global) tilt magnitude. Drives baryon velocity pre-recomb.
    v_loc : np.ndarray, optional
        Observer local peculiar velocity (3-vector, units of c). Drives
        post-recombination Doppler boost only. If None, defaults to zero.
    R_patch_mpc : float, optional
        Radius of local patch in Mpc. Required if v_loc is nonzero.
    """
    beta_bar: float = 0.0
    v_loc: np.ndarray = field(default_factory=lambda: np.zeros(3))
    R_patch_mpc: Optional[float] = None

    def __post_init__(self):
        self.v_loc = np.asarray(self.v_loc, dtype=float)
        if self.v_loc.shape != (3,):
            raise ValueError(
                f"v_loc must be 3-vector, got shape {self.v_loc.shape}"
            )

    @property
    def v_loc_magnitude(self) -> float:
        return float(np.linalg.norm(self.v_loc))

    def is_local_active(self) -> bool:
        """True if the local observer patch is activated (|v_loc| > 0)."""
        return self.v_loc_magnitude > 1e-15

    def is_global_active(self) -> bool:
        """True if the global cosmological tilt is activated (β̄ ≠ 0)."""
        return abs(self.beta_bar) > 1e-15

    # ── Core routing ──

    def route(self, effect: TiltEffect, channel: Channel) -> float:
        """Return the coupling amplitude for (effect, channel) pair.

        Enforces:
          - GLOBAL tilt couples to both TT and EE (via Thomson)
          - LOCAL tilt couples to TT only (EE returns zero — architectural)
          - TE and BB follow the same sign rules as EE for local
            (future work may extend to nontrivial BB from tilted shear)

        Parameters
        ----------
        effect : TiltEffect
            GLOBAL or LOCAL.
        channel : Channel
            TT, TE, EE, or BB.

        Returns
        -------
        amplitude : float
            Coupling amplitude (dimensionless).
            For GLOBAL: |β̄| for both TT and EE; 0 for BB (no E-B mixing at
              linear order; full analysis at Week 3).
            For LOCAL: |v_loc| for TT; exactly 0 for EE, TE, BB.
        """
        if effect == TiltEffect.GLOBAL:
            if channel in (Channel.TT, Channel.EE):
                return abs(self.beta_bar)
            elif channel == Channel.TE:
                # Nontrivial for global: TE correlation exists but is
                # scaled by √(TT×EE); returning β̄ as leading approximation
                return abs(self.beta_bar)
            elif channel == Channel.BB:
                # Linear tilt does not generate BB in baryon-only architecture
                return 0.0

        elif effect == TiltEffect.LOCAL:
            if channel == Channel.TT:
                return self.v_loc_magnitude
            # ENFORCED ZERO for all polarization channels (ch09)
            elif channel in (Channel.TE, Channel.EE, Channel.BB):
                return 0.0

        raise ValueError(f"Unknown (effect, channel): ({effect}, {channel})")

    def enforce_local_EE_zero(self) -> None:
        """Sentinel check: raises if local-EE coupling is ever nonzero.

        This is a structural invariant of the architecture: by design, the
        observer's local motion cannot source E-mode polarization at
        post-recombination epochs. Called at the end of any computation that
        produces EE amplitudes.
        """
        ee_local = self.route(TiltEffect.LOCAL, Channel.EE)
        if abs(ee_local) > 1e-15:
            raise AssertionError(
                f"Architectural violation: local-EE = {ee_local}, must be 0. "
                f"v_loc = {self.v_loc} is sourcing E-mode polarisation, which "
                f"the post-recombination baryon-only policy forbids."
            )

    # ── Boost application ──

    def apply_local_boost(
        self, T_multipoles: np.ndarray,
    ) -> np.ndarray:
        """Apply the local observer boost to a Teff multipole state.

        Uses Paper I Prop 5 linear coefficients with v = |v_loc|.

        Parameters
        ----------
        T_multipoles : ndarray shape (L+1,)
            Axisymmetric Teff multipoles [T_0, ..., T_L].

        Returns
        -------
        T_tilde : ndarray same shape
            Boosted multipoles T̃.
        """
        return apply_boost_to_teff(T_multipoles, self.v_loc_magnitude)

    def apply_global_tilt(
        self, T_multipoles: np.ndarray,
    ) -> np.ndarray:
        """Apply the global cosmological tilt to a Teff multipole state.

        Uses Paper I Prop 5 with v = β̄. Note: this is the kinematic mixing
        only; the full cosmological effect includes Thomson-sourced
        polarisation which enters at the solver level (Week 2 onwards).

        Returns
        -------
        T_tilde : ndarray
            Tilt-transformed multipoles (kinematic contribution only).
        """
        return apply_boost_to_teff(T_multipoles, self.beta_bar)

    # ── W_R window ──

    def window(self, r: np.ndarray) -> np.ndarray:
        """Evaluate the patch window W_R at radial distances r.

        Parameters
        ----------
        r : array-like
            Radial distance in Mpc.

        Returns
        -------
        W : array
            W_R(r) values.

        Raises
        ------
        ValueError
            If R_patch_mpc was not specified (local patch inactive).
        """
        if self.R_patch_mpc is None:
            raise ValueError(
                "No R_patch_mpc specified; cannot evaluate window function. "
                "Set R_patch_mpc when constructing the TiltRouter."
            )
        return window_W_R(r, self.R_patch_mpc)

    def summary(self) -> dict:
        """Return a structured summary of the routing state."""
        return {
            'global_active': self.is_global_active(),
            'local_active': self.is_local_active(),
            'beta_bar': self.beta_bar,
            'v_loc_magnitude': self.v_loc_magnitude,
            'R_patch_mpc': self.R_patch_mpc,
            'routing': {
                f'{e.value}-{c.value}': self.route(e, c)
                for e in TiltEffect for c in Channel
            },
        }


# ═══════════════════════════════════════════════════════════════
# §5 — Factory functions
# ═══════════════════════════════════════════════════════════════

def make_global_only_router(beta_bar: float) -> TiltRouter:
    """Router with only cosmological tilt (no local patch)."""
    return TiltRouter(beta_bar=beta_bar, v_loc=np.zeros(3))


def make_local_only_router(
    v_loc: np.ndarray, R_patch_mpc: float,
) -> TiltRouter:
    """Router with only observer local patch (no global tilt)."""
    return TiltRouter(
        beta_bar=0.0, v_loc=np.asarray(v_loc, dtype=float),
        R_patch_mpc=R_patch_mpc,
    )


def make_combined_router(
    beta_bar: float, v_loc: np.ndarray, R_patch_mpc: float,
) -> TiltRouter:
    """Router with both global tilt and local patch active.

    This is the full VER06 production configuration.
    """
    return TiltRouter(
        beta_bar=beta_bar, v_loc=np.asarray(v_loc, dtype=float),
        R_patch_mpc=R_patch_mpc,
    )
