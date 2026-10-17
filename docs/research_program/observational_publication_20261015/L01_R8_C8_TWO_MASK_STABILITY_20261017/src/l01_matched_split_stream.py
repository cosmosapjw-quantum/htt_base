"""Same-support native full/HM/OE low fits in ONE shared-basis streaming pass.

Reuses the archived Gram/hole moments and the user's matched_pair kernel.
Only raw Q/U right-hand sides are accumulated. No SHT, smoothing, inpainting,
new Gram calculation, beam correction, noise subtraction or additional sky.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib
import json
from pathlib import Path
import sys
import time

import numpy as np
import l01_matched_window_refit as refit

SCHEMA = 'htt.L01_native_matched_split_stream/1'
PRODUCTS = ('full', 'hm1', 'hm2', 'oe1', 'oe2')
MASKS = refit.NAMES
REFIT_BLOB = '845c4034bd5dacd684a3d83de29bde5179514dc9'
ARCHIVE_BLOB = '2b7453997162e30edeb6803ca0d4d274ec2c8bd3'


def _power_two(n):
    return type(n) is int and n > 0 and n & (n-1) == 0


def stream_raw_rhs(window, coarse, base_nside, nside, design_at, data_at,
                   *, ncoeff=64, nproducts=5, chunk_pixels=8192, progress=None):
    """Accumulate common and removed-shell RHS, with Q rows before U rows.

    data_at(ids) returns (2, len(ids), nproducts); only fixed common*W IDs
    are requested. Missing data INSIDE that support are errors, never new masks.
    design_at(ids) is evaluated once per selected pixel, shared by all maps.
    """
    w = np.asarray(window)
    if (not _power_two(base_nside) or not _power_two(nside) or nside < base_nside
        or w.dtype != np.bool_ or w.shape != (12*nside*nside,)
        or set(coarse) != set(MASKS) or type(ncoeff) is not int or not 1 <= ncoeff <= 64
        or type(nproducts) is not int or not 1 <= nproducts <= 5
        or type(chunk_pixels) is not int or not 1 <= chunk_pixels <= 65536):
        raise ValueError('STREAM_DIMENSION_OR_MASK_CONTRACT')
    c, t = (np.asarray(coarse[k]) for k in MASKS)
    if any(a.dtype != np.bool_ or a.shape != (12*base_nside**2,) for a in (c,t)):
        raise ValueError('COARSE_MASK_SHAPE_OR_TYPE')
    if np.any(t & ~c):
        raise ValueError('NON_NESTED_FIT_MASKS')
    ratio = (nside//base_nside)**2
    total = {k:np.zeros((ncoeff,nproducts)) for k in ('common','removed_shell')}
    compensation = {k:np.zeros_like(v) for k,v in total.items()}
    counts = {'common':0, 'three_way_intersection':0, 'removed_shell':0}
    last_quarter = -1
    for start in range(0,len(w),chunk_pixels):
        stop = min(len(w),start+chunk_pixels)
        ids = np.arange(start,stop,dtype=np.int64)
        ids = ids[c[ids//ratio] & w[start:stop]]
        if ids.size:
            a = refit.arr(design_at(ids),2)
            x = refit.arr(data_at(ids),3)
            if a.shape != (2*ids.size,ncoeff) or x.shape != (2,ids.size,nproducts):
                raise ValueError('PAIRED_QU_MULTIPRODUCT_SHAPE')
            if np.any(np.abs(x) >= 1e20):
                raise ValueError('INVALID_QU_INSIDE_FIXED_SUPPORT')
            v = x.reshape(2*ids.size,nproducts)
            shell = ~t[ids//ratio]
            rows = np.r_[shell,shell]
            parts = {'common':a.T@v, 'removed_shell':a[rows].T@v[rows]}
            for k, part in parts.items():
                if not np.isfinite(part).all():
                    raise ValueError('RHS_NUMERICAL_OVERFLOW')
                increment = part-compensation[k]
                updated = total[k]+increment
                compensation[k] = (updated-total[k])-increment
                total[k] = updated
            counts['common'] += int(ids.size)
            counts['removed_shell'] += int(shell.sum())
            counts['three_way_intersection'] += int((~shell).sum())
        quarter = 4*stop//len(w)
        if progress is not None and quarter > last_quarter:
            progress(stop,len(w)); last_quarter = quarter
    omega = 4*np.pi/len(w)
    return {**{k:v*omega for k,v in total.items()}, 'selected_pixels':counts,
            'pixel_area':omega, 'basis_pixels_evaluated':counts['common'],
            'Gram_recomputed':False, 'product_count':nproducts}


def selectors(n):
    if n != 64:
        return {'all':np.arange(n)}
    e,b,off = [],[],0
    for ell in range(2,6):
        q = 2*ell+1; e.extend(range(off,off+q)); b.extend(range(off+q,off+2*q)); off += 2*q
    return {'all':np.arange(n), 'E':np.array(e), 'B':np.array(b)}


def linear_subjects(matrix):
    a = refit.arr(matrix,2)
    if not a.shape[0] or a.shape[1] != len(PRODUCTS):
        raise ValueError('EXACT_FIVE_PRODUCT_COLUMNS_REQUIRED')
    out = {p:a[:,j] for j,p in enumerate(PRODUCTS)}
    for label,j,k in (('HM',1,2),('OE',3,4)):
        out[label+'_half_sum'] = a[:,j]/2+a[:,k]/2
        out[label+'_half_difference'] = a[:,j]/2-a[:,k]/2
        out['full_minus_'+label+'_mean'] = a[:,0]-out[label+'_half_sum']
    return out


def solve_products(grams, holes, common_rhs, shell_rhs):
    """Same raw estimator for every product; verify deletion and split linearity.

    S_t*(beta_t-beta_c) = (S_c-S_t)*beta_c-b_shell.
    The shell is computed directly, not by subtracting two nearly equal sums.
    """
    bc, bj = refit.arr(common_rhs,2), refit.arr(shell_rhs,2)
    if bc.shape != bj.shape or bc.shape[1] != 5 or not 1 <= bc.shape[0] <= 64:
        raise ValueError('RHS_FIVE_PRODUCT_SHAPE')
    bt = bc-bj
    original, matched = {}, {}
    for j,p in enumerate(PRODUCTS):
        result = refit.matched_pair(grams,holes,{MASKS[0]:bc[:,j],MASKS[1]:bt[:,j]})
        original[p],matched[p] = result['original'],result['matched']
    old = {k:np.column_stack([original[p][k] for p in PRODUCTS]) for k in MASKS}
    new = {k:np.column_stack([matched[p][k] for p in PRODUCTS]) for k in MASKS}
    s = {k:refit.arr(grams[k],2)-refit.arr(holes[k],2) for k in MASKS}
    delta = new[MASKS[1]]-new[MASKS[0]]
    shell_prediction = np.linalg.solve(s[MASKS[1]], (s[MASKS[0]]-s[MASKS[1]])@new[MASKS[0]]-bj)
    shell_error = refit.close(delta,shell_prediction,'MATCHED_SHELL_IDENTITY',
                             refit.norm(new[MASKS[0]])+refit.norm(new[MASKS[1]]))
    input_subjects = {k:linear_subjects(v) for k,v in ((MASKS[0],bc),(MASKS[1],bt))}
    linear_error = 0.
    for k in MASKS:
        for label,b in input_subjects[k].items():
            direct = np.linalg.solve(s[k],b)
            linear_error = max(linear_error,refit.close(direct,linear_subjects(new[k])[label],
                'SPLIT_FIT_LINEARITY',refit.norm(new[k])))
    ensembles = {'matched_'+k:v for k,v in new.items()}
    ensembles['matched_contrast'] = delta
    ensembles['original_contrast'] = old[MASKS[1]]-old[MASKS[0]]
    stats = {}
    for name,matrix in ensembles.items():
        subjects = linear_subjects(matrix); groups = {}
        for group,ix in selectors(len(matrix)).items():
            vectors = {key:v[ix] for key,v in subjects.items()}
            energies = {key:float(v@v) for key,v in vectors.items()}
            if not np.isfinite(list(energies.values())).all():
                raise ValueError('COEFFICIENT_ENERGY_RANGE')
            pair_checks = {}
            for label,j,k in (('HM','hm1','hm2'),('OE','oe1','oe2')):
                cross = float(vectors[j]@vectors[k])
                difference = energies[label+'_half_sum']-energies[label+'_half_difference']
                err = abs(difference-cross)/max(energies[j]+energies[k],np.finfo(float).tiny)
                if err > 2e-12:
                    raise ValueError('COEFFICIENT_CROSS_IDENTITY')
                pair_checks[label] = {'cross_inner_product_K_CMB2':cross,'identity_relative':err}
            groups[group] = {'norms_K_CMB':{key:refit.norm(v) for key,v in vectors.items()},
                'energies_K_CMB2':energies, 'split_cross_checks':pair_checks,
                'HM_OE_half_difference_inner_product_K_CMB2':float(vectors['HM_half_difference']@vectors['OE_half_difference']),
                'ratios_to_full_energy':{key:v/energies['full'] if energies['full'] else None for key,v in energies.items()}}
        stats[name] = groups
    return {'original_coefficients':old, 'matched_coefficients':new,
            'matched_contrast':delta, 'shell_prediction':shell_prediction,
            'shell_identity_relative':shell_error,'split_linearity_relative':linear_error,
            'statistics':stats, 'coefficient_products_are_ensemble_covariance':False,
            'energy_space':'REAL_LOW64_COEFFICIENT_INNER_PRODUCT_NOT_PSEUDOCL',
            'noise_debiasing':False, 'independent_sky_count':1, 'p_value':None}


def _blob(path):
    b = Path(path).read_bytes()
    return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()


def _identity(path):
    st=Path(path).stat()
    return st.st_size,st.st_mtime_ns,st.st_ino,st.st_dev


def open_qu_table(path, product, npix, read_header):
    p=Path(path)
    if p.is_symlink() or not p.is_file():
        raise ValueError('SOURCE_NOT_REGULAR_FILE')
    before=_identity(p)
    with p.open('rb') as f:
        _,offset=read_header(f,0,before[0]); h,offset=read_header(f,offset,before[0])
    width=10 if product=='full' else 3
    if int(h['NAXIS1'])!=width*4 or int(h['NAXIS2'])!=npix:
        raise ValueError('NATIVE_QU_LAYOUT_CHANGED')
    return np.memmap(p,dtype='>f4',mode='r',offset=offset,shape=(npix,width)),before


def _plain(value):
    if isinstance(value,np.ndarray): return value.tolist()
    if isinstance(value,dict): return {k:_plain(v) for k,v in value.items()}
    if isinstance(value,(tuple,list)): return [_plain(v) for v in value]
    return value


def run(root,native_report,injection_report,native_receipt,chunk_pixels=8192):
    # Only this adapter needs native files/healpy. The shared core tests need neither.
    import l01_matched_window_data as archive
    import l01_smica_processed_bands as producer
    from l01_smica_fits_integrity import _read_header
    import healpy as hp
    previous=archive.previous
    if _blob(refit.__file__)!=REFIT_BLOB or _blob(archive.__file__)!=ARCHIVE_BLOB:
        raise ValueError('PINNED_MATCHED_ESTIMATOR_VERSION_CHANGED')
    versions={archive.injection:archive.INJECTION_SHA256,previous:archive.VISIBILITY_SHA256,
              previous.native:previous.PRODUCER_SHA256}
    if any(previous.digest(mod.__file__)!=sha for mod,sha in versions.items()):
        raise ValueError('PINNED_VALIDATOR_VERSION_CHANGED')
    old,probe,links=archive.load_linked(native_report,injection_report)
    grams,expected_counts=archive.validate_inputs(old,probe)
    if old['product']!='full' or old['nside']!=2048 or type(chunk_pixels) is not int or not 256<=chunk_pixels<=65536:
        raise ValueError('NATIVE_FULL_ANCHOR_OR_CHUNK_CONTRACT')
    contract=old['checkpoint']['contract']
    if (hp.__version__!=contract['healpy_version'] or previous.digest(producer.__file__)!=contract['analysis_code_sha256']
        or previous.digest(native_receipt)!=contract['native_receipt_sha256']):
        raise ValueError('SOURCE_PRODUCER_OR_HEALPY_VERSION_CHANGED')
    for name,sha in contract['dependency_sha256'].items():
        if previous.digest(importlib.import_module(name).__file__)!=sha:
            raise ValueError('SOURCE_DEPENDENCY_CHANGED_'+name)
    # All sources are verified before any multiproduct scan. No downloads.
    sources=producer.check_sources(root,PRODUCTS)
    native,_=producer.verify_receipt(native_receipt,enforce_reported_pins=True)
    window,coarse,window_sha=producer.read_windows(root,hp,native)
    if window_sha!=old['native_window_sha256']:
        raise ValueError('FIXED_SOURCE_WINDOW_CHANGED')
    nested={k:hp.reorder(coarse[k].astype(np.uint8),r2n=True).astype(bool) for k in MASKS}
    tables,identities={},{}
    started=time.perf_counter()
    try:
        for p in PRODUCTS:
            tables[p],identities[p]=open_qu_table(sources[p]['path'],p,len(window),_read_header)
        def data_at(ids):
            return np.stack([np.stack((tables[p][ids,1],tables[p][ids,2])) for p in PRODUCTS],axis=-1)
        def design_at(ids):
            theta,phi=hp.pix2ang(2048,ids,nest=True)
            return producer.block_design(theta,phi,2,5)
        def progress(done,total):
            print(json.dumps({'phase':'SHARED_NATIVE_RAW_RHS','completed_pixels':done,
                              'total_pixels':total,'products':list(PRODUCTS)}),flush=True)
        rhs=stream_raw_rhs(window,nested,64,2048,design_at,data_at,chunk_pixels=chunk_pixels,progress=progress)
        for p in PRODUCTS:
            if _identity(sources[p]['path'])!=identities[p]:
                raise ValueError('SOURCE_CHANGED_DURING_SCAN_'+p)
    finally:
        for table in tables.values(): table._mmap.close()
    for k in MASKS:
        if rhs['selected_pixels'][k]!=expected_counts[k]:
            raise ValueError('FIXED_MATCHED_SUPPORT_COUNT_MISMATCH_'+k)
    bt=rhs['common']-rhs['removed_shell']
    replay={}
    for k,b in ((MASKS[0],rhs['common'][:,0]),(MASKS[1],bt[:,0])):
        saved=np.asarray(old['solver_states'][k]['rhs'])[:,0]
        replay[k]=refit.close(b,saved,'FULL_RAW_NATIVE_RHS_REPLAY_MISMATCH_'+k)
    result=solve_products(grams,probe['hole_moments'],rhs['common'],rhs['removed_shell'])
    anchor=refit.matched_pair(grams,probe['hole_moments'],
        {k:np.asarray(old['solver_states'][k]['rhs'])[:,0] for k in MASKS})
    refit.close(result['matched_contrast'][:,0],anchor['matched_contrast'],
                'FULL_MATCHED_VECTOR_REPLAY_MISMATCH',sum(refit.norm(v) for v in anchor['matched'].values()))
    return _plain({'schema':SCHEMA,'status':'PASS_NATIVE_MATCHED_SPLIT_ACCOUNTING',
        'input_evidence':links,'sources':sources,'source_window_sha256':window_sha,
        'nside':2048,'input_fields':'Q_STOKES_U_STOKES_NOT_INPAINTED',
        'products':list(PRODUCTS),'coefficient_ells':[2,3,4,5],
        'direct_input_high_ell_truncated':False,'native_SHT_run':False,'beam_applied_again':False,
        'old_estimator_or_files_replaced':False,'raw_moments':rhs,
        'grams':grams,'hole_moments':probe['hole_moments'],
        'full_native_moment_replay':replay,'result':result,'seconds':time.perf_counter()-started,
        'dependency_sha256':{mod.__name__:previous.digest(mod.__file__) for mod in (refit,archive,producer,previous,previous.native,archive.injection)},
        'interpretation':'SAME_ESTIMATOR_NATIVE_SPLIT_DIAGNOSTIC_NOT_COSMIC_EB_OR_CALIBRATED_NULL',
        'high_ell_physical_identification':False,'paper_gate':'NOT_READY_TO_SUBMIT'})


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',required=True);ap.add_argument('--native-report',required=True)
    ap.add_argument('--injection-report',required=True);ap.add_argument('--native-receipt',required=True)
    ap.add_argument('--chunk-pixels',type=int,default=8192);ap.add_argument('--out',required=True)
    args=ap.parse_args(argv)
    try:
        if Path(args.out).exists() or Path(args.out).is_symlink():
            raise ValueError('OUTPUT_EXISTS_NOT_OVERWRITTEN')
        report=run(args.root,args.native_report,args.injection_report,args.native_receipt,args.chunk_pixels)
        import l01_native_residual_visibility as previous
        report['code_sha256']=previous.digest(__file__)
        previous.write_new(args.out,report)
    except (ValueError,TypeError,OSError,ImportError,KeyError,OverflowError,FloatingPointError,np.linalg.LinAlgError) as exc:
        print(json.dumps({'status':'BLOCKED','error_type':type(exc).__name__,'error':str(exc)}),file=sys.stderr)
        return 2
    print(json.dumps({'status':report['status'],'selected_pixels':report['raw_moments']['selected_pixels'],
        'full_native_moment_replay':report['full_native_moment_replay'],
        'matched_contrast':report['result']['statistics']['matched_contrast'],
        'out':args.out,'paper_gate':report['paper_gate']},indent=2,allow_nan=False))
    return 0


if __name__=='__main__':raise SystemExit(main())
