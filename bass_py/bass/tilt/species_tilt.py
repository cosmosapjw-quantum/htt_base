"""bass/tilt/species_tilt.py — Tilted-species energy-momentum decomposition
(§3.2 of the low-ℓ Bianchi solver reference).

For a tilted Bianchi background the species 4-velocity is

    u_(s)^a = γ_s (n^a + v_(s)^a),     γ_s = (1 − v_s²)^{-1/2}

and the rest-frame perfect-fluid stress-energy

    T^(s)_ab = (ρ̂_s + p̂_s) u^(s)_a u^(s)_b + p̂_s g_ab

decomposes in the normal frame n^a as

    T^(s)_ab = μ_s n_a n_b + 2 n_(a q^(s)_{b)} + p_s h_ab + π^(s)_ab,

with

    μ_s       = γ_s² (ρ̂_s + p̂_s) − p̂_s                                 (eq. 203)
    q_a^(s)   = γ_s² (ρ̂_s + p̂_s) v_a^(s)                                (eq. 206)
    p_s       = p̂_s + (1/3) γ_s² (ρ̂_s + p̂_s) v_s²                       (eq. 208)
    π_ab^(s)  = γ_s² (ρ̂_s + p̂_s) v_⟨a^(s) v_b⟩^(s)                      (eq. 212)

The small-tilt limit (|v_s| ≪ 1) reduces to

    μ_s  → ρ̂_s + (1 + w_s) ρ̂_s · v_s²  + O(v⁴)
    q_a^(s) → (1 + w_s) ρ̂_s · v_a^(s)  + O(v³)
    π_ab^(s) = O(v²)

which matches the leading-order tilted-fluid expansion used in the
reference §3.2 and in ``bass.background.nonperturbative_tilt``
(where Ω_tilt = (1+w) Ω sinh² β supplies the species analogue at
the cosmology level).

This module also provides the total-momentum-constraint helper
(reference §3.2 eq 226-229):

    8π P_i^(tot) = e^{-α} (σ_{jk} C^j_{ki} − σ_{ij} C^k_{kj})

so that species tilts can be chosen consistently with the Bianchi
structure constants and background shear.

External-code policy
--------------------
All expressions are evaluated with NumPy scalars / arrays; no
cosmology package (CAMB/CLASS/AniCLASS) is invoked. The small-tilt
limit is a *derived* approximation for self-consistency tests, not an
oracle.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Tuple

import numpy as np

from bass.background.bianchi_types import StructureConstants


__all__ = [
    'TiltedSpeciesParams',
    'TiltedSpeciesDecomposition',
    'decompose_tilted_species',
    'small_tilt_limit',
    'total_momentum_constraint',
]


# ════════════════════════════════════════════════════════════════════
# Parameters and output containers
# ════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class TiltedSpeciesParams:
    """Input rest-frame thermodynamics and tilt for one species.

    Attributes
    ----------
    rho_hat : float
        Rest-frame energy density ρ̂_s (any consistent units).
    p_hat : float
        Rest-frame pressure p̂_s. For CDM / dust: p̂ = 0; for photons
        / relativistic: p̂ = ρ̂ / 3.
    v : (3,) ndarray
        3-velocity v_(s)^a in the n^a-frame basis (aligned with the
        tetrad axes from ``tetrad_state``).
    label : str
        Human-readable identifier (e.g. 'photon', 'baryon', 'CDM').
    """
    rho_hat: float
    p_hat: float
    v: np.ndarray
    label: str = ''

    def __post_init__(self):
        v = np.asarray(self.v, dtype=np.float64)
        if v.shape != (3,):
            raise ValueError(
                f"v must have shape (3,), got {v.shape}"
            )
        if float(np.dot(v, v)) >= 1.0:
            raise ValueError(
                f"|v|² = {float(np.dot(v, v)):.4f} ≥ 1: superluminal tilt"
            )
        # replace stored v with an immutable-ish copy
        object.__setattr__(self, 'v', v)

    @property
    def w(self) -> float:
        """Equation of state w_s = p̂_s / ρ̂_s (well-defined for ρ̂ > 0)."""
        if self.rho_hat <= 0.0:
            return 0.0
        return self.p_hat / self.rho_hat

    @property
    def v_sq(self) -> float:
        """v_s² = v^a v_a in flat 3-space."""
        return float(np.dot(self.v, self.v))

    @property
    def gamma(self) -> float:
        """Lorentz factor γ_s = (1 − v_s²)^{-1/2}."""
        return 1.0 / np.sqrt(1.0 - self.v_sq)


@dataclass(frozen=True)
class TiltedSpeciesDecomposition:
    """Normal-frame decomposition of T_ab for one tilted species.

    Attributes
    ----------
    mu : float
        Total energy density in n^a-frame, μ_s = γ_s² (ρ̂ + p̂) − p̂.
    q : (3,) ndarray
        Momentum density q_a^(s) = γ_s² (ρ̂ + p̂) v_a.
    p : float
        Isotropic pressure p_s = p̂ + (1/3) γ_s² (ρ̂ + p̂) v².
    pi : (3, 3) ndarray
        Anisotropic stress π_ab = γ_s² (ρ̂ + p̂) v_⟨a v_b⟩
        (symmetric trace-free).
    params : TiltedSpeciesParams
        Original input for traceability.
    """
    mu: float
    q: np.ndarray
    p: float
    pi: np.ndarray
    params: TiltedSpeciesParams

    @property
    def trace_pi(self) -> float:
        """tr π_ab — exact trace, should be 0 by construction."""
        return float(np.trace(self.pi))


# ════════════════════════════════════════════════════════════════════
# Main decomposition
# ════════════════════════════════════════════════════════════════════

def _sym_traceless(tensor: np.ndarray) -> np.ndarray:
    """Project a 3×3 tensor onto its symmetric trace-free part."""
    sym = 0.5 * (tensor + tensor.T)
    return sym - (np.trace(sym) / 3.0) * np.eye(3)


def decompose_tilted_species(
    params: TiltedSpeciesParams,
) -> TiltedSpeciesDecomposition:
    """Return (μ_s, q_a^(s), p_s, π_ab^(s)) from (ρ̂, p̂, v).

    Exact nonperturbative evaluation of reference §3.2 equations
    203-212. No small-v expansion anywhere.

    Parameters
    ----------
    params : TiltedSpeciesParams
        Rest-frame species input.

    Returns
    -------
    TiltedSpeciesDecomposition
    """
    rho_hat = float(params.rho_hat)
    p_hat = float(params.p_hat)
    v = params.v
    v_sq = params.v_sq
    gamma_sq = 1.0 / max(1.0 - v_sq, 1.0e-30)
    rho_plus_p = rho_hat + p_hat

    mu = gamma_sq * rho_plus_p - p_hat
    q = gamma_sq * rho_plus_p * v
    p = p_hat + (1.0 / 3.0) * gamma_sq * rho_plus_p * v_sq
    # v_⟨a v_b⟩ = v_a v_b − (1/3) v² δ_ab (symmetric trace-free)
    v_outer = np.outer(v, v) - (v_sq / 3.0) * np.eye(3)
    pi = gamma_sq * rho_plus_p * v_outer

    return TiltedSpeciesDecomposition(
        mu=mu, q=q, p=p, pi=pi, params=params,
    )


# ════════════════════════════════════════════════════════════════════
# Small-tilt consistency check
# ════════════════════════════════════════════════════════════════════

def small_tilt_limit(
    params: TiltedSpeciesParams,
) -> TiltedSpeciesDecomposition:
    """Leading-order small-|v| expansion of ``decompose_tilted_species``.

    Used for self-consistency tests against the exact decomposition:

        μ_s  ≈ ρ̂_s + (ρ̂ + p̂) · v_s²
        q_a  ≈ (ρ̂ + p̂) · v_a
        p_s  ≈ p̂_s + (1/3)(ρ̂ + p̂) · v_s²
        π_ab ≈ (ρ̂ + p̂) · v_⟨a v_b⟩

    Matches the exact formulas to O(v⁴) for μ / p and to O(v²) for
    q / π. The residual grows as v_s² × (γ² − 1).
    """
    rho_hat = float(params.rho_hat)
    p_hat = float(params.p_hat)
    v = params.v
    v_sq = params.v_sq
    rho_plus_p = rho_hat + p_hat

    mu = rho_hat + rho_plus_p * v_sq
    q = rho_plus_p * v
    p = p_hat + (1.0 / 3.0) * rho_plus_p * v_sq
    v_outer = np.outer(v, v) - (v_sq / 3.0) * np.eye(3)
    pi = rho_plus_p * v_outer

    return TiltedSpeciesDecomposition(
        mu=mu, q=q, p=p, pi=pi, params=params,
    )


# ════════════════════════════════════════════════════════════════════
# Total-momentum constraint (reference §3.2 eq 226-229)
# ════════════════════════════════════════════════════════════════════

def total_momentum_constraint(
    structure: StructureConstants,
    sigma_ab: np.ndarray,
    alpha: float,
) -> np.ndarray:
    """Bianchi total momentum density from shear × structure constants.

    Evaluates

        8π P_i^(tot) = e^{-α} (σ_{jk} C^j_{ki} − σ_{ij} C^k_{kj})

    (reference eq 226). The species tilts (v_s^a) must be chosen so
    that Σ_s q_a^(s) matches P_i^(tot) up to 8π.

    Parameters
    ----------
    structure : StructureConstants
        Bianchi structure constants with the (n_ab, a_alpha)
        decomposition.
    sigma_ab : (3, 3) ndarray
        Shear tensor σ_ab (not the conformal Σ_ab — this is the
        physical shear).
    alpha : float
        α = ln a.

    Returns
    -------
    (3,) ndarray
        8π P_i^(tot) in the natural units of ``sigma_ab``.

    Notes
    -----
    The structure-constant form C^i_{jk} is recovered from the
    Ellis-MacCallum n_ab + a_alpha split via

        C^i_{jk} = ε_{jkl} n^{li} + δ^i_j a_k − δ^i_k a_j.

    For Type I (n^ij = a^i = 0) the constraint is trivially zero.
    For Type V (a^i ≠ 0 only) and others with a^i ≠ 0 the right-hand
    side acquires a contribution from the (δ^i_j a_k − δ^i_k a_j) part.
    """
    sigma = np.asarray(sigma_ab, dtype=np.float64)
    e_neg_alpha = float(np.exp(-alpha))

    # Build C^i_{jk} from the Ellis-MacCallum (n^{ab}, a_α) split.
    # Pontzen-Challinor frame convention (bass_py/bass/background/
    # bianchi_types.py docstring, line ~126): a_α = (0, a_twist, 0),
    # n^{ab} = diag(n1, n2, n3).
    n_up = np.diag([structure.n1, structure.n2, structure.n3]).astype(np.float64)
    a = np.array([0.0, structure.a_twist, 0.0], dtype=np.float64)

    # ε_{jkl} in 3D Cartesian (fully antisymmetric, ε_{123} = +1)
    eps = np.zeros((3, 3, 3), dtype=np.float64)
    eps[0, 1, 2] = eps[1, 2, 0] = eps[2, 0, 1] = +1.0
    eps[0, 2, 1] = eps[2, 1, 0] = eps[1, 0, 2] = -1.0

    # C^i_{jk} via C = ε·n + δ*a anti-symmetric part
    # Term 1: ε_{jkl} n^{li}
    term1 = np.einsum('jkl,li->ijk', eps, n_up)
    # Term 2: δ^i_j a_k − δ^i_k a_j
    delta = np.eye(3, dtype=np.float64)
    term2 = (
        np.einsum('ij,k->ijk', delta, a)
        - np.einsum('ik,j->ijk', delta, a)
    )
    C_up_low_low = term1 + term2  # C^i_{jk}

    # 8π P_i = e^{-α} (σ_{jk} C^j_{ki} − σ_{ij} C^k_{kj})
    # First term: σ_{jk} C^j_{ki}, contract j first and k-then-i
    first = np.einsum('jk,jki->i', sigma, C_up_low_low)
    # Second term: σ_{ij} C^k_{kj}, contract k:k → scalar trace over
    # the upper-lower pair (i.e. contract first and third indices of C)
    trace_C = np.einsum('kkj->j', C_up_low_low)  # C^k_{kj}
    second = np.einsum('ij,j->i', sigma, trace_C)

    return e_neg_alpha * (first - second)
