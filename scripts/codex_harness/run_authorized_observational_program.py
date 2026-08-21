#!/usr/bin/env python3
"""One-command, fail-closed dispatcher for the registered observed-data program.

``--check`` is always read-only and reports every canonical runbook lane.
``--execute-authorized`` is deliberately all-or-nothing: it runs the checked-in
human-gated integration entrypoints only after every included lane has a real
entrypoint, terminal dependencies, and its own current human authorization.
It never downloads data, synthesizes an authorization, or treats a blocked lane
as a zero-filled contribution.
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path
import shlex
import subprocess
from typing import Mapping, Sequence

import yaml


ROOT = Path(__file__).resolve().parents[2]
RUNBOOKS = ROOT / "docs/research_program/post_pr275/data_runbooks.yaml"
BACKLOG = ROOT / "docs/codex_handoff/pr_backlog.yaml"
STATUS = ROOT / "docs/codex_handoff/pr_status.yaml"


class ObservationalProgramError(RuntimeError):
    """Raised for an invalid checked-in observational-program declaration."""


@dataclass(frozen=True)
class ProgramLane:
    lane: str
    authorization_gate: str
    owner_pr: str
    entrypoint: tuple[str, ...] | None
    status: str
    blocked_reasons: tuple[str, ...]


def _mapping(path: Path) -> dict[str, object]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ObservationalProgramError(f"{path} must be a mapping")
    return payload


def _cards(backlog: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    raw_cards = backlog.get("prs")
    if not isinstance(raw_cards, list):
        raise ObservationalProgramError("canonical backlog omits prs")
    cards: dict[str, Mapping[str, object]] = {}
    for raw in raw_cards:
        if not isinstance(raw, Mapping) or not isinstance(raw.get("id"), str):
            raise ObservationalProgramError("canonical backlog has a malformed PR card")
        card_id = raw["id"]
        if card_id in cards:
            raise ObservationalProgramError(f"duplicate PR card: {card_id}")
        cards[card_id] = raw
    return cards


def _human_gated_entrypoint(card: Mapping[str, object]) -> tuple[str, ...] | None:
    raw_tests = card.get("tests")
    if not isinstance(raw_tests, list):
        raise ObservationalProgramError(f"{card.get('id')} has no test declaration")
    declared = [item for item in raw_tests if isinstance(item, str) and item.startswith("human-gated:")]
    if len(declared) > 1:
        raise ObservationalProgramError(f"{card.get('id')} declares multiple human-gated entrypoints")
    if declared:
        return tuple(shlex.split(declared[0].split(":", 1)[1].strip()))
    if any(isinstance(item, str) and item.startswith("to-be-created:") for item in raw_tests):
        return None
    return None


def _entrypoint_exists(argv: Sequence[str]) -> bool:
    for token in argv:
        if token.endswith(".py") or token.startswith("tests/"):
            if not (ROOT / token).is_file():
                return False
    return True


def _command_and_environment(argv: Sequence[str]) -> tuple[tuple[str, ...], dict[str, str]]:
    """Parse only leading ``NAME=value`` declarations; never invoke a shell."""

    environment = dict(os.environ)
    position = 0
    for token in argv:
        name, separator, value = token.partition("=")
        if not separator or not name.replace("_", "").isalnum() or name[0].isdigit():
            break
        environment[name] = value
        position += 1
    command = tuple(argv[position:])
    if not command:
        raise ObservationalProgramError("human-gated entrypoint has no executable argv")
    return command, environment


def _dependency_reasons(card: Mapping[str, object], resolutions: Mapping[str, object]) -> tuple[str, ...]:
    owner_pr = card.get("id")
    dependencies = card.get("depends", [])
    if not isinstance(dependencies, list):
        raise ObservationalProgramError(f"{owner_pr} has malformed dependencies")
    reasons: list[str] = []
    for dependency in dependencies:
        if not isinstance(dependency, str) or dependency == owner_pr:
            continue
        resolution = resolutions.get(dependency)
        if not isinstance(resolution, Mapping) or resolution.get("resolution") not in {
            "COMPLETED_SUCCESS",
            "COMPLETED_FAILED_WITH_RECEIPT",
            "BLOCKED_WITH_RECEIPT",
        }:
            reasons.append(f"upstream_not_terminal:{dependency}")
    return tuple(reasons)


def _pr151_is_invalidated(status: Mapping[str, object]) -> bool:
    amendment = status.get("wave19_amendment")
    entry = amendment.get("PR-151") if isinstance(amendment, Mapping) else None
    return isinstance(entry, Mapping) and entry.get("execution_state") == (
        "invalidated_pending_formalism_revalidation"
    )


def build_program(
    *,
    runbooks_path: Path = RUNBOOKS,
    backlog_path: Path = BACKLOG,
    status_path: Path = STATUS,
) -> tuple[ProgramLane, ...]:
    """Build the full program without importing an analysis producer."""

    runbooks = _mapping(runbooks_path)
    backlog = _mapping(backlog_path)
    status = _mapping(status_path)
    cards = _cards(backlog)
    external_events = status.get("external_events")
    resolutions = status.get("execution_resolutions", {})
    if not isinstance(external_events, Mapping) or not isinstance(resolutions, Mapping):
        raise ObservationalProgramError("status lacks external events or execution resolutions")
    raw_runbooks = runbooks.get("runbooks")
    if not isinstance(raw_runbooks, list):
        raise ObservationalProgramError("data runbooks omit runbooks")

    lanes: list[ProgramLane] = []
    seen_lanes: set[str] = set()
    for raw in raw_runbooks:
        if not isinstance(raw, Mapping):
            raise ObservationalProgramError("malformed data runbook")
        lane = raw.get("lane")
        owner_pr = raw.get("owner_pr")
        gate = raw.get("execution_authorization_gate")
        if not all(isinstance(value, str) and value for value in (lane, owner_pr, gate)):
            raise ObservationalProgramError("runbook omits lane, owner PR, or authorization gate")
        if lane in seen_lanes:
            raise ObservationalProgramError(f"duplicate runbook lane: {lane}")
        seen_lanes.add(lane)
        if owner_pr not in cards:
            raise ObservationalProgramError(f"runbook owner PR is absent from canonical backlog: {owner_pr}")
        card = cards[owner_pr]
        entrypoint = _human_gated_entrypoint(card)
        reasons: list[str] = []
        if owner_pr == "PR-151" or (lane == "DESI" and _pr151_is_invalidated(status)):
            reasons.append("pr151_formalism_revalidation_required")
        if entrypoint is None:
            reasons.append("execution_entrypoint_not_implemented")
        elif not _entrypoint_exists(entrypoint):
            reasons.append("execution_entrypoint_path_missing")
        gate_status = external_events.get(gate)
        if not isinstance(gate_status, Mapping) or gate_status.get("status") != "AUTHORIZED":
            reasons.append(f"human_authorization_not_current:{gate}")
        reasons.extend(_dependency_reasons(card, resolutions))
        lanes.append(
            ProgramLane(
                lane=lane,
                authorization_gate=gate,
                owner_pr=owner_pr,
                entrypoint=entrypoint,
                status="READY_FOR_MANUAL_EXECUTION" if not reasons else "BLOCKED",
                blocked_reasons=tuple(reasons),
            )
        )
    if tuple(item.lane for item in lanes) != (
        "PLANCK",
        "CF4",
        "HSC_KIDS",
        "ACT",
        "DESI",
        "JWST_SN",
        "CROSS_PROBE",
    ):
        raise ObservationalProgramError("canonical observed-lane inventory drifted")
    return tuple(lanes)


def payload(lanes: Sequence[ProgramLane]) -> dict[str, object]:
    return {
        "schema": "htt.authorized_observational_program.v1",
        "observed_data_executed": False,
        "artifact_mode": "readiness_only",
        "one_command": "PYTHONPATH=htt/src:htt/htt venv/bin/python -B scripts/codex_harness/run_authorized_observational_program.py --execute-authorized",
        "lanes": [
            {
                "lane": item.lane,
                "authorization_gate": item.authorization_gate,
                "owner_pr": item.owner_pr,
                "entrypoint": list(item.entrypoint) if item.entrypoint else None,
                "status": item.status,
                "blocked_reasons": list(item.blocked_reasons),
            }
            for item in lanes
        ],
    }


def execute_authorized(lanes: Sequence[ProgramLane]) -> int:
    """Run the reviewed entrypoints only after the all-lane preflight is READY."""

    if any(item.status != "READY_FOR_MANUAL_EXECUTION" for item in lanes):
        return 3
    for lane in lanes:
        assert lane.entrypoint is not None
        command, environment = _command_and_environment(lane.entrypoint)
        result = subprocess.run(command, cwd=ROOT, env=environment, check=False)
        if result.returncode:
            return result.returncode
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--execute-authorized", action="store_true")
    args = parser.parse_args(argv)
    lanes = build_program()
    print(json.dumps(payload(lanes), sort_keys=True))
    return execute_authorized(lanes) if args.execute_authorized else 0


if __name__ == "__main__":
    raise SystemExit(main())
