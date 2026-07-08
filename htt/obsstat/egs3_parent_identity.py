"""EGS3 Axis F: SymPy seal of the parent constraint identity + W^2 convention (B1).

The external review (B1) found the v5 report registering W^2 = omega_a omega^a / H^2
while the P3 conversion rule and the Gauss constraint force
W^2 = omega_ab omega^ab / (6 H^2) = omega_a omega^a / (3 H^2) -- a factor-3 slip in
the DOCUMENT only. This module derives, symbolically and fail-closed:

(1) ``derive_parent_identity`` -- the generalized Friedmann/Gauss constraint of the
    1+3 covariant formalism,

        Theta^2/3 = kappa mu + Lambda - (1/2) R3 + sigma^2 - omega^2,
        sigma^2 = sigma_ab sigma^ab / 2,   omega^2 = omega_ab omega^ab / 2,

    divided by 3 H^2 (Theta = 3H), with the tilted-frame energy density
    mu_u = mu + (mu + p) sinh^2(beta) (v gamma = sinh beta), yields

        1 = Omega_m + Omega_Lambda + Omega_k + Omega_tilt + Sigma^2 - W^2,

    with Sigma^2 = sigma_ab sigma^ab/(6H^2), W^2 = omega_ab omega^ab/(6H^2),
    Omega_k = -R3/(6H^2), Omega_tilt = (1+w) Omega_m sinh^2 beta. The comparator
    sign vector c = (+1, -1, +1, +1) on (Sigma^2, W^2, Omega_tilt, Omega_k) is READ
    OFF this identity, not postulated.

(2) ``w2_convention_table`` -- omega_ab omega^ab = 2 omega_a omega^a (verified on a
    symbolic antisymmetric matrix built from the vorticity vector), so the
    registered W^2 = omega_ab omega^ab/(6H^2) equals omega_a omega^a/(3H^2); the
    v5 document's omega_a omega^a/H^2 is exactly 3x the registered value.

(3) ``three_halves_rule`` -- with X^2 := x_ab x^ab/(6H^2) and H = Theta/3, a bound
    sqrt(x_ab x^ab)/Theta <= B converts to X^2 <= (3/2) B^2. This derives the P3
    conversion factor instead of asserting it.

(4) ``mes_coefficient_provenance`` -- the epsilon coefficients of the diagonal MES
    budgets (B_sigma, B_omega, B_accel) are REGISTERED EXTERNAL values
    (Maartens-Ellis-Stoeger 1995; carried in `htt/tsc/admissibility/
    three_bound_hierarchy.py` and `htt/htt/htt/core/bounds.py`); they are recorded
    here for comparison, NOT rederived.

The code side needs no change: `comparator_policy.py` (Wstd_sq = omega_sq/(6 H^2)),
`bounds.py` and `three_bound_hierarchy.py` (W2_max = (3/2) B_omega^2) already use
the registered convention, so every bit-identical x_C anchor is untouched.

Fail-closed: every check returns an explicit boolean; ``parent_identity_seal``
reports status FAIL if ANY symbolic simplification is nonzero. No fallback value is
ever substituted.

Claim discipline. Symbolic algebra + convention registration only; no data claim,
no detection, no family/geometry/native-solver/posterior claim.
"""
from __future__ import annotations

from fractions import Fraction

import sympy as sp

__all__ = [
    "COMPARATOR_SIGN_VECTOR",
    "MES_EPSILON_COEFFICIENTS",
    "derive_parent_identity",
    "w2_convention_table",
    "three_halves_rule",
    "mes_coefficient_provenance",
    "parent_identity_seal",
]

# read off the parent identity below; asserted equal to the derived signs
COMPARATOR_SIGN_VECTOR = (1, -1, 1, 1)

# registered EXTERNAL values (Maartens-Ellis-Stoeger 1995 linearized hierarchy),
# as carried by three_bound_hierarchy.COEFFS / bounds.py -- recorded, not rederived
MES_EPSILON_COEFFICIENTS = {
    "B_sigma": (Fraction(5, 3), Fraction(3), Fraction(3, 7)),
    "B_omega": (Fraction(3, 4), Fraction(2), Fraction(2, 7)),
    "B_accel": (Fraction(3, 4), Fraction(1), Fraction(3, 14)),
}


