"""TSUM: exact two-temperature fingerprint sum bound R_3 + R_5 >= 2 (v9,
REV-R172; promotion of the v8 numeric-only certificate flagged by the
2026-07-10 re-review as a theorem candidate).

Setup (registered Teff lane, htt/teff/representative.py): the two-temperature
ratios are R_p(s) = a(s)^p [(1+s)^p + (1-s)^p] / 2 with
a(s) = (1 + 6 s^2 + s^4)^{-1/4}. Writing mu_p(s) = [(1+s)^p + (1-s)^p]/2,
the p=4 anchor gives a(s)^{-4} = mu_4(s), hence EXACTLY

    R_p = mu_p / mu_4^{p/4},   so   R_3 R_5 = mu_3 mu_5 / mu_4^2 .

Theorem (proved symbolically here, exact factorization):

    mu_3 mu_5 - mu_4^2 = s^2 (1 - s^2)^3        (identically in s)

so on 0 <= s <= 1:  R_3 R_5 = 1 + s^2 (1-s^2)^3 / mu_4^2 >= 1, and by AM-GM

    R_3 + R_5 >= 2 sqrt(R_3 R_5) >= 2,     equality iff s = 0.

(The product bound is the Lyapunov moment log-convexity mu_4^2 <= mu_3 mu_5
for the symmetric two-point law on {1-s, 1+s}, here in explicit nonnegative
product form rather than as an inequality.) The AM-GM equality condition
R_3 = R_5 also holds at s = 0 (both equal 1), so the combined equality case
is exactly s = 0.

Claim discipline: exact symbolic algebra on the registered representative-
theory ratios at tier diagnostic_only; no data claim, no signal-discovery
claim, no probabilistic-inference claim about the sky.
"""
from __future__ import annotations

import numpy as np
import sympy as sp

from htt.teff.representative import two_temperature_ratio

__all__ = [
    "mu_poly",
    "product_factorization",
    "sum_bound_symbolic",
    "representative_consistency",
    "fingerprint_sum_theorem_seal",
]


def mu_poly(p: int, s: sp.Symbol) -> sp.Expr:
    """mu_p(s) = [(1+s)^p + (1-s)^p]/2, expanded."""
    return sp.expand(((1 + s) ** p + (1 - s) ** p) / 2)


def product_factorization() -> dict:
    """Exact factorization mu_3 mu_5 - mu_4^2 = s^2 (1 - s^2)^3."""
    s = sp.symbols("s", nonnegative=True)
    mu3, mu4, mu5 = mu_poly(3, s), mu_poly(4, s), mu_poly(5, s)
    diff = sp.expand(mu3 * mu5 - mu4 ** 2)
    target = sp.expand(s ** 2 * (1 - s ** 2) ** 3)
    return {
        "mu3": str(mu3), "mu4": str(mu4), "mu5": str(mu5),
        "difference_expanded": str(diff),
        "factorization_exact": bool(sp.simplify(diff - target) == 0),
        "factored_form": "s**2*(1 - s**2)**3",
        "nonnegative_on_unit_interval": True,  # product of even powers on [0,1]
    }


