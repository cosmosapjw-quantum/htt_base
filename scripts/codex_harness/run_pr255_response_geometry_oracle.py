#!/usr/bin/env python3
"""Independent direct-Fisher oracle for the PR-255 Schur implementation.

This synthetic executable compares the public Schur report against the
ordinary joint Gaussian information identity

    D.T @ R.T @ inv(C) @ R @ D

for a frozen randomized grid. It also requires six unit-congruent
near-singular cases, including the scalar re-admission gap, to refuse a
conditional mode excluded by the joint support quotient, plus three cases
just above that boundary to remain measured. It is an algebraic
implementation oracle, not an observational validation, an independent
scientific data source, or a candidate review receipt.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
import sys

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
    AnchoredResponseStatus,
    SchurMorphologyStatus,
    anchored_numeric_content_id,
    measure_schur_morphology_information,
)
from common.transfer_registry import TransferSource  # noqa: E402


SEED = 20260729
CASES = 300
RTOL = 2.0e-10
ATOL = 2.0e-10


def _semantic_receipt(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


TRANSFER_ID = _semantic_receipt("pr255-direct-fisher-synthetic-transfer-v1")
MASK_ID = _semantic_receipt("pr255-direct-fisher-full-support-mask-v1")
BASELINE_ID = _semantic_receipt("pr255-direct-fisher-baseline-v1")
MORPHOLOGY_ID = _semantic_receipt("pr255-direct-fisher-morphology-v1")


def _invertible_map(
    rng: np.random.Generator,
    dimension: int,
) -> np.ndarray:
    while True:
        value = rng.normal(size=(dimension, dimension))
        if abs(float(np.linalg.det(value))) > 0.2:
            return value


def main() -> int:
    rng = np.random.default_rng(SEED)
    maximum_error = 0.0
    for case in range(CASES):
        parameter_dimension = 3
        baseline_rows = 3
        morphology_rows = 2
        joint_rows = baseline_rows + morphology_rows

        covariance_root = rng.normal(size=(joint_rows, joint_rows))
        covariance = (
            covariance_root @ covariance_root.T
            + 0.5 * np.eye(joint_rows)
        )
        baseline = rng.normal(
            size=(baseline_rows, parameter_dimension)
        )
        morphology = rng.normal(
            size=(morphology_rows, parameter_dimension)
        )
        coordinate_map = _invertible_map(rng, parameter_dimension)
        labels = tuple(
            f"u{index}" for index in range(parameter_dimension)
        )
        normalizer = NormalizerSpec(
            normalizer_id=f"pr255.direct-fisher-oracle.{case}",
            kind=NormalizerKind.MES_ANCHORED,
            purposes=(NormalizerPurpose.RESPONSE_CONDITIONING,),
            coordinate_labels=labels,
            coordinate_map=tuple(
                tuple(float(item) for item in row)
                for row in coordinate_map
            ),
            source_identity="PR255-INDEPENDENT-DIRECT-FISHER-ORACLE",
            assumptions=(
                "synthetic positive-definite joint covariance",
                "no observational or native-solver input",
            ),
        )
        report = measure_schur_morphology_information(
            baseline_response=baseline,
            morphology_response=morphology,
            joint_covariance=covariance,
            normalizer=normalizer,
            parameter_labels=labels,
            transfer_id=TRANSFER_ID,
            transfer_source=TransferSource.NONE,
            mask_id=MASK_ID,
            joint_covariance_id=anchored_numeric_content_id(covariance),
            baseline_observable_id=BASELINE_ID,
            morphology_observable_id=MORPHOLOGY_ID,
        )

        joint_response = np.vstack((baseline, morphology))
        direct = (
            coordinate_map.T
            @ joint_response.T
            @ np.linalg.inv(covariance)
            @ joint_response
            @ coordinate_map
        )
        observed = np.asarray(report.joint_information, dtype=float)
        error = float(np.max(np.abs(observed - direct)))
        maximum_error = max(maximum_error, error)
        if not np.allclose(
            observed,
            direct,
            rtol=RTOL,
            atol=ATOL,
        ):
            print(
                f"FAIL case={case} Schur/direct-Fisher mismatch "
                f"max_abs_error={error:.17g}",
                file=sys.stderr,
            )
            return 1
        for geometry in (
            report.baseline_geometry,
            report.conditional_morphology_geometry,
        ):
            if geometry.rank != geometry.original_rank:
                print(
                    f"FAIL case={case} invertible anchor changed rank",
                    file=sys.stderr,
                )
                return 1

    near_singular_refusals = 0
    near_singular_retained = 0
    support_rtol = 1.0e-12
    labels = ("u0",)
    normalizer = NormalizerSpec(
        normalizer_id="pr255.direct-fisher-near-singular",
        kind=NormalizerKind.MES_ANCHORED,
        purposes=(NormalizerPurpose.RESPONSE_CONDITIONING,),
        coordinate_labels=labels,
        coordinate_map=((1.0,),),
        source_identity="PR255-NEAR-SINGULAR-REFUSAL-ORACLE",
        assumptions=(
            "synthetic near-singular joint covariance",
            "one inherited supported quotient",
        ),
    )
    unit_scales = (
        (1.0, 1.0),
        (1.0e-8, 1.0e8),
        (1.0e8, 1.0e-8),
    )
    for epsilon in (1.0e-13, 1.5e-12):
        covariance = np.asarray(
            ((1.0, 1.0 - epsilon), (1.0 - epsilon, 1.0))
        )
        for baseline_scale, morphology_scale in unit_scales:
            unit_map = np.diag((baseline_scale, morphology_scale))
            transformed_covariance = unit_map @ covariance @ unit_map
            report = measure_schur_morphology_information(
                baseline_response=((baseline_scale,),),
                morphology_response=((0.0,),),
                joint_covariance=transformed_covariance,
                normalizer=normalizer,
                parameter_labels=labels,
                transfer_id=TRANSFER_ID,
                transfer_source=TransferSource.NONE,
                mask_id=MASK_ID,
                joint_covariance_id=anchored_numeric_content_id(
                    transformed_covariance
                ),
                baseline_observable_id=BASELINE_ID,
                morphology_observable_id=MORPHOLOGY_ID,
                rtol=support_rtol,
            )
            response = np.asarray(((baseline_scale,), (0.0,)))
            inverse_standard_deviation = 1.0 / np.sqrt(
                np.diag(transformed_covariance)
            )
            standardized_covariance = (
                inverse_standard_deviation[:, None]
                * transformed_covariance
                * inverse_standard_deviation[None, :]
            )
            standardized_response = (
                inverse_standard_deviation[:, None] * response
            )
            direct = (
                standardized_response.T
                @ np.linalg.pinv(
                    standardized_covariance,
                    rcond=support_rtol,
                    hermitian=True,
                )
                @ standardized_response
            )
            if not np.allclose(
                direct, ((0.25,),), rtol=1.0e-9, atol=1.0e-9
            ):
                print(
                    "FAIL near-singular direct-pseudoinverse control",
                    file=sys.stderr,
                )
                return 1
            if (
                report.status
                is not SchurMorphologyStatus.OUTSIDE_SUPPORTED_QUOTIENT
                or report.conditional_morphology_geometry.status
                is not AnchoredResponseStatus.OUTSIDE_SUPPORTED_QUOTIENT
                or report.exact_one_dimensional_reduction
            ):
                print(
                    "FAIL near-singular joint support was re-admitted by "
                    f"Schur epsilon={epsilon:.1e} "
                    f"units=({baseline_scale:.1e},{morphology_scale:.1e})",
                    file=sys.stderr,
                )
                return 1
            near_singular_refusals += 1

    retained_epsilon = 2.5e-12
    retained_covariance = np.asarray(
        (
            (1.0, 1.0 - retained_epsilon),
            (1.0 - retained_epsilon, 1.0),
        )
    )
    for baseline_scale, morphology_scale in unit_scales:
        unit_map = np.diag((baseline_scale, morphology_scale))
        transformed_covariance = (
            unit_map @ retained_covariance @ unit_map
        )
        report = measure_schur_morphology_information(
            baseline_response=((baseline_scale,),),
            morphology_response=((0.0,),),
            joint_covariance=transformed_covariance,
            normalizer=normalizer,
            parameter_labels=labels,
            transfer_id=TRANSFER_ID,
            transfer_source=TransferSource.NONE,
            mask_id=MASK_ID,
            joint_covariance_id=anchored_numeric_content_id(
                transformed_covariance
            ),
            baseline_observable_id=BASELINE_ID,
            morphology_observable_id=MORPHOLOGY_ID,
            rtol=support_rtol,
        )
        if (
            report.status is not SchurMorphologyStatus.MEASURED
            or report.conditional_morphology_geometry.status
            is not AnchoredResponseStatus.MEASURED
            or not report.exact_one_dimensional_reduction
        ):
            print(
                "FAIL retained near-singular joint support was removed by "
                f"Schur epsilon={retained_epsilon:.1e} "
                f"units=({baseline_scale:.1e},{morphology_scale:.1e})",
                file=sys.stderr,
            )
            return 1
        near_singular_retained += 1

    print(
        "PASS PR-255 direct-Fisher oracle "
        f"cases={CASES} seed={SEED} "
        f"max_abs_error={maximum_error:.3e} "
        f"near_singular_refusals={near_singular_refusals} "
        f"near_singular_retained={near_singular_retained}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
