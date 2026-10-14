import importlib.util
import os
from pathlib import Path
import numpy as np
import pytest

CANDIDATE = Path(os.environ.get('HTT_FFP_CANDIDATE', Path(__file__).resolve().parents[2]))
spec=importlib.util.spec_from_file_location('run_ffp_first_pair',
                                             CANDIDATE/'scripts/run_ffp_first_pair.py')
audit=importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)
hp=pytest.importorskip('healpy')


def spin_fixture():
    nside=64;lmax=16
    e=np.zeros(hp.Alm.getsize(lmax),complex);b=e.copy()
    e[hp.Alm.getidx(lmax,4,2)]=1e-5+2e-6j
    b[hp.Alm.getidx(lmax,7,3)]=3e-6-1e-6j
    q,u=hp.alm2map_spin([e,b],nside=nside,spin=2,lmax=lmax,mmax=lmax)
    return e,b,q,u


def test_native_spin_fixture_recovery_and_packed_power():
    e,b,q,u=spin_fixture()
    recovered=hp.map2alm_spin([q,u],spin=2,lmax=16,mmax=16)
    error=np.linalg.norm(np.r_[recovered[0]-e,recovered[1]-b])/np.linalg.norm(np.r_[e,b])
    assert error<=1e-3
    assert len(e)==153
    for alm in (e,b,recovered[0],recovered[1]):
        np.testing.assert_allclose(audit.manual_cl(alm),hp.alm2cl(alm,lmax=16,mmax=16),
                                   rtol=1e-12,atol=1e-24)
    np.testing.assert_allclose(audit.manual_cl(e, b),hp.alm2cl(e,b,lmax=16,mmax=16),
                               rtol=1e-12,atol=1e-24)


def test_map_scaling_and_u_flip_involution_are_not_eb_swap():
    e,b,q,u=spin_fixture()
    plus=hp.map2alm_spin([q,u],spin=2,lmax=16,mmax=16)
    doubled=hp.map2alm_spin([2*q,2*u],spin=2,lmax=16,mmax=16)
    minus=hp.map2alm_spin([q,-u],spin=2,lmax=16,mmax=16)
    np.testing.assert_allclose(doubled,2*np.asarray(plus),rtol=1e-12,atol=1e-18)
    for a,d in zip(plus,doubled):
        np.testing.assert_allclose(hp.alm2cl(d),4*hp.alm2cl(a),rtol=1e-12,atol=1e-24)
    np.testing.assert_array_equal(-(-u),u)
    assert np.linalg.norm(minus[0]-plus[1])>0.1*np.linalg.norm(np.r_[plus[0],plus[1]])
    assert np.linalg.norm(minus[1]-plus[0])>0.1*np.linalg.norm(np.r_[plus[0],plus[1]])


def test_six_transform_linearity_and_signed_cross(monkeypatch):
    _,_,q,u=spin_fixture()
    monkeypatch.setattr(audit,'PIXELS',len(q))
    qs=.7*q;us=.7*u;qn=.3*q+np.roll(q,7)*.02;un=-.2*u
    for sign in (1,-1):
        s=audit.spin_alms(qs,us,sign)
        n=audit.spin_alms(qn,un,sign)
        total=audit.spin_alms(qs+qn,us+un,sign)
        check=audit.parity_checks(s,n,total,audit.spectra(*s),audit.spectra(*n),
                                  audit.spectra(*total),audit.cross_spectra(s,n))
        assert check['status']=='PASS'
        assert check['sum_alm_relative_norm']<=1e-9


def test_invalid_pixels_hold_without_zero_fill(tmp_path,monkeypatch):
    from astropy.io import fits
    monkeypatch.setattr(audit,'PIXELS',12)
    monkeypatch.setattr(audit,'header_record',lambda path:{'path':str(path)})
    q=np.ones((3,4),dtype='f4');u=q.copy();u[0,1]=hp.UNSEEN
    columns=[fits.Column(name='Q-POLARISATION',format='4E',unit='K_CMB',array=q),
             fits.Column(name='U-POLARISATION',format='4E',unit='K_CMB',array=u)]
    fits.HDUList([fits.PrimaryHDU(),fits.BinTableHDU.from_columns(columns)]).writeto(tmp_path/'u.fits')
    with pytest.raises(ValueError,match='FULL_SKY_HOLD_NONFINITE_OR_UNSEEN'):
        audit.load_qu(tmp_path/'u.fits')


def test_header_layout_refusal(tmp_path):
    from astropy.io import fits
    fits.HDUList([fits.PrimaryHDU(),fits.BinTableHDU()]).writeto(tmp_path/'wrong.fits')
    with pytest.raises(ValueError,match='SOURCE_HEADER_LAYOUT_IDENTITY_MISMATCH'):
        audit.header_record(tmp_path/'wrong.fits')


def test_zero_denominator_and_wrong_sum_controls():
    zero=np.zeros(153,complex)
    pair=(zero,zero)
    power={'EE_K_CMB2':np.zeros(15),'BB_K_CMB2':np.zeros(15)}
    good=audit.parity_checks(pair,pair,pair,power,power,power,power)
    assert good['status']=='PASS'
    assert good['spectra']['EE_K_CMB2']['zero_denominator_count']==15
    bad_e=zero.copy();bad_e[hp.Alm.getidx(16,4,2)]=1
    bad=audit.parity_checks(pair,pair,(bad_e,zero),power,power,power,power)
    assert bad['status']=='FAIL'
