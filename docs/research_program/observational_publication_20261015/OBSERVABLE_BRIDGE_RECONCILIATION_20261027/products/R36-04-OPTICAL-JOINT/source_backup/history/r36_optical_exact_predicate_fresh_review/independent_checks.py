import json, math, sys, traceback
from fractions import Fraction as F
from itertools import product
from pathlib import Path
import numpy as np

OUT=Path('/mnt/extdrive/workdir/htt_open_data/r36_optical_exact_predicate_fresh_review')
CAND=OUT/'small_fixture/docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-04-OPTICAL-JOINT/repair_03'
sys.path.insert(0,str(CAND))
import optical_joint as m
from consume import directions
records=[]
def f(x): return F.from_float(float(x))
def norm2(v): return sum((f(x)**2 for x in v),F(0))
def feasible(d,c,e,R):
    return sum(((f(x)-f(y))**2 for x,y in zip(d,c)),F(0))<=f(e)**2 and (R is None or norm2(d)<=f(R)**2)
def k_for(s):
    a=np.max(np.abs(s));return (m.KAPPA*a)*m.lift_matrix(s/a) if a else np.zeros((7,3))
def run(name,fn):
    try: detail=fn();r=dict(name=name,status='PASS',detail=detail)
    except Exception as exc: r=dict(name=name,status='FAIL',exception=type(exc).__name__,message=str(exc),traceback=traceback.format_exc())
    records.append(r);print(json.dumps(r),flush=True)

def exact_empty():
    c=np.array([.125,1e-60,0]);s=np.diag([.001,-.001,0]);
    delta=norm2(c)-f(.125)**2
    out=m.joint_test(k_for(s)@c,s,c,1e-7,e_d=0,d_max=.125)
    assert delta>0 and out['physical_set_empty'] and not out['compatible']
    return dict(exact_squared_excess=str(delta),actual=out)
run('NCF1_exact_binary_empty',exact_empty)

def directed():
    allout=[]
    for n,budget in ((2,2.),(3,2.),(3,.7)):
        out=m.joint_test(np.r_[np.ones(n),np.zeros(7-n)],np.zeros((3,3)),np.zeros(3),budget)
        assert f(out['certified_lower_bound'])**2<=n<=f(out['certified_upper_bound'])**2
        assert f(out['score'])>=f(out['certified_upper_bound'])/f(budget)
        allout.append(out)
    eq=m.joint_test(np.r_[.001,np.zeros(6)],np.zeros((3,3)),np.zeros(3),.001)
    assert eq['compatible'] and eq['score']==1
    return dict(cases=allout,equality=eq)
run('NCF2_fraction_directed_endpoints_and_score',directed)

def tangent():
    s=np.diag([.001,-.001,0]);c=np.array([.25,0,0])
    out=m.joint_test(np.zeros(7),s,c,.001,e_d=.125,d_max=.125)
    assert out['compatible'] and out['profiled_d']==[.125,0.,0.] and feasible(out['profiled_d'],c,.125,.125)
    return out
run('NCF3_exact_representable_tangent',tangent)

def near_tangent(ss):
    c=np.array([math.nextafter(.25,0.),0.,0.]);d=np.array([.125,0.,0.]);s=np.diag([ss,-ss,0.]);budget=.001
    k=k_for(s)
    residual=[sum((f(k[i,j])*f(d[j]) for j in range(3)),F(0)) for i in range(7)]
    r2=sum((r*r for r in residual),F(0))
    assert feasible(d,c,.125,.125) and r2<f(budget)**2
    oracle=dict(center=c.tolist(),e_d=.125,d_max=.125,S=s.tolist(),O=[0.]*7,budget=budget,
        witness=d.tolist(),direct_squared_slack=str(f(.125)**2-sum(((f(x)-f(y))**2 for x,y in zip(d,c)),F(0))),
        physical_squared_slack=str(f(.125)**2-norm2(d)),residual_squared=str(r2),budget_squared=str(f(budget)**2),
        exact_oracle='nonempty closed-ball intersection; representable witness; residual strictly within unchanged budget')
    try: oracle['actual']=m.joint_test(np.zeros(7),s,c,budget,e_d=.125,d_max=.125)
    except m.NumericalProfileFailure as exc: oracle['actual']=dict(code=exc.code,detail=str(exc))
    name='NEAR_TANGENT_ZERO' if ss==0 else 'NEAR_TANGENT_NONZERO'
    (OUT/(name+'_COUNTEREXAMPLE.json')).write_text(json.dumps(oracle,indent=2)+'\n')
    assert oracle['actual'].get('compatible') is True, json.dumps(oracle)
    return oracle
