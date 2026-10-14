#!/usr/bin/env python3
"""Compile the independent CAS-02-C04 Lean certificate and emit one axis JSON."""

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess


HERE = Path(__file__).resolve().parent
REPO = Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
ORACLE = Path("/home/cosmosapjw/lean_oracles/viii_oracle")
CONTRACT = HERE.parent / "EXECUTION_CONTRACT.json"
ADMITTED = HERE.parent / "ADMITTED_INPUTS.json"
COMMON = REPO / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
LEAN = HERE / "InverseBound.lean"
RESULT = HERE / "axis_result.json"
EXPECTED = {
    ADMITTED: "4a48c60d726b977ff4a0129b6218aa065038c72b10241f2e4fcf0f0d31a106de",
    COMMON: "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
    ORACLE / "lean-toolchain": "efac0b94923b2d8b6840cd35be9177ad0fc5ab2332f4f4311c98712cee92fdee",
    ORACLE / "lake-manifest.json": "1a7cbb6b0487b078e2e5f768fc9e1bd78e2e36d0d896477cadf1d8971464db08",
}
EXPECTED_AXIOMS = (
    "'CAS02C04.CAS_02_C04' depends on axioms: "
    "[propext, Classical.choice, Quot.sound]"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_command(argv: list[str], stem: str) -> dict:
    env = os.environ.copy()
    env["ELAN_TOOLCHAIN"] = "leanprover/lean4:v4.31.0"
    completed = subprocess.run(argv, cwd=ORACLE, env=env, capture_output=True, text=True,
                               check=False, timeout=300)
    stdout = HERE / f"{stem}.stdout.log"
    stderr = HERE / f"{stem}.stderr.log"
    stdout.write_text(completed.stdout)
    stderr.write_text(completed.stderr)
    return {
        "argv": argv,
        "cwd": str(ORACLE),
        "exit_code": completed.returncode,
        "stdout_path": str(stdout.relative_to(REPO)),
        "stdout_sha256": sha256(stdout),
        "stderr_path": str(stderr.relative_to(REPO)),
        "stderr_sha256": sha256(stderr),
    }


def main() -> int:
    bindings = {str(p): {"actual": sha256(p), "expected": want} for p, want in EXPECTED.items()}
    bindings_ok = all(v["actual"] == v["expected"] for v in bindings.values())
    manifest = json.loads((ORACLE / "lake-manifest.json").read_text())
    mathlib_rev = next(p["rev"] for p in manifest["packages"] if p["name"] == "mathlib")
    source = LEAN.read_text()
    forbidden = re.findall(r"\b(?:sorry|admit|axiom)\b", source)
    lean_path_cmd = run_command(["elan", "which", "lean"], "lean_path")
    lake_path_cmd = run_command(["elan", "which", "lake"], "lake_path")
    version = run_command(["lean", "--version"], "version")
    compile_cmd = run_command(["lake", "env", "lean", str(LEAN)], "compile")
    compile_stdout = (HERE / "compile.stdout.log").read_text()
    axioms_ok = EXPECTED_AXIOMS in compile_stdout
    version_ok = "Lean (version 4.31.0," in (HERE / "version.stdout.log").read_text()
    toolchain_ok = bindings_ok and mathlib_rev == "fabf563a7c95a166b8d7b6efca11c8b4dc9d911f"
    executable_paths = {
        "lean": Path((HERE / "lean_path.stdout.log").read_text().strip()),
        "lake": Path((HERE / "lake_path.stdout.log").read_text().strip()),
    }
    executable_artifacts = {
        name: {"path": str(path), "sha256": sha256(path) if path.is_file() else None}
        for name, path in executable_paths.items()
    }
    executables_ok = (lean_path_cmd["exit_code"] == 0 and lake_path_cmd["exit_code"] == 0
                      and all(v["sha256"] for v in executable_artifacts.values()))
    proof_ok = (compile_cmd["exit_code"] == 0 and version["exit_code"] == 0 and
                executables_ok and
                axioms_ok and version_ok and toolchain_ok and not forbidden)
    result = {
        "axis": "lean",
        "status": "PASS" if proof_ok else "BLOCKED",
        "contract_sha256": sha256(CONTRACT),
        "contract_id": "GRSTAT-20260930-CAS-02-C04-INVERSE-BOUND-V1",
        "evidence_class": "exact",
        "completed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "checks": {"CAS-02-C04": "PASS" if proof_ok else "BLOCKED"},
        "statement_alignment": {
            "domain": "real symmetric COMMON_SPEC S embedding admitted; Lean proves the stronger all-real-4x4 statement",
            "observer_frame": "one fixed orthonormal frame; g=diag(-1,1,1,1)",
            "norms": "positive Euclidean 4-vector, Frobenius matrix, L2 spectral matrix norms",
            "branches": "positive square roots for u0 and M; both min spectral anchor branches",
            "rapidity": "R>=0 derived from admitted ||d||<=sinh R; d=0 included",
            "domain_assumption_diff": [],
            "target": "||B2-B1||F <= (1+2 M^2) epsilonH + 4 M L epsilonZ",
        },
        "proof_coverage": [
            "metric_frobenius_norm", "future_norm_sq", "future_norm_le_cap",
            "quad_frobenius_bound", "quad_spectral_bound", "quad_fixed_lipschitz",
            "quad_pair_bound", "inverse_pair_bound", "CAS_02_C04",
            "rapidity_zero_forces_d_zero", "epsilonH_zero_forces_S_equal",
            "epsilonZ_zero_forces_u_equal",
        ],
        "axioms_line": EXPECTED_AXIOMS if axioms_ok else None,
        "forbidden_tokens": forbidden,
        "tool_versions": {
            "lean": (HERE / "version.stdout.log").read_text().strip(),
            "mathlib_rev": mathlib_rev,
            "lake_manifest_sha256": sha256(ORACLE / "lake-manifest.json"),
        },
        "executable_artifacts": executable_artifacts,
        "input_bindings": bindings,
        "artifacts": {
            "lean_path": str(LEAN.relative_to(REPO)),
            "lean_sha256": sha256(LEAN),
            "runner_path": str(Path(__file__).resolve().relative_to(REPO)),
            "runner_sha256": sha256(Path(__file__).resolve()),
        },
        "commands": [lean_path_cmd, lake_path_cmd, version, compile_cmd],
        "global_registration": {
            "requirement": "REQUIRED",
            "launch_id": None,
            "profile": None,
            "observed_model": "UNKNOWN",
            "observed_effort": "UNKNOWN",
            "status": "NOT_MET",
            "lifecycle": "BLOCKED",
        },
        "frozen_context_binding": "UNKNOWN",
        "runner_observed_four_axis_status": "NOT_EVALUATED",
        "scientific_admission": "HOLD",
    }
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": {"CAS-02-C04": proof_ok},
                      "domain_assumption_diff": [], "counterexample": None},
                     sort_keys=True, separators=(",", ":")))
    return 0 if proof_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
