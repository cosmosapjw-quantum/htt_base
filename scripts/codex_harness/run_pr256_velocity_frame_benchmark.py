#!/usr/bin/env python3
"""Replay the PR-256 synthetic local/global response benchmark.

The script uses only registered analytic/synthetic hypothesis responses and
the PR-222 finite-window operator as a synthetic design input.  It does not
read PR-151, an observational catalogue, an external transfer product, old
Rust science output, or a native solver result.
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
for entry in (ROOT / "htt" / "src", ROOT / "htt"):
    text = str(entry)
    if text not in sys.path:
        sys.path.insert(0, text)

from common.anchor_geometry import (  # noqa: E402
    NormalizerKind,
    NormalizerPurpose,
    NormalizerSpec,
)
from common.anchored_response_geometry import (  # noqa: E402
    anchored_numeric_content_id,
)
from common.revival_bulk_bridge import W as PR222_WINDOW_OPERATOR  # noqa: E402
from common.transfer_registry import TransferSource  # noqa: E402
from htt.departure.velocity_frame_decomposition import (  # noqa: E402
    ResponseProviderAvailability,
    ResponseProviderKind,
    SourceHypothesis,
    SourceResponseGeometryStatus,
    VelocityComponent,
    measure_source_response_geometry,
    register_source_response_provider,
)


MASTER_SEED = 20260728
TOTAL_REPLICATES_PER_CELL = 200_000
TRAIN_REPLICATES = 120_000
VALIDATION_REPLICATES = 40_000
HELD_OUT_REPLICATES = 40_000
MAX_REPLICATES_PER_CELL = 400_000
MAX_MCSE = 0.0025
SEPARATION_THRESHOLD_RADIANS = 0.2
DETECTION_Z = 1.959963984540054
FIRST_ORDER_BETA_CEILING = 0.01
SYNTHETIC_RESPONSE_PER_BETA_SCALE = 1_000.0
TARGET_SHA = "f96403e0e6885b7e23986833ebb75b49630fa265"
OUTPUT = (
    ROOT
    / "docs/generated/pr256_local_global/"
    "velocity_frame_benchmark.json"
)
GENERATOR_SOURCE_ID = "sha256:" + hashlib.sha256(
    Path(__file__).read_bytes()
).hexdigest()

OBSERVABLE_LABELS = (
    "dipole_amplitude",
    "diagonal_Cl",
    "morphology_even",
    "morphology_directional",
    "anchor_stress_diagnostic",
    "finite_window_depth_contrast",
)
METHODS: dict[str, tuple[int, ...]] = {
    "dipole_amplitude": (0,),
    "diagonal_Cl": (1,),
    "morphology_only": (2, 3),
    "anchor_stress_only": (4,),
    "anchored_response_geometry": (0, 1, 2, 3, 4),
    "full_held_out_source_competition": (0, 1, 2, 3, 4, 5),
}
CELL_THETA = {
    "pure_local": (0.004, 0.0),
    "pure_global": (0.0, 0.004),
    "mixed_source": (0.004, 0.004),
    "confusable_sum_only": (0.002, 0.002),
}
DECISIONS = ("ABSTAIN", "LOCAL_CANDIDATE", "GLOBAL_CANDIDATE", "MIXED_CANDIDATE")


def _canonical_float(value: float) -> float:
    if not math.isfinite(value):
        raise ValueError("benchmark values must be finite")
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


def _semantic_receipt(*, role: str, descriptor: object) -> str:
    body = json.dumps(
        {
            "descriptor": descriptor,
            "role": role,
            "schema": "PR256_SYNTHETIC_SEMANTIC_RECEIPT_V1",
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    return "sha256:" + hashlib.sha256(body).hexdigest()


def _validate_theta_domain() -> float:
    maximum_sum = 0.0
    for cell_id, theta in CELL_THETA.items():
        if len(theta) != 2 or any(
            not math.isfinite(value) for value in theta
        ):
            raise ValueError(
                f"{cell_id} beta coordinates must be two finite values"
            )
        source_norm_sum = sum(abs(value) for value in theta)
        if source_norm_sum > FIRST_ORDER_BETA_CEILING:
            raise ValueError(
                f"{cell_id} beta coordinates exceed the registered "
                "first-order domain"
            )
        maximum_sum = max(maximum_sum, source_norm_sum)
    return maximum_sum


TRANSFER_ID = _semantic_receipt(
    role="transfer",
    descriptor={
        "source": "none",
        "response_role": "hypothesis_only",
        "family": "pr256_analytic_synthetic_response_bank",
        "version": 1,
    },
)
MASK_ID = _semantic_receipt(
    role="mask",
    descriptor={
        "kind": "synthetic_full_support",
        "sky_fraction": 1.0,
        "version": 1,
    },
)
PR222_WINDOW_ID = anchored_numeric_content_id(PR222_WINDOW_OPERATOR)
PREDICTION_RULE_ID = _semantic_receipt(
    role="prediction_rule",
    descriptor={
        "rule": "positive GLS coefficient z above fixed threshold",
        "threshold": DETECTION_Z,
        "rank_deficient_action": "ABSTAIN",
        "version": 1,
    },
)
SCORING_RULE_ID = _semantic_receipt(
    role="scoring_rule",
    descriptor={
        "outputs": list(DECISIONS),
        "pure_local_false_global": "GLOBAL_CANDIDATE or MIXED_CANDIDATE",
        "mixed_single_global": "GLOBAL_CANDIDATE",
        "version": 1,
    },
)


def _response_bank(*, confusable: bool) -> tuple[np.ndarray, np.ndarray]:
    depth_contrast = float(
        np.linalg.norm(
            PR222_WINDOW_OPERATOR[:, 0] - PR222_WINDOW_OPERATOR[:, 1]
        )
    )
    local = np.array(
        (1.0, 0.8, 0.3, -0.1, 0.7, -depth_contrast),
        dtype=float,
    )
    if confusable:
        global_value = local.copy()
    else:
        global_value = np.array(
            (1.0, 0.8, 0.3, 0.1, 0.7, depth_contrast),
            dtype=float,
        )
    return (
        SYNTHETIC_RESPONSE_PER_BETA_SCALE * local,
        SYNTHETIC_RESPONSE_PER_BETA_SCALE * global_value,
    )


def _normalizer() -> NormalizerSpec:
    return NormalizerSpec(
        normalizer_id="pr256.synthetic.block_identity",
        kind=NormalizerKind.EXPANSION_NORMALIZED,
        purposes=(NormalizerPurpose.RESPONSE_CONDITIONING,),
        coordinate_labels=("beta_MO_amplitude", "beta_RM_amplitude"),
        coordinate_map=((1.0, 0.0), (0.0, 1.0)),
        source_identity="PR256-SYNTHETIC-HYPOTHESIS-COORDINATES",
        assumptions=("block-preserving local/global coordinate map",),
    )


def _provider(
    *,
    cell_id: str,
    method_id: str,
    hypothesis: SourceHypothesis,
    labels: tuple[str, ...],
    response: np.ndarray,
):
    is_local = hypothesis is SourceHypothesis.LOCAL_BOOST
    return register_source_response_provider(
        provider_id=_semantic_receipt(
            role="response_provider",
            descriptor={
                "cell_id": cell_id,
                "method_id": method_id,
                "hypothesis": hypothesis.value,
                "response_role": "hypothesis_only",
                "version": 1,
            },
        ),
        hypothesis=hypothesis,
        velocity_component=(
            VelocityComponent.BETA_MO
            if is_local
            else VelocityComponent.BETA_RM
        ),
        provider_kind=ResponseProviderKind.SYNTHETIC,
        availability=ResponseProviderAvailability.AVAILABLE,
        observable_labels=labels,
        parameter_labels=(
            ("beta_MO_amplitude",)
            if is_local
            else ("beta_RM_amplitude",)
        ),
        response=response[:, None],
        transfer_id=TRANSFER_ID,
        transfer_source=TransferSource.NONE,
        basis="registered synthetic observable basis",
        epoch_window="registered common synthetic window",
        assumptions=(
            "first-order response",
            "PR-222 window operator used as synthetic design input only",
        ),
        caveats=(
            "hypothesis-only response",
            "not observational validation",
        ),
    )


def _geometry(
    *,
    cell_id: str,
    method_id: str,
    selector: tuple[int, ...],
    local_response: np.ndarray,
    global_response: np.ndarray,
):
    labels = tuple(OBSERVABLE_LABELS[index] for index in selector)
    local = local_response[list(selector)]
    global_value = global_response[list(selector)]
    covariance = np.eye(len(selector), dtype=float)
    return measure_source_response_geometry(
        local_provider=_provider(
            cell_id=cell_id,
            method_id=method_id,
            hypothesis=SourceHypothesis.LOCAL_BOOST,
            labels=labels,
            response=local,
        ),
        global_provider=_provider(
            cell_id=cell_id,
            method_id=method_id,
            hypothesis=SourceHypothesis.GLOBAL_TILT,
            labels=labels,
            response=global_value,
        ),
        covariance=covariance,
        normalizer=_normalizer(),
        covariance_id=anchored_numeric_content_id(covariance),
        mask_id=MASK_ID,
        separation_threshold_radians=SEPARATION_THRESHOLD_RADIANS,
        assumptions=(
            "first-order small-velocity response",
            "identity synthetic covariance",
            "PR-222 finite-window operator is synthetic-only",
        ),
    )


def _decision_summary(
    *,
    geometry_status: SourceResponseGeometryStatus,
    response: np.ndarray,
    held_out: np.ndarray,
) -> dict[str, object]:
    nrep = held_out.shape[0]
    if geometry_status is not SourceResponseGeometryStatus.SEPARABLE_CANDIDATE:
        counts = {decision: 0 for decision in DECISIONS}
        counts["ABSTAIN"] = nrep
    else:
        fisher = response.T @ response
        coefficient_covariance = np.linalg.inv(fisher)
        estimator = coefficient_covariance @ response.T
        coefficients = held_out @ estimator.T
        standard_errors = np.sqrt(np.diag(coefficient_covariance))
        z_local = coefficients[:, 0] / standard_errors[0]
        z_global = coefficients[:, 1] / standard_errors[1]
        local_hit = z_local > DETECTION_Z
        global_hit = z_global > DETECTION_Z
        counts = {
            "ABSTAIN": int(np.count_nonzero(~local_hit & ~global_hit)),
            "LOCAL_CANDIDATE": int(
                np.count_nonzero(local_hit & ~global_hit)
            ),
            "GLOBAL_CANDIDATE": int(
                np.count_nonzero(~local_hit & global_hit)
            ),
            "MIXED_CANDIDATE": int(
                np.count_nonzero(local_hit & global_hit)
            ),
        }
    rates = {
        decision: counts[decision] / nrep for decision in DECISIONS
    }
    mcse = {
        decision: math.sqrt(
            rates[decision] * (1.0 - rates[decision]) / nrep
        )
        for decision in DECISIONS
    }
    return {
        "counts": counts,
        "rates": rates,
        "mcse": mcse,
        "maximum_decision_mcse": max(mcse.values()),
    }


def _cell_payload(cell_id: str, *, seed: int) -> dict[str, object]:
    confusable = cell_id == "confusable_sum_only"
    local_response, global_response = _response_bank(confusable=confusable)
    response = np.column_stack((local_response, global_response))
    theta = np.asarray(CELL_THETA[cell_id], dtype=float)
    mean = response @ theta
    rng = np.random.default_rng(seed)
    draws = mean + rng.normal(
        size=(TOTAL_REPLICATES_PER_CELL, len(OBSERVABLE_LABELS))
    )
    train = draws[:TRAIN_REPLICATES]
    validation = draws[
        TRAIN_REPLICATES : TRAIN_REPLICATES + VALIDATION_REPLICATES
    ]
    held_out = draws[-HELD_OUT_REPLICATES:]
    methods: dict[str, object] = {}
    for method_id, selector in METHODS.items():
        geometry = _geometry(
            cell_id=cell_id,
            method_id=method_id,
            selector=selector,
            local_response=local_response,
            global_response=global_response,
        )
        selected_response = response[list(selector), :]
        decisions = _decision_summary(
            geometry_status=geometry.status,
            response=selected_response,
            held_out=held_out[:, list(selector)],
        )
        methods[method_id] = {
            "geometry": geometry.as_payload(),
            "decisions": decisions,
        }
    return {
        "cell_id": cell_id,
        "seed": seed,
        "theta_beta_MO_beta_RM": list(CELL_THETA[cell_id]),
        "theta_units": "dimensionless_beta_c_equals_1",
        "theta_source_norm_sum": float(np.sum(np.abs(theta))),
        "target_identity": _semantic_receipt(
            role="held_out_target",
            descriptor={
                "cell_id": cell_id,
                "theta_beta_MO_beta_RM": list(CELL_THETA[cell_id]),
                "response_mode": (
                    "confusable_identical_local_global"
                    if confusable
                    else "registered_separated_synthetic"
                ),
            },
        ),
        "response_mode": (
            "confusable_identical_local_global"
            if confusable
            else "registered_separated_synthetic"
        ),
        "partition_receipts": {
            "train": anchored_numeric_content_id(train),
            "validation": anchored_numeric_content_id(validation),
            "held_out": anchored_numeric_content_id(held_out),
        },
        "methods": methods,
    }


def build_payload() -> dict[str, object]:
    maximum_theta_source_norm_sum = _validate_theta_domain()
    cells = [
        _cell_payload(cell_id, seed=MASTER_SEED + 1009 * index)
        for index, cell_id in enumerate(CELL_THETA, start=1)
    ]
    by_id = {cell["cell_id"]: cell for cell in cells}
    pure_local_full = by_id["pure_local"]["methods"][
        "full_held_out_source_competition"
    ]["decisions"]
    mixed_full = by_id["mixed_source"]["methods"][
        "full_held_out_source_competition"
    ]["decisions"]
    false_global_rate = (
        pure_local_full["rates"]["GLOBAL_CANDIDATE"]
        + pure_local_full["rates"]["MIXED_CANDIDATE"]
    )
    false_global_mcse = math.sqrt(
        false_global_rate
        * (1.0 - false_global_rate)
        / HELD_OUT_REPLICATES
    )
    mixed_single_global_rate = mixed_full["rates"]["GLOBAL_CANDIDATE"]
    mixed_single_global_mcse = mixed_full["mcse"]["GLOBAL_CANDIDATE"]
    confusable_abstains = all(
        row["decisions"]["rates"]["ABSTAIN"] == 1.0
        for row in by_id["confusable_sum_only"]["methods"].values()
    )
    baseline_geometry = by_id["pure_local"]["methods"][
        "anchored_response_geometry"
    ]["geometry"]
    full_geometry = by_id["pure_local"]["methods"][
        "full_held_out_source_competition"
    ]["geometry"]
    baseline_angle = baseline_geometry["minimum_principal_angle_radians"]
    full_angle = full_geometry["minimum_principal_angle_radians"]
    observable_gain = (
        full_geometry["joint_rank"] > baseline_geometry["joint_rank"]
        or (
            full_angle is not None
            and baseline_angle is not None
            and full_angle > baseline_angle
        )
    )
    max_observed_mcse = max(
        method["decisions"]["maximum_decision_mcse"]
        for cell in cells
        for method in cell["methods"].values()
    )
    controls = {
        "confusable_mandatory_abstention": confusable_abstains,
        "pure_local_false_global_rate": false_global_rate,
        "pure_local_false_global_mcse": false_global_mcse,
        "pure_local_false_global_ceiling": 0.05 + 3.0 * false_global_mcse,
        "pure_local_false_global_pass": (
            false_global_rate <= 0.05 + 3.0 * false_global_mcse
        ),
        "mixed_source_single_global_rate": mixed_single_global_rate,
        "mixed_source_single_global_mcse": mixed_single_global_mcse,
        "mixed_source_single_global_ceiling": (
            0.05 + 3.0 * mixed_single_global_mcse
        ),
        "mixed_source_single_global_pass": (
            mixed_single_global_rate
            <= 0.05 + 3.0 * mixed_single_global_mcse
        ),
        "added_observable_rank_or_angle_gain": observable_gain,
        "baseline_minimum_angle_radians": baseline_angle,
        "full_minimum_angle_radians": full_angle,
        "maximum_observed_mcse": max_observed_mcse,
        "mcse_pass": max_observed_mcse <= MAX_MCSE,
    }
    passed = (
        controls["confusable_mandatory_abstention"]
        and controls["pure_local_false_global_pass"]
        and controls["mixed_source_single_global_pass"]
        and controls["added_observable_rank_or_angle_gain"]
        and controls["mcse_pass"]
    )
    return _canonical(
        {
            "schema_version": "pr256.velocity_frame_benchmark.v1",
            "status": "PASS" if passed else "FAIL",
            "owner": "HTT",
            "scope": "pre_solver_synthetic_methodology",
            "claim_tier": "diagnostic_only",
            "scientific_artifact_mode": "diagnostic_only",
            "data_source": "synthetic_only",
            "response_role": "hypothesis_only",
            "transfer_source": "none",
            "sky_support_status": (
                "synthetic_directional_feature_space_not_observed_sky"
            ),
            "null_mock_status": (
                "preregistered_synthetic_dgp_only_no_observational_null"
            ),
            "covariance_status": (
                "registered_synthetic_covariance_supported_quotient_only"
            ),
            "pr151_data_used": False,
            "old_rust_science_output_used": False,
            "native_solver_used": False,
            "observational_validation": False,
            "configuration": {
                "master_seed": MASTER_SEED,
                "total_replicates_per_cell": TOTAL_REPLICATES_PER_CELL,
                "train_validation_held_out_split": [0.6, 0.2, 0.2],
                "train_replicates": TRAIN_REPLICATES,
                "validation_replicates": VALIDATION_REPLICATES,
                "held_out_replicates": HELD_OUT_REPLICATES,
                "maximum_replicates_per_cell": MAX_REPLICATES_PER_CELL,
                "maximum_mcse": MAX_MCSE,
                "separation_threshold_radians": (
                    SEPARATION_THRESHOLD_RADIANS
                ),
                "detection_z": DETECTION_Z,
                "theta_units": "dimensionless_beta_c_equals_1",
                "first_order_beta_ceiling": FIRST_ORDER_BETA_CEILING,
                "maximum_theta_source_norm_sum": (
                    maximum_theta_source_norm_sum
                ),
                "response_units": (
                    "synthetic_observable_units_per_dimensionless_beta"
                ),
                "synthetic_response_per_beta_scale": (
                    SYNTHETIC_RESPONSE_PER_BETA_SCALE
                ),
                "partition_use": {
                    "train": "sealed_unused_partition",
                    "validation": "sealed_unused_partition",
                    "held_out": "decision_scoring_only",
                },
                "method_selectors": {
                    method: list(selector)
                    for method, selector in METHODS.items()
                },
            },
            "provenance": {
                "target_ref": "origin/research/pr04-multicomponent",
                "target_sha": TARGET_SHA,
                "generating_procedure": (
                    "scripts/codex_harness/"
                    "run_pr256_velocity_frame_benchmark.py"
                ),
                "generating_procedure_sha256": GENERATOR_SOURCE_ID,
                "transfer_id": TRANSFER_ID,
                "mask_id": MASK_ID,
                "pr222_window_operator_id": PR222_WINDOW_ID,
                "pr222_window_role": (
                    "registered synthetic finite-window design input only"
                ),
                "prediction_rule_id": PREDICTION_RULE_ID,
                "scoring_rule_id": SCORING_RULE_ID,
            },
            "observable_labels": list(OBSERVABLE_LABELS),
            "cells": cells,
            "controls": controls,
            "allowed_use": [
                "synthetic local/global response-method comparison",
                "mandatory-abstention calibration",
                "next-observable planning",
            ],
            "forbidden_use": [
                "observed global-tilt detection",
                "FLRW departure or geometry detection",
                "Bianchi family identification",
                "native-solver validation",
                "posterior odds, Bayes factor, e-value, or evidence",
            ],
            "caveats": [
                "All responses and draws are analytic or synthetic hypotheses.",
                (
                    "Injection coordinates are dimensionless beta with c=1 "
                    "inside the registered 0.01 first-order domain; response "
                    "columns are synthetic observable units per unit beta."
                ),
                "PR-222 W is used only as a synthetic finite-window design input.",
                "No PR-151 partial byte or observational DESI/CMB product is used.",
                "SEPARABLE_CANDIDATE is a tangent-space diagnostic, not detection.",
            ],
        }
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--write",
        action="store_true",
        help="write the canonical generated diagnostic artifact",
    )
    args = parser.parse_args(argv)
    payload = build_payload()
    if args.write:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(
        "PASS PR-256 synthetic local/global benchmark"
        if payload["status"] == "PASS"
        else "FAIL PR-256 synthetic local/global benchmark"
    )
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
