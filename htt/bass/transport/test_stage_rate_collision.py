"""R106: Thomson rate and electron velocity share SDIRK stage times in opaque photon cells.

Analytic special solution (zero geometry, tiny beta): the temperature dipole
a = -T_10/sqrt(4 pi/3) obeys a' = R(u)(beta(u) - a), a(0)=0, with R = R0 exp(-k u)
and beta = vf u. Then
a(u) = vf [u - exp(-tau(u)) exp(R0/k)/k (E1(w(u)) - E1(R0/k))],
tau(u) = (R0/k)(1 - e^{-k u}), w(u) = (R0/k) e^{-k u}.
"""
import math

import numpy as np
from scipy.special import exp1

from bass.recombination.opacity_history import OpacityHistory
from bass.transport.coupled_einstein_boltzmann import _advance_moving_photon_cell, _optical_substeps
from bass.transport.general_lie_stokes import GeneralLieStokesOperator, LieGeometry

ZERO = LieGeometry(np.zeros((3, 3)), np.zeros(3), np.zeros((3, 3)))


def _ramp(op, r0, k, cap, staged, vf=1e-8):
    nodes = np.linspace(0.0, 1.0, 4001)
    opacity = OpacityHistory(nodes, r0 * np.exp(-k * nodes))
    edges, depths = _optical_substeps(opacity, 0.0, 1.0, 2, cap)
    state = _advance_moving_photon_cell(
        op, np.zeros(op.dim, complex), 1.0, ZERO, np.zeros(op.dim, complex), depths,
        lambda u: np.array([0.0, 0.0, vf * u]), sub_edges=edges,
        opacity_rate_at=(lambda u: float(opacity.rate(min(u, 1.0)))) if staged else None)
    measured = -state[op.idx["T"][1, 0]].real / math.sqrt(4 * math.pi / 3)
    w1, w0 = (r0 / k) * math.exp(-k), r0 / k
    exact = vf * (1 - math.exp(-(w0 - w1)) * math.exp(w0) / k * (exp1(w1) - exp1(w0)))
    return (measured - exact) / (exact - vf)


def test_stage_rate_recovers_tight_coupling_slip_at_second_order():
    op = GeneralLieStokesOperator(2, n_gl_theta=8)
    r0, k = 0.3 * 98.4 * math.exp(1.65), 1.65
    errors = [_ramp(op, r0, k, cap, True) for cap in (1.0, 0.5, 0.25)]
    assert abs(errors[0]) <= 1e-4
    orders = [math.log2(abs(a / b)) for a, b in zip(errors, errors[1:])]
    assert all(1.8 <= p <= 2.2 for p in orders), orders
    # The R105 substep-average rate leaves a slip error >20x larger at the same cap.
    assert abs(_ramp(op, r0, k, 1.0, False)) >= 20 * abs(errors[0])


def test_constant_rate_unchanged_by_stage_sampling():
    op = GeneralLieStokesOperator(2, n_gl_theta=8)
    opacity = OpacityHistory([0.0, 1.0], [6.0, 6.0])
    edges, depths = _optical_substeps(opacity, 0.0, 1.0, 2, 1.0)
    beta = lambda u: np.array([0.0, 0.0, 1e-6 * (-math.expm1(-5 * u))])
    runs = [_advance_moving_photon_cell(op, np.zeros(op.dim, complex), 1.0, ZERO, np.zeros(op.dim, complex),
                                        depths, beta, sub_edges=edges,
                                        opacity_rate_at=rate) for rate in (None, lambda u: float(opacity.rate(u)))]
    assert np.max(np.abs(runs[0] - runs[1])) <= 1e-15 * np.max(np.abs(runs[0]))


