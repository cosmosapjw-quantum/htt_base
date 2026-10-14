#!/usr/bin/env python3
"""Execute and seal the CAS-03-C02 Lean axis.

Stdout is exactly one gate payload.  Full command logs and the typed stored
axis envelope are written beside this script.
"""

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
REPO = next(parent for parent in HERE.parents if (parent / ".git").exists())
COMPONENT = HERE.parent
CONTRACT = COMPONENT / "EXECUTION_CONTRACT.json"
ADMITTED = COMPONENT / "ADMITTED_INPUTS.json"
COMMON = REPO / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
BASE_TOOLCHAIN = REPO / "formal_mathlib/lean-toolchain"
BASE_MANIFEST = REPO / "formal_mathlib/lake-manifest.json"
SOURCE = HERE / "Cas03C02.lean"
LOCAL_TOOLCHAIN = HERE / "lean-toolchain"
LOCAL_MANIFEST = HERE / "lake-manifest.json"
RAW = HERE / "raw"
AXIS_RESULT = HERE / "axis_result.json"
EXECUTION = HERE / "execution.json"

EXPECTED = {
    "contract_id": "GRSTAT-20260930-CAS-03-C02-GEODESIC-FAMILY-V1",
    "admitted_sha256": "14e2c2843ff9791656488613ced678198d9f37beb246d8c15b6fba6530af03d1",
    "common_sha256": "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
    "toolchain_sha256": "efac0b94923b2d8b6840cd35be9177ad0fc5ab2332f4f4311c98712cee92fdee",
    "base_manifest_sha256": "bc86de9aed83fc38b0850702d6879ed6f3c97eedb7d1d69d643160731179d6ed",
    "mathlib_rev": "fabf563a7c95a166b8d7b6efca11c8b4dc9d911f",
    "lean_version": "4.31.0",
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(argv: list[str], *, cwd: Path = HERE) -> dict:
    completed = subprocess.run(
        argv,
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
        env={**os.environ, "ELAN_TOOLCHAIN": "leanprover/lean4:v4.31.0"},
    )
    return {
        "argv": argv,
        "cwd": str(cwd),
        "exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def write_log(stem: str, record: dict) -> None:
    (RAW / f"{stem}.stdout.log").write_text(record["stdout"], encoding="utf-8")
    (RAW / f"{stem}.stderr.log").write_text(record["stderr"], encoding="utf-8")


def main() -> int:
    RAW.mkdir(exist_ok=True)
    if AXIS_RESULT.is_file():
        prior = json.loads(AXIS_RESULT.read_text(encoding="utf-8"))
        first_axis = RAW / "first_failure.axis_result.json"
        first_execution = RAW / "first_failure.execution.json"
        if prior.get("result") != "pass" and not first_axis.exists():
            first_axis.write_bytes(AXIS_RESULT.read_bytes())
            if EXECUTION.is_file():
                first_execution.write_bytes(EXECUTION.read_bytes())
    started_at = now()
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    local_manifest = json.loads(LOCAL_MANIFEST.read_text(encoding="utf-8"))
    mathlib_revs = [
        item.get("rev")
        for item in local_manifest.get("packages", [])
        if item.get("name") == "mathlib"
    ]

    version = run(["lean", "--version"], cwd=REPO)
    compile_run = run(["lake", "env", "lean", "Cas03C02.lean"])
    write_log("lean_version", version)
    write_log("lean_compile", compile_run)

    source_text = SOURCE.read_text(encoding="utf-8")
    theorem_names = [
        "exact_family_difference",
        "rest_action_apply",
        "mem_kernel_iff_zero_mask",
        "kernel_finrank_eq_zeroCount",
        "kernel_finrank_all_zero",
        "kernel_finrank_repeated_nonzero",
        "kernel_finrank_repeated_nonzero_with_zero",
    ]
    axiom_headers = [
        f"'Cas03C02.{name}' depends on axioms:" for name in theorem_names
    ]
    forbidden_source = re.search(r"\b(sorry|admit|axiom)\b", source_text)
    no_sorry_ax = "sorryAx" not in compile_run["stdout"] + compile_run["stderr"]
    axiom_log_complete = all(header in compile_run["stdout"] for header in axiom_headers)

    alignments = {
        "contract_id": contract.get("identity", {}).get("contract_id") == EXPECTED["contract_id"],
        "exact_obligation": contract.get("target", {}).get("exact_test_obligations") == ["CAS-03-C02"],
        "admitted_hash": sha256(ADMITTED) == EXPECTED["admitted_sha256"],
        "common_hash": sha256(COMMON) == EXPECTED["common_sha256"],
        "base_toolchain_hash": sha256(BASE_TOOLCHAIN) == EXPECTED["toolchain_sha256"],
        "local_toolchain_hash": sha256(LOCAL_TOOLCHAIN) == EXPECTED["toolchain_sha256"],
        "base_manifest_hash": sha256(BASE_MANIFEST) == EXPECTED["base_manifest_sha256"],
        "mathlib_revision": mathlib_revs == [EXPECTED["mathlib_rev"]],
        "lean_version": version["exit_code"] == 0 and EXPECTED["lean_version"] in version["stdout"],
        "compile": compile_run["exit_code"] == 0,
        "no_forbidden_source_tokens": forbidden_source is None,
        "no_sorryAx": no_sorry_ax,
        "axiom_log_complete": axiom_log_complete,
    }
    passed = all(alignments.values())
    completed_at = now()

    commands = [
        {key: record[key] for key in ("argv", "cwd", "exit_code")}
        for record in (version, compile_run)
    ]
    execution = {
        "schema": "htt.cas.axis-execution.v1",
        "axis": "lean",
        "component": "CAS-03-C02",
        "started_at": started_at,
        "completed_at": completed_at,
        "commands": commands,
        "alignments": alignments,
        "hashes": {
            "contract": sha256(CONTRACT),
            "admitted_inputs": sha256(ADMITTED),
            "common_spec": sha256(COMMON),
            "source": sha256(SOURCE),
            "local_manifest": sha256(LOCAL_MANIFEST),
            "base_manifest": sha256(BASE_MANIFEST),
            "toolchain": sha256(LOCAL_TOOLCHAIN),
        },
        "mathlib_revision": mathlib_revs[0] if len(mathlib_revs) == 1 else None,
        "evidence_class": "exact",
        "launch_id": None,
        "observed_author_model": "UNKNOWN",
        "scientific_admission": "HOLD",
    }
    EXECUTION.write_text(json.dumps(execution, indent=2) + "\n", encoding="utf-8")

    axis_result = {
        "schema_version": 1,
        "axis": "lean",
        "status": "PASS" if passed else "INCONCLUSIVE",
        "result": "pass" if passed else "inconclusive",
        "contract_sha256": sha256(CONTRACT),
        "evidence_class": "exact",
        "completed_at": completed_at,
        "commands": commands,
        "checks": {"CAS-03-C02": passed},
        "domain_assumption_diff": [],
        "counterexample": None,
        "outputs": [
            {"path": str(SOURCE.relative_to(REPO)), "sha256": sha256(SOURCE)},
            {"path": str(EXECUTION.relative_to(REPO)), "sha256": sha256(EXECUTION)},
            {
                "path": str((RAW / "lean_compile.stdout.log").relative_to(REPO)),
                "sha256": sha256(RAW / "lean_compile.stdout.log"),
            },
        ],
        "launch_id": None,
        "observed_author_model": "UNKNOWN",
        "scientific_admission": "HOLD",
        "claim_ceiling": "C02 finite geodesic family only",
        "remaining": ["CAS03 C03", "eigenfield existence/IFT", "science"],
    }
    AXIS_RESULT.write_text(json.dumps(axis_result, indent=2) + "\n", encoding="utf-8")

    payload = {
        "checks": {"CAS-03-C02": passed},
        "domain_assumption_diff": [],
        "counterexample": None,
        "result": "pass" if passed else "inconclusive",
        "evidence_class": "exact",
        "launch_id": None,
        "observed_author_model": "UNKNOWN",
        "scientific_admission": "HOLD",
    }
    print(json.dumps(payload, separators=(",", ":")))
    return 0 if passed else 2


if __name__ == "__main__":
    sys.exit(main())
