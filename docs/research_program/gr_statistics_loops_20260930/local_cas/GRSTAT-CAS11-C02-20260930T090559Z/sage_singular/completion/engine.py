"""Exact Sage algebra and ordered-polynomial certificates for the C02 proof.

Run with Sage's Python, never ambient Python. The universal spectral lifting is
proved in proof.md and is explicitly outside a formal proof-assistant kernel.
"""

import json
from pathlib import Path
import sys

from sage.all import PolynomialRing, QQ
from sage.version import version


P = PolynomialRing(QQ, names=("lam", "mu", "z", "ep", "h", "s", "d", "A", "B", "x", "y"))
lam, mu, z, ep, h, s, d, A, B, x, y = P.gens()
certificates = []


def ideal_certificate(name, target, generators, multipliers):
    """Check an explicit ideal-membership witness and an exact normal form."""
    witness = sum((m * g for m, g in zip(multipliers, generators)), P.zero())
    residual = target - witness
    basis = P.ideal(generators).groebner_basis()
    normal_form = target.reduce(basis)
    passed = len(generators) == len(multipliers) and residual == 0 and normal_form == 0
    record = {
        "name": name,
        "target": str(target),
        "generators": [str(g) for g in generators],
        "multipliers": [str(m) for m in multipliers],
        "explicit_witness_residual": str(residual),
        "groebner_basis": [str(g) for g in basis],
        "groebner_remainder": str(normal_form),
        "passed": bool(passed),
    }
    certificates.append(record)
    print(json.dumps(record, sort_keys=True))
    if not passed:
        raise ArithmeticError(name)


def identity(name, polynomial):
    residual = P(polynomial)
    passed = residual == 0
    record = {"name": name, "identity_residual": str(residual), "passed": bool(passed)}
    certificates.append(record)
    print(json.dumps(record, sort_keys=True))
    if not passed:
        raise ArithmeticError(name)


def strict_positive_polynomial(name, polynomial, signs):
    """Check a positive-cone witness using only ordered-real arithmetic rules.

    This is a transparent certificate checker, not a real-closed-field or
    proof-assistant kernel. Each supported monomial has a positive rational
    coefficient and nonnegative factors; at least one is strictly positive.
    Even powers of a nonzero real are strictly positive.
    """
    monomials = []
    for powers, coefficient in polynomial.dict().items():
        if coefficient <= 0:
            raise ArithmeticError("cone witness has a nonpositive coefficient")
        strict = True
        for variable, power in zip(P.gens(), powers):
            if power == 0:
                continue
            sign = signs.get(str(variable))
            if sign == "positive":
                continue
            if sign == "nonnegative":
                strict = False
                continue
            if sign == "nonzero_real" and power % 2 == 0:
                continue
            raise ArithmeticError("unsupported monomial sign")
        monomials.append({"powers": list(powers), "coefficient": str(coefficient), "strict": strict})
    passed = bool(monomials) and any(m["strict"] for m in monomials)
    record = {
        "name": name,
        "polynomial": str(polynomial),
        "conditional_sign_premises": signs,
        "monomial_witnesses": monomials,
        "strict_positive_under_premises": passed,
        "passed": passed,
    }
    print(json.dumps(record, sort_keys=True))
    if not passed:
        raise ArithmeticError(name)
    return record


print("SageMath " + version)
print("polynomial_type=" + type(lam).__module__ + "." + type(lam).__name__)
print("ring=" + str(P))

# For a single eigenvector, h = 2*epsilon*lambda - z^2 >= 0 follows
# from the FOR-ALL-a premise. The following two certificates need no inverse.
slack_relation = h + z**2 - 2 * ep * lam
ideal_certificate("null_mode_slack", h + z**2, [slack_relation, lam], [P.one(), 2 * ep])
ideal_certificate("epsilon_zero_slack", h + z**2, [slack_relation, ep], [P.one(), 2 * lam])

# Only the strictly positive eigenvalue branch introduces mu=1/lambda.
positive_relation = lam * mu - 1
ideal_certificate("positive_range", lam * mu * z - z, [positive_relation], [z])
ideal_certificate("positive_energy", lam * (mu * z)**2 - mu * z**2, [positive_relation], [mu * z**2])
ideal_certificate("positive_mp_one", lam * mu * lam - lam, [positive_relation], [lam])
ideal_certificate("positive_mp_two", mu * lam * mu - mu, [positive_relation], [mu])

# Here z=0 is a DERIVED consequence of null_mode_slack and real order,
# never an input restriction on e. mu=0 is the spectral definition.
zero_generators = [lam, mu, z]
ideal_certificate("zero_range", lam * mu * z - z, zero_generators, [mu * z, P.zero(), -P.one()])
ideal_certificate("zero_energy", lam * (mu * z)**2 - mu * z**2, zero_generators, [mu**2 * z**2, -z**2, P.zero()])
ideal_certificate("zero_mp_one", lam * mu * lam - lam, [lam, mu], [mu * lam - 1, P.zero()])
ideal_certificate("zero_mp_two", mu * lam * mu - mu, [lam, mu], [P.zero(), lam * mu - 1])
identity("dot_energy", (mu * z) * z - mu * z**2)

# This is a universally quantified induction STEP in four arbitrary scalars,
# together with its empty-sum base, not a check for a fixed matrix dimension.
identity("sum_base", P.zero() - P.zero())
ideal_certificate("sum_step", (A + x) - (B + y), [A - B, x - y], [P.one(), P.one()])

# Under a putative bound violation d=s-2*epsilon>0 and the premise slack
# h=2*epsilon*s-s^2>=0, h+d^2+2*epsilon*d is both zero and positive.
bound_generators = [h - 2 * ep * s + s**2, d - s + 2 * ep]
ideal_certificate("bound_contradiction", h + d**2 + 2 * ep * d, bound_generators, [P.one(), d + s])

sign_checks = [
    strict_positive_polynomial("null_mode_sign", h + z**2, {"h": "nonnegative", "z": "nonzero_real"}),
    strict_positive_polynomial("bound_sign", h + d**2 + 2 * ep * d, {"h": "nonnegative", "d": "positive", "ep": "nonnegative"}),
]
result = {
    "sage_version": version,
    "algebra_certificates": certificates,
    "ordered_polynomial_certificates": sign_checks,
    "all_computations_passed": all(c["passed"] for c in certificates + sign_checks),
    "formal_kernel_proof": False,
    "universal_lifting": "proof.md; real spectral theorem, finite-sum induction, and ordered-real rules",
}
Path(sys.argv[1]).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
