#!/usr/bin/env python3
"""Exact, fail-closed C04 proof-certificate checker. See SYMPY_CERTIFICATE_SCOPE.md.

Only standard-library imports occur before the sealed contract is authenticated.
This file prepares a local SymPy check; it does not install any package.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import sys
from dataclasses import dataclass
from typing import Any


COMPONENT = "CAS13-C04-RELATIVE-MINIMAX"
CONTRACT_SHA256 = "0002809c73fd5de362deded39735fe884183bb953029f671552a525f74086f63"
EXACT_TARGETS = [
    "For every x in [L,U], loss(a_star,x)<=r_star",
    "loss(a_star,L)=r_star and loss(a_star,U)=r_star",
    "For every real a, r_star<=max(loss(a,L),loss(a,U))",
]
EXACT_DOMAIN = {
    "field": "real",
    "base_variables": ["L", "U", "a"],
    "base_assumptions": ["L > 0", "U - L >= 0"],
    "interval_variable": "x",
    "interval_assumptions": ["x - L >= 0", "U - x >= 0"],
    "predictor_restriction": None,
    "auxiliary_definition": "t = max(abs(a/L - 1), abs(a/U - 1))",
}


class CertificateError(Exception):
    """A rejected certificate is not a mathematical counterexample."""


class DomainError(CertificateError):
    def __init__(self, supplied: Any):
        super().__init__("certificate domain differs from the complete target domain")
        self.diff = [{"expected": EXACT_DOMAIN, "supplied": supplied}]


def authenticate_contract(path: Path) -> dict:
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != CONTRACT_SHA256:
        raise CertificateError(f"sealed contract SHA-256 mismatch: {digest}")
    contract = json.loads(raw)
    if contract["target"]["exact_statement"] != EXACT_TARGETS:
        raise CertificateError("sealed contract statement alignment failed")
    if contract["target"]["exact_test_obligations"] != [COMPONENT]:
        raise CertificateError("sealed contract component alignment failed")
    if contract["semantics"]["field"] != "real":
        raise CertificateError("sealed contract field alignment failed")
    return contract


@dataclass(frozen=True)
class PolyFact:
    expr: Any
    strict: bool
    rule: str


@dataclass(frozen=True)
class Rat:
    numerator: Any
    denominator: Any
    denominator_fact: PolyFact


@dataclass(frozen=True)
class NonnegativeRat:
    value: Rat
    rule: str


@dataclass(frozen=True)
class MaxAbsDefinition:
    symbol: Any
    entries: tuple[Rat, Rat]


class OrderedRealKernel:
    """Small proof-rule boundary, not a general solver or a proof-assistant kernel.

    All equalities are exact polynomial identities over QQ. Positivity comes only
    from declared domain generators, positive-coefficient sums/products, positive
    denominators, or the explicit absolute-value/max order rules below.
    """

    def __init__(self, sp: Any, symbols: tuple, interval: bool):
        self.sp, self.symbols = sp, symbols
        L, U, x, a, t = symbols
        self.facts = {
            "L": PolyFact(L, True, "domain: L > 0"),
            "gap": PolyFact(U - L, False, "domain: U - L >= 0"),
        }
        if interval:
            self.facts.update({
                "lo": PolyFact(x - L, False, "domain: x - L >= 0"),
                "hi": PolyFact(U - x, False, "domain: U - x >= 0"),
            })
        self.log: list[dict] = []
        self.identity_count = 0
        self.denominator_checks = 0

    def polynomial_equal(self, left: Any, right: Any) -> bool:
        # Reject floats explicitly: QQ can otherwise rationalize a Float input.
        # Do not parse untrusted strings as SymPy expressions.
        operands = []
        for value in (left, right):
            if type(value) is int:
                value = self.sp.Integer(value)
            if not isinstance(value, self.sp.Expr) or value.has(self.sp.Float):
                raise CertificateError("polynomial operands must be exact symbolic expressions")
            operands.append(value)
        left, right = operands
        # QQ rejects other symbolic coefficient fields and rational functions
        # in the generators. No numerical tolerance is used.
        delta = self.sp.Poly(self.sp.expand(left - right), *self.symbols,
                             domain=self.sp.QQ)
        return delta.is_zero is True

    def require_equal(self, left: Any, right: Any, name: str) -> None:
        if not self.polynomial_equal(left, right):
            raise CertificateError(f"polynomial identity rejected: {name}")
        self.identity_count += 1

    def add_sign_certificate(self, node: dict) -> None:
        if set(node) != {"name", "target", "terms", "require"}:
            raise CertificateError("unknown or missing sign-certificate fields")
        name, requirement = node["name"], node["require"]
        if name in self.facts or requirement not in {"positive", "nonnegative"}:
            raise CertificateError(f"invalid sign-certificate declaration: {name}")
        if not isinstance(node["terms"], list) or not node["terms"]:
            raise CertificateError("a sign certificate needs nonempty terms")
        total = self.sp.Integer(0)
        some_strict_term = False
        normalized_terms = []
        for term in node["terms"]:
            if set(term) != {"coefficient", "factors"}:
                raise CertificateError("invalid nonnegative-polynomial term")
            raw_coefficient = term["coefficient"]
            if not isinstance(raw_coefficient, str) or not re.fullmatch(
                    r"[+-]?\d+(?:/\d+)?", raw_coefficient):
                raise CertificateError("coefficients must be exact rational strings")
            coefficient = self.sp.Rational(raw_coefficient)
            if coefficient <= 0:
                raise CertificateError("a cone coefficient must be strictly positive")
            if not isinstance(term["factors"], list):
                raise CertificateError("factors must be a list of proved fact names")
            product, term_strict = self.sp.Integer(1), True
            for factor in term["factors"]:
                if not isinstance(factor, str) or factor not in self.facts:
                    raise CertificateError(f"unproved sign factor: {factor}")
                fact = self.facts[factor]
                product *= fact.expr
                term_strict = term_strict and fact.strict
            total += coefficient * product
            some_strict_term = some_strict_term or term_strict
            normalized_terms.append({"coefficient": str(coefficient),
                                     "factors": term["factors"]})
        self.require_equal(node["target"], total, name)
        if requirement == "positive" and not some_strict_term:
            raise CertificateError(f"strict positivity is not certified: {name}")
        self.facts[name] = PolyFact(node["target"], some_strict_term,
                                    "positive-coefficient sum of nonnegative products")
        self.log.append({"name": name, "polynomial": str(node["target"]),
                         "strictly_positive": some_strict_term,
                         "terms": normalized_terms})

    def check_denominator(self, denominator: Any, fact: PolyFact) -> None:
        self.require_equal(denominator, fact.expr, "denominator sign binding")
        if not fact.strict:
            raise CertificateError("denominator is not proved strictly positive")
        self.denominator_checks += 1

    def rat(self, numerator: Any, denominator: Any, fact: PolyFact) -> Rat:
        self.check_denominator(denominator, fact)
        return Rat(numerator, denominator, fact)

    def polynomial_rat(self, value: Any) -> Rat:
        one = self.sp.Integer(1)
        return self.rat(value, one, PolyFact(one, True, "1 > 0"))

    def negate(self, q: Rat) -> Rat:
        return self.rat(-q.numerator, q.denominator, q.denominator_fact)

    def add(self, left: Rat, right: Rat) -> Rat:
        self.check_denominator(left.denominator, left.denominator_fact)
        self.check_denominator(right.denominator, right.denominator_fact)
        denominator = left.denominator * right.denominator
        fact = PolyFact(denominator, True, "product of positive denominators")
        return self.rat(left.numerator * right.denominator
                        + right.numerator * left.denominator, denominator, fact)

    def subtract(self, left: Rat, right: Rat) -> Rat:
        return self.add(left, self.negate(right))

    def divide_positive(self, q: Rat, polynomial: Any, fact: PolyFact) -> Rat:
        self.check_denominator(q.denominator, q.denominator_fact)
        self.check_denominator(polynomial, fact)
        denominator = q.denominator * polynomial
        return self.rat(q.numerator, denominator,
                        PolyFact(denominator, True, "product of positive denominators"))

    def rational_equal(self, left: Rat, right: Rat, name: str) -> None:
        self.check_denominator(left.denominator, left.denominator_fact)
        self.check_denominator(right.denominator, right.denominator_fact)
        self.require_equal(left.numerator * right.denominator,
                           right.numerator * left.denominator, name)

    def rational_nonnegative(self, value: Rat, numerator_fact: PolyFact) -> NonnegativeRat:
        self.check_denominator(value.denominator, value.denominator_fact)
        self.require_equal(value.numerator, numerator_fact.expr, "numerator sign binding")
        return NonnegativeRat(value, "nonnegative numerator / positive denominator")

    def transport_nonnegative(self, target: Rat, evidence: NonnegativeRat,
                              name: str) -> NonnegativeRat:
        self.rational_equal(target, evidence.value, name)
        return NonnegativeRat(target, "equality substitution in >= 0")

    def abs_upper(self, q: Rat, bound: Rat, plus: NonnegativeRat,
                  minus: NonnegativeRat, bound_sign: NonnegativeRat) -> str:
        self.rational_equal(bound, bound_sign.value, "absolute bound is nonnegative")
        self.rational_equal(self.add(bound, q), plus.value, "bound + value >= 0")
        self.rational_equal(self.subtract(bound, q), minus.value, "bound - value >= 0")
        return "abs_le: (-bound <= value <= bound) iff abs(value) <= bound"

    def abs_equal(self, q: Rat, bound: Rat, sign: int,
                  bound_sign: NonnegativeRat) -> str:
        if sign not in {-1, 1}:
            raise CertificateError("absolute equality requires sign +1 or -1")
        self.rational_equal(bound, bound_sign.value, "absolute equality bound >= 0")
        rhs = bound if sign == 1 else self.negate(bound)
        self.rational_equal(q, rhs, "endpoint signed equality")
        return "abs_eq: bound >= 0 and value = +/-bound imply abs(value) = bound"

    def max_projection(self, definition: MaxAbsDefinition, index: int,
                       sign: int) -> NonnegativeRat:
        if index not in {0, 1} or sign not in {-1, 1}:
            raise CertificateError("invalid absolute maximum projection")
        q = definition.entries[index]
        signed_q = q if sign == 1 else self.negate(q)
        difference = self.add(self.polynomial_rat(definition.symbol), signed_q)
        return NonnegativeRat(difference,
            "t=max(abs(q0),abs(q1)) implies t >= abs(qi) >= +/-qi")

    def clear_positive_denominator(self, evidence: NonnegativeRat) -> PolyFact:
        q = evidence.value
        self.check_denominator(q.denominator, q.denominator_fact)
        return PolyFact(q.numerator, False,
                        "q >= 0 and denominator > 0 imply numerator >= 0")


def build_certificate(sp: Any) -> dict:
    L, U, x, a, t = sp.symbols("L U x a t", real=True)
    S, gap = L + U, U - L

    def node(name: str, target: Any, terms: list, positive: bool = False) -> dict:
        return {"name": name, "target": target,
                "terms": [{"coefficient": c, "factors": factors} for c, factors in terms],
                "require": "positive" if positive else "nonnegative"}

    return {
        "domain": copy.deepcopy(EXACT_DOMAIN),
        "base": [
            node("U", U, [("1", ["L"]), ("1", ["gap"])], True),
            node("S", S, [("2", ["L"]), ("1", ["gap"])], True),
            node("LS", L * S, [("1", ["L", "S"])], True),
            node("US", U * S, [("1", ["U", "S"])], True),
        ],
        "interval": [
            node("x", x, [("1", ["L"]), ("1", ["lo"])], True),
            node("xS", x * S, [("1", ["x", "S"])], True),
            node("upper_numerator", 2 * U * (x - L), [("2", ["U", "lo"])]),
            node("lower_numerator", 2 * L * (U - x), [("2", ["L", "hi"])]),
        ],
        "minimax": [
            node("minimax_numerator", S * t - gap,
                 [("1", ["left_projection"]), ("1", ["right_projection"])])
        ],
    }


def _apply_nodes(kernel: OrderedRealKernel, nodes: Any, expected: list[str]) -> None:
    if not isinstance(nodes, list) or [n.get("name") for n in nodes] != expected:
        raise CertificateError("missing, extra, or reordered certificate nodes")
    for node in nodes:
        kernel.add_sign_certificate(node)


def verify_certificate(certificate: dict, sp: Any) -> dict:
    """Callable verifier. Raises on rejection; never treats rejection as a witness.

    The supplied data contain algebraic sign certificates, not executable code.
    The theorem formulas and inference rules are fixed in this verifier.
    """
    if set(certificate) != {"domain", "base", "interval", "minimax"}:
        raise CertificateError("certificate section mismatch")
    if certificate["domain"] != EXACT_DOMAIN:
        raise DomainError(certificate["domain"])
    symbols = sp.symbols("L U x a t", real=True)
    L, U, x, a, t = symbols
    S, gap = L + U, U - L
    base = OrderedRealKernel(sp, symbols, interval=False)
    interval = OrderedRealKernel(sp, symbols, interval=True)
    for kernel in (base, interval):
        _apply_nodes(kernel, certificate["base"], ["U", "S", "LS", "US"])
    _apply_nodes(interval, certificate["interval"],
                 ["x", "xS", "upper_numerator", "lower_numerator"])

    def definitions(kernel: OrderedRealKernel) -> tuple[Rat, Rat, NonnegativeRat]:
        a_star = kernel.rat(2 * L * U, S, kernel.facts["S"])
        error = kernel.rat(gap, S, kernel.facts["S"])
        error_nn = kernel.rational_nonnegative(error, kernel.facts["gap"])
        return a_star, error, error_nn

    # Universal interval theorem: e-y = 2U(x-L)/(xS), e+y = 2L(U-x)/(xS).
    star_i, error_i, error_i_nn = definitions(interval)
    yx = interval.subtract(interval.divide_positive(star_i, x, interval.facts["x"]),
                           interval.polynomial_rat(1))
    upper = interval.rat(2 * U * (x - L), x * S, interval.facts["xS"])
    lower = interval.rat(2 * L * (U - x), x * S, interval.facts["xS"])
    upper_nn = interval.rational_nonnegative(upper, interval.facts["upper_numerator"])
    lower_nn = interval.rational_nonnegative(lower, interval.facts["lower_numerator"])
    minus = interval.transport_nonnegative(interval.subtract(error_i, yx), upper_nn,
                                           "interval upper factorization")
    plus = interval.transport_nonnegative(interval.add(error_i, yx), lower_nn,
                                          "interval lower factorization")
    bound_rule = interval.abs_upper(yx, error_i, plus, minus, error_i_nn)

    # Endpoint equalities use the base context alone; no x assumptions enter.
    star, error, error_nn = definitions(base)
    yL = base.rat(2 * L * U - L * S, L * S, base.facts["LS"])
    yU = base.rat(2 * L * U - U * S, U * S, base.facts["US"])
    for q, endpoint, fact_name in ((yL, L, "L"), (yU, U, "U")):
        original = base.subtract(base.divide_positive(star, endpoint, base.facts[fact_name]),
                                  base.polynomial_rat(1))
        base.rational_equal(q, original, "endpoint binding to a_star/endpoint - 1")
    endpoint_rules = [base.abs_equal(yL, error, 1, error_nn),
                      base.abs_equal(yU, error, -1, error_nn)]

    # t is a definitional auxiliary, not an additional restriction on a.
    zL = base.rat(a - L, L, base.facts["L"])
    zU = base.rat(a - U, U, base.facts["U"])
    max_definition = MaxAbsDefinition(t, (zL, zU))
    left = base.max_projection(max_definition, 0, -1)  # t - (a/L - 1) >= 0
    right = base.max_projection(max_definition, 1, 1)  # t + (a/U - 1) >= 0
    base.facts["left_projection"] = base.clear_positive_denominator(left)
    base.facts["right_projection"] = base.clear_positive_denominator(right)
    _apply_nodes(base, certificate["minimax"], ["minimax_numerator"])
    difference = base.rat(S * t - gap, S, base.facts["S"])
    difference_nn = base.rational_nonnegative(difference, base.facts["minimax_numerator"])
    final_difference = base.subtract(base.polynomial_rat(t), error)
    base.transport_nonnegative(final_difference, difference_nn,
                                "t - r_star is nonnegative")

    # Each entry is constructed only after its complete rule chain has succeeded.
    proven_targets = {
        EXACT_TARGETS[0]: {"rule": bound_rule, "context": "interval"},
        EXACT_TARGETS[1]: {"rules": endpoint_rules, "context": "base"},
        EXACT_TARGETS[2]: {"rule": "max projections + positive denominator clearing + order",
                           "context": "base", "auxiliary_definition": EXACT_DOMAIN["auxiliary_definition"]},
    }
    coverage_complete = set(proven_targets) == set(EXACT_TARGETS)
    # Boundary audit: gap is allowed to be zero, and a is absent from domain facts.
    boundary_preserved = (not base.facts["gap"].strict
                           and certificate["domain"]["predictor_restriction"] is None
                           and all(a not in fact.expr.free_symbols
                                   for key, fact in base.facts.items()
                                   if key in {"L", "gap", "U", "S", "LS", "US"}))
    if not coverage_complete or not boundary_preserved:
        raise CertificateError("incomplete theorem coverage or excluded domain branch")
    return {
        "checks": {COMPONENT: coverage_complete and boundary_preserved},
        "domain_assumption_diff": [],
        "counterexample": None,
        "status": "PASS_CERTIFICATE",
        "statement_alignment": {"exact_statement": EXACT_TARGETS,
                                 "domain": certificate["domain"]},
        "proof_coverage": proven_targets,
        "certificate_details": {
            "base_sign_certificates": base.log,
            "interval_sign_certificates": interval.log,
            "exact_polynomial_identity_checks": base.identity_count + interval.identity_count,
            "strict_denominator_checks": base.denominator_checks + interval.denominator_checks,
            "branches": ["L=U>0", "0<L<U", "a<0", "a=0", "a>0"],
            "method": "exact nonnegative polynomial certificates and explicit ordered-real rules",
            "trust_boundary": ["Python implementation of the listed proof rules",
                               "SymPy exact rational polynomial arithmetic",
                               "ordered real field and absolute value / finite maximum laws"],
            "not_claimed": ["proof-assistant kernel checking", "general quantifier elimination",
                            "scientific admission", "validation of other CAS-13 components",
                            "construction of a supremum operator"],
        },
    }


def run_mutation_controls(sp: Any) -> dict[str, bool]:
    """All controls must reject; these are certificate-integrity checks, not sampling."""
    controls: dict[str, bool] = {}
    mutations = {
        "corrupt_positive_coefficient": lambda c: c["interval"][2]["terms"][0].update(coefficient="3"),
        "corrupt_nonnegative_sign": lambda c: c["interval"][3]["terms"][0].update(coefficient="-2"),
        "drop_strict_positive_domain": lambda c: c["domain"]["base_assumptions"].__setitem__(0, "L >= 0"),
        "exclude_equal_endpoints": lambda c: c["domain"]["base_assumptions"].__setitem__(1, "U - L > 0"),
        "restrict_predictor": lambda c: c["domain"].update(predictor_restriction="a > 0"),
        "corrupt_denominator_sign": lambda c: c["base"][1].update(target=-c["base"][1]["target"]),
        "missing_universal_lower_bound": lambda c: c.update(minimax=[]),
    }
    for name, mutate in mutations.items():
        corrupted = build_certificate(sp)
        mutate(corrupted)
        try:
            verify_certificate(corrupted, sp)
        except CertificateError:
            controls[name] = True
        else:
            controls[name] = False
    return controls


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True,
                        help="exact sealed CAS13-C04-RELATIVE-MINIMAX.json bytes")
    parser.add_argument("--self-test", action="store_true",
                        help="also require coefficient, sign, and domain mutation rejection")
    args = parser.parse_args(argv)
    try:
        contract = authenticate_contract(args.contract)
    except (OSError, ValueError, KeyError, TypeError, CertificateError) as exc:
        # No scientific payload, no SymPy import, and no success JSON on bad input.
        print(f"CONTRACT_REJECTED: {exc}", file=sys.stderr)
        return 2
    try:
        import sympy as sp
    except ImportError as exc:
        print(f"DEPENDENCY_UNAVAILABLE: {exc}", file=sys.stderr)
        return 3
    try:
        payload = verify_certificate(build_certificate(sp), sp)
        if args.self_test:
            controls = run_mutation_controls(sp)
            payload["mutation_controls"] = controls
            if not controls or not all(controls.values()):
                raise CertificateError("a corrupted-certificate mutation was accepted")
        exit_code = 0 if payload["checks"][COMPONENT] else 1
    except CertificateError as exc:
        # A rejected certificate is not a disproof of the target. Keep it off
        # the scientific-result channel; the host must record INCONCLUSIVE.
        print(json.dumps({"execution_status": "certificate_rejected",
                          "domain_assumption_diff": getattr(exc, "diff", []),
                          "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        return 1
    except Exception as exc:
        # Backend/API errors also must not become checks[target]=False.
        print(json.dumps({"execution_status": "error",
                          "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        return 3
    payload["contract_sha256"] = CONTRACT_SHA256
    payload["source_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    payload["execution"] = {"argv": sys.argv if argv is None else [sys.argv[0], *argv],
                            "python_version": sys.version, "sympy_version": sp.__version__,
                            "exit_code": exit_code}
    payload["claim_ceiling"] = contract["identity"]["claim_ceiling"]
    payload["parent_remains_open"] = contract["full_theorem_boundary"]["parent_remains_open"]
    print(json.dumps(payload, sort_keys=True, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
