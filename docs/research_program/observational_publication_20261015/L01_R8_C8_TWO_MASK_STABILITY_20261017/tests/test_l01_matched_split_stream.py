"""Synthetic raw-pixel controls; no simulated skies are called Planck nulls."""
import hashlib
import importlib
from pathlib import Path
import subprocess
import sys
import numpy as np
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
import l01_matched_split_stream as m
import l01_matched_window_refit as fit


def fixture(nside=2,ncoeff=4,scale=1e-6):
    N=12*nside**2;r=np.random.default_rng(22)
    A=r.normal(size=(2,N,ncoeff));x=scale*r.normal(size=(2,N,5))
    w=np.ones(N,bool);w[::7]=False
    coarse={'common':np.ones(12,bool),'three_way_intersection':np.r_[np.ones(9,bool),np.zeros(3,bool)]}
    c=np.repeat(coarse['common'],nside*nside);t=np.repeat(coarse['three_way_intersection'],nside*nside)
    def design(ids):return A[:,ids,:].reshape(2*len(ids),ncoeff)
    def data(ids):return x[:,ids,:]
    omega=4*np.pi/N
    G={};C={};B={}
    for name,mask in [('common',c),('three_way_intersection',t)]:
        a=A[:,mask,:].reshape(-1,ncoeff);z=A[:,mask&~w,:].reshape(-1,ncoeff)
        aw=A[:,mask&w,:].reshape(-1,ncoeff);v=x[:,mask&w,:].reshape(-1,5)
        G[name]=omega*a.T@a;C[name]=omega*z.T@z;B[name]=omega*aw.T@v
    return w,coarse,design,data,G,C,B,A,x


def test_shared_stream_matches_explicit_selected_pixel_integral():
    w,coarse,A,x,G,C,B,*_=fixture()
    out=m.stream_raw_rhs(w,coarse,1,2,A,x,ncoeff=4,chunk_pixels=7)
    np.testing.assert_allclose(out['common'],B['common'],rtol=1e-13,atol=1e-21)
    np.testing.assert_allclose(out['removed_shell'],B['common']-B['three_way_intersection'],rtol=1e-13,atol=1e-21)


@pytest.mark.parametrize('chunk',[1,3,7,17,48,65536])
def test_chunk_invariance_and_counts(chunk):
    w,coarse,A,x,G,C,B,*_=fixture()
    out=m.stream_raw_rhs(w,coarse,1,2,A,x,ncoeff=4,chunk_pixels=chunk)
    for name,expected in [('common',B['common']),('removed_shell',B['common']-B['three_way_intersection'])]:
        np.testing.assert_allclose(out[name],expected,rtol=3e-13,atol=2e-21)
    assert out['basis_pixels_evaluated']==int(w.sum())
    assert out['selected_pixels']['common']==out['selected_pixels']['three_way_intersection']+out['selected_pixels']['removed_shell']
    assert out['Gram_recomputed'] is False


@pytest.mark.parametrize('scale',[1e-100,1e-6,1.,1e10])
def test_five_map_fits_against_independent_lstsq(scale):
    w,coarse,design,data,G,C,B,A,x=fixture(scale=scale)
    rhs=m.stream_raw_rhs(w,coarse,1,2,design,data,ncoeff=4,chunk_pixels=7)
    r=m.solve_products(G,C,rhs['common'],rhs['removed_shell'])
    for name,small in coarse.items():
        chosen=np.repeat(small,4)&w
        oracle=np.linalg.lstsq(A[:,chosen,:].reshape(-1,4),x[:,chosen,:].reshape(-1,5),rcond=None)[0]
        np.testing.assert_allclose(r['matched_coefficients'][name],oracle,rtol=2e-12,atol=scale*1e-14)
    assert r['shell_identity_relative']<1e-13
    assert r['split_linearity_relative']<1e-13
    assert r['p_value'] is None and r['noise_debiasing'] is False


def test_linear_combination_matches_fitting_raw_half_difference():
    w,coarse,design,data,G,C,B,A,x=fixture()
    r=m.solve_products(G,C,B['common'],B['common']-B['three_way_intersection'])
    for name,small in coarse.items():
        chosen=np.repeat(small,4)&w
        low=A[:,chosen,:].reshape(-1,4)
        hm=(x[:,chosen,1]-x[:,chosen,2]).reshape(-1)/2
        oracle=np.linalg.lstsq(low,hm,rcond=None)[0]
        got=m.linear_subjects(r['matched_coefficients'][name])['HM_half_difference']
        np.testing.assert_allclose(got,oracle,rtol=1e-12,atol=1e-20)


