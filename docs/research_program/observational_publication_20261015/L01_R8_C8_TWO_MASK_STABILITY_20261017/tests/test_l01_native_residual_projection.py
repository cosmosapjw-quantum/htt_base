"""Synthetic finite-pixel controls; not a run on native Planck FITS."""
from pathlib import Path
import importlib.util
import subprocess
import sys
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))


def api():
    import l01_native_residual_projection as m
    return m


def test_feature_present():
    assert importlib.util.find_spec('l01_native_residual_projection') is not None


def problem(seed=4):
    rng=np.random.default_rng(seed)
    a=rng.normal(size=(48,6)); c=np.ones(48);c[:4]=0
    t=c.copy();t[30:]=0; w=.07
    gc=w*a.T@(c[:,None]*a);gt=w*a.T@(t[:,None]*a)
    pc=np.linalg.solve(gc,a.T*c)*np.sqrt(w)
    pt=np.linalg.solve(gt,a.T*t)*np.sqrt(w)
    return a,c,t,w,gc,gt,pc,pt


@pytest.mark.parametrize('seed',[1,3,8])
def test_dual_gram_equals_explicit_pixel_operator(seed):
    m=api();*_,gc,gt,pc,pt=problem(seed)
    h,meta=m.nested_dual_gram(gc,gt)
    np.testing.assert_allclose(h,(pt-pc)@(pt-pc).T,rtol=2e-12,atol=1e-15)
    assert meta['gain_all']==pytest.approx(np.linalg.norm(pt-pc,2),rel=1e-12)


def test_sharp_bound_is_attained_by_right_singular_vector():
    m=api();*_,gc,gt,pc,pt=problem()
    _,meta=m.nested_dual_gram(gc,gt)
    u,s,vh=np.linalg.svd(pt-pc,full_matrices=False)
    assert np.linalg.norm((pt-pc)@vh[0])==pytest.approx(meta['gain_all'])


def test_same_region_has_zero_contrast_gain():
    m=api();*_,gc,gt,pc,pt=problem()
    h,meta=m.nested_dual_gram(gc,gc)
    assert meta['gain_all']==0
    assert np.count_nonzero(h)==0


@pytest.mark.parametrize('fault',['nonfinite','nonsquare','nonsymmetric','singular','nonnested_gram'])
def test_bad_grams_are_rejected(fault):
    m=api();*_,gc,gt,pc,pt=problem()
    if fault=='nonfinite':gc[0,0]=np.nan
    if fault=='nonsquare':gc=gc[:,:-1]
    if fault=='nonsymmetric':gc[1,0]+=1
    if fault=='singular':gt=np.zeros_like(gt)
    if fault=='nonnested_gram':gt=2*gc
    with pytest.raises(ValueError):m.nested_dual_gram(gc,gt)


def test_window_zeros_data_but_does_not_rewindow_reconstruction():
    m=api()
    raw=np.array([[1.,np.nan,3.],[2.,1e30,4.]])
    rec=np.array([[.5,8.,.2],[1.,9.,.3]])
    w=np.array([True,False,True]);c=np.ones(3,dtype=bool);t=np.array([True,False,True])
    fields,energy=m.prepare_block(raw,rec,w,c,t)
    np.testing.assert_array_equal(fields[1],[0.,8.,-8.])
    np.testing.assert_array_equal(fields[4],[0.,9.,-9.])
    assert energy==pytest.approx(np.sum(fields[:,2]**2))


@pytest.mark.parametrize('bad',['inside_nan','inside_unseen','nonnested','shape','window_type'])
def test_invalid_block_rejected(bad):
    m=api();raw=np.ones((2,5));rec=np.zeros_like(raw)
    w=np.ones(5,dtype=bool);c=w.copy();t=w.copy()
    if bad=='inside_nan':raw[0,2]=np.nan
    if bad=='inside_unseen':raw[0,2]=-1.6375e30
    if bad=='nonnested':c[0]=False
    if bad=='shape':rec=rec[:,:-1]
    if bad=='window_type':w=w.astype(int)
    with pytest.raises(ValueError):m.prepare_block(raw,rec,w,c,t)


