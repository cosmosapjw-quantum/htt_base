#!/usr/bin/env python3
"""Independent numerical oracle for PR-256 source-response geometry.

The public implementation inherits the PR-255 eigen-supported whitener.  This
oracle deliberately uses a Cholesky whitener and a direct nuisance projector
on strictly positive-definite random covariances, then compares ranks,
singular spectra, principal angles, and abstention status.  It also checks the
velocity closure directly.  No repository data or observational product is
read.
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
    anchored_numeric_content_id,
)
from common.transfer_registry import TransferSource  # noqa: E402
from htt.departure.velocity_frame_decomposition import (  # noqa: E402
    ResponseProviderAvailability,
    ResponseProviderKind,
    SourceHypothesis,
    SourceResponseGeometryStatus,
    VelocityComponent,
    VelocityDecompositionStatus,
    build_velocity_frame_decomposition,
    measure_source_response_geometry,
    register_source_response_provider,
)


SEED = 20260729
CASES = 300
RTOL = 1.0e-12
ANGLE_THRESHOLD = 0.2


def _receipt(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


TRANSFER_ID = _receipt("pr256-oracle-synthetic-transfer-none")
MASK_ID = _receipt("pr256-oracle-synthetic-full-mask")


def _provider(
    *,
    case: int,
    hypothesis: SourceHypothesis,
    response: np.ndarray,
    observable_labels: tuple[str, ...],
):
    local = hypothesis is SourceHypothesis.LOCAL_BOOST
    return register_source_response_provider(
        provider_id=_receipt(f"pr256-oracle-provider-{case}-{hypothesis.value}"),
        hypothesis=hypothesis,
        velocity_component=(
            VelocityComponent.BETA_MO
            if local
            else VelocityComponent.BETA_RM
        ),
        provider_kind=ResponseProviderKind.SYNTHETIC,
        availability=ResponseProviderAvailability.AVAILABLE,
        observable_labels=observable_labels,
        parameter_labels=(
            ("beta_MO_amplitude",)
            if local
            else ("beta_RM_amplitude",)
        ),
        response=response,
        transfer_id=TRANSFER_ID,
        transfer_source=TransferSource.NONE,
        basis="oracle Cartesian basis",
        epoch_window="oracle common synthetic window",
        assumptions=("strictly positive-definite covariance",),
        caveats=("independent numerical oracle only",),
    )


def _direct_geometry(
    *,
    response: np.ndarray,
    covariance: np.ndarray,
    nuisance: np.ndarray,
    scaling: np.ndarray,
) -> tuple[int, tuple[float, ...], float]:
    cholesky = np.linalg.cholesky(covariance)
    whitener = np.linalg.inv(cholesky)
    nuisance_white = whitener @ nuisance
    projector = np.eye(response.shape[0]) - (
        nuisance_white @ np.linalg.pinv(nuisance_white)
    )
    anchored = projector @ whitener @ response @ scaling
    singular = np.linalg.svd(anchored, compute_uv=False)
    rank = int(np.count_nonzero(singular > RTOL * singular[0]))
    left = anchored[:, :1]
    right = anchored[:, 1:]
    left_basis = np.linalg.svd(left, full_matrices=False)[0][:, :1]
    right_basis = np.linalg.svd(right, full_matrices=False)[0][:, :1]
    cosine = float(
        np.linalg.svd(left_basis.T @ right_basis, compute_uv=False)[0]
    )
    angle = float(np.arccos(np.clip(cosine, -1.0, 1.0)))
    return rank, tuple(float(value) for value in singular), angle


def main() -> int:
    rng = np.random.default_rng(SEED)
    maximum_singular_error = 0.0
    maximum_angle_error = 0.0
    for case in range(CASES):
        nobs = 5 + case % 3
        raw = rng.normal(size=(nobs, nobs))
        covariance = raw @ raw.T + 0.5 * np.eye(nobs)
        nuisance = rng.normal(size=(nobs, 1))
        response = rng.normal(size=(nobs, 2))
        scales = np.exp(rng.normal(scale=0.6, size=2))
        scaling = np.diag(scales)
        labels = tuple(f"oracle_observable_{index}" for index in range(nobs))
        normalizer = NormalizerSpec(
            normalizer_id=f"pr256-oracle-normalizer-{case}",
            kind=NormalizerKind.EXPANSION_NORMALIZED,
            purposes=(NormalizerPurpose.RESPONSE_CONDITIONING,),
            coordinate_labels=("beta_MO_amplitude", "beta_RM_amplitude"),
            coordinate_map=(
                (float(scales[0]), 0.0),
                (0.0, float(scales[1])),
            ),
            source_identity="PR256-INDEPENDENT-CHOLESKY-ORACLE",
            assumptions=("block-diagonal invertible scaling",),
        )
        public = measure_source_response_geometry(
            local_provider=_provider(
                case=case,
                hypothesis=SourceHypothesis.LOCAL_BOOST,
                response=response[:, :1],
                observable_labels=labels,
            ),
            global_provider=_provider(
                case=case,
                hypothesis=SourceHypothesis.GLOBAL_TILT,
                response=response[:, 1:],
                observable_labels=labels,
            ),
            covariance=covariance,
            normalizer=normalizer,
            covariance_id=anchored_numeric_content_id(covariance),
            mask_id=MASK_ID,
            nuisance_response=nuisance,
            separation_threshold_radians=ANGLE_THRESHOLD,
            rtol=RTOL,
        )
        direct_rank, direct_singular, direct_angle = _direct_geometry(
            response=response,
            covariance=covariance,
            nuisance=nuisance,
            scaling=scaling,
        )
        if public.joint_rank != direct_rank:
            raise AssertionError(
                f"case {case}: rank {public.joint_rank} != {direct_rank}"
            )
        singular_error = float(
            np.max(
                np.abs(
                    np.asarray(public.joint_singular_values)
                    - np.asarray(direct_singular)
                )
            )
        )
        maximum_singular_error = max(maximum_singular_error, singular_error)
        if not np.allclose(
            public.joint_singular_values,
            direct_singular,
            rtol=2.0e-10,
            atol=2.0e-11,
        ):
            raise AssertionError(
                f"case {case}: singular spectrum mismatch "
                f"{public.joint_singular_values} != {direct_singular}"
            )
        if public.minimum_principal_angle_radians is None:
            raise AssertionError(f"case {case}: missing principal angle")
        angle_error = abs(
            public.minimum_principal_angle_radians - direct_angle
        )
        maximum_angle_error = max(maximum_angle_error, angle_error)
        if angle_error > 2.0e-10:
            raise AssertionError(
                f"case {case}: principal angle mismatch "
                f"{public.minimum_principal_angle_radians} != {direct_angle}"
            )
        expected_status = (
            SourceResponseGeometryStatus.SEPARABLE_CANDIDATE
            if direct_rank == 2 and direct_angle > ANGLE_THRESHOLD
            else SourceResponseGeometryStatus.SUM_ONLY
        )
        if public.status is not expected_status:
            raise AssertionError(
                f"case {case}: status {public.status} != {expected_status}"
            )
        beta_rm = rng.normal(scale=1.0e-3, size=3)
        beta_mo = rng.normal(scale=1.0e-3, size=3)
        closure = build_velocity_frame_decomposition(
            beta_RO=beta_rm + beta_mo,
            beta_RM=beta_rm,
            beta_MO=beta_mo,
            basis="oracle Cartesian basis",
            epoch_window="oracle common synthetic window",
            first_order_beta_ceiling=1.0e-2,
        )
        if closure.status is not VelocityDecompositionStatus.CLOSURE_VERIFIED:
            raise AssertionError(f"case {case}: exact closure was rejected")
    print(
        "PASS PR-256 independent Cholesky oracle "
        f"cases={CASES} "
        f"max_singular_error={maximum_singular_error:.3e} "
        f"max_angle_error={maximum_angle_error:.3e}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
