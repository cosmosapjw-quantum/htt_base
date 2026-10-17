"""Manufactured tests; no native FITS or physical Planck null is asserted."""
import importlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
import l01_cutoff_band_diagnostics as base
import l01_split_checkpoint_spectra as shared


def api():
    return importlib.import_module('l01_target_transition')


def test_transition_feature_is_available():
    assert importlib.util.find_spec('l01_target_transition') is not None


def v(x=0.,y=0.):
    z=np.zeros(64);z[5:7]=[x,y];return z


@pytest.mark.parametrize('scale',[1.,1e-6,1e-100,1e100])
def test_radial_transverse_energy_exact_example(scale):
    r=api().transition(v(3,4)*scale,v(4,2)*scale)['B']
    assert r['radial_fraction']==pytest.approx(-.2)
    assert r['transverse_fraction']==pytest.approx(.4)
    assert r['relative_increment_target']==pytest.approx(np.sqrt(.2))
    assert r['energy_after_over_before']==pytest.approx(.8)
    assert r['coefficient_angle_degrees']==pytest.approx(np.degrees(np.arctan(.5)))
    assert r['energy_identity_relative']<1e-14


@pytest.mark.parametrize('q',[.01,.16104676798085926,.6,.99])
def test_sharp_angle_witness(q):
    new=v(1-q*q,q*np.sqrt(1-q*q))
    r=api().transition(v(1),new)['B']
    assert r['relative_increment_target']==pytest.approx(q)
    assert r['coefficient_angle_degrees']==pytest.approx(np.degrees(np.arcsin(q)))
    assert r['angle_upper_bound_degrees']==pytest.approx(r['coefficient_angle_degrees'])


def test_equal_norm_rotation_not_misreported_as_small():
    r=api().transition(v(1),v(0,1))['B']
    assert r['energy_after_over_before']==pytest.approx(1)
    assert r['relative_increment_target']==pytest.approx(np.sqrt(2))
    assert r['coefficient_angle_degrees']==pytest.approx(90)
    assert r['angle_upper_bound_degrees'] is None


@pytest.mark.parametrize('scale',[.8,1.,1.2,-1.])
def test_parallel_shrink_grow_flip(scale):
    r=api().transition(v(1),v(scale))['B']
    assert r['coefficient_angle_degrees']==pytest.approx(180 if scale<0 else 0)
    assert r['transverse_fraction']<1e-14
    assert r['energy_after_over_before']==pytest.approx(scale**2)


def test_zero_base_and_zero_destination_are_explicit():
    m=api();a=m.transition(v(),v(1))['B'];b=m.transition(v(1),v())['B']
    assert a['relative_increment_target'] is None
    assert a['coefficient_angle_degrees'] is None
    assert b['relative_increment_target']==1
    assert b['coefficient_angle_degrees'] is None
    assert b['energy_after_over_before']==0


@pytest.mark.parametrize('damage',['nan','shape','complex'])
def test_invalid_vector_fails(damage):
    a=v(1)
    if damage=='nan':a[0]=np.nan
    elif damage=='shape':a=a[:-1]
    else:a=a.astype(complex)
    with pytest.raises(ValueError):api().transition(a,v(1))


def test_orthogonal_coordinate_change_preserves_all_geometry():
    rng=np.random.default_rng(19);a=rng.normal(size=64);b=rng.normal(size=64)
    q,_=np.linalg.qr(rng.normal(size=(64,64)))
    r=api().transition(a,b)['all'];s=api().transition(q@a,q@b)['all']
    for k in ['relative_increment_target','radial_fraction','transverse_fraction','coefficient_angle_degrees','energy_after_over_before']:
        assert r[k]==pytest.approx(s[k],rel=2e-13,abs=1e-14)


