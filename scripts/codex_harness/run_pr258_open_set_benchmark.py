#!/usr/bin/env python3
"""Replay the PR-258 finite-library open-set synthetic benchmark.

The response supports, metric, thresholds, split identities and generator
families are frozen before held-out draws.  The output validates software
behavior only.  It does not read PR-151, an observed sky, old Rust science
output, an external transfer, or a native solver.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
for entry in (ROOT / "htt/src", ROOT / "htt"):
    text = str(entry)
    if text not in sys.path:
        sys.path.insert(0, text)

from common.open_set_response_classes import (  # noqa: E402
    FiniteSupportPerturbationKind,
    OpenSetBenchmarkStatus,
    PR258_ARTIFACT_MODE,
    PR258_ARTIFACT_OWNER,
    PR258_ARTIFACT_SCOPE,
    PR258_COVARIANCE_STATUS,
    PR258_MAXIMUM_MC_REPLICATES,
    PR258_MAXIMUM_MCSE,
    PR258_MINIMUM_MC_REPLICATES,
    PR258_NULL_MOCK_STATUS,
    PR258_SKY_SUPPORT_STATUS,
    ResponseSupportKind,
    build_reopening_observable_spec,
    build_response_class_manifold,
    build_response_equivalence_report,
    classify_open_set_response_batch,
    evaluate_open_set_benchmark,
    source_separation_not_applicable,
)


MASTER_SEED = 20260728
REPLICATES_PER_CELL = 20_000
TARGET_SHA = "d62d63de6fdae1fbaf595ccce52b3abf532899e5"
ATOL = 1.0e-12
RTOL = 1.0e-12
EQUIVALENCE_SQUARED_TOLERANCE = 0.01
UNKNOWN_SQUARED_THRESHOLD = 4.0
DECISION_SQUARED_MARGIN = 0.5
COVARIANCE_NULL_TOLERANCE = 1.0e-10
OUTPUT = (
    ROOT
    / "docs/generated/pr258_open_set_response_classes/"
    "open_set_benchmark.json"
)
GENERATION_INPUTS = (
    Path(__file__),
    ROOT / "htt/src/common/open_set_response_classes.py",
    ROOT / "htt/htt/htt/statistics/open_set_response_classes.py",
    ROOT / "docs/research_program/premise_anchor/pr258_spec.yaml",
)


def _receipt(role: str, descriptor: object) -> str:
    encoded = json.dumps(
        {
            "descriptor": descriptor,
            "role": role,
            "schema": "PR258_SYNTHETIC_RECEIPT_V1",
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


CONVENTION_ID = _receipt(
    "observable_convention",
    {"labels": ["response-x", "response-y"], "units": "synthetic_dimensionless"},
)
NUISANCE_ID = _receipt("nuisance_policy", {"kind": "none"})
CALIBRATION_RECEIPT = _receipt(
    "fixed_calibration",
    {
        "metric": "OBSERVABLE_COVARIANCE_SQUARED_DISTANCE_V1",
        "equivalence_squared_distance_tolerance": (
            EQUIVALENCE_SQUARED_TOLERANCE
        ),
        "unknown_squared_distance_threshold": UNKNOWN_SQUARED_THRESHOLD,
        "decision_squared_margin": DECISION_SQUARED_MARGIN,
        "covariance_null_tolerance": COVARIANCE_NULL_TOLERANCE,
        "frozen_before_generation": True,
    },
)
SPLIT_RECEIPT = _receipt(
    "split",
    {
        "train_validation_held_out": [0.6, 0.2, 0.2],
        "benchmark_uses": "held_out_only_after_fixed_calibration",
        "master_seed": MASTER_SEED,
    },
)


def _canonical_float(value: float) -> float:
    if not math.isfinite(value):
        raise ValueError("benchmark payload must contain finite numbers")
    if abs(value) < 1.0e-14:
        return 0.0
    return float(f"{value:.14g}")


def _canonical(value: Any) -> Any:
    if isinstance(value, (float, np.floating)):
        return _canonical_float(float(value))
    if isinstance(value, dict):
        return {key: _canonical(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    return value


def _worktree_state() -> dict[str, object]:
    inputs = [
        {
            "path": path.relative_to(ROOT).as_posix(),
            "sha256": "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        for path in GENERATION_INPUTS
    ]
    descriptor = {
        "base_target_sha": TARGET_SHA,
        "inputs": inputs,
        "kind": "content_addressed_precommit_worktree_inputs",
        "output_excluded": OUTPUT.relative_to(ROOT).as_posix(),
        "schema": "PR258_GENERATION_WORKTREE_STATE_V1",
    }
    return {
        **descriptor,
        "state_sha256": _receipt("generation_worktree_state", descriptor),
    }


def _response_class(
    suffix: str,
    nodes: list[list[float]],
):
    return build_response_class_manifold(
        class_id=f"response-class-{suffix}",
        support_kind=ResponseSupportKind.FINITE_SYNTHETIC_SUPPORT,
        provider_id=_receipt("provider", suffix),
        observable_labels=("response-x", "response-y"),
        convention_id=CONVENTION_ID,
        nuisance_policy_id=NUISANCE_ID,
        support_nodes=nodes,
    )


def _class_library(kind: FiniteSupportPerturbationKind | None):
    if kind is FiniteSupportPerturbationKind.EXACT_DUPLICATE:
        left = [[-2.0, 0.0], [-1.8, 0.0], [-2.0, 0.0]]
        right = [[2.0, 0.0], [1.8, 0.0], [2.0, 0.0]]
    elif kind is FiniteSupportPerturbationKind.REFINEMENT:
        left = [[-2.0, 0.0], [-1.9, 0.0], [-1.8, 0.0]]
        right = [[1.8, 0.0], [1.9, 0.0], [2.0, 0.0]]
    elif kind is FiniteSupportPerturbationKind.EXPANSION:
        left = [[-2.2, 0.0], [-2.0, 0.0], [-1.8, 0.0]]
        right = [[1.8, 0.0], [2.0, 0.0], [2.2, 0.0]]
    elif kind is FiniteSupportPerturbationKind.CONTRACTION:
        left = [[-1.8, 0.0]]
        right = [[1.8, 0.0]]
    elif kind is FiniteSupportPerturbationKind.BOUNDARY_RESTRICTION:
        left = [[-2.0, 0.0]]
        right = [[2.0, 0.0]]
    else:
        left = [[-2.0, 0.0], [-1.8, 0.0]]
        right = [[1.8, 0.0], [2.0, 0.0]]
    return (_response_class("left", left), _response_class("right", right))


def _equivalence(classes, covariance):
    return build_response_equivalence_report(
        classes=classes,
        covariance=covariance,
        nuisance_tangent=None,
        equivalence_squared_distance_tolerance=(
            EQUIVALENCE_SQUARED_TOLERANCE
        ),
        absolute_tolerance=ATOL,
        relative_tolerance=RTOL,
    )


def _classify(observations, classes, report, covariance):
    return classify_open_set_response_batch(
        observations=observations,
        classes=classes,
        equivalence_report=report,
        covariance=covariance,
        nuisance_tangent=None,
        unknown_squared_distance_threshold=UNKNOWN_SQUARED_THRESHOLD,
        decision_squared_margin=DECISION_SQUARED_MARGIN,
        covariance_null_tolerance=COVARIANCE_NULL_TOLERANCE,
        absolute_tolerance=ATOL,
        relative_tolerance=RTOL,
        source_separation_gate=source_separation_not_applicable(),
    )


def _known_draws(rng: np.random.Generator) -> tuple[np.ndarray, tuple[str, ...]]:
    count = REPLICATES_PER_CELL
    half = count // 2
    left = rng.normal(loc=(-2.0, 0.0), scale=(0.18, 0.18), size=(half, 2))
    right = rng.normal(loc=(2.0, 0.0), scale=(0.18, 0.18), size=(half, 2))
    values = np.vstack((left, right))
    truth = np.asarray(
        ("response-class-left",) * half
        + ("response-class-right",) * half,
        dtype=object,
    )
    order = rng.permutation(count)
    return values[order], tuple(str(item) for item in truth[order])


def _equivalence_fixture(covariance):
    classes = (
        _response_class("equiv-a", [[0.0, 0.0]]),
        _response_class("equiv-b", [[0.0, 0.0]]),
    )
    responses = {
        item.class_id: {
            item.support_node_ids[0]: [float(index)]
        }
        for index, item in enumerate(classes)
    }
    reopening = build_reopening_observable_spec(
        observable_id=_receipt("reopening", "polarization-like-synthetic"),
        classes=classes,
        added_observable_labels=("added-polarization-like",),
        responses_by_class_and_node=responses,
        joint_covariance=np.eye(3),
        joint_nuisance_response=None,
        joint_nuisance_policy_id=_receipt("joint_nuisance", "none"),
        convention_id=CONVENTION_ID,
    )
    report = build_response_equivalence_report(
        classes=classes,
        covariance=covariance,
        nuisance_tangent=None,
        equivalence_squared_distance_tolerance=(
            EQUIVALENCE_SQUARED_TOLERANCE
        ),
        absolute_tolerance=ATOL,
        relative_tolerance=RTOL,
        reopening_observables=(reopening,),
    )
    return classes, report


def build_payload() -> dict[str, object]:
    rng = np.random.default_rng(MASTER_SEED)
    covariance = np.eye(2)
    known_observations, truth = _known_draws(rng)
    baseline_classes = _class_library(None)
    baseline_equivalence = _equivalence(baseline_classes, covariance)
    known_reports = _classify(
        known_observations,
        baseline_classes,
        baseline_equivalence,
        covariance,
    )

    equivalent_classes, equivalent_report = _equivalence_fixture(covariance)
    equivalent_observations = rng.normal(
        loc=(0.0, 0.0),
        scale=(0.18, 0.18),
        size=(REPLICATES_PER_CELL, 2),
    )
    equivalent_reports = _classify(
        equivalent_observations,
        equivalent_classes,
        equivalent_report,
        covariance,
    )
    unknown_observations = rng.normal(
        loc=(0.0, 7.0),
        scale=(0.25, 0.25),
        size=(REPLICATES_PER_CELL, 2),
    )
    unknown_reports = _classify(
        unknown_observations,
        baseline_classes,
        baseline_equivalence,
        covariance,
    )

    perturbed_reports = {}
    perturbed_classes = {}
    perturbed_equivalence_reports = {}
    perturbation_receipts = {}
    for kind in FiniteSupportPerturbationKind:
        classes = _class_library(kind)
        perturbed_classes[kind] = classes
        report = _equivalence(classes, covariance)
        perturbed_equivalence_reports[kind] = report
        perturbed_reports[kind] = _classify(
            known_observations,
            classes,
            report,
            covariance,
        )
        perturbation_receipts[kind.value] = {
            "class_contract_ids": [
                list(item) for item in report.class_contract_ids
            ],
            "class_response_ids": [
                list(item) for item in report.class_response_ids
            ],
            "equivalence_report_id": report.report_id,
        }

    benchmark = evaluate_open_set_benchmark(
        known_reports=known_reports,
        known_truth_class_ids=truth,
        equivalence_reports=equivalent_reports,
        expected_equivalence_class=equivalent_report.components[0],
        unknown_reports=unknown_reports,
        support_perturbed_reports=perturbed_reports,
        baseline_classes=baseline_classes,
        support_perturbed_classes=perturbed_classes,
        baseline_equivalence_report=baseline_equivalence,
        equivalence_report=equivalent_report,
        support_perturbed_equivalence_reports=(
            perturbed_equivalence_reports
        ),
        master_seed=MASTER_SEED,
        calibration_receipt=CALIBRATION_RECEIPT,
        split_receipt=SPLIT_RECEIPT,
        thresholds_frozen_before_held_out=True,
    )
    if benchmark.status is not OpenSetBenchmarkStatus.MEASURED_PASS:
        raise AssertionError(
            f"PR-258 synthetic benchmark did not pass: {benchmark.status}"
        )
    if (
        _class_library(None)[0].response_content_id
        != _class_library(FiniteSupportPerturbationKind.EXACT_DUPLICATE)[
            0
        ].response_content_id
    ):
        raise AssertionError("exact duplicate canonical identity changed")

    payload = {
        "schema": "PR258_OPEN_SET_SYNTHETIC_BENCHMARK_V2",
        "status": "PASS",
        "work_unit_id": "PR-258",
        "artifact_mode": PR258_ARTIFACT_MODE,
        "covariance_status": PR258_COVARIANCE_STATUS,
        "null_mock_status": PR258_NULL_MOCK_STATUS,
        "owner": PR258_ARTIFACT_OWNER,
        "scope": PR258_ARTIFACT_SCOPE,
        "sky_support_status": PR258_SKY_SUPPORT_STATUS,
        "benchmark_report": benchmark.as_payload(),
        "cell_equivalence_bindings": {
            "baseline_known_and_unknown": (
                baseline_equivalence.report_id
            ),
            "equivalence_cell": equivalent_report.report_id,
            "finite_support_perturbations": {
                kind.value: report.report_id
                for kind, report in sorted(
                    perturbed_equivalence_reports.items(),
                    key=lambda item: item[0].value,
                )
            },
        },
        "protocol": {
            "master_seed": MASTER_SEED,
            "replicates_per_cell": REPLICATES_PER_CELL,
            "maximum_mcse": PR258_MAXIMUM_MCSE,
            "minimum_replicates_per_cell": (
                PR258_MINIMUM_MC_REPLICATES
            ),
            "maximum_replicates_per_cell": (
                PR258_MAXIMUM_MC_REPLICATES
            ),
            "metric_id": "OBSERVABLE_COVARIANCE_SQUARED_DISTANCE_V1",
            "equivalence_squared_distance_tolerance": (
                EQUIVALENCE_SQUARED_TOLERANCE
            ),
            "unknown_squared_distance_threshold": (
                UNKNOWN_SQUARED_THRESHOLD
            ),
            "decision_squared_margin": DECISION_SQUARED_MARGIN,
            "covariance_null_tolerance": COVARIANCE_NULL_TOLERANCE,
            "calibration_receipt": CALIBRATION_RECEIPT,
            "split_receipt": SPLIT_RECEIPT,
            "thresholds_frozen_before_generation": True,
            "held_out_labels_consumed_by_calibration": False,
            "unknown_detection_scope": (
                "conditional on the preregistered displaced synthetic generator"
            ),
        },
        "finite_support_perturbations": perturbation_receipts,
        "provenance": {
            "artifact_mode": PR258_ARTIFACT_MODE,
            "covariance_status": PR258_COVARIANCE_STATUS,
            "target_ref": "origin/research/pr04-multicomponent",
            "target_sha": TARGET_SHA,
            "specification": (
                "docs/research_program/premise_anchor/pr258_spec.yaml"
            ),
            "generating_procedure": (
                "scripts/codex_harness/"
                "run_pr258_open_set_benchmark.py"
            ),
            "generation_worktree_state": _worktree_state(),
            "data_source": "synthetic_only",
            "null_mock_status": PR258_NULL_MOCK_STATUS,
            "owner": PR258_ARTIFACT_OWNER,
            "scope": PR258_ARTIFACT_SCOPE,
            "sky_support_status": PR258_SKY_SUPPORT_STATUS,
            "transfer_source": "none",
            "response_role": "hypothesis_only",
            "pr151_data_used": False,
            "observed_data_used": False,
            "old_rust_output_used": False,
            "native_solver_output_used": False,
        },
        "claim_tier_ceiling": "diagnostic_only",
        "roadmap_claim_level": {
            "scheme": "roadmap_rescue_v1",
            "level": "C2",
        },
        "allowed_use": [
            "finite synthetic response-library software validation",
            "equivalence, unknown and abstention behavior audit",
            "finite-support perturbation sensitivity",
            "next-observable planning",
        ],
        "forbidden_use": [
            "observed anomaly or FLRW departure detection",
            "Bianchi family identification or ranking",
            "native or external-transfer validation",
            "likelihood, posterior, probability, p-value, e-value or evidence",
            "prior or parameter-volume robustness",
        ],
    }
    return _canonical(payload)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--write",
        action="store_true",
        help="replace the frozen PR-258 synthetic diagnostic artifact",
    )
    args = parser.parse_args(argv)
    payload = build_payload()
    if args.write:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(f"WROTE {OUTPUT.relative_to(ROOT)}")
    elif not OUTPUT.is_file():
        print(f"MISSING {OUTPUT.relative_to(ROOT)}", file=sys.stderr)
        return 1
    else:
        frozen = json.loads(OUTPUT.read_text(encoding="utf-8"))
        if frozen != payload:
            print(
                "FAIL frozen PR-258 open-set benchmark drifted",
                file=sys.stderr,
            )
            return 1
    print(
        "PASS PR-258 synthetic open-set benchmark "
        f"replicates_per_cell={REPLICATES_PER_CELL}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
