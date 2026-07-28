"""Joint partial-identification and finite-covariance inference contracts.

These objects keep four questions separate:

* what the data identify;
* how a random numerator and random anchor co-vary;
* whether a finite simulation covariance admits an evidence-grade likelihood;
* whether prior learning used genuinely held-out information.

Nothing in this module promotes a departure state to a morphology, source,
geometry, or Bianchi-family claim.
"""

from __future__ import annotations

import math
from dataclasses import InitVar, dataclass, field
from enum import Enum
from statistics import NormalDist
from typing import Mapping, Sequence

import numpy as np

from common.statistical_foundations import (
    AnchorConditioning,
    IdentificationStatus,
    NullKind,
    ScalarRange,
    StressStatus,
)


class StatisticalInferenceError(ValueError):
    """Raised when a claim-bearing inference contract is incomplete."""


class _StringEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class InferenceLane(_StringEnum):
    CLAIM_BEARING = "CLAIM_BEARING"
    EXPLORATORY = "EXPLORATORY"


class CrossCovarianceStatus(_StringEnum):
    BOUND = "BOUND"
    MISSING = "MISSING"
    EXPLORATORY_FACTORIZED = "EXPLORATORY_FACTORIZED"


class FiellerSetKind(_StringEnum):
    BOUNDED = "BOUNDED"
    DISJOINT_UNBOUNDED = "DISJOINT_UNBOUNDED"
    LEFT_UNBOUNDED = "LEFT_UNBOUNDED"
    RIGHT_UNBOUNDED = "RIGHT_UNBOUNDED"
    ALL_REAL = "ALL_REAL"
    EMPTY = "EMPTY"


class CovarianceLikelihoodStatus(_StringEnum):
    DEFINED = "DEFINED"
    OUTSIDE_SUPPORTED_QUOTIENT = "OUTSIDE_SUPPORTED_QUOTIENT"
    BLOCKED_ASSUMPTIONS = "BLOCKED_ASSUMPTIONS"


_EVIDENCE_MAX_RELATIVE_TOLERANCE = math.sqrt(np.finfo(float).eps)
_RATIO_INFERENCE_RESULT_TOKEN = object()
_FINITE_COVARIANCE_RESULT_TOKEN = object()
_FINITE_COVARIANCE_ALLOWED_USE = {
    CovarianceLikelihoodStatus.DEFINED: (
        "conditional likelihood under registered Gaussian/Wishart assumptions",
    ),
    CovarianceLikelihoodStatus.OUTSIDE_SUPPORTED_QUOTIENT: (
        "support-mismatch diagnostic",
    ),
    CovarianceLikelihoodStatus.BLOCKED_ASSUMPTIONS: (
        "assumption failure report",
    ),
}


class PriorLearningMode(_StringEnum):
    FIXED_PHYSICAL = "FIXED_PHYSICAL"
    SPLIT_SAMPLE = "SPLIT_SAMPLE"
    CROSS_FIT = "CROSS_FIT"


class FactorizationPremise(_StringEnum):
    EXPLORATORY_ZERO_CROSS_COVARIANCE = (
        "EXPLORATORY_ZERO_CROSS_COVARIANCE"
    )


def _real(value: object, name: str) -> float:
    if isinstance(value, (bool, np.bool_)):
        raise StatisticalInferenceError(f"{name} must not be boolean")
    try:
        out = float(value)
    except (TypeError, ValueError) as exc:
        raise StatisticalInferenceError(f"{name} must be a real number") from exc
    if not math.isfinite(out):
        raise StatisticalInferenceError(f"{name} must be finite")
    return out


def _nonnegative(value: object, name: str) -> float:
    out = _real(value, name)
    if out < 0.0:
        raise StatisticalInferenceError(f"{name} must be non-negative")
    return out


def _positive(value: object, name: str) -> float:
    out = _nonnegative(value, name)
    if out == 0.0:
        raise StatisticalInferenceError(f"{name} must be positive")
    return out


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise StatisticalInferenceError(f"{name} must be non-empty trimmed text")
    return value


def _texts(values: Sequence[object], name: str, *, empty_ok: bool = False) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise StatisticalInferenceError(f"{name} must be a sequence")
    out = tuple(_text(value, name) for value in values)
    if not out and not empty_ok:
        raise StatisticalInferenceError(f"{name} must not be empty")
    if len(set(out)) != len(out):
        raise StatisticalInferenceError(f"{name} must not contain duplicates")
    return out


