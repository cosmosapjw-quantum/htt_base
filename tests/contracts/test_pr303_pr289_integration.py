"""PR-303 integration must retain both exact admission bytes and quarantine."""
from __future__ import annotations

import ast
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "scripts/codex_harness/run_pr303_pr289_integration.py"


def _runner():
    spec = importlib.util.spec_from_file_location("pr303_runner", RUNNER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_pr303_receipt_is_a_zero_execution_integration_only_result() -> None:
    payload = _runner().build_payload()
    assert payload["terminal"] == "PASS_PR289_PR300_INTEGRATION_ONLY"
    assert len(payload["exact_pr289_source_hashes"]) == 7
    assert payload["refused_lane_statuses"] == {
        lane: "REJECTED_NOT_PRESENT" for lane in _runner().EXPECTED_ROOTLESS_LANES
    }
    assert payload["not_authorized_lane_ids"] == list(
        _runner().EXPECTED_ROOTLESS_LANES
    )
    assert payload["admitted_lane_count"] == 0
    assert payload["authorized_lane_count"] == 0
    assert payload["executed_lane_count"] == 0
    assert payload["observed_data_executed"] is False
    assert payload["scientific_effect"] == "none"
    assert payload["authorization_successor_present"] is False
    assert payload["pr151_withdrawn_artifacts_absent"] is True


def test_pr303_receipt_write_is_atomic_and_confined_to_the_requested_output(tmp_path: Path) -> None:
    output = tmp_path / "receipt.json"
    command = (sys.executable, "-B", str(RUNNER), "--write", "--output", str(output))
    written = subprocess.run(command, check=True, capture_output=True, text=True)
    payload = json.loads(written.stdout)
    assert json.loads(output.read_text(encoding="utf-8")) == payload
    assert {path.name for path in tmp_path.iterdir()} == {"receipt.json"}
    checked = subprocess.run(
        (sys.executable, "-B", str(RUNNER), "--check", "--output", str(output)),
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(checked.stdout) == payload


def test_pr303_runner_has_no_network_or_subprocess_execution_surface() -> None:
    tree = ast.parse(RUNNER.read_text(encoding="utf-8"))
    forbidden = {"socket", "subprocess", "urllib", "requests", "http", "ftplib"}
    imports = {
        alias.name.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    assert not imports & forbidden


def test_pr303_rejects_reappearance_of_the_stale_pr289_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _runner()
    stale = tmp_path / "pr289_data_identity_v2_receipt.json"
    stale.write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(module, "STALE_RECEIPT", stale)
    with pytest.raises(RuntimeError, match="STALE_PR289_CANDIDATE_RECEIPT_PRESENT"):
        module.build_payload()


def test_pr303_rejects_a_noncanonical_rootless_refusal() -> None:
    module = _runner()
    pr289 = module._load_exact_pr289_runner(ROOT)
    preflight = deepcopy(pr289._build(ROOT))
    preflight["lane_decisions"][0]["status"] = "REJECTED_IDENTITY_MISMATCH"

    with pytest.raises(RuntimeError, match="PR289_NONCANONICAL_ROOTLESS_REFUSAL"):
        module._validate_rootless_preflight(preflight)


def test_pr303_rejects_a_refusal_authorization_with_record_ids() -> None:
    module = _runner()
    pr289 = module._load_exact_pr289_runner(ROOT)
    preflight = deepcopy(pr289._build(ROOT))
    preflight["authorization_receipts"][0]["exact_admission_record_ids"] = [
        "record-that-must-not-survive-rootless-refusal"
    ]

    with pytest.raises(RuntimeError, match="PR289_REFUSAL_AUTH_RETAINED_RECORD_IDS"):
        module._validate_rootless_preflight(preflight)
