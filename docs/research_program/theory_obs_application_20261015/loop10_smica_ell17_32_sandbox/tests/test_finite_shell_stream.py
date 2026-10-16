"""Independent manufactured falsifiers: never an actual Planck/E2E test."""
import pathlib,sys
import numpy as np
import pytest
from scipy.special import sph_harm_y

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'code'))
from finite_shell_stream import real_harmonic_shell,prepare_low_fit,response_shells,inject_omitted_shell,streaming_injection,combined_bounds


def sphere(n=401):
    j=np.arange(n,dtype=float)+.5
    z=1.-2.*j/n
    phi=(np.pi*(3.-np.sqrt(5.))*j)%(2*np.pi)
    r=np.sqrt(1.-z*z)
    v=np.column_stack((r*np.cos(phi),r*np.sin(phi),z))
    mask=((z>-.8) & (v[:,0]<.75))
    return v,mask


def test_addition_theorem_and_real_cartesian_sign():
    n,_=sphere(127)
    c=np.sqrt(3/(4*np.pi))
    y1=real_harmonic_shell(n,1)
    np.testing.assert_allclose(y1[:,0],c*n[:,2],rtol=0,atol=3e-15)
    np.testing.assert_allclose(y1[:,1],-c*n[:,0],rtol=0,atol=3e-15)
    np.testing.assert_allclose(y1[:,2],-c*n[:,1],rtol=0,atol=3e-15)
    for ell in (0,2,8,17,32):
        q=real_harmonic_shell(n,ell)
        np.testing.assert_allclose(np.sum(q*q,axis=1),
                                   np.full(len(n),(2*ell+1)/(4*np.pi)),atol=3e-12,rtol=0)


def test_stream_finite_17_32_random_injections_vs_independent_lstsq():
    n,mask=sphere(401)
    f=prepare_low_fit(n,mask)
    k,shells=response_shells(f,17,32)
    assert k.shape==(36,800) and len(shells)==16
    assert sum(row['columns'] for row in shells)==800
    z=inject_omitted_shell(f,k,17,32,seed=93)
    z_stream=streaming_injection(f,k,17,32,seed=93)
    assert z_stream['passed']
    np.testing.assert_allclose(z_stream['leakage_norm'],z['observed_finite_leak_norm'],rtol=0,atol=1e-12)
    assert z['bound_holds']
    assert z['low_ols_prediction_max_abs']<1e-10
    assert z['independent_lstsq_max_abs']<1e-10
    assert np.linalg.norm(k[4:36],2)>0


def test_qr_reproduces_direct_mode_columns_and_linear_scaling():
    n,mask=sphere(307)
    f=prepare_low_fit(n,mask)
    k,_=response_shells(f,17,18)
    ylow=np.column_stack([real_harmonic_shell(n[mask],ell) for ell in range(6)])
    high=np.column_stack([real_harmonic_shell(n[mask],ell) for ell in range(17,19)])
    for j in (0,3,20,71):
        exact=np.linalg.lstsq(ylow,high[:,j],rcond=None)[0]
        np.testing.assert_allclose(k[:,j],exact,atol=5e-12,rtol=0)
    k2,_=response_shells(f,17,18)
    np.testing.assert_array_equal(k,k2)


def test_psd_combination_and_old_shell_same_synthetic_geometry():
    n,mask=sphere(255)
    f=prepare_low_fit(n,mask)
    old,_=response_shells(f,6,16)
    new,_=response_shells(f,17,32)
    bound=combined_bounds(old,new)
    assert bound['combined_ell6_32_norm']>=bound['old_ell6_16_norm']-1e-11
    assert bound['combined_ell6_32_norm']>=bound['new_ell17_32_norm']-1e-11
    assert bound['combined_ell6_32_norm']<=bound['psd_upper']+1e-11
    np.testing.assert_allclose(new[:,0],
        np.linalg.lstsq(np.column_stack([real_harmonic_shell(f.selected_directions,l) for l in range(6)]),
                        real_harmonic_shell(f.selected_directions,17)[:,0],rcond=None)[0],
        atol=2e-11,rtol=0)


def test_invalid_source_mask_geometry_and_shell_range():
    n,mask=sphere(80)
    with pytest.raises(ValueError):
        prepare_low_fit(n,np.ones(len(n),float))
    with pytest.raises(ValueError):
        prepare_low_fit(n,np.zeros(len(n),bool))
    bad=n.copy();bad[0,0]*=10
    with pytest.raises(ValueError):
        prepare_low_fit(bad,mask)
    f=prepare_low_fit(n,mask)
    with pytest.raises(ValueError):
        response_shells(f,17,16)
    with pytest.raises(ValueError):
        response_shells(f,2,32)
