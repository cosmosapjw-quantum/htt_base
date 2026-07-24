"""Independent SymPy axis for the PR-190 shear-substitution falsifier."""

from __future__ import annotations

import json

import sympy as sp

s, z = sp.symbols("s z")
d = s + (1 - s) * z
sigma = s / d
omega = (1 - s) * z / d
sigma_prime = 3 * z * sp.diff(sigma, z)
log_hubble_prime = -3 + sp.Rational(3, 2) * (1 - s) * z / d


def component_vector(s_value: sp.Rational, t_value: sp.Rational) -> dict[str, sp.Expr]:
    return {
        "Sigma2": sp.Rational(1, 10) + t_value / 50,
        "W2": sp.Rational(3, 100) + 3 * t_value / 200,
        "Omega_tilt": sp.Rational(1, 50) + s_value / 100,
        "DeltaOmega_k": -sp.Rational(1, 100) + s_value / 100 - t_value / 200,
    }


def candidate(x_c: sp.Rational) -> dict[str, sp.Expr]:
    return {
        "Sigma2": x_c,
        "W2": sp.Integer(0),
        "Omega_tilt": sp.Integer(0),
        "DeltaOmega_k": sp.Integer(0),
    }


def x_c(vector: dict[str, sp.Expr]) -> sp.Expr:
    return sp.factor(
        vector["Sigma2"]
        - vector["W2"]
        + vector["Omega_tilt"]
        + vector["DeltaOmega_k"]
    )


def gap(left: dict[str, sp.Expr], right: dict[str, sp.Expr]) -> sp.Expr:
    return max(abs(sp.factor(left[key] - right[key])) for key in left)


lower_target = component_vector(sp.Rational(0), -sp.Rational(2, 3))
upper_target = component_vector(sp.Rational(1), sp.Rational(0))
lower_candidate = candidate(sp.Rational(2, 25))
upper_candidate = candidate(sp.Rational(1, 10))

checks = {
    "dust_gauss_constraint_identity": sp.factor(sigma + omega - 1) == 0,
    "dust_logistic_evolution_identity": sp.factor(
        sigma_prime + 3 * sigma * (1 - sigma)
    )
    == 0,
    "dust_hubble_evolution_identity": sp.factor(
        log_hubble_prime + sp.Rational(3, 2) * (1 + sigma)
    )
    == 0,
    "lower_scalar_match_component_gap": (
        x_c(lower_target) == x_c(lower_candidate) == sp.Rational(2, 25)
        and gap(lower_target, lower_candidate) == sp.Rational(1, 50)
        and lower_target["Omega_tilt"] == sp.Rational(1, 50)
    ),
    "upper_scalar_match_component_gap": (
        x_c(upper_target) == x_c(upper_candidate) == sp.Rational(1, 10)
        and gap(upper_target, upper_candidate) == sp.Rational(3, 100)
        and upper_target["Omega_tilt"] == sp.Rational(3, 100)
    ),
}
payload = {
    "checks": checks,
    "domain_assumption_diff": [],
    "computed": {
        "lower_x_c": "2/25",
        "upper_x_c": "1/10",
        "lower_component_gap": "1/50",
        "upper_component_gap": "3/100",
    },
    "counterexample": None,
}
print(json.dumps(payload, sort_keys=True))
raise SystemExit(0 if all(checks.values()) else 2)
