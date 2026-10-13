#!/usr/bin/env python3
"""Reproduce only the frozen CAS-11-C01 Wolfram+xTensor axis."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[7]
UNIT = HERE.parent
CONTRACT = UNIT / "EXECUTION_CONTRACT.json"
INPUT = UNIT / "ADMITTED_INPUTS.json"
COMMON = ROOT / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
SOURCE = HERE / "bregman_three_point.wl"
EXPECTED = {
    CONTRACT: "3e0adbd4b1a31163e58c13d48e1ebe703a6d7daa55cdb8d247f6c1a41bd4b16a",
    INPUT: "c65019a54a477d4d75738579741c33ace4e19db42142e0bde0c20b013cd79e55",
    COMMON: "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
}
CHECKS = (
    "tensor_identity",
    "transpose_factorization",
    "universal_bilinear_identity",
    "cubic_orientation",
    "approximate_nonzero",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path: Path, obj: dict) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    observed = {str(path.relative_to(ROOT)): sha(path) for path in EXPECTED}
    drift = [str(path) for path, expected in EXPECTED.items() if sha(path) != expected]
    if drift:
        print("Frozen input hash drift: " + ", ".join(drift), file=sys.stderr)
        return 2
    exe = shutil.which("wolframscript")
    if exe is None:
        print("wolframscript unavailable", file=sys.stderr)
        return 2
    argv = [exe, "-file", str(SOURCE)]
    start = datetime.now(timezone.utc).isoformat()
    try:
        process = subprocess.run(argv, cwd=ROOT, text=True, capture_output=True, timeout=1800)
    except subprocess.TimeoutExpired as exc:
        (HERE / "stdout.log").write_text(exc.stdout or "", encoding="utf-8")
        (HERE / "stderr.log").write_text(exc.stderr or "", encoding="utf-8")
        print("Wolfram timed out", file=sys.stderr)
        return 2
    (HERE / "stdout.log").write_text(process.stdout, encoding="utf-8")
    (HERE / "stderr.log").write_text(process.stderr, encoding="utf-8")
    check_values = {
        name: (f"CHECK:{name}=True" in process.stdout) for name in CHECKS
    }
    exact_values = {
        "cubic_forward_4_over_3": "CUBIC_FORWARD=4/3" in process.stdout,
        "cubic_reverse_5_over_3": "CUBIC_REVERSE=5/3" in process.stdout,
        "approximate_residual_1_over_10": "APPROX_RESIDUAL=1/10" in process.stdout,
    }
    engine = {
        "wolfram_version": next((line.split("=", 1)[1] for line in process.stdout.splitlines() if line.startswith("WOLFRAM_VERSION=")), None),
        "xtensor_version": next((line.split("=", 1)[1] for line in process.stdout.splitlines() if line.startswith("XTENSOR_VERSION=")), None),
    }
    passed = (
        process.returncode == 0
        and all(check_values.values())
        and all(exact_values.values())
        and "ALL_CHECKS=True" in process.stdout
        and engine["wolfram_version"] is not None
        and engine["xtensor_version"] is not None
    )
    finished = datetime.now(timezone.utc).isoformat()
    result = {
        "axis": "wolfram_xact",
        "component": "CAS-11-C01",
        "status": "PASS" if passed else "FAIL",
        "contract_sha256": EXPECTED[CONTRACT],
        "input_sha256": EXPECTED[INPUT],
        "common_spec_sha256": EXPECTED[COMMON],
        "input_hashes_observed": observed,
        "started_utc": start,
        "finished_utc": finished,
        "completed_at": finished,
        "evidence_class": "exact",
        "commands": [{"argv": argv, "cwd": str(ROOT), "exit_code": process.returncode}],
        "exits": [process.returncode],
        "argv": argv,
        "cwd": str(ROOT),
        "exit_code": process.returncode,
        "engine": engine,
        "checks": check_values,
        "exact_values": exact_values,
        "artifacts": {
            name: {"path": str(HERE / name), "sha256": sha(HERE / name), "size": (HERE / name).stat().st_size}
            for name in ("bregman_three_point.wl", "run.py", "stdout.log", "stderr.log")
        },
        "statement_alignment": "Exact finite-dimensional Euclidean Bregman orientation identity for arbitrary symbolic H values and gradients; q=V lambda and V^T(f-h)=0 imply exact zero through index contraction; cubic orientation and 1/10 nonzero residual controls.",
        "domain_assumption_diff": [],
        "branch_diff": [],
        "remaining": ["integrability", "continuum entropy bounds", "science"],
        "scientific_admission": "HOLD",
        "launch_id": None,
        "author_observed_model": "UNAVAILABLE",
        "author_observed_effort": "UNKNOWN",
    }
    dump(HERE / "result.json", result)
    dump(HERE / "axis_result.json", result)
    payload = {
        "checks": {"CAS-11-C01": passed},
        "domain_assumption_diff": [],
        "counterexample": None,
    }
    print(json.dumps(payload, separators=(",", ":")))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
