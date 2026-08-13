#!/usr/bin/env python3
"""Fail-closed sentinel for the invalidated PR-288 blind claim review."""

from __future__ import annotations

import json


def main() -> int:
    payload = {
        "assignment_id": "A-PR288-FROZEN-CLAIM",
        "breach_code": "BLIND_RESULTS_ISOLATION_BREACH",
        "candidate_verdict": "NOT_EXAMINED",
        "gate_disposition": "INCONCLUSIVE",
        "status": "ERROR_REVIEW_INVALIDATED",
    }
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
