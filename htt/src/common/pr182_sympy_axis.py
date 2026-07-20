"""PR-182 SymPy axis: solver-free parity identities (exact rationals).

Verifies, over exact rationals/symbols only:

I1  Reflection parity on the (E, B) doublet is an involution, and an
    axisymmetric mirror-fixed source has an exactly zero B component
    (the solution space of v = P v in the m=0 sector is spanned by the
    pure-E vector).
I2  Reflection R = diag(1, 1, -1) on (T, E, B) flips TB and EB and
    preserves TT/EE/BB/TE (symbolically and on the rational fixture
    TB = 3/7, EB = -2/5).
I3  The Bianchi VII_h structure tensor n = diag(0, 1, 1) with vector
    a = (1/2, 0, 0) satisfies a.n = 0, and the orientation-reversing
    transform Lambda = diag(-1, 1, 1) (det = -1) maps the density
    n -> det(Lambda) * Lambda n Lambda^T = -n exactly, with a.n' = 0
    preserved: the handedness sign is orientation-odd at the level of
    the structure constants.
I4  The boost kernel 1/(gamma (1 - beta mu)) expanded to O(beta^3) has
    coefficients that are polynomials in mu = cos(theta) ONLY
    (axisymmetric about the boost axis), with exact coefficient lists
    [1], [0, 1], [-1/2, 0, 1], [0, -1/2, 0, 1].

No data enters; no family is adjudicated. Attribution: the parity split
(axisymmetric -> E only; helical -> parity-odd TB/EB) is CONFIRMATORY of
Pontzen & Challinor 2007; this axis only re-verifies exact mechanics.
"""

from __future__ import annotations

import json

import sympy as sp


def check_parity_involution_and_axisym_b_zero() -> dict:
    parity = sp.Matrix([[1, 0], [0, -1]])  # reflection on (E, B) at m=0
    involution = parity * parity == sp.eye(2)
    fixed = (parity - sp.eye(2)).nullspace()
    dim = len(fixed)
    basis = fixed[0] if fixed else None
    b_zero = basis is not None and basis[1] == 0 and basis[0] != 0
    return {
        "parity_involution_exact": bool(involution),
        "axisymmetric_source_forces_B_zero": bool(dim == 1 and b_zero),
        "fixed_space_dim": str(dim),
    }


def check_reflection_tb_eb() -> dict:
    tt, ee, bb, te, tb, eb = sp.symbols("tt ee bb te tb eb")
    m = sp.Matrix([[tt, te, tb], [te, ee, eb], [tb, eb, bb]])
    r = sp.diag(1, 1, -1)
    mp = r * m * r
    symbolic = (
        sp.simplify(mp[0, 2] + tb) == 0
        and sp.simplify(mp[1, 2] + eb) == 0
        and sp.simplify(mp[0, 0] - tt) == 0
        and sp.simplify(mp[1, 1] - ee) == 0
        and sp.simplify(mp[2, 2] - bb) == 0
        and sp.simplify(mp[0, 1] - te) == 0
    )
    fixture = m.subs(
        {tt: 1, ee: sp.Rational(2, 3), bb: sp.Rational(1, 9),
         te: sp.Rational(1, 4), tb: sp.Rational(3, 7),
         eb: sp.Rational(-2, 5)}
    )
    fixture_p = r * fixture * r
    fixture_ok = (
        fixture_p[0, 2] == sp.Rational(-3, 7)
        and fixture_p[1, 2] == sp.Rational(2, 5)
        and fixture_p[0, 0] == 1
        and fixture_p[1, 1] == sp.Rational(2, 3)
        and fixture_p[2, 2] == sp.Rational(1, 9)
        and fixture_p[0, 1] == sp.Rational(1, 4)
    )
    return {
        "reflection_flips_TB_EB_fixture": bool(symbolic and fixture_ok),
        "reflection_preserves_TT_EE_BB_TE_fixture": bool(fixture_ok),
        "fixture_TB_flip": f"{sp.Rational(3, 7)}->{fixture_p[0, 2]}",
        "fixture_EB_flip": f"{sp.Rational(-2, 5)}->{fixture_p[1, 2]}",
    }


def check_vii_h_handedness() -> dict:
    n = sp.diag(0, 1, 1)
    a = sp.Matrix([[sp.Rational(1, 2), 0, 0]])
    lam = sp.diag(-1, 1, 1)
    n_prime = lam.det() * lam * n * lam.T
    flips = n_prime == -n
    constraint_before = (a * n) == sp.zeros(1, 3)
    constraint_after = (a * n_prime) == sp.zeros(1, 3)
    return {
        "vii_h_improper_transform_flips_n_sign": bool(flips),
        "vii_h_vector_constraint_holds_both_orientations": bool(
            constraint_before and constraint_after
        ),
        "n_prime_diagonal": str([n_prime[0, 0], n_prime[1, 1], n_prime[2, 2]]),
    }


def check_boost_kernel() -> dict:
    beta, mu = sp.symbols("beta mu")
    kernel = sp.sqrt(1 - beta**2) / (1 - beta * mu)
    series = sp.series(kernel, beta, 0, 4).removeO().expand()
    expected = {
        0: [sp.Integer(1)],
        1: [sp.Integer(0), sp.Integer(1)],
        2: [sp.Rational(-1, 2), sp.Integer(0), sp.Integer(1)],
        3: [sp.Integer(0), sp.Rational(-1, 2), sp.Integer(0), sp.Integer(1)],
    }
    coefficient_lists = {}
    all_ok = True
    for order, expect in expected.items():
        poly = sp.expand(series.coeff(beta, order))
        got = [
            sp.nsimplify(poly.coeff(mu, k)) for k in range(len(expect))
        ]
        if sp.expand(
            poly - sum(c * mu**k for k, c in enumerate(expect))
        ) != 0:
            all_ok = False
        coefficient_lists[str(order)] = str([str(value) for value in got])
    return {
        "boost_kernel_mu_only_coefficients_exact": bool(all_ok),
        "boost_coefficient_lists": coefficient_lists,
    }


def run_axis() -> dict:
    rows = {}
    rows.update(check_parity_involution_and_axisym_b_zero())
    rows.update(check_reflection_tb_eb())
    rows.update(check_vii_h_handedness())
    rows.update(check_boost_kernel())
    checks = {
        key: value
        for key, value in rows.items()
        if isinstance(value, bool)
    }
    computed = {
        key: value
        for key, value in rows.items()
        if not isinstance(value, bool)
    }
    return {
        "all_pass": all(checks.values()),
        "checks": checks,
        "computed": computed,
        "sympy_version": sp.__version__,
    }


if __name__ == "__main__":
    print(json.dumps(run_axis(), sort_keys=True))
