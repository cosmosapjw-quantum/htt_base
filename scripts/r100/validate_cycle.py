"""R100 end-to-end verification and immutable R78/R99 authority validator."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "docs/research_program/observational_publication_20261015"
R78_DIR = BASE / "R78_UNIFIED_SCIENCE_DAG_20261119"
R99_DIR = BASE / "R99_FIFTH_BLOCKER_RESOLUTION_20261123"
OUT = BASE / "R100_SOURCE_LAW_OPTICAL_MULTIPROBE_20261123"
PY = sys.executable

R100_CODE_AND_TESTS = [
    "htt/bass/transport/position_drift_optics.py",
    "scripts/r100/__init__.py",
    "scripts/r100/source_intake.py",
    "scripts/r100/optical_drift.py",
    "scripts/r100/cf4_upstream_and_kband.py",
    "scripts/r100/radio_exposure_selection.py",
    "scripts/r100/gaia_optical_joint.py",
    "scripts/r100/bianchi_selfconsistent_and_phy.py",
    "scripts/r100/program_preparation.py",
    "scripts/r100/validate_cycle.py",
    "tests/obsstat/test_r100_optical_drift.py",
    "tests/obsstat/test_r100_cf4.py",
    "tests/obsstat/test_r100_radio_exposure.py",
    "tests/obsstat/test_r100_gaia_optical.py",
    "tests/obsstat/test_r100_bianchi_phy.py",
    "tests/obsstat/test_r100_program_preparation.py",
]

R100_RESULTS = [
    "SOURCE_INTAKE_RECEIPT.json",
    "OPTICAL_DRIFT_RESULTS.json",
    "OPTICAL_DRIFT_TEMPLATES.npz",
    "CF4_UPSTREAM_KBAND_RESULTS.json",
    "CF4_FULL_KBAND_COVARIANCES.npz",
    "RADIO_EXPOSURE_SELECTION_RESULTS.json",
    "GAIA_OPTICAL_JOINT_RESULTS.json",
    "BIANCHI_SELFCONSISTENT_AND_PHY_RESULTS.json",
    "NODE60_EXECUTION_PREPARATION.json",
    "BLOCKER_ACTIONS.md",
    "ARTIFACT_MANIFEST.json",
    "REPORT_KO.md",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _run_step(label: str, argv: list[str], expected_exit: int = 0, timeout: int = 240) -> dict[str, object]:
    env = {
        **os.environ,
        "OMP_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
        "NUMEXPR_NUM_THREADS": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPATH": ".:htt",
    }
    t0 = time.monotonic()
    proc = subprocess.run(argv, cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=timeout)
    dt = time.monotonic() - t0
    ok = proc.returncode == expected_exit
    out = {
        "label": label,
        "argv": argv,
        "expected_exit_code": expected_exit,
        "exit_code": proc.returncode,
        "elapsed_seconds": dt,
        "matched_expected_exit": ok,
        "stdout_tail": "\n".join(proc.stdout.splitlines()[-25:]),
        "stderr_tail": "\n".join(proc.stderr.splitlines()[-15:]),
    }
    if not ok:
        raise RuntimeError(f"Step {label} failed (rc={proc.returncode} != {expected_exit}):\n{proc.stdout}\n{proc.stderr}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.parse_args()
    started = time.monotonic()

    # 1. Verify frozen R99 code, test, and result hashes remain untouched
    r99_val = json.loads((R99_DIR / "VALIDATION.json").read_text())
    r99_mismatches = []
    for rel, exp in r99_val["code_and_tests_sha256"].items():
        act = sha256(ROOT / rel)
        if act != exp:
            r99_mismatches.append((rel, exp, act))
    for rel, exp in r99_val["result_artifact_sha256"].items():
        act = sha256(R99_DIR / rel)
        if act != exp:
            r99_mismatches.append((f"R99/{rel}", exp, act))
    if r99_mismatches:
        raise RuntimeError(f"Frozen R99 artifacts mutated: {r99_mismatches}")

    # 2. Verify claim firewalls across generated R100 JSON artifacts
    for name in (
        "CF4_UPSTREAM_KBAND_RESULTS.json",
        "RADIO_EXPOSURE_SELECTION_RESULTS.json",
        "GAIA_OPTICAL_JOINT_RESULTS.json",
        "BIANCHI_SELFCONSISTENT_AND_PHY_RESULTS.json",
    ):
        d = json.loads((OUT / name).read_text())
        if d.get("physical_Pi") is not None or d.get("physical_GF") is not None:
            raise RuntimeError(f"Claim firewall violation in {name}: physical_Pi={d.get('physical_Pi')}, physical_GF={d.get('physical_GF')}")

    # 3. Execute verification subprocesses
    runs = [
        _run_step(
            "r100_pytest_suite",
            [
                PY, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider",
                "tests/obsstat/test_r100_optical_drift.py",
                "tests/obsstat/test_r100_cf4.py",
                "tests/obsstat/test_r100_radio_exposure.py",
                "tests/obsstat/test_r100_gaia_optical.py",
                "tests/obsstat/test_r100_bianchi_phy.py",
                "tests/obsstat/test_r100_program_preparation.py",
            ],
            expected_exit=0,
        ),
        _run_step(
            "strict_science_authority",
            [PY, "-B", str(R78_DIR / "validate_unified.py"), "--strict-authority"],
            expected_exit=0,
        ),
        _run_step(
            "r100_preparation_check",
            [PY, "-B", "-m", "scripts.r100.program_preparation", "--check"],
            expected_exit=0,
        ),
        _run_step(
            "r100_science_fail_closed_sq_cf4",
            [PY, "-B", "-m", "scripts.r100.program_preparation", "science", "--node", "SQ-CF4"],
            expected_exit=3,
        ),
    ]

    # Ensure zero skipped tests in r100_pytest_suite
    pt_tail = runs[0]["stdout_tail"]
    if "skipped" in pt_tail.lower() or "failed" in pt_tail.lower():
        raise RuntimeError(f"R100 pytest suite had skips or failures: {pt_tail}")

    code_hashes = {rel: sha256(ROOT / rel) for rel in R100_CODE_AND_TESTS}
    result_hashes = {rel: sha256(OUT / rel) for rel in R100_RESULTS}

    report = {
        "schema": "htt.r100.bounded_validation/1",
        "checkout": str(ROOT),
        "r99_frozen_pins_intact": True,
        "science_authority_sha256": sha256(R78_DIR / "INTEGRATED_DAG.json"),
        "claim_firewall_verified": True,
        "code_and_tests_sha256": code_hashes,
        "result_artifact_sha256": result_hashes,
        "runs": runs,
        "environment": {
            "python": platform.python_version(),
            "threads": {k: os.getenv(k) for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS")},
        },
        "elapsed_seconds": time.monotonic() - started,
        "overall_pass": all(r["matched_expected_exit"] for r in runs),
    }
    (OUT / "VALIDATION.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"overall_pass": report["overall_pass"], "r100_pytest": pt_tail.splitlines()[-1], "elapsed_s": report["elapsed_seconds"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
