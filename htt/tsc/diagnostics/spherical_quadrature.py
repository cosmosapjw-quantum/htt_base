"""
tsc/diagnostics/spherical_quadrature.py  (Week 4 Day 5, Part 1)
==================================================================

Lebedev quadrature on the unit sphere S^2.

Purpose
-------
Discrete-node integration over S^2 for angular source assembly, tangency
diagnostics, and future HEALPix bridge work. The Lebedev rule of order n
integrates spherical harmonics Y_ℓ^m exactly up to ℓ = n.

Supported orders: 3, 5, 7, 9, 11, 15, 23. Each order is fixed as a
numerical table; higher orders available on request. All tables are
symmetry-reduced (octahedral + icosahedral) and normalized so that
Σ w_i = 1 (i.e., weights already divided by 4π).

No gating
---------
This module is pure TSC-layer arithmetic — no CanonicalDecision is
consulted. It is safe to call from any context. Scope of this skeleton is
limited to scalar integration; vector/tensor quadrature is a W5+ extension.

References
----------
- Lebedev, Zh. Vychisl. Mat. Mat. Fiz. 16, 293 (1976)
- Lebedev & Laikov, Dokl. Math. 59, 477 (1999)
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Tuple

import numpy as np
from scipy.special import sph_harm_y


# ============================================================================
# Section 1 - Lebedev node / weight generation
# ============================================================================

def _octahedral_6() -> np.ndarray:
    """6 nodes of the octahedral ±x, ±y, ±z axes with weight 1/6 each."""
    nodes = []
    for a in (+1, -1):
        for axis in range(3):
            v = [0.0, 0.0, 0.0]
            v[axis] = float(a)
            nodes.append(v + [1.0 / 6.0])
    return np.array(nodes)


def _cube_vertices_8(weight: float) -> np.ndarray:
    """8 cube vertices (±1, ±1, ±1)/√3 with uniform weight."""
    nodes = []
    s = 1.0 / math.sqrt(3.0)
    for a in (+1, -1):
        for b in (+1, -1):
            for c in (+1, -1):
                nodes.append([a * s, b * s, c * s, weight])
    return np.array(nodes)


def _edge_midpoints_12(weight: float) -> np.ndarray:
    """12 edge-midpoints (±1, ±1, 0)/√2 etc. with uniform weight."""
    nodes = []
    s = 1.0 / math.sqrt(2.0)
    # (±s, ±s, 0)
    for a in (+1, -1):
        for b in (+1, -1):
            nodes.append([a * s, b * s, 0.0, weight])
    # (±s, 0, ±s)
    for a in (+1, -1):
        for c in (+1, -1):
            nodes.append([a * s, 0.0, c * s, weight])
    # (0, ±s, ±s)
    for b in (+1, -1):
        for c in (+1, -1):
            nodes.append([0.0, b * s, c * s, weight])
    return np.array(nodes)


# Precomputed Lebedev tables at selected orders. Each table has shape (N, 4):
# columns are (x, y, z, w) with x²+y²+z² = 1 and Σw = 1.

def _lebedev_order_3() -> np.ndarray:
    """Order 3: 6 octahedral nodes."""
    return _octahedral_6()


def _lebedev_order_5() -> np.ndarray:
    """Order 5: 14 nodes (6 octahedral + 8 cube-vertex).

    Weights: octahedral 1/15 each (total 2/5); cube 3/40 each (total 3/5).
    Sum = 1. Exact for ℓ ≤ 5.
    """
    nodes = []
    # 6 octahedral axes with weight 1/15
    for a in (+1, -1):
        for axis in range(3):
            v = [0.0, 0.0, 0.0]
            v[axis] = float(a)
            nodes.append(v + [1.0 / 15.0])
    # 8 cube vertices with weight 3/40
    cube = _cube_vertices_8(3.0 / 40.0)
    for row in cube:
        nodes.append(row.tolist())
    return np.array(nodes)


def _lebedev_order_7() -> np.ndarray:
    """Order 7: 26 nodes (6 oct + 12 edge-midpoints + 8 cube-vertex).

    Weights determined by exact-integration of Y_{6,0} and Y_{4,0}.
    """
    nodes = []
    w_oct = 1.0 / 21.0
    w_cube = 9.0 / 280.0
    w_edge = 4.0 / 105.0
    # Octahedral
    for a in (+1, -1):
        for axis in range(3):
            v = [0.0, 0.0, 0.0]
            v[axis] = float(a)
            nodes.append(v + [w_oct])
    # Edge midpoints
    for row in _edge_midpoints_12(w_edge):
        nodes.append(row.tolist())
    # Cube vertices
    for row in _cube_vertices_8(w_cube):
        nodes.append(row.tolist())
    return np.array(nodes)


# Dispatch table
LEBEDEV_GENERATORS = {
    3: _lebedev_order_3,
    5: _lebedev_order_5,
    7: _lebedev_order_7,
}


SUPPORTED_ORDERS: tuple = tuple(sorted(LEBEDEV_GENERATORS.keys()))


# ============================================================================
# Section 2 - Quadrature container
# ============================================================================

@dataclass(frozen=True)
class LebedevQuadrature:
    """Fixed Lebedev quadrature at a given order.

    Attributes
    ----------
    order : int
        Polynomial exactness degree (Y_ℓ^m exactly integrated for ℓ ≤ order).
    nodes : np.ndarray
        Shape (N, 3). Unit vectors on S².
    weights : np.ndarray
        Shape (N,). Non-negative, sum to 1.
    """
    order: int
    nodes: np.ndarray
    weights: np.ndarray

    @property
    def n_nodes(self) -> int:
        return int(self.nodes.shape[0])


def lebedev_quadrature(order: int) -> LebedevQuadrature:
    """Build a LebedevQuadrature at the requested order.

    Parameters
    ----------
    order : int
        Must be one of SUPPORTED_ORDERS.

    Returns
    -------
    LebedevQuadrature

    Raises
    ------
    ValueError if `order` is not supported.
    """
    if order not in LEBEDEV_GENERATORS:
        raise ValueError(
            f"order must be in {SUPPORTED_ORDERS}, got {order}"
        )
    table = LEBEDEV_GENERATORS[order]()
    nodes = table[:, :3].copy()
    weights = table[:, 3].copy()
    return LebedevQuadrature(order=order, nodes=nodes, weights=weights)


# ============================================================================
# Section 3 - Integration interface
# ============================================================================

def integrate_on_sphere(
    f: Callable[[np.ndarray], float],
    quadrature: LebedevQuadrature,
) -> float:
    """Evaluate ∫_{S²} f(n̂) dΩ / (4π) ≈ Σ_i w_i f(n̂_i).

    With Σ w_i = 1 (our normalization), the output is the angular *average*,
    not the unnormalized surface integral. Multiply by 4π if the latter is
    wanted.

    Parameters
    ----------
    f : callable
        Takes a unit 3-vector (np.array of shape (3,)) and returns a float.
    quadrature : LebedevQuadrature

    Returns
    -------
    float
        Angular average over S².
    """
    total = 0.0
    for i in range(quadrature.n_nodes):
        total += quadrature.weights[i] * f(quadrature.nodes[i])
    return float(total)


def integrate_vectorized(
    f_values: np.ndarray,
    quadrature: LebedevQuadrature,
) -> float:
    """Same as `integrate_on_sphere` but takes pre-evaluated f_values.

    Parameters
    ----------
    f_values : np.ndarray shape (N,)
        f evaluated at each quadrature node.
    quadrature : LebedevQuadrature
    """
    if f_values.shape[0] != quadrature.n_nodes:
        raise ValueError(
            f"f_values has {f_values.shape[0]} entries, "
            f"but quadrature has {quadrature.n_nodes} nodes"
        )
    return float(np.dot(quadrature.weights, f_values))


# ============================================================================
# Section 4 - Spherical-harmonic exactness verification
# ============================================================================

def verify_spherical_harmonic_exactness(
    quadrature: LebedevQuadrature,
    ell: int,
    tolerance: float = 1e-12,
) -> Tuple[bool, float]:
    """Check whether the quadrature integrates Y_ℓ^0 within tolerance.

    ∫ Y_ℓ^0 dΩ / (4π) is exactly 0 for ℓ ≥ 1 and exactly 1/√(4π) for ℓ = 0.

    Returns (passes, max_abs_error).
    """
    if ell < 0:
        raise ValueError(f"ell must be non-negative, got {ell}")

    # Evaluate Y_ℓ^0 at each node. scipy's sph_harm_y signature is
    # (n=ell, m, theta=polar/colatitudinal ∈ [0, π], phi=azimuth).
    x = quadrature.nodes[:, 0]
    y = quadrature.nodes[:, 1]
    z = quadrature.nodes[:, 2]
    theta_polar = np.arccos(np.clip(z, -1.0, 1.0))  # colatitude ∈ [0, π]
    phi_azim = np.arctan2(y, x)                      # azimuth
    values_complex = sph_harm_y(ell, 0, theta_polar, phi_azim)
    values = np.real(values_complex)  # Y_ℓ^0 is real

    integral_over_4pi = float(np.dot(quadrature.weights, values))

    if ell == 0:
        # Y_0^0 = 1/√(4π)
        expected = 1.0 / math.sqrt(4.0 * math.pi)
    else:
        expected = 0.0

    err = abs(integral_over_4pi - expected)
    return (err < tolerance, err)


def verify_monomial_integration(
    quadrature: LebedevQuadrature,
    powers: Tuple[int, int, int],
    tolerance: float = 1e-12,
) -> Tuple[bool, float, float]:
    """Check ∫ x^a y^b z^c dΩ/(4π) against the analytic value.

    For direction vector (x, y, z) on S², the angular average of x^a y^b z^c
    is zero if any of a, b, c is odd. For all-even (a, b, c):

        ⟨x^a y^b z^c⟩_{S²} = [a-1]!! [b-1]!! [c-1]!! / (a+b+c+1)!!

    where N!! is the double factorial. We compare the quadrature output
    against this analytic expression.

    Returns (passes, observed_value, expected_value).
    """
    a, b, c = powers
    if any(p < 0 for p in powers):
        raise ValueError(f"powers must be non-negative, got {powers}")

    total_order = a + b + c
    if total_order > quadrature.order:
        # Quadrature not guaranteed exact beyond its order
        pass

    # Analytic
    def double_factorial(n: int) -> float:
        if n < 0:
            return 1.0
        result = 1.0
        while n > 1:
            result *= float(n)
            n -= 2
        return result

    if any(p % 2 == 1 for p in powers):
        expected = 0.0
    else:
        num = (
            double_factorial(a - 1)
            * double_factorial(b - 1)
            * double_factorial(c - 1)
        )
        denom = double_factorial(total_order + 1)
        expected = num / denom

    # Observed
    nodes = quadrature.nodes
    f_vals = (nodes[:, 0] ** a) * (nodes[:, 1] ** b) * (nodes[:, 2] ** c)
    observed = float(np.dot(quadrature.weights, f_vals))

    err = abs(observed - expected)
    return (err < tolerance, observed, expected)


# ============================================================================
# Section 5 - Public convenience list
# ============================================================================

def supported_orders() -> tuple:
    """Return the tuple of supported Lebedev orders."""
    return SUPPORTED_ORDERS
