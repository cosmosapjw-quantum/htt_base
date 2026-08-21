#!/usr/bin/env python3
"""Read-only PR-299 readiness inspection for every registered observed lane."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def build_payload() -> dict[str, object]:
    from htt.infer.bayesian_production import (
        LaneReadinessStatus,
        assess_lane_readiness,
        load_observational_lane_descriptors,
    )

    spec = ROOT / "docs/research_program/post_pr275/pr299_spec.yaml"
    descriptors = load_observational_lane_descriptors(spec)
    missing = [
        path
        for descriptor in descriptors
        for path in descriptor.runner_patterns
        if not (ROOT / path).is_file()
    ]
    if missing:
        raise SystemExit(f"registered runner path is missing: {sorted(missing)}")
    decisions = [assess_lane_readiness(descriptor) for descriptor in descriptors]
    if any(item.status is not LaneReadinessStatus.BLOCKED_PRODUCTION_MODEL_CONTRACT_UNBOUND for item in decisions):
        raise SystemExit("unexpected observed-data readiness state")
    return {
        "schema": "htt.pr299.observed_bayesian_readiness.v1",
        "observed_data_executed": False,
        "artifact_mode": "readiness_only",
        "lanes": [
            {
                "lane_id": item.lane_id,
                "status": item.status.value,
                "blocked_reasons": list(item.blocked_reasons),
            }
            for item in decisions
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", required=True)
    args = parser.parse_args(argv)
    del args
    print(json.dumps(build_payload(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
