"""Finite known-source injections; no real Planck map or physical null."""
from pathlib import Path
import sys
import numpy as np
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
import l01_windowed_low_injections as mod


def test_known_input_exposes_masked_data_unmasked_design_response():
    a=np.array([[1,0],[0,1],[1,1],[1,-1]],float)
    common=np.ones(4,bool);inner=np.array([1,1,1,0],bool)
    w=np.array([1,1,1,0],bool)
    grams={k:a[m].T@a[m] for k,m in zip(mod.MASKS,(common,inner))}
    holes={k:a[m & ~w].T@a[m & ~w] for k,m in zip(mod.MASKS,(common,inner))}
    r=mod.response_from_holes(grams,holes)
    expected=np.array([[1,-1],[-1,1]],float)/3
    np.testing.assert_allclose(r['difference'],expected,rtol=1e-14,atol=1e-15)
    for name,m in zip(mod.MASKS,(common,inner)):
        direct=np.linalg.lstsq(a[m],(a*w[:,None])[m],rcond=None)[0]
        np.testing.assert_allclose(r['responses'][name],direct,atol=1e-15)
        np.testing.assert_allclose(r['matched_controls'][name]['response'],np.eye(2),atol=1e-15)


def test_window_unity_has_zero_difference_and_identity_response():
    g={k:np.eye(3) for k in mod.MASKS};c={k:np.zeros((3,3)) for k in mod.MASKS}
    r=mod.response_from_holes(g,c)
    np.testing.assert_array_equal(r['difference'],np.zeros((3,3)))
    for name in mod.MASKS:np.testing.assert_array_equal(r['responses'][name],np.eye(3))


def test_no_observed_window_has_no_identifiable_matched_model():
    g={mod.MASKS[0]:2*np.eye(2),mod.MASKS[1]:np.eye(2)}
    r=mod.response_from_holes(g,g)
    np.testing.assert_array_equal(r['difference'],np.zeros((2,2)))
    for k in mod.MASKS:assert r['matched_controls'][k]['response'] is None


@pytest.mark.parametrize('scale',[1.,1e-6,1e6])
def test_common_solid_angle_factor_does_not_change_response(scale):
    a=np.random.default_rng(3).normal(size=(30,4));w=np.arange(30)%4!=0
    masks=[np.ones(30,bool),np.arange(30)<22]
    grams={k:scale*a[m].T@a[m] for k,m in zip(mod.MASKS,masks)}
    holes={k:scale*a[m & ~w].T@a[m & ~w] for k,m in zip(mod.MASKS,masks)}
    r=mod.response_from_holes(grams,holes)
    oracle=[np.linalg.lstsq(a[m],(a*w[:,None])[m],rcond=None)[0] for m in masks]
    np.testing.assert_allclose(r['difference'],oracle[1]-oracle[0],atol=3e-15)


@pytest.mark.parametrize('bad',['nan','complex','asymmetric','nonpositive','hole_negative','hole_too_large','non_nested'])
def test_incompatible_moment_geometry_rejected(bad):
    g={mod.MASKS[0]:2*np.eye(2),mod.MASKS[1]:np.eye(2)}
    c={k:.2*np.eye(2) for k in mod.MASKS}
    if bad=='nan':g[mod.MASKS[0]][0,0]=np.nan
    if bad=='complex':g[mod.MASKS[0]]=g[mod.MASKS[0]].astype(complex)
    if bad=='asymmetric':g[mod.MASKS[0]][0,1]=.1
    if bad=='nonpositive':g[mod.MASKS[0]][0,0]=-1
    if bad=='hole_negative':c[mod.MASKS[0]][0,0]=-.1
    if bad=='hole_too_large':c[mod.MASKS[1]]*=20
    if bad=='non_nested':g[mod.MASKS[1]]*=4
    with pytest.raises(ValueError):mod.response_from_holes(g,c)


@pytest.mark.parametrize('chunk',[1,7,48])
def test_sparse_complement_scan_matches_full_array_and_skips_observed(chunk):
    nside=2;base=1;npix=48;ratio=4
    rng=np.random.default_rng(2);a=rng.normal(size=(2*npix,4))
    masks={mod.MASKS[0]:np.arange(12)<10,mod.MASKS[1]:np.arange(12)<7}
    w=np.arange(npix)%5!=0;seen=[]
    def design(ids):
        seen.extend(ids.tolist());return np.vstack([a[ids],a[npix+ids]])
    c,receipt=mod.accumulate_holes(w,masks,base,nside,design,chunk_pixels=chunk,ncoeff=4)
    for k in mod.MASKS:
        selected=np.repeat(masks[k],ratio)&~w;rows=np.r_[selected,selected]
        np.testing.assert_allclose(c[k],(4*np.pi/npix)*a[rows].T@a[rows],atol=2e-15)
        assert receipt['excluded_source_pixels_in_fit_region'][k]==int(selected.sum())
    expected=np.flatnonzero(np.repeat(masks[mod.MASKS[0]],ratio)&~w)
    np.testing.assert_array_equal(seen,expected)


def test_all_observed_window_never_evaluates_basis():
    masks={k:np.ones(12,bool) for k in mod.MASKS}
    def forbidden(ids):raise AssertionError('No omitted pixels should be evaluated')
    c,r=mod.accumulate_holes(np.ones(48,bool),masks,1,2,forbidden,ncoeff=4)
    assert r['design_evaluated_spatial_pixels']==0
    assert all(np.count_nonzero(x)==0 for x in c.values())


