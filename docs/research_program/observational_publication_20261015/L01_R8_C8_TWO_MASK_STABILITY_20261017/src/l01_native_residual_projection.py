"""Direct native-pixel comparator for L01, with an exact finite residual identity.

Use the SAME saved source window and coarse-mask regions. Compare the delivered
windowed map to one saved harmonic reconstruction on the SAME native grid.
This new pixel comparator does not replace the archived NSIDE64 estimator and
is not a cosmic E/B separation, infinite-tail bound, or calibrated noise model.
"""
from __future__ import annotations
import argparse
import importlib
import json
from pathlib import Path
import sys
import time
import zipfile

import numpy as np

SCHEMA = 'htt.L01_native_pixel_residual_comparator/1'


def _real(x, ndim):
    a=np.asarray(x)
    if a.ndim!=ndim or a.dtype.kind not in 'fiu' or np.iscomplexobj(a):
        raise ValueError('REAL_ARRAY_SHAPE_OR_TYPE')
    a=a.astype(float,copy=False)
    if not np.isfinite(a).all():
        raise ValueError('NONFINITE_ARRAY')
    return a


def nested_dual_gram(common_gram, inner_gram):
    """D D^T = G_inner^-1 - G_common^-1 for nested binary equal-area masks.

    D acts on sqrt(pixel_area)*f. Caller must verify actual mask nesting.
    The returned norm is a floating-point evaluation, not interval arithmetic.
    """
    gc,gt=(_real(g,2) for g in (common_gram,inner_gram))
    if not gc.size or gc.shape!=gt.shape or gc.shape[0]!=gc.shape[1]:
        raise ValueError('GRAM_SHAPE')
    inv=[]
    for g in (gc,gt):
        scale=max(float(np.linalg.norm(g)),np.finfo(float).tiny)
        if np.linalg.norm(g-g.T)>1e-13*scale:
            raise ValueError('GRAM_ASYMMETRIC')
        ev=np.linalg.eigvalsh((g+g.T)/2)
        if ev[0]<=0 or ev[-1]/ev[0]>1e8:
            raise ValueError('GRAM_NONPOSITIVE_OR_ILL_CONDITIONED')
        inv.append(np.linalg.solve(g,np.eye(len(g))))
    h=inv[1]-inv[0];h=(h+h.T)/2
    ev=np.linalg.eigvalsh(h)
    slack=256*np.finfo(float).eps*max(np.linalg.norm(inv[0],2),np.linalg.norm(inv[1],2))
    if ev[0]<-slack:
        raise ValueError('GRAMS_INCONSISTENT_WITH_NESTED_MASKS')
    gain=float(np.sqrt(max(0.,ev[-1])))
    return h,{'gain_all':gain,'smallest_eigenvalue':float(ev[0]),
              'psd_roundoff_allowance':float(slack),
              'norm_domain':'SQRT_SOLID_ANGLE_WEIGHTED_QU_ON_COMMON_REGION',
              'verified_interval_bound':False}


def prepare_block(raw_qu, reconstructed_qu, native_window, common, inner):
    """Zero raw data outside original W only. Never multiply reconstruction by W.

    The fit mask M remains unchanged in the Gram. W and M are different objects.
    Returns columns raw, reconstructed, raw-reconstructed in Q-then-U row order.
    """
    a=np.asarray(raw_qu);b=_real(reconstructed_qu,2)
    masks=[np.asarray(x) for x in (native_window,common,inner)]
    if (a.ndim!=2 or a.shape[0]!=2 or a.shape!=b.shape or a.dtype.kind not in 'fiu'
        or any(m.dtype!=np.bool_ or m.shape!=(a.shape[1],) for m in masks)):
        raise ValueError('NATIVE_BLOCK_SHAPE_OR_MASK')
    w,c,t=masks
    if np.any(t & ~c):
        raise ValueError('REGIONS_ARE_NOT_NESTED')
    valid=np.isfinite(a) & (np.abs(a)<1e20)
    if np.any(~valid[:,w]):
        raise ValueError('INVALID_QU_INSIDE_FIXED_NATIVE_WINDOW')
    f=np.where(w[None,:],a,0.).astype(float)
    residual=f-b
    data=np.column_stack((f.ravel(),b.ravel(),residual.ravel()))
    energy=float(np.sum(residual[:,c]**2))
    if not np.isfinite(data).all() or not np.isfinite(energy):
        raise ValueError('RESIDUAL_NUMERICAL_RANGE')
    return data,energy