@dataclass(frozen=True)
class JointRandomAnchorEstimate:
    """A numerator and data-derived anchor as one joint random object."""

    numerator_estimate: float
    anchor_estimate: float
    numerator_variance: float
    anchor_variance: float
    cross_covariance: float | None
    cross_covariance_status: CrossCovarianceStatus
    conditioning: AnchorConditioning
    identification_status: IdentificationStatus
    shared_data_id: str
    assumptions: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "numerator_estimate", _real(self.numerator_estimate, "numerator_estimate")
        )
        object.__setattr__(
            self, "anchor_estimate", _real(self.anchor_estimate, "anchor_estimate")
        )
        vn = _nonnegative(self.numerator_variance, "numerator_variance")
        vd = _nonnegative(self.anchor_variance, "anchor_variance")
        object.__setattr__(self, "numerator_variance", vn)
        object.__setattr__(self, "anchor_variance", vd)
        if not isinstance(self.cross_covariance_status, CrossCovarianceStatus):
            raise StatisticalInferenceError(
                "cross_covariance_status must be a CrossCovarianceStatus"
            )
        if self.cross_covariance_status is CrossCovarianceStatus.MISSING:
            if self.cross_covariance is not None:
                raise StatisticalInferenceError(
                    "MISSING cross covariance must carry value=None"
                )
        else:
            cov = _real(self.cross_covariance, "cross_covariance")
            covariance_limit = math.sqrt(vn) * math.sqrt(vd)
            if covariance_limit == 0.0:
                covariance_valid = cov == 0.0
            else:
                covariance_valid = abs(cov) <= covariance_limit * (
                    1.0 + np.finfo(float).eps * 64.0
                )
            if not covariance_valid:
                raise StatisticalInferenceError(
                    "joint numerator-anchor covariance is not positive semidefinite"
                )
            if (
                self.cross_covariance_status
                is CrossCovarianceStatus.EXPLORATORY_FACTORIZED
                and cov != 0.0
            ):
                raise StatisticalInferenceError(
                    "exploratory factorization must bind cross_covariance=0"
                )
            object.__setattr__(self, "cross_covariance", cov)
        if not isinstance(self.conditioning, AnchorConditioning):
            raise StatisticalInferenceError(
                "conditioning must be REALIZATION_CONDITIONAL or ENSEMBLE_CALIBRATED"
            )
        if not isinstance(self.identification_status, IdentificationStatus):
            raise StatisticalInferenceError(
                "identification_status must be an IdentificationStatus"
            )
        _text(self.shared_data_id, "shared_data_id")
        assumptions = _texts(self.assumptions, "assumptions")
        if (
            self.cross_covariance_status
            is CrossCovarianceStatus.EXPLORATORY_FACTORIZED
            and not any("factor" in value.casefold() for value in assumptions)
        ):
            raise StatisticalInferenceError(
                "exploratory factorization requires an explicit factorization assumption"
            )
        object.__setattr__(self, "assumptions", assumptions)


@dataclass(frozen=True)
class FiellerConfidenceSet:
    kind: FiellerSetKind
    intervals: tuple[ScalarRange, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.kind, FiellerSetKind):
            raise StatisticalInferenceError("kind must be a FiellerSetKind")
        if any(not isinstance(value, ScalarRange) for value in self.intervals):
            raise StatisticalInferenceError("intervals must contain ScalarRange values")
        expected_counts = {
            FiellerSetKind.BOUNDED: 1,
            FiellerSetKind.DISJOINT_UNBOUNDED: 2,
            FiellerSetKind.LEFT_UNBOUNDED: 1,
            FiellerSetKind.RIGHT_UNBOUNDED: 1,
            FiellerSetKind.ALL_REAL: 1,
            FiellerSetKind.EMPTY: 0,
        }
        if len(self.intervals) != expected_counts[self.kind]:
            raise StatisticalInferenceError(
                f"{self.kind.value} has the wrong number of intervals"
            )
        if self.kind is FiellerSetKind.ALL_REAL and self.intervals != (
            ScalarRange(-math.inf, math.inf),
        ):
            raise StatisticalInferenceError("ALL_REAL must span the real line")

    @property
    def is_unbounded(self) -> bool:
        return any(
            math.isinf(interval.lower) or math.isinf(interval.upper)
            for interval in self.intervals
        )


@dataclass(frozen=True)
class RatioInferenceResult:
    status: StressStatus
    point_estimate: float | None
    confidence_set: FiellerConfidenceSet
    denominator_interval: ScalarRange
    confidence_level: float
    atol: float
    rtol: float
    lane: InferenceLane
    conditioning: AnchorConditioning
    assumptions: tuple[str, ...]
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _RATIO_INFERENCE_RESULT_TOKEN:
            raise StatisticalInferenceError(
                "RatioInferenceResult must be created by fieller_ratio"
            )
        if not isinstance(self.status, StressStatus) or self.status not in {
            StressStatus.DEFINED,
            StressStatus.RATIO_UNIDENTIFIED,
            StressStatus.NUMERATOR_UNIDENTIFIED,
        }:
            raise StatisticalInferenceError(
                "ratio status is not valid for joint random-anchor inference"
            )
        if type(self.confidence_set) is not FiellerConfidenceSet:
            raise StatisticalInferenceError(
                "confidence_set must be a FiellerConfidenceSet"
            )
        if type(self.denominator_interval) is not ScalarRange:
            raise StatisticalInferenceError(
                "denominator_interval must be a ScalarRange"
            )
        confidence = _real(self.confidence_level, "confidence_level")
        if not 0.0 < confidence < 1.0:
            raise StatisticalInferenceError(
                "confidence_level must lie in (0, 1)"
            )
        atol = _nonnegative(self.atol, "atol")
        rtol = _nonnegative(self.rtol, "rtol")
        if not isinstance(self.lane, InferenceLane):
            raise StatisticalInferenceError("lane must be an InferenceLane")
        if not isinstance(self.conditioning, AnchorConditioning):
            raise StatisticalInferenceError(
                "conditioning must be an AnchorConditioning"
            )
        assumptions = _texts(self.assumptions, "assumptions")
        object.__setattr__(self, "confidence_level", confidence)
        object.__setattr__(self, "atol", atol)
        object.__setattr__(self, "rtol", rtol)
        object.__setattr__(self, "assumptions", assumptions)
        if self.status is StressStatus.DEFINED:
            object.__setattr__(
                self, "point_estimate", _real(self.point_estimate, "point_estimate")
            )
            if self.confidence_set.kind is not FiellerSetKind.BOUNDED:
                raise StatisticalInferenceError(
                    "DEFINED ratio requires a bounded Fieller set"
                )
            if not self.denominator_interval.separated_from_zero(
                atol=atol, rtol=rtol
            ):
                raise StatisticalInferenceError(
                    "DEFINED ratio denominator interval must exclude zero"
                )
        elif self.point_estimate is not None:
            raise StatisticalInferenceError(
                "unidentified ratio must not carry a finite point estimate"
            )
        if (
            self.status is StressStatus.RATIO_UNIDENTIFIED
            and not self.confidence_set.is_unbounded
        ):
            raise StatisticalInferenceError(
                "RATIO_UNIDENTIFIED requires an unbounded Fieller set"
            )
        if (
            self.status is StressStatus.NUMERATOR_UNIDENTIFIED
            and self.confidence_set.kind is not FiellerSetKind.EMPTY
        ):
            raise StatisticalInferenceError(
                "NUMERATOR_UNIDENTIFIED requires an empty Fieller set"
            )


