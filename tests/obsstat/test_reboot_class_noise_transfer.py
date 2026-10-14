import importlib.util
from pathlib import Path
import sys
import numpy as np
import pytest

CANDIDATE=Path(__file__).resolve().parents[2]
path=CANDIDATE/'scripts/run_reboot_class_noise_transfer.py'
if not path.exists():path=Path.cwd()/'scripts/run_reboot_class_noise_transfer.py'
spec=importlib.util.spec_from_file_location('class_control',path)
mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod)


def test_transfer_rows_output_veb_blocks_and_out_of_band():
    n=8;f=np.zeros((3*n,3*n))
    # E input ell5 -> B output ell6 and ell0; output rows first.
    f[2*n+6,n+5]=2
    f[2*n+0,n+5]=3
    f[n+5,n+5]=4
    g=mod.transfer_geometry(f,n_ell=n,low=5,high=6)
    assert g['blocks']['B<-E']['frobenius_norm_low_output']==pytest.approx(2)
    assert g['blocks']['B<-E']['frobenius_norm_outside_output_band']==pytest.approx(3)
    assert g['blocks']['E<-B']['frobenius_norm_low_output']==0
    assert g['leakage_geometry']['E_to_B_over_E_to_E_norm']==pytest.approx(.5)
    assert g['blocks']['B<-E']['svd_rank_at_machine_tolerance']==1


def test_pairing_permutation_deterministic_no_reuse_or_special_identity():
    p=mod.pairing()
    assert p.shape==(200,2)
    assert np.array_equal(p[:,0],np.arange(200))
    assert sorted(p[:,1])==list(range(200))
    assert np.array_equal(p,mod.pairing())
    assert np.any(p[:,0]!=p[:,1])


def test_half_difference_alm_power_factor_quarter_and_cross():
    hp=pytest.importorskip('healpy')
    size=hp.Alm.getsize(32)
    a=np.zeros(size,complex);b=np.zeros(size,complex)
    a[hp.Alm.getidx(32,10,0)]=2
    b[hp.Alm.getidx(32,10,0)]=6
    d=mod.half_difference(a,b)
    assert d[hp.Alm.getidx(32,10,0)]==-2
    assert hp.alm2cl(d)[10]==pytest.approx(hp.alm2cl(a-b)[10]/4)
    assert np.array_equal(mod.half_difference(a,a),np.zeros(size))


def test_eb_feature_means_absolute_per_ell_not_absolute_of_mean():
    hp=pytest.importorskip('healpy')
    e=np.zeros(hp.Alm.getsize(32),complex);b=e.copy()
    for ell in range(5,31):
        idx=hp.Alm.getidx(32,ell,0)
        e[idx]=1
        b[idx]=(-1)**ell
    coefficients={mask+'_'+kind:array for mask in mod.MASKS for kind,array in (('E',e),('B',b))}
    values=mod.feature_vector(coefficients)
    eb=np.real(hp.alm2cl(e,b))[5:31]
    assert values[2]==pytest.approx(np.abs(eb).mean())
    assert values[2]>abs(eb.mean())
    assert values[5]==values[2]


def test_max_rank_two_sided_and_fixed_floor():
    train=np.tile(np.arange(40)[:,None],(1,6)).astype(float)
    cal=np.tile(np.arange(160)[:,None],(1,6)).astype(float)
    obs=np.full(6,-1e6)
    result=mod.max_statistic(obs,train,cal)
    assert result['exceedances']==0
    assert result['rank_p']==pytest.approx(1/161)
    with pytest.raises(ValueError):mod.max_statistic(obs,train,cal[:159])