def compare_states(common,inner,residual_norm,groups=None):
    """Read three independently accumulated RHS columns from the same pixel loop."""
    if not np.isfinite(residual_norm) or residual_norm<0:
        raise ValueError('RESIDUAL_NORM_INVALID')
    h,gain_meta=nested_dual_gram(common['gram'],inner['gram'])
    c,t=(_real(s['coefficients'],2) for s in (common,inner))
    if c.shape!=t.shape or c.shape!=(len(h),3):
        raise ValueError('THREE_MOMENT_COLUMNS_REQUIRED')
    delta=t-c
    scale=max(float(np.linalg.norm(c)),float(np.linalg.norm(t)),np.finfo(float).tiny)
    closure=float(np.linalg.norm(delta[:,0]-delta[:,1]-delta[:,2])/scale)
    if closure>2e-9:
        raise ValueError('NATIVE_RESIDUAL_PROJECTION_IDENTITY_FAILED')
    groups={'all':np.arange(len(h))} if groups is None else groups
    components={}
    for name,ix in groups.items():
        ix=np.asarray(ix)
        if ix.ndim!=1 or ix.dtype.kind not in 'iu' or not ix.size or np.any(ix<0) or np.any(ix>=len(h)) or len(np.unique(ix))!=len(ix):
            raise ValueError('COEFFICIENT_SELECTOR')
        block=h[np.ix_(ix,ix)]
        k=float(np.sqrt(max(0.,np.linalg.eigvalsh(block)[-1])))
        nr=float(np.linalg.norm(delta[ix,2]));bound=k*residual_norm
        if not np.isfinite([nr,bound]).all():
            raise ValueError('BOUND_NUMERICAL_RANGE')
        # A numeric falsification check; no claim of an outward-rounded bound.
        if nr>bound+2e-10*max(bound,scale):
            raise ValueError('FINITE_RESIDUAL_GAIN_BOUND_FAILED')
        direct=float(np.linalg.norm(delta[ix,0]));synth=float(np.linalg.norm(delta[ix,1]))
        components[name]={'direct_norm_K_CMB':direct,'reconstructed_norm_K_CMB':synth,
            'measured_residual_norm_K_CMB':nr,'residual_norm_bound_K_CMB':bound,
            'gain':k,'relative_residual_to_direct':nr/direct if direct else None}
    return {'contrast_raw_K_CMB':delta[:,0].tolist(),
        'contrast_reconstructed_K_CMB':delta[:,1].tolist(),
        'contrast_residual_K_CMB':delta[:,2].tolist(),
        'closure_relative':closure,'residual_map_norm_K_CMB':float(residual_norm),
        'dual_gram':h.tolist(),'dual_meta':gain_meta,'components':components,
        'is_infinite_spectral_tail_bound':False,'physical_EB_identification':False}