def _quadratic_fieller_set(a: float, b: float, c: float, *, tol: float) -> FiellerConfidenceSet:
    """Solve ``a r^2 + b r + c <= 0`` as a union of closed intervals."""
    if abs(a) <= tol:
        if abs(b) <= tol:
            if c <= tol:
                return FiellerConfidenceSet(
                    FiellerSetKind.ALL_REAL,
                    (ScalarRange(-math.inf, math.inf),),
                )
            return FiellerConfidenceSet(FiellerSetKind.EMPTY, ())
        root = -c / b
        if b > 0.0:
            return FiellerConfidenceSet(
                FiellerSetKind.LEFT_UNBOUNDED,
                (ScalarRange(-math.inf, root),),
            )
        return FiellerConfidenceSet(
            FiellerSetKind.RIGHT_UNBOUNDED,
            (ScalarRange(root, math.inf),),
        )
    discriminant = b * b - 4.0 * a * c
    if discriminant < -tol:
        if a < 0.0:
            return FiellerConfidenceSet(
                FiellerSetKind.ALL_REAL,
                (ScalarRange(-math.inf, math.inf),),
            )
        return FiellerConfidenceSet(FiellerSetKind.EMPTY, ())
    discriminant = max(discriminant, 0.0)
    if a < 0.0 and discriminant <= tol:
        return FiellerConfidenceSet(
            FiellerSetKind.ALL_REAL,
            (ScalarRange(-math.inf, math.inf),),
        )
    sqrt_disc = math.sqrt(discriminant)
    r1, r2 = sorted(((-b - sqrt_disc) / (2.0 * a), (-b + sqrt_disc) / (2.0 * a)))
    if a > 0.0:
        return FiellerConfidenceSet(
            FiellerSetKind.BOUNDED,
            (ScalarRange(r1, r2),),
        )
    return FiellerConfidenceSet(
        FiellerSetKind.DISJOINT_UNBOUNDED,
        (ScalarRange(-math.inf, r1), ScalarRange(r2, math.inf)),
    )


