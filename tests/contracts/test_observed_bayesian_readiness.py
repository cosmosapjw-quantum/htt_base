from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "scripts/codex_harness/check_observed_bayesian_readiness.py"


def test_readiness_runner_is_read_only_and_reports_every_registered_lane() -> None:
    module_spec = importlib.util.spec_from_file_location("pr299_readiness", RUNNER)
    assert module_spec is not None and module_spec.loader is not None
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    payload = module.build_payload()
    assert payload["observed_data_executed"] is False
    assert payload["artifact_mode"] == "readiness_only"
    assert [row["lane_id"] for row in payload["lanes"]] == ["H-PLANCK", "H-DESI", "H-CF4", "H-JWST", "H-ACT"]
    assert {row["status"] for row in payload["lanes"]} == {"BLOCKED_PRODUCTION_MODEL_CONTRACT_UNBOUND"}
