import sys
from pathlib import Path
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from l03_paired_scan import *
FILE=Path(__file__).resolve().parents[1]/'inputs/processing_coefficients.npz'

def test_locked_processing_bank():
    o,p=read_bank(FILE)
    assert o.shape==(6,32) and p.shape==(6,300,32)

def test_independent_sky_count():
    o,p=read_bank(FILE);r=process_scan(o,p)
    assert r['calibration_latent_rows']==100 and r['heldout_latent_rows']==200
    assert 1/201<=r['descriptive_rank_p']<=1
    assert r['heldout_scan_exceed']==round(r['descriptive_rank_p']*201-1)

def test_identical_processing_products_not_six_skies():
    rng=np.random.default_rng(42);bank=rng.normal(size=(1,43,3));o=np.ones((1,3))
    a=process_scan(np.repeat(o,6,axis=0),np.repeat(bank,6,axis=0),10)
    assert np.allclose(a['method_energy_correlation_lower_tri'],1,atol=1e-5)
    assert a['descriptive_rank_p']==a['per_method_descriptive_rank_p'][0]

def test_unpaired_order_invariant():
    o,p=read_bank(FILE);r=process_scan(o,p)
    order=[2,1,0,3,5,4]
    s=process_scan(o[order],p[order])
    assert r['descriptive_rank_p']==s['descriptive_rank_p']

def test_pair_breaking_detection():
    o,p=read_bank(FILE)
    a=process_scan(o,p)
    changed=p.copy();changed[2,100:]=changed[2,100:][::-1]
    b=process_scan(o,changed)
    assert not np.allclose(a['method_energy_correlation_lower_tri'],b['method_energy_correlation_lower_tri'])

def test_invalid_inputs():
    o,p=read_bank(FILE)
    with pytest.raises(ValueError):process_scan(o,p[:,:,:-1])
    with pytest.raises(ValueError):process_scan(o,p,300)
    with pytest.raises(ValueError):process_scan(o,p,3)

def test_two_way_variance_exact():
    x=crossed_reuse_variance(999,300,1,1)
    assert np.isclose(x['sd_inflation_vs_iid'],np.sqrt((999+300)/2))
    assert x['sd_inflation_vs_iid']>25

def test_two_way_without_common_noise():
    x=crossed_reuse_variance(100,1,1,0)
    assert np.isclose(x['sd_inflation_vs_iid'],1)
