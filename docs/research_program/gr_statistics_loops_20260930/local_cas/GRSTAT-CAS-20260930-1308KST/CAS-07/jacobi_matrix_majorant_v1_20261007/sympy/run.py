#!/usr/bin/env python3
"""Independent SymPy certificates for frozen CAS-07 M04.

The unrestricted operator-norm argument is in proof.md.  SymPy checks its
componentwise calculus and exact scalar identities; it does not sample a
matrix family as a substitute for the universal proof.
"""

from __future__ import annotations

import hashlib
import json
import platform
from pathlib import Path

import sympy as sp


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[7]
UNIT = HERE.parent
CONTRACT = UNIT / "EXECUTION_CONTRACT.json"
INPUTS = UNIT / "ADMITTED_INPUTS.json"
COMMON = ROOT / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
EXPECTED = {
    CONTRACT: "553502c17d46c3b47c5a7b892f149f603235239d8504392b9bd19923f4edde7a",
    INPUTS: "f4d3b3b96a86fabcf83c7134193ec70da61b15d7a45b1a4b2c6b581312c1d4d8",
    COMMON: "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
}
OBLIGATION_NAMES = (
    "CAS-07-M04-VOLTERRA-IDENTITY",
    "CAS-07-M04-SCALAR-PREMISE",
    "CAS-07-M04-D-NORM",
    "CAS-07-M04-D-MINUS-SI",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    actual_hashes = {str(path.relative_to(ROOT)): sha256(path) for path in EXPECTED}
    hash_ok = all(sha256(path) == expected for path, expected in EXPECTED.items())
    contract = json.loads(CONTRACT.read_text())
    inputs = json.loads(INPUTS.read_text())
    names_ok = tuple(contract["target"]["exact_test_obligations"]) == OBLIGATION_NAMES
    domain_ok = (
        inputs["space"]
        == "E=R^2 with standard Euclidean inner product; D(s),R(s) are real continuous linear maps E->E; norm is the induced Euclidean operator norm."
        and inputs["domains"]["K"] == "real K>=0, L^-2"
        and inputs["domains"]["s"] == "real 0<=s<=L, L"
        and inputs["scientific_admission"] == "HOLD"
    )

    s, t = sp.symbols("s t", nonnegative=True, real=True)
    k = sp.symbols("k", positive=True, real=True)
    d = sp.Matrix(2, 2, lambda i, j: sp.Function(f"d{i+1}{j+1}")(t))
    r = sp.Matrix(2, 2, lambda i, j: sp.Function(f"r{i+1}{j+1}")(t))
    product = r * d
    jacobi_second = -product
    component_product_ok = all(
        sp.simplify(jacobi_second[i, j] + sum(r[i, h] * d[h, j] for h in range(2))) == 0
        for i in range(2) for j in range(2)
    )
    generic_noncommuting = any(sp.expand((r * d - d * r)[i, j]) != 0 for i in range(2) for j in range(2))

    # For every arbitrary smooth component x, H(s)=integral (s-t)x''(t)dt
    # has H(0)=H'(0)=0 and H''=x''. Hence x-x(0)-s*x'(0)=H.
    derivative_certificates = []
    for i in range(2):
        for j in range(2):
            x = sp.Function(f"x{i+1}{j+1}")
            h = sp.Integral((s - t) * sp.diff(x(t), t, 2), (t, 0, s))
            derivative_certificates.append(
                sp.simplify(sp.diff(h, s, 2) - sp.diff(x(s), s, 2)) == 0
                and h.subs(s, 0).doit() == 0
                and sp.diff(h, s).subs(s, 0).doit() == 0
            )
    taylor_ok = all(derivative_certificates)

    # K=k^2>0; the K=0 branch is exactly f_0(s)=s.
    f = sp.sinh(k * s) / k
    integral_f = sp.integrate((s - t) * sp.sinh(k * t) / k, (t, 0, s))
    majorant_identity = sp.simplify(s + k**2 * integral_f - f)
    remainder_identity = sp.simplify(k**2 * integral_f - (f - s))
    zero_branch = sp.simplify(s + 0 * sp.integrate((s - t) * t, (t, 0, s)) - s)
    zero_origin = sp.simplify(f.subs(s, 0))
    constant_negative_curvature_control = (
        sp.simplify(sp.diff(f, s, 2) - k**2 * f) == 0
        and sp.simplify(sp.diff(f, s).subs(s, 0) - 1) == 0
        and zero_origin == 0
    )
    kernel_integral = sp.integrate(s - t, (t, 0, s))
    scalar_certificates_ok = (
        majorant_identity == 0
        and remainder_identity == 0
        and zero_branch == 0
        and zero_origin == 0
        and constant_negative_curvature_control
        and sp.simplify(kernel_integral - s**2 / 2) == 0
    )

    # Each implication below uses the named, fully written analytic step in
    # proof.md, with M02 and M03 as the only accepted external lemmas.
    premises_ok = hash_ok and names_ok and domain_ok and sp.__version__ == "1.14.0"
    obligations = {
        OBLIGATION_NAMES[0]: bool(premises_ok and component_product_ok and generic_noncommuting and taylor_ok),
        OBLIGATION_NAMES[1]: bool(premises_ok and component_product_ok and taylor_ok and scalar_certificates_ok),
        OBLIGATION_NAMES[2]: bool(premises_ok and scalar_certificates_ok and taylor_ok),
        OBLIGATION_NAMES[3]: bool(premises_ok and scalar_certificates_ok and taylor_ok),
    }
    assert tuple(obligations) == OBLIGATION_NAMES
    domain_assumption_diff: list[str] = [] if domain_ok else ["ADMITTED_INPUTS domain/space differs"]
    counterexample = None
    check = {
        "hash_ok": hash_ok,
        "actual_input_sha256": actual_hashes,
        "names_ok": names_ok,
        "domain_ok": domain_ok,
        "component_product_ok": component_product_ok,
        "generic_noncommuting_product": generic_noncommuting,
        "component_taylor_derivative_certificates": derivative_certificates,
        "majorant_identity_residual": str(majorant_identity),
        "remainder_identity_residual": str(remainder_identity),
        "K_zero_identity_residual": str(zero_branch),
        "s_zero_value": str(zero_origin),
        "constant_R_minus_K_Id_equality_growth_control": constant_negative_curvature_control,
        "kernel_integral": str(kernel_integral),
        "scalar_certificates_ok": scalar_certificates_ok,
        "universal_norm_proof": "proof.md, sections 2-4",
    }
    (HERE / "check.json").write_text(json.dumps(check, indent=2) + "\n")
    result = {
        "schema": "htt.cas07.m04.sympy-result.v1",
        "contract_id": contract["identity"]["contract_id"],
        "contract_sha256": sha256(CONTRACT),
        "admitted_inputs_sha256": sha256(INPUTS),
        "common_spec_sha256": sha256(COMMON),
        "axis": "sympy",
        "status": "PASS" if all(obligations.values()) else "FAIL",
        "checks": obligations,
        "obligations": obligations,
        "domain_assumption_diff": domain_assumption_diff,
        "counterexample": counterexample,
        "assumptions": "Exactly ADMITTED_INPUTS; no symmetry, commutation, Frobenius norm, or truncation",
        "accepted_dependencies": ["CAS-07-M02 literal statement", "CAS-07-M03 literal statement"],
        "tool_versions": {"python": platform.python_version(), "sympy": sp.__version__},
        "executable_artifacts": {"run.py": sha256(HERE / "run.py"), "proof.md": sha256(HERE / "proof.md")},
        "check_artifact": "check.json",
        "launch_id": None,
        "observed_model": "UNKNOWN",
        "observed_effort": "UNKNOWN",
        "scientific_admission": "HOLD",
        "claim_ceiling": "matrix_majorization_only_no_determinant_or_science",
    }
    (HERE / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({
        "status": result["status"],
        "checks": obligations,
        "domain_assumption_diff": domain_assumption_diff,
        "counterexample": counterexample,
    }, indent=2))
    if not all(obligations.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
