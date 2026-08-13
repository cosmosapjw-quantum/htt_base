#!/usr/bin/env python3
"""Fail-closed oracle for the A-PR287-FROZEN-REPLAY-R2 independence stop."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
RUN_ID = "pr287-fresh-independent-review-20260811"
ASSIGNMENT_ID = "A-PR287-FROZEN-REPLAY-R2"
ARTIFACT_DIR = ROOT / ".agent-harness" / "runs" / RUN_ID / "artifacts" / ASSIGNMENT_ID


def main() -> int:
    assignment_path = ROOT / ".agent-harness" / "runs" / RUN_ID / "assignments" / f"{ASSIGNMENT_ID}.json"
    context_path = ROOT / ".agent-harness" / "context" / "CONTEXT_INDEX.json"
    incident_path = ARTIFACT_DIR / "INDEPENDENCE_INCIDENT.json"

    assignment = json.loads(assignment_path.read_text(encoding="utf-8"))
    context = json.loads(context_path.read_text(encoding="utf-8"))
    incident = json.loads(incident_path.read_text(encoding="utf-8"))

    assert assignment["run_id"] == RUN_ID
    assert assignment["assignment_id"] == ASSIGNMENT_ID
    assert assignment["independence_mode"] == "blind-results"
    assert assignment["context_version"] == context["context_version"]
    for required in assignment["required_inputs"]:
        payload = (ROOT / required["path"]).read_bytes()
        assert hashlib.sha256(payload).hexdigest() == required["sha256"]

    assert incident["prohibited_surface_exposed"] == "other_agent_output"
    assert incident["results_directory_inspected"] is False
    assert incident["process_command_lines_inspected"] is False
    assert incident["policy_cells_executed_after_incident"] is False
    assert incident["substantive_verdict_issued"] is False
    assert incident["terminal_disposition"] == "INCONCLUSIVE"
    print(json.dumps({
        "assignment_id": ASSIGNMENT_ID,
        "context_and_required_inputs": "PASS",
        "independence_contract": "CONTAMINATED_STOP",
        "terminal_disposition": "INCONCLUSIVE",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
