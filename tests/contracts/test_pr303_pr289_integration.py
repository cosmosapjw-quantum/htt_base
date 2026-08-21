"""PR-303 integration must retain both exact admission bytes and quarantine."""
from __future__ import annotations

import ast
import importlib.util
import json
from pathlib import Path
import subprocess
import sys


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


def test_pr303_rejects_reappearance_of_the_stale_pr289_receipt() -> None:
    module = _runner()
    stale = ROOT / module.STALE_RECEIPT
    assert not stale.exists()
    stale.write_text("{}\n", encoding="utf-8")
    try:
        try:
            module.build_payload()
        except RuntimeError as exc:
            assert "STALE_PR289_CANDIDATE_RECEIPT_PRESENT" in str(exc)
        else:
            raise AssertionError("stale PR-289 receipt was accepted")
    finally:
        stale.unlink()
