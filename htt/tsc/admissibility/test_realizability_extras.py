"""Supplementary admissibility tests (TSC-01, INDEPENDENT_TRACKS_PLAN.md §2.7).

The main `test_realizability.py` already covers the bulk of Paper I Prop 14/15
checks (40 cases, all passing). This file fills in the three §2.7 items not
explicitly covered:

  1. cross-check between `check_field_admissible` and an independent
     Lebedev-quadrature probe of Θ(μ) > 0 on S²;
  2. simplex / probability-measure positivity edge cases;
  3. degenerate mass configurations (all-mass-in-one-moment).
"""
from __future__ import annotations

import math
import numpy as np
import pytest

from tsc.admissibility.realizability import (
    AdmissibilityVerdict,
    check_field_admissible,
    check_moment_admissible,
    assess_realizability,
)
from tsc.charts.forward_F_to_T import (
    AxisymmetricField, isotropic_theta, dipole_theta, quadrupole_theta,
)
from tsc.diagnostics.spherical_quadrature import (
    lebedev_quadrature, integrate_on_sphere,
)
from tsc.diagnostics.tangency import TangentKind


# ---------------------------------------------------------------------------
# §1 — Cross-check with spherical quadrature
# ---------------------------------------------------------------------------

def _theta_on_unitvec(Theta: AxisymmetricField):
    """Wrap an axisymmetric Θ(μ) for use with Lebedev quadrature (μ = n_z)."""
    def f(n_hat: np.ndarray) -> float:
        mu = float(n_hat[2])
        return float(Theta.evaluate(np.array([mu]))[0])
    return f


class TestSphericalQuadratureCrossCheck:
    def test_isotropic_admissible_consistent_with_quadrature(self):
        """check_field_admissible agrees with Lebedev min(Θ) probe."""
        Theta = isotropic_theta(1.0)
        r = check_field_admissible(Theta, xi=0)
        quad = lebedev_quadrature(order=7)
        vals = np.array([_theta_on_unitvec(Theta)(n) for n in quad.nodes])
        assert r.theta_positive == (vals.min() > 0)

    def test_large_dipole_caught_by_both(self):
        """Θ = 1 + 1.2 P_1 dips below 0; both probes concur."""
        Theta = dipole_theta(1.0, 1.2)
        r = check_field_admissible(Theta, xi=0)
        quad = lebedev_quadrature(order=7)
        vals = np.array([_theta_on_unitvec(Theta)(n) for n in quad.nodes])
        assert not r.theta_positive
        assert vals.min() < 0

    def test_quadrature_average_matches_monopole(self):
        """For admissible Θ, Lebedev ⟨Θ⟩ ≈ Θ_0 (monopole coefficient)."""
        Theta = dipole_theta(1.0, 0.3)  # admissible (Θ_min = 0.7)
        quad = lebedev_quadrature(order=7)
        avg = integrate_on_sphere(_theta_on_unitvec(Theta), quad)
        assert math.isclose(avg, 1.0, abs_tol=1e-6)


# ---------------------------------------------------------------------------
# §2 — Simplex / probability-measure positivity
# ---------------------------------------------------------------------------

class TestSimplexPositivity:
    def test_unit_mass_concentrated_on_one_moment_admissible_if_T0(self):
        """T_ell = δ_{ℓ,0} × 1 — pure monopole, trivially admissible."""
        T = np.array([1.0, 0.0, 0.0, 0.0])
        r = check_moment_admissible(T)
        assert r.is_admissible
        assert r.max_abs_ratio == 0.0

    def test_zero_mass_fails_T0_positivity(self):
        """T_0 = 0 marks vanishing energy density → fails."""
        T = np.array([0.0, 0.0, 0.0])
        r = check_moment_admissible(T)
        assert not r.T_0_positive

    def test_degenerate_T0_equal_T1_at_heuristic_boundary(self):
        """|T_1/T_0| = 1 sits on the heuristic bound (strict '<' → reject)."""
        T = np.array([1.0, 1.0])
        r = check_moment_admissible(T, heuristic_bound=1.0)
        assert not r.within_heuristic_bound  # strict inequality

    def test_heuristic_bound_relaxation_admits_boundary(self):
        T = np.array([1.0, 1.0])
        r = check_moment_admissible(T, heuristic_bound=1.0 + 1e-12)
        assert r.within_heuristic_bound


# ---------------------------------------------------------------------------
# §3 — Degenerate configurations through assess_realizability
# ---------------------------------------------------------------------------

class TestDegenerateConfigurations:
    def test_pure_quadrupole_admissible_when_bounded(self):
        """Θ = 1 + 0.1 P_2(μ) — small enough that both layers pass."""
        audit = assess_realizability(
            quadrupole_theta(1.0, 0.1), xi=0, kind=TangentKind.ONE_FIELD,
        )
        assert audit.is_admissible

    def test_pure_quadrupole_fails_when_crosses_zero(self):
        """Θ = 1 + 2 P_2(μ); Θ(0) = 1 − 1 = 0 (hits zero) → fails."""
        audit = assess_realizability(
            quadrupole_theta(1.0, 2.0), xi=0, kind=TangentKind.ONE_FIELD,
        )
        assert not audit.is_admissible

    def test_verdict_is_enum_instance(self):
        """Type-safety: verdict must be an AdmissibilityVerdict member."""
        audit = assess_realizability(
            isotropic_theta(1.0), xi=0, kind=TangentKind.ONE_FIELD,
        )
        assert isinstance(audit.verdict, AdmissibilityVerdict)