def fieller_ratio(
    joint: JointRandomAnchorEstimate,
    *,
    confidence_level: float,
    atol: float,
    rtol: float,
    lane: InferenceLane,
) -> RatioInferenceResult:
    """Return a ratio only when its random denominator is separated from zero."""
    if not isinstance(joint, JointRandomAnchorEstimate):
        raise StatisticalInferenceError("joint must be a JointRandomAnchorEstimate")
    if not isinstance(lane, InferenceLane):
        raise StatisticalInferenceError("lane must be an InferenceLane")
    confidence = _real(confidence_level, "confidence_level")
    if not 0.0 < confidence < 1.0:
        raise StatisticalInferenceError("confidence_level must lie in (0, 1)")
    atol = _nonnegative(atol, "atol")
    rtol = _nonnegative(rtol, "rtol")
    if (
        lane is InferenceLane.CLAIM_BEARING
        and joint.cross_covariance_status is not CrossCovarianceStatus.BOUND
    ):
        raise StatisticalInferenceError(
            "claim-bearing ratio requires bound cross covariance"
        )
    if (
        lane is InferenceLane.EXPLORATORY
        and joint.cross_covariance_status is CrossCovarianceStatus.MISSING
    ):
        raise StatisticalInferenceError(
            "exploratory factorization must be explicit, not MISSING"
        )
    if joint.identification_status in {
        IdentificationStatus.EMPTY,
        IdentificationStatus.NON_IDENTIFIED,
        IdentificationStatus.PARTIALLY_IDENTIFIED,
    }:
        return RatioInferenceResult(
            status=StressStatus.NUMERATOR_UNIDENTIFIED,
            point_estimate=None,
            confidence_set=FiellerConfidenceSet(FiellerSetKind.EMPTY, ()),
            denominator_interval=ScalarRange(-math.inf, math.inf),
            confidence_level=confidence,
            atol=atol,
            rtol=rtol,
            lane=lane,
            conditioning=joint.conditioning,
            assumptions=joint.assumptions,
            _construction_token=_RATIO_INFERENCE_RESULT_TOKEN,
        )
    z = NormalDist().inv_cdf(0.5 + confidence / 2.0)
    denominator_interval = ScalarRange(
        joint.anchor_estimate - z * math.sqrt(joint.anchor_variance),
        joint.anchor_estimate + z * math.sqrt(joint.anchor_variance),
    )
    cov = float(joint.cross_covariance)
    coefficient_unit = max(
        abs(joint.numerator_estimate),
        abs(joint.anchor_estimate),
        math.sqrt(joint.numerator_variance),
        math.sqrt(joint.anchor_variance),
        math.sqrt(abs(cov)),
    )
    if coefficient_unit == 0.0:
        normalized_numerator = 0.0
        normalized_anchor = 0.0
        normalized_numerator_variance = 0.0
        normalized_anchor_variance = 0.0
        normalized_covariance = 0.0
    else:
        normalized_numerator = joint.numerator_estimate / coefficient_unit
        normalized_anchor = joint.anchor_estimate / coefficient_unit
        normalized_numerator_variance = (
            joint.numerator_variance / coefficient_unit / coefficient_unit
        )
        normalized_anchor_variance = (
            joint.anchor_variance / coefficient_unit / coefficient_unit
        )
        normalized_covariance = cov / coefficient_unit / coefficient_unit
    a = normalized_anchor**2 - z**2 * normalized_anchor_variance
    b = -2.0 * (
        normalized_numerator * normalized_anchor
        - z**2 * normalized_covariance
    )
    c = normalized_numerator**2 - z**2 * normalized_numerator_variance
    coefficient_scale = max(abs(a), abs(b), abs(c))
    if coefficient_scale > 0.0:
        a /= coefficient_scale
        b /= coefficient_scale
        c /= coefficient_scale
    confidence_set = _quadratic_fieller_set(
        a,
        b,
        c,
        tol=np.finfo(float).eps * 64.0,
    )
    separated = denominator_interval.separated_from_zero(atol=atol, rtol=rtol)
    if not separated:
        if not confidence_set.is_unbounded:
            confidence_set = FiellerConfidenceSet(
                FiellerSetKind.ALL_REAL,
                (ScalarRange(-math.inf, math.inf),),
            )
        return RatioInferenceResult(
            status=StressStatus.RATIO_UNIDENTIFIED,
            point_estimate=None,
            confidence_set=confidence_set,
            denominator_interval=denominator_interval,
            confidence_level=confidence,
            atol=atol,
            rtol=rtol,
            lane=lane,
            conditioning=joint.conditioning,
            assumptions=joint.assumptions,
            _construction_token=_RATIO_INFERENCE_RESULT_TOKEN,
        )
    return RatioInferenceResult(
        status=StressStatus.DEFINED,
        point_estimate=joint.numerator_estimate / joint.anchor_estimate,
        confidence_set=confidence_set,
        denominator_interval=denominator_interval,
        confidence_level=confidence,
        atol=atol,
        rtol=rtol,
        lane=lane,
        conditioning=joint.conditioning,
        assumptions=joint.assumptions,
        _construction_token=_RATIO_INFERENCE_RESULT_TOKEN,
    )


@dataclass(frozen=True)
class FiniteCovarianceAssumptions:
    gaussian_simulations: bool
    wishart_sample_covariance: bool
    observation_independent_of_simulations: bool
    known_simulation_mean: bool

    def __post_init__(self) -> None:
        for name in (
            "gaussian_simulations",
            "wishart_sample_covariance",
            "observation_independent_of_simulations",
            "known_simulation_mean",
        ):
            if type(getattr(self, name)) is not bool:
                raise StatisticalInferenceError(f"{name} must be boolean")

    @property
    def evidence_grade(self) -> bool:
        return all(
            (
                self.gaussian_simulations,
                self.wishart_sample_covariance,
                self.observation_independent_of_simulations,
            )
        )


