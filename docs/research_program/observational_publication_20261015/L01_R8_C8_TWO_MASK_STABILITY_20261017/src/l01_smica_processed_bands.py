"""Source-pinned SMICA Q/U -> common-window spin-2 finite-band diagnostics.

Reuses the checked-in native mask/K and harmonic conventions. These are
coefficients of a WINDOWED DELIVERED MAP, not identified cosmic E/B or p-values.
No network, inpainting, Q/U pixel averaging, beam multiplication or deconvolution.
"""
from __future__ import annotations
import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np
from scipy.linalg import qr, solve_triangular
from l01_repo_imports import activate
activate()
from spin2_finite import block_design
from healpix_ring_coords import pix2ang_ring
from fits_source_identity import inspect_planck_pmask
from l01_k_spectral_certificate import (digest_file, verify_receipt, eb_indices,
    V2_INPUT_HASHES, spin2_full_ell_healpy_check)
from native_planck_pol_response import NAME, choose_support, canonical_ring64_mask_sha256

NATIVE_NSIDE = 2048
OUT_NSIDE = 64
PRODUCTS = ('full', 'hm1', 'hm2', 'oe1', 'oe2')
SOURCE_SHA = {
    'full': '60952c645eb33d151905ddf5837477e15ca02a3261feca4ceca3c3feece4f9ac',
    'hm1': '736338208cf0b494c3b6c13c444f116262c8052dcb4a7842dc738bf6a4a426b0',
    'hm2': '0a4dc860a6f7bbdb5980cd7ac1d187ba9139a383c9c47f159e069281c3d5f3a5',
    'oe1': '5473304ed71348cb346b335bca0deb417c9dd3f0286c7e3d2dfd5e1fc93f503a',
    'oe2': 'da9c3e3e09fdff87ada31db00417ae7688facc8b47756576ed8daec12fe1e2f0',
}
SCHEMA = 'htt.L01_SMICA_windowed_QU_band_accounting/1'
CLAIM = 'PROCESSED_MAP_DIAGNOSTIC_NOT_COSMIC_EB_OR_CALIBRATED_NULL'


def real_array(value, name):
    a = np.asarray(value)
    if np.iscomplexobj(a) or not np.issubdtype(a.dtype, np.number):
        raise ValueError(name + '_NOT_REAL_NUMERIC')
    a = a.astype(np.float64, copy=False)
    if not np.isfinite(a).all():
        raise ValueError(name + '_NONFINITE')
    return a


def account_projected_bands(total, low, mid, tail, *, reference_scale=0.):
    """Exact linear identity, checked relatively in the supplied physical units."""
    v = [real_array(x, 'BAND') for x in (total, low, mid, tail)]
    if v[0].ndim != 1 or not v[0].size or any(x.shape != v[0].shape for x in v):
        raise ValueError('BAND_SHAPES')
    if not np.isfinite(reference_scale) or reference_scale < 0:
        raise ValueError('CLOSURE_REFERENCE_SCALE')
    norms = [float(np.linalg.norm(x)) for x in v]
    scale = max(sum(norms[1:]), norms[0], float(reference_scale), np.finfo(float).tiny)
    if not np.isfinite(scale):
        raise ValueError('BAND_NORM_OVERFLOW')
    residual = float(np.linalg.norm(v[0] - (v[1] + v[2] + v[3]))) / scale
    if residual > 2e-9:
        raise ValueError(f'BAND_CLOSURE_FAILED: {residual}')
    return {'total_K_CMB': v[0].tolist(), 'low_2_to_5_K_CMB': v[1].tolist(),
            'mid_6_to_8_K_CMB': v[2].tolist(), 'tail_9_to_L_K_CMB': v[3].tolist(),
            'component_norms_K_CMB': dict(zip(('total', 'low', 'mid', 'tail'), norms)),
            'closure_relative': residual, 'roundoff_reference_scale_K_CMB': scale,
            'tail_beyond_L': 'NOT_BOUNDED', 'claim': CLAIM}


