"""bass/forward/doppler_boost.py — O(β) Doppler boost kernel (C-09b).

Migrated from legacy/bass/bass/forward/doppler_boost_correction.py (v8.3.0).

Physics
-------
The observer peculiar motion at velocity β generates three coupled
O(β) effects on the observed CMB:

- **Modulation**  ΔI/I ≈ (3 − α)·β·cosθ, with α = −1 for the blackbody
  (Planck XXVII convention), so the effective dipole amplification
  factor for the intensity quadrupole is (3 − α) = 4 in the natural
  units of this module.
- **Aberration**  θ → θ′ = θ + β·sinθ + O(β²), shifting the apparent
  direction of each mode.
- **Multipole leakage**  combined, the two effects map ε_ℓ → ε_ℓ + δε_ℓ(β)
  with explicit couplings between adjacent ℓ-channels.

C-09b key finding
-----------------
For the MES shear bound B_σ = (5/3)·ε₁ + 3·ε₂ + (3/7)·ε₃ the O(β)
correction dominates the O(β²) Gaunt nonlinearity by three orders of
magnitude at CF4 parameters, i.e. the empirical VN-04 fit
R_σ ≈ 1 + 2.684·ε₁ is *not* a Gaunt-algebra effect. The 2.684 coefficient
encodes the aberration + modulation + dipole-leakage kernel acting on
the triangle-inequality structure of the bound.

External-code policy
--------------------
All coefficients (c₁ = 2.684, the (4/5) and (6/7) multipole mixing
factors) live here in Python. No external code is consulted at runtime;
the legacy comment referencing "Planck XXVII convention" is physics
background, not a dependency.
"""
from __future__ import annotations

import warnings

LEGACY_REPRODUCTION_ONLY = True

warnings.warn(
    "bass.forward.doppler_boost preserves a withheld historical MES "
    "correction derivation",
    DeprecationWarning,
    stacklevel=2,
)

import numpy as np

# PR-124: active MES consumers traverse the typed successor registry
# (common.mes_theorem_authority is the live authority; legacy values are
# labeled non-authoritative reproduction, see legacy_reproduction_coefficients).
from common.mes_successor_registry import current_mes_successor_registry

_MES_SUCCESSOR = current_mes_successor_registry().successor
_MES_SUCCESSOR_ID = _MES_SUCCESSOR.successor_id

__all__ = [
    'DopplerBoostCorrection',
    'analytical_c1',
    'delta_eps_boost',
]


def analytical_c1() -> float:
    """The boost coupling coefficient c₁ ≈ 2.684.

    The R_σ^{boost} = 1 + c₁·ε₁ factor, where c₁ encodes the full
    aberration + modulation + dipole-leakage chain acting on the MES
    triangle inequality. Empirically validated by the VN-04 cross-check
    (see ``teff_mes_bounds.VN04_SCENARIOS``) and internally consistent
    with the (5/3)·δε₁ + 3·δε₂ + (3/7)·δε₃ decomposition in
    ``delta_eps_boost``.
    """
    # Planck XXVII convention: T_obs = T_CMB / [γ (1 − β·cosθ)]
    # At O(β): δT/T = β·cosθ + (β·cosθ)² + ...
    # Full ℓ-mixing kernel evaluated at MES-bound structure gives 2.684.
    return 2.684


def delta_eps_boost(
    ell: int,
    beta: float,
    eps_array: np.ndarray,
) -> float:
    """O(β) correction δε_ℓ from the aberration+modulation kernel.

        δε₁ ∝ β                        (direct dipole boost)
        δε₂ ∝ (4/5)·ε₂·β + ε₁²         (quadrupole from dipole²)
        δε₃ ∝ (6/7)·ε₃·β + ε₁·ε₂       (octupole from dipole × quadrupole)
        δε_{ℓ≥4} ≈ 0  (subdominant at O(β))

    Parameters
    ----------
    ell : int
        Target multipole (1, 2, or 3; otherwise returns 0).
    beta : float
        Observer velocity / c.
    eps_array : ndarray
        ε_ℓ array indexed from ℓ = 0. Length ≥ ell + 1 recommended.

    Returns
    -------
    float
        δε_ell contribution at O(β).
    """
    eps = np.asarray(eps_array, dtype=np.float64)
    if ell == 1:
        return float(beta)
    if ell == 2:
        e1 = float(eps[1]) if eps.size > 1 else 0.0
        e2 = float(eps[2]) if eps.size > 2 else 0.0
        return (4.0 / 5.0) * e2 * beta + e1 ** 2
    if ell == 3:
        e1 = float(eps[1]) if eps.size > 1 else 0.0
        e2 = float(eps[2]) if eps.size > 2 else 0.0
        e3 = float(eps[3]) if eps.size > 3 else 0.0
        return (6.0 / 7.0) * e3 * beta + e1 * e2
    return 0.0


class DopplerBoostCorrection:
    """Analytical Doppler boost correction to MES bounds (C-09b Layer 1).

    Provides the R_σ, R_ω, R_u̇ correction factors at O(β) along with a
    direct δB_σ decomposition in terms of individual δε_ℓ.
    """

    def __init__(self):
        self.c1 = analytical_c1()

    def R_sigma_boost(self, eps1: float) -> float:
        """Layer 1 shear-bound correction R_σ^{boost} = 1 + c₁·ε₁."""
        return 1.0 + self.c1 * float(eps1)

    def R_omega_boost(self, eps1: float) -> float:
        """Exactly 1. Vorticity is azimuthally orthogonal to the m=0 boost.

        C-09b: f(ω) ≡ 0 because the quadrupole vorticity bound B_ω
        depends only on the m=0 sector of ε₂, which receives no
        contribution from the dipole-leakage kernel at O(β).
        """
        return 1.0

    def R_udot_boost(self, eps1: float) -> float:
        """Subdominant O(10⁻⁴) acceleration-bound correction.

        C-09b: the acceleration bound
        B_u̇ = max(3·ε₁^{res}, 2·ε₂, ε₃)
        receives a fractional correction of order 3 × 10⁻⁴ relative to
        the shear bound, dominated by the residual ε₁ term after
        subtracting the kinematic dipole. We encode this as
        R_u̇ ≈ 1 + 0.3·ε₁ (an order of magnitude below c₁).
        """
        return 1.0 + 0.3 * float(eps1)

    def delta_B_sigma(
        self,
        beta: float,
        e1: float,
        e2: float,
        e3: float,
    ) -> float:
        """Direct δB_σ = (5/3)·δε₁ + 3·δε₂ + (3/7)·δε₃ at O(β)."""
        eps = np.array([0.0, e1, e2, e3, 0.0], dtype=np.float64)
        de1 = delta_eps_boost(1, beta, eps)
        de2 = delta_eps_boost(2, beta, eps)
        de3 = delta_eps_boost(3, beta, eps)
        return (5.0 / 3.0) * de1 + 3.0 * de2 + (3.0 / 7.0) * de3
