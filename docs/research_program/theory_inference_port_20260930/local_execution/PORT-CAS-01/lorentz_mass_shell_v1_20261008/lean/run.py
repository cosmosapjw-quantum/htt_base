#!/usr/bin/env python3
"""Run the frozen PORT-CAS-01 Lean axis; stdout is one minimal gate JSON line."""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
TASK = ROOT.parent
REPO = ROOT.parents[6]
ORACLE = Path("/home/cosmosapjw/lean_oracles/viii_oracle")
SOURCE = ROOT / "PortCas01.lean"
CONTRACT = TASK / "EXECUTION_CONTRACT.json"
ADMITTED = TASK / "ADMITTED_INPUTS.json"
EXPECTED = {
    CONTRACT: "1085005167c4bfeeb2ec6c7199f94c73d2b0651b381bcce00fdc05275f090169",
    ADMITTED: "e6c66e6a944ee4f67c591d54281f5c3577d32852f66084767a5a6fec215d2992",
}
EXPECTED_AXIOMS = [
    "'PortCas01.metric_identity' depends on axioms: [propext, Classical.choice, Quot.sound]",
    "'PortCas01.inverse_identity' depends on axioms: [propext, Classical.choice, Quot.sound]",
    "'PortCas01.future_mass_shell' depends on axioms: [propext, Classical.choice, Quot.sound]",
    "'PortCas01.future_converse' depends on axioms: [propext, Classical.choice, Quot.sound]",
    "'PortCas01.zero_boost' depends on axioms: [propext, Classical.choice, Quot.sound]",
    "'PortCas01.zero_fourVelocity' depends on axioms: [propext, Classical.choice, Quot.sound]",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(argv: list[str], name: str) -> dict:
    completed = subprocess.run(argv, cwd=ORACLE, capture_output=True, text=True, check=False)
    out = ROOT / f"{name}.stdout"
    err = ROOT / f"{name}.stderr"
    out.write_text(completed.stdout)
    err.write_text(completed.stderr)
    return {
        "argv": argv,
        "cwd": str(ORACLE),
        "exit_code": completed.returncode,
        "stdout": str(out.relative_to(REPO)),
        "stderr": str(err.relative_to(REPO)),
        "stdout_sha256": sha(out),
        "stderr_sha256": sha(err),
    }


def main() -> None:
    commands = []
    status = "INCONCLUSIVE"
    errors = []
    try:
        for path, digest in EXPECTED.items():
            if sha(path) != digest:
                errors.append(f"frozen input hash mismatch: {path.name}")
        toolchain = (ORACLE / "lean-toolchain").read_text().strip()
        if toolchain != "leanprover/lean4:v4.31.0":
            errors.append("Lean toolchain pin mismatch")
        mathlib = subprocess.run(
            ["git", "-C", str(ORACLE / ".lake/packages/mathlib"), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=False,
        )
        if mathlib.returncode != 0 or mathlib.stdout.strip() != "fabf563a7c95a166b8d7b6efca11c8b4dc9d911f":
            errors.append("mathlib pin mismatch")
        if not errors:
            commands.append(run(["lake", "env", "lean", "--version"], "version"))
            commands.append(run(["lake", "env", "lean", "-j1", str(SOURCE)], "compile"))
            compile_out = (ROOT / "compile.stdout").read_text()
            if commands[-1]["exit_code"] == 0 and commands[0]["exit_code"] == 0 \
                    and compile_out.splitlines() == EXPECTED_AXIOMS:
                status = "PASS"
            else:
                errors.append("Lean compilation or exact axiom report failed")
    except Exception as exc:
        errors.append(f"runner exception: {type(exc).__name__}: {exc}")
    result = {
        "schema_version": 1,
        "axis": "lean",
        "status": status,
        "evidence_class": "exact",
        "contract_sha256": EXPECTED[CONTRACT],
        "admitted_inputs_sha256": EXPECTED[ADMITTED],
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "commands": commands,
        "tool_versions": {
            "lean": (ROOT / "version.stdout").read_text().strip() if (ROOT / "version.stdout").exists() else "UNKNOWN",
            "lean_toolchain": (ORACLE / "lean-toolchain").read_text().strip() if (ORACLE / "lean-toolchain").exists() else "UNKNOWN",
            "mathlib_commit": mathlib.stdout.strip() if "mathlib" in locals() and mathlib.returncode == 0 else "UNKNOWN",
        },
        "artifacts": {
            "source": str(SOURCE.relative_to(REPO)),
            "source_sha256": sha(SOURCE),
            "runner": str(Path(__file__).resolve().relative_to(REPO)),
            "runner_sha256": sha(Path(__file__)),
        },
        "statement_alignment": {
            "domain": "real beta components with s < 1",
            "branch": "nonnegative real sqrt; positive gamma; converse t >= 1",
            "metric": "diag(-1,1,1,1)",
            "units": "dimensionless u=U/c",
            "proved": [
                "entrywise boost transpose eta boost equals eta",
                "entrywise boost beta times boost negative beta equals identity",
                "future four-velocity components and mass shell",
                "future mass-shell converse and exact beta=zeta/t",
                "zero-beta boundary control",
            ],
        },
        "launch_id": None,
        "global_registered_launch": False,
        "observed_model": "UNKNOWN",
        "observed_effort": "UNKNOWN",
        "lifecycle_status": "BLOCKED_NO_GLOBAL_LAUNCH",
        "scientific_admission": "HOLD",
        "claim_ceiling": "PORT-CAS-01 finite exact algebra only",
        "errors": errors,
    }
    (ROOT / "axis_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "checks": {"PORT-CAS-01": status == "PASS"},
        "domain_assumption_diff": [],
        "counterexample": None,
    }, separators=(",", ":")))


if __name__ == "__main__":
    main()
