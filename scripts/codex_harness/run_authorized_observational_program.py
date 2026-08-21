#!/usr/bin/env python3
"""Structural, non-executing preflight for the observed-lane program.

This is intentionally not an authorization issuer and does not interpret a
status string as an execution grant.  It verifies the phase-A lane vocabulary
and reports the present hard block: no lane backend/input admission is ready.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

import yaml


ROOT = Path(__file__).resolve().parents[2]
RUNBOOKS = ROOT / "docs/research_program/post_pr275/data_runbooks.yaml"
BACKLOG = ROOT / "docs/codex_handoff/pr_backlog.yaml"
PRIMARY = ("PLANCK", "CF4", "HSC_KIDS", "ACT", "DESI", "JWST_SN")
ALL = PRIMARY + ("CROSS_PROBE",)
EXPECTED_GATES = ("H-PLANCK", "H-CF4", "H-HSC-KiDS", "H-ACT", "H-DESI", "H-JWST", "H-PR294-SCHEDULE")


class ObservationalProgramError(RuntimeError):
    """The checked-in route is malformed or attempts to bypass authorization."""


@dataclass(frozen=True)
class ProgramLane:
    lane: str
    authorization_gate: str
    owner_pr: str
    phase: str
    status: str
    blocked_reasons: tuple[str, ...]


def _mapping(path: Path) -> Mapping[str, object]:
    if path.is_symlink() or not path.is_file():
        raise ObservationalProgramError(f"required regular file missing: {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ObservationalProgramError(f"malformed YAML: {path}") from exc
    if not isinstance(data, Mapping):
        raise ObservationalProgramError(f"YAML mapping required: {path}")
    return data


def _backlog_cards(backlog: Mapping[str, object]) -> Mapping[str, Mapping[str, object]]:
    raw = backlog.get("prs")
    if not isinstance(raw, list):
        raise ObservationalProgramError("backlog has no PR cards")
    cards: dict[str, Mapping[str, object]] = {}
    for card in raw:
        if not isinstance(card, Mapping) or not isinstance(card.get("id"), str) or card["id"] in cards:
            raise ObservationalProgramError("backlog contains malformed or duplicate PR cards")
        cards[card["id"]] = card
    return cards


def build_program(*, runbooks_path: Path = RUNBOOKS, backlog_path: Path = BACKLOG) -> tuple[ProgramLane, ...]:
    runbooks, cards = _mapping(runbooks_path), _backlog_cards(_mapping(backlog_path))
    raw_rows = runbooks.get("runbooks")
    if not isinstance(raw_rows, list):
        raise ObservationalProgramError("runbook inventory is not a list")
    rows: list[ProgramLane] = []
    for row in raw_rows:
        if not isinstance(row, Mapping):
            raise ObservationalProgramError("runbook row is malformed")
        lane, owner, gate, deps = row.get("lane"), row.get("owner_pr"), row.get("execution_authorization_gate"), row.get("dependencies")
        if not all(isinstance(item, str) and item for item in (lane, owner, gate)) or not isinstance(deps, list):
            raise ObservationalProgramError("runbook lacks exact lane/owner/gate/dependencies")
        if lane not in ALL or owner not in cards or any(not isinstance(item, str) or not item or item == owner for item in deps):
            raise ObservationalProgramError("runbook dependency contains unknown, self, or malformed semantic identity")
        if tuple(cards[owner].get("depends", ())) != tuple(deps):
            raise ObservationalProgramError(f"runbook/backlog dependency mismatch for {lane}")
        rows.append(ProgramLane(lane, gate, owner, "phase_b" if lane == "CROSS_PROBE" else "phase_a", "BLOCKED", ("no_admitted_lane_backend_or_external_authorization",)))
    if tuple(row.lane for row in rows) != ALL:
        raise ObservationalProgramError("canonical observed-lane order drifted")
    actual_gates = tuple(row.authorization_gate for row in rows)
    if actual_gates != EXPECTED_GATES:
        raise ObservationalProgramError("authorization gate vocabulary drifted; aliases are forbidden")
    return tuple(rows)


def payload(lanes: Sequence[ProgramLane]) -> dict[str, object]:
    return {
        "schema": "htt.authorized_observational_program.v2",
        "observed_data_executed": False,
        "artifact_mode": "structural_preflight_only",
        "phase_a_lanes": list(PRIMARY),
        "phase_b": {"lane": "CROSS_PROBE", "requires_separate_pr294_schedule_authorization": True},
        "lanes": [item.__dict__ | {"blocked_reasons": list(item.blocked_reasons)} for item in lanes],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--check-strict", action="store_true")
    mode.add_argument("--execute-authorized", action="store_true")
    args = parser.parse_args(argv)
    lanes = build_program()
    print(json.dumps(payload(lanes), sort_keys=True))
    if args.check:
        return 0
    if args.check_strict:
        return 3 if any(row.status != "READY" for row in lanes if row.phase == "phase_a") else 0
    raise ObservationalProgramError(
        "execution is unavailable: this revision has no admitted backend, externally validated receipt, or observed payload access"
    )


if __name__ == "__main__":
    raise SystemExit(main())