@dataclass(frozen=True)
class FiniteCovarianceLikelihoodResult:
    status: CovarianceLikelihoodStatus
    log_likelihood: float | None
    chi2_supported: float | None
    rank: int
    null_residual_norm: float
    n_simulations: int
    method: str
    assumptions: FiniteCovarianceAssumptions
    rcond: float
    null_atol: float
    evidence_null_atol_ceiling: float
    allowed_use: tuple[str, ...] = field(init=False)
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _FINITE_COVARIANCE_RESULT_TOKEN:
            raise StatisticalInferenceError(
                "FiniteCovarianceLikelihoodResult must be created by "
                "covariance_marginalized_t_loglikelihood"
            )
        if not isinstance(self.status, CovarianceLikelihoodStatus):
            raise StatisticalInferenceError(
                "status must be a CovarianceLikelihoodStatus"
            )
        if isinstance(self.rank, (bool, np.bool_)) or not isinstance(
            self.rank, (int, np.integer)
        ) or self.rank < 0:
            raise StatisticalInferenceError("rank must be a non-negative integer")
        if isinstance(self.n_simulations, (bool, np.bool_)) or not isinstance(
            self.n_simulations, (int, np.integer)
        ) or self.n_simulations < 2:
            raise StatisticalInferenceError(
                "n_simulations must be an integer of at least 2"
            )
        null_norm = _nonnegative(
            self.null_residual_norm, "null_residual_norm"
        )
        rcond = _positive(self.rcond, "rcond")
        if rcond >= 1.0:
            raise StatisticalInferenceError("rcond must be less than 1")
        null_atol = _nonnegative(self.null_atol, "null_atol")
        ceiling = _nonnegative(
            self.evidence_null_atol_ceiling,
            "evidence_null_atol_ceiling",
        )
        _text(self.method, "method")
        if not isinstance(self.assumptions, FiniteCovarianceAssumptions):
            raise StatisticalInferenceError(
                "assumptions must be FiniteCovarianceAssumptions"
            )
        object.__setattr__(self, "rank", int(self.rank))
        object.__setattr__(self, "n_simulations", int(self.n_simulations))
        object.__setattr__(self, "null_residual_norm", null_norm)
        object.__setattr__(self, "rcond", rcond)
        object.__setattr__(self, "null_atol", null_atol)
        object.__setattr__(self, "evidence_null_atol_ceiling", ceiling)
        object.__setattr__(
            self, "allowed_use", _FINITE_COVARIANCE_ALLOWED_USE[self.status]
        )
        if self.status is CovarianceLikelihoodStatus.DEFINED:
            if not self.assumptions.evidence_grade:
                raise StatisticalInferenceError(
                    "DEFINED likelihood requires evidence-grade assumptions"
                )
            if self.rank == 0:
                raise StatisticalInferenceError(
                    "DEFINED likelihood requires positive supported rank"
                )
            object.__setattr__(
                self,
                "log_likelihood",
                _real(self.log_likelihood, "log_likelihood"),
            )
            object.__setattr__(
                self,
                "chi2_supported",
                _nonnegative(self.chi2_supported, "chi2_supported"),
            )
            if self.null_residual_norm > self.null_atol:
                raise StatisticalInferenceError(
                    "DEFINED likelihood cannot exceed null_atol"
                )
        else:
            if self.log_likelihood is not None or self.chi2_supported is not None:
                raise StatisticalInferenceError(
                    "undefined likelihood statuses must not carry likelihood values"
                )
            if (
                self.status
                is CovarianceLikelihoodStatus.OUTSIDE_SUPPORTED_QUOTIENT
                and self.null_residual_norm <= self.null_atol
            ):
                raise StatisticalInferenceError(
                    "OUTSIDE_SUPPORTED_QUOTIENT requires a null residual "
                    "above null_atol"
                )
            if (
                self.status is CovarianceLikelihoodStatus.BLOCKED_ASSUMPTIONS
                and self.assumptions.evidence_grade
            ):
                raise StatisticalInferenceError(
                    "BLOCKED_ASSUMPTIONS requires a failed evidence premise"
                )


