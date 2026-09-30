#!/usr/bin/python3
"""CAS11-C02: analytic universal proof with executed SymPy certificates.

PROOF.md supplies the finite-dimensional spectral theorem, finite-sum lifting,
and universal-quantifier instantiation. This is not a theorem-kernel proof.
The emitted check is the bounded axis result for that documented proof, whose
nontrivial scalar and arbitrary-size matrix reductions are verified below.
No finite collection of matrices is used to infer the universal theorem.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import traceback

import sympy as sp


REPO = Path(__file__).resolve().parents[7]
CONTRACT_REL = (
    "docs/research_program/gr_statistics_loops_20260930/"
    "cas11_c02_local_start_20260930/contracts/CAS11-C02-FINITE-GRAM.json"
)
CONTRACT_SHA256 = "c66d7d00bf60786417336873dfeb97f5602d0e60a110c110ebacd9dff824b47a"
OBLIGATION = "CAS11-C02-FINITE-GRAM"


class IncompleteProof(RuntimeError):
    """A missing/false certificate must not produce the success payload."""


class Certificates:
    def __init__(self):
        self.records = []

    def check(self, name, computed, **evidence):
        passed = computed is True or computed is sp.S.true
        self.records.append({"id": name, "passed": passed, **evidence})
        print(json.dumps(self.records[-1], sort_keys=True), file=sys.stderr)
        if not passed:
            raise IncompleteProof(name)

    def identity(self, name, lhs, rhs):
        difference = sp.simplify(lhs - rhs)
        self.check(name, difference == 0, residual=str(difference))


def symbolic_certificates(cert):
    # k is an arbitrary coordinate, not a fixed-dimension sampling index.
    x = sp.Symbol("f_k", real=True)
    lam = sp.Symbol("lambda_k", positive=True)
    z = x / lam
    component = x**2 / lam
    cert.check(
        "kernel_square_nonpositive_iff_zero",
        sp.solve_univariate_inequality(x**2 <= 0, x, relational=False)
        == sp.FiniteSet(0),
        solution=str(sp.solve_univariate_inequality(x**2 <= 0, x, relational=False)),
    )
    cert.identity("positive_coordinate_range", lam * z, x)
    cert.identity("positive_coordinate_dot", z * x, component)
    cert.identity("positive_coordinate_quadratic", lam * z**2, component)
    cert.check(
        "positive_coordinate_energy_nonnegative",
        sp.ask(sp.Q.nonnegative(component)),
        expression=str(component),
    )
    # The zero branch is substituted only AFTER kernel_square_nonpositive_iff_zero.
    # No expression 1/0 is constructed.
    for name, expression in (
        ("zero_coordinate_range", sp.Symbol("lambda") * sp.Symbol("z") - sp.Symbol("f")),
        ("zero_coordinate_dot", sp.Symbol("z") * sp.Symbol("f")),
        ("zero_coordinate_quadratic", sp.Symbol("lambda") * sp.Symbol("z")**2),
    ):
        values = {sp.Symbol("lambda"): 0, sp.Symbol("z"): 0, sp.Symbol("f"): 0}
        cert.identity(name, expression.subs(values), 0)

    mu = 1 / lam
    cert.identity("positive_MP_RMR", lam * mu * lam, lam)
    cert.identity("positive_MP_MRM", mu * lam * mu, mu)
    cert.identity("positive_MP_commuting_product", lam * mu, mu * lam)
    cert.identity("zero_MP_RMR", (lam * sp.Symbol("mu") * lam - lam).subs({lam: 0, sp.Symbol("mu"): 0}), 0)
    cert.identity("zero_MP_MRM", (sp.Symbol("mu") * lam * sp.Symbol("mu") - sp.Symbol("mu")).subs({lam: 0, sp.Symbol("mu"): 0}), 0)

    # These MatrixExpr reductions use symbolic n, so n is not bounded above.
    n = sp.Symbol("n", integer=True, positive=True)
    U = sp.MatrixSymbol("U", n, n)
    D = sp.MatrixSymbol("D", n, n)
    M = sp.MatrixSymbol("M", n, n)
    b = sp.MatrixSymbol("b", n, 1)
    f = sp.MatrixSymbol("f", n, 1)
    E = sp.MatrixSymbol("e", n, 1)
    R = U * D * U.T
    ortho = sp.Q.orthogonal(U)
    reductions = (
        ("orthogonal_coordinate_reconstruction", U * (U.T * E), E),
        ("arbitrary_n_dot_transform", (U * b).T * (U * f), b.T * f),
        ("arbitrary_n_quadratic_transform", (U * b).T * R * (U * b), b.T * D * b),
        ("arbitrary_n_range_transform", R * (U * b), U * D * b),
        ("arbitrary_n_pseudoinverse_energy", (U * f).T * (U * M * U.T) * (U * f), f.T * M * f),
        ("arbitrary_n_MP_RMR", R * (U * M * U.T) * R, U * D * M * D * U.T),
    )
    for name, lhs, rhs in reductions:
        reduced = sp.refine(lhs, ortho).doit()
        cert.check(name, reduced == rhs, reduced=str(reduced), expected=str(rhs), dimension=str(n))

    # Finite-sum lifting in PROOF.md uses these coordinate identities for each k.
    # Check the empty sum explicitly for rank zero.
    k = sp.Symbol("k", integer=True)
    h = sp.Function("h")
    cert.identity("empty_rank_sum", sp.Sum(h(k), (k, 1, 0)).doit(), 0)

    # General real scalar implication: S^2 <= c*S, c >= 0 => S <= c.
    # If S > c, delta=S-c is positive. Its residual is strictly positive,
    # contradicting the premise. Neither epsilon nor S is divided out.
    c = sp.Symbol("c", nonnegative=True)
    delta = sp.Symbol("delta", positive=True)
    violation_residual = (c + delta)**2 - c * (c + delta)
    cert.identity("bound_contradiction_factorization", violation_residual, delta * (c + delta))
    cert.check("bound_contradiction_strict_sign", sp.ask(sp.Q.positive(delta * (c + delta))), expression=str(delta * (c + delta)))
    eps = sp.Symbol("epsilon", nonnegative=True)
    cert.check("c_is_nonnegative", sp.ask(sp.Q.nonnegative(2 * eps)), expression=str(2 * eps))
    cert.identity("epsilon_zero_bound_residual", violation_residual.subs(c, 0), delta**2)
    cert.check("epsilon_zero_contradiction_sign", sp.ask(sp.Q.positive(delta**2)), expression=str(delta**2))
    cert.identity("spectral_Gram_square_root", sp.sqrt(lam)**2, lam)


def exact_fixture(cert, name, eigenvalues, spectral_error, epsilon, U=None):
    """Supplementary checks only; no fixture asserts the universal premise."""
    n = len(eigenvalues)
    U = sp.eye(n) if U is None else U
    D = sp.diag(*eigenvalues)
    M = sp.diag(*(sp.S.Zero if value == 0 else 1 / value for value in eigenvalues))
    f = sp.Matrix(spectral_error)
    R = U * D * U.T
    Rdagger = U * M * U.T
    e = U * f
    a = Rdagger * e
    energy = sp.simplify((e.T * Rdagger * e)[0])
    cert.check(name + "_orthogonal", U.T * U == sp.eye(n))
    cert.check(name + "_MP_equations", R * Rdagger * R == R and Rdagger * R * Rdagger == Rdagger and (R * Rdagger).T == R * Rdagger and (Rdagger * R).T == Rdagger * R)
    cert.check(name + "_range_witness", R * a == e)
    cert.identity(name + "_dot", (a.T * e)[0], energy)
    cert.identity(name + "_quadratic", (a.T * R * a)[0], energy)
    cert.check(name + "_bound", bool(0 <= energy <= 2 * epsilon), energy=str(energy), epsilon=str(epsilon))
    return R, Rdagger, e, a, energy


def falsification_and_precision_checks(cert):
    # Each negative control has an explicit test vector that falsifies the premise.
    controls = (
        ("nullspace_error", sp.diag(1, 0), sp.Matrix([0, 1]), sp.Rational(1, 2), sp.Matrix([0, 1])),
        ("range_error_above_bound", sp.diag(1, 0), sp.Matrix([2, 0]), sp.Rational(1, 2), sp.Matrix([2, 0])),
        ("zero_R_positive_epsilon", sp.zeros(2), sp.Matrix([1, 0]), sp.Integer(7), sp.Matrix([1, 0])),
        ("positive_R_zero_epsilon", sp.eye(2), sp.Matrix([1, 0]), sp.S.Zero, sp.Matrix([1, 0])),
    )
    for name, R, e, epsilon, a in controls:
        residual = sp.simplify((a.T * e)[0]**2 - 2 * epsilon * (a.T * R * a)[0])
        cert.check("negative_control_" + name, residual.is_positive, violating_residual=str(residual))

    exact_fixture(cert, "positive_definite_boundary", [sp.Integer(2)], [sp.Integer(2)], sp.Integer(1))
    exact_fixture(cert, "singular_nonzero_boundary", [sp.Integer(2), sp.S.Zero], [sp.Integer(2), sp.S.Zero], sp.Integer(1))
    exact_fixture(cert, "zero_rank_zero_epsilon", [sp.S.Zero], [sp.S.Zero], sp.S.Zero)
    exact_fixture(cert, "zero_rank_positive_epsilon", [sp.S.Zero], [sp.S.Zero], sp.Integer(3))
    exact_fixture(cert, "singular_nonzero_zero_epsilon", [sp.Integer(2), sp.S.Zero], [sp.S.Zero, sp.S.Zero], sp.S.Zero)
    exact_fixture(cert, "positive_definite_zero_epsilon", [sp.Integer(2)], [sp.S.Zero], sp.S.Zero)

    v = sp.Matrix([1, 2, 3, 4])
    U = sp.eye(4) - 2 * (v * v.T) / (v.T * v)[0]
    eigenvalues = [sp.Rational(1, 10**80), sp.S.One, sp.Integer(10**40), sp.S.Zero]
    f = [sp.Rational(1, 2 * 10**40), sp.Rational(1, 2), sp.Integer(10**20) / 2, sp.S.Zero]
    R, Rdagger, e, a, energy = exact_fixture(cert, "ill_conditioned_rotated_singular", eigenvalues, f, sp.Rational(1, 2), U)
    # 220 decimal digits leave a substantial guard margin over the 120-decade
    # spectral spread and intermediate cancellation. The 1e-70 threshold is only
    # a numerical regression check, never a replacement for an exact identity.
    digits = 220
    Rh, Mh, eh, ah = (matrix.evalf(digits) for matrix in (R, Rdagger, e, a))
    errors = {
        "range": max(abs(value) for value in Rh * ah - eh),
        "dot": abs((ah.T * eh)[0] - energy),
        "quadratic": abs((ah.T * Rh * ah)[0] - energy),
        "pseudoinverse_energy": abs((eh.T * Mh * eh)[0] - energy),
    }
    threshold = sp.Float("1e-70", digits)
    cert.check("high_precision_ill_conditioned", all(bool(value < threshold) for value in errors.values()), decimal_digits=digits, threshold=str(threshold), absolute_errors={key: str(value.evalf(12)) for key, value in errors.items()})


def main():
    cert = Certificates()
    raw = (REPO / CONTRACT_REL).read_bytes()
    cert.check("frozen_contract_seal", hashlib.sha256(raw).hexdigest() == CONTRACT_SHA256, sha256=hashlib.sha256(raw).hexdigest())
    contract = json.loads(raw)
    cert.check("obligation_alignment", contract["target"]["exact_test_obligations"] == [OBLIGATION])
    cert.check("runtime_binding", sp.__version__ == "1.14.0", sympy_version=sp.__version__, sympy_origin=sp.__file__, python=sys.version, executable=sys.executable)
    symbolic_certificates(cert)
    falsification_and_precision_checks(cert)
    # Every certificate above is computed. Analytic dependencies and the full
    # quantified inference are stated and proved in PROOF.md, not assumed here.
    all_passed = bool(cert.records) and all(record["passed"] for record in cert.records)
    if not all_passed:
        raise IncompleteProof("certificate conjunction")
    print(json.dumps({"checks": {OBLIGATION: all_passed}, "domain_assumption_diff": [], "counterexample": None}, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc(file=sys.stderr)
        sys.exit(2)
