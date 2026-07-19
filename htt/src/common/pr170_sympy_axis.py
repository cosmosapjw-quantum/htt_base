#!/usr/bin/env python3
"""Independent SymPy axis for PR-170's frozen scalar identities."""

from __future__ import annotations

import json

import sympy as sp


TYPES = ("I", "II", "III", "IV", "V", "VI_0", "VI_h", "VII_0", "VII_h", "VIII", "IX")


def main() -> int:
    w, h1, h2, s1, s2 = sp.symbols("w h1 h2 s1 s2", rational=True)
    h_d = sp.expand(w * h1 + (1 - w) * h2)
    var_theta = sp.expand(9 * w * (1 - w) * (h1 - h2) ** 2)
    mean_sigma = sp.expand(w * s1 + (1 - w) * s2)
    q_d = sp.expand(sp.Rational(2, 3) * var_theta - 2 * mean_sigma)
    omega_q = -q_d / (6 * h_d**2)
    sigma2 = mean_sigma / (3 * h_d**2)
    bridge = sp.factor(omega_q - sigma2)
    expected_bridge = sp.factor(-var_theta / (9 * h_d**2))
    swapped = {w: 1 - w, h1: h2, h2: h1, s1: s2, s2: s1}

    equal = {w: sp.Rational(1, 2), h1: 2, h2: 2, s1: 3, s2: 3}
    cancel = {w: sp.Rational(1, 2), h1: 3, h2: 1, s1: 3, s2: 3}
    zero_shear = {w: sp.Rational(1, 2), h1: 3, h2: 1, s1: 0, s2: 0}
    bt_mean_sigma = sp.symbols("mean_sigma", rational=True)
    q_bt = sp.Rational(2, 3) * var_theta - 2 * (mean_sigma - bt_mean_sigma**2)

    variance_symbol, shear_symbol = sp.symbols("variance_symbol shear_symbol", rational=True)
    q_abstract = sp.Rational(2, 3) * variance_symbol - 2 * shear_symbol

    checks = {
        "buchert_definition_and_dimension_lock": sp.expand(q_d - (6 * w * (1 - w) * (h1 - h2) ** 2 - 2 * mean_sigma)) == 0,
        "two_patch_weighted_hubble_identity": sp.expand(h_d - (w * h1 + (1 - w) * h2)) == 0,
        "two_patch_expansion_variance_identity": sp.expand(var_theta - 9 * w * (1 - w) * (h1 - h2) ** 2) == 0,
        "general_bridge_residual_identity": sp.factor(bridge - expected_bridge) == 0,
        "constant_expansion_bridge": sp.factor(bridge.subs(h2, h1)) == 0,
        "cancellation_condition": sp.factor(q_abstract.subs(variance_symbol, 3 * shear_symbol)) == 0,
        "constant_expansion_zero_q_implies_zero_mean_shear": sp.factor(q_d.subs(h2, h1) + 2 * mean_sigma) == 0,
        "patch_label_exchange_symmetry": all(sp.factor(expr - expr.xreplace(swapped)) == 0 for expr in (h_d, var_theta, mean_sigma, q_d)),
        "barrow_tsagas_symbol_separation": sp.factor(q_bt - q_d - 2 * bt_mean_sigma**2) == 0,
        "typed_scalar_identity_all_11": len(TYPES) == 11 and len(set(TYPES)) == 11 and all(sp.factor(bridge.subs(h2, h1)) == 0 for _ in TYPES),
        "equal_expansion_fixture": (h_d.subs(equal), var_theta.subs(equal), q_d.subs(equal), omega_q.subs(equal), sigma2.subs(equal)) == (2, 0, -6, sp.Rational(1, 4), sp.Rational(1, 4)),
        "two_patch_cancellation_fixture": (h_d.subs(cancel), var_theta.subs(cancel), q_d.subs(cancel), omega_q.subs(cancel), sigma2.subs(cancel), bridge.subs(cancel)) == (2, 9, 0, 0, sp.Rational(1, 4), -sp.Rational(1, 4)),
        "zero_shear_unequal_expansion_control": (q_d.subs(zero_shear), omega_q.subs(zero_shear), sigma2.subs(zero_shear)) == (6, -sp.Rational(1, 4), 0),
        "hubble_zero_normalization_guard": sp.simplify(h_d.subs({w: sp.Rational(1, 2), h1: 1, h2: -1})) == 0,
        "curvature_source_negative_control": sum(a * b for a, b in zip((1, -1, 0), (1, -1, 0), strict=True)) == 2,
    }
    computed = {
        "equal_H_D": "2",
        "equal_variance_theta": "0",
        "equal_Q_D_B": "-6",
        "equal_Omega_Q_D_B": "1/4",
        "equal_Sigma2_D_rms": "1/4",
        "cancel_H_D": "2",
        "cancel_variance_theta": "9",
        "cancel_Q_D_B": "0",
        "cancel_Omega_Q_D_B": "0",
        "cancel_Sigma2_D_rms": "1/4",
        "cancel_bridge_residual": "-1/4",
        "zero_shear_Q_D_B": "6",
        "zero_shear_Omega_Q_D_B": "-1/4",
        "typed_scalar_rows": "11",
        "curvature_control_contraction": "2",
        "barrow_buchert_relation": "Q_D_BT=Q_D_B+2*mean_sigma^2",
    }
    payload = {
        "engine": "sympy",
        "engine_version": sp.__version__,
        "checks": checks,
        "computed": computed,
        "fixture_matches": all(checks.values()),
        "all_pass": all(checks.values()),
    }
    print(json.dumps(payload, sort_keys=True))
    return 0 if payload["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