run('near_tangent_representable_zero_response',lambda:near_tangent(0.))
run('near_tangent_representable_nonzero_response',lambda:near_tangent(.001))

def interval(c,e,R,target,factor,unit):
    s=np.diag([.001,-.001,0.])*unit;k=k_for(s);o=k[:,0]*target
    lo=max(f(c)-f(e),-f(R));hi=min(f(c)+f(e),f(R))
    kk=[f(x) for x in k[:,0]];oo=[f(x) for x in o]
    opt=max(lo,min(hi,sum((a*b for a,b in zip(kk,oo)),F(0))/sum((a*a for a in kk),F(0))))
    rsq=sum(((b-a*opt)**2 for a,b in zip(kk,oo)),F(0))
    # float conversion of rsq can underflow, so use its dimensionless unscaled equivalent.
    budget=factor*math.sqrt(float(rsq/f(unit)**2))*unit
    out=m.joint_test(o,s,np.array([c,0,0]),budget,e_d=e,d_max=R)
    assert feasible(out['profiled_d'],[c,0,0],e,R)
    assert f(out['certified_lower_bound'])**2<=rsq<=f(out['certified_upper_bound'])**2
    assert out['compatible']==(factor>1)
    actual_res=[f(o[i])-sum((f(k[i,j])*f(out['profiled_d'][j]) for j in range(3)),F(0)) for i in range(7)]
    assert sum((x*x for x in actual_res),F(0))<=f(out['certified_upper_bound'])**2
    return dict(parameters=[c,e,R,target,factor,unit],actual=out,oracle_min_squared=str(rsq))
for args in product(((.01,1e-6,.1,.010002),(0.,.1,.0001,.0001000000009),(-.003,.001,.1,-.0015)),(.7,1.3),(1.,1e-30,1e-150)):
    p,fac,unit=args
    run('exact_interval_'+str((*p,fac,unit)),lambda p=p,fac=fac,unit=unit:interval(*p,fac,unit))

def special_domains():
    outputs=[]
    for s in (np.zeros((3,3)),np.diag([1e-200,-1e-200,0])):
        out=m.joint_test(np.r_[1e-200,np.zeros(6)],s,np.zeros(3),0)
        assert not out['compatible'];outputs.append(out)
    assert outputs[1]['branch']=='INVERTIBLE_S'
    for o,s,kw in [(np.r_[1e200,np.zeros(6)],np.zeros((3,3)),{}),(np.zeros(7),np.diag([1e200,-1e200,0]),dict(kappa=1e200))]:
        try: m.joint_test(o,s,np.zeros(3),0,**kw)
        except m.NumericalProfileFailure as exc: assert exc.code=='NUMERIC_RANGE';outputs.append(dict(code=exc.code,detail=str(exc)))
        else: raise AssertionError('missing typed range')
    for c,e,R,expected in (([0,0,0],0,0,True),([.25,0,0],.125,0,False),([.125,0,0],.125,0,True)):
        out=m.joint_test(np.zeros(7),np.zeros((3,3)),np.array(c),0,e_d=e,d_max=R)
        assert out['compatible']==expected;outputs.append(out)
    return outputs
run('tiny_nonzero_range_and_zero_singleton_empty_controls',special_domains)

