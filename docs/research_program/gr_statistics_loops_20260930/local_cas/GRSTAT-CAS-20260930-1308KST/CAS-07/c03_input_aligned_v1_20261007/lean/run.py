#!/usr/bin/env python3
"""Run the blind CAS-07 C03 Lean axis and emit exactly one JSON document."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
AXIS = Path(__file__).resolve().parent
INPUT = AXIS.parent
ORACLE = Path("/home/cosmosapjw/lean_oracles/viii_oracle")
CONTRACT = INPUT / "EXECUTION_CONTRACT.json"
ADMITTED = INPUT / "ADMITTED_INPUTS.json"
COMMON = ROOT / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
SOURCE = AXIS / "Main.lean"
RESULT = AXIS / "RESULT.json"
EXPECTED_CONTRACT_SHA256 = "a65d1f9c9c64a149f554855be39400755cb2aee394440d813877a6fcd6e25b6d"
EXPECTED_ADMITTED_SHA256 = "8e87c30466c362dc85071c64fd722933fa5e170d8128f81de29d859a045aa827"
EXPECTED_COMMON_SHA256 = "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897"
EXPECTED_MATHLIB_REV = "fabf563a7c95a166b8d7b6efca11c8b4dc9d911f"
CHECK_NAMES = ("CAS-07-C03-FD1", "CAS-07-C03-FD2", "CAS-07-C03-FD3")
ALLOWED_AXIOMS = {"propext", "Classical.choice", "Quot.sound"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def execute(argv: list[str], cwd: Path, timeout: int = 60) -> dict:
    try:
        completed = subprocess.run(
            argv, cwd=cwd, text=True, capture_output=True, check=False, timeout=timeout
        )
        return {
            "argv": argv,
            "cwd": str(cwd),
            "exit_code": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "argv": argv,
            "cwd": str(cwd),
            "exit_code": None,
            "stdout": (exc.stdout or b"").decode(errors="replace")
            if isinstance(exc.stdout, bytes) else (exc.stdout or ""),
            "stderr": (exc.stderr or b"").decode(errors="replace")
            if isinstance(exc.stderr, bytes) else (exc.stderr or ""),
            "timed_out": True,
        }


def main() -> tuple[dict, int]:
    contract = json.loads(CONTRACT.read_text())
    admitted = json.loads(ADMITTED.read_text())
    pins = contract["axes"]["lean"]["pinned_toolchain"]
    hashes = {
        "EXECUTION_CONTRACT.json": digest(CONTRACT),
        "ADMITTED_INPUTS.json": digest(ADMITTED),
        "COMMON_SPEC.md": digest(COMMON),
        "formal_mathlib/lean-toolchain": digest(ROOT / pins["toolchain_path"]),
        "formal_mathlib/lake-manifest.json": digest(ROOT / pins["lake_manifest_path"]),
        "Main.lean": digest(SOURCE),
        "run.py": digest(Path(__file__).resolve()),
        "oracle/lean-toolchain": digest(ORACLE / "lean-toolchain"),
    }
    hash_match = (
        hashes["EXECUTION_CONTRACT.json"] == EXPECTED_CONTRACT_SHA256
        and hashes["ADMITTED_INPUTS.json"] == EXPECTED_ADMITTED_SHA256
        and hashes["COMMON_SPEC.md"] == EXPECTED_COMMON_SHA256
        and hashes["formal_mathlib/lean-toolchain"] == pins["toolchain_sha256"]
        and hashes["formal_mathlib/lake-manifest.json"] == pins["lake_manifest_sha256"]
        and hashes["oracle/lean-toolchain"] == pins["toolchain_sha256"]
    )
    oracle_manifest = json.loads((ORACLE / "lake-manifest.json").read_text())
    mathlib_manifest_rev = next(
        entry["rev"] for entry in oracle_manifest["packages"] if entry["name"] == "mathlib"
    )
    mathlib_git = execute(
        ["git", "-C", str(ORACLE / ".lake/packages/mathlib"), "rev-parse", "HEAD"],
        ORACLE,
    )
    mathlib_rev = mathlib_git["stdout"].strip()
    lean_version = execute(["lake", "env", "lean", "--version"], ORACLE)
    lake_version = execute(["lake", "--version"], ORACLE)
    lean_path_probe = execute(["lake", "env", "which", "lean"], ORACLE)
    lean_path = Path(lean_path_probe["stdout"].strip())
    lake_path = Path(shutil.which("lake") or "")
    binary_hashes = {
        "lean": digest(lean_path) if lean_path.is_file() else None,
        "lake": digest(lake_path) if lake_path.is_file() else None,
    }
    version_match = (
        lean_version["exit_code"] == 0
        and "Lean (version 4.31.0," in lean_version["stdout"]
        and mathlib_git["exit_code"] == 0
        and mathlib_rev == EXPECTED_MATHLIB_REV == pins["mathlib_revision"]
        and mathlib_manifest_rev == EXPECTED_MATHLIB_REV
        and lean_path_probe["exit_code"] == 0
    )
    source = SOURCE.read_text()
    forbidden = re.findall(r"\b(?:sorry|admit|unsafe|native_decide)\b", source, re.I)
    new_axiom_decls = re.findall(r"(?m)^\s*(?:axiom|constant)\b", source)
    theorem_decls = re.findall(r"(?m)^theorem (FD[123])\b", source)
    source_scan_ok = not forbidden and not new_axiom_decls and theorem_decls == ["FD1", "FD2", "FD3"]
    binding_ok = hash_match and version_match and admitted["targets"] == {
        name: expression for name, expression in zip(CHECK_NAMES, contract["target"]["canonical_form"])
    }
    compiler = execute(["lake", "env", "lean", "-j1", str(SOURCE)], ORACLE, timeout=3600)
    axiom_lines = {}
    for theorem in theorem_decls:
        match = re.search(
            rf"'Cas07C03\.{theorem}' depends on axioms: \[([^]]*)\]",
            compiler["stdout"],
        )
        axiom_lines[theorem] = match.group(1).split(", ") if match else None
    checks = {
        name: bool(
            binding_ok
            and source_scan_ok
            and compiler["exit_code"] == 0
            and not compiler["timed_out"]
            and axiom_lines[theorem] is not None
            and set(axiom_lines[theorem]) <= ALLOWED_AXIOMS
        )
        for name, theorem in zip(CHECK_NAMES, ("FD1", "FD2", "FD3"))
    }
    report = {
        "axis": "lean",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "domain_assumption_diff": [],
        "counterexample": None,
        "contract_id": contract["identity"]["contract_id"],
        "claim_ceiling": contract["identity"]["claim_ceiling"],
        "scientific_admission": "HOLD",
        "global_launch": None,
        "actual_author_model": None,
        "actual_author_effort": None,
        "actual_author_runtime_observation": "unknown_not_exposed_to_axis",
        "independence_mode": contract["independence"]["mode"],
        "result_path": str(RESULT),
        "hashes": hashes,
        "hash_match": hash_match,
        "mathlib_revision": mathlib_rev,
        "mathlib_manifest_revision": mathlib_manifest_rev,
        "version_match": version_match,
        "versions": {"lean": lean_version, "lake": lake_version},
        "executables": {
            "lean_path_probe": lean_path_probe,
            "lean_path": str(lean_path),
            "lake_path": str(lake_path),
            "sha256": binary_hashes,
        },
        "source_scan": {
            "forbidden_tokens": forbidden,
            "new_axiom_declarations": new_axiom_decls,
            "theorem_declarations": theorem_decls,
            "passed": source_scan_ok,
        },
        "axioms": axiom_lines,
        "compiler": compiler,
    }
    return report, 0 if all(checks.values()) else 1


if __name__ == "__main__":
    result, exit_code = main()
    json.dump(result, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    raise SystemExit(exit_code)
