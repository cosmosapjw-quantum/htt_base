"""Known low E/B input response of the existing native L01 comparator.

Reuse saved fit Grams. Only visit pixels in M_common AND NOT W_native when
building new low-mode moments: no observed Q/U reads and no native SHT.
The matched-window control is a distinct finite-band estimator, not a change
of archived results, a full-sky purification or a physical high-tail bound.
"""
from __future__ import annotations
import argparse
import importlib
import json
from pathlib import Path
import sys
import time
import numpy as np

SCHEMA='htt.L01_windowed_low_source_injection/1'
MASKS=('common','three_way_intersection')
CONDITION_LIMIT=1e8


def _real(value, ndim):
    a=np.asarray(value)
    if a.ndim!=ndim or a.dtype.kind not in 'fiu' or np.iscomplexobj(a):
        raise ValueError('REAL_ARRAY_SHAPE_OR_TYPE')
    a=a.astype(float,copy=False)
    if not np.isfinite(a).all():
        raise ValueError('NONFINITE_ARRAY')
    return a


def _symmetric(value, scale):
    a=_real(value,2)
    if not a.size or a.shape[0]!=a.shape[1]:
        raise ValueError('SQUARE_MATRIX_REQUIRED')
    if np.linalg.norm(a-a.T,ord=2)>512*np.finfo(float).eps*scale:
        raise ValueError('MOMENT_NOT_SYMMETRIC')
    return (a+a.T)/2


def response_from_holes(grams, holes):
    """R_i=I-G_i^-1 C_i; DeltaR=Gc^-1 Cc-Gt^-1 Ct, C_i=A^T M_i(1-W)A.

    All matrices include the SAME pixel-area factor. This avoids subtracting
    two near-identity responses to obtain a small contrast. No inverse is formed.
    """
    if set(grams)!=set(MASKS) or set(holes)!=set(MASKS):
        raise ValueError('TWO_MATCHED_MASK_MOMENTS_REQUIRED')
    g={k:_real(grams[k],2) for k in MASKS}
    n=g[MASKS[0]].shape[0]
    if not 1<=n<=64 or any(v.shape!=(n,n) for v in g.values()):
        raise ValueError('GRAM_SHAPE')
    scale=max(np.linalg.norm(v,2) for v in g.values())
    if not np.isfinite(scale) or scale<=0:
        raise ValueError('GRAM_SCALE')
    g={k:_symmetric(v,scale) for k,v in g.items()}
    c={k:_symmetric(holes[k],scale) for k in MASKS}
    if any(v.shape!=(n,n) for v in c.values()):
        raise ValueError('HOLE_MOMENT_SHAPE')
    slack=512*np.finfo(float).eps*scale
    for k in MASKS:
        ev=np.linalg.eigvalsh(g[k])
        if ev[0]<=0 or ev[-1]/ev[0]>CONDITION_LIMIT:
            raise ValueError('FIT_GRAM_NOT_POSITIVE_OR_CONDITIONED')
    cc,ct=(c[k] for k in MASKS);gc,gt=(g[k] for k in MASKS)
    for v in (cc,ct,cc-ct,gc-gt,gc-cc,gt-ct,(gc-gt)-(cc-ct)):
        if np.linalg.eigvalsh(v)[0]<-slack:
            raise ValueError('INCONSISTENT_BINARY_NESTED_MASK_MOMENTS')
    defects={k:np.linalg.solve(g[k],c[k]) for k in MASKS}
    responses={k:np.eye(n)-defects[k] for k in MASKS}
    difference=defects[MASKS[0]]-defects[MASKS[1]]
    controls={}
    for k in MASKS:
        match=g[k]-c[k];ev=np.linalg.eigvalsh(match)
        if ev[0]>slack and ev[-1]/ev[0]<=CONDITION_LIMIT:
            r=np.linalg.solve(match,match)
            controls[k]={'status':'FINITE_LOW_MODEL_IDENTIFIABLE',
                         'condition':float(ev[-1]/ev[0]),'response':r.tolist(),
                         'identity_max_abs':float(np.max(abs(r-np.eye(n))))}
        else:
            controls[k]={'status':'MATCHED_LOW_MODEL_NOT_NUMERICALLY_IDENTIFIABLE',
                         'condition':None,'response':None,'identity_max_abs':None}
    residual=max(float(np.linalg.norm(g[k]@responses[k]-(g[k]-c[k]),2)/scale) for k in MASKS)
    if residual>2e-11:
        raise ValueError('SOURCE_RESPONSE_NORMAL_IDENTITY_FAILED')
    return {'responses':responses,'difference':difference,'matched_controls':controls,
            'response_equation_relative':residual,'psd_roundoff_allowance':float(slack),
            'matched_control_is_new_estimator':True,'observed_data_corrected':False}


