#!/usr/bin/env python3
"""Build the preregistered PR-169 CAS v2 contract from immutable v1."""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
V1 = REPO / "docs/generated/pr169_cas/CAS_CONTRACT_PR169_UNSIGNED_LEAKAGE.json"
V2 = REPO / "docs/generated/pr169_cas/CAS_CONTRACT_PR169_UNSIGNED_LEAKAGE_V2.json"
EXPECTED_V1_SHA256 = "b4b2cf6a247209ff22406b7c1f493387934b9e4d2b2824b396a8f3fbc23c2781"
UPDATED_AXIS_HASHES = {
    "htt/src/common/pr169_sympy_axis.py": "eb22b4dbc5d50876308d70f32fde92373430df0756d95e8f3057654ecd4d94c7",
    "sage/pr169_unsigned_leakage_axis.sage": "3417b99472a79d22ed1f9e65e796d6db72c270b3932e3b8397f444475955cfe9",
    "wolfram/pr169_unsigned_leakage_axis.wls": "eb98108317eda34cdea25d02769d0ff89265009259f1397d3c29b68efb76ea05",
    "formal_pr169/Pr169UnsignedLeakage.lean": "86c7217b87bd2b3a1a761d15e30b60fd3dfca88b31490e5bd849d8d9368dd751",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    if sha(V1) != EXPECTED_V1_SHA256:
        raise SystemExit("refusing v2 build: immutable v1 contract hash drifted")
    for relative, expected in UPDATED_AXIS_HASHES.items():
        if sha(REPO / relative) != expected:
            raise SystemExit(f"refusing v2 build: repaired source drifted: {relative}")
    contract = json.loads(V1.read_text(encoding="utf-8"))
    contract["identity"]["contract_id"] = "CAS-PR169-UNSIGNED-LEAKAGE-002"
    contract["identity"]["contract_version"] = 2
    contract["identity"]["supersedes_contract_sha256"] = EXPECTED_V1_SHA256
    contract["revision"] = {
        "reason": (
            "All three symbolic v1 axes exposed an inert chained-substitution "
            "projection mutant, and the Lean v1 executable used a noncomputable "
            "decide expression. The universal theorem statements and canonical "
            "expected values are unchanged; every v1 axis envelope is invalidated."
        ),
        "v1_axis_results_reusable": False,
        "fresh_four_axis_run_required": True,
        "changes": [
            "construct the clipped-curvature fixture before substitution on all three symbolic axes",
            "make the Lean runtime receipt decide one explicit missing-gate witness while retaining the machine-checked universal theorem",
        ],
    }
    for details in contract["axes"].values():
        for row in details["sources"]:
            path = row["path"]
            if path in UPDATED_AXIS_HASHES:
                row["sha256"] = UPDATED_AXIS_HASHES[path]
    rendered = json.dumps(contract, indent=2, sort_keys=True) + "\n"
    V2.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=V2.parent, delete=False
    ) as handle:
        handle.write(rendered)
        temporary = Path(handle.name)
    os.replace(temporary, V2)
    print(json.dumps({"path": str(V2.relative_to(REPO)), "sha256": sha(V2)}))


if __name__ == "__main__":
    main()

