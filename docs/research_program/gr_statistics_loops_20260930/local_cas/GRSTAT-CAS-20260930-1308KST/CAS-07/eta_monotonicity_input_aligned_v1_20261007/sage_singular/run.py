#!/usr/bin/python3.12
"""Independent Sage+Singular runner for frozen CAS-07-M01."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

REPO = Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
BASE = REPO / "docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-07/eta_monotonicity_input_aligned_v1_20261007"
OWN = BASE / "sage_singular"
SAGE = Path("/home/cosmosapjw/opt/sage/sage")
SINGULAR = Path("/home/cosmosapjw/opt/sage/local/bin/Singular")
EXPECTED = {
    BASE / "EXECUTION_CONTRACT.json": "b5a49f066f95a010607eb800d323094d5d4050c986c3cb26f78bba022977cc70",
    BASE / "ADMITTED_INPUTS.json": "89949f14b9671720a7df7e73ab2bdf2e8cede8ed7937a86ea531635f29259400",
    REPO / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md": "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
    SINGULAR: "9430832b7c972b6b26d29ded4d91a3e1df8fd87d67f4b8d3f14d8201a75f923c",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(argv: list[str], label: str) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(argv, cwd=REPO, text=True, capture_output=True, timeout=900, check=False)
    (OWN / f"{label}.stdout.log").write_text(proc.stdout)
    (OWN / f"{label}.stderr.log").write_text(proc.stderr)
    return proc


def main() -> int:
    seals_ok = all(sha(path) == expected for path, expected in EXPECTED.items())
    version = run([str(SINGULAR), "--version"], "singular_version")
    sage = run([str(SAGE), "-python", str(OWN / "proof_sage.py")], "sage_proof")
    singular = run([str(SINGULAR), "-q", str(OWN / "proof_singular.sing")], "singular_proof")
    errors = version.stderr + sage.stderr + singular.stderr
    version_ok = version.returncode == 0 and "version 4.4.1" in version.stdout and "44100" in version.stdout
    sage_rows = [json.loads(line) for line in sage.stdout.splitlines() if line.startswith("{")]
    sage_ok = sage.returncode == 0 and len(sage_rows) == 1 and sage_rows[0].get("all") is True
    markers = ("CERT derivative_identity=0", "CERT monotone_factorization=0", "ALL_SINGULAR_CERTIFICATES_ZERO")
    diagnostic = re.search(r"(?im)(^\s*\?|\berror\b|\bundefined\b|\bsyntax\b|\bFAIL\b)", singular.stdout + "\n" + singular.stderr)
    singular_ok = singular.returncode == 0 and all(singular.stdout.count(m) == 1 for m in markers) and diagnostic is None
    full = seals_ok and version_ok and sage_ok and singular_ok
    record = {
        "sage_exit_code": sage.returncode,
        "singular_exit_code": singular.returncode,
        "singular_version_exit_code": version.returncode,
        "singular_version": version.stdout.strip(),
        "singular_binary_sha256": sha(SINGULAR),
        "seals_ok": seals_ok,
        "sage": sage_rows[0] if sage_rows else None,
        "singular_markers": {m: singular.stdout.count(m) for m in markers},
        "raw_error_output": errors,
        "diagnostic_match": diagnostic.group(0) if diagnostic else None,
        "proof_scope": "Sage proves the universal analytic sign chain; Singular checks exact derivative and monotone-difference polynomial identities without replacing the infinite analytic proof by a truncation.",
    }
    (OWN / "proof_record.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    payload = {"checks": {"CAS-07-M01": full}, "domain_assumption_diff": [], "counterexample": None}
    print(json.dumps(payload, sort_keys=True))
    return 0 if full else 2


if __name__ == "__main__":
    raise SystemExit(main())