def accumulate_holes(window, coarse_nested, base_nside, nside, design_at,
                     *, chunk_pixels=8192, ncoeff=64):
    """Build C_i only on omitted source-window pixels of the original fit region.

    design_at(pixel_ids) returns Q rows followed by U rows at NESTED native IDs.
    Pixel numbering is not changed by this helper; the native adapter supplies it.
    """
    def power_two(n):
        return isinstance(n,(int,np.integer)) and not isinstance(n,bool) and n>0 and n&(n-1)==0
    w=np.asarray(window)
    if (not power_two(base_nside) or not power_two(nside) or nside<base_nside
        or w.dtype!=np.bool_ or w.shape!=(12*nside*nside,)
        or isinstance(chunk_pixels,bool) or not isinstance(chunk_pixels,int) or not 1<=chunk_pixels<=65536
        or not isinstance(ncoeff,int) or isinstance(ncoeff,bool) or not 1<=ncoeff<=64):
        raise ValueError('NATIVE_MASK_OR_CHUNK_BOUNDS')
    if set(coarse_nested)!=set(MASKS):
        raise ValueError('TWO_FIT_MASKS_REQUIRED')
    m={k:np.asarray(coarse_nested[k]) for k in MASKS}
    if any(v.dtype!=np.bool_ or v.shape!=(12*base_nside**2,) for v in m.values()):
        raise ValueError('COARSE_MASK_SHAPE_OR_TYPE')
    if np.any(m[MASKS[1]] & ~m[MASKS[0]]):
        raise ValueError('NON_NESTED_FIT_MASKS')
    ratio=(nside//base_nside)**2
    c={k:np.zeros((ncoeff,ncoeff)) for k in MASKS};counts={k:0 for k in MASKS}
    for start in range(0,len(w),chunk_pixels):
        ids=np.arange(start,min(len(w),start+chunk_pixels),dtype=np.int64)
        keep=m[MASKS[0]][ids//ratio] & ~w[start:start+len(ids)]
        pixels=ids[keep]
        if not pixels.size:
            continue
        a=_real(design_at(pixels),2)
        if a.shape!=(2*len(pixels),ncoeff):
            raise ValueError('PAIRED_QU_DESIGN_SHAPE')
        c[MASKS[0]]+=a.T@a;counts[MASKS[0]]+=len(pixels)
        t=m[MASKS[1]][pixels//ratio]
        if t.any():
            rows=np.r_[t,t];part=a[rows]
            c[MASKS[1]]+=part.T@part;counts[MASKS[1]]+=int(t.sum())
    area=4*np.pi/len(w)
    return {k:v*area for k,v in c.items()}, {
        'excluded_source_pixels_in_fit_region':counts,
        'design_evaluated_spatial_pixels':counts[MASKS[0]],
        'total_native_pixels':len(w),'native_pixel_area':area,
        'original_fit_selected_pixels':{k:int(v.sum())*ratio for k,v in m.items()},
        'source_pixels_or_estimator_changed':False}


def block_summary(matrix, e_indices, b_indices):
    r=_real(matrix,2);e=np.asarray(e_indices);b=np.asarray(b_indices)
    if (r.shape[0]!=r.shape[1] or e.ndim!=1 or b.ndim!=1 or e.size!=b.size or not e.size
        or e.dtype.kind not in 'iu' or b.dtype.kind not in 'iu'
        or sorted(np.r_[e,b].tolist())!=list(range(len(r)))):
        raise ValueError('MATCHED_EB_INDICES_REQUIRED')
    block=r[np.ix_(b,e)];u,s,vh=np.linalg.svd(block,full_matrices=False)
    witness=vh[0].copy()
    if witness[np.argmax(abs(witness))]<0:
        witness=-witness
    k=float(s[0]);out=block@witness
    if abs(np.linalg.norm(out)-k)>2e-12*max(k,np.finfo(float).tiny):
        raise ValueError('PURE_E_UNIT_SOURCE_WITNESS_FAILED')
    j=np.zeros_like(r);j[np.ix_(e,b)]=-np.eye(len(e));j[np.ix_(b,e)]=np.eye(len(e))
    scale=max(float(np.linalg.norm(r,2)),1.)
    return {'all_gain':float(np.linalg.norm(r,2)), 'E_to_B_gain':k,
        'B_to_E_gain':float(np.linalg.norm(r[np.ix_(e,b)],2)),
        'unit_E_input_coefficients':witness.tolist(),'unit_E_B_response':out.tolist(),
        'per_unit_E_basis_B_norm':np.linalg.norm(block,axis=0).tolist(),
        'EB_complex_structure_absolute_residual':float(np.linalg.norm(r@j-j@r,2)),
        'EB_complex_structure_relative_to_max_one':float(np.linalg.norm(r@j-j@r,2)/scale),
        'input_amplitude_units':'ONE_K_CMB_COEFFICIENT_NORM_LINEAR_UNIT_PROBE_NOT_REAL_SKY'}


def run(root, native_report, native_receipt, chunk_pixels=8192):
    import l01_native_residual_visibility as previous
    import l01_smica_processed_bands as producer
    import healpy as hp
    # Replay the already qualified small matrices, not the large native scan.
    old,report_sha=previous.read_report(native_report)
    previous.analyze_report(old)
    contract=old['checkpoint']['contract']
    if (previous.digest(previous.native.__file__)!=previous.PRODUCER_SHA256
        or hp.__version__!=contract['healpy_version']
        or previous.digest(producer.__file__)!=contract['analysis_code_sha256']
        or previous.digest(native_receipt)!=contract['native_receipt_sha256']):
        raise ValueError('REFERENCE_PRODUCER_OR_NATIVE_SOURCE_MISMATCH')
    for name,expected in contract['dependency_sha256'].items():
        module=importlib.import_module(name)
        if previous.digest(module.__file__)!=expected:
            raise ValueError('REFERENCE_DEPENDENCY_MISMATCH_'+name)
    original,_=producer.verify_receipt(native_receipt,enforce_reported_pins=True)
    window,coarse,window_sha=producer.read_windows(root,hp,original)
    if window_sha!=old['native_window_sha256']:
        raise ValueError('SOURCE_WINDOW_IDENTITY_MISMATCH')
    nested={k:hp.reorder(coarse[k].astype(np.uint8),r2n=True).astype(bool) for k in MASKS}
    nside=old['nside']
    def design(ids):
        theta,phi=hp.pix2ang(nside,ids,nest=True)
        return producer.block_design(theta,phi,2,5)
    start=time.perf_counter()
    holes,scan=accumulate_holes(window,nested,64,nside,design,chunk_pixels=chunk_pixels)
    del window
    for k in MASKS:
        if scan['original_fit_selected_pixels'][k]!=old['solver_states'][k]['selected_pixels']:
            raise ValueError('REFERENCE_FIT_REGION_COUNT_CHANGED')
    grams={k:np.asarray(old['solver_states'][k]['gram']) for k in MASKS}
    result=response_from_holes(grams,holes)
    # Existing finite all-m independent healpy/Wigner convention test at NSIDE8.
    convention=producer.spin2_full_ell_healpy_check(nside=8)
    groups=previous.groups()
    summaries={k:block_summary(v,groups['E'],groups['B']) for k,v in result['responses'].items()}
    summaries['two_mask_difference']=block_summary(result['difference'],groups['E'],groups['B'])
    if max(v['EB_complex_structure_relative_to_max_one'] for v in summaries.values())>2e-9:
        raise ValueError('SCALAR_QU_WINDOW_COMPLEX_STRUCTURE_FAILED')
    return {'schema':SCHEMA,'status':'PASS_FINITE_LOW_SOURCE_WINDOW_RESPONSE',
        'input_ells':[2,3,4,5],'output_ells':[2,3,4,5],'nside':nside,
        'source_model':'INJECTED_DELIVERED_LOW_BAND_FIELD_A_C_NOT_MEASURED_COSMIC_COEFFICIENTS',
        'responses':{k:v.tolist() for k,v in result['responses'].items()},
        'two_mask_difference':result['difference'].tolist(),
        'hole_moments':{k:v.tolist() for k,v in holes.items()},
        'matched_controls':result['matched_controls'],'summaries':summaries,
        'response_equation_relative':result['response_equation_relative'],
        'scan':scan,'seconds':time.perf_counter()-start,'convention_check':convention,
        'native_report_sha256':report_sha,'source_window_sha256':window_sha,
        'native_receipt_sha256':previous.digest(native_receipt),
        'reused_code_sha256':{m.__name__:previous.digest(m.__file__) for m in (previous,previous.native,producer)},
        'native_observed_QU_reread':False,'native_SHT_run':False,
        'small_grid_convention_synthesis_run':True,
        'original_estimator_changed':False,'matched_control_applied_to_observed_data':False,
        'noise_covariance':None,'p_value':None,'infinite_tail_bound':'NOT_ESTABLISHED',
        'paper_gate':'NOT_READY_TO_SUBMIT'}


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',required=True);ap.add_argument('--native-report',required=True)
    ap.add_argument('--native-receipt',required=True);ap.add_argument('--out',required=True)
    ap.add_argument('--chunk-pixels',type=int,default=8192)
    args=ap.parse_args(argv)
    try:
        if Path(args.out).exists() or Path(args.out).is_symlink():
            raise ValueError('OUTPUT_EXISTS_NOT_OVERWRITTEN')
        result=run(args.root,args.native_report,args.native_receipt,args.chunk_pixels)
        import l01_native_residual_visibility as previous
        result['code_sha256']=previous.digest(__file__)
        previous.write_new(args.out,result)
    except (ValueError,OSError,ImportError,KeyError,TypeError,OverflowError,FloatingPointError,np.linalg.LinAlgError) as exc:
        print(json.dumps({'status':'BLOCKED','error_type':type(exc).__name__,'error':str(exc)}),file=sys.stderr)
        return 2
    print(json.dumps({'status':result['status'],'scan':result['scan'],
        'gains':{k:{key:v[key] for key in ('all_gain','E_to_B_gain','B_to_E_gain')}
                 for k,v in result['summaries'].items()},
        'matched_controls':{k:{key:v[key] for key in ('status','condition','identity_max_abs')}
                            for k,v in result['matched_controls'].items()},
        'out':args.out,'paper_gate':result['paper_gate']},indent=2))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
