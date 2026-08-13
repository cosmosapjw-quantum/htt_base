#!/usr/bin/env python3
"""Verify the frozen assignment binding after an independence incident.

This oracle deliberately makes no scientific or publication-readiness verdict.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
RUN_ID = "pr289-frozen-independent-review-20260811"
ASSIGNMENT_ID = "A-PR289-FROZEN-PHYSSTAT"
CONTEXT_VERSION = "e9b385d7fbc4f8e47c97c3b0c7edae4e522d9be4e025d9342e26ab24829e3019"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: object, *, omit: set[str] = set()) -> str:
    if isinstance(value, dict):
        value = {key: item for key, item in value.items() if key not in omit}
    raw = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    return hashlib.sha256(raw).hexdigest()


def assignment_sha256(value: dict[str, object]) -> str:
    payload = dict(value)
    payload.pop("assignment_sha256", None)
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> None:
    assignment_path = ROOT / (
        ".agent-harness/runs/" + RUN_ID + "/assignments/" + ASSIGNMENT_ID + ".json"
    )
    seal_path = ROOT / ".prguard/runtime/PR289_CANDIDATE_SEAL.json"
    assignment = json.loads(assignment_path.read_text(encoding="utf-8"))
    seal = json.loads(seal_path.read_text(encoding="utf-8"))

    require(assignment["run_id"] == RUN_ID, "run identity drift")
    require(assignment["assignment_id"] == ASSIGNMENT_ID, "assignment identity drift")
    require(assignment["context_version"] == CONTEXT_VERSION, "context drift")
    require(assignment["independence_mode"] == "blind-results", "independence drift")
    require(assignment["candidate_binding"]["state"] == "frozen", "candidate not frozen")
    require(
        assignment["assignment_sha256"]
        == assignment_sha256(assignment),
        "assignment checksum drift",
    )
    require(
        digest(seal_path) == assignment["candidate_binding"]["seal_file_sha256"],
        "candidate seal file drift",
    )
    for field in (
        "base_sha",
        "candidate_sha",
        "merge_base_sha",
        "candidate_tree_sha",
        "diff_sha256",
        "changed_files_sha256",
        "production_hash",
        "seal_sha256",
    ):
        require(
            seal[field] == assignment["candidate_binding"][field],
            f"candidate binding drift: {field}",
        )

    print(
        json.dumps(
            {
                "ok": True,
                "binding_verified": True,
                "independence_incident": (
                    "schema-discovery rg emitted snippets from historical result "
                    "envelopes because its exclusion glob was ineffective"
                ),
                "review_stopped": True,
                "scientific_verdict_asserted": False,
                "publication_readiness_asserted": False,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
