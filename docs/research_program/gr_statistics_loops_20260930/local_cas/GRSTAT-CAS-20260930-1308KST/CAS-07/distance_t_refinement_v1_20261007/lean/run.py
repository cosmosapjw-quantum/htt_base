#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[8]
AXIS = Path(__file__).resolve().parent
UNIT = AXIS.parent
EVIDENCE = AXIS / "evidence"
ORACLE = Path("/home/cosmosapjw/lean_oracles/viii_oracle")
CONTRACT_SHA256 = "e4169b089e5c19accb838e3b43daa0fe44bfab43b0a5025a3167280069a6eb13"
INPUT_SHA256 = "9c85a30bdde1a294930ae40009b121e0e1a767a5c2d5e97fa9e27a3dc14b5bd3"
DEPENDENCIES = {
    "CAS07M01Accepted.olean": "83acab45987909a490f90af775cc0f3ce538de3a5e04ed5a04abc311d9c15ca2",
    "CAS07C03Accepted.olean": "7d4ec056d0b4f1f8dc43e941d00e842ea39901b496108ad2c4cdfd9c334a74a8",
    "CAS07M05Accepted.olean": "694b6683d9027ca7602277e4fdd9a65444a4ee0add69f7bdba42ccd0b7fbfab0",
}
PINNED_TOOLCHAIN_SHA256 = "efac0b94923b2d8b6840cd35be9177ad0fc5ab2332f4f4311c98712cee92fdee"
PINNED_MANIFEST_SHA256 = "bc86de9aed83fc38b0850702d6879ed6f3c97eedb7d1d69d643160731179d6ed"
MATHLIB_REVISION = "fabf563a7c95a166b8d7b6efca11c8b4dc9d911f"
EXPECTED_AXIOMS = {
    "CAS07M06.t_domain",
    "CAS07M06.eta_order",
    "CAS07M06.refined_fd1",
    "CAS07M06.no_worse_than_fd2",
    "CAS07M06.k_zero_control",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write(path: Path, data: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data, encoding="utf-8")


def main() -> int:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    source = AXIS / "Main.lean"
    contract = UNIT / "EXECUTION_CONTRACT.json"
    admitted = UNIT / "ADMITTED_INPUTS.json"
    checks = {
        "CAS-07-M06-T-DOMAIN": False,
        "CAS-07-M06-ETA-ORDER": False,
        "CAS-07-M06-REFINED-FD1": False,
        "CAS-07-M06-NO-WORSE-THAN-FD2": False,
    }
    failures: list[str] = []

    if sha256(contract) != CONTRACT_SHA256:
        failures.append("contract_sha256_mismatch")
    if sha256(admitted) != INPUT_SHA256:
        failures.append("admitted_input_sha256_mismatch")
    dependency_hashes: dict[str, str] = {}
    for name, expected in DEPENDENCIES.items():
        actual = sha256(ORACLE / name)
        dependency_hashes[name] = actual
        if actual != expected:
            failures.append(f"dependency_sha256_mismatch:{name}")

    formal_toolchain = ROOT / "formal_mathlib" / "lean-toolchain"
    formal_manifest = ROOT / "formal_mathlib" / "lake-manifest.json"
    oracle_toolchain = ORACLE / "lean-toolchain"
    oracle_manifest = ORACLE / "lake-manifest.json"
    if sha256(formal_toolchain) != PINNED_TOOLCHAIN_SHA256:
        failures.append("formal_toolchain_sha256_mismatch")
    if sha256(formal_manifest) != PINNED_MANIFEST_SHA256:
        failures.append("formal_manifest_sha256_mismatch")
    if sha256(oracle_toolchain) != PINNED_TOOLCHAIN_SHA256:
        failures.append("oracle_toolchain_sha256_mismatch")
    formal_packages = {
        item["name"]: item.get("rev")
        for item in json.loads(formal_manifest.read_text(encoding="utf-8"))["packages"]
    }
    oracle_packages = {
        item["name"]: item.get("rev")
        for item in json.loads(oracle_manifest.read_text(encoding="utf-8"))["packages"]
    }
    package_revision_parity = formal_packages == oracle_packages
    if not package_revision_parity or oracle_packages.get("mathlib") != MATHLIB_REVISION:
        failures.append("oracle_package_revision_mismatch")

    source_text = source.read_text(encoding="utf-8")
    forbidden_patterns = {
        "sorry": r"\bsorry\b",
        "admit": r"\badmit\b",
        "unsafe": r"\bunsafe\b",
        "native_decide": r"\bnative_decide\b",
        "new_axiom_declaration": r"(?m)^\s*axiom\b",
    }
    forbidden_hits = {
        name: bool(re.search(pattern, source_text))
        for name, pattern in forbidden_patterns.items()
    }
    if any(forbidden_hits.values()):
        failures.extend(name for name, hit in forbidden_hits.items() if hit)

    version_argv = ["lake", "env", "lean", "--version"]
    version_proc = subprocess.run(
        version_argv, cwd=ORACLE, text=True, capture_output=True, check=False
    )
    write(EVIDENCE / "version.stdout", version_proc.stdout)
    write(EVIDENCE / "version.stderr", version_proc.stderr)
    write(EVIDENCE / "version.exit", f"{version_proc.returncode}\n")

    temp_source = ORACLE / "CAS07M06Main.generated.lean"
    shutil.copyfile(source, temp_source)
    output_olean = EVIDENCE / "Main.olean"
    compile_argv = [
        "lake", "env", "lean", "-R", str(ORACLE), "-o", str(output_olean),
        str(temp_source.relative_to(ORACLE)),
    ]
    env = dict(os.environ)
    env["LEAN_PATH"] = str(ORACLE)
    try:
        proc = subprocess.run(
            compile_argv,
            cwd=ORACLE,
            env=env,
            text=True,
            capture_output=True,
            check=False,
            timeout=7200,
        )
    finally:
        temp_source.unlink(missing_ok=True)

    write(EVIDENCE / "compile.stdout", proc.stdout)
    write(EVIDENCE / "compile.stderr", proc.stderr)
    write(EVIDENCE / "compile.exit", f"{proc.returncode}\n")
    axiom_lines = {
        line.split("'", 2)[1]
        for line in proc.stdout.splitlines()
        if line.startswith("'") and " depends on axioms: " in line
    }
    standard_axioms_only = axiom_lines == EXPECTED_AXIOMS and all(
        line.endswith("[propext, Classical.choice, Quot.sound]")
        for line in proc.stdout.splitlines()
        if " depends on axioms: " in line
    )
    if proc.returncode != 0:
        failures.append("lean_compile_nonzero")
    if not standard_axioms_only:
        failures.append("axiom_output_mismatch")

    if not failures:
        checks = {key: True for key in checks}

    status = "PASS" if all(checks.values()) else "FAIL"
    result = {
        "schema": "htt.cas-axis-result.v2",
        "axis": "lean",
        "status": status,
        "evidence_class": "exact",
        "contract_sha256": CONTRACT_SHA256,
        "admitted_inputs_sha256": INPUT_SHA256,
        "checks": checks,
        "domain_assumption_diff": [],
        "counterexample": None,
        "boundary_controls": {
            "K=0": "CAS07M06.k_zero_control kernel-compiled",
            "both_min_branches": "min lower and both min projections used in universal proof",
            "H0=0": "subsumed by universal exact theorem",
            "M2=0": "subsumed by universal exact theorem",
        },
        "execution": {
            "launch_id": None,
            "authority_status": "UNAVAILABLE",
            "observed_model": "UNKNOWN",
            "observed_effort": "UNKNOWN",
            "argv": compile_argv,
            "cwd": str(ORACLE),
            "exit_code": proc.returncode,
            "lean_version_argv": version_argv,
            "lean_version_exit_code": version_proc.returncode,
            "lean_version": version_proc.stdout.strip(),
            "mathlib_revision": MATHLIB_REVISION,
        },
        "source": {
            "path": str(source.relative_to(ROOT)),
            "sha256": sha256(source),
            "forbidden_token_hits": forbidden_hits,
        },
        "dependencies": dependency_hashes,
        "toolchain_binding": {
            "formal_toolchain_sha256": sha256(formal_toolchain),
            "formal_manifest_sha256": sha256(formal_manifest),
            "oracle_toolchain_sha256": sha256(oracle_toolchain),
            "oracle_manifest_sha256": sha256(oracle_manifest),
            "oracle_manifest_byte_identity": sha256(oracle_manifest) == sha256(formal_manifest),
            "manifest_mismatch_class": "packaging_metadata" if sha256(oracle_manifest) != sha256(formal_manifest) else None,
            "package_revision_parity": package_revision_parity,
            "package_revisions": oracle_packages,
        },
        "artifacts": {
            "olean_sha256": sha256(output_olean) if output_olean.exists() else None,
            "compile_stdout_sha256": sha256(EVIDENCE / "compile.stdout"),
            "compile_stderr_sha256": sha256(EVIDENCE / "compile.stderr"),
            "compile_exit_sha256": sha256(EVIDENCE / "compile.exit"),
            "version_stdout_sha256": sha256(EVIDENCE / "version.stdout"),
            "version_stderr_sha256": sha256(EVIDENCE / "version.stderr"),
            "version_exit_sha256": sha256(EVIDENCE / "version.exit"),
        },
        "axioms": {
            "theorems_seen": sorted(axiom_lines),
            "expected_theorems": sorted(EXPECTED_AXIOMS),
            "standard_axioms_only": standard_axioms_only,
        },
        "preserved_failed_attempts": [
            {
                "attempt": 1,
                "classification": "input_outside_lean_root",
                "exit_code": int((EVIDENCE / "failures" / "compile_attempt1.exit").read_text().strip()),
                "stdout_sha256": sha256(EVIDENCE / "failures" / "compile_attempt1.stdout"),
                "stderr_sha256": sha256(EVIDENCE / "failures" / "compile_attempt1.stderr"),
            },
            {
                "attempt": 2,
                "classification": "real_division_definitions_needed_noncomputable",
                "exit_code": int((EVIDENCE / "failures" / "compile_attempt2.exit").read_text().strip()),
                "stdout_sha256": sha256(EVIDENCE / "failures" / "compile_attempt2.stdout"),
                "stderr_sha256": sha256(EVIDENCE / "failures" / "compile_attempt2.stderr"),
            },
        ],
        "failures": failures,
        "claim_ceiling": "distance-only refinement; no endpoint identification or scientific admission",
        "scientific_admission": "HOLD",
    }
    result_path = AXIS / "result.json"
    write(result_path, json.dumps(result, indent=2, sort_keys=True) + "\n")
    envelope = {
        "status": status,
        "checks": checks,
        "domain_assumption_diff": [],
        "counterexample": None,
        "result_path": str(result_path.relative_to(ROOT)),
    }
    print(json.dumps(envelope, separators=(",", ":")))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
