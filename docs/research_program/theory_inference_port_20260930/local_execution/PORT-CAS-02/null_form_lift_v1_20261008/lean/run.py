#!/usr/bin/env python3
"""No-argument, pinned Lean execution for the PORT-CAS-02 finite contract."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import uuid


AXIS_DIR = pathlib.Path(__file__).resolve().parent
TASK_DIR = AXIS_DIR.parent
REPO = AXIS_DIR.parents[6]
ORACLE = pathlib.Path("/home/cosmosapjw/lean_oracles/viii_oracle")
CONTRACT_SHA = "d62613255f18b2d2d2140cc6d73fbac27f6b2f8ac40ed9b268b9f5fc0fa166af"
INPUT_SHA = "849f9ebde2894f1deb15ba61452a3cc911d46af960b8630694cfe8cc15e3620a"
MATHLIB_COMMIT = "fabf563a7c95a166b8d7b6efca11c8b4dc9d911f"
SOURCE = AXIS_DIR / "PortCAS02.lean"
RESULT = AXIS_DIR / "axis_result.json"


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(argv: list[str], cwd: pathlib.Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, cwd=cwd, text=True, capture_output=True, check=False)


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def write_json(path: pathlib.Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def main() -> int:
    if len(sys.argv) != 1:
        print(json.dumps({"checks": {"PORT-CAS-02": False}, "domain_assumption_diff": ["unexpected arguments"], "counterexample": None}, separators=(",", ":")))
        return 2

    run_id = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ") + "-" + uuid.uuid4().hex[:8]
    evidence = AXIS_DIR / "runs" / run_id
    evidence.mkdir(parents=True, exist_ok=False)
    diff: list[str] = []
    commands: list[dict] = []

    def observed(argv: list[str], cwd: pathlib.Path, label: str) -> subprocess.CompletedProcess[str]:
        p = run(argv, cwd)
        stdout = evidence / f"{label}.stdout.log"
        stderr = evidence / f"{label}.stderr.log"
        stdout.write_text(p.stdout)
        stderr.write_text(p.stderr)
        commands.append({
            "argv": argv, "cwd": str(cwd), "exit_code": p.returncode,
            "stdout_path": str(stdout), "stdout_sha256": sha256(stdout),
            "stderr_path": str(stderr), "stderr_sha256": sha256(stderr),
        })
        return p

    try:
        contract_sha = sha256(TASK_DIR / "EXECUTION_CONTRACT.json")
        input_sha = sha256(TASK_DIR / "ADMITTED_INPUTS.json")
        source_sha = sha256(SOURCE)
        if contract_sha != CONTRACT_SHA:
            diff.append("contract hash drift")
        if input_sha != INPUT_SHA:
            diff.append("admitted input hash drift")
        if re.search(r"\b(sorry|admit|axiom)\b", SOURCE.read_text()):
            diff.append("forbidden proof token in source")

        lean_version = observed(["lake", "env", "lean", "--version"], ORACLE, "lean_version")
        lake_version = observed(["lake", "--version"], ORACLE, "lake_version")
        lean_path = observed(["lake", "env", "which", "lean"], ORACLE, "lean_path")
        mathlib = observed(["git", "-C", str(ORACLE / ".lake/packages/mathlib"), "rev-parse", "HEAD"], ORACLE, "mathlib_commit")
        executable = pathlib.Path(lean_path.stdout.strip()).resolve() if lean_path.returncode == 0 else None
        mathlib_commit = mathlib.stdout.strip()
        if lean_version.returncode or "version 4.31.0" not in lean_version.stdout:
            diff.append("Lean version drift")
        if mathlib.returncode or mathlib_commit != MATHLIB_COMMIT:
            diff.append("mathlib commit drift")
        if not executable or not executable.is_file():
            diff.append("Lean executable unavailable")

        compile_argv = ["lake", "env", "lean", str(SOURCE)]
        compile_result = observed(compile_argv, ORACLE, "lean_compile") if not diff else None
        if compile_result is not None and compile_result.returncode != 0:
            diff.append("Lean compilation failed")

        execution = {
            "schema": "htt.cas.axis-execution.v1", "axis": "lean", "run_id": run_id,
            "completed_at": utc_now(), "commands": commands,
            "contract_sha256": contract_sha, "admitted_input_sha256": input_sha,
            "source_path": str(SOURCE), "source_sha256": source_sha,
            "runner_path": str(pathlib.Path(__file__).resolve()),
            "runner_sha256": sha256(pathlib.Path(__file__).resolve()),
            "lean_version": lean_version.stdout.strip(), "lake_version": lake_version.stdout.strip(),
            "mathlib_commit": mathlib_commit, "lean_executable": str(executable) if executable else None,
            "lean_executable_sha256": sha256(executable) if executable and executable.is_file() else None,
            "python_executable": sys.executable, "python_executable_sha256": sha256(pathlib.Path(sys.executable).resolve()),
            "domain_assumption_diff": diff,
        }
        execution_path = evidence / "execution.json"
        write_json(execution_path, execution)

        if not diff:
            result = {
                "schema_version": 2, "axis": "lean", "status": "PASS", "evidence_class": "exact",
                "contract_id": "TYPEFREE-PORT-CAS-02-NULL-FORM-LIFT-V1", "contract_sha256": contract_sha,
                "admitted_input_sha256": input_sha, "completed_at": execution["completed_at"],
                "commands": commands, "tool_versions": {
                    "lean": execution["lean_version"], "lake": execution["lake_version"],
                    "mathlib_commit": mathlib_commit, "lean_executable": execution["lean_executable"],
                    "lean_executable_sha256": execution["lean_executable_sha256"],
                },
                "artifacts": {
                    "source_path": str(SOURCE), "source_sha256": source_sha,
                    "runner_path": execution["runner_path"], "runner_sha256": execution["runner_sha256"],
                    "execution_receipt": str(execution_path), "execution_receipt_sha256": sha256(execution_path),
                    "compile_stdout_path": commands[-1]["stdout_path"],
                    "compile_stdout_sha256": commands[-1]["stdout_sha256"],
                    "compile_stderr_path": commands[-1]["stderr_path"],
                    "compile_stderr_sha256": commands[-1]["stderr_sha256"],
                },
                "exact_targets": {
                    "null_metric": "null_metric", "null_polynomial": "null_S", "null_shift": "contraction_B",
                    "mixed_index_kernel_iff": "kernel_eigen_iff", "tracefree_spatial_monopole": "tracefree_monopole",
                    "symmetric_B": "B_symm", "gauge_B": "gauge_B", "gauge_null": "gauge_null",
                    "gauge_eigen": "gauge_eigen_iff", "antisymmetric_invisibility": "skew_contraction_zero",
                    "numeric_test_vector": "exact_test_vector", "metric_multiple_zero": "metric_multiple_zero",
                },
                "alignment": {
                    "metric_signature": "(-,+,+,+)", "metric_inverse": "g^{-1}=g; metric_involution and raise_lower proved",
                    "K": "contravariant (-1,n)", "n_domain": "dot n n=1",
                    "S_components": "S00=h0; S0i=Si0=-h1_i/2; Sij=qij",
                    "q_domain": "symmetric and tracefree in domain_null_form",
                    "u_branch": "FutureUnit premise in future_unit_kernel_eigen_iff; all-u kernel algebra proved",
                    "st": "real", "equivalence": "exact real equality/iff",
                    "exclusions": ["eigenline existence/uniqueness", "geodesicity", "finite-distance inference", "Bianchi family/science"],
                },
                "axioms": "Lean standard propext, Classical.choice, Quot.sound only; see compile stdout",
                "independence_mode": "blind-results-and-derivations", "sibling_artifacts_read": False,
                "registered_launch_id": None, "global_registered_launch": False,
                "observed_model": "UNKNOWN", "observed_effort": "UNKNOWN",
                "lifecycle_status": "BLOCKED_UNREGISTERED_LAUNCH",
                "runner_observed_four_axis_eligible": False, "scientific_admission": "HOLD",
                "scope": "PORT-CAS-02 finite exact algebra only",
            }
            temporary = AXIS_DIR / ("axis_result.json.tmp-" + run_id)
            write_json(temporary, result)
            temporary.replace(RESULT)
            gate_argv = [sys.executable, str(REPO / ".agent-harness/scripts/cas_gate.py"), "check-axis",
                         "--contract", str((TASK_DIR / "EXECUTION_CONTRACT.json").relative_to(REPO)),
                         "--result", str(RESULT.relative_to(REPO))]
            gate = observed(gate_argv, REPO, "check_axis")
            write_json(evidence / "check_axis.json", {
                "argv": gate_argv, "cwd": str(REPO), "exit_code": gate.returncode,
                "stdout": gate.stdout.strip(), "stderr": gate.stderr.strip(), "completed_at": utc_now(),
            })
            if gate.returncode != 0:
                diff.append("check-axis rejected result")
        write_json(evidence / "outcome.json", {
            "checks": {"PORT-CAS-02": not diff}, "domain_assumption_diff": diff,
            "counterexample": None, "completed_at": utc_now(),
        })
    except Exception as exc:
        diff.append(f"runner error: {type(exc).__name__}: {exc}")
        write_json(evidence / "failure.json", {"domain_assumption_diff": diff, "completed_at": utc_now()})

    print(json.dumps({"checks": {"PORT-CAS-02": not diff}, "domain_assumption_diff": diff, "counterexample": None}, separators=(",", ":")))
    return 0 if not diff else 1


if __name__ == "__main__":
    raise SystemExit(main())