def test_stage_opacity_rate_units_clamp_and_depth():
    from bass.transport.coupled_einstein_boltzmann import _stage_opacity_rate
    n0, n_stop = -7.3, -7.15
    nodes = np.linspace(n0, n_stop, 301)
    opacity = OpacityHistory(nodes, 60.0 * np.exp(-12.0 * (nodes - n0)))
    rate = _stage_opacity_rate(opacity, n0, n_stop)
    dn = n_stop - n0
    assert rate(0.0) == dn * float(opacity.rate(n0))
    # The clamp absorbs any overshoot past the last PCHIP node without raising.
    assert rate(np.nextafter(1.0, 2.0)) == rate(1.0)
    u = np.linspace(0.0, 1.0, 20001)
    depth = np.trapezoid([rate(x) for x in u], u)
    exact = float(opacity.cells(np.array([n0, n_stop])).delta_tau[0])
    assert abs(depth / exact - 1) < 1e-7


def test_log_rate_bisection_bounds_rate_change():
    nodes = np.linspace(0.0, 1.0, 2001)
    opacity = OpacityHistory(nodes, 40.0 * np.exp(-6.0 * nodes))
    edges_u, depths = _optical_substeps(opacity, 0.0, 1.0, 2, 1.0, 0.25)
    r = np.asarray(opacity.rate(edges_u))
    assert np.max(np.abs(np.diff(np.log(r)))) <= 0.25 * (1 + 1e-12)
    assert abs(np.sum(depths) - float(opacity.cells(np.array([0.0, 1.0])).delta_tau[0])) < 1e-12


def test_pure_damping_applies_exact_depth():
    op = GeneralLieStokesOperator(4, n_gl_theta=16)
    i3 = op.idx["T"][3, 0]
    nodes = np.linspace(0.0, 1.0, 2001)
    opacity = OpacityHistory(nodes, 1.5 * np.exp(-5.0 * nodes))
    y0 = np.zeros(op.dim, complex)
    y0[i3] = 1.0
    errors = {}
    for lr in (None, 0.25):
        edges, depths = _optical_substeps(opacity, 0.0, 1.0, 2, 1.0, lr)
        y = _advance_moving_photon_cell(op, y0, 1.0, ZERO, np.zeros(op.dim, complex), depths,
                                        lambda u: np.zeros(3), sub_edges=edges,
                                        opacity_rate_at=lambda u: float(opacity.rate(min(u, 1.0))))
        errors[lr] = abs(y[i3].real / math.exp(-float(np.sum(depths))) - 1)
    assert errors[0.25] < 2e-4 and errors[0.25] < errors[None]


def test_stage_rate_requires_depth_cap():
    import pytest
    from bass.transport.coupled_einstein_boltzmann import CoupledSolverConfig, solve_coupled_einstein_boltzmann
    with pytest.raises(ValueError, match="finite max_substep_depth"):
        solve_coupled_einstein_boltzmann("VII_h", CoupledSolverConfig(n_cells=2, max_substep_depth=None))


def test_adaptive_picard_continues_until_local_stress_converges():
    import pytest
    from bass.transport.coupled_einstein_boltzmann import CoupledSolverConfig, solve_coupled_einstein_boltzmann
    with pytest.raises(ValueError, match="picard_rtol"):
        solve_coupled_einstein_boltzmann("VII_h", CoupledSolverConfig(n_cells=2, picard_rtol=-1.0))
    base = dict(n_cells=8, ell_max=2, n_picard=2, epsilon=2e-4, max_substep_depth=1.0)
    fixed = solve_coupled_einstein_boltzmann("VI_-1/9", CoupledSolverConfig(**base, picard_rtol=None))
    adaptive = solve_coupled_einstein_boltzmann("VI_-1/9", CoupledSolverConfig(**base, picard_rtol=1e-6, max_picard=12))
    assert fixed.picard_iterations_used == 2
    assert adaptive.picard_iterations_used > 2 and adaptive.picard_pi_local_rel_change <= 1e-6
    assert fixed.picard_pi_local_rel_change > 1e-6
