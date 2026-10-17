"""L01 finite band interference and matched-cutoff diagnostics from checkpoints.

Reuses the source-bound checkpoint reader and pseudo-spectrum arithmetic.
No FITS reads, downloads, SHT, beam correction, noise subtraction or p-values.
A finite L-to-H difference is not a bound on modes above H.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
import zipfile

import numpy as np
import l01_split_checkpoint_spectra as shared

SCHEMA = 'htt.L01_checkpoint_band_interference_and_cutoff/1'
CLOSURE_RTOL = 2e-9  # inherited producer arithmetic check, not physical accuracy
FIELDS = ('total_K_CMB', 'low_2_to_5_K_CMB', 'mid_6_to_8_K_CMB', 'tail_9_to_L_K_CMB')
MASKS = ('common', 'three_way_intersection')


def _vector(value):
    a = np.asarray(value)
    if a.shape != (64,) or a.dtype.kind not in 'fiu' or np.iscomplexobj(a):
        raise ValueError('FINITE_REAL_LOW64_VECTOR_REQUIRED')
    a = a.astype(float, copy=False)
    if not np.isfinite(a).all():
        raise ValueError('NONFINITE_BAND_VECTOR')
    return a


def _norm(a):
    n = float(np.linalg.norm(a))
    if not np.isfinite(n):
        raise ValueError('NUMERICAL_NORM_OVERFLOW')
    return n


def _close(left, right, reference=0.):
    scale = max(_norm(left), _norm(right), float(reference), np.finfo(float).tiny)
    residual = _norm(left-right)/scale
    if not np.isfinite(reference) or reference < 0 or residual > CLOSURE_RTOL:
        raise ValueError('ARCHIVED_BAND_CLOSURE_MISMATCH')
    return residual


def low_indices():
    """Existing per-ell ordering E(m0,cos,sin...), then B; ell=2..5."""
    e, b, offset = [], [], 0
    for ell in range(2, 6):
        n = 2*ell+1
        e.extend(range(offset, offset+n)); b.extend(range(offset+n, offset+2*n))
        offset += 2*n
    return {'all': np.arange(64), 'E': np.array(e), 'B': np.array(b)}


def band_budget(total, mid, tail, *, reference_scale=0.):
    """||d||^2 = ||m||^2 + ||t||^2 + 2 m.t, including its sign.

    Energies are raw coefficient norms squared (K_CMB^2), NOT the
    (2ell+1)/(4pi)-weighted pseudo-spectrum band sums used elsewhere.
    """
    d, m, t = map(_vector, (total, mid, tail))
    if not np.isfinite(reference_scale) or reference_scale < 0:
        raise ValueError('INVALID_REFERENCE_SCALE')
    reference = max(float(reference_scale), _norm(m)+_norm(t))
    residual = _close(d, m+t, reference)
    out = {}
    for name, ix in low_indices().items():
        x, y, z = d[ix], m[ix], t[ix]
        nx, ny, nz = _norm(x), _norm(y), _norm(z)
        dot = float(y @ z)
        values = [float(x @ x), float(y @ y), float(z @ z), 2*dot]
        if not np.isfinite(values).all():
            raise ValueError('NUMERICAL_ENERGY_OVERFLOW')
        out[name] = {
            'total_energy_K_CMB2': values[0], 'mid_energy_K_CMB2': values[1],
            'tail_energy_K_CMB2': values[2], 'interference_K_CMB2': values[3],
            'coherence': float(dot/ny/nz) if ny and nz else None,
            'triangle_saturation': float(nx/(ny+nz)) if ny+nz else None,
            'closure_relative_to_parent_scale': residual,
            'reference_scale_K_CMB': reference,
        }
    return out


def restrict_alms(alms, source_lmax, target_lmax):
    """Re-index (ell,m); high-lmax m-major storage is NOT prefix compatible."""
    a = shared.checked_alms(alms, source_lmax)
    if (isinstance(target_lmax, bool) or not isinstance(target_lmax, (int, np.integer))
            or not 2 <= target_lmax <= source_lmax):
        raise ValueError('INVALID_RESTRICTION_CUTOFF')
    b = np.zeros((2, (target_lmax+1)*(target_lmax+2)//2), dtype=complex)
    for m in range(target_lmax+1):
        ell = np.arange(m, target_lmax+1)
        old = m*(2*source_lmax+1-m)//2+ell
        new = m*(2*target_lmax+1-m)//2+ell
        b[:, new] = a[:, old]
    return shared.checked_alms(b, target_lmax)


def _alm_norm(a, lmax):
    a = shared.checked_alms(a, lmax)
    return _norm(np.concatenate((a[:, :lmax+1].real.ravel(),
        np.sqrt(2.)*a[:, lmax+1:].real.ravel(), np.sqrt(2.)*a[:, lmax+1:].imag.ravel())))


def _derived_subjects(products):
    out = dict(products)
    for label, a, b in (('HM', 'hm1', 'hm2'), ('OE', 'oe1', 'oe2')):
        out[label+'_half_difference'] = (products[a]-products[b])/2
        out['full_minus_'+label+'_mean'] = products['full']-(products[a]+products[b])/2
    return out


def load_run(folder):
    """Reuse SHA/contract checks; bind archived vectors to their own summary.

    Archive closure is rechecked. This does NOT independently re-synthesize
    the archived band projections from the source FITS or saved alms.
    """
    folder = Path(folder)
    arrays, contract, evidence = shared.read_checkpoints(folder)
    summary = shared._json(folder/'summary.json')
    vectors, scales = {}, {}
    for product in shared.PRODUCTS:
        record = shared._json(folder/(product+'.json'))
        r = record['result']
        if summary.get('results', {}).get(product) != r:
            raise ValueError('SUMMARY_AND_PRODUCT_RESULT_DIFFER')
        expected = {'schema': shared.PRODUCER_SCHEMA, 'lmax': contract['lmax'],
            'units': 'K_CMB', 'claim': shared.CLAIM,
            'coefficients_are': 'PSEUDO_ALMS_OF_COMMON_WINDOW_TIMES_DELIVERED_QU',
            'beam_applied_again': False, 'beam_deconvolution': False,
            'tail_beyond_L': 'NOT_BOUNDED', 'p_value': None}
        if any(r.get(k) != v for k, v in expected.items()):
            raise ValueError('RESULT_SCOPE_OR_UNITS_MISMATCH')
        c, t = [np.stack([_vector(r['masks'][name][key]) for key in FIELDS]) for name in MASKS]
        parent = max(_norm(c[0]), _norm(t[0]), sum(_norm(x) for x in c[1:]),
                     sum(_norm(x) for x in t[1:]))
        _close(c[0], c[1]+c[2]+c[3], parent)
        _close(t[0], t[1]+t[2]+t[3], parent)
        delta = t-c
        _close(delta[1], np.zeros(64), parent)
        archived = np.stack([_vector(r['two_mask_difference'][key]) for key in FIELDS])
        for x, y in zip(delta, archived):
            _close(x, y, parent)
        # Columns: total, mid6..8, tail9..L. The shared low2..5 term cancels.
        vectors[product] = delta[[0, 2, 3]]
        scales[product] = parent
    vec = _derived_subjects(vectors)
    # Propagate parent roundoff scales through linear split combinations.
    for label, a, b in (('HM', 'hm1', 'hm2'), ('OE', 'oe1', 'oe2')):
        scales[label+'_half_difference'] = (scales[a]+scales[b])/2
        scales['full_minus_'+label+'_mean'] = scales['full']+(scales[a]+scales[b])/2
    return {'arrays': arrays, 'contract': contract, 'evidence': evidence,
            'vectors': vec, 'scales': scales}


def describe_run(run):
    L = run['contract']['lmax']
    subjects = _derived_subjects(run['arrays'])
    bands = {name: shared.spectrum_record(shared.cross_spectrum_matrix(a, a, L))['weighted_band_sums']['2_to_5']
             for name, a in subjects.items()}
    f = bands['full']
    ratios = {}
    for name, q in bands.items():
        ee, bb, eb = (q[key] for key in ('EE_K_CMB2', 'BB_K_CMB2', 'EB_K_CMB2'))
        ratios[name] = {'EE_over_full_EE': ee/f['EE_K_CMB2'] if f['EE_K_CMB2'] else None,
                       'BB_over_full_BB': bb/f['BB_K_CMB2'] if f['BB_K_CMB2'] else None,
                       'normalized_EB': float(eb/np.sqrt(ee)/np.sqrt(bb)) if ee>0 and bb>0 else None}
    return {'lmax': L, 'contract': run['contract'], 'evidence': run['evidence'],
            'low_pseudocl_band_K_CMB2': bands, 'dimensionless_descriptive_ratios': ratios,
            'ratios_are_noise_fractions': False,
            'band_budgets': {name: band_budget(*v, reference_scale=run['scales'][name])
                             for name, v in run['vectors'].items()},
            'band_budget_space': 'LOW64_REAL_COEFFICIENT_NORM_NOT_PSEUDOCL_BAND_POWER',
            'projections_independently_recomputed': False}


def compare_runs(low, high):
    lc, hc = low['contract'], high['contract']
    L, H = lc['lmax'], hc['lmax']
    if H <= L:
        raise ValueError('CUTOFF_MUST_INCREASE')
    if {k:v for k,v in lc.items() if k!='lmax'} != {k:v for k,v in hc.items() if k!='lmax'}:
        raise ValueError('CUTOFF_PROCESSING_CONTRACT_MISMATCH')
    products = {}
    for p in shared.PRODUCTS:
        a, b = low['arrays'][p], high['arrays'][p]
        overlap = restrict_alms(b, H, L)
        diff = _alm_norm(overlap-a, L)
        scale = max(_alm_norm(a,L), _alm_norm(overlap,L), np.finfo(float).tiny)
        added = b.copy()
        for m in range(L+1):
            ell = np.arange(m,L+1)
            added[:, m*(2*H+1-m)//2+ell] = 0
        products[p] = {'overlap_alm_difference_norm_K_CMB': diff,
                       'overlap_alm_relative_l2': diff/scale,
                       'added_band_alm_norm_K_CMB': _alm_norm(added,H),
                       'added_band': [L+1,H]}
    contrasts = {}
    for name in low['vectors']:
        a, b = low['vectors'][name], high['vectors'][name]
        reference = low['scales'][name]+high['scales'][name]
        contrasts[name] = {'change_budget': band_budget(*(b-a), reference_scale=reference),
            'total_difference_norm_K_CMB': _norm(b[0]-a[0]),
            'change_relative_to_low_norm': _norm(b[0]-a[0])/_norm(a[0]) if _norm(a[0]) else None,
            'change_relative_to_parent_scale': _norm(b[0]-a[0])/reference if reference else None}
    return {'status': 'RECORDED_MATCHED_FINITE_CUTOFF_CHANGE', 'cutoffs': [L,H],
            'products': products, 'projected_contrast_changes': contrasts,
            'tail_term_change': 'ADDED_BAND_PLUS_OVERLAPPING_BAND_NUMERICAL_CHANGE',
            'convergence_certified': False, 'infinite_tail_bound': 'NOT_ESTABLISHED',
            'common_ell_agreement_is_independent_physical_validation': False}


def analyze(band_dir, higher_band_dir=None):
    low = load_run(band_dir)
    report = {'schema': SCHEMA, 'status': 'PASS_FINITE_BAND_DIAGNOSTICS',
              'low': describe_run(low), 'cutoff_comparison': {'status': 'NOT_RUN_NO_HIGH_DIRECTORY'},
              'claim': shared.CLAIM, 'p_value': None, 'independent_sky_count': 1,
              'infinite_tail_bound': 'NOT_ESTABLISHED', 'paper_gate': 'NOT_READY_TO_SUBMIT'}
    if higher_band_dir is not None:
        high = load_run(higher_band_dir)
        report['cutoff_comparison'] = compare_runs(low, high)
        report['high'] = describe_run(high)
    return report


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--band-dir', required=True)
    ap.add_argument('--higher-band-dir')
    ap.add_argument('--out', required=True)
    args = ap.parse_args(argv)
    try:
        result = analyze(args.band_dir, args.higher_band_dir)
        result['code_sha256'] = shared.digest(__file__)
        result['reader_sha256'] = shared.digest(shared.__file__)
        shared.write_new_json(args.out, result)
    except (ValueError, OSError, KeyError, TypeError, FloatingPointError, zipfile.BadZipFile) as exc:
        print(json.dumps({'status':'BLOCKED','error_type':type(exc).__name__,'error':str(exc)}),file=sys.stderr)
        return 2
    focus = ('full','HM_half_difference','OE_half_difference','full_minus_HM_mean','full_minus_OE_mean')
    print(json.dumps({'status':result['status'],'lmax':result['low']['lmax'],
        'low_B_coefficient_budgets':{p:result['low']['band_budgets'][p]['B'] for p in focus},
        'cutoff_comparison_status':result['cutoff_comparison']['status'],
        'out':args.out,'paper_gate':result['paper_gate']},indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