def run(root,band_dir,native_receipt,product='full',chunk_pixels=8192):
    # Existing modules are lazy: math tests and --help have no FITS/healpy dependency.
    import l01_cutoff_band_diagnostics as base
    import l01_smica_processed_bands as producer
    import l01_fixed_region_grid_audit as grid
    from l01_smica_fits_integrity import _read_header
    import healpy as hp
    if product not in producer.PRODUCTS or not 256<=chunk_pixels<=65536:
        raise ValueError('NATIVE_COMPARATOR_BOUNDS')
    old=base.load_run(band_dir);contract=old['contract'];L=contract['lmax']
    if (hp.__version__!=contract['healpy_version'] or
        base.shared.digest(producer.__file__)!=contract['analysis_code_sha256'] or
        base.shared.digest(native_receipt)!=contract['native_receipt_sha256']):
        raise ValueError('SAVED_PRODUCER_OR_SOURCE_IDENTITY_MISMATCH')
    for name,expected in contract['dependency_sha256'].items():
        mod=importlib.import_module(name)
        if base.shared.digest(mod.__file__)!=expected:
            raise ValueError('SAVED_DEPENDENCY_CHANGED_'+name)
    source=producer.check_sources(root,[product])[product]
    native,_=producer.verify_receipt(native_receipt,enforce_reported_pins=True)
    window,coarse,window_sha=producer.read_windows(root,hp,native)
    if window_sha!=contract['native_window_sha256']:
        raise ValueError('NATIVE_WINDOW_CHANGED')
    nside=producer.NATIVE_NSIDE;npix=12*nside**2
    nested={name:hp.reorder(mask.astype(np.uint8),r2n=True).astype(bool)
            for name,mask in coarse.items()}
    names=('common','three_way_intersection')
    if np.any(nested[names[1]] & ~nested[names[0]]):
        raise ValueError('REGIONS_ARE_NOT_NESTED')
    # One saved band reconstruction, not a new forward harmonic analysis.
    print(json.dumps({'phase':'SYNTHESIZE_SAVED_ALMS_ON_NATIVE_GRID','product':product,
                      'nside':nside,'saved_lmax':L}),flush=True)
    q,u=hp.alm2map_spin(old['arrays'][product],nside,spin=2,lmax=L,mmax=L)
    q=hp.reorder(q,r2n=True);u=hp.reorder(u,r2n=True)
    if q.shape!=(npix,) or u.shape!=(npix,):
        raise ValueError('RECONSTRUCTED_NATIVE_MAP_SHAPE')
    p=Path(source['path']);stat=p.stat();identity=(stat.st_size,stat.st_mtime_ns,stat.st_ino)
    with p.open('rb') as f:
        _,offset=_read_header(f,0,stat.st_size)
        header,offset=_read_header(f,offset,stat.st_size)
    width=10 if product=='full' else 3
    if int(header['NAXIS2'])!=npix or int(header['NAXIS1'])!=4*width:
        raise ValueError('NATIVE_QU_LAYOUT_CHANGED')
    mm=np.memmap(p,dtype='>f4',mode='r',offset=offset,shape=(npix,width))
    moments={name:grid.Moments(64,3) for name in names}
    energies=[];ratio=(nside//64)**2;start_time=time.perf_counter();last=-1
    for start in range(0,npix,chunk_pixels):
        stop=min(npix,start+chunk_pixels);pixels=np.arange(start,stop,dtype=np.int64)
        masks={name:nested[name][pixels//ratio] for name in names}
        raw=np.stack((mm[start:stop,1],mm[start:stop,2]))
        reconstruction=np.stack((q[start:stop],u[start:stop]))
        data,energy=prepare_block(raw,reconstruction,window[start:stop],masks[names[0]],masks[names[1]])
        energies.append(energy)
        if masks[names[0]].any():
            theta,phi=hp.pix2ang(nside,pixels,nest=True)
            design=producer.block_design(theta,phi,2,5)
            for name in names:
                moments[name].add(design,data,masks[name])
        quarter=4*stop//npix
        if quarter>last:
            print(json.dumps({'phase':'NATIVE_LOW_MOMENTS','completed_pixels':stop,'total_pixels':npix}),flush=True)
            last=quarter
    del mm,q,u
    stat=p.stat()
    if (stat.st_size,stat.st_mtime_ns,stat.st_ino)!=identity:
        raise ValueError('NATIVE_SOURCE_CHANGED_DURING_READ')
    import math
    area=4*np.pi/npix
    states={name:moments[name].solve(area) for name in names}
    for name in names:
        if states[name]['selected_pixels']!=int(coarse[name].sum())*ratio:
            raise ValueError('NATIVE_REGION_AREA_CHANGED')
    result=compare_states(states[names[0]],states[names[1]],
                          np.sqrt(area*math.fsum(energies)),base.low_indices())
    raw=np.asarray(result['contrast_raw_K_CMB']);syn=np.asarray(result['contrast_reconstructed_K_CMB'])
    archived=old['vectors'][product][0]
    result.update(schema=SCHEMA,status='PASS_NATIVE_PIXEL_RESIDUAL_ACCOUNTING',
        product=product,nside=nside,saved_lmax=L,seconds=time.perf_counter()-start_time,
        source=source,checkpoint={'contract':contract,'evidence':old['evidence']},
        native_window_sha256=window_sha,
        region='SAME_UNION_OF_NSIDE64_NESTED_CELLS_SAMPLED_AT_NATIVE_NSIDE',
        gram_uses='M_REGION_ONLY_NOT_M_TIMES_SOURCE_WINDOW',
        source_uses='ORIGINAL_NATIVE_W_TIMES_DELIVERED_QU',
        reconstructed_field_rewindowed=False,forward_SHT_rerun=False,
        source_harmonic_cutoff_in_direct_fit=None,beam_applied_again=False,
        estimator_relation='NEW_NATIVE_PIXEL_COMPARATOR_NOT_REPLACEMENT_OF_ARCHIVED_NSIDE64',
        original_nside64_contrast_K_CMB=archived.tolist(),
        fixed_L_grid_shift_K_CMB=(syn-archived).tolist(),
        endpoint_minus_archived_K_CMB=(raw-archived).tolist(),
        interpretation='DIRECT_MINUS_NATIVE_SYNTH_IS_FINITE_MAP_RECONSTRUCTION_RESIDUAL_NOT_COSMIC_HIGH_ELL_TAIL',
        solver_states=grid._jsonable(states),infinite_tail_bound='NOT_ESTABLISHED',
        p_value=None,paper_gate='NOT_READY_TO_SUBMIT')
    return result


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',required=True);ap.add_argument('--band-dir',required=True)
    ap.add_argument('--native-receipt',required=True);ap.add_argument('--out',required=True)
    ap.add_argument('--product',choices=('full','hm1','hm2','oe1','oe2'),default='full')
    ap.add_argument('--chunk-pixels',type=int,default=8192)
    args=ap.parse_args(argv)
    try:
        if Path(args.out).exists() or Path(args.out).is_symlink():
            raise ValueError('OUTPUT_EXISTS_NOT_OVERWRITTEN')
        report=run(args.root,args.band_dir,args.native_receipt,args.product,args.chunk_pixels)
        import l01_split_checkpoint_spectra as shared
        report['code_sha256']=shared.digest(__file__)
        report['reuse_sha256']={name:shared.digest(sys.modules[name].__file__) for name in
            ('l01_fixed_region_grid_audit','l01_smica_processed_bands','l01_cutoff_band_diagnostics','l01_split_checkpoint_spectra')}
        shared.write_new_json(args.out,report)
    except (ValueError,OSError,ImportError,KeyError,TypeError,FloatingPointError,zipfile.BadZipFile) as exc:
        print(json.dumps({'status':'BLOCKED','error_type':type(exc).__name__,'error':str(exc)}),file=sys.stderr)
        return 2
    print(json.dumps({'status':report['status'],'product':report['product'],
        'native_nside':report['nside'],'saved_lmax':report['saved_lmax'],
        'components':report['components'],'closure_relative':report['closure_relative'],
        'out':args.out,'paper_gate':report['paper_gate']},indent=2))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
