from __future__ import annotations
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]

def test_pr321_reaudit_package_is_machine_valid() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/validate_pr321_reaudit_plan.py"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload == {
        "P0": 0,
        "P1": 6,
        "canonical_DAG_changed": False,
        "schema": "htt.pr321.reaudit.plan_validation.v1",
        "science_repair_executed": False,
        "status": "PASS",
    }

def test_pr321_reaudit_handoff_preserves_mes_boundary() -> None:
    text = (
        ROOT / "docs/codex_handoff/pr321_reaudit/CODEX_HANDOFF.md"
    ).read_text(encoding="utf-8")
    assert "SCALAR_TOMOGRAPHIC_CONTROL_ONLY" in text
    assert "PROJECTED_OUT_IN_TOMOGRAPHIC_CL_EE" in text
    assert "fiducial_vector_length: 60" in text
    assert "claim_unexecuted_rerun: forbidden" in text