def covariance_marginalized_t_loglikelihood(
    residual: Sequence[object],
    sample_covariance: Sequence[Sequence[object]],
    *,
    n_simulations: int,
    assumptions: FiniteCovarianceAssumptions,
    rcond: float,
    null_atol: float,
) -> FiniteCovarianceLikelihoodResult:
    """Sellentin-Heavens likelihood on the supported covariance quotient."""
    if isinstance(n_simulations, (bool, np.bool_)) or not isinstance(
        n_simulations, (int, np.integer)
    ):
        raise StatisticalInferenceError("n_simulations must be an integer")
    if n_simulations < 2:
        raise StatisticalInferenceError("n_simulations must be at least 2")
    if not isinstance(assumptions, FiniteCovarianceAssumptions):
        raise StatisticalInferenceError(
            "assumptions must be FiniteCovarianceAssumptions"
        )
    rcond = _positive(rcond, "rcond")
    null_atol = _nonnegative(null_atol, "null_atol")
    if rcond >= 1.0:
        raise StatisticalInferenceError("rcond must be less than 1")
    if (
        assumptions.evidence_grade
        and rcond > _EVIDENCE_MAX_RELATIVE_TOLERANCE
    ):
        raise StatisticalInferenceError(
            "evidence-grade rcond exceeds the registered "
            "sqrt(machine-epsilon) ceiling"
        )
    raw_residual = np.asarray(residual, dtype=object)
    raw_covariance = np.asarray(sample_covariance, dtype=object)
    if any(isinstance(value, (bool, np.bool_)) for value in raw_residual.flat):
        raise StatisticalInferenceError("residual must not contain booleans")
    if any(isinstance(value, (bool, np.bool_)) for value in raw_covariance.flat):
        raise StatisticalInferenceError("sample_covariance must not contain booleans")
    vector = np.asarray(residual, dtype=float)
    covariance = np.asarray(sample_covariance, dtype=float)
    if vector.ndim != 1 or vector.size == 0 or not np.all(np.isfinite(vector)):
        raise StatisticalInferenceError("residual must be a non-empty finite vector")
    if covariance.shape != (vector.size, vector.size) or not np.all(
        np.isfinite(covariance)
    ):
        raise StatisticalInferenceError(
            "sample_covariance must be a finite square matrix matching residual"
        )
    scale = float(np.max(np.abs(covariance)))
    if not np.allclose(
        covariance, covariance.T, atol=rcond * scale, rtol=rcond
    ):
        raise StatisticalInferenceError("sample_covariance must be symmetric")
    # The registered tolerance admits harmless round-off asymmetry, but the
    # eigensolver consumes one triangle.  Canonicalize the accepted matrix so
    # transposing identical evidence cannot change the likelihood.
    with np.errstate(over="ignore", invalid="ignore"):
        covariance = covariance * 0.5 + covariance.T * 0.5
    if not np.all(np.isfinite(covariance)):
        raise StatisticalInferenceError(
            "sample_covariance symmetrization produced non-finite values"
        )
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    spectral_scale = float(np.max(np.abs(eigenvalues)))
    if spectral_scale == 0.0:
        supported = np.zeros_like(eigenvalues, dtype=bool)
    else:
        if float(np.min(eigenvalues)) < -rcond * spectral_scale:
            raise StatisticalInferenceError(
                "sample_covariance must be positive semidefinite"
            )
        supported = eigenvalues > rcond * spectral_scale
    rank = int(np.count_nonzero(supported))
    residual_scale = max(
        1.0,
        float(np.max(np.abs(vector))),
        math.sqrt(spectral_scale),
    )
    evidence_null_atol_ceiling = (
        _EVIDENCE_MAX_RELATIVE_TOLERANCE * residual_scale
    )
    if (
        assumptions.evidence_grade
        and null_atol > evidence_null_atol_ceiling
    ):
        raise StatisticalInferenceError(
            "evidence-grade null_atol exceeds the registered "
            "scale-aware sqrt(machine-epsilon) ceiling"
        )
    if assumptions.evidence_grade and rank == 0:
        raise StatisticalInferenceError(
            "evidence-grade covariance must retain at least one "
            "supported direction"
        )
    supported_basis = eigenvectors[:, supported]
    null_basis = eigenvectors[:, ~supported]
    with np.errstate(over="ignore", invalid="ignore"):
        supported_coordinates = vector @ supported_basis
        null_coordinates = vector @ null_basis
    if not (
        np.all(np.isfinite(supported_coordinates))
        and np.all(np.isfinite(null_coordinates))
    ):
        raise StatisticalInferenceError(
            "covariance quotient projection produced a non-finite coordinate"
        )
    with np.errstate(over="ignore", invalid="ignore"):
        null_norm = float(np.linalg.norm(null_coordinates))
    if not math.isfinite(null_norm):
        raise StatisticalInferenceError(
            "covariance quotient null residual norm is non-finite"
        )
    if null_norm > null_atol:
        return FiniteCovarianceLikelihoodResult(
            status=CovarianceLikelihoodStatus.OUTSIDE_SUPPORTED_QUOTIENT,
            log_likelihood=None,
            chi2_supported=None,
            rank=rank,
            null_residual_norm=null_norm,
            n_simulations=int(n_simulations),
            method="covariance_marginalized_multivariate_t_supported_quotient",
            assumptions=assumptions,
            rcond=rcond,
            null_atol=null_atol,
            evidence_null_atol_ceiling=evidence_null_atol_ceiling,
            _construction_token=_FINITE_COVARIANCE_RESULT_TOKEN,
        )
    if not assumptions.evidence_grade:
        return FiniteCovarianceLikelihoodResult(
            status=CovarianceLikelihoodStatus.BLOCKED_ASSUMPTIONS,
            log_likelihood=None,
            chi2_supported=None,
            rank=rank,
            null_residual_norm=null_norm,
            n_simulations=int(n_simulations),
            method="covariance_marginalized_multivariate_t_supported_quotient",
            assumptions=assumptions,
            rcond=rcond,
            null_atol=null_atol,
            evidence_null_atol_ceiling=evidence_null_atol_ceiling,
            _construction_token=_FINITE_COVARIANCE_RESULT_TOKEN,
        )
    wishart_df = n_simulations if assumptions.known_simulation_mean else n_simulations - 1
    if wishart_df < rank:
        raise StatisticalInferenceError(
            "covariance-marginalized t requires Wishart degrees of freedom "
            "at least the supported rank"
        )
    if rank:
        positive = eigenvalues[supported]
        with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
            chi2_terms = supported_coordinates**2 / positive
        if not np.all(np.isfinite(chi2_terms)):
            raise StatisticalInferenceError(
                "supported covariance quadratic form is non-finite"
            )
        chi2 = float(np.sum(chi2_terms))
        log_pseudodeterminant = float(np.sum(np.log(positive)))
    else:
        chi2 = 0.0
        log_pseudodeterminant = 0.0
    if not (
        math.isfinite(chi2)
        and math.isfinite(log_pseudodeterminant)
    ):
        raise StatisticalInferenceError(
            "supported covariance likelihood terms must be finite"
        )
    try:
        nu = float(wishart_df)
    except OverflowError as exc:
        raise StatisticalInferenceError(
            "Wishart degrees of freedom exceed the finite likelihood domain"
        ) from exc
    if not math.isfinite(nu):
        raise StatisticalInferenceError(
            "Wishart degrees of freedom exceed the finite likelihood domain"
        )
    log_normalization = (
        math.lgamma((nu + 1.0) / 2.0)
        - math.lgamma((nu - rank + 1.0) / 2.0)
        - 0.5 * rank * math.log(math.pi * nu)
        - 0.5 * log_pseudodeterminant
    )
    log_likelihood = log_normalization - 0.5 * (nu + 1.0) * math.log1p(
        chi2 / nu
    )
    if not (
        math.isfinite(log_normalization)
        and math.isfinite(log_likelihood)
    ):
        raise StatisticalInferenceError(
            "covariance-marginalized likelihood produced a non-finite result"
        )
    return FiniteCovarianceLikelihoodResult(
        status=CovarianceLikelihoodStatus.DEFINED,
        log_likelihood=float(log_likelihood),
        chi2_supported=chi2,
        rank=rank,
        null_residual_norm=null_norm,
        n_simulations=int(n_simulations),
        method=(
            "covariance_marginalized_multivariate_t_supported_quotient_"
            + ("known_mean" if assumptions.known_simulation_mean else "estimated_mean")
        ),
        assumptions=assumptions,
        rcond=rcond,
        null_atol=null_atol,
        evidence_null_atol_ceiling=evidence_null_atol_ceiling,
        _construction_token=_FINITE_COVARIANCE_RESULT_TOKEN,
    )


