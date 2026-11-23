import math

import numpy as np
import pytest
from scipy.integrate import quad
from scipy.special import ndtr, roots_hermitenorm
from scipy.stats import norm

from scripts.r99 import cf4_source_law as cf


class CoastingDistance:
    # Constant H(z), chi=c*z/H0 gives an independent exact distance integral.
    H0 = 70.

    @staticmethod
    def distance_integral(z, order):
        return z


def test_finite_redshift_types_and_sign():
    sci = CoastingDistance()
    z = np.array([.01,.04,.1])
    r = np.arctanh(250/cf.C)
    zb = (1+z)*math.exp(-r)-1
    expected = np.log(z/zb)
    for obs, exponent in cf.TYPES.items():
        actual = cf.finite_shift(sci,z,r,obs)
        np.testing.assert_allclose(actual, expected+exponent*r, atol=4e-14)
        zero = cf.finite_shift(sci,z,0,obs)
        np.testing.assert_allclose(zero,0,atol=2e-15)
        assert np.all(actual > 0)
    with pytest.raises(ValueError):
        cf.finite_shift(sci,z,np.log1p(z),"bolometric")
    with pytest.raises(ValueError):
        cf.finite_shift(sci,[np.nan],0,"bolometric")


def test_joint_selection_against_integrated_native_marks():
    y = np.array([.2,-.5])
    means = np.array([[-1, .2], [.8,1.]])
    sd = np.array([.5,.7])
    cut = np.array([.1,0.])
    softness = .35
    prior = np.array([.4,.6])
    result = cf.joint_selected_logpdf(y, means, sd, cut, softness, prior)
    det, num = [], []
    for vals in means:
        def integrand(yval,i):
            return norm.pdf(yval, vals[i], sd[i])*ndtr((cut[i]-yval)/softness)
        det.append(np.prod([quad(lambda t:integrand(t,i),-np.inf,np.inf)[0] for i in range(2)]))
        num.append(np.prod([integrand(y[i],i) for i in range(2)]))
    np.testing.assert_allclose(result["log_density"], np.log(prior@num)-np.log(prior@det),atol=2e-12)
    np.testing.assert_allclose(result["included_field_weights"], prior*det/(prior@det))
    wrong = np.log(prior@(np.array(num)/det))
    assert abs(wrong-result["log_density"]) > .1
    with pytest.raises(ValueError):
        cf.joint_selected_logpdf(y,means,sd,cut,softness,[.5,.8])
    with pytest.raises(ValueError):
        cf.inclusion_logs(y,means,sd,cut,0.)
    with pytest.raises(ValueError):
        cf.inclusion_logs(y,means,[0,.5],cut,1.)


@pytest.mark.parametrize("p", [0.,.18,.65,1.])
def test_gamma_sharp_witnesses(p):
    G = 3.1
    lo,hi = cf.gamma_bounds(p,G)
    w = np.array([p,1-p])
    assert lo == pytest.approx(p/(w@[1,G]))
    assert hi == pytest.approx(G*p/(w@[G,1]))
    assert cf.gamma_bounds(p,1.) == pytest.approx([p,p])


@pytest.mark.parametrize("p,g", [(-.1,2),(.5,.9),(1.1,1),(.5,np.inf)])
def test_gamma_invalid(p,g):
    with pytest.raises(ValueError):
        cf.gamma_bounds(p,g)


def test_nonlinear_covariance_orthogonality_and_bound():
    sci = CoastingDistance()
    z = np.array([.01,.03])
    sigma = np.array([220.,300.])
    moments = cf.hermite_moments(sci,z,sigma,32)[2] # bolometric
    mean,a1,_,e = moments.T
    x,w = roots_hermitenorm(22)
    w /= math.sqrt(2*math.pi)
    rho = -.55
    X = x[:,None] + np.zeros_like(x)[None,:]
    Y = rho*X + math.sqrt(1-rho*rho)*x[None,:]
    # Truncation probability below 5e-42 at z=.01 under this test prior;
    # direct finite velocities here are far inside both boundaries.
    f1 = cf.finite_shift(sci,z[0],sigma[0]*X/cf.C,"bolometric")
    f2 = cf.finite_shift(sci,z[1],sigma[1]*Y/cf.C,"bolometric")
    ww = w[:,None]*w[None,:]
    cov = ((f1-mean[0])*(f2-mean[1])*ww).sum()
    first_c = rho*a1[0]*a1[1]
    assert abs(cov-first_c) <= math.sqrt(e[0]*e[1])+1e-13
    assert abs(cov-first_c)>1e-8
    h = np.array([1.,-.8])
    extra = h@np.array([[e[0],cov-first_c],[cov-first_c,e[1]]])@h
    assert 0 <= extra <= (abs(h)@np.sqrt(e))**2 + 1e-13
    assert cf.hermite_moments(sci,np.array([.001]),np.array([400.]),64).shape==(3,1,4)
    with pytest.raises(ValueError):
        cf.hermite_moments(sci,z,np.array([-1.,2.]),24)


def test_hermite_zero_dispersion_mixed_and_deterministic():
    z = np.array([.01, .04, .05, .09])
    sigma = np.array([0., 150., 0., 250.])
    pos = sigma > 0
    with np.errstate(divide="raise", invalid="raise"):
        mixed = cf.hermite_moments(CoastingDistance(), z, sigma, 16)
        fixed = cf.hermite_moments(CoastingDistance(), z, np.zeros_like(sigma), 16)
        fluctuating = cf.hermite_moments(CoastingDistance(), z[pos], sigma[pos], 16)
    np.testing.assert_array_equal(fixed, np.zeros((3, len(z), 4)))
    np.testing.assert_array_equal(mixed[:, ~pos], fixed[:, ~pos])
    np.testing.assert_array_equal(mixed[:, pos], fluctuating)
    for invalid in (-1., np.nan, np.inf):
        with pytest.raises(ValueError):
            cf.hermite_moments(CoastingDistance(), z, [0., 100., invalid, 150.], 16)
