"""Same-window SMICA split spectra from EXISTING processed-band checkpoints.

Consumes l01_smica_processed_bands.py JSON/NPZ products, without re-reading FITS,
recomputing spin transforms, applying a second beam, or inferring a noise prior.
C_ell here is a windowed delivered-map pseudo-spectrum in K_CMB^2, not cosmic C_ell.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import zipfile

import numpy as np

PRODUCER_SCHEMA = 'htt.L01_SMICA_windowed_QU_band_accounting/1'
CLAIM = 'PROCESSED_MAP_DIAGNOSTIC_NOT_COSMIC_EB_OR_CALIBRATED_NULL'
PRODUCTS = ('full', 'hm1', 'hm2', 'oe1', 'oe2')
NATIVE_RECEIPT_SHA = '7b4763afe8e5d30a02be296b0d4f7281a30f4e80937975dcda5f929643c2a7b6'
# User-reported source identities, NOT publisher signatures.
SOURCE_SHA = {
    'full': '60952c645eb33d151905ddf5837477e15ca02a3261feca4ceca3c3feece4f9ac',
    'hm1': '736338208cf0b494c3b6c13c444f116262c8052dcb4a7842dc738bf6a4a426b0',
    'hm2': '0a4dc860a6f7bbdb5980cd7ac1d187ba9139a383c9c47f159e069281c3d5f3a5',
    'oe1': '5473304ed71348cb346b335bca0deb417c9dd3f0286c7e3d2dfd5e1fc93f503a',
    'oe2': 'da9c3e3e09fdff87ada31db00417ae7688facc8b47756576ed8daec12fe1e2f0',
}


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(4 << 20), b''):
            h.update(block)
    return h.hexdigest()


def checked_alms(value, lmax):
    if isinstance(lmax, bool) or not isinstance(lmax, (int, np.integer)) or not 2 <= lmax <= 128:
        raise ValueError('LMAX_REQUIRES_INTEGER_2_TO_128')
    a = np.asarray(value)
    if a.shape != (2, (lmax+1)*(lmax+2)//2) or a.dtype.kind not in 'fci':
        raise ValueError('SPIN2_ALM_SHAPE_OR_TYPE')
    a = a.astype(np.complex128, copy=False)
    if not np.isfinite(a).all():
        raise ValueError('SPIN2_ALM_NONFINITE')
    if np.any(a[:, :lmax+1].imag != 0):
        raise ValueError('REAL_MAP_M0_REQUIRED')
    if np.any(a[:, :2] != 0) or np.any(a[:, lmax+1] != 0):
        raise ValueError('SPIN2_ELL_LESS_2_MUST_BE_ZERO')
    return a


def cross_spectrum_matrix(first, second, lmax):
    """Real C_ell^{X(first),Y(second)}, X,Y=E,B; healpy m-major packed alms.

    Negative m follows a_l,-m=(-1)^m conjugate(a_lm). Its contribution is
    2 Re(a_lm b_lm*) for m>0; m=0 has multiplicity one.
    """
    a, b = checked_alms(first, lmax), checked_alms(second, lmax)
    out = np.zeros((2, 2, lmax+1))
    with np.errstate(over='raise', invalid='raise'):
        for ell in range(2, lmax+1):
            m = np.arange(ell+1)
            ix = m*(2*lmax+1-m)//2+ell
            weights = np.full(ell+1, 2.); weights[0] = 1.
            out[:, :, ell] = np.einsum('im,jm,m->ij', a[:, ix], b[:, ix].conj(), weights).real/(2*ell+1)
    if not np.isfinite(out).all():
        raise ValueError('SPECTRUM_NOT_FINITE')
    return out


def spectrum_record(matrix):
    c = np.asarray(matrix)
    bands = {}
    for name, lo, hi in (('2_to_5', 2, min(5, c.shape[-1]-1)),
                         ('6_to_8', 6, min(8, c.shape[-1]-1)),
                         ('9_to_L', 9, c.shape[-1]-1)):
        if lo <= hi:
            weights = (2*np.arange(lo, hi+1)+1)/(4*np.pi)
            integrated = np.sum(c[:, :, lo:hi+1]*weights, axis=-1)
            bands[name] = {'EE_K_CMB2': float(integrated[0, 0]),
                           'BB_K_CMB2': float(integrated[1, 1]),
                           'EB_K_CMB2': float(integrated[0, 1])}
    return {'EE_K_CMB2': c[0, 0].tolist(), 'EB_K_CMB2': c[0, 1].tolist(),
            'BE_K_CMB2': c[1, 0].tolist(), 'BB_K_CMB2': c[1, 1].tolist(),
            'weighted_band_sums': bands}


def pair_diagnostics(first, second, lmax):
    a, b = checked_alms(first, lmax), checked_alms(second, lmax)
    plus, minus = (a+b)/2, (a-b)/2
    aa = cross_spectrum_matrix(a, a, lmax)
    bb = cross_spectrum_matrix(b, b, lmax)
    pp = cross_spectrum_matrix(plus, plus, lmax)
    mm = cross_spectrum_matrix(minus, minus, lmax)
    ab = cross_spectrum_matrix(a, b, lmax)
    symmetric = (ab+ab.transpose(1, 0, 2))/2
    # Scale in physical units by parent auto-power, not a fixed K_CMB^2 floor
    # and not a near-zero difference. This is arithmetic closure, NOT uncertainty.
    scale = np.maximum(np.max(abs(aa)+abs(bb), axis=(0, 1)), np.finfo(float).tiny)
    relative = float(np.max(np.max(abs(pp-mm-symmetric), axis=(0, 1))/scale))
    if relative > 5e-12:
        raise ValueError('SPLIT_SUM_DIFFERENCE_CROSS_IDENTITY_FAILED')
    return {'half_sum': spectrum_record(pp), 'half_difference': spectrum_record(mm),
            'cross_12': spectrum_record(ab), 'cross_symmetrized': spectrum_record(symmetric),
            'sum_difference_cross_max_relative': relative,
            'noise_covariance_estimated': False,
            'interpretation': 'HALF_DIFFERENCE_RETAINS_TRANSFER_RESIDUAL_AND_CORRELATED_NOISE'}


def _regular(path, limit):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > limit:
        raise ValueError('CHECKPOINT_MISSING_UNSAFE_OR_OVERSIZE: '+str(path))


def _json(path):
    _regular(path, 16 << 20)
    def pairs(items):
        d = {}
        for k, v in items:
            if k in d:
                raise ValueError('JSON_DUPLICATE_KEY: '+k)
            d[k] = v
        return d
    def bad_constant(s):
        raise ValueError('JSON_NONFINITE: '+s)
    value = json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=pairs,
                       parse_constant=bad_constant)
    if not isinstance(value, dict):
        raise ValueError('CHECKPOINT_JSON_MUST_BE_OBJECT')
    return value


def read_checkpoints(folder):
    """Bind five archived alms to one producer contract and all five source pins.

    This checks checkpoint attribution/bytes; it does not re-authenticate the
    multi-GB FITS source or establish physical simulation exchangeability.
    """
    folder = Path(folder)
    summary_path = folder/'summary.json'
    summary = _json(summary_path)
    if (summary.get('schema') != PRODUCER_SCHEMA or
        summary.get('status') != 'PASS_WINDOWED_QU_FINITE_BAND_ACCOUNTING' or
        summary.get('paper_gate') != 'NOT_READY_TO_SUBMIT' or
        summary.get('independent_sky_count') != 1):
        raise ValueError('PRODUCER_SUMMARY_SCHEMA_STATUS_OR_CLAIM_MISMATCH')
    common = summary.get('contract', {})
    lmax = common.get('lmax')
    if isinstance(lmax, bool) or not isinstance(lmax, int) or lmax not in (16, 32, 64, 128):
        raise ValueError('CHECKPOINT_LMAX')
    fields = {'schema': PRODUCER_SCHEMA, 'nside_out': 64,
              'native_receipt_sha256': NATIVE_RECEIPT_SHA,
              'mask_order': 'NESTED2048', 'missing_inside_fixed_window': 'REJECT',
              'native_window': 'AND_OF_THREE_NATIVE_PMASKS_STRICTLY_GT_0_5',
              'processing': 'MASK_NATIVE_QU_THEN_MAP2ALM_SPIN_THEN_ALM2MAP_SPIN_RING64'}
    if any(common.get(k) != v for k, v in fields.items()):
        raise ValueError('PRODUCER_PROCESSING_CONTRACT_MISMATCH')
    for key in ('native_window_sha256', 'analysis_code_sha256'):
        if not re.fullmatch('[0-9a-f]{64}', str(common.get(key, ''))):
            raise ValueError('MALFORMED_CONTRACT_DIGEST: '+key)
    dependencies = common.get('dependency_sha256')
    if (not isinstance(dependencies, dict) or not dependencies or
        any(not re.fullmatch('[0-9a-f]{64}', str(v)) for v in dependencies.values()) or
        not isinstance(common.get('healpy_version'), str) or not common['healpy_version']):
        raise ValueError('PRODUCER_DEPENDENCY_IDENTITY_MISSING')
    arrays, evidence = {}, {}
    for product in PRODUCTS:
        p, j = folder/(product+'.npz'), folder/(product+'.json')
        record = _json(j)
        expected = dict(common, product=product, source_sha256=SOURCE_SHA[product])
        if record.get('contract') != expected:
            raise ValueError('SPLIT_CHECKPOINT_CONTRACT_MISMATCH: '+product)
        if (summary.get('source_receipts', {}).get(product, {}).get('sha256') != SOURCE_SHA[product]
            or record.get('result', {}).get('claim') != CLAIM):
            raise ValueError('SPLIT_SOURCE_OR_CLAIM_MISMATCH: '+product)
        _regular(p, 4 << 20)
        observed = digest(p)
        if observed != record.get('alms_npz_sha256'):
            raise ValueError('SPLIT_NPZ_BYTE_MISMATCH: '+product)
        with zipfile.ZipFile(p) as archive:
            info = archive.infolist()
            if sorted(x.filename for x in info) != ['B.npy', 'E.npy'] or sum(x.file_size for x in info) > (1 << 20):
                raise ValueError('CHECKPOINT_NPZ_LAYOUT_OR_EXPANSION')
        with np.load(p, allow_pickle=False) as data:
            arrays[product] = checked_alms(np.stack((data['E'], data['B'])), lmax).copy()
        evidence[product] = {'npz_sha256': observed, 'record_sha256': digest(j),
                             'source_sha256': SOURCE_SHA[product]}
    return arrays, common, {'producer_summary_sha256': digest(summary_path), 'products': evidence}


def analyze_checkpoints(folder):
    arrays, contract, evidence = read_checkpoints(folder)
    lmax = contract['lmax']
    pairs, residuals = {}, {}
    differences = {}
    for name, first, second in (('HM', 'hm1', 'hm2'), ('OE', 'oe1', 'oe2')):
        a, b = arrays[first], arrays[second]
        pairs[name] = pair_diagnostics(a, b, lmax)
        differences[name] = (a-b)/2
        residual = arrays['full']-(a+b)/2
        residuals['full_minus_'+name.lower()+'_mean'] = spectrum_record(cross_spectrum_matrix(residual, residual, lmax))
    return {'schema': 'htt.L01_same_window_split_pseudocl/1',
            'status': 'PASS_SAME_WINDOW_SPLIT_SPECTRA', 'lmax': lmax,
            'ell': list(range(lmax+1)), 'units': 'K_CMB^2',
            'source_kind': 'ARCHIVED_WINDOWED_DELIVERED_MAP_ALMS',
            'producer_contract': contract, 'checkpoint_evidence': evidence,
            'auto_spectra': {p: spectrum_record(cross_spectrum_matrix(a, a, lmax)) for p, a in arrays.items()},
            'split_pairs': pairs, 'residuals': residuals,
            'HM_OE_half_difference_cross': spectrum_record(cross_spectrum_matrix(differences['HM'], differences['OE'], lmax)),
            'cross_is_covariance_estimator': False, 'independent_sky_count': 1,
            'tail_beyond_lmax': 'NOT_BOUNDED', 'beam_applied_again': False,
            'beam_deconvolution': False, 'noise_debiasing': False,
            'p_value': None, 'paper_gate': 'NOT_READY_TO_SUBMIT', 'claim': CLAIM}


def write_new_json(path, result):
    path = Path(path)
    if path.exists() or path.is_symlink():
        raise ValueError('OUTPUT_EXISTS_NOT_OVERWRITTEN')
    payload = (json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+'\n').encode('utf-8')
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix='.'+path.name+'.', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(payload); stream.flush(); os.fsync(stream.fileno())
        os.link(temp, path)  # same-filesystem, no-clobber atomic publication
    finally:
        os.unlink(temp)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--band-dir', required=True, help='Existing producer directory containing summary and five JSON/NPZ pairs')
    ap.add_argument('--out', required=True)
    args = ap.parse_args(argv)
    try:
        result = analyze_checkpoints(args.band_dir)
        result['analysis_code_sha256'] = digest(__file__)
        write_new_json(args.out, result)
    except (ValueError, OSError, KeyError, TypeError, FloatingPointError, zipfile.BadZipFile) as exc:
        print(json.dumps({'status': 'BLOCKED', 'error_type': type(exc).__name__, 'error': str(exc)}), file=sys.stderr)
        return 2
    residuals = {k: v['sum_difference_cross_max_relative'] for k, v in result['split_pairs'].items()}
    print(json.dumps({'status': result['status'], 'lmax': result['lmax'],
                      'identity_residuals': residuals, 'out': args.out,
                      'low_band_2_to_5_K_CMB2': {
                          'full_auto': result['auto_spectra']['full']['weighted_band_sums']['2_to_5'],
                          'HM_half_difference': result['split_pairs']['HM']['half_difference']['weighted_band_sums']['2_to_5'],
                          'OE_half_difference': result['split_pairs']['OE']['half_difference']['weighted_band_sums']['2_to_5'],
                          'full_minus_HM_mean': result['residuals']['full_minus_hm_mean']['weighted_band_sums']['2_to_5'],
                          'full_minus_OE_mean': result['residuals']['full_minus_oe_mean']['weighted_band_sums']['2_to_5']},
                      'noise_debiasing': False, 'paper_gate': result['paper_gate']}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
