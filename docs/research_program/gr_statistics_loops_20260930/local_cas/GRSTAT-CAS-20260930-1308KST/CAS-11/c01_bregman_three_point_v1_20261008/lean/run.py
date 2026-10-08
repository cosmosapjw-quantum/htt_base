#!/usr/bin/env python3
"""Run the frozen CAS-11-C01 Lean axis and emit an exact boolean CAS payload."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
TASK = HERE.parent
REPO = next(p for p in HERE.parents if (p / ".agent-harness/scripts/cas_gate.py").is_file())
ORACLE = Path("/home/cosmosapjw/lean_oracles/viii_oracle")
CONTRACT = TASK / "EXECUTION_CONTRACT.json"
ADMITTED = TASK / "ADMITTED_INPUTS.json"
COMMON = REPO / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
SOURCE = HERE / "BregmanThreePoint.lean"
MANIFEST = ORACLE / "lake-manifest.json"
TOOLCHAIN = ORACLE / "lean-toolchain"
MATHLIB = ORACLE / ".lake/packages/mathlib"
OLEAN = MATHLIB / ".lake/build/lib/lean/Mathlib.olean"
EXPECTED = {
    CONTRACT: "3e0adbd4b1a31163e58c13d48e1ebe703a6d7daa55cdb8d247f6c1a41bd4b16a",
    ADMITTED: "c65019a54a477d4d75738579741c33ace4e19db42142e0bde0c20b013cd79e55",
    COMMON: "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
    MANIFEST: "1a7cbb6b0487b078e2e5f768fc9e1bd78e2e36d0d896477cadf1d8971464db08",
    TOOLCHAIN: "efac0b94923b2d8b6840cd35be9177ad0fc5ab2332f4f4311c98712cee92fdee",
}
OBLIGATION = "CAS-11-C01"
THEOREMS = (
    "three_point",
    "transpose_pairing",
    "exact_moment_cancellation",
    "orientation_control_forward",
    "orientation_control_reverse",
    "approximate_moment_control",
    "approximate_moment_nonzero",
)
STANDARD_AXIOMS = "[propext, Classical.choice, Quot.sound]"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(argv: list[str], cwd: Path, env: dict[str, str], timeout: int = 3600) -> dict:
    try:
        completed = subprocess.run(
            argv, cwd=cwd, env=env, text=True, capture_output=True,
            timeout=timeout, check=False,
        )
        return {"argv": argv, "cwd": str(cwd), "exit_code": completed.returncode,
                "stdout": completed.stdout, "stderr": completed.stderr, "timeout": False}
    except subprocess.TimeoutExpired as exc:
        return {"argv": argv, "cwd": str(cwd), "exit_code": None,
                "stdout": (exc.stdout or b"").decode(errors="replace"),
                "stderr": (exc.stderr or b"").decode(errors="replace"), "timeout": True}


def main() -> int:
    differences: list[str] = []
    for path, expected in EXPECTED.items():
        if not path.is_file() or sha256(path) != expected:
            differences.append(f"frozen file mismatch: {path}")
    source = SOURCE.read_text()
    if re.search(r"\b(sorry|admit|sorryAx)\b", source):
        differences.append("source contains a forbidden proof bypass")
    if re.search(r"(?m)^\s*axiom\b", source):
        differences.append("source declares an axiom")
    if not OLEAN.is_file():
        differences.append("pinned Mathlib.olean missing")
    manifest = json.loads(MANIFEST.read_text())
    manifest_rev = next(p["rev"] for p in manifest["packages"] if p["name"] == "mathlib")
    git_rev_run = run(["git", "rev-parse", "HEAD"], MATHLIB, os.environ.copy(), 30)
    mathlib_rev = git_rev_run["stdout"].strip()
    if manifest_rev != "fabf563a7c95a166b8d7b6efca11c8b4dc9d911f" or mathlib_rev != manifest_rev:
        differences.append("mathlib revision mismatch")
    env = os.environ.copy()
    env["ELAN_TOOLCHAIN"] = "leanprover/lean4:v4.31.0"
    version_run = run(["lean", "--version"], ORACLE, env, 30)
    if version_run["exit_code"] != 0 or not version_run["stdout"].startswith("Lean (version 4.31.0,"):
        differences.append("Lean version mismatch")
    lake_version_run = run(["lake", "--version"], ORACLE, env, 30)
    if lake_version_run["exit_code"] != 0 or "Lean version 4.31.0" not in lake_version_run["stdout"]:
        differences.append("Lake version mismatch")
    lean_path_run = run(["elan", "which", "lean"], ORACLE, env, 30)
    lake_path_run = run(["elan", "which", "lake"], ORACLE, env, 30)
    lean_bin = Path(lean_path_run["stdout"].strip())
    lake_bin = Path(lake_path_run["stdout"].strip())
    if not lean_bin.is_file() or not lake_bin.is_file():
        differences.append("pinned compiler executable missing")
    lean_run = run(["lake", "env", "lean", str(SOURCE)], ORACLE, env)
    (HERE / "lean_stdout.log").write_text(lean_run["stdout"])
    (HERE / "lean_stderr.log").write_text(lean_run["stderr"])
    lines = set(lean_run["stdout"].splitlines())
    axioms_ok = all(
        f"'CAS11C01.{name}' depends on axioms: {STANDARD_AXIOMS}" in lines
        for name in THEOREMS
    ) and len(lines) == len(THEOREMS)
    proof_ok = lean_run["exit_code"] == 0 and axioms_ok
    if not axioms_ok:
        differences.append("theorem axiom report incomplete or unexpected")
    if lean_run["timeout"]:
        differences.append("Lean compilation timed out")
    status = "PASS" if proof_ok and not differences else "INCONCLUSIVE"
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    payload = {
        "checks": {OBLIGATION: status == "PASS"},
        "domain_assumption_diff": differences,
        "counterexample": None,
    }
    result = {
        "schema_version": 1,
        "axis": "lean",
        "status": status,
        "contract_sha256": EXPECTED[CONTRACT],
        "evidence_class": "exact",
        "completed_at": now,
        "source": str(SOURCE.relative_to(REPO)),
        "source_sha256": sha256(SOURCE),
        "runner_sha256": sha256(Path(__file__)),
        "statement_alignment": {
            "space": "Fin n -> Real with coordinate Euclidean dot product",
            "bregman_orientation": "H(x)-H(y)-dot(gradH(y),x-y)",
            "gradient_condition": "gradH(h)-gradH(g)=V lambda",
            "moment_condition": "V^T(f-h)=0 exactly",
            "controls": ["cubic 4/3 versus 5/3", "1/10 residual is nonzero"],
            "claim_ceiling": "finite/local CAS-11-C01 only",
            "remaining": ["integrability", "continuum entropy bounds", "science"],
        },
        "toolchain": {
            "lean_version": version_run["stdout"].strip(),
            "lake_version": lake_version_run["stdout"].strip(),
            "lean_executable": str(lean_bin),
            "lean_executable_sha256": sha256(lean_bin) if lean_bin.is_file() else None,
            "lake_executable": str(lake_bin),
            "lake_executable_sha256": sha256(lake_bin) if lake_bin.is_file() else None,
            "toolchain_sha256": sha256(TOOLCHAIN),
            "manifest_sha256": sha256(MANIFEST),
            "mathlib_revision": mathlib_rev,
            "mathlib_olean_present": OLEAN.is_file(),
            "mathlib_olean_sha256": sha256(OLEAN) if OLEAN.is_file() else None,
        },
        "commands": [
            {"argv": item["argv"], "cwd": item["cwd"],
             "exit_code": item["exit_code"], "timeout": item["timeout"]}
            for item in (git_rev_run, version_run, lake_version_run,
                         lean_path_run, lake_path_run, lean_run)
        ],
        "logs": ["lean_stdout.log", "lean_stderr.log"],
        "payload": payload,
        "evidence_origin": "own_axis_local_subprocess; runner adjudication pending",
        "launch_id": None,
        "observed_author_model": "UNKNOWN",
    }
    (HERE / "axis_result.json").write_text(json.dumps(result, indent=2) + "\n")
    sys.stdout.write(json.dumps(payload, separators=(",", ":")) + "\n")
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
