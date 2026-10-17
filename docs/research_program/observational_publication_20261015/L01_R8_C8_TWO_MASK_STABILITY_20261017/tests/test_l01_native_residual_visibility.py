"""Manufactured finite operators and native-report protocol, never real Planck."""
import json
from pathlib import Path
import subprocess
import sys
import numpy as np
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import l01_native_residual_projection as native
import l01_native_residual_visibility as mod


def test_minimum_energy_discards_large_exact_kernel_component():
    d=np.array([[1.,0,0],[0,2.,0]])
    z=np.array([1.,1.,10000.]); e=d@z
    r=mod.retained_residual_energy(d@d.T,e,np.linalg.norm(z))
    assert r['retained_input_energy_K_CMB2']==pytest.approx(2.)
    assert r['retained_input_energy_fraction']==pytest.approx(2/100000002)
    assert r['remaining_input_energy_K_CMB2']==pytest.approx(100000000)
    assert r['factor_product_for_retained_target']==pytest.approx(r['bound_over_measured'])


@pytest.mark.parametrize('scale',[1.,1e-6,1e-100,1e100])
def test_independent_rectangular_operator_pinv_oracle(scale):
    rng=np.random.default_rng(9);d=rng.normal(size=(5,12));z=scale*rng.normal(size=12)
    e=d@z; visible=np.linalg.pinv(d)@e
    r=mod.retained_residual_energy(d@d.T,e,np.linalg.norm(z))
    assert r['retained_rank_numeric']==5
    assert r['retained_input_energy_K_CMB2']==pytest.approx(visible@visible,rel=1e-12,abs=0)
    assert r['retained_input_energy_fraction']==pytest.approx((visible@visible)/(z@z),rel=1e-12)
    assert r['unresolved_target_fraction']<2e-14


def test_rank_deficiency_and_exact_zero_kernel():
    d=np.array([[1.,2.,0,0],[2.,4.,0,0]])
    z=np.array([3.,-1.,100.,-100.]);e=d@z
    r=mod.retained_residual_energy(d@d.T,e,np.linalg.norm(z))
    assert r['retained_rank_numeric']==1
    assert r['retained_input_energy_K_CMB2']==pytest.approx(.2)
    assert r['unresolved_target_norm_K_CMB']<1e-14


def test_degenerate_rotations_do_not_change_energy():
    h=np.diag([4.,4.,1.,0.]);e=np.array([1.,2.,3.,0.]);R=10.
    a=mod.retained_residual_energy(h,e,R)
    q,_=np.linalg.qr(np.random.default_rng(25).normal(size=(4,4)))
    b=mod.retained_residual_energy(q@h@q.T,q@e,R)
    for key in ('retained_input_energy_K_CMB2','retained_input_energy_fraction','bound_over_measured'):
        assert a[key]==pytest.approx(b[key],rel=2e-13)


def test_truncation_not_falsely_called_entire_kernel():
    h=np.diag([1.,1e-20]);e=np.array([1.,1e-10])
    r=mod.retained_residual_energy(h,e,np.sqrt(2.))
    assert r['retained_rank_numeric']==1
    assert r['retained_input_energy_fraction']==pytest.approx(.5)
    assert r['unresolved_target_norm_K_CMB']==pytest.approx(1e-10)
    assert r['remaining_energy_includes_kernel_and_discarded_positive_modes'] is True
    assert r['formal_rank_or_interval_certificate'] is False


def test_e_and_b_selected_input_projections_not_additive():
    d=np.array([[1.,0],[1.,0]]);e=np.ones(2)
    allr=mod.retained_residual_energy(d@d.T,e,2.)
    er=mod.retained_residual_energy(np.ones((1,1)),e[:1],2.)
    assert allr['retained_input_energy_K_CMB2']==pytest.approx(1.)
    assert 2*er['retained_input_energy_K_CMB2']>allr['retained_input_energy_K_CMB2']


@pytest.mark.parametrize('R',[0.,5.])
def test_zero_operator_stays_defined(R):
    r=mod.retained_residual_energy(np.zeros((2,2)),np.zeros(2),R)
    assert r['retained_rank_numeric']==0
    assert r['retained_input_energy_K_CMB2']==0
    assert r['bound_over_measured'] is None
    assert r['remaining_input_energy_K_CMB2']==R*R