def fixture(folder,L,delta):
    folder.mkdir()
    common={'schema':shared.PRODUCER_SCHEMA,'lmax':L,'nside_out':64,
        'native_window_sha256':'2'*64,'native_receipt_sha256':shared.NATIVE_RECEIPT_SHA,
        'analysis_code_sha256':'3'*64,'healpy_version':'manufactured',
        'dependency_sha256':{'spin2_finite':'4'*64},
        'native_window':'AND_OF_THREE_NATIVE_PMASKS_STRICTLY_GT_0_5',
        'mask_order':'NESTED2048','missing_inside_fixed_window':'REJECT',
        'processing':'MASK_NATIVE_QU_THEN_MAP2ALM_SPIN_THEN_ALM2MAP_SPIN_RING64'}
    results={}
    for i,p in enumerate(shared.PRODUCTS):
        # Exact, tiny alm files; vectors here manufacture the archive protocol,
        # not a physical map-to-vector correspondence (unchanged loader boundary).
        a=np.zeros((2,(L+1)*(L+2)//2),complex);a[0,2]=(i+1)*1e-6
        path=folder/(p+'.npz');np.savez_compressed(path,E=a[0],B=a[1])
        low=v(1e-6);mid=v(3e-7);tail=v(1e-7)
        masks={}
        for name,change in [('common',v()),('three_way_intersection',delta)]:
            masks[name]=dict(zip(base.FIELDS,[(low+mid+tail+change).tolist(),low.tolist(),mid.tolist(),(tail+change).tolist()]))
        difference=dict(zip(base.FIELDS,[delta.tolist(),v().tolist(),v().tolist(),delta.tolist()]))
        result={'schema':shared.PRODUCER_SCHEMA,'lmax':L,'units':'K_CMB','claim':shared.CLAIM,
                'coefficients_are':'PSEUDO_ALMS_OF_COMMON_WINDOW_TIMES_DELIVERED_QU',
                'masks':masks,'two_mask_difference':difference,
                'beam_applied_again':False,'beam_deconvolution':False,'tail_beyond_L':'NOT_BOUNDED','p_value':None}
        results[p]=result
        record={'contract':dict(common,product=p,source_sha256=shared.SOURCE_SHA[p]),
                'alms_npz_sha256':shared.digest(path),'result':result}
        (folder/(p+'.json')).write_text(json.dumps(record))
    summary={'schema':shared.PRODUCER_SCHEMA,'status':'PASS_WINDOWED_QU_FINITE_BAND_ACCOUNTING',
             'contract':common,'results':results,'source_receipts':{p:{'sha256':shared.SOURCE_SHA[p]} for p in shared.PRODUCTS},
             'independent_sky_count':1,'paper_gate':'NOT_READY_TO_SUBMIT'}
    (folder/'summary.json').write_text(json.dumps(summary));return folder


def test_two_checkpoint_cli_reports_actual_after_values(tmp_path):
    lo=fixture(tmp_path/'lo',32,v(3e-7,4e-7));hi=fixture(tmp_path/'hi',64,v(4e-7,2e-7))
    out=tmp_path/'out.json';m=api()
    snapshot={str(p):p.read_bytes() for root in [lo,hi] for p in root.iterdir()}
    cmd=[sys.executable,m.__file__,'--band-dirs',str(lo),str(hi),'--out',str(out)]
    done=subprocess.run(cmd,capture_output=True,text=True,timeout=30)
    assert done.returncode==0,done.stderr
    r=json.loads(out.read_text());full=r['transitions'][0]['subjects']['full']['B']
    assert full['radial_fraction']==pytest.approx(-.2)
    assert full['energy_after_over_before']==pytest.approx(.8)
    assert r['convergence_certified'] is False
    assert r['empirical_successive_steps']['status']=='NOT_EVALUATED_REQUIRES_THREE_CUTOFFS'
    assert snapshot=={str(p):p.read_bytes() for root in [lo,hi] for p in root.iterdir()}
    assert subprocess.run(cmd,capture_output=True).returncode==2


def test_three_cutoffs_empirical_ratio_is_not_a_bound(tmp_path):
    folders=[fixture(tmp_path/str(L),L,v(x*1e-6)) for L,x in [(32,1),(64,1.2),(128,1.3)]]
    r=api().analyze(folders);emp=r['empirical_successive_steps']['subjects']['full']['B']
    assert emp['second_step_over_first']==pytest.approx(.5)
    assert emp['step_alignment']==pytest.approx(1)
    assert emp['is_future_contraction_bound'] is False
    assert r['infinite_tail_bound']=='NOT_ESTABLISHED'


def test_three_cutoffs_zero_first_increment_is_not_zero_error(tmp_path):
    folders=[fixture(tmp_path/str(L),L,v(x*1e-6)) for L,x in [(32,1),(64,1),(128,2)]]
    emp=api().analyze(folders)['empirical_successive_steps']['subjects']['full']['B']
    assert emp['second_step_over_first'] is None
    assert emp['status']=='ZERO_FIRST_INCREMENT_RATIO_UNDEFINED'
    assert emp['second_step_norm_K_CMB']>0


@pytest.mark.parametrize('mutate',['window','lmax','bytes'])
def test_existing_identity_contract_not_relaxed(tmp_path,mutate):
    lo=fixture(tmp_path/'lo',32,v(1e-6));hi=fixture(tmp_path/'hi',64,v(1.2e-6))
    if mutate=='bytes':
        with (hi/'full.npz').open('ab') as f:f.write(b'X')
    elif mutate=='lmax':
        hi=fixture(tmp_path/'wrong',16,v(1.2e-6))
    else:
        for p in hi.glob('*.json'):
            r=json.loads(p.read_text());r['contract']['native_window_sha256']='7'*64;p.write_text(json.dumps(r))
    with pytest.raises(ValueError):api().analyze([lo,hi])


def test_no_new_data_is_needed_for_cli_help(tmp_path):
    m=api();r=subprocess.run([sys.executable,m.__file__,'--help'],cwd=tmp_path,capture_output=True,text=True)
    assert r.returncode==0 and '--band-dirs' in r.stdout


def test_two_to_three_runs_required():
    with pytest.raises(ValueError,match='TWO_OR_THREE'):api().analyze([])
