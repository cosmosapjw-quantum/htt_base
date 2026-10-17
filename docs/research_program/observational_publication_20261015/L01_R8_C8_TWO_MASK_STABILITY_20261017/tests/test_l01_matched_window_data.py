"""Finite operators and source-report fixtures, not native Planck data."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import l01_matched_window_data as app
import l01_windowed_low_injections as injection


def test_matched_recovers_known_source_instead_of_zero_filled_response():
    a=np.array([[1,0],[0,1],[1,1],[1,-1]],float)
    w=np.array([True,True,False,True])
    masks={'common':np.ones(4,bool), 'three_way_intersection':np.array([True,True,False,False])}
    c=np.array([2.,-3.]); f=np.where(w,a@c,0.)
    g={k:a[m].T@a[m] for k,m in masks.items()}
    h={k:a[m & ~w].T@a[m & ~w] for k,m in masks.items()}
    rhs={k:a[m].T@f[m] for k,m in masks.items()}
    out=app.matched_fit(g,h,rhs)
    for k in masks:
        np.testing.assert_allclose(out['matched_coefficients'][k],c,rtol=1e-13,atol=1e-13)

import copy
import json
import subprocess
import pytest
import l01_native_residual_visibility as previous


def problem(n=5,seed=17):
    rng=np.random.default_rng(seed)
    a=rng.normal(size=(8*n,n))
    masks={'common':np.ones(len(a),bool),'three_way_intersection':np.arange(len(a))<6*n}
    w=(np.arange(len(a))%4!=1)
    x=rng.normal(size=len(a))
    g={k:a[m].T@a[m] for k,m in masks.items()}
    h={k:a[m & ~w].T@a[m & ~w] for k,m in masks.items()}
    rhs={k:a[m].T@np.where(w,x,0)[m] for k,m in masks.items()}
    return a,masks,w,x,g,h,rhs


@pytest.mark.parametrize('n',[2,5,16,64])
def test_saved_moments_equal_direct_selected_pixel_lstsq(n):
    a,masks,w,x,g,h,rhs=problem(n)
    result=app.matched_fit(g,h,rhs)
    for k,m in masks.items():
        direct=np.linalg.lstsq(a[m & w],x[m & w],rcond=None)[0]
        np.testing.assert_allclose(result['matched_coefficients'][k],direct,rtol=3e-12,atol=3e-14)
    old=result['original_contrast_K_CMB']
    np.testing.assert_allclose(old,np.array(result['response_term_K_CMB'])+result['matched_term_in_old_coordinates_K_CMB'],rtol=3e-12,atol=3e-14)


def test_rational_symmetric_decomposition_oracle():
    a=np.array([[1,0],[0,1],[1,1],[1,-1],[2,1],[1,2]],float)
    mc=np.ones(6,bool);mt=np.array([1,1,1,1,0,0],bool);w=np.array([1,0,1,1,1,0],bool)
    x=np.array([2,11,4,1,7,-3],float); masks=dict(zip(injection.MASKS,(mc,mt)))
    g={k:a[m].T@a[m] for k,m in masks.items()}
    h={k:a[m & ~w].T@a[m & ~w] for k,m in masks.items()}
    b={k:a[m].T@np.where(w,x,0)[m] for k,m in masks.items()}
    r=app.matched_fit(g,h,b)
    np.testing.assert_allclose(r['original_contrast_K_CMB'],[-1/3,13/12],rtol=2e-14)
    np.testing.assert_allclose(r['matched_contrast_K_CMB'],[-10/51,-5/34],rtol=2e-14)
    np.testing.assert_allclose(r['response_term_K_CMB'],[-107/816,77/68],rtol=2e-14)
    np.testing.assert_allclose(r['matched_term_in_old_coordinates_K_CMB'],[-55/272,-5/102],rtol=2e-14)


@pytest.mark.parametrize('scale',[1e-100,1e-6,1.,1e100])
def test_scale_covariance_of_vectors_and_energies(scale):
    *_,g,h,b=problem()
    r=app.matched_fit(g,h,b);rs=app.matched_fit(g,h,{k:v*scale for k,v in b.items()})
    np.testing.assert_allclose(np.array(rs['matched_contrast_K_CMB'])/scale,r['matched_contrast_K_CMB'],rtol=2e-12,atol=2e-14)
    q=rs['components']['all']; base=r['components']['all']
    assert q['original_energy_K_CMB2']/scale**2==pytest.approx(base['original_energy_K_CMB2'],rel=3e-12)
    assert q['interference_K_CMB2']/scale**2==pytest.approx(base['interference_K_CMB2'],rel=3e-12)


def test_full_window_changes_no_estimator():
    *_,g,h,b=problem()
    h={k:np.zeros_like(v) for k,v in g.items()}
    r=app.matched_fit(g,h,b)
    np.testing.assert_allclose(r['matched_contrast_K_CMB'],r['original_contrast_K_CMB'],atol=1e-14)
    np.testing.assert_array_equal(r['response_term_K_CMB'],np.zeros(5))


def test_identical_regions_give_zero_contrast():
    *_,g,h,b=problem()
    for d in (g,h,b):d['three_way_intersection']=d['common'].copy()
    r=app.matched_fit(g,h,b)
    np.testing.assert_array_equal(r['matched_contrast_K_CMB'],np.zeros(5))
    assert r['components']['all']['matched_over_original_norm'] is None


def test_omitted_orthogonal_full_domain_mode_not_purified():
    a,masks,w,x,g,h,b=problem()
    hidden=x-a@np.linalg.lstsq(a,x,rcond=None)[0]
    np.testing.assert_allclose(a.T@hidden,0,atol=2e-14)
    c=np.arange(5.)
    data=a@c+hidden
    rhs={k:a[m].T@np.where(w,data,0)[m] for k,m in masks.items()}
    result=app.matched_fit(g,h,rhs)
    assert np.linalg.norm(result['matched_contrast_K_CMB'])>1e-3
    assert np.linalg.norm(result['matched_coefficients']['common']-c)>1e-3


@pytest.mark.parametrize('failure',['rhs_nan','rhs_matrix','rhs_complex','holes','singular'])
def test_no_silent_rank_or_input_fallback(failure):
    *_,g,h,b=problem()
    if failure=='rhs_nan': b['common'][0]=np.nan
    if failure=='rhs_matrix':b['common']=b['common'][:,None]
    if failure=='rhs_complex':b['common']=b['common'].astype(complex)
    if failure=='holes':h['common']=2*g['common']
    if failure=='singular':h={k:v.copy() for k,v in g.items()}
    with pytest.raises(ValueError):app.matched_fit(g,h,b)


def fixture_reports(tmp_path,reconstruction_seed=19):
    rng=np.random.default_rng(31);n=64; pixels=240
    a=rng.normal(size=(2*pixels,n))
    common=np.ones(pixels,bool);inner=np.arange(pixels)<180
    w=np.arange(pixels)%4!=1
    masks=dict(zip(injection.MASKS,(common,inner)))
    rows={k:np.r_[m,m] for k,m in masks.items()};wr=np.r_[w,w]
    data=rng.normal(size=2*pixels)*1e-6
    raw=np.where(wr,data,0.)
    recon=np.random.default_rng(reconstruction_seed).normal(size=2*pixels)*1e-6
    cols=np.column_stack((raw,recon,raw-recon))
    area=4*np.pi/(12*2048**2)
    g={k:area*a[m].T@a[m] for k,m in rows.items()}
    holes={k:area*a[m & ~wr].T@a[m & ~wr] for k,m in rows.items()}
    states={}
    for k,m in masks.items():
        b=area*a[rows[k]].T@cols[rows[k]]
        states[k]={'gram':g[k].tolist(),'rhs':b.tolist(),
            'coefficients':np.linalg.solve(g[k],b).tolist(),'selected_pixels':int(m.sum())}
    R=float(np.sqrt(area)*np.linalg.norm((raw-recon)[rows['common']]))
    native=previous.native.compare_states(states['common'],states['three_way_intersection'],R,previous.groups())
    native.update(schema=previous.native.SCHEMA,status='PASS_NATIVE_PIXEL_RESIDUAL_ACCOUNTING',
        product='full',nside=2048,saved_lmax=128,paper_gate='NOT_READY_TO_SUBMIT',p_value=None,
        region='SAME_UNION_OF_NSIDE64_NESTED_CELLS_SAMPLED_AT_NATIVE_NSIDE',
        gram_uses='M_REGION_ONLY_NOT_M_TIMES_SOURCE_WINDOW',source_uses='ORIGINAL_NATIVE_W_TIMES_DELIVERED_QU',
        reconstructed_field_rewindowed=False,forward_SHT_rerun=False,beam_applied_again=False,
        estimator_relation='NEW_NATIVE_PIXEL_COMPARATOR_NOT_REPLACEMENT_OF_ARCHIVED_NSIDE64',
        code_sha256=previous.PRODUCER_SHA256,source={'sha256':previous.SOURCE_SHA['full']},
        native_window_sha256='7'*64,solver_states=states,
        checkpoint={'contract':{'native_receipt_sha256':previous.NATIVE_RECEIPT_SHA,
            'native_window_sha256':'7'*64,'lmax':128,'analysis_code_sha256':'a'*64}})
    path=tmp_path/'native.json';path.write_text(json.dumps(native))
    response=injection.response_from_holes(g,holes)
    probe={'schema':injection.SCHEMA,'status':'PASS_FINITE_LOW_SOURCE_WINDOW_RESPONSE',
        'input_ells':[2,3,4,5],'output_ells':[2,3,4,5],'nside':2048,
        'source_model':'INJECTED_DELIVERED_LOW_BAND_FIELD_A_C_NOT_MEASURED_COSMIC_COEFFICIENTS',
        'responses':{k:v.tolist() for k,v in response['responses'].items()},
        'two_mask_difference':response['difference'].tolist(),
        'hole_moments':{k:v.tolist() for k,v in holes.items()},'matched_controls':response['matched_controls'],
        'code_sha256':app.INJECTION_SHA256,'source_window_sha256':'7'*64,
        'native_receipt_sha256':previous.NATIVE_RECEIPT_SHA,'native_report_sha256':previous.digest(path),
        'reused_code_sha256':{'l01_native_residual_projection':previous.PRODUCER_SHA256,
            'l01_native_residual_visibility':app.VISIBILITY_SHA256,'l01_smica_processed_bands':'a'*64},
        'original_estimator_changed':False,'matched_control_applied_to_observed_data':False,
        'native_observed_QU_reread':False,'native_SHT_run':False,'noise_covariance':None,'p_value':None,
        'infinite_tail_bound':'NOT_ESTABLISHED','paper_gate':'NOT_READY_TO_SUBMIT',
        'scan':{'total_native_pixels':12*2048**2,'native_pixel_area':area,
            'source_pixels_or_estimator_changed':False,
            'original_fit_selected_pixels':{k:int(m.sum()) for k,m in masks.items()},
            'excluded_source_pixels_in_fit_region':{k:int((m & ~w).sum()) for k,m in masks.items()},
            'design_evaluated_spatial_pixels':int((common & ~w).sum())}}
    ip=tmp_path/'injection.json';ip.write_text(json.dumps(probe))
    return native,probe,path,ip,a,masks,w,data


def test_full_report_pipeline_matches_direct_pixel_fit(tmp_path):
    native,probe,_,_,a,masks,w,data=fixture_reports(tmp_path)
    r=app.analyze_reports(native,probe)
    wr=np.r_[w,w]
    for k,m in masks.items():
        select=np.r_[m,m]&wr
        oracle=np.linalg.lstsq(a[select],data[select],rcond=None)[0]
        np.testing.assert_allclose(r['fit_metadata'][k]['matched_coefficients_K_CMB'],oracle,rtol=2e-12,atol=1e-20)
    assert r['matched_control_applied_to_raw_moments'] is True
    assert r['physical_sky_identification'] is False and r['p_value'] is None
    assert r['reconstruction_and_residual_columns_reinterpreted'] is False


def test_reconstruction_column_changes_do_not_change_raw_fit(tmp_path):
    first=tmp_path/'a';second=tmp_path/'b';first.mkdir();second.mkdir()
    n1,p1,*_=fixture_reports(first,reconstruction_seed=19)
    n2,p2,*_=fixture_reports(second,reconstruction_seed=71)
    a=app.analyze_reports(n1,p1);b=app.analyze_reports(n2,p2)
    assert a['fit_metadata']==b['fit_metadata']
    assert a['components']==b['components']


@pytest.mark.parametrize('bad',['native_source','window','code','dependency','counts','response','difference','control','area','scope'])
def test_report_binding_rejects_specific_mismatch(tmp_path,bad):
    n,p,*_=fixture_reports(tmp_path)
    if bad=='native_source':n['source']['sha256']='1'*64
    if bad=='window':p['source_window_sha256']='1'*64
    if bad=='code':p['code_sha256']='1'*64
    if bad=='dependency':p['reused_code_sha256']['l01_native_residual_visibility']='1'*64
    if bad=='counts':p['scan']['original_fit_selected_pixels']['common']+=1
    if bad=='response':p['responses']['common'][0][0]+=.01
    if bad=='difference':p['two_mask_difference'][0][0]+=.01
    if bad=='control':p['matched_controls']['common']['condition']*=2
    if bad=='area':p['scan']['native_pixel_area']*=2
    if bad=='scope':p['matched_control_applied_to_observed_data']=True
    with pytest.raises(ValueError):app.analyze_reports(n,p)


def test_cli_no_clobber_and_no_inputs_modified(tmp_path):
    _,_,n,p,*_=fixture_reports(tmp_path)
    before=[n.read_bytes(),p.read_bytes()];out=tmp_path/'new.json'
    args=['--native-report',str(n),'--injection-report',str(p),'--out',str(out)]
    assert app.main(args)==0
    old=out.read_bytes();assert app.main(args)==2;assert out.read_bytes()==old
    assert before==[n.read_bytes(),p.read_bytes()]
    report=json.loads(old)
    assert report['input_evidence']['native_link_relation']=='BYTE_IDENTICAL_TO_LINKED_REPORT'


def test_json_byte_and_canonical_identity_are_separate(tmp_path,capsys):
    native,probe,n,p,*_=fixture_reports(tmp_path)
    reformatted=tmp_path/'formatted.json'
    reformatted.write_text(json.dumps(native,sort_keys=True,indent=2))
    args=['--native-report',str(reformatted),'--injection-report',str(p),'--out',str(tmp_path/'out.json')]
    assert app.main(args)==2
    assert 'BYTE_MISMATCH__SEMANTICS_UNRESOLVED' in capsys.readouterr().err
    assert app.main(args+['--linked-native-report',str(n)])==0
    result=json.loads((tmp_path/'out.json').read_text())
    assert result['input_evidence']['native_link_relation']=='CANONICAL_JSON_IDENTICAL_TO_BYTE_LINKED_REFERENCE'
    assert result['input_evidence']['native_report_sha256']!=result['input_evidence']['linked_native_report_sha256']


def test_semantic_change_not_admitted_as_reformatting(tmp_path):
    native,probe,n,p,*_=fixture_reports(tmp_path)
    native['nside']=1024;bad=tmp_path/'bad.json';bad.write_text(json.dumps(native))
    with pytest.raises(ValueError,match='CANONICAL_CONTENT_MISMATCH'):app.load_linked(bad,p,n)


def test_cli_in_independent_directory_does_not_need_healpy(tmp_path):
    _,_,n,p,*_=fixture_reports(tmp_path)
    out=tmp_path/'output.json'
    r=subprocess.run([sys.executable,app.__file__,'--native-report',str(n),
        '--injection-report',str(p),'--out',str(out)],cwd=tmp_path,capture_output=True,text=True,timeout=20)
    assert r.returncode==0,r.stderr
    assert json.loads(r.stdout)['status']=='PASS_MATCHED_WINDOW_RAW_COMPARISON'
    assert out.exists()


def test_objective_tradeoff_is_reported_from_small_moments():
    a,masks,w,x,g,h,b=problem()
    r=app.matched_fit(g,h,b)
    for k,m in masks.items():
        saved=r['fit_metadata'][k]
        assert 'matched_loss_excess_of_original_K_CMB2' in saved
        old=r['original_coefficients'][k];new=r['matched_coefficients'][k]
        loss=lambda c:np.linalg.norm((x-a@c)[m & w])**2
        old_loss=lambda c:np.linalg.norm((np.where(w,x,0)-a@c)[m])**2
        assert saved['matched_loss_excess_of_original_K_CMB2']==pytest.approx(loss(old)-loss(new),rel=1e-11,abs=1e-13)
        assert saved['original_loss_excess_of_matched_K_CMB2']==pytest.approx(old_loss(new)-old_loss(old),rel=1e-11,abs=1e-13)


def test_zero_fill_objective_equals_matched_loss_plus_hole_penalty():
    a,masks,w,x,g,h,b=problem()
    c=np.arange(a.shape[1],dtype=float)
    for k,m in masks.items():
        original=np.linalg.norm((np.where(w,x,0)-a@c)[m])**2
        matched=np.linalg.norm((x-a@c)[m & w])**2
        assert original==pytest.approx(matched+c@h[k]@c,rel=3e-14)
