"""Finite linear ellipsoid fibers and bounded rational-polytope support.

Results describe the supplied mathematical domain, not confidence calibration
or global physical identifiability. Unresolved numerical strata are retained.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math

import numpy as np

from .joint_feasible_set import exact_support, InfeasibleError
from .typefree_functionals import _array


def _psd_factor(shape):
    u = _array(shape, ndim=2, name="ellipsoid shape")
    if u.shape[0] != u.shape[1] or not len(u):
        raise ValueError("nonempty square shape matrix required")
    error = 64 * len(u) * np.finfo(float).eps * float(np.linalg.norm(u, 2))
    if np.max(np.abs(u-u.T)) > error:
        raise ValueError("shape must be symmetric")
    values, vectors = np.linalg.eigh((u+u.T)/2)
    if np.any(values < -error):
        raise ValueError("shape must be positive semidefinite")
    if np.any((values != 0) & (np.abs(values) <= error)):
        return "NUMERICALLY_UNRESOLVED", None
    positive = values > error
    return "DEFINED", vectors[:, positive] * np.sqrt(values[positive])


def _solve_range(a, b):
    """Conservative numerical range solve and orthonormal parameter kernel."""
    rows, cols = a.shape
    if rows == 0:
        return "DEFINED", np.zeros(cols), np.eye(cols), 0
    if cols == 0 or not np.any(a):
        if np.any(b):
            return "OUTSIDE_RESPONSE_RANGE", None, None, 0
        return "DEFINED", np.zeros(cols), np.eye(cols), 0
    left, singular, right = np.linalg.svd(a, full_matrices=True)
    error = 64 * max(a.shape) * np.finfo(float).eps * singular[0]
    if np.any((singular != 0) & (singular <= error)):
        return "NUMERICALLY_UNRESOLVED", None, None, None
    rank = int(np.count_nonzero(singular > error))
    z = right[:rank].T @ ((left[:, :rank].T @ b)/singular[:rank])
    if rank < rows:
        residual = float(np.linalg.norm(b-a@z))
        bound = 128 * max(a.shape) * np.finfo(float).eps * (
            float(np.linalg.norm(b)) + float(np.linalg.norm(a, 2))*float(np.linalg.norm(z)))
        if residual:
            return ("NUMERICALLY_UNRESOLVED" if residual <= bound else
                    "OUTSIDE_RESPONSE_RANGE"), None, None, rank
    return "DEFINED", z, right[rank:].T, rank


@dataclass(frozen=True)
class QuotientGauge:
    status: str
    gauge: float | None = None
    radius_sq: float | None = None
    witness: np.ndarray | None = None
    response_rank: int | None = None

    def __post_init__(self):
        if self.witness is not None:
            object.__setattr__(self, "witness", _array(self.witness))


def ellipsoid_quotient_gauge(shape, projection, value):
    """Minimum gauge over p*x=value for the centered shape ellipsoid.

    A feasible lift attains the minimum. It does not identify an actual hidden
    physical lift, which can have larger gauge or be constrained separately.
    """
    status, factor = _psd_factor(shape)
    n = np.asarray(shape).shape[0]
    p = _array(projection, ndim=2, name="projection")
    if p.shape[1] != n:
        raise ValueError("projection ambient dimension mismatch")
    v = _array(value, shape=(p.shape[0],), name="projected value")
    if status != "DEFINED":
        return QuotientGauge(status)
    status, z, _, rank = _solve_range(p@factor, v)
    if status != "DEFINED":
        return QuotientGauge(status, response_rank=rank)
    radius_sq = float(z@z)
    return QuotientGauge("NO_DIRECTIONS" if rank == 0 else "DEFINED",
                         math.sqrt(radius_sq), radius_sq, factor@z, rank)


@dataclass(frozen=True)
class FiberSupport:
    status: str
    value: float | None = None
    witness: np.ndarray | None = None

    def __post_init__(self):
        if self.witness is not None:
            object.__setattr__(self, "witness", _array(self.witness))


@dataclass(frozen=True)
class EllipsoidFiberImage:
    status: str
    target_center: np.ndarray | None = None
    target_factor: np.ndarray | None = None
    lift_center: np.ndarray | None = None
    lift_factor: np.ndarray | None = None
    minimum_radius_sq: float | None = None
    response_rank: int | None = None

    def __post_init__(self):
        for name in ("target_center", "target_factor", "lift_center", "lift_factor"):
            if getattr(self, name) is not None:
                object.__setattr__(self, name, _array(getattr(self, name)))

    @property
    def target_shape(self):
        if self.target_factor is None:
            return None
        return _array(self.target_factor @ self.target_factor.T)

    def support(self, direction):
        if self.status not in {"DEFINED", "POINT_IMAGE", "NO_DIRECTIONS"}:
            return FiberSupport(self.status)
        u = _array(direction, shape=self.target_center.shape, name="support direction")
        dual = self.target_factor.T @ u
        norm = float(np.linalg.norm(dual))
        witness = self.lift_center if norm == 0 else self.lift_center + self.lift_factor@(dual/norm)
        return FiberSupport(self.status, float(u@self.target_center)+norm, witness)


def ellipsoid_fiber_image(shape, observation, observed_value, projection, *, center=None):
    """Compute P(K intersect {B*x=y}) for K=c+U^(1/2) closed unit ball."""
    status, factor = _psd_factor(shape)
    n = np.asarray(shape).shape[0]
    b = _array(observation, ndim=2, name="observation operator")
    p = _array(projection, ndim=2, name="target operator")
    if b.shape[1] != n or p.shape[1] != n:
        raise ValueError("operator ambient dimension mismatch")
    y = _array(observed_value, shape=(b.shape[0],), name="observed value")
    c = np.zeros(n) if center is None else _array(center, shape=(n,), name="ellipsoid center")
    if status != "DEFINED":
        return EllipsoidFiberImage(status)
    status, z, kernel, rank = _solve_range(b@factor, y-b@c)
    if status == "OUTSIDE_RESPONSE_RANGE":
        return EllipsoidFiberImage("EMPTY_SET", response_rank=rank)
    if status != "DEFINED":
        return EllipsoidFiberImage(status, response_rank=rank)
    eta = float(z@z)
    radius_sq = 1-eta
    singular = np.linalg.svd(b@factor, compute_uv=False)
    positive = singular[singular > 0]
    condition = positive[0]/positive[-1] if positive.size else 1.
    error = 128 * max(n, len(y), 1) * np.finfo(float).eps * max(1., eta) * condition**2
    if radius_sq < -error:
        return EllipsoidFiberImage("EMPTY_SET", minimum_radius_sq=eta, response_rank=rank)
    if abs(radius_sq) <= error:
        return EllipsoidFiberImage("BOUNDARY_NUMERICALLY_UNRESOLVED",
                                   minimum_radius_sq=eta, response_rank=rank)
    lift_center = c+factor@z
    lift_factor = math.sqrt(radius_sq)*factor@kernel
    target_factor = p@lift_factor
    # Separate a zero original quotient from a point produced by constraints.
    result_status = ("NO_DIRECTIONS" if not np.any(p@factor) else
                     "POINT_IMAGE" if not np.any(target_factor) else "DEFINED")
    return EllipsoidFiberImage(result_status, p@lift_center, target_factor,
                               lift_center, lift_factor, eta, rank)


def _rational(value):
    if isinstance(value, bool):
        raise ValueError("boolean coefficients are not rational inputs")
    if isinstance(value, (Fraction, int, np.integer, str)):
        return Fraction(value)
    value = float(value)
    if not math.isfinite(value):
        raise ValueError("finite rational/dyadic coefficients required")
    return Fraction(value)


@dataclass(frozen=True)
class BoundedRationalPolytope:
    """K={A*x<=b, lower<=x<=upper}; explicit finite box proves boundedness.

    The box is part of the declared domain, not an artificial big-M clip.
    Coefficients are interpreted exactly as given (floats as dyadic rationals).
    """
    matrix: tuple[tuple[Fraction, ...], ...]
    bounds: tuple[Fraction, ...]
    lower: tuple[Fraction, ...]
    upper: tuple[Fraction, ...]

    def __post_init__(self):
        low, high = tuple(map(_rational, self.lower)), tuple(map(_rational, self.upper))
        if not low or len(low) != len(high) or any(a>b for a, b in zip(low, high)):
            raise ValueError("nonempty ordered finite bounding box required")
        rows = tuple(tuple(map(_rational, row)) for row in self.matrix)
        bounds = tuple(map(_rational, self.bounds))
        if len(rows) != len(bounds) or any(len(row) != len(low) for row in rows):
            raise ValueError("polytope matrix/bounds dimension mismatch")
        for name, value in (("matrix", rows), ("bounds", bounds), ("lower", low), ("upper", high)):
            object.__setattr__(self, name, value)


@dataclass(frozen=True)
class RationalFiberSupport:
    status: str
    lower: Fraction | None = None
    upper: Fraction | None = None
    enumerated_vertex_count: int = 0


def rational_polytope_fiber_support(polytope, observation, observed_value, direction):
    """Exact scalar support interval over a bounded rational equality slice.

    For target P and direction u, pass direction=P.T*u with exact coefficients.
    This vertex-enumeration adapter is intended for small finite dimensions.
    """
    if not isinstance(polytope, BoundedRationalPolytope):
        raise TypeError("BoundedRationalPolytope required")
    n = len(polytope.lower)
    c = list(map(_rational, direction))
    obs = [list(map(_rational, row)) for row in observation]
    y = list(map(_rational, observed_value))
    if len(c) != n or len(obs) != len(y) or any(len(row) != n for row in obs):
        raise ValueError("fiber/support dimension mismatch")
    a = [list(row) for row in polytope.matrix]
    b = list(polytope.bounds)
    for j, (low, high) in enumerate(zip(polytope.lower, polytope.upper)):
        e = [Fraction(0)]*n
        e[j] = Fraction(1)
        a.extend((e, [-v for v in e]))
        b.extend((high, -low))
    for row, value in zip(obs, y):
        a.extend((row, [-v for v in row]))
        b.extend((value, -value))
    try:
        result = exact_support(c, a, b)
    except InfeasibleError:
        # Unlike the general engine, this adapter has a proved finite box.
        return RationalFiberSupport("EMPTY_SET")
    return RationalFiberSupport("EXACT_BOUNDED_POLYTOPE", result["exact_lo"],
                                result["exact_hi"], result["n_vertices"])


__all__ = ["QuotientGauge", "ellipsoid_quotient_gauge", "FiberSupport", "EllipsoidFiberImage",
           "ellipsoid_fiber_image", "BoundedRationalPolytope", "RationalFiberSupport",
           "rational_polytope_fiber_support"]
