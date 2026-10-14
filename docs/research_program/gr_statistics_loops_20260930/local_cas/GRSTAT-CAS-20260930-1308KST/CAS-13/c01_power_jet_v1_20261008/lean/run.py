#!/usr/bin/python3.12
"""CAS-13-C01 Lean axis: compile the pinned positive-power jet proof."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
PACKAGE = HERE.parent
ORACLE = Path("/home/cosmosapjw/lean_oracles/viii_oracle")
SOURCE = HERE / "PowerJet.lean"
CONTRACT = PACKAGE / "EXECUTION_CONTRACT.json"
INPUT = PACKAGE / "ADMITTED_INPUTS.json"
TEFF = REPO / "docs/research_program/gr_statistics_loops_20260930/cas/TEFF_INTERVAL_SPEC.md"
COMMON = REPO / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
EXPECTED = {
    CONTRACT: "a603f1f31004a278095ea6ec4523aff77789bd3c5cf58fa74ee51033b566c638",
    INPUT: "6e29ae54d7e065d784ddf673958b8c9b56a1ebe5532e5a4d8d05aca6f588fa3a",
    TEFF: "bc055d391d3231c634a14e146f228d3b8179a043485c41ce08754cdeac4fd0fe",
    COMMON: "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
}
EXPECTED_TOOLCHAIN = "leanprover/lean4:v4.31.0"
EXPECTED_MATHLIB = "fabf563a7c95a166b8d7b6efca11c8b4dc9d911f"
PROOF_NAMES = (
    "Cas13C01.psi_positive_branch",
    "Cas13C01.deriv3_psi",
    "Cas13C01.deriv3_q",
    "Cas13C01.jets_at_one",
    "Cas13C01.third_mismatch",
    "Cas13C01.unit_mismatch",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(argv: list[str], cwd: Path, timeout: int = 60) -> dict:
    try:
        cp = subprocess.run(argv, cwd=cwd, text=True, capture_output=True, timeout=timeout, check=False)
        return {"argv": argv, "cwd": str(cwd), "exit_code": cp.returncode,
                "stdout": cp.stdout, "stderr": cp.stderr}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"argv": argv, "cwd": str(cwd), "exit_code": None,
                "stdout": "", "stderr": repr(exc)}


def main() -> int:
    if len(sys.argv) != 1:
        raise SystemExit("run.py takes no arguments")
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    commands: list[dict] = []
    observed_hashes: dict[str, str | None] = {}
    for path in EXPECTED:
        observed_hashes[str(path)] = sha256(path) if path.is_file() else None
    bindings_ok = all(observed_hashes[str(p)] == expected for p, expected in EXPECTED.items())

    toolchain = ORACLE / "lean-toolchain"
    toolchain_text = toolchain.read_text().strip() if toolchain.is_file() else None
    mathlib_rev = run(["git", "-C", str(ORACLE / ".lake/packages/mathlib"), "rev-parse", "HEAD"], ORACLE)
    commands.append({k: v for k, v in mathlib_rev.items() if k != "stdout" and k != "stderr"})
    mathlib_head = mathlib_rev["stdout"].strip() if mathlib_rev["exit_code"] == 0 else None
    version = run(["lake", "env", "lean", "--version"], ORACLE)
    commands.append({k: v for k, v in version.items() if k != "stdout" and k != "stderr"})
    lean_version = version["stdout"].strip() if version["exit_code"] == 0 else None
    lean_location = run(["lake", "env", "which", "lean"], ORACLE)
    commands.append({k: v for k, v in lean_location.items() if k != "stdout" and k != "stderr"})
    lean_path = Path(lean_location["stdout"].strip()) if lean_location["exit_code"] == 0 else None
    lake_name = shutil.which("lake")
    lake_path = Path(lake_name) if lake_name else None
    toolchain_ok = (toolchain_text == EXPECTED_TOOLCHAIN and mathlib_head == EXPECTED_MATHLIB
                    and lean_version is not None and "version 4.31.0" in lean_version
                    and lean_path is not None and lean_path.is_file())

    compile_result = None
    if bindings_ok and toolchain_ok and SOURCE.is_file():
        compile_result = run(["lake", "env", "lean", str(SOURCE)], ORACLE, timeout=3500)
        commands.append({k: v for k, v in compile_result.items() if k != "stdout" and k != "stderr"})
        (HERE / "lean.stdout.log").write_text(compile_result["stdout"])
        (HERE / "lean.stderr.log").write_text(compile_result["stderr"])

    stdout = compile_result["stdout"] if compile_result is not None else ""
    proof_axioms = {name: next((line for line in stdout.splitlines()
                               if line.startswith(f"'{name}' depends on axioms:")), None)
                    for name in PROOF_NAMES}
    proof_ok = (compile_result is not None and compile_result["exit_code"] == 0
                and all(line is not None and "sorryAx" not in line for line in proof_axioms.values()))
    status = "PASS" if bindings_ok and toolchain_ok and proof_ok else "INCONCLUSIVE"
    artifacts = {str(path): sha256(path) for path in
                 (SOURCE, Path(__file__).resolve(), HERE / "lean.stdout.log", HERE / "lean.stderr.log")
                 if path.is_file()}
    executables = {str(path): sha256(path) for path in (lake_path, lean_path)
                   if path is not None and path.is_file()}
    result = {
        "axis": "lean",
        "status": status,
        "contract_sha256": EXPECTED[CONTRACT],
        "evidence_class": "exact",
        "completed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "started_at": started,
        "commands": commands,
        "versions": {"python": sys.version.split()[0], "lean": lean_version,
                     "toolchain": toolchain_text, "mathlib_commit": mathlib_head},
        "artifacts_sha256": artifacts,
        "executables_sha256": executables,
        "source_binding_sha256": observed_hashes,
        "assumptions_domains_branches": {
            "p": "real > 4", "y": "real > 0", "power": "Real.rpow = exp(log y * p) on y > 0",
            "units": "dimensionless", "scope": "pointwise CAS-13-C01 only",
        },
        "proof_axioms": proof_axioms,
        "checks": {"CAS-13-C01": status == "PASS"},
        "domain_assumption_diff": [],
        "counterexample": None,
        "limitation": "Finite positive-power jet only; no Taylor integration, general bandpass, or scientific admission.",
    }
    (HERE / "axis_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    if status == "PASS":
        print(json.dumps({"checks": {"CAS-13-C01": True},
                          "domain_assumption_diff": [], "counterexample": None}, sort_keys=True))
        return 0
    print(json.dumps({"domain_assumption_diff": [], "counterexample": None,
                      "inconclusive": {"bindings_ok": bindings_ok, "toolchain_ok": toolchain_ok,
                                       "proof_ok": proof_ok}}, sort_keys=True))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
