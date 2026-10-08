#!/usr/bin/python3.12
"""No-argument, blind Lean axis runner for frozen CAS-13-C02."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


AXIS_DIR = Path(__file__).resolve().parent
REPO = Path.cwd().resolve()
SOURCE = AXIS_DIR / "TwoNode.lean"
RESULT = AXIS_DIR / "axis_result.json"
LEAN_PROJECT = Path("/home/cosmosapjw/lean_oracles/viii_oracle")
MATHLIB = LEAN_PROJECT / ".lake/packages/mathlib"
CONTRACT = AXIS_DIR.parent / "EXECUTION_CONTRACT.json"
ADMITTED = AXIS_DIR.parent / "ADMITTED_INPUTS.json"
TEFF = REPO / "docs/research_program/gr_statistics_loops_20260930/cas/TEFF_INTERVAL_SPEC.md"
COMMON = REPO / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
TOOLCHAIN = REPO / "formal/lean-toolchain"

EXPECTED = {
    CONTRACT: "66b839cb44573842f36f73c234c4b5b6c8cca639465c58e525b86be8aea754b0",
    ADMITTED: "83bb552d9cbc733c58bd57bef88a53ac060261b343b6e9596181586104a68725",
    TEFF: "bc055d391d3231c634a14e146f228d3b8179a043485c41ce08754cdeac4fd0fe",
    COMMON: "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
}
EXPECTED_MATHLIB = "fabf563a7c95a166b8d7b6efca11c8b4dc9d911f"
EXPECTED_AXIOMS = {"propext", "Classical.choice", "Quot.sound"}
THEOREMS = [
    "secant_deriv", "secant_deriv_pos", "secant_strictMonoOn",
    "root_properties", "strict_brackets", "lower_node_existsUnique",
    "upper_node_existsUnique", "lower_weight_moments", "upper_weight_moments",
    "dirac_boundary", "chord_boundary", "left_endpoint_dirac",
    "right_endpoint_dirac", "chord_left_endpoint", "chord_right_endpoint",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def execute(argv: list[str], cwd: Path, name: str) -> dict:
    completed = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, check=False)
    out = AXIS_DIR / f"{name}.stdout.log"
    err = AXIS_DIR / f"{name}.stderr.log"
    out.write_text(completed.stdout, encoding="utf-8")
    err.write_text(completed.stderr, encoding="utf-8")
    return {
        "argv": argv,
        "cwd": str(cwd),
        "exit_code": completed.returncode,
        "stdout": {"path": str(out.relative_to(REPO)), "sha256": sha256(out)},
        "stderr": {"path": str(err.relative_to(REPO)), "sha256": sha256(err)},
    }


def file_receipt(path: Path) -> dict:
    return {"path": str(path), "sha256": sha256(path), "size_bytes": path.stat().st_size}


def main() -> int:
    if len(sys.argv) != 1:
        raise SystemExit("run.py accepts no arguments")
    commands: list[dict] = []
    findings: list[str] = []
    versions: dict[str, str] = {}
    scanned_axioms: dict[str, list[str]] = {}
    status = "INCONCLUSIVE"
    try:
        if not all(path.is_file() and sha256(path) == expected for path, expected in EXPECTED.items()):
            raise RuntimeError("FROZEN_INPUT_HASH_MISMATCH")
        if TOOLCHAIN.read_text(encoding="utf-8").strip() != "leanprover/lean4:v4.31.0":
            raise RuntimeError("LEAN_TOOLCHAIN_MISMATCH")
        if not SOURCE.is_file():
            raise RuntimeError("LEAN_SOURCE_MISSING")
        if re.search(r"\b(?:sorry|admit|axiom)\b", SOURCE.read_text(encoding="utf-8")):
            raise RuntimeError("FORBIDDEN_LEAN_ESCAPE_TOKEN")

        git = shutil.which("git")
        lake = shutil.which("lake")
        if git is None or lake is None:
            raise RuntimeError("REQUIRED_EXECUTABLE_MISSING")
        command = execute([git, "-C", str(MATHLIB), "rev-parse", "HEAD"], REPO, "mathlib_commit")
        commands.append(command)
        if command["exit_code"] != 0:
            raise RuntimeError("MATHLIB_COMMIT_UNAVAILABLE")
        versions["mathlib_commit"] = (AXIS_DIR / "mathlib_commit.stdout.log").read_text().strip()
        if versions["mathlib_commit"] != EXPECTED_MATHLIB:
            raise RuntimeError("MATHLIB_COMMIT_MISMATCH")

        command = execute([lake, "env", "lean", "--version"], LEAN_PROJECT, "lean_version")
        commands.append(command)
        if command["exit_code"] != 0:
            raise RuntimeError("LEAN_VERSION_FAILED")
        versions["lean"] = (AXIS_DIR / "lean_version.stdout.log").read_text().strip()
        if "Lean (version 4.31.0," not in versions["lean"]:
            raise RuntimeError("LEAN_VERSION_MISMATCH")
        versions["python"] = sys.version.splitlines()[0]

        command = execute([lake, "env", "lean", str(SOURCE)], LEAN_PROJECT, "lean_compile")
        commands.append(command)
        if command["exit_code"] != 0:
            raise RuntimeError("LEAN_COMPILATION_FAILED")
        output = (AXIS_DIR / "lean_compile.stdout.log").read_text(encoding="utf-8")
        pattern = re.compile(r"^'CAS13C02\.([^']+)' depends on axioms: \[([^]]*)\]$", re.MULTILINE)
        scanned_axioms = {
            theorem: [part.strip() for part in listed.split(",")]
            for theorem, listed in pattern.findall(output)
        }
        if set(scanned_axioms) != set(THEOREMS):
            raise RuntimeError("AXIOM_REPORT_INCOMPLETE")
        if any(set(axioms) != EXPECTED_AXIOMS for axioms in scanned_axioms.values()):
            raise RuntimeError("UNEXPECTED_AXIOM_DEPENDENCY")
        status = "PASS"
    except Exception as exc:
        findings.append(f"{type(exc).__name__}: {exc}")

    evidence = {
        "axis": "lean",
        "status": status,
        "contract_sha256": EXPECTED[CONTRACT],
        "input_sha256": EXPECTED[ADMITTED],
        "evidence_class": "exact",
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "checks": {"CAS-13-C02": status == "PASS"},
        "domain_assumption_diff": [],
        "counterexample": None,
        "commands": commands,
        "tool_versions": versions,
        "axiom_scan": scanned_axioms,
        "input_artifacts": [file_receipt(p) for p in EXPECTED if p.is_file()],
        "source_artifacts": [file_receipt(p) for p in [SOURCE, Path(__file__).resolve()] if p.is_file()],
        "executable_artifacts": [
            file_receipt(Path(p).resolve()) for p in [shutil.which("lake"), shutil.which("lean")]
            if p is not None and Path(p).resolve().is_file()
        ],
        "toolchain_artifact": file_receipt(TOOLCHAIN) if TOOLCHAIN.is_file() else None,
        "mathlib_commit": versions.get("mathlib_commit"),
        "launch_id": None,
        "lifecycle_status": "BLOCKED_UNOBSERVED_GLOBAL_LAUNCH",
        "claim_ceiling": "CAS-13-C02 two-node existence/uniqueness/feasibility only",
        "full_scientific_admission": "HOLD",
        "findings": findings,
    }
    RESULT.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"checks": evidence["checks"], "domain_assumption_diff": [], "counterexample": None},
                     separators=(",", ":")))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
