from pathlib import Path
import sys
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from s02_interval_coupled import original_source_draws,ratio_intervals,sharp_event_bounds,run
ROOT=Path(__file__).resolve().parents[1]/'source'


def test_original_2048_coupled_real_source():
    samples=original_source_draws(ROOT)
    assert samples.shape==(2048,4,9)
    assert len(samples)==2048 and (samples[:,:,0]>0).all()
    q=np.linalg.norm(samples[:,:,4:9],axis=2)/samples[:,:,0]
    assert np.allclose(np.median(q,axis=0),[.02987438999091302,.042993402675345294,.051269805071950045,.031119742899754166],atol=1e-12)
    assert np.isclose((q[:,2]>.05).mean(),.59814453125)


def test_zero_radius_exact_and_joint_unit():
    x=original_source_draws(ROOT)
    a,b=ratio_intervals(x,[0.]*4,[0.]*4)
    assert np.array_equal(a,b)
    bounds=sharp_event_bounds(a,b,[.05],mode='per_window')[0]
    assert bounds['lower']==bounds['upper']
    assert np.allclose(bounds['lower'],[0.,.06640625,.59814453125,.00537109375])


def test_formula_endpoints_reachable_for_individual_draw():
    x=original_source_draws(ROOT)[:1].copy()
    lower,upper=ratio_intervals(x,[1]*4,[.25]*4)
    for j in range(4):
        s=x[0,j,4:9]
        n=np.linalg.norm(s);h=x[0,j,0]
        direction=s/n
        assert np.isclose(np.linalg.norm(s-direction*min(n,1.))/(h+.25),lower[0,j])
        assert np.isclose(np.linalg.norm(s+direction*1.)/(h-.25),upper[0,j])


def test_sharp_probability_bounds_strict_endpoint():
    a=np.array([[.5,.5,.5,.5],[1.,1.,1.,1.]])
    b=np.array([[1.,1.,1.,1.],[2.,2.,2.,2.]])
    out=sharp_event_bounds(a,b,[1.],mode='per_window')[0]
    assert out['lower']==[0.]*4 and out['upper']==[.5]*4
    y=sharp_event_bounds(a,b,[1.],mode='at_least_one')[0]
    assert y['lower']==0 and y['upper']==.5
    y2=sharp_event_bounds(a,b,[1.],mode='all_windows')[0]
    assert y2['lower']==0 and y2['upper']==.5
    with pytest.raises(ValueError):sharp_event_bounds(a,b,[1.],weights=[1.,1.])


def test_coupled_any_all_lower_upper():
    low=np.array([[.2,.0,.0,.0],[0,.2,.0,.0]])
    high=np.array([[.2,.0,.0,.9],[.5,.2,.0,0]])
    anyev=sharp_event_bounds(low,high,[.1],mode='at_least_one')[0]
    all_ev=sharp_event_bounds(low,high,[.1],mode='all_windows')[0]
    assert anyev['lower']==anyev['upper']==1.
    assert all_ev['lower']==all_ev['upper']==0.


def test_bad_physical_radius_must_fail():
    x=original_source_draws(ROOT)[:6]
    with pytest.raises(ValueError):ratio_intervals(x,[1]*4,[1e8]*4)
    with pytest.raises(ValueError):ratio_intervals(x,[1]*4,[-1]*4)
    with pytest.raises(ValueError):ratio_intervals(x,[float('nan')]*4,[0]*4)
    with pytest.raises(ValueError):ratio_intervals(x,[1]*3,[0]*4)
    with pytest.raises(ValueError):ratio_intervals(x[:,:,0],[1]*4,[0]*4)


def test_scenarios_nested_and_physical_fully_unknown():
    o=run(ROOT)
    ex=o['scenarios']['exact_working']['working_ratio_joint_event_bounds']['per_window']
    m=o['scenarios']['assumed_stf0p5_H0p2']['working_ratio_joint_event_bounds']['per_window']
    w=o['scenarios']['assumed_stf1p0_H0p5']['working_ratio_joint_event_bounds']['per_window']
    for e,x,y in zip(ex,m,w):
        assert np.all(np.array(y['lower'])<=np.array(x['lower'])+1e-14)
        assert np.all(np.array(x['lower'])<=np.array(e['lower'])+1e-14)
        assert np.all(np.array(e['upper'])<=np.array(x['upper'])+1e-14)
        assert np.all(np.array(x['upper'])<=np.array(y['upper'])+1e-14)
    assert o['physical_functionals']['physical_unknown_mass']==1.
    assert o['physical_functionals']['physical_Pi_outer']==[0.,1.]
    assert 'NOT_PHYSICAL' in o['claim']


def test_source_corruption_refused(tmp_path):
    d=tmp_path/'raw';d.mkdir()
    for n in ('selected_source_observables.npz','H03_CONDITIONAL_MATRIX.npz','h03_source_original.zip'):
        (d/n).write_bytes((ROOT/n).read_bytes())
    f=d/'H03_CONDITIONAL_MATRIX.npz';f.write_bytes(f.read_bytes()+b'corrupt')
    with pytest.raises(ValueError,match='source digest'):original_source_draws(d)


def test_joint_weight_and_permutation_invariance():
    x=original_source_draws(ROOT)[:100]
    low,high=ratio_intervals(x,[.1]*4,[.2]*4)
    rng=np.random.default_rng(7);order=rng.permutation(len(low))
    a=sharp_event_bounds(low,high,[.05],mode='at_least_one')[0]
    b=sharp_event_bounds(low[order],high[order],[.05],mode='at_least_one')[0]
    assert a==b
    ww=np.ones(len(low))/len(low)
    ww[0]*=.7;ww=ww/ww.sum()
    c=sharp_event_bounds(low,high,[.05],weights=ww,mode='per_window')[0]
    assert all(0<=p<=1 for p in c['lower']+c['upper'])


def test_drawwise_worstcase_event_bounds_attainable():
    x=original_source_draws(ROOT)[:3]
    a,b=ratio_intervals(x,[.3]*4,[.2]*4)
    threshold=float((a[0,0]+b[0,0])/2)
    v=sharp_event_bounds(a,b,[threshold])[0]
    assert v['lower'][0]<=v['upper'][0]
    # For per-point choices, q_min/q_max are attained by aligned perturbations:
    s=x[0,0,4:9];n=np.linalg.norm(s);h=x[0,0,0]
    assert np.isclose(np.linalg.norm(s-.3*s/n)/(h+.2),a[0,0])
    assert np.isclose(np.linalg.norm(s+.3*s/n)/(h-.2),b[0,0])
