"""Finite Planck PR3 POL-mask spin-2 geometry: checked spectral certificate.

Inputs are v2 user-local **already produced** JSON/NPZ outputs. Nothing in this
module claims observed E/B power, an inferred sky coefficient prior, a beam
transfer, matched end-to-end simulations or an astrophysical significance.

Conventions: per ell, [E(m0,cos1,sin1,...), B(m0,cos1,sin1,...)].
K maps high ell6..8 90 real coefficients to low ell2..5 64 real coefficients.
The exact (Q,U)-isotropic mask induces complex linearity K J_H = J_L K.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import tempfile
from pathlib import Path

import numpy as np

SCHEMA = 'htt.L01_native_PR3_POL_ell2to5_vs6to8_geometric_operator/1'
NSIDE = 64
MASKS = ('common', 'three_way_intersection')
# These are the **reported** user-local source hashes, not official signed digests.
V2_INPUT_HASHES = {
    'common': 'c967e45449596c561c940d7ca0d494f1a26d947e6b5a9ef44185fdbf93b036d4',
    'HM': '33226759f339c099818968f777013984f97d5ec2c04e1816f61ae72930b40296',
    'OE': '1b2b4138f791b739938485fa0ebcac5f462e04fbc55626e93d71abd04aac3900',
}
PINNED_V2_MANIFEST_SHA = '3818b3c399c7c12320bf861697576d289788fe6d74dde3d6d220e276e4fb897e'
SUPPORTED_POLICY = 'threshold_after_ud_grade_per_source_then_binary_intersection'
# One user-supplied 2026-10-17 native run, independently pinned as a local receipt.
# These are NOT publisher-side fingerprints or all-sky physical null results.
USER_REPORTED_K = {
    'common': {'pixels':38329,
        'mask_sha256':'7f586d02e8ff62f0846264a91e211790e486c6f58a879564f75b8c6cd0b3ba54',
        'npz_sha256':'a45acd13c079bd871b6704dc6d4952ee6294db0f3f50403978abbd7606f06969',
        'norm':1.2813681702334279},
    'three_way_intersection': {'pixels':37054,
        'mask_sha256':'6bc8c073766f283efaf71b0ef6ec054f61dc94be15240bfa796a612f56176a16',
        'npz_sha256':'3df2b8f2624ea7c831f72979788f08c176e3eaff661865d7759a9434c5ae9a59',
        'norm':1.2993976990506202},
}



def digest_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def eb_indices(ells: tuple[int, ...]) -> tuple[np.ndarray, np.ndarray]:
    e, b, offset = [], [], 0
    for ell in ells:
        if ell < 2:
            raise ValueError('spin2 supports ell>=2')
        count = 2 * ell + 1
        e.extend(range(offset, offset + count))
        b.extend(range(offset + count, offset + 2 * count))
        offset += 2 * count
    return np.asarray(e, dtype=int), np.asarray(b, dtype=int)


def coefficient_complex_structure(ells: tuple[int, ...]) -> np.ndarray:
    """J maps (e,b) -> (-b,e) in the per-ell source layout."""
    e, b = eb_indices(ells)
    j = np.zeros((len(e) + len(b),) * 2, dtype=np.float64)
    j[e, b] = -1.
    j[b, e] = 1.
    return j


def inspect_operator(K: np.ndarray, *, relative_symmetry_tolerance: float = 2e-10) -> dict:
    """Validate *geometric* E/B complex linearity and exact finite sharp bounds.

    Raises on scientific convention mismatch. The threshold is a roundoff guard
    for double precision finite matrices, not an observational significance cut.
    """
    K = np.asarray(K)
    if K.shape != (64, 90) or not np.issubdtype(K.dtype, np.number) or np.iscomplexobj(K):
        raise ValueError('expected real 64x90 spin2 response')
    if not np.isfinite(K).all():
        raise ValueError('nonfinite spin2 response')
    K = K.astype(np.float64, copy=False)
    low = (2, 3, 4, 5)
    high = (6, 7, 8)
    jl = coefficient_complex_structure(low)
    jh = coefficient_complex_structure(high)
    intertwine = K @ jh - jl @ K
    rel_sym = np.linalg.norm(intertwine) / max(np.linalg.norm(K), np.finfo(float).tiny)
    if rel_sym > relative_symmetry_tolerance:
        raise ValueError(f'E_B_COMPLEX_STRUCTURE_BROKEN relative={rel_sym:.6g}')
    el, bl = eb_indices(low)
    eh, bh = eb_indices(high)
    ee, eb, be, bb = (K[np.ix_(el, eh)], K[np.ix_(el, bh)],
                      K[np.ix_(bl, eh)], K[np.ix_(bl, bh)])
    pair_residual = max(float(np.max(np.abs(ee-bb))), float(np.max(np.abs(eb+be))))
    s = np.linalg.svd(K, compute_uv=False)
    s_ee = np.linalg.svd(ee, compute_uv=False)
    s_eb = np.linalg.svd(eb, compute_uv=False)
    # Exact realification K=[[A,B],[-B,A]] is equivalent to A-iB.
    complex_K = ee-1j*eb
    s_complex = np.linalg.svd(complex_K,compute_uv=False)
    doublet_residual = float(np.max(np.abs(s[0::2] - s[1::2])))
    complex_svd_residual = float(np.max(np.abs(s[0::2]-s_complex)))
    rank_threshold = float(max(K.shape) * np.finfo(float).eps * s[0])
    rank = int(np.count_nonzero(s > rank_threshold))
    be_rank_threshold = float(max(be.shape)*np.finfo(float).eps*s_eb[0])
    be_rank = int(np.count_nonzero(s_eb>be_rank_threshold))
    if complex_svd_residual > 5e-10 * max(1.,float(s[0])) or rank%2:
        raise ValueError('COMPLEX_SPECTRAL_DOUBLET_MISMATCH')
    # E and B blocks should share complex structure; unit high-E -> low-B
    # is a coefficient-space bound, not an observed B-mode amplitude.
    norm_E_to_B = float(np.linalg.norm(be, ord=2))
    norm_B_to_E = float(np.linalg.norm(eb, ord=2))
    norm_total = float(s[0])
    # Construct an attainable unit-coefficient sharp bound for a fixed low-B contrast.
    first_B = np.zeros(64)
    first_B[bl[0]] = 1.0
    sharp_single_B = float(np.linalg.norm(K.T @ first_B))
    if sharp_single_B > 0:
        min_source_for_unit_B_contrast = 1. / sharp_single_B
        optimizer = (K.T @ first_B) / sharp_single_B
        attainable = float(first_B @ K @ optimizer)
    else:
        min_source_for_unit_B_contrast = None
        attainable = 0.0
    if abs(attainable - sharp_single_B) > 5e-12:
        raise ArithmeticError('sharp fixed contrast optimizer failed')
    return {
        'schema': 'htt.L01_spin2_finite_spectral_certificate/1',
        'operator_shape': [64,90],
        'harmonic_range_low': [2,5], 'harmonic_range_high': [6,8],
        'source_basis': 'real E/B m0 cos/sin per ell, HEALPix Galactic polar frame',
        'complex_structure_relative_residual': float(rel_sym),
        'block_pair_max_abs_residual': pair_residual,
        'singular_value_pair_max_abs_residual': doublet_residual,
        'complex_reduction_singular_max_abs_residual':complex_svd_residual,
        'singular_values': [float(a) for a in s],
        'numerical_rank': rank,
        'rank_relative_convention': 'rank when sv > max(shape)*eps*svmax',
        'rank_absolute_threshold': rank_threshold,
        'kernel_dimension': int(90-rank),
        'nonzero_singular_min': float(s[rank-1]) if rank else None,
        'norm_total': norm_total,
        'norm_E_high_to_B_low': norm_E_to_B,
        'norm_B_high_to_E_low': norm_B_to_E,
        'rank_E_high_to_B_low':be_rank,
        'nullity_E_high_to_B_low':45-be_rank,
        'full_low_B_reachability_from_high_E':bool(be_rank==32),
        'smallest_nonzero_singular_E_high_to_B_low':float(s_eb[be_rank-1]) if be_rank else None,
        'best_case_high_E_norm_per_unit_low_B':float(1/s_eb[0]) if s_eb[0]>0 else None,
        'worst_case_high_E_norm_per_unit_low_B':float(1/s_eb[-1]) if be_rank==32 else None,
        'low_B_identification_note':'Only ell6..8 synthetic-harmonic coefficient geometry; none of actual E high amplitudes are supplied.',
        'norm_E_high_to_E_low': float(np.linalg.norm(ee, ord=2)),
        'norm_B_high_to_B_low': float(np.linalg.norm(bb, ord=2)),
        'block_EE_singular_values': [float(x) for x in s_ee],
        'block_EB_singular_values': [float(x) for x in s_eb],
        'sharp_one_unit_high_coefficient_to_low_bound': norm_total,
        'sharp_one_unit_high_E_to_low_B_bound': norm_E_to_B,
        'sharp_one_unit_high_B_to_low_E_bound': norm_B_to_E,
        'sharp_first_low_B_contrast_per_unit_high_norm': sharp_single_B,
        'minimum_high_coefficient_norm_for_unit_first_B_contrast': min_source_for_unit_B_contrast,
        'hypothetical_source_constraint': '||h_ell6to8||_2<=R implies ||Kh||_2<=R||K||; R NOT supplied',
        'physical_B_mode_or_p_value': 'NOT_ESTABLISHED',
    }


def _read_checked_npz(path: Path, expected_sha: str) -> np.ndarray:
    if digest_file(path) != expected_sha:
        raise ValueError(f'NPZ_BYTE_IDENTITY_MISMATCH: {path}')
    with np.load(path, allow_pickle=False) as fd:
        if set(fd.files) != {'K_low2to5_high6to8'}:
            raise ValueError('NPZ_SCHEMA_MISMATCH')
        k = np.array(fd['K_low2to5_high6to8'], copy=True)
    return k


def verify_receipt(receipt_file: str | Path, *, enforce_reported_pins=True) -> tuple[dict, dict[str,np.ndarray]]:
    source = Path(receipt_file)
    payload = json.loads(source.read_text(encoding='utf-8'))
    if (payload.get('schema') != SCHEMA or payload.get('component') != 'POLARIZATION PMASK'
        or payload.get('support_policy') != SUPPORTED_POLICY
        or payload.get('effective_order') != 'RING'
        or payload.get('effective_nside') != NSIDE
        or payload.get('source_nside') != 2048
        or payload.get('source_order') != 'NESTED'):
        raise ValueError('NATIVE_RECEIPT_CONTRACT_MISMATCH')
    q = payload.get('source_qualification', {})
    if (q.get('source_lock') != 'v2'
        or q.get('source_lock_v2_manifest_sha256') != PINNED_V2_MANIFEST_SHA
        or payload.get('mask_native_sha256') != V2_INPUT_HASHES):
        raise ValueError('V2_SOURCE_IDENTITY_MISMATCH')
    refs = q.get('reference_qualification',{})
    if refs.get('OE') != 'REFERENCE_BYTE_IDENTICAL_TO_PINNED_SOURCE':
        raise ValueError('OE_REFERENCE_QUALIFICATION_MISSING')
    if not (isinstance(payload.get('threshold'), (int,float))
            and float(payload['threshold']) == .5):
        raise ValueError('PREDECLARED_MASK_THRESHOLD_MISMATCH')
    if payload.get('independent_spin2_reference',{}).get('status')!='HEALPY_NATIVE_SIGN_FRAME_MATCH':
        raise ValueError('NATIVE_M0_SPIN_CHECK_MISSING')
    kdata: dict[str,np.ndarray] = {}
    for name in MASKS:
        entry = payload.get(name,{})
        if entry.get('shape') != [64,90] or not isinstance(entry.get('selected_pixels'),int):
            raise ValueError(f'OPERATOR_METADATA_MALFORMED_{name}')
        maskhash = entry.get('ring64_binary_mask_sha256','')
        if len(maskhash) !=64 or any(ch not in '0123456789abcdef' for ch in maskhash):
            raise ValueError(f'EFFECTIVE_MASK_SHA_INVALID_{name}')
        ksha=entry.get('K_npz_sha256','')
        if len(ksha)!=64 or any(ch not in '0123456789abcdef' for ch in ksha):
            raise ValueError(f'NPZ_SHA_INVALID_{name}')
        if enforce_reported_pins:
            old=USER_REPORTED_K[name]
            if (entry['selected_pixels']!=old['pixels'] or
                maskhash!=old['mask_sha256'] or
                ksha!=old['npz_sha256'] or
                not np.isclose(float(entry['norm']),old['norm'],rtol=1e-12,atol=1e-12)):
                raise ValueError(f'USER_REPORTED_NATIVE_OUTPUT_PIN_MISMATCH_{name}')
        npz=Path(entry['output_npz'])
        if not npz.is_absolute():
            npz = (source.parent / npz).resolve()
        kdata[name] = _read_checked_npz(npz,ksha)
        norm = np.linalg.norm(kdata[name],ord=2)
        if not np.isclose(norm, float(entry['norm']), rtol=3e-10, atol=1e-11):
            raise ValueError(f'REPORTED_OPERATOR_NORM_DRIFT_{name}')
    if payload['common']['selected_pixels'] >= payload['three_way_intersection']['selected_pixels']:
        pass
    else:
        raise ValueError('TRIPLE_INTERSECTION_CANNOT_EXCEED_COMMON')
    return payload, kdata


def audit_native_receipt(receipt_file: str | Path, *, enforce_reported_pins=True) -> dict:
    receipt, kmat = verify_receipt(receipt_file, enforce_reported_pins=enforce_reported_pins)
    blocks={k:inspect_operator(v) for k,v in kmat.items()}
    delta=kmat['three_way_intersection']-kmat['common']
    dnorm=float(np.linalg.norm(delta,ord=2))
    lower=abs(blocks['three_way_intersection']['norm_total']-blocks['common']['norm_total'])
    if dnorm+1e-12<lower:
        raise ArithmeticError('SPECTRAL_REVERSE_TRIANGLE_FAILURE')
    el, bl=eb_indices((2,3,4,5))
    eh, bh=eb_indices((6,7,8))
    delta_B_from_E=delta[np.ix_(bl,eh)]
    return {
        'schema':'htt.L01_real_native_K_spectral_audit/1',
        'source_evidence':'user-native PR3 PMASK-derived K, checked NPZ bytes; no observed Q/U',
        'native_receipt_file_sha256':digest_file(receipt_file),
        'source_lock':'v2',
        'user_reported_output_pins_checked': bool(enforce_reported_pins),
        'v2_manifest_sha256':PINNED_V2_MANIFEST_SHA,
        'underlying_source_sha256':V2_INPUT_HASHES,
        'support_policy':SUPPORTED_POLICY,
        'common':blocks['common'],
        'three_way_intersection':blocks['three_way_intersection'],
        'common_vs_three_way':{
          'common_selected_pixels':receipt['common']['selected_pixels'],
          'triple_selected_pixels':receipt['three_way_intersection']['selected_pixels'],
          'removed_pixels':receipt['common']['selected_pixels']-receipt['three_way_intersection']['selected_pixels'],
          'spectral_norm_K_difference':dnorm,
          'reverse_triangle_lower_bound':float(lower),
          'norm_E_to_B_difference':float(np.linalg.norm(delta_B_from_E,ord=2)),
          'sharp_unit_high_coefficient_response_difference':dnorm,
          'interpretation':'Finite geometry only. No physical high-ell coefficient amplitude R given.'},
        'physical_P2_L01':'PENDING_FULL_ELL_TAIL_BEAM_OBS_Q_U_FFP_MATCHED_NULL',
        'paper_submission':'NOT_READY_TO_SUBMIT',
    }


def spin2_full_ell_healpy_check(nside: int = 16, seeds=(101,203)) -> dict:
    """Optional independent m=0,cos,sin mixed E/B synthesis at ell2..8.

    This is stronger than the prior native check restricted to ell2/3 m0.
    Tests harmonic conventions; still does not certify beams or observed Q/U.
    """
    import healpy as hp
    from healpix_ring_coords import pix2ang_ring
    from spin2_finite import block_design
    if nside not in (8,16,32):
        raise ValueError('finite reference nside=8,16,32 only')
    lmax=8
    npix=12*nside*nside
    ipix=np.unique(np.r_[np.arange(0,min(32,npix)),
                            np.linspace(0,npix-1,num=min(npix,128),dtype=int)])
    theta,phi=pix2ang_ring(nside,ipix)
    D=block_design(theta,phi,2,8)
    assert D.shape==(2*len(ipix),154)
    residuals={}
    for seed in seeds:
        rng=np.random.default_rng(seed)
        coeff=rng.standard_normal(154)
        alms=[np.zeros(hp.Alm.getsize(lmax),complex) for _ in range(2)]
        offset=0
        for ell in range(2,lmax+1):
            nm=2*ell+1
            for knd in range(2):
                c=coeff[offset:offset+nm]
                offset+=nm
                alms[knd][hp.Alm.getidx(lmax,ell,0)] = float(c[0])
                for m in range(1,ell+1):
                    alms[knd][hp.Alm.getidx(lmax,ell,m)] = (c[2*m-1]-1j*c[2*m])/np.sqrt(2.)
        Q,U=hp.alm2map_spin(alms,nside,spin=2,lmax=lmax)
        ref=np.r_[Q[ipix],U[ipix]]
        got=D@coeff
        err=float(np.max(abs(ref-got)))
        residuals[str(seed)]=err
        if err>5e-9*max(1.,float(np.max(abs(ref)))):
            raise ValueError(f'HEALPY_ALL_M_SPIN_CONVENTION_MISMATCH {seed} {err}')
    return {'status':'ALL_M_ELL2_TO8_SIGN_FRAME_MATCH',
            'nside':nside,'pixel_count':int(len(ipix)),
            'seeds':list(seeds),'per_seed_max_abs_error':residuals}


def optional_native_replay(original: dict, root: str, compare_root: str) -> dict:
    """Costly opt-in source replay; does not rely on ZIP byte identity of reserialized NPZ."""
    from native_planck_pol_response import run_from_native_source
    with tempfile.TemporaryDirectory(prefix='l01-native-replay-') as tmp:
        outfile=Path(tmp)/'replay.json'
        rebuilt=run_from_native_source(root,outfile,source_lock='v2',compare_root=compare_root)
        out={}
        for key in MASKS:
            src=Path(original[key]['output_npz'])
            with np.load(src, allow_pickle=False) as z:
                ka=np.array(z['K_low2to5_high6to8'],copy=True)
            with np.load(rebuilt[key]['output_npz'],allow_pickle=False) as z:
                kb=np.array(z['K_low2to5_high6to8'],copy=True)
            normdiff=float(np.linalg.norm(ka-kb,ord=2))
            mask_ok=original[key]['ring64_binary_mask_sha256']==rebuilt[key]['ring64_binary_mask_sha256']
            if not mask_ok or normdiff>2e-9:
                raise ValueError(f'PHYSICAL_MASK_REPLAY_MISMATCH {key} {normdiff} {mask_ok}')
            out[key]={'mask_byte_hash_equal':mask_ok,'spectral_difference':normdiff,
                      'operator_numerical_equivalence':'PASS_GEOMETRY_REPLAY'}
        return out


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--receipt',required=True,help='original native geometry JSON')
    ap.add_argument('--out',required=True)
    ap.add_argument('--all-m-spin-check',action='store_true',help='independent healpy all-m real spin2 check')
    ap.add_argument('--native-replay',action='store_true',help='rerun local FITS->mask->K source path')
    ap.add_argument('--root',default=None)
    ap.add_argument('--compare-root',default=None)
    args=ap.parse_args(argv)
    result=audit_native_receipt(args.receipt)
    if args.all_m_spin_check:
        result['all_m_spin_check']=spin2_full_ell_healpy_check()
    else:
        result['all_m_spin_check']='NOT_RUN'
    if args.native_replay:
        if not args.root or not args.compare_root:
            ap.error('--native-replay requires both --root and --compare-root')
        result['native_replay']=optional_native_replay(json.loads(Path(args.receipt).read_text()),args.root,args.compare_root)
    else:
        result['native_replay']='NOT_RUN'
    dest=Path(args.out)
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({'status':'PASS_FINITE_GEOMETRY_SPECTRAL_AUDIT',
                      'out':str(dest), 'source_sha256':result['native_receipt_file_sha256'],
                      'common_norm':result['common']['norm_total'],
                      'triple_norm':result['three_way_intersection']['norm_total'],
                      'delta_norm':result['common_vs_three_way']['spectral_norm_K_difference'],
                      'paper_gate':result['paper_submission']},indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
