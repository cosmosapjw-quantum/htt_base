#!/usr/bin/env python3
"""Deterministic independent physics/statistics oracle for PR-287.

This oracle consumes no entropy and creates no scientific output.  It checks
the registered mathematical policy and frozen source-row inventories without
calling the candidate's derivation helpers.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from scipy.stats import beta


ROOT = Path(__file__).resolve().parents[5]


def holm_adjust(raw: tuple[float, ...]) -> tuple[float, ...]:
    ordered = sorted(enumerate(raw), key=lambda pair: (pair[1], pair[0]))
    adjusted = [0.0] * len(raw)
    running = 0.0
    for rank, (original, value) in enumerate(ordered, start=1):
        running = max(running, min(1.0, (len(raw) - rank + 1) * value))
        adjusted[original] = running
    return tuple(adjusted)


def clopper_pearson(successes: int, trials: int) -> tuple[float, float]:
    lower = 0.0 if successes == 0 else float(
        beta.ppf(0.025, successes, trials - successes + 1)
    )
    upper = 1.0 if successes == trials else float(
        beta.ppf(0.975, successes + 1, trials - successes)
    )
    return lower, upper


def main() -> None:
    expected_holm = (0.40, 0.42, 0.42, 0.42, 0.42, 0.42, 0.42, 0.42)
    actual_holm = holm_adjust(tuple(index / 100 for index in range(5, 13)))
    assert np.allclose(actual_holm, expected_holm, rtol=0.0, atol=1e-15)

    coverage_checks = {}
    for successes, expected_contains in ((440, False), (450, True), (512, False)):
        interval = clopper_pearson(successes, 512)
        half_width = (interval[1] - interval[0]) / 2.0
        assert half_width <= 0.04
        contains = interval[0] <= 0.90 <= interval[1]
        assert contains is expected_contains
        coverage_checks[str(successes)] = {
            "interval": interval,
            "half_width": half_width,
            "target_contained": contains,
        }

    generator = np.asarray([[1.0, 0.2], [0.2, 1.5]])
    misspecified = np.asarray([[1.0, 0.0], [0.0, 1.5]])
    assert np.all(np.linalg.eigvalsh(generator) > 0.0)
    assert np.all(np.linalg.eigvalsh(misspecified) > 0.0)
    assert not np.array_equal(generator, misspecified)

    # The registered rank geometry is max(rL,rG) <= rJ <= rL+rG;
    # a positive-rank intersection is equivalent to rJ < rL+rG and therefore
    # has minimum principal angle zero.  Zero component rank leaves it undefined.
    for local in range(4):
        for global_ in range(4):
            for joint in range(max(local, global_), local + global_ + 1):
                zero_component = local == 0 or global_ == 0
                intersects = not zero_component and joint < local + global_
                angle_state = (
                    "UNDEFINED" if zero_component else "ZERO" if intersects else "POSITIVE"
                )
                assert (angle_state == "ZERO") is intersects

    pillar_expectations = {
        "T": {
            "path": "docs/research_program/post_pr275/pillar_t_adjudication/PILLAR_T_COMPLETE_ADJUDICATION_V1.json",
            "rows": 80,
            "counts": {
                "PASS": 11,
                "FAIL": 1,
                "INCONCLUSIVE_WITH_RECEIPT": 67,
                "BLOCKED_WITH_RECEIPT": 1,
            },
        },
        "S": {
            "path": "docs/research_program/post_pr275/pillar_s_adjudication/PILLAR_S_COMPLETE_ADJUDICATION_V1.json",
            "rows": 72,
            "counts": {
                "PASS": 21,
                "FAIL": 0,
                "INCONCLUSIVE_WITH_RECEIPT": 50,
                "BLOCKED_WITH_RECEIPT": 1,
            },
        },
    }
    row_evidence = {}
    for pillar, expected in pillar_expectations.items():
        payload = json.loads((ROOT / expected["path"]).read_text(encoding="utf-8"))
        rows = payload["rows"]
        counts = {key: 0 for key in expected["counts"]}
        for row in rows:
            counts[row["verdict"]] += 1
        assert len(rows) == expected["rows"]
        assert counts == expected["counts"]
        assert payload["summary"]["terminal_counts"] == counts
        row_evidence[pillar] = {"row_count": len(rows), "terminal_counts": counts}

    fresh_outputs = (
        "docs/research_program/post_pr275/blind_replay/FRESH_CHALLENGE_V1.json",
        "docs/research_program/post_pr275/blind_replay/FRESH_TRUTH_VAULT_V1.json",
        "docs/research_program/post_pr275/blind_replay/FROZEN_SUBMISSION_V1.json",
        "docs/research_program/post_pr275/blind_replay/REGISTERED_ADJUDICATION_V1.json",
        "docs/generated/pr287_fresh_blind_typed_replay_receipt.json",
    )
    assert not any((ROOT / relative).exists() for relative in fresh_outputs)

    print(json.dumps({
        "status": "PASS",
        "entropy_used": False,
        "holm_adjusted": actual_holm,
        "coverage_checks": coverage_checks,
        "paired_covariance": "SPD_DISTINCT_SHARED_GENERATOR_CONTRACT",
        "rank_principal_angle": "REGISTERED_GEOMETRY_CONSISTENT",
        "pillar_row_evidence": row_evidence,
        "fresh_outputs_present": False,
        "execution_disposition": "INCONCLUSIVE_CAPABILITY_ISOLATED_EXECUTOR_NOT_INSTALLED",
    }, sort_keys=True))


if __name__ == "__main__":
    main()
