from fractions import Fraction as F
from dataclasses import replace
import numpy as np
import pytest
from common.r7_contracts import RadiationJet,AcceptanceResult
from common.r7_radiation_jet import kinematics_from_radiation_jet
from htt.infer.r7_confidence import PhysicalDomain,PhysicalRegion,project_joint_region
from htt.infer.r7_mes_region import AffineRatioFunctional,affine_box_gf_bound

def jet():
    stf=np.diag([1.,-1.,0.]);anti=np.array([[0.,1.,0.],[-1.,0.,0.],[0.,0.,0.]])
    return RadiationJet(3.,2.,"OUTWARD","F","J",q=stf,q_dot=4*stf,tbar_dot=2.,grad_d=2*stf,
        div_o=7*stf,curl_d=anti,curl_d_dot=2*anti,curl_div_q=5*anti)

def test_normalized_derivative_and_outward_propagation_equivalence():
    a=jet();s=kinematics_from_radiation_jet(a)
    p=replace(a,convention="PROPAGATION",grad_d=-a.grad_d,div_o=-a.div_o,curl_d=-a.curl_d,curl_d_dot=-a.curl_d_dot)
    t=kinematics_from_radiation_jet(p)
    np.testing.assert_allclose(s.shear,t.shear)
    np.testing.assert_allclose(s.vorticity,t.vorticity)
    np.testing.assert_allclose(s.shear,np.diag([3.5,-3.5,0.])/3)
    np.testing.assert_allclose(s.vorticity,a.curl_d/3)
    assert kinematics_from_radiation_jet(replace(a,q_dot=None)).status=="MISSING_RADIATION_JET"
    with pytest.raises(ValueError,match="positive"): kinematics_from_radiation_jet(replace(a,theta=0))

def test_same_state_signed_ratio_outer_and_inner_are_distinct():
    domain=PhysicalDomain("box",("x",),lambda t,e:True,((-1.,1.),),([0.],))
    region=PhysicalRegion(None,domain,None,lambda t,e:AcceptanceResult(True,0,1,1,abs(t[0])<.2,"RESOLVED"),.95,"fixture",("s",))
    f=AffineRatioFunctional("signed_G",F(-1),F(2),(F(1),),(F(1),))
    r=project_joint_region(region,f,affine_box_gf_bound)
    assert r.outer_bounds[0]<=-2. and r.outer_bounds[1]>=0.
    assert r.inner_values==(-.5,) and r.status=="CERTIFIED_OUTER_BOUND"
    unresolved=project_joint_region(region,f,None)
    assert unresolved.outer_bounds is None and unresolved.inner_values==(-.5,)
    bad=replace(f,denominator_constant=F(0))
    r=project_joint_region(region,bad,affine_box_gf_bound)
    assert r.status=="DENOMINATOR_UNRESOLVED" and r.undefined_witnesses
