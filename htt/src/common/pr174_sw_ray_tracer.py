"""PR-174: SW-only real-space anisotropic ray-integration mechanics.

hypothesis_only / public_use=false / ceiling roadmap_rescue_v1:C1.

A numerical RK4 null-ray energy-transport integration on a PRESCRIBED
kinematic diagonal Bianchi I background is compared against the
independent conserved-momentum closed form ray by ray, and the induced
full-sky temperature pattern is compared against the closed-form linear
parity/shear quadrupole prediction. An analytic mismatch blocks the
mechanics WITHOUT selecting which side is physically correct.

No likelihood, no transfer registration, no production consumer, no
mixing with the FLRW LoS Bessel path. The background is an analytic
stand-in, not an Einstein-equation solution; nothing here is an
observable prediction.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import numpy as np

SPEC_PATH = Path("docs/research_program/long_horizon_rescue/pr174_spec.yaml")

TERMINAL_CONSISTENT = "SW_ONLY_MECHANICS_CONSISTENT_WITH_CLOSED_FORM"
TERMINAL_MISMATCH = "BLOCKED_ANALYTIC_MISMATCH_UNATTRIBUTED"
TERMINAL_INTEGRITY = "BLOCKED_NO_SCIENTIFIC_RESULT"


@dataclass(frozen=True)
class Pr174Config:
    """Preregistered configuration (mirrors pr174_spec.yaml; frozen)."""

    b_vector: tuple[float, float, float] = (2.0e-6, -0.5e-6, -1.5e-6)
    t_emit_over_t0: float = 1.0e-3
    steps_primary: int = 1024
    steps_convergence: tuple[int, ...] = (256, 512, 1024)
    n_costheta: int = 32
    n_phi: int = 64
    ell_max: int = 4
    ray_level_relative_energy_error_max: float = 1.0e-10
    rk4_convergence_order_window: tuple[float, float] = (3.7, 4.3)
    quadrupole_relative_match_max: float = 5.0e-6
    odd_ell_relative_power_max: float = 1.0e-12
    monopole_dipole_residual_relative_max: float = 1.0e-12

    def config_hash(self) -> str:
        payload = json.dumps(
            {
                "b_vector": list(self.b_vector),
                "t_emit_over_t0": self.t_emit_over_t0,
                "steps_primary": self.steps_primary,
                "steps_convergence": list(self.steps_convergence),
                "n_costheta": self.n_costheta,
                "n_phi": self.n_phi,
                "ell_max": self.ell_max,
                "tolerances": [
                    self.ray_level_relative_energy_error_max,
                    list(self.rk4_convergence_order_window),
                    self.quadrupole_relative_match_max,
                    self.odd_ell_relative_power_max,
                    self.monopole_dipole_residual_relative_max,
                ],
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    def validate(self) -> None:
        if abs(sum(self.b_vector)) > 1e-18:
            raise ValueError("trace condition sum_i B_i = 0 violated")
        if not 0.0 < self.t_emit_over_t0 < 1.0:
            raise ValueError("t_emit_over_t0 must lie in (0, 1)")
        if self.steps_primary != max(self.steps_convergence):
            raise ValueError("steps_primary must equal max(steps_convergence)")


# ---------------------------------------------------------------------------
# Background (prescribed kinematic Bianchi I; NOT an Einstein solution)
# ---------------------------------------------------------------------------

def log_scale_factor(axis_b: float, s: float) -> float:
    """ln a_i at s = ln(t/t0), for a_i = (t/t0)^(2/3) exp(B_i t/t0)."""
    return (2.0 / 3.0) * s + axis_b * math.exp(s)


def transport_coefficient(b_vector: np.ndarray, s: float) -> np.ndarray:
    """t*H_i at s = ln(t/t0): d(ln a_i)/ds = 2/3 + B_i * t/t0, shape (3,)."""
    return (2.0 / 3.0) + b_vector * math.exp(s)


# ---------------------------------------------------------------------------
# Tracer: RK4 transport of physical momentum components in s = ln(t/t0)
# ---------------------------------------------------------------------------

def rk4_ray_energies(
    directions: np.ndarray,
    config: Pr174Config,
    n_steps: int,
    coefficient: Callable[[np.ndarray, float], np.ndarray] = transport_coefficient,
    stages: int = 4,
) -> np.ndarray:
    """Integrate dq_i/ds = -coef_i(s) q_i backward for a batch of rays.

    ``directions`` has shape (N, 3); returns E_emit of shape (N,). Every
    ray carries its own momentum state q; the per-axis coefficient is
    direction-independent, so the batch update applies the identical RK4
    arithmetic to each ray simultaneously.

    ``stages=4`` is classical RK4; ``stages=1`` is forward Euler and
    exists only so the mutation battery can demonstrate the
    convergence-order guard kills an integrator downgrade.
    """
    if stages not in (4, 1):
        raise ValueError("stages must be 4 (RK4) or 1 (Euler mutant)")
    s_end = math.log(config.t_emit_over_t0)
    h = s_end / float(n_steps)
    q = np.array(directions, dtype=np.float64)
    if q.ndim == 1:
        q = q[None, :]
    b = np.array(config.b_vector, dtype=np.float64)
    s = 0.0
    for _ in range(n_steps):
        if stages == 4:
            c1 = coefficient(b, s)
            c_mid = coefficient(b, s + 0.5 * h)
            c4 = coefficient(b, s + h)
            k1 = -c1[None, :] * q
            k2 = -c_mid[None, :] * (q + 0.5 * h * k1)
            k3 = -c_mid[None, :] * (q + 0.5 * h * k2)
            k4 = -c4[None, :] * (q + h * k3)
            q = q + (h / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
        else:
            k1 = -coefficient(b, s)[None, :] * q
            q = q + h * k1
        s += h
    return np.sqrt(np.sum(q * q, axis=1))


def rk4_ray_energy(
    direction: np.ndarray,
    config: Pr174Config,
    n_steps: int,
    coefficient: Callable[[np.ndarray, float], np.ndarray] = transport_coefficient,
    stages: int = 4,
) -> float:
    """Single-ray wrapper around :func:`rk4_ray_energies`."""
    return float(
        rk4_ray_energies(
            np.asarray(direction, dtype=np.float64)[None, :],
            config,
            n_steps,
            coefficient=coefficient,
            stages=stages,
        )[0]
    )


# ---------------------------------------------------------------------------
# Independent analytic fixture: conserved covariant momentum (no integration)
# ---------------------------------------------------------------------------

def closed_form_ray_energy(direction: np.ndarray, config: Pr174Config) -> float:
    """E_emit(n) = sqrt(sum_i n_i^2 (a_i(t0)/a_i(t_e))^2), p_i conserved."""
    s_emit = math.log(config.t_emit_over_t0)
    total = 0.0
    for i in range(3):
        ln_ratio = log_scale_factor(config.b_vector[i], 0.0) - log_scale_factor(
            config.b_vector[i], s_emit
        )
        total += float(direction[i]) ** 2 * math.exp(2.0 * ln_ratio)
    return math.sqrt(total)


def linear_quadrupole_prediction(config: Pr174Config) -> dict[str, float]:
    """Closed-form real-basis a_2m of -sum_i (n_i^2 - 1/3) delta_beta_i."""
    delta_beta = [
        b * (1.0 - config.t_emit_over_t0) for b in config.b_vector
    ]
    a20 = -2.0 * math.sqrt(math.pi / 5.0) * delta_beta[2]
    a22 = -2.0 * math.sqrt(math.pi / 15.0) * (delta_beta[0] - delta_beta[1])
    return {"a20": a20, "a21": 0.0, "a2m1": 0.0, "a22": a22, "a2m2": 0.0}


# ---------------------------------------------------------------------------
# Direction grid and real spherical harmonics (explicit, ell <= 4)
# ---------------------------------------------------------------------------

def direction_grid(config: Pr174Config) -> tuple[np.ndarray, np.ndarray]:
    """Gauss-Legendre x uniform-phi grid: directions (N,3), weights (N,)."""
    nodes, weights = np.polynomial.legendre.leggauss(config.n_costheta)
    phi = 2.0 * math.pi * np.arange(config.n_phi) / config.n_phi
    w_phi = 2.0 * math.pi / config.n_phi
    cos_t = np.repeat(nodes, config.n_phi)
    w = np.repeat(weights, config.n_phi) * w_phi
    sin_t = np.sqrt(1.0 - cos_t**2)
    phis = np.tile(phi, config.n_costheta)
    dirs = np.stack(
        [sin_t * np.cos(phis), sin_t * np.sin(phis), cos_t], axis=1
    )
    return dirs, w


def real_harmonics(dirs: np.ndarray, ell_max: int) -> dict[str, np.ndarray]:
    """Real orthonormal spherical harmonics up to ell_max as polynomials."""
    x, y, z = dirs[:, 0], dirs[:, 1], dirs[:, 2]
    pi = math.pi
    table: dict[str, np.ndarray] = {
        "a00": np.full(len(dirs), math.sqrt(1.0 / (4.0 * pi))),
        "a10": math.sqrt(3.0 / (4.0 * pi)) * z,
        "a11": math.sqrt(3.0 / (4.0 * pi)) * x,
        "a1m1": math.sqrt(3.0 / (4.0 * pi)) * y,
        "a20": math.sqrt(5.0 / (16.0 * pi)) * (3.0 * z**2 - 1.0),
        "a21": math.sqrt(15.0 / (4.0 * pi)) * x * z,
        "a2m1": math.sqrt(15.0 / (4.0 * pi)) * y * z,
        "a22": math.sqrt(15.0 / (16.0 * pi)) * (x**2 - y**2),
        "a2m2": math.sqrt(15.0 / (4.0 * pi)) * x * y,
    }
    if ell_max >= 3:
        table.update(
            {
                "a30": math.sqrt(7.0 / (16.0 * pi)) * (5.0 * z**3 - 3.0 * z),
                "a31": math.sqrt(21.0 / (32.0 * pi)) * x * (5.0 * z**2 - 1.0),
                "a3m1": math.sqrt(21.0 / (32.0 * pi)) * y * (5.0 * z**2 - 1.0),
                "a32": math.sqrt(105.0 / (16.0 * pi)) * (x**2 - y**2) * z,
                "a3m2": math.sqrt(105.0 / (4.0 * pi)) * x * y * z,
                "a33": math.sqrt(35.0 / (32.0 * pi)) * x * (x**2 - 3.0 * y**2),
                "a3m3": math.sqrt(35.0 / (32.0 * pi)) * y * (3.0 * x**2 - y**2),
            }
        )
    if ell_max >= 4:
        table.update(
            {
                "a40": (3.0 / 16.0)
                * math.sqrt(1.0 / pi)
                * (35.0 * z**4 - 30.0 * z**2 + 3.0),
                "a41": (3.0 / 4.0)
                * math.sqrt(5.0 / (2.0 * pi))
                * x
                * z
                * (7.0 * z**2 - 3.0),
                "a4m1": (3.0 / 4.0)
                * math.sqrt(5.0 / (2.0 * pi))
                * y
                * z
                * (7.0 * z**2 - 3.0),
                "a42": (3.0 / 8.0)
                * math.sqrt(5.0 / pi)
                * (x**2 - y**2)
                * (7.0 * z**2 - 1.0),
                "a4m2": (3.0 / 4.0)
                * math.sqrt(5.0 / pi)
                * x
                * y
                * (7.0 * z**2 - 1.0),
                "a43": (3.0 / 4.0)
                * math.sqrt(35.0 / (2.0 * pi))
                * x
                * z
                * (x**2 - 3.0 * y**2),
                "a4m3": (3.0 / 4.0)
                * math.sqrt(35.0 / (2.0 * pi))
                * y
                * z
                * (3.0 * x**2 - y**2),
                "a44": (3.0 / 16.0)
                * math.sqrt(35.0 / pi)
                * (x**4 - 6.0 * x**2 * y**2 + y**4),
                "a4m4": (3.0 / 4.0)
                * math.sqrt(35.0 / pi)
                * x
                * y
                * (x**2 - y**2),
            }
        )
    return table


def project_alm(
    values: np.ndarray, dirs: np.ndarray, weights: np.ndarray, ell_max: int
) -> dict[str, float]:
    """Quadrature projection a_lm = sum_k w_k Y_lm(n_k) f(n_k)."""
    table = real_harmonics(dirs, ell_max)
    return {key: float(np.sum(weights * basis * values)) for key, basis in table.items()}


# ---------------------------------------------------------------------------
# Mechanics run
# ---------------------------------------------------------------------------

def temperature_map(
    energies_emit: np.ndarray, weights: np.ndarray
) -> np.ndarray:
    """Mean-normalized inverse-redshift map: (1/E_e)/<1/E_e> - 1."""
    inv = 1.0 / energies_emit
    mean = float(np.sum(weights * inv) / np.sum(weights))
    return inv / mean - 1.0


def run_mechanics(
    config: Pr174Config,
    coefficient: Callable[[np.ndarray, float], np.ndarray] = transport_coefficient,
    stages: int = 4,
    map_mutation: Callable[[np.ndarray, np.ndarray], np.ndarray] | None = None,
    prediction: Callable[[Pr174Config], dict[str, float]] | None = None,
) -> dict:
    """Run the full preregistered mechanics comparison.

    The optional overrides exist ONLY for the mutation battery; the
    production path uses the defaults.
    """
    config.validate()
    dirs, weights = direction_grid(config)

    # Ray-level check on a probe subset (stride 61 is coprime to the
    # 64-point phi grid, so the probes sweep mixed phi values and every
    # momentum component appears in mixed directions) plus the three
    # coordinate axes, against the closed form.
    probe_dirs = np.vstack([dirs[::61], np.eye(3)])
    probe_num = rk4_ray_energies(
        probe_dirs, config, config.steps_primary,
        coefficient=coefficient, stages=stages,
    )
    probe_exact = np.array(
        [closed_form_ray_energy(d, config) for d in probe_dirs]
    )
    ray_errors = np.abs(probe_num - probe_exact) / probe_exact
    max_ray_error = float(np.max(ray_errors))

    # Convergence order from the step ladder on a fixed off-axis probe ray.
    probe = np.array([1.0, 1.0, 1.0]) / math.sqrt(3.0)
    e_exact = closed_form_ray_energy(probe, config)
    ladder_errors = []
    for n_steps in config.steps_convergence:
        e_num = rk4_ray_energy(probe, config, n_steps,
                               coefficient=coefficient, stages=stages)
        ladder_errors.append(abs(e_num - e_exact) / e_exact)
    lo, mid = ladder_errors[0], ladder_errors[1]
    if mid == 0.0:
        convergence_order = float("inf")
    else:
        convergence_order = math.log(lo / mid) / math.log(
            config.steps_convergence[1] / config.steps_convergence[0]
        )

    # Full-sky map from the numerical tracer (batched, identical arithmetic).
    energies = rk4_ray_energies(
        dirs, config, config.steps_primary,
        coefficient=coefficient, stages=stages,
    )
    tmap = temperature_map(energies, weights)
    if map_mutation is not None:
        tmap = map_mutation(tmap, dirs)
    alm = project_alm(tmap, dirs, weights, config.ell_max)

    predict = (prediction or linear_quadrupole_prediction)(config)
    quad_keys = ["a20", "a21", "a2m1", "a22", "a2m2"]
    quad_scale = max(abs(predict[k]) for k in quad_keys)
    quad_errors = {
        k: abs(alm[k] - predict[k]) / quad_scale for k in quad_keys
    }
    max_quad_error = max(quad_errors.values())

    quad_power = sum(alm[k] ** 2 for k in quad_keys)
    odd_keys = [k for k in alm if k.startswith(("a1", "a3"))]
    odd_power = sum(alm[k] ** 2 for k in odd_keys)
    odd_ratio = odd_power / quad_power
    residual_keys = ["a00", "a10", "a11", "a1m1"]
    residual_power = sum(alm[k] ** 2 for k in residual_keys)
    residual_ratio = residual_power / quad_power

    checks = {
        "ray_level": max_ray_error <= config.ray_level_relative_energy_error_max,
        "convergence_order": (
            config.rk4_convergence_order_window[0]
            <= convergence_order
            <= config.rk4_convergence_order_window[1]
        ),
        "quadrupole_match": max_quad_error <= config.quadrupole_relative_match_max,
        "odd_ell_parity": odd_ratio <= config.odd_ell_relative_power_max,
        "monopole_dipole_residual": (
            residual_ratio <= config.monopole_dipole_residual_relative_max
        ),
    }
    terminal = (
        TERMINAL_CONSISTENT if all(checks.values()) else TERMINAL_MISMATCH
    )
    return {
        "schema": "htt.pr174.mechanics_result.v1",
        "config_hash": config.config_hash(),
        "terminal": terminal,
        "checks": checks,
        "check_semantics": {
            "discriminating_checks": [
                "ray_level",
                "convergence_order",
                "quadrupole_match",
            ],
            "structural_consistency_guards": [
                "odd_ell_parity",
                "monopole_dipole_residual",
            ],
            "note": (
                "The map is exactly even under point reflection and is "
                "mean-normalized on the same quadrature for ANY per-axis "
                "transport coefficient, so the two structural guards can "
                "fail on the production path only through injected map "
                "defects; independent discrimination of tracer errors is "
                "carried by the three discriminating checks."
            ),
        },
        "max_ray_relative_energy_error": max_ray_error,
        "convergence_ladder_relative_errors": ladder_errors,
        "measured_convergence_order": convergence_order,
        "recovered_alm": alm,
        "predicted_quadrupole": predict,
        "max_quadrupole_relative_error": max_quad_error,
        "odd_ell_relative_power": odd_ratio,
        "monopole_dipole_residual_relative_power": residual_ratio,
        "ray_probe_count": len(ray_errors),
        "interpretation": (
            "SW-only internal forward mechanics on a prescribed kinematic "
            "background; hypothesis_only, ceiling roadmap_rescue_v1:C1; "
            "a mismatch terminal never selects which side is physically "
            "correct; no likelihood, transfer, observable, family, or "
            "geometry content."
        ),
    }


# ---------------------------------------------------------------------------
# Mutation battery (each mutant must be KILLED by its registered guard)
# ---------------------------------------------------------------------------

def _isotropic_coefficient(b_vector: np.ndarray, s: float) -> np.ndarray:
    return np.full(3, 2.0 / 3.0)


def _sign_flipped_coefficient(b_vector: np.ndarray, s: float) -> np.ndarray:
    return -transport_coefficient(b_vector, s)


def _dipole_injection(tmap: np.ndarray, dirs: np.ndarray) -> np.ndarray:
    return tmap + 1.0e-7 * dirs[:, 2]


def _perturbed_prediction(config: Pr174Config) -> dict[str, float]:
    predict = dict(linear_quadrupole_prediction(config))
    predict["a20"] = predict["a20"] * 1.01
    return predict


def _trace_broken_prediction(config: Pr174Config) -> dict[str, float]:
    """Feed a PURE-TRACE shift through the trace-reduced formula.

    The correct deviatoric quadrupole is invariant under
    delta_beta_i -> delta_beta_i + c (a pure trace changes no anisotropy),
    but the shipped trace-reduced a20 formula is valid ONLY for traceless
    input and shifts by -2*sqrt(pi/5)*c. Applying it to shifted input
    therefore exercises the sum_i B_i = 0 requirement of the reduction:
    the mutant prediction disagrees with the (trace-free) recovered map.
    """
    shift = 1.0e-6
    delta_beta = [
        b * (1.0 - config.t_emit_over_t0) + shift for b in config.b_vector
    ]
    a20 = -2.0 * math.sqrt(math.pi / 5.0) * delta_beta[2]
    a22 = -2.0 * math.sqrt(math.pi / 15.0) * (delta_beta[0] - delta_beta[1])
    return {"a20": a20, "a21": 0.0, "a2m1": 0.0, "a22": a22, "a2m2": 0.0}


MUTATIONS: dict[str, dict] = {
    "MUT-174-ISO": {
        "kwargs": {"coefficient": _isotropic_coefficient},
        "killed_by": "ray_level",
    },
    "MUT-174-SIGN": {
        "kwargs": {"coefficient": _sign_flipped_coefficient},
        "killed_by": "ray_level",
    },
    "MUT-174-EULER": {
        "kwargs": {"stages": 1},
        "killed_by": "convergence_order",
    },
    "MUT-174-PARITY": {
        "kwargs": {"map_mutation": _dipole_injection},
        "killed_by": "odd_ell_parity",
    },
    "MUT-174-COEFF": {
        "kwargs": {"prediction": _perturbed_prediction},
        "killed_by": "quadrupole_match",
    },
    "MUT-174-TRACE": {
        "kwargs": {"prediction": _trace_broken_prediction},
        "killed_by": "quadrupole_match",
    },
}


def run_mutation_battery(config: Pr174Config) -> dict:
    """Run every registered mutant; each must fail its registered guard."""
    rows = {}
    for mut_id, entry in MUTATIONS.items():
        result = run_mechanics(config, **entry["kwargs"])
        guard = entry["killed_by"]
        rows[mut_id] = {
            "registered_guard": guard,
            "guard_check_failed": not result["checks"][guard],
            "terminal": result["terminal"],
            "killed": (
                not result["checks"][guard]
                and result["terminal"] == TERMINAL_MISMATCH
            ),
        }
    return {
        "schema": "htt.pr174.mutation_report.v1",
        "config_hash": config.config_hash(),
        "mutations": rows,
        "all_killed": all(row["killed"] for row in rows.values()),
    }
