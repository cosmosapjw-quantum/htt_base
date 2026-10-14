#!/usr/bin/env python3
"""Exact SageMath/libSingular certificate for the pinned C04 contract.

Run with Sage's Python, not ordinary Python. This is a certificate interpreter
over QQ with an explicit ordered-real/absolute-value trust boundary; it is not
a proof assistant. Runtime or certificate failures produce stderr and nonzero
exit, never a fabricated theorem-result JSON object.
"""

import argparse
import hashlib
import json
from pathlib import Path
import sys


TARGET = "CAS13-C04-RELATIVE-MINIMAX"
CONTRACT_SHA256 = "0002809c73fd5de362deded39735fe884183bb953029f671552a525f74086f63"
CONTRACT_ID = "GRSTAT-20260930-CAS13-C04-RELATIVE-MINIMAX"
STATEMENT = [
    "For every x in [L,U], loss(a_star,x)<=r_star",
    "loss(a_star,L)=r_star and loss(a_star,U)=r_star",
    "For every real a, r_star<=max(loss(a,L),loss(a,U))",
]
TRUST_BOUNDARY = [
    "SageMath QQ polynomial arithmetic and the libSingular Groebner/reduction implementation",
    "The small certificate interpreter and Python runtime",
    "Ordered-real rules: sums/products of nonnegative terms are nonnegative; a sum with a strictly positive term is positive; positive division preserves order",
    "Absolute-value rules: -b<=z<=b with b>=0 implies abs(z)<=b; abs(b)=abs(-b)=b for b>=0; abs(z)>=z and abs(z)>=-z",
    "The maximum of two real values is at least each value; substitution of definitions and equality preserves real statements",
    "Positive denominators permit the recorded rational-to-polynomial translations",
]


class CertificateFailure(Exception):
    """An exact certificate or a required logical precondition was rejected."""


def require(condition, message):
    if not condition:
        raise CertificateFailure(message)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def validate_contract_bytes(raw):
    require(sha256(raw) == CONTRACT_SHA256, "Contract SHA-256 does not match the pinned bytes")
    contract = json.loads(raw.decode("utf-8"))
    require(contract["identity"]["contract_id"] == CONTRACT_ID, "Contract ID mismatch")
    require(contract["identity"]["contract_version"] == 3, "Contract version mismatch")
    require(contract["semantics"]["field"] == "real", "Expected the real field")
    require(contract["semantics"]["quantifiers"] == [
        "For every real L,U with 0<L<=U, and every real predictor a."
    ], "Quantifier mismatch")
    require(contract["semantics"]["assumptions"] == [], "Unexpected additional assumptions")
    require(contract["semantics"]["candidate_expressions_to_verify"] == [
        "a_star=2 L U/(L+U)", "r_star=(U-L)/(L+U)"
    ], "Candidate expression mismatch")
    require(contract["target"]["exact_statement"] == STATEMENT, "Statement mismatch")
    require(contract["target"]["exact_test_obligations"] == [TARGET], "Obligation mismatch")
    require(contract["axes"]["sage_singular"]["obligation"] == STATEMENT, "Axis mismatch")
    return contract


