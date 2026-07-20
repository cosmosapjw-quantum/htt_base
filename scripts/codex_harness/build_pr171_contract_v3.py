#!/usr/bin/env python3
"""Build PR-171 CAS contract v3 after preserving two failed generations."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
V1 = Path("docs/generated/pr171_cas/CAS_CONTRACT_PR171_CLASS_CONDITIONAL_TILT_V2.json")
V2 = Path("docs/generated/pr171_cas/CAS_CONTRACT_PR171_CLASS_CONDITIONAL_TILT_V3.json")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build() -> dict:
    value = json.loads((REPO / V1).read_text(encoding="utf-8"))
    value["identity"]["contract_id"] = "CAS-PR171-CLASS-CONDITIONAL-TILT-003"
    value["identity"]["contract_version"] = 3
    value["identity"]["supersedes_contract_sha256"] = _sha(REPO / V1)
    value["revision"] = {
        "generation_2_aggregate": "CAS_FAIL",
        "generation_1_or_2_reuse_allowed": False,
        "fresh_four_axis_run_required": True,
        "changes": [
            "construct the SymPy characteristic polynomial from det(rI-A) to avoid same-name symbol identity drift",
            "use mapping-form Sage substitution everywhere and coerce Sage booleans and precision to JSON-native values",
            "normalize the Lean characteristic identity with ring and correct the registered negative sign fixture"
        ],
        "mathematical_statement_changed": False,
        "engineering_preflight": "SymPy, Sage/Singular, and Lean sources each completed locally after the repairs; these preflights are tool-readiness evidence only and are not axis results.",
        "reason": "Generation 2 exposed three additional representation and proof-script defects; no generation-2 result is reused."
    }
    for details in value["axes"].values():
        for row in details["sources"]:
            row["sha256"] = _sha(REPO / row["path"])
    for row in value["identity"]["source_input_hashes"]:
        row["sha256"] = _sha(REPO / row["path"])
    return value


def _render(value: dict) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    data = _render(build())
    if args.write:
        (REPO / V2).parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("wb", dir=(REPO / V2).parent, delete=False) as handle:
            handle.write(data)
            temporary = Path(handle.name)
        os.replace(temporary, REPO / V2)
    if args.check and (not (REPO / V2).is_file() or (REPO / V2).read_bytes() != data):
        print(json.dumps({"ok": False, "path": str(V2)}))
        return 2
    print(json.dumps({"ok": True, "path": str(V2), "sha256": hashlib.sha256(data).hexdigest()}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
