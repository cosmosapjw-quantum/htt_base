"""Catalog-independent K6 continuum mechanics for PR-123.

Only analytic fields enter this module.  It has no catalogue, mask, transfer,
or empirical artifact interface and cannot report observed vorticity.
"""
from __future__ import annotations

from typing import Any

import numpy as np

from .oracle_lab import PropertyResult, content_sha256, make_outcome


def derivative_periodic(field: np.ndarray, spacing: float, axis: int, order: int) -> np.ndarray:
    if order == 2:
        return (np.roll(field, -1, axis) - np.roll(field, 1, axis)) / (2.0 * spacing)
    if order == 4:
        return (
            -np.roll(field, -2, axis)
            + 8.0 * np.roll(field, -1, axis)
            - 8.0 * np.roll(field, 1, axis)
            + np.roll(field, 2, axis)
        ) / (12.0 * spacing)
    raise ValueError("order must be 2 or 4")


def derivative_closed(field: np.ndarray, spacing: float, axis: int, order: int) -> np.ndarray:
    values = np.moveaxis(np.asarray(field, float), axis, 0)
    if values.shape[0] < 5:
        raise ValueError("closed derivative requires at least five grid points")
    out = np.empty_like(values)
    if order == 2:
        out[1:-1] = (values[2:] - values[:-2]) / (2.0 * spacing)
        out[0] = (-3.0 * values[0] + 4.0 * values[1] - values[2]) / (2.0 * spacing)
        out[-1] = (3.0 * values[-1] - 4.0 * values[-2] + values[-3]) / (2.0 * spacing)
    elif order == 4:
        out[2:-2] = (
            -values[4:] + 8.0 * values[3:-1] - 8.0 * values[1:-3] + values[:-4]
        ) / (12.0 * spacing)
        out[0] = (-25.0 * values[0] + 48.0 * values[1] - 36.0 * values[2] + 16.0 * values[3] - 3.0 * values[4]) / (12.0 * spacing)
        out[1] = (-3.0 * values[0] - 10.0 * values[1] + 18.0 * values[2] - 6.0 * values[3] + values[4]) / (12.0 * spacing)
        out[-2] = (3.0 * values[-1] + 10.0 * values[-2] - 18.0 * values[-3] + 6.0 * values[-4] - values[-5]) / (12.0 * spacing)
        out[-1] = (25.0 * values[-1] - 48.0 * values[-2] + 36.0 * values[-3] - 16.0 * values[-4] + 3.0 * values[-5]) / (12.0 * spacing)
    else:
        raise ValueError("order must be 2 or 4")
    return np.moveaxis(out, 0, axis)


def curl_divergence(
    velocity: np.ndarray, spacing: float, order: int, *, periodic: bool
) -> tuple[np.ndarray, np.ndarray]:
    derivative = derivative_periodic if periodic else derivative_closed
    dv = lambda component, axis: derivative(velocity[component], spacing, axis, order)
    curl = np.array((dv(2, 1) - dv(1, 2), dv(0, 2) - dv(2, 0), dv(1, 0) - dv(0, 1)))
    divergence = dv(0, 0) + dv(1, 1) + dv(2, 2)
    return curl, divergence


def _vector_l2(field: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.sum(np.asarray(field, float) ** 2, axis=0))))


def _scalar_l2(field: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.asarray(field, float) ** 2)))


