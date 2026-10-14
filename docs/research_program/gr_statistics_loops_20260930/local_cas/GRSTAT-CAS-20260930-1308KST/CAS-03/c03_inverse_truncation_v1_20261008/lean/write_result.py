"""Create the typed C03 Lean result from fresh local execution evidence."""

import json
import pathlib

here = pathlib.Path(__file__).resolve().parent
execution = json.loads((here / "execution.json").read_text())
commands = execution["commands"]
assert execution["contract_sha256"] == "dbf2a71676fff9aadd9e017ce3853df6d15e9d83b2f53278b38386b7dee1151f"
assert execution["admitted_inputs_sha256"] == "c198d91d6df5265b6bc2646b4f7d7797f705e4d62c5ca5f09db5faced7dbad45"
assert commands["lean_check"]["exit_code"] == 0
assert commands["forbidden_source_scan"]["exit_code"] == 1
assert (here / "mathlib_revision.stdout.log").read_text().strip() == "fabf563a7c95a166b8d7b6efca11c8b4dc9d911f"
assert "Lean (version 4.31.0," in (here / "lean_version.stdout.log").read_text()
axioms_log = (here / "lean_check.stdout.log").read_text()
assert "sorryAx" not in axioms_log
assert axioms_log.count("depends on axioms:") == 14

result = {
    "schema_version": 2,
    "axis": "lean",
    "status": "PASS",
    "contract_id": "GRSTAT-20260930-CAS-03-C03-INVERSE-TRUNCATION-V1",
    "contract_hash": execution["contract_sha256"],
    "contract_sha256": execution["contract_sha256"],
    "admitted_inputs_sha256": execution["admitted_inputs_sha256"],
    "common_spec_sha256": execution["common_spec_sha256"],
    "evidence_class": "exact",
    "completed_at": execution["completed_at"],
    "source_path": execution["source"],
    "source_sha256": execution["source_sha256"],
    "command": commands["lean_check"],
    "commands": [{"name": name, **command} for name, command in commands.items()],
    "tool_versions": {
        "lean": (here / "lean_version.stdout.log").read_text().strip(),
        "mathlib_revision": (here / "mathlib_revision.stdout.log").read_text().strip(),
    },
    "domain_assumption_diff": [],
    "statement_alignment": {
        "field": "real",
        "matrix": "3x3",
        "vector": "3x1 real column, equivalent to a real 3-vector",
        "invertibility": "det D != 0 for exact inverse; H unrestricted",
        "truncation_domain": "H != 0 proof argument required",
        "branches": "ordinary nonsingular matrix inverse; no branch ambiguity",
        "proved": [
            "H=trace(D)/3, sigma=D-HI, trace(sigma)=0, h1=-2D beta",
            "beta=-(1/2)D^-1 h1 for det D != 0, including H=0",
            "beta-beta_trunc=(1/H^2)sigma^2 beta for H != 0",
            "H=0 diagonal(1,1,-2) with determinant -2 and exact inverse",
            "rational diagonal control D/H=(3/2,3/4,3/4), sigma/H=(1/2,-1/4,-1/4), beta_trunc=3epsilon/4 and defect=epsilon/4",
        ],
        "excluded": ["Taylor remainder", "eigenfield existence/IFT", "science"],
    },
    "axiom_scan": {
        "print_axioms_count": 14,
        "sorryAx_present": False,
        "new_target_axiom_present": False,
        "source_scan_exit_code": 1,
    },
    "launch_id": None,
    "global_launch_authority": "UNAVAILABLE",
    "observed_model": "UNKNOWN",
    "observed_effort": "UNKNOWN",
    "scientific_admission": "HOLD",
    "cache_note": "Pinned oracle was invoked with lake env lean; no local lean/.lake cache created.",
}
for name in ("result.json", "axis_result.json"):
    (here / name).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
