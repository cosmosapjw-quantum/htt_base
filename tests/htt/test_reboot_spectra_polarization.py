import importlib.util
import os
from pathlib import Path
import numpy as np
import pytest

candidate=os.environ.get('HTT_SP_CANDIDATE')
if candidate:
    spec=importlib.util.spec_from_file_location('reboot_spectra_polarization',candidate)
    suite=importlib.util.module_from_spec(spec);spec.loader.exec_module(suite)
else:
    from scripts import reboot_spectra_polarization as suite


def test_dl_cl_and_exact_grid_no_interpolation_shortcut():
    ell=np.array([2,3,4]);cl=np.array([1.,2.,3.])
    dl=cl*ell*(ell+1)/(2*np.pi)
    assert np.allclose(suite.dl_to_cl(ell,dl),cl)
    assert np.array_equal(suite.exact_reference([2,4],ell,dl),dl[[0,2]])
    with pytest.raises(ValueError):suite.exact_reference([2,5],ell,dl)


def test_asymmetric_errors_toward_reference_and_negative_bandpower():
    r=suite.residuals(np.array([-1.,3.]),np.array([0.,1.]),np.array([2.,2.]),np.array([4.,4.]))
    assert np.array_equal(r['signed_residual_over_error_toward_reference'],[-.25,1.])


def test_fortran_covariance_record_and_source_lower_triangle():
    c=np.array([[2.,999.],[.3,4.]])
    marker=np.array([32],dtype='<u4').tobytes()
    decoded=suite.fortran_covariance(marker+c.astype('<f8').tobytes()+marker,2)
    assert np.array_equal(decoded,np.array([[2.,.3],[.3,4.]]))
    with pytest.raises(ValueError):suite.fortran_covariance(marker+c.tobytes()+b'XXXX',2)


def test_spt_window_contract_dl_order():
    w=np.zeros((2,3,3));w[0,1,:]=1;w[1,2,:]=1
    spectra={'TT':np.array([10.,20.,30.]),'TE':np.array([-1.,-2.,-3.]),'EE':np.array([1.,2.,3.])}
    result=suite.spt_window_model(w,np.array([1,2,3]),spectra,['90_Tx90_T','90_Tx90_E','90_Ex90_E'])
    assert np.array_equal(result,[[20,30],[-2,-3],[2,3]])


def make_qu(path,nside=1,unit='K',pol='COSMO',coords='C',nested=False,packed=False):
    from astropy.io import fits
    n=12*nside*nside;q=np.arange(n,dtype=float)*1e-6;u=-q
    form='4D' if packed else 'D'
    if packed:q=q.reshape(-1,4);u=u.reshape(-1,4)
    h=fits.BinTableHDU.from_columns([fits.Column(name='Q_POLARISATION',format=form,unit=unit,array=q),
                                  fits.Column(name='U_POLARISATION',format=form,unit=unit,array=u)])
    h.header['PIXTYPE']='HEALPIX';h.header['ORDERING']='NESTED' if nested else 'RING';h.header['NSIDE']=nside
    h.header['POLCCONV']=pol
    if coords is not None:h.header['COORDSYS']=coords
    fits.HDUList([fits.PrimaryHDU(),h]).writeto(path)


def test_named_packed_qu_units_and_unknown_frame_preservation(tmp_path):
    path=tmp_path/'q.fits';make_qu(path,packed=True)
    q,u,valid,meta=suite.read_qu(path,expected_nside=1,expected_coords='C')
    assert np.array_equal(q,np.arange(12)) and np.array_equal(u,-np.arange(12))
    assert valid.all() and meta['native_unit']=='K'
    path2=tmp_path/'u.fits';make_qu(path2,coords=None)
    assert suite.read_qu(path2,expected_nside=1)[3]['coordinate_frame']=='UNSPECIFIED'


@pytest.mark.parametrize('kwargs',[{'unit':'Jy'},{'pol':'IAU'},{'nested':True},{'coords':'G'}])
def test_qu_reader_rejects_unqualified_conventions(tmp_path,kwargs):
    p=tmp_path/'bad.fits';make_qu(p,**kwargs)
    with pytest.raises(ValueError):suite.read_qu(p,expected_nside=1,expected_coords='C')


def test_nonpositive_covariance_returns_hold_no_repair():
    result=suite.covariance_quadratic(np.diag([1.,-1.]),np.ones(2))
    assert result['quadratic'] is None and result['status'].startswith('HOLD_')


def test_mask_operator_excludes_injected_qu_and_spin_zeroes():
    pytest.importorskip('healpy')
    nside=2;n=12*nside*nside
    q=np.zeros(n);u=np.zeros(n);mask=np.ones(n,dtype=bool)
    mask[5]=False
    baseline=suite.spin_pseudo_spectra(q,u,mask,nside,3)
    q[5]=1e9;u[5]=-1e9
    hidden=suite.spin_pseudo_spectra(q,u,mask,nside,3)
    for key in ('EE_pseudo_Cl','BB_pseudo_Cl','EB_pseudo_Cl'):
        assert np.array_equal(baseline[key],hidden[key])
        assert np.array_equal(hidden[key],np.zeros(4))
    mask[5]=True
    exposed=suite.spin_pseudo_spectra(q,u,mask,nside,3)
    assert exposed['EE_pseudo_Cl'][2:].max()>0
