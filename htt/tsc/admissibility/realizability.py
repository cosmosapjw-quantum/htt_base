"""
bass/teff/realizability.py  (Week 2 Day 5)
============================================

Paper I realizability constraints (Prop 14/15 + ch03 Definition 3.1/3.2).

Three layers of admissibility
-----------------------------
Layer 1 — **Field-level admissibility**:
  Θ(ê) > 0 for all directions (positivity of the angular temperature field).
  For BE (ξ = +1), additionally η(ê) ≤ 0 (to ensure f ≥ 0 everywhere).
  This is the bare admissibility of the distribution function.

Layer 2 — **Identifiability (Gram positive-definiteness)**:
  For two-field ansatz f = Φ_ξ(x/Θ − η), the ability to uniquely recover
  (Θ, η) from the moment sector {ρ, n} (energy + number) requires the
  Fisher-information-like Gram matrix G(Θ, η) to be strictly positive
  definite at the operating point. Degeneracy signals a loss of
  identifiability — often encountered at large FD degeneracy (η >> 1).

Layer 3 — **Moment-space admissibility domain**:
  Given observed multipoles (T_0, T_1, T_2, ...), can one find a valid
  field (Θ(ê), η(ê)) mapping to these multipoles via F? Answer yes iff
  certain inequalities on T_ℓ/T_0 hold. For axisymmetric Θ > 0, the
  necessary conditions include |T_1/T_0| bounded by (n+1) × Θ_max / Θ_min
  relations. This module provides checkable diagnostic bounds, not tight
  necessary-and-sufficient conditions (the full characterization is
  ongoing research; see Paper III-A tangency survival).

Known-limit recovery
--------------------
The DOC-01 admissibility contract requires:
  - FLRW limit (σ = 0, tilt = 0): realizability trivially holds
  - Small-shear regime: admissibility persists for bounded |Θ_ℓ/Θ_0|
  - v = 0 boost: realizability preserved (identity)
  - v ≠ 0 one-field boost: Paper I Thm 3 ensures admissibility preserved
    exactly (no new μ-defect)

Scope clarification
-------------------
Paper I Prop 14, 15 cover *distribution-function-level* admissibility.
Full *moment-space* admissibility is a projection of this onto finite
multipole spaces. We implement both:
  - `check_field_admissible`: Layer 1 (reuses Day 2 primitives)
  - `check_gram_positive_definite`: Layer 2 (Gram of tangent basis must be PD)
  - `check_moment_admissible`: Layer 3 (heuristic diagnostic bounds)
  - `assess_realizability`: unified audit returning all three

References
----------
  Paper I (Park-Cheoun-Park 2026) Prop 14, 15
  ch03_framework.tex §sec:species-teff (admissibility constraints)
  DOC-01 §XI (validation contract, admissibility consistency)
  consolidated_research_surveys.md (Paper III-A Gram-Hessian identity)
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple
import math

import numpy as np

from tsc.charts.forward_F_to_T import (
    AxisymmetricField,
    check_theta_positive, check_be_admissibility,
    isotropic_theta, dipole_theta, quadrupole_theta,
    axisymmetric_F,
)
from tsc.diagnostics.tangency import (
    TangentKind, tangent_basis, build_gram_matrix,
)


# ═══════════════════════════════════════════════════════════════
# §1 — Verdict enum
# ═══════════════════════════════════════════════════════════════

class AdmissibilityVerdict(Enum):
    """Outcome of a realizability check."""
    ADMISSIBLE = "admissible"           # All three layers pass
    FIELD_VIOLATION = "field_violation"  # Layer 1 fails (Θ ≤ 0 or BE η > 0)
    GRAM_DEGENERATE = "gram_degenerate"  # Layer 2 fails (identifiability lost)
    MOMENT_OUT_OF_DOMAIN = "moment_out_of_domain"  # Layer 3 fails (T_ℓ bounds)
    MULTIPLE_VIOLATIONS = "multiple_violations"


# ═══════════════════════════════════════════════════════════════
# §2 — Layer 1: Field-level admissibility
# ═══════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class FieldAdmissibilityResult:
    """Per-direction Θ and η admissibility outcome."""
    theta_positive: bool
    theta_min: float                  # min Θ(μ) over [-1, 1]
    theta_max: float                  # max Θ(μ) over [-1, 1]
    be_admissible: bool               # η ≤ 0 everywhere (or ξ ≠ +1)
    eta_max: Optional[float]          # max η(μ); None if η not provided

    @property
    def is_admissible(self) -> bool:
        return self.theta_positive and self.be_admissible


def check_field_admissible(
    Theta: AxisymmetricField,
    xi: int,
    eta: Optional[AxisymmetricField] = None,
    n_check: int = 400,
) -> FieldAdmissibilityResult:
    """Layer 1: verify field-level admissibility on [-1, 1].

    Checks:
      Θ(μ) > 0 at all sampled μ (DENSE positivity).
      η(μ) ≤ 0 at all sampled μ if ξ = +1 (BE).

    Parameters
    ----------
    Theta : AxisymmetricField
        Angular temperature field.
    xi : int
        Statistics ∈ {-1, 0, +1}.
    eta : AxisymmetricField, optional
        Angular fugacity field. If None, η ≡ 0 (one-field).
    n_check : int, optional
        Sampling density on [-1, 1].

    Returns
    -------
    FieldAdmissibilityResult
    """
    mu = np.linspace(-1.0, 1.0, n_check)
    theta_vals = Theta.evaluate(mu)
    theta_min = float(np.min(theta_vals))
    theta_max = float(np.max(theta_vals))
    theta_positive = theta_min > 0

    if eta is not None:
        eta_vals = eta.evaluate(mu)
        eta_max = float(np.max(eta_vals))
    else:
        eta_max = None

    if xi == +1:
        be_admissible = (eta_max is None) or (eta_max <= 1e-15)
    else:
        be_admissible = True

    return FieldAdmissibilityResult(
        theta_positive=theta_positive,
        theta_min=theta_min,
        theta_max=theta_max,
        be_admissible=be_admissible,
        eta_max=eta_max,
    )


# ═══════════════════════════════════════════════════════════════
# §3 — Layer 2: Gram positive-definiteness (identifiability)
# ═══════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class GramPositiveDefiniteResult:
    """Outcome of the Gram positive-definiteness check."""
    kind: TangentKind
    eigenvalues: np.ndarray           # ascending eigvals of Gram matrix
    min_eigenvalue: float
    condition_number: float           # λ_max / λ_min
    is_positive_definite: bool        # all eigvals > threshold


def check_gram_positive_definite(
    kind: TangentKind,
    xi: int, eta: float = 0.0,
    alpha: float = 2.0,
    eig_threshold: float = 1e-12,
) -> GramPositiveDefiniteResult:
    """Layer 2: verify the tangent-space Gram matrix is strictly positive definite.

    For Paper I one-field (ONE_FIELD, span{x}), the Gram matrix is 1×1 with
    entry ⟨x, x⟩_{*,s} = I_4(ξ, η) × (related measure). This is always > 0
    for admissible η — the check is a sanity assertion.

    For two-field (TWO_FIELD, span{1, x}), the 2×2 Gram must be strictly PD.
    At large FD degeneracy (η ≫ 1), the Fisher-information metric becomes
    degenerate and the smaller eigenvalue shrinks toward zero. The
    `min_eigenvalue < eig_threshold` signals identifiability loss.

    Parameters
    ----------
    kind : TangentKind
        ONE_FIELD or TWO_FIELD.
    xi : int
        Statistics.
    eta : float
        Fugacity operating point.
    alpha : float
        Laguerre weight parameter.
    eig_threshold : float
        Minimum acceptable eigenvalue (below which identifiability is lost).
    """
    basis = tangent_basis(kind)
    G = build_gram_matrix(basis, xi=xi, eta=eta, alpha=alpha)
    eigs = np.sort(np.linalg.eigvalsh(G))
    min_eig = float(eigs[0])
    max_eig = float(eigs[-1])
    cond = max_eig / min_eig if min_eig > 0 else math.inf
    is_pd = min_eig > eig_threshold
    return GramPositiveDefiniteResult(
        kind=kind,
        eigenvalues=eigs,
        min_eigenvalue=min_eig,
        condition_number=cond,
        is_positive_definite=is_pd,
    )


# ═══════════════════════════════════════════════════════════════
# §4 — Layer 3: Moment-space admissibility bounds
# ═══════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class MomentAdmissibilityResult:
    """Moment-space admissibility diagnostic outcome."""
    T_0: float
    T_0_positive: bool                # T_0 > 0 (energy density nonneg)
    ratios: np.ndarray                # [T_1/T_0, T_2/T_0, ...]
    max_abs_ratio: float              # max |T_ℓ/T_0| over ℓ ≥ 1
    within_heuristic_bound: bool      # max_abs_ratio < bound

    @property
    def is_admissible(self) -> bool:
        return self.T_0_positive and self.within_heuristic_bound


def check_moment_admissible(
    T_ell: np.ndarray,
    heuristic_bound: float = 1.0,
) -> MomentAdmissibilityResult:
    """Layer 3: moment-space admissibility via diagnostic bounds.

    Heuristic checks:
      - T_0 > 0 (nonnegative energy density)
      - |T_ℓ / T_0| < heuristic_bound for ℓ ≥ 1

    The `heuristic_bound = 1` default corresponds to roughly isotropic +
    moderate perturbations. For a strictly axisymmetric Θ(μ) > 0 field
    with Θ_ℓ/Θ_0 ratios of order |Θ_ℓ/Θ_0|, the induced T_ℓ/T_0 scales
    as (n+1) × Θ_ℓ/Θ_0 at leading order (Day 2 linear response). Values
    approaching the heuristic bound indicate near-zero Θ at some μ.

    Parameters
    ----------
    T_ell : ndarray shape (L+1,)
        Multipole output from axisymmetric_F.
    heuristic_bound : float, optional
        Upper bound on |T_ℓ/T_0| for ℓ ≥ 1.

    Returns
    -------
    MomentAdmissibilityResult
    """
    T_ell = np.asarray(T_ell, dtype=float)
    T_0 = float(T_ell[0])
    T_0_positive = T_0 > 0

    if len(T_ell) > 1 and T_0_positive:
        ratios = T_ell[1:] / T_0
        max_abs_ratio = float(np.max(np.abs(ratios)))
        within_bound = max_abs_ratio < heuristic_bound
    else:
        ratios = np.array([])
        max_abs_ratio = 0.0
        within_bound = True

    return MomentAdmissibilityResult(
        T_0=T_0,
        T_0_positive=T_0_positive,
        ratios=ratios,
        max_abs_ratio=max_abs_ratio,
        within_heuristic_bound=within_bound,
    )


# ═══════════════════════════════════════════════════════════════
# §5 — Unified realizability audit
# ═══════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class RealizabilityAudit:
    """Combined outcome of all three admissibility layers."""
    verdict: AdmissibilityVerdict
    field_result: FieldAdmissibilityResult
    gram_result: GramPositiveDefiniteResult
    moment_result: MomentAdmissibilityResult
    xi: int

    @property
    def is_admissible(self) -> bool:
        return self.verdict == AdmissibilityVerdict.ADMISSIBLE


def assess_realizability(
    Theta: AxisymmetricField,
    xi: int,
    eta: Optional[AxisymmetricField] = None,
    kind: TangentKind = TangentKind.ONE_FIELD,
    eta_operating_point: float = 0.0,
    L_out: int = 3,
    heuristic_bound: float = 1.0,
) -> RealizabilityAudit:
    """Run all three admissibility layers and return a unified audit.

    Parameters
    ----------
    Theta : AxisymmetricField
    xi : int
    eta : AxisymmetricField, optional
    kind : TangentKind
        ONE_FIELD or TWO_FIELD (decides Gram matrix size).
    eta_operating_point : float
        Scalar η at which Gram matrix is evaluated (0 for one-field; for
        two-field with η(μ), we use the monopole of η).
    L_out : int
        Highest multipole for moment admissibility.
    heuristic_bound : float
        Threshold on |T_ℓ/T_0|.
    """
    # Layer 1: field admissibility
    field_r = check_field_admissible(Theta, xi, eta)

    # Layer 2: Gram positive-definite
    gram_r = check_gram_positive_definite(kind, xi, eta=eta_operating_point)

    # Layer 3: moment admissibility (only if field admissible — else skip
    # F evaluation which may itself raise)
    if field_r.is_admissible:
        res_F = axisymmetric_F(
            xi, Theta, eta=eta, L_out=L_out,
            check_admissibility=False,  # already checked in Layer 1
        )
        moment_r = check_moment_admissible(res_F.T_ell, heuristic_bound)
    else:
        # Skip moment-level check; report conservatively as not applicable
        moment_r = MomentAdmissibilityResult(
            T_0=math.nan, T_0_positive=False, ratios=np.array([]),
            max_abs_ratio=0.0, within_heuristic_bound=False,
        )

    # Verdict aggregation
    violations = []
    if not field_r.is_admissible:
        violations.append(AdmissibilityVerdict.FIELD_VIOLATION)
    if not gram_r.is_positive_definite:
        violations.append(AdmissibilityVerdict.GRAM_DEGENERATE)
    if field_r.is_admissible and not moment_r.is_admissible:
        violations.append(AdmissibilityVerdict.MOMENT_OUT_OF_DOMAIN)

    if len(violations) == 0:
        verdict = AdmissibilityVerdict.ADMISSIBLE
    elif len(violations) == 1:
        verdict = violations[0]
    else:
        verdict = AdmissibilityVerdict.MULTIPLE_VIOLATIONS

    return RealizabilityAudit(
        verdict=verdict,
        field_result=field_r,
        gram_result=gram_r,
        moment_result=moment_r,
        xi=xi,
    )


# ═══════════════════════════════════════════════════════════════
# §6 — Known-limit recovery verifications
# ═══════════════════════════════════════════════════════════════

def verify_flrw_limit_admissible(xi: int = 0) -> bool:
    """FLRW limit: Θ = const = 1, η = 0 (one-field). Must be admissible."""
    Theta = isotropic_theta(1.0)
    audit = assess_realizability(Theta, xi=xi, kind=TangentKind.ONE_FIELD)
    return audit.is_admissible


def verify_small_shear_admissible(
    xi: int = 0, Theta_1: float = 0.05,
) -> bool:
    """Small shear (Θ_1 small): Θ = 1 + Θ_1 × P_1(μ), still > 0 everywhere."""
    Theta = dipole_theta(1.0, Theta_1)
    audit = assess_realizability(Theta, xi=xi, kind=TangentKind.ONE_FIELD)
    return audit.is_admissible


def verify_large_dipole_breaks_positivity() -> bool:
    """Θ = 1 + 1.2 × P_1(μ) dips below 0 at μ = -1. Must fail Layer 1."""
    Theta = dipole_theta(1.0, 1.2)
    audit = assess_realizability(Theta, xi=0, kind=TangentKind.ONE_FIELD)
    return (audit.verdict == AdmissibilityVerdict.FIELD_VIOLATION
            or audit.verdict == AdmissibilityVerdict.MULTIPLE_VIOLATIONS)
