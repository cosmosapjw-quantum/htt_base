import numpy as np
import pytest
from numpy.testing import assert_allclose

from bass.recombination.opacity_history import OpacityHistory
from bass.recombination.rei_observer_rays import ReiObserverRays


class ConstantSlab:
    def __init__(self, slope, offset=0):
        self.N = np.linspace(-3.,-1.,101)
        self.z = np.expm1(-self.N)
        self.b = slope*self.N + offset
        self.opacity = OpacityHistory(self.N, np.full_like(self.N,2.3))
        self.cells = self.opacity.cells
        self.rate = self.opacity.rate


def test_principal_axes_fixed_observer_and_foreground():
    m = ConstantSlab(.12)
    zo = np.expm1(1.37)
    rays = ReiObserverRays(m, zo)
    z = np.array([0,.2,.7])
    for mu,K in [(0,1-.12),(1,1+2*.12)]:
        res = rays.evaluate(z,mu)
        assert_allclose(res.emission_N,-1.37-np.log1p(z)/K,rtol=2e-15)
        assert_allclose(res.optical_depth,2.3*np.log1p(z)/K,atol=1e-15)
        assert_allclose(res.depth_per_redshift,2.3/(1+z)/K,rtol=1e-14)
    with pytest.raises(ValueError,match="outside"):
        rays.evaluate(12,0)
    with pytest.raises(ValueError,match="finite mean-redshift"):
        ReiObserverRays(m,0)


def test_mixed_ray_jacobian_angular_parity_and_gauge():
    m = ConstantSlab(-.085)
    ray = ReiObserverRays(m,m.z[-1])
    other = ReiObserverRays(ConstantSlab(-.085,15.6),m.z[-1])
    z = np.array([.2,.8,.9])[:,None]
    mu = np.array([-.91,.15,.93])
    v = ray.evaluate(z,mu)
    assert_allclose(v.optical_depth,other.evaluate(z,-mu).optical_depth,atol=8e-14)
    dz = 1e-5
    fd = (ray.evaluate(z+dz,mu).optical_depth-ray.evaluate(z-dz,mu).optical_depth)/(2*dz)
    assert_allclose(v.depth_per_redshift,fd,rtol=2e-9)
    assert_allclose(v.visibility_per_redshift,v.depth_per_redshift*np.exp(-v.optical_depth),rtol=2e-14)


def test_endpoints_isotropic_and_nonmonotonic_histories():
    m = ConstantSlab(0.0)
    r = ReiObserverRays(m,m.z[-1])
    mu = np.linspace(-1,1,9)
    end = np.expm1(r.log_frequency_ratio(m.N[0],mu))
    assert_allclose(r.evaluate(end,mu).optical_depth,4.6,rtol=2e-15)
    assert_allclose(r.evaluate(0,mu).optical_depth,0,atol=0)
    assert_allclose(r.evaluate(.3,mu).emission_N,-1-np.log1p(.3),rtol=2e-15)
    with pytest.raises(ValueError):
        r.evaluate(np.nextafter(end,np.inf),mu)
    with pytest.raises(ValueError):
        r.evaluate(.1,1.001)
    broken=ConstantSlab(-.51)
    with pytest.raises(ValueError, match="monotonic"):
        ReiObserverRays(broken,broken.z[-1])
