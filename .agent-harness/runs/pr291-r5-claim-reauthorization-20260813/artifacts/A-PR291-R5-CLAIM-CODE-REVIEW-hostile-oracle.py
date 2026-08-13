#!/usr/bin/env python3
"""Independent hostile claim oracle for A-PR291-R5-CLAIM-CODE-REVIEW.

Exit zero means that the oracle executed to completion.  The JSON
``candidate_verdict`` is the scientific/review verdict: it is FAIL whenever a
forbidden promotion survives or an approved structured/downclaim control is
rejected.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "htt" / "src"))

from common.semantic_guards.no_overclaim import scan_text  # noqa: E402


FORBIDDEN: tuple[tuple[str, str], ...] = (
    # Exact eight false-negative classes named by the owner-authorized repair.
    ("prior_plural_subject", "The analyses identify Bianchi families in the CF4 result."),
    ("prior_both_determiner", "The analysis identifies both Bianchi families in the CF4 result."),
    ("prior_these_determiner", "The analysis identifies these Bianchi families in the CF4 result."),
    ("prior_possessive_subject", "Our analysis identifies a Bianchi family in the CF4 result."),
    ("prior_multiline_determiner", "The analysis definitively identifies both Bianchi\nfamilies in the CF4 result."),
    ("prior_forward_scalar", "The low-ell scalar therefore implies identification of a Bianchi family."),
    ("prior_reverse_scalar", "Identification of a Bianchi family follows from the scalar x/Q result."),
    ("prior_unrelated_publication_negation", "The analysis is not public but identifies both Bianchi families."),
    # Broader quantifier, possessive, reordered, multiline, and implication attacks.
    ("quantifier_every", "The analysis identifies every Bianchi family in the result."),
    ("quantifier_each", "The analysis identifies each Bianchi family in the result."),
    ("quantifier_multiple_plural", "The analyses identify multiple Bianchi families in the result."),
    ("quantifier_many_possessive_plural", "Their analyses identify many Bianchi families in the result."),
    ("quantifier_all", "The analysis identifies all Bianchi families in the result."),
    ("possessive_analysis_output", "This analysis's output identifies its Bianchi family."),
    ("possessive_plural_analysis_output", "The analyses' outputs identify all Bianchi families."),
    ("reordered_family_first", "Every Bianchi family is identified by the analysis."),
    ("multiline_quantifier", "The analyses identify\nmultiple Bianchi families in the result."),
    ("scalar_forward_quantifier", "The scalar implies identification of every Bianchi family."),
    ("scalar_reverse_quantifier", "Identification of multiple Bianchi families follows from the scalar."),
    ("unrelated_negation_quantifier", "The analysis is not public but identifies every Bianchi family."),
)


SAFE: tuple[tuple[str, str, Path], ...] = (
    ("downclaim_every", "The analysis does not identify every Bianchi family.", Path("downclaim.md")),
    ("downclaim_possessive", "This analysis's output does not identify its Bianchi family.", Path("downclaim.md")),
    ("downclaim_scalar_forward", "The scalar does not imply identification of every Bianchi family.", Path("downclaim.md")),
    ("downclaim_scalar_reverse", "Identification of multiple Bianchi families does not follow from the scalar.", Path("downclaim.md")),
    (
        "markdown_forbidden_status",
        "| Claim | Owner | Status |\n|---|---|---|\n| The analysis identifies every Bianchi family. | HTT | FORBIDDEN / NOT_GRANTED |",
        Path("claim_ledger.md"),
    ),
    (
        "markdown_forbidden_reading",
        "| Allowed reading | Forbidden reading |\n|---|---|\n| Diagnostic only. | The analysis identifies every Bianchi family. |",
        Path("claim_matrix.md"),
    ),
    (
        "yaml_forbidden_uses",
        "forbidden_uses:\n  - The analysis identifies every Bianchi family\n",
        Path("spec.yaml"),
    ),
)


POSITIVE_STRUCTURED: tuple[tuple[str, str, Path], ...] = (
    (
        "markdown_supported_claim",
        "| Claim | Owner | Status |\n|---|---|---|\n| The analysis identifies every Bianchi family. | HTT | SUPPORTED |",
        Path("claim_ledger.md"),
    ),
    (
        "yaml_positive_claim",
        "forbidden_uses:\n  - Bianchi family identification\nresult:\n  claim_text: The analysis identifies every Bianchi family\n",
        Path("result.yaml"),
    ),
)


def main() -> int:
    false_negatives: list[dict[str, str]] = []
    false_positives: list[dict[str, object]] = []
    structured_leaks: list[dict[str, str]] = []

    for case_id, text in FORBIDDEN:
        issues = scan_text(text, path=Path("hostile_claim.md"))
        if not issues:
            false_negatives.append({"case_id": case_id, "text": text})

    for case_id, text, path in SAFE:
        issues = scan_text(text, path=path)
        if issues:
            false_positives.append(
                {
                    "case_id": case_id,
                    "text": text,
                    "rule_ids": [issue.rule_id for issue in issues],
                }
            )

    for case_id, text, path in POSITIVE_STRUCTURED:
        if not scan_text(text, path=path):
            structured_leaks.append({"case_id": case_id, "text": text})

    candidate_verdict = (
        "PASS"
        if not false_negatives and not false_positives and not structured_leaks
        else "FAIL"
    )
    print(
        json.dumps(
            {
                "schema_version": 1,
                "oracle_id": "PR291_R5_CLAIM_HOSTILE_ORACLE",
                "candidate_verdict": candidate_verdict,
                "forbidden_cases": len(FORBIDDEN),
                "safe_cases": len(SAFE),
                "positive_structured_cases": len(POSITIVE_STRUCTURED),
                "false_negatives": false_negatives,
                "false_positives": false_positives,
                "structured_exemption_leaks": structured_leaks,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
