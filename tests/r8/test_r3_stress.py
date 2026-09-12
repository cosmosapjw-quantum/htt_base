import numpy as np
import pytest
from bass.transfer.r8_restricted_history import Initial, stress, integrate, residuals, temperature, rhs


def test_isotropic_radiation_trace_scaling_and_parity():
    initial = Initial()
    for a in (1., 1.5, 2.):
        m = stress(a, 0., initial)
        assert m['photons'] == pytest.approx(.1/a**4, rel=1e-14)
        assert m['photon_parallel'] == pytest.approx(m['photons']/3, rel=1e-13)
    n = np.eye(3)
    assert np.array_equal(temperature(n, 2., .03), temperature(-n, 2., .03))
    assert np.allclose(temperature(n, 2., 0.), .5)


def test_small_b_coefficient_and_doppler():
    e = 1e-6; m = stress(1., e, Initial())
    assert (m['photon_parallel']/.1-1/3)/e == pytest.approx(-16/15, abs=3e-6)
    assert (m['photon_perpendicular']/.1-1/3)/e == pytest.approx(8/15, abs=3e-6)
    n = np.eye(3); beta = np.array([.01, 0, 0])
    assert np.allclose(temperature(n, 1, 0, beta), np.sqrt(1-beta@beta)/(1-n@beta))


def test_coupled_conservation_and_nonvacuous_mutants():
    h = integrate(Initial(.1, .01)); r = residuals(h)
    assert max(r.values()) < 1e-8
    for scale in (0., 2.):
        bad = integrate(Initial(.1, .01), pi_scale=scale)
        assert residuals(bad)['einstein_spatial'] > 1e-5
    bad = integrate(Initial(.1, .01), rapidity_mutant=True)
    assert residuals(bad)['killing_rapidity'] > 1e-5
    assert np.max(np.abs(h.solution.y[2]-0)) > 0


def test_domain_and_dust_rapidity_equation():
    with pytest.raises(ValueError): Initial(zeta=1)
    y = [1., .03, .01, 1., .5]
    assert rhs(0, y, Initial(.1))[4] == pytest.approx(-1.02*np.tanh(.5))
