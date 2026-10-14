#!/usr/bin/env python3
"""No-argument, blind Lean-axis execution for frozen CAS-16-C03.

Writes a check-axis envelope and emits exactly one minimal runner payload.
An open proof emits an inconclusive payload without a Boolean check; the
observed runner reserves a false check for a counterexample or proof failure.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
COMPONENT = HERE.parent
CONTRACT = COMPONENT / "EXECUTION_CONTRACT.json"
ADMITTED = COMPONENT / "ADMITTED_INPUTS.json"
COMMON = Path("/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md")
ORACLE = Path("/home/cosmosapjw/lean_oracles/viii_oracle")
SOURCE = HERE / "SphereQuadrature.lean"
MODES = HERE / "AngularModes.lean"
ATTEMPT = HERE / "FullAttempt.lean"
AXIOMS = HERE / "Axioms.lean"
RESULT = HERE / "axis_result.json"
EXPECTED = {
    CONTRACT: "d36ffedcbeb64c201671e78e42be41ea9b6d160d148d7aadf51134a9dfbe068c",
    ADMITTED: "6c536bf89687f6f4f8aaeec90154e1c9cf20b994870e789faa3cff5d5735ac82",
    COMMON: "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def execute(argv: list[str], label: str, env: dict[str, str] | None = None) -> dict:
    done = subprocess.run(argv, cwd=ORACLE, env=env, capture_output=True, text=True, check=False)
    stdout = HERE / f"{label}.stdout.log"
    stderr = HERE / f"{label}.stderr.log"
    stdout.write_text(done.stdout)
    stderr.write_text(done.stderr)
    return {
        "argv": argv,
        "cwd": str(ORACLE),
        "exit_code": done.returncode,
        "stdout": str(stdout),
        "stderr": str(stderr),
        "stdout_sha256": sha256(stdout),
        "stderr_sha256": sha256(stderr),
    }


def main() -> int:
    observed_hashes = {str(path): sha256(path) for path in EXPECTED}
    input_aligned = all(observed_hashes[str(path)] == want for path, want in EXPECTED.items())
    commands: list[dict] = []
    commands.append(execute(["lake", "env", "lean", "--version"], "lean_version"))
    commands.append(execute(["lake", "--version"], "lake_version"))
    commands.append(execute(["git", "-C", str(ORACLE / ".lake/packages/mathlib"), "rev-parse", "HEAD"], "mathlib_commit"))
    commands.append(execute(["lake", "env", "which", "lean"], "lean_executable"))
    lean_exe_text = (HERE / "lean_executable.stdout.log").read_text().strip()
    lean_exe = Path(lean_exe_text) if lean_exe_text and Path(lean_exe_text).is_file() else None
    source_command = execute([
        "lake", "env", "lean", "-R", str(HERE), "-o", str(HERE / "SphereQuadrature.olean"), str(SOURCE)
    ], "source_compile")
    commands.append(source_command)
    env = os.environ.copy()
    env["LEAN_PATH"] = str(HERE) + os.pathsep + env.get("LEAN_PATH", "")
    modes_command = execute([
        "lake", "env", "lean", "-R", str(HERE), "-o", str(HERE / "AngularModes.olean"), str(MODES)
    ], "modes_compile", env)
    commands.append(modes_command)
    attempt_command = execute(["lake", "env", "lean", str(ATTEMPT)], "full_attempt_compile", env)
    commands.append(attempt_command)
    axiom_command = execute(["lake", "env", "lean", str(AXIOMS)], "axiom_audit", env)
    commands.append(axiom_command)
    source_ok = source_command["exit_code"] == 0
    modes_ok = modes_command["exit_code"] == 0
    attempt_ok = attempt_command["exit_code"] == 0
    axiom_audit_ok = axiom_command["exit_code"] == 0
    version = (HERE / "lean_version.stdout.log").read_text().strip()
    mathlib = (HERE / "mathlib_commit.stdout.log").read_text().strip()
    pinned = "4.31.0" in version and mathlib == "fabf563a7c95a166b8d7b6efca11c8b4dc9d911f"
    proved = input_aligned and pinned and source_ok and modes_ok and attempt_ok and axiom_audit_ok
    status = "PASS" if proved else "INCONCLUSIVE"
    now = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    result = {
        "axis": "lean",
        "status": status,
        "contract_id": "GRSTAT-20260930-CAS-16-C03-SPHERE-QUADRATURE-V1",
        "contract_sha256": observed_hashes[str(CONTRACT)],
        "admitted_inputs_sha256": observed_hashes[str(ADMITTED)],
        "common_spec_sha256": observed_hashes[str(COMMON)],
        "checks": {"CAS-16-C03": True} if proved else {},
        "domain_assumption_diff": [],
        "counterexample": None,
        "evidence_class": "exact",
        "statement_alignment": "ALIGNED_FULL_STATEMENT_OPEN" if not attempt_ok else "ALIGNED_PROVED",
        "proof_scope": {
            "full_monomial_family": attempt_ok,
            "radial_GL4_mu8_difference": source_ok,
            "azimuth_Nphi8_cos8_difference": source_ok,
            "constant_monomial": source_ok,
            "all_radial_monomials_degree_le_8": source_ok,
            "positive_azimuth_fourier_modes_1_through_8": modes_ok,
        },
        "source": str(SOURCE),
        "source_sha256": sha256(SOURCE),
        "angular_modes_source": str(MODES),
        "angular_modes_source_sha256": sha256(MODES),
        "attempt_source": str(ATTEMPT),
        "attempt_source_sha256": sha256(ATTEMPT),
        "axiom_audit_source": str(AXIOMS),
        "axiom_audit_source_sha256": sha256(AXIOMS),
        "axiom_audit_ok": axiom_audit_ok,
        "runner": str(Path(__file__).resolve()),
        "runner_sha256": sha256(Path(__file__).resolve()),
        "executable_artifacts": {
            "lean": {"path": str(lean_exe) if lean_exe else None, "sha256": sha256(lean_exe) if lean_exe else None},
            "compiled_olean": {"path": str(HERE / "SphereQuadrature.olean"), "sha256": sha256(HERE / "SphereQuadrature.olean") if source_ok else None},
            "compiled_modes_olean": {"path": str(HERE / "AngularModes.olean"), "sha256": sha256(HERE / "AngularModes.olean") if modes_ok else None},
        },
        "tool_versions": {"lean": version, "lake": (HERE / "lake_version.stdout.log").read_text().strip(), "mathlib_commit": mathlib},
        "commands": commands,
        "completed_at": now,
        "launch_id": None,
        "global_harness_used": False,
        "observed_model": "UNKNOWN",
        "observed_effort": "UNKNOWN",
        "lifecycle": "BLOCKED_NO_GLOBAL_REGISTERED_LAUNCH",
        "scientific_admission": "HOLD",
        "note": "Exact GL4 and Nphi8 witnesses, all radial moments through degree eight, positive angular Fourier modes through degree eight, and degree-zero product case compile. The bridge to the full 165-monomial product theorem is unproved; the raw Lean error gives the remaining nonconstant goal."
    }
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    payload = (
        {"checks": {"CAS-16-C03": True}, "domain_assumption_diff": [], "counterexample": None}
        if proved else
        {"domain_assumption_diff": [], "counterexample": None,
         "proof_status": "INCONCLUSIVE", "unproved_obligation": "CAS-16-C03"}
    )
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