def tensors_and_sources():
    # Direct index expression independent of stf3/lift implementation.
    s=np.array([[.02,.003,-.004],[.003,-.03,.006],[-.004,.006,.01]]);d=np.array([.012,-.009,.006])
    sd=s@d;full=np.zeros((3,3,3))
    for i,j,k in product(range(3),repeat=3):
        full[i,j,k]=(d[i]*s[j,k]+d[j]*s[i,k]+d[k]*s[i,j])/3-2*((i==j)*sd[k]+(i==k)*sd[j]+(j==k)*sd[i])/15
    reconstructed=np.tensordot(m.lift_matrix(s)@d,m.B3,axes=1)
    np.testing.assert_allclose(reconstructed,full,rtol=1e-13,atol=1e-18)
    np.testing.assert_allclose(np.einsum('iik->k',full),0,atol=2e-19)
    np.testing.assert_allclose(m.lift_matrix(s).T@m.lift_matrix(s),np.sum(s*s)*np.eye(3)/3+2*(s@s)/5,rtol=3e-14,atol=1e-18)
    n=directions(96);w=1+.4*n[:,2];u=np.linspace(-1,1,96);C=1e-8*(np.eye(96)+.2*np.outer(u,u))
    X=np.column_stack([np.ones(96),n,np.einsum('aij,ni,nj->na',m.B2,n,n),np.einsum('aijk,ni,nj,nk->na',m.B3,n,n,n)])
    fit=np.linalg.solve(X.T@(w[:,None]*X),X.T*w)
    K=np.vstack([-fit[1:4]/m.KAPPA,fit[9:16]])
    actual=m.raw_to_target(n,s,d,w,C)
    np.testing.assert_allclose(actual['estimator'],K,rtol=1e-11,atol=1e-14)
    expectedC=K@C@K.T;A=np.column_stack([-m.KAPPA*m.lift_matrix(s),np.eye(7)])
    np.testing.assert_allclose(actual['summary_covariance'],expectedC,rtol=1e-10,atol=1e-21)
    np.testing.assert_allclose(m.residual_covariance(actual['summary_covariance'],s),A@expectedC@A.T,rtol=1e-10,atol=1e-21)
    cross=expectedC[:3,3:];assert np.linalg.norm(cross)>0
    diagonal=expectedC.copy();diagonal[:3,3:]=0;diagonal[3:,:3]=0
    assert np.linalg.norm(A@expectedC@A.T-A@diagonal@A.T)>1e-14
    for j in range(8):
        dd=np.zeros(3);ds=np.zeros((3,3));h=1e-6
        if j<3:dd[j]=h
        else:ds=h*m.B2[j-3]
        fd=(m.raw_to_target(n,s+ds,d+dd,w)['summary']-m.raw_to_target(n,s-ds,d-dd,w)['summary'])/(2*h)
        np.testing.assert_allclose(fd,actual['jacobian_d_S'][:,j],rtol=5e-7,atol=2e-9)
    return dict(full_tensor_max_error=float(np.max(np.abs(full-reconstructed))),cross_covariance_norm=float(np.linalg.norm(cross)),cross_term_effect=float(np.linalg.norm(A@expectedC@A.T-A@diagonal@A.T)),derivative_columns_checked=8)
run('full_tensor_independent_indices_full_correlated_covariance_and_all_jacobian_columns',tensors_and_sources)

def rotation():
    s=np.diag([.001,-.001,0]);d=np.array([.01,0,0]);O=k_for(s)@np.array([.0100005,0,0]);B=5.606717652542515e-10
    axis=np.array([1.,2.,-3.]);axis/=np.linalg.norm(axis);t=.61;cross=np.array([[0,-axis[2],axis[1]],[axis[2],0,-axis[0]],[-axis[1],axis[0],0]])
    R=np.eye(3)*np.cos(t)+(1-np.cos(t))*np.outer(axis,axis)+np.sin(t)*cross
    T=np.tensordot(O,m.B3,axes=1);OT=np.einsum('ia,jb,kc,abc->ijk',R,R,R,T);Or=np.einsum('aijk,ijk->a',m.B3,OT)
    out=m.joint_test(Or,R@s@R.T,R@d,B,e_d=1e-6,d_max=.1)
    assert out['compatible'] and feasible(out['profiled_d'],R@d,1e-6,.1)
    return out
run('three_axis_rotation_narrow_ball_witness',rotation)

def finite_z_and_chart():
    result=json.loads((CAND/'RESULT.json').read_text());z=np.array(result['finite_z_example']['z']);shift=np.array(result['finite_z_example']['STF3_norm']);
    assert np.all((shift[:-1]/shift[1:]>1.99)&(shift[:-1]/shift[1:]<2.01))
    g=1.004;ell=np.array([0.,.01,.02]);zz=.07*ell;dl=ell*(1+zz)**2
    ch=m.boost_chart(zz,dl,g)
    np.testing.assert_allclose(ch['d_l_star_tilde'],g*ell,rtol=2e-14,atol=1e-17)
    np.testing.assert_allclose(np.diff(ch['z_tilde'])/np.diff(ch['d_l_star_tilde']),.07/g**2,rtol=1e-12)
    assert ch['vertex_z_tilde']==1/g-1
    return dict(doubling_ratios=(shift[:-1]/shift[1:]).tolist(),vertex=ch['vertex_z_tilde'])
run('finite_z_source_and_shifted_corrected_chart',finite_z_and_chart)

(OUT/'INDEPENDENT_CHECKS.json').write_text(json.dumps(dict(cases=records,pass_count=sum(r['status']=='PASS' for r in records),failure_count=sum(r['status']=='FAIL' for r in records)),indent=2)+'\n')
print('SUMMARY',sum(r['status']=='PASS' for r in records),'PASS',sum(r['status']=='FAIL' for r in records),'FAIL',flush=True)
