from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from htt_ext.lowell.alm import axisymmetric_alm, check_reality, random_real_alm, rotate_alm_zyz
from htt_ext.lowell.poles import angular_separation_deg, pole_from_alm
from htt_ext.lowell.identified import coherent_fraction_interval


def test_reality_and_axisymmetric_pole():
    rng = np.random.default_rng(1)
    for ell in range(1, 6):
        assert check_reality(random_real_alm(ell, rng), ell)
        axis = np.array([0.3, -0.4, np.sqrt(0.75)])
        axis /= np.linalg.norm(axis)
        pole, _ = pole_from_alm(axisymmetric_alm(ell, axis), ell)
        assert abs(float(pole @ axis)) > 1 - 1e-10


def test_rotation_covariance():
    rng = np.random.default_rng(2)
    for ell in (1, 2, 3, 4):
        a = random_real_alm(ell, rng)
        angles = (0.4, 0.8, -0.3)
        p, _ = pole_from_alm(a, ell)
        pp, _ = pole_from_alm(rotate_alm_zyz(a, ell, *angles), ell)
        r = Rotation.from_euler("ZYZ", angles).as_matrix()
        assert abs(float(pp @ (r @ p))) > 1 - 1e-10


def test_unoriented_angle():
    a = np.array([1.0, 0.0, 0.0])
    assert angular_separation_deg(a, -a) < 1e-10


def test_coherent_fraction_interval_monotone():
    lo1, hi1 = coherent_fraction_interval(0.6)
    lo2, hi2 = coherent_fraction_interval(0.8)
    assert lo2 > lo1
    assert hi2 >= hi1


def test_shell_transfer_conservation():
    from htt_ext.lowell.transfer import integrate_kernel_on_edges, shell_sum_relative_error

    z = np.linspace(0.0, 4.0, 4001)
    k = np.exp(-z) + 1j * 0.1 * z * np.exp(-z)
    edges = np.array([0.0, 0.2, 0.7, 1.5, 2.5, 4.0])
    shell = integrate_kernel_on_edges(
        z, k, edges, ell=2, source_name="unit_test", convention="test"
    )
    total = np.trapezoid(k, z)
    assert shell_sum_relative_error(shell, total) < 1e-6
