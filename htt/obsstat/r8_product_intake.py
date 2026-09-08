"""Measured temperature-map controls; no simulator or physical response law."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
from pathlib import Path
import numpy as np

from common.r7_contracts import content_id
from .r7_cmb_product_response import pixel_fit_geometry, build_tensor_record


@dataclass(frozen=True)
class ReducedTemperatureMap:
    sample_id: str
    release: str
    temperature_K: np.ndarray
    valid: np.ndarray
    source: dict


def reduce_temperature_map(path, sample_id, release) -> ReducedTemperatureMap:
    import healpy as hp
    from astropy.io import fits
    path=Path(path)
    if not sample_id or not release:raise ValueError('explicit product identity/release required')
    with fits.open(path,memmap=True) as hdus:
        hdu=hdus[1];header=hdu.header
        nside=header.get('NSIDE');order=header.get('ORDERING','').strip()
        if not isinstance(nside,int) or nside<64 or not hp.isnsideok(nside):raise ValueError('HEALPix NSIDE >=64 required')
        if order not in {'RING','NESTED'}:raise ValueError('explicit HEALPix ordering required')
        if header.get('COORDSYS','').strip() not in {'G','GALACTIC'}:raise ValueError('Galactic coordinate map required')
        if 'I_STOKES' not in hdu.columns.names or 'TMASK' not in hdu.columns.names:
            raise ValueError('released I_STOKES and temperature confidence mask required')
        unit=hdu.columns['I_STOKES'].unit
        scale={'K_CMB':1.,'mK_CMB':1e-3,'uK_CMB':1e-6}.get(unit)
        if scale is None:raise ValueError('explicit thermodynamic temperature unit conversion unavailable')
        values=np.asarray(hdu.data['I_STOKES'],dtype=np.float64).reshape(-1)
        mask=np.asarray(hdu.data['TMASK'],dtype=np.float64).reshape(-1)
        if values.shape!=(hp.nside2npix(nside),) or mask.shape!=values.shape:
            raise ValueError('map/header pixel count mismatch')
        if not np.isfinite(mask).all() or np.any((mask<0)|(mask>1)):
            raise ValueError('temperature confidence mask must be finite in [0,1]')
        valid=np.isfinite(values)&~hp.mask_bad(values)&(mask>=.5)
        if not np.any(valid):raise ValueError('no released valid temperature pixels')
        values=values*scale;values[~valid]=0.
        sky=hp.ud_grade(values,64,order_in=order,order_out='RING')
        coverage=hp.ud_grade(valid.astype(float),64,order_in=order,order_out='RING')
        reduced_valid=coverage==1.
        if not reduced_valid.any():raise ValueError('no fully supported NSIDE64 pixels')
        stat=path.stat()
        source={'path':str(path),'release':release,'size_bytes':stat.st_size,'mtime_ns':stat.st_mtime_ns,
                'header':{k:header.get(k) for k in ('NSIDE','ORDERING','COORDSYS','POLCCONV','BAD_DATA')},
                'input_unit':unit,'input_column':'I_STOKES','mask_column':'TMASK',
                'header_sha256':hashlib.sha256(header.tostring().encode()).hexdigest(),
                'reduced_temperature_sha256':hashlib.sha256(sky.tobytes()).hexdigest(),
                'reduced_mask_sha256':hashlib.sha256(reduced_valid.tobytes()).hexdigest(),
                'whole_source_byte_hash':'NOT_COMPUTED; release/header/selected reduced input identities retained'}
    return ReducedTemperatureMap(str(sample_id),str(release),sky,reduced_valid,source)


def fit_common_temperature_records(products):
    if not products or len({p.sample_id for p in products})!=len(products):
        raise ValueError('nonempty distinct products required')
    _,design=pixel_fit_geometry()
    if any(p.temperature_K.shape!=(49152,) or p.valid.shape!=(49152,) for p in products):
        raise ValueError('registered NSIDE64 input shape required')
    valid=np.logical_and.reduce([p.valid for p in products])
    if valid.sum()<36:raise ValueError('common temperature support cannot fit ell0..5')
    mask_id=hashlib.sha256(valid.tobytes()).hexdigest()
    policy={'id':'R8_SAME_SKY_PIXEL_CONTROL_V1','nside':64,'fit_ells':[0,5],'retained_ells':[2,5],
            'mask_rule':'TMASK>=0.5, all high-resolution contributors valid; common intersection',
            'mask_sha256':mask_id,'input_products':[p.sample_id for p in products],
            'beam_policy':'released maps followed by pixel averaging; no beam deconvolution',
            'signal':'released signed temperature anisotropy, not absolute thermal source',
            'empirical_eligible':False,'covariance':None,'null_law':None}
    processing_id=content_id(policy);records=[];fits=[]
    for p in products:
        y=p.temperature_K[valid]
        if not np.isfinite(y).all():raise ValueError('nonfinite temperature on common support')
        coef,_,rank,_=np.linalg.lstsq(design[valid],y,rcond=None)
        if rank!=36:raise ValueError('common fit is rank deficient')
        meta={'sample_id':p.sample_id,'product_id':p.sample_id,'release':p.release,'units':'K',
              'harmonic_layout':'ORTHONORMAL_REAL_M0_COS_SIN','frame':'GALACTIC',
              'processing_id':processing_id,'mask_id':mask_id}
        records.append(build_tensor_record(coef[4:],meta,None))
        fits.append({'sample_id':p.sample_id,'all_coefficients_K':coef.tolist(),'rank':int(rank),
                     'residual_rms_K':float(np.sqrt(np.mean((y-design[valid]@coef)**2))),
                     'source':p.source})
    return records,{**policy,'processing_id':processing_id,'valid_pixels':int(valid.sum()),'fits':fits}
