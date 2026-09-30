"""Pre-data, fixed-distance endpoint cosmography owned by HTT.

The response is 1+z, with four free angular intercept coefficients and nine
area-distance slope coefficients.  Known Gaussian noise, fixed independent
area distances/directions and fixed selection are explicit assumptions.  This
module neither loads catalogues nor infers the homogeneous normal N.  Its GLS
centre/covariance are not an empirical coverage certificate or a posterior.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math

import numpy as np

from common.r7_contracts import NumericalUnresolved, finite_array
from htt.infer.r7_gaussian_law import decompose_covariance, gaussian_loglik


COEFFICIENT_NAMES = (
    "zeta_0", "zeta_x", "zeta_y", "zeta_z",
    "h_0", "h_x", "h_y", "h_z", "q_xx", "q_yy", "q_xy", "q_xz", "q_yz",
)
COEFFICIENT_UNITS = ("1",) * 4 + ("km/s/Mpc",) * 9
DIRECTION_CONVENTION = "SOURCEWARD_UNIT_VECTOR_IN_OBSERVER_REST_SPACE"
_MISSING_TAGS = {"", "unknown", "unspecified", "unavailable", "none", "null"}


class EndpointInferenceUnavailable(ValueError):
    """The observation contract lacks a supported conditional inference law."""


class EndpointRankUnresolved(NumericalUnresolved):
    """The selected design/covariance cannot resolve all requested coefficients."""


class DistanceTreatment(str, Enum):
    FIXED_INDEPENDENT_AREA_DISTANCE = "FIXED_INDEPENDENT_AREA_DISTANCE"
    ERROR_INTEGRATION_UNAVAILABLE = "ERROR_INTEGRATION_UNAVAILABLE"


class RemainderKind(str, Enum):
    EXACT_ZERO_ASSUMED = "EXACT_ZERO_ASSUMED"
    BOUNDED_DETERMINISTIC = "BOUNDED_DETERMINISTIC"
    UNKNOWN = "UNKNOWN"


def _tag(value: str, name: str) -> str:
    if not isinstance(value, str) or value.strip().lower() in _MISSING_TAGS:
        raise ValueError(f"{name} must name an explicit source/frame/conditioning")
    return value.strip()


def _ids(values, name: str) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{name} must be ordered row identities")
    result = tuple(_tag(value, name) for value in values)
    if not result or len(set(result)) != len(result):
        raise ValueError(f"{name} must be nonempty and unique")
    return result


def _covariance(value, count: int, *, positive_definite: bool) -> np.ndarray:
    array = finite_array(value, shape=(count, count), name="covariance")
    decomposition = decompose_covariance(array)
    if not decomposition.resolved:
        raise EndpointRankUnresolved("covariance support rank is numerically unresolved")
    if positive_definite and decomposition.rank != count:
        raise EndpointRankUnresolved("this GLS branch requires positive definite covariance; no jitter")
    # Preserve the caller's matrix. Do not canonicalize distinct represented
    # Gaussian laws into equality by symmetrizing them in the F6 comparison.
    if not np.array_equal(array, array.T):
        raise ValueError("covariance must be exactly symmetric as supplied")
    return array


@dataclass(frozen=True)
class FiniteDistanceRemainder:
    """Bounds on the dimensionless additive 1+z remainder, in original row order.

    Deterministic bounds are not extra Gaussian noise.  UNKNOWN remains an
    explicit unavailable branch; no finite-distance model is invented for it.
    """

    kind: RemainderKind
    source: str
    absolute_bounds: np.ndarray | None = None

    def __post_init__(self):
        if not isinstance(self.kind, RemainderKind):
            raise TypeError("kind must be RemainderKind")
        object.__setattr__(self, "source", _tag(self.source, "remainder source"))
        if self.kind is RemainderKind.BOUNDED_DETERMINISTIC:
            bounds = finite_array(self.absolute_bounds, ndim=1, name="remainder bounds")
            if np.any(bounds < 0):
                raise ValueError("remainder bounds must be nonnegative")
            object.__setattr__(self, "absolute_bounds", bounds)
        elif self.absolute_bounds is not None:
            raise ValueError("only bounded remainder accepts an absolute-bounds array")


@dataclass(frozen=True)
class EndpointObservations:
    """Explicit selected observation law; none of these tags is inferred.

    ``observer_frame``/``redshift_frame`` name the same velocity reference;
    ``direction_frame`` separately names the spatial coordinate basis.
    Use a concrete correction source, or ``NATIVE_OBSERVER_NO_CORRECTION``.
    ``area_distance_mpc`` is d_A, never d_L/(1+z) or redshift-defined depth.
    """

    row_ids: tuple[str, ...]
    directions: np.ndarray
    redshift: np.ndarray
    area_distance_mpc: np.ndarray
    covariance: np.ndarray
    covariance_row_ids: tuple[str, ...]
    support_mask: np.ndarray
    source_congruence: str
    observer_frame: str
    redshift_frame: str
    direction_frame: str
    redshift_correction_source: str
    distance_treatment: DistanceTreatment
    distance_source: str
    selection_source: str
    covariance_source: str
    remainder: FiniteDistanceRemainder
    geodesic_source: bool | None = None
    direction_convention: str = DIRECTION_CONVENTION
    covariance_sampling_law: str = "KNOWN_GAUSSIAN_CONDITIONAL"
    c_km_s: float = 299792.458

    def __post_init__(self):
        ids = _ids(self.row_ids, "row_ids")
        covariance_ids = _ids(self.covariance_row_ids, "covariance_row_ids")
        if covariance_ids != ids:
            raise ValueError("covariance row order must equal observation row order")
        count = len(ids)
        directions = finite_array(self.directions, shape=(count, 3), name="directions")
        if np.any(np.abs(np.linalg.norm(directions, axis=1) - 1.0) > 2e-12):
            raise ValueError("directions must be unit sourceward vectors")
        redshift = finite_array(self.redshift, shape=(count,), name="redshift")
        if np.any(redshift <= -1):
            raise ValueError("redshift requires 1+z > 0")
        distance = finite_array(self.area_distance_mpc, shape=(count,), name="area_distance_mpc")
        if np.any(distance <= 0):
            raise ValueError("area distances must be positive")
        mask = np.asarray(self.support_mask)
        if mask.shape != (count,) or mask.dtype.kind != "b" or not np.any(mask):
            raise ValueError("support_mask must select rows with a nonempty boolean mask")
        mask = np.array(mask, copy=True)
        mask.setflags(write=False)
        covariance = _covariance(self.covariance, count, positive_definite=True)
        for field in ("source_congruence", "observer_frame", "redshift_frame", "direction_frame",
                      "redshift_correction_source", "distance_source", "selection_source", "covariance_source"):
            object.__setattr__(self, field, _tag(getattr(self, field), field))
        if self.observer_frame != self.redshift_frame:
            raise ValueError("redshift_frame must match observer_frame; supply a consistent transformed law")
        if self.direction_convention != DIRECTION_CONVENTION:
            raise ValueError("unsupported direction convention")
        if not isinstance(self.distance_treatment, DistanceTreatment):
            raise TypeError("distance_treatment must be explicit DistanceTreatment")
        if self.covariance_sampling_law != "KNOWN_GAUSSIAN_CONDITIONAL":
            raise EndpointInferenceUnavailable("estimated or unspecified covariance needs its own sampling law")
        if not isinstance(self.remainder, FiniteDistanceRemainder):
            raise TypeError("typed finite-distance remainder required")
        if self.remainder.absolute_bounds is not None and self.remainder.absolute_bounds.shape != (count,):
            raise ValueError("remainder bounds must follow original row order")
        if self.geodesic_source is not None and type(self.geodesic_source) is not bool:
            raise TypeError("geodesic_source must be bool or None")
        c = float(self.c_km_s)
        if not math.isfinite(c) or c <= 0:
            raise ValueError("c_km_s must be positive finite")
        for key, value in (("row_ids", ids), ("covariance_row_ids", covariance_ids),
                           ("directions", directions), ("redshift", redshift),
                           ("area_distance_mpc", distance), ("covariance", covariance),
                           ("support_mask", mask), ("c_km_s", c)):
            object.__setattr__(self, key, value)


def endpoint_design(directions, area_distance_mpc, *, c_km_s: float = 299792.458) -> np.ndarray:
    """The 13-column free-intercept plus monopole/dipole/STF slope design."""
    n = finite_array(directions, ndim=2, name="directions")
    if n.shape[1:] != (3,) or len(n) == 0:
        raise ValueError("directions must have nonempty shape (N,3)")
    if np.any(np.abs(np.linalg.norm(n, axis=1) - 1) > 2e-12):
        raise ValueError("directions must be unit vectors")
    distance = finite_array(area_distance_mpc, shape=(len(n),), name="area_distance_mpc")
    c = float(c_km_s)
    if np.any(distance <= 0) or not math.isfinite(c) or c <= 0:
        raise ValueError("positive area distances and c_km_s required")
    x, y, z = n.T
    intercept = np.column_stack((np.ones(len(n)), n))
    slope = np.column_stack((intercept, x*x-z*z, y*y-z*z, 2*x*y, 2*x*z, 2*y*z))
    return np.column_stack((intercept, distance[:, None] / c * slope))


def _selected(observations: EndpointObservations):
    if not isinstance(observations, EndpointObservations):
        raise TypeError("EndpointObservations required")
    if observations.distance_treatment is not DistanceTreatment.FIXED_INDEPENDENT_AREA_DISTANCE:
        raise EndpointInferenceUnavailable("distance-error integration is unavailable; fixed-distance law not admitted")
    if observations.remainder.kind is RemainderKind.UNKNOWN:
        raise EndpointInferenceUnavailable("unknown finite-distance remainder: endpoint coefficients unresolved")
    index = np.flatnonzero(observations.support_mask)
    design = endpoint_design(observations.directions[index], observations.area_distance_mpc[index],
                             c_km_s=observations.c_km_s)
    covariance = observations.covariance[np.ix_(index, index)]
    bounds = (np.zeros(len(index)) if observations.remainder.absolute_bounds is None
              else observations.remainder.absolute_bounds[index])
    return index, design, 1.0 + observations.redshift[index], covariance, bounds


@dataclass(frozen=True)
class EndpointCosmographyFit:
    """Nominal zero-remainder GLS centre with noise covariance and bias bounds.

    For an allowed deterministic remainder r, the conditional mean of the
    fitted coefficients is theta + M r. ``deterministic_bias_bound`` bounds
    |M r| componentwise. It is not covariance or a simultaneous confidence set.
    No physical intercept normalization or eigenframe projection is performed.
    """

    coefficients: np.ndarray
    coefficient_covariance: np.ndarray
    deterministic_bias_bound: np.ndarray
    selected_row_ids: tuple[str, ...]
    singular_values: np.ndarray
    scaled_condition_number: float
    remainder_kind: RemainderKind
    source_congruence: str
    observer_frame: str
    direction_frame: str
    redshift_correction_source: str
    distance_source: str
    selection_source: str
    covariance_source: str
    remainder_source: str
    coefficient_identification_status: str
    geodesic_source: bool | None
    design_rank: int = 13
    empirical_coverage_status: str = "NOT_CALIBRATED"
    physical_scope: str = "OBSERVER_SOURCE_ENDPOINT_COEFFICIENTS_ONLY"
    normal_tilt_status: str = "UNAVAILABLE_NO_GEOMETRIC_NORMAL"

    @property
    def coefficient_names(self):
        return COEFFICIENT_NAMES

    @property
    def coefficient_units(self):
        return COEFFICIENT_UNITS


def fit_endpoint_cosmography(observations: EndpointObservations, *, max_condition: float = 1e8) -> EndpointCosmographyFit:
    """Fit fixed-distance coefficients by dense whitening and column-scaled SVD.

    Rank deficiency or numerical ambiguity refuses a fit. No pseudo-inverse
    minimum-norm estimate, covariance jitter, prior, or catalogue calibration is
    used to replace missing information.
    """
    index, design, response, covariance, bounds = _selected(observations)
    if not math.isfinite(max_condition) or max_condition < 1:
        raise ValueError("max_condition must be finite and at least one")
    decomposition = decompose_covariance(covariance)
    if not decomposition.resolved or decomposition.rank != len(response):
        raise EndpointRankUnresolved("selected covariance rank unresolved")
    cholesky = np.linalg.cholesky(covariance)
    whitened = np.linalg.solve(cholesky, design)
    target = np.linalg.solve(cholesky, response)
    norms = np.linalg.norm(whitened, axis=0)
    if np.any(norms == 0) or not np.all(np.isfinite(norms)):
        raise EndpointRankUnresolved("selected design has unresolved column scales")
    u, singular, vt = np.linalg.svd(whitened / norms, full_matrices=False)
    tolerance = 64 * np.finfo(float).eps * max(whitened.shape) * singular[0]
    if len(singular) != 13 or singular[-1] <= tolerance:
        raise EndpointRankUnresolved("selected design rank below 13 or numerically unresolved")
    condition = float(singular[0] / singular[-1])
    if condition > max_condition:
        raise EndpointRankUnresolved("selected design exceeds declared scaled condition limit")
    coefficient_factor = (vt.T / singular) / norms[:, None]
    coefficients = coefficient_factor @ (u.T @ target)
    coefficient_covariance = coefficient_factor @ coefficient_factor.T
    influence = coefficient_factor @ u.T @ np.linalg.solve(cholesky, np.eye(len(response)))
    bias_bound = np.abs(influence) @ bounds
    return EndpointCosmographyFit(
        coefficients=finite_array(coefficients, shape=(13,)),
        coefficient_covariance=finite_array(coefficient_covariance, shape=(13, 13)),
        deterministic_bias_bound=finite_array(bias_bound, shape=(13,)),
        selected_row_ids=tuple(observations.row_ids[i] for i in index),
        singular_values=finite_array(singular, shape=(13,)),
        scaled_condition_number=condition,
        remainder_kind=observations.remainder.kind,
        source_congruence=observations.source_congruence,
        observer_frame=observations.observer_frame,
        direction_frame=observations.direction_frame,
        redshift_correction_source=observations.redshift_correction_source,
        distance_source=observations.distance_source,
        selection_source=observations.selection_source,
        covariance_source=observations.covariance_source,
        remainder_source=observations.remainder.source,
        coefficient_identification_status=(
            "IDENTIFIED_WITHIN_EXACT_TRUNCATED_CONDITIONAL_MODEL"
            if observations.remainder.kind is RemainderKind.EXACT_ZERO_ASSUMED
            else "BOUNDED_REMAINDER_SET_NO_POINT_IDENTIFICATION"
        ),
        geodesic_source=observations.geodesic_source,
    )


def endpoint_log_likelihood(observations: EndpointObservations, coefficients, *, remainder=None) -> float:
    """Normalized fixed Gaussian likelihood, conditional on supplied remainder.

    Nonzero-bound remainders must be supplied in original row order. They are
    neither integrated out nor treated as independent noise. Exact-zero mode
    permits omission only because that assumption was explicit in the contract.
    """
    index, design, response, covariance, bounds = _selected(observations)
    theta = finite_array(coefficients, shape=(13,), name="coefficients")
    if remainder is None:
        if observations.remainder.kind is not RemainderKind.EXACT_ZERO_ASSUMED:
            raise EndpointInferenceUnavailable("supply the bounded remainder nuisance explicitly")
        r = np.zeros(len(index))
    else:
        full_r = finite_array(remainder, shape=(len(observations.row_ids),), name="remainder")
        full_bounds = (np.zeros(len(full_r)) if observations.remainder.absolute_bounds is None
                       else observations.remainder.absolute_bounds)
        if np.any(np.abs(full_r) > full_bounds):
            raise ValueError("remainder exceeds declared deterministic bounds")
        r = full_r[index]
    return float(gaussian_loglik(response - design @ theta - r, covariance))


@dataclass(frozen=True)
class GaussianStateLaw:
    """One supplied state's complete finite-dimensional Gaussian observation law.

    The shared law/domain/conditioning identities are caller declarations, not
    evidence that a physical domain or a covariance family has been calibrated.
    Covariance includes all selected measurement dependence in this row order.
    """

    state_id: str
    domain_id: str
    shared_sampling_law_id: str
    conditioning_id: str
    frame_id: str
    selection_id: str
    measurement_ids: tuple[str, ...]
    mean: np.ndarray
    covariance: np.ndarray

    def __post_init__(self):
        for name in ("state_id", "domain_id", "shared_sampling_law_id", "conditioning_id", "frame_id", "selection_id"):
            object.__setattr__(self, name, _tag(getattr(self, name), name))
        ids = _ids(self.measurement_ids, "measurement_ids")
        object.__setattr__(self, "measurement_ids", ids)
        object.__setattr__(self, "mean", finite_array(self.mean, shape=(len(ids),), name="mean"))
        object.__setattr__(self, "covariance", _covariance(self.covariance, len(ids), positive_definite=False))


@dataclass(frozen=True)
class GaussianLawComparison:
    left_state_id: str
    right_state_id: str
    domain_id: str
    shared_sampling_law_id: str
    means_equal: bool
    covariances_equal: bool
    equal_joint_gaussian_law: bool
    scope: str = "TWO_SUPPLIED_STATES_ONLY"
    equality_basis: str = "EXACT_REPRESENTED_MEAN_AND_COVARIANCE"


def compare_gaussian_state_laws(left: GaussianStateLaw, right: GaussianStateLaw) -> GaussianLawComparison:
    """F6: compare two complete represented Gaussian laws in one declared scope.

    Equality of predictions alone is insufficient. Equality is exact on supplied
    finite arrays, never an allclose-based mathematical proof or a statement
    about every state in a physical domain. Inequality of a finite pair does not
    establish global identifiability either.
    """
    if not isinstance(left, GaussianStateLaw) or not isinstance(right, GaussianStateLaw):
        raise TypeError("two GaussianStateLaw inputs required")
    for name in ("domain_id", "shared_sampling_law_id", "conditioning_id", "frame_id", "selection_id", "measurement_ids"):
        if getattr(left, name) != getattr(right, name):
            raise ValueError(f"two-state comparison requires shared {name}")
    means_equal = bool(np.array_equal(left.mean, right.mean))
    covariances_equal = bool(np.array_equal(left.covariance, right.covariance))
    return GaussianLawComparison(left.state_id, right.state_id, left.domain_id,
                                 left.shared_sampling_law_id, means_equal, covariances_equal,
                                 means_equal and covariances_equal)


__all__ = [
    "COEFFICIENT_NAMES", "COEFFICIENT_UNITS", "DIRECTION_CONVENTION",
    "DistanceTreatment", "RemainderKind", "FiniteDistanceRemainder",
    "EndpointObservations", "EndpointCosmographyFit", "EndpointInferenceUnavailable",
    "EndpointRankUnresolved", "endpoint_design", "fit_endpoint_cosmography",
    "endpoint_log_likelihood", "GaussianStateLaw", "GaussianLawComparison",
    "compare_gaussian_state_laws",
]