@pytest.mark.parametrize('bad',['window_float','bad_ratio','non_nested','bad_design','bad_chunk'])
def test_sparse_mask_contract_errors(bad):
    masks={k:np.ones(12,bool) for k in mod.MASKS};w=np.zeros(48,bool);nside=2;chunk=8
    design=lambda ids:np.ones((2*len(ids),4))
    if bad=='window_float':w=w.astype(float)
    if bad=='bad_ratio':nside=3
    if bad=='non_nested':masks[mod.MASKS[0]][0]=False
    if bad=='bad_design':design=lambda ids:np.ones((len(ids),4))
    if bad=='bad_chunk':chunk=0
    with pytest.raises(ValueError):mod.accumulate_holes(w,masks,1,nside,design,ncoeff=4,chunk_pixels=chunk)


def spherical_case():
    # Read the exact inherited checked-in real spin2 basis, no substitute formula.
    try:
        from spin2_finite import block_design
    except ImportError:
        from l01_repo_imports import activate
        activate()
        from spin2_finite import block_design
    n=300;ids=np.arange(n);z=1-2*(ids+.5)/n
    theta=np.arccos(z);phi=np.mod(ids*np.pi*(3-np.sqrt(5)),2*np.pi)
    a=block_design(theta,phi,2,5)
    common=np.ones(n,bool);inner=(z>-.65)
    window=~((phi<1.1)&(z<.6)&(z>-.5))
    masks=[common,inner];g={};c={};e=[];b=[];offset=0
    for ell in range(2,6):
        k=2*ell+1;e.extend(range(offset,offset+k));b.extend(range(offset+k,offset+2*k));offset+=2*k
    for key,m in zip(mod.MASKS,masks):
        rows=np.r_[m,m];holes=np.r_[m & ~window,m & ~window]
        g[key]=a[rows].T@a[rows];c[key]=a[holes].T@a[holes]
    return a,window,masks,g,c,np.array(e),np.array(b)


def test_actual_spherical_basis_pure_E_and_B_paired_injections():
    a,w,masks,g,c,e,b=spherical_case();result=mod.response_from_holes(g,c)
    input_coeff=np.eye(64)  # all 64 unit low E/B sources
    synthetic=a@input_coeff
    masked=synthetic*np.r_[w,w][:,None]
    direct=[]
    for key,m in zip(mod.MASKS,masks):
        rows=np.r_[m,m]
        fitted=np.linalg.lstsq(a[rows],masked[rows],rcond=None)[0]
        direct.append(fitted)
        np.testing.assert_allclose(result['responses'][key],fitted,atol=4e-15)
        mw=m&w;matched_rows=np.r_[mw,mw]
        matched=np.linalg.lstsq(a[matched_rows],masked[matched_rows],rcond=None)[0]
        np.testing.assert_allclose(matched,input_coeff,atol=5e-15)
    np.testing.assert_allclose(result['difference'],direct[1]-direct[0],atol=5e-15)
    summary=mod.block_summary(result['difference'],e,b)
    assert summary['E_to_B_gain']>.001  # known pure E input creates nonzero inferred B
    assert summary['E_to_B_gain']==pytest.approx(summary['B_to_E_gain'],rel=1e-12)
    # Comm(G^-1 C,J)=G^-1[Comm(C,J)-Comm(G,J)G^-1 C].
    # Raw absolute 4e-15 is unjustified here: the inner Gram condition is ~209.
    # Propagate measured input commutators rather than relaxing the physics gate.
    j=np.zeros((64,64));j[np.ix_(e,b)]=-np.eye(32);j[np.ix_(b,e)]=np.eye(32)
    propagated=0.
    for k in mod.MASKS:
        x=np.linalg.solve(g[k],c[k])
        propagated+=(np.linalg.norm(c[k]@j-j@c[k],2)
            +np.linalg.norm(g[k]@j-j@g[k],2)*np.linalg.norm(x,2))/np.linalg.eigvalsh(g[k])[0]
    arithmetic=128*np.finfo(float).eps*max(1.,summary['all_gain'])
    assert summary['EB_complex_structure_absolute_residual']<=propagated+arithmetic
    assert np.linalg.norm(summary['unit_E_input_coefficients'])==pytest.approx(1.)
    assert np.linalg.norm(summary['unit_E_B_response'])==pytest.approx(summary['E_to_B_gain'])


def test_input_amplitude_and_degenerate_witness_keep_response_meaning():
    r=np.array([[.2,.3],[-.3,.2]])
    out=mod.block_summary(r,np.array([0]),np.array([1]))
    assert out['E_to_B_gain']==pytest.approx(.3)
    assert out['unit_E_B_response']==pytest.approx([-.3])
    zero=mod.block_summary(np.zeros((2,2)),np.array([0]),np.array([1]))
    assert zero['E_to_B_gain']==0
    for amplitude in (1e-6,-1e-6,1e-12):
        assert np.linalg.norm(r@np.array([amplitude,0]))==pytest.approx(abs(amplitude)*np.sqrt(.13))


def test_bad_EB_indices_rejected():
    with pytest.raises(ValueError):mod.block_summary(np.eye(4),np.array([0,1]),np.array([1,2]))


def test_cli_help_and_no_overwrite_does_not_import_native_dependencies(tmp_path):
    import subprocess
    out=tmp_path/'result.json';out.write_text('preserve')
    p=subprocess.run([sys.executable,mod.__file__,'--help'],capture_output=True,text=True,cwd=tmp_path)
    assert p.returncode==0 and '--native-report' in p.stdout
    assert mod.main(['--root','unused','--native-report','unused','--native-receipt','unused','--out',str(out)])==2
    assert out.read_text()=='preserve'
