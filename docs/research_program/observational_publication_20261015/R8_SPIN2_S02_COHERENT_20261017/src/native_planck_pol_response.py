"""Fail-closed local-only PR3 POL mask spin-2 geometric response.

Immutable source-byte admission and scoped scientific semantic comparison are separate.
The manuscript P2/L01 remains held until qualified POL/beam/FFP matched null inputs.
"""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
import numpy as np
from fits_source_identity import (audit_source_files, SourceIdentityError,
                                  inspect_planck_pmask, semantic_compare_pmask,
                                  classify_byte_semantic, digest_file)
from healpix_ring_coords import pix2ang_ring, healpy_crosscheck
from spin2_finite import block_design, response_from_design, spin2_shell
from source_lock_v2 import load_v2_manifest, qualify_v2, require_v2_admission, V2_ACCEPTED

SOURCE = {
    'common': 'c967e45449596c561c940d7ca0d494f1a26d947e6b5a9ef44185fdbf93b036d4',
    'HM': '33226759f339c099818968f777013984f97d5ec2c04e1816f61ae72930b40296',
    # Historical lock is malformed (45 hexadecimal digits), not a real SHA256.
    # Preserve the bad original as evidence; never substitute the local observed hash.
    'OE': '1b2b4138f791b739938485fa0ebcac5f462e04aac3900',
}
NAME = {
    'common': 'COM_Mask_CMB-common-Mask-Pol_2048_R3.00.fits',
    'HM': 'COM_Mask_CMB-HM-Misspix-Mask-Pol_2048_R3.00.fits',
    'OE': 'COM_Mask_CMB-OE-Misspix-Mask-Pol_2048_R3.00.fits',
}
EXPECTED_SIZE = 201335040


def audit_native_identity(root, compare_root=None, files=NAME, sha=SOURCE,
                          expected_size=EXPECTED_SIZE, nside=2048):
    """Diagnostic receipts NEVER change admission policy or pin hashes.

    Semantic comparisons require an independently qualified candidate reference;
    their reported equivalence is restricted to decoded Planck PMASK pixels.
    """
    receipt = audit_source_files(root, files, sha, expected_size)
    for k, entry in receipt.items():
        candidate = Path(entry['path'])
        entry['structural_status'] = 'NOT_EVALUATED'
        if candidate.is_file() and not candidate.is_symlink():
            try:
                geometry = inspect_planck_pmask(candidate, nside=nside)
                entry['structural_status'] = 'PLANCK_PMASK_LAYOUT_VALID'
                entry['fits_layout'] = {x: v for x, v in geometry.items() if x != 'data_offset'}
            except (ValueError, KeyError, OSError) as exc:
                entry['structural_status'] = 'STRUCTURAL_MISMATCH'
                entry['structure_diagnostic'] = str(exc)
        entry['semantic_status'] = 'SEMANTIC_NOT_EVALUATED_NO_REFERENCE'
        if compare_root is not None and entry['structural_status'] == 'PLANCK_PMASK_LAYOUT_VALID':
            reference = Path(compare_root) / 'planck/PR3/masks' / files[k]
            entry['reference_path'] = str(reference)
            if reference.is_file() and not reference.is_symlink():
                entry['reference_observed_sha256'] = digest_file(reference)
                try:
                    s = semantic_compare_pmask(candidate, reference, nside=nside)
                    entry['semantic_status'] = s['semantic_status']
                    entry['semantic_comparison'] = s
                except (ValueError, KeyError, OSError) as exc:
                    entry['semantic_status'] = 'SEMANTIC_NOT_EVALUATED_UNSUPPORTED_REFERENCE'
                    entry['semantic_diagnostic'] = str(exc)
        entry['admission'] = classify_byte_semantic(entry['byte_status'], entry['semantic_status'])
        # File integrity, source provenance and qualified observational science are independent.
        if entry['structural_status'] == 'STRUCTURAL_MISMATCH':
            entry['admission'] = 'BLOCK_STRUCTURAL_MISMATCH'
        entry['scientific_status'] = 'P2_L01_NOT_READY_FOR_PHYSICAL_CLAIM'
    return receipt


