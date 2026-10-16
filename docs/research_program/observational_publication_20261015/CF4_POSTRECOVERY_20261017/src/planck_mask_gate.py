"""PR3 mask byte-lock and source-matched low-resolution mask support audit.

No E/B null law or actual polarization transfer is admitted by this tool.
Heavy 201 MB maps are streamed one at a time; healpy is only required for
--analyse (not for --verify).
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from typing import Mapping
import numpy as np

SOURCE = 'Planck PR3 release_3/ancillary-data/masks at IRSA'
NSIDE_SOURCE=2048
NSIDE_AUDIT=64
NPIX_SOURCE=12*NSIDE_SOURCE**2
MIB=1024**2
LOCKED={
 'common_Int': ('COM_Mask_CMB-common-Mask-Int_2048_R3.00.fits','23f49a3479073408b83a7f1bb2cca490d9be7f934b2e0e891524b6a1d06a5fc4'),
 'common_Pol': ('COM_Mask_CMB-common-Mask-Pol_2048_R3.00.fits','c967e45449596c561c940d7ca0d494f1a26d947e6b5a9ef44185fdbf93b036d4'),
 'HM_Int': ('COM_Mask_CMB-HM-Misspix-Mask-Int_2048_R3.00.fits','f4fd909734d80fb80214018b3ef9b44a378a4d04418337786c48f6d388dfb2a0'),
 'HM_Pol': ('COM_Mask_CMB-HM-Misspix-Mask-Pol_2048_R3.00.fits','33226759f339c099818968f777013984f97d5ec2c04e1816f61ae72930b40296'),
 'OE_Int': ('COM_Mask_CMB-OE-Misspix-Mask-Int_2048_R3.00.fits','ecb39152ad5b93ea309baf396aad404a062edd6745a30c0b941b3556ca28aff9'),
 'OE_Pol': ('COM_Mask_CMB-OE-Misspix-Mask-Pol_2048_R3.00.fits','1b2b4138f791b739938485fa0ebcac5f462e04fbc55626e93d71abd04aac3900'),
}
EXPECTED_BYTES=201335040

def digest_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        while True:
            b=f.read(4*MIB)
            if not b:break
            h.update(b)
    return h.hexdigest()


def verify_masks(root:Path, *,locked:Mapping=LOCKED,expected_bytes:int|None=EXPECTED_BYTES):
    base=root/'planck/PR3/masks';results={}
    for key,(file,sha) in locked.items():
        path=base/file
        if not path.is_file() or path.is_symlink():
            raise FileNotFoundError(f'missing/unsafe PR3 mask: {path}')
        if expected_bytes is not None and path.stat().st_size!=expected_bytes:
            raise ValueError(f'mask length mismatch {key} {path.stat().st_size} != {expected_bytes}')
        with path.open('rb') as f:header=f.read(80)
        if not header.startswith(b'SIMPLE  ='):
            raise ValueError(f'non-FITS header: {key}')
        observed=digest_file(path)
        if sha!=observed:
            raise ValueError(f'SHA mismatch {key}: {observed}')
        results[key]={'status':'BYTES_REHASHED','source':SOURCE,'sha256':observed,'size_bytes':path.stat().st_size,'source_type':'INTENSITY' if key.endswith('_Int') else 'POLARIZATION'}
    return results


def support_masks(arrays:Mapping[str,np.ndarray], *,threshold=.5):
    if not np.isfinite(threshold) or not (0<=threshold<=1):raise ValueError('bad threshold')
    keys=set(LOCKED)
    if set(arrays)!=keys:raise ValueError('all six map IDs required')
    shape={tuple(np.shape(x)) for x in arrays.values()}
    if len(shape)!=1 or len(next(iter(shape)))!=1:raise ValueError('wrong pixel support')
    support={}
    for k,a in arrays.items():
        a=np.asarray(a,dtype=float)
        if not np.isfinite(a).all() or a.min() < -1e-7 or a.max()>1+1e-7:
            raise ValueError('invalid finite mask weights')
        support[k]=a>threshold
    out={'source_mask_ids':sorted(keys),'npix':len(next(iter(support.values()))),'threshold':threshold,'one_latent_sky':True,
         'fraction_by_map':{k:float(np.mean(v)) for k,v in support.items()},
         'joint':{},'claim':'SIX_PR3_RELEASE_MASKS_ONLY_NOT_PLANCK_E2E_NULL'}
    for kind in ['Int','Pol']:
        allthree=support['common_'+kind]&support['HM_'+kind]&support['OE_'+kind]
        out['joint'][f'{kind}_common_HM_OE_intersection_fraction']=float(allthree.mean())
        out['joint'][f'{kind}_common_HM_OE_union_fraction']=float((support['common_'+kind]|support['HM_'+kind]|support['OE_'+kind]).mean())
    out['joint']['all_six_intersection_fraction']=float(np.logical_and.reduce(list(support.values())).mean())
    out['joint']['polarization_minus_temperature_common_fraction']=float(np.mean(support['common_Pol'] & ~support['common_Int']))
    return out


def analyse_real(root:Path,receipt:dict, nside_out=NSIDE_AUDIT):
    try:import healpy as hp
    except ImportError as e:raise RuntimeError('healpy required only for --analyse: pip install healpy astropy') from e
    if nside_out<1 or nside_out&(nside_out-1):raise ValueError('power-of-two nside required')
    if nside_out>NSIDE_SOURCE:raise ValueError('out NSIDE cannot exceed source')
    maps={}
    for key,(fname,digest) in LOCKED.items():
        filepath=root/'planck/PR3/masks'/fname
        # healpy.read_map converts NESTED raw input to canonical RING pixels by default.
        sky,h=hp.read_map(str(filepath),field=0,dtype=np.float32,h=True,verbose=False)
        hdr=dict(h)
        nsrc=hp.get_nside(sky)
        if nsrc!=NSIDE_SOURCE or sky.size!=NPIX_SOURCE:
            raise ValueError(f'wrong source NSIDE for {key}')
        if nside_out<nsrc:
            sky=hp.ud_grade(sky,nside_out=nside_out,order_in='RING',order_out='RING')
        maps[key]=np.asarray(sky,dtype=np.float32)
    res=support_masks(maps)
    res['nside_out']=nside_out;res['pixel_order_out']='RING';res['mask_source_digests']={k:v['sha256'] for k,v in receipt.items()}
    res['downsampling']='healpy.ud_grade averaging, then registered threshold 0.5; not an E/B transfer'
    return res


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=Path('/mnt/extdrive/workdir/htt_open_data'))
    p.add_argument('--analyse',action='store_true')
    p.add_argument('--out-nside',type=int,default=NSIDE_AUDIT)
    p.add_argument('--output',type=Path,default=None)
    a=p.parse_args(argv)
    rec=verify_masks(a.root)
    out={'schema':'htt.planck_PR3_mask_receipts/1','nside_source':NSIDE_SOURCE,'source':'IRSA PR3 six actual masks','masks':rec,
         'physics_claim':'SOURCE_MASKS_BYTES_ACCEPTED; POL_MASK_OPERATOR_NOT_YET_E2E'}
    if a.analyse:out['low_resolution_support']=analyse_real(a.root,rec,a.out_nside)
    dest=a.output or a.root/'provenance/PLANCK_MASK_SUPPORT_AUDIT.json'
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':'PASS_MASK_BYTE_LOCK','n_masks':len(rec),'support_executed':a.analyse,'result':str(dest),'physics_claim':out['physics_claim']}))
if __name__=='__main__':main()
