#!/usr/bin/env python3
"""Blind hostile reproducer for PR-291 R5 claim-language false negatives.

Exit zero only when the candidate still exhibits every independently derived
false negative and the positive/negative structured controls behave as
expected.  Thus PASS means the review finding is reproducible, not that the
candidate claim gate passes.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[4]
COMMON_SRC = REPO_ROOT / "htt" / "src"
if str(COMMON_SRC) not in sys.path:
    sys.path.insert(0, str(COMMON_SRC))

from common.semantic_guards.no_overclaim import scan_text  # noqa: E402


FORBIDDEN_FALSE_NEGATIVES = {
    "active_plural_analysis_subject": (
        "The analyses identify Bianchi families in the CF4 result."
    ),
    "determiner_both": (
        "The analysis identifies both Bianchi families in the CF4 result."
    ),
    "determiner_these": (
        "The analysis identifies these Bianchi families in the CF4 result."
    ),
    "possessive_analysis_subject": (
        "Our analysis identifies a Bianchi family in the CF4 result."
    ),
    "multiline_determiner": (
        "The analysis definitively identifies both Bianchi\n"
        "families in the CF4 result."
    ),
    "scalar_family_implication": (
        "The low-ell scalar therefore implies identification of a Bianchi family."
    ),
    "reversed_scalar_implication": (
        "Identification of a Bianchi family follows from the scalar x/Q result."
    ),
    "unrelated_negation": (
        "The analysis is not public but identifies both Bianchi families."
    ),
}

FORBIDDEN_DETECTED_CONTROLS = {
    "registered_active_plural": (
        "The analysis identifies several Bianchi families in the CF4 result."
    ),
    "subject_predicate_reversal": (
        "Several Bianchi families are identified by this analysis."
    ),
    "registered_reordered": (
        "The analysis identifies the families as Bianchi VII_h."
    ),
    "registered_scalar_reversal": (
        "Bianchi family identification follows from the scalar x/Q result."
    ),
    "unrelated_never": (
        "The analysis never publishes but identifies a Bianchi family."
    ),
}

SAFE_DOWNCLAIMS = {
    "predicate_scoped_active": (
        "The analysis does not identify both Bianchi families."
    ),
    "predicate_scoped_passive": (
        "Both Bianchi families are not identified by this analysis."
    ),
    "predicate_scoped_scalar": (
        "Bianchi family identification does not follow from the scalar x/Q result."
    ),
}

STRUCTURED_SAFE = {
    "markdown_forbidden_column": (
        "| Allowed reading | Forbidden reading |\n"
        "|---|---|\n"
        "| Diagnostic only. | The analysis identifies several Bianchi families. |\n"
    ),
    "markdown_forbidden_status": (
        "| Claim | Owner | Status |\n"
        "|---|---|---|\n"
        "| The analysis identifies several Bianchi families. | HTT | FORBIDDEN |\n"
    ),
    "yaml_exact_guardrails": (
        "forbidden_uses:\n"
        "  - The analysis identifies several Bianchi families.\n"
        "result:\n"
        "  claim_tier: diagnostic_only\n"
    ),
}


def rules(text: str, filename: str) -> list[str]:
    return [
        issue.rule_id
        for issue in scan_text(text, path=Path(filename))
    ]


def main() -> int:
    observations: dict[str, dict[str, object]] = {}
    failures: list[str] = []

    for name, text in FORBIDDEN_FALSE_NEGATIVES.items():
        observed = rules(text, "hostile.md")
        observations[name] = {
            "semantic_expectation": "FORBIDDEN",
            "scanner_rules": observed,
            "reproduced_false_negative": observed == [],
        }
        if observed:
            failures.append(f"false negative no longer reproduces: {name}: {observed}")

    for name, text in FORBIDDEN_DETECTED_CONTROLS.items():
        observed = rules(text, "hostile.md")
        observations[name] = {
            "semantic_expectation": "FORBIDDEN",
            "scanner_rules": observed,
            "detected_control": bool(observed),
        }
        if not observed:
            failures.append(f"forbidden control was not detected: {name}")

    for name, text in SAFE_DOWNCLAIMS.items():
        observed = rules(text, "safe.md")
        observations[name] = {
            "semantic_expectation": "ALLOWED_DOWNCLAIM",
            "scanner_rules": observed,
            "allowed": observed == [],
        }
        if observed:
            failures.append(f"predicate-scoped downclaim rejected: {name}: {observed}")

    for name, text in STRUCTURED_SAFE.items():
        suffix = ".yaml" if name.startswith("yaml_") else ".md"
        observed = rules(text, f"structured{suffix}")
        observations[name] = {
            "semantic_expectation": "ALLOWED_STRUCTURED_GUARDRAIL",
            "scanner_rules": observed,
            "allowed": observed == [],
        }
        if observed:
            failures.append(f"structured guardrail rejected: {name}: {observed}")

    payload = {
        "oracle_id": "PR291-R5-CLAIM-FALSE-NEGATIVE-REPRODUCER",
        "meaning_of_pass": (
            "All eight independently derived false negatives reproduce, while "
            "registered detections and safe guardrails retain expected behavior."
        ),
        "false_negative_count": sum(
            bool(row.get("reproduced_false_negative"))
            for row in observations.values()
        ),
        "observations": observations,
        "oracle_errors": failures,
        "status": "PASS" if not failures else "FAIL",
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
