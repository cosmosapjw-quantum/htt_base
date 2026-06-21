from __future__ import annotations

import numpy as np
import pytest

from obsstat.bulkflow_depth import (
    angle_between_deg,
    bootstrap_apex_dispersion,
    radial_shell_bulkflow,
)


def test_angle_between_is_directional():
    assert angle_between_deg([1, 0, 0], [1, 0, 0]) == pytest.approx(0.0)
    assert angle_between_deg([1, 0, 0], [0, 1, 0]) == pytest.approx(90.0)
    assert angle_between_deg([1, 0, 0], [-1, 0, 0]) == pytest.approx(180.0)


def test_radial_shell_bulkflow_partitions_and_averages():
    pos = np.array([[1, 0, 0], [1.2, 0, 0], [3, 0, 0], [3.1, 0, 0]], dtype=float)
    vel = np.array([[10, 0, 0], [20, 0, 0], [0, 5, 0], [0, 7, 0]], dtype=float)
    rows = radial_shell_bulkflow(pos, vel, edges=[0.5, 2.0, 4.0])
    assert len(rows) == 2
    assert rows[0]["n"] == 2
    assert rows[0]["bulk_vector"][0] == pytest.approx(15.0)
    assert rows[0]["bulk_magnitude"] == pytest.approx(15.0)
    # second shell apex points along +y
    assert rows[1]["apex_unit"][1] == pytest.approx(1.0)


def test_bootstrap_apex_dispersion_zero_for_constant_field():
    vel = np.tile(np.array([7.0, 0.0, 0.0]), (50, 1))
    out = bootstrap_apex_dispersion(vel, n_boot=64, seed=1)
    assert out["bulk_magnitude"] == pytest.approx(7.0)
    assert out["apex_angular_dispersion_deg_median"] == pytest.approx(0.0, abs=1e-9)
    assert out["bulk_magnitude_p16"] == pytest.approx(7.0)


def test_bootstrap_is_deterministic_for_seed():
    rng = np.random.default_rng(0)
    vel = rng.normal(size=(200, 3)) + np.array([5.0, 0.0, 0.0])
    a = bootstrap_apex_dispersion(vel, n_boot=128, seed=7)
    b = bootstrap_apex_dispersion(vel, n_boot=128, seed=7)
    assert a == b
    assert a["apex_angular_dispersion_deg_median"] > 0.0


def test_radial_shell_rejects_bad_edges():
    pos = np.zeros((3, 3))
    vel = np.zeros((3, 3))
    with pytest.raises(ValueError):
        radial_shell_bulkflow(pos, vel, edges=[1.0])
