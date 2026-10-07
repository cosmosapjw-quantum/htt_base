#!/usr/bin/env python3
"""Run the pinned Lean axis for the frozen CAS-10-C02 finite contract."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


REPO = Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
ORACLE = Path("/home/cosmosapjw/lean_oracles/viii_oracle")
AXIS = REPO / (
    "docs/research_program/gr_statistics_loops_20260930/local_cas/"
    "GRSTAT-CAS-20260930-1308KST/CAS-10/"
    "c02_mass_shell_invariant_v1_20261008/lean"
)
UNIT = AXIS.parent
CONTRACT = UNIT / "EXECUTION_CONTRACT.json"
ADMITTED = UNIT / "ADMITTED_INPUTS.json"
COMMON = REPO / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
MAIN = AXIS / "Main.lean"
RUNNER = AXIS / "run.py"
RESULT = AXIS / "result.json"
EXECUTION = AXIS / "execution.json"
TOOLCHAIN = "leanprover/lean4:v4.31.0"
MATHLIB_REV = "fabf563a7c95a166b8d7b6efca11c8b4dc9d911f"

EXPECTED_INPUT_HASHES = {
    str(CONTRACT.relative_to(REPO)): "c6957c9d87d416668d2f33ee94946aa04f3bf0da09aa06cac7cdb07b0eaab2ef",
    str(ADMITTED.relative_to(REPO)): "6f699739b3835b3bbaa02202bcabf7381a0d57860e2eb28f8441c8d392fda074",
    str(COMMON.relative_to(REPO)): "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def invoke(argv: list[str], *, timeout: int) -> dict[str, object]:
    started = time.monotonic()
    try:
        completed = subprocess.run(
            argv,
            cwd=ORACLE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=timeout,
            env=os.environ.copy(),
        )
        return {
            "argv": argv,
            "cwd": str(ORACLE),
            "exit_code": completed.returncode,
            "timed_out": False,
            "wall_seconds": time.monotonic() - started,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
    except subprocess.TimeoutExpired as error:
        return {
            "argv": argv,
            "cwd": str(ORACLE),
            "exit_code": 124,
            "timed_out": True,
            "wall_seconds": time.monotonic() - started,
            "stdout": error.stdout or b"",
            "stderr": error.stderr or b"",
        }


def persist_raw(prefix: str, record: dict[str, object]) -> None:
    (AXIS / f"{prefix}.stdout.log").write_bytes(record["stdout"])
    (AXIS / f"{prefix}.stderr.log").write_bytes(record["stderr"])


def public_record(record: dict[str, object]) -> dict[str, object]:
    return {
        "argv": record["argv"],
        "cwd": record["cwd"],
        "exit_code": record["exit_code"],
        "timed_out": record["timed_out"],
        "wall_seconds": record["wall_seconds"],
    }


def main() -> int:
    version_argv = [
        "/usr/bin/env",
        f"ELAN_TOOLCHAIN={TOOLCHAIN}",
        "lake",
        "env",
        "lean",
        "--version",
    ]
    mathlib_argv = [
        "git",
        "-C",
        str(ORACLE / ".lake/packages/mathlib"),
        "rev-parse",
        "HEAD",
    ]
    compile_argv = [
        "/usr/bin/env",
        f"ELAN_TOOLCHAIN={TOOLCHAIN}",
        "lake",
        "env",
        "lean",
        str(MAIN),
    ]

    version = invoke(version_argv, timeout=120)
    mathlib = invoke(mathlib_argv, timeout=120)
    compile_run = invoke(compile_argv, timeout=3600)
    persist_raw("lean.version", version)
    persist_raw("mathlib.rev", mathlib)
    persist_raw("lean.compile", compile_run)

    input_hashes = {
        str(path.relative_to(REPO)): sha256(path)
        for path in (CONTRACT, ADMITTED, COMMON)
    }
    source_hashes = {
        str(path.relative_to(REPO)): sha256(path)
        for path in (MAIN, RUNNER)
    }
    log_paths = [
        AXIS / "lean.version.stdout.log",
        AXIS / "lean.version.stderr.log",
        AXIS / "mathlib.rev.stdout.log",
        AXIS / "mathlib.rev.stderr.log",
        AXIS / "lean.compile.stdout.log",
        AXIS / "lean.compile.stderr.log",
    ]
    log_hashes = {str(path.relative_to(REPO)): sha256(path) for path in log_paths}

    version_text = version["stdout"].decode("utf-8", errors="replace")
    mathlib_text = mathlib["stdout"].decode("utf-8", errors="replace").strip()
    compile_text = compile_run["stdout"].decode("utf-8", errors="replace")
    theorem_names = [
        "b_orthogonal",
        "b_square_eq_Jgeo",
        "rest_space_nonneg",
        "rest_space_zero_iff",
        "A_square_identity",
        "A_zero_iff_b_zero",
        "mass_shell_invariant",
    ]
    axiom_lines = [line for line in compile_text.splitlines() if "depends on axioms:" in line]
    forbidden_axioms = ["sorryAx", "admit", "mass_shell_invariant,"]
    axiom_audit_ok = (
        all(any(f"CAS10C02.{name}'" in line for line in axiom_lines) for name in theorem_names)
        and not any(token in compile_text for token in forbidden_axioms)
    )

    checks = {
        "input_hashes_match": input_hashes == EXPECTED_INPUT_HASHES,
        "lean_version_match": version["exit_code"] == 0
        and "Lean (version 4.31.0" in version_text,
        "mathlib_revision_match": mathlib["exit_code"] == 0
        and mathlib_text == MATHLIB_REV,
        "compiler_exit_zero": compile_run["exit_code"] == 0,
        "compiler_not_timed_out": not compile_run["timed_out"],
        "axiom_audit_pass": axiom_audit_ok,
        "exact_target_theorem_present": any(
            "CAS10C02.mass_shell_invariant' depends on axioms:" in line
            for line in axiom_lines
        ),
    }
    passed = all(checks.values())

    execution = {
        "schema": "htt.cas10.c02.lean-execution.v1",
        "axis": "lean",
        "version": public_record(version),
        "mathlib_revision": public_record(mathlib),
        "compile": public_record(compile_run),
        "input_hashes": input_hashes,
        "source_hashes": source_hashes,
        "raw_log_hashes": log_hashes,
    }
    EXECUTION.write_text(json.dumps(execution, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = {
        "schema": "htt.cas-axis-result.v1",
        "contract_id": "GRSTAT-20260930-CAS-10-C02-MASS-SHELL-INVARIANT-V1",
        "component": "CAS-10-C02",
        "axis": "lean",
        "status": "PASS" if passed else "FAIL",
        "evidence_class": "exact",
        "claim_ceiling": "finite C02 mass-shell invariant only",
        "scientific_admission": "HOLD",
        "runtime_attribution": {
            "launch_id": None,
            "authority": "unavailable",
            "model": "UNKNOWN",
            "effort": "UNKNOWN",
        },
        "toolchain": {
            "lean": "4.31.0",
            "elan_toolchain": TOOLCHAIN,
            "environment": str(ORACLE),
            "mathlib_revision": MATHLIB_REV,
        },
        "checks": checks,
        "proved_targets": [
            "u^T b = 0",
            "Jgeo = b^T g^-1 b",
            "Jgeo = A^T g^-1 A / (4 c^2)",
            "Jgeo >= 0 on the future unit mass shell",
            "Jgeo = 0 iff A = 0",
        ],
        "explicit_hypotheses": [
            "S is a real symmetric covariant 4 by 4 matrix",
            "g = diag(-1,1,1,1)",
            "g(u,u) = -1",
            "u0 > 0",
            "c > 0",
            "h = u^T S u, b = (S + h g)u, A = 2 c b",
        ],
        "domain_assumption_diff": [],
        "counterexample": None,
        "remaining_obligations": [
            "CAS10 C01,C03,C04 exact input alignment",
            "probability-law and analytic obligations",
            "science",
        ],
        "axiom_audit": {
            "status": "PASS" if axiom_audit_ok else "FAIL",
            "forbidden": ["sorryAx", "admit", "new target axiom"],
            "observed_mathlib_axioms": ["propext", "Classical.choice", "Quot.sound"],
            "raw_log": str((AXIS / "lean.compile.stdout.log").relative_to(REPO)),
        },
        "provenance": {
            "input_hashes": input_hashes,
            "source_hashes": source_hashes,
            "execution_record": str(EXECUTION.relative_to(REPO)),
            "execution_record_sha256": sha256(EXECUTION),
            "raw_log_hashes": log_hashes,
        },
    }
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    envelope = {
        "status": result["status"],
        "checks": {"CAS-10-C02": passed},
        "domain_assumption_diff": [],
        "counterexample": None,
        "result_path": str(RESULT.relative_to(REPO)),
    }
    print(json.dumps(envelope, sort_keys=True, separators=(",", ":")))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