@dataclass(frozen=True)
class BlockCovarianceAssembly:
    matrix: tuple[tuple[float, ...], ...]
    block_order: tuple[str, ...]
    cross_covariance_status: CrossCovarianceStatus
    lane: InferenceLane
    assumptions: tuple[str, ...]


def assemble_block_covariance(
    blocks: Mapping[str, Sequence[Sequence[object]]],
    cross_blocks: Mapping[tuple[str, str], Sequence[Sequence[object]]],
    *,
    lane: InferenceLane,
    factorization_assumption: FactorizationPremise | None = None,
) -> BlockCovarianceAssembly:
    """Assemble all cross blocks; missing pieces never silently become zero."""
    if not isinstance(lane, InferenceLane):
        raise StatisticalInferenceError("lane must be an InferenceLane")
    if not blocks:
        raise StatisticalInferenceError("blocks must not be empty")
    names = tuple(sorted(_text(name, "block name") for name in blocks))
    valid_names = set(names)
    for key in cross_blocks:
        if (
            not isinstance(key, tuple)
            or len(key) != 2
            or key[0] not in valid_names
            or key[1] not in valid_names
            or key[0] == key[1]
        ):
            raise StatisticalInferenceError(
                f"invalid cross-covariance block key: {key!r}"
            )
    arrays: dict[str, np.ndarray] = {}
    for name in names:
        raw_array = np.asarray(blocks[name], dtype=object)
        if any(isinstance(value, (bool, np.bool_)) for value in raw_array.flat):
            raise StatisticalInferenceError(f"block {name} must not contain booleans")
        array = np.asarray(blocks[name], dtype=float)
        if (
            array.ndim != 2
            or array.shape[0] == 0
            or array.shape[0] != array.shape[1]
            or not np.all(np.isfinite(array))
            or not np.allclose(array, array.T)
        ):
            raise StatisticalInferenceError(f"block {name} must be finite symmetric square")
        arrays[name] = array
    missing: list[tuple[str, str]] = []
    offsets: dict[str, slice] = {}
    start = 0
    for name in names:
        stop = start + arrays[name].shape[0]
        offsets[name] = slice(start, stop)
        start = stop
    matrix = np.zeros((start, start), dtype=float)
    for name in names:
        matrix[offsets[name], offsets[name]] = arrays[name]
    for index, left in enumerate(names):
        for right in names[index + 1 :]:
            key = (left, right)
            reverse = (right, left)
            if key in cross_blocks and reverse in cross_blocks:
                raise StatisticalInferenceError(
                    f"duplicate cross-covariance orientations for {left}/{right}"
                )
            if key in cross_blocks:
                raw_cross = np.asarray(cross_blocks[key], dtype=object)
                cross = np.asarray(cross_blocks[key], dtype=float)
            elif reverse in cross_blocks:
                raw_cross = np.asarray(cross_blocks[reverse], dtype=object)
                cross = np.asarray(cross_blocks[reverse], dtype=float).T
            else:
                missing.append(key)
                continue
            if any(isinstance(value, (bool, np.bool_)) for value in raw_cross.flat):
                raise StatisticalInferenceError(
                    f"cross block {left}/{right} must not contain booleans"
                )
            expected = (arrays[left].shape[0], arrays[right].shape[0])
            if cross.shape != expected or not np.all(np.isfinite(cross)):
                raise StatisticalInferenceError(
                    f"cross block {left}/{right} has wrong shape or non-finite values"
                )
            matrix[offsets[left], offsets[right]] = cross
            matrix[offsets[right], offsets[left]] = cross.T
    if missing:
        if lane is InferenceLane.CLAIM_BEARING:
            raise StatisticalInferenceError(
                f"missing cross covariance blocks: {missing}"
            )
        if (
            factorization_assumption
            is not FactorizationPremise.EXPLORATORY_ZERO_CROSS_COVARIANCE
        ):
            raise StatisticalInferenceError(
                "missing exploratory cross blocks require the typed "
                "EXPLORATORY_ZERO_CROSS_COVARIANCE premise"
            )
        assumptions = (factorization_assumption.value,)
        status = CrossCovarianceStatus.EXPLORATORY_FACTORIZED
    else:
        if factorization_assumption is not None:
            raise StatisticalInferenceError(
                "factorization_assumption is only valid for missing exploratory blocks"
            )
        assumptions = ("all cross covariance blocks explicitly bound",)
        status = CrossCovarianceStatus.BOUND
    eigenvalues = np.linalg.eigvalsh(matrix)
    spectral_scale = float(np.max(np.abs(eigenvalues)))
    if spectral_scale and float(np.min(eigenvalues)) < -1e-12 * spectral_scale:
        raise StatisticalInferenceError(
            "assembled block covariance must be positive semidefinite"
        )
    return BlockCovarianceAssembly(
        matrix=tuple(tuple(float(value) for value in row) for row in matrix),
        block_order=names,
        cross_covariance_status=status,
        lane=lane,
        assumptions=assumptions,
    )


