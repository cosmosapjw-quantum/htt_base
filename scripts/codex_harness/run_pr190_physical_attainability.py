#!/usr/bin/env python3
"""PR-190 physical-attainability attempt and decisive falsifier.

The Bianchi-I dust developments in this runner are valid scalar-match
negative controls.  They cannot promote the registered comparator endpoints
because their full component vectors have exact nonzero gaps.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for entry in (str(REPO / "htt"), str(REPO / "htt" / "src")):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from common.pr190_physical_attainability import (  # noqa: E402
    endpoint_substitution_analysis,
    run_scalar_match_grid,
)

SPEC = REPO / "docs/research_program/strengthening/pr190_spec.yaml"
CARD = REPO / "docs/generated/pr190_result_card.json"
CAS_CONTRACT = (
    REPO
    / "docs/generated/pr190_cas/CAS_CONTRACT_PR190_SHEAR_SUBSTITUTION.json"
)
CAS_ADJUDICATION = REPO / "docs/generated/pr190_cas/adjudication.json"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _cas_status() -> dict:
    adjudication = json.loads(CAS_ADJUDICATION.read_text(encoding="utf-8"))
    contract_sha = _sha(CAS_CONTRACT)
    return {
        "contract": (
            "docs/generated/pr190_cas/"
            "CAS_CONTRACT_PR190_SHEAR_SUBSTITUTION.json"
        ),
        "contract_sha256": contract_sha,
        "contract_hash_matches_adjudication": (
            adjudication.get("contract_sha256") == contract_sha
        ),
        "aggregate": "CAS_BLOCKED",
        "historical_aggregate": adjudication.get("aggregate_status"),
        "required_axes": adjudication.get("required_axes"),
        "axis_statuses": adjudication.get("axis_statuses"),
        "verification_state": "STORED_DIAGNOSTIC_ONLY",
        "evidence_origin": "stored_adjudication_json",
        "claim_promotion_cas_eligible": False,
        "stored_cas_diagnostic_only": True,
        "scientific_role": (
            "exact_dust_identities_and_component_mismatch_only"
        ),
    }


def build_payload() -> dict:
    endpoints = endpoint_substitution_analysis()
    grid = run_scalar_match_grid()
    cas = _cas_status()
    dynamics_valid = (
        grid["grid_size"] == 100
        and grid["all_developments_succeeded"]
        and grid["minimum_interval_efolds"] >= 5.0
        and grid["max_normalized_gauss_residual"] < 1.0e-10
        and grid["expanding_branch_preserved"]
        and grid["lorentzian_metric_signature_fixed_by_ansatz"]
        and grid["dust_energy_conditions_preserved"]
    )
    cas_valid = (
        cas["aggregate"] == "CAS_5AXIS_PASS"
        and cas["contract_hash_matches_adjudication"]
        and cas["verification_state"] == "RUNNER_OBSERVED_EXECUTION"
        and cas["evidence_origin"] == "runner_observed_local_subprocess"
        and all(value == "PASS" for value in cas["axis_statuses"].values())
    )
    full_endpoints_realized = endpoints["full_endpoint_vectors_realized"]
    terminal = (
        "BLOCKED_COMPONENT_ENDPOINT_NOT_ATTAINED"
        if dynamics_valid and cas_valid and not full_endpoints_realized
        else "BLOCKED_PR190_VALIDATION_FAILURE"
    )
    return {
        "schema": "htt.pr190.result_card.v1",
        "pr_id": "PR-190",
        "metadata": {
            "owner": "BASS",
            "scope": "pre-solver physical-attainability attempt",
            "spec_sha256": _sha(SPEC),
            "claim_level": {
                "scheme": "roadmap_rescue_v1",
                "level": "C1",
            },
            "transfer_source": "none",
            "public_use": False,
            "readiness_state": "BLOCKED_BY_DECISIVE_FALSIFIER",
            "independence_gate": "OPEN",
            "sky_support_status": "not_applicable",
            "null_mock_status": "not_applicable",
            "generating_command": (
                "env PYTHONHASHSEED=0 venv/bin/python -B "
                "scripts/codex_harness/"
                "run_pr190_physical_attainability.py --write"
            ),
            "baseline_commit": (
                "c80e35c9c8484f56c1654bfe96b66ce64bd03985"
            ),
        },
        "result": {
            "registered_endpoint_comparison": endpoints,
            "bianchi_i_dust_scalar_match_grid": grid,
            "exact_structural_constraints": {
                "momentum_constraint": "0 (homogeneous diagonal comoving ansatz)",
                "jacobi_constraint": "0 (Bianchi-I structure constants vanish)",
                "matter_conservation": "d(rho)/dN=-3*rho",
                "normal_equals_matter_frame": True,
            },
            "gate_evaluation": {
                "lower_full_component_endpoint_realized": False,
                "upper_full_component_endpoint_realized": False,
                "scalar_interval_negative_controls_valid": dynamics_valid,
                "normalized_gauss_residual_below_1e_10": (
                    grid["max_normalized_gauss_residual"] < 1.0e-10
                ),
                "five_efolds_completed": (
                    grid["minimum_interval_efolds"] >= 5.0
                ),
                "cas_exact_obligations_valid": cas_valid,
                "conjunctive_pr190_pass": False,
            },
            "cas_status": cas,
        },
        "terminal": terminal,
        "scientific_interpretation": (
            "The tested diagonal comoving Bianchi-I dust family is a valid "
            "Einstein-matter solution family over the scalar interval, but it "
            "does not realize either registered four-component endpoint. "
            "Therefore it cannot establish full physical attainability or "
            "dynamical sharpness."
        ),
        "claim_boundary": [
            "CAS_5AXIS_PASS applies only to the registered exact identities and mismatch.",
            "The CAS result does not promote scientific validity, novelty, release, or family identification.",
            "A valid shear-only scalar match is not a replacement for nonzero W2, tilt, or curvature components.",
            "The result is internal and non-public; the Independence gate remains OPEN.",
        ],
    }


def _render(payload: dict) -> bytes:
    return (json.dumps(payload, sort_keys=True, indent=1) + "\n").encode()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    payload = build_payload()
    rendered = _render(payload)
    if args.write:
        print(
            "refusing to overwrite the frozen historical result card without "
            "a new parent-observed cas_gate.py run-adjudicate execution",
            file=sys.stderr,
        )
        return 2
    ok = CARD.is_file() and CARD.read_bytes() == rendered
    print(
        json.dumps(
            {
                "mode": "check",
                "ok": ok,
                "read_only": True,
                "terminal": payload["terminal"],
            },
            sort_keys=True,
        )
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
