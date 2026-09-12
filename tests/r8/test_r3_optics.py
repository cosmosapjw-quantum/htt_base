import numpy as np
import pytest
from scipy.integrate import quad
from bass.transfer.r8_restricted_history import Initial, integrate, trace_distance, boost_matrix, ETA


def test_lorentz_frame():
    b = boost_matrix((.1, .2, -.05))
    assert np.allclose(b.T@ETA@b, ETA, atol=1e-14)


def test_flrw_distance_against_independent_radial_integral():
    h = integrate(Initial())
    result = trace_distance(h, (1., 0., 0.))
    chi = quad(lambda a: 1/(a*a*np.sqrt(.3/a**3+.1/a**4+.6)), 1., 2., epsabs=1e-12)[0]
    assert result['redshift'] == pytest.approx(1., abs=1e-8)
    assert result['angular_distance'] == pytest.approx(chi, rel=1e-8)
    assert result['reciprocity_residual'] < 1e-8
    assert result['return_position_residual'] < 1e-8


def test_actual_reverse_oblique_boosted_ray_and_screens():
    h = integrate(Initial(.1, .01))
    result = trace_distance(h, np.ones(3)/np.sqrt(3), (.001, 0., 0.))
    assert result['forward_steps'] > 2 and result['reverse_steps'] > 2
    assert max(result['invariants'].values()) < 1e-8
    assert max(result['reverse_invariants'].values()) < 1e-8
    for key in ('reciprocity_residual', 'return_position_residual', 'return_energy_residual'):
        assert result[key] < 1e-8
    assert result['jet_status'] == 'INPUT_UNAVAILABLE'


def test_flat_jacobi_solution_without_curvature():
    from bass.transfer.r8_restricted_history import _trace, screen_basis
    class Flat:
        end=1.
        def at(self,t):return None,{'scales':np.ones(3)},np.zeros(3),np.zeros(3)
    n=np.array([1.,0.,0.]);initial=np.r_[1.,np.zeros(3),-1.,n,screen_basis(n).ravel(),np.zeros(4),np.eye(2).ravel()]
    last,checks,_=_trace(Flat(),initial,0.,1e-10)
    assert np.allclose(last[16:20].reshape(2,2),np.eye(2),atol=1e-12)
    assert max(checks.values())<1e-12
