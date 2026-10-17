"""Explain a native L01 residual using its saved small matrices, not a new SHT.

For e=D z and H=D D.T, e.T H^+ e is the squared norm of the input-space
row projection. Numerical cut modes remain unresolved, not physical noise.
Reuses the unchanged native comparator; never changes the measured error.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

import numpy as np
import l01_native_residual_projection as native

SCHEMA = 'htt.L01_native_residual_visibility/1'
PRODUCER_SHA256 = '4259df97ce6aeed6a0a1653ef62438604f27f7de045f067fc510e608c09d2209'
SOURCE_SHA = {
    'full': '60952c645eb33d151905ddf5837477e15ca02a3261feca4ceca3c3feece4f9ac',
    'hm1': '736338208cf0b494c3b6c13c444f116262c8052dcb4a7842dc738bf6a4a426b0',
    'hm2': '0a4dc860a6f7bbdb5980cd7ac1d187ba9139a383c9c47f159e069281c3d5f3a5',
    'oe1': '5473304ed71348cb346b335bca0deb417c9dd3f0286c7e3d2dfd5e1fc93f503a',
    'oe2': 'da9c3e3e09fdff87ada31db00417ae7688facc8b47756576ed8daec12fe1e2f0',
}
NATIVE_RECEIPT_SHA = '7b4763afe8e5d30a02be296b0d4f7281a30f4e80937975dcda5f929643c2a7b6'
EPS = np.finfo(float).eps


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _scalar(x):
    if isinstance(x, (bool, str)) or not np.isscalar(x) or not np.isrealobj(x):
        raise ValueError('FINITE_NONNEGATIVE_SCALAR_REQUIRED')
    v = float(x)
    if not np.isfinite(v) or v < 0:
        raise ValueError('FINITE_NONNEGATIVE_SCALAR_REQUIRED')
    return v


def _norm(x):
    a = np.asarray(x, dtype=float)
    scale = float(np.max(np.abs(a))) if a.size else 0.
    value = float(scale*np.linalg.norm(a/scale)) if scale else 0.
    if not np.isfinite(value):
        raise ValueError('NORM_RANGE')
    return value


def _close(a, b, label, reference=0., rtol=2e-9):
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if a.shape != b.shape or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError(label)
    scale = max(_norm(a), _norm(b), _scalar(reference), np.finfo(float).tiny)
    error = _norm(a-b)/scale
    if error > rtol:
        raise ValueError(label)
    return error


def groups():
    e, b, offset = [], [], 0
    for ell in range(2, 6):
        n = 2*ell+1
        e.extend(range(offset, offset+n)); b.extend(range(offset+n, offset+2*n))
        offset += 2*n
    return {'all': np.arange(64), 'E': np.array(e), 'B': np.array(b)}


def retained_residual_energy(dual_gram, target_residual, residual_norm, *, roundoff_atol=0.):
    """Retained row-space energy, invariant under signs/degenerate rotations.

    Positive H eigenvalues below max(4*atol,256*n*eps*lambda_max) are not
    inverted. The remaining input energy can contain BOTH exact kernel energy
    and discarded positive modes. This is not a noise-covariance analysis.
    """
    h, e = native._real(dual_gram, 2), native._real(target_residual, 1)
    R, atol = _scalar(residual_norm), _scalar(roundoff_atol)
    if not e.size or h.shape != (e.size, e.size):
        raise ValueError('DUAL_GRAM_TARGET_SHAPE')
    scale = max(_norm(h), np.finfo(float).tiny)
    if _norm(h-h.T) > max(atol, 1e-13*scale):
        raise ValueError('DUAL_GRAM_ASYMMETRIC')
    values, vectors = np.linalg.eigh((h+h.T)/2)
    top = max(0., float(values[-1]))
    allowance = max(atol, 64*e.size*EPS*top)
    if values[0] < -allowance:
        raise ValueError('DUAL_GRAM_NONPOSITIVE')
    cutoff = max(4*atol, 256*e.size*EPS*top)
    keep = values > cutoff
    q = vectors[:, keep].T @ e
    target_kept = vectors[:, keep] @ q
    target_unresolved = e-target_kept
    n_kept, n_all = _norm(target_kept), _norm(e)
    input_kept = _norm(q/np.sqrt(values[keep])) if keep.any() else 0.
    gain = float(np.sqrt(top))
    bound = gain*R
    if n_all > bound + 2e-9*max(n_all, bound, np.finfo(float).tiny):
        raise ValueError('TARGET_EXCEEDS_DECLARED_RESIDUAL_ENVELOPE')
    if input_kept > R*(1+2e-9):
        raise ValueError('RETAINED_ENERGY_EXCEEDS_TOTAL_INPUT_ENERGY')
    energy, total = input_kept**2, R**2
    if not np.isfinite([energy,total]).all():
        raise ValueError('ENERGY_RANGE')
    effective = n_kept/input_kept if input_kept else None
    input_factor = R/input_kept if input_kept else None
    orientation_factor = gain/effective if effective else None
    return {
        'retained_rank_numeric': int(keep.sum()), 'output_dimension': int(e.size),
        'eigenvalue_cutoff': cutoff, 'input_roundoff_atol': atol,
        'eigenvalues_ascending': values.tolist(),
        'retained_input_norm_K_CMB': input_kept,
        'retained_input_energy_K_CMB2': energy,
        'retained_input_energy_fraction': energy/total if total else None,
        'remaining_input_energy_K_CMB2': max(0., total-energy),
        'remaining_energy_includes_kernel_and_discarded_positive_modes': True,
        'retained_target_norm_K_CMB': n_kept,
        'unresolved_target_norm_K_CMB': _norm(target_unresolved),
        'unresolved_target_fraction': _norm(target_unresolved)/n_all if n_all else None,
        'uniform_gain': gain, 'effective_gain_on_retained_residual': effective,
        'uniform_bound_K_CMB': bound,
        'bound_over_measured': bound/n_all if n_all else None,
        'input_norm_dilution_factor': input_factor,
        'spectral_orientation_factor': orientation_factor,
        'factor_product_for_retained_target': input_factor*orientation_factor if input_factor is not None and orientation_factor is not None else None,
        'norm_domain': 'SQRT_SOLID_ANGLE_WEIGHTED_QU_ON_COMMON_REGION',
        'statistical_noise_fraction': False, 'pure_EB_separation': False,
        'formal_rank_or_interval_certificate': False,
    }


def deletion_forcing(common, inner):
    """Gt(yt-yc) = -[(bc-bt)-(Gc-Gt)yc], raw/reconstruction/residual columns."""
    gc, gt = (native._real(x['gram'], 2) for x in (common, inner))
    bc, bt = (native._real(x['rhs'], 2) for x in (common, inner))
    yc, yt = (native._real(x['coefficients'], 2) for x in (common, inner))
    if gc.shape != gt.shape or bc.shape != bt.shape or yc.shape != bc.shape or yt.shape != bc.shape or gc.shape != (len(yc), len(yc)):
        raise ValueError('MOMENT_SHAPE')
    for g, b, y in ((gc,bc,yc),(gt,bt,yt)):
        _close(g@y,b,'SAVED_NORMAL_EQUATION_MISMATCH',_norm(g)*_norm(y)+_norm(b),1e-12)
    removed = gc-gt
    forcing = (bc-bt)-removed@yc
    predicted = -np.linalg.solve(gt, forcing)
    error = _close(predicted,yt-yc,'DELETION_IDENTITY_MISMATCH',_norm(yc)+_norm(yt))
    return {'removed_region_fit_residual_moment_K_CMB': forcing.tolist(),
            'predicted_contrast_K_CMB': predicted.tolist(),
            'identity_relative_to_parent': error,
            'same_report_identity_not_independent_map_measurement': True}


def analyze_report(report):
    """Read the existing native report, verify attribution, replay small algebra."""
    expected = {
        'schema':native.SCHEMA, 'status':'PASS_NATIVE_PIXEL_RESIDUAL_ACCOUNTING',
        'nside':2048, 'paper_gate':'NOT_READY_TO_SUBMIT', 'p_value':None,
        'region':'SAME_UNION_OF_NSIDE64_NESTED_CELLS_SAMPLED_AT_NATIVE_NSIDE',
        'gram_uses':'M_REGION_ONLY_NOT_M_TIMES_SOURCE_WINDOW',
        'source_uses':'ORIGINAL_NATIVE_W_TIMES_DELIVERED_QU',
        'reconstructed_field_rewindowed':False, 'forward_SHT_rerun':False,
        'beam_applied_again':False,
        'estimator_relation':'NEW_NATIVE_PIXEL_COMPARATOR_NOT_REPLACEMENT_OF_ARCHIVED_NSIDE64',
        'code_sha256':PRODUCER_SHA256,
    }
    if not isinstance(report,dict) or any(report.get(k)!=v for k,v in expected.items()):
        raise ValueError('NATIVE_REPORT_CONTRACT_OR_PRODUCER_MISMATCH')
    product = report.get('product')
    if product not in SOURCE_SHA or report.get('source',{}).get('sha256')!=SOURCE_SHA[product]:
        raise ValueError('SOURCE_IDENTITY_MISMATCH')
    contract = report['checkpoint']['contract']
    if (contract.get('native_receipt_sha256')!=NATIVE_RECEIPT_SHA or
        contract.get('native_window_sha256')!=report.get('native_window_sha256') or
        contract.get('lmax')!=report.get('saved_lmax') or
        report.get('saved_lmax') not in (16,32,64,128)):
        raise ValueError('NATIVE_CHECKPOINT_CONTRACT_MISMATCH')
    c, t = (report['solver_states'][k] for k in ('common','three_way_intersection'))
    if any(native._real(x['gram'],2).shape!=(64,64) for x in (c,t)):
        raise ValueError('NATIVE_LOW64_GRAM_REQUIRED')
    counts = [x['selected_pixels'] for x in (c,t)]
    if any(isinstance(v,bool) or not isinstance(v,int) or v<=0 for v in counts) or counts[1]>counts[0]:
        raise ValueError('NESTED_SELECTED_PIXEL_COUNTS')
    replay = native.compare_states(c,t,_scalar(report['residual_map_norm_K_CMB']),groups())
    for k in ('dual_gram','contrast_raw_K_CMB','contrast_reconstructed_K_CMB','contrast_residual_K_CMB'):
        _close(report[k],replay[k],'NATIVE_REPORT_ALGEBRA_MISMATCH_'+k)
    for group in groups():
        for key in ('direct_norm_K_CMB','reconstructed_norm_K_CMB','measured_residual_norm_K_CMB','gain','residual_norm_bound_K_CMB'):
            _close(report['components'][group][key],replay['components'][group][key],'NATIVE_SUMMARY_MISMATCH_'+key)
    shell = deletion_forcing(c,t)
    h = np.asarray(replay['dual_gram']); e = np.asarray(replay['contrast_residual_K_CMB'])
    raw = np.asarray(replay['contrast_raw_K_CMB']); syn = np.asarray(replay['contrast_reconstructed_K_CMB'])
    components = {}
    for group, ix in groups().items():
        r = retained_residual_energy(h[np.ix_(ix,ix)],e[ix],report['residual_map_norm_K_CMB'],roundoff_atol=replay['dual_meta']['psd_roundoff_allowance'])
        x,y = raw[ix], syn[ix]; nx,ny=_norm(x),_norm(y)
        angle = None
        if nx and ny:
            u,v=x/nx,y/ny
            angle=float(np.degrees(2*np.arctan2(_norm(u-v),_norm(u+v))))
        r.update(replay['components'][group])
        r.update(reconstructed_energy_over_direct=(ny/nx)**2 if nx else None,
                 coefficient_angle_degrees=angle,
                 angle_space='REAL_LOWELL_COEFFICIENT_SPACE_NOT_SKY_OR_POLARIZATION_ANGLE')
        components[group] = r
    return {'schema':SCHEMA,'status':'PASS_NATIVE_RESIDUAL_VISIBILITY_ACCOUNTING',
        'product':product,'saved_lmax':report['saved_lmax'],
        'source_sha256':report['source']['sha256'], 'producer_code_sha256':report['code_sha256'],
        'components':components,'deletion_shell':shell,
        'input_energy_groups_are_additive':False,
        'algebra_recomputed_from_saved_moments':True,'native_maps_replayed':False,
        'native_measured_error_changed':False,'new_sky_information':False,
        'interpretation':'RETAINED_OPERATOR_ROWSPACE_NOT_PURE_EB_OR_A_NOISE_MODEL',
        'publication_gate':'NOT_READY_TO_SUBMIT','p_value':None,
        'infinite_tail_bound':'NOT_ESTABLISHED'}


def read_report(path):
    p=Path(path)
    if p.is_symlink() or not p.is_file() or p.stat().st_size>8<<20:
        raise ValueError('NATIVE_REPORT_MISSING_UNSAFE_OR_OVERSIZE')
    def pairs(items):
        out={}
        for k,v in items:
            if k in out:raise ValueError('DUPLICATE_JSON_KEY')
            out[k]=v
        return out
    def constant(x):raise ValueError('NONFINITE_JSON_CONSTANT_'+x)
    def number(x):
        v=float(x)
        if not np.isfinite(v):raise ValueError('NONFINITE_JSON_NUMBER')
        return v
    data=p.read_bytes()
    return json.loads(data,object_pairs_hook=pairs,parse_constant=constant,parse_float=number),hashlib.sha256(data).hexdigest()


def write_new(path, report):
    p=Path(path)
    if p.exists() or p.is_symlink():raise ValueError('OUTPUT_EXISTS_NOT_OVERWRITTEN')
    payload=(json.dumps(report,indent=2,sort_keys=True,allow_nan=False)+'\n').encode()
    p.parent.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(prefix='.'+p.name+'.',dir=p.parent)
    try:
        with os.fdopen(fd,'wb') as out:
            out.write(payload);out.flush();os.fsync(out.fileno())
        os.link(name,p)
    finally:os.unlink(name)


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--native-report',required=True);ap.add_argument('--out',required=True)
    args=ap.parse_args(argv)
    try:
        if digest(native.__file__)!=PRODUCER_SHA256:
            raise ValueError('UNSUPPORTED_NATIVE_COMPARATOR_VERSION')
        old,h=read_report(args.native_report)
        result=analyze_report(old)
        result.update(native_report_sha256=h,analysis_code_sha256=digest(__file__))
        write_new(args.out,result)
    except (ValueError,TypeError,KeyError,OSError,OverflowError,FloatingPointError,np.linalg.LinAlgError) as exc:
        print(json.dumps({'status':'BLOCKED','error_type':type(exc).__name__,'error':str(exc)}),file=sys.stderr)
        return 2
    focus=('retained_rank_numeric','retained_input_energy_fraction','unresolved_target_fraction',
           'relative_residual_to_direct','bound_over_measured','input_norm_dilution_factor',
           'spectral_orientation_factor','coefficient_angle_degrees','reconstructed_energy_over_direct')
    print(json.dumps({'status':result['status'],'components':{g:{k:r[k] for k in focus} for g,r in result['components'].items()},
          'native_maps_replayed':False,'out':args.out,'paper_gate':'NOT_READY_TO_SUBMIT'},indent=2))
    return 0


if __name__=='__main__':raise SystemExit(main())
