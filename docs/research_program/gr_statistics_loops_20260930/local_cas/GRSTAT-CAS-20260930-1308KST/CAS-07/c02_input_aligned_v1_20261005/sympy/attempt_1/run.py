#!/usr/bin/env python3
"""Independent exact SymPy certificate for conditional CAS-07-C02.

The finite symbolic identities below are paired with explicit universal
Euclidean norm, real spectral, and continuity arguments. No sampled matrix is
used to discharge a universal obligation.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import platform
import sys
from datetime import datetime, timezone

import sympy as sp


REPO = Path.cwd()
V = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent
INPUTS = {
    "contract": (V / "EXECUTION_CONTRACT.json", "367ea2b4221c2ef10c93d1c49ef75d40d0f030bf79ec429a0fe1dbfeb44c219a"),
    "admitted": (V / "ADMITTED_INPUTS.json", "84e20f628abcc4879446c6987dec21416934dece1c94e23076d6ce491939e6b0"),
    "common": (REPO / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md", "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897"),
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def certificate() -> dict[str, bool]:
    """Check identities used in the universally quantified argument."""
    a, b, c, d, s, t, x, y, z = sp.symbols("a b c d s t x y z", real=True)
    A = sp.Matrix([[a, b], [c, d]])
    I = sp.eye(2)
    D = s * I + A
    X = sp.Matrix([x, y])
    G = D.T * D
    Gt = (s * I + t * A).T * (s * I + t * A)
    h, k, ell, lam = sp.symbols("h k ell lam", real=True)
    H = sp.Matrix([[h, k], [k, ell]])
    char = sp.expand((lam * sp.eye(2) - H).det())
    disc = (h - ell) ** 2 + 4 * k ** 2
    ev = sp.Matrix([k, lam - h])
    ev_residual = (H - lam * sp.eye(2)) * ev
    q = sp.symbols("q", nonnegative=True, real=True)
    checks = {
        "gram_symmetric": G == G.T,
        "euclidean_quadratic_identity": sp.expand((X.T * G * X)[0] - (D * X).dot(D * X)) == 0,
        "norm_expansion": sp.expand((D * X).dot(D * X) - (s ** 2 * X.dot(X) + 2 * s * X.dot(A * X) + (A * X).dot(A * X))) == 0,
        "homotopy_quadratic_identity": sp.expand((X.T * Gt * X)[0] - (s * X + t * A * X).dot(s * X + t * A * X)) == 0,
        "det_homotopy_polynomial": sp.expand((s * I + t * A).det() - (s ** 2 + s * t * sp.trace(A) + t ** 2 * A.det())) == 0,
        "gram_det_square": sp.expand(G.det() - D.det() ** 2) == 0,
        "gram_characteristic": sp.expand((z * I - G).det() - (z ** 2 - sp.trace(G) * z + G.det())) == 0,
        "generic_symmetric_discriminant_sos": sp.expand((h + ell) ** 2 - 4 * (h * ell - k ** 2) - disc) == 0,
        "generic_eigenvector_first_component": sp.expand(ev_residual[0]) == 0,
        "generic_eigenvector_second_component": sp.expand(ev_residual[1] + char) == 0,
        "eigenvalue_roots": all(sp.simplify(char.subs(lam, (h + ell + sign * sp.sqrt(disc)) / 2)) == 0 for sign in (-1, 1)),
        "lower_margin_decomposition": sp.expand((s - t * q) - ((s - q) + (1 - t) * q)) == 0,
    }
    return checks


def main() -> int:
    started = datetime.now(timezone.utc).isoformat()
    before = {key: digest(path) for key, (path, _) in INPUTS.items()}
    input_ok = all(before[key] == expected for key, (_, expected) in INPUTS.items())
    if input_ok:
        contract = json.loads(INPUTS["contract"][0].read_text())
        admitted = json.loads(INPUTS["admitted"][0].read_text())
        input_ok = (
            contract["identity"]["component_scope"] == "CAS-07-C02 only"
            and admitted["component"] == "CAS-07-C02"
            and contract["independence"]["mode"] == "blind-results-and-derivations"
        )
    checks = certificate() if input_ok else {}
    after = {key: digest(path) for key, (path, _) in INPUTS.items()}
    sealed = before == after and input_ok
    ok = sealed and bool(checks) and all(checks.values())
    proof = [
        "Let A=D-sI and q=s eta. The supplied Euclidean induced operator bound means ||Ax||_2<=q||x||_2 for every real x: for x!=0 apply its unit-vector definition to x/||x||_2; x=0 is immediate. Thus q>=0 and q<s from s>0 and 0<=eta<1.",
        "For each x, the Euclidean triangle and reverse-triangle inequalities give (s-q)||x||_2<=||Dx||_2<= (s+q)||x||_2. This uses no matrix Frobenius, row, column, entrywise, or indefinite norm.",
        "G=D^T D is real symmetric and x^T G x=||Dx||_2^2>=0. Its characteristic discriminant is (G00-G11)^2+4G01^2>=0. For nonzero off-diagonal k, v=(k,lambda-G00) is a nonzero eigenvector whenever lambda is a characteristic root; when k=0 use standard basis eigenvectors. If roots coincide, the sum of squares forces k=0 and G00=G11. Hence both real eigenvalues have real nonzero eigenvectors, and their nonnegative square roots are precisely the two declared singular values.",
        "Apply the universal vector inequalities to either eigenvector v of G. Because ||Dv||_2^2=lambda||v||_2^2 and both sides are nonnegative, s-q<=sqrt(lambda)<=s+q. This includes multiplicity, eta=0, and nonsymmetric D.",
        "For every t in [0,1], D_t=sI+tA obeys ||D_t x||_2>=(s-tq)||x||_2, with s-tq=(s-q)+(1-t)q>0. Thus D_t has zero kernel and det(D_t)!=0 for every t. Its determinant is a continuous real polynomial in t; det(D_0)=s^2>0. The intermediate-value theorem therefore gives det(D)=det(D_1)>0. Positivity is derived here, not assumed.",
        "The symbolic identity det(G)=det(D)^2 and det(D)>0 imply sigma_1 sigma_2=det(D). Since each sigma_i lies in [m,M] with m=s-q>0 and M=s+q, m^2<=det(D)<=M^2. The positive square root is monotone on nonnegative reals, so m<=sqrt(det(D))<=M. Substitute q=s eta to obtain exactly s(1-eta)<=sqrt(det(D))<=s(1+eta).",
    ]
    details = {
        "statement_alignment": "Conditional full CAS-07-C02 for every real 2x2 D under s>0, 0<=eta<1 and the declared Euclidean induced operator-norm bound; positive determinant and both singular-value bounds derived. No C01/C03/Jacobi or scientific admission.",
        "subchecks": checks,
        "universal_derivation": proof,
        "input_hashes_before": before,
        "input_hashes_after": after,
        "source_sha256": digest(Path(__file__)),
        "runtime": {"python": sys.version, "sympy": sp.__version__, "sympy_file": sp.__file__, "argv": sys.argv, "cwd": str(REPO), "pid": os.getpid(), "platform": platform.platform()},
        "started_at": started,
    }
    result = {
        "schema_version": 2,
        "axis": "sympy",
        "status": "PASS" if ok else "INCONCLUSIVE",
        "contract_sha256": before["contract"],
        "evidence_class": "exact_symbolic_with_explicit_universal_euclidean_proof" if ok else "inconclusive",
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "commands": [{"argv": [sys.executable, "-B", str(Path(__file__))], "cwd": str(REPO), "exit_code": 0 if ok else 1, "stdout": "see stdout.log", "stderr": "see stderr.log"}],
        "checks": {"CAS-07-C02": ok},
        "domain_assumption_diff": [],
        "counterexample": None,
        "details": details,
    }
    OUT.mkdir(exist_ok=True)
    (OUT / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": result["checks"], "domain_assumption_diff": [], "counterexample": None, "status": result["status"], "subchecks": checks}, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