def _periodic_coordinates(n: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    spacing = 2.0 * np.pi / n
    axis = np.arange(n, dtype=float) * spacing
    return (*np.meshgrid(axis, axis, axis, indexing="ij"), spacing)


def _periodic_fields(n: int) -> dict[str, Any]:
    x, y, z, spacing = _periodic_coordinates(n)
    phi = np.sin(x) * np.sin(y) * np.sin(z)
    potential = np.array((np.cos(x) * np.sin(y) * np.sin(z), np.sin(x) * np.cos(y) * np.sin(z), np.sin(x) * np.sin(y) * np.cos(z)))
    solenoidal = np.array((np.sin(z), np.sin(x), np.sin(y)))
    solenoidal_curl = np.array((np.cos(y), np.cos(z), np.cos(x)))
    return {
        "coordinates": (x, y, z),
        "spacing": spacing,
        "potential": (potential, np.zeros_like(potential), -3.0 * phi),
        "mixed": (potential + 0.4 * solenoidal, 0.4 * solenoidal_curl, -3.0 * phi),
        "solenoidal": solenoidal,
        "solenoidal_curl": solenoidal_curl,
    }


def _boundary_fields(n: int) -> dict[str, Any]:
    axis = np.linspace(-1.0, 1.0, n)
    x, y, z = np.meshgrid(axis, axis, axis, indexing="ij")
    spacing = float(axis[1] - axis[0])
    solid = np.array((-0.7 * y, 0.7 * x, np.zeros_like(x)))
    solid_curl = np.array((np.zeros_like(x), np.zeros_like(x), np.full_like(x, 1.4)))
    manufactured = np.array((np.exp(x) + y * z + 0.1 * x * y, np.sin(y) + x * z**2 + 0.2 * x * y, np.cos(z) + x**2 * y + 0.1 * y * z))
    manufactured_curl = np.array((x**2 + 0.1 * z - 2.0 * x * z, y - 2.0 * x * y, z**2 - z + 0.2 * y - 0.1 * x))
    manufactured_div = np.exp(x) + np.cos(y) - np.sin(z) + 0.2 * x + 0.2 * y
    return {
        "spacing": spacing,
        "solid": (solid, solid_curl, np.zeros_like(x)),
        "manufactured": (manufactured, manufactured_curl, manufactured_div),
    }


def _observed_order(spacings: list[float], errors: list[float]) -> float:
    return float(np.polyfit(np.log(spacings), np.log(errors), 1)[0])


def _continuum_summary(spacings: list[float], errors: list[float], power: int) -> dict[str, float]:
    design = np.column_stack((np.ones(len(spacings)), np.asarray(spacings) ** power))
    intercept, coefficient = np.linalg.lstsq(design, np.asarray(errors), rcond=None)[0]
    residual = np.asarray(errors) - design @ np.array((intercept, coefficient))
    return {
        "intercept": float(intercept),
        "coefficient": float(coefficient),
        "max_fit_residual": float(np.max(np.abs(residual))),
        "numerical_upper_bound": float(abs(intercept) + np.max(np.abs(residual))),
    }


def _midpoint_interpolation_error(n: int) -> float:
    fields = _periodic_fields(n)
    velocity = fields["mixed"][0]
    interpolated = sum(
        np.roll(velocity, (-ix, -iy, -iz), axis=(1, 2, 3))
        for ix in (0, 1) for iy in (0, 1) for iz in (0, 1)
    ) / 8.0
    h = fields["spacing"]
    axis = (np.arange(n, dtype=float) + 0.5) * h
    x, y, z = np.meshgrid(axis, axis, axis, indexing="ij")
    phi_velocity = np.array((np.cos(x) * np.sin(y) * np.sin(z), np.sin(x) * np.cos(y) * np.sin(z), np.sin(x) * np.sin(y) * np.cos(z)))
    exact = phi_velocity + 0.4 * np.array((np.sin(z), np.sin(x), np.sin(y)))
    return _vector_l2(interpolated - exact)


def _amplitude_decomposition(n: int, order: int) -> dict[str, float]:
    fields = _periodic_fields(n)
    x, _, _, = fields["coordinates"]
    h = fields["spacing"]
    base = fields["solenoidal"]
    amplitude = 1.0 + 0.15 * np.sin(x)
    full_curl, _ = curl_divergence(amplitude[None, ...] * base, h, order, periodic=True)
    kernel_curl, _ = curl_divergence(base, h, order, periodic=True)
    grad_a = np.array((derivative_periodic(amplitude, h, 0, order), derivative_periodic(amplitude, h, 1, order), derivative_periodic(amplitude, h, 2, order)))
    amplitude_term = np.cross(np.moveaxis(grad_a, 0, -1), np.moveaxis(base, 0, -1))
    amplitude_term = np.moveaxis(amplitude_term, -1, 0)
    kernel_term = amplitude[None, ...] * kernel_curl
    closure = _vector_l2(full_curl - kernel_term - amplitude_term)
    scale = max(_vector_l2(full_curl), np.finfo(float).tiny)
    return {
        "kernel_rms": _vector_l2(kernel_term),
        "amplitude_gradient_rms": _vector_l2(amplitude_term),
        "full_rms": _vector_l2(full_curl),
        "closure_rms": closure,
        "closure_relative": closure / scale,
    }


def _sqrt2_tensor_ensemble(n: int, order: int) -> dict[str, float]:
    axis = np.linspace(-1.0, 1.0, n)
    coordinates = np.meshgrid(axis, axis, axis, indexing="ij")
    spacing = float(axis[1] - axis[0])
    curl_energy = 0.0
    divergence_energy = 0.0
    gradient_atoms: list[np.ndarray] = []
    for component in range(3):
        for derivative_axis in range(3):
            for sign in (-1.0, 1.0):
                velocity = np.zeros((3, n, n, n), float)
                velocity[component] = sign * coordinates[derivative_axis]
                curl, divergence = curl_divergence(
                    velocity, spacing, order, periodic=False
                )
                curl_energy += float(np.mean(np.sum(curl * curl, axis=0))) / 18.0
                divergence_energy += float(np.mean(divergence * divergence)) / 18.0
                gradient = np.zeros((3, 3), float)
                gradient[component, derivative_axis] = sign
                gradient_atoms.append(gradient.reshape(-1))
    atoms = np.asarray(gradient_atoms)
    gradient_mean = np.mean(atoms, axis=0)
    gradient_covariance = (atoms - gradient_mean).T @ (atoms - gradient_mean) / len(atoms)
    covariance_target = np.eye(9) / 9.0
    correlated = np.array((sum(coordinates),) * 3)
    challenge_curl, challenge_div = curl_divergence(
        correlated, spacing, order, periodic=False
    )
    challenge_ratio = _vector_l2(challenge_curl) / _scalar_l2(challenge_div)
    return {
        "ratio": float(np.sqrt(curl_energy / divergence_energy)),
        "curl_energy": curl_energy,
        "divergence_energy": divergence_energy,
        "correlated_challenge_ratio": challenge_ratio,
        "signed_atom_count": len(atoms),
        "gradient_mean_norm": float(np.linalg.norm(gradient_mean)),
        "gradient_covariance_isotropy_max_error": float(
            np.max(np.abs(gradient_covariance - covariance_target))
        ),
    }


def run_second_order_only_mutant(periodic_grids: list[int]) -> dict[str, Any]:
    """Execute D2 while falsely presenting it as the registered D4 branch."""
    errors, spacings = [], []
    for n in periodic_grids:
        fields = _periodic_fields(n)
        h = fields["spacing"]
        mixed, exact_curl, exact_div = fields["mixed"]
        curl, divergence = curl_divergence(mixed, h, 2, periodic=True)
        errors.append(float(np.hypot(
            _vector_l2(curl - exact_curl),
            _scalar_l2(divergence - exact_div),
        )))
        spacings.append(h)
    return {
        "executed_grid_count": len(periodic_grids),
        "claimed_order_four_errors": errors,
        "claimed_order_four_observed_order": _observed_order(spacings, errors),
        "field_interpretation": "finite_grid_field_content",
    }


def run_k6_continuum_suite(
    contract: dict[str, Any],
    *,
    consumer_inventory: list[str],
    unexpected_consumers: list[str],
) -> tuple[dict[str, Any], Any]:
    periodic_grids = [int(value) for value in contract["periodic_grids"]]
    boundary_grids = [int(value) for value in contract["boundary_grids"]]
    orders = [int(value) for value in contract["stencil_orders"]]
    periodic_report: dict[str, Any] = {}
    boundary_report: dict[str, Any] = {}
    for order in orders:
        mixed_errors, potential_div_errors, spacings = [], [], []
        for n in periodic_grids:
            fields = _periodic_fields(n); h = fields["spacing"]; spacings.append(h)
            mixed, exact_curl, exact_div = fields["mixed"]
            curl, divergence = curl_divergence(mixed, h, order, periodic=True)
            mixed_errors.append(float(np.hypot(_vector_l2(curl - exact_curl), _scalar_l2(divergence - exact_div))))
            potential, _, potential_div = fields["potential"]
            _, numerical_div = curl_divergence(potential, h, order, periodic=True)
            potential_div_errors.append(_scalar_l2(numerical_div - potential_div))
        periodic_report[str(order)] = {
            "spacings": spacings,
            "mixed_errors": mixed_errors,
            "potential_divergence_errors": potential_div_errors,
            "mixed_observed_order": _observed_order(spacings, mixed_errors),
            "potential_observed_order": _observed_order(spacings, potential_div_errors),
            "continuum": _continuum_summary(spacings, mixed_errors, order),
        }
        manufactured_full, manufactured_interior, manufactured_collar = [], [], []
        solid_errors, boundary_spacings = [], []
        for n in boundary_grids:
            fields = _boundary_fields(n); h = fields["spacing"]; boundary_spacings.append(h)
            manufactured, exact_curl, exact_div = fields["manufactured"]
            curl, divergence = curl_divergence(manufactured, h, order, periodic=False)
            point_error = np.sqrt(
                np.sum((curl - exact_curl) ** 2, axis=0)
                + (divergence - exact_div) ** 2
            )
            collar_mask = np.ones(point_error.shape, dtype=bool)
            collar_mask[2:-2, 2:-2, 2:-2] = False
            manufactured_full.append(_scalar_l2(point_error))
            manufactured_interior.append(_scalar_l2(point_error[2:-2, 2:-2, 2:-2]))
            manufactured_collar.append(_scalar_l2(point_error[collar_mask]))
            solid, solid_curl, solid_div = fields["solid"]
            curl, divergence = curl_divergence(solid, h, order, periodic=False)
            solid_errors.append(float(np.hypot(_vector_l2(curl - solid_curl), _scalar_l2(divergence - solid_div))))
        boundary_report[str(order)] = {
            "spacings": boundary_spacings,
            "manufactured_full_errors": manufactured_full,
            "manufactured_interior_errors": manufactured_interior,
            "manufactured_boundary_collar_errors": manufactured_collar,
            "manufactured_observed_order": _observed_order(boundary_spacings, manufactured_full),
            "interior_observed_order": _observed_order(boundary_spacings, manufactured_interior),
            "boundary_collar_observed_order": _observed_order(boundary_spacings, manufactured_collar),
            "solid_body_max_error": max(solid_errors),
            "boundary_collar_width": 2,
        }
    interpolation_errors = [_midpoint_interpolation_error(n) for n in periodic_grids]
    interpolation_order = _observed_order([2.0 * np.pi / n for n in periodic_grids], interpolation_errors)
    decomposition = {str(order): _amplitude_decomposition(periodic_grids[-1], order) for order in orders}
    sqrt2 = {str(order): _sqrt2_tensor_ensemble(17, order) for order in orders}
    mutant = run_second_order_only_mutant(periodic_grids)
    order_min = contract["observed_order_minimum"]
    continuum_pass = all(
        periodic_report[str(order)]["continuum"]["numerical_upper_bound"]
        <= contract["continuum_upper_bound_max"][str(order)]
        for order in orders
    )
    boundary_decomposition_pass = all(
        boundary_report[str(order)]["interior_observed_order"]
        >= order_min[f"boundary_order_{order}"]
        and boundary_report[str(order)]["boundary_collar_observed_order"]
        >= order_min[f"boundary_order_{order}"]
        for order in orders
    )
    sqrt2_error = max(
        abs(value["ratio"] - np.sqrt(2.0)) for value in sqrt2.values()
    )
    challenge_suspends_lock = all(
        abs(value["correlated_challenge_ratio"] - np.sqrt(2.0)) > 0.1
        for value in sqrt2.values()
    )
    signed_covariance_pass = all(
        value["signed_atom_count"] == 18
        and value["gradient_mean_norm"] <= contract["sqrt2_absolute_tolerance"]
        and value["gradient_covariance_isotropy_max_error"]
        <= contract["sqrt2_absolute_tolerance"]
        for value in sqrt2.values()
    )
    properties = (
        PropertyResult("analytic_anchors", max(boundary_report[str(order)]["solid_body_max_error"] for order in orders) < contract["exact_anchor_absolute_tolerance"], max(boundary_report[str(order)]["solid_body_max_error"] for order in orders), contract["exact_anchor_absolute_tolerance"], "solid-body curl and divergence"),
        PropertyResult("observed_orders", periodic_report["2"]["mixed_observed_order"] >= order_min["order_2"] and periodic_report["4"]["mixed_observed_order"] >= order_min["order_4"], min(periodic_report["2"]["mixed_observed_order"], periodic_report["4"]["mixed_observed_order"]), f">={order_min['order_2']}/{order_min['order_4']}", "mixed Helmholtz D2/D4"),
        PropertyResult("boundary_order", boundary_report["2"]["manufactured_observed_order"] >= order_min["boundary_order_2"] and boundary_report["4"]["manufactured_observed_order"] >= order_min["boundary_order_4"], min(boundary_report["2"]["manufactured_observed_order"], boundary_report["4"]["manufactured_observed_order"]), f">={order_min['boundary_order_2']}/{order_min['boundary_order_4']}", "manufactured closed-boundary field"),
        PropertyResult("boundary_decomposition", boundary_decomposition_pass, min(min(value["interior_observed_order"], value["boundary_collar_observed_order"]) for value in boundary_report.values()), f">={order_min['boundary_order_2']}/{order_min['boundary_order_4']}", "full, strict-interior, and boundary-collar curves execute separately"),
        PropertyResult("decomposition", all(decomposition[str(order)]["closure_relative"] <= contract["product_rule_closure_finest_relative_tolerance"][f"order_{order}"] for order in orders), max(decomposition[str(order)]["closure_relative"] for order in orders), str(contract["product_rule_closure_finest_relative_tolerance"]), "kernel plus amplitude-gradient closure"),
        PropertyResult("interpolation", interpolation_order >= contract["interpolation_observed_order_minimum"], interpolation_order, contract["interpolation_observed_order_minimum"], "periodic trilinear midpoint error"),
        PropertyResult("continuum_upper_bound", continuum_pass, max(periodic_report[str(order)]["continuum"]["numerical_upper_bound"] for order in orders), str(contract["continuum_upper_bound_max"]), "intercept plus max fit residual"),
        PropertyResult("sqrt2", bool(sqrt2_error < contract["sqrt2_absolute_tolerance"] and signed_covariance_pass and challenge_suspends_lock), float(sqrt2_error), contract["sqrt2_absolute_tolerance"], "explicit signed zero-mean isotropic gradient-tensor covariance cubature plus correlated challenge"),
        PropertyResult("two_stencil_execution", set(orders) == {2, 4}, len(orders), 2, "both numerical operators executed on identical fields"),
        PropertyResult("no_empirical_consumer", not unexpected_consumers and not contract["empirical_inputs"] and not contract["empirical_consumers"], len(unexpected_consumers), 0, "repository consumer inventory is allowlisted"),
    )
    mutant_failed = (
        "observed_orders",
        "two_stencil_execution",
    ) if mutant["claimed_order_four_observed_order"] < order_min["order_4"] else ()
    outcome = make_outcome(
        "low_order_curl_stencil", "k6_catalog_independent_continuum", properties,
        reference_symbol="run_k6_continuum_suite",
        mutant_symbol="run_second_order_only_mutant",
        fixture_hash=content_sha256({"contract": contract, "consumer_inventory": consumer_inventory}),
        reference_execution_count=1,
        mutant_execution_count=1,
        mutant_failed_properties=mutant_failed,
        metrics={"periodic_orders": {key: value["mixed_observed_order"] for key, value in periodic_report.items()}, "boundary_orders": {key: value["manufactured_observed_order"] for key, value in boundary_report.items()}, "interpolation_order": interpolation_order, "sqrt2": sqrt2, "mutant": mutant},
    )
    report = {
        "schema": "htt.pr123.k6_continuum_card.v3",
        "input_mode": "analytic_manufactured",
        "periodic_grids": periodic_grids,
        "boundary_grids": boundary_grids,
        "stencil_orders": orders,
        "analytic_fields": list(contract["analytic_fields"]),
        "periodic": periodic_report,
        "boundary": boundary_report,
        "interpolation": {"errors": interpolation_errors, "observed_order": interpolation_order},
        "amplitude_gradient_decomposition": decomposition,
        "sqrt2_residual_lock": {"expected": float(np.sqrt(2.0)), "observed": sqrt2, "domain": contract["sqrt2_domain"], "correlated_challenge_suspends_lock": challenge_suspends_lock},
        "empirical_inputs": [],
        "consumer_inventory": consumer_inventory,
        "unexpected_consumers": unexpected_consumers,
        "empirical_consumers": unexpected_consumers,
        "empirical_consumer_count": len(unexpected_consumers),
        "interpretation": "catalog-independent numerical upper-bound mechanics only",
        "scientific_status": "OPEN",
    }
    return report, outcome
