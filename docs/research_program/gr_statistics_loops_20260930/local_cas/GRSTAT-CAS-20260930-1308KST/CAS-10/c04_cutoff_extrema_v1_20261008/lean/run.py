#!/usr/bin/env python3
"""Reproduce the frozen CAS-10-C04 Lean proof and exact Boolean payload."""

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import re
import subprocess
import sys


REPO = Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
ORACLE = Path("/home/cosmosapjw/lean_oracles/viii_oracle")
UNIT = REPO / "docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-10/c04_cutoff_extrema_v1_20261008"
AXIS = UNIT / "lean"
CONTRACT = UNIT / "EXECUTION_CONTRACT.json"
INPUT = UNIT / "ADMITTED_INPUTS.json"
COMMON = REPO / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
SOURCE = AXIS / "CutoffExtrema.lean"
EXPECTED = {
    CONTRACT: "8f2f5e387e8130f605073c650c9c0174253dd70e34ae4d4fbb23c697b53ead3a",
    INPUT: "1df59b533e32a7f21d3a7a1ee90c39cf6451b42bcd10d4ec580bdb031a47e992",
    COMMON: "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
    SOURCE: "ab2f98d27e4d00694c428258e78a81dd438d38066b5d28c08090fd2c12b7c1f3",
    ORACLE / "lake-manifest.json": "1a7cbb6b0487b078e2e5f768fc9e1bd78e2e36d0d896477cadf1d8971464db08",
    ORACLE / "lean-toolchain": "efac0b94923b2d8b6840cd35be9177ad0fc5ab2332f4f4311c98712cee92fdee",
}
MATHLIB_REV = "fabf563a7c95a166b8d7b6efca11c8b4dc9d911f"
OLEAN = ORACLE / ".lake/packages/mathlib/.lake/build/lib/lean/Mathlib.olean"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def command(argv: list[str], *, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ, ELAN_TOOLCHAIN="leanprover/lean4:v4.31.0")
    return subprocess.run(argv, cwd=ORACLE, env=env, text=True, capture_output=True,
                          timeout=timeout, check=False)


