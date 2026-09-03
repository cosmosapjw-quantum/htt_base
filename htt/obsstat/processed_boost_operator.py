"""Processed joint-estimator wrapper for PMG-WU-011.

This module owns only the composition of the WU-011 finite source map with
the existing ``fit_joint_cutsky_alm`` operator.  Source-sky positivity,
Lorentz pullback, and source beam/pixel convolution remain in
``processed_boost_response``.  The split prevents the HEALPix source model and
the weighted joint-fit identity from becoming one untestable unit.

The public retained carrier is returned in the scientific stored-real
convention.  The existing joint solver's ``sqrt(2)`` real basis is retained
only as internal diagnostic content.  No observed data, empirical velocity,
global tilt, or Bianchi attribution is introduced.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import math

import numpy as np

from .planck_pr3_operator import (
    JOINT_CUTSKY_ESTIMATOR_ID,
    JointCutSkyOperator,
    fit_joint_cutsky_alm,
)
from .processed_boost_response import (
    FIT_LMAX,
    PROCESSING_ORDER,
    RETAINED_LMIN,
    SOURCE_LMAX,
    PositiveAbsoluteSkySpec,
    ProcessedBoostError,
    joint_to_scientific_real,
    source_convolved_finite_map,
)


_OPERATOR_SCHEMA = "HTT_WU011_PROCESSED_BOOST_OPERATOR_V1"
_EVALUATION_SCHEMA = "HTT_WU011_PROCESSED_BOOST_EVALUATION_V1"
_TRANSFER_RATIO_ATOL = 1.0e-10


def _finite_vector(values: object, *, size: int, label: str) -> np.ndarray:
    try:
        raw = np.asarray(values)
    except (TypeError, ValueError) as exc:
        raise ProcessedBoostError(
            f"{label} must be a finite real vector with shape ({size},)"
        ) from exc
    if raw.dtype.kind not in "iuf" or raw.dtype.kind == "b":
        raise ProcessedBoostError(
            f"{label} must be a finite real vector with shape ({size},)"
        )
    vector = np.asarray(raw, dtype=np.float64)
    if vector.shape != (size,) or not np.all(np.isfinite(vector)):
        raise ProcessedBoostError(
            f"{label} must be finite with shape ({size},)"
        )
    return vector


def _sealed(values: np.ndarray) -> np.ndarray:
    return np.frombuffer(np.asarray(values, dtype="<f8").tobytes(), dtype="<f8")


def _canonical_hash(payload: dict[str, object], *arrays: np.ndarray) -> str:
    digest = hashlib.sha256()
    digest.update(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    )
    for array in arrays:
        value = np.ascontiguousarray(array)
        digest.update(b"\0")
        digest.update(value.dtype.str.encode("ascii"))
        digest.update(b"\0")
        digest.update(repr(value.shape).encode("ascii"))
        digest.update(b"\0")
        digest.update(memoryview(value).cast("B"))
    return "sha256:" + digest.hexdigest()


@dataclass(frozen=True)
class ProcessedBoostOperator:
    """Content-bound wrapper around the existing weighted joint estimator."""

    mask: np.ndarray
    joint_operator: JointCutSkyOperator
    processing_lmax: int
    source_beam: np.ndarray
    source_pixel_window: np.ndarray
    target_beam: np.ndarray
    target_pixel_window: np.ndarray
    nside: int = field(init=False)
    joint_operator_id: str = field(init=False)
    content_id: str = field(init=False)

    @classmethod
    def from_components(
        cls,
        *,
        mask: object,
        joint_operator: JointCutSkyOperator,
        processing_lmax: int,
        source_beam: object,
        source_pixel_window: object,
        target_beam: object,
        target_pixel_window: object,
    ) -> "ProcessedBoostOperator":
        return cls(
            mask=np.asarray(mask),
            joint_operator=joint_operator,
            processing_lmax=processing_lmax,
            source_beam=np.asarray(source_beam),
            source_pixel_window=np.asarray(source_pixel_window),
            target_beam=np.asarray(target_beam),
            target_pixel_window=np.asarray(target_pixel_window),
        )

    def __post_init__(self) -> None:
        if type(self.joint_operator) is not JointCutSkyOperator:
            raise ProcessedBoostError(
                "joint operator must be an exact JointCutSkyOperator"
            )
        joint = self.joint_operator
        if (
            joint.lmin != 0
            or joint.lmax != FIT_LMAX
            or joint.retained_lmin != RETAINED_LMIN
            or joint.dimension != 36
            or joint.retained_dimension != 32
            or JOINT_CUTSKY_ESTIMATOR_ID
            != "joint_weighted_real_harmonic_l0_l5_retain_l2_l5:v1"
        ):
            raise ProcessedBoostError(
                "joint operator identity or fitted harmonic band is not the frozen WU-011 contract"
            )

        try:
            raw_mask = np.asarray(self.mask)
        except (TypeError, ValueError) as exc:
            raise ProcessedBoostError(
                "mask must exactly match the bound joint operator identity"
            ) from exc
        if raw_mask.dtype.kind not in "iuf" or raw_mask.dtype.kind == "b":
            raise ProcessedBoostError(
                "mask must exactly match the bound joint operator identity"
            )
        mask = np.asarray(raw_mask, dtype=np.float64)
        if (
            mask.shape != joint.mask.shape
            or not np.all(np.isfinite(mask))
            or not np.array_equal(mask, joint.mask)
        ):
            raise ProcessedBoostError(
                "mask differs from the bound joint operator identity"
            )

        if (
            type(self.processing_lmax) is not int
            or self.processing_lmax < SOURCE_LMAX
            or self.processing_lmax > 3 * joint.nside - 1
        ):
            raise ProcessedBoostError(
                "processing lmax must contain the source band and obey the HEALPix ceiling"
            )
        size = self.processing_lmax + 1
        source_beam = _finite_vector(
            self.source_beam, size=size, label="source beam transfer"
        )
        source_pixel = _finite_vector(
            self.source_pixel_window,
            size=size,
            label="source pixel-window transfer",
        )
        target_beam = _finite_vector(
            self.target_beam, size=size, label="target beam transfer"
        )
        target_pixel = _finite_vector(
            self.target_pixel_window,
            size=size,
            label="target pixel-window transfer",
        )
        for label, transfer in (
            ("source beam", source_beam),
            ("source pixel-window", source_pixel),
            ("target beam", target_beam),
            ("target pixel-window", target_pixel),
        ):
            if np.any(transfer <= 0.0):
                raise ProcessedBoostError(f"{label} transfer must be strictly positive")

        source_total = source_beam * source_pixel
        target_total = target_beam * target_pixel
        fitted_ratio = target_total[: FIT_LMAX + 1] / source_total[: FIT_LMAX + 1]
        if np.any(fitted_ratio > 1.0 + _TRANSFER_RATIO_ATOL):
            raise ProcessedBoostError(
                "post-fit target/source commonization would sharpen the fitted sky"
            )

        sealed_mask = _sealed(mask)
        sealed_source_beam = _sealed(source_beam)
        sealed_source_pixel = _sealed(source_pixel)
        sealed_target_beam = _sealed(target_beam)
        sealed_target_pixel = _sealed(target_pixel)
        content_id = _canonical_hash(
            {
                "schema": _OPERATOR_SCHEMA,
                "joint_estimator_id": JOINT_CUTSKY_ESTIMATOR_ID,
                "joint_operator_id": joint.operator_sha256,
                "joint_mask_id": joint.mask_sha256,
                "nside": joint.nside,
                "processing_lmax": self.processing_lmax,
                "processing_order": list(PROCESSING_ORDER),
                "source_lmax": SOURCE_LMAX,
                "fit_lmax": FIT_LMAX,
                "retained_lmin": RETAINED_LMIN,
            },
            sealed_mask,
            sealed_source_beam,
            sealed_source_pixel,
            sealed_target_beam,
            sealed_target_pixel,
        )

        object.__setattr__(self, "mask", sealed_mask)
        object.__setattr__(self, "source_beam", sealed_source_beam)
        object.__setattr__(self, "source_pixel_window", sealed_source_pixel)
        object.__setattr__(self, "target_beam", sealed_target_beam)
        object.__setattr__(self, "target_pixel_window", sealed_target_pixel)
        object.__setattr__(self, "nside", joint.nside)
        object.__setattr__(self, "joint_operator_id", joint.operator_sha256)
        object.__setattr__(self, "content_id", content_id)


@dataclass(frozen=True)
class ProcessedBoostEvaluation:
    """One content-bound retained scientific carrier from the joint solver."""

    retained_coefficients: np.ndarray
    joint_all_coefficients: np.ndarray
    weighted_residual_norm: float
    beta: np.ndarray
    mode: str
    operator_id: str
    source_map_id: str
    content_id: str = field(init=False)

    def __post_init__(self) -> None:
        retained = _finite_vector(
            self.retained_coefficients,
            size=32,
            label="scientific retained coefficients",
        )
        all_joint = _finite_vector(
            self.joint_all_coefficients,
            size=36,
            label="joint all coefficients",
        )
        beta = _finite_vector(self.beta, size=3, label="beta")
        try:
            residual = float(self.weighted_residual_norm)
        except (TypeError, ValueError) as exc:
            raise ProcessedBoostError(
                "weighted residual norm must be finite and nonnegative"
            ) from exc
        if not math.isfinite(residual) or residual < 0.0:
            raise ProcessedBoostError(
                "weighted residual norm must be finite and nonnegative"
            )
        if self.mode != "FINITE":
            raise ProcessedBoostError("processed evaluation mode is outside the frozen registry")
        if not isinstance(self.operator_id, str) or not self.operator_id:
            raise ProcessedBoostError("processed operator identity is required")
        if not isinstance(self.source_map_id, str) or not self.source_map_id:
            raise ProcessedBoostError("processed source-map identity is required")

        sealed_retained = _sealed(retained)
        sealed_all = _sealed(all_joint)
        sealed_beta = _sealed(beta)
        content_id = _canonical_hash(
            {
                "schema": _EVALUATION_SCHEMA,
                "operator_id": self.operator_id,
                "source_map_id": self.source_map_id,
                "mode": self.mode,
                "weighted_residual_norm_hex": residual.hex(),
                "retained_basis": "SCIENTIFIC_STORED_REAL_L2_L5_V1",
                "all_basis": "JOINT_SQRT2_REAL_L0_L5_V1",
            },
            sealed_retained,
            sealed_all,
            sealed_beta,
        )
        object.__setattr__(self, "retained_coefficients", sealed_retained)
        object.__setattr__(self, "joint_all_coefficients", sealed_all)
        object.__setattr__(self, "weighted_residual_norm", residual)
        object.__setattr__(self, "beta", sealed_beta)
        object.__setattr__(self, "content_id", content_id)


def evaluate_processed_boost(
    source_sky: PositiveAbsoluteSkySpec,
    operator: ProcessedBoostOperator,
    beta: object,
    *,
    mode: str,
) -> ProcessedBoostEvaluation:
    """Run the exact finite source path through the authoritative joint solver."""

    if type(source_sky) is not PositiveAbsoluteSkySpec:
        raise ProcessedBoostError("source sky must be an exact PositiveAbsoluteSkySpec")
    if type(operator) is not ProcessedBoostOperator:
        raise ProcessedBoostError("operator must be an exact ProcessedBoostOperator")
    if mode != "FINITE":
        raise ProcessedBoostError("only the finite processed evaluation is implemented")

    source_map = source_convolved_finite_map(
        source_sky,
        beta,
        nside=operator.nside,
        processing_lmax=operator.processing_lmax,
        source_beam=operator.source_beam,
        source_pixel_window=operator.source_pixel_window,
    )
    fit = fit_joint_cutsky_alm(
        source_map.pixel_map,
        mask=operator.mask,
        operator=operator.joint_operator,
        source_beam=operator.source_beam,
        source_pixel_window=operator.source_pixel_window,
        target_beam=operator.target_beam,
        target_pixel_window=operator.target_pixel_window,
    )
    retained_scientific = joint_to_scientific_real(
        fit.retained_coefficients,
        lmin=RETAINED_LMIN,
        lmax=FIT_LMAX,
    )
    return ProcessedBoostEvaluation(
        retained_coefficients=retained_scientific,
        joint_all_coefficients=fit.all_coefficients,
        weighted_residual_norm=fit.weighted_residual_norm,
        beta=np.asarray(beta, dtype=np.float64),
        mode=mode,
        operator_id=operator.content_id,
        source_map_id=source_map.content_id,
    )


__all__ = [
    "ProcessedBoostEvaluation",
    "ProcessedBoostOperator",
    "evaluate_processed_boost",
]
