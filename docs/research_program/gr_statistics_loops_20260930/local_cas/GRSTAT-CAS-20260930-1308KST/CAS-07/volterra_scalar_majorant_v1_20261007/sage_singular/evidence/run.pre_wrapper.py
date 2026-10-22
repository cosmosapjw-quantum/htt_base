"""Exact Sage/Singular evidence for the frozen CAS-07 M03 scalar comparison.

Run with `sage -python run.py > result.json`; stdout is one JSON document.
The universal functional argument is in proof.md. Finite CAS checks validate
its algebraic identities but are not substituted for that argument.
"""

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

from sage.all import QQ, PolynomialRing, PowerSeriesRing, factorial
from sage.version import version as sage_version


HERE = Path(__file__).resolve().parent
REPO = next(p for p in HERE.parents if (p / "AGENTS.md").is_file())
CONTRACT = REPO / "docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-07/volterra_scalar_majorant_v1_20261007/EXECUTION_CONTRACT.json"
INPUTS = REPO / "docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-07/volterra_scalar_majorant_v1_20261007/ADMITTED_INPUTS.json"
COMMON = REPO / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
SINGULAR = Path("/home/cosmosapjw/opt/sage/local/bin/Singular")
EXPECTED = {
    str(CONTRACT): "6c840eaffac0744da3d1b2f9c7de3f8b1c45af2d949ba4831b5e90d4ec9a51ae",
    str(INPUTS): "bbb0f93dc43ddd3ee96cdee065f8173ccac44007a6908ae66714f25e3214661d",
    str(COMMON): "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
    str(SINGULAR): "9430832b7c972b6b26d29ded4d91a3e1df8fd87d67f4b8d3f14d8201a75f923c",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def exact_sage_checks():
    K_ring = PolynomialRing(QQ, "k")
    k = K_ring.gen()
    R = PolynomialRing(K_ring, "x")
    x = R.gen()

    def T(poly):
        # K integral_0^x (x-t) t^m dt = K*x^(m+2)/((m+1)(m+2)).
        return sum((c * k * x ** (m + 2) / ((m + 1) * (m + 2))
                    for m, c in enumerate(poly.list())), R.zero())

    term = x
    seed_residuals = []
    for n in range(17):
        expected = k ** n * x ** (2 * n + 1) / factorial(2 * n + 1)
        seed_residuals.append(str(term - expected))
        if term != expected:
            raise AssertionError(f"Sage seed coefficient n={n}: {term - expected}")
        term = T(term)

    S = PowerSeriesRing(QQ, "z", default_prec=37)
    z = S.gen()
    sinh_coefficients = [(z.sinh())[2 * n + 1] for n in range(17)]
    for n, coeff in enumerate(sinh_coefficients):
        if coeff != 1 / factorial(2 * n + 1):
            raise AssertionError(f"Sage sinh coefficient n={n}: {coeff}")

    # A bounded continuous u uses this exact integral bound, also checked by
    # polynomial integration for the universal kernel exponent parameter n.
    remainder_coefficients = []
    for n in range(1, 17):
        coeff = QQ(1) / factorial(2 * n - 1) / (2 * n)
        remainder_coefficients.append(str(coeff))
        if coeff != 1 / factorial(2 * n):
            raise AssertionError(f"Sage remainder coefficient n={n}")
    return {
        "seed_residuals_n0_16": seed_residuals,
        "sinh_coefficients_n0_16": [str(c) for c in sinh_coefficients],
        "remainder_coefficients_n1_16": remainder_coefficients,
        "functional_proof": "proof.md: arbitrary continuous u, positivity induction, compact bound, uniform remainder and series convergence",
    }


def main():
    evidence = HERE / "evidence"
    evidence.mkdir(exist_ok=True)
    observed = {path: sha(path) for path in EXPECTED}
    hash_ok = observed == EXPECTED
    version = subprocess.run([str(SINGULAR), "--version"], capture_output=True, text=True, timeout=30)
    (evidence / "singular_version.stdout").write_text(version.stdout)
    (evidence / "singular_version.stderr").write_text(version.stderr)
    singular_version_ok = version.returncode == 0 and bool(re.search(r"version 4\.4\.1 \(44100", version.stdout))
    singular = subprocess.run([str(SINGULAR), "-q", str(HERE / "kernel.sing")],
                              capture_output=True, text=True, timeout=120)
    (evidence / "singular.stdout").write_text(singular.stdout)
    (evidence / "singular.stderr").write_text(singular.stderr)
    expected_lines = ([f"PASS kernel n={n}" for n in range(1, 9)]
                      + [f"PASS seed n={n}" for n in range(9)]
                      + ["ALL_POLYNOMIAL_IDENTITIES_PASS"])
    singular_ok = (singular.returncode == 0
                   and singular.stdout.splitlines() == expected_lines
                   and not singular.stderr.strip())
    sage_checks = exact_sage_checks()
    ok = hash_ok and sage_version.startswith("10.9") and singular_version_ok and singular_ok
    out = {
        "axis": "sage_singular",
        "contract_id": "GRSTAT-20260930-CAS-07-M03-SCALAR-VOLTERRA-V1",
        "contract_sha256": observed[str(CONTRACT)],
        "admitted_inputs_sha256": observed[str(INPUTS)],
        "checks": {"CAS-07-M03-SCALAR-VOLTERRA": bool(ok)},
        "domain_assumption_diff": [],
        "counterexample": None,
        "evidence_class": "exact",
        "result_scope": "universal scalar functional comparison only; finite CAS checks support written arbitrary-n and arbitrary-continuous-u proof",
        "tool_versions": {"sage": sage_version, "singular": "4.4.1/44100" if singular_version_ok else "UNKNOWN"},
        "executables": {"sage_python": sys.executable, "singular": str(SINGULAR), "singular_sha256": observed[str(SINGULAR)]},
        "hashes": {"expected": EXPECTED, "observed": observed},
        "raw_execution": {"singular_exit_code": singular.returncode, "singular_version_exit_code": version.returncode,
                          "singular_stdout": "evidence/singular.stdout", "singular_stderr": "evidence/singular.stderr",
                          "singular_version_stdout": "evidence/singular_version.stdout", "singular_version_stderr": "evidence/singular_version.stderr"},
        "sage_exact_checks": sage_checks,
        "proof_file": "proof.md",
        "source_files": ["run.py", "kernel.sing"],
        "source_sha256": {name: sha(HERE / name) for name in ("run.py", "kernel.sing", "proof.md")},
        "raw_sha256": {name: sha(evidence / name) for name in
                       ("singular.stdout", "singular.stderr", "singular_version.stdout", "singular_version.stderr")},
        "global_launch_id": None,
        "global_authority": "UNAVAILABLE_OWNER_AUTHORIZED_DIRECT_LOCAL_EXCEPTION",
        "observed_model": "UNKNOWN",
        "observed_effort": "UNKNOWN",
        "scientific_admission": "HOLD",
    }
    print(json.dumps(out, sort_keys=True, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"axis": "sage_singular", "checks": {"CAS-07-M03-SCALAR-VOLTERRA": False},
                          "domain_assumption_diff": [], "counterexample": None,
                          "error": f"{type(exc).__name__}: {exc}", "global_launch_id": None,
                          "observed_model": "UNKNOWN", "observed_effort": "UNKNOWN"}, sort_keys=True, indent=2))
        raise SystemExit(1)
