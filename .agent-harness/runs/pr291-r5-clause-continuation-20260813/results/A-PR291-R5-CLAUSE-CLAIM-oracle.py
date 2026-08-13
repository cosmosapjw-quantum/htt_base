"""Assignment-local blind grammar oracle for the PR-291 clause continuation."""

from __future__ import annotations

import json
from pathlib import Path

from common.semantic_guards.no_overclaim import scan_text


CASES = (
    ("positive_arbitrary_actor", "The referee appendix definitively identifies three viable Bianchi families.", True, "md"),
    ("positive_family_as_bianchi", "The catalogue report identifies several candidate families as Bianchi type VII_h.", True, "md"),
    ("positive_modal_passive", "Each candidate family should already have been identified as Bianchi VII_h by the committee.", True, "md"),
    ("positive_passive_adverb_order", "Each viable family could already conclusively have been formally identified as Bianchi VII_h.", True, "md"),
    ("positive_passive_scalar_attribution", "Every viable family is directly identified by the scalar as Bianchi VII_h.", True, "md"),
    ("positive_scalar_forward_family_as", "The scalar therefore implies identification of every viable family as Bianchi VII_h.", True, "md"),
    ("positive_scalar_reverse_family_as", "Identification of three viable families as Bianchi IX follows from the low-ell feature.", True, "md"),
    ("positive_scalar_direct", "The scalar identifies every candidate Bianchi family.", True, "md"),
    ("positive_multiline_actor", "The independent report conclusively identifies every candidate\nBianchi family in the registered set.", True, "md"),
    ("positive_multiline_passive", "Every candidate family could already have been\nidentified as Bianchi VII_h by the report.", True, "md"),
    ("negative_cannot_adverbs", "The independent report cannot conclusively uniquely identify every Bianchi family.", False, "md"),
    ("negative_does_not_adverbs", "The independent report does not conclusively uniquely identify every Bianchi family.", False, "md"),
    ("negative_does_adverb_not", "The independent report does conclusively not identify every Bianchi family.", False, "md"),
    ("negative_ascii_cant", "The independent report can't conclusively identify every Bianchi family.", False, "md"),
    ("negative_unicode_cant", "The independent report can’t conclusively identify every Bianchi family.", False, "md"),
    ("negative_ascii_wont", "The scalar won't uniquely imply identification of any Bianchi family.", False, "md"),
    ("negative_ascii_shant", "The report shan't directly identify any Bianchi family.", False, "md"),
    ("negative_never", "The report never conclusively identifies any Bianchi family.", False, "md"),
    ("negative_passive_not_middle", "Every Bianchi family could conclusively not have been uniquely identified by this report.", False, "md"),
    ("negative_passive_never_middle", "Every Bianchi family has clearly never been conclusively identified by this report.", False, "md"),
    ("negative_passive_contraction", "Every Bianchi family couldn't conclusively have been identified by this report.", False, "md"),
    ("control_not_public_positive", "The report is not public but conclusively identifies every Bianchi family.", True, "md"),
    ("control_never_public_positive", "The report is never public but conclusively identifies every Bianchi family.", True, "md"),
    ("control_unrelated_cannot_sentence", "This cannot be public. The report identifies every Bianchi family.", True, "md"),
    ("markdown_forbidden_cell", "| Allowed reading | Forbidden reading |\n|---|---|\n| diagnostic only | Bianchi family identified |", False, "md"),
    ("markdown_allowed_cell", "| Allowed reading | Forbidden reading |\n|---|---|\n| Bianchi family identified | diagnostic only |", True, "md"),
    ("markdown_forbidden_status", "| Claim | Status |\n|---|---|\n| Bianchi family identified | FORBIDDEN / NOT_EVALUATED |", False, "md"),
    ("markdown_near_status", "| Claim | Status |\n|---|---|\n| Bianchi family identified | FORBIDDENISH |", True, "md"),
    ("yaml_exact_guardrail", "forbidden_uses:\n  - Bianchi family identified", False, "yaml"),
    ("yaml_near_guardrail", "forbidden_use:\n  - Bianchi family identified", True, "yaml"),
    ("yaml_sibling_no_leak", "forbidden_uses:\n  - Bianchi family identified\nresult:\n  text: Bianchi geometry detected", True, "yaml"),
)


def main() -> int:
    rows = []
    for case_id, text, expected_issue, suffix in CASES:
        rules = [
            issue.rule_id
            for issue in scan_text(text, path=Path(f"oracle.{suffix}"))
        ]
        rows.append(
            {
                "case_id": case_id,
                "expected_issue": expected_issue,
                "observed_issue": bool(rules),
                "rule_ids": rules,
            }
        )
    mismatches = [
        row["case_id"]
        for row in rows
        if row["expected_issue"] != row["observed_issue"]
    ]
    expected_mismatches = ["negative_does_adverb_not"]
    print(
        json.dumps(
            {
                "case_count": len(rows),
                "expected_mismatches": expected_mismatches,
                "mismatches": mismatches,
                "reproduced_blocker": mismatches == expected_mismatches,
                "rows": rows,
            },
            sort_keys=True,
        )
    )
    return 0 if mismatches == expected_mismatches else 1


if __name__ == "__main__":
    raise SystemExit(main())
