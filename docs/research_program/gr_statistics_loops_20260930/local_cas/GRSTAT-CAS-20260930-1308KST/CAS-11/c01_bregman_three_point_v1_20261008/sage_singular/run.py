#!/usr/bin/env python3
"""Standard-Python wrapper for the exact Sage/Singular CAS-11-C01 proof.

Run from any cwd with ``/usr/bin/python3.12 -B run.py``. Output is one compact
JSON object. The unchanged Sage proof and pinned Singular are subprocesses.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[7]
SINGULAR = Path("/home/cosmosapjw/opt/sage/local/bin/Singular")
EXPECTED = {
    HERE.parent / "EXECUTION_CONTRACT.json": "3e0adbd4b1a31163e58c13d48e1ebe703a6d7daa55cdb8d247f6c1a41bd4b16a",
    HERE.parent / "ADMITTED_INPUTS.json": "c65019a54a477d4d75738579741c33ace4e19db42142e0bde0c20b013cd79e55",
    ROOT / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md": "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
    SINGULAR: "9430832b7c972b6b26d29ded4d91a3e1df8fd87d67f4b8d3f14d8201a75f923c",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def engine(argv: list[str], stem: str, timeout: int) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PATH"] = str(SINGULAR.parent) + os.pathsep + env.get("PATH", "")
    proc = subprocess.run(argv, cwd=HERE, env=env, text=True, capture_output=True, timeout=timeout)
    (HERE / f"{stem}.stdout.log").write_text(proc.stdout)
    (HERE / f"{stem}.stderr.log").write_text(proc.stderr)
    assert proc.returncode == 0, f"{argv[0]} exit={proc.returncode}; inspect {stem} logs"
    return proc


def main() -> int:
    for path, expected in EXPECTED.items():
        assert sha256(path) == expected, f"frozen SHA mismatch: {path}"

    sage_version_cmd = ["sage", "--version"]
    sage_version = engine(sage_version_cmd, "sage.version", 60)
    assert "SageMath version 10.9" in sage_version.stdout and not sage_version.stderr.strip()
    singular_version_cmd = [str(SINGULAR), "--version"]
    singular_version = engine(singular_version_cmd, "singular.version", 60)
    assert "version 4.4.1 (44100" in singular_version.stdout and not singular_version.stderr.strip()

    sage_cmd = ["sage", "-python", str(HERE / "sage_proof.py")]
    sage = engine(sage_cmd, "sage", 900)
    assert not sage.stderr.strip(), "Sage stderr is nonempty"
    assert json.loads(sage.stdout) == {"CAS-11-C01": True}, "Sage returned a non-exact C01 payload"

    singular_cmd = [str(SINGULAR), "-q", str(HERE / "bregman_c01.sing")]
    singular = engine(singular_cmd, "singular", 300)
    assert not singular.stderr.strip(), "Singular stderr is nonempty"
    assert "?" not in singular.stdout and "FAIL" not in singular.stdout, "Singular reported an engine or assertion error"
    markers = (
        "PASS identity_residual=0",
        "PASS transpose_residual=0 quotient_remainder=0",
        "PASS orientation=4/3,5/3 approximate_residual=1/10",
        "CAS-11-C01=true",
    )
    assert all(marker in singular.stdout for marker in markers), "Singular omitted a required marker"

    detail = {
        "wrapper_python": sys.version.split()[0],
        "sage_version": sage_version.stdout.strip(),
        "singular_version": "4.4.1/44100",
        "singular_binary_sha256": sha256(SINGULAR),
        "sage_version_argv": sage_version_cmd,
        "singular_version_argv": singular_version_cmd,
        "sage_proof_argv": sage_cmd,
        "singular_proof_argv": singular_cmd,
        "exit_codes": {"sage_version": 0, "singular_version": 0, "sage_proof": 0, "singular_proof": 0},
        "input_sha256": {str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path): expected for path, expected in EXPECTED.items()},
    }
    (HERE / "wrapper_detail.json").write_text(json.dumps(detail, indent=2, sort_keys=True) + "\n")
    payload = {"CAS-11-C01": True}
    (HERE / "result.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    runner_payload = {"checks": payload, "domain_assumption_diff": [], "counterexample": None}
    print(json.dumps(runner_payload, separators=(",", ":")), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
