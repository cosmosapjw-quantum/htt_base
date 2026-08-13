#!/usr/bin/env python3
"""Fail-closed oracle for the A-PR286-R3-CLAIM isolation incident.

This oracle validates only the procedural classification.  It does not inspect
or adjudicate either assigned scientific claim.
"""

from __future__ import annotations

import json
from pathlib import Path


RUN_ID = "pr286-mio-nonfinite-r3-rereview-20260811"
ASSIGNMENT_ID = "A-PR286-R3-CLAIM"
CONTEXT_VERSION = (
    "e9b385d7fbc4f8e47c97c3b0c7edae4e522d9be4e025d9342e26ab24829e3019"
)


def main() -> int:
    repo = Path(__file__).resolve().parents[4]
    assignment_path = (
        repo
        / ".agent-harness"
        / "runs"
        / RUN_ID
        / "assignments"
        / f"{ASSIGNMENT_ID}.json"
    )
    assignment = json.loads(assignment_path.read_text(encoding="utf-8"))
    assert assignment["assignment_id"] == ASSIGNMENT_ID
    assert assignment["context_version"] == CONTEXT_VERSION
    assert assignment["independence_mode"] == "blind-results"
    assert assignment["allowed_sibling_results"] == []
    assert assignment["may_spawn"] is False
    assert set(assignment["claim_ids"]) == {
        "C-PR273-BLIND-INTEGRATION",
        "C-PR274-DATA-ADMISSION",
    }
    print(
        json.dumps(
            {
                "assignment_id": ASSIGNMENT_ID,
                "classification": "BLIND_RESULTS_ISOLATION_BREACH",
                "required_disposition": "ERROR_NO_CLAIM_VERDICT",
                "assurance_extension_authorized": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
