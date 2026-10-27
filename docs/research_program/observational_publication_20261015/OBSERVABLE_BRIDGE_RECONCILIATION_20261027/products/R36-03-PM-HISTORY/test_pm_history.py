"""Focused physical and retained-statistic falsifiers for R36-03-PM-HISTORY."""
import importlib.util
from pathlib import Path

import numpy as np
import pytest
from scipy.linalg import solve_triangular

SRC = Path(__file__).with_name("pm_history.py")
spec = importlib.util.spec_from_file_location("pm_history", SRC)
pm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pm)


def test_stf_forward_limits_and_wrong_sign():
    e = pm.E
    assert np.allclose(np.einsum("kij,lij->kl", e, e), np.eye(5), atol=1e-15)
    a = pm.tensor(np.array([.03, -.02, .05, .01, -.04]))
    assert np.allclose(pm.coefficients(a), [.03,-.02,.05,.01,-.04], atol=1e-15)
    assert np.allclose(pm.coefficients(1e-18*e[0]),[1e-18,0,0,0,0],rtol=1e-12,atol=1e-34)
    assert np.array_equal(pm.checked_stf(np.zeros((3,3))),np.zeros((3,3)))
    subnormal=1e-320*e[0]
    assert np.array_equal(pm.checked_stf(subnormal),subnormal)
    with pytest.raises(ValueError): pm.checked_stf(1e-320*np.eye(3))
    with pytest.raises(ValueError): pm.checked_stf(1e-18*np.eye(3))
    with pytest.raises(ValueError): pm.checked_stf(1e-18*np.array([[0,1,0],[-1,0,0],[0,0,0]]))
    assert np.array_equal(pm.endpoint_response(np.zeros((3,3)),np.zeros((3,3)),np.zeros((3,3)),1,c=1),np.zeros((3,3)))
    dt = 1e-3
    # B(t)=t*a for t_o=0 and D=c*Delta_t: exactly the positive affine sign.
    forward = pm.endpoint_response(-dt*a,np.zeros((3,3)),a,dt,c=1)
    assert np.allclose(forward,a,rtol=1e-12,atol=1e-14)
    n = np.array([.2,.3,np.sqrt(.87)])
    h = 1e-5
    sep = lambda t: (np.eye(3)+t*a)@n / np.linalg.norm((np.eye(3)+t*a)@n)
    fd = (sep(h)-sep(-h))/(2*h)
    actual = pm.unit_direction_field(forward,n)
    assert np.linalg.norm(fd-actual) < 1e-9
    assert np.linalg.norm(fd+actual)>0.01  # reversed sign must fail
    angle=.37
    rot=np.array([[np.cos(angle),-np.sin(angle),0],[np.sin(angle),np.cos(angle),0],[0,0,1.]])
    assert np.allclose(pm.unit_direction_field(rot@a@rot.T,rot@n),rot@actual,rtol=1e-12,atol=1e-12)
    assert abs(np.linalg.norm(rot@a@rot.T)-np.linalg.norm(a))<1e-14
    with pytest.raises(ValueError): pm.unit_direction_field(a,[1,1,0])
    with pytest.raises(ValueError): pm.endpoint_response(a,a,a,0)
    with pytest.raises(ValueError): pm.endpoint_response(a,a,np.eye(3),1)


def test_history_bound_and_endpoint_witness():
    t=pm.E[0]
    eps=1e-4; dt=2.; c=1.
    # delta B=eps*tau*(1-tau)*T, endpoints vanish, dot B_o=-eps/dt*T.
    da=pm.endpoint_response(np.zeros((3,3)),np.zeros((3,3)),-eps/dt*t,dt,c=c)
    assert np.linalg.norm(da-eps/dt*t)<=1e-12*eps/dt
    assert abs(np.linalg.norm(da)/np.sqrt(5)-2.2360679774997898e-5)<1e-15
    # B(t)=(L/2)t^2*T, t_o=0. The finite-history bound saturates for D=c*Delta_t.
    L=.04
    for delta in (1.,.5,.25):
        actual=pm.endpoint_response(.5*L*delta**2*t,np.zeros((3,3)),np.zeros((3,3)),delta,c=1)
        bound=pm.history_bound(np.zeros((3,3)),delta,delta,L,c=1)
        assert abs(np.linalg.norm(actual)-bound)<1e-14
        assert abs(np.linalg.norm(actual)/delta-L)<1e-14
        assert np.linalg.norm(actual)>pm.history_bound(np.zeros((3,3)),delta,delta,L/2,c=1)
    with pytest.raises(ValueError): pm.history_bound(t,1,1,-1,c=1)