@pytest.mark.parametrize('bad',['nan','complex','negative','shape','nonsym','negativeR','above_bound','above_energy'])
def test_invalid_subspace_inputs_are_blocked(bad):
    h=np.eye(2);e=np.ones(2);R=5.
    if bad=='nan':e[0]=np.nan
    if bad=='complex':e=e.astype(complex)
    if bad=='negative':h[0,0]=-1.
    if bad=='shape':h=np.eye(3)
    if bad=='nonsym':h[0,1]=.2
    if bad=='negativeR':R=-1.
    if bad=='above_bound':R=.01
    if bad=='above_energy':h=np.diag([1.,.01]);e=np.array([0.,1.]);R=2.
    with pytest.raises(ValueError):mod.retained_residual_energy(h,e,R)


def make_report():
    rng=np.random.default_rng(42);A=rng.normal(size=(256,64));omega=.05
    c=np.ones(256,dtype=bool)
    t=c.copy(); t[90:128]=False;t[218:256]=False
    synth=1e-6*rng.normal(size=256);res=1e-6*rng.normal(size=256)
    data=np.column_stack((synth+res,synth,res))
    def solve(mask):
        gram=omega*A[mask].T@A[mask];b=omega*A[mask].T@data[mask]
        return {'gram':gram,'rhs':b,'coefficients':np.linalg.solve(gram,b),
                'selected_pixels':int(mask.sum()//2)}
    sc,st=solve(c),solve(t)
    result=native.compare_states(sc,st,np.sqrt(omega)*np.linalg.norm(res),mod.groups())
    result.update(schema=native.SCHEMA,status='PASS_NATIVE_PIXEL_RESIDUAL_ACCOUNTING',
        nside=2048,product='full',saved_lmax=128,paper_gate='NOT_READY_TO_SUBMIT',p_value=None,
        region='SAME_UNION_OF_NSIDE64_NESTED_CELLS_SAMPLED_AT_NATIVE_NSIDE',
        gram_uses='M_REGION_ONLY_NOT_M_TIMES_SOURCE_WINDOW',
        source_uses='ORIGINAL_NATIVE_W_TIMES_DELIVERED_QU',
        reconstructed_field_rewindowed=False,forward_SHT_rerun=False,beam_applied_again=False,
        estimator_relation='NEW_NATIVE_PIXEL_COMPARATOR_NOT_REPLACEMENT_OF_ARCHIVED_NSIDE64',
        code_sha256=mod.PRODUCER_SHA256,
        source={'sha256':mod.SOURCE_SHA['full']},
        checkpoint={'contract':{'lmax':128,'native_receipt_sha256':mod.NATIVE_RECEIPT_SHA,
                    'native_window_sha256':'a'*64}},native_window_sha256='a'*64,
        solver_states={'common':sc,'three_way_intersection':st},synthetic_fixture=True)
    return json.loads(json.dumps(result,default=lambda x:x.tolist()))


def test_deletion_forcing_matches_direct_removed_rows():
    A=np.array([[1.,0],[0,1],[1,1],[1,-1.]])
    f=np.array([2.,3.,-1.,5.]);syn=f*.9
    data=np.column_stack((f,syn,f-syn))
    gc=A.T@A;gt=A[:3].T@A[:3];bc=A.T@data;bt=A[:3].T@data[:3]
    yc=np.linalg.solve(gc,bc);yt=np.linalg.solve(gt,bt)
    c={'gram':gc,'rhs':bc,'coefficients':yc};t={'gram':gt,'rhs':bt,'coefficients':yt}
    r=mod.deletion_forcing(c,t)
    np.testing.assert_allclose(r['predicted_contrast_K_CMB'],yt-yc,rtol=1e-12,atol=1e-15)
    oracle=A[3:].T@(data[3:]-A[3:]@yc)
    np.testing.assert_allclose(r['removed_region_fit_residual_moment_K_CMB'],oracle)


def test_complete_report_real_cli_and_preserved_inputs(tmp_path):
    p=tmp_path/'native.json';r=make_report();p.write_text(json.dumps(r));before=p.read_bytes()
    out=tmp_path/'visibility.json'
    cmd=[sys.executable,mod.__file__,'--native-report',str(p),'--out',str(out)]
    run=subprocess.run(cmd,capture_output=True,text=True)
    assert run.returncode==0,run.stderr
    got=json.loads(out.read_text())
    assert got['status']=='PASS_NATIVE_RESIDUAL_VISIBILITY_ACCOUNTING'
    assert got['native_maps_replayed'] is False and got['new_sky_information'] is False
    assert got['input_energy_groups_are_additive'] is False
    assert got['components']['all']['retained_rank_numeric']==64
    assert 0<got['components']['all']['retained_input_energy_fraction']<1
    # Independent rectangular pixel-space oracle for native fixture.
    assert got['deletion_shell']['identity_relative_to_parent']<1e-12
    assert p.read_bytes()==before
    again=subprocess.run(cmd,capture_output=True,text=True)
    assert again.returncode==2 and 'OUTPUT_EXISTS' in again.stderr
    assert p.read_bytes()==before


@pytest.mark.parametrize('damage',['source','schema','window','code','lmax','gram','rhs','summary','contrast','paper','rewindow','dimension','counts'])
def test_report_corruption_is_rejected(damage):
    r=make_report()
    if damage=='source':r['source']['sha256']='b'*64
    if damage=='schema':r['schema']='other'
    if damage=='window':r['native_window_sha256']='b'*64
    if damage=='code':r['code_sha256']='b'*64
    if damage=='lmax':r['saved_lmax']=32
    if damage=='gram':r['solver_states']['common']['gram'][0][0]=-1.
    if damage=='rhs':r['solver_states']['common']['rhs'][0][0]+=.1
    if damage=='summary':r['components']['B']['direct_norm_K_CMB']*=2
    if damage=='contrast':r['contrast_residual_K_CMB'][0]+=1e-4
    if damage=='paper':r['paper_gate']='READY'
    if damage=='rewindow':r['reconstructed_field_rewindowed']=True
    if damage=='dimension':r['solver_states']['common']['gram']=[[1.]]
    if damage=='counts':r['solver_states']['three_way_intersection']['selected_pixels']=100000000
    with pytest.raises(ValueError):mod.analyze_report(r)


@pytest.mark.parametrize('text',['{"a":1,"a":2}','{"a":NaN}','{"a":1e999}'])
def test_json_ambiguity_or_nonfinite_rejected(tmp_path,text):
    p=tmp_path/'r.json';p.write_text(text)
    with pytest.raises(ValueError):mod.read_report(p)


def test_json_byte_difference_preserves_semantic_result(tmp_path):
    r=make_report();a=tmp_path/'a.json';b=tmp_path/'b.json'
    a.write_text(json.dumps(r));b.write_text(json.dumps(r,sort_keys=True,indent=2))
    x,hx=mod.read_report(a);y,hy=mod.read_report(b)
    assert hx!=hy and x==y
    assert mod.analyze_report(x)==mod.analyze_report(y)


def test_symlink_rejected_and_help_standalone(tmp_path):
    p=tmp_path/'real';p.write_text('{}');q=tmp_path/'link';q.symlink_to(p)
    with pytest.raises(ValueError):mod.read_report(q)
    run=subprocess.run([sys.executable,mod.__file__,'--help'],cwd=tmp_path,capture_output=True,text=True)
    assert run.returncode==0 and '--native-report' in run.stdout


def test_original_native_source_is_exact_expected_dependency():
    assert mod.digest(native.__file__)==mod.PRODUCER_SHA256


def test_loose_bound_can_come_only_from_small_gain_not_kernel():
    d=np.diag([1.,1e-3]);z=np.array([0.,1.]);e=d@z
    r=mod.retained_residual_energy(d@d.T,e,np.linalg.norm(z))
    assert r['retained_input_energy_fraction']==pytest.approx(1.)
    assert r['input_norm_dilution_factor']==pytest.approx(1.)
    assert r['spectral_orientation_factor']==pytest.approx(1000.)
    assert r['bound_over_measured']==pytest.approx(1000.)
