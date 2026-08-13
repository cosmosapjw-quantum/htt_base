#!/usr/bin/env python3
"""Independent adversarial oracle for PR-291 claim-language boundaries.

This only imports the frozen candidate scanner and checks that positive
forbidden claims cannot be silenced by prose shape or unrelated negation.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "htt" / "src"))

from common.semantic_guards.no_overclaim import scan_text  # noqa: E402


CASES = (
    (
        "determiner",
        "A Bianchi geometry was detected in the CF4 result.",
        ("geometry_detected",),
    ),
    (
        "plural",
        "Bianchi families were identified in the CF4 result.",
        ("geometry_detected",),
    ),
    (
        "reordered_modifier",
        "The Bianchi family was conclusively identified in the CF4 result.",
        ("geometry_detected",),
    ),
    (
        "multiline",
        "The Bianchi geometry\nwas detected in the CF4 result.",
        ("geometry_detected",),
    ),
    (
        "markdown_table_allowed_cell",
        "| Allowed reading | Forbidden reading |\n"
        "|---|---|\n"
        "| Bianchi geometry detected in the CF4 result. | Do not claim it. |",
        ("geometry_detected",),
    ),
    (
        "markdown_list",
        "- We detected a Bianchi geometry in the CF4 result.",
        ("geometry_detected",),
    ),
    (
        "markdown_blockquote",
        "> The 0.0089 curl diagnostic is evidence for physical cosmic vorticity.",
        ("legacy_curl_physics_promotion",),
    ),
    (
        "separate_sentence_negation",
        "No posterior is computed. Bianchi geometry detected in the CF4 result.",
        ("geometry_detected",),
    ),
    (
        "same_sentence_unrelated_without",
        "Without a public release, Bianchi geometry detected in the CF4 result.",
        ("geometry_detected",),
    ),
)


def main() -> int:
    rows = []
    for case_id, text, expected in CASES:
        actual = tuple(issue.rule_id for issue in scan_text(text, path=Path("hostile.md")))
        rows.append(
            {
                "case_id": case_id,
                "expected_rule_ids": expected,
                "actual_rule_ids": actual,
                "pass": actual == expected,
            }
        )
    payload = {"oracle": "PR291_CLAIM_HOSTILE_V1", "rows": rows}
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if all(row["pass"] for row in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
