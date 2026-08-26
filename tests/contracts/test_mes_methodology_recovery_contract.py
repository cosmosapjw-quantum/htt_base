from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def test_mes_methodology_recovery_contract_validator_passes() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/validate_mes_methodology_recovery_contract.py", "--json"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["status"] == "PASS"
    assert payload["canonical_DAG_changed"] is False
    assert payload["science_code_changed"] is False
    assert payload["work_units"] == [f"MR-WU-{index:03d}" for index in range(9)]
    assert payload["failure_modes"] == 13


def test_recovery_package_is_planning_only() -> None:
    index = (
        ROOT / "docs/codex_handoff/mes_methodology_recovery/PACKAGE_INDEX.yaml"
    ).read_text(encoding="utf-8")
    assert "canonical_DAG_changed: false" in index
    assert "science_code_changed: false" in index
    assert "observed_data_executed: false" in index


def test_handoff_forbids_core_scientific_drift() -> None:
    handoff = (
        ROOT / "docs/codex_handoff/mes_methodology_recovery/CODEX_HANDOFF.md"
    ).read_text(encoding="utf-8").lower()
    for required in (
        "generic planck low-ell 12-feature rank is a frozen benchmark control",
        "do not reactivate `htt/bass/observational/planck_mes_bounds.py`",
        "do not infer a vector, axis or tensor orientation from scalar mes values",
        "do not identify local boost versus global tilt from one shell",
    ):
        assert required in handoff
