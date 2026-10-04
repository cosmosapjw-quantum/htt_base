#!/usr/bin/env python3
"""Standalone pinned Lean execution for the adopted CAS-06 successor.

An exit-zero compiler result certifies only the theorem names printed by Proof.lean.
The four contracted components remain INCONCLUSIVE until their complete, aligned
proofs exist; this script never infers an axis PASS from partial compilation.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import signal
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[9]
BASE = Path(__file__).resolve().parent
SUCCESSOR = BASE.parent
SCALAR = SUCCESSOR.parent / "lean" / "Proof.lean"
PROOF = BASE / "Proof.lean"
CONTRACT = SUCCESSOR / "EXECUTION_CONTRACT.json"
ADMITTED = SUCCESSOR / "ADMITTED_INPUTS.json"
COMMON = ROOT / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
TOOLCHAIN = ROOT / "formal/lean-toolchain"
MATHLIB_TOOLCHAIN = ROOT / "formal_mathlib/lean-toolchain"
MANIFEST = ROOT / "formal_mathlib/lake-manifest.json"
MATHLIB = ROOT / "formal_mathlib"
EXPECTED = {
    CONTRACT: "9936c95ac128126d34688bbd8ece9fb90c92aa7dfeea8fa7b41716ab449e88f3",
    ADMITTED: "711de321c374a85b4b0414d5df1f8a62b55368f73c2a3d31e502e209af8793eb",
    COMMON: "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
    SCALAR: "83352ea65bb391d2bd17bf4e25e6149dc5f1cff14f75c28de1a7f30b1d12f46e",
    TOOLCHAIN: "efac0b94923b2d8b6840cd35be9177ad0fc5ab2332f4f4311c98712cee92fdee",
    MATHLIB_TOOLCHAIN: "efac0b94923b2d8b6840cd35be9177ad0fc5ab2332f4f4311c98712cee92fdee",
    MANIFEST: "bc86de9aed83fc38b0850702d6879ed6f3c97eedb7d1d69d643160731179d6ed",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identity() -> dict[str, str]:
    return {str(path.relative_to(ROOT)): sha(path) for path in (*EXPECTED, PROOF, BASE / "run.py")}


def call(name: str, argv: list[str], cwd: Path, out: Path, timeout: int) -> dict:
    env = dict(os.environ, ELAN_TOOLCHAIN="leanprover/lean4:v4.31.0")
    p = subprocess.Popen(argv, cwd=cwd, env=env, text=True,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         start_new_session=True)
    try:
        stdout, stderr = p.communicate(timeout=timeout)
        status = p.returncode
        timed_out = False
    except subprocess.TimeoutExpired:
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        stdout, stderr = p.communicate()
        status = None
        timed_out = True
    (out / f"{name}.stdout.log").write_text(stdout)
    (out / f"{name}.stderr.log").write_text(stderr)
    return {"name": name, "argv": argv, "cwd": str(cwd), "exit_code": status,
            "timed_out": timed_out, "stdout_log": str((out / f"{name}.stdout.log").relative_to(ROOT)),
            "stderr_log": str((out / f"{name}.stderr.log").relative_to(ROOT))}


def main() -> int:
    if Path.cwd().resolve() != ROOT:
        raise SystemExit("frozen runner requires repository-root cwd")
    started = dt.datetime.now(dt.timezone.utc)
    out = BASE / "attempts" / started.strftime("%Y%m%dT%H%M%S%fZ")
    out.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(PROOF, out / "Proof.lean")
    shutil.copyfile(BASE / "run.py", out / "run.py")
    before = identity()
    mismatches = {str(path.relative_to(ROOT)): [sha(path), wanted]
                  for path, wanted in EXPECTED.items() if sha(path) != wanted}
    commands = []
    if not mismatches:
        commands.append(call("lean_version", ["lean", "--version"], MATHLIB, out, 30))
        commands.append(call("lake_version", ["lake", "--version"], MATHLIB, out, 30))
        commands.append(call("accepted_scalar", ["lake", "env", "lean", "-j1", str(SCALAR)],
                             MATHLIB, out, 1500))
        commands.append(call("adopted_proof", ["lake", "env", "lean", "-j1", str(PROOF)],
                             MATHLIB, out, 1500))
    after = identity()
    drift = {p: [v, after.get(p)] for p, v in before.items() if after.get(p) != v}
    result = {
        "axis": "lean", "status": "INCONCLUSIVE", "evidence_class": "exact",
        "contract_sha256": EXPECTED[CONTRACT],
        "started_at": started.isoformat(),
        "completed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "attempt_dir": str(out.relative_to(ROOT)),
        "commands": commands,
        "source_input_toolchain_sha256_before": before,
        "source_input_toolchain_sha256_after": after,
        "expected_identity_mismatches": mismatches,
        "during_run_hash_drift": drift,
        "toolchain": {"lean": "4.31.0", "mathlib_rev": "fabf563a7c95a166b8d7b6efca11c8b4dc9d911f"},
        "component_status": {
            "CAS-06-C01": "PARTIAL_GENERIC_ACTUAL_CONNECTION_DERIVATIVE_RIEMANN_MIXED_ZERO_RICCI_AND_EINSTEIN_COMPONENTS_WITH_TOV_TANGENTIAL_JET_ALGEBRA; EXPLICIT_DERIV_NU_DERIV_F_METRIC_INSTANTIATION_AND_FULL_TOV_CLOSURE_UNPROVED",
            "CAS-06-C02": "PARTIAL_STATIC_VELOCITY_ACCELERATION_VECTOR_AND_METRIC_NORM; FULL_WEYL_COVARIANT_DERIVATIVE_AND_OTHER_RATES_UNPROVED",
            "CAS-06-C03": "UNPROVED_ACTION_VARIATION_STRESS_CURRENT_AND_MATCHED_JETS",
            "CAS-06-C04": "PROVED_FIXED_FAMILY_STATIC_ACCELERATION_METRIC_NORM_AND_ONE_SIDED_LIMIT; FULL_C02_DEPENDENCY_UNPROVED",
        },
        "first_full_contract_gap": "C01 has a generic actual-connection Riemann/Ricci/Einstein contraction and tangential TOV algebra, but the generic νr/Fr functions are not yet instantiated as deriv ν/deriv F with a proved full metric-partial array; the TOV quotient derivative is proved separately and a final all-component metric theorem remains open.",
        "additional_gaps": ["C02 full covariant Weyl derivative before event specialization and remaining kinematic rates",
                            "C03 metric and scalar action variations plus matched source jets",
                            "C04 analytic existence/distinct-germ interpretation remains separately HOLD"],
        "domain_assumption_diff": [],
        "statement_alignment": "Partial exact sublemmas only; no full C01-C04 statement is declared.",
        "scientific_admission": "HOLD",
        "prior_exploratory_compile_log_status": "Tool-call transcript only; early source bytes and raw logs unavailable for exact replay.",
    }
    (out / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    (BASE / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "result": str(BASE / "result.json"),
                      "attempt": str(out), "commands": commands}, indent=2))
    if mismatches or drift or any(c["exit_code"] != 0 or c["timed_out"] for c in commands):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
