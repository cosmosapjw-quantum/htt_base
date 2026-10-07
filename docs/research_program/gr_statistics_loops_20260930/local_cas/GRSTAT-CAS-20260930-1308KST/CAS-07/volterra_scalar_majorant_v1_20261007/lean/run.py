#!/usr/bin/env python3
"""Reproduce the frozen CAS-07 M03 Lean axis and emit one typed JSON result."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


AXIS = Path(__file__).resolve().parent
REPO = AXIS.parents[7]
LEAN_PROJECT = Path("/home/cosmosapjw/lean_oracles/viii_oracle")
MATHLIB = LEAN_PROJECT / ".lake/packages/mathlib"
CONTRACT = AXIS.parent / "EXECUTION_CONTRACT.json"
INPUTS = AXIS.parent / "ADMITTED_INPUTS.json"
COMMON = REPO / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
TOOLCHAIN = REPO / "formal_mathlib/lean-toolchain"
MANIFEST = REPO / "formal_mathlib/lake-manifest.json"
MAIN = AXIS / "Main.lean"
EXPECTED = {
    "contract": "6c840eaffac0744da3d1b2f9c7de3f8b1c45af2d949ba4831b5e90d4ec9a51ae",
    "admitted_inputs": "bbb0f93dc43ddd3ee96cdee065f8173ccac44007a6908ae66714f25e3214661d",
    "common_spec": "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
    "toolchain": "efac0b94923b2d8b6840cd35be9177ad0fc5ab2332f4f4311c98712cee92fdee",
    "lake_manifest": "bc86de9aed83fc38b0850702d6879ed6f3c97eedb7d1d69d643160731179d6ed",
    "mathlib_revision": "fabf563a7c95a166b8d7b6efca11c8b4dc9d911f",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command(argv: list[str], cwd: Path) -> dict:
    try:
        p = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=7200)
        return {"argv": argv, "cwd": str(cwd), "exit_code": p.returncode,
                "stdout": p.stdout, "stderr": p.stderr}
    except subprocess.TimeoutExpired as exc:
        return {"argv": argv, "cwd": str(cwd), "exit_code": None,
                "stdout": (exc.stdout or b"").decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or ""),
                "stderr": (exc.stderr or b"").decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or ""),
                "timeout": True}


def main() -> int:
    hashes = {
        "contract": sha256(CONTRACT),
        "admitted_inputs": sha256(INPUTS),
        "common_spec": sha256(COMMON),
        "toolchain": sha256(TOOLCHAIN),
        "lake_manifest": sha256(MANIFEST),
        "Main.lean": sha256(MAIN),
        "run.py": sha256(Path(__file__)),
    }
    mathlib_revision = command(["git", "rev-parse", "HEAD"], MATHLIB)
    lean_location = command(["lake", "env", "which", "lean"], LEAN_PROJECT)
    lean_version = command(["lake", "env", "lean", "--version"], LEAN_PROJECT)
    lake_version = command(["lake", "--version"], LEAN_PROJECT)
    lean_binary = Path(lean_location["stdout"].strip()) if lean_location["exit_code"] == 0 else None
    lake_binary = Path(shutil.which("lake") or "")
    python_binary = Path(sys.executable)
    binaries = {
        "lean": {"path": str(lean_binary) if lean_binary else None,
                 "sha256": sha256(lean_binary) if lean_binary and lean_binary.is_file() else None},
        "lake": {"path": str(lake_binary) if lake_binary.is_file() else None,
                 "sha256": sha256(lake_binary) if lake_binary.is_file() else None},
        "python": {"path": str(python_binary), "sha256": sha256(python_binary)},
    }
    lean_run = command(["lake", "env", "lean", str(MAIN)], LEAN_PROJECT)
    (AXIS / "lean_stdout.log").write_text(lean_run["stdout"])
    (AXIS / "lean_stderr.log").write_text(lean_run["stderr"])

    source = MAIN.read_text()
    forbidden = re.findall(r"\b(?:sorry|admit|axiom|unsafe|native_decide)\b", source)
    axiom_line = next((line for line in lean_run["stdout"].splitlines()
                       if line.startswith("'CAS07M03.scalar_volterra_comparison' depends on axioms:")), None)
    allowed_axioms = "[propext, Classical.choice, Quot.sound]"
    binding_ok = all(hashes[key] == EXPECTED[key] for key in
                     ("contract", "admitted_inputs", "common_spec", "toolchain", "lake_manifest"))
    revision_ok = mathlib_revision["exit_code"] == 0 and mathlib_revision["stdout"].strip() == EXPECTED["mathlib_revision"]
    theorem_ok = "theorem scalar_volterra_comparison" in source and axiom_line is not None
    axioms_ok = axiom_line is not None and axiom_line.endswith(allowed_axioms) and "sorryAx" not in lean_run["stdout"]
    check = (binding_ok and revision_ok and lean_version["exit_code"] == 0
             and all(item["sha256"] is not None for item in binaries.values())
             and lean_run["exit_code"] == 0 and theorem_ok and axioms_ok and not forbidden)
    result = {
        "schema": "htt.cas-axis-result.v1",
        "axis": "lean",
        "contract_id": "GRSTAT-20260930-CAS-07-M03-SCALAR-VOLTERRA-V1",
        "contract_sha256": hashes["contract"],
        "input_sha256": hashes["admitted_inputs"],
        "status": "PASS" if check else "BLOCKED",
        "checks": {"CAS-07-M03-SCALAR-VOLTERRA": bool(check)},
        "domain_assumption_diff": [],
        "counterexample": None,
        "theorem": "CAS07M03.scalar_volterra_comparison",
        "scope": "Universal scalar Volterra comparison only; no matrix or scientific admission",
        "global_launch_id": None,
        "observed_model": "UNKNOWN",
        "observed_effort": "UNKNOWN",
        "execution_mode": "direct_local_owner_authorized",
        "source_hashes": hashes,
        "mathlib_revision": mathlib_revision["stdout"].strip(),
        "versions": {"lean": lean_version["stdout"].strip(), "lake": lake_version["stdout"].strip(),
                     "python": sys.version.split()[0]},
        "executable_artifacts": binaries,
        "execution": {"argv": lean_run["argv"], "cwd": lean_run["cwd"],
                      "exit_code": lean_run["exit_code"], "stdout_log": str(AXIS / "lean_stdout.log"),
                      "stderr_log": str(AXIS / "lean_stderr.log")},
        "axiom_report": axiom_line,
        "forbidden_source_tokens": forbidden,
        "binding_ok": binding_ok,
        "mathlib_revision_ok": revision_ok,
        "remaining_scope": ["Matrix Jacobi ODE to scalar premise", "determinant/sign continuity",
                            "physics/observation/scientific admission"],
    }
    (AXIS / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if check else 1


if __name__ == "__main__":
    sys.exit(main())
