"""Finite consumer controls, not four-axis or observational qualification."""
import numpy as np
import pytest
from optical_fixture import sphere,ray_generator,unpack,inverse,moments,flat_endpoint,source_temperature,expected_qo,kz,jacobi

@pytest.mark.parametrize('grid',[8,16])
def test_basis_inverse(grid):
    n,w=sphere(grid)
    for x in np.eye(12):
        h,v=ray_generator(n,*unpack(x))
        np.testing.assert_allclose(inverse(n,w,h,v),x,atol=1e-10,rtol=0)

@pytest.mark.parametrize('distance',[.2,.5])
def test_endpoint_kelvin_and_wrong_parity(distance):
    n,w=sphere();x,d,_=flat_endpoint(n,distance,np.eye(3))
    t=source_temperature(x,d)/1.25
    mean,q,o=moments(n,w,t);eq,eo=expected_qo(np.eye(3))
    np.testing.assert_allclose(q,eq,atol=1e-10,rtol=0)
    np.testing.assert_allclose(o,eo,atol=1e-10,rtol=0)
    np.testing.assert_allclose(mean,2.16,atol=1e-10,rtol=0)
    wrong=moments(-n,w,t)[2]
    with pytest.raises(AssertionError):np.testing.assert_allclose(wrong,eo,atol=1e-10,rtol=0)

def test_affine_and_inverse_domains():
    d,dp=jacobi(.3)
    np.testing.assert_allclose(kz(d,dp,1.6),kz(d,dp/3,1.6/3),atol=1e-10,rtol=0)
    for dd,zp in [(np.zeros((2,2)),1),(d,0),(jacobi(np.pi)[0],1)]:
        with pytest.raises(ValueError):kz(dd,dp,zp)
