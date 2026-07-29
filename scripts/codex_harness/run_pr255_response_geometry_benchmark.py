#!/usr/bin/env python3
"""Replay the PR-255 synthetic anchored-response benchmark.

The benchmark is deliberately small and synthetic.  It checks the registered
matrix identities, eight phase-diagram cells, mandatory abstention, and Monte
Carlo precision.  It does not read PR-151, an observational catalogue, an
external transfer product, or a native solver output.
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
    AnchorGaugeInterval,
    AnchorGaugeStatus,
    NormalizerKind,
    NormalizerPurpose,
    NormalizerSpec,
)
from common.anchored_response_geometry import (  # noqa: E402
    NonlinearityDGPKind,
    NonlinearityPhaseStatus,
    anchored_numeric_content_id,
    build_nonlinearity_phase_cell,
    build_nonlinearity_phase_diagram,
    measure_anchored_response_geometry,
    measure_schur_morphology_information,
)
from common.orbit_nonlinearity import (  # noqa: E402
    CandidateKind,
    build_candidate_independence_receipt,
    decompose_nonlinearity,
    evaluate_candidate_predictions,
)
from common.transfer_registry import TransferSource  # noqa: E402


MASTER_SEED = 20260728
MIN_REPLICATES = 20_000
MAX_REPLICATES = 400_000
MAX_MCSE = 0.0025
OFF_MANIFOLD_THRESHOLD = 1.959963984540054**2
OUTPUT = (
    ROOT
    / "docs/generated/pr255_response_geometry/"
    "response_geometry_benchmark.json"
)
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


def _array_identity(value: np.ndarray, *, role: str) -> str:
    array = np.ascontiguousarray(value, dtype="<f8")
    header = json.dumps(
        {
            "dtype": "<f8",
            "role": role,
            "schema": "PR255_SYNTHETIC_ARRAY_V1",
            "shape": list(array.shape),
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    digest = hashlib.sha256()
    digest.update(header)
    digest.update(b"\0")
    digest.update(array.tobytes(order="C"))
    return f"sha256:{digest.hexdigest()}"


def _numeric_array_identity(value: np.ndarray) -> str:
    """Match the public numeric-content identity used by candidate receipts."""

    array = np.ascontiguousarray(value, dtype="<f8")
    header = json.dumps(
        {
            "dtype": "<f8",
            "schema": "HTT_NUMERIC_ARRAY_V1",
            "shape": list(array.shape),
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
    digest = hashlib.sha256()
    digest.update(header)
    digest.update(b"\0")
    digest.update(array.tobytes(order="C"))
    return f"sha256:{digest.hexdigest()}"


def _semantic_receipt(*, role: str, descriptor: dict[str, Any]) -> str:
    """Content-bind one explicitly named synthetic semantic descriptor."""

    body = json.dumps(
        {
            "descriptor": descriptor,
            "role": role,
            "schema": "PR255_SYNTHETIC_SEMANTIC_RECEIPT_V1",
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
    return f"sha256:{hashlib.sha256(body).hexdigest()}"


TRANSFER_DESCRIPTOR = {
    "source": "none",
    "response_family": "analytic_synthetic_pr255_phase_bank",
    "role": "hypothesis_only",
    "version": 1,
}
MASK_DESCRIPTOR = {
    "kind": "synthetic_full_support",
    "sky_fraction": 1.0,
    "version": 1,
}
BASELINE_OBSERVABLE_DESCRIPTOR = {
    "role": "baseline",
    "rows": ["synthetic_scalar_0", "synthetic_scalar_1"],
    "version": 1,
}
MORPHOLOGY_OBSERVABLE_DESCRIPTOR = {
    "role": "morphology_increment",
    "rows": ["synthetic_morphology_0"],
    "version": 1,
}
TRANSFER_ID = _semantic_receipt(
    role="transfer",
    descriptor=TRANSFER_DESCRIPTOR,
)
MASK_ID = _semantic_receipt(role="mask", descriptor=MASK_DESCRIPTOR)
BASELINE_ID = _semantic_receipt(
    role="baseline_observable",
    descriptor=BASELINE_OBSERVABLE_DESCRIPTOR,
)
MORPHOLOGY_ID = _semantic_receipt(
    role="morphology_observable",
    descriptor=MORPHOLOGY_OBSERVABLE_DESCRIPTOR,
)
PHASE_COVARIANCE_ID = _numeric_array_identity(np.eye(2))


def _normalizer() -> NormalizerSpec:
    return NormalizerSpec(
        normalizer_id="pr255.synthetic.mes_coordinate_map",
        kind=NormalizerKind.MES_ANCHORED,
        purposes=(
            NormalizerPurpose.RESPONSE_CONDITIONING,
            NormalizerPurpose.PARTIAL_IDENTIFICATION,
            NormalizerPurpose.SOURCE_SCREENING,
        ),
        coordinate_labels=("u0", "u1"),
        coordinate_map=((2.0, 0.0), (0.0, 0.5)),
        source_identity="PR255-SYNTHETIC-TYPED-ANCHOR",
        assumptions=(
            "synthetic-only fixed coordinate map",
            "not an observational MES validation",
        ),
    )


def _point_gauge(value: float, *, cell_id: str) -> AnchorGaugeInterval:
    return AnchorGaugeInterval(
        anchor_id="pr255.synthetic.anchor",
        vector_id=f"pr255.synthetic.{cell_id}",
        lower=value,
        upper=value,
        status=AnchorGaugeStatus.DEFINED,
        conditional_values=(("pr255.synthetic.anchor", value),),
        assumptions=("synthetic phase-diagram fixture",),
    )


def _candidate_competition(
    *,
    winner: CandidateKind,
    held_out_target: np.ndarray,
    matched_target: np.ndarray,
    cell_index: int,
    training_data_id: str,
    split_receipt_id: str,
) -> tuple:
    kinds = (
        CandidateKind.NONLINEAR,
        CandidateKind.LINEAR,
        CandidateKind.SYSTEMATICS,
        CandidateKind.FRAME_MISMATCH,
        CandidateKind.DERIVATIVE_FAILURE,
    )
    values = []
    for candidate_index, kind in enumerate(kinds):
        candidate_id = f"pr255.cell{cell_index}.{kind.value.lower()}"
        model_config_id = (
            "sha256:"
            + f"{1000 + 10 * cell_index + candidate_index:064x}"
        )
        receipt = build_candidate_independence_receipt(
            candidate_id=candidate_id,
            model_config_id=model_config_id,
            training_data_id=training_data_id,
            held_out_target=held_out_target,
            matched_injection_target=matched_target,
            fit_receipt_id=(
                "sha256:"
                + f"{2000 + 10 * cell_index + candidate_index:064x}"
            ),
            split_receipt_id=split_receipt_id,
        )
        offset = 0.02 if kind is winner else 1.0
        values.append(
            evaluate_candidate_predictions(
                candidate_id=candidate_id,
                kind=kind,
                held_out_prediction=held_out_target + offset,
                held_out_target=held_out_target,
                matched_injection_prediction=matched_target + offset,
                matched_injection_target=matched_target,
                model_config_id=model_config_id,
                independence_receipt=receipt,
            )
        )
    return tuple(values)


def _phase_report(
    rng: np.random.Generator,
    *,
    replicates: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    split_counts = {
        "train": int(0.6 * replicates),
        "validation": int(0.2 * replicates),
        "held_out": replicates - int(0.8 * replicates),
    }
    dgp_config = (
        (
            NonlinearityDGPKind.LINEAR_ANCHOR_COMPATIBLE,
            0.5,
            0.0,
            None,
            NonlinearityPhaseStatus.LINEAR_PREMISE_COMPATIBLE,
        ),
        (
            NonlinearityDGPKind.LINEAR_PREMISE_MISMATCH,
            1.5,
            0.0,
            None,
            NonlinearityPhaseStatus.LINEAR_PREMISE_MISMATCH,
        ),
        (
            NonlinearityDGPKind.NONLINEAR_ANCHOR_COMPATIBLE,
            0.5,
            5.0,
            CandidateKind.NONLINEAR,
            NonlinearityPhaseStatus.NONLINEAR_WITHIN_ANCHOR,
        ),
        (
            NonlinearityDGPKind.NONLINEAR_PLUS_EXCEEDANCE,
            1.5,
            5.0,
            CandidateKind.NONLINEAR,
            NonlinearityPhaseStatus.NONLINEAR_AND_EXCEEDANCE,
        ),
        (
            NonlinearityDGPKind.OBSERVER_FRAME_MISMATCH,
            0.5,
            5.0,
            CandidateKind.FRAME_MISMATCH,
            NonlinearityPhaseStatus.UNATTRIBUTED_OFF_MANIFOLD,
        ),
        (
            NonlinearityDGPKind.DERIVATIVE_CONTROL_FAILURE,
            0.5,
            5.0,
            CandidateKind.DERIVATIVE_FAILURE,
            NonlinearityPhaseStatus.UNATTRIBUTED_OFF_MANIFOLD,
        ),
        (
            NonlinearityDGPKind.SYSTEMATICS_MIMIC,
            0.5,
            5.0,
            CandidateKind.SYSTEMATICS,
            NonlinearityPhaseStatus.UNATTRIBUTED_OFF_MANIFOLD,
        ),
        (
            NonlinearityDGPKind.UNKNOWN_SOURCE,
            0.5,
            5.0,
            None,
            NonlinearityPhaseStatus.UNATTRIBUTED_OFF_MANIFOLD,
        ),
    )
    cells = []
    diagnostics = []
    false_positive_values: np.ndarray | None = None
    for cell_index, (
        kind,
        gauge_value,
        perpendicular_signal,
        winner,
        expected_status,
    ) in enumerate(dgp_config):
        residual_draws = rng.normal(size=(replicates, 2))
        residual_draws[:, 1] += perpendicular_signal
        off_manifold = residual_draws[:, 1] ** 2 > OFF_MANIFOLD_THRESHOLD
        if kind is NonlinearityDGPKind.LINEAR_ANCHOR_COMPATIBLE:
            false_positive_values = off_manifold
        registered_decision = (
            ~off_manifold if perpendicular_signal == 0.0 else off_manifold
        )
        rate = float(np.mean(registered_decision))
        mcse = math.sqrt(rate * (1.0 - rate) / replicates)

        partition_draws = rng.normal(size=replicates)
        train_stop = split_counts["train"]
        validation_stop = train_stop + split_counts["validation"]
        training_values = partition_draws[:train_stop]
        validation_values = partition_draws[train_stop:validation_stop]
        held_out_target = partition_draws[validation_stop:]
        matched_target = validation_values + 0.25
        training_data_id = _numeric_array_identity(training_values)
        validation_data_id = _numeric_array_identity(matched_target)
        held_out_data_receipt = _numeric_array_identity(held_out_target)
        split_receipt_id = _array_identity(
            np.asarray(
                [
                    MASTER_SEED,
                    cell_index,
                    split_counts["train"],
                    split_counts["validation"],
                    split_counts["held_out"],
                ],
                dtype=float,
            ),
            role=f"{kind.value}:split_policy",
        )
        candidates = (
            ()
            if winner is None
            else _candidate_competition(
                winner=winner,
                held_out_target=held_out_target,
                matched_target=matched_target,
                cell_index=cell_index,
                training_data_id=training_data_id,
                split_receipt_id=split_receipt_id,
            )
        )
        held_receipt = (
            None if not candidates else candidates[0].held_out_data_id
        )
        matched_receipt = (
            None
            if not candidates
            else candidates[0].matched_injection_data_id
        )
        representative_residual = (
            (1.0, 0.0)
            if perpendicular_signal == 0.0
            else (0.0, perpendicular_signal)
        )
        nonlinearity = decompose_nonlinearity(
            residual=representative_residual,
            tangent_response=((1.0,), (0.0,)),
            covariance=np.eye(2),
            transfer_id=TRANSFER_ID,
            mask_id=MASK_ID,
            covariance_id=PHASE_COVARIANCE_ID,
            candidates=candidates,
            held_out_receipt=held_receipt,
            matched_injection_receipt=matched_receipt,
            off_manifold_tolerance=OFF_MANIFOLD_THRESHOLD,
            null_residual_tolerance=1.0e-12,
            nonlinear_gain_margin=0.1,
        )
        cell = build_nonlinearity_phase_cell(
            cell_id=f"pr255.{kind.value.lower()}",
            dgp_kind=kind,
            anchor_gauge=_point_gauge(
                gauge_value, cell_id=kind.value.lower()
            ),
            nonlinearity=nonlinearity,
        )
        cell_payload = cell.as_payload()
        if cell.status is not expected_status:
            raise RuntimeError(
                f"{kind.value}: observed {cell.status.value}, "
                f"expected {expected_status.value}"
            )
        cells.append(cell)
        diagnostics.append(
            {
                "dgp_kind": kind.value,
                "replicates": replicates,
                "registered_decision_metric": (
                    "linear_acceptance_rate"
                    if perpendicular_signal == 0.0
                    else "off_manifold_detection_power"
                ),
                "registered_decision_rate": rate,
                "registered_decision_mcse": mcse,
                "observed_status": cell.status.value,
                "expected_status": expected_status.value,
                "attribution_status": (
                    nonlinearity.attribution_status.value
                ),
                "stress_interval": [gauge_value, gauge_value],
                "t_parallel": nonlinearity.tangent_statistic,
                "t_perp": nonlinearity.perpendicular_statistic,
                "delta_nl": nonlinearity.delta_nl,
                "delta_nl_status": (
                    "DEFINED"
                    if nonlinearity.delta_nl is not None
                    else "NOT_COMPUTED_NO_NONLINEAR_MANIFOLD_DISTANCE"
                ),
                "nonlinear_candidate_gains": (
                    cell_payload["nonlinear_candidate_gains"]
                ),
                "mandatory_abstention": (
                    expected_status
                    is NonlinearityPhaseStatus.UNATTRIBUTED_OFF_MANIFOLD
                ),
                "source_competition_replicated": False,
                "source_competition_evaluation_count_per_split": (
                    0 if not candidates else split_counts["held_out"]
                ),
                "partition_receipts": {
                    "training": training_data_id,
                    "validation": validation_data_id,
                    "held_out": held_out_data_receipt,
                    "split_policy": split_receipt_id,
                    "validation_role": "matched_injection_evaluation",
                },
                "coverage": (
                    {
                        "status": (
                            "PASS"
                            if rate >= 0.95 - 3.0 * mcse
                            else "FAIL"
                        ),
                        "estimand": (
                            "linear_compatibility_region_coverage"
                        ),
                        "nominal": 0.95,
                        "rate": rate,
                        "mcse": mcse,
                        "three_mcse_floor": 0.95 - 3.0 * mcse,
                    }
                    if perpendicular_signal == 0.0
                    else {
                        "status": "NOT_APPLICABLE_NONLINEAR_DGP",
                        "estimand": None,
                        "nominal": None,
                        "rate": None,
                        "mcse": None,
                        "three_mcse_floor": None,
                    }
                ),
                "status": (
                    "PASS"
                    if (
                        mcse <= MAX_MCSE
                        and (
                            perpendicular_signal != 0.0
                            or rate >= 0.95 - 3.0 * mcse
                        )
                    )
                    else "INCONCLUSIVE_MC_PRECISION"
                ),
            }
        )

    if false_positive_values is None:
        raise RuntimeError("linear false-positive cell was not executed")
    false_positive_rate = float(np.mean(false_positive_values))
    false_positive_mcse = math.sqrt(
        false_positive_rate * (1.0 - false_positive_rate) / replicates
    )
    phase = build_nonlinearity_phase_diagram(
        cells=tuple(cells),
        master_seed=MASTER_SEED,
        transfer_id=TRANSFER_ID,
        transfer_source=TransferSource.NONE,
    )
    diagnostics_summary = {
        "cells": diagnostics,
        "linear_false_off_manifold_rate": false_positive_rate,
        "linear_false_off_manifold_mcse": false_positive_mcse,
        "nominal_size_upper_3mcse": 0.05 + 3.0 * false_positive_mcse,
        "nominal_size_pass": (
            false_positive_rate
            <= 0.05 + 3.0 * false_positive_mcse
        ),
        "all_cell_mcse_pass": all(
            row["registered_decision_mcse"] <= MAX_MCSE
            for row in diagnostics
        ),
        "all_phase_statuses_pass": all(
            row["observed_status"] == row["expected_status"]
            for row in diagnostics
        ),
        "all_applicable_coverage_pass": all(
            row["coverage"]["status"]
            in {"PASS", "NOT_APPLICABLE_NONLINEAR_DGP"}
            for row in diagnostics
        ),
    }
    return phase.as_payload(), diagnostics_summary


def build_payload() -> dict[str, Any]:
    rng = np.random.default_rng(MASTER_SEED)
    normalizer = _normalizer()
    geometry_covariance = np.diag((1.0, 2.0, 0.0))
    joint_covariance = np.asarray(
        (
            (1.0, 0.0, 0.25),
            (0.0, 2.0, 0.0),
            (0.25, 0.0, 1.0),
        )
    )
    geometry = measure_anchored_response_geometry(
        response=((1.0, 0.0), (0.0, 1.0), (0.25, 0.5)),
        covariance=geometry_covariance,
        normalizer=normalizer,
        parameter_labels=("u0", "u1"),
        transfer_id=TRANSFER_ID,
        transfer_source=TransferSource.NONE,
        mask_id=MASK_ID,
        covariance_id=anchored_numeric_content_id(geometry_covariance),
        nuisance_response=((1.0,), (1.0,), (0.0,)),
        comparison_response=((0.0, 1.0), (1.0, 0.0), (0.5, 0.25)),
    )
    schur = measure_schur_morphology_information(
        baseline_response=((1.0, 0.0), (0.0, 0.5)),
        morphology_response=((0.5, 1.0),),
        joint_covariance=joint_covariance,
        normalizer=normalizer,
        parameter_labels=("u0", "u1"),
        transfer_id=TRANSFER_ID,
        transfer_source=TransferSource.NONE,
        mask_id=MASK_ID,
        joint_covariance_id=anchored_numeric_content_id(joint_covariance),
        baseline_observable_id=BASELINE_ID,
        morphology_observable_id=MORPHOLOGY_ID,
    )

    replicates = MIN_REPLICATES
    while True:
        phase, diagnostics = _phase_report(rng, replicates=replicates)
        if diagnostics["all_cell_mcse_pass"] or replicates >= MAX_REPLICATES:
            break
        replicates *= 2
    status = (
        "PASS"
        if (
            diagnostics["all_cell_mcse_pass"]
            and diagnostics["all_phase_statuses_pass"]
            and diagnostics["all_applicable_coverage_pass"]
            and diagnostics["nominal_size_pass"]
        )
        else "INCONCLUSIVE_MC_PRECISION"
    )
    payload = {
        "schema_version": "pr255.response_geometry_benchmark.v1",
        "work_unit_id": "PR-255",
        "owner": "HTT",
        "scope": "pre_solver_synthetic_methodology",
        "claim_tier": "diagnostic_only",
        "scientific_artifact_mode": "diagnostic_only",
        "data_source": "synthetic_only",
        "pr151_data_used": False,
        "native_solver_used": False,
        "observational_validation": False,
        "transfer_source": TransferSource.NONE.value,
        "response_role": "hypothesis_only_analytic_synthetic",
        "provenance": {
            "target_sha": "090525951cc30ad29da7fa8ae0a11bd4553f5b4f",
            "specification": (
                "docs/research_program/premise_anchor/pr255_spec.yaml"
            ),
            "generating_procedure": (
                "scripts/codex_harness/"
                "run_pr255_response_geometry_benchmark.py"
            ),
            "response_contract": (
                "htt/src/common/anchored_response_geometry.py"
            ),
            "source_competition_contract": (
                "htt/src/common/orbit_nonlinearity.py"
            ),
            "exact_replay_note": (
                "candidate commit identity is bound later by the candidate "
                "seal; this receipt binds its synthetic inputs and outputs"
            ),
        },
        "caveats": [
            "synthetic methodology cell only",
            "no PR-151 partial data or observational catalogue",
            "no external or native transfer provider",
            "source competition is one identity-bound representative "
            "evaluation, not replicated classification validation",
            "Delta_NL is not computed without a registered nonlinear "
            "model-manifold distance",
        ],
        "configuration": {
            "master_seed": MASTER_SEED,
            "replicates_per_cell": replicates,
            "minimum_replicates_per_cell": MIN_REPLICATES,
            "maximum_replicates_per_cell": MAX_REPLICATES,
            "maximum_mcse": MAX_MCSE,
            "train_validation_held_out_split": [0.6, 0.2, 0.2],
            "off_manifold_threshold": OFF_MANIFOLD_THRESHOLD,
            "normalizer_id": normalizer.normalizer_id,
            "normalizer_source_identity": normalizer.source_identity,
        },
        "input_receipts": {
            "synthetic_rng_stream": _array_identity(
                np.asarray([MASTER_SEED, replicates], dtype=float),
                role="rng_configuration",
            ),
            "transfer": {
                "id": TRANSFER_ID,
                "descriptor": TRANSFER_DESCRIPTOR,
            },
            "mask": {
                "id": MASK_ID,
                "descriptor": MASK_DESCRIPTOR,
            },
            "baseline_observable": {
                "id": BASELINE_ID,
                "descriptor": BASELINE_OBSERVABLE_DESCRIPTOR,
            },
            "morphology_observable": {
                "id": MORPHOLOGY_ID,
                "descriptor": MORPHOLOGY_OBSERVABLE_DESCRIPTOR,
            },
            "covariance_ids": {
                "anchored_geometry": anchored_numeric_content_id(
                    geometry_covariance
                ),
                "schur_joint": anchored_numeric_content_id(
                    joint_covariance
                ),
                "phase_nonlinearity": PHASE_COVARIANCE_ID,
            },
            "split_policy": "per-cell content-bound 60/20/20 partition",
        },
        "anchored_response_geometry": geometry.as_payload(),
        "schur_morphology_information": schur.as_payload(),
        "phase_diagram": phase,
        "diagnostics": diagnostics,
        "status": status,
        "claim_boundary": {
            "allowed": [
                "synthetic pre-solver response diagnostic",
                "matrix-valued conditional morphology information",
                "mandatory abstention methodology",
            ],
            "forbidden": [
                "FLRW departure or geometry detection",
                "Bianchi family identification",
                "native solver validation",
                "observational inference",
                "information gain from anchor scaling",
            ],
        },
    }
    return _canonical(payload)


def _write(payload: dict[str, Any]) -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--write",
        action="store_true",
        help="replace the frozen synthetic receipt",
    )
    args = parser.parse_args(argv)
    payload = build_payload()
    if args.write:
        _write(payload)
        print(f"WROTE {OUTPUT.relative_to(ROOT)}")
        return 0
    if not OUTPUT.is_file():
        print(f"MISSING {OUTPUT.relative_to(ROOT)}", file=sys.stderr)
        return 1
    frozen = json.loads(OUTPUT.read_text(encoding="utf-8"))
    if frozen != payload:
        print("FAIL frozen PR-255 benchmark receipt drifted", file=sys.stderr)
        return 1
    if payload["status"] != "PASS":
        print(
            f"FAIL PR-255 benchmark status={payload['status']}",
            file=sys.stderr,
        )
        return 1
    print("PASS PR-255 synthetic response-geometry benchmark")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