def derive_parent_identity() -> dict:
    """Symbolically derive 1 = Om + OL + Ok + Otilt + Sigma2 - W2 and read off c."""
    H, kappa, mu, Lam, R3, s2t, w2t, beta, w = sp.symbols(
        "H kappa mu Lambda R3 sigma2t omega2t beta w", positive=True)
    # tilted-frame energy density: mu_u = mu + (mu + p) sinh^2(beta), p = w mu
    mu_u = mu + (mu + w * mu) * sp.sinh(beta) ** 2
    # Gauss constraint, Theta = 3H, sigma^2 = s2t/2, omega^2 = w2t/2:
    #   3 H^2 = kappa mu_u + Lambda - R3/2 + s2t/2 - w2t/2
    lhs = 3 * H ** 2
    rhs = kappa * mu_u + Lam - R3 / 2 + s2t / 2 - w2t / 2
    budget = sp.expand((rhs - lhs) / (3 * H ** 2))

    Omega_m = kappa * mu / (3 * H ** 2)
    Omega_L = Lam / (3 * H ** 2)
    Omega_k = -R3 / (6 * H ** 2)
    Omega_tilt = (1 + w) * Omega_m * sp.sinh(beta) ** 2
    Sigma2 = s2t / (6 * H ** 2)
    W2 = w2t / (6 * H ** 2)

    # identity check: budget == (Om + OL + Ok + Otilt + Sigma2 - W2) - 1
    reassembled = Omega_m + Omega_L + Omega_k + Omega_tilt + Sigma2 - W2 - 1
    identity_ok = sp.simplify(budget - reassembled) == 0

    # read off the comparator signs: rewrite the budget in the four dimensionless
    # component symbols (S, Wc, T, K) and differentiate
    S, Wc, T, K = sp.symbols("S Wc T K", positive=True)
    budget_components = sp.expand(budget.subs({
        s2t: 6 * H ** 2 * S,                                  # Sigma2 = S
        w2t: 6 * H ** 2 * Wc,                                 # W2 = Wc
        R3: -6 * H ** 2 * K,                                  # Omega_k = K
        sp.sinh(beta) ** 2: T * 3 * H ** 2 / (kappa * mu * (1 + w)),  # Omega_tilt = T
    }))
    c_derived = tuple(int(sp.simplify(sp.diff(budget_components, v)))
                      for v in (S, Wc, T, K))
    signs_ok = c_derived == COMPARATOR_SIGN_VECTOR
    return {
        "identity_ok": bool(identity_ok),
        "c_derived": list(c_derived),
        "c_registered": list(COMPARATOR_SIGN_VECTOR),
        "signs_ok": bool(signs_ok),
        "parent_identity": "1 = Omega_m + Omega_Lambda + Omega_k + Omega_tilt"
                           " + Sigma2 - W2",
        "omega_tilt_closed_form": "(1+w) * Omega_m * sinh(beta)**2",
        "normalizations_forced": {
            "Sigma2": "sigma_ab sigma^ab / (6 H^2)",
            "W2": "omega_ab omega^ab / (6 H^2)",
            "Omega_k": "-R3 / (6 H^2)",
        },
    }


def w2_convention_table() -> dict:
    """omega_ab omega^ab = 2 omega_a omega^a (symbolic) and the 3x v5 mismatch."""
    w1, w2, w3, H = sp.symbols("w1 w2 w3 H", positive=True)
    omega_ab = sp.Matrix([[0, w3, -w2],
                          [-w3, 0, w1],
                          [w2, -w1, 0]])
    tensor_sq = sum(omega_ab[i, j] ** 2 for i in range(3) for j in range(3))
    vector_sq = w1 ** 2 + w2 ** 2 + w3 ** 2
    doubling_ok = sp.simplify(tensor_sq - 2 * vector_sq) == 0

    registered = tensor_sq / (6 * H ** 2)             # = vector_sq / (3 H^2)
    v5_document = vector_sq / H ** 2
    mismatch = sp.simplify(v5_document / registered)
    return {
        "tensor_equals_twice_vector": bool(doubling_ok),
        "registered_convention": "omega_ab omega^ab / (6 H^2) "
                                 "= omega_a omega^a / (3 H^2)",
        "v5_document_convention": "omega_a omega^a / H^2",
        "mismatch_factor": int(mismatch),
        "mismatch_is_three": bool(mismatch == 3),
        "code_already_registered": [
            "htt/bass/validation/comparator_policy.py:337",
            "htt/htt/htt/core/bounds.py:109-111",
            "htt/tsc/admissibility/three_bound_hierarchy.py:168-171",
        ],
    }


def three_halves_rule() -> dict:
    """Derive X^2_max = (3/2) B^2 from X^2 = x_ab x^ab/(6H^2), H = Theta/3."""
    x2t, Theta, B = sp.symbols("x2t Theta B", positive=True)
    H = Theta / 3
    X2 = x2t / (6 * H ** 2)
    # bound: sqrt(x2t)/Theta <= B  =>  x2t <= B^2 Theta^2
    X2_at_bound = X2.subs(x2t, B ** 2 * Theta ** 2)
    factor = sp.simplify(X2_at_bound / B ** 2)
    return {
        "rule": "X^2 = x_ab x^ab/(6 H^2), H = Theta/3, sqrt(x_ab x^ab)/Theta <= B "
                "=> X^2_max = (3/2) B^2",
        "derived_factor": str(factor),
        "factor_is_three_halves": bool(factor == sp.Rational(3, 2)),
    }


def mes_coefficient_provenance() -> dict:
    """The registered external MES epsilon coefficients (recorded, not rederived)."""
    return {
        "provenance": "Maartens-Ellis-Stoeger 1995 linearized multipole hierarchy; "
                      "registered external values carried by "
                      "htt/tsc/admissibility/three_bound_hierarchy.py COEFFS and "
                      "htt/htt/htt/core/bounds.py",
        "coefficients": {
            name: [str(f) for f in fracs]
            for name, fracs in MES_EPSILON_COEFFICIENTS.items()
        },
        "rederived_here": False,
    }


def parent_identity_seal() -> dict:
    """Aggregate seal; status FAIL if any symbolic check fails (fail-closed)."""
    parent = derive_parent_identity()
    w2 = w2_convention_table()
    rule = three_halves_rule()
    prov = mes_coefficient_provenance()
    ok = (parent["identity_ok"] and parent["signs_ok"]
          and w2["tensor_equals_twice_vector"] and w2["mismatch_is_three"]
          and rule["factor_is_three_halves"])
    return {
        "seal": "egs3.parent_identity",
        "status": "PASS" if ok else "FAIL",
        "sympy_version": sp.__version__,
        "parent_identity": parent,
        "w2_convention": w2,
        "three_halves_rule": rule,
        "mes_epsilon_provenance": prov,
        "claim_boundary": "symbolic convention seal only; document-side B1 repair; "
                          "code already on the registered convention; no data, "
                          "detection, family/geometry, or native-solver claim",
    }
