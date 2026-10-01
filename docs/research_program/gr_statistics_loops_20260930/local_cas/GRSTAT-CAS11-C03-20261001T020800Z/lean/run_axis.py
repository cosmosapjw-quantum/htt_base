#!/usr/bin/env python3
"""Execute the repo-pinned Lean proof for frozen CAS11-C03; emit one JSON payload."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
AXIS_DIR = Path(__file__).resolve().parent
FORMAL = ROOT / "formal_mathlib"
SOURCE = AXIS_DIR / "WeightedProjection.lean"
CONTRACT = ROOT / "docs/research_program/gr_statistics_loops_20260930/cas_corr_followup_20260930/intake/contracts/CAS11-C03-WEIGHTED-PROJECTION.json"
CONTRACT_SHA = "a97dc88082095ba636d326ea390cf629b86ca333577a27638c83c2b7f9a55794"
OBLIGATION = "CAS11-C03-WEIGHTED-PROJECTION"
THEOREMS = (
    "projection_idempotent", "projection_orthogonal", "gram_quadratic_identity",
    "gram_quadratic_norm_sq", "gram_positive_semidefinite", "weighted_cauchy_schwarz",
)
EXPECTED_AXIOMS = {"propext", "Classical.choice", "Quot.sound"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def run(label: str, argv: list[str]) -> dict:
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    try:
        proc = subprocess.run(argv, cwd=FORMAL, capture_output=True, text=True,
                              timeout=300, check=False)
        stdout, stderr, code = proc.stdout, proc.stderr, proc.returncode
        error = None
    except (OSError, subprocess.TimeoutExpired) as exc:
        stdout = exc.stdout or "" if isinstance(exc, subprocess.TimeoutExpired) else ""
        stderr = exc.stderr or "" if isinstance(exc, subprocess.TimeoutExpired) else ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", "replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", "replace")
        code = None
        error = repr(exc)
    (AXIS_DIR / f"{label}.stdout.log").write_text(stdout)
    (AXIS_DIR / f"{label}.stderr.log").write_text(stderr)
    return {"argv": argv, "cwd": str(FORMAL), "started_at": started,
            "completed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "exit_code": code, "error": error,
            "stdout_path": f"{label}.stdout.log", "stderr_path": f"{label}.stderr.log"}


def main() -> int:
    commands = []
    errors = []
    try:
        if sha256(CONTRACT) != CONTRACT_SHA:
            errors.append("frozen contract SHA mismatch")
        source_text = SOURCE.read_text()
        if re.search(r"\b(?:sorry|admit|axiom)\b", source_text):
            errors.append("forbidden proof gap or custom axiom token in source")
        version = run("version", ["lake", "env", "lean", "--version"])
        commands.append(version)
        compilation = run("compile", ["cuhg-telemetry", "run", "--project", "htt_base",
                                      "--task", "GRSTAT-CAS11-C03-20261001T020800Z-lean", "--",
                                      "lake", "env", "lean", str(SOURCE)])
        commands.append(compilation)
        output = (AXIS_DIR / "compile.stdout.log").read_text()
        stderr = (AXIS_DIR / "compile.stderr.log").read_text()
        for name in THEOREMS:
            match = re.search(r"'CAS11C03\." + name +
                              r"' depends on axioms: \[([^\]]*)\]", output + "\n" + stderr)
            if not match:
                errors.append(f"missing axiom report for {name}")
            else:
                axioms = {part.strip() for part in match.group(1).split(",")}
                if axioms != EXPECTED_AXIOMS:
                    errors.append(f"unexpected axioms for {name}: {sorted(axioms)}")
        if version["exit_code"] != 0 or "Lean (version 4.31.0" not in (AXIS_DIR / "version.stdout.log").read_text():
            errors.append("pinned Lean version unavailable or mismatched")
        if compilation["exit_code"] != 0:
            errors.append(f"Lean compilation exit: {compilation['exit_code']}")
        if "sorryAx" in output + stderr:
            errors.append("Lean axiom output contains sorryAx")
        success = not errors
    except Exception as exc:
        errors.append(f"runner error: {type(exc).__name__}: {exc}")
        success = False
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    source_sha = sha256(SOURCE) if SOURCE.exists() else None
    evidence = {
        "axis": "lean", "status": "PASS" if success else "INCONCLUSIVE",
        "contract_sha256": CONTRACT_SHA, "source_sha256": source_sha,
        "evidence_class": "exact", "completed_at": now,
        "commands": commands, "statement_alignment": "Full arbitrary finite-dimensional real positive-definite inner-product instance; any submodule and any finite index type, including zero dimension and empty index; no Gram invertibility or independent residual assumptions.",
        "proof_coverage": {name: success for name in THEOREMS},
        "domain_assumption_diff": [], "counterexample": None,
        "errors": errors, "requested_runtime": {"model": "gpt-6-sol", "effort": "high"},
        "observed_runtime": "NOT_MEASURED", "cost": "NOT_MEASURED",
        "scope": "finite deterministic weighted projection and residual Gram only; no scientific admission",
    }
    write_json(AXIS_DIR / "AXIS_RESULT.json", evidence)
    write_json(AXIS_DIR / "execution.json", {"source_sha256": source_sha, "contract_sha256": CONTRACT_SHA,
                                                "commands": commands, "errors": errors})
    print(json.dumps({"checks": {OBLIGATION: success}, "domain_assumption_diff": [],
                      "counterexample": None}, separators=(",", ":")))
    return 0 if success else 2


if __name__ == "__main__":
    sys.exit(main())
