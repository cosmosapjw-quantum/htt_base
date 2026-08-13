#!/usr/bin/env python3
"""Independent hostile oracle for A-PR291-FROZEN-CLAIM.

This artifact is assignment-local.  It exercises positive, semantically
forbidden prose against the production claim scanner and records whether each
mutation is actually rejected.  The expected outcome for every cell is at
least one issue; a missed cell is a claim-firewall false negative.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys


REPO = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(REPO / "htt/src"), str(REPO / "htt")]

from common.semantic_guards.no_overclaim import scan_text  # noqa: E402


CASES = (
    ("01_geometry_determiner", "determiner", "A Bianchi geometry was detected in this result."),
    ("02_geometry_plural", "plural", "Bianchi geometries were detected in this result."),
    ("03_geometry_reordered", "reordered", "This result detected a Bianchi geometry."),
    ("04_scalar_multiline", "multiline", "The scalar x/Q/F/G departure\nestablishes Bianchi family identification."),
    ("05_tsc_determiner", "determiner", "The Teff parameter closes the full polarisation hierarchy."),
    ("06_tsc_reordered", "reordered", "A full solver for Bianchi morphology is supplied by TSC."),
    ("07_mio_plural", "plural", "MIO diagnostic certificates provide posterior evidence."),
    ("08_mio_reordered", "reordered", "Posterior evidence is adjudicated by MIO."),
    ("09_external_transfer_plural", "plural", "External transfers are native solver results."),
    ("10_external_transfer_reordered", "reordered", "Native solver evidence is validated by external transfer."),
    ("11_curl_multiline", "multiline", "Physical cosmic vorticity is supported by\nthe 0.0089 curl diagnostic."),
    ("12_curl_table", "table", "| Claim | Guardrail |\n|---|---|\n| The 0.0089 curl diagnostic is evidence for physical cosmic vorticity. | no |"),
    ("13_curl_list", "list", "- The 0.0089 curl diagnostic is evidence for physical cosmic vorticity."),
    ("14_curl_blockquote", "blockquote", "> The 0.0089 curl diagnostic is evidence for physical cosmic vorticity."),
    ("15_p0_determiner", "determiner", "The PR-291 rescues the retired P0 velocity-shape headline."),
    ("16_source_observable_multiline", "multiline", "Source adequacy therefore means\nthe observable is adequate."),
)


def main() -> int:
    cells = []
    for cell_id, mutation_class, text in CASES:
        issues = scan_text(text, path=Path(f"{cell_id}.md"))
        cells.append(
            {
                "cell_id": cell_id,
                "mutation_class": mutation_class,
                "expected": "rejected_positive_forbidden_claim",
                "detected": bool(issues),
                "rule_ids": [issue.rule_id for issue in issues],
                "text": text,
            }
        )
    payload = {
        "schema_version": 1,
        "assignment_id": "A-PR291-FROZEN-CLAIM",
        "candidate_sha": "67076abbfce5e6bf549f1282c95729bfe89b4be8",
        "coverage_cell_count": len(cells),
        "cells": cells,
        "missed_cell_ids": [cell["cell_id"] for cell in cells if not cell["detected"]],
    }
    payload["status"] = "pass" if not payload["missed_cell_ids"] else "fail"
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