def test_shared_known_low_sky_has_zero_matched_shell_contrast():
    w,coarse,design,data,G,C,B,A,x=fixture()
    truth=np.array([1.,-2.,3.,-.5])*1e-6
    shared=np.broadcast_to((A@truth)[:,:,None],x.shape)
    rhs=m.stream_raw_rhs(w,coarse,1,2,design,lambda ids:shared[:,ids,:],ncoeff=4,chunk_pixels=5)
    result=m.solve_products(G,C,rhs['common'],rhs['removed_shell'])
    np.testing.assert_allclose(result['matched_contrast'],0,atol=2e-20)
    for name in coarse:
        np.testing.assert_allclose(result['matched_coefficients'][name],np.tile(truth[:,None],(1,5)),rtol=1e-12,atol=1e-20)
    assert result['statistics']['matched_contrast']['all']['norms_K_CMB']['HM_half_difference']==0


def test_no_design_or_data_requests_outside_fixed_support():
    w,coarse,design,data,G,C,B,A,x=fixture()
    coarse['common'][-1]=False
    visited=[]
    expected=np.repeat(coarse['common'],4)&w
    def wrapped(ids):
        assert expected[ids].all();visited.extend(ids.tolist());return design(ids)
    m.stream_raw_rhs(w,coarse,1,2,wrapped,data,ncoeff=4,chunk_pixels=9)
    assert visited==np.flatnonzero(expected).tolist()


@pytest.mark.parametrize('bad',['float_mask','different_shape','non_nested','float_chunk','negative_chunk','not_power_two','bool_nside'])
def test_support_contracts_fail_closed(bad):
    w,c,A,x,*_=fixture();base=1;ns=2;chunk=8
    if bad=='float_mask':w=w.astype(float)
    if bad=='different_shape':w=w[:-1]
    if bad=='non_nested':c['common'][0]=False
    if bad=='float_chunk':chunk=8.
    if bad=='negative_chunk':chunk=-1
    if bad=='not_power_two':ns=3
    if bad=='bool_nside':ns=True
    with pytest.raises(ValueError):m.stream_raw_rhs(w,c,base,ns,A,x,ncoeff=4,chunk_pixels=chunk)


@pytest.mark.parametrize('bad',['nan','unseen','wrong_shape','complex'])
def test_invalid_included_data_rejected_without_changing_masks(bad):
    w,c,A,x,*_=fixture()
    def broken(ids):
        y=x(ids).copy()
        if bad=='nan':y[0,0,1]=np.nan
        if bad=='unseen':y[0,0,1]=-1.6375e30
        if bad=='wrong_shape':y=y[:,:,0]
        if bad=='complex':y=y.astype(complex)
        return y
    with pytest.raises(ValueError):m.stream_raw_rhs(w,c,1,2,A,broken,ncoeff=4)


def test_empty_support_is_not_observed_data():
    w,c,A,x,*_=fixture();w[:]=False
    def never(_):raise AssertionError('Provider must not be called')
    r=m.stream_raw_rhs(w,c,1,2,never,never,ncoeff=4)
    assert not r['common'].any() and r['selected_pixels']['common']==0
    # The native driver additionally requires exact known nonzero support counts.


def test_no_removed_region_gives_zero_contrast():
    w,c,A,x,G,C,B,*_=fixture();c['three_way_intersection']=c['common'].copy()
    rhs=m.stream_raw_rhs(w,c,1,2,A,x,ncoeff=4)
    assert not rhs['removed_shell'].any()
    g={k:G['common'] for k in m.MASKS};holes={k:C['common'] for k in m.MASKS}
    r=m.solve_products(g,holes,rhs['common'],rhs['removed_shell'])
    assert not r['matched_contrast'].any()


def test_full_E_B_index_partition_and_cross_closure():
    w,c,A,x,G,C,B,*_=fixture(nside=4,ncoeff=64)
    r=m.solve_products(G,C,B['common'],B['common']-B['three_way_intersection'])
    all_stats=r['statistics']['matched_contrast']
    assert set(all_stats)=={'all','E','B'}
    for name,e in all_stats['all']['energies_K_CMB2'].items():
        assert e==pytest.approx(all_stats['E']['energies_K_CMB2'][name]+all_stats['B']['energies_K_CMB2'][name],rel=1e-13,abs=0)
    for group in all_stats.values():
        for label in ('HM','OE'):assert group['split_cross_checks'][label]['identity_relative']<2e-14