def sum_bound_symbolic() -> dict:
    """R_3 R_5 = 1 + s^2(1-s^2)^3/mu_4^2 >= 1 and R_3 + R_5 >= 2 via AM-GM;
    equality iff s = 0 (both steps closed symbolically)."""
    s = sp.symbols("s", nonnegative=True)
    mu3, mu4, mu5 = mu_poly(3, s), mu_poly(4, s), mu_poly(5, s)
    r3 = mu3 / mu4 ** sp.Rational(3, 4)
    r5 = mu5 / mu4 ** sp.Rational(5, 4)
    product_minus_one = sp.simplify(r3 * r5 - 1 - s ** 2 * (1 - s ** 2) ** 3 / mu4 ** 2)
    # AM-GM residual: (sqrt(R3) - sqrt(R5))^2 >= 0 gives R3+R5 >= 2 sqrt(R3 R5)
    amgm_identity = sp.simplify(
        (sp.sqrt(r3) - sp.sqrt(r5)) ** 2 - (r3 + r5 - 2 * sp.sqrt(r3 * r5)))
    at_zero = (r3.subs(s, 0), r5.subs(s, 0))
    # equality analysis: R3 R5 = 1 iff s^2 (1-s^2)^3 = 0 iff s in {0, 1};
    # at s=1 the sum is R3+R5 = mu3/mu4^(3/4) + mu5/mu4^(5/4) with mu_p(1)=2^(p-1)
    sum_at_one = sp.nsimplify(r3.subs(s, 1) + r5.subs(s, 1))
    return {
        "R4_anchor_gives_Rp_mu_form": True,
        "product_identity_holds": bool(product_minus_one == 0),
        "amgm_identity_holds": bool(amgm_identity == 0),
        "both_ratios_one_at_s0": at_zero == (sp.Integer(1), sp.Integer(1)),
        "sum_at_s1": str(sum_at_one),
        "sum_at_s1_exceeds_two": bool(sp.N(sum_at_one) > 2),
        "equality_iff_s0": "R3*R5 = 1 iff s in {0,1}; at s=1 the sum still "
                           "exceeds 2 (AM-GM strict since R3 != R5 there), "
                           "so R3+R5 = 2 iff s = 0",
    }


def representative_consistency(n_grid: int = 41) -> dict:
    """Cross-check against the registered two_temperature_ratio expressions:
    the mu-form equals the registered R_p symbolically, and the numeric
    minimum of R_3 + R_5 - 2 over a grid is nonnegative with zero only at
    s = 0."""
    s = sp.symbols("s", nonnegative=True)
    checks = {}
    for p in (3, 4, 5):
        expr, svar = two_temperature_ratio(p)
        mu4 = mu_poly(4, s)
        mu_form = mu_poly(p, s) / mu4 ** sp.Rational(p, 4)
        checks[f"registered_R{p}_equals_mu_form"] = bool(
            sp.simplify(expr.subs(svar, s) - mu_form) == 0)
    expr3, sv3 = two_temperature_ratio(3)
    expr5, sv5 = two_temperature_ratio(5)
    f = sp.lambdify(sv3, expr3.subs(sv3, sv3) + expr5.subs(sv5, sv3) - 2,
                    "numpy")
    grid = np.linspace(0.0, 0.999, n_grid)
    vals = np.asarray(f(grid), dtype=float)
    checks["numeric_min_nonnegative"] = bool(vals.min() >= -1e-15)
    checks["zero_only_at_s0"] = bool(vals[0] < 1e-12 and (vals[1:] > 0).all())
    return checks


def fingerprint_sum_theorem_seal() -> dict:
    """Fail-closed TSUM seal (registry id TSUM; rendered by the v9 report)."""
    fact = product_factorization()
    sym = sum_bound_symbolic()
    rep = representative_consistency()
    ok = (fact["factorization_exact"]
          and sym["product_identity_holds"] and sym["amgm_identity_holds"]
          and sym["both_ratios_one_at_s0"] and sym["sum_at_s1_exceeds_two"]
          and all(rep.values()))
    return {
        "seal": "egs3.fingerprint_sum_theorem",
        "theorem_id": "TSUM",
        "status": "PASS" if ok else "FAIL",
        "statement": "R_3(s) + R_5(s) >= 2 on 0 <= s <= 1 with equality iff "
                     "s = 0; proof: mu_3 mu_5 - mu_4^2 = s^2 (1-s^2)^3 "
                     "exactly, so R_3 R_5 >= 1, then AM-GM",
        "promotes": "the v8 numeric-only R_3 + R_5 >= 2 certificate "
                    "(2026-07-10 re-review theorem candidate)",
        "product_factorization": fact,
        "sum_bound_symbolic": sym,
        "representative_consistency": rep,
        "claim_boundary": "exact symbolic algebra on the registered "
                          "representative-theory ratios; diagnostic_only; no "
                          "data claim, no probabilistic-inference claim",
    }
