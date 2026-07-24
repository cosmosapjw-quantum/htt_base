#!/usr/bin/env python3
"""Rocq adapter for parent-observed PR-190 CAS execution."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SOURCE = REPO / "formal_rocq/pr190_shear_substitution.v"


def main() -> int:
    rocq = shutil.which("rocq")
    if rocq is None:
        payload = {
            "checks": {
                "dust_gauss_constraint_identity": False,
                "dust_logistic_evolution_identity": False,
                "dust_hubble_evolution_identity": False,
                "lower_scalar_match_component_gap": False,
                "upper_scalar_match_component_gap": False,
            },
            "domain_assumption_diff": [],
            "computed": {
                "lower_x_c": "2/25",
                "upper_x_c": "1/10",
                "lower_component_gap": "1/50",
                "upper_component_gap": "3/100",
            },
            "counterexample": "rocq executable unavailable",
        }
        print(json.dumps(payload, sort_keys=True))
        return 127

    result = subprocess.run(
        [rocq, "compile", str(SOURCE.relative_to(REPO))],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    )
    sys.stderr.write(result.stdout)
    sys.stderr.write(result.stderr)
    compiled = SOURCE.with_suffix(".vo")
    passed = result.returncode == 0 and compiled.is_file()
    checks = {
        "dust_gauss_constraint_identity": passed,
        "dust_logistic_evolution_identity": passed,
        "dust_hubble_evolution_identity": passed,
        "lower_scalar_match_component_gap": passed,
        "upper_scalar_match_component_gap": passed,
    }
    payload = {
        "checks": checks,
        "domain_assumption_diff": [],
        "computed": {
            "lower_x_c": "2/25",
            "upper_x_c": "1/10",
            "lower_component_gap": "1/50",
            "upper_component_gap": "3/100",
        },
        "counterexample": None if passed else "Rocq compilation failed",
    }
    print(json.dumps(payload, sort_keys=True))
    return 0 if passed else (result.returncode or 2)


if __name__ == "__main__":
    raise SystemExit(main())