def test_orthogonal_coefficient_rotation_preserves_norms():
    w,c,A,x,G,C,B,*_=fixture();q,_=np.linalg.qr(np.random.default_rng(8).normal(size=(4,4)))
    first=m.solve_products(G,C,B['common'],B['common']-B['three_way_intersection'])
    g={k:q.T@v@q for k,v in G.items()};holes={k:q.T@v@q for k,v in C.items()}
    second=m.solve_products(g,holes,q.T@B['common'],q.T@(B['common']-B['three_way_intersection']))
    np.testing.assert_allclose(second['matched_contrast'],q.T@first['matched_contrast'],rtol=3e-12,atol=1e-20)


def test_source_window_cannot_be_inferred_from_product_values():
    w,c,A,x,G,C,B,design,raw=fixture();raw[:,:,1]=0
    rhs=m.stream_raw_rhs(w,c,1,2,A,lambda ids:raw[:,ids,:],ncoeff=4)
    assert rhs['selected_pixels']['common']==int(w.sum())
    assert not rhs['common'][:,1].any()


def test_opposite_maps_keep_negative_cross_products():
    w,c,A,x,G,C,B,*_=fixture();B={k:v.copy() for k,v in B.items()}
    for b in B.values():b[:,2]=-b[:,1]
    r=m.solve_products(G,C,B['common'],B['common']-B['three_way_intersection'])
    q=r['statistics']['matched_common']['all']
    assert q['split_cross_checks']['HM']['cross_inner_product_K_CMB2']<0
    assert q['energies_K_CMB2']['HM_half_sum']==0


def test_linear_subject_shape_and_rhs_shape_checks():
    with pytest.raises(ValueError):m.linear_subjects(np.zeros((4,4)))
    w,c,A,x,G,C,B,*_=fixture()
    with pytest.raises(ValueError):m.solve_products(G,C,B['common'][:,:4],B['common'][:,:4])


@pytest.mark.parametrize('product,width',[('full',10),('hm1',3),('oe2',3)])
def test_native_memmap_uses_big_endian_original_QU_columns(tmp_path,product,width):
    N=12;values=np.arange(N*width,dtype='>f4').reshape(N,width)
    p=tmp_path/(product+'.fits');p.write_bytes(b' '*32+values.tobytes())
    def header(f,offset,size):return ({'NAXIS1':4*width,'NAXIS2':N},16 if offset==0 else 32)
    table,identity=m.open_qu_table(p,product,N,header)
    try:
        np.testing.assert_array_equal(table[[1,3],1],values[[1,3],1])
        np.testing.assert_array_equal(table[[1,3],2],values[[1,3],2])
        assert not np.array_equal(table[:,1],table[:,0])
        with p.open('ab') as f:f.write(b'x')
        assert m._identity(p)!=identity
    finally:table._mmap.close()


def test_symlink_source_rejected(tmp_path):
    p=tmp_path/'source';p.write_bytes(b'abc');q=tmp_path/'link';q.symlink_to(p)
    with pytest.raises(ValueError,match='NOT_REGULAR'):m.open_qu_table(q,'hm1',12,lambda *x:None)


def test_saved_full_baseline_mismatch_fails():
    with pytest.raises(ValueError,match='BASELINE'):
        fit.close(np.ones(64)*1e-6,np.ones(64)*1.01e-6,'BASELINE')


def test_cli_help_without_native_dependencies_and_no_clobber(tmp_path):
    help_run=subprocess.run([sys.executable,m.__file__,'--help'],cwd=tmp_path,text=True,capture_output=True)
    assert help_run.returncode==0 and '--injection-report' in help_run.stdout
    out=tmp_path/'exists.json';out.write_text('preserve me')
    result=m.main(['--root','/absent','--native-report','a','--injection-report','b','--native-receipt','c','--out',str(out)])
    assert result==2 and out.read_text()=='preserve me'


def test_exact_user_published_refit_dependency():
    assert m._blob(fit.__file__)==m.REFIT_BLOB
