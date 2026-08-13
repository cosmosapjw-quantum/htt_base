#!/usr/bin/env python3
"""Independent bounded grammar oracle for PR-291 predicate continuation.

Exit zero means the scanner reproduced this review's frozen observations,
including the explicitly named mismatch set.  It does not mean the candidate
claim-language gate passed.
"""

from __future__ import annotations

import json
from pathlib import Path

from common.semantic_guards.no_overclaim import scan_text


CASES = (
    # Positive active/passive claims.
    ("active_analysis", "The analysis identifies whichever Bianchi family fits best.", ("geometry_detected",)),
    ("active_generic_actor", "The report identifies every Bianchi family in the catalogue.", ("geometry_detected",)),
    ("passive_positive_adverbs", "Each viable family has formally already been identified as Bianchi VII_h.", ("geometry_detected",)),
    ("passive_modal_auxiliary", "Every candidate family could already have been identified as Bianchi VII_h.", ("geometry_detected",)),
    # Determiners, possessives, Bianchi-family, and family-as-Bianchi objects.
    ("possessive_analysis", "Our analysis's output identifies its preferred Bianchi family.", ("geometry_detected",)),
    ("possessive_object", "The analysis identifies the team's preferred Bianchi family.", ("geometry_detected",)),
    ("family_as_bianchi", "Several candidate families have now been identified as Bianchi type VII_h.", ("geometry_detected",)),
    ("bianchi_family_plural", "The analyses identify whichever Bianchi families survive.", ("geometry_detected",)),
    # Scalar forward, reverse, and direct attribution.
    ("scalar_forward", "The low-ell scalar implies identification of each viable Bianchi family.", ("scalar_family_identification",)),
    ("scalar_reverse", "Identification of each viable Bianchi family follows from the scalar.", ("scalar_family_identification",)),
    ("scalar_family_as_bianchi_forward", "The scalar implies identification of each candidate family as Bianchi VII_h.", ("scalar_family_identification",)),
    ("scalar_direct_attribution", "Each candidate family is identified by the scalar as Bianchi VII_h.", ("geometry_detected",)),
    # Multiline and unrelated negation controls.
    ("multiline_active", "The analysis identifies every registered Bianchi\nfamily in the catalogue.", ("geometry_detected",)),
    ("multiline_passive", "Every viable candidate family has clearly\nbeen identified as Bianchi VII_h.", ("geometry_detected",)),
    ("unrelated_negation", "The result is not public, yet the analysis identifies every Bianchi family.", ("geometry_detected",)),
    # Predicate-scoped negative controls.
    ("negative_does_not", "The analysis does not identify every Bianchi family.", ()),
    ("negative_aux_not", "Every Bianchi family has not been identified by this analysis.", ()),
    ("negative_adverb_before_not", "Every Bianchi family has clearly not been identified by this analysis.", ()),
    ("negative_cannot_adverb", "The analysis cannot conclusively identify every Bianchi family.", ()),
    ("negative_contraction", "The analysis doesn't identify every Bianchi family.", ()),
    ("negative_scalar", "The scalar cannot uniquely imply identification of each Bianchi family.", ()),
    # Exact Markdown/YAML guardrails and positive near-controls.
    ("markdown_forbidden_column", "| Allowed reading | Forbidden reading |\n|---|---|\n| Diagnostic only. | The report identifies every Bianchi family. |", ()),
    ("markdown_allowed_column", "| Allowed reading | Forbidden reading |\n|---|---|\n| The analysis identifies every Bianchi family. | Do not identify a family. |", ("geometry_detected",)),
    ("yaml_guardrail", "forbidden_uses:\n  - The analysis identifies every Bianchi family.\n", ()),
    ("yaml_positive_neighbor", "forbidden_uses:\n  - Bianchi family identified\nresult:\n  claim: The analysis identifies every Bianchi family.\n", ("geometry_detected",)),
)

EXPECTED_MISMATCH_IDS = {
    "active_generic_actor",
    "passive_modal_auxiliary",
    "negative_aux_not",
    "negative_adverb_before_not",
    "negative_cannot_adverb",
    "negative_contraction",
    "negative_scalar",
}


def main() -> int:
    rows = []
    mismatch_ids = set()
    for case_id, text, expected in CASES:
        path = Path("oracle.yaml" if case_id.startswith("yaml_") else "oracle.md")
        observed = tuple(issue.rule_id for issue in scan_text(text, path=path))
        matches = observed == expected
        if not matches:
            mismatch_ids.add(case_id)
        rows.append(
            {
                "case_id": case_id,
                "expected": list(expected),
                "observed": list(observed),
                "matches": matches,
            }
        )
    payload = {
        "schema_version": 1,
        "case_count": len(CASES),
        "expected_mismatch_ids": sorted(EXPECTED_MISMATCH_IDS),
        "observed_mismatch_ids": sorted(mismatch_ids),
        "observations_reproduced": mismatch_ids == EXPECTED_MISMATCH_IDS,
        "rows": rows,
    }
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0 if payload["observations_reproduced"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
