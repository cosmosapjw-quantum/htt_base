#!/usr/bin/env python3
"""Independent SymPy certificates for the frozen CAS-02 C01--C03 components."""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import mpmath as mp
import sympy as sp


ROOT = Path(__file__).resolve().parents[8]
BASE = Path(__file__).resolve().parent.parent
CONTRACT = BASE / "EXECUTION_CONTRACT.json"
INPUTS = BASE / "ADMITTED_INPUTS.json"
COMMON = ROOT / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
RESULT = Path(__file__).with_name("result.json")
EXPECTED = {
    str(CONTRACT): "f1df856a0da477256e8adfbb889001d75fd659dda6f834ea72e87f314ff844a8",
    str(INPUTS): "e7cfe79d7ad075899ee75f166687f40363e207ba334da3d8733fa2ab5a4b82bd",
    str(COMMON): "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def zero(expression: sp.Expr, label: str) -> str:
    residual = sp.factor(sp.cancel(sp.expand(expression)))
    if residual != 0:
        raise AssertionError(f"{label}: residual {residual}")
    return "exact zero polynomial/rational residual"


def matrix_zero(matrix: sp.MatrixBase, label: str) -> str:
    for i in range(matrix.rows):
        for j in range(matrix.cols):
            zero(matrix[i, j], f"{label}[{i},{j}]")
    return "all entries exact zero"


def optical(h0: sp.Expr, h1: sp.Matrix, h2: sp.Matrix) -> sp.Matrix:
    return sp.Matrix.vstack(
        sp.Matrix([[h0, -h1[0] / 2, -h1[1] / 2, -h1[2] / 2]]),
        sp.Matrix.hstack(-h1 / 2, h2),
    )


def c01() -> dict:
    a0, b0 = sp.symbols("a0 b0", real=True)
    av = sp.Matrix(sp.symbols("a1:4", real=True))
    bv = sp.Matrix(sp.symbols("b1:4", real=True))
    aa, ab, ac, ad, ae = sp.symbols("aa ab ac ad ae", real=True)
    ba, bb, bc, bd, be = sp.symbols("ba bb bc bd be", real=True)
    ah = sp.Matrix([[aa, ab, ac], [ab, ad, ae], [ac, ae, -aa - ad]])
    bh = sp.Matrix([[ba, bb, bc], [bb, bd, be], [bc, be, -ba - bd]])
    ds = optical(b0, bv, bh) - optical(a0, av, ah)
    dh = bh - ah
    frob = lambda m: sum(m[i, j] ** 2 for i in range(m.rows) for j in range(m.cols))
    target = (b0 - a0) ** 2 + sum((bv[i] - av[i]) ** 2 for i in range(3)) / 2 + frob(dh)
    zero(frob(ds) - target, "C01 delta optical squared norm")
    g = sp.diag(-1, 1, 1, 1)
    zero(frob(g) - 4, "C01 metric squared Frobenius norm")
    assert frob(g) == 4 and sp.sqrt(frob(g)) == 2
    return {
        "component": "CAS-02-C01",
        "status": "PASS",
        "certificate": "Independent real STF pairs h2_33=-h2_11-h2_22, all five free entries per pair; direct positive component sum gives zero residual for ||S2-S1||F^2-(delta h0)^2-|delta h1|^2/2-||delta h2||F^2. The diagonal metric has squared Frobenius norm four and positive norm two.",
        "domain": "All independent optical entries real; spatial h2 symmetric and tracefree; Euclidean component norms.",
    }


def c02() -> dict:
    def symmetric(prefix: str) -> sp.Matrix:
        entries = sp.symbols(" ".join(f"{prefix}{i}{j}" for i in range(4) for j in range(i, 4)), real=True)
        table = {(i, j): entries[k] for k, (i, j) in enumerate((i, j) for i in range(4) for j in range(i, 4))}
        return sp.Matrix(4, 4, lambda i, j: table[min(i, j), max(i, j)])

    s1, s2 = symmetric("A"), symmetric("B")
    u1 = sp.Matrix(sp.symbols("v0:4", real=True))
    u2 = sp.Matrix(sp.symbols("w0:4", real=True))
    du = u2 - u1
    delta = (u2.T * s2 * u2)[0] - (u1.T * s1 * u1)[0]
    first = (u2.T * (s2 - s1) * u2)[0] + (du.T * s1 * u2)[0] + (u1.T * s1 * du)[0]
    second = (u1.T * (s2 - s1) * u1)[0] + (du.T * s2 * u2)[0] + (u1.T * s2 * du)[0]
    zero(delta - first, "C02 S1 anchor")
    zero(delta - second, "C02 S2 anchor")
    return {
        "component": "CAS-02-C02",
        "status": "PASS",
        "certificate": "Two independently generated symmetric 4x4 real matrices and two independent real four-vectors give identically zero expanded residual for each anchor. No unit constraint is used; hence both identities hold for every declared future g-unit pair.",
        "first_anchor": "u2^T(S2-S1)u2+(u2-u1)^T S1 u2+u1^T S1(u2-u1)",
        "swapped_anchor": "u1^T(S2-S1)u1+(u2-u1)^T S2 u2+u1^T S2(u2-u1)",
        "domain": "All matrix/vector entries real; symmetry as declared; future g-unit vectors form a subset of the verified universal domain.",
    }


def c03() -> dict:
    d = sp.Matrix(sp.symbols("d0:3", real=True))
    q = sum(x**2 for x in d)
    u = sp.Matrix([sp.sqrt(1 + q), *d])
    jac = u.jacobian(d)
    expected_jac = sp.Matrix.vstack((d / sp.sqrt(1 + q)).T, sp.eye(3))
    matrix_zero(jac - expected_jac, "C03 actual chart derivative")
    gram = jac.T * jac
    expected_gram = sp.eye(3) + d * d.T / (1 + q)
    matrix_zero(gram - expected_gram, "C03 Gram")
    lam = sp.symbols("lambda", real=True)
    characteristic = sp.factor((lam * sp.eye(3) - gram).det())
    expected_char = (lam - 1) ** 2 * (lam - (1 + 2*q)/(1 + q))
    zero(characteristic - expected_char, "C03 characteristic polynomial")
    matrix_zero(gram * d - ((1 + 2*q)/(1 + q))*d, "C03 radial eigenvector")
    z = sp.Matrix(sp.symbols("z0:3", real=True))
    matrix_zero((gram-sp.eye(3))*z - d*(d.dot(z))/(1+q), "C03 transverse eigenspace")
    gram_at_zero = gram.subs({x: 0 for x in d})
    assert gram_at_zero == sp.eye(3)
    zero(characteristic.subs({x: 0 for x in d}) - (lam-1)**3, "C03 zero chart triple root")

    # The norm inequality has an admissible point only if sinh(R)>=0, hence R>=0
    # by strict monotonicity of real sinh. Put b=sinh(R), q=|d|^2.
    b, qq = sp.symbols("b qq", nonnegative=True, real=True)
    f = lambda x: x/(1+x)
    difference = sp.factor(f(b*b)-f(qq))
    zero(difference - (b*b-qq)/((1+b*b)*(1+qq)), "C03 bound difference")
    R = sp.symbols("R", real=True)
    zero(sp.sinh(R)**2/(1+sp.sinh(R)**2)-sp.tanh(R)**2, "C03 hyperbolic endpoint")
    assert sp.ask(sp.Q.positive(1+qq)) is True
    assert sp.ask(sp.Q.positive(1+b*b)) is True
    return {
        "component": "CAS-02-C03",
        "status": "PASS",
        "certificate": "Differentiating the actual positive-root chart yields Du=[d^T/sqrt(1+q);I3], q=sum d_i^2>=0; 1+q>0. Its Gram equals I3+dd^T/(1+q), and the checked determinant is (lambda-1)^2(lambda-(1+2q)/(1+q)). For q>0, d is a radial eigenvector, and the orthogonal plane has eigenvalue 1 twice; q=0 gives I3 and a triple eigenvalue 1. Thus the largest is 1+q/(1+q). If |d|<=sinh R, then sinh R>=0 and strict monotonicity of real sinh with sinh 0=0 derives R>=0. With b=sinh R and 0<=q<=b^2, checked difference b^2/(1+b^2)-q/(1+q)=(b^2-q)/((1+b^2)(1+q))>=0. Both denominators are strictly positive; 1+sinh(R)^2=cosh(R)^2>0 yields the checked endpoint tanh(R)^2. No target inequality was assumed.",
        "jacobian": "[d^T/sqrt(1+q); I3]",
        "gram": "I3+dd^T/(1+q)",
        "characteristic_polynomial": str(expected_char),
        "eigenvalues_q_positive": ["1 (multiplicity 2)", "(1+2q)/(1+q) (multiplicity 1)"],
        "eigenvalues_q_zero": ["1 (multiplicity 3)"],
        "largest": "1+q/(1+q)",
        "domain": "d in R^3, positive sqrt; q>=0 and 1+q>0. The ball premise implies R>=0; endpoint R=0 and d=0 included.",
    }


def numerical_diagnostics() -> dict:
    mp.mp.dps = 80
    tol_abs, tol_rel = mp.mpf("1e-50"), mp.mpf("1e-40")
    values = []
    for R_text, d_text in [("0", ("0", "0", "0")), ("1.2", ("0.25", "-0.5", "0.375"))]:
        R = mp.mpf(R_text)
        d = mp.matrix([mp.mpf(x) for x in d_text])
        q = sum(x*x for x in d)
        assert mp.sqrt(q) <= mp.sinh(R)
        jac = mp.matrix(4, 3)
        for i in range(3):
            jac[0, i] = d[i]/mp.sqrt(1+q)
            for j in range(3):
                jac[j+1, i] = int(i == j)
        gram = jac.T*jac
        intended = mp.eye(3) + d*d.T/(1+q)
        gram_residual = max(abs(gram[i,j]-intended[i,j]) for i in range(3) for j in range(3))
        largest = 1+q/(1+q)
        slack = 1+mp.tanh(R)**2-largest
        assert gram_residual <= tol_abs + tol_rel*max(abs(largest),1)
        assert slack >= -tol_abs
        values.append({"R": R_text, "d": list(d_text), "q": mp.nstr(q,80), "gram_max_absolute_residual": mp.nstr(gram_residual,80), "largest_eigenvalue": mp.nstr(largest,80), "bound_slack": mp.nstr(slack,80)})
    return {"precision_decimal_digits": 80, "absolute_tolerance": "1e-50", "relative_tolerance": "1e-40", "scope": "ancillary nondimensionalized diagnostics only; exact certificates are independent", "cases": values}


def main() -> int:
    actual = {path: digest(Path(path)) for path in EXPECTED}
    if actual != EXPECTED:
        raise RuntimeError(f"frozen input SHA mismatch: {actual}")
    checks = [c01(), c02(), c03()]
    result = {
        "schema_version": 2,
        "axis": "sympy",
        "status": "PASS",
        "evidence_class": "exact",
        "contract_sha256": EXPECTED[str(CONTRACT)],
        "source_sha256": digest(Path(__file__)),
        "input_sha256": actual,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "commands": [{"argv": sys.argv, "cwd": str(Path.cwd()), "exit_code": 0, "timeout_seconds": 1800}],
        "toolchain": {"python": sys.version, "sympy": sp.__version__, "sympy_file": sp.__file__, "mpmath": mp.__version__},
        "domain_assumption_diff": [],
        "checks": checks,
        "counterexample": None,
        "numerical_diagnostics": numerical_diagnostics(),
        "claim_scope": "C01-C03 specified finite mathematical components only; C04 NEEDS_OWNER_DECISION; global projection/Lipschitz extension and physical/observational science HOLD.",
        "correlation_disclosure": "Native Codex SymPy author; shared LLM family may correlate with other axes. No sibling author proof/script/result was read.",
    }
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "checks": [(x["component"], x["status"]) for x in checks], "source_sha256": result["source_sha256"], "toolchain": result["toolchain"], "numerical_diagnostics": result["numerical_diagnostics"]}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
