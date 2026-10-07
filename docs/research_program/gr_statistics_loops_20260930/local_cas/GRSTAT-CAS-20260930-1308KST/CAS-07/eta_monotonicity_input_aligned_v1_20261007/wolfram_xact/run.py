#!/usr/bin/python3.12
"""Independent Wolfram+xAct runner for frozen CAS-07-M01."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

REPO = Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
BASE = REPO / "docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-07/eta_monotonicity_input_aligned_v1_20261007"
OWN = BASE / "wolfram_xact"
SOURCE = OWN / "proof.wl"
EXPECTED = {
    BASE / "EXECUTION_CONTRACT.json": "b5a49f066f95a010607eb800d323094d5d4050c986c3cb26f78bba022977cc70",
    BASE / "ADMITTED_INPUTS.json": "89949f14b9671720a7df7e73ab2bdf2e8cede8ed7937a86ea531635f29259400",
    REPO / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md": "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
    SOURCE: "a1112c94f9429a5a3b74030691298a6b5980cfffac9e4c5f3e57bd324739b935",
}
MARKERS = (
    "piecewise_k_zero", "eta_derivative_identity", "sinh_minus_x_derivative",
    "numerator_derivative", "sinh_ge_x_universal", "numerator_nonnegative_universal",
    "numerator_positive_universal",
    "positive_substitution", "eta_substitution_identity", "eta_nonnegative_universal",
    "eta_monotone_universal", "xact_eta_gradient_nonzero_generic",
    "xact_eta_gradient_component_binding", "xact_eta_gradient_nonzero_on_domain",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    before = {str(path.relative_to(REPO)): sha(path) for path in EXPECTED}
    seals_ok = all(sha(path) == expected for path, expected in EXPECTED.items())
    proc = subprocess.run(["/usr/bin/wolframscript", "-file", str(SOURCE)], cwd=REPO,
                          text=True, capture_output=True, timeout=1200, check=False)
    (OWN / "proof.stdout.log").write_text(proc.stdout)
    (OWN / "proof.stderr.log").write_text(proc.stderr)
    after_ok = all(sha(path) == expected for path, expected in EXPECTED.items())
    markers = {name: proc.stdout.count(f"CHECK:{name}:TRUE") == 1 for name in MARKERS}
    version_ok = "ENGINE_VERSION=15.0.0" in proc.stdout and "XTENSOR_VERSION={\"1.3.0\"" in proc.stdout
    xact_nonzero = ("XACT_ETA_GRADIENT=" in proc.stdout and "XACT_ETA_GRADIENT=0" not in proc.stdout
                    and "XACT_BOUND_ETA_GRADIENT=" in proc.stdout and "XACT_BOUND_ETA_GRADIENT=0" not in proc.stdout)
    diagnostic = re.search(r"(?im)(Reduce::nsmet|\berror\b|\bFAIL\b|CAS07_M01_FULL_SCOPE_CERTIFIED=FALSE)", proc.stdout + "\n" + proc.stderr)
    full = seals_ok and after_ok and proc.returncode == 0 and all(markers.values()) and version_ok and xact_nonzero and diagnostic is None and "CAS07_M01_FULL_SCOPE_CERTIFIED=TRUE" in proc.stdout
    record = {
        "argv": ["/usr/bin/wolframscript", "-file", str(SOURCE)],
        "exit_code": proc.returncode,
        "input_source_sha256": before,
        "markers": markers,
        "version_ok": version_ok,
        "xact_nonzero_generic_gradient": xact_nonzero,
        "diagnostic_match": diagnostic.group(0) if diagnostic else None,
    }
    (OWN / "proof_record.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": {"CAS-07-M01": full}, "domain_assumption_diff": [], "counterexample": None}, sort_keys=True))
    return 0 if full else 2


if __name__ == "__main__":
    raise SystemExit(main())
