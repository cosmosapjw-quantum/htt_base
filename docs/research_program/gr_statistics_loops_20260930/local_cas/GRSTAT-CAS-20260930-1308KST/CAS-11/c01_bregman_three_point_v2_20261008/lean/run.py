#!/usr/bin/env python3
"""Deterministic independent Lean runner for frozen CAS-11-C01 v2."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path


AXIS = Path(__file__).resolve().parent
BASE = AXIS.parent
REPO = Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
ORACLE = Path("/home/cosmosapjw/lean_oracles/viii_oracle")
SOURCE = AXIS / "BregmanThreePoint.lean"
EXPECTED = {
    BASE / "EXECUTION_CONTRACT.json": "b62b4eed9cf40b400348f396aefa166f85a24d9880ec31d429b5d75f280dc884",
    BASE / "ADMITTED_INPUTS.json": "c65019a54a477d4d75738579741c33ace4e19db42142e0bde0c20b013cd79e55",
    REPO / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md": "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
    ORACLE / "lake-manifest.json": "1a7cbb6b0487b078e2e5f768fc9e1bd78e2e36d0d896477cadf1d8971464db08",
    ORACLE / "lean-toolchain": "efac0b94923b2d8b6840cd35be9177ad0fc5ab2332f4f4311c98712cee92fdee",
    SOURCE: "12f3dd682db93f0966fd3547f10f25eb4fca9e8506ff58fc7c1ba6ac7cf9975c",
}
EXPECTED_REV = "fabf563a7c95a166b8d7b6efca11c8b4dc9d911f"
EXPECTED_VERSION = "Lean (version 4.31.0,"
EXPECTED_AXIOMS = {
    "CAS11C01.three_point",
    "CAS11C01.dot_matVec",
    "CAS11C01.exact_moment_cancellation",
    "CAS11C01.three_point_cancel",
    "CAS11C01.cubic_orientation_nonzero",
    "CAS11C01.approximate_moment_nonzero",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def call(argv: list[str], *, cwd: Path, timeout: int = 300) -> subprocess.CompletedProcess[bytes]:
    env = os.environ.copy()
    env["ELAN_TOOLCHAIN"] = "leanprover/lean4:v4.31.0"
    return subprocess.run(
        argv, cwd=cwd, env=env, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, timeout=timeout, check=False
    )


def emit(ok: bool, reason: str | None, computed: dict, *, platform: bool = False) -> int:
    # A platform/seal failure is inconclusive for mathematics: return nonzero
    # with checks still true, so cas_gate does not mislabel it a counterexample.
    print(json.dumps({
        "checks": {"CAS-11-C01": ok or platform},
        "domain_assumption_diff": [],
        "counterexample": None,
        "computed": computed,
    }, sort_keys=True))
    if reason:
        print(reason, file=sys.stderr)
    return 2 if platform else (0 if ok else 1)


def main() -> int:
    observed = {}
    try:
        for path, expected in EXPECTED.items():
            actual = sha(path)
            observed[str(path)] = actual
            if actual != expected:
                return emit(False, f"frozen source/toolchain hash mismatch: {path}", observed, platform=True)
        if re.search(r"\b(?:sorry|admit|axiom)\b", SOURCE.read_text()):
            return emit(False, "forbidden proof token in source", observed)
        rev = call(["git", "-C", str(ORACLE / ".lake/packages/mathlib"), "rev-parse", "HEAD"], cwd=ORACLE)
        if rev.returncode != 0 or rev.stdout.decode().strip() != EXPECTED_REV:
            return emit(False, "mathlib revision mismatch or unavailable", observed, platform=True)
        version = call(["lean", "--version"], cwd=ORACLE)
        if version.returncode != 0 or not version.stdout.decode().startswith(EXPECTED_VERSION):
            return emit(False, "Lean version mismatch or unavailable", observed, platform=True)
        run = call(["lake", "env", "lean", str(SOURCE)], cwd=ORACLE, timeout=3600)
        combined = run.stdout + run.stderr
        log_hash = hashlib.sha256(combined).hexdigest()
        observed.update({
            "mathlib_revision": EXPECTED_REV,
            "lean_version": version.stdout.decode().strip(),
            "lean_exit": run.returncode,
            "raw_log_sha256": log_hash,
            "raw_log_matches_final": combined == (AXIS / "compile_attempt_2.log").read_bytes(),
        })
        # Preserve a new raw failure under the owned axis, without replacing
        # the first or final compile logs.
        if run.returncode != 0:
            failure = AXIS / f"runner_failure_{log_hash}.log"
            if not failure.exists():
                failure.write_bytes(combined)
            return emit(False, f"Lean compilation failed; raw log: {failure}", observed)
        lines = combined.decode().splitlines()
        seen = set()
        for line in lines:
            match = re.fullmatch(r"'([^']+)' depends on axioms: \[propext, Classical.choice, Quot.sound\]", line)
            if not match:
                return emit(False, f"unexpected Lean output: {line}", observed)
            seen.add(match.group(1))
        if seen != EXPECTED_AXIOMS or len(lines) != len(EXPECTED_AXIOMS):
            return emit(False, "missing theorem axiom print or unexpected duplicate", observed)
        if not observed["raw_log_matches_final"]:
            return emit(False, "raw Lean output differs from retained final log", observed)
        observed["formal_axioms"] = ["propext", "Classical.choice", "Quot.sound"]
        observed["dimension_scope"] = "arbitrary Fin n and Fin k, including zero dimensions"
        return emit(True, None, observed)
    except (OSError, subprocess.TimeoutExpired, UnicodeError) as exc:
        return emit(False, f"platform execution error: {exc}", observed, platform=True)


if __name__ == "__main__":
    sys.exit(main())