def check_alms(alms, lmax):
    if isinstance(lmax, bool) or not isinstance(lmax, (int, np.integer)) or lmax < 2:
        raise ValueError('LMAX_INVALID')
    a = np.asarray(alms)
    if a.shape != (2, (lmax + 1) * (lmax + 2) // 2) or not np.issubdtype(a.dtype, np.number):
        raise ValueError('ALM_SHAPE')
    a = a.astype(np.complex128, copy=False)
    if not np.isfinite(a).all():
        raise ValueError('ALM_NONFINITE')
    # m=0 occupies the first lmax+1 slots in healpy's m-major storage.
    if np.any(a[:, :lmax + 1].imag != 0):
        raise ValueError('ALM_M0_NOT_REAL')
    return a


def alm_index(lmax, ell, m):
    if not 0 <= m <= ell <= lmax:
        raise ValueError('ALM_INDEX')
    return m * (2 * lmax + 1 - m) // 2 + ell


def packed_real(alms, lmax, lo, hi):
    """Per ell: E(m0,cos1,sin1,...), B(...); sin coefficient=-sqrt(2) Im alm."""
    a = check_alms(alms, lmax)
    if not 2 <= lo <= hi <= lmax:
        raise ValueError('REAL_COEFFICIENT_BAND')
    out = []
    for ell in range(lo, hi + 1):
        for field in a:
            out.append(field[ell].real)
            for m in range(1, ell + 1):
                c = field[alm_index(lmax, ell, m)]
                out.extend((np.sqrt(2.) * c.real, -np.sqrt(2.) * c.imag))
    return np.asarray(out)


def filter_alm(alms, lmax, lo, hi, *, e_only=False):
    a = check_alms(alms, lmax)
    if not 2 <= lo <= hi <= lmax:
        raise ValueError('ALM_BAND')
    b = np.zeros_like(a)
    for m in range(hi + 1):
        first = max(m, lo)
        if first <= hi:
            start = alm_index(lmax, first, m)
            end = alm_index(lmax, hi, m) + 1
            b[:, start:end] = a[:, start:end]
    if e_only:
        b[1] = 0
    return b


def masked_field(field, window):
    """A fixed shared window, no per-product support reduction and no gap fitting."""
    a = np.asarray(field)
    w = np.asarray(window)
    if a.ndim != 1 or w.shape != a.shape or w.dtype != np.bool_ or np.iscomplexobj(a):
        raise ValueError('FIELD_WINDOW_SHAPE')
    out = np.asarray(a, dtype=np.float64).copy()
    valid = np.isfinite(out) & (np.abs(out) < 1e20)
    if np.any(w & ~valid):
        raise ValueError('INVALID_QU_INSIDE_FIXED_NATIVE_WINDOW')
    out[~w] = 0.
    return out


@dataclass
class Projector:
    selected_rows: np.ndarray
    q: np.ndarray
    r: np.ndarray
    condition: float

    @classmethod
    def from_design(cls, low, spatial_mask):
        a = real_array(low, 'LOW_DESIGN'); m = np.asarray(spatial_mask)
        if a.ndim != 2 or m.ndim != 1 or m.dtype != np.bool_ or 2 * len(m) != len(a):
            raise ValueError('PAIRED_QU_MASK_SHAPE')
        rows = np.r_[m, m]
        if rows.sum() <= a.shape[1]:
            raise ValueError('LOW_DESIGN_INSUFFICIENT_ROWS')
        q, r = qr(a[rows], mode='economic', check_finite=False)
        s = np.linalg.svd(r, compute_uv=False)
        if s[-1] <= 0 or s[0] / s[-1] > 1e6:
            raise ValueError('LOW_DESIGN_RANK_OR_CONDITION')
        return cls(rows, q, r, float(s[0] / s[-1]))

    def apply(self, data):
        d = real_array(data, 'QU_DATA')
        if d.ndim != 1 or d.size != self.selected_rows.size:
            raise ValueError('QU_DATA_SHAPE')
        return solve_triangular(self.r, self.q.T @ d[self.selected_rows], check_finite=False)


def analyze_alms(alms, lmax, hp, projectors, matrices, *, nside=OUT_NSIDE):
    """Projection of a processed pseudo-alm field, NEVER physical sky deconvolution."""
    a = check_alms(alms, lmax)
    if not 9 <= lmax <= 128:
        raise ValueError('LMAX_REQUIRES_9_TO_128')
    if set(projectors) != set(matrices) or set(matrices) != {'common', 'three_way_intersection'}:
        raise ValueError('TWO_MATCHED_PROJECTIONS_REQUIRED')
    def synth(b):
        return np.concatenate(hp.alm2map_spin(b, nside, spin=2, lmax=lmax, mmax=lmax))
    all_map = synth(filter_alm(a, lmax, 2, lmax))
    mid_map = synth(filter_alm(a, lmax, 6, 8))
    tail_map = synth(filter_alm(a, lmax, 9, lmax))
    tail_e_map = synth(filter_alm(a, lmax, 9, lmax, e_only=True))
    low = packed_real(a, lmax, 2, 5); mid = packed_real(a, lmax, 6, 8)
    result = {}
    for name, proj in projectors.items():
        k = real_array(matrices[name], 'K')
        if k.shape != (64, 90):
            raise ValueError('K_SHAPE_64_90')
        total = proj.apply(all_map); measured_mid = proj.apply(mid_map)
        predicted_mid = k @ mid
        scale = max(np.linalg.norm(mid_map) / np.sqrt(mid_map.size),
                    np.linalg.norm(predicted_mid), np.finfo(float).tiny)
        mid_error = float(np.linalg.norm(measured_mid - predicted_mid) / scale)
        if mid_error > 2e-8:
            raise ValueError('STORED_K_VS_DIRECT_MID_SYNTHESIS_MISMATCH')
        r = account_projected_bands(total, low, predicted_mid, proj.apply(tail_map))
        r['tail_E_only_projection_K_CMB'] = proj.apply(tail_e_map).tolist()
        r['mid_K_direct_relative'] = mid_error
        r['low_design_condition'] = proj.condition
        result[name] = r
    c, t = result['common'], result['three_way_intersection']
    total_d = np.asarray(t['total_K_CMB']) - c['total_K_CMB']
    mid_d = (matrices['three_way_intersection'] - matrices['common']) @ mid
    tail_d = np.asarray(t['tail_9_to_L_K_CMB']) - c['tail_9_to_L_K_CMB']
    contrast = account_projected_bands(total_d, np.zeros(64), mid_d, tail_d,
        reference_scale=max(np.linalg.norm(c['total_K_CMB']), np.linalg.norm(t['total_K_CMB'])))
    bl = eb_indices((2, 3, 4, 5))[1]
    e_diff = np.asarray(t['tail_E_only_projection_K_CMB']) - c['tail_E_only_projection_K_CMB']
    contrast['delta_B_from_processed_E_9_to_L_K_CMB'] = e_diff[bl].tolist()
    return {'schema': SCHEMA, 'lmax': lmax, 'units': 'K_CMB',
            'coefficients_are': 'PSEUDO_ALMS_OF_COMMON_WINDOW_TIMES_DELIVERED_QU',
            'masks': result, 'two_mask_difference': contrast,
            'beam_applied_again': False, 'beam_deconvolution': False,
            'tail_beyond_L': 'NOT_BOUNDED', 'p_value': None, 'claim': CLAIM}


def half_difference(first, second):
    a, b = np.asarray(first), np.asarray(second)
    if a.shape != b.shape or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError('SPLIT_ALM_SHAPE_OR_VALUES')
    return (a - b) / 2.


def source_path(root, product):
    if product not in PRODUCTS:
        raise ValueError('PRODUCT_NOT_SUPPORTED')
    return Path(root) / 'planck/PR3/cmb' / f'COM_CMB_IQU-smica_2048_R3.00_{product}.fits'


def check_sources(root, products):
    from l01_smica_fits_integrity import inspect_smica_fits
    records = {}
    for product in products:
        p = source_path(root, product)
        layout = inspect_smica_fits(p, product)
        obs = digest_file(p)
        if obs != SOURCE_SHA[product]:
            raise ValueError('SMICA_REPORTED_SOURCE_SHA_MISMATCH_' + product)
        records[product] = {'path': str(p), 'sha256': obs, 'layout': layout,
            'origin': 'USER_REPORTED_IRSA_DOWNLOAD_NOT_PUBLISHER_SIGNED'}
    return records


def read_windows(root, hp, native_receipt):
    coarse = {}; window = np.ones(12 * NATIVE_NSIDE**2, dtype=bool)
    for name, basename in NAME.items():
        p = Path(root) / 'planck/PR3/masks' / basename
        if p.is_symlink() or digest_file(p) != V2_INPUT_HASHES[name]:
            raise ValueError('PMASK_SOURCE_SHA_MISMATCH_' + name)
        layout = inspect_planck_pmask(p)
        mm = np.memmap(p, dtype='>f4', mode='r', offset=layout['data_offset'], shape=(layout['count'],))
        for start in range(0, len(mm), 1 << 20):
            x = mm[start:start + (1 << 20)]
            if not np.isfinite(x).all() or np.any((x < 0) | (x > 1)):
                raise ValueError('INVALID_NATIVE_PMASK_VALUES')
            window[start:start + len(x)] &= x > .5
        coarse[name] = hp.ud_grade(mm, nside_out=OUT_NSIDE, order_in='NESTED', order_out='RING')
        del mm
    masks, _ = choose_support(coarse, threshold=.5)
    for name, mask in masks.items():
        if canonical_ring64_mask_sha256(mask) != native_receipt[name]['ring64_binary_mask_sha256']:
            raise ValueError('COARSE_MASK_CHANGED_' + name)
    whash = hashlib.sha256(window.astype(np.uint8).tobytes()).hexdigest()
    return window, masks, whash


def native_alms(path, product, window, lmax, hp):
    """Read strided native NESTED Q/U with bounded array count; no data is rewritten."""
    from l01_smica_fits_integrity import _read_header
    p = Path(path)
    before = (p.stat().st_size, p.stat().st_mtime_ns)
    with p.open('rb') as f:
        _, offset = _read_header(f, 0, before[0])
        h, offset = _read_header(f, offset, before[0])
    width = 10 if product == 'full' else 3
    if int(h['NAXIS2']) != window.size or int(h['NAXIS1']) != 4 * width:
        raise ValueError('NATIVE_QU_LAYOUT')
    mm = np.memmap(p, dtype='>f4', mode='r', offset=offset, shape=(window.size, width))
    maps = []
    for col in (1, 2):
        field = masked_field(mm[:, col], window)
        maps.append(hp.reorder(field, n2r=True))
        del field
    del mm
    alms = np.asarray(hp.map2alm_spin(maps, spin=2, lmax=lmax, mmax=lmax))
    del maps
    if before != (p.stat().st_size, p.stat().st_mtime_ns):
        raise ValueError('SOURCE_CHANGED_DURING_READ')
    check_alms(alms, lmax)
    return alms


def save_checkpoint(folder, name, alms, report, contract):
    folder = Path(folder); folder.mkdir(parents=True, exist_ok=True)
    npz = folder / (name + '.npz'); js = folder / (name + '.json')
    if any(x.exists() for x in (npz, js)):
        raise ValueError('CHECKPOINT_ALREADY_EXISTS_' + name)
    with npz.open('xb') as stream:
        np.savez_compressed(stream, E=alms[0], B=alms[1])
    record = {'contract': contract, 'alms_npz_sha256': digest_file(npz), 'result': report}
    with js.open('x', encoding='utf-8') as stream:
        json.dump(record, stream, sort_keys=True, indent=2, allow_nan=False); stream.write('\n')


def load_checkpoint(folder, name, contract):
    npz = Path(folder) / (name + '.npz'); js = Path(folder) / (name + '.json')
    if not npz.exists() and not js.exists():
        return None
    if not (npz.is_file() and js.is_file()) or npz.is_symlink() or js.is_symlink():
        raise ValueError('INCOMPLETE_OR_UNSAFE_CHECKPOINT_' + name)
    record = json.loads(js.read_text())
    if record.get('contract') != contract or digest_file(npz) != record.get('alms_npz_sha256'):
        raise ValueError('CHECKPOINT_IDENTITY_MISMATCH_' + name)
    with np.load(npz, allow_pickle=False) as data:
        if set(data.files) != {'E', 'B'}:
            raise ValueError('CHECKPOINT_ALM_KEYS')
        a = np.array([data['E'], data['B']])
    check_alms(a, contract['lmax'])
    return a


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', required=True)
    ap.add_argument('--native-receipt', required=True)
    ap.add_argument('--out-dir', required=True)
    ap.add_argument('--lmax', type=int, choices=(16, 32, 64, 128), default=32)
    ap.add_argument('--products', nargs='+', choices=PRODUCTS, default=list(PRODUCTS))
    ap.add_argument('--check-inputs-only', action='store_true')
    args = ap.parse_args(argv)
    products = list(dict.fromkeys(args.products))
    native, k = verify_receipt(args.native_receipt, enforce_reported_pins=True)
    sources = check_sources(args.root, products)
    if args.check_inputs_only:
        print(json.dumps({'status': 'PASS_PINNED_SMICA_AND_EXISTING_K_INPUTS', 'sources': sources}, indent=2))
        return 0
    try:
        import healpy as hp
    except ImportError as exc:
        raise RuntimeError('HEALPY_REQUIRED_FOR_NATIVE_SPIN2_ANALYSIS') from exc
    spin = spin2_full_ell_healpy_check()
    window, masks, window_sha = read_windows(args.root, hp, native)
    theta, phi = pix2ang_ring(OUT_NSIDE)
    low = block_design(theta, phi, 2, 5)
    projectors = {name: Projector.from_design(low, m) for name, m in masks.items()}
    del low
    common_contract = {'schema': SCHEMA, 'lmax': args.lmax, 'nside_out': OUT_NSIDE,
        'native_window_sha256': window_sha, 'native_receipt_sha256': digest_file(args.native_receipt),
        'analysis_code_sha256': digest_file(__file__), 'healpy_version': hp.__version__,
        'dependency_sha256': {name: digest_file(sys.modules[name].__file__) for name in
            ('spin2_finite', 'healpix_ring_coords', 'fits_source_identity',
             'l01_k_spectral_certificate', 'native_planck_pol_response', 'l01_smica_fits_integrity')},
        'native_window': 'AND_OF_THREE_NATIVE_PMASKS_STRICTLY_GT_0_5',
        'mask_order': 'NESTED2048', 'missing_inside_fixed_window': 'REJECT',
        'processing': 'MASK_NATIVE_QU_THEN_MAP2ALM_SPIN_THEN_ALM2MAP_SPIN_RING64'}
    all_alms = {}; results = {}
    for product in products:
        contract = dict(common_contract, product=product, source_sha256=sources[product]['sha256'])
        cached = load_checkpoint(args.out_dir, product, contract)
        start = time.perf_counter()
        alms = cached if cached is not None else native_alms(sources[product]['path'], product, window, args.lmax, hp)
        report = analyze_alms(alms, args.lmax, hp, projectors, k)
        if cached is None:
            save_checkpoint(args.out_dir, product, alms, report, contract)
        all_alms[product] = alms; results[product] = report
        print(json.dumps({'product': product, 'status': 'PASS_PROCESSED_MAP_BAND_CLOSURE',
            'checkpoint_reused': cached is not None, 'seconds': time.perf_counter() - start}), flush=True)
    split_results = {}
    for name, a, b in (('hm_half_difference', 'hm1', 'hm2'), ('oe_half_difference', 'oe1', 'oe2')):
        if a in all_alms and b in all_alms:
            split_results[name] = analyze_alms(half_difference(all_alms[a], all_alms[b]), args.lmax, hp, projectors, k)
    summary = {'schema': SCHEMA, 'status': 'PASS_WINDOWED_QU_FINITE_BAND_ACCOUNTING',
        'contract': common_contract, 'source_receipts': sources, 'all_m_check': spin,
        'results': results, 'split_results': split_results, 'independent_sky_count': 1,
        'split_noise_covariance': 'NOT_INFERRED_FROM_TWO_DIFFERENCE_MAPS',
        'beam_policy': 'DELIVERED_MAP_BEAM_LEFT_IN_PLACE_NOT_APPLIED_TWICE',
        'physical_tail_beyond_lmax': 'NOT_BOUNDED', 'p_value': None,
        'publication_dag_completed': 14, 'publication_dag_total': 42,
        'paper_gate': 'NOT_READY_TO_SUBMIT'}
    dest = Path(args.out_dir) / 'summary.json'
    temp = dest.with_suffix('.json.tmp')
    temp.write_text(json.dumps(summary, indent=2, sort_keys=True, allow_nan=False) + '\n')
    temp.replace(dest)
    print(json.dumps({'status': summary['status'], 'summary': str(dest), 'products': products,
        'lmax': args.lmax, 'paper_gate': summary['paper_gate']}, indent=2))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, RuntimeError, OSError) as exc:
        print(json.dumps({'status': 'BLOCKED', 'error': str(exc), 'error_type': type(exc).__name__}), file=sys.stderr)
        raise SystemExit(2)
