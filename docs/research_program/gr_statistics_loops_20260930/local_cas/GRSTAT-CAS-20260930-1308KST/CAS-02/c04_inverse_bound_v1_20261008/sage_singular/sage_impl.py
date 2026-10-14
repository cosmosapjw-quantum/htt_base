"""Exact CAS-02-C04 Sage/Singular certificate; stdout is one gate JSON document."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from sage.all import PolynomialRing, QQ, matrix, vector
from sage.version import version as sage_version


HERE = Path(__file__).resolve().parent
REPO = Path.cwd().resolve()
CONTRACT = HERE.parent / "EXECUTION_CONTRACT.json"
ADMITTED = HERE.parent / "ADMITTED_INPUTS.json"
COMMON = REPO / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
SINGULAR = Path("/home/cosmosapjw/opt/sage/local/bin/Singular")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def singular_source():
    # Generic symmetric real 4x4 matrices and unrestricted real 4-vectors.
    names = [f"a{i}{j}" for i in range(4) for j in range(i, 4)]
    names += [f"b{i}{j}" for i in range(4) for j in range(i, 4)]
    names += [f"x{i}" for i in range(4)] + [f"y{i}" for i in range(4)]
    names += [f"v{i}" for i in range(4)] + [f"w{i}" for i in range(4)]
    terms = lambda prefix, left, right: "+".join(
        f"{left[i]}*{prefix}{min(i,j)}{max(i,j)}*{right[j]}"
        for i in range(4) for j in range(4)
    )
    x = [f"x{i}" for i in range(4)]
    y = [f"y{i}" for i in range(4)]
    delta = [f"(y{i}-x{i})" for i in range(4)]
    plus = [f"(y{i}+x{i})" for i in range(4)]
    q1, q2 = terms("a", x, x), terms("b", y, y)
    delta_y = f"({terms('b', y, y)})-({terms('a', y, y)})"
    delta_x = f"({terms('b', x, x)})-({terms('a', x, x)})"
    anchor1 = f"({delta_y})+({terms('a', delta, plus)})"
    anchor2 = f"({delta_x})+({terms('b', delta, plus)})"
    vv = "+".join(f"v{i}^2" for i in range(4))
    ww = "+".join(f"w{i}^2" for i in range(4))
    vw = "+".join(f"v{i}*w{i}" for i in range(4))
    squares = "+".join(
        f"(v{i}*w{j}-v{j}*w{i})^2"
        for i in range(4) for j in range(i + 1, 4)
    )
    return "\n".join([
        "// Generated deterministically by run.py; QQ polynomial certificates.",
        f"ring r=0,({','.join(names)}),dp;",
        f"poly c1=({q2})-({q1})-({anchor1});",
        f"poly c2=({q2})-({q1})-({anchor2});",
        f"poly cs=({vv})*({ww})-({vw})^2-({squares});",
        'if (c1 != 0 || c2 != 0 || cs != 0) { print("CERTIFICATE_FAIL"); quit; }',
        'print("CERTIFICATE_PASS anchor1 anchor2 lagrange4");',
        'print(system("version"));',
        "quit;",
        "",
    ])


def calculate():
    contract = json.loads(CONTRACT.read_text())
    admitted = json.loads(ADMITTED.read_text())
    diffs = []
    if contract["identity"]["contract_id"] != "GRSTAT-20260930-CAS-02-C04-INVERSE-BOUND-V1":
        diffs.append("contract identity")
    if admitted["admission"] != "OWNER_ADOPTED":
        diffs.append("admission")
    for item in contract["identity"]["source_input_hashes"]:
        if item["path"] == "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md":
            if sha(COMMON) != item["sha256"]:
                diffs.append("COMMON_SPEC SHA")
        elif item["path"].endswith("/ADMITTED_INPUTS.json"):
            if sha(ADMITTED) != item["sha256"]:
                diffs.append("ADMITTED_INPUTS SHA")
    if diffs:
        return {"checks": {"CAS-02-C04": False}, "domain_assumption_diff": diffs,
                "counterexample": None, "details": {"error": "frozen inputs differ"}}

    names = [f"a{i}{j}" for i in range(4) for j in range(i, 4)]
    names += [f"b{i}{j}" for i in range(4) for j in range(i, 4)]
    names += [f"x{i}" for i in range(4)] + [f"y{i}" for i in range(4)]
    P = PolynomialRing(QQ, names=names)
    g = dict(zip(names, P.gens()))
    S1 = matrix(P, 4, 4, lambda i, j: g[f"a{min(i,j)}{max(i,j)}"])
    S2 = matrix(P, 4, 4, lambda i, j: g[f"b{min(i,j)}{max(i,j)}"])
    u1 = vector(P, [g[f"x{i}"] for i in range(4)])
    u2 = vector(P, [g[f"y{i}"] for i in range(4)])
    q1 = u1.dot_product(S1 * u1)
    q2 = u2.dot_product(S2 * u2)
    anchor1 = u2.dot_product((S2-S1)*u2) + (u2-u1).dot_product(S1*(u2+u1))
    anchor2 = u1.dot_product((S2-S1)*u1) + (u2-u1).dot_product(S2*(u2+u1))
    sage_anchor1 = q2-q1-anchor1 == 0
    sage_anchor2 = q2-q1-anchor2 == 0

    H = PolynomialRing(QQ, names=["h0", "p1", "p2", "p3", "r", "s", "t", "v", "w"])
    h0, p1, p2, p3, r, s, t, v, w = H.gens()
    h2 = matrix(H, [[r,s,t],[s,v,w],[t,w,-r-v]])
    hs = matrix(H, 4, 4, lambda i,j: h0 if i==j==0 else
                (-[p1,p2,p3][j-1]/2 if i==0 else
                 (-[p1,p2,p3][i-1]/2 if j==0 else h2[i-1,j-1])))
    sage_embedding = sum(z*z for z in hs.list()) == (
        h0*h0 + (p1*p1+p2*p2+p3*p3)/2 + sum(z*z for z in h2.list()))
    sage_tracefree = sum(h2[i,i] for i in range(3)) == 0

    C = PolynomialRing(QQ, names=["t0", "d1", "d2", "d3"])
    t0,d1,d2,d3 = C.gens()
    relation = t0*t0-1-d1*d1-d2*d2-d3*d3
    norm2 = t0*t0+d1*d1+d2*d2+d3*d3
    sage_chart_norm = (norm2-(1+2*(d1*d1+d2*d2+d3*d3))).reduce(C.ideal(relation).groebner_basis()) == 0
    sage_unit = (-t0*t0+d1*d1+d2*d2+d3*d3+1).reduce(C.ideal(relation).groebner_basis()) == 0

    V = PolynomialRing(QQ, names=[f"v{i}" for i in range(4)]+[f"w{i}" for i in range(4)])
    v4, w4 = V.gens()[:4], V.gens()[4:]
    lagrange = sum(z*z for z in v4)*sum(z*z for z in w4) - sum(v4[i]*w4[i] for i in range(4))**2
    lagrange -= sum((v4[i]*w4[j]-v4[j]*w4[i])**2 for i in range(4) for j in range(i+1,4))
    sage_lagrange = lagrange == 0

    source = singular_source()
    sing_path = HERE / "certificate.sing"
    sing_path.write_text(source)
    version = subprocess.run([str(SINGULAR), "-v"], text=True, capture_output=True, timeout=30)
    (HERE / "singular.version.stdout.log").write_text(version.stdout)
    (HERE / "singular.version.stderr.log").write_text(version.stderr)
    execution = subprocess.run([str(SINGULAR), "-q", str(sing_path)],
                               text=True, capture_output=True, timeout=120)
    (HERE / "singular.stdout.log").write_text(execution.stdout)
    (HERE / "singular.stderr.log").write_text(execution.stderr)
    singular_ok = (version.returncode == 0 and "44100" in version.stdout+version.stderr
                   and execution.returncode == 0
                   and execution.stdout.splitlines() ==
                   ["CERTIFICATE_PASS anchor1 anchor2 lagrange4", "44100"]
                   and execution.stderr == "")
    checks = [sage_anchor1,sage_anchor2,sage_embedding,sage_tracefree,
              sage_chart_norm,sage_unit,sage_lagrange,singular_ok]
    return {"checks": {"CAS-02-C04": all(checks)}, "domain_assumption_diff": [],
            "counterexample": None,
            "details": {"sage_version": sage_version, "singular_version_code": "44100" if singular_ok else "unconfirmed",
                        "sage_checks": dict(zip(["anchor1","anchor2","embedding","tracefree","chart_norm","unit","lagrange4"], checks[:-1])),
                        "singular_certificate": singular_ok,
                        "source_sha256": sha(Path(__file__)), "singular_source_sha256": sha(sing_path),
                        "singular_stdout_sha256": sha(HERE / "singular.stdout.log"),
                        "singular_stderr_sha256": sha(HERE / "singular.stderr.log"),
                        "singular_version_stdout_sha256": sha(HERE / "singular.version.stdout.log"),
                        "singular_version_stderr_sha256": sha(HERE / "singular.version.stderr.log")}}


if __name__ == "__main__":
    try:
        result = calculate()
        print(json.dumps(result, sort_keys=True))
        sys.exit(0 if result["checks"]["CAS-02-C04"] else 2)
    except Exception as exc:
        print(json.dumps({"checks": {"CAS-02-C04": False}, "domain_assumption_diff": [],
                          "counterexample": None, "details": {"exception": repr(exc)}}))
        sys.exit(2)
