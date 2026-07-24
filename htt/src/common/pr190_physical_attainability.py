"""PR-190 physical-attainability attempt and decisive shear-substitution block.

The registered comparator endpoint is a *component vector*, not only the
scalar ``x_C = Sigma2 - W2 + Omega_tilt + DeltaOmega_k``.  A diagonal,
comoving Bianchi-I dust family is an exact Einstein--matter solution family,
but it has ``W2 = Omega_tilt = DeltaOmega_k = 0``.  Tuning its shear can match
the scalar endpoint values while failing to realize the registered endpoint
vectors.  PR-190 explicitly forbids using that scalar match as a replacement
for the vorticity/tilt/curvature corner.

Conventions: metric signature (-,+,+,+), 8*pi*G = 1, normal/comoving frame
``n = u``, mean e-fold time ``N = ln(a/a0)``, expanding branch H > 0, dust
pressure p = 0.  ``Sigma2 = sigma_ab sigma^ab / (6 H^2)``.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as Fr

import numpy as np
from scipy.integrate import solve_ivp

from .revival_joint_comparator import (
    comparator_value_exact,
    component_vector_exact,
)

LOWER_X = Fr(2, 25)
UPPER_X = Fr(1, 10)
LOWER_T_WITNESS = Fr(-2, 3)
UPPER_T_WITNESS = Fr(0)
LOWER_COMPONENT_GAP = Fr(1, 50)
UPPER_COMPONENT_GAP = Fr(3, 100)
FIVE_EFOLDS = 5.0
GRID_SIZE = 100


def shear_only_vector(x_c: Fr) -> dict[str, Fr]:
    """A comoving diagonal Bianchi-I state tuned to scalar comparator ``x_c``."""
    if not Fr(0) <= x_c <= Fr(1):
        raise ValueError("Bianchi-I dust shear fraction must lie in [0, 1]")
    return {
        "Sigma2": x_c,
        "W2": Fr(0),
        "Omega_tilt": Fr(0),
        "DeltaOmega_k": Fr(0),
    }


def component_linf_gap(left: dict[str, Fr], right: dict[str, Fr]) -> Fr:
    if set(left) != set(right):
        raise ValueError("component vectors must use identical axes")
    return max(abs(left[name] - right[name]) for name in left)


def endpoint_substitution_analysis() -> dict:
    """Exact lower/upper endpoint comparison with component-level witnesses."""
    lower_target = component_vector_exact(Fr(0), LOWER_T_WITNESS)
    upper_target = component_vector_exact(Fr(1), UPPER_T_WITNESS)
    lower_candidate = shear_only_vector(LOWER_X)
    upper_candidate = shear_only_vector(UPPER_X)

    lower_gap = component_linf_gap(lower_target, lower_candidate)
    upper_gap = component_linf_gap(upper_target, upper_candidate)
    if lower_gap != LOWER_COMPONENT_GAP or upper_gap != UPPER_COMPONENT_GAP:
        raise RuntimeError("registered exact endpoint-gap witness drift")
    return {
        "lower": {
            "target_parameter": {"s": "0", "t": str(LOWER_T_WITNESS)},
            "target_components": {
                key: str(value) for key, value in lower_target.items()
            },
            "shear_only_components": {
                key: str(value) for key, value in lower_candidate.items()
            },
            "target_x_c": str(comparator_value_exact(lower_target)),
            "candidate_x_c": str(comparator_value_exact(lower_candidate)),
            "scalar_gap": str(
                abs(
                    comparator_value_exact(lower_target)
                    - comparator_value_exact(lower_candidate)
                )
            ),
            "component_linf_gap": str(lower_gap),
        },
        "upper": {
            "target_parameter": {"s": "1", "t": str(UPPER_T_WITNESS)},
            "target_components": {
                key: str(value) for key, value in upper_target.items()
            },
            "shear_only_components": {
                key: str(value) for key, value in upper_candidate.items()
            },
            "target_x_c": str(comparator_value_exact(upper_target)),
            "candidate_x_c": str(comparator_value_exact(upper_candidate)),
            "scalar_gap": str(
                abs(
                    comparator_value_exact(upper_target)
                    - comparator_value_exact(upper_candidate)
                )
            ),
            "component_linf_gap": str(upper_gap),
        },
        "lower_gap_is_globally_minimal": True,
        "lower_gap_lower_bound_axis": "Omega_tilt=1/50",
        "upper_gap_is_globally_minimal": True,
        "upper_gap_lower_bound_axis": "Omega_tilt=3/100",
        "full_endpoint_vectors_realized": False,
    }


def analytic_state(n_efolds: np.ndarray, sigma2_initial: float) -> dict[str, np.ndarray]:
    """Exact expanding Bianchi-I dust solution in Hubble-normalized variables."""
    if not 0.0 <= sigma2_initial <= 1.0:
        raise ValueError("sigma2_initial must lie in [0, 1]")
    n = np.asarray(n_efolds, dtype=np.float64)
    exp3n = np.exp(3.0 * n)
    denominator = sigma2_initial + (1.0 - sigma2_initial) * exp3n
    sigma2 = sigma2_initial / denominator
    hubble = np.exp(-3.0 * n) * np.sqrt(denominator)
    density = 3.0 * (1.0 - sigma2_initial) * np.exp(-3.0 * n)
    return {"Sigma2": sigma2, "H": hubble, "rho": density}


def _dust_rhs(_n_efolds: float, state: np.ndarray) -> np.ndarray:
    sigma2, log_hubble, density = state
    return np.asarray(
        (
            -3.0 * sigma2 * (1.0 - sigma2),
            -1.5 * (1.0 + sigma2),
            -3.0 * density,
        ),
        dtype=np.float64,
    )


@dataclass(frozen=True)
class DustDevelopment:
    sigma2_initial: float
    success: bool
    interval_efolds: float
    max_normalized_gauss_residual: float
    max_sigma2_exact_error: float
    max_hubble_relative_error: float
    min_density: float
    min_hubble: float


def develop_dust_witness(sigma2_initial: float) -> DustDevelopment:
    """Integrate one independent five-e-fold ODE witness and compare to exact form."""
    initial = np.asarray(
        (sigma2_initial, 0.0, 3.0 * (1.0 - sigma2_initial)),
        dtype=np.float64,
    )
    solution = solve_ivp(
        _dust_rhs,
        (0.0, FIVE_EFOLDS),
        initial,
        method="DOP853",
        rtol=1.0e-12,
        atol=1.0e-14,
        max_step=0.05,
    )
    exact = analytic_state(solution.t, sigma2_initial)
    sigma2 = solution.y[0]
    hubble = np.exp(solution.y[1])
    density = solution.y[2]
    normalized_gauss = sigma2 + density / (3.0 * hubble**2) - 1.0
    return DustDevelopment(
        sigma2_initial=sigma2_initial,
        success=bool(solution.success and solution.t[-1] >= FIVE_EFOLDS),
        interval_efolds=float(solution.t[-1]),
        max_normalized_gauss_residual=float(np.max(np.abs(normalized_gauss))),
        max_sigma2_exact_error=float(np.max(np.abs(sigma2 - exact["Sigma2"]))),
        max_hubble_relative_error=float(
            np.max(np.abs(hubble - exact["H"]) / exact["H"])
        ),
        min_density=float(np.min(density)),
        min_hubble=float(np.min(hubble)),
    )


def run_scalar_match_grid(size: int = GRID_SIZE) -> dict:
    """Run valid dust developments across the scalar endpoint interval.

    These developments are a negative control.  Passing their Einstein--dust
    equations does not repair the component-vector mismatch.
    """
    if size < 2:
        raise ValueError("grid size must be at least two")
    grid = np.linspace(float(LOWER_X), float(UPPER_X), size)
    rows = [develop_dust_witness(float(value)) for value in grid]
    return {
        "grid_size": size,
        "interval": [str(LOWER_X), str(UPPER_X)],
        "all_developments_succeeded": all(row.success for row in rows),
        "minimum_interval_efolds": min(row.interval_efolds for row in rows),
        "max_normalized_gauss_residual": max(
            row.max_normalized_gauss_residual for row in rows
        ),
        "max_sigma2_exact_error": max(row.max_sigma2_exact_error for row in rows),
        "max_hubble_relative_error": max(
            row.max_hubble_relative_error for row in rows
        ),
        "minimum_density": min(row.min_density for row in rows),
        "minimum_hubble": min(row.min_hubble for row in rows),
        "expanding_branch_preserved": all(row.min_hubble > 0.0 for row in rows),
        "lorentzian_metric_signature_fixed_by_ansatz": True,
        "dust_energy_conditions_preserved": all(
            row.min_density >= 0.0 for row in rows
        ),
        "normal_equals_matter_frame": True,
        "vorticity_exact": "0",
        "tilt_exact": "0",
        "spatial_curvature_exact": "0",
        "scientific_role": "valid_scalar-match_negative_control_only",
    }
