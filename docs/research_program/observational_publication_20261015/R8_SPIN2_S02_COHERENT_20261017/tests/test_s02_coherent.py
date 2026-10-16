import sys
from pathlib import Path
import numpy as np
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from s02_coherent_stf import lower_certificates,run
from s02_interval_coupled_original import original_source_draws,ratio_intervals


def actual_draws():return original_source_draws(ROOT/'source')


def test_source_digest_and_joint_size():
    d=actual_draws();assert d.shape==(2048,4,9)
    assert np.isfinite(d).all() and (d[:,:,0]>0).all()


def test_real_case_improvement_with_shared_stf():
    r=lower_certificates(actual_draws(),.02,3.,[.2]*4)
    assert r['rectangular_lower_count']==85
    assert r['coherent_pairwise_lower_count']==1094
    assert r['pairwise_only_count']==1009
    assert r['coherent_certified_lower_mass']>r['rectangle_lower_mass']


def test_original_lower_never_exceeded_by_upper():
    d=actual_draws()
    for b in [.5,1.,2.,3.,4.]:
        lo,hi=ratio_intervals(d,[b]*4,[.2]*4)
        for threshold in [.015,.02,.025,.05]:
            res=lower_certificates(d,threshold,b,[.2]*4)
            upper=float(np.any(hi>threshold,axis=1).mean())
            assert 0<=res['rectangle_lower_mass']<=res['coherent_certified_lower_mass']<=upper<=1


def test_antipodal_common_offset_nontrivial_certification():
    d=np.zeros((1,4,9));d[:,:,0]=2
    d[0,0,4]=1;d[0,1,4]=-1
    x=lower_certificates(d,.2,5.,[0]*4)
    assert x['rectangular_lower_count']==0
    assert x['coherent_pairwise_lower_count']==1


def test_pairwise_triangle_lower_under_random_shifts():
    d=actual_draws();r=lower_certificates(d,.02,3.,[.2]*4)
    H=d[:,:,0];s=d[:,:,4:9]
    ids=np.flatnonzero(np.linalg.norm(s[:,0]-s[:,3],axis=1)>.02*(H[:,0]+H[:,3]+.4))[:5]
    assert len(ids)>0
    rng=np.random.default_rng(2026)
    for i in ids:
       for _ in range(70):
           delta=rng.normal(size=5);delta=delta/max(1,np.linalg.norm(delta)/3)
           dh=rng.uniform(-.2,.2,size=4)
           value=np.linalg.norm(s[i]+delta[None,:],axis=1)/(H[i]+dh)
           assert np.any(value>.02)


def test_common_additive_offset_cancels_exactly():
    d=actual_draws()[:5];s=d[:,:,4:9]
    delta=np.array([.5,-.7,.1,1.,0.])
    assert np.allclose((s[:,0]+delta)-(s[:,3]+delta),s[:,0]-s[:,3],atol=1e-14)


def test_invariance_under_correlated_draw_permutation():
    d=actual_draws();rng=np.random.default_rng(405);p=rng.permutation(len(d))
    r1=lower_certificates(d,.02,3.,[.2]*4)
    r2=lower_certificates(d[p],.02,3.,[.2]*4)
    assert r1['coherent_pairwise_lower_count']==r2['coherent_pairwise_lower_count']


def test_refuse_invalid_source_shapes_and_radius():
    d=actual_draws()[:10]
    with pytest.raises(ValueError):lower_certificates(d[:,:,:8],.02,3.,[.2]*4)
    with pytest.raises(ValueError):lower_certificates(d,0.,3.,[.2]*4)
    with pytest.raises(ValueError):lower_certificates(d,.02,-1,[.2]*4)
    with pytest.raises(ValueError):lower_certificates(d,.02,3.,[100.]*4)


def test_deterministic_result_counts(tmp_path):
    a=run(ROOT/'source',tmp_path/'a.json')
    b=run(ROOT/'source',tmp_path/'b.json')
    assert a==b
    assert (tmp_path/'a.json').read_bytes()==(tmp_path/'b.json').read_bytes()
    assert len(a['results'])==25


def test_same_source_not_four_independent_sky_realizations():
    a=run(ROOT/'source',ROOT/'results/S02_COHERENT_STF_SOURCE_BOUNDS.json')
    assert a['joint_draw_ids']==2048
    assert a['four_windows_not_independent'] is True
    assert 'UNMEASURED' in a['physical_x_C_Q_F_G_F']


def test_transfer_decoherence_reduces_certified_lower():
    d=actual_draws();vals=[]
    for eta in [0.,.1,.25,.5,1.]:
        r=lower_certificates(d,.02,3.,[.2]*4,transfer_gap=eta)
        vals.append(r['coherent_certified_lower_mass'])
    assert vals[0]==1094/2048
    assert all(a>=b for a,b in zip(vals,vals[1:]))
    assert vals[-1]>=85/2048


def test_transfer_gap_rule_proved_by_constructed_bounded_matrix():
    # T_i and T_j differ by 0.1*I, both norms <=1. For arbitrary common
    # delta with radius3 and arbitrary per-window denominator radii .2,
    # any pair certificate remains valid.
    d=actual_draws();a=.2;b=3.;t=.02;eta=.1
    r=lower_certificates(d,t,b,[a]*4,transfer_gap=eta)
    s=d[:,:,4:9];H=d[:,:,0];rng=np.random.default_rng(904)
    guaranteed=(np.linalg.norm(s[:,1]-s[:,3],axis=1)>t*(H[:,1]+H[:,3]+2*a)+eta*b)
    ids=np.flatnonzero(guaranteed)[:8];assert len(ids)>0
    for i in ids:
        for _ in range(40):
            delta=rng.normal(size=5);delta=delta/max(1,np.linalg.norm(delta)/b)
            h=rng.uniform(-a,a,size=4)
            T=np.array([1.,.95,.92,.85])
            values=np.linalg.norm(s[i]+T[:,None]*delta[None,:],axis=1)/(H[i]+h)
            assert np.any(values>t)


def test_negative_transfer_gap_rejected():
    with pytest.raises(ValueError):lower_certificates(actual_draws()[:2],.02,3.,[.2]*4,transfer_gap=-.1)