class Checker:
    """A restricted nonnegative-polynomial certificate interpreter.

    Facts originate only in interval-domain atoms, checked positive sums and
    products, or the single documented maximum/absolute-value bridge. There is
    no general assume-a-polynomial-is-nonnegative API.
    """

    def __init__(self, PolynomialRing, QQ, mutation=None):
        self.QQ = QQ
        self.mutation = mutation
        self.ring = PolynomialRing(QQ, names=("d", "k", "e", "n", "L", "U", "x", "a", "t"), order="lex")
        self.d, self.k, self.e, self.n, self.L, self.U, self.x, self.a, self.t = self.ring.gens()
        self.definitions = [
            self.d - self.L - self.U,
            self.k - 2 * self.L * self.U,
            self.e - self.U + self.L,
            self.n - self.k + self.x * self.d,
        ]
        self.ideal = self.ring.ideal(self.definitions)
        # Explicitly select Singular's exact backend; failure is fatal.
        self.basis = self.ideal.groebner_basis(algorithm="libsingular:std")
        require(len(self.basis) > 0, "Empty definitional Groebner basis")
        require(all(g != 1 for g in self.basis), "Inconsistent definitional ideal")
        self.facts = {}
        self.identities = []
        self.logical_steps = []
        self.obligations = {}
        self.branch_checks = []

    def identity(self, label, lhs, rhs, basis=None):
        lhs, rhs = self.ring(lhs), self.ring(rhs)
        residual = lhs - rhs
        reduction_basis = self.basis if basis is None else basis
        # Nonzero residuals are reduced modulo independently declared
        # definitional equalities. Zero residuals are honestly classified as
        # coefficient identities, not advertised as Singular evidence.
        remainder = residual.reduce(reduction_basis) if residual else self.ring.zero()
        require(remainder == 0, "Identity rejected: " + label + "; remainder=" + str(remainder))
        self.identities.append({
            "name": label,
            "lhs": str(lhs), "rhs": str(rhs),
            "pre_reduction_residual": str(residual),
            "normal_form": str(remainder),
            "method": "libSingular reduction of a nonzero polynomial" if residual else "exact QQ coefficient identity",
            "passed": True,
        })

    def fact(self, name):
        require(name in self.facts, "Missing sign premise: " + name)
        return self.facts[name]

    def positive(self, name):
        result = self.fact(name)
        require(result["strict"], "Strict positivity not established: " + name)
        return result

    def domain(self):
        # These are precisely the quantified interval's domain conditions.
        entries = [
            ("L", self.L, self.mutation != "weaken_L_to_nonnegative", "0<L"),
            ("gap", self.U - self.L, False, "L<=U"),
            ("left_slack", self.x - self.L, False, "L<=x"),
            ("right_slack", self.U - self.x, False, "x<=U"),
        ]
        for name, polynomial, strict, source in entries:
            if name == "left_slack" and self.mutation == "drop_interior_premise":
                continue
            self.facts[name] = {"polynomial": polynomial, "strict": strict, "source": source}
        self.positive("L")

    def nonnegative_sum(self, name, target, terms):
        """Check target = sum(c * product(previous sign facts)), c>0."""
        rhs = self.ring.zero()
        strict = False
        serialized_terms = []
        for coefficient, factors in terms:
            coefficient = self.QQ(coefficient)
            require(coefficient > 0, "Certificate coefficients must be positive")
            require(len(factors) > 0, "A product must identify its sign premises")
            term = self.ring(coefficient)
            term_strict = True
            for factor_name in factors:
                factor = self.fact(factor_name)
                term *= factor["polynomial"]
                term_strict = term_strict and factor["strict"]
            rhs += term
            strict = strict or term_strict
            serialized_terms.append({"coefficient": str(coefficient), "factors": list(factors)})
        self.identity(name, target, rhs)
        self.facts[name] = {"polynomial": self.ring(target), "strict": strict, "source": "checked nonnegative polynomial certificate"}
        self.logical_steps.append({"rule": "nonnegative_sum_of_products", "name": name, "terms": serialized_terms, "strict": strict})

    def max_absolute_value_slack(self, name, endpoint_name, sign):
        require(sign in (-1, 1), "Invalid absolute-value sign")
        endpoint = self.positive(endpoint_name)["polynomial"]
        require(endpoint in (self.L, self.U), "Only the theorem's endpoints may be used")
        # t is defined, without constraining a, as
        # max(abs((a-L)/L), abs((a-U)/U)).
        # Hence t >= abs((a-endpoint)/endpoint) >= sign*(a-endpoint)/endpoint.
        # Multiplying by the proved-positive endpoint gives this polynomial.
        slack = endpoint * self.t - sign * (self.a - endpoint)
        self.facts[name] = {"polynomial": slack, "strict": False, "source": "trusted max/absolute-value rule with checked positive denominator"}
        self.logical_steps.append({
            "rule": "max_abs_signed_bound_then_positive_multiplication",
            "name": name, "endpoint": str(endpoint), "sign": sign,
            "t_definition": "max(abs(a/L-1), abs(a/U-1))",
            "rational_identity": "a/endpoint-1=(a-endpoint)/endpoint",
            "positive_denominator_fact": endpoint_name,
            "conclusion_polynomial_ge_zero": str(slack),
        })

    def finish_interval_bound(self):
        self.positive("d")
        self.positive("candidate_denominator")
        self.fact("e")
        self.identity("upper_bound_translation", self.fact("interval_upper")["polynomial"], self.x * self.e - self.n)
        self.identity("lower_bound_translation", self.fact("interval_lower")["polynomial"], self.x * self.e + self.n)
        self.logical_steps.append({
            "rule": "absolute_value_from_two_signed_bounds",
            "nonnegative_slacks": ["interval_upper", "interval_lower"],
            "positive_denominator": "x*d",
            "nonnegative_radius": "e/d",
            "signed_residual": "n/(x*d)",
            "conclusion": "abs(a_star/x-1)<=r_star for every L<=x<=U",
        })
        self.obligations["uniform_interval_bound"] = True

    def finish_endpoints(self):
        self.positive("L")
        self.positive("U")
        self.positive("d")
        self.fact("e")
        self.identity("lower_endpoint_signed_residual", self.k - self.L * self.d, self.L * self.e)
        endpoint_sign = 1 if self.mutation == "wrong_upper_endpoint_sign" else -1
        self.identity("upper_endpoint_signed_residual", self.k - self.U * self.d, endpoint_sign * self.U * self.e)
        self.logical_steps.append({
            "rule": "abs_of_nonnegative_radius_and_its_negative",
            "checked_residual_equalities": ["a_star/L-1=e/d", "a_star/U-1=-e/d"],
            "nonnegative_radius_fact": "e>=0 and d>0",
            "conclusion": "loss(a_star,L)=loss(a_star,U)=r_star",
        })
        self.obligations["both_endpoint_equalities"] = True

    def finish_competitor(self):
        self.positive("d")
        self.identity("competitor_translation", self.fact("competitor_gap")["polynomial"], self.d * self.t - self.e)
        self.logical_steps.append({
            "rule": "positive_division",
            "premises": ["d>0", "d*t-e>=0", "t=max(loss(a,L),loss(a,U))"],
            "conclusion": "r_star<=max(loss(a,L),loss(a,U)) for every real a",
            "predictor_sign_assumptions": [],
        })
        self.obligations["all_real_competitor_lower_bound"] = True

    def degenerate_branch(self):
        # A specialization of the same certificate, not a replacement for its
        # general proof. There is no division by U-L anywhere.
        branch_ideal = self.ring.ideal(self.definitions + [self.U - self.L])
        branch_basis = branch_ideal.groebner_basis(algorithm="libsingular:std")
        require(all(g != 1 for g in branch_basis), "Inconsistent degenerate branch")
        for label, lhs, rhs in [
            ("L_equals_U_radius_numerator", self.e, 0),
            ("L_equals_U_positive_denominator", self.d, 2 * self.L),
            ("L_equals_U_candidate", self.k, self.L * self.d),
        ]:
            self.identity(label, lhs, rhs, basis=branch_basis)
        self.branch_checks.append({
            "branch": "L=U>0", "passed": True,
            "extra_equality_for_this_specialization_only": "U-L=0",
            "general_certificate_already_includes_branch": True,
        })

    def run(self):
        self.domain()
        self.nonnegative_sum("e", self.e, [(1, ["gap"])])
        self.nonnegative_sum("U", self.U, [(1, ["L"]), (1, ["e"])])
        self.nonnegative_sum("x", self.x, [(1, ["L"]), (1, ["left_slack"])])
        self.nonnegative_sum("d", self.d, [(1, ["L"]), (1, ["U"])])
        self.nonnegative_sum("candidate_denominator", self.x * self.d, [(1, ["x", "d"])])
        # Connect the checked polynomials to the contract's literal formulas.
        self.identity("candidate_formula", self.k * (self.L + self.U), 2 * self.L * self.U * self.d)
        self.identity("radius_formula", self.e * (self.L + self.U), (self.U - self.L) * self.d)
        self.identity("signed_residual_numerator", self.n, 2 * self.L * self.U - self.x * (self.L + self.U))
        self.identity("signed_residual_denominator", self.x * self.d, self.x * (self.L + self.U))
        upper_coefficient = 1 if self.mutation == "wrong_interior_multiplier" else 2
        self.nonnegative_sum("interval_upper", self.x * self.e - self.n, [(upper_coefficient, ["U", "left_slack"])])
        lower_sign = -1 if self.mutation == "wrong_interior_lower_sign" else 1
        self.nonnegative_sum("interval_lower", self.x * self.e + lower_sign * self.n, [(2, ["L", "right_slack"])])
        self.finish_interval_bound()
        self.finish_endpoints()
        self.max_absolute_value_slack("endpoint_L_slack", "L", 1)
        self.max_absolute_value_slack("endpoint_U_slack", "U", -1)
        competitor_target = self.d * self.t - self.e
        if self.mutation == "overstate_competitor_bound":
            competitor_target = self.d * self.t - 2 * self.e
        if self.mutation == "uncancelled_predictor":
            competitor_target += self.a
        self.nonnegative_sum("competitor_gap", competitor_target, [(1, ["endpoint_L_slack"]), (1, ["endpoint_U_slack"])])
        self.finish_competitor()
        self.degenerate_branch()
        require(set(self.obligations) == {"uniform_interval_bound", "both_endpoint_equalities", "all_real_competitor_lower_bound"}, "Incomplete obligation coverage")
        require(all(self.obligations.values()), "An obligation did not pass")
        require(any(item["method"].startswith("libSingular") for item in self.identities), "No meaningful Singular reduction occurred")
        return self

    def report(self):
        return {
            "kind": "universal semialgebraic nonnegative-polynomial certificates with explicit ordered-real bridges",
            "ring": str(self.ring),
            "coefficient_field": "QQ",
            "groebner_algorithm": "libsingular:std",
            "definitions_generating_ideal": [str(p) for p in self.definitions],
            "groebner_basis": [str(p) for p in self.basis],
            "ordered_domain_atoms": ["L>0", "U-L>=0", "x-L>=0", "U-x>=0"],
            "auxiliary_definitions": ["d=L+U", "k=2*L*U", "e=U-L", "n=k-x*d", "t=max(abs(a/L-1),abs(a/U-1))"],
            "predictor_domain": "a is any real number; no sign restriction",
            "identities": self.identities,
            "nonnegative_facts": {name: {"polynomial": str(f["polynomial"]), "strict": f["strict"], "source": f["source"]} for name, f in self.facts.items()},
            "logical_steps": self.logical_steps,
            "obligation_checks": self.obligations,
            "branch_checks": self.branch_checks,
            "branch_coverage": {"L=U>0": True, "0<L<U": True, "a<0": True, "a=0": True, "a>0": True},
            "trust_boundary": TRUST_BOUNDARY,
            "formal_Lean_proof_claim": False,
        }


