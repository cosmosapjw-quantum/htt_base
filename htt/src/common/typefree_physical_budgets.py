"""P2/W1 supplied-bound arithmetic; no observational bound is manufactured."""
from __future__ import annotations

from dataclasses import dataclass
import math
import numpy as np

from .r7_contracts import finite_array


def _nonnegative(value, name):
    value = float(value)
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"{name} must be finite and nonnegative")
    return value


@dataclass(frozen=True)
class StressBudgetContext:
    """Identity of the supplied smooth symmetric stress eigenbranch."""
    stress_component: str
    congruence: str
    frame: str
    epoch: str
    derivative_norm_definition: str
    provenance: str

    def __post_init__(self):
        for name in self.__dataclass_fields__:
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must identify the supplied premise")


@dataclass(frozen=True)
class StressGapBudget:
    context: StressBudgetContext
    speed_of_light: float
    rate_budget: float
    quadratic: np.ndarray | None
    status: str
    coordinate_order: tuple[str, ...] = ("theta", "sigma1", "sigma2", "sigma3", "sigma4", "sigma5", "omega1", "omega2", "omega3", "A1", "A2", "A3")

    def gauge(self, kinematics):
        """STF coefficients use a Frobenius-orthonormal five-vector basis."""
        x = finite_array(kinematics, shape=(12,), name="kinematics")
        if self.quadratic is None:
            return 0. if not np.any(x) else math.inf
        return math.sqrt(float(x @ self.quadratic @ x))


def stress_gap_budget(*, derivative_bound, spectral_gap_lower, speed_of_light, context):
    """Conditional P2 body from B*=c d*/delta*.

    d* bounds the positive observer norm of all 4x3 projected stress
    derivatives; it is not a Lorentzian contraction. The same-state timelike
    eigenbranch and the actual gap/derivative bounds are supplied premises.
    theta,sigma,omega have inverse-time units, A acceleration units, and c
    length/time. This is separate from the original geodesic MES anchor.
    """
    if not isinstance(context, StressBudgetContext):
        raise ValueError("explicit StressBudgetContext required")
    d = _nonnegative(derivative_bound, "derivative_bound")
    gap = _nonnegative(spectral_gap_lower, "spectral_gap_lower")
    c = _nonnegative(speed_of_light, "speed_of_light")
    if gap == 0 or c == 0:
        raise ValueError("positive spectral gap and speed_of_light required")
    budget = c*d/gap
    if not math.isfinite(budget) or (d > 0 and budget == 0):
        raise ValueError("rate budget not representable")
    if budget == 0:
        return StressGapBudget(context, c, 0., None, "ZERO_BODY")
    q = np.diag(np.r_[1/3, np.ones(5), 2*np.ones(3), np.ones(3)/c**2])/budget**2
    q = finite_array(q, shape=(12, 12), name="stress quadratic")
    if np.any(np.diag(q) <= 0):
        raise ValueError("stress quadratic not representable")
    return StressGapBudget(context, c, budget, q, "CONDITIONAL_SUPPLIED_BOUND")


@dataclass(frozen=True)
class WeakResponseBudget:
    response: np.ndarray
    error_radius: float
    variation_error: float
    coefficient_error: float
    numerical_error: float
    provenance: str


def weak_response_budget(*, integral_ws, integral_wprime_m, endpoint_a, endpoint_b,
                         lipschitz_bound, variation_integral, numerical_error,
                         provenance, coefficient_error_integral=0., kinematic_bound=None):
    """W1: K=I_ws+I_w'm-(w_b m_b-w_a m_a), with supplied error bounds.

    variation_integral=int |w| ||A|| |t-t0|; coefficient_error_integral=
    int |w| ||delta A||. The latter needs a finite bound on ||k||. Inputs
    are integrals and endpoint products, not sampled functions; no quadrature
    error or observational response is inferred by this routine.
    """
    if not isinstance(provenance, str) or not provenance.strip():
        raise ValueError("integral/error provenance required")
    s = finite_array(integral_ws, ndim=1, name="integral_ws")
    wp = finite_array(integral_wprime_m, shape=s.shape, name="integral_wprime_m")
    a = finite_array(endpoint_a, shape=s.shape, name="endpoint_a")
    b = finite_array(endpoint_b, shape=s.shape, name="endpoint_b")
    if s.size == 0:
        raise ValueError("nonempty response required")
    l = _nonnegative(lipschitz_bound, "lipschitz_bound")
    v = _nonnegative(variation_integral, "variation_integral")
    numerical = _nonnegative(numerical_error, "numerical_error")
    perturbation = _nonnegative(coefficient_error_integral, "coefficient_error_integral")
    if perturbation > 0 and kinematic_bound is None:
        raise ValueError("uncertain coefficients require a finite kinematic_bound")
    bound = 0. if kinematic_bound is None else _nonnegative(kinematic_bound, "kinematic_bound")
    error = l*v+bound*perturbation+numerical
    if not math.isfinite(error):
        raise ValueError("error radius not representable")
    return WeakResponseBudget(finite_array(s+wp-(b-a)), error, l*v, bound*perturbation, numerical, provenance)
