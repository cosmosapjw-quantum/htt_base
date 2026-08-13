#!/usr/bin/env python3
"""Independent bounded oracle for PR-291 R4 claim-language review.

Exit zero means that the oracle executed and reproduced its frozen expectation;
``candidate_pass`` in the emitted JSON is the candidate verdict.
"""

from __future__ import annotations

import json
from pathlib import Path

from common.semantic_guards.no_overclaim import scan_text


CASES = (
    (
        "active_plural",
        "The analysis identifies several Bianchi families from the CF4 statistic.",
        ("geometry_detected",),
    ),
    (
        "reordered_active_as_bianchi",
        "The analysis identifies the families as Bianchi VII_h.",
        (),
    ),
    (
        "passive_as_bianchi",
        "Those families were conclusively identified as Bianchi VII_h.",
        ("geometry_detected",),
    ),
    (
        "multiline_direct_family",
        "We identified those Bianchi\nfamilies from the CF4 statistic.",
        ("geometry_detected",),
    ),
    (
        "multiline_scalar_family",
        "The scalar result establishes Bianchi\nfamily identification.",
        (),
    ),
    (
        "reordered_scalar_family",
        "Bianchi family identification follows from the scalar x/Q result.",
        (),
    ),
    (
        "unrelated_not_family",
        "Bianchi families are not public but are identified in the CF4 result.",
        (),
    ),
    (
        "unrelated_not_geometry",
        "Bianchi geometry is not public but was detected in the CF4 result.",
        (),
    ),
    (
        "unrelated_not_curl",
        "The 0.0089 curl diagnostic is not public but is evidence for physical cosmic vorticity.",
        ("legacy_curl_physics_promotion",),
    ),
    (
        "unrelated_not_retired_p0",
        "PR-291 is not public but rescues the retired P0 velocity-shape headline.",
        ("retired_p0_rescue",),
    ),
    (
        "unrelated_not_scalar",
        "The scalar result is not public but establishes Bianchi family identification.",
        ("scalar_family_identification",),
    ),
    ("downclaim_family", "Bianchi family is not identified in this artifact.", ()),
    (
        "downclaim_curl",
        "The 0.0089 curl diagnostic is not evidence for physical cosmic vorticity.",
        (),
    ),
    (
        "downclaim_retired_p0",
        "PR-291 does not rescue the retired P0 velocity-shape headline.",
        (),
    ),
    (
        "downclaim_scalar",
        "The scalar result does not establish Bianchi family identification.",
        (),
    ),
)


def main() -> None:
    rows = []
    for case_id, text, frozen_expected_rules in CASES:
        observed = tuple(
            issue.rule_id for issue in scan_text(text, path=Path("oracle.md"))
        )
        if observed != frozen_expected_rules:
            raise AssertionError(
                f"{case_id}: expected frozen {frozen_expected_rules}, got {observed}"
            )
        rows.append(
            {
                "case_id": case_id,
                "observed_rule_ids": list(observed),
                "scanner_flagged": bool(observed),
            }
        )

    missed_positive_cases = [
        "reordered_active_as_bianchi",
        "multiline_scalar_family",
        "reordered_scalar_family",
        "unrelated_not_family",
        "unrelated_not_geometry",
    ]
    print(
        json.dumps(
            {
                "oracle_id": "pr291-r4-claim-grammar-v1",
                "candidate_pass": False,
                "missed_positive_cases": missed_positive_cases,
                "predicate_scoped_downclaims_preserved": True,
                "curl_p0_scalar_unrelated_negation_caught": True,
                "cases": rows,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