def self_tests(PolynomialRing, QQ, contract_raw):
    outcomes = []
    for mutation in [
        "wrong_interior_multiplier", "wrong_interior_lower_sign",
        "wrong_upper_endpoint_sign", "overstate_competitor_bound",
        "uncancelled_predictor", "weaken_L_to_nonnegative",
        "drop_interior_premise",
    ]:
        try:
            Checker(PolynomialRing, QQ, mutation=mutation).run()
        except CertificateFailure as exc:
            outcomes.append({"mutation": mutation, "rejected": True, "reason": str(exc)})
        else:
            raise CertificateFailure("Negative control was unexpectedly accepted: " + mutation)
    try:
        validate_contract_bytes(contract_raw + b"\n")
    except CertificateFailure as exc:
        outcomes.append({"mutation": "contract_bytes_changed", "rejected": True, "reason": str(exc)})
    else:
        raise CertificateFailure("Modified contract bytes were unexpectedly accepted")
    return {"requested": True, "passed": all(x["rejected"] for x in outcomes), "negative_controls": outcomes}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", required=True, type=Path, help="Exact JSON contract whose bytes match the pinned SHA-256")
    parser.add_argument("--self-test", action="store_true", help="Also require all exact negative/mutation controls to be rejected")
    args = parser.parse_args()
    # Validate the file before importing the backend. A hash mismatch is never
    # treated as a valid run of a modified theorem.
    contract_raw = args.contract.read_bytes()
    validate_contract_bytes(contract_raw)
    from sage.all import PolynomialRing, QQ
    from sage.env import SAGE_VERSION
    checker = Checker(PolynomialRing, QQ).run()
    controls = self_tests(PolynomialRing, QQ, contract_raw) if args.self_test else {"requested": False, "passed": None}
    entire_chain_passed = all(checker.obligations.values()) and (not args.self_test or controls["passed"])
    require(entire_chain_passed, "The entire certificate chain did not pass")
    output = {
        "checks": {TARGET: bool(entire_chain_passed)},
        "domain_assumption_diff": [],
        "counterexample": None,
        "execution_status": "certificate_chain_checked",
        "source_sha256": sha256(Path(__file__).read_bytes()),
        "contract_sha256": sha256(contract_raw),
        "contract_path": str(args.contract.resolve()),
        "actual_argv": [sys.executable] + sys.argv,
        "runtime": {"sage_version": str(SAGE_VERSION), "python_version": sys.version.split()[0]},
        "statement_alignment": {"contract_id": CONTRACT_ID, "exact_statement": STATEMENT, "aligned": True},
        "proof_coverage": checker.obligations,
        "certificate_details": checker.report(),
        "self_test": controls,
        "claim_ceiling": "finite mathematical component only; no scientific admission; parent CAS-13 remains open",
        "authorship": {"input_exposure": "task instructions and pinned C04 contract only; no sibling source or result reads", "model_identity": "unknown", "cross_model_independence_claim": False, "formal_blind_authorship_claim": False},
    }
    # Prepare the complete string before the first stdout write. Failed imports,
    # reductions, controls, serialization, or logical checks emit no target bool.
    rendered = json.dumps(output, sort_keys=True, indent=2)
    sys.stdout.write(rendered + "\n")
    return 0


if __name__ == "__main__":
    try:
        exit_status = main()
    except Exception as exc:
        sys.stderr.write(json.dumps({"execution_status": "error", "error_type": type(exc).__name__, "message": str(exc)}, sort_keys=True) + "\n")
        exit_status = 2
    sys.exit(exit_status)
