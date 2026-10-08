#!/usr/bin/env python3
"""Stdlib runner for the Sage+Singular CAS-07 M05 axis."""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
import subprocess
import sys
from datetime import datetime, timezone


HERE = pathlib.Path(__file__).resolve().parent
REPO = next(parent for parent in (HERE, *HERE.parents) if (parent / ".git").exists())
BRIDGE = HERE.parent
CONTRACT = BRIDGE / "EXECUTION_CONTRACT.json"
INPUTS = BRIDGE / "ADMITTED_INPUTS.json"
COMMON_SPEC = REPO / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
SAGE = pathlib.Path("/home/cosmosapjw/opt/sage/sage")
SINGULAR = pathlib.Path("/home/cosmosapjw/opt/sage/local/bin/Singular")

EXPECTED_HASHES = {
    CONTRACT: "24e3ae1e11d2a75335cd7fac436e8d1656100dc7877672d08464a4612a19348e",
    INPUTS: "22fbf2a3fcc428d25f8e9fb0d6e1866c8057ebc7e76dd4ad248bd144300a5a75",
    COMMON_SPEC: "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
    SINGULAR: "9430832b7c972b6b26d29ded4d91a3e1df8fd87d67f4b8d3f14d8201a75f923c",
}


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(argv: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=1800,
        check=False,
    )


def write_raw(name: str, completed: subprocess.CompletedProcess[str]) -> None:
    (HERE / f"{name}.stdout.log").write_text(completed.stdout, encoding="utf-8")
    (HERE / f"{name}.stderr.log").write_text(completed.stderr, encoding="utf-8")


hashes = {str(path): sha256(path) for path in EXPECTED_HASHES}
hashes_match = all(hashes[str(path)] == expected for path, expected in EXPECTED_HASHES.items())

sage_version = run([str(SAGE), "--version"])
singular_version = run([str(SINGULAR), "--version"])
sage_run = run([str(SAGE), str(HERE / "determinant_distance_bridge.sage")])
singular_run = run([str(SINGULAR), "-q", str(HERE / "polynomial_controls.sing")])

write_raw("sage", sage_run)
write_raw("singular", singular_run)
write_raw("sage_version", sage_version)
write_raw("singular_version", singular_version)

singular_error_lines = [
    line
    for line in (singular_run.stdout + "\n" + singular_run.stderr).splitlines()
    if re.match(r"^\s*\?", line) or "error occurred" in line.lower()
]
diagnostics_clean = (
    sage_run.returncode == 0
    and singular_run.returncode == 0
    and not sage_run.stderr.strip()
    and not singular_run.stderr.strip()
    and not singular_error_lines
)

sage_markers = {
    "SAGE_REWRITE_EXACT=true",
    "SAGE_C02_PREMISE_GAP_IDENTITY=true",
    "SAGE_ARBITRARY_NONSYMMETRIC_SCOPE=true",
    "SAGE_K0_CONTROL=true",
}
singular_markers = {
    "SINGULAR_REWRITE_EXACT=true",
    "SINGULAR_C02_PREMISE_GAP_IDENTITY=true",
    "SINGULAR_ARBITRARY_NONSYMMETRIC_SCOPE=true",
    "SINGULAR_K0_CONTROL=true",
}
algebra_ok = sage_markers.issubset(set(sage_run.stdout.splitlines())) and singular_markers.issubset(
    set(singular_run.stdout.splitlines())
)

with INPUTS.open(encoding="utf-8") as stream:
    admitted = json.load(stream)
dependency_statements = {
    item["component"]: item["statement"] for item in admitted["accepted_dependencies"]
}
interfaces_bound = set(dependency_statements) == {"CAS-07-M01", "CAS-07-M04", "CAS-07-C02"}
m01_bound = "0<=eta_K(s)<=eta_K(L)<1" in dependency_statements.get("CAS-07-M01", "")
m04_bound = "||D(s)-s Id||op<=f_K(s)-s" in dependency_statements.get("CAS-07-M04", "")
c02_statement = dependency_statements.get("CAS-07-C02", "")
c02_sign_bound = "det(D)>0" in c02_statement
c02_distance_bound = "positive sqrt(det(D)) lies in the same interval" in c02_statement
c02_scope_bound = "arbitrary real 2x2 D" in c02_statement

version_ok = (
    sage_version.returncode == 0
    and "SageMath version 10.9" in sage_version.stdout
    and singular_version.returncode == 0
    and "version 4.4.1 (44100" in singular_version.stdout
)

rewrite = hashes_match and version_ok and diagnostics_clean and algebra_ok
premise = rewrite and interfaces_bound and m01_bound and m04_bound
determinant_sign = premise and c02_scope_bound and c02_sign_bound
distance_bound = determinant_sign and c02_distance_bound
domain_assumption_diff: list[str] = []
counterexample = None

receipt = {
    "schema": "htt.cas07.m05.sage-singular-run-receipt.v1",
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "argv": {
        "sage": [str(SAGE), str(HERE / "determinant_distance_bridge.sage")],
        "singular": [str(SINGULAR), "-q", str(HERE / "polynomial_controls.sing")],
    },
    "cwd": str(REPO),
    "returncodes": {"sage": sage_run.returncode, "singular": singular_run.returncode},
    "hashes": hashes,
    "hashes_match": hashes_match,
    "version_ok": version_ok,
    "diagnostics_clean": diagnostics_clean,
    "singular_error_lines": singular_error_lines,
    "checks": {
        "CAS-07-M05-REWRITE": rewrite,
        "CAS-07-M05-C02-PREMISE": premise,
        "CAS-07-M05-DETERMINANT-SIGN": determinant_sign,
        "CAS-07-M05-DISTANCE-BOUND": distance_bound,
    },
    "domain_assumption_diff": domain_assumption_diff,
    "counterexample": counterexample,
}
(HERE / "run_receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")

stdout_document = {
    "status": "PASS" if all(receipt["checks"].values()) else "BLOCKED",
    "checks": receipt["checks"],
    "domain_assumption_diff": domain_assumption_diff,
    "counterexample": counterexample,
    "result_path": str((HERE / "result.json").relative_to(REPO)),
}
print(json.dumps(stdout_document, sort_keys=True))

if not all(receipt["checks"].values()):
    sys.exit(1)
