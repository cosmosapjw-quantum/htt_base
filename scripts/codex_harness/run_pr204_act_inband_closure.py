#!/usr/bin/env python3
"""Build or verify the bounded PR-204 author-side result card."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Mapping

import yaml


REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from obsstat.act_inband_injection import (  # noqa: E402
    terminal_from_analysis,
)
from obsstat.act_inband_modulation import (  # noqa: E402
    ActInbandModulationError,
    canonical_sha256,
)
from scripts.act_inband_injection_card import (  # noqa: E402
    _validate_card,
)


SPEC = REPO / "docs/research_program/strengthening/pr204_spec.yaml"
CALIBRATION = REPO / "docs/generated/pr204_injection_calibration.json"
PR177_RESULT = REPO / "docs/generated/pr177_result_card.json"
PR177_REPLAY = REPO / "docs/generated/pr177_deep_replay_receipt.json"
PR152_INVENTORY = REPO / "docs/generated/pr152_inventory.json"
PR152_AVAILABILITY = (
    REPO / "docs/generated/pr152_availability_decision.json"
)
MODULE = REPO / "htt/obsstat/act_inband_injection.py"
PRODUCER = REPO / "scripts/act_inband_injection_card.py"
SCRIPT = Path(__file__).resolve()
OUT = REPO / "docs/generated/pr204_result_card.json"


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(1 << 20):
            digest.update(block)
    return digest.hexdigest()


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ActInbandModulationError(f"{path} must contain a JSON object")
    return value


def _yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ActInbandModulationError(f"{path} must contain a YAML mapping")
    return value


def _semantic_digest(payload: Mapping[str, object]) -> str:
    material = dict(payload)
    material.pop("semantic_digest", None)
    return canonical_sha256(material)


def _serialized(payload: Mapping[str, object]) -> str:
    return json.dumps(payload, indent=1, sort_keys=True) + "\n"


def _atomic_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(_serialized(payload), encoding="utf-8")
    temporary.replace(path)


def _validate_upstream(spec: Mapping[str, Any]) -> dict[str, Any]:
    pr177 = _json(PR177_RESULT)
    replay = _json(PR177_REPLAY)
    inventory = _json(PR152_INVENTORY)
    availability = _json(PR152_AVAILABILITY)
    checks = {
        "PR-177 result schema drift": pr177.get("schema")
        == "htt.pr177.result_card.v1",
        "PR-177 result drift": pr177.get("scientific_result")
        == "NO_RESOLVED_COUPLING_AT_CURRENT_MC_RESOLUTION",
        "PR-177 process status drift": pr177.get("process_execution_status")
        == "PASS_REPRODUCIBLE_RESULT",
        "PR-177 raw-QE drift": pr177.get("raw_qe_reproduction") is False,
        "PR-177 public-use drift": pr177.get("public_use") is False,
        "PR-177 support drift": pr177.get("analysis_support")
        == {
            "coordinate_frame": "Equatorial",
            "endpoints_40_and_763_included": False,
            "inequality": "40 < L < 763",
            "integer_count": 722,
            "integer_max": 762,
            "integer_min": 41,
        },
        "PR-177 replay schema drift": replay.get("schema")
        == "htt.pr177.deep_replay_receipt.v1",
        "PR-177 replay process status drift": replay.get(
            "process_execution_status"
        )
        == "PASS_AUTHORITATIVE_401_UNIT_FEATURE_REPLAY",
        "PR-177 replay completeness drift": replay.get(
            "features_match_raw_authority"
        )
        is True
        and replay.get("raw_units_opened") == 401
        and replay.get("feature_units_replayed") == 401
        and replay.get("feature_mismatch_count") == 0,
        "PR-152 raw-QE inventory drift": inventory.get(
            "raw_qe_inputs_on_disk"
        )
        is False,
        "PR-152 availability decision drift": availability.get("decision")
        == "DEFER_RAW_QE_RDN0_PUBLIC_INPUTS_LARGE_RECONSTRUCTION",
    }
    errors = [message for message, passed in checks.items() if not passed]
    for name, path in (
        ("pr177_result", PR177_RESULT),
        ("pr177_deep_replay", PR177_REPLAY),
        ("pr152_inventory", PR152_INVENTORY),
        ("pr152_availability", PR152_AVAILABILITY),
    ):
        expected = spec["source_authorities"][name]["sha256"]
        if _sha(path) != expected:
            errors.append(f"{name} frozen hash drift")
    if errors:
        raise ActInbandModulationError("; ".join(errors))
    return {
        "pr177_scientific_result": pr177["scientific_result"],
        "pr177_result_sha256": _sha(PR177_RESULT),
        "pr177_replay_sha256": _sha(PR177_REPLAY),
        "raw_qe_inputs_on_disk": False,
        "raw_qe_route_selected": False,
        "availability_decision": availability["decision"],
    }


def build_result_card() -> dict[str, Any]:
    spec = _yaml(SPEC)
    if (
        spec.get("claim_tier") != "exploratory"
        or spec.get("readiness_ceiling") != "EVIDENCE_READY"
        or spec.get("independence_gate") != "OPEN"
        or spec.get("public_use") is not False
    ):
        raise ActInbandModulationError("PR-204 claim ceiling drift")
    calibration = _json(CALIBRATION)
    _validate_card(calibration)
    upstream = _validate_upstream(spec)
    analysis = calibration["analysis"]
    calibration_terminal = terminal_from_analysis(analysis)
    passed = calibration_terminal == spec["terminal_routing"]["pass"]
    readiness = "EVIDENCE_READY" if passed else "BLOCKED"
    author_gates = {
        "mechanics": "EVIDENCE_READY",
        "identification": "EVIDENCE_READY",
        "calibration": "EVIDENCE_READY" if passed else "BLOCKED",
        "provenance": "EVIDENCE_READY",
    }
    terminal = (
        "PR204_AUTHOR_EVIDENCE_READY_INDEPENDENCE_OPEN"
        if passed
        else calibration_terminal
    )
    input_hashes = {
        str(path.relative_to(REPO)): _sha(path)
        for path in (
            SPEC,
            CALIBRATION,
            PR177_RESULT,
            PR177_REPLAY,
            PR152_INVENTORY,
            PR152_AVAILABILITY,
            MODULE,
            PRODUCER,
            SCRIPT,
        )
    }
    content_receipt = canonical_sha256(
        {
            "input_hashes": input_hashes,
            "calibration_semantic_digest": calibration["semantic_digest"],
        }
    )
    card: dict[str, Any] = {
        "schema": "htt.pr204.result_card.v1",
        "process_execution_status": (
            "PASS_REPRODUCIBLE_AUTHOR_SIDE_CALIBRATION"
        ),
        "scientific_status": "NOT_EVALUATED_AUTHOR_CALIBRATION_ONLY",
        "scientific_result": None,
        "terminal": terminal,
        "calibration_terminal": calibration_terminal,
        "owner": "OBSSTAT",
        "implementation_scope": ["obsstat"],
        "claim_tier": "exploratory",
        "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C1"},
        "scientific_artifact_mode": "standard_internal",
        "public_use": False,
        "transfer_source": "none",
        "readiness_state": readiness,
        "readiness_ceiling": "EVIDENCE_READY",
        "author_side_gates": author_gates,
        "identification_scope": (
            "artifact_and_route_identity_only_not_model_or_family_identification"
        ),
        "independence_gate": "OPEN",
        "independence_note": (
            "Non-author derivation lineage and preserved dissent were not "
            "adjudicated by this author-side run."
        ),
        "spec_sha256": _sha(SPEC),
        "calibration_card_sha256": _sha(CALIBRATION),
        "input_hashes": input_hashes,
        "worktree_content_receipt": content_receipt,
        "worktree_state": (
            f"{spec['baseline_commit']}+content-sha256:{content_receipt}"
        ),
        "analysis_support": calibration["analysis_support"],
        "injection_stage": calibration["injection_stage"],
        "raw_qe_reproduction": False,
        "raw_qe_route_selected": False,
        "release_simulation_count": calibration["unit_count"],
        "response_summary": {
            "controlled_response_diagonal": analysis[
                "controlled_response_diagonal"
            ],
            "controlled_maximum_absolute_off_diagonal": analysis[
                "controlled_maximum_absolute_off_diagonal"
            ],
            "controlled_response_condition_number": analysis[
                "controlled_response_condition_number"
            ],
            "response_gate_passed": analysis["response_gate_passed"],
        },
        "coverage_summary": {
            "per_axis": analysis["split_coverage"],
            "coverage_gate_passed": analysis["coverage_gate_passed"],
        },
        "mask_sensitivity_summary": {
            "evaluation_ratio_p95": analysis[
                "evaluation_mask_sensitivity_ratio_p95"
            ],
            "mask_sensitivity_gate_passed": analysis[
                "mask_sensitivity_gate_passed"
            ],
        },
        "upstream_context": upstream,
        "upstream_result_role": (
            "retained_context_only_not_a_new_PR204_scientific_result"
        ),
        "sky_support_status": calibration["sky_support_status"],
        "mask_status": calibration["mask_status"],
        "covariance_status": calibration["covariance_status"],
        "null_mock_status": calibration["null_mock_status"],
        "generating_command": (
            "env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 "
            "MKL_NUM_THREADS=1 venv/bin/python -B "
            "scripts/codex_harness/run_pr204_act_inband_closure.py --write"
        ),
        "caveats": [
            "The injection starts from released reconstructed-kappa alms after the ACT quadratic estimator.",
            "This author-side calibration does not reproduce raw-QE filtering, RDN0, or reconstruction transfer.",
            "PR-177's release-simulation-conditional null remains upstream context and is not promoted into a new PR-204 scientific result.",
            "This does not establish detection, isotropy, cosmological anisotropy, geometry, novelty, release readiness, or family identification.",
            "The non-author Independence gate remains OPEN.",
        ],
    }
    card["semantic_digest"] = _semantic_digest(card)
    return card


def validate_result_card(card: Mapping[str, Any]) -> None:
    expected = build_result_card()
    if dict(card) != expected:
        raise ActInbandModulationError("PR-204 result card is not byte-current")
    if card.get("semantic_digest") != _semantic_digest(card):
        raise ActInbandModulationError("PR-204 result-card digest mismatch")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if args.write:
        card = build_result_card()
        _atomic_json(OUT, card)
        print(
            json.dumps(
                {
                    "ok": True,
                    "terminal": card["terminal"],
                    "readiness_state": card["readiness_state"],
                    "independence_gate": card["independence_gate"],
                },
                sort_keys=True,
            )
        )
        return 0
    card = _json(OUT)
    validate_result_card(card)
    if OUT.read_text(encoding="utf-8") != _serialized(card):
        raise ActInbandModulationError("PR-204 result-card serialization drift")
    print(json.dumps({"ok": True, "read_only": True}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
