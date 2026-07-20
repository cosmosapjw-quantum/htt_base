#!/usr/bin/env python3
"""Build/check the reproducible PR-171 source-counterexample result pack."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import sys
import tempfile
from copy import deepcopy
from fractions import Fraction
from pathlib import Path
from typing import Any

import yaml

from pr171_cas_support import COLLECTION_PATH, CONTRACT_PATH, REPO, atomic_write, load, render, sha

sys.path.insert(0, str(REPO / "htt/src"))
from common.tilt_relaxation import (  # noqa: E402
    DragTiltSystem,
    LinearTiltSystem,
    TiltRelaxationError,
    route_terminal_result,
    rw_relaxation_sign,
    source_counterexample_fixture,
    suppression_functional,
)


SPEC = Path("docs/research_program/long_horizon_rescue/pr171_spec.yaml")
PROVENANCE = Path("docs/research_program/long_horizon_rescue/pr171_primary_source_provenance.yaml")
SOURCE_RECEIPT = Path("docs/generated/pr171_source_verification.json")
RUNNER = Path("scripts/codex_harness/run_pr171_tilt_relaxation.py")
OUTPUTS = {
    "mechanics": Path("docs/generated/pr171_exact_mechanics.json"),
    "counterexample": Path("docs/generated/pr171_source_counterexample.json"),
    "closure": Path("docs/generated/pr171_source_space_closure.json"),
    "mutations": Path("docs/generated/pr171_mutation_report.json"),
    "result": Path("docs/generated/pr171_result_card.json"),
    "manifest": Path("docs/generated/pr171_artifact_manifest.json"),
}
FORBIDDEN = [
    re.compile(r"generic fluid cannot source persistent tilt", re.I),
    re.compile(r"universal no-go theorem", re.I),
    re.compile(r"proof of (?:isotropy|FLRW)", re.I),
    re.compile(r"Bianchi (?:geometry detected|family identified)", re.I),
    re.compile(r"validated as native", re.I),
    re.compile(r"(?:1e-6|10\^-6).{0,80}(?:expected|threshold|conclusion)", re.I),
]


def _yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected YAML object: {path}")
    return value


def validate_public_claims(value: Any) -> None:
    text = json.dumps(value, sort_keys=True)
    for pattern in FORBIDDEN:
        if pattern.search(text):
            raise ValueError(f"forbidden PR-171 claim pattern: {pattern.pattern}")
    if isinstance(value, dict) and value.get("public_use") is True:
        raise ValueError("PR-171 public_use promotion forbidden")


def validate_terminal_card(card: dict[str, Any]) -> None:
    validate_public_claims(card)
    if card.get("claim_level") != {"scheme": "roadmap_rescue_v1", "level": "C2"}:
        raise ValueError("claim-level promotion or drift")
    if card.get("scientific_artifact_mode") != "hypothesis_only":
        raise ValueError("hypothesis-only mode removed")
    if card.get("suppression_result") is not None:
        raise ValueError("unidentified numerical suppression must remain null")
    if card.get("cas_status") != "CAS_4AXIS_PASS" and card.get("exact_stability_result") is not None:
        raise ValueError("non-pass CAS branch carries a positive exact target")
    if card.get("published_counterexample_gate") is True and card.get("blanket_no_go_status") != "RETIRED_BY_AUTHENTICATED_EXTERNAL_SOURCE":
        raise ValueError("published counterexample did not retire blanket no-go")


def execute_mutations(base: dict[str, Any]) -> list[dict[str, Any]]:
    mutations: list[tuple[str, Any]] = []
    promoted = deepcopy(base); promoted["public_use"] = True
    mutations.append(("public_use_promotion", promoted))
    level = deepcopy(base); level["claim_level"]["level"] = "C3"
    mutations.append(("claim_level_promotion", level))
    mode = deepcopy(base); mode["scientific_artifact_mode"] = "standard_internal"
    mutations.append(("hypothesis_only_removed", mode))
    stale = deepcopy(base); stale["suppression_result"] = "1e-6 expected conclusion"
    mutations.append(("numerical_precommitment", stale))
    positive = deepcopy(base); positive["cas_status"] = "CAS_BLOCKED"; positive["exact_stability_result"] = "STABLE"
    mutations.append(("blocked_positive_target", positive))
    survived = deepcopy(base); survived["blanket_no_go_status"] = "SUPPORTED"
    mutations.append(("counterexample_discarded", survived))
    generic = deepcopy(base); generic["summary"] = "generic fluid cannot source persistent tilt"
    mutations.append(("generic_no_go_language", generic))
    family = deepcopy(base); family["summary"] = "Bianchi family identified"
    mutations.append(("family_promotion", family))
    native = deepcopy(base); native["summary"] = "external transfer validated as native"
    mutations.append(("native_promotion", native))
    rows: list[dict[str, Any]] = []
    for mutation_id, value in mutations:
        detected = False
        violation = None
        try:
            validate_terminal_card(value)
        except ValueError as exc:
            detected = True
            violation = str(exc)
        rows.append({
            "mutation_id": mutation_id,
            "target": str(OUTPUTS["result"]),
            "execution_kind": "live_production_validator",
            "detected": detected,
            "observed_violation": violation,
        })
    if not all(row["detected"] for row in rows):
        raise ValueError("one or more PR-171 mutations survived")
    return rows


def _input_paths() -> list[Path]:
    paths = [SPEC, PROVENANCE, SOURCE_RECEIPT, CONTRACT_PATH, COLLECTION_PATH, Path("htt/src/common/tilt_relaxation.py"), RUNNER]
    collection = load(REPO / COLLECTION_PATH)
    for axis in ("wolfram_xact", "sympy", "sage_singular", "lean"):
        paths.append(Path(f"docs/generated/pr171_cas/generation_1/axis_result_{axis}.json"))
    return paths


def _input_hashes() -> dict[str, str]:
    return {str(path): sha(REPO / path) for path in _input_paths()}


def build() -> dict[str, dict[str, Any]]:
    spec = _yaml(REPO / SPEC)
    provenance = _yaml(REPO / PROVENANCE)
    source_receipt = load(REPO / SOURCE_RECEIPT)
    collection = load(REPO / COLLECTION_PATH)
    if source_receipt.get("ok") is not True or source_receipt.get("source_count") != 5:
        raise ValueError("source authentication gate failed")
    cas_status = collection.get("aggregate_status")
    if cas_status not in {"CAS_4AXIS_PASS", "CAS_BLOCKED", "CAS_CONFLICT", "CAS_FAIL"}:
        raise ValueError(f"invalid CAS aggregate: {cas_status}")
    fixture = source_counterexample_fixture()
    counterexample_gate = all(
        fixture[key] is True
        for key in ("w_less_than_one_third", "Gamma_nonnegative", "weak_energy_condition", "dominant_energy_condition")
    ) and fixture["source_asymptotic_result"] == "GENERIC_EXTREME_TILT"
    route = route_terminal_result(
        cas_status,
        provenance_ok=True,
        counterexample_gate=counterexample_gate if cas_status == "CAS_4AXIS_PASS" else False,
        source_space_closed=False,
    )
    stable = DragTiltSystem(Fraction(1, 4), Fraction(1, 2), Fraction(1, 3))
    persistent = LinearTiltSystem(Fraction(1), Fraction(1), Fraction(1), Fraction(1))
    exact_allowed = cas_status == "CAS_4AXIS_PASS"
    inputs = _input_hashes()
    common = {
        "owner": "COMMON",
        "implementation_scope": "common",
        "claim_tier": "conditional",
        "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C2"},
        "scientific_artifact_mode": "hypothesis_only",
        "execution_authorization": "EXPLICIT_APPROVED_SEQUENCE",
        "public_use": False,
        "transfer_source": "none",
        "config_hash": sha(REPO / SPEC),
        "input_hashes": inputs,
        "sky_support_status": "not_applicable_exact_mechanics",
        "mask_status": "not_applicable_exact_mechanics",
        "covariance_status": "not_applicable",
        "null_mock_status": "not_applicable",
        "generating_command": "venv/bin/python -B scripts/codex_harness/run_pr171_tilt_relaxation.py --write",
        "runtime_environment": {"python": platform.python_version()},
        "git_commit": spec["baseline_commit"],
        "worktree_state": f"{spec['baseline_commit']}+PR-171-worktree",
    }
    mechanics = {
        **common,
        "artifact_mode": "exact_class_conditional_mechanics",
        "cas_status": cas_status,
        "exact_stability_result": "LOCAL_LINEAR_STABLE_IN_FROZEN_DRAG_CLASS" if exact_allowed else None,
        "stable_fixture": {
            "trace": str(stable.trace),
            "determinant": str(stable.determinant),
            "strictly_stable": stable.strictly_stable,
        } if exact_allowed else None,
        "persistent_negative_control": {
            "trace": str(persistent.trace),
            "determinant": str(persistent.determinant),
            "strictly_stable": persistent.strictly_stable,
        } if exact_allowed else None,
        "rw_relaxation_fixture": rw_relaxation_sign(Fraction(1, 2), Fraction(1, 4)) if exact_allowed else None,
        "caveats": ["CAS_BLOCKED withholds all exact targets" if not exact_allowed else "local linear result only", "no nonlinear shear closure"],
    }
    counterexample = {
        **common,
        "artifact_mode": "authenticated_external_source_counterexample_audit",
        "published_counterexample_gate": counterexample_gate,
        "fixture": fixture,
        "blanket_no_go_status": "RETIRED_BY_AUTHENTICATED_EXTERNAL_SOURCE",
        "source_claim": "Hervik-Lim report generic extreme tilt in the frozen gamma-law Bianchi-VIII interval",
        "new_theorem_claimed": False,
        "caveats": ["external source result, not a CAS-derived theorem", "not an observational or family-identification result"],
    }
    closure = {
        **common,
        "artifact_mode": "source_space_closure_audit",
        "restricted_rw_branch": "AUTHENTICATED",
        "near_flrw_drag_closure": "STIPULATED_CLASS_ONLY",
        "generic_dark_sector_closure": "NOT_ESTABLISHED",
        "khronon_shear_leakage_bridge": "UNINSTANTIATED_LOOPHOLE",
        "suppression": suppression_functional(w=Fraction(1, 4), g=Fraction(0), delta_n=None),
        "caveats": ["absence of a closure is not evidence of stability", "no generic numerical ceiling"],
    }
    result = {
        **common,
        "artifact_mode": "class_conditional_source_counterexample_result",
        "cas_status": cas_status,
        "process_gate_status": route["process_gate_status"],
        "scientific_result": (
            "source_counterexample_audit_only_cas_blocked"
            if cas_status == "CAS_BLOCKED"
            else route["scientific_result"]
        ),
        "exact_stability_result": mechanics["exact_stability_result"],
        "suppression_result": None,
        "suppression_status": "SUPPRESSION_CEILING_NOT_IDENTIFIED",
        "published_counterexample_gate": counterexample_gate,
        "blanket_no_go_status": "RETIRED_BY_AUTHENTICATED_EXTERNAL_SOURCE",
        "khronon_status": "UNINSTANTIATED_LOOPHOLE",
        "summary": "Authenticated source counterexample retires the blanket no-go; restricted RW relaxation remains class-conditional; a generic suppression ceiling is not identified.",
        "allowed_use": ["internal source-provenance audit", "class-conditional exact mechanics when CAS permits"],
        "forbidden_use": ["universal no-go", "isotropy proof", "family identification", "native-transfer validation", "observational detection"],
        "caveats": ["public_use=false", "the published counterexample is external", "CAS status controls exact algebra only"],
    }
    validate_terminal_card(result)
    mutations_rows = execute_mutations(result)
    mutations = {
        **common,
        "artifact_mode": "live_claim_and_terminal_mutation_report",
        "registered_count": len(mutations_rows),
        "killed_count": sum(row["detected"] for row in mutations_rows),
        "survivors": [row["mutation_id"] for row in mutations_rows if not row["detected"]],
        "mutations": mutations_rows,
        "caveats": ["validator mutation evidence only; not physical validation"],
    }
    artifacts = {"mechanics": mechanics, "counterexample": counterexample, "closure": closure, "mutations": mutations, "result": result}
    manifest_rows = []
    for name, value in artifacts.items():
        data = render(value)
        manifest_rows.append({"name": name, "path": str(OUTPUTS[name]), "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)})
    manifest = {
        **common,
        "artifact_mode": "content_addressed_result_manifest",
        "artifacts": manifest_rows,
        "caveats": ["manifest excludes itself to avoid recursive hashing"],
    }
    return {**artifacts, "manifest": manifest}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    artifacts = build()
    mismatches: list[str] = []
    for name, value in artifacts.items():
        path = REPO / OUTPUTS[name]
        data = render(value)
        if args.write:
            atomic_write(path, data)
        if args.check and (not path.is_file() or path.read_bytes() != data):
            mismatches.append(str(OUTPUTS[name]))
    print(json.dumps({"ok": not mismatches, "cas_status": artifacts["result"]["cas_status"], "scientific_result": artifacts["result"]["scientific_result"], "mismatches": mismatches}, indent=2, sort_keys=True))
    return 0 if not mismatches else 2


if __name__ == "__main__":
    raise SystemExit(main())
