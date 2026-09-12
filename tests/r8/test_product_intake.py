from pathlib import Path
import numpy as np
import pytest
from astropy.io import fits
from obsstat.r8_product_intake import reduce_temperature_map, fit_common_temperature_records
from obsstat.r7_cmb_product_response import pixel_fit_geometry


def make_map(path, values, unit='K_CMB', coords='GALACTIC', mask=None):
    if mask is None: mask=np.ones(len(values))
    hdu=fits.BinTableHDU.from_columns([fits.Column(name='I_STOKES',format='D',unit=unit,array=values),
                                     fits.Column(name='TMASK',format='D',array=mask)])
    hdu.header['NSIDE']=64;hdu.header['ORDERING']='RING';hdu.header['COORDSYS']=coords
    fits.HDUList([fits.PrimaryHDU(),hdu]).writeto(path)


def test_joint_fit_preserves_full_coefficients_units_and_frame(tmp_path):
    _,design=pixel_fit_geometry();coef=np.arange(36)*1e-7;coef[0]=1e-4
    path=tmp_path/'toy.fits';make_map(path,design@coef*1000.,unit='mK_CMB')
    p=reduce_temperature_map(path,'toy','fixture')
    records,meta=fit_common_temperature_records([p])
    assert np.allclose(records[0].retained,coef[4:],atol=2e-17,rtol=0)
    assert records[0].Q.shape==(3,3) and records[0].O.shape==(3,3,3)
    assert records[0].frame=='GALACTIC' and records[0].covariance is None
    assert meta['fit_ells']==[0,5] and not meta['empirical_eligible']


@pytest.mark.parametrize('unit,coords',[('Jy','GALACTIC'),('K_CMB','ECLIPTIC')])
def test_header_semantics_cannot_be_filled_by_product_name(tmp_path,unit,coords):
    path=tmp_path/'bad.fits';make_map(path,np.zeros(49152),unit=unit,coords=coords)
    with pytest.raises(ValueError):reduce_temperature_map(path,'PLANCK','R3')


def test_common_mask_all_rows_and_bad_pixel(tmp_path):
    _,d=pixel_fit_geometry();coef=np.arange(36)*1e-7
    mask=np.ones(len(d));mask[:100]=0
    a=tmp_path/'a.fits';b=tmp_path/'b.fits'
    make_map(a,d@coef,mask=mask);make_map(b,d@(2*coef),mask=mask)
    products=[reduce_temperature_map(p,p.stem,'fixture') for p in (a,b)]
    records,meta=fit_common_temperature_records(products)
    assert [r.sample_id for r in records]==['a','b']
    assert meta['valid_pixels']==len(d)-100
    assert np.allclose(records[1].retained,2*records[0].retained,atol=1e-17,rtol=0)
    with pytest.raises(ValueError):fit_common_temperature_records(products[:1]*2)


# R8 full continuation: selected distance-product intake regressions.
import numpy as np
import pytest
from scripts.observed_runs.r8_product_intake import decode_union3,profile_offset,inspect_products


def test_union3_published_matrix_convention_and_offset():
    m=np.zeros((4,4));m[0,1:]=[.1,.2,.3];m[1:,0]=[35,36,37];m[1:,1:]=np.diag([1.,2.,3.])
    z,mu,p=decode_union3(m)
    offset,chi=profile_offset(mu,[1,2,3],p)
    assert offset==34 and chi==0
    with pytest.raises(ValueError):decode_union3(m.T)
    m[2,2]=-1
    with pytest.raises(np.linalg.LinAlgError):decode_union3(m)


def test_missing_product_does_not_suppress_siblings(tmp_path):
    products=inspect_products(tmp_path)
    assert set(products)=={'cf4_full','jwst_anchors','union3','desi_raw'}
    assert all(v['outcome']=='INPUT_UNAVAILABLE' for v in products.values())


def test_released_precision_antisymmetry_preserves_quadratic():
    m=np.zeros((4,4));m[0,1:]=[.1,.2,.3];m[1:,0]=[35,36,37];m[1:,1:]=np.diag([1.,2.,3.])
    m[1,2]+=4e-11
    _,_,precision=decode_union3(m)
    r=np.array([.7,-.2,.3])
    assert r@precision@r==pytest.approx(r@m[1:,1:]@r,abs=1e-15)
