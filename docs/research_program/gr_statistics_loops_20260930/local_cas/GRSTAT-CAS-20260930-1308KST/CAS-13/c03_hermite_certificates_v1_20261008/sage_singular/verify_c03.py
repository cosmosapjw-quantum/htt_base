#!/usr/bin/env python3
"""Independent Sage/Singular finite CAS-13-C03 certificate.

Run with the pinned Sage interpreter: sage -python verify_c03.py.
Only EXECUTION_CONTRACT.json and ADMITTED_INPUTS.json and their two admitted
specifications supply mathematical targets. No sibling result is consumed.
"""

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from datetime import datetime, timezone

from sage.all import QQ, PolynomialRing, matrix, vector
from sage.version import version as sage_version


HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parent
REPO = next(p for p in HERE.parents if (p / "AGENTS.md").exists())
SINGULAR = Path("/home/cosmosapjw/opt/sage/local/bin/Singular")
INPUTS = [
    (PACKAGE / "EXECUTION_CONTRACT.json", "d9b1e59d9e8648e74db64bdf9e7ef82d23e409c9456a5f307fb30dabb0e8e21e"),
    (PACKAGE / "ADMITTED_INPUTS.json", "916055a8eff4787ff56bd4e7629cef837333890a9dc5c1a9e8a33aa82c1665b4"),
    (REPO / "docs/research_program/gr_statistics_loops_20260930/cas/TEFF_INTERVAL_SPEC.md", "bc055d391d3231c634a14e146f228d3b8179a043485c41ce08754cdeac4fd0fe"),
    (REPO / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md", "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897"),
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record(msg):
    with (HERE / "sage_raw.log").open("a") as out:
        out.write(msg + "\n")


def sing_form(polynomial):
    return str(polynomial).replace("**", "^")


def main():
    (HERE / "sage_raw.log").write_text("")
    record("Sage version: " + sage_version)
    record("Sage argv: " + json.dumps(sys.argv))
    for path, expected in INPUTS:
        got = sha(path)
        record(f"input_sha256 {path.relative_to(REPO)} {got}")
        assert got == expected, f"frozen input drift: {path}"
    assert SINGULAR.is_file()
    record("Singular executable: " + str(SINGULAR))
    record("Singular executable sha256: " + sha(SINGULAR))
    vr = subprocess.run([str(SINGULAR), "--version"], cwd=HERE, text=True,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (HERE / "singular_version.stdout.log").write_text(vr.stdout)
    (HERE / "singular_version.stderr.log").write_text(vr.stderr)
    record("Singular version argv: " + json.dumps(vr.args))
    record("Singular version exit: " + str(vr.returncode))
    assert vr.returncode == 0 and "version 4.4.1" in vr.stdout + vr.stderr

    B = PolynomialRing(QQ, names=("A", "U"))
    A, U = B.gens()
    F = B.fraction_field()
    Y = PolynomialRing(F, "y")
    y = Y.gen()
    delta = 3*A**2 + 2*A*U + U**2
    M = matrix(F, [[1, A**3, A**4], [1, U**3, U**4],
                   [0, 3*U**2, 4*U**3]])
    determinant = B(M.det())
    record("coefficient_matrix_determinant: " + str(determinant))
    assert determinant != 0
    assert B(determinant / (U**2*(U-A)**2)) == delta

    derived = {}
    for p in (5, 6):
        rhs = vector(F, [A**p, U**p, p*U**(p-1)])
        c0, c3, c4 = M.solve_right(rhs)
        q = c0 + c3*y**3 + c4*y**4
        assert q(A) == A**p and q(U) == U**p
        assert (3*c3*U**2 + 4*c4*U**3) == p*U**(p-1)
        W = PolynomialRing(F, "w")
        w = W.gen()
        node_m3 = (1-w)*A**3 + w*U**3
        node_m4 = (1-w)*A**4 + w*U**4
        assert (1-w)*q(A) + w*q(U) == c0 + c3*node_m3 + c4*node_m4
        assert (1-w)*A**p + w*U**p == c0 + c3*node_m3 + c4*node_m4
        numerator = Y(delta*(y**p-q))
        # Cancellation is required: these are polynomial, not rational-function,
        # numerators in the pinned Singular coefficient domain QQ[A,U,y].
        R = PolynomialRing(QQ, names=("A", "U", "y"))
        AR, UR, yr = R.gens()
        number_R = R(sum(R(str(coef).replace("^", "**")) * yr**i
                         for i, coef in enumerate(numerator.list())))
        derived[p] = number_R
        record(f"p={p} c0={c0}")
        record(f"p={p} c3={c3}")
        record(f"p={p} c4={c4}")
        record(f"p={p} delta_times_error={number_R}")
        record(f"p={p} arbitrary two-node weight moment identity and interpolation equality: PASS")

    targets = {
        5: delta*y**2 + (2*A**2*U+A*U**2)*y + A**2*U**2,
        6: delta*y**3 + (3*A**3+8*A**2*U+5*A*U**2+2*U**3)*y**2
           + (2*A**3*U+5*A**2*U**2+2*A*U**3)*y
           + A**3*U**2+2*A**2*U**3,
    }
    target_R = {}
    for p in (5, 6):
        target_R[p] = R(sum(R(str(coef).replace("^", "**"))*yr**i
                            for i, coef in enumerate(targets[p].list())))
    script = ["ring r = 0,(A,U,y),dp;", "option(redSB);",
              "poly divisor = (y-A)*(y-U)^2;"]
    for p in (5, 6):
        script += [f"poly n{p} = {sing_form(derived[p])};",
                   f"poly target{p} = {sing_form(target_R[p])};",
                   f"ideal i{p} = divisor;",
                   f"ideal gb{p} = std(i{p});",
                   f"poly rem{p} = reduce(n{p},gb{p});",
                   f"poly qpoly{p} = n{p}/divisor;",
                   f'print("P{p}_NF_ZERO");', f"print(rem{p}==0);",
                   f'print("P{p}_DIVISION_ZERO");',
                   f"print(n{p}-qpoly{p}*divisor==0);",
                   f'print("P{p}_TARGET_EQUAL");',
                   f"print(qpoly{p}-target{p}==0);",
                   f'print("P{p}_QUOTIENT");', f"print(qpoly{p});"]
    script += ["quit;"]
    sing_file = HERE / "factor_checks.sing"
    sing_file.write_text("\n".join(script) + "\n")
    argv = [str(SINGULAR), "-q", str(sing_file)]
    run = subprocess.run(argv, cwd=HERE, text=True, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    (HERE / "singular.stdout.log").write_text(run.stdout)
    (HERE / "singular.stderr.log").write_text(run.stderr)
    record("Singular division argv: " + json.dumps(argv))
    record("Singular division exit: " + str(run.returncode))
    record("Singular division stdout sha256: " + sha(HERE / "singular.stdout.log"))
    record("Singular division stderr sha256: " + sha(HERE / "singular.stderr.log"))
    assert run.returncode == 0, "Singular nonzero exit"
    assert not re.search(r"(?i)(error|warning|undefined)", run.stderr + run.stdout), "Singular diagnostic"
    for p in (5, 6):
        assert re.search(rf"P{p}_NF_ZERO\s*\n1\s*\n", run.stdout)
        assert re.search(rf"P{p}_DIVISION_ZERO\s*\n1\s*\n", run.stdout)
        assert re.search(rf"P{p}_TARGET_EQUAL\s*\n1\s*\n", run.stdout)
        assert f"P{p}_QUOTIENT\n" in run.stdout
        # This equality is a check of Singular's independently computed quotient,
        # not a target supplied to its division step.
        assert derived[p] == R((yr-AR)*(yr-UR)**2) * target_R[p]
        # Every monomial coefficient of P_p in A,U,y is nonnegative; the
        # leading y term has positive Delta. This proves P_p>0 at positive
        # ordered nodes and y>0, without sampling the continuum.
        tR = target_R[p]
        assert all(coef >= 0 for coef in tR.dict().values())
        assert tR(1, 2, 1) > 0 and tR(3, 2, 1) > 0
        # Both coalescent node specializations are legitimate polynomial
        # identities because Delta(A,A)=6A^2>0 for A>0.
        assert delta(A, A) == 6*A**2
        assert derived[p](AR, AR, yr) == (((yr-AR)*(yr-AR)**2*tR)(AR, AR, yr))
        for av, uv in [(1, 2), (3, 2)]:
            assert delta(av, uv) > 0
            for yv in [1, 2, 3]:
                lhs = QQ(derived[p](av, uv, yv))
                rhs = QQ((yv-av)*(yv-uv)**2*tR(av, uv, yv))
                assert lhs == rhs
        record(f"p={p} Singular remainder/division zero; quotient target equality; positive coefficient certificate; boundary polynomial specialization; numeric vectors: PASS")

    record("lower: 0<a<u, y in [a,b], b>=u => y-a>=0, (y-u)^2>=0, Delta>0, P>0")
    record("upper: 0<d<b, y in [a,b], a<=d => y-b<=0, (y-d)^2>=0, Delta>0, P>0")
    record("moment: integral Q dπ = c0 + c3*m3 + c4*m4 for any probability π with moments m3,m4; two-node equality conditional on admitted weights and exact moment matching")
    record("boundary: polynomial specialization only; no 0/0 node or weight substitution")
    record("exclusions: no node existence, unconditional moment matching, general p, bandpass, full theorem, or scientific admission")
    print(json.dumps({"CAS-13-C03": True}, separators=(",", ":")))


if __name__ == "__main__":
    main()