def main() -> int:
    AXIS.mkdir(exist_ok=True)
    actual = {str(p): digest(p) for p in EXPECTED}
    hashes_ok = all(actual[str(p)] == expected for p, expected in EXPECTED.items())
    source_text = SOURCE.read_text()
    shortcuts_absent = re.search(r"\b(?:sorry|admit|axiom)\b", source_text) is None
    olean_present = OLEAN.is_file()
    rev = command(["git", "-C", str(ORACLE / ".lake/packages/mathlib"), "rev-parse", "HEAD"])
    rev_ok = rev.returncode == 0 and rev.stdout.strip() == MATHLIB_REV
    lean_version = command(["lean", "--version"])
    version_ok = (lean_version.returncode == 0 and
                  "Lean (version 4.31.0" in lean_version.stdout)
    lake_version = command(["lake", "--version"])
    preflight_ok = all([hashes_ok, shortcuts_absent, olean_present, rev_ok, version_ok,
                        lake_version.returncode == 0])

    argv = ["lake", "env", "lean", str(SOURCE)]
    if preflight_ok:
        proof = command(argv, timeout=3600)
    else:
        proof = subprocess.CompletedProcess(argv, 125, "", "Preflight binding failed.\n")
    (AXIS / "lean.stdout.log").write_text(proof.stdout)
    (AXIS / "lean.stderr.log").write_text(proof.stderr)
    compiled = preflight_ok and proof.returncode == 0

    # Each Boolean is backed by a named theorem in the sealed, compiled source.
    theorem_names = {
        "first_derivative_identity": "F_hasDerivAt",
        "second_derivative_identity": "Fp_hasDerivAt",
        "endpoint_jets": "endpoint_jets",
        "global_abs_first_derivative_bound": "fp_abs_bound",
        "first_derivative_midpoint_equality": "fp_mid",
        "global_abs_second_derivative_bound": "fpp_abs_bound",
        "both_second_derivative_critical_points_in_domain": "tminus_mem",
        "both_second_derivative_equalities": "fpp_critical_values",
        "rational_margin": "rational_margin",
    }
    checks = {name: compiled and f"theorem {theorem}" in source_text
              for name, theorem in theorem_names.items()}
    checks["both_second_derivative_critical_points_in_domain"] = (
        checks["both_second_derivative_critical_points_in_domain"] and
        "theorem tplus_mem" in source_text
    )

    execution = {
        "argv": argv,
        "cwd": str(ORACLE),
        "env_override": {"ELAN_TOOLCHAIN": "leanprover/lean4:v4.31.0"},
        "exit_code": proof.returncode,
        "lean_version": lean_version.stdout.strip(),
        "lake_version": lake_version.stdout.strip(),
        "mathlib_revision": rev.stdout.strip(),
        "version_probes": [
            {"argv": ["lean", "--version"], "exit_code": lean_version.returncode,
             "stdout": lean_version.stdout, "stderr": lean_version.stderr},
            {"argv": ["lake", "--version"], "exit_code": lake_version.returncode,
             "stdout": lake_version.stdout, "stderr": lake_version.stderr},
            {"argv": ["git", "-C", str(ORACLE / ".lake/packages/mathlib"), "rev-parse", "HEAD"],
             "exit_code": rev.returncode, "stdout": rev.stdout, "stderr": rev.stderr},
        ],
        "olean_path": str(OLEAN),
        "olean_present": olean_present,
        "input_sha256": actual,
        "hashes_ok": hashes_ok,
        "shortcuts_absent": shortcuts_absent,
        "preflight_ok": preflight_ok,
        "stdout_path": str(AXIS / "lean.stdout.log"),
        "stderr_path": str(AXIS / "lean.stderr.log"),
    }
    (AXIS / "execution.json").write_text(json.dumps(execution, indent=2) + "\n")
    payload = {
        "schema": "htt.cas10.c04.lean.exact-boolean.v1",
        "contract_sha256": actual[str(CONTRACT)],
        "admitted_input_sha256": actual[str(INPUT)],
        "source_sha256": actual[str(SOURCE)],
        "domain": "real t in [0,1]",
        "branch": "positive real sqrt(3)",
        "checks": checks,
        "all_pass": all(checks.values()),
        "remaining": ["mollifier existence/smooth radial extension",
                      "two-point probability bounds", "science"],
    }
    (AXIS / "result.json").write_text(json.dumps(payload, indent=2) + "\n")
    axis_result = {
        "axis": "lean",
        "status": "PASS" if payload["all_pass"] else "BLOCKED",
        "contract_sha256": actual[str(CONTRACT)],
        "evidence_class": "exact",
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "commands": [{"argv": argv, "cwd": str(ORACLE),
                      "env_override": execution["env_override"],
                      "exit_code": proof.returncode,
                      "stdout_path": execution["stdout_path"],
                      "stderr_path": execution["stderr_path"]}],
        "actual_tool_versions": {
            "lean": lean_version.stdout.strip(),
            "lake": lake_version.stdout.strip(),
            "mathlib_revision": rev.stdout.strip(),
        },
        "toolchain_binding": {
            "manifest_sha256": actual[str(ORACLE / "lake-manifest.json")],
            "lean_toolchain_sha256": actual[str(ORACLE / "lean-toolchain")],
            "olean_path": str(OLEAN),
            "olean_present": olean_present,
        },
        "source_paths": [str(SOURCE)],
        "result_path": str(AXIS / "result.json"),
        "execution_path": str(AXIS / "execution.json"),
        "domain_assumption_diff": [],
        "branch_diff": [],
        "findings": checks,
        "remaining_obligations": payload["remaining"],
        "claim_ceiling": "CAS10 C04 finite polynomial extrema and rational bound only",
        "scientific_admission": "HOLD",
        "global_launch_id": None,
        "global_launch_status": "UNAVAILABLE",
        "observed_author_model": "UNKNOWN",
        "observed_author_effort": "UNKNOWN",
        "shared_llm_family": "UNKNOWN",
    }
    (AXIS / "axis_result.json").write_text(json.dumps(axis_result, indent=2) + "\n")
    print(json.dumps({
        "checks": {"CAS-10-C04": payload["all_pass"]},
        "domain_assumption_diff": [],
        "counterexample": None,
    }, separators=(",", ":")))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
