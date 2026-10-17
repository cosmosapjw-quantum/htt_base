"""Fail-closed local-only PR3 POL mask T/E/B geometric transfer contract.

Reads original native NESTED NSIDE2048 Planck PR3 common, HM, OE polarization
FITS, performs audited RING conversion via healpy, reduces to NSIDE64,
and computes low(l2..5) vs high(l6..8) spin-2 pseudo-OLS response.
Input must be the user's ORIGINAL source files. Does NOT certify component
separation, beam, noise, foreground, full high-ell tail or physics E2E.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from healpix_ring_coords import pix2ang_ring, healpy_crosscheck
from spin2_finite import block_design,response_from_design,spin2_shell
SOURCE={
  'common':'c967e45449596c561c940d7ca0d494f1a26d947e6b5a9ef44185fdbf93b036d4',
  'HM':'33226759f339c099818968f777013984f97d5ec2c04e1816f61ae72930b40296',
  'OE':'1b2b4138f791b739938485fa0ebcac5f462e04aac3900',
}
NAME={
  'common':'COM_Mask_CMB-common-Mask-Pol_2048_R3.00.fits',
  'HM':'COM_Mask_CMB-HM-Misspix-Mask-Pol_2048_R3.00.fits',
  'OE':'COM_Mask_CMB-OE-Misspix-Mask-Pol_2048_R3.00.fits',
}
EXPECTED_SIZE=201335040


def digest_file(path):
    sha=hashlib.sha256()
    with Path(path).open('rb') as f:
       for block in iter(lambda:f.read(4<<20),b''):
          sha.update(block)
    return sha.hexdigest()


def verify_native_files(root, files=NAME,sha=SOURCE, expected_size=EXPECTED_SIZE):
    base=Path(root)/'planck/PR3/masks'
    results={}
    for k,name in files.items():
        path=base/name
        if not path.is_file() or path.is_symlink():raise FileNotFoundError(f'missing or symlink {path}')
        if expected_size is not None and path.stat().st_size!=expected_size:raise ValueError('FITS source size mismatch '+k)
        with path.open('rb') as f:
            if not f.read(80).startswith(b'SIMPLE  ='):raise ValueError('not FITS '+k)
        obs=digest_file(path)
        if obs!=sha[k]:raise ValueError('FITS original SHA drift '+k)
        results[k]={'path':str(path),'sha256':obs,'source_size_bytes':int(path.stat().st_size)}
    return results


def choose_support(source_arrays,threshold=.5):
    if set(source_arrays)!=set(NAME):raise ValueError('three official polarization masks required')
    if not np.isfinite(threshold) or threshold<0 or threshold>1:raise ValueError('threshold')
    s={k:np.asarray(v) for k,v in source_arrays.items()}
    shape={v.shape for v in s.values()}
    if len(shape)!=1 or any(v.ndim!=1 for v in s.values()):raise ValueError('same RING support needed')
    if any(not np.isfinite(v).all() or (v<-.00001).any() or (v>1.00001).any() for v in s.values()):raise ValueError('mask range')
    masks={k:v>threshold for k,v in s.items()}
    return {'common':masks['common'], 'three_way_intersection':np.logical_and.reduce(list(masks.values()))}, {k:int(v.sum()) for k,v in masks.items()}


def response_from_binary_mask(selection,nside,low=(2,5),high=(6,8)):
    sel=np.asarray(selection)
    if sel.dtype!=np.bool_ or sel.shape!=(12*nside*nside,):raise ValueError('RING selection shape')
    if sel.sum()<=80:raise ValueError('low spin rank impossible')
    ipix=np.flatnonzero(sel)
    th,ph=pix2ang_ring(nside,ipix)
    L=block_design(th,ph,*low)
    H=block_design(th,ph,*high)
    K,meta=response_from_design(L,H,np.ones(len(ipix),dtype=bool))
    assert K.shape==(64,90)
    return K,meta


def independent_healpy_spin_convention_check(nside=8):
    """Crosscheck E/B signs, spin basis and e_theta/e_phi orientation.

    Uses independent HEALPix spin harmonic synthesis (alm2map_spin), not a
    duplicate call to the local Wigner-d routine. Stops physical pipeline
    on mismatches instead of fitting an unknown global sign in hindsight.
    """
    import healpy as hp
    ip=np.arange(12*nside*nside)
    theta,phi=pix2ang_ring(nside,ip)
    err={}
    for ell in (2,3):
        design=spin2_shell(theta,phi,ell)
        for kind in ('E','B'):
            almE=np.zeros(hp.Alm.getsize(ell),dtype=complex)
            almB=np.zeros_like(almE)
            array=almE if kind=='E' else almB
            array[hp.Alm.getidx(ell,ell,0)]=1.
            q,u=hp.alm2map_spin([almE,almB],nside,spin=2,lmax=ell)
            col=0 if kind=='E' else 2*ell+1
            local=np.r_[q,u]
            err[f'{ell}_{kind}_m0']=float(np.max(abs(local-design[:,col])))
    largest=max(err.values())
    if largest>5e-7:
        raise RuntimeError(f'healpy CMB spin-2 sign/frame convention mismatch {largest}: {err}')
    return {'max_abs_difference':largest,'per_mode':err,'status':'HEALPY_NATIVE_SIGN_FRAME_MATCH'}


def run_from_native_source(root,out,nside=64,threshold=.5):
    receipt=verify_native_files(root)
    try:
        import healpy as hp
    except ImportError as e:raise RuntimeError('pip install healpy astropy; cannot read native PR3 FITS') from e
    if nside!=64:raise ValueError('fixed chosen local contract nside=64')
    spin_reference=independent_healpy_spin_convention_check()
    arrays={};info={}
    for k in ['common','HM','OE']:
        full,h=hp.read_map(receipt[k]['path'],field=0,nest=False,dtype=np.float32,h=True)
        hdr=dict(h)
        if int(hdr.get('NSIDE',0))!=2048 or str(hdr.get('ORDERING','')).strip().upper()!='NESTED':
            raise ValueError('unexpected original NSIDE / NESTED metadata '+k)
        if len(full)!=12*2048*2048:raise ValueError('FITS geometry')
        # healpy.read_map(...,nest=False) returns RING regardless native NESTED.
        arr=hp.ud_grade(full,nside_out=nside,order_in='RING',order_out='RING')
        arrays[k]=arr
        info[k]={'native_header':{name:hdr.get(name) for name in ['NSIDE','ORDERING','COORDSYS','POLCCONV']},'ring64_min':float(np.min(arr)),'ring64_max':float(np.max(arr))}
        del full
    support,counts=choose_support(arrays,threshold)
    res={'schema':'htt.L01_native_PR3_POL_ell2to5_vs6to8_geometric_operator/1',
         'mask_native_sha256':{k:v['sha256'] for k,v in receipt.items()},
         'source_nside':2048,'source_order':'NESTED','effective_order':'RING','effective_nside':nside,
         'threshold':threshold,'component':'POLARIZATION PMASK','native_headers':info,'source_mask_support_counts':counts,'independent_spin2_reference':spin_reference,
         'pixel_center_crosscheck_vs_healpy':float(healpy_crosscheck(nside,np.array([0,1,255,2048,49151]))),
         'geometry_only':'NOT_AN_E2E_PHYSICAL_TRANSFER_OR_COSMIC_B'}
    for name,mask in support.items():
        K,meta=response_from_binary_mask(mask,nside)
        fname=Path(out).with_name(Path(out).stem+'_'+name+'.npz')
        np.savez_compressed(fname,K_low2to5_high6to8=K)
        res[name]={'selected_pixels':int(mask.sum()),'shape':[64,90],
                   'norm':float(np.linalg.norm(K,ord=2)),'low_identity_residual':meta['low_identity_residual'],
                   'low_condition':meta['low_condition'],
                   'output_npz':str(fname),
                   'K_npz_sha256':digest_file(fname)}
    dest=Path(out);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(res,indent=2,sort_keys=True)+'\n')
    return res

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--root',default='/mnt/extdrive/workdir/htt_open_data')
    ap.add_argument('--out',default='/mnt/extdrive/workdir/htt_open_data/provenance/L01_NATIVE_PR3_POL_K64x90.json')
    ap.add_argument('--threshold',type=float,default=.5)
    ap.add_argument('--verify-only',action='store_true')
    args=ap.parse_args()
    if args.verify_only:print(json.dumps(verify_native_files(args.root),indent=2))
    else:print(json.dumps(run_from_native_source(args.root,args.out,threshold=args.threshold),indent=2))
