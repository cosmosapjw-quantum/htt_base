#!/usr/bin/env python3
"""Portable PR-270 focused, adjacent, smoke, and four-axis CAS runner."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


REPO = Path(__file__).resolve().parents[2]
SOURCE_PATHS = (REPO, REPO / "htt/src", REPO / "htt")
FOCUSED_TESTS = ("tests/contracts/test_pillar_t_cas.py",)
ADJACENT_TESTS = (
    "tests/contracts/test_pillar_t_core.py",
    "tests/contracts/test_theorem_signatures_v3.py",
    "tests/contracts/test_orbit_catalogue_v3.py",
    "tests/pr_cards/test_pr_255_anchored_response_geometry.py",
    "tests/pr_cards/test_pr_258_open_set_response_classes.py",
)
CONTRACT = (
    "docs/research_program/vector_tensor/cas/CAS_CONTRACT.json"
)
RUN_SPEC = (
    "docs/research_program/vector_tensor/cas/CAS_RUN_SPEC.json"
)
TRACKED_ADJUDICATION = (
    "docs/research_program/vector_tensor/cas/CAS_ADJUDICATION.json"
)


def _activate_source_layout() -> None:
    resolved = [str(path) for path in SOURCE_PATHS]
    sys.path[:] = resolved + [
        entry for entry in sys.path if entry not in resolved
    ]
    existing = [
        entry
        for entry in os.environ.get("PYTHONPATH", "").split(os.pathsep)
        if entry and entry not in resolved
    ]
    os.environ["PYTHONPATH"] = os.pathsep.join((*resolved, *existing))
    os.environ["PR270_PILLAR_T_CAS_RUNNER_ACTIVE"] = "1"


def _pytest(paths: tuple[str, ...]) -> int:
    import pytest

    return int(
        pytest.main(
            [
                "-p",
                "no:cacheprovider",
                "-q",
                *(str(REPO / path) for path in paths),
            ]
        )
    )


def _run_gate(*argv: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-B",
            str(REPO / ".agent-harness/scripts/cas_gate.py"),
            *argv,
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )


def _expected_four_axis_pass(payload: object) -> bool:
    if not isinstance(payload, dict):
        return False
    statuses = payload.get("axis_statuses")
    return (
        payload.get("aggregate_status") == "CAS_4AXIS_PASS"
        and payload.get("required_axes")
        == ["wolfram_xact", "sympy", "sage_singular", "lean"]
        and statuses
        == {
            "wolfram_xact": "PASS",
            "sympy": "PASS",
            "sage_singular": "PASS",
            "lean": "PASS",
        }
        and payload.get("claim_promotion_cas_eligible") is True
        and payload.get("claim_promotion_cas_requirement")
        == "SATISFIED"
    )


def _preflight() -> int:
    completed = _run_gate("preflight", "--all")
    if completed.returncode != 0:
        sys.stderr.write(completed.stdout + completed.stderr)
        return 1
    actual: dict[str, str] = {}
    for line in completed.stdout.splitlines():
        if ": " not in line:
            continue
        axis, status = line.split(": ", 1)
        actual[axis] = status
    expected = {
        "wolfram_xact": "PASS",
        "sympy": "PASS",
        "sage_singular": "PASS",
        "lean": "PASS",
    }
    if {axis: actual.get(axis) for axis in expected} != expected:
        sys.stderr.write(completed.stdout + completed.stderr)
        return 1
    return 0


def _adjudication_replay() -> int:
    tracked = json.loads(
        (REPO / TRACKED_ADJUDICATION).read_text(encoding="utf-8")
    )
    with tempfile.TemporaryDirectory(prefix="pr270-cas-") as temporary:
        output = Path(temporary) / "CAS_ADJUDICATION.json"
        completed = _run_gate(
            "run-adjudicate",
            "--contract",
            CONTRACT,
            "--run-spec",
            RUN_SPEC,
            "--out",
            str(output),
        )
        if completed.returncode != 0 or not output.is_file():
            sys.stderr.write(completed.stdout + completed.stderr)
            return 1
        replay = json.loads(output.read_text(encoding="utf-8"))
    if (
        not _expected_four_axis_pass(tracked)
        or not _expected_four_axis_pass(replay)
    ):
        sys.stderr.write(
            "tracked/replayed adjudication is not expected CAS_4AXIS_PASS\n"
        )
        return 1
    for field in (
        "schema_version",
        "contract_id",
        "contract_sha256",
        "risk_tier",
        "required_axes",
        "axis_statuses",
        "verification_state",
        "evidence_origin",
        "claim_promotion_cas_eligible",
        "claim_promotion_cas_requirement",
    ):
        if tracked.get(field) != replay.get(field):
            sys.stderr.write(f"adjudication replay drifted at {field}\n")
            return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "mode",
        choices=("focused", "adjacent", "smoke", "preflight", "adjudication"),
    )
    args = parser.parse_args(argv)
    _activate_source_layout()
    if args.mode == "focused":
        return _pytest(FOCUSED_TESTS)
    if args.mode == "adjacent":
        return _pytest(ADJACENT_TESTS)
    if args.mode == "preflight":
        return _preflight()
    if args.mode == "adjudication":
        return _adjudication_replay()
    import pytest

    return int(pytest.main(["-p", "no:cacheprovider", "-q", "-m", "smoke"]))


if __name__ == "__main__":
    raise SystemExit(main())
