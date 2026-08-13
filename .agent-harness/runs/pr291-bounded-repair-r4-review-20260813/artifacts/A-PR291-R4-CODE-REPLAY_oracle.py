#!/usr/bin/env python3
"""Independent hostile oracle for the frozen PR-291 R4 code/replay lane."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import inspect
import json
from pathlib import Path
import sys

import numpy as np
import yaml


ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "htt" / "src"))
sys.path.insert(0, str(ROOT / "htt"))

from common.semantic_guards.no_overclaim import scan_text  # noqa: E402
from common.source_separation import (  # noqa: E402
    build_weak_identification_threshold_contract,
    evaluate_source_separation,
)
from obsstat import cf4_post275_lane as cf4  # noqa: E402


def sha_id(label: str) -> str:
    return "sha256:" + hashlib.sha256(label.encode("ascii")).hexdigest()


def expect_raises(callable_, expected: str) -> None:
    try:
        callable_()
    except Exception as exc:  # hostile oracle checks fail-closed class/message
        if expected.lower() not in str(exc).lower():
            raise AssertionError(
                f"expected error containing {expected!r}, got {type(exc).__name__}: {exc}"
            ) from exc
    else:
        raise AssertionError(f"expected refusal containing {expected!r}")


def response_report(matrix: object | None = None) -> cf4.Cf4ResponseNullReport:
    return cf4.analyze_synthetic_response_nullspace(
        matrix or [[1.0, 0.0, 1.0], [0.0, 1.0, 1.0]],
        [[1.0, 0.2], [0.2, 1.0]],
        covariance_id=sha_id("covariance"),
        response_id=sha_id("response"),
        parameter_labels=("local", "global", "nuisance"),
        parameter_roles=("LOCAL", "GLOBAL", "NUISANCE"),
    )


def weak_decision(response: cf4.Cf4ResponseNullReport, *, joint_rank: int = 2):
    return evaluate_source_separation(
        source_geometry_report_id=sha_id("estimand"),
        covariance_id=response.covariance_id,
        nuisance_tangent_id=sha_id("nuisance"),
        normalizer_id=response.normalizer_id,
        normalizer_source_identity="PR291-ORACLE-NORMALIZER",
        normalizer_coordinate_map_id=sha_id("coordinate-map"),
        parameter_coordinate_units="dimensionless_beta_c_equals_1",
        provider_available=True,
        covariance_supported=True,
        local_parameter_count=1,
        global_parameter_count=1,
        local_rank=1,
        global_rank=1,
        joint_rank=joint_rank,
        principal_angles_radians=(0.1,) if joint_rank == 2 else (),
        joint_singular_values=(1.0, 0.5) if joint_rank == 2 else (1.0,),
        threshold_contract=build_weak_identification_threshold_contract(
            minimum_principal_angle_radians=0.2,
            minimum_normalizer_bound_relative_joint_singular_value=0.01,
        ),
    )


def check_numerical_contract() -> dict[str, object]:
    for function, forbidden in (
        (cf4.analyze_synthetic_shear, "eigengap_floor"),
        (cf4.analyze_synthetic_eigenspace_drift, "eigengap_floor"),
        (cf4.analyze_synthetic_response_nullspace, "rank_tolerance"),
    ):
        assert forbidden not in inspect.signature(function).parameters

    response = response_report()
    payload = response.as_payload()
    assert payload["relative_singular_floor"] == cf4.RELATIVE_SINGULAR_FLOOR == 1e-12
    assert payload["covariance_content_id"].startswith("sha256:")
    assert payload["normalized_response_content_id"].startswith("sha256:")
    assert (payload["response_rank"], payload["nullity"]) == (2, 1)

    for attribute, replacement, error in (
        ("covariance_whitened_response", ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)), "normalized response identity"),
        ("right_null_basis", ((1.0, 0.0, 0.0),), "right-null basis"),
        ("response_rank", 1, "rank/nullity"),
        ("null_residual_bound", 1.0, "right-null basis"),
    ):
        forged = copy.deepcopy(response)
        object.__setattr__(forged, attribute, replacement)
        expect_raises(forged.as_payload, error)

    assert "RELATIVE_SINGULAR_FLOOR" not in cf4._null_replay_bound.__code__.co_names
    near_threshold = response_report(
        [[1.0, 1.0, 1.0], [0.0, 1.0e-13, 2.0e-13]]
    )
    assert near_threshold.response_rank == 1
    assert near_threshold.nullity == 2
    assert near_threshold.null_residual_norm <= near_threshold.null_residual_bound
    manual_bound = (
        128.0
        * np.finfo(float).eps
        * max(np.asarray(near_threshold.covariance_whitened_response).shape)
        * max(
            1.0,
            float(
                np.linalg.norm(
                    np.asarray(near_threshold.covariance_whitened_response), ord=2
                )
            ),
        )
        * max(
            1.0,
            float(np.linalg.norm(np.asarray(near_threshold.right_null_basis), ord=2)),
        )
    )
    assert near_threshold.null_residual_bound == manual_bound

    identified = cf4.build_structural_identified_set(
        lower=-1.0,
        upper=2.0,
        nuisance_box_id="nuisance:oracle:v1",
        response=response,
        source_separation=weak_decision(response),
    )
    assert identified["bounds"] == [-1.0, 2.0]
    assert identified["reported_point"] is None
    for lower, upper in ((0.0, 0.0), (1.0, -1.0)):
        expect_raises(
            lambda lower=lower, upper=upper: cf4.build_structural_identified_set(
                lower=lower,
                upper=upper,
                nuisance_box_id="nuisance:oracle:v1",
                response=response,
                source_separation=weak_decision(response),
            ),
            "strictly ordered",
        )

    rank_one = response_report([[1.0, 1.0, 1.0], [2.0, 2.0, 2.0]])
    assert (rank_one.response_rank, rank_one.nullity) == (1, 2)
    expect_raises(
        lambda: cf4.build_structural_identified_set(
            lower=-1.0,
            upper=2.0,
            nuisance_box_id="nuisance:oracle:v1",
            response=rank_one,
            source_separation=weak_decision(rank_one, joint_rank=2),
        ),
        "rank/nullity",
    )
    return {
        "fixed_singular_floor": payload["relative_singular_floor"],
        "rank_nullity": [payload["response_rank"], payload["nullity"]],
        "near_threshold_rank_nullity": [
            near_threshold.response_rank,
            near_threshold.nullity,
        ],
        "content_id": response.content_id,
    }


def check_claim_grammar() -> dict[str, int]:
    reproduced_miss = (
        "The analysis is not public but definitively identifies several "
        "Bianchi families."
    )
    assert not scan_text(reproduced_miss, path=Path("oracle.md"))
    forbidden = (
        "Those Bianchi geometries have been conclusively detected in the CF4 result.",
        "The family was definitively identified as Bianchi VII_h.",
        "The Bianchi geometry\nwas definitively detected in the CF4 result.",
        "The curl diagnostic is not public but is evidence for physical cosmic vorticity.",
        "PR-291 is not public but revives the retired P0 velocity-shape headline.",
    )
    safe = (
        "The analysis does not identify a Bianchi family.",
        "Bianchi geometry was not detected in this result.",
        "The 0.0089 curl diagnostic is not evidence for physical cosmic vorticity.",
        "PR-291 does not rescue the retired P0 velocity-shape headline.",
    )
    for text in forbidden:
        assert scan_text(text, path=Path("oracle.md")), text
    for text in safe:
        assert not scan_text(text, path=Path("oracle.md")), text
    return {
        "blocking_miss_reproduced": 1,
        "forbidden_detected": len(forbidden),
        "downclaims_allowed": len(safe),
    }


def load_runner():
    path = ROOT / "scripts/codex_harness/run_pr291_cf4_lane.py"
    spec = importlib.util.spec_from_file_location("pr291_r4_oracle_runner", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_replay_and_lifecycle() -> dict[str, object]:
    runner = load_runner()
    bindings = runner._base_source_bindings(ROOT)
    transaction = runner._load_transaction_module(
        ROOT,
        expected_sha256=bindings[
            runner.PR290_TRANSACTION_RUNNER.relative_to(ROOT).as_posix()
        ],
    )
    first = transaction._encoded(runner._build(ROOT))
    second = transaction._encoded(runner._build(ROOT))
    frozen = (
        ROOT
        / "docs/research_program/post_pr275/data_runs/cf4/PR291_NONEXECUTION_RECEIPT.json"
    ).read_bytes()
    assert first == second == frozen
    receipt = json.loads(first)
    assert receipt["terminal"] == "BLOCKED_PREDECESSOR_FINAL_SUCCESS"
    assert receipt["numeric_outputs_written"] == []
    assert receipt["observed_data_executed"] is False
    assert receipt["network_or_download_side_effect"] is False

    canonical_status = yaml.safe_load(
        (ROOT / "docs/codex_handoff/pr_status.yaml").read_text(encoding="utf-8")
    )
    mirror_status = yaml.safe_load(
        (ROOT / "machine_readable/pr_status.yaml").read_text(encoding="utf-8")
    )
    assert canonical_status == mirror_status
    stack = canonical_status["stacked_pr_execution"]
    assert stack["merge_policy"] == "HUMAN_ONLY"
    pr292 = stack["prs"]["PR-292"]
    assert pr292["lifecycle"] == "PLANNED"
    assert pr292["gate_dispositions"]["eligibility"] == "INELIGIBLE"
    assert pr292["assurance_budget"] == {"maximum": 16, "consumed": 0}
    return {
        "receipt_sha256": hashlib.sha256(frozen).hexdigest(),
        "terminal": receipt["terminal"],
        "merge_policy": stack["merge_policy"],
        "pr292": {
            "lifecycle": pr292["lifecycle"],
            "eligibility": pr292["gate_dispositions"]["eligibility"],
            "assurance_budget_consumed": pr292["assurance_budget"]["consumed"],
        },
    }


def main() -> None:
    result = {
        "schema": "PR291_R4_CODE_REPLAY_HOSTILE_ORACLE_V1",
        "status": "FAIL_FINDING_REPRODUCED",
        "numerical_contract": check_numerical_contract(),
        "claim_grammar": check_claim_grammar(),
        "replay_and_lifecycle": check_replay_and_lifecycle(),
    }
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
