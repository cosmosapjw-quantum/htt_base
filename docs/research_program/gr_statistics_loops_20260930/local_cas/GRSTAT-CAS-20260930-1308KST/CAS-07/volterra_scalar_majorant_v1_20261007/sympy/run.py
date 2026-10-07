"""Emit exactly one CAS-07 M03 SymPy axis JSON document to stdout."""

import json
import platform

import sympy as sp

from check import exact_checks


def main():
    checks_detail = exact_checks()
    result = {
        "axis": "sympy",
        "contract_id": "GRSTAT-20260930-CAS-07-M03-SCALAR-VOLTERRA-V1",
        "contract_sha256": "6c840eaffac0744da3d1b2f9c7de3f8b1c45af2d949ba4831b5e90d4ec9a51ae",
        "inputs_sha256": "bbb0f93dc43ddd3ee96cdee065f8173ccac44007a6908ae66714f25e3214661d",
        "checks": {"CAS-07-M03-SCALAR-VOLTERRA": all(checks_detail.values())},
        "checks_detail": checks_detail,
        "counterexample": None,
        "domain_assumption_diff": [],
        "proof_artifact": "proof.md",
        "status": "PASS" if all(checks_detail.values()) else "FAIL",
        "tool_versions": {"python": platform.python_version(), "sympy": sp.__version__},
        "launch_id": None,
        "observed_model": "UNKNOWN",
        "observed_effort": "UNKNOWN",
        "scientific_admission": "HOLD",
    }
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
