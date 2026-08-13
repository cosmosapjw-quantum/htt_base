#!/usr/bin/env python3
"""Independent frozen-candidate oracle for PR-291 quantified claim grammar.

Exit zero means the oracle reproduced its complete sealed-candidate diagnostic:
the twenty named repaired promotions are blocked, exact negative guardrail
contexts remain exempt, and the independently discovered bypass set remains
reproducible.  A zero exit is an oracle-execution PASS, not candidate acceptance;
the bypass count is consumed by the reviewer result and coverage verdict.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO_ROOT / "htt" / "src"))

from common.semantic_guards.no_overclaim import scan_text  # noqa: E402


PRIOR_FORBIDDEN = (
    "The analyses identify Bianchi families in the CF4 result.",
    "The analysis identifies both Bianchi families in the CF4 result.",
    "The analysis identifies these Bianchi families in the CF4 result.",
    "Our analysis identifies a Bianchi family in the CF4 result.",
    "The analysis definitively identifies both Bianchi\nfamilies in the CF4 result.",
    "The low-ell scalar therefore implies identification of a Bianchi family.",
    "Identification of a Bianchi family follows from the scalar x/Q result.",
    "The analysis is not public but identifies both Bianchi families.",
    "The analysis identifies every Bianchi family in the result.",
    "The analysis identifies each Bianchi family in the result.",
    "The analyses identify multiple Bianchi families in the result.",
    "Their analyses identify many Bianchi families in the result.",
    "The analysis identifies all Bianchi families in the result.",
    "This analysis's output identifies its Bianchi family.",
    "The analyses' outputs identify all Bianchi families.",
    "Every Bianchi family is identified by the analysis.",
    "The analyses identify\nmultiple Bianchi families in the result.",
    "The scalar implies identification of every Bianchi family.",
    "Identification of multiple Bianchi families follows from the scalar.",
    "The analysis is not public but identifies every Bianchi family.",
)

NOVEL_BLOCKED = (
    "Each analysis identifies every registered Bianchi family.",
    "Every analysis identifies all currently admissible Bianchi families.",
    "Both analyses identify multiple pre-native candidate Bianchi families.",
    "This analysis's output identifies each still viable Bianchi family.",
    "The analyses' outputs identify all model-equivalent Bianchi families.",
    "All registered candidate Bianchi families are identified by the analysis.",
    "Every registered family is conclusively identified as Bianchi VII_h.",
    "The analysis identifies each currently admissible family as Bianchi VII_h.",
    "The analysis identifies\nevery registered candidate Bianchi family.",
    "The scalar implies identification of exactly every registered Bianchi family.",
    "Identification of all currently admissible Bianchi families follows from the scalar.",
)

# These are positive family-identification claims under the governing claim
# ceiling.  They are deliberately ordinary prose, use at most three bounded
# modifiers around family/families, and contain no predicate-scoped negation.
EXPECTED_BYPASSES = (
    "All candidate families have now been identified as Bianchi VII_h.",
    "Every candidate family is hereby identified as Bianchi VII_h.",
    "Each viable family has conclusively now been identified as Bianchi VII_h.",
    "Identification of every candidate family as Bianchi VII_h follows from the scalar.",
    "The scalar implies identification of every candidate family as Bianchi VII_h.",
    "Every candidate family is identified by the scalar as Bianchi VII_h.",
    "All candidate families have\nnow been identified as Bianchi VII_h.",
)

SAFE_DOWNCLAIMS = (
    "The analysis does not identify every Bianchi family.",
    "This analysis's output does not identify its Bianchi family.",
    "All candidate families have not been identified as Bianchi VII_h.",
    "Every candidate family is not identified as Bianchi VII_h.",
    "The scalar does not imply identification of every Bianchi family.",
    "Identification of multiple Bianchi families does not follow from the scalar.",
    "Identification of every candidate family as Bianchi VII_h does not follow from the scalar.",
)

MARKDOWN_SAFE = """
| Allowed reading | Forbidden reading |
|---|---|
| Diagnostic-only morphology compatibility. | Bianchi family identified in this artifact. |
"""

MARKDOWN_POSITIVE = """
| Allowed reading | Forbidden reading |
|---|---|
| Bianchi family identified in this artifact. | Do not claim family identification. |
"""

YAML_SAFE = """
forbidden_uses:
  - Bianchi family identified in this artifact.
mutation_registry:
  - intended_defect: The analysis identifies every Bianchi family.
"""

YAML_POSITIVE = """
forbidden_uses:
  - Bianchi family identified in this artifact.
result:
  claim_text: Bianchi family identified in this artifact.
"""


def rules(text: str, suffix: str = ".md") -> list[str]:
    return [
        issue.rule_id
        for issue in scan_text(text, path=Path(f"hostile_oracle{suffix}"))
    ]


def main() -> int:
    prior_misses = [text for text in PRIOR_FORBIDDEN if not rules(text)]
    novel_misses = [text for text in NOVEL_BLOCKED if not rules(text)]
    reproduced_bypasses = [text for text in EXPECTED_BYPASSES if not rules(text)]
    safe_false_positives = [text for text in SAFE_DOWNCLAIMS if rules(text)]
    markdown_safe_rules = rules(MARKDOWN_SAFE)
    markdown_positive_rules = rules(MARKDOWN_POSITIVE)
    yaml_safe_rules = rules(YAML_SAFE, ".yaml")
    yaml_positive_rules = rules(YAML_POSITIVE, ".yaml")

    diagnostic = {
        "schema": "PR291_R5_QUANTIFIER_HOSTILE_ORACLE_V1",
        "prior_forbidden_count": len(PRIOR_FORBIDDEN),
        "prior_false_negatives": prior_misses,
        "novel_blocked_count": len(NOVEL_BLOCKED),
        "novel_false_negatives": novel_misses,
        "expected_bypass_count": len(EXPECTED_BYPASSES),
        "reproduced_bypasses": reproduced_bypasses,
        "safe_downclaim_count": len(SAFE_DOWNCLAIMS),
        "safe_false_positives": safe_false_positives,
        "markdown_safe_rules": markdown_safe_rules,
        "markdown_positive_rules": markdown_positive_rules,
        "yaml_safe_rules": yaml_safe_rules,
        "yaml_positive_rules": yaml_positive_rules,
        "candidate_acceptance": "FAIL" if reproduced_bypasses else "PASS",
    }
    print(json.dumps(diagnostic, sort_keys=True, indent=2))

    execution_contract_holds = (
        not prior_misses
        and not novel_misses
        and reproduced_bypasses == list(EXPECTED_BYPASSES)
        and not safe_false_positives
        and not markdown_safe_rules
        and markdown_positive_rules == ["geometry_detected"]
        and not yaml_safe_rules
        and yaml_positive_rules == ["geometry_detected"]
    )
    return 0 if execution_contract_holds else 1


if __name__ == "__main__":
    raise SystemExit(main())
