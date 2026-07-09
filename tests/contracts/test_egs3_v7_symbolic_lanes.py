"""Contract: the EGS3 v7 symbolic-seal lanes (Sage / Lean / Wolfram) are present,
current, and PASS. Each engine-backed re-run is skipped when the engine is absent
(the runner returns exit 2 = registered blocker), so this suite is green on hosts
without Sage/Lean/Wolfram while still enforcing artifact currency where they exist.
"""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
GEN = ROOT / "docs/generated"


def _load(name: str) -> dict:
    path = GEN / name
    assert path.exists(), f"missing v7 seal artifact {path} (run make v7-seals)"
    return json.loads(path.read_text(encoding="utf-8"))


def test_sage_seal_artifact_pass():
    payload = _load("egs3_sage_seal.json")
    assert payload["status"] == "PASS"
    assert payload["checks"], "empty check set"
    assert all(v is True for v in payload["checks"].values())
    # F1 / T1' exact endpoints reproduced in exact rational arithmetic
    assert payload["endpoints"]["open_branch"] == ["11/100", "17/100"]
    assert payload["endpoints"]["all_branch"] == ["9/100", "17/100"]


def test_lean_seal_artifact_pass():
    payload = _load("egs3_lean_seal.json")
    assert payload["status"] == "PASS"
    assert payload["checks"]
    assert all(v is True for v in payload["checks"].values())
    for key in ("open_branch_lo_11_100", "all_branch_lo_9_100", "dl1_lower_gap_2_100",
                "promote_blocks_on_false"):
        assert payload["checks"].get(key) is True


def test_wolfram_v7_seal_artifact_pass():
    payload = _load("egs3_v7_wolfram_proofs.json")
    assert payload["status"] == "PASS"
    results = payload.get("results", [])
    assert results, "no Wolfram results recorded"
    checks = results[0]["result"]["checks"]
    assert all(v is True for v in checks.values())
    assert checks["hotelling_F_threshold_exceeds_chi2"] is True
    assert checks["uncorrected_chi2_size_exceeds_alpha"] is True


@pytest.mark.skipif(shutil.which("sage") is None, reason="SageMath not installed")
def test_sage_lane_check_mode_current():
    r = subprocess.run([sys.executable, "scripts/run_egs3_sage_seals.py", "--check"],
                       cwd=ROOT, text=True, capture_output=True, timeout=1200)
    assert r.returncode == 0, r.stdout + r.stderr


@pytest.mark.skipif(shutil.which("lake") is None, reason="Lean/lake not installed")
def test_lean_lane_check_mode_current():
    r = subprocess.run([sys.executable, "scripts/run_egs3_lean_seals.py", "--check"],
                       cwd=ROOT, text=True, capture_output=True, timeout=900)
    assert r.returncode == 0, r.stdout + r.stderr
