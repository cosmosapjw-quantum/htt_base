"""Tests for the post-REI (z <= 4) electron-history continuation."""

from __future__ import annotations

import math

import numpy as np
import pytest

from bass.recombination.reionization import ReionizationParameters, tanh_reionization_xe
from bass.recombination.rei_lowz_continuation import (
    DonorMatchedContinuation,
    FlrwBackground,
    delta_tau_on_nodes,
    opacity_per_efold,
    tau_flrw,
)

# R105 SOLVER_SOURCES_KO.md: ZERO donor normalisation and the common tanh foreground
N_H0 = 1.898198450714027e-7
F_HE = 0.08130135170951498
BG = FlrwBackground(67.4, 0.315, 0.000092)


@pytest.mark.parametrize("include_heii, expected", [(False, 0.02112795923), (True, 0.02243045425)])
def test_reproduces_the_r105_common_foreground_depth(include_heii, expected):
    p = ReionizationParameters(z_reion_H=7.67, delta_z_H=0.5, z_reion_HeII=3.5, delta_z_HeII=0.5, include_HeII=include_heii)
    tau = tau_flrw(0.0, 4.0, lambda z: tanh_reionization_xe(z, p, F_HE), N_H0, BG)
    assert abs(tau - expected) < 2e-10


def test_donor_matched_history_is_continuous_and_fully_ionized_today():
    c = DonorMatchedContinuation(x_e_match=1.08339435, f_he=F_HE)
    assert math.isclose(float(c.x_e(4.0)), 1.08339435, rel_tol=0, abs_tol=1e-14)
    assert math.isclose(float(c.x_e(0.0)), 1.0 + 2.0 * F_HE, rel_tol=0, abs_tol=1e-14)
    z = np.linspace(0.0, 4.0, 401)
    assert np.all(np.diff(c.x_e(z)) <= 1e-15)  # monotone: x_e decreases with z
    taus = [tau_flrw(0.0, 4.0, DonorMatchedContinuation(1.08339435, F_HE, z_heii=zh).x_e, N_H0, BG) for zh in (3.0, 3.5, 3.9)]
    assert taus[0] < taus[1] < taus[2] and 0.0215 < taus[0] and taus[2] < 0.0230


def test_node_depths_sum_to_the_integral_and_match_the_opacity():
    c = DonorMatchedContinuation(1.08339435, F_HE)
    N = np.linspace(-math.log(5.0), 0.0, 41)
    dt = delta_tau_on_nodes(N, c.x_e, N_H0, BG)
    assert abs(dt.sum() - tau_flrw(0.0, 4.0, c.x_e, N_H0, BG)) < 1e-12
    kap = opacity_per_efold(N, c.x_e, N_H0, BG)
    trap = 0.5 * (kap[1:] + kap[:-1]) * np.diff(N)
    assert np.max(np.abs(trap - dt) / dt) < 2e-3


def test_invalid_inputs_fail_closed():
    with pytest.raises(ValueError):
        DonorMatchedContinuation(0.9, F_HE)
    with pytest.raises(ValueError):
        DonorMatchedContinuation(1.08, 0.5)
    with pytest.raises(ValueError):
        DonorMatchedContinuation(1.08, F_HE).x_e(4.5)
    with pytest.raises(ValueError):
        delta_tau_on_nodes(np.array([-1.0, -2.0]), lambda z: 1.0, N_H0, BG)
