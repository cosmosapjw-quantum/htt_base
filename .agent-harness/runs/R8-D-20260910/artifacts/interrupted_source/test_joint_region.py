from fractions import Fraction as F
import numpy as np
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
