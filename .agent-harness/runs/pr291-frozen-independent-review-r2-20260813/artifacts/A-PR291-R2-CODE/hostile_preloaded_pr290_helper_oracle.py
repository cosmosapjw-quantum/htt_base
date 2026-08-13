#!/usr/bin/env python3
"""Demonstrate whether PR-291 binds the imported PR-290 transaction helpers.

This intentionally runs only inside the registered assignment artifacts.  It
preloads a forged ``run_pr290_planck_lane`` before loading the PR-291 runner,
then asks ``_write`` to target a path outside the candidate root.  A secure
runner must reject that request before payload generation.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import types


ROOT = Path("/home/cosmosapjw/worktrees/htt-process-inflation-recovery-pr283-20260810")
ARTIFACT_DIR = Path(__file__).resolve().parent
OUTPUT = ARTIFACT_DIR / "forged_helper_outside_root.json"
RUNNER_PATH = ROOT / "scripts/codex_harness/run_pr291_cf4_lane.py"


def main() -> int:
    marker: list[str] = []
    fake = types.ModuleType("run_pr290_planck_lane")

    def fake_validate_output_destinations(**_kwargs: object) -> None:
        marker.append("forged_validate_called")

    def fake_atomic_write(output: Path, payload: bytes, **_kwargs: object) -> None:
        marker.append("forged_atomic_write_called")
        output.write_bytes(payload)

    fake._validate_output_destinations = fake_validate_output_destinations
    fake._atomic_write = fake_atomic_write
    fake._encoded = lambda payload: json.dumps(
        payload, sort_keys=True, separators=(",", ":")
    ).encode("ascii")
    fake._tracked_manifest = lambda *_args, **_kwargs: {}
    fake._tracked_paths = lambda *_args, **_kwargs: ()

    original = sys.modules.get("run_pr290_planck_lane")
    sys.modules["run_pr290_planck_lane"] = fake
    try:
        spec = importlib.util.spec_from_file_location("pr291_hostile_runner", RUNNER_PATH)
        assert spec is not None and spec.loader is not None
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        if OUTPUT.exists():
            OUTPUT.unlink()
        exit_code = runner._write(root=ROOT, output=OUTPUT)
    finally:
        if original is None:
            sys.modules.pop("run_pr290_planck_lane", None)
        else:
            sys.modules["run_pr290_planck_lane"] = original

    report = {
        "oracle": "preloaded_pr290_transaction_helper_substitution",
        "exit_code": exit_code,
        "forged_helper_calls": marker,
        "outside_root_output_exists": OUTPUT.exists(),
        "outside_root_output_terminal": (
            json.loads(OUTPUT.read_text(encoding="ascii")).get("terminal")
            if OUTPUT.exists()
            else None
        ),
        "expected_secure_outcome": "reject before payload generation",
        "verdict": "VULNERABLE"
        if exit_code == 0 and "forged_atomic_write_called" in marker and OUTPUT.exists()
        else "NOT_DEMONSTRATED",
    }
    print(json.dumps(report, sort_keys=True))
    return 0 if report["verdict"] == "VULNERABLE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
