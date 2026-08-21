from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/codex_harness/run_authorized_observational_program.py"


def _program_module():
    spec = importlib.util.spec_from_file_location("authorized_program", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_DISP_008_to_011_cross_probe_is_phase_b_and_aliases_are_rejected() -> None:
    module = _program_module()
    lanes = module.build_program()
    assert tuple(item.lane for item in lanes if item.phase == "phase_a") == module.PRIMARY
    assert lanes[-1].lane == "CROSS_PROBE"
    assert lanes[-1].authorization_gate == "H-PR294-SCHEDULE"
    assert module.main(["--check-strict"]) == 3


def test_DISP_005_and_006_dependency_drift_is_a_hard_error(tmp_path: Path) -> None:
    module = _program_module()
    runbooks = yaml.safe_load((ROOT / "docs/research_program/post_pr275/data_runbooks.yaml").read_text())
    runbooks["runbooks"][0]["dependencies"].append("PR-290")
    changed = tmp_path / "runbooks.yaml"
    changed.write_text(yaml.safe_dump(runbooks), encoding="utf-8")
    with pytest.raises(module.ObservationalProgramError, match="dependency"):
        module.build_program(runbooks_path=changed)


@pytest.mark.parametrize("script", tuple(sorted((ROOT / "scripts/observed_runs").glob("run_*.py"))))
def test_DISP_001_to_004_lane_clis_have_side_effect_free_plan_mode(script: Path) -> None:
    result = subprocess.run((sys.executable, "-B", str(script), "--plan"), check=False, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["payload_access"] is False
    assert payload["network_access"] is False
    assert payload["observed_data_executed"] is False
