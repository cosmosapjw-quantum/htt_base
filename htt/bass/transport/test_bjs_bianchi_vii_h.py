"""Tests for the published BJS Bianchi VII_h template (independent comparator of the line-of-sight engine)."""

from __future__ import annotations

import math

import numpy as np
import pytest

from bass.transport.bjs_bianchi_vii_h import (
    BJSParameters,
    bjs_coefficients,
    bjs_lie_geometry_today,
    bjs_temperature,
    bjs_vorticity_over_hubble,
)

THETA = np.linspace(0.05, math.pi - 0.05, 41)
PHI = np.linspace(0.0, 2.0 * math.pi, 64, endpoint=False)


def test_quadrature_is_converged():
    a1, b1 = bjs_coefficients(THETA, BJSParameters(0.5, 0.62, n_quadrature=1024))
    a2, b2 = bjs_coefficients(THETA, BJSParameters(0.5, 0.62, n_quadrature=4096))
    scale = max(np.max(np.abs(a2)), np.max(np.abs(b2)))
    assert max(np.max(np.abs(a1 - a2)), np.max(np.abs(b1 - b2))) < 1e-9 * scale


def test_only_azimuthal_modes_one_are_present():
    th, ph = np.meshgrid(THETA, PHI, indexing="ij")
    m = bjs_temperature(th, ph, BJSParameters(0.3, 0.62))
    f = np.fft.rfft(m, axis=1)
    power = np.sum(np.abs(f) ** 2, axis=0)
    assert np.sum(power[[0] + list(range(2, power.size))]) < 1e-24 * power[1]


def test_handedness_is_a_mirror_reflection_and_amplitude_is_linear():
    th, ph = np.meshgrid(THETA, PHI, indexing="ij")
    right = bjs_temperature(th, ph, BJSParameters(0.5, 1.0, handedness=1, sigma_over_h=2e-10))
    left_mirror = bjs_temperature(th, math.pi - ph, BJSParameters(0.5, 1.0, handedness=-1, sigma_over_h=2e-10))
    assert np.max(np.abs(right - left_mirror)) < 1e-12 * np.max(np.abs(right))
    unit = bjs_temperature(th, ph, BJSParameters(0.5, 1.0, handedness=1, sigma_over_h=1.0))
    assert np.allclose(right, 2e-10 * unit, rtol=1e-12, atol=0.0)


def test_published_variants_differ_and_are_both_available():
    th, ph = np.meshgrid(THETA, PHI, indexing="ij")
    a = bjs_temperature(th, ph, BJSParameters(0.5, 0.62, variant="mcewen2006"))
    b = bjs_temperature(th, ph, BJSParameters(0.5, 0.62, variant="kogut1997"))
    assert np.max(np.abs(a - b)) > 1e-3 * np.max(np.abs(a))


def test_background_identities_and_lie_dictionary():
    p = BJSParameters(0.4, 0.8)
    rh = math.sqrt(p.h)
    assert math.isclose(math.sinh(0.5 * rh * p.tau_0) ** 2, (1 - p.omega0) / p.omega0, rel_tol=1e-13)
    assert math.isclose(math.sinh(0.5 * rh * p.tau_0) ** 2 / math.sinh(0.5 * rh * p.tau_E) ** 2, 1 + p.z_emission, rel_tol=1e-12)
    a, n = bjs_lie_geometry_today(p)
    assert np.allclose(n @ a, 0.0) and math.isclose((a[2] / n[0, 0]) ** 2, p.h, rel_tol=1e-13)
    expect = math.sqrt(2) * math.sqrt(1 + p.h) * math.sqrt(1 + 9 * p.h) / (6 * p.x ** 2 * p.omega0)
    assert math.isclose(bjs_vorticity_over_hubble(p), expect, rel_tol=1e-15)


@pytest.mark.parametrize("kwargs", [dict(omega0=1.0, x=1.0), dict(omega0=0.5, x=0.0), dict(omega0=0.5, x=1.0, handedness=0),
                                    dict(omega0=0.5, x=1.0, variant="other"), dict(omega0=0.5, x=1.0, n_quadrature=8)])
def test_invalid_parameters_fail_closed(kwargs):
    with pytest.raises(ValueError):
        BJSParameters(**kwargs)


def test_axis_is_rejected():
    with pytest.raises(ValueError):
        bjs_coefficients(np.array([0.0, 1.0]), BJSParameters(0.5, 1.0))