def verify_native_files(root, files=NAME, sha=SOURCE, expected_size=EXPECTED_SIZE):
    """Compatibility with the original API: fail closed; no partial admission."""
    report = audit_source_files(root, files, sha, expected_size)
    if any(v['byte_status'] != 'BYTE_IDENTICAL' for v in report.values()):
        raise SourceIdentityError(report)
    for k, r in report.items():
        p = Path(r['path'])
        with p.open('rb') as f:
            if not f.read(80).startswith(b'SIMPLE  ='):
                raise ValueError('not FITS ' + k)
        if set(files) == set(NAME):
            inspect_planck_pmask(p)
    return {k: {'path': r['path'], 'sha256': r['observed_sha256'],
                'source_size_bytes': r['source_size_bytes']} for k, r in report.items()}


def choose_support(source_arrays, threshold=.5):
    if set(source_arrays) != set(NAME):
        raise ValueError('three official polarization masks required')
    if not np.isfinite(threshold) or threshold<0 or threshold>1:
        raise ValueError('threshold')
    s={k: np.asarray(v) for k, v in source_arrays.items()}
    if len({v.shape for v in s.values()})!=1 or any(v.ndim!=1 for v in s.values()):
        raise ValueError('same RING support needed')
    if any(not np.isfinite(v).all() or (v<-.00001).any() or (v>1.00001).any() for v in s.values()):
        raise ValueError('mask range')
    masks={k:v>threshold for k,v in s.items()}
    return ({'common':masks['common'],
             'three_way_intersection':np.logical_and.reduce(list(masks.values()))},
            {k:int(v.sum()) for k,v in masks.items()})


def canonical_ring64_mask_sha256(selection):
    """Canonical byte identity for RING64 support: 1 byte per boolean pixel, C order."""
    mask=np.asarray(selection)
    if mask.dtype!=np.bool_ or mask.shape!=(12*64*64,):
        raise ValueError('expected complete RING64 boolean mask')
    return hashlib.sha256(mask.astype(np.uint8).tobytes(order='C')).hexdigest()


def response_from_binary_mask(selection,nside,low=(2,5),high=(6,8)):
    sel=np.asarray(selection)
    if sel.dtype!=np.bool_ or sel.shape!=(12*nside*nside,):
        raise ValueError('RING selection shape')
    if sel.sum()<=80:
        raise ValueError('low spin rank impossible')
    ipix=np.flatnonzero(sel)
    th,ph=pix2ang_ring(nside,ipix)
    L=block_design(th,ph,*low)
    H=block_design(th,ph,*high)
    K,meta=response_from_design(L,H,np.ones(len(ipix),dtype=bool))
    assert K.shape==(64,90)
    return K,meta


def independent_healpy_spin_convention_check(nside=8):
    """Independent CMB polarization basis verification, not fitted sign flipping."""
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
            err[f'{ell}_{kind}_m0']=float(np.max(abs(np.r_[q,u]-design[:,col])))
    largest=max(err.values())
    if largest>5e-7:
        raise RuntimeError(f'healpy CMB spin-2 sign/frame convention mismatch {largest}: {err}')
    return {'max_abs_difference':largest,'per_mode':err,'status':'HEALPY_NATIVE_SIGN_FRAME_MATCH'}


