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
from dataclasses import dataclass
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


class PriorLearningMode(_StringEnum):
    FIXED_PHYSICAL = "FIXED_PHYSICAL"
    SPLIT_SAMPLE = "SPLIT_SAMPLE"
    CROSS_FIT = "CROSS_FIT"


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
            determinant_scale = max(vn * vd, cov * cov)
            determinant_tol = np.finfo(float).eps * 64.0 * determinant_scale
            if cov * cov > vn * vd + determinant_tol:
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

    def __post_init__(self) -> None:
        if self.status is StressStatus.DEFINED:
            object.__setattr__(
                self, "point_estimate", _real(self.point_estimate, "point_estimate")
            )
            if self.confidence_set.kind is not FiellerSetKind.BOUNDED:
                raise StatisticalInferenceError(
                    "DEFINED ratio requires a bounded Fieller set"
                )
        elif self.point_estimate is not None:
            raise StatisticalInferenceError(
                "unidentified ratio must not carry a finite point estimate"
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
        )
    z = NormalDist().inv_cdf(0.5 + confidence / 2.0)
    denominator_interval = ScalarRange(
        joint.anchor_estimate - z * math.sqrt(joint.anchor_variance),
        joint.anchor_estimate + z * math.sqrt(joint.anchor_variance),
    )
    cov = float(joint.cross_covariance)
    a = joint.anchor_estimate**2 - z**2 * joint.anchor_variance
    b = -2.0 * (
        joint.numerator_estimate * joint.anchor_estimate - z**2 * cov
    )
    c = joint.numerator_estimate**2 - z**2 * joint.numerator_variance
    coefficient_scale = max(abs(a), abs(b), abs(c), 1.0)
    confidence_set = _quadratic_fieller_set(
        a, b, c, tol=np.finfo(float).eps * 64.0 * coefficient_scale
    )
    separated = denominator_interval.separated_from_zero(atol=atol, rtol=rtol)
    if not separated:
        if not confidence_set.is_unbounded and confidence_set.kind is not FiellerSetKind.ALL_REAL:
            raise StatisticalInferenceError(
                "Fieller invariant violated: zero-crossing denominator produced "
                "a bounded confidence set"
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
                self.known_simulation_mean,
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
    allowed_use: tuple[str, ...]


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
    supported_basis = eigenvectors[:, supported]
    null_basis = eigenvectors[:, ~supported]
    supported_coordinates = vector @ supported_basis
    null_coordinates = vector @ null_basis
    null_norm = float(np.linalg.norm(null_coordinates))
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
            allowed_use=("support-mismatch diagnostic",),
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
            allowed_use=("assumption failure report",),
        )
    if n_simulations <= rank:
        raise StatisticalInferenceError(
            "covariance-marginalized t requires n_simulations > supported rank"
        )
    if rank:
        positive = eigenvalues[supported]
        chi2 = float(np.sum(supported_coordinates**2 / positive))
        log_pseudodeterminant = float(np.sum(np.log(positive)))
    else:
        chi2 = 0.0
        log_pseudodeterminant = 0.0
    n = float(n_simulations)
    log_normalization = (
        math.lgamma(n / 2.0)
        - math.lgamma((n - rank) / 2.0)
        - 0.5 * rank * math.log(math.pi * (n - 1.0))
        - 0.5 * log_pseudodeterminant
    )
    log_likelihood = log_normalization - 0.5 * n * math.log1p(
        chi2 / (n - 1.0)
    )
    return FiniteCovarianceLikelihoodResult(
        status=CovarianceLikelihoodStatus.DEFINED,
        log_likelihood=float(log_likelihood),
        chi2_supported=chi2,
        rank=rank,
        null_residual_norm=null_norm,
        n_simulations=int(n_simulations),
        method="covariance_marginalized_multivariate_t_supported_quotient",
        assumptions=assumptions,
        allowed_use=("conditional likelihood under registered Gaussian/Wishart assumptions",),
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
    factorization_assumption: str | None = None,
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
        assumption = _text(factorization_assumption, "factorization_assumption")
        assumptions = (assumption,)
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
        object.__setattr__(self, "selection_ids", selection)
        object.__setattr__(self, "estimation_ids", estimation)
        if any(not isinstance(fold, CrossFitFold) for fold in self.folds):
            raise StatisticalInferenceError("folds must contain CrossFitFold values")
        if self.mode is PriorLearningMode.FIXED_PHYSICAL:
            if self.data_dependent or selection or self.folds:
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
            if not self.folds:
                raise StatisticalInferenceError("cross-fit mode requires folds")
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
