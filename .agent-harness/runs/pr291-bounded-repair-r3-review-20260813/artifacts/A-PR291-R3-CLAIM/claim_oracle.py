#!/usr/bin/env python3
"""Independent PR-291 claim-language oracle for A-PR291-R3-CLAIM.

This oracle is assignment-local and intentionally does not import repository tests.
It evaluates the production scanner directly against positive promotions and exact
negative/structured controls. A non-zero exit means at least one expected semantic
classification was missed or spuriously reported.
"""

from __future__ import annotations

import json
from pathlib import Path

from common.semantic_guards.no_overclaim import scan_text


CASES: tuple[tuple[str, str, str, tuple[str, ...]], ...] = (
    (
        "determiner_singular_passive",
        "claims.md",
        "A Bianchi geometry was detected in the CF4 result.",
        ("geometry_detected",),
    ),
    (
        "determiner_plural_passive",
        "claims.md",
        "Those Bianchi families were identified in the CF4 result.",
        ("geometry_detected",),
    ),
    (
        "active_plural_determiner",
        "claims.md",
        "We identified those Bianchi families from the CF4 statistic.",
        ("geometry_detected",),
    ),
    (
        "active_plural_quantifier",
        "claims.md",
        "The analysis identified several Bianchi families from the CF4 statistic.",
        ("geometry_detected",),
    ),
    (
        "reordered_active_modifier",
        "claims.md",
        "We conclusively identified a Bianchi family from the CF4 statistic.",
        ("geometry_detected",),
    ),
    (
        "reordered_family_predicate",
        "claims.md",
        "The family was conclusively identified as Bianchi VII_h.",
        ("geometry_detected",),
    ),
    (
        "multiline_active_plural",
        "claims.md",
        "We conclusively identified\nthose Bianchi families from the CF4 statistic.",
        ("geometry_detected",),
    ),
    (
        "same_sentence_unrelated_not_prefix",
        "claims.md",
        "The pipeline is not public, but Bianchi geometry was detected in the CF4 result.",
        ("geometry_detected",),
    ),
    (
        "same_sentence_unrelated_no_prefix",
        "claims.md",
        "No posterior is computed, but Bianchi geometry was detected in the CF4 result.",
        ("geometry_detected",),
    ),
    (
        "same_sentence_unrelated_without_prefix",
        "claims.md",
        "Without a public release, Bianchi geometry was detected in the CF4 result.",
        ("geometry_detected",),
    ),
    (
        "same_match_unrelated_not_curl",
        "claims.md",
        "The 0.0089 curl diagnostic is not public but is evidence for physical cosmic vorticity.",
        ("legacy_curl_physics_promotion",),
    ),
    (
        "same_match_unrelated_not_p0",
        "claims.md",
        "PR-291 is not public but rescues the retired P0 velocity-shape headline.",
        ("retired_p0_rescue",),
    ),
    (
        "same_match_unrelated_not_scalar",
        "claims.md",
        "The scalar result is not public but establishes Bianchi family identification.",
        ("scalar_family_identification",),
    ),
    (
        "exact_geometry_downclaim",
        "claims.md",
        "Bianchi geometry was not detected in the CF4 result.",
        (),
    ),
    (
        "exact_curl_downclaim",
        "claims.md",
        "The 0.0089 curl diagnostic is not evidence for physical cosmic vorticity.",
        (),
    ),
    (
        "exact_reverse_curl_downclaim",
        "claims.md",
        "Cosmic potential flow is not established by the WF curl-div ratio.",
        (),
    ),
    (
        "exact_p0_downclaim",
        "claims.md",
        "PR-291 does not rescue the retired P0 velocity-shape headline.",
        (),
    ),
    (
        "markdown_forbidden_reading",
        "matrix.md",
        "| Allowed reading | Forbidden reading |\n|---|---|\n| Stencil self-check only | Bianchi geometry was detected. |",
        (),
    ),
    (
        "markdown_allowed_cell_positive",
        "matrix.md",
        "| Allowed reading | Forbidden reading |\n|---|---|\n| Bianchi geometry was detected. | Do not claim family identification. |",
        ("geometry_detected",),
    ),
    (
        "markdown_forbidden_status",
        "ledger.md",
        "| Claim | Owner | Status |\n|---|---|---|\n| PR-291 rescues the retired P0 headline. | HTT | FORBIDDEN / NOT_GRANTED |",
        (),
    ),
    (
        "markdown_supported_status",
        "ledger.md",
        "| Claim | Owner | Status |\n|---|---|---|\n| PR-291 rescues the retired P0 headline. | HTT | SUPPORTED |",
        ("retired_p0_rescue",),
    ),
    (
        "yaml_registered_guardrail",
        "spec.yaml",
        "forbidden_uses:\n  - Bianchi geometry was detected\n",
        (),
    ),
    (
        "yaml_positive_after_guardrail",
        "result.yaml",
        "forbidden_uses:\n  - Bianchi geometry was detected\nresult:\n  claim: Bianchi family was identified\n",
        ("geometry_detected",),
    ),
    (
        "multiline_curl_downclaim",
        "claims.md",
        "Physical cosmic vorticity is not supported by\nthe 0.0089 curl diagnostic.",
        (),
    ),
)


def main() -> int:
    rows: list[dict[str, object]] = []
    for case_id, suffix_name, text, expected in CASES:
        actual = tuple(
            issue.rule_id for issue in scan_text(text, path=Path(suffix_name))
        )
        rows.append(
            {
                "case_id": case_id,
                "expected": list(expected),
                "actual": list(actual),
                "pass": actual == expected,
            }
        )
    payload = {
        "assignment_id": "A-PR291-R3-CLAIM",
        "context_version": "e9b385d7fbc4f8e47c97c3b0c7edae4e522d9be4e025d9342e26ab24829e3019",
        "oracle": "independent_production_scanner_semantic_classification",
        "case_count": len(rows),
        "passed": sum(bool(row["pass"]) for row in rows),
        "failed": sum(not bool(row["pass"]) for row in rows),
        "cases": rows,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
