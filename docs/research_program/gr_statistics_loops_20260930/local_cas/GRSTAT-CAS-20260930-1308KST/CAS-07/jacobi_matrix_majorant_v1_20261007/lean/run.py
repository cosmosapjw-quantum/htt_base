#!/usr/bin/env python3
"""Compile and record the frozen CAS-07-M04 Lean axis (stdlib only)."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from datetime import datetime, timezone


HERE = Path(__file__).resolve().parent
TASK = HERE.parent
REPO = TASK.parents[6]
ORACLE = Path("/home/cosmosapjw/lean_oracles/viii_oracle")
M03_OLEAN = ORACLE / "CAS07M03Accepted.olean"
EXPECTED = {
    TASK / "EXECUTION_CONTRACT.json": "553502c17d46c3b47c5a7b892f149f603235239d8504392b9bd19923f4edde7a",
    TASK / "ADMITTED_INPUTS.json": "f4d3b3b96a86fabcf83c7134193ec70da61b15d7a45b1a4b2c6b581312c1d4d8",
    REPO / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md": "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
    REPO / "formal_mathlib/lean-toolchain": "efac0b94923b2d8b6840cd35be9177ad0fc5ab2332f4f4311c98712cee92fdee",
    REPO / "formal_mathlib/lake-manifest.json": "bc86de9aed83fc38b0850702d6879ed6f3c97eedb7d1d69d643160731179d6ed",
    M03_OLEAN: "2728fb438129c39a9e9aae40e8ab8c70438014a7c713962baa13adbdabccca9e",
}
CHECKS = {
    "CAS-07-M04-VOLTERRA-IDENTITY": "Cas07M04.volterra_identity",
    "CAS-07-M04-SCALAR-PREMISE": "Cas07M04.scalar_premise",
    "CAS-07-M04-D-NORM": "Cas07M04.d_norm",
    "CAS-07-M04-D-MINUS-SI": "Cas07M04.d_minus_si",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def call(args: list[str], *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ORACLE, env=env, text=True, capture_output=True, check=False)


def main() -> int:
    started = datetime.now(timezone.utc).isoformat()
    hashes = {str(path): sha256(path) if path.is_file() else None for path in EXPECTED}
    hash_ok = all(hashes[str(path)] == expected for path, expected in EXPECTED.items())
    main_source = HERE / "Main.lean"
    forbidden = re.findall(r"\b(?:sorry|admit|unsafe|native_decide|axiom)\b", main_source.read_text())
    tool_versions = {
        "lean": call(["lean", "--version"]).stdout.strip(),
        "lake": call(["lake", "--version"]).stdout.strip(),
        "python": sys.version.splitlines()[0],
        "mathlib_revision": call(["git", "-C", str(ORACLE / ".lake/packages/mathlib"), "rev-parse", "HEAD"]).stdout.strip(),
    }
    env = dict(os.environ)
    env["LEAN_PATH"] = str(ORACLE) + os.pathsep + str(HERE)
    main_olean = HERE / "Main.olean"
    compile_result = call(["lake", "env", "lean", "-R", str(HERE), "-o", str(main_olean), str(main_source)], env=env)
    (HERE / "compiler.log").write_text(
        "command: lake env lean -R LEAN_DIR -o Main.olean Main.lean\n"
        f"cwd: {ORACLE}\nexit_code: {compile_result.returncode}\n"
        + compile_result.stdout + compile_result.stderr
    )
    check_result = None
    if compile_result.returncode == 0:
        check_result = call(["lake", "env", "lean", "-R", str(HERE), str(HERE / "Checks.lean")], env=env)
    check_output = "" if check_result is None else check_result.stdout + check_result.stderr
    (HERE / "checks.log").write_text(
        "command: lake env lean -R LEAN_DIR Checks.lean\n"
        f"cwd: {ORACLE}\nexit_code: {None if check_result is None else check_result.returncode}\n"
        + check_output
    )
    checks_ok = check_result is not None and check_result.returncode == 0
    axiom_rows = re.findall(r"'(Cas07M04\.[^']+)' depends on axioms: \[([^\]]*)\]", check_output)
    allowed_axioms = {"propext", "Classical.choice", "Quot.sound"}
    axioms_ok = checks_ok and len(axiom_rows) == 6 and all(
        set(map(str.strip, row.split(","))) <= allowed_axioms for _, row in axiom_rows
    )
    global_ok = hash_ok and not forbidden and compile_result.returncode == 0 and checks_ok and axioms_ok
    check_status = {
        label: {
            "status": "PASS" if global_ok and theorem in check_output else "BLOCKED",
            "theorem": theorem,
            "evidence": "checks.log",
        }
        for label, theorem in CHECKS.items()
    }
    if any(item["status"] != "PASS" for item in check_status.values()):
        global_ok = False
    artifacts = {}
    for name in ("Main.lean", "Main.olean", "Checks.lean", "run.py", "compiler.log", "checks.log", "PROOF_NOTES.md"):
        path = HERE / name
        artifacts[name] = {"sha256": sha256(path), "size_bytes": path.stat().st_size} if path.is_file() else None
    result = {
        "schema": "htt.cas07.m04.lean-result.v1",
        "contract_id": "GRSTAT-20260930-CAS-07-M04-JACOBI-MAJORANT-V1",
        "axis": "lean",
        "status": "PASS" if global_ok else "BLOCKED",
        "reason": None if global_ok else "COMPILE_OR_BINDING_OR_AXIOM_CHECK_FAILED",
        "started_utc": started,
        "finished_utc": datetime.now(timezone.utc).isoformat(),
        "launch_id": None,
        "authority_status": "UNAVAILABLE",
        "observed_model": "UNKNOWN",
        "observed_effort": "UNKNOWN",
        "execution_mode": "OWNER_AUTHORIZED_DIRECT_LOCAL",
        "checks": check_status,
        "domain_assumption_diff": [],
        "counterexample": None,
        "input_hashes": hashes,
        "input_hashes_match": hash_ok,
        "forbidden_source_tokens": forbidden,
        "tool_versions": tool_versions,
        "m03_dependency": {
            "module": "CAS07M03Accepted.olean",
            "accepted_theorem": "CAS07M03.scalar_volterra_comparison",
            "source_sha256_reported_by_coordinator": "98497a877b4a8be30f7449c706229c9e64070d84968951cc729a1a2ff3a74102",
            "olean_sha256": hashes[str(M03_OLEAN)],
            "proof_source_inspected": False,
        },
        "compile_exit_code": compile_result.returncode,
        "checks_exit_code": None if check_result is None else check_result.returncode,
        "axioms_ok": axioms_ok,
        "axiom_dependencies": {theorem: row.split(", ") for theorem, row in axiom_rows},
        "artifacts": artifacts,
        "scientific_admission": "HOLD",
        "claim_ceiling": "matrix_majorization_only_no_determinant_or_science",
    }
    (HERE / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": result["status"],
        "result_path": str(HERE / "result.json"),
        "checks": {label: item["status"] == "PASS" for label, item in check_status.items()},
        "domain_assumption_diff": [],
        "counterexample": None,
    }, sort_keys=True))
    return 0 if global_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