def run_from_native_source(root,out,nside=64,threshold=.5,source_lock="v1",compare_root=None):
    if source_lock == "v1":
        receipt=verify_native_files(root)
        source_receipt={"source_lock": "v1", "reference_provenance": "NOT_APPLICABLE"}
    elif source_lock == "v2":
        manifest=load_v2_manifest()
        qualified=qualify_v2(root, compare_root, names=NAME,
                              expected_sha=manifest["expected_sha256"],
                              expected_size=EXPECTED_SIZE)
        receipt=require_v2_admission(qualified)
        source_receipt={"source_lock": "v2",
                        "reference_provenance": manifest["reference_qualification"],
                        "reference_qualification": {k:v["reference_status"] for k,v in qualified.items()},
                        "source_lock_v2_manifest_sha256": digest_file(Path(__file__).resolve().parents[1]/"research/OE_SOURCE_LOCK_V2.json")}
    else:
        raise ValueError("UNSUPPORTED_SOURCE_LOCK")
    try:
        import healpy as hp
    except ImportError as e:
        raise RuntimeError('pip install healpy astropy; cannot read native PR3 FITS') from e
    if nside!=64:
        raise ValueError('fixed chosen local contract nside=64')
    spin_reference=independent_healpy_spin_convention_check()
    arrays={};info={}
    for k in ['common','HM','OE']:
        full,h=hp.read_map(receipt[k]['path'],field=0,nest=False,dtype=np.float32,h=True)
        hdr=dict(h)
        if int(hdr.get('NSIDE',0))!=2048 or str(hdr.get('ORDERING','')).strip().upper()!='NESTED':
            raise ValueError('unexpected original NSIDE / NESTED metadata '+k)
        if len(full)!=12*2048*2048:
            raise ValueError('FITS geometry')
        arr=hp.ud_grade(full,nside_out=nside,order_in='RING',order_out='RING')
        arrays[k]=arr
        info[k]={'native_header':{name:hdr.get(name) for name in ['NSIDE','ORDERING','COORDSYS','POLCCONV']},
                 'ring64_min':float(np.min(arr)),'ring64_max':float(np.max(arr))}
        del full
    support,counts=choose_support(arrays,threshold)
    res={'schema':'htt.L01_native_PR3_POL_ell2to5_vs6to8_geometric_operator/1',
         'source_qualification':source_receipt,
         'mask_native_sha256':{k:v['sha256'] for k,v in receipt.items()},
         'source_nside':2048,'source_order':'NESTED','effective_order':'RING','effective_nside':nside,
         'threshold':threshold,'component':'POLARIZATION PMASK','native_headers':info,
         'support_policy':'threshold_after_ud_grade_per_source_then_binary_intersection',
         'coarsening_intersection_commutation_assumed':False,
         'source_mask_support_counts':counts,'independent_spin2_reference':spin_reference,
         'pixel_center_crosscheck_vs_healpy':float(healpy_crosscheck(nside,np.array([0,1,255,2048,49151]))),
         'geometry_only':'NOT_AN_E2E_PHYSICAL_TRANSFER_OR_COSMIC_B'}
    dest=Path(out);dest.parent.mkdir(parents=True,exist_ok=True)
    for name,mask in support.items():
        K,meta=response_from_binary_mask(mask,nside)
        fname=dest.with_name(dest.stem+'_'+name+'.npz')
        np.savez_compressed(fname,K_low2to5_high6to8=K)
        res[name]={'selected_pixels':int(mask.sum()),'shape':[64,90],
                   'ring64_binary_mask_sha256':canonical_ring64_mask_sha256(mask),
                   'norm':float(np.linalg.norm(K,ord=2)),
                   'low_identity_residual':meta['low_identity_residual'],
                   'low_condition':meta['low_condition'], 'output_npz':str(fname),
                   'K_npz_sha256':digest_file(fname)}
    dest.write_text(json.dumps(res,indent=2,sort_keys=True)+'\n')
    return res


def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument('--root',default='/mnt/extdrive/workdir/htt_open_data')
    ap.add_argument('--out',default='/mnt/extdrive/workdir/htt_open_data/provenance/L01_NATIVE_PR3_POL_K64x90.json')
    ap.add_argument('--threshold',type=float,default=.5)
    ap.add_argument('--verify-only',action='store_true')
    ap.add_argument('--compare-root',default=None,help='native reference root; mandatory for v2 admission')
    ap.add_argument('--source-lock',choices=['v1','v2'],default='v1',
                    help='v1 original historical lock, v2 opt-in reference-compared lock')
    args=ap.parse_args(argv)
    if args.verify_only:
        if args.source_lock == 'v1':
            result=audit_native_identity(args.root,compare_root=args.compare_root)
            print(json.dumps(result,indent=2,sort_keys=True))
            return 0 if all(e['admission']=='ORIGINAL_BYTES_ADMITTED' for e in result.values()) else 2
        manifest=load_v2_manifest()
        result=qualify_v2(args.root,args.compare_root,names=NAME,
                          expected_sha=manifest['expected_sha256'],
                          expected_size=EXPECTED_SIZE)
        print(json.dumps(result,indent=2,sort_keys=True))
        return 0 if all(e['admission'] in V2_ACCEPTED for e in result.values()) else 2
    try:
        result=run_from_native_source(args.root,args.out,threshold=args.threshold,
                                      source_lock=args.source_lock,compare_root=args.compare_root)
    except SourceIdentityError as exc:
        print(json.dumps({'error':'SOURCE_IDENTITY_NOT_ADMITTED', 'receipt':exc.receipt},indent=2,sort_keys=True),file=sys.stderr)
        return 2
    print(json.dumps(result,indent=2))
    return 0


if __name__=='__main__':
    sys.exit(main())
