from fractions import Fraction as F
import numpy as np
import pytest
from common.r8_jet_set import JetDomain,jet_image
from htt.infer.r8_confidence_image import (CompatibleTuple,outer_region,project,LinearTarget,recession_certificate,closure_frontier)
from htt.infer.r7_confidence import PhysicalDomain,PhysicalRegion
from common.r7_contracts import AcceptanceResult


def dom():return PhysicalDomain('d',('x',),lambda x,e:True,((-10,10),),((0.,),(3.,)))
def region(rule):
    return PhysicalRegion(None,dom(),None,lambda x,e:AcceptanceResult(True,None,None,None,rule(float(x[0])), 'RESOLVED'),.975,'EXPLICIT_TEST_LAW',('test',))


def test_fixed_missing_scope_alternatives_and_unresolved_outer():
    left=region(lambda x:x<=0);right=region(lambda x:x>=2)
    tuples=[CompatibleTuple('one',dom(),{'CMB':'left','CF4':'right'})]
    joint=outer_region({'left':left,'right':right},tuples,{'CMB':F(1,40),'CF4':F(1,40)})
    assert not joint.contains([0.]) and not joint.contains([3.])
    missing=outer_region({'left':left},tuples,{'CMB':F(1,40),'CF4':F(1,40)})
    assert missing.contains([0.]) and missing.coverage_lower==.95
    union=outer_region({'left':left,'right':right},[CompatibleTuple('a',dom(),{'CMB':'left'}),CompatibleTuple('b',dom(),{'CMB':'right'})],{'CMB':F(1,40)})
    assert union.contains([0.]) and union.contains([3.])
    unknown=PhysicalRegion(None,dom(),None,lambda x,e:AcceptanceResult(False,None,None,None,False,'NUMERICALLY_UNRESOLVED'),.975,'TEST',('u',))
    outer=outer_region({'u':unknown},[CompatibleTuple('u',dom(),{'CMB':'u'})],{'CMB':F(1,40)})
    result=project(outer,LinearTarget('x',[1.]))
    assert result.bounds==(-10,10) and result.status=='CERTIFIED_OUTER_BOUND'


def test_recession_target_specific_and_compact_constraint():
    R=np.eye(8)[:4];K=np.eye(8);v=np.eye(8)[7]
    cert=recession_certificate(R,K,v,domain_A=np.zeros((0,8)),target=v)
    assert cert['status']=='UNBOUNDED_LOCAL_DOMAIN'
    assert recession_certificate(R,K,v,domain_A=np.array([v]),target=v)['status']=='NOT_A_RECESSION_WITNESS'
    assert recession_certificate(R,K,v,domain_A=np.zeros((0,8)),target=np.eye(8)[0])['status']=='TARGET_UNCHANGED'


def test_same_image_projections_and_frontier():
    factory=lambda rho:jet_image(np.zeros(8),np.eye(8),rho,(0,0),3,JetDomain('j','GALACTIC',np.eye(8),('fixture',)))
    im=factory(2);linear=project(im,LinearTarget('S1',np.eye(8)[0]))
    assert linear.bounds==(-2,2)
    norm=project(im,'s2');assert norm.bounds[0]==0 and norm.bounds[1]>=4
    assert project(im,'G_F').status=='OUTER_RANGE_UNRESOLVED'
    f=closure_frontier(factory,LinearTarget('S1',np.eye(8)[0]),1,(0,F(1,4),F(1,2),1,2,4))
    assert f['rho_lower']==F(1,2) and f['rho_upper']==1


@pytest.mark.parametrize('target,index', [('s2',0),('w2',5)])
def test_half_contraction_normalization(target,index):
    center=np.zeros(8);center[index]=2
    d=JetDomain('half-contraction','GALACTIC',np.eye(8),('orthonormal tensor coordinates',))
    im=jet_image(center,np.zeros((8,1)),0,(0,0),3,d)
    assert project(im,target).bounds==(2,2)  # S:S/2 and W:W/2, contract item 1


def test_frontier_refuses_changed_family_and_wrong_radius():
    d=JetDomain('fixed','GALACTIC',np.eye(8),('fixture',))
    target=LinearTarget('s1',np.eye(8)[0])
    with pytest.raises(ValueError,match='fixed closure family'):
        closure_frontier(lambda r:jet_image(np.ones(8)*float(r),np.eye(8),r,(0,0),3,d),target,1,(0,1))
    with pytest.raises(ValueError,match='requested radius'):
        closure_frontier(lambda r:jet_image(np.zeros(8),np.eye(8),0,(0,0),3,d),target,1,(0,1))


def test_recession_requires_feasible_ray_and_keeps_observation():
    R=[[1,0]];K=[[0,1]];v=[0,1];A=[[0,-1]]
    assert recession_certificate(R,K,v,domain_A=A,target=[1])['status']=='FEASIBILITY_UNRESOLVED'
    assert recession_certificate(R,K,v,domain_A=A,domain_b=[-1],target=[1],feasible_state=[0,0])['status']=='INFEASIBLE_BASE_STATE'
    assert recession_certificate(R,K,v,domain_A=A,domain_b=[0],target=[1],feasible_state=[0,1],observation=[1])['status']=='BASE_STATE_OBSERVATION_MISMATCH'
    good=recession_certificate(R,K,v,domain_A=A,domain_b=[0],target=[1],feasible_state=[1,1],observation=[1])
    assert good['status']=='UNBOUNDED_LOCAL_DOMAIN' and good['target_slope']==1


def test_affine_ratio_denominator_and_shared_state():
    from htt.infer.r7_mes_region import AffineRatioFunctional
    d=PhysicalDomain('positive-box',('x',),lambda x,e:True,((0,1),))
    r=PhysicalRegion(None,d,None,lambda x,e:AcceptanceResult(True,0,0,0,True,'RESOLVED'),.95,'FIXTURE',('same-state',))
    f=AffineRatioFunctional('F_fixture',F(1),F(2),(F(1),),(F(1),))
    b=project(r,f)
    assert b.bounds[0]<=.5<=b.bounds[1] and b.bounds[0]<=2/3<=b.bounds[1]
    bad=AffineRatioFunctional('F_zero_denominator',F(1),F(0),(F(1),),(F(1),))
    assert project(r,bad).status=='DENOMINATOR_UNRESOLVED'


def test_fixed_allocation_and_shared_nuisance_survive_missing_data():
    from htt.infer.r8_confidence_image import FIXED_INTEGRATED_ALLOCATION
    unknown=PhysicalRegion(None,dom(),None,lambda x,e:AcceptanceResult(False,None,None,None,False,'NUMERICALLY_UNRESOLVED'),.99,'TEST',('u',))
    outer=outer_region({'u':unknown},[CompatibleTuple('u',dom(),{'CMB':'u'})],FIXED_INTEGRATED_ALLOCATION)
    assert outer.outer_contains([0.]) and outer.coverage_lower==.95
    # Every block receives the identical shared nuisance value.
    def one(sign):
        return PhysicalRegion(None,dom(),None,lambda x,e:AcceptanceResult(True,None,None,None,sign*e>=1,'RESOLVED'),.99,'TEST',('shared',))
    joint=outer_region({'a':one(1),'b':one(-1)},[CompatibleTuple('joint',dom(),{'CMB':'a','CF4':'b'})],FIXED_INTEGRATED_ALLOCATION)
    assert not joint.contains([0.],1) and not joint.contains([0.],-1)