@pytest.mark.parametrize('amp',[1.,1e-6,1e-12,1e-100])
def test_residual_projection_decomposition_and_bound(amp):
    m=api();a,c,t,w,gc,gt,pc,pt=problem()
    rng=np.random.default_rng(42)
    raw=amp*rng.normal(size=48);syn=amp*rng.normal(size=48)
    data=np.column_stack([raw,syn,raw-syn])
    states=[]
    for mask,g in [(c,gc),(t,gt)]:
        rhs=w*a.T@(mask[:,None]*data)
        states.append({'gram':g,'rhs':rhs,'coefficients':np.linalg.solve(g,rhs)})
    evidence=m.compare_states(states[0],states[1],np.sqrt(w*np.sum(c*(raw-syn)**2)))
    x=states[1]['coefficients']-states[0]['coefficients']
    np.testing.assert_allclose(evidence['contrast_raw_K_CMB'],x[:,0],atol=0,rtol=1e-13)
    assert evidence['components']['all']['measured_residual_norm_K_CMB']<=evidence['components']['all']['residual_norm_bound_K_CMB']*(1+1e-12)
    assert evidence['closure_relative']<1e-12
    assert evidence['is_infinite_spectral_tail_bound'] is False


def test_transformed_low_fit_is_not_cosmic_B_claim():
    m=api();a,c,t,w,gc,gt,pc,pt=problem()
    h=np.arange(6)/1e6;f=a@h
    # Full low-design injection: both masks recover h; no band assumption about other maps.
    states=[]
    for mask,g in [(c,gc),(t,gt)]:
        data=np.column_stack((f,np.zeros_like(f),f));rhs=w*a.T@(mask[:,None]*data)
        states.append({'gram':g,'rhs':rhs,'coefficients':np.linalg.solve(g,rhs)})
    r=m.compare_states(*states,np.sqrt(w*np.sum(c*f*f)))
    assert np.linalg.norm(r['contrast_raw_K_CMB'])<1e-19
    assert r['physical_EB_identification'] is False


def test_zero_residual_has_zero_measured_contrast():
    m=api();a,c,t,w,gc,gt,pc,pt=problem()
    f=np.sin(np.arange(48));data=np.column_stack((f,f,np.zeros_like(f)))
    ss=[]
    for mask,g in [(c,gc),(t,gt)]:
        rhs=w*a.T@(mask[:,None]*data);ss.append({'gram':g,'rhs':rhs,'coefficients':np.linalg.solve(g,rhs)})
    r=m.compare_states(*ss,0.)
    assert r['components']['all']['measured_residual_norm_K_CMB']==0


def test_existing_result_not_overwritten_before_optional_native_import(tmp_path):
    m=api();p=tmp_path/'result.json';p.write_text('preserve')
    assert m.main(['--root',str(tmp_path),'--band-dir',str(tmp_path),'--native-receipt','missing', '--out',str(p)])==2
    assert p.read_text()=='preserve'


def test_cli_help_needs_no_healpy():
    m=api();r=subprocess.run([sys.executable,m.__file__,'--help'],capture_output=True,text=True)
    assert r.returncode==0 and '--band-dir' in r.stdout


def test_selected_component_gain_matches_explicit_rows():
    m=api();a,c,t,w,gc,gt,pc,pt=problem()
    rng=np.random.default_rng(21);f=rng.normal(size=48);s=rng.normal(size=48)
    data=np.column_stack((f,s,f-s));states=[]
    for mask,g in [(c,gc),(t,gt)]:
        rhs=w*a.T@(mask[:,None]*data)
        states.append({'gram':g,'rhs':rhs,'coefficients':np.linalg.solve(g,rhs)})
    out=m.compare_states(*states,np.sqrt(w*np.sum(c*(f-s)**2)),{'selected':np.array([1,3,5])})
    assert out['components']['selected']['gain']==pytest.approx(np.linalg.norm((pt-pc)[[1,3,5]],2),rel=1e-12)


def test_window_is_not_an_implicit_redefinition_of_fit_region():
    m=api();a,c,t,w,gc,gt,pc,pt=problem()
    # A fixed data window zeroes four samples but does not remove them from G.
    data=np.ones(48);data[8:12]=0
    y=np.linalg.solve(gc,w*a.T@(c*data))
    incorrectly_restricted=c.copy();incorrectly_restricted[8:12]=0
    wrong=np.linalg.lstsq(a[incorrectly_restricted.astype(bool)],data[incorrectly_restricted.astype(bool)],rcond=None)[0]
    assert np.linalg.norm(y-wrong)>1e-3
    np.testing.assert_allclose(y,np.linalg.lstsq(a[c.astype(bool)],data[c.astype(bool)],rcond=None)[0],rtol=1e-12)