@dataclass(frozen=True)
class CrossFitFold:
    selection_ids: tuple[str, ...]
    estimation_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        selection = _texts(self.selection_ids, "selection_ids")
        estimation = _texts(self.estimation_ids, "estimation_ids")
        if set(selection) & set(estimation):
            raise StatisticalInferenceError(
                "one fold may not select and estimate on the same observations"
            )
        object.__setattr__(self, "selection_ids", selection)
        object.__setattr__(self, "estimation_ids", estimation)


@dataclass(frozen=True)
class PriorLearningReceipt:
    mode: PriorLearningMode
    prior_center: float
    data_dependent: bool
    selection_ids: tuple[str, ...]
    estimation_ids: tuple[str, ...]
    folds: tuple[CrossFitFold, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.mode, PriorLearningMode):
            raise StatisticalInferenceError("mode must be a PriorLearningMode")
        object.__setattr__(self, "prior_center", _real(self.prior_center, "prior_center"))
        if type(self.data_dependent) is not bool:
            raise StatisticalInferenceError("data_dependent must be boolean")
        selection = _texts(self.selection_ids, "selection_ids", empty_ok=True)
        estimation = _texts(self.estimation_ids, "estimation_ids", empty_ok=True)
        folds = tuple(self.folds)
        object.__setattr__(self, "selection_ids", selection)
        object.__setattr__(self, "estimation_ids", estimation)
        object.__setattr__(self, "folds", folds)
        if any(not isinstance(fold, CrossFitFold) for fold in folds):
            raise StatisticalInferenceError("folds must contain CrossFitFold values")
        if self.mode is PriorLearningMode.FIXED_PHYSICAL:
            if self.data_dependent or selection or estimation or self.folds:
                raise StatisticalInferenceError(
                    "fixed physical priors must not be data learned"
                )
        elif not self.data_dependent:
            raise StatisticalInferenceError(
                "split/cross-fit prior receipts must be data_dependent"
            )
        if self.mode is PriorLearningMode.SPLIT_SAMPLE:
            if not selection or not estimation or set(selection) & set(estimation):
                raise StatisticalInferenceError(
                    "split-sample prior learning requires disjoint non-empty samples"
                )
            if self.folds:
                raise StatisticalInferenceError("split-sample mode must not carry folds")
        if self.mode is PriorLearningMode.CROSS_FIT:
            if len(self.folds) < 2:
                raise StatisticalInferenceError(
                    "cross-fit mode requires at least two folds"
                )
            validation_ids = [
                value for fold in self.folds for value in fold.estimation_ids
            ]
            if len(validation_ids) != len(set(validation_ids)):
                raise StatisticalInferenceError(
                    "each observation must be held out exactly once"
                )
            if set(validation_ids) != set(estimation):
                raise StatisticalInferenceError(
                    "cross-fit estimation_ids must equal the held-out fold union"
                )
            training_ids = {
                value for fold in self.folds for value in fold.selection_ids
            }
            if training_ids != set(selection):
                raise StatisticalInferenceError(
                    "cross-fit selection_ids must equal the training fold union"
                )

    @property
    def allowed_use(self) -> tuple[str, ...]:
        if self.mode is PriorLearningMode.FIXED_PHYSICAL:
            return ("identified-coordinate physical prior",)
        return ("conditional prior-sensitivity analysis",)


@dataclass(frozen=True)
class NullSectorReport:
    null_kind: NullKind
    bounds: ScalarRange
    prior_sensitivity_class: str
    posterior_created: bool = False
    likelihood_evidence: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.null_kind, NullKind) or self.null_kind is NullKind.NONE:
            raise StatisticalInferenceError("null_kind must name a real null sector")
        if not isinstance(self.bounds, ScalarRange):
            raise StatisticalInferenceError("bounds must be a ScalarRange")
        _text(self.prior_sensitivity_class, "prior_sensitivity_class")
        if type(self.posterior_created) is not bool or type(self.likelihood_evidence) is not bool:
            raise StatisticalInferenceError(
                "posterior_created and likelihood_evidence must be boolean"
            )
        if self.posterior_created or self.likelihood_evidence:
            raise StatisticalInferenceError(
                "null sectors expose bounds/sensitivity, never posterior evidence"
            )


__all__ = [
    "BlockCovarianceAssembly",
    "CovarianceLikelihoodStatus",
    "CrossCovarianceStatus",
    "CrossFitFold",
    "FiellerConfidenceSet",
    "FiellerSetKind",
    "FactorizationPremise",
    "FiniteCovarianceAssumptions",
    "FiniteCovarianceLikelihoodResult",
    "InferenceLane",
    "JointRandomAnchorEstimate",
    "NullSectorReport",
    "PriorLearningMode",
    "PriorLearningReceipt",
    "RatioInferenceResult",
    "StatisticalInferenceError",
    "assemble_block_covariance",
    "covariance_marginalized_t_loglikelihood",
    "fieller_ratio",
]