def test_sphere_and_e2_embedding_independent_grid():
    model=pm.model_module()
    m,j,check=pm.embedding(model)
    assert max(check.values())<1e-12
    ra,dec,w=pm.grid(13,29,.17)
    d=np.stack([pm.tangent(e,ra,dec) for e in pm.E],axis=-1)
    sphere=np.einsum('n,nki,nkj->ij',w,d,d)
    assert np.max(np.abs(sphere-np.eye(5)/5))<1e-12
    assert np.max(np.abs(m.T@m-np.eye(5)/5))<1e-12
    v=model.vsh(ra,dec,[2])[:,:,:5]
    assert np.max(np.abs(v@m-d))<1e-12
    assert np.max(np.abs(v@(-m)-d))>.1
    alpha,delta=np.deg2rad(ra),np.deg2rad(dec)
    n=np.stack([np.cos(delta)*np.cos(alpha),np.cos(delta)*np.sin(alpha),np.sin(delta)],axis=1)
    east=np.stack([-np.sin(alpha),np.cos(alpha),np.zeros_like(alpha)],axis=1)
    north=np.stack([-np.sin(delta)*np.cos(alpha),-np.sin(delta)*np.sin(alpha),np.cos(delta)],axis=1)
    spin=np.cross(np.array([.2,-.1,.3]),n)
    glide=np.array([.1,.2,-.2])-n*(n@np.array([.1,.2,-.2]))[:,None]
    for field in (spin,glide):
        tangent=np.stack([np.einsum('ni,ni->n',field,east),np.einsum('ni,ni->n',field,north)],axis=1)
        assert np.max(np.abs(np.einsum('n,nki,nk->i',w,d,tangent)))<1e-12


def test_psd_projection_against_direct_gls_with_cross_source_covariance():
    # Two 2-component sources; both within-source and cross-source covariance.
    x=np.array([[1.,.2,.5,-.3],[.1,1.,-.2,.4],[.7,-.4,1.,.2],[-.3,.6,.4,1.]])
    cov=np.array([[2.,.3,.2,-.1],[.3,1.5,.1,.2],[.2,.1,1.7,-.4],[-.1,.2,-.4,2.2]])
    l=np.linalg.cholesky(cov)
    q=solve_triangular(l,x,lower=True)
    j=np.eye(4)[:,:2]; n=np.eye(4)[:,2:]
    result=pm.profile(q,j,n)
    g=x.T@np.linalg.solve(cov,x)
    direct=g[:2,:2]-g[:2,2:]@np.linalg.solve(g[2:,2:],g[2:,:2])
    assert np.allclose(result['information'],direct,rtol=1e-9,atol=1e-10)
    rotation=np.array([[0.,-1.],[1.,0.]])
    mixed=np.array([[2.,.3],[-.4,1.]])
    changed=pm.profile(q,j@rotation,n@mixed)
    assert np.allclose(changed['information'],rotation.T@direct@rotation,rtol=1e-9,atol=1e-10)


def test_retained_gram_rank_annihilation_history_and_power():
    out=pm.build()
    g=out['gram']; p=g['primary_spin_glide6']['profile']; sens=g['all97_sensitivity']['profile']
    assert p['rank']==5 and p['nuisance_rank']==6
    assert sens['rank']==5 and sens['nuisance_rank']==97
    assert np.linalg.eigvalsh(np.array(sens['information'])-np.array(p['information']))[-1]<1e-8*p['unprofiled_scale']
    assert g['e2_nuisance_falsifier']['rank']==0
    assert g['common_b1_spin_falsifier']['rank']==0
    assert g['primary_spin_glide6']['joint']['joint_rank']==11
    assert g['all97_sensitivity']['joint']['joint_rank']==102
    assert all(v=={'spin_glide6':5,'all97':5,'e2_free':0} for v in g['rank_sensitivity_relative_to_unprofiled'].values())
    assert np.linalg.norm(g['primary_spin_glide6']['joint']['cross_gram'])>0
    assert np.linalg.norm(g['primary_spin_glide6']['joint']['selected_sample_full5_coefficients_uasyr'])>0
    for h in out['history_images']:
        image=np.array(h['information_10x10']); null=np.array(h['null_columns_10x5'])
        assert h['rank']==5 and np.linalg.norm(image@null)<1e-10*np.linalg.norm(image)
        assert np.linalg.norm(h['endpoint_derivative_cross_5x5'])>0 if h['k'] else np.linalg.norm(h['endpoint_derivative_cross_5x5'])==0
    rows=out['power_frontier']['grid']
    assert abs(rows[0]['power_best']-.05)<1e-12 and abs(rows[0]['power_worst']-.05)<1e-12
    assert all(a['power_best']<=b['power_best'] for a,b in zip(rows,rows[1:]))
    assert all(a['power_worst']<=b['power_worst'] for a,b in zip(rows,rows[1:]))
    assert abs(pm.power_frontier(np.array(p['information']))['rho80_best_uasyr']-out['power_frontier']['rho80_best_uasyr'])<1e-12
