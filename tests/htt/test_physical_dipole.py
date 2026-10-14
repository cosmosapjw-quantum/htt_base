import numpy as np
import pytest
from htt.infer.physical_dipole import *


def test_source_covariance_and_shared_t0():
    beta,c=measurement_proxy()
    assert np.linalg.norm(beta)*C_KM_S==pytest.approx(369.81604238249406)
    assert np.linalg.eigvalsh(c).min()>0
    np.testing.assert_allclose(physical_reference_dipole(2.8)/(2.8e6),beta,atol=1e-17)
    assert log_density(beta,extra_dipole=np.zeros(3))>log_density(beta+[1e-6,0,0],extra_dipole=np.zeros(3))
    with pytest.raises(TypeError):log_density(beta)
    with pytest.raises(ValueError,match='real'):log_density(beta.astype(complex)+1j,extra_dipole=np.zeros(3))
    with pytest.raises(ValueError,match='three-vector'):log_density(beta,extra_dipole=0.)


def test_composition_limits_and_quadrupole():
    u=np.array([.01,0,0]);v=np.array([.02,0,0])
    np.testing.assert_allclose(compose_velocities(u,v),[.03/1.0002,0,0])
    np.testing.assert_allclose(compose_velocities(u,-u),np.zeros(3),atol=1e-16)
    beta,_=measurement_proxy();q=kinematic_quadrupole(beta,T_REF_K*1e6)
    assert abs(np.trace(q))<1e-14
    assert 8*np.pi/75*np.sum(q*q)==pytest.approx(3.842673726897597)


def test_template_sign_and_missing_history():
    n=np.eye(3);old=np.array([1.,2.,3.]);new=old+.1
    m=np.zeros(3)
    with pytest.raises(ValueError,match='provenance'):change_removed_template(m,old,new,n,lambda x:x,product_history={})
    np.testing.assert_allclose(change_removed_template(m,old,new,n,lambda x:x,product_history={'dipole_removal_known':True}),[-.1,-.1,-.1])
