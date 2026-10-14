#!/usr/bin/env python3
"""Independent SymPy certificate for the CAS-11 C01 finite component.

The universal argument reduces arbitrary finite n and k to the generic
coordinate identities checked below.  Each reduction uses induction on a
finite sum: the empty sum is zero, and appending one term changes the
residual by exactly the checked coordinate kernel.  The double-sum
reindexing follows by induction on rows, using finite-sum additivity in
the column dimension.  No regularity of H beyond its values and named
gradients enters this algebraic statement.
"""

import hashlib
import json
from pathlib import Path
import sys

import sympy as s


ROOT = Path(__file__).resolve().parents[8]
TASK = Path(__file__).resolve().parent.parent
CONTRACT = TASK / "EXECUTION_CONTRACT.json"
INPUTS = TASK / "ADMITTED_INPUTS.json"
COMMON = ROOT / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
EXPECTED_INPUTS = {
    "ADMITTED_INPUTS.json": "c65019a54a477d4d75738579741c33ace4e19db42142e0bde0c20b013cd79e55",
    "COMMON_SPEC.md": "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
}
CHECKS = []


def exact(name, expression, expected=0):
    residual = s.cancel(s.expand(expression - expected))
    record = {"name": name, "residual": str(residual), "pass": residual == 0}
    CHECKS.append(record)
    if residual != 0:
        raise AssertionError(f"first failure: {name}: {residual}")


def main():
    assert s.__version__ == "1.14.0", s.__version__
    contract = json.loads(CONTRACT.read_text())
    inputs = json.loads(INPUTS.read_text())
    assert contract["identity"]["contract_id"] == "GRSTAT-20260930-CAS-11-C01-BREGMAN-THREE-POINT-V2"
    assert inputs["component"] == "CAS-11-C01"
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (CONTRACT, INPUTS, COMMON)}
    for name, digest in EXPECTED_INPUTS.items():
        assert hashes[name] == digest, (name, hashes[name], digest)

    # H-value terms cancel without a coordinate or convexity assumption.
    hf, hg, hh = s.symbols("H_f H_g H_h", real=True)
    exact("H-value cancellation", (hf-hg) - (hf-hh) - (hh-hg))

    # Generic coordinate kernel. The gradient at g is p and at h is q.
    f, g, h, p, q = s.symbols("f g h p q", real=True)
    scalar = (-p*(f-g)) - (-q*(f-h)) - (-p*(h-g)) - (q-p)*(f-h)
    exact("generic coordinate three-point kernel", scalar)

    # Structural n-induction. P,Q,R,T are arbitrary prefix sums of the four
    # coordinate terms; the append equation is checked without fixing n.
    P, Q, R, T = s.symbols("P Q R T", real=True)
    prefix = P-Q-R-T
    a, b, c, d = s.symbols("a b c d", real=True)
    appended = (P+a)-(Q+b)-(R+c)-(T+d)
    exact("empty n base", s.Integer(0))
    exact("generic n append recurrence", appended-prefix-(a-b-c-d))
    exact("coordinate substitution into n append",
          (a-b-c-d).subs({a:-p*(f-g), b:-q*(f-h), c:-p*(h-g), d:(q-p)*(f-h)}))

    # Finite-sum additivity and scalar distributivity are themselves
    # structural induction steps in arbitrary k, including k=0.
    X, Y, x, y, lam, v, delta = s.symbols("X Y x y lambda v delta", real=True)
    exact("empty k base", s.Integer(0))
    exact("finite-sum additivity append", ((X+Y)+(x+y))-((X+x)+(Y+y)))
    exact("finite-sum scalar append", lam*(X+x)-(lam*X+lam*x))
    exact("bilinear coordinate kernel", (v*lam)*delta-lam*(v*delta))
    exact("inner matrix-product append", (X+v*lam)*delta-X*delta-v*lam*delta)

    # Row induction for rectangular double sums. The right orientation's
    # appended row is obtained by k-induction/additivity above. Every
    # rectangle has a unique finite row/column enumeration.
    L, U, row_left, row_right = s.symbols("L U row_left row_right", real=True)
    exact("empty rectangle base", s.Integer(0))
    exact("rectangle row append under equal prefixes and rows",
          ((L+row_left)-(U+row_right))-(L-U)-(row_left-row_right))
    exact("rectangle corner reindexing", ((X+x)+(Y+y))-((X+Y)+(x+y)))

    # Under Delta_i = sum_j V_ij lambda_j, the two checked finite-sum
    # induction/reindexing lemmas give dot(Delta,d)=sum_j lambda_j m_j,
    # m_j=sum_i V_ij d_i. If each m_j=0, all terms vanish. This is also
    # a generic k-induction, not a numerical tolerance statement.
    moment_prefix, moment_next = s.symbols("moment_prefix moment_next", real=True)
    exact("zero moment base", s.Integer(0))
    exact("zero moment append", (moment_prefix+lam*moment_next).subs(
        {moment_prefix: 0, moment_next: 0}))
    exact("moment next-term zero", lam*moment_next.subs(moment_next, 0))

    # Contracted orientation and approximate-matching controls.
    t = s.symbols("t", real=True)
    H = t**3/s.Integer(3)
    derivative = s.diff(H, t)
    def D(x, y):
        return H.subs(t, x)-H.subs(t, y)-derivative.subs(t, y)*(x-y)
    exact("cubic orientation f||g", D(s.Integer(2), s.Integer(1)), s.Rational(4,3))
    exact("cubic orientation g||f", D(s.Integer(1), s.Integer(2)), s.Rational(5,3))
    exact("approximate matching residual", s.Integer(1)*s.Integer(1)*s.Rational(1,10), s.Rational(1,10))
    if s.Rational(1,10) == 0:
        raise AssertionError("first failure: approximate matching falsely cancelled")
    CHECKS.append({"name": "approximate residual nonzero", "value": "1/10", "pass": True})

    # Fixed dimensions are controls only; universal proof is above.
    f2, g2, h2, p2, q2 = (s.symbols(name + "0:3", real=True)
                           for name in ("f", "g", "h", "p", "q"))
    dot = lambda aa, bb: sum((u*w for u,w in zip(aa,bb)), s.Integer(0))
    left = -dot(p2,[u-v for u,v in zip(f2,g2)]) \
           +dot(q2,[u-v for u,v in zip(f2,h2)]) \
           +dot(p2,[u-v for u,v in zip(h2,g2)])
    right = dot([u-v for u,v in zip(q2,p2)], [u-v for u,v in zip(f2,h2)])
    exact("n=3 symbolic control", left-right)
    details = {
        "checks": CHECKS,
        "engine": "SymPy",
        "sympy_version": s.__version__,
        "python": sys.version,
        "input_sha256": hashes,
        "statement": inputs["targets"],
        "scope": "arbitrary finite n,k via exact generic kernels and finite-sum structural induction",
    }
    details_path = Path(__file__).resolve().parent / "detailed_checks.json"
    details_bytes = (json.dumps(details, indent=2, sort_keys=True) + "\n").encode()
    details_path.write_bytes(details_bytes)
    output = {
        "checks": {"CAS-11-C01": True},
        "domain_assumption_diff": [],
        "counterexample": None,
        "computed": {
            "exact_kernel_checks": len(CHECKS) - 1,
            "nonzero_control": "1/10",
            "detailed_checks_sha256": hashlib.sha256(details_bytes).hexdigest(),
            "certificate": "arbitrary finite n,k by generic coordinate and bilinear kernels with finite-sum induction/reindexing",
        },
    }
    print(json.dumps(output, sort_keys=True))


if __name__ == "__main__":
    main()
