"""Finite vector and cutoff diagnostics; all files/arrays here are manufactured."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import l01_split_checkpoint_spectra as shared


def api():
    import l01_cutoff_band_diagnostics as m
    return m


def test_new_module_presence():
    assert importlib.util.find_spec('l01_cutoff_band_diagnostics') is not None


def vector(first=0., second=0.):
    a=np.zeros(64); a[5]=first; a[6]=second
    return a


@pytest.mark.parametrize('scale', [1., 1e-6, 1e-12, 1e-100])
def test_signed_interference_and_units(scale):
    m=api(); mid=scale*vector(3,4); tail=scale*vector(-2,-4)
    r=m.band_budget(mid+tail,mid,tail)['B']
    assert r['mid_energy_K_CMB2']==pytest.approx(25*scale**2,rel=1e-13,abs=0.)
    assert r['tail_energy_K_CMB2']==pytest.approx(20*scale**2,rel=1e-13,abs=0.)
    assert r['interference_K_CMB2']==pytest.approx(-44*scale**2,rel=1e-13,abs=0.)
    assert r['total_energy_K_CMB2']==pytest.approx(scale**2,rel=1e-13,abs=0.)
    assert r['coherence']==pytest.approx(-22/np.sqrt(500))
    assert 0<r['triangle_saturation']<.11


def test_zero_and_orthogonal_budget():
    m=api(); z=np.zeros(64)
    assert m.band_budget(z,z,z)['B']['coherence'] is None
    a=vector(1,0);b=vector(0,2)
    r=m.band_budget(a+b,a,b)['B']
    assert r['interference_K_CMB2']==0
    assert r['total_energy_K_CMB2']==5


def test_cancellation_and_amplification():
    m=api(); a=vector(1,2)
    assert m.band_budget(a-a,a,-a)['B']['triangle_saturation']==0
    assert m.band_budget(2*a,a,a)['B']['triangle_saturation']==pytest.approx(1)


@pytest.mark.parametrize('bad', ['shape','complex','nan','closure'])
def test_bad_budget_rejected(bad):
    m=api();a=vector(1,2);b=vector(-1,0);total=a+b
    if bad=='shape':a=a[:-1]
    if bad=='complex':a=a.astype(complex)
    if bad=='nan':a[0]=np.nan
    if bad=='closure':total[5]+=.1
    with pytest.raises(ValueError):m.band_budget(total,a,b)


def test_parent_scale_handles_tiny_difference_roundoff():
    m=api(); a=vector(1e-20); b=-a;total=vector(1e-22)
    m.band_budget(total,a,b,reference_scale=1e-6)
    with pytest.raises(ValueError):m.band_budget(total,a,b)


def alms(L,seed=0):
    r=np.random.default_rng(seed)
    a=1e-6*(r.normal(size=(2,(L+1)*(L+2)//2))+1j*r.normal(size=(2,(L+1)*(L+2)//2)))
    a[:,:L+1]=a[:,:L+1].real;a[:,:2]=0;a[:,L+1]=0
    return a


@pytest.mark.parametrize('low,high',[(16,32),(32,64),(64,128)])
def test_m_major_reindex_not_prefix(low,high):
    m=api();a=alms(high)
    b=m.restrict_alms(a,high,low)
    for ell in range(low+1):
        for mm in range(ell+1):
            ih=mm*(2*high+1-mm)//2+ell
            il=mm*(2*low+1-mm)//2+ell
            np.testing.assert_array_equal(b[:,il],a[:,ih])
    assert not np.array_equal(a[:,:b.shape[1]],b)


def fixture(folder,L=32,*,large_alms=None):
    m=api();folder.mkdir()
    common={'schema':shared.PRODUCER_SCHEMA,'lmax':L,'nside_out':64,
        'native_window_sha256':'2'*64,'native_receipt_sha256':shared.NATIVE_RECEIPT_SHA,
        'analysis_code_sha256':'3'*64,'healpy_version':'manufactured',
        'dependency_sha256':{'spin2_finite':'4'*64},
        'native_window':'AND_OF_THREE_NATIVE_PMASKS_STRICTLY_GT_0_5',
        'mask_order':'NESTED2048','missing_inside_fixed_window':'REJECT',
        'processing':'MASK_NATIVE_QU_THEN_MAP2ALM_SPIN_THEN_ALM2MAP_SPIN_RING64'}
    results={}
    for seed,p in enumerate(shared.PRODUCTS):
        a=alms(L,seed) if large_alms is None else m.restrict_alms(large_alms[seed],64,L)
        npz=folder/(p+'.npz');np.savez_compressed(npz,E=a[0],B=a[1])
        low=vector((seed+1)*1e-6);mid=vector(3e-7,4e-7);tail=vector(-2e-7,-4e-7)
        masks={}
        for name,k in [('common',1.),('three_way_intersection',2.)]:
            masks[name]={'total_K_CMB':(low+k*(mid+tail)).tolist(),
                'low_2_to_5_K_CMB':low.tolist(),'mid_6_to_8_K_CMB':(k*mid).tolist(),
                'tail_9_to_L_K_CMB':(k*tail).tolist()}
        d={'total_K_CMB':(mid+tail).tolist(),'low_2_to_5_K_CMB':np.zeros(64).tolist(),
           'mid_6_to_8_K_CMB':mid.tolist(),'tail_9_to_L_K_CMB':tail.tolist()}
        result={'schema':shared.PRODUCER_SCHEMA,'lmax':L,'units':'K_CMB',
            'coefficients_are':'PSEUDO_ALMS_OF_COMMON_WINDOW_TIMES_DELIVERED_QU',
            'masks':masks,'two_mask_difference':d,'beam_applied_again':False,
            'beam_deconvolution':False,'tail_beyond_L':'NOT_BOUNDED','p_value':None,'claim':shared.CLAIM}
        results[p]=result
        record={'contract':dict(common,product=p,source_sha256=shared.SOURCE_SHA[p]),
            'alms_npz_sha256':shared.digest(npz),'result':result}
        (folder/(p+'.json')).write_text(json.dumps(record))
    summary={'schema':shared.PRODUCER_SCHEMA,'status':'PASS_WINDOWED_QU_FINITE_BAND_ACCOUNTING',
        'contract':common,'results':results,'source_receipts':{p:{'sha256':shared.SOURCE_SHA[p]} for p in shared.PRODUCTS},
        'paper_gate':'NOT_READY_TO_SUBMIT','independent_sky_count':1}
    (folder/'summary.json').write_text(json.dumps(summary))
    return folder


def mutate(p,fn):
    a=json.loads(p.read_text());fn(a);p.write_text(json.dumps(a))


def test_complete_single_checkpoint_audit(tmp_path):
    m=api(); f=fixture(tmp_path/'L32');before={p.name:p.read_bytes() for p in f.iterdir()}
    out=m.analyze(f)
    assert out['status']=='PASS_FINITE_BAND_DIAGNOSTICS'
    assert out['cutoff_comparison']['status']=='NOT_RUN_NO_HIGH_DIRECTORY'
    assert len(out['low']['band_budgets'])==9
    assert out['low']['band_budgets']['full']['B']['interference_K_CMB2']<0
    assert out['p_value'] is None and out['infinite_tail_bound']=='NOT_ESTABLISHED'
    assert before=={p.name:p.read_bytes() for p in f.iterdir()}


def test_paired_cutoff_reindex_and_preserve_identity(tmp_path):
    m=api(); aa=[alms(64,i) for i in range(5)]
    lo=fixture(tmp_path/'L32',32,large_alms=aa);hi=fixture(tmp_path/'L64',64,large_alms=aa)
    r=m.analyze(lo,hi)['cutoff_comparison']
    assert r['status']=='RECORDED_MATCHED_FINITE_CUTOFF_CHANGE'
    assert r['products']['full']['overlap_alm_relative_l2']==0
    assert r['products']['full']['overlap_alm_difference_norm_K_CMB']==0
    assert r['products']['full']['added_band_alm_norm_K_CMB']>0
    assert r['convergence_certified'] is False


@pytest.mark.parametrize('field',['native_window_sha256','analysis_code_sha256','healpy_version','dependency_sha256','nside_out'])
def test_cutoff_contract_change_blocked(tmp_path,field):
    m=api();lo=fixture(tmp_path/'lo');hi=fixture(tmp_path/'hi',64)
    # Update all high records consistently to isolate between-run contract check.
    value={'changed':'5'*64} if field=='dependency_sha256' else ('8'*64 if 'sha256' in field else 'different')
    for p in hi.glob('*.json'):
        mutate(p,lambda r:r['contract'].update({field:value}))
    with pytest.raises(ValueError):m.analyze(lo,hi)


@pytest.mark.parametrize('damage',['summary_result','npz','vector_closure','nan','symlink','missing'])
def test_damaged_checkpoint_or_result_blocked(tmp_path,damage):
    m=api();lo=fixture(tmp_path/'lo')
    if damage=='summary_result':mutate(lo/'summary.json',lambda r:r['results']['full'].update(unexpected=True))
    if damage=='npz':
        with (lo/'full.npz').open('ab') as f:f.write(b'x')
    if damage=='vector_closure':
        for p in [lo/'full.json',lo/'summary.json']:
            def change(r):
                res=r['result'] if 'result' in r else r['results']['full']
                res['masks']['common']['total_K_CMB'][0]=1.
            mutate(p,change)
    if damage=='nan':mutate(lo/'full.json',lambda r:r['result'].update(foo=float('nan')))
    if damage=='symlink':
        p=lo/'full.json';p.rename(lo/'original.json');p.symlink_to(lo/'original.json')
    if damage=='missing':(lo/'summary.json').unlink()
    with pytest.raises((ValueError,OSError)):m.analyze(lo)


def test_cli_no_overwrite_and_help(tmp_path):
    m=api();lo=fixture(tmp_path/'lo');p=tmp_path/'report.json'
    assert m.main(['--band-dir',str(lo),'--out',str(p)])==0
    b=p.read_bytes()
    assert m.main(['--band-dir',str(lo),'--out',str(p)])==2
    assert p.read_bytes()==b
    r=subprocess.run([sys.executable,m.__file__,'--help'],capture_output=True,text=True,cwd=tmp_path)
    assert r.returncode==0 and '--higher-band-dir' in r.stdout


def test_cutoffs_must_increase(tmp_path):
    m=api();a=fixture(tmp_path/'a',32);b=fixture(tmp_path/'b',16)
    with pytest.raises(ValueError,match='CUTOFF_MUST_INCREASE'):m.analyze(a,b)


def test_overlap_change_is_detected_not_called_new_band(tmp_path):
    m=api();aa=[alms(64,i) for i in range(5)]
    lo=fixture(tmp_path/'lo',32,large_alms=aa);hi=fixture(tmp_path/'hi',64,large_alms=aa)
    p=hi/'full.npz'
    with np.load(p) as fd:a=np.stack((fd['E'],fd['B']))
    a[0,4]+=1e-8
    np.savez_compressed(p,E=a[0],B=a[1])
    mutate(hi/'full.json',lambda r:r.update(alms_npz_sha256=shared.digest(p)))
    result=m.analyze(lo,hi)['cutoff_comparison']['products']['full']
    assert result['overlap_alm_difference_norm_K_CMB']==pytest.approx(1e-8)
    assert result['overlap_alm_relative_l2']>0


def test_equal_scalar_norms_but_rotated_contrast_are_distinguished(tmp_path):
    m=api();lo=fixture(tmp_path/'lo');hi=fixture(tmp_path/'hi',64)
    def rotate_result(r):
        for part in list(r['masks'].values())+[r['two_mask_difference']]:
            for key in m.FIELDS:
                a=np.array(part[key]);a[5],a[6]=-a[6],a[5];part[key]=a.tolist()
    mutate(hi/'full.json',lambda r:rotate_result(r['result']))
    mutate(hi/'summary.json',lambda r:rotate_result(r['results']['full']))
    result=m.analyze(lo,hi)
    old=result['low']['band_budgets']['full']['B']['total_energy_K_CMB2']
    new=result['high']['band_budgets']['full']['B']['total_energy_K_CMB2']
    assert old==pytest.approx(new,rel=1e-13,abs=0.)
    change=result['cutoff_comparison']['projected_contrast_changes']['full']
    assert change['total_difference_norm_K_CMB']==pytest.approx(np.sqrt(2)*1e-7)
