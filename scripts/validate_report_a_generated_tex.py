#!/usr/bin/env python3
"""Validate the generated Report A LaTeX without promoting it to authority."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import yaml


class GeneratedTexValidationError(RuntimeError):
    pass


def load_claim_ids(path: Path) -> list[str]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not isinstance(value.get("claims"), list):
        raise GeneratedTexValidationError("claim ledger is malformed")
    ids = [claim.get("id") for claim in value["claims"]]
    if any(not isinstance(item, str) or not item for item in ids):
        raise GeneratedTexValidationError("claim ledger contains an invalid identifier")
    if len(ids) != len(set(ids)):
        raise GeneratedTexValidationError("claim ledger contains duplicate identifiers")
    return ids


def validate_generated_tex(text: str, claim_ids: list[str]) -> dict[str, object]:
    required_fragments = (
        "Tensorized Low-Multipole CMB Inference",
        "Scope, authority, and supersession",
        "References",
        "\\appendix",
        "RANK_UNRESOLVED",
        "DEFERRED_BY_OWNER",
    )
    for fragment in required_fragments:
        if fragment not in text:
            raise GeneratedTexValidationError(f"generated TeX lacks {fragment!r}")

    if re.search(r"\\section\*?\{Abstract\}", text) is None:
        raise GeneratedTexValidationError("generated TeX lacks the Abstract section")
    if re.search(r"\\section\{\d+(?:\.\d+)*\.?\s", text):
        raise GeneratedTexValidationError("generated TeX retains a manual numeric section prefix")
    if text.count("\\appendix") != 1:
        raise GeneratedTexValidationError("generated TeX must enter appendix mode exactly once")

    # These identify the pre-Abstract repository/control-plane prologue or the
    # quarantined legacy manuscript. The scientific boundary statements later
    # in the report (NONE, DEFERRED_BY_OWNER, RANK_UNRESOLVED) are intentional.
    forbidden_fragments = (
        "R3 flattened draft",
        "Repository: cosmosapjw-quantum/htt_base",
        "Status: theory/methods release candidate",
        "CURRENT_OBSERVATIONAL_RESULT",
        "docs/manuscript/main.tex",
        "Claim-Tiered FLRW Departure Diagnostics",
        "Bianchi-Conditioned Observables",
        "[@",
        "\\bibliography{references}",
    )
    for fragment in forbidden_fragments:
        if fragment in text:
            raise GeneratedTexValidationError(f"generated TeX contains forbidden fragment {fragment!r}")

    missing_claims = [claim_id for claim_id in claim_ids if claim_id not in text]
    if missing_claims:
        raise GeneratedTexValidationError(
            "generated TeX omits canonical claims: " + ", ".join(missing_claims)
        )

    return {
        "claim_count": len(claim_ids),
        "missing_claim_count": 0,
        "appendix_count": 1,
        "citation_markers_unresolved": False,
        "control_plane_prologue_removed": True,
        "scientific_boundary_statements_preserved": True,
        "legacy_manuscript_content_absent": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tex", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()

    data = args.tex.read_bytes()
    text = data.decode("utf-8")
    claim_ids = load_claim_ids(args.ledger)
    checks = validate_generated_tex(text, claim_ids)
    receipt = {
        "schema": "htt.report_a.r4b0.generated_tex_validation.v2",
        "tex_path": args.tex.as_posix(),
        "tex_sha256": hashlib.sha256(data).hexdigest(),
        "tex_bytes": len(data),
        "checks": checks,
        "authority_grade": "GENERATED_BUILD_ARTIFACT_NOT_SCIENTIFIC_SOURCE",
        "pdf_generated": False,
        "publication_authorized": False,
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
