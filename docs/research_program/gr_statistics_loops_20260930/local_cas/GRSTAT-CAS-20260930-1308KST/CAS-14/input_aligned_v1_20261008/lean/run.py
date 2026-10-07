#!/usr/bin/env python3
"""Run the CAS-14 Lean axis against its frozen contract and pinned mathlib."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

AXIS = Path(__file__).resolve().parent
UNIT = AXIS.parent
SOURCE = AXIS / "Main.lean"
ORACLE = Path("/home/cosmosapjw/lean_oracles/viii_oracle")
MATHLIB = ORACLE / ".lake/packages/mathlib"
CONTRACT_SHA = "afee8b0f823bb89f9a1507a5c8fbcff97c95f152296f88e55e15cdcdbce21639"
INPUT_SHA = "ed8d777bf74f3b35af925e807a90842af9530355a6f392dab5d5e0bbcf1a7591"
MATHLIB_REV = "fabf563a7c95a166b8d7b6efca11c8b4dc9d911f"
STANDARD_AXIOMS = {"propext", "Classical.choice", "Quot.sound"}
THEOREMS = {
    "CAS-14-C01": ["W_sign", "C01_cross_data", "C01_b_eq_G"],
    "CAS-14-C02": ["C02_stack_normal", "C02_kernel_intersection",
                   "C02_two_nonparallel_pos", "C02_inverse_formula",
                   "C02_all_parallel_control", "C02_e1_e2_control"],
    "CAS-14-C03": ["C03_exact_bound", "C03_perturbed_bound",
                   "C03_frobenius", "C03_no_amplitude_control",
                   "C03_zero_data_error", "C03_zero_operator_error"],
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command(argv: list[str], *, cwd: Path, timeout: int = 60) -> dict:
    started = time.monotonic()
    env = dict(os.environ, ELAN_TOOLCHAIN="leanprover/lean4:v4.31.0")
    try:
        p = subprocess.run(argv, cwd=cwd, env=env, text=True,
                           capture_output=True, timeout=timeout, check=False)
        return {"argv": argv, "cwd": str(cwd), "exit_code": p.returncode,
                "stdout": p.stdout, "stderr": p.stderr,
                "wall_seconds": round(time.monotonic() - started, 3)}
    except subprocess.TimeoutExpired as exc:
        return {"argv": argv, "cwd": str(cwd), "exit_code": None,
                "timeout_seconds": timeout,
                "stdout": (exc.stdout or b"").decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or ""),
                "stderr": (exc.stderr or b"").decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or ""),
                "wall_seconds": round(time.monotonic() - started, 3)}


def main() -> int:
    contract_ok = digest(UNIT / "EXECUTION_CONTRACT.json") == CONTRACT_SHA
    input_ok = digest(UNIT / "ADMITTED_INPUTS.json") == INPUT_SHA
    version = command(["lake", "env", "lean", "--version"], cwd=ORACLE)
    revision = command(["git", "rev-parse", "HEAD"], cwd=MATHLIB)
    argv = ["lake", "env", "lean", str(SOURCE)]
    execution = command(argv, cwd=ORACLE, timeout=3600)
    (AXIS / "run.stdout.log").write_text(execution["stdout"])
    (AXIS / "run.stderr.log").write_text(execution["stderr"])
    axioms = {}
    for name in {name for values in THEOREMS.values() for name in values}:
        match = re.search(r"'CAS14\." + re.escape(name) +
                          r"' depends on axioms: \[([^\]]*)\]", execution["stdout"])
        axioms[name] = [s.strip() for s in match.group(1).split(",")] if match else None
    source_text = SOURCE.read_text()
    no_forbidden_source = not re.search(r"\b(?:sorry|admit|unsafe|native_decide|axiom)\b", source_text)
    axiom_ok = all(values is not None and set(values) <= STANDARD_AXIOMS
                   for values in axioms.values())
    checks = {
        key: bool(contract_ok and input_ok and version["exit_code"] == 0
                  and "Lean (version 4.31.0" in version["stdout"]
                  and revision["stdout"].strip() == MATHLIB_REV
                  and execution["exit_code"] == 0 and no_forbidden_source
                  and axiom_ok and all(axioms[name] is not None for name in names))
        for key, names in THEOREMS.items()
    }
    status = "PASS" if all(checks.values()) else "FAIL"
    result = {
        "schema": "htt.cas.axis-result.v1", "axis": "lean", "status": status,
        "evidence_class": "exact", "checks": checks,
        "domain_assumption_diff": [], "counterexample": None,
        "contract_sha256": CONTRACT_SHA, "input_sha256": INPUT_SHA,
        "source_sha256": digest(SOURCE), "runner_sha256": digest(Path(__file__)),
        "toolchain": {"lean_version": version["stdout"].strip(),
                      "mathlib_revision": revision["stdout"].strip(),
                      "oracle_path": str(ORACLE),
                      "manifest_sha256": digest(ORACLE / "lake-manifest.json")},
        "execution": {k: v for k, v in execution.items() if k not in ("stdout", "stderr")},
        "version_execution": version,
        "revision_execution": revision,
        "axioms_by_theorem": axioms,
        "source_forbidden_token_absent": no_forbidden_source,
        "raw_stdout_path": str(AXIS / "run.stdout.log"),
        "raw_stderr_path": str(AXIS / "run.stderr.log"),
        "runtime_observation": {"launch_id": None, "authority_status": "UNAVAILABLE",
                                "observed_model": "UNKNOWN", "observed_effort": "UNKNOWN"},
        "scope": "finite mathematical components only; observation and scientific admission HOLD",
    }
    (AXIS / "result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"status": status, "checks": checks,
                      "domain_assumption_diff": [], "counterexample": None,
                      "result_path": str(AXIS / "result.json")}, separators=(",", ":")))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
