"""Shared non-payload CLI surface for future lane-owned observed-run executors.

The repository has no admitted observed inputs or registered lane backends at
this revision.  These commands therefore provide inspectable plans and reject
execution before any payload import, rather than pretending a pytest node is a
production analysis program.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence


PRIMARY_LANES = ("PLANCK", "CF4", "HSC_KIDS", "ACT", "DESI", "JWST_SN")
ALL_LANES = PRIMARY_LANES + ("CROSS_PROBE",)


class ObservedLaneExecutionBlocked(RuntimeError):
    """The lane has no accepted backend/input authorization at this revision."""


def plan(lane: str) -> dict[str, object]:
    if lane not in ALL_LANES:
        raise ObservedLaneExecutionBlocked(f"unknown observed lane: {lane}")
    return {
        "schema": "htt.observed_lane_cli_plan.v1",
        "lane": lane,
        "observed_data_executed": False,
        "payload_access": False,
        "network_access": False,
        "execution_state": "BLOCKED_NO_ADMITTED_LANE_BACKEND",
        "cross_probe_phase": "phase_b_only" if lane == "CROSS_PROBE" else "phase_a_primary",
    }


def main_for_lane(lane: str, argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--plan", action="store_true")
    mode.add_argument("--validate-inputs", action="store_true")
    mode.add_argument("--execute", action="store_true")
    mode.add_argument("--resume", action="store_true")
    parser.add_argument("--run-id")
    parser.add_argument("--authorization-receipt", type=Path)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args(argv)
    result = plan(lane)
    print(json.dumps(result, sort_keys=True))
    if args.plan:
        return 0
    if args.validate_inputs:
        return 3
    if not args.authorization_receipt or not args.output_dir or not args.run_id:
        raise ObservedLaneExecutionBlocked("execution requires run id, external receipt, and output directory")
    raise ObservedLaneExecutionBlocked(
        "no lane-owned observed backend has passed admission/formalism validation; no payload was opened"
    )
