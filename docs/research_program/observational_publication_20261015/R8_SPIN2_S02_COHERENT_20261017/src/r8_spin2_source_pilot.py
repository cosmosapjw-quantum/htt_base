"""Native-looking spin2 block audit on original R8 PR3 TEMPERATURE intersection.

IMPORTANT: R8 mask is NOT the official PR3 polarization confidence mask.
No `L01` physical completion, E/B source power, high-ell sky realization, beam,
foreground, component separation, or E2E instrument null admitted.

When given a true Planck POL NSIDE64 RING selection obtained from the official
NESTED 2048 FITS, this finite geometric routine can be rerun unmodified.
"""
from __future__ import annotations
import hashlib,json
from pathlib import Path
import numpy as np
from healpix_ring_coords import pix2ang_ring
from spin2_finite import block_design,response_from_design
R8_SOURCE_SHA='196ea21a8bf8a7077560599117390d8e48e77ab2fc91194639fd5ca656e9ec7b'
R8_MASK_ARRAY_SHA='2d8de2e26e7781d60438206c96016b6ead5d07455d67267e6d4d85d717220311'


def audit_source_mask(npz, *, source_digest=R8_SOURCE_SHA, nside=64, low=(2,5),high=(6,8)):
    path=Path(npz)
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    if source_digest is not None and digest!=source_digest:raise ValueError('source SHA mismatch')
    with np.load(path,allow_pickle=False) as z:mask=z['common_mask']
    if mask.dtype!=np.bool_ or mask.shape!=(12*nside*nside,):raise ValueError('one source RING mask needed')
    masksha=hashlib.sha256(mask.tobytes()).hexdigest()
    if masksha!=R8_MASK_ARRAY_SHA and source_digest==R8_SOURCE_SHA:raise ValueError('source mask drift')
    if sum(mask)<200:raise ValueError('too few pixels for spin2 low block')
    th,ph=pix2ang_ring(nside,np.flatnonzero(mask))
    lo=block_design(th,ph,*low)
    hi=block_design(th,ph,*high)
    K,meta=response_from_design(lo,hi,np.ones(len(th),dtype=bool))
    # low E/B ordering: ell2 E5 B5, ell3 E7 B7, ...; high likewise
    idx=lambda x,y,code:np.array([j for l in range(x,y+1) for j in range(sum(2*(2*k+1) for k in range(x,l)) + ((2*l+1) if code=='B' else 0), sum(2*(2*k+1) for k in range(x,l)) + ((2*l+1) if code=='B' else 0) + (2*l+1))])
    EL,BL=idx(*low,'E'),idx(*low,'B');EH,BH=idx(*high,'E'),idx(*high,'B')
    norms={f'{out}_from_{inn}':float(np.linalg.norm(K[np.ix_(ix,jx)],ord=2))
           for out,ix in [('E',EL),('B',BL)] for inn,jx in [('E',EH),('B',BH)]}
    raw=np.asarray(mask,dtype=bool)
    return {'schema':'htt.r8_planck_temperature_mask_spin2_geometry_pilot/1',
            'source':{'r8_cmb_controls_npz_sha256':digest,'temperature_intersection_mask_array_sha256':masksha,
                      'source_id':'R8_SAME_SKY_PIXEL_CONTROL_V1','official_PR3_POL_mask':'NOT_PROVIDED','NSIDE':nside,'ORDERING':'RING'},
            'low_range':list(low),'high_range':list(high),'matrix_shape':list(K.shape),
            'source_selected_pixels':int(raw.sum()),'source_fraction':float(raw.mean()),
            'response_operator_norm':float(np.linalg.norm(K,ord=2)),
            'four_block_norms':norms,
            'low_condition':meta['low_condition'],
            'low_identity_residual':meta['low_identity_residual'],
            'response_status':'SOURCE_REAL_TEMPERATURE_MASK_WITH_MANUFACTURED_SPIN2_FIELDS_ONLY',
            'physical_gate':'L01_PENDING_UNTIL_NATIVE_POL_MASK_BEAM_AND_TRANSFER_VERIFIED'},K


def run(root,output):
    obj,K=audit_source_mask(root)
    path=Path(output);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')
    np.savez_compressed(path.with_suffix('.npz'),K_lowhigh=K)
    return obj

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--mask-source',type=Path,default=Path('source/r8_cmb_controls.npz'));ap.add_argument('--output',type=Path,default=Path('results/R8_T_MASK_SPIN2_PILOT.json'));args=ap.parse_args()
    print(json.dumps(run(args.mask_source,args.output),indent=2))
