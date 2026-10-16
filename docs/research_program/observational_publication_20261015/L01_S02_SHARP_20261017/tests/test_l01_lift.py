from pathlib import Path
import sys
import numpy as np
import pytest
from scipy.linalg import lstsq
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from finite_t_lift import read_sources,min_high_norm,sharp_linear_interval,run
ROOT=Path(__file__).resolve().parents[1]/'source'

def test_real_source_shapes_and_norm():
    k,t,n=read_sources(ROOT)
    assert k.shape==(32,1053) and t.shape==(9,32) and len(set(n))==9
    out=run(ROOT)
    assert out['row_rank']==32 and out['nullity']==1021
    assert abs(out['operator_norm']-2.4328695605629203)<1e-11
    assert all(p['relative_residual']<1e-12 for p in out['product_rows'])
    assert out['physical_sky_count']==1

def test_real_source_min_norm_is_sharp_and_orthogonal():
    k,t,n=read_sources(ROOT)
    radius,residual,x=min_high_norm(k,t[n.index('SMICA_FULL')])
    assert np.linalg.norm(k@x-t[n.index('SMICA_FULL')])<1e-10
    rng=np.random.default_rng(17)
    raw=rng.normal(size=k.shape[1]);null=raw-k.T@np.linalg.solve(k@k.T,k@raw)
    assert np.linalg.norm(k@null)<1e-11
    assert abs(x@null)<1e-10
    assert np.linalg.norm(x+null)>radius
    # Independent SVD minimum norm, no reliance on same Cholesky expression
    sol,*_=lstsq(k,t[n.index('SMICA_FULL')],lapack_driver='gelsd')
    assert np.allclose(sol,x,rtol=3e-11,atol=1e-10)

def test_real_source_processing_difference_is_not_second_sky():
    o=run(ROOT)
    assert len(o['product_rows'])==9 and o['physical_sky_count']==1
    assert 1.<o['SMICA_HM1_minus_HM2_min_high_diff_norm']<5.
    assert 250.<o['product_rows'][0]['min_high_l6_32_coeff_norm_microK_if_true_low_set_to_zero']<300.

def test_sharp_scalar_interval_constructive():
    k=np.array([[1.,2.,0.],[0.,1.,-1.]])
    y=np.array([3.,-1.]);v=np.array([1.,-2.]);r=3.0
    lo,hi=sharp_linear_interval(k,y,v,r)
    w=k.T@v
    hmin=+r*w/np.linalg.norm(w)
    hmax=-hmin
    assert np.isclose(v@(y-k@hmin),lo)
    assert np.isclose(v@(y-k@hmax),hi)
    assert np.isclose((lo+hi)/2,v@y)
    assert sharp_linear_interval(k,y,v,0.)==(float(v@y),float(v@y))

def test_minimum_high_mode_tiny_independent_case():
    k=np.array([[1.,2.,0.],[0.,1.,1.]])
    y=np.array([.1,3.])
    norm,residual,x=min_high_norm(k,y)
    v=np.linalg.pinv(k)@y
    assert np.allclose(x,v,atol=1e-13)
    assert abs(norm-np.linalg.norm(v))<1e-13

def test_invalid_nonfinite_rank_and_hash(tmp_path):
    k=np.zeros((2,3));y=np.ones(2)
    with pytest.raises(Exception):min_high_norm(k,y)
    with pytest.raises(ValueError):min_high_norm(np.ones((3,2)),np.ones(3))
    with pytest.raises(ValueError):min_high_norm(np.array([[np.nan,0,1]]),np.ones(1))
    with pytest.raises(ValueError):sharp_linear_interval(np.ones((2,3)),np.ones(2),np.ones(2),-1.)
    d=tmp_path/'source';d.mkdir()
    for f in ROOT.glob('*.npz'):(d/f.name).write_bytes(f.read_bytes())
    x=d/'retained_common_support_coefficients.npz';x.write_bytes(x.read_bytes()+b'A')
    with pytest.raises(ValueError,match='source mismatch'):read_sources(d)

def test_orthogonal_change_of_high_harmonic_basis():
    k,t,_=read_sources(ROOT)
    idx=np.arange(k.shape[1])[::-1]
    norm,_,_=min_high_norm(k,t[0]);norm2,_,_=min_high_norm(k[:,idx],t[0])
    assert abs(norm-norm2)<1e-9


def test_source_bands_separately_are_full_row_rank():
    out=run(ROOT)
    rows=out['band_comparison']
    assert [r['columns'] for r in rows]==[253,800,1053]
    assert all(r['row_rank']==32 for r in rows)
    assert [round(r['SMICA_FULL_min_high_norm_microK'],5) for r in rows]==[353.31133,527.21214,273.15095]
    assert rows[2]['SMICA_FULL_min_high_norm_microK']<min(r['SMICA_FULL_min_high_norm_microK'] for r in rows[:2])
