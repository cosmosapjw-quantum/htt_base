"""
tsc/diagnostics/entropy_invariants.py  (Week 4 Day 5, Part 2)
================================================================

Scalar entropy invariants on the Paper I Teff exponential-family chart.

Role
----
Three related diagnostics that extend the L0 precision dashboard with
structural cross-checks on the exponential-family distribution:

  1. Entropy-density / number-density ratio s/n derived from I_n moments
     (dimensionless thermodynamic identity; η-dependence encoded).
  2. Gram-matrix admissibility invariants: λ_min, λ_max, κ of the TWO_FIELD
     Gram under the Fisher-entropy inner product.
  3. MB η-independence check: for Maxwell-Boltzmann at any η the moment
     ratios I_n₁/I_n₂ are ξ- and η-independent (I_n = e^η n!).

Scope note on theorem numbering
-------------------------------
The D4 packet referenced Paper I "Thm 9 / 10 / 11" as target content. The
present implementation covers the substantive content (entropy-density
ratio, Gram admissibility, η-independence of MB ratios) that commonly
appears under these theorem labels in exponential-family literature, but
does not claim theorem-label alignment to a specific numbered statement
in the thesis Paper I — that alignment is CONDITIONAL. The mathematical
content itself is established from standard exponential-family theory.

No gating
---------
Pure TSC-layer scalar computation. No CanonicalDecision consulted.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Tuple

import numpy as np

from tsc.charts.laguerre_basis import xi_moment


# ============================================================================
# Section 1 - Entropy-density / number-density ratio
# ============================================================================

def entropy_over_number(
    xi: int, eta: float = 0.0,
) -> float:
    """s/n for an exponential-family distribution.

    For the generic family f = Φ(x; ξ, η), the entropy density per particle
    depends only on dimensionless combinations of the I_n moments at a given
    (ξ, η). The standard Gibbs form yields

        s/n = (1 + β·⟨E⟩/n_density) − β·μ = (I_3 + I_2 - η I_2) / I_2
            = I_3/I_2 + 1 - η

    in units where β = 1 (see Paper I §II for the exponential-family
    normalization). For Bose-Einstein (ξ=+1) and Fermi-Dirac (ξ=−1) at η=0,
    s/n is a pure function of ξ through I_3/I_2.

    Parameters
    ----------
    xi : int
        Statistics ∈ {-1, 0, +1}.
    eta : float
        Fugacity. Must be ≤ 0 for BE (ξ = +1).

    Returns
    -------
    float
        s/n (dimensionless).
    """
    if xi not in (-1, 0, +1):
        raise ValueError(f"xi must be in {{-1, 0, +1}}, got {xi}")
    if xi == +1 and eta > 1e-15:
        raise ValueError(
            f"BE requires eta ≤ 0, got eta={eta}"
        )
    I_2 = xi_moment(2, xi, eta)
    I_3 = xi_moment(3, xi, eta)
    if I_2 <= 0:
        raise ValueError(
            f"I_2 ≤ 0 at ξ={xi}, η={eta}; cannot form s/n"
        )
    return I_3 / I_2 + 1.0 - eta


def entropy_over_energy(
    xi: int, eta: float = 0.0,
) -> float:
    """s/ρ = (1 - η·I_2/I_3) + I_2/I_3 energy-density normalized entropy.

    Complementary to `entropy_over_number`, using I_3 (energy density proxy)
    in the denominator. At η = 0 this reduces to 1 + I_2/I_3.
    """
    if xi not in (-1, 0, +1):
        raise ValueError(f"xi must be in {{-1, 0, +1}}, got {xi}")
    I_2 = xi_moment(2, xi, eta)
    I_3 = xi_moment(3, xi, eta)
    if I_3 <= 0:
        raise ValueError(
            f"I_3 ≤ 0 at ξ={xi}, η={eta}; cannot form s/ρ"
        )
    return 1.0 - eta * I_2 / I_3 + I_2 / I_3


# ============================================================================
# Section 2 - Gram-matrix admissibility invariants
# ============================================================================

@dataclass(frozen=True)
class GramAdmissibility:
    """Eigenvalue-based admissibility invariants for a Gram matrix.

    Attributes
    ----------
    lambda_min : float
        Smallest eigenvalue. Must be > 0 for admissibility.
    lambda_max : float
        Largest eigenvalue.
    kappa : float
        Condition number = λ_max / λ_min.
    is_admissible : bool
        True iff λ_min > threshold.
    """
    lambda_min: float
    lambda_max: float
    kappa: float
    is_admissible: bool


ADMISSIBILITY_THRESHOLD: float = 1e-14
"""λ_min > this for the Gram to pass admissibility."""


def gram_admissibility(
    gram: np.ndarray,
    threshold: float = ADMISSIBILITY_THRESHOLD,
) -> GramAdmissibility:
    """Compute eigenvalue-based invariants of a Gram matrix.

    Parameters
    ----------
    gram : np.ndarray, shape (n, n)
        Symmetric Gram matrix. The input is symmetrized before eigenvalue
        computation to guard against numerical asymmetry.
    threshold : float
        λ_min must exceed this for admissibility.

    Returns
    -------
    GramAdmissibility
    """
    if gram.ndim != 2 or gram.shape[0] != gram.shape[1]:
        raise ValueError(
            f"gram must be square 2D, got shape {gram.shape}"
        )
    # Symmetrize to guard against numerical drift
    sym = 0.5 * (gram + gram.T)
    eigs = np.linalg.eigvalsh(sym)
    lambda_min = float(eigs.min())
    lambda_max = float(eigs.max())
    kappa = float(lambda_max / lambda_min) if lambda_min > 0 else float("inf")
    is_admissible = bool(lambda_min > threshold)
    return GramAdmissibility(
        lambda_min=lambda_min,
        lambda_max=lambda_max,
        kappa=kappa,
        is_admissible=is_admissible,
    )


# ============================================================================
# Section 3 - MB η-independence check
# ============================================================================

@dataclass(frozen=True)
class MBIndependenceResult:
    """η-independence diagnostic for MB moment ratios.

    For MB (ξ = 0), I_n(η) = e^η · n!, so any ratio I_n₁/I_n₂ is exactly
    η-independent (the e^η factor cancels).
    """
    n_pairs: tuple
    eta_values: tuple
    observed_ratios: np.ndarray   # shape (n_pairs, n_etas)
    max_deviation_across_eta: float
    all_within_tolerance: bool


def verify_mb_eta_independence(
    n_pairs: List[Tuple[int, int]],
    eta_values: List[float],
    tolerance: float = 1e-12,
) -> MBIndependenceResult:
    """Check that MB moment ratios I_{n₁}/I_{n₂} are η-independent.

    Parameters
    ----------
    n_pairs : list of (n1, n2) integer tuples
        Pairs of moment orders to form ratios for.
    eta_values : list of float
        η values to evaluate. Can include ≤ 0 (MB accepts any η).
    tolerance : float
        Max absolute deviation of ratio from its η=0 value allowed.

    Returns
    -------
    MBIndependenceResult
    """
    if not n_pairs:
        raise ValueError("n_pairs must be non-empty")
    if not eta_values:
        raise ValueError("eta_values must be non-empty")

    n_p = len(n_pairs)
    n_e = len(eta_values)
    ratios = np.zeros((n_p, n_e))
    for i, (n1, n2) in enumerate(n_pairs):
        for j, eta in enumerate(eta_values):
            I1 = xi_moment(n1, 0, eta)
            I2 = xi_moment(n2, 0, eta)
            ratios[i, j] = I1 / I2

    # For each pair, deviation across all η values
    max_dev = 0.0
    for i in range(n_p):
        ref = ratios[i, 0]
        dev = float(np.max(np.abs(ratios[i, :] - ref)))
        if dev > max_dev:
            max_dev = dev

    return MBIndependenceResult(
        n_pairs=tuple(n_pairs),
        eta_values=tuple(eta_values),
        observed_ratios=ratios,
        max_deviation_across_eta=max_dev,
        all_within_tolerance=bool(max_dev < tolerance),
    )
