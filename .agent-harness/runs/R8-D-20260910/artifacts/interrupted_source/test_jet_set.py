from fractions import Fraction as F
import numpy as np
import pytest
from common.r8_jet_set import JetDomain,jet_image,support,p1_operator


def domain():return JetDomain('fixture','GALACTIC',np.eye(8),('mathematical fixture only',))


def test_zero_center_remainder_is_a_set_not_center():
    im=jet_image(np.zeros(8),np.eye(8),0,(F(3,10),F(6,10)),3,domain())
    for i in range(8):
        a=np.eye(8)[i];b=support(im,a);exact=F(1,10) if i<5 else F(1,5)
        assert b.lo<=exact<=b.hi and b.lo>0
    assert support(im,np.zeros(8)).lo==support(im,np.zeros(8)).hi==0


def test_support_rho_nesting_signed_center_and_p1_map():
    old=None
    for rho in (0,F(1,4),F(1,2),1,2,4):
        im=jet_image(np.ones(8),np.diag([1,2,1,2,1,2,1,2]),rho,(0,0),3,domain())
        b=support(im,-np.eye(8)[1]);assert b.lo<=-1+2*rho<=b.hi
        if old is not None:assert b.lo>=old.lo
        old=b
    k=p1_operator(F(3));assert k.shape==(8,24)
    assert k[0,0]==-F(1,3) and k[0,5]==F(1,3) and k[0,10]==F(1,7)
    assert k[5,15]==F(1,3) and k[5,18]==F(1,3) and k[5,21]==-F(2,15)


def test_theta_and_nonlinear_boundary():
    with pytest.raises(ValueError):jet_image(np.zeros(8),np.eye(8),1,(0,0),0,domain())
    im=jet_image(np.zeros(8),np.eye(8),1,(0,0),(2,4),domain())
    assert im.status=='PARAMETERIZED_THETA_UNRESOLVED'
    assert support(im,np.ones(8)).hi==float('inf')
    with pytest.raises(ValueError):jet_image(np.zeros(8),np.eye(8),-1,(0,0),3,domain())
