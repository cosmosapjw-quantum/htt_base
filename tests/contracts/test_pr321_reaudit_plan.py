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
        "canonical_DAG_changed": False,
        "contract_failure_classes": {"P0": 2, "P1": 8},
        "generated_result_terminal": (
            "READY_FOR_PREREGISTERED_FIDUCIAL_WINDOW_CONVOLVED_REFERENCE"
        ),
        "guards_present": 10,
        "schema": "htt.pr321.reaudit.plan_validation.v2",
        "science_repair_executed": True,
        "status": "PASS",
    }

def test_pr321_reaudit_handoff_preserves_mes_boundary() -> None:
    text = (
        ROOT / "docs/codex_handoff/pr321_reaudit/CODEX_HANDOFF.md"
    ).read_text(encoding="utf-8")
    assert "SCALAR_TOMOGRAPHIC_CONTROL_ONLY" in text
    assert "NONE_COMPRESSED_ROTATION_INVARIANT_POWER_SPECTRA" in text
    assert "PROJECTED_OUT_IN_TOMOGRAPHIC_CL_EE" not in text
    assert "FORBIDDEN_NO_DIRECTION_INDEXED_FIELD" in text
    assert "NOT_APPLICABLE_NO_DIRECTIONAL_RESPONSE" in text
    assert "BLOCKED_CROSS_CHANNEL_NO_PHYSICAL_TRANSFER" in text
    assert "fiducial_vector_length: 60" in text
    assert "claim_unexecuted_rerun: forbidden" in text
